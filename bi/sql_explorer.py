"""Consultas SQL: read-only analytical SQL on the gold layer of datos.duckdb.

The destination of the «Consultas SQL» node of the pipeline diagram. Unlike the
console removed in D-143, the visitor never sees surrogate keys: every query runs
on a layer of temporary views with readable Spanish columns (precios, semanas,
productos, ipc_semanal, ipc_mensual, cargas, rechazos, modelos_dbt), created on
each new connection.

Safety, in layers:
- a NEW connection per query, opened read-only and with external access disabled
  (no files, no URLs, no extensions); the configuration is then locked;
- only one statement, of type SELECT, starting with SELECT, WITH, DESCRIBE, SHOW
  or SUMMARIZE; file-reading functions are rejected with a clear message;
- the user text is never interpolated into other SQL except as the body of
  SELECT * FROM (<query>) LIMIT n, after it parsed as exactly one SELECT;
- a timer interrupts the connection after TIMEOUT_SECONDS.
"""
import html
import os
import re
import tempfile
import threading
import time
from dataclasses import dataclass
from functools import partial

import duckdb
import pandas as pd

from bi import charts, queries

# region Variables
ROW_LIMIT = 5000
TIMEOUT_SECONDS = 10
MEMORY_LIMIT = "1GB"
EXPORT_WEEKS = 52
ALLOWED_FIRST_WORDS = ("SELECT", "WITH", "DESCRIBE", "SHOW", "SUMMARIZE")
# Table functions that read files or URLs. External access is disabled anyway;
# this check only gives the visitor a clear message instead of an engine error.
FILE_FUNCTION_PATTERN = re.compile(
    r"\b(read_\w+|\w+_scan|glob|sniff_csv|parquet_\w+|iceberg_\w+|delta_\w+|query|query_table)\s*\(",
    re.IGNORECASE)
URL_PATTERN = re.compile(r"'\s*(https?|s3|s3a|gcs|gs|az|azure|abfss|r2|hf)://", re.IGNORECASE)
FIRST_WORD_PATTERN = re.compile(r"[A-Za-z_]+")

# Each view: (name, what it holds, SQL). Ordered as the visitor should read them.
VIEWS = [
    ("precios",
     "Un precio semanal por producto, región y canal (consumidor y mayorista). "
     "marca = 'SIN_MARCA' es un precio válido para los indicadores; 'ATIPICO' y "
     "'UNIDAD_NO_CONVERTIBLE' quedan fuera de ellos.",
     """SELECT CAST(w.week_start AS DATE) AS semana,
       d.year AS anio,
       d.month AS mes,
       p.product_group AS familia,
       p.product AS producto,
       p.variety AS variedad,
       p.quality AS calidad,
       c.channel AS canal,
       CASE c.source WHEN 'wholesale' THEN 'mayorista' ELSE 'consumidor' END AS fuente,
       r.region AS region,
       w.normalized_unit AS unidad,
       w.price AS precio,
       w.volume AS volumen,
       w.observation_count AS observaciones,
       COALESCE(w.flag, 'SIN_MARCA') AS marca
FROM weekly_price AS w
JOIN dim_product AS p ON p.product_id = w.product_id
JOIN dim_region AS r ON r.region_id = w.region_id
JOIN dim_channel AS c ON c.channel_id = w.channel_id
LEFT JOIN dim_date AS d ON d.week_start = w.week_start"""),
    ("semanas",
     "Calendario: una fila por semana, desde la primera hasta la última con precios.",
     """SELECT CAST(week_start AS DATE) AS semana, iso_year AS anio_iso, iso_week AS semana_iso,
       month AS mes, month_name AS nombre_mes, year AS anio, season AS estacion
FROM dim_date"""),
    ("productos",
     "Catálogo de productos: familia, producto, variedad y calidad.",
     """SELECT product_group AS familia, product AS producto, variety AS variedad, quality AS calidad
FROM dim_product"""),
    ("ipc_semanal",
     "IPC de alimentos del INE llevado a cada semana. precio × factor_real = precio en "
     "pesos del último mes publicado; provisional = el mes aún no está publicado.",
     """SELECT CAST(week_start AS DATE) AS semana, ipc_year AS anio_ipc, ipc_month AS mes_ipc,
       food_index AS indice_alimentos, reference_year AS anio_referencia,
       reference_month AS mes_referencia, real_factor AS factor_real, provisional
FROM ipc_weekly"""),
    ("ipc_mensual",
     "IPC de alimentos del INE, un valor por mes publicado.",
     """SELECT year AS anio, month AS mes, food_index AS indice_alimentos, origin AS origen
FROM ipc_monthly"""),
    ("cargas",
     "Ejecuciones del pipeline: cuándo empezó cada carga, su estado y cuántas filas leyó, "
     "cargó y rechazó.",
     """SELECT CAST(started_at AS TIMESTAMP) AS inicio, status AS estado, rows_read AS filas_leidas,
       rows_loaded AS filas_cargadas, rows_rejected AS filas_rechazadas, message AS mensaje
FROM etl_run"""),
    ("rechazos",
     "Filas de origen que la validación rechazó, con su motivo y los datos que traían.",
     """SELECT CAST(e.started_at AS TIMESTAMP) AS inicio_carga,
       CASE r.source WHEN 'wholesale' THEN 'mayorista' ELSE 'consumidor' END AS fuente,
       r.reason AS motivo,
       COALESCE(r.original_row ->> 'price_date', r.original_row ->> 'week_start') AS fecha_precio,
       r.original_row ->> 'region' AS region,
       r.original_row ->> 'product' AS producto,
       r.original_row ->> 'variety' AS variedad,
       r.original_row AS fila_original
FROM rejection AS r
LEFT JOIN etl_run AS e ON e.run_id = r.run_id"""),
    ("modelos_dbt",
     "Modelos y pruebas de dbt que construyen esta base, con el resultado de su última ejecución.",
     """SELECT n.name AS nombre, n.resource_type AS tipo, NULLIF(n.layer, '') AS capa,
       NULLIF(n.materialized, '') AS materializacion, NULLIF(n.column_name, '') AS columna,
       n.description AS descripcion, r.status AS estado,
       r.execution_time AS segundos, r.failures AS fallas
FROM dbt_node AS n
LEFT JOIN dbt_result AS r ON r.unique_id = n.unique_id"""),
]
VIEW_NAMES = [name for name, _, _ in VIEWS]

# Each example: (title, the question it answers, SQL). All run on the views above.
EXAMPLES = [
    ("Margen por región",
     "¿Cuánto más paga el consumidor que el mayorista en cada región, la última semana con ambos precios?",
     """-- Mismo producto, región, unidad y semana en los dos canales; solo precios válidos.
WITH ultima AS (
    SELECT max(semana) AS semana FROM precios WHERE fuente = 'mayorista'
),
pares AS (
    SELECT c.region, c.precio AS consumidor, m.precio AS mayorista
    FROM precios AS c
    JOIN precios AS m
      ON m.semana = c.semana AND m.region = c.region AND m.producto = c.producto
     AND m.variedad = c.variedad AND m.calidad = c.calidad AND m.unidad = c.unidad
    WHERE c.fuente = 'consumidor' AND m.fuente = 'mayorista'
      AND c.marca = 'SIN_MARCA' AND m.marca = 'SIN_MARCA'
      AND c.semana = (SELECT semana FROM ultima)
)
SELECT region,
       count(*) AS comparaciones,
       round(median((consumidor - mayorista) / mayorista) * 100, 1) AS margen_mediano_pct,
       round(avg((consumidor - mayorista) / mayorista) * 100, 1) AS margen_promedio_pct
FROM pares
GROUP BY region
ORDER BY margen_mediano_pct DESC"""),
    ("Mayores subidas de la semana",
     "¿Qué productos subieron más respecto de la semana anterior, comparando solo regiones presentes en ambas?",
     """-- Cada región entra solo si tiene precio las dos semanas (regiones comunes).
WITH semanas AS (
    SELECT max(semana) AS actual, max(semana) - INTERVAL 7 DAY AS anterior FROM precios
),
pares AS (
    SELECT a.producto, a.variedad, a.calidad, a.canal, a.unidad, a.region,
           a.precio AS actual, b.precio AS anterior
    FROM precios AS a
    JOIN precios AS b
      ON b.producto = a.producto AND b.variedad = a.variedad AND b.calidad = a.calidad
     AND b.canal = a.canal AND b.unidad = a.unidad AND b.region = a.region
    WHERE a.semana = (SELECT actual FROM semanas)
      AND b.semana = (SELECT anterior FROM semanas)
      AND a.marca = 'SIN_MARCA' AND b.marca = 'SIN_MARCA'
)
SELECT producto, variedad, calidad, canal, unidad,
       count(*) AS regiones_comunes,
       round(avg(anterior)) AS precio_anterior,
       round(avg(actual)) AS precio_actual,
       round((avg(actual) / avg(anterior) - 1) * 100, 1) AS variacion_pct
FROM pares
GROUP BY ALL
HAVING count(*) >= 3
ORDER BY variacion_pct DESC
LIMIT 10"""),
    ("Precio real vs nominal",
     "¿Cuánto subió el tomate en supermercado descontando la inflación de alimentos?",
     """-- Promedio nacional simple de las regiones con precio esa semana.
-- precio real = precio × factor_real (pesos del último mes publicado del IPC).
SELECT p.semana,
       round(avg(p.precio)) AS precio_nominal,
       round(avg(p.precio) * any_value(i.factor_real)) AS precio_real,
       any_value(i.provisional) AS ipc_provisional
FROM precios AS p
JOIN ipc_semanal AS i ON i.semana = p.semana
WHERE p.producto = 'Tomate' AND p.variedad = 'Larga vida' AND p.calidad = 'Primera'
  AND p.unidad = 'kilo' AND p.canal = 'Supermercado' AND p.marca = 'SIN_MARCA'
GROUP BY p.semana
ORDER BY p.semana"""),
    ("Evolución anual por familia",
     "¿Cuánto subió cada familia de productos respecto del año anterior, en el mismo tramo del año?",
     """-- Compara de enero a la misma semana ISO de la última semana con datos, para no
-- mezclar un año completo con uno en curso. Por producto, canal y unidad se toma el
-- promedio nacional del tramo; la familia resume con la mediana de esas variaciones.
WITH corte AS (
    SELECT semana_iso FROM semanas WHERE semana = (SELECT max(semana) FROM precios)
),
anual AS (
    SELECT p.familia, p.producto, p.variedad, p.calidad, p.canal, p.unidad, s.anio_iso AS anio,
           avg(p.precio) AS precio
    FROM precios AS p
    JOIN semanas AS s ON s.semana = p.semana
    WHERE p.marca = 'SIN_MARCA' AND s.semana_iso <= (SELECT semana_iso FROM corte)
    GROUP BY ALL
),
variaciones AS (
    SELECT familia, anio,
           precio / lag(precio) OVER (PARTITION BY familia, producto, variedad, calidad, canal, unidad
                                      ORDER BY anio) - 1 AS variacion,
           anio - lag(anio) OVER (PARTITION BY familia, producto, variedad, calidad, canal, unidad
                                  ORDER BY anio) AS salto
    FROM anual
)
SELECT familia, anio,
       count(*) AS series_comparadas,
       round(median(variacion) * 100, 1) AS variacion_mediana_pct
FROM variaciones
WHERE salto = 1
GROUP BY familia, anio
ORDER BY familia, anio"""),
    ("Regiones más caras",
     "¿En qué regiones el tomate es más caro al consumidor en las últimas 4 semanas?",
     """WITH ventana AS (
    SELECT * FROM precios
    WHERE producto = 'Tomate' AND variedad = 'Larga vida' AND calidad = 'Primera'
      AND unidad = 'kilo' AND fuente = 'consumidor' AND marca = 'SIN_MARCA'
      AND semana > (SELECT max(semana) FROM precios) - INTERVAL 28 DAY
)
SELECT region,
       count(*) AS precios,
       round(avg(precio)) AS precio_promedio,
       round((avg(precio) / (SELECT avg(precio) FROM ventana) - 1) * 100, 1) AS sobre_promedio_nacional_pct
FROM ventana
GROUP BY region
ORDER BY precio_promedio DESC"""),
    ("Rechazos por motivo",
     "¿Por qué se rechazaron filas de origen en la última carga, y de qué regiones venían?",
     """SELECT fuente, motivo, region, count(*) AS filas, min(fecha_precio) AS primera_fecha,
       max(fecha_precio) AS ultima_fecha
FROM rechazos
WHERE inicio_carga = (SELECT max(inicio_carga) FROM rechazos)
GROUP BY ALL
ORDER BY filas DESC"""),
    ("Cobertura semanal",
     "¿Cuántos precios, productos y regiones trae cada una de las últimas 12 semanas, y con qué IPC?",
     """SELECT s.semana,
       count(*) FILTER (WHERE p.fuente = 'consumidor') AS precios_consumidor,
       count(*) FILTER (WHERE p.fuente = 'mayorista') AS precios_mayorista,
       count(DISTINCT p.producto) AS productos,
       count(DISTINCT p.region) AS regiones,
       round(avg(CASE WHEN p.marca = 'SIN_MARCA' THEN 1 ELSE 0 END) * 100, 1) AS validos_pct,
       any_value(i.provisional) AS ipc_provisional
FROM semanas AS s
LEFT JOIN precios AS p ON p.semana = s.semana
LEFT JOIN ipc_semanal AS i ON i.semana = s.semana
WHERE s.semana > (SELECT max(semana) FROM semanas) - INTERVAL 84 DAY
GROUP BY s.semana
ORDER BY s.semana DESC"""),
    ("Pruebas de dbt",
     "¿Qué modelos y pruebas de dbt construyen esta base y cómo terminó su última ejecución?",
     """SELECT tipo, coalesce(capa, '—') AS capa, estado, count(*) AS nodos,
       round(sum(segundos), 2) AS segundos_totales, sum(fallas) AS fallas
FROM modelos_dbt
GROUP BY ALL
ORDER BY tipo, capa"""),
]

# Gold tables offered as CSV in «Llevar los datos a otra herramienta».
EXPORTS = [
    ("precios_52_semanas.csv", f"Precios de las últimas {EXPORT_WEEKS} semanas",
     f"SELECT * FROM precios WHERE semana > (SELECT max(semana) FROM precios) "
     f"- INTERVAL {EXPORT_WEEKS * 7} DAY ORDER BY semana, familia, producto, region, canal"),
    ("productos.csv", "Catálogo de productos", "SELECT * FROM productos ORDER BY ALL"),
    ("regiones.csv", "Regiones", "SELECT region FROM dim_region ORDER BY region"),
    ("canales.csv", "Canales",
     "SELECT channel AS canal, CASE source WHEN 'wholesale' THEN 'mayorista' ELSE 'consumidor' END "
     "AS fuente FROM dim_channel ORDER BY fuente, canal"),
    ("semanas.csv", "Calendario de semanas", "SELECT * FROM semanas ORDER BY semana"),
    ("ipc_semanal.csv", "IPC de alimentos por semana", "SELECT * FROM ipc_semanal ORDER BY semana"),
]
# endregion


# region Validation
class QueryRejected(ValueError):
    """A query that the explorer does not run; the message is for the visitor."""


class QueryTimeout(RuntimeError):
    """A query interrupted after TIMEOUT_SECONDS."""


def strip_comments(sql):
    """The text without -- and /* */ comments, leaving string literals untouched."""
    result, position, length = [], 0, len(sql)
    while position < length:
        character = sql[position]
        if character in ("'", '"'):
            end = position + 1
            while end < length:
                if sql[end] == character:
                    if end + 1 < length and sql[end + 1] == character:
                        end += 2
                        continue
                    break
                end += 1
            result.append(sql[position:end + 1])
            position = end + 1
        elif sql.startswith("--", position):
            newline = sql.find("\n", position)
            position = length if newline == -1 else newline
        elif sql.startswith("/*", position):
            close = sql.find("*/", position + 2)
            position = length if close == -1 else close + 2
            result.append(" ")
        else:
            result.append(character)
            position += 1
    return "".join(result)


def validate_query(sql):
    """The query ready to wrap, or QueryRejected with a message in Spanish."""
    text = strip_comments(sql or "").strip()
    while text.endswith(";"):
        text = text[:-1].rstrip()
    if not text:
        raise QueryRejected("Escribe una consulta SELECT antes de ejecutar.")
    first_word = FIRST_WORD_PATTERN.match(text.lstrip("( \n\t"))
    if not first_word or first_word.group(0).upper() not in ALLOWED_FIRST_WORDS:
        raise QueryRejected(
            "Solo se permiten consultas de lectura: SELECT o WITH (también DESCRIBE, SHOW y "
            "SUMMARIZE). INSERT, UPDATE, DELETE, DROP, CREATE, ATTACH, COPY, PRAGMA, SET y "
            "otras instrucciones no se ejecutan.")
    try:
        statements = duckdb.extract_statements(text)
    except duckdb.Error as error:
        raise QueryRejected(f"La consulta no se pudo interpretar: {error}") from error
    if len(statements) != 1:
        raise QueryRejected("Ejecuta una sola consulta a la vez (sin varias instrucciones "
                            "separadas por punto y coma).")
    if statements[0].type != duckdb.StatementType.SELECT:
        raise QueryRejected("Solo se permiten consultas de lectura (SELECT o WITH).")
    if FILE_FUNCTION_PATTERN.search(text) or URL_PATTERN.search(text):
        raise QueryRejected("Las consultas trabajan solo sobre las tablas de esta base: leer "
                            "archivos o direcciones web (read_csv, read_parquet, http…) está "
                            "desactivado.")
    return text
# endregion


# region Connection and execution
def open_explorer_connection(database_file=queries.DATABASE_FILE):
    """A new read-only connection, without external access, with the analysis views.

    External access can only be disabled when the connection opens, so it goes in
    the config; the configuration is locked once the views exist, so no query
    can change it back.
    """
    connection = duckdb.connect(str(database_file), read_only=True,
                                config={"enable_external_access": False})
    try:
        connection.execute("SET enable_external_access = false")
        connection.execute(f"SET memory_limit = '{MEMORY_LIMIT}'")
        for name, _, sql in VIEWS:
            connection.execute(f"CREATE TEMP VIEW {name} AS {sql}")
        connection.execute("SET lock_configuration = true")
    except Exception:
        connection.close()
        raise
    return connection


@dataclass
class QueryResult:
    rows: pd.DataFrame
    truncated: bool
    seconds: float


def run_user_query(sql, database_file=queries.DATABASE_FILE, timeout=TIMEOUT_SECONDS,
                   row_limit=ROW_LIMIT):
    """Validate and run a visitor query; at most row_limit rows, at most timeout seconds."""
    body = validate_query(sql)
    wrapped = f"SELECT * FROM (\n{body}\n) AS consulta LIMIT {int(row_limit) + 1}"
    connection = open_explorer_connection(database_file)
    timer = threading.Timer(timeout, connection.interrupt)
    started = time.perf_counter()
    try:
        timer.start()
        rows = connection.execute(wrapped).df()
    except duckdb.InterruptException as error:
        raise QueryTimeout(f"La consulta superó el límite de {timeout:g} segundos y se detuvo. "
                           "Prueba filtrando por semana, producto o región.") from error
    finally:
        timer.cancel()
        connection.close()
    seconds = time.perf_counter() - started
    truncated = len(rows) > row_limit
    return QueryResult(rows.head(row_limit), truncated, seconds)


def read_view(sql, database_file=queries.DATABASE_FILE):
    """Rows of one of our own queries on the analysis views (never visitor text)."""
    connection = open_explorer_connection(database_file)
    try:
        return connection.execute(sql).df()
    finally:
        connection.close()


def describe_views(database_file=queries.DATABASE_FILE):
    """[(view, description, row count, [(column, type)])] read from the database."""
    connection = open_explorer_connection(database_file)
    try:
        catalog = []
        for name, description, _ in VIEWS:
            columns = [(row[0], row[1]) for row in connection.execute(f"DESCRIBE {name}").fetchall()]
            count = connection.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
            catalog.append((name, description, count, columns))
        return catalog
    finally:
        connection.close()


def to_csv_bytes(rows):
    """CSV with BOM so Excel reads the accents."""
    return rows.to_csv(index=False).encode("utf-8-sig")


def to_parquet_bytes(rows):
    """Parquet written by DuckDB's native writer (pyarrow is not a panel dependency).

    It runs on a separate in-memory connection, on our own DataFrame and our own
    temporary path, never on visitor text.
    """
    handle, path = tempfile.mkstemp(suffix=".parquet")
    os.close(handle)
    connection = duckdb.connect(":memory:")
    try:
        connection.register("resultado", rows)
        quoted_path = path.replace("'", "''")
        connection.execute(f"COPY resultado TO '{quoted_path}' (FORMAT parquet)")
        with open(path, "rb") as file:
            return file.read()
    finally:
        connection.close()
        os.remove(path)


def export_csv(sql, database_file=queries.DATABASE_FILE):
    return to_csv_bytes(read_view(sql, database_file))
# endregion


# region Page
def build_css(palette):
    return f"""<style>
.sqlx-bar {{ display:flex; flex-wrap:wrap; align-items:center; gap:6px 8px; margin:2px 0 10px; }}
.sqlx-bar .sqlx-bar-label {{ font-size:.72rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase;
  color:{palette['reference']}; margin-right:4px; }}
[class*="st-key-sqlx_chip_"] button {{ min-height:28px !important; padding:2px 11px !important; border-radius:999px !important;
  border:1px solid {palette['card_border']} !important; background:{palette['card']} !important;
  box-shadow:none !important; }}
[class*="st-key-sqlx_chip_"] button p {{ font-size:.8rem !important; color:{palette['strong_text']} !important; }}
[class*="st-key-sqlx_chip_"] button:hover {{ border-color:{palette['accent']} !important; }}
.st-key-sqlx_chips {{ flex-wrap:wrap !important; gap:6px 8px !important; }}
.sqlx-side h4 {{ margin:0 0 4px; font-size:.72rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase;
  color:{palette['reference']}; }}
[class*="st-key-sqlx_view_"] button {{ width:100%; justify-content:flex-start; min-height:26px !important;
  padding:2px 6px !important; border:0 !important; background:transparent !important; box-shadow:none !important;
  border-radius:6px; }}
[class*="st-key-sqlx_view_"] button:hover {{ background:color-mix(in srgb,{palette['accent']} 8%,transparent) !important; }}
[class*="st-key-sqlx_view_"] button p {{ font-family:ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.8rem !important;
  color:{palette['strong_text']} !important; }}
.sqlx-side small {{ display:block; font-size:.72rem; color:{palette['reference']}; line-height:1.3; margin:-8px 0 2px 6px; }}
.sqlx-question {{ color:{palette['text']}; font-size:.86rem; margin:0 0 .3rem; }}
.sqlx-question b {{ color:{palette['strong_text']}; }}
div[data-testid="stTextArea"] textarea {{
  font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:.85rem; line-height:1.5; }}
.st-key-sqlx_editor_box {{ border:1px solid {palette['card_border']}; border-radius:10px; background:{palette['card']};
  padding:8px 10px 6px; }}
.sqlx-note {{ color:{palette['text']}; font-size:.82rem; margin:0; }}
</style>"""


def build_header_html():
    """The compact header of the technical pages (same classes as the dashboard)."""
    description = ("SQL de solo lectura sobre la capa gold del data warehouse, con vistas de "
                   "columnas legibles; nada de identificadores internos.")
    limit = f"{ROW_LIMIT:,}".replace(",", ".")
    return (f'<div class="compact-header"><h1 title="{html.escape(description, quote=True)}">'
            f'Consultas SQL</h1><span class="page-freshness">DuckDB · solo lectura · '
            f'máx. {limit} filas · {TIMEOUT_SECONDS} s</span></div>')


def build_view_html(name, description, count, columns):
    """One quiet line under a table's name: its rows; the rest waits in the tooltip."""
    count_text = f"{count:,}".replace(",", ".")
    return f'<small>{count_text} filas · {len(columns)} columnas</small>' 


def load_catalog():
    import streamlit as st

    @st.cache_data(ttl=600, show_spinner=False)
    def cached(database_file, modified):
        return describe_views(database_file)
    database_file = str(queries.DATABASE_FILE)
    modified = os.path.getmtime(database_file) if os.path.exists(database_file) else 0
    return cached(database_file, modified)


def choose_example(index):
    import streamlit as st
    st.session_state["sqlx_editor"] = EXAMPLES[index][2]
    st.session_state["sqlx_example"] = index
    st.session_state.pop("sqlx_result", None)


def choose_view(name):
    """A table clicked in the side list: its first rows, as a SQL client would."""
    import streamlit as st
    st.session_state["sqlx_editor"] = f"SELECT *\nFROM {name}\nLIMIT 100"
    st.session_state["sqlx_example"] = None
    st.session_state.pop("sqlx_result", None)


def show_result(st, outcome):
    if isinstance(outcome, str):
        st.error(outcome)
        return
    rows, truncated, seconds = outcome.rows, outcome.truncated, outcome.seconds
    count_text = f"{len(rows):,}".replace(",", ".")
    note = f" · se muestran las primeras {ROW_LIMIT:,}".replace(",", ".") if truncated else ""
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.caption(f"{count_text} filas · {seconds * 1000:,.0f} ms{note}".replace(",", "."))
        if not rows.empty:
            st.download_button("CSV", to_csv_bytes(rows), "consulta.csv", "text/csv", key="sqlx_csv",
                               on_click="ignore", icon=":material/download:")
            st.download_button("Parquet", partial(to_parquet_bytes, rows), "consulta.parquet",
                               "application/vnd.apache.parquet", key="sqlx_parquet", on_click="ignore",
                               icon=":material/download:")
    st.dataframe(rows, use_container_width=True, hide_index=True)


def show_exports(st):
    """The main gold tables as CSV, behind one small button (D-168)."""
    with st.popover("Descargar tablas", icon=":material/download:", help="Las tablas gold en CSV, para Excel o Power BI."):
        st.markdown(f'<p class="sqlx-note">Los precios se limitan a las últimas {EXPORT_WEEKS} semanas; el historial '
                    'completo está en la base. El archivo <code>etl/datos.duckdb</code> también se abre con DBeaver, '
                    'Python, R, o con Power BI y Excel mediante el driver ODBC de DuckDB.</p>', unsafe_allow_html=True)
        for file_name, label, sql in EXPORTS:
            st.download_button(label, partial(export_csv, sql), file_name, "text/csv",
                               key=f"sqlx_export_{file_name}", on_click="ignore", icon=":material/download:")


def show_sql_explorer_page(mode):
    """The «Consultas SQL» page as a small SQL client (D-168): the examples as labels
    on top, the tables beside the editor, the result under it."""
    import streamlit as st

    palette = charts.get_palette(mode)
    st.markdown(build_css(palette), unsafe_allow_html=True)
    st.markdown(build_header_html(), unsafe_allow_html=True)
    if "sqlx_editor" not in st.session_state:
        st.session_state["sqlx_editor"] = EXAMPLES[0][2]
        st.session_state["sqlx_example"] = 0
    with st.container(key="sqlx_chips", horizontal=True, vertical_alignment="center"):
        st.markdown('<span class="sqlx-bar-label">Ejemplos</span>', unsafe_allow_html=True)
        for index, (title, question, _) in enumerate(EXAMPLES):
            st.button(title, key=f"sqlx_chip_{index}", help=question, on_click=choose_example, args=(index,))
    try:
        catalog = load_catalog()
    except Exception as error:  # the page still explains itself without the database
        catalog = []
        st.warning(f"No se pudo leer la base de datos: {error}")
    side, main = st.columns([1, 3.6], gap="medium")
    with side:
        st.markdown('<div class="sqlx-side"><h4>Tablas</h4></div>', unsafe_allow_html=True)
        for name, description, count, columns in catalog:
            st.button(name, key=f"sqlx_view_{name}", on_click=choose_view, args=(name,),
                      help=f"{description} Columnas: " + ", ".join(column for column, _ in columns))
            st.markdown('<div class="sqlx-side">' + build_view_html(name, description, count, columns)
                        + '</div>', unsafe_allow_html=True)
        show_exports(st)
    with main:
        example = st.session_state.get("sqlx_example")
        if example is not None and st.session_state["sqlx_editor"] == EXAMPLES[example][2]:
            st.markdown(f'<p class="sqlx-question"><b>{html.escape(EXAMPLES[example][0])}.</b> '
                        f'{html.escape(EXAMPLES[example][1])}</p>', unsafe_allow_html=True)
        with st.container(key="sqlx_editor_box"):
            sql = st.text_area("Consulta SQL", key="sqlx_editor", height=230, label_visibility="collapsed")
            if st.button("Ejecutar", type="primary", key="sqlx_run", icon=":material/play_arrow:"):
                try:
                    with st.spinner("Ejecutando…"):
                        st.session_state["sqlx_result"] = run_user_query(sql)
                except (QueryRejected, QueryTimeout) as error:
                    st.session_state["sqlx_result"] = str(error)
                except duckdb.Error as error:
                    st.session_state["sqlx_result"] = f"DuckDB devolvió un error: {error}"
        if "sqlx_result" in st.session_state:
            show_result(st, st.session_state["sqlx_result"])
# endregion
