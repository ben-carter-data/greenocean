"""The stores of the project and the brand marks every diagram shares (D-189, D-236).

The data of the storage architecture: each store with what it holds and why (NODES), the
three groups of the 12 served tables (ORIGINS) and the brand discs. The drawing itself is in
bi/storage_map.py; the other views take their logos from here.
"""
from bi import brand_icons, charts, operation_center

MAIN_Y = 235
BACKUP_Y = MAIN_Y + 270
# Brand marks on a soft gradient disc: (top, bottom, glyph color).
BRANDS = {
    "sqlite": ("#5db7f2", "#0b6aa8", "#ffffff"),
    "apacheparquet": ("#5fd7a4", "#13825a", "#ffffff"),
    "dbt": ("#ff9a7a", "#e2431a", "#ffffff"),
    "duckdb": ("#ffe66d", "#e6b800", "#1f1f1f"),
    "python": ("#6fa8dc", "#2a5d96", "#ffffff"),
    "github": ("#59616b", "#1b1f24", "#ffffff"),
}
# The three origins of the 12 served tables: (key, label, brand, tables, what, why).
ORIGINS = [
    ("marts", "Modelos dbt", "dbt",
     ["weekly_price", "dim_product", "dim_region", "dim_channel", "dim_date", "rejection", "ipc_weekly",
      "ipc_monthly", "ine_ipc_source"],
     "Las nueve tablas del modelo: los precios semanales, sus dimensiones, las filas rechazadas y el IPC.",
     "dbt las construye y las prueba en cada carga; el pipeline las copia tal cual a la base servida."),
    ("log", "Registro de cargas", "python", ["etl_run"],
     "Una fila por ejecución real: cuándo empezó, qué leyó, qué cargó y qué rechazó.",
     "La escribe el pipeline en Python al terminar. Una reconstrucción local no la toca, para no inventar cargas."),
    ("trace", "Trazas de dbt", "dbt", ["dbt_node", "dbt_result"],
     "Cada modelo y prueba de dbt de la última construcción, con su resultado.",
     "El linaje y la página de calidad las leen para mostrar qué se probó. No son datos de precios."),
]
# The stores, left to right: (key, logo, label, file, place (x, y), what, why).
NODES = [
    ("odepa", "odepa", "ODEPA consumidor", "CSV por año", (95, MAIN_Y),
     "Los precios al consumidor que ODEPA publica cada semana, por región y canal, en archivos CSV por año.",
     "Es la fuente oficial. El agente los descarga y anota su huella SHA-256 en manifest.json."),
    ("wholesale", "odepa", "ODEPA mayorista", "CSV por año", (95, MAIN_Y + 165),
     "Los precios mayoristas que ODEPA publica cada semana, solo de frutas y hortalizas, en archivos CSV por año.",
     "Es la otra fuente oficial: permite comparar lo que paga el consumidor con lo que cuesta al por mayor."),
    ("ine", "ine", "INE · IPC", "índice mensual", (95, 52),
     "El índice de precios de alimentos, un valor por mes.",
     "Sirve para pasar los precios a pesos reales y separar la inflación de una subida de verdad. No pasa por SQLite: "
     "son dos CSV pequeños que el pipeline escribe directo en Parquet. Si el INE no responde una semana, se rehace "
     "desde ine_ipc_source, que se guarda en la base servida."),
    ("raw", "sqlite", "SQLite", "etl/raw.db", (275, MAIN_Y),
     "Las filas de los CSV exactamente como se publican, sin limpiar. Es un archivo de unos 665 MB.",
     "Una copia fiel permite auditar y reconstruir todo desde el origen. No se sube a GitHub por su tamaño."),
    ("bronze", "apacheparquet", "Parquet", "capa bronce", (435, MAIN_Y),
     "Las mismas filas, más el IPC del INE, en archivos Parquet: uno por fuente y año.",
     "Parquet guarda los datos por columnas y comprimidos, y casi cualquier herramienta de datos lo lee. "
     "dbt parte de aquí."),
    ("dbt", "dbt", "dbt + DuckDB", "warehouse_build.duckdb", (595, MAIN_Y),
     "Una base de trabajo con las capas staging, intermedio y marts, más las pruebas de datos de dbt.",
     "Se construye y se prueba aparte. Si una prueba falla, la base publicada no se toca. No se sube a GitHub."),
    ("served", "duckdb", "DuckDB", "etl/datos.duckdb", (755, MAIN_Y),
     "La base que el panel lee: 12 tablas, agrupadas por quién las escribe (abajo).",
     "Es un solo archivo, rápido para consultas analíticas y de solo lectura para el panel."),
    ("github", "github", "GitHub", "release y repositorio", (915, MAIN_Y),
     "La base servida, en el release «base-actual»: una sola copia, que cada carga reemplaza.",
     "Git guardaría cada versión para siempre; así el historial no crece y el panel toma del release la base de la "
     "última carga, tras comprobar su huella (D-270)."),
    ("backup", "sqlite", "SQLite · respaldo", "etl/datos.db", (755, BACKUP_Y),
     "Los mismos precios semanales, calculados otra vez por el ETL en Python (etl/etl.py), sin dbt.",
     "Es una segunda opinión independiente: si dbt y el ETL no coinciden, algo está mal. El panel no lo lee y no se "
     "publica: se rehace en la máquina de cada carga para la prueba de paridad (D-270)."),
]
def thousands(value):
    return charts.format_thousands(value) if value is not None else "—"


def brand_logo(slug, suffix=""):
    """A real brand mark in white (or ink) on a lit disc, with a gloss and a drop shadow."""
    top, bottom, glyph = BRANDS[slug]
    gradient = f"disc-{slug}{suffix}"
    return (f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs>'
            f'<radialGradient id="{gradient}" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></radialGradient></defs>'
            f'<circle cx="36" cy="36" r="31" fill="url(#{gradient})"/>'
            f'<ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" opacity=".3"/>'
            f'<g fill="{glyph}" transform="translate(17 17) scale(1.58)">{brand_icons.logo_body(slug)}</g></svg>')


def source_logo(key):
    """ODEPA's and the INE's marks, the ones of the operation center."""
    return (f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs>{operation_center.LOGOS[key]}</svg>')
