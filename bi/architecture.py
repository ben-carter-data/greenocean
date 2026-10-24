"""Live "data journey" diagram: how the data travels from ODEPA and the INE to the dashboard.

Layers from left to right (sources, ingestion, landing, bronze, dbt staging,
intermediate and marts, gold, consumption; D-154, D-155), an orchestration band
on top, observability at the bottom,
and a quarantine for rejected rows. Each step carries a status dot with its real
state (latest pipeline run and current database); dots travel along the arrows
and the dashed links move only while a run is in progress: every animation shows
real data (D-043, D-051). The rest of the time the diagram stays still.
The result is a standalone SVG text, shown with st.image (st.html removes SVG).
Only steps that really exist in this project are drawn.
"""
import html

from bi import brand_icons, charts, control, tech_glossary

# region Constants
STATE_UNKNOWN = "unknown"
STATE_SKIPPED = "skipped"
STATE_COLORS = {
    control.RUN_OK: "#22b35a", control.RUN_FAILED: "#e66767",
    control.RUN_IN_PROGRESS: "#5b9cf0", STATE_SKIPPED: "#8a8984", STATE_UNKNOWN: "#8a8984",
}
# One color per layer, the same in both modes.
LAYER_COLORS = {"sources": "#22b35a", "ingestion": "#3987e5", "bronze": "#c98500",
                "processing": "#9085e9", "quality": "#d55181", "gold": "#eda100",
                "consumption": "#199e70", "quarantine": "#e66767",
                "orchestration": "#c98500"}

WIDTH = 1560
HEIGHT = 720
# The main row sits halfway between the two ODEPA sources, and the three sources
# mirror the three uses on the right (same rows): the diagram stays symmetric.
MAIN_ROW_Y = 285
SIDE_ROWS_Y = [210, 360, 510]
QUARANTINE_Y = 480
TILE_SIZE = 64
# Center x of each layer column: nine columns 171 apart, with the same 96 margin
# on both sides.
COLUMN_X = {name: 96 + index * 171 for index, name in enumerate(
    ["sources", "ingestion", "landing", "bronze", "staging", "intermediate", "marts",
     "gold", "consumption"])}
COLUMN_HEADERS = [
    ("sources", "FUENTES", "HTTPS · CSV · sin API", "sources"),
    ("ingestion", "INGESTA", "Python · requests", "ingestion"),
    ("landing", "ATERRIZAJE", "SQLite · tal cual llega", "ingestion"),
    ("bronze", "BRONZE", "Parquet · copia exacta", "bronze"),
    ("staging", "STAGING", "dbt · tipos y textos", "processing"),
    ("intermediate", "INTERMEDIO", "dbt · reglas de negocio", "processing"),
    ("marts", "MARTS", "dbt · modelos y pruebas", "quality"),
    ("gold", "SERVING", "DuckDB · modelo estrella", "gold"),
    ("consumption", "CONSUMO", "Streamlit · GitHub · SQL", "consumption"),
]
# The medallion architecture over those columns: bronze (the Parquet copy), silver (the
# dbt staging and intermediate models) and gold (the marts and datos.duckdb). Each band
# is (key, first column, last column, label detail); the silver ink depends on the mode.
MEDALLION = [("bronze", "bronze", "bronze", "Parquet"),
             ("silver", "staging", "intermediate", "Transformación dbt"),
             ("gold", "marts", "gold", "Marts → datos.duckdb")]
SILVER_INK = {charts.BASE_DARK: "#aab6c6", charts.BASE_LIGHT: "#6f7c8e"}
# Bands of the journey (SVG units): half widths around their columns, so that each band
# holds the texts of its steps and the three sit 7 apart.
MEDALLION_SPAN = {"bronze": (535, 683), "silver": (690, 1041), "gold": (1048, 1362)}
MEDALLION_TOP = 224
MEDALLION_BOTTOM = 394
# The vertical version, for narrow screens: one step per row.
VERTICAL_WIDTH = 400
VERTICAL_TILE_X = 64
VERTICAL_FIRST_Y = 170
VERTICAL_ROW = 112
VERTICAL_BAND_ABOVE = 46   # a medallion band starts this far above its first tile centre
VERTICAL_BAND_BELOW = 44   # and ends this far below its last one
# Explanation shown on hover over each piece: what it does, with its acronyms.
TOOLTIPS = {
    "ODEPA mayorista": "Precios diarios de los mercados mayoristas, publicados por ODEPA "
                       "(Oficina de Estudios y Políticas Agrarias) en archivos CSV.",
    "ODEPA consumidor": "Precios semanales al consumidor por región y canal, en archivos CSV "
                        "de ODEPA.",
    "INE · IPC": "IPC (índice de precios al consumidor) del INE (Instituto Nacional de "
                 "Estadísticas): división «Alimentos y bebidas no alcohólicas», mensual, en "
                 "dos archivos CSV oficiales. Sirve para expresar los precios en pesos reales "
                 "(D-155).",
    "ODEPA mayorista y consumidor": "Las dos fuentes de ODEPA (Oficina de Estudios y Políticas "
                                    "Agrarias): precios mayoristas diarios y precios al "
                                    "consumidor semanales, en archivos CSV.",
    "Agente ODEPA": "agent/agent.py: Python y requests descargan los CSV de ODEPA por HTTPS, "
                    "reintentan si falla y revisan el encabezado antes de guardar nada.",
    "Descarga INE": "etl/ine.py: Python y requests descargan los dos CSV del IPC y los guardan "
                    "en bronce como texto. Si el INE no responde, la carga sigue con el IPC ya "
                    "publicado.",
    "Descarga ODEPA e INE": "agent/agent.py descarga los CSV de ODEPA y etl/ine.py los del IPC "
                            "del INE, ambos con Python y requests por HTTPS.",
    "raw.db": "Zona de aterrizaje: los CSV de ODEPA tal como llegan, con un hash por archivo "
              "para saber si cambiaron. No se sube al repositorio.",
    "SQLite · raw.db": "Base SQLite local de aterrizaje: conserva los CSV de ODEPA tal como "
                       "llegan y su hash. No se sube al repositorio.",
    "Parquet · bronce": "Capa bronce: copia exacta en Parquet, todas las columnas como texto, "
                        "por fuente y año (ODEPA) y por archivo (INE). etl/bronze.py con pyarrow.",
    "Staging": "Modelos dbt de staging (stg_odepa__wholesale, stg_odepa__consumer, "
               "stg_ine__ipc_monthly): convierten tipos y normalizan textos (RN-01, RN-02, "
               "RN-13; RN = regla de negocio).",
    "Intermedio": "Modelos dbt intermedios: validan y apartan las filas inválidas (RN-11), "
                  "llevan los precios a kilo o unidad, los agrupan por semana y marcan los "
                  "atípicos (RN-03 a RN-12).",
    "Marts y pruebas": "Marts de dbt: el modelo estrella (dim_product, dim_region, dim_channel, "
                       "dim_date, weekly_price), rejection y el IPC mensual y semanal. Las "
                       "pruebas de dbt revisan claves, relaciones y la conciliación: si una "
                       "falla, no se publica nada.",
    "datos.duckdb": "Capa oro: el data warehouse DuckDB que leen el panel, el informe y las "
                    "consultas. Se reemplaza solo si todos los modelos y pruebas pasaron.",
    "datos.db": "Respaldo SQLite que aún escribe etl/etl.py; una prueba de paridad lo compara "
                "con datos.duckdb cada semana (D-154).",
    "Rechazos": "Mart rejection: cada fila descartada, tal como venía, con su motivo (RN-11).",
    "Panel Streamlit": "Este panel: lee datos.duckdb en modo solo lectura.",
    "Informe semanal": "Issue de GitHub con el estado de la carga y las alertas de la semana.",
    "Consultas SQL": "SQL (lenguaje de consultas estructurado) sobre la capa oro: los indicadores de "
                     "bi/queries.sql y la página «Consultas SQL», donde cualquiera cruza las tablas en "
                     "solo lectura y descarga el resultado en CSV, por ejemplo para Excel o Power BI.",
    "GitHub Actions": "Servicio de GitHub que ejecuta el workflow semanal cada martes, sin "
                      "intervención.",
    "etl/pipeline.py": "Copia bronce a Parquet, corre dbt build (modelos y pruebas) en una base "
                       "de trabajo y solo si todo pasa reemplaza datos.duckdb.",
    "Pruebas automáticas": "pytest corre contra la base nueva, con la paridad SQLite y DuckDB: "
                           "si una prueba falla, no se guarda nada.",
    "Secretos": "Claves que no están en el código: el token de GitHub y la clave del botón "
                "«Ejecutar ahora».",
    "etl_run": "Tabla con una fila por carga. ETL = extraer, transformar y cargar.",
    "dbt_result": "Tablas dbt_node y dbt_result: el linaje de cada modelo y el resultado de "
                  "cada prueba de dbt en la última carga.",
    "Logs del agente": "Un archivo de texto por ejecución con lo que hizo la descarga.",
    "Correo de GitHub": "GitHub avisa por correo al autor si el workflow semanal falla.",
    "Centro de control": "Página del panel con el historial de ejecuciones en vivo.",
    "ODEPA e INE · CSV": "Archivos CSV publicados por ODEPA y por el INE, descargados por "
                         "HTTPS; ninguna de las dos fuentes ofrece una API en el flujo "
                         "utilizado por el proyecto.",
    "Python · requests": "Python ejecuta la ingesta y requests descarga los CSV por HTTPS.",
    "dbt · DuckDB": "dbt Core con dbt-duckdb transforma y prueba los datos: staging, "
                    "intermedio y marts.",
    "Streamlit": "Aplicación web que consulta DuckDB y presenta el dashboard.",
    "Datos abiertos": "Portal de datos abiertos de ODEPA: un CSV por año y fuente, descargado "
                      "por HTTPS.",
    "ODEPA · precios": "Portal de datos abiertos de ODEPA: un CSV por año y fuente (mayorista "
                       "y consumidor), descargado por HTTPS.",
    "INE · IPC alimentos": "IPC mensual del INE, división «Alimentos y bebidas no "
                           "alcohólicas»: dos CSV oficiales descargados por HTTPS (D-155).",
    "VS Code · Claude Code": "Donde se escribe el código: el editor VS Code y el asistente "
                             "Claude Code. pytest corre antes de cada commit.",
    "Job semanal.yml": "Workflow de GitHub Actions: cada martes descarga, construye el data "
                       "warehouse con dbt, prueba, guarda datos.duckdb y publica el informe.",
    "Caché de Actions": "Guarda los CSV de los años cerrados para no descargarlos cada semana "
                        "(D-047).",
    "Issues": "Donde se publica el informe semanal, uno por ejecución.",
    "Repositorio": "La rama main en GitHub: el código, datos.duckdb y el respaldo datos.db. "
                   "Es la única fuente de la verdad.",
    "Pruebas (CI)": "CI = integración continua: pruebas.yml compila el proyecto dbt (dbt parse) "
                    "y corre pytest en cada push, y avisa si algo se rompe.",
    "Permisos del job": "Mínimo privilegio: el job solo puede escribir contenido (el commit de "
                        "la base) y crear issues.",
    "App Streamlit": "El panel publicado en Streamlit Community Cloud; abre datos.duckdb en "
                     "solo lectura.",
    "Visitantes": "Quien abre el enlace público del panel desde su navegador.",
    "ODEPA": "Las dos fuentes de precios de ODEPA, en archivos CSV.",
    "ODEPA · INE": "Las fuentes públicas: los precios de ODEPA y el IPC de alimentos del INE, "
                   "en archivos CSV.",
    "Ingesta": "La descarga de los archivos, con reintentos y validación.",
    "ETL": "Extraer, transformar y cargar: bronce en Parquet y modelos dbt con sus pruebas.",
    "Data warehouse": "datos.duckdb: la base DuckDB lista para analizar.",
    "Panel": "Este panel, con los datos de la última carga.",
}


# Real technology per step (D-103): one list, used by every diagram instead of
# scattering tool names through each node's own caption. "logo" names a file of
# bi/assets/logos/ (already local, no network); when there is none, the badge is
# a styled text pill instead of a fabricated logo (an explicit project choice,
# not a missing asset).
TECH = {
    "python":    {"label": "Python", "logo": "python"},
    "requests":  {"label": "requests", "logo": None},
    "pandas":    {"label": "pandas", "logo": None},
    "pyarrow":   {"label": "pyarrow", "logo": None},
    "sqlite":    {"label": "SQLite", "logo": "sqlite"},
    "duckdb":    {"label": "DuckDB", "logo": "duckdb"},
    "dbt":       {"label": "dbt", "logo": "dbt"},
    "parquet":   {"label": "Parquet", "logo": "apacheparquet"},
    "streamlit": {"label": "Streamlit", "logo": "streamlit"},
    "github":    {"label": "GitHub CLI", "logo": "github"},
    "https":     {"label": "HTTPS", "logo": None},
    "csv":       {"label": "CSV", "logo": None},
    "markdown":  {"label": "Markdown", "logo": None},
    "sql":       {"label": "SQL", "logo": None},
}
# {node title: [tech id, ...]}, 1 to 3 per step, keyed exactly like TOOLTIPS so
# both the horizontal and the vertical diagram (which share these titles) pick
# up the same badges without a second lookup table.
PIPELINE_STACK = {
    "ODEPA mayorista": ["https", "csv"],
    "ODEPA consumidor": ["https", "csv"],
    "INE · IPC": ["https", "csv"],
    "ODEPA mayorista y consumidor": ["https", "csv"],
    "Agente ODEPA": ["python", "requests"],
    "Descarga INE": ["python", "requests"],
    "Descarga ODEPA e INE": ["python", "requests"],
    # «SQLite · raw.db» already spells out SQLite in its own title, and the DuckDB
    # logo of datos.duckdb is its own tile icon: no pill repeats them.
    "Parquet · bronce": ["parquet", "python", "pyarrow"],
    "Staging": ["dbt", "sql", "duckdb"],
    "Intermedio": ["dbt", "sql", "duckdb"],
    "Marts y pruebas": ["dbt", "sql"],
    "Panel Streamlit": ["streamlit"],
    "Informe semanal": ["python", "markdown", "github"],
    "Consultas SQL": ["duckdb", "sql"],
}
# Explanation of what travels through each link.
CHIP_TOOLTIPS = {
    "API de GitHub": "El Centro de operación lee las ejecuciones del workflow y, con la clave guardada en los secretos, "
                     "lo lanza con «Ejecutar pipeline ahora». Va en los dos sentidos: pregunta y recibe.",
    "CSV": "CSV: archivo de texto con valores separados por comas.",
    "HTTPS · CSV": "HTTPS: conexión web cifrada; por ella llegan los archivos CSV.",
    "manifest": "manifest.json: registro de cada archivo descargado, con su hash.",
    "raw_*": "Tablas crudas raw_wholesale y raw_consumer de raw.db, copiadas a Parquet como "
             "texto.",
    "ine_ipc": "Las filas del IPC del INE, como texto, en bronze/ine_ipc.",
    "sources": "sources.yml: dbt lee los archivos Parquet de bronce como fuentes.",
    "stg_*": "Modelos de staging: datos con tipos y textos normalizados.",
    "int_*": "Capa plata: modelos intermedios, con las reglas de negocio aplicadas.",
    "inválidas": "Filas rechazadas: van al mart rejection con su motivo.",
    "OK": "Todos los modelos y pruebas de dbt pasaron: la base se publica.",
    "SQL": "SQL: consultas que leen el data warehouse.",
    "MD": "MD = Markdown: formato de texto del informe semanal.",
    "EJECUTA": "GitHub Actions da la orden de ejecutar; no toca los datos.",
    "git push": "Sube los cambios del computador al repositorio.",
    "checkout · commit": "El job baja el repositorio (checkout) y guarda la base nueva (commit).",
    "cache": "El job restaura y guarda los CSV de los años cerrados.",
    "gh issue create": "Comando de GitHub que publica el informe como issue.",
    "on: push": "pruebas.yml se activa con cada push.",
    "despliegue de main": "Streamlit vuelve a publicar el panel cada vez que cambia main.",
    "st.secrets": "La app lee sus secretos sin que estén escritos en el código.",
    "HTTPS": "Conexión web cifrada entre el navegador y la app.",
}
# endregion


# region States
def has_real_state(state):
    """True for a state read from a run or from the database; unknown is not one."""
    return state in STATE_COLORS and state != STATE_UNKNOWN


def add_tooltip(svg_part, explanation):
    """Group a piece with its explanation: the browser shows it on hover."""
    if not explanation:
        return svg_part
    return f'<g class="has-tooltip"><title>{html.escape(explanation)}</title>{svg_part}</g>'


def add_tech_tooltip(svg_part, key):
    """Group a technology (pill, logo, chip, label) with its glossary entry: the browser
    shows it on hover, and the inner title wins over the step's own explanation."""
    return add_tech_explanation(svg_part, tech_glossary.describe(key))


def add_tech_explanation(svg_part, explanation):
    """The same group for a ready text (several glossary entries, one per line)."""
    if not explanation:
        return svg_part
    return (f'<g class="tech-tip" style="cursor:help"><title>{html.escape(explanation)}</title>'
            f'{svg_part}</g>')
# endregion


# region Icons
# Each icon is drawn inside a 64 x 64 tile centered on (x, y), with the layer color.
def draw_file_icon(x, y, color):
    """A sheet of paper with a folded corner (a CSV file)."""
    return (f'<path d="M{x-12} {y-16} h16 l8 8 v24 h-24 z" fill="none" stroke="{color}" '
            f'stroke-width="2.2" stroke-linejoin="round"/>'
            f'<path d="M{x+4} {y-16} v8 h8" fill="none" stroke="{color}" stroke-width="2.2"/>'
            f'<text x="{x}" y="{y+9}" text-anchor="middle" font-size="8" font-weight="700" '
            f'fill="{color}">CSV</text>')


def draw_database_icon(x, y, color):
    """A cylinder: a stored database."""
    return (f'<ellipse cx="{x}" cy="{y-11}" rx="15" ry="5" fill="none" stroke="{color}" '
            f'stroke-width="2.2"/>'
            f'<path d="M{x-15} {y-11} v22 a15 5 0 0 0 30 0 v-22 M{x-15} {y} a15 5 0 0 0 30 0" '
            f'fill="none" stroke="{color}" stroke-width="2.2"/>')


def draw_funnel_icon(x, y, color):
    """A funnel: rows are filtered and cleaned."""
    return (f'<path d="M{x-16} {y-13} h32 l-12 14 v12 l-8 4 v-16 z" fill="none" '
            f'stroke="{color}" stroke-width="2.2" stroke-linejoin="round"/>')


def draw_sliders_icon(x, y, color):
    """Three sliders: business rules adjust each value."""
    lines = "".join(f'<path d="M{x-15} {y+offset} h30" stroke="{color}" stroke-width="2.2" '
                    f'stroke-linecap="round"/><circle cx="{x+knob}" cy="{y+offset}" r="4" '
                    f'fill="{color}"/>'
                    for offset, knob in [(-10, -6), (0, 7), (10, -1)])
    return lines


def draw_shield_icon(x, y, color):
    """A shield with a check mark: the load passes its checks."""
    return (f'<path d="M{x} {y-17} l14 5 v9 c0 9 -6 15 -14 18 c-8 -3 -14 -9 -14 -18 v-9 z" '
            f'fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round"/>'
            f'<path d="M{x-6} {y} l4 5 l8 -9" fill="none" stroke="{color}" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def draw_chart_icon(x, y, color):
    """Four bars: the dashboard."""
    return "".join(f'<rect x="{x-14+index*8}" y="{y+12-height}" width="5" height="{height}" '
                   f'rx="1.5" fill="{color}"/>'
                   for index, height in enumerate([10, 16, 22, 28]))


def draw_report_icon(x, y, color):
    """A page with text lines: the weekly report."""
    lines = "".join(f'<path d="M{x-7} {y+offset} h14" stroke="{color}" stroke-width="2"/>'
                    for offset in [-6, 0, 6])
    return (f'<rect x="{x-12}" y="{y-16}" width="24" height="32" rx="3" fill="none" '
            f'stroke="{color}" stroke-width="2.2"/>' + lines)


def draw_code_icon(x, y, color):
    """Angle brackets: reusable SQL queries."""
    return (f'<path d="M{x-6} {y-10} l-9 10 l9 10 M{x+6} {y-10} l9 10 l-9 10" fill="none" '
            f'stroke="{color}" stroke-width="2.4" stroke-linecap="round" '
            f'stroke-linejoin="round"/>')


def draw_python_icon(x, y, color):
    """The real Python logo, centered in a journey tile."""
    return brand_icons.logo("python", x - 18, y - 18, color, 36)


def draw_sqlite_icon(x, y, color):
    """The traditional cylinder, not the SQLite brand mark: the node's own title
    already says «SQLite» in words, and a plain database shape reads clearer at
    this size than the brand's lettering (explicit choice, not a missing asset)."""
    return draw_database_icon(x, y, color)


def draw_streamlit_icon(x, y, color):
    """The real Streamlit logo, centered in a journey tile."""
    return brand_icons.logo("streamlit", x - 18, y - 18, color, 36)


def draw_github_icon(x, y, color):
    """The real GitHub logo, centered in a journey tile."""
    return brand_icons.logo("github", x - 18, y - 18, color, 36)


def draw_duckdb_icon(x, y, color):
    """The real DuckDB logo (Simple Icons), centered in a journey tile."""
    return brand_icons.logo("duckdb", x - 18, y - 18, color, 36)


def draw_dbt_icon(x, y, color):
    """The real dbt logo (Simple Icons), centered in a journey tile."""
    return brand_icons.logo("dbt", x - 18, y - 18, color, 36)


def draw_parquet_icon(x, y, color):
    """The real Apache Parquet logo (Simple Icons), centered in a journey tile."""
    return brand_icons.logo("apacheparquet", x - 18, y - 18, color, 36)


# Which brand slug a node's own tile icon already shows, so a stack badge never
# repeats the same logo right under it (D-103).
ICON_LOGO_SLUG = {draw_python_icon: "python", draw_streamlit_icon: "streamlit",
                  draw_github_icon: "github", draw_duckdb_icon: "duckdb",
                  draw_dbt_icon: "dbt", draw_parquet_icon: "apacheparquet"}


def draw_tile_icon(draw_icon, x, y, color):
    """A tile icon; a brand logo also explains its technology on hover."""
    slug = ICON_LOGO_SLUG.get(draw_icon)
    icon = draw_icon(x, y, color)
    return add_tech_tooltip(icon, tech_glossary.LOGO_KEYS[slug]) if slug else icon


def draw_warning_icon(x, y, color):
    """A triangle with an exclamation mark: rejected rows."""
    return (f'<path d="M{x} {y-15} l16 28 h-32 z" fill="none" stroke="{color}" '
            f'stroke-width="2.2" stroke-linejoin="round"/>'
            f'<path d="M{x} {y-5} v9" stroke="{color}" stroke-width="2.4" '
            f'stroke-linecap="round"/><circle cx="{x}" cy="{y+9}" r="1.6" fill="{color}"/>')


def draw_clock_icon(x, y, color):
    """A clock: the job that runs on a schedule."""
    return (f'<circle cx="{x}" cy="{y}" r="15" fill="none" stroke="{color}" '
            f'stroke-width="2.2"/><path d="M{x} {y-9} v9 l7 5" fill="none" '
            f'stroke="{color}" stroke-width="2.4" stroke-linecap="round" '
            f'stroke-linejoin="round"/>')


# endregion


# region Pieces
def build_style(is_running):
    """Style the flow illustration; status pulses are attached to real running nodes."""
    dash_motion = ("animation: journey-dash 1.2s linear infinite;" if is_running else "")
    return f"""<style>
    .journey-running {{ animation: journey-pulse 1.2s ease-in-out infinite; }}
    .journey-dashed {{ stroke-dasharray: 5 5; {dash_motion} }}
    @keyframes journey-pulse {{ 50% {{ opacity: 0.2; }} }}
    @keyframes journey-dash {{ to {{ stroke-dashoffset: -20; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .journey-running, .journey-dashed {{ animation: none; }}
      .journey-flow {{ display: none; }}
    }}
    </style>"""


def build_column_headers():
    """Name and short description of each layer, above its column."""
    parts = []
    for column, title, subtitle, layer in COLUMN_HEADERS:
        x = COLUMN_X[column]
        parts.append(f'<text x="{x}" y="40" text-anchor="middle" font-size="15" '
                     f'font-weight="700" letter-spacing="1" fill="{LAYER_COLORS[layer]}">'
                     f'{title}</text>'
                     + add_tech_explanation(
                         f'<text x="{x}" y="60" text-anchor="middle" font-size="13" '
                         f'fill="#8a8984">{subtitle}</text>',
                         tech_glossary.describe_words(subtitle)))
    return "".join(parts)


def measure_stack_badge(tech_id):
    """Width in SVG units of one technology pill, logo and label included."""
    tech = TECH[tech_id]
    icon_width = 13 if tech["logo"] else 0
    return 6 + icon_width + (3 if tech["logo"] else 0) + len(tech["label"]) * 5.6 + 6


def build_stack_badge(x, y, tech_id, palette):
    """One pill: a local logo when there is one, a styled text label otherwise."""
    tech = TECH[tech_id]
    width = measure_stack_badge(tech_id)
    height = 16
    color = palette["text"]
    parts = [f'<rect x="{x:.1f}" y="{y - height / 2:.1f}" width="{width:.1f}" height="{height}" '
             f'rx="8" fill="{palette["field"]}" stroke="{palette["card_border"]}" stroke-width="1"/>']
    cursor = x + 6
    if tech["logo"]:
        size = 13
        parts.append(brand_icons.logo(tech["logo"], cursor, y - size / 2, color, size))
        cursor += size + 3
    parts.append(f'<text x="{cursor:.1f}" y="{y + 3.3:.1f}" font-size="9.5" font-weight="600" '
                 f'fill="{color}">{html.escape(tech["label"])}</text>')
    return add_tech_tooltip("".join(parts), tech_glossary.TECH_KEYS.get(tech_id, tech_id))


def build_stack_row(x, y, tech_ids, palette, align="center"):
    """The real tools of one step, as 1 to 3 small pills (D-103, PIPELINE_STACK).

    align="center" centers the row on x (the horizontal diagram); "left" starts
    it at x (the narrow-screen diagram, which reads left to right from the tile).
    """
    gap = 5
    widths = [measure_stack_badge(tech_id) for tech_id in tech_ids]
    total = sum(widths) + gap * (len(widths) - 1)
    cursor = x - total / 2 if align == "center" else x
    parts = []
    for tech_id, width in zip(tech_ids, widths):
        parts.append(build_stack_badge(cursor, y, tech_id, palette))
        cursor += width + gap
    # Each pill carries its own glossary entry (bi/tech_glossary.py).
    return f'<g>{"".join(parts)}</g>'


def visible_stack(title, draw_icon):
    """PIPELINE_STACK for a node, without the logo its own tile icon already shows.

    A node whose whole stack is that one already-pictured tool (SQLite · raw.db,
    Panel Streamlit) gets no pill row at all: nothing new to say, so the node
    stays exactly as it was before D-103.
    """
    stack = PIPELINE_STACK.get(title)
    if not stack:
        return None
    icon_logo = ICON_LOGO_SLUG.get(draw_icon)
    # Only drop a pill that has a real logo matching the tile's own icon; a text
    # pill (no logo of its own) is never "the same" as an icon with no logo.
    return [tech_id for tech_id in stack if not (TECH[tech_id]["logo"] and TECH[tech_id]["logo"] == icon_logo)]


def build_node(x, y, layer, draw_icon, title, lines, palette, state=None):
    """Icon tile, title, up to two lines of detail and, when known, a status dot.

    A node listed in PIPELINE_STACK also gets a row of technology pills (D-103),
    in the same vertical space the first caption line used: the diagram keeps
    its exact size, only the step's own tools become explicit.
    """
    color = LAYER_COLORS[layer]
    half = TILE_SIZE / 2
    parts = [f'<rect x="{x-half}" y="{y-half}" width="{TILE_SIZE}" height="{TILE_SIZE}" '
             f'rx="16" fill="{palette["card"]}" stroke="{color}" stroke-width="1.5"/>',
             draw_tile_icon(draw_icon, x, y, color),
             f'<text x="{x}" y="{y+half+22}" text-anchor="middle" font-size="16" '
             f'font-weight="700" fill="{palette["strong_text"]}">{html.escape(title)}</text>']
    stack = visible_stack(title, draw_icon)
    shown_lines = lines[1:2] if stack else lines[:2]
    if stack:
        parts.append(build_stack_row(x, y + half + 36, stack, palette))
    for line_number, line in enumerate(shown_lines):
        base_y = y + half + 58 if stack else y + half + 42
        parts.append(f'<text x="{x}" y="{base_y+line_number*17}" text-anchor="middle" '
                     f'font-size="13" fill="{palette["text"]}">{html.escape(line)}</text>')
    # Only a real state gets a dot; an unknown one gets none (a grey dot would
    # look like a state).
    if has_real_state(state):
        pulse = ' class="journey-running"' if state == control.RUN_IN_PROGRESS else ""
        parts.append(f'<circle{pulse} cx="{x+half-4}" cy="{y-half+4}" r="7" '
                     f'fill="{STATE_COLORS[state]}" '
                     f'stroke="{palette["card"]}" stroke-width="2.5"/>')
    return add_tooltip("".join(parts), TOOLTIPS.get(title))


def build_chip(x, y, text, color, palette):
    """Small label on a link that says what kind of data travels through it."""
    width = len(text) * 7.6 + 16
    chip = (
        f'<rect x="{x-width/2}" y="{y-11}" width="{width}" height="22" rx="6" '
        f'fill="{palette["card"]}" stroke="{color}" stroke-width="1"/>'
        f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="12" font-weight="700" '
        f'font-family="monospace" fill="{color}">{html.escape(text)}</text>')
    if text in tech_glossary.CHIP_KEYS:
        return add_tech_tooltip(chip, tech_glossary.CHIP_KEYS[text])
    # A chip that names several technologies («HTTPS · CSV») keeps its own line and
    # adds the glossary entry of each one.
    words = tech_glossary.describe_words(text)
    if words:
        return add_tech_explanation(chip, "\n".join(filter(None, [CHIP_TOOLTIPS.get(text), words])))
    return add_tooltip(chip, CHIP_TOOLTIPS.get(text))


def build_link(start, end, color, palette, chip_text=None, dashed=False, moving_dot=False):
    """Curved link between two points, with an optional chip and a travelling dot."""
    (x1, y1), (x2, y2) = start, end
    middle_x = (x1 + x2) / 2
    path = f"M{x1} {y1} C{middle_x} {y1} {middle_x} {y2} {x2} {y2}"
    dash_class = ' class="journey-dashed"' if dashed else ""
    parts = [f'<path{dash_class} d="{path}" fill="none" stroke="{color}" stroke-width="1.6" '
             f'opacity="0.85"/>']
    if moving_dot:
        parts.append(f'<circle class="journey-flow" r="3.5" fill="{color}"><animateMotion dur="2.4s" '
                     f'repeatCount="indefinite" path="{path}"/></circle>')
    if chip_text:
        parts.append(build_chip(middle_x, (y1 + y2) / 2, chip_text, color, palette))
    return "".join(parts)


def build_routed_link(start, end, lane_x, color, palette, chip_text=None, moving_dot=False):
    """Link that runs flat, climbs straight up a free lane at lane_x and turns into
    its target: for a link that must pass beside, not through, another step."""
    (x1, y1), (x2, y2) = start, end
    radius = 14
    path = (f"M{x1} {y1} H{lane_x - radius} Q{lane_x} {y1} {lane_x} {y1 - radius} "
            f"V{y2 + radius} Q{lane_x} {y2} {lane_x + radius} {y2} H{x2}")
    parts = [f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.6" '
             f'opacity="0.85"/>']
    if moving_dot:
        parts.append(f'<circle class="journey-flow" r="3.5" fill="{color}"><animateMotion dur="2.4s" '
                     f'repeatCount="indefinite" path="{path}"/></circle>')
    if chip_text:
        parts.append(build_chip((x1 + lane_x) / 2, y1, chip_text, color, palette))
    return "".join(parts)


def build_band(x, y, width, height, title, color, palette):
    """Dashed area with a title (orchestration, observability)."""
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" fill="none" '
            f'stroke="{color}" stroke-width="1" stroke-dasharray="4 4" opacity="0.8"/>'
            f'<text x="{x+16}" y="{y+22}" font-size="13" font-weight="700" letter-spacing="1" '
            f'fill="{palette["text"]}">{html.escape(title)}</text>')


def build_band_item(x, y, title, detail, palette, state=None):
    """One item of a band: a title, a detail and, only with a real state, its dot.

    An item without a known state has no dot: a grey dot would look like a state.
    """
    dot = ""
    if has_real_state(state):
        pulse = ' class="journey-running"' if state == control.RUN_IN_PROGRESS else ""
        dot = f'<circle{pulse} cx="{x}" cy="{y-4}" r="5" fill="{STATE_COLORS[state]}"/>'
    name = (f'<text x="{x+12}" y="{y}" font-size="14" font-weight="700" '
            f'fill="{palette["strong_text"]}">{html.escape(title)}</text>')
    if title in tech_glossary.LABEL_KEYS:
        name = add_tech_tooltip(name, tech_glossary.LABEL_KEYS[title])
    return add_tooltip(f'{dot}{name}'
                       f'<text x="{x+12}" y="{y+18}" font-size="13" '
                       f'fill="{palette["text"]}">{html.escape(detail)}</text>',
                       TOOLTIPS.get(title))
# endregion


# region Diagram
def read_dbt_state(states):
    """State of the dbt transformation: its own state when the caller has one,
    otherwise the ETL step of the same weekly run."""
    return states.get("dbt", states["etl"])


def build_main_nodes(states, figures, palette):
    """The steps of the data, from the ODEPA and INE files to the data warehouse."""
    column = COLUMN_X
    odepa_wholesale_y, odepa_consumer_y, ine_y = SIDE_ROWS_Y
    dbt_state = read_dbt_state(states)
    return "".join([
        build_node(column["sources"], odepa_wholesale_y, "sources", draw_file_icon,
                   "ODEPA mayorista", ["HTTPS · CSV · sin API", figures["source_years"]],
                   palette, states["sources"]),
        build_node(column["sources"], odepa_consumer_y, "sources", draw_file_icon,
                   "ODEPA consumidor", ["HTTPS · CSV · sin API", figures["source_years"]],
                   palette, states["sources"]),
        build_node(column["sources"], ine_y, "sources", draw_file_icon, "INE · IPC",
                   ["HTTPS · CSV · sin API", "alimentos · mensual"], palette),
        build_node(column["ingestion"], MAIN_ROW_Y, "ingestion", draw_python_icon,
                   "Agente ODEPA", ["Python · requests", figures["last_run"]],
                   palette, states["download"]),
        build_node(column["ingestion"], ine_y, "ingestion", draw_python_icon,
                   "Descarga INE", ["Python · requests", "etl/ine.py"], palette),
        build_node(column["landing"], MAIN_ROW_Y, "ingestion", draw_sqlite_icon,
                   "SQLite · raw.db", ["zona de aterrizaje", "hash por archivo"], palette),
        build_node(column["bronze"], MAIN_ROW_Y, "bronze", draw_parquet_icon,
                   "Parquet · bronce", ["Python · pyarrow", "texto, por fuente y año"],
                   palette),
        build_node(column["staging"], MAIN_ROW_Y, "processing", draw_dbt_icon, "Staging",
                   ["dbt · SQL", figures["rows_read"]], palette, dbt_state),
        build_node(column["intermediate"], MAIN_ROW_Y, "processing", draw_dbt_icon,
                   "Intermedio", ["dbt · SQL", "unidades · semanas · RN-12"], palette,
                   dbt_state),
        build_node(column["marts"], MAIN_ROW_Y, "quality", draw_shield_icon,
                   "Marts y pruebas", ["dbt · SQL", "estrella · IPC · pruebas"], palette,
                   states["load"]),
        build_node(column["gold"], MAIN_ROW_Y, "gold", draw_duckdb_icon, "datos.duckdb",
                   [figures["weekly_prices"], figures["latest_week"]], palette, states["load"]),
    ])


def build_consumption_nodes(states, figures, palette):
    """Where the data is used: dashboard, weekly report and SQL queries."""
    x = COLUMN_X["consumption"]
    panel_y, report_y, queries_y = SIDE_ROWS_Y
    return "".join([
        build_node(x, panel_y, "consumption", draw_streamlit_icon, "Panel Streamlit",
                   ["esta página", figures["panel_time"]], palette, states["panel"]),
        build_node(x, report_y, "consumption", draw_github_icon, "Informe semanal",
                   ["GitHub Issue · Markdown", "alertas y estado"], palette, states["report"]),
        build_node(x, queries_y, "consumption", draw_code_icon, "Consultas SQL",
                   ["DuckDB · queries.sql", "página Consultas SQL"], palette),
    ])


def build_links(palette, is_running):
    """Links between steps, each with the kind of data that travels through it.

    Dots travel along them only while a run is in progress.
    """
    column = COLUMN_X
    half = TILE_SIZE / 2
    first_y, second_y, third_y = SIDE_ROWS_Y

    def right_of(name, y=MAIN_ROW_Y):
        return (column[name] + half, y)

    def left_of(name, y=MAIN_ROW_Y):
        return (column[name] - half, y)

    return "".join([
        build_link(right_of("sources", first_y), left_of("ingestion"), LAYER_COLORS["sources"],
                   palette, moving_dot=is_running),
        build_link(right_of("sources", second_y), left_of("ingestion"),
                   LAYER_COLORS["sources"], palette, moving_dot=is_running),
        build_link(right_of("sources", third_y), left_of("ingestion", third_y),
                   LAYER_COLORS["sources"], palette, moving_dot=is_running),
        # The INE files skip the landing database: etl/ine.py writes bronze directly,
        # through the free lane between the landing and bronze captions.
        build_routed_link(right_of("ingestion", third_y), left_of("bronze", MAIN_ROW_Y + 20),
                          (column["landing"] + column["bronze"]) / 2,
                          LAYER_COLORS["ingestion"], palette, "ine_ipc", moving_dot=is_running),
        build_link(right_of("ingestion"), left_of("landing"), LAYER_COLORS["ingestion"],
                   palette, "manifest", moving_dot=is_running),
        build_link(right_of("landing"), left_of("bronze"), LAYER_COLORS["ingestion"],
                   palette, "raw_*", moving_dot=is_running),
        build_link(right_of("bronze"), left_of("staging"), LAYER_COLORS["bronze"],
                   palette, "sources", moving_dot=is_running),
        build_link(right_of("staging"), left_of("intermediate"), LAYER_COLORS["processing"],
                   palette, "stg_*", moving_dot=is_running),
        build_link(right_of("intermediate"), left_of("marts"), LAYER_COLORS["processing"],
                   palette, "int_*", moving_dot=is_running),
        build_link(right_of("marts"), left_of("gold"), LAYER_COLORS["quality"],
                   palette, "OK", moving_dot=is_running),
        build_link(right_of("gold"), left_of("consumption", first_y), LAYER_COLORS["gold"],
                   palette, "SQL", moving_dot=is_running),
        build_link(right_of("gold"), left_of("consumption", second_y), LAYER_COLORS["gold"],
                   palette, "MD", moving_dot=is_running),
        # D-162: the gold layer is queried for real now, so this link flows like the others.
        build_link(right_of("gold"), left_of("consumption", third_y), LAYER_COLORS["gold"],
                   palette, "consultas", moving_dot=is_running),
    ])


def build_quarantine(figures, palette):
    """Rejected rows go to the rejection mart with their reason (RN-11)."""
    x = (COLUMN_X["staging"] + COLUMN_X["intermediate"]) / 2
    y = QUARANTINE_Y
    start = (COLUMN_X["staging"] + TILE_SIZE / 2, MAIN_ROW_Y + 14)
    path = (f"M{start[0]} {start[1]} C{x} {start[1]} {x} {start[1] + 60} {x} "
            f"{y - TILE_SIZE / 2}")
    return (f'<path class="journey-dashed" d="{path}" fill="none" '
            f'stroke="{LAYER_COLORS["quarantine"]}" stroke-width="1.6"/>'
            + build_chip(x, MAIN_ROW_Y + 132, "inválidas", LAYER_COLORS["quarantine"],
                         palette)
            + build_node(x, y, "quarantine", draw_warning_icon, "Rechazos",
                         ["DuckDB · mart rejection", figures["rows_rejected"]], palette))


def build_orchestration(states, figures, palette):
    """Top band: who gives the orders. It never touches the data itself."""
    left = COLUMN_X["ingestion"] - 70
    width = COLUMN_X["gold"] + 70 - left
    spacing = (width - 60) / 4
    parts = [build_band(left, 84, width, 70,
                        "ORQUESTACIÓN — da las órdenes; no toca los datos",
                        LAYER_COLORS["orchestration"], palette),
             build_band_item(left + 30, 128, "GitHub Actions",
                             f"cada martes · próxima {figures['next_run']}", palette,
                             states["workflow"]),
             build_band_item(left + 30 + spacing, 128, "etl/pipeline.py",
                             "dbt build · publica si todo pasa", palette),
             build_band_item(left + 30 + 2 * spacing, 128, "Pruebas automáticas",
                             "pytest · si fallan, no se guarda", palette, states["tests"]),
             build_band_item(left + 30 + 3 * spacing, 128, "Secretos",
                             "GitHub Actions · Secrets", palette)]
    # Orders go down to the agent; they are commands, not data.
    agent_x = COLUMN_X["ingestion"]
    parts.append(f'<path class="journey-dashed" d="M{agent_x} 154 V{MAIN_ROW_Y - 34}" '
                 f'stroke="{LAYER_COLORS["orchestration"]}" stroke-width="1.4" fill="none"/>')
    parts.append(build_chip(agent_x, (154 + MAIN_ROW_Y - 34) / 2, "EJECUTA",
                            LAYER_COLORS["orchestration"], palette))
    return "".join(parts)


def build_observability(states, figures, palette):
    """Bottom band: how we know what happened in each run."""
    left = COLUMN_X["landing"] - 70
    width = COLUMN_X["gold"] + 70 - left
    items = [("etl_run", "DuckDB · una fila por carga", states.get("etl_run")),
             ("dbt_result", "DuckDB · linaje y pruebas", None),
             ("Logs del agente", "Python · por ejecución", None),
             ("Correo de GitHub", "GitHub · si el job falla", None),
             ("Centro de control", "Streamlit · historial", None)]
    spacing = (width - 60) / len(items)
    return (build_band(left, 618, width, 72, "OBSERVABILIDAD — cómo sabemos qué pasó",
                       palette["text"], palette)
            + "".join(build_band_item(left + 30 + index * spacing, 662, title, detail,
                                      palette, state)
                      for index, (title, detail, state) in enumerate(items)))


def build_container(palette):
    """Area that groups the storage and transformation steps."""
    left = COLUMN_X["landing"] - 85
    width = COLUMN_X["gold"] + 85 - left
    return (f'<rect x="{left}" y="186" width="{width}" height="410" rx="18" fill="none" '
            f'stroke="{palette["card_border"]}" stroke-width="1.2"/>'
            f'<text x="{left + 18}" y="212" font-size="13" font-weight="700" '
            f'letter-spacing="1" fill="{palette["text"]}">ALMACENAMIENTO Y TRANSFORMACIÓN</text>')


def medallion_color(key, palette):
    """Ink of a medallion band: the bronze and gold layer colours, a cool silver."""
    return SILVER_INK[palette["base"]] if key == "silver" else LAYER_COLORS[key]


def build_medallion_label(x, y, key, detail, palette, anchor="middle"):
    """«SILVER · Transformación dbt»: the medallion name in its ink, small and spaced,
    then what the band holds; it explains the medallion layer on hover."""
    color = medallion_color(key, palette)
    text = (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="11" letter-spacing="1.3">'
            f'<tspan font-weight="700" fill="{color}">{key.upper()}</tspan>'
            f'<tspan font-weight="600" letter-spacing=".3" fill="{palette["text"]}"> · '
            f'{html.escape(detail)}</tspan></text>')
    return add_tech_tooltip(text, tech_glossary.LABEL_KEYS[key.upper()])


def build_medallion_band(left, top, width, height, key, palette, radius=12):
    """A sober container: thin rounded outline and a very faint tint of its medallion."""
    color = medallion_color(key, palette)
    dark = palette["base"] == charts.BASE_DARK
    return (f'<rect class="medallion-band medallion-{key}" x="{left}" y="{top}" width="{width}" '
            f'height="{height}" rx="{radius}" fill="{color}" fill-opacity="{.05 if dark else .035}" '
            f'stroke="{color}" stroke-opacity="{.42 if dark else .5}" stroke-width="1"/>')


def build_medallion_bands(palette):
    """Bronze, silver and gold as background containers of the main row, left to right,
    each named at its top: the medallion reading of the transformation steps."""
    parts = []
    for key, _, _, detail in MEDALLION:
        left, right = MEDALLION_SPAN[key]
        parts.append(build_medallion_band(left, MEDALLION_TOP, right - left,
                                          MEDALLION_BOTTOM - MEDALLION_TOP, key, palette))
        parts.append(build_medallion_label((left + right) / 2, MEDALLION_TOP + 14, key, detail,
                                           palette))
    return "".join(parts)


def build_dbt_frame(figures, palette):
    """The three dbt steps named by a thin bracket above them, staging to marts: the part
    of the journey that the «Linaje dbt» view opens model by model. It straddles the
    silver and gold bands, as dbt builds both."""
    color = LAYER_COLORS["processing"]
    left = MEDALLION_SPAN["silver"][0]
    right = COLUMN_X["marts"] + 74
    middle = (left + right) / 2
    detail = figures.get("dbt", "")
    label = "dbt CORE · staging → intermedio → marts" + (f" · {detail}" if detail else "")
    half = len(label) * 3.35 + 10  # half the label, bold 11, and a little air
    line_y = MEDALLION_TOP - 16
    stroke = f'stroke="{color}" stroke-opacity=".75" stroke-width="1.2" fill="none"'
    return (f'<path d="M{left} {MEDALLION_TOP - 4} V{line_y} H{middle - half}" {stroke}/>'
            f'<path d="M{middle + half} {line_y} H{right} V{MEDALLION_TOP - 4}" {stroke}/>'
            + add_tech_tooltip(f'<text x="{middle}" y="{line_y + 4}" text-anchor="middle" font-size="11" '
                               f'font-weight="700" letter-spacing=".5" fill="{color}">{html.escape(label)}</text>',
                               "dbt"))


def build_journey_svg(states, figures, mode, animate_flow=None):
    """The whole live diagram, in the colors of the active mode.

    states holds the state of: sources, download, etl, load, panel, report,
    workflow and tests. figures holds the short texts shown under the steps.
    """
    palette = charts.get_palette(mode)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
             f'width="{WIDTH}" height="{HEIGHT}" role="img" '
             f'aria-label="Recorrido de los datos de ODEPA al panel" '
             f'font-family="{charts.CHART_FONT}">',
             build_style((states.get("workflow") == control.RUN_IN_PROGRESS if animate_flow is None else animate_flow)),
             build_column_headers(), build_container(palette), build_medallion_bands(palette),
             build_dbt_frame(figures, palette),
             build_orchestration(states, figures, palette),
             build_links(palette, (states.get("workflow") == control.RUN_IN_PROGRESS if animate_flow is None else animate_flow)),
             build_quarantine(figures, palette), build_main_nodes(states, figures, palette),
             build_consumption_nodes(states, figures, palette),
             build_observability(states, figures, palette), "</svg>"]
    return "".join(parts)


def list_vertical_steps(states, figures):
    """(layer header, layer, icon, title, lines, state, chip to the next step), in order.

    The two sources come first: ODEPA joins the INE link through a trunk on the
    left (build_vertical_journey_svg), so the INE row carries the chip.
    """
    dbt_state = read_dbt_state(states)
    return [
        ("FUENTES", "sources", draw_file_icon, "ODEPA mayorista y consumidor",
         ["HTTPS · CSV · sin API", figures["source_years"]], states["sources"], None),
        (None, "sources", draw_file_icon, "INE · IPC",
         ["HTTPS · CSV · sin API", "alimentos · mensual"], None, "HTTPS · CSV"),
        ("INGESTA", "ingestion", draw_python_icon, "Descarga ODEPA e INE",
         ["Python · requests", figures["last_run"]], states["download"], "manifest"),
        ("ATERRIZAJE", "ingestion", draw_sqlite_icon, "SQLite · raw.db",
         ["zona de aterrizaje · solo ODEPA", "hash por archivo"], None, "raw_*"),
        ("BRONZE", "bronze", draw_parquet_icon, "Parquet · bronce",
         ["Python · pyarrow", "texto, por fuente y año"], None, "sources"),
        ("STAGING", "processing", draw_dbt_icon, "Staging",
         ["dbt · SQL", figures["rows_read"]], dbt_state, "stg_*"),
        ("INTERMEDIO", "processing", draw_dbt_icon, "Intermedio",
         ["dbt · SQL", f"Rechazos {figures['rows_rejected']}"], dbt_state, "int_*"),
        ("MARTS", "quality", draw_shield_icon, "Marts y pruebas",
         ["dbt · SQL", "estrella · IPC · pruebas"], states["load"], "OK"),
        ("SERVING", "gold", draw_duckdb_icon, "datos.duckdb",
         [figures["weekly_prices"], figures["latest_week"]], states["load"], None),
    ]


def build_vertical_node(y, header, layer, draw_icon, title, lines, palette, state):
    """One step of the vertical diagram: tile on the left, text on its right."""
    x = VERTICAL_TILE_X
    half = TILE_SIZE / 2
    color = LAYER_COLORS[layer]
    parts = [f'<rect x="{x-half}" y="{y-half}" width="{TILE_SIZE}" height="{TILE_SIZE}" '
             f'rx="16" fill="{palette["card"]}" stroke="{color}" stroke-width="1.5"/>',
             draw_tile_icon(draw_icon, x, y, color)]
    text_x = x + half + 18
    if header:
        parts.append(f'<text x="{text_x}" y="{y-20}" font-size="12" font-weight="700" '
                     f'letter-spacing="1" fill="{color}">{header}</text>')
    parts.append(f'<text x="{text_x}" y="{y}" font-size="16" font-weight="700" '
                 f'fill="{palette["strong_text"]}">{html.escape(title)}</text>')
    # A node of PIPELINE_STACK gets its technology pills where the first caption
    # line would sit (D-103): same footprint, its real tools made explicit.
    stack = visible_stack(title, draw_icon)
    shown_lines = lines[1:2] if stack else lines[:2]
    if stack:
        parts.append(build_stack_row(text_x, y + 12, stack, palette, align="left"))
    for line_number, line in enumerate(shown_lines):
        line_color = (LAYER_COLORS["quarantine"] if line.startswith(("inválidas", "Rechazos"))
                      else palette["text"])
        base_y = y + 36 if stack else y + 19
        parts.append(f'<text x="{text_x}" y="{base_y+line_number*17}" font-size="13" '
                     f'fill="{line_color}">{html.escape(line)}</text>')
    if has_real_state(state):
        pulse = ' class="journey-running"' if state == control.RUN_IN_PROGRESS else ""
        parts.append(f'<circle{pulse} cx="{x+half-4}" cy="{y-half+4}" r="7" '
                     f'fill="{STATE_COLORS[state]}" '
                     f'stroke="{palette["card"]}" stroke-width="2.5"/>')
    return add_tooltip("".join(parts), TOOLTIPS.get(title))


def build_vertical_link(y1, y2, color, palette, chip_text, moving_dot):
    """Straight link down from one tile to the next, with its chip on the line."""
    x = VERTICAL_TILE_X
    path = f"M{x} {y1} V{y2}"
    parts = [f'<path d="{path}" stroke="{color}" stroke-width="1.6" opacity="0.85"/>']
    if moving_dot:
        parts.append(f'<circle class="journey-flow" r="3.5" fill="{color}"><animateMotion dur="1.6s" '
                     f'repeatCount="indefinite" path="{path}"/></circle>')
    if chip_text:
        parts.append(build_chip(x, (y1 + y2) / 2, chip_text, color, palette))
    return "".join(parts)


def build_vertical_band(y, title, items, palette):
    """A band as a short list: a title and one line per item (dot only if real)."""
    parts = [f'<text x="16" y="{y}" font-size="12" font-weight="700" letter-spacing="1" '
             f'fill="{palette["text"]}">{html.escape(title)}</text>']
    for position, (item_title, detail, state) in enumerate(items):
        parts.append(build_band_item(28, y + 26 + position * 40, item_title, detail, palette,
                                     state))
    return "".join(parts)


def build_vertical_medallion(first_y, headers, palette):
    """The bronze, silver and gold bands behind their rows, each named at its top right;
    the chips between two bands sit in the gap between them."""
    row_of = {header: first_y + index * VERTICAL_ROW for index, header in enumerate(headers) if header}
    column_header = {column: title for column, title, _, _ in COLUMN_HEADERS}
    parts = []
    for key, first, last, detail in MEDALLION:
        top = row_of[column_header[first]] - VERTICAL_BAND_ABOVE
        bottom = row_of[column_header[last]] + VERTICAL_BAND_BELOW
        parts.append(build_medallion_band(8, top, VERTICAL_WIDTH - 16, bottom - top, key, palette))
        parts.append(build_medallion_label(VERTICAL_WIDTH - 20, top + 15, key, detail, palette,
                                           anchor="end"))
    return "".join(parts)


def build_vertical_journey_svg(states, figures, mode, animate_flow=None):
    """The whole live diagram from top to bottom, readable on a phone.

    It shows the same steps, real states and figures as build_journey_svg.
    """
    palette = charts.get_palette(mode)
    is_running = (states.get("workflow") == control.RUN_IN_PROGRESS
                  if animate_flow is None else animate_flow)
    half = TILE_SIZE / 2
    orchestration = [("GitHub Actions", f"cada martes · próxima {figures['next_run']}",
                      states["workflow"]),
                     ("Pruebas automáticas", "pytest · bloquea el guardado", states["tests"])]
    parts = [build_vertical_band(24, "ORQUESTACIÓN — da las órdenes", orchestration, palette)]
    y = VERTICAL_FIRST_Y
    # ODEPA, the first source, joins the INE link below the INE tile through a
    # trunk on the left: both sources feed the ingestion step.
    trunk_x = VERTICAL_TILE_X - half - 12
    junction_y = y + VERTICAL_ROW + half + 6
    parts.append(f'<path d="M{VERTICAL_TILE_X - half} {y} H{trunk_x} V{junction_y} '
                 f'H{VERTICAL_TILE_X}" fill="none" stroke="{LAYER_COLORS["sources"]}" '
                 f'stroke-width="1.6" opacity="0.85"/>')
    steps = list_vertical_steps(states, figures)
    parts.append(build_vertical_medallion(y, [step[0] for step in steps], palette))
    for header, layer, draw_icon, title, lines, state, chip_text in steps:
        parts.append(build_vertical_node(y, header, layer, draw_icon, title, lines, palette,
                                         state))
        if chip_text:
            parts.append(build_vertical_link(y + half, y + VERTICAL_ROW - half,
                                             LAYER_COLORS[layer], palette, chip_text,
                                             is_running))
        y += VERTICAL_ROW
    # Consumption: three uses of datos.duckdb, joined to it by one trunk on the left.
    gold_bottom = y - VERTICAL_ROW + half
    consumption = [(draw_streamlit_icon, "Panel Streamlit", ["esta página", figures["panel_time"]],
                    states["panel"]),
                   (draw_github_icon, "Informe semanal", ["GitHub Issue · Markdown",
                                                          "alertas y estado"],
                    states["report"]),
                   (draw_code_icon, "Consultas SQL", ["DuckDB · queries.sql", "bi/queries.sql"],
                    None)]
    last_y = y + (len(consumption) - 1) * VERTICAL_ROW
    parts.append(f'<path d="M{VERTICAL_TILE_X} {gold_bottom} V{gold_bottom + 22} '
                 f'H{trunk_x} V{last_y}" fill="none" stroke="{LAYER_COLORS["gold"]}" '
                 f'stroke-width="1.6" opacity="0.85"/>')
    for position, (draw_icon, title, lines, state) in enumerate(consumption):
        row_y = y + position * VERTICAL_ROW
        parts.append(f'<path d="M{trunk_x} {row_y} H{VERTICAL_TILE_X - half}" '
                     f'stroke="{LAYER_COLORS["gold"]}" stroke-width="1.6" opacity="0.85"/>')
        parts.append(build_vertical_node(row_y, "CONSUMO" if position == 0 else None,
                                         "consumption", draw_icon, title, lines, palette,
                                         state))
    observability = [("etl_run", "DuckDB · una fila por carga", states.get("etl_run")),
                     ("dbt_result", "DuckDB · linaje y pruebas", None),
                     ("Centro de control", "Streamlit · historial", None)]
    band_y = last_y + half + 44
    height = band_y + 26 + (len(observability) - 1) * 40 + 36
    parts.append(build_vertical_band(band_y, "OBSERVABILIDAD — qué pasó",
                                     observability, palette))
    return "".join([f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'viewBox="0 0 {VERTICAL_WIDTH} {height}" role="img" '
                    f'aria-label="Recorrido de los datos de ODEPA al panel" '
                    f'font-family="{charts.CHART_FONT}">', build_style(is_running), *parts,
                    "</svg>"])
# endregion


# Glossary entry of the brand logo each component shows (what that logo stands for here).
COMPONENT_LOGO_KEYS = {"Job semanal.yml": "github_actions", "Caché de Actions": "actions_cache",
                       "Issues": "github_issues", "Repositorio": "git", "Pruebas (CI)": "pytest",
                       "App Streamlit": "streamlit"}


# endregion


