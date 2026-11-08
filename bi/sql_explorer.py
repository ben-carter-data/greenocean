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

import functools
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

from bi import charts, i18n, queries, static_files
from bi.i18n import tr


# region Constants
ROW_LIMIT = 5000
TIMEOUT_SECONDS = 10
MEMORY_LIMIT = "1GB"
EXPORT_WEEKS = 52
ALLOWED_FIRST_WORDS = ("SELECT", "WITH", "DESCRIBE", "SHOW", "SUMMARIZE")
# Table functions that read files or URLs. External access is disabled anyway;
# this check only gives the visitor a clear message instead of an engine error.
FILE_FUNCTION_PATTERN = re.compile(
    r"\b(read_\w+|\w+_scan|glob|sniff_csv|parquet_\w+|iceberg_\w+|delta_\w+|query|query_table)\s*\(", re.IGNORECASE
)
URL_PATTERN = re.compile(r"'\s*(https?|s3|s3a|gcs|gs|az|azure|abfss|r2|hf)://", re.IGNORECASE)
FIRST_WORD_PATTERN = re.compile(r"[A-Za-z_]+")

# Each view: (name, what it holds, SQL). Ordered as the visitor should read them.
VIEWS = [
    (
        "precios",
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
LEFT JOIN dim_date AS d ON d.week_start = w.week_start""",
    ),
    (
        "semanas",
        "Calendario: una fila por semana, desde la primera hasta la última con precios.",
        """SELECT CAST(week_start AS DATE) AS semana, iso_year AS anio_iso, iso_week AS semana_iso,
       month AS mes, month_name AS nombre_mes, year AS anio, season AS estacion
FROM dim_date""",
    ),
    (
        "productos",
        "Catálogo de productos: familia, producto, variedad y calidad.",
        """SELECT product_group AS familia, product AS producto, variety AS variedad, quality AS calidad
FROM dim_product""",
    ),
    (
        "ipc_semanal",
        "IPC de alimentos del INE llevado a cada semana. precio × factor_real = precio en "
        "pesos del último mes publicado; provisional = el mes aún no está publicado.",
        """SELECT CAST(week_start AS DATE) AS semana, ipc_year AS anio_ipc, ipc_month AS mes_ipc,
       food_index AS indice_alimentos, reference_year AS anio_referencia,
       reference_month AS mes_referencia, real_factor AS factor_real, provisional
FROM ipc_weekly""",
    ),
    (
        "ipc_mensual",
        "IPC de alimentos del INE, un valor por mes publicado.",
        """SELECT year AS anio, month AS mes, food_index AS indice_alimentos, origin AS origen
FROM ipc_monthly""",
    ),
    (
        "cargas",
        "Ejecuciones del pipeline: cuándo empezó cada carga, su estado y cuántas filas leyó, cargó y rechazó.",
        """SELECT CAST(started_at AS TIMESTAMP) AS inicio, status AS estado, rows_read AS filas_leidas,
       rows_loaded AS filas_cargadas, rows_rejected AS filas_rechazadas, message AS mensaje
FROM etl_run""",
    ),
    (
        "rechazos",
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
LEFT JOIN etl_run AS e ON e.run_id = r.run_id""",
    ),
    (
        "modelos_dbt",
        "Modelos y pruebas de dbt que construyen esta base, con el resultado de su última ejecución.",
        """SELECT n.name AS nombre, n.resource_type AS tipo, NULLIF(n.layer, '') AS capa,
       NULLIF(n.materialized, '') AS materializacion, NULLIF(n.column_name, '') AS columna,
       n.description AS descripcion, r.status AS estado,
       r.execution_time AS segundos, r.failures AS fallas
FROM dbt_node AS n
LEFT JOIN dbt_result AS r ON r.unique_id = n.unique_id""",
    ),
]
VIEW_NAMES = [name for name, _, _ in VIEWS]
# Each example: (title, the question it answers, SQL). All run on the views above.
# Each example: (title, question, SQL template, parameters). Parameters are filled
# from the selectors above the editor (D-180); render_example writes the final SQL.
TEMPLATES = [
    (
        'Tabla completa',
        'Todos los precios semanales con cada dimensión (familia, producto, variedad, calidad, canal, región) y el precio real según el IPC de alimentos; los filtros de arriba acotan la tabla.',
        """-- Tabla completa: un precio semanal por producto, variedad, calidad, canal y región,
-- cruzado con el IPC de alimentos del INE. precio_real = precio × factor_real
-- (pesos del último mes publicado). Filtros elegidos sobre el editor; un filtro sin elegir no filtra.
SELECT p.semana, p.familia, p.producto, p.variedad, p.calidad, p.canal, p.fuente, p.region,
       p.unidad, p.precio,
       round(p.precio * i.factor_real) AS precio_real,
       i.indice_alimentos AS ipc_alimentos,
       i.provisional AS ipc_provisional,
       p.marca
FROM precios AS p
LEFT JOIN ipc_semanal AS i ON i.semana = p.semana{where}
ORDER BY p.semana DESC, p.familia, p.producto, p.region, p.canal""",
        ('familia', 'producto_filtro', 'canal_filtro', 'region', 'anio_filtro'),
    ),
    (
        'Precio vs. época',
        '¿Qué productos están caros o baratos frente a la misma época de los años anteriores, en pesos reales? Conviene comprar lo barato y esperar lo caro.',
        """-- Precio vs. época: ¿está caro o barato frente a la misma época de años anteriores?
-- Cada serie (producto, variedad, calidad, canal, unidad y región) se compara consigo misma:
-- últimas 4 semanas frente a las mismas semanas ISO de los años anteriores, en pesos reales.
WITH ultima AS (
    SELECT semana, anio_iso FROM semanas
    WHERE semana = (SELECT max(semana) FROM precios WHERE fuente = 'consumidor')
),
epoca AS (
    SELECT semana_iso FROM semanas
    WHERE semana BETWEEN (SELECT semana FROM ultima) - INTERVAL 21 DAY AND (SELECT semana FROM ultima)
),
real AS (
    SELECT p.familia, p.producto, p.variedad, p.calidad, p.canal, p.unidad, p.region,
           s.anio_iso AS anio, p.precio * i.factor_real AS precio_real
    FROM precios AS p
    JOIN semanas AS s ON s.semana = p.semana
    JOIN ipc_semanal AS i ON i.semana = p.semana
    WHERE p.fuente = 'consumidor' AND p.marca = 'SIN_MARCA'
      AND s.semana_iso IN (SELECT semana_iso FROM epoca){filtros}
),
series AS (
    SELECT familia, producto, variedad, calidad, canal, unidad, region,
           avg(precio_real) FILTER (WHERE anio = (SELECT anio_iso FROM ultima)) AS actual,
           avg(precio_real) FILTER (WHERE anio < (SELECT anio_iso FROM ultima)) AS habitual,
           count(DISTINCT anio) FILTER (WHERE anio < (SELECT anio_iso FROM ultima)) AS anios
    FROM real
    GROUP BY ALL
    HAVING actual IS NOT NULL AND anios >= 2
)
SELECT familia, producto, variedad, calidad, unidad,
       count(*) AS series_comparadas,
       round(median(actual / habitual - 1) * 100, 1) AS diferencia_real_pct,
       CASE WHEN median(actual / habitual - 1) >= 0.15 THEN 'Caro para la época: conviene esperar'
            WHEN median(actual / habitual - 1) >= 0.05 THEN 'Algo caro para la época'
            WHEN median(actual / habitual - 1) <= -0.15 THEN 'Barato para la época: buen momento para comprar'
            WHEN median(actual / habitual - 1) <= -0.05 THEN 'Algo barato para la época'
            ELSE 'Normal para la época' END AS lectura
FROM series
GROUP BY familia, producto, variedad, calidad, unidad
HAVING count(*) >= 3
ORDER BY diferencia_real_pct DESC""",
        ('familia',),
    ),
    (
        'Canal más barato',
        '¿En qué canal conviene comprar cada producto y cuánto se ahorra frente al canal más caro, en la misma región y semanas?',
        """-- Canal más barato: ¿dónde comprar cada producto y cuánto se ahorra?
-- Se comparan canales con el mismo producto, variedad, calidad, unidad, región y semanas
-- (promedio de las últimas 4 semanas, para no depender de una sola semana).
WITH ventana AS (
    SELECT p.familia, p.producto, p.variedad, p.calidad, p.unidad, p.region, p.canal,
           avg(p.precio) AS precio
    FROM precios AS p
    WHERE p.fuente = 'consumidor' AND p.marca = 'SIN_MARCA'
      AND p.semana > (SELECT max(semana) FROM precios) - INTERVAL 28 DAY{filtros}
    GROUP BY ALL
),
por_region AS (
    SELECT familia, producto, variedad, calidad, unidad, region,
           arg_min(canal, precio) AS canal_mas_barato,
           arg_max(canal, precio) AS canal_mas_caro,
           min(precio) AS precio_minimo, max(precio) AS precio_maximo
    FROM ventana
    GROUP BY ALL
    HAVING count(*) >= 2
)
SELECT familia, producto, variedad, calidad, unidad,
       mode(canal_mas_barato) AS canal_mas_barato,
       mode(canal_mas_caro) AS canal_mas_caro,
       count(*) AS regiones,
       round(median(precio_minimo)) AS precio_mas_barato,
       round(median(precio_maximo)) AS precio_mas_caro,
       round(median(1 - precio_minimo / precio_maximo) * 100, 1) AS ahorro_pct
FROM por_region
GROUP BY familia, producto, variedad, calidad, unidad
HAVING count(*) >= {min_regiones}  -- 3 regiones en todo el país; 1 si se eligió una región
ORDER BY ahorro_pct DESC""",
        ('familia', 'region'),
    ),
    (
        'Inflación vs IPC',
        '¿Qué productos subieron más que el IPC de alimentos en el período elegido, medido serie a serie en las mismas fechas?',
        """-- Inflación vs IPC: ¿qué productos subieron más que la inflación de alimentos?
-- Período elegido arriba ({periodo}). Cada serie se mide entre su primer y su último precio
-- del período, y el IPC entre esas mismas dos semanas: la comparación es exacta, serie a serie.
WITH periodo AS (
    SELECT {desde} AS desde, {hasta} AS hasta
),
series AS (
    SELECT p.familia, p.producto, p.variedad, p.calidad, p.canal, p.unidad, p.region,
           arg_min(p.precio, p.semana) AS precio_inicial, arg_max(p.precio, p.semana) AS precio_final,
           min(p.semana) AS semana_inicial, max(p.semana) AS semana_final
    FROM precios AS p, periodo
    WHERE p.fuente = 'consumidor' AND p.marca = 'SIN_MARCA'
      AND p.semana BETWEEN periodo.desde AND periodo.hasta{filtros}
    GROUP BY ALL
    HAVING count(*) >= 10
       AND min(p.semana) <= any_value(periodo.desde) + INTERVAL 56 DAY
       AND max(p.semana) >= least(any_value(periodo.hasta), (SELECT max(semana) FROM precios)) - INTERVAL 28 DAY
),
comparacion AS (
    SELECT s.*,
           s.precio_final / s.precio_inicial - 1 AS alza,
           f.indice_alimentos / i.indice_alimentos - 1 AS alza_ipc
    FROM series AS s
    JOIN ipc_semanal AS i ON i.semana = s.semana_inicial
    JOIN ipc_semanal AS f ON f.semana = s.semana_final
)
SELECT familia, producto, variedad, calidad, unidad,
       count(*) AS series_comparadas,
       round(median(alza) * 100, 1) AS alza_producto_pct,
       round(median(alza_ipc) * 100, 1) AS alza_ipc_pct,
       round((median(alza) - median(alza_ipc)) * 100, 1) AS sobre_inflacion_pp,
       CASE WHEN median(alza) - median(alza_ipc) >= 0.10 THEN 'Subió mucho más que la inflación'
            WHEN median(alza) - median(alza_ipc) >= 0.02 THEN 'Subió más que la inflación'
            WHEN median(alza) - median(alza_ipc) > -0.02 THEN 'Al ritmo de la inflación'
            ELSE 'Subió menos: se abarató en pesos reales' END AS lectura
FROM comparacion
GROUP BY familia, producto, variedad, calidad, unidad
HAVING count(*) >= 3
ORDER BY sobre_inflacion_pp DESC""",
        ('periodo', 'familia'),
    ),
    (
        'Brecha mayorista',
        '¿Cuánto más paga el consumidor que el mayorista por el mismo producto, y cómo cambió en un año? Solo Frutas y Hortalizas.',
        """-- Brecha mayorista-consumidor: ¿cuánto más paga el consumidor que el mayorista?
-- Solo Frutas y Hortalizas tienen precio mayorista. Se emparejan el mismo producto, variedad,
-- calidad, unidad, región y semana en los dos canales. Es una brecha, no un margen:
-- no incluye transporte, mermas ni costos del comercio.
WITH ultima AS (SELECT max(semana) AS semana FROM precios WHERE fuente = 'mayorista'),
pares AS (
    SELECT c.familia, c.producto, c.variedad, c.calidad, c.unidad, c.region, c.semana,
           c.precio AS consumidor, m.precio AS mayorista
    FROM precios AS c
    JOIN precios AS m
      ON m.semana = c.semana AND m.region = c.region AND m.producto = c.producto
     AND m.variedad = c.variedad AND m.calidad = c.calidad AND m.unidad = c.unidad
    WHERE c.fuente = 'consumidor' AND m.fuente = 'mayorista'
      AND c.marca = 'SIN_MARCA' AND m.marca = 'SIN_MARCA'
)
SELECT familia, producto, variedad, calidad, unidad,
       count(DISTINCT region) FILTER (WHERE semana > (SELECT semana FROM ultima) - INTERVAL 28 DAY) AS regiones,
       round(median(consumidor / mayorista - 1) FILTER (WHERE semana > (SELECT semana FROM ultima) - INTERVAL 28 DAY) * 100, 1) AS brecha_actual_pct,
       round(median(consumidor / mayorista - 1) FILTER (WHERE semana BETWEEN (SELECT semana FROM ultima) - INTERVAL 392 DAY
                                                                AND (SELECT semana FROM ultima) - INTERVAL 364 DAY) * 100, 1) AS brecha_hace_un_anio_pct,
       round((median(consumidor / mayorista - 1) FILTER (WHERE semana > (SELECT semana FROM ultima) - INTERVAL 28 DAY)
            - median(consumidor / mayorista - 1) FILTER (WHERE semana BETWEEN (SELECT semana FROM ultima) - INTERVAL 392 DAY
                                                                AND (SELECT semana FROM ultima) - INTERVAL 364 DAY)) * 100, 1) AS cambio_pp,
       CASE WHEN brecha_actual_pct - brecha_hace_un_anio_pct >= 10 THEN 'La brecha creció'
            WHEN brecha_actual_pct - brecha_hace_un_anio_pct <= -10 THEN 'La brecha se achicó'
            ELSE 'Brecha estable' END AS lectura
FROM pares
GROUP BY familia, producto, variedad, calidad, unidad
HAVING brecha_actual_pct IS NOT NULL AND brecha_hace_un_anio_pct IS NOT NULL AND regiones >= 2
ORDER BY cambio_pp DESC""",
        (),
    ),
    (
        'Calendario de compra',
        '¿En qué mes cada producto suele estar más barato y más caro, en pesos reales, y cuánto se ahorra comprando en el mes barato?',
        """-- Calendario de compra: ¿en qué mes cada producto suele estar más barato y más caro?
-- Índice estacional en pesos reales: en cada serie y año, el precio de cada mes se divide por la
-- mediana de ese año; luego se toma la mediana por mes. 100 = precio típico del año.
WITH real AS (
    SELECT p.familia, p.producto, p.variedad, p.calidad, p.canal, p.unidad, p.region,
           p.anio, p.mes, p.precio * i.factor_real AS precio_real
    FROM precios AS p
    JOIN ipc_semanal AS i ON i.semana = p.semana
    WHERE p.fuente = 'consumidor' AND p.marca = 'SIN_MARCA'{filtros}
),
indice AS (
    SELECT familia, producto, variedad, calidad, unidad, mes,
           median(precio_real) / median(median(precio_real)) OVER (
               PARTITION BY familia, producto, variedad, calidad, canal, unidad, region, anio) AS indice
    FROM real
    GROUP BY familia, producto, variedad, calidad, canal, unidad, region, anio, mes
),
por_mes AS (
    SELECT familia, producto, variedad, calidad, unidad, mes, median(indice) * 100 AS indice, count(*) AS observaciones
    FROM indice
    GROUP BY ALL
)
SELECT familia, producto, variedad, calidad, unidad,
       (['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'])[arg_min(mes, indice)] AS mes_mas_barato,
       round(min(indice)) AS indice_mes_barato,
       (['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'])[arg_max(mes, indice)] AS mes_mas_caro,
       round(max(indice)) AS indice_mes_caro,
       round((1 - min(indice) / max(indice)) * 100, 1) AS ahorro_comprando_en_el_mes_barato_pct
FROM por_mes
GROUP BY familia, producto, variedad, calidad, unidad
HAVING count(*) = 12 AND min(observaciones) >= 6
ORDER BY ahorro_comprando_en_el_mes_barato_pct DESC""",
        ('familia',),
    ),
]
# The script name of each query in the editor's tab, as a SQL Server file (D-182).
SCRIPT_NAMES = {
    "Tabla completa": "tabla_completa.sql",
    "Precio vs. época": "precio_vs_epoca.sql",
    "Canal más barato": "canal_mas_barato.sql",
    "Inflación vs IPC": "inflacion_vs_ipc.sql",
    "Brecha mayorista": "brecha_mayorista.sql",
    "Calendario de compra": "calendario_compra.sql",
}
ALL_VALUES = "Todas"
SINCE_2022 = "Desde 2022"
PARAMETER_DEFAULTS = {
    "periodo": SINCE_2022,
    "familia": ALL_VALUES,
    "producto_filtro": ALL_VALUES,
    "canal_filtro": ALL_VALUES,
    "region": ALL_VALUES,
    "anio_filtro": ALL_VALUES,
}
# Filter parameter -> the column it filters in the full table (D-185).
FILTER_COLUMNS = {
    "familia": "p.familia",
    "producto_filtro": "p.producto",
    "canal_filtro": "p.canal",
    "region": "p.region",
    "anio_filtro": "year(p.semana)",
}
# A run of whole comment lines reads as one text; a comment after code, as another.
COMMENT_PATTERN = re.compile(r"(?:^--[^\n]*(?:\n|$))+|--[^\n]*", re.MULTILINE)
# Gold tables offered as CSV in «Llevar los datos a otra herramienta».
EXPORTS = [
    (
        "precios_52_semanas.csv",
        f"Precios de las últimas {EXPORT_WEEKS} semanas",
        f"SELECT * FROM precios WHERE semana > (SELECT max(semana) FROM precios) "
        f"- INTERVAL {EXPORT_WEEKS * 7} DAY ORDER BY semana, familia, producto, region, canal",
    ),
    ("productos.csv", "Catálogo de productos", "SELECT * FROM productos ORDER BY ALL"),
    ("regiones.csv", "Regiones", "SELECT region FROM dim_region ORDER BY region"),
    (
        "canales.csv",
        "Canales",
        "SELECT channel AS canal, CASE source WHEN 'wholesale' THEN 'mayorista' ELSE 'consumidor' END "
        "AS fuente FROM dim_channel ORDER BY fuente, canal",
    ),
    ("semanas.csv", "Calendario de semanas", "SELECT * FROM semanas ORDER BY semana"),
    ("ipc_semanal.csv", "IPC de alimentos por semana", "SELECT * FROM ipc_semanal ORDER BY semana"),
]
# The messages for the reader, whole, so that the English layer finds them (D-443).
ONLY_READING = (
    "Solo se permiten consultas de lectura: SELECT o WITH (también DESCRIBE, SHOW y "
    "SUMMARIZE). INSERT, UPDATE, DELETE, DROP, CREATE, ATTACH, COPY, PRAGMA, SET y "
    "otras instrucciones no se ejecutan."
)
ONLY_THIS_DATABASE = (
    "Las consultas trabajan solo sobre las tablas de esta base: leer "
    "archivos o direcciones web (read_csv, read_parquet, http…) está "
    "desactivado."
)
TOO_LONG = "La consulta superó el límite de {} segundos y se detuvo. Prueba filtrando por semana, producto o región."
DATABASE_LABEL = "datos.duckdb"
# Words the editor paints: keywords first, then the usual functions. Identifiers
# (columns, views) keep the ink color, as in SQL Server Management Studio.
KEYWORDS = (
    "SELECT FROM WHERE AND OR NOT IN IS NULL AS ON JOIN LEFT RIGHT INNER FULL OUTER CROSS "
    "GROUP BY ORDER HAVING LIMIT OFFSET WITH UNION ALL DISTINCT CASE WHEN THEN ELSE END "
    "BETWEEN LIKE ILIKE SIMILAR EXISTS OVER PARTITION ROWS RANGE PRECEDING FOLLOWING UNBOUNDED "
    "CURRENT ROW ASC DESC NULLS FIRST LAST FILTER INTERVAL DAY DAYS WEEK MONTH YEAR DATE "
    "TIMESTAMP INTEGER BIGINT DOUBLE DECIMAL VARCHAR BOOLEAN TRUE FALSE DESCRIBE SHOW SUMMARIZE "
    "USING QUALIFY WINDOW CAST TRY_CAST EXCLUDE PIVOT UNPIVOT SAMPLE VALUES LATERAL ANY SOME "
    "EXCEPT INTERSECT RECURSIVE TABLES COLUMNS"
)
FUNCTIONS = (
    "COUNT SUM AVG MIN MAX MEDIAN MODE ROUND FLOOR CEIL CEILING ABS COALESCE NULLIF IFNULL IF "
    "LAG LEAD ROW_NUMBER RANK DENSE_RANK NTILE ANY_VALUE ARG_MAX ARG_MIN LIST STRING_AGG "
    "ARRAY_AGG DATE_TRUNC DATE_PART DATEDIFF DATE_DIFF DATEADD EXTRACT STRFTIME STRPTIME LOWER "
    "UPPER TRIM LENGTH SUBSTRING SUBSTR CONCAT REPLACE REGEXP_MATCHES REGEXP_REPLACE QUANTILE "
    "QUANTILE_CONT STDDEV STDDEV_SAMP VARIANCE GENERATE_SERIES UNNEST GREATEST LEAST TYPEOF "
    "EPOCH YEAR MONTH DAY WEEK TO_DAYS NOW TODAY CURRENT_DATE MAKE_DATE LAST_DAY"
)
DESCRIPTION = (
    "SQL de solo lectura sobre la capa gold del data warehouse, con vistas de "
    "columnas legibles; nada de identificadores internos."
)
PARAMETER_KEYS = {
    "periodo": "sqlx_param_periodo",
    "familia": "sqlx_param_familia",
    "producto_filtro": "sqlx_param_producto_filtro",
    "canal_filtro": "sqlx_param_canal_filtro",
    "region": "sqlx_param_region",
    "anio_filtro": "sqlx_param_anio_filtro",
}
PARAMETER_LABELS = {
    "periodo": "Período",
    "familia": "Familia",
    "producto_filtro": "Producto",
    "canal_filtro": "Canal",
    "region": "Región",
    "anio_filtro": "Año",
}
# D-516: the grid takes all the height the window leaves under the editor, so the rows read without scrolling more
# than needed; below the floor the page scrolls instead. A few rows keep their own height: an empty grid says nothing.
AROUND_GRID, GRID_FLOOR, GRID_ROW = 348, 190, 28
# endregion

# region Variables
# The editor's paint layer (D-173): a transparent textarea over a <pre> that a script
# repaints on every keystroke with the SQL colors, plus a gutter of line numbers.
# One script per block, no HTML tags inside it and no node moves (CLAUDE.md).
EDITOR_HTML = (
    static_files.read("sql_editor.html").replace("__KEYWORDS__", KEYWORDS).replace("__FUNCTIONS__", FUNCTIONS)
)  # D-543
# endregion


# region The examples and their parameters
def sql_text(value):
    """A SQL string literal; the values come from our own lists, quoted anyway."""
    return "'" + str(value).replace("'", "''") + "'"


def build_conditions(values, names):
    """One SQL condition per chosen filter among the template's own parameters; none for «Todas»."""
    conditions = []
    for name in names:
        column = FILTER_COLUMNS.get(name)
        value = values.get(name, ALL_VALUES)
        if column is None or value == ALL_VALUES:
            continue
        literal = str(int(value)) if name == "anio_filtro" else sql_text(value)
        conditions.append(f"{column} = {literal}")
    return conditions


def period_bounds(period, read=tr):
    """(text, from, to) of the inflation period: a calendar year, or since January 2022."""
    if str(period) == SINCE_2022:
        return read("desde enero de 2022"), "DATE '2022-01-01'", "DATE '2099-12-31'"
    year = int(period)
    return read("año {}").format(year), f"DATE '{year}-01-01'", f"DATE '{year}-12-31'"


def _translated_comment(read, match):
    text = match.group(0)
    return read(text.rstrip("\n")) + text[len(text.rstrip("\n")) :]


def translate_comments(template, read=tr):
    """D-516: the comments of a template in the language of the visit. The SQL, its names and its data stay."""

    return COMMENT_PATTERN.sub(functools.partial(_translated_comment, read), template)


def render_example(index, values=None, read=tr):
    """The example's SQL with its parameters filled in (D-180, D-185), its comments in the language of the visit."""
    values = {**PARAMETER_DEFAULTS, **(values or {})}
    _, _, template, names = TEMPLATES[index]
    template = translate_comments(template, read)
    conditions = build_conditions(values, names)
    text, start, end = period_bounds(values["periodo"], read)
    return (
        template.replace("{where}", ("\nWHERE " + "\n  AND ".join(conditions)) if conditions else "")
        .replace("{filtros}", "".join(f"\n      AND {condition}" for condition in conditions))
        .replace("{periodo}", text)
        .replace("{desde}", start)
        .replace("{hasta}", end)
        .replace("{min_regiones}", "1" if values.get("region", ALL_VALUES) != ALL_VALUES and "region" in names else "3")
    )


@functools.cache
def examples():
    """(title, question, SQL with the default parameters), as the tests and the chips read them. In the text they are
    written in: the list is built once for every visit, so the page asks render_example for the language of each."""
    return [
        (title, question, render_example(index, read=str)) for index, (title, question, _, _) in enumerate(TEMPLATES)
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
            result.append(sql[position : end + 1])
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
        raise QueryRejected(tr("Escribe una consulta SELECT antes de ejecutar."))
    first_word = FIRST_WORD_PATTERN.match(text.lstrip("( \n\t"))
    if not first_word or first_word.group(0).upper() not in ALLOWED_FIRST_WORDS:
        raise QueryRejected(tr(ONLY_READING))
    try:
        statements = duckdb.extract_statements(text)
    except duckdb.Error as error:
        raise QueryRejected(tr("La consulta no se pudo interpretar: {}").format(error)) from error
    if len(statements) != 1:
        raise QueryRejected(
            tr("Ejecuta una sola consulta a la vez (sin varias instrucciones separadas por punto y coma).")
        )
    if statements[0].type != duckdb.StatementType.SELECT:
        raise QueryRejected(tr("Solo se permiten consultas de lectura (SELECT o WITH)."))
    if FILE_FUNCTION_PATTERN.search(text) or URL_PATTERN.search(text):
        raise QueryRejected(tr(ONLY_THIS_DATABASE))
    return text


# endregion


# region Connection and execution
def open_explorer_connection(database_file=queries.DATABASE_FILE):
    """A new read-only connection, without external access, with the analysis views.

    External access can only be disabled when the connection opens, so it goes in
    the config; the configuration is locked once the views exist, so no query
    can change it back.
    """
    connection = duckdb.connect(str(database_file), read_only=True, config={"enable_external_access": False})
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


def run_user_query(sql, database_file=queries.DATABASE_FILE, timeout=TIMEOUT_SECONDS, row_limit=ROW_LIMIT):
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
        raise QueryTimeout(tr(TOO_LONG).format(f"{timeout:g}")) from error
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
    """The studio: one raised panel with a toolbar, the object explorer, the editor
    and the results, all lit from above (D-173)."""
    dark = palette["base"] == charts.BASE_DARK
    accent, card, field, border = palette["accent"], palette["card"], palette["field"], palette["card_border"]
    ink, text, muted = palette["strong_text"], palette["text"], palette["reference"]
    if dark:
        editor = f"color-mix(in srgb, {card} 72%, #000)"
        panel_shadow = (
            "0 1px 0 rgba(255,255,255,.07) inset, 0 34px 70px -34px rgba(0,0,0,.9), 0 0 0 1px rgba(255,255,255,.04)"
        )
        raised = "0 1px 0 rgba(255,255,255,.08) inset, 0 2px 4px rgba(0,0,0,.45)"
        inset = "inset 0 2px 8px rgba(0,0,0,.55), inset 0 0 0 1px rgba(255,255,255,.04)"
        toolbar = f"linear-gradient(180deg, color-mix(in srgb, {card} 84%, #fff) 0%, {card} 100%)"
        explorer = f"color-mix(in srgb, {card} 86%, #000)"
        tokens = {
            "k": "#7ab8ff",
            "f": "#e0a8ff",
            "s": "#ffb07a",
            "n": "#86e2c9",
            "c": "#80c880",
            "o": "#9aa4b2",
            "q": "#c7b8ff",
        }
        gutter = "rgba(255,255,255,.28)"
        selection = f"color-mix(in srgb, {accent} 28%, transparent)"
    else:
        editor = "#ffffff"
        panel_shadow = (
            "0 1px 0 #fff inset, 0 34px 70px -40px rgba(15,27,45,.5), "
            "0 10px 24px -14px rgba(15,27,45,.22), 0 0 0 1px rgba(15,27,45,.04)"
        )
        raised = "0 1px 0 rgba(255,255,255,.9) inset, 0 1px 3px rgba(15,27,45,.12)"
        inset = "inset 0 2px 7px rgba(15,27,45,.09), inset 0 0 0 1px rgba(15,27,45,.04)"
        toolbar = f"linear-gradient(180deg, #ffffff 0%, {field} 100%)"
        explorer = f"color-mix(in srgb, {field} 70%, #fff)"
        tokens = {
            "k": "#1b4fd8",
            "f": "#a0269b",
            "s": "#c2410c",
            "n": "#0f766e",
            "c": "#2e7d32",
            "o": "#64748b",
            "q": "#6d28d9",
        }
        gutter = "rgba(15,27,45,.32)"
        selection = f"color-mix(in srgb, {accent} 22%, transparent)"
    mono = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Cascadia Code', monospace"
    return static_files.style(
        "sql_explorer.css",
        {
            'var(--go-card)': card,
            'var(--go-border)': border,
            'var(--go-panel-shadow)': panel_shadow,
            'var(--go-toolbar)': toolbar,
            'var(--go-06-if-dark-else-9)': '.06' if dark else '.9',
            'var(--go-field)': field,
            'var(--go-raised)': raised,
            'var(--go-ink)': ink,
            'var(--go-mono)': mono,
            'var(--go-muted)': muted,
            'var(--go-charts-status-colors-good)': charts.STATUS_COLORS['good'],
            'var(--go-charts-legible-muted-field-if-field-startswith-e)': charts.legible(muted, field)
            if field.startswith('#')
            else muted,
            'var(--go-charts-chart-font)': charts.CHART_FONT,
            'var(--go-accent)': accent,
            'var(--go-explorer)': explorer,
            'var(--go-editor)': editor,
            'var(--go-text)': text,
            'var(--go-inset)': inset,
            'var(--go-selection)': selection,
            'var(--go-gutter)': gutter,
            'var(--go-tokens-k)': tokens['k'],
            'var(--go-tokens-f)': tokens['f'],
            'var(--go-tokens-s)': tokens['s'],
            'var(--go-tokens-n)': tokens['n'],
            'var(--go-tokens-c)': tokens['c'],
            'var(--go-tokens-o)': tokens['o'],
            'var(--go-tokens-q)': tokens['q'],
            'var(--go-charts-status-colors-good-if-dark-else-charts-st)': charts.STATUS_COLORS['good']
            if dark
            else charts.STATUS_TEXT_ON_LIGHT['good'],
            'var(--go-charts-status-colors-critical-if-dark-else-chart)': charts.STATUS_COLORS['critical']
            if dark
            else charts.STATUS_TEXT_ON_LIGHT['critical'],
            'var(--go-18-if-dark-else-12)': '18%' if dark else '12%',
            'var(--go-10-if-dark-else-6)': '10%' if dark else '6%',
            'var(--go-05-if-dark-else-7)': '.05' if dark else '.7',
            'var(--go-charts-status-colors-critical)': charts.STATUS_COLORS['critical'],
        },
    )


def build_limits_html():
    """D-514: the studio's two limits, in small letters beside «Ejecutar»; the engine and «solo lectura» are already in
    the connection pill. Each text whole, so the English layer finds it."""
    limit = f"{ROW_LIMIT:,}".replace(",", ".")
    return (
        f'<span class="sqlx-limits" title="Muestra como máximo {limit} filas por consulta; una consulta se detiene a los '
        f'{TIMEOUT_SECONDS} segundos.">máx. {limit} filas · {TIMEOUT_SECONDS} s</span>'
    )


def build_database_html():
    """The connection pill of the toolbar: the database, its engine, read-only."""
    return (
        f'<span class="sqlx-db"><i></i>{DATABASE_LABEL} <small>DuckDB {duckdb.__version__} · '
        'solo lectura</small></span>'
    )


def build_tree_html():
    """The top of the object explorer: its title and the database (D-182)."""
    return (
        '<div class="sqlx-tree-title">Explorador de objetos</div>'
        f'<div class="sqlx-node"><span class="tw">▾</span><span class="sqlx-ico db"></span>{DATABASE_LABEL}</div>'
    )


def build_folder_html(name, count):
    """A folder of the tree, as SQL Server's «Tables» and «Views»."""
    return (
        f'<div class="sqlx-node branch"><span class="tw">▾</span><span class="sqlx-ico folder"></span>{html.escape(name)} '
        f'<small>({count})</small></div>'
    )


def build_column_names(columns):
    """The columns of a table on hover, as code: their names read the same in every language (D-516)."""
    return ", ".join(f"`{column}`" for column, _ in columns)


def build_view_html(name, description, count, columns):
    """One quiet line under a view's name: its rows and columns."""
    count_text = f"{count:,}".replace(",", ".")
    return f'<div class="sqlx-rows">{count_text} filas · {len(columns)} col.</div>'


def build_tab_html(example):
    """The editor's tab strip: the script's file name and an «i» that tells, on hover,
    which question it answers (D-182)."""
    if example is None:
        return (
            '<div class="sqlx-tabstrip"><span class="sqlx-tab"><span class="dot"></span>'
            + tr("consulta.sql")
            + "</span></div>"
        )
    title, question, _ = examples()[example]
    script = tr(SCRIPT_NAMES.get(title, "consulta.sql"))
    return (
        f'<div class="sqlx-tabstrip"><span class="sqlx-tab"><span class="dot"></span>{html.escape(script)}</span>'
        f'<span class="sqlx-info" tabindex="0" title="{html.escape(question, quote=True)}">'
        f'i<span class="sqlx-info-tip" role="tooltip"><b>{html.escape(title)}</b>{html.escape(question)}</span></span></div>'
    )


def editor_height(sql):
    """Enough lines to show the query without an inner scroll, within one screen."""
    lines = (sql or "").count("\n") + 1
    # D-233: six to eight lines; a longer query scrolls inside the editor. D-511 and D-514: the room the filters' line
    # and the chips' row gave back goes to the editor, so up to thirteen lines show without a scroll.
    return max(252, min(292, 21 * lines + 24))


def format_elapsed(seconds):
    """hh:mm:ss.mmm, as a SQL client's status bar."""
    whole = int(seconds)
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}.{int(seconds * 1000) % 1000:03d}"


def format_count(value):
    """D-284: a figure in the language of the visit."""
    return f"{value:,.0f}" if i18n.is_english() else f"{value:,.0f}".replace(",", ".")


def build_status_html(outcome):
    """The status bar: the verdict, the engine, the database, the time and the rows."""
    if outcome is None:
        kind, verdict, elapsed, rows = "idle", "Lista para ejecutar (Ctrl + Enter o «Ejecutar»).", "00:00:00.000", "—"
    elif isinstance(outcome, str):
        kind, verdict, elapsed, rows = "err", tr("La consulta terminó con errores."), "00:00:00.000", tr("0 filas")
    else:
        kind, verdict = "ok", "Consulta ejecutada correctamente."
        elapsed = format_elapsed(outcome.seconds)
        rows = f"{len(outcome.rows):,} filas".replace(",", ".")
    mark = "✓" if kind == "ok" else ("!" if kind == "err" else "·")
    return (
        f'<div class="sqlx-status {kind}"><span><i class="mark">{mark}</i>{verdict}</span>'
        f'<span>DuckDB {duckdb.__version__}</span><span>solo lectura</span><span>{DATABASE_LABEL}</span>'
        f'<span class="num">{elapsed}</span><span class="num">{rows}</span></div>'
    )


def build_messages_html(outcome):
    """The «Mensajes» tab, as a SQL client writes it."""
    if outcome is None:
        return f'<pre class="sqlx-msg">{tr("Sin mensajes todavía. Ejecuta una consulta.")}</pre>'
    if isinstance(outcome, str):
        return f'<pre class="sqlx-msg"><span class="err">{html.escape(outcome)}</span>\n\n{tr("La consulta no se ejecutó.")}</pre>'
    note = (
        "\n" + tr("Se muestran las primeras {} filas; el resultado tenía más.").format(format_count(ROW_LIMIT))
        if outcome.truncated
        else ""
    )
    return (
        f'<pre class="sqlx-msg">{tr("({} filas afectadas)").format(format_count(len(outcome.rows)))}{note}\n\n'
        f'<span class="ok">✓ {tr("Consulta ejecutada correctamente.")}</span>  '
        f'{tr("Tiempo: {} ms").format(format_count(outcome.seconds * 1000))}</pre>'
    )


def describe_tables(database_file=queries.DATABASE_FILE):
    """[(table, row count, [(column, type)])] of the real tables of the database (D-182)."""
    connection = open_explorer_connection(database_file)
    try:
        names = [
            row[0]
            for row in connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' "
                "AND table_type = 'BASE TABLE' ORDER BY table_name"
            ).fetchall()
        ]
        return [
            (
                name,
                connection.execute(f'SELECT count(*) FROM main."{name}"').fetchone()[0],
                [(row[0], row[1]) for row in connection.execute(f'DESCRIBE main."{name}"').fetchall()],
            )
            for name in names
        ]
    finally:
        connection.close()


def _read_tables(database_file, modified):
    """The tables of the database; `modified` changes the cache key when the file changes."""
    return describe_tables(database_file)


def load_tables():
    import streamlit as st

    database_file = str(queries.DATABASE_FILE)
    modified = os.path.getmtime(database_file) if os.path.exists(database_file) else 0
    return st.cache_data(ttl=600, show_spinner=False)(_read_tables)(database_file, modified)


def _read_catalog(database_file, modified):
    """The views of «Consultas SQL»; `modified` changes the cache key when the file changes."""
    return describe_views(database_file)


def load_catalog():
    import streamlit as st

    database_file = str(queries.DATABASE_FILE)
    modified = os.path.getmtime(database_file) if os.path.exists(database_file) else 0
    return st.cache_data(ttl=600, show_spinner=False)(_read_catalog)(database_file, modified)


def parameter_values():
    import streamlit as st

    return {name: st.session_state.get(key, PARAMETER_DEFAULTS[name]) for name, key in PARAMETER_KEYS.items()}


def outcome_of(sql):
    """Run a query and keep what the page shows: the rows, or the message for the visitor."""
    try:
        return run_user_query(sql)
    except (QueryRejected, QueryTimeout) as error:
        return str(error)
    except duckdb.Error as error:
        return tr("DuckDB devolvió un error: {}").format(error)


def choose_example(index):
    """One click (D-180): the example's SQL, with the chosen parameters, is written in
    the editor and run, so the answer and the code that gives it appear together."""
    import streamlit as st

    sql = render_example(index, parameter_values())
    st.session_state["sqlx_editor"] = sql
    st.session_state["sqlx_example"] = index
    st.session_state["sqlx_rendered"] = sql
    st.session_state["sqlx_result"] = outcome_of(sql)


def apply_parameters():
    """A selector changed: values that no longer fit are reset, then the current
    example is written and run again."""
    import streamlit as st

    index = st.session_state.get("sqlx_example")
    try:
        choices = parameter_choices(load_parameter_options(), st.session_state)
    except Exception:
        choices = {}
    for name, options in choices.items():
        key = PARAMETER_KEYS[name]
        if key in st.session_state and options and st.session_state[key] not in options:
            st.session_state[key] = options[0]
    if index is not None:
        choose_example(index)


def _read_parameter_options(database_file, modified):
    """Every list the selectors offer; `modified` changes the cache key when the file changes."""
    years = read_view("SELECT DISTINCT anio FROM semanas WHERE anio IS NOT NULL ORDER BY anio DESC", database_file)
    combos = read_view(
        "SELECT familia, producto, canal, count(*) AS n FROM precios WHERE marca = 'SIN_MARCA' "
        "GROUP BY ALL ORDER BY familia, producto, n DESC",
        database_file,
    )
    regions = read_view("SELECT DISTINCT region FROM precios ORDER BY region", database_file)
    channels, by_family = {}, {}
    for row in combos.itertuples():
        channels.setdefault(row.producto, [])
        if row.canal not in channels[row.producto]:
            channels[row.producto].append(row.canal)
        by_family.setdefault(row.familia, set()).add(row.producto)
    return dict(
        years=[int(year) for year in years["anio"]],
        channels=channels,
        families={family: sorted(products) for family, products in by_family.items()},
        regions=list(regions["region"]),
    )


def load_parameter_options():
    """Every list the selectors offer, read from the database once (cached per database)."""
    import streamlit as st

    database_file = str(queries.DATABASE_FILE)
    modified = os.path.getmtime(database_file) if os.path.exists(database_file) else 0
    return st.cache_data(ttl=600, show_spinner=False)(_read_parameter_options)(database_file, modified)


def parameter_choices(options, state):
    """The choices of each selector, narrowed by the ones above it (family → product → channel)."""
    family = state.get(PARAMETER_KEYS["familia"], ALL_VALUES)
    products = (
        options["families"].get(family, [])
        if family != ALL_VALUES
        else sorted(product for names in options["families"].values() for product in names)
    )
    product = state.get(PARAMETER_KEYS["producto_filtro"], ALL_VALUES)
    if product != ALL_VALUES and product in options["channels"]:
        channels = options["channels"][product]
    else:
        channels = sorted(
            {channel for product_channels in options["channels"].values() for channel in product_channels}
        )
    return {
        "periodo": [SINCE_2022] + options["years"],
        "familia": [ALL_VALUES] + sorted(options["families"]),
        "producto_filtro": [ALL_VALUES] + products,
        "canal_filtro": [ALL_VALUES] + channels,
        "region": [ALL_VALUES] + options["regions"],
        "anio_filtro": [ALL_VALUES] + options["years"],
    }


def show_parameters(st, index):
    """The template parameters of the chosen example, in one quiet row above the editor
    (as SQL Server's «Specify values for template parameters»)."""
    names = TEMPLATES[index][3]
    if not names:
        return
    try:
        options = parameter_choices(load_parameter_options(), st.session_state)
    except Exception:  # the defaults still work without the lists
        return
    # D-511: thin pills on the line of the script's tab; a pill says its filter («Producto») until a value is chosen
    for name in names:
        key = PARAMETER_KEYS[name]
        choices = options[name]
        if st.session_state.get(key) not in choices:
            default = PARAMETER_DEFAULTS[name]
            st.session_state[key] = default if default in choices else choices[0]
        with st.container(key=f"sqlx_pill_{name}"):
            st.selectbox(
                PARAMETER_LABELS[name],
                choices,
                key=key,
                on_change=apply_parameters,
                label_visibility="collapsed",
                help=tr("{}: elige uno o déjalo en todos").format(tr(PARAMETER_LABELS[name])),
                format_func=lambda value, name=name: tr(PARAMETER_LABELS[name]) if value == ALL_VALUES else str(value),
            )


def choose_table(name):
    """A real table clicked in the explorer: its first rows, as SQL Server's «Select Top 100 Rows»."""
    import streamlit as st

    sql = f"SELECT *\nFROM main.{name}\nLIMIT 100"
    st.session_state["sqlx_editor"] = sql
    st.session_state["sqlx_example"] = None
    st.session_state["sqlx_result"] = outcome_of(sql)


def choose_view(name):
    """A view clicked in the explorer: its first rows, as a SQL client would."""
    import streamlit as st

    st.session_state["sqlx_editor"] = f"SELECT *\nFROM {name}\nLIMIT 100"
    st.session_state["sqlx_example"] = None
    st.session_state.pop("sqlx_result", None)


def execute_editor(st, sql):
    """Run the editor's text and keep the outcome (rows or a message) in the session."""
    try:
        with st.spinner(tr("Ejecutando…")):
            st.session_state["sqlx_result"] = run_user_query(sql)
    except (QueryRejected, QueryTimeout) as error:
        st.session_state["sqlx_result"] = str(error)
    except duckdb.Error as error:
        st.session_state["sqlx_result"] = tr("DuckDB devolvió un error: {}").format(error)


def results_height(row_count):
    """The grid's height: what its container gives it, or just what its rows need when they are few."""
    needed = GRID_ROW * (row_count + 1) + 3
    return needed if needed <= GRID_FLOOR else "stretch"


def build_grid_css(sql):
    """The window's height minus what is above and below the grid; the editor above it grows with its text."""
    offset = AROUND_GRID + editor_height(sql)
    return (
        f'<style>[data-testid="stLayoutWrapper"]:has(> .st-key-sqlx_grid) '
        f"{{ height:max(calc(100vh - {offset}px), {GRID_FLOOR}px); }}</style>"
    )


def show_result(st, outcome):
    if outcome is None:
        st.markdown('<p class="sqlx-empty">El resultado aparecerá aquí.</p>', unsafe_allow_html=True)
        return
    if isinstance(outcome, str):
        st.error(outcome)
        return
    rows, truncated, seconds = outcome.rows, outcome.truncated, outcome.seconds
    summary = tr("{} filas · {} columnas · {} ms").format(
        format_count(len(rows)), len(rows.columns), format_count(seconds * 1000)
    )
    note = tr(" · se muestran las primeras {}").format(format_count(ROW_LIMIT)) if truncated else ""
    file_name = tr("consulta")
    with st.container(key="sqlx_resultbar", horizontal=True, vertical_alignment="center", gap="small"):
        st.caption(summary + note)
        if not rows.empty:
            st.download_button(
                "CSV",
                to_csv_bytes(rows),
                f"{file_name}.csv",
                "text/csv",
                key="sqlx_csv",
                on_click="ignore",
                icon=":material/download:",
            )
            st.download_button(
                "Parquet",
                partial(to_parquet_bytes, rows),
                f"{file_name}.parquet",
                "application/vnd.apache.parquet",
                key="sqlx_parquet",
                on_click="ignore",
                icon=":material/download:",
            )
    numbered = rows.set_axis(range(1, len(rows) + 1))  # rows count from 1, as a SQL client
    numbered.attrs[i18n.KEEP_NAMES] = True  # the grid shows the names the query uses, in any language (D-516)
    # Weeks are dates: show them without a midnight time.
    dates = {
        column: st.column_config.DateColumn(column, format="YYYY-MM-DD")
        for column in rows.columns
        if pd.api.types.is_datetime64_any_dtype(rows[column])
        and (rows[column].dropna().dt.normalize() == rows[column].dropna()).all()
    }
    with st.container(key="sqlx_grid"):
        st.dataframe(
            numbered,
            width="stretch",
            hide_index=False,
            height=results_height(len(rows)),
            row_height=GRID_ROW,
            column_config=dates,
        )


def follow_language(st):
    """D-516: the visit changed language with an example in the editor: its comments follow. A text the reader wrote
    or edited stays as it is."""
    language, before = i18n.get_language(), st.session_state.get("sqlx_language")
    st.session_state["sqlx_language"] = language
    if before in (None, language):
        return
    if isinstance(st.session_state.get("sqlx_result"), str):  # a message written in the language left behind
        st.session_state.pop("sqlx_result")
    example = st.session_state.get("sqlx_example")
    if example is not None and st.session_state.get("sqlx_editor") == st.session_state.get("sqlx_rendered"):
        st.session_state["sqlx_editor"] = st.session_state["sqlx_rendered"] = render_example(
            example, parameter_values()
        )


def show_relations_dialog(st, mode, descriptions):
    """D-515: the relationships between the views, as a SQL client draws them, and the joins ready to copy."""
    st.dialog("Relaciones entre las vistas", width="large")(_relations_window)(st, mode, descriptions)


def _relations_window(st, mode, descriptions):
    """The window «Relaciones»: the diagram of the views and the joins ready to copy."""
    from bi import sql_relations  # here, not at the top: sql_relations reads the views of this module

    schema, counts = sql_relations.read_schema()
    drawing, joins = st.tabs(["Diagrama", "JOIN listos para copiar"])
    with drawing:
        st.markdown(
            '<div class="sqlx-relations">' + sql_relations.build_svg(schema, counts, mode, descriptions) + "</div>",
            unsafe_allow_html=True,
        )
    with joins:
        st.code(sql_relations.build_joins(), language="sql", wrap_lines=False)


def show_exports(st):
    """The main gold tables as CSV, behind one small button (D-168)."""
    with st.popover(
        "Descargar tablas", icon=":material/download:", help="Las tablas gold en CSV, para Excel o Power BI."
    ):
        st.markdown(
            f'<p class="sqlx-note">Los precios se limitan a las últimas {EXPORT_WEEKS} semanas; el historial '
            'completo está en la base. El archivo <code>etl/datos.duckdb</code> también se abre con DBeaver, '
            'Python, R, o con Power BI y Excel mediante el driver ODBC de DuckDB.</p>',
            unsafe_allow_html=True,
        )
        for file_name, label, sql in EXPORTS:
            st.download_button(
                label,
                partial(export_csv, sql),
                file_name,
                "text/csv",
                key=f"sqlx_export_{file_name}",
                on_click="ignore",
                icon=":material/download:",
            )


def show_sql_explorer_page(mode, header=None):
    """«Consultas SQL» as a small SQL studio (D-173): a toolbar with «Ejecutar» and
    the examples, the object explorer on the left, the painted editor and the
    Resultados / Mensajes tabs on the right, and a status bar at the bottom."""
    import streamlit as st

    palette = charts.get_palette(mode)
    st.markdown(build_css(palette), unsafe_allow_html=True)
    if header:  # the page bar of the dashboard (D-267)
        header()
    if "sqlx_editor" not in st.session_state:
        st.session_state["sqlx_editor"] = st.session_state["sqlx_rendered"] = render_example(0)
        st.session_state["sqlx_example"] = 0
    follow_language(st)
    st.markdown(build_grid_css(st.session_state["sqlx_editor"]), unsafe_allow_html=True)
    try:
        catalog = load_catalog()
    except Exception as error:  # the page still explains itself without the database
        catalog = []
        st.warning(tr("No se pudo leer la base de datos: {}").format(error))
    with st.container(key="sqlx_studio"):
        with st.container(key="sqlx_toolbar"):
            with st.container(key="sqlx_toolbar_main", horizontal=True, vertical_alignment="center"):
                st.markdown(build_database_html(), unsafe_allow_html=True)
                run = st.button(
                    "Ejecutar",
                    type="primary",
                    key="sqlx_run",
                    icon=":material/play_arrow:",
                    help="Ejecuta la consulta del editor (también Ctrl + Enter).",
                )
                st.markdown(build_limits_html(), unsafe_allow_html=True)  # D-514
            # The five queries on a row of their own, so none hides under the others (D-184).
            with st.container(key="sqlx_chips_row", horizontal=True, vertical_alignment="center"):
                st.markdown(
                    '<span class="sqlx-bar-label" title="Cinco consultas para decidir. Para ir más lejos, '
                    'escribe tu propia consulta en el editor: las tablas y vistas están a la izquierda.">'
                    'Consultas</span>',
                    unsafe_allow_html=True,
                )
                for index, (title, question, _) in enumerate(examples()):
                    st.button(title, key=f"sqlx_chip_{index}", help=question, on_click=choose_example, args=(index,))
        with st.container(key="sqlx_body"):
            side, main = st.columns([1, 3.5], gap="small")
            with side, st.container(key="sqlx_explorer"):
                try:
                    tables = load_tables()
                except Exception:  # the views still work without the listing
                    tables = []
                st.markdown(build_tree_html(), unsafe_allow_html=True)
                st.markdown(build_folder_html("Tablas", len(tables)), unsafe_allow_html=True)
                for name, count, columns in tables:
                    st.button(
                        f"main.{name}",
                        key=f"sqlx_table_{name}",
                        icon=":material/table:",
                        on_click=choose_table,
                        args=(name,),
                        help=tr("Tabla del data warehouse. Columnas: {}").format(build_column_names(columns)),
                    )
                    st.markdown(build_view_html(name, "", count, columns), unsafe_allow_html=True)
                st.markdown(build_folder_html("Vistas", len(catalog)), unsafe_allow_html=True)
                for name, description, count, columns in catalog:
                    st.button(
                        i18n.Verbatim(name),  # the name of a view is code: a query writes it as it is (D-516)
                        key=f"sqlx_view_{name}",
                        icon=":material/view_list:",
                        on_click=choose_view,
                        args=(name,),
                        help=i18n.translate_text(description)
                        + " "
                        + tr("Columnas: {}").format(build_column_names(columns)),
                    )
                    st.markdown(build_view_html(name, description, count, columns), unsafe_allow_html=True)
                # D-515: how the views join, before the exports; a SQL client shows its keys the same way
                if st.button(
                    "Relaciones",
                    icon=":material/schema:",
                    key="sqlx_relations",
                    help="Cómo se unen las vistas: el diagrama entidad-relación y cada JOIN listo para copiar.",
                    width="stretch",
                ):
                    show_relations_dialog(st, mode, {name: description for name, description, _ in VIEWS})
                show_exports(st)
            with main, st.container(key="sqlx_main"):
                example = st.session_state.get("sqlx_example")
                written = st.session_state.get("sqlx_rendered", render_example(0))
                if example is not None and st.session_state["sqlx_editor"] not in (written, render_example(example)):
                    example = None
                # D-511: one line holds the script's tab and, to its right, the filters
                with st.container(key="sqlx_tabrow", horizontal=True, vertical_alignment="center", gap="small"):
                    st.markdown(build_tab_html(example), unsafe_allow_html=True, width="stretch")
                    if example is not None:
                        show_parameters(st, example)
                with st.container(key="sqlx_editor_box"):
                    st.html(EDITOR_HTML, unsafe_allow_javascript=True)
                    sql = st.text_area(
                        "Consulta SQL",
                        key="sqlx_editor",
                        label_visibility="collapsed",
                        height=editor_height(st.session_state["sqlx_editor"]),
                    )
                if run:
                    execute_editor(st, sql)
                outcome = st.session_state.get("sqlx_result")
                with st.container(key="sqlx_results"):
                    results, messages = st.tabs(["Resultados", "Mensajes"])
                    with results:
                        show_result(st, outcome)
                    with messages:
                        st.markdown(build_messages_html(outcome), unsafe_allow_html=True)
        st.markdown(build_status_html(st.session_state.get("sqlx_result")), unsafe_allow_html=True)


# endregion
