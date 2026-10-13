"""Live "data journey" diagram: how the data travels from ODEPA to the dashboard.

Layers from left to right (sources, ingestion, bronze, cleaning, rules, quality,
gold, consumption), an orchestration band on top, observability at the bottom,
and a quarantine for rejected rows. Each step carries a status dot with its real
state (latest pipeline run and current database); dots travel along the arrows
and the dashed links move only while a run is in progress: every animation shows
real data (D-043, D-051). The rest of the time the diagram stays still.
The result is a standalone SVG text, shown with st.image (st.html removes SVG).
Only steps that really exist in this project are drawn.
"""
import html

from bi import brand_icons, charts, control

# region Constants
STATE_UNKNOWN = "unknown"
STATE_SKIPPED = "skipped"
STATE_COLORS = {
    control.RUN_OK: "#22b35a", control.RUN_FAILED: "#e66767",
    control.RUN_IN_PROGRESS: "#5b9cf0", STATE_SKIPPED: "#8a8984", STATE_UNKNOWN: "#8a8984",
}
STATE_LABELS = {
    control.RUN_OK: "OK", control.RUN_FAILED: "Falla", control.RUN_IN_PROGRESS: "En curso",
    STATE_SKIPPED: "Omitido", STATE_UNKNOWN: "Sin datos",
}
# One color per layer, the same in both modes.
LAYER_COLORS = {"sources": "#22b35a", "ingestion": "#3987e5", "bronze": "#c98500",
                "processing": "#9085e9", "quality": "#d55181", "gold": "#eda100",
                "consumption": "#199e70", "quarantine": "#e66767",
                "orchestration": "#c98500"}

WIDTH = 1560
HEIGHT = 720
MAIN_ROW_Y = 330
TILE_SIZE = 64
# Center x of each layer column.
COLUMN_X = {"sources": 110, "ingestion": 300, "bronze": 490, "cleaning": 680,
            "rules": 870, "quality": 1060, "gold": 1250, "consumption": 1440}
COLUMN_HEADERS = [
    ("sources", "FUENTES", "dónde nace el dato", "sources"),
    ("ingestion", "INGESTA", "descarga y control", "ingestion"),
    ("bronze", "BRONCE", "copia exacta", "bronze"),
    ("cleaning", "LIMPIEZA", "tipos y validación", "processing"),
    ("rules", "REGLAS", "unidades y semanas", "processing"),
    ("quality", "CALIDAD", "controles de carga", "quality"),
    ("gold", "ORO", "listo para analizar", "gold"),
    ("consumption", "CONSUMO", "decisiones", "consumption"),
]
# The small version shown at the top of the project page.
MINI_WIDTH = 1000
MINI_HEIGHT = 160
MINI_ROW_Y = 64
MINI_COLUMN_X = [100, 300, 500, 700, 900]
# The vertical version, for narrow screens: one step per row.
VERTICAL_WIDTH = 400
VERTICAL_TILE_X = 64
VERTICAL_FIRST_Y = 170
VERTICAL_ROW = 112
# The infrastructure: one frame per platform with its components inside, and
# each connection labelled with how the two pieces talk (D-054).
PLATFORM_WIDTH = 1420
PLATFORM_HEIGHT = 700
# The frames start below this line: the space above it is not drawn.
PLATFORM_TOP = 80
COMPONENT_WIDTH = 250
COMPONENT_HEIGHT = 90
# Center x of the three component columns inside GitHub, and center y of the rows.
GITHUB_COLUMN_X = [560, 900, 1240]
TOP_ROW_Y = 185
MIDDLE_ROW_Y = 380
BOTTOM_ROW_Y = 605
LEFT_COLUMN_X = 200
# (x, y, width, height, title, subtitle, layer) of each platform frame.
PLATFORMS = [
    (40, 95, 320, 155, "ODEPA", "fuente pública", "sources"),
    (40, 305, 320, 140, "TU COMPUTADOR", "desarrollo", "ingestion"),
    (420, 95, 965, 350, "GITHUB", "código, automatización e informes", "processing"),
    (40, 500, 720, 180, "STREAMLIT COMMUNITY CLOUD", "publicación del panel", "quality"),
    (1110, 500, 275, 180, "USUARIOS", "quién lo usa", "consumption"),
]
# Explanation shown on hover over each piece: what it does, with its acronyms.
TOOLTIPS = {
    "ODEPA mayorista": "Precios diarios de los mercados mayoristas, publicados por ODEPA "
                       "(Oficina de Estudios y Políticas Agrarias) en archivos CSV.",
    "ODEPA consumidor": "Precios semanales al consumidor por región y canal, en archivos CSV "
                        "de ODEPA.",
    "ODEPA mayorista y consumidor": "Las dos fuentes de ODEPA (Oficina de Estudios y Políticas "
                                    "Agrarias): precios mayoristas diarios y precios al "
                                    "consumidor semanales, en archivos CSV.",
    "Agente de descarga": "agent.py descarga los CSV, reintenta si falla y revisa el "
                          "encabezado antes de guardar nada.",
    "raw.db": "Capa bronce: los archivos tal como llegan, con un hash por archivo para saber "
              "si cambiaron. No se sube al repositorio.",
    "Limpieza": "Convierte tipos y textos y rechaza las filas inválidas con su motivo (RN-11; "
                "RN = regla de negocio).",
    "Reglas de negocio": "Lleva los precios a kilo o unidad, los agrupa por semana y marca los "
                         "atípicos (RN-03 a RN-12).",
    "Controles de carga": "Revisa filas, semanas, regiones y canales: si algo no cuadra, no se "
                          "guarda nada.",
    "datos.db": "Capa oro: el data warehouse SQLite con el modelo estrella que leen el panel, "
                "el informe y las consultas.",
    "Rechazos": "Tabla rejection: cada fila descartada, tal como venía, con su motivo.",
    "Panel Streamlit": "Este panel: lee datos.db en modo solo lectura.",
    "Informe semanal": "Issue de GitHub con el estado de la carga y las alertas de la semana.",
    "Consultas SQL": "SQL (lenguaje de consultas estructurado): una consulta por indicador, en "
                     "bi/queries.sql.",
    "GitHub Actions": "Servicio de GitHub que ejecuta el job semanal cada martes, sin "
                      "intervención.",
    "Pruebas automáticas": "pytest corre contra la base nueva: si una prueba falla, no se "
                           "guarda nada.",
    "Secretos": "Claves que no están en el código: el token de GitHub y la clave del botón "
                "«Ejecutar ahora».",
    "etl_run": "Tabla con una fila por carga. ETL = extraer, transformar y cargar.",
    "Logs del agente": "Un archivo de texto por ejecución con lo que hizo la descarga.",
    "Correo de GitHub": "GitHub avisa por correo a la autora si el job semanal falla.",
    "Centro de control": "Página del panel con el historial de ejecuciones en vivo.",
    "Datos abiertos": "Portal de datos abiertos de ODEPA: un CSV por año y fuente, descargado "
                      "por HTTPS.",
    "VS Code · Claude Code": "Donde se escribe el código: el editor VS Code y el asistente "
                             "Claude Code. pytest corre antes de cada commit.",
    "Job semanal.yml": "Workflow de GitHub Actions: cada martes descarga, ejecuta el ETL, "
                       "prueba, guarda datos.db y publica el informe.",
    "Caché de Actions": "Guarda los CSV de los años cerrados para no descargarlos cada semana "
                        "(D-047).",
    "Issues": "Donde se publica el informe semanal, uno por ejecución.",
    "Repositorio": "La rama main en GitHub: el código y datos.db. Es la única fuente de la "
                   "verdad.",
    "Pruebas (CI)": "CI = integración continua: pruebas.yml corre pytest en cada push y avisa "
                    "si algo se rompe.",
    "Permisos del job": "Mínimo privilegio: el job solo puede escribir contenido (el commit de "
                        "la base) y crear issues.",
    "App Streamlit": "El panel publicado en Streamlit Community Cloud; abre datos.db en solo "
                     "lectura.",
    "Visitantes": "Quien abre el enlace público del panel desde su navegador.",
    "ODEPA": "Las dos fuentes de precios de ODEPA, en archivos CSV.",
    "Ingesta": "La descarga de los archivos, con reintentos y validación.",
    "ETL": "Extraer, transformar y cargar: limpieza, reglas y controles.",
    "Data warehouse": "datos.db: la base lista para analizar.",
    "Panel": "Este panel, con los datos de la última carga.",
}
# Explanation of what travels through each link.
CHIP_TOOLTIPS = {
    "CSV": "CSV: archivo de texto con valores separados por comas.",
    "HTTPS · CSV": "HTTPS: conexión web cifrada; por ella llegan los archivos CSV.",
    "manifest": "manifest.json: registro de cada archivo descargado, con su hash.",
    "raw_*": "Tablas crudas raw_wholesale y raw_consumer, en raw.db.",
    "válidas": "Filas que pasaron la validación.",
    "inválidas": "Filas rechazadas: van a la tabla rejection con su motivo.",
    "plata": "Capa plata: datos limpios, con las reglas de negocio aplicadas.",
    "OK": "La carga pasó todos los controles y se guarda.",
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


def draw_download_icon(x, y, color):
    """An arrow going down into a tray."""
    return (f'<path d="M{x} {y-16} v20 M{x-8} {y-3} l8 8 l8 -8 M{x-15} {y+6} v8 h30 v-8" '
            f'fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round" '
            f'stroke-linejoin="round"/>')


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


def draw_warning_icon(x, y, color):
    """A triangle with an exclamation mark: rejected rows."""
    return (f'<path d="M{x} {y-15} l16 28 h-32 z" fill="none" stroke="{color}" '
            f'stroke-width="2.2" stroke-linejoin="round"/>'
            f'<path d="M{x} {y-5} v9" stroke="{color}" stroke-width="2.4" '
            f'stroke-linecap="round"/><circle cx="{x}" cy="{y+9}" r="1.6" fill="{color}"/>')


def draw_laptop_icon(x, y, color):
    """A laptop: the computer where the code is written."""
    return (f'<rect x="{x-14}" y="{y-13}" width="28" height="19" rx="2" fill="none" '
            f'stroke="{color}" stroke-width="2.2"/>'
            f'<path d="M{x-19} {y+11} h38" stroke="{color}" stroke-width="2.4" '
            f'stroke-linecap="round"/>')


def draw_branch_icon(x, y, color):
    """Two branches joined: a git repository."""
    return (f'<circle cx="{x-8}" cy="{y-12}" r="4" fill="none" stroke="{color}" '
            f'stroke-width="2.2"/><circle cx="{x-8}" cy="{y+12}" r="4" fill="none" '
            f'stroke="{color}" stroke-width="2.2"/><circle cx="{x+9}" cy="{y-6}" r="4" '
            f'fill="none" stroke="{color}" stroke-width="2.2"/>'
            f'<path d="M{x-8} {y-8} v16 M{x+9} {y-2} c0 8 -17 4 -17 10" fill="none" '
            f'stroke="{color}" stroke-width="2.2"/>')


def draw_clock_icon(x, y, color):
    """A clock: the job that runs on a schedule."""
    return (f'<circle cx="{x}" cy="{y}" r="15" fill="none" stroke="{color}" '
            f'stroke-width="2.2"/><path d="M{x} {y-9} v9 l7 5" fill="none" '
            f'stroke="{color}" stroke-width="2.4" stroke-linecap="round" '
            f'stroke-linejoin="round"/>')


def draw_cloud_icon(x, y, color):
    """A cloud: the service that hosts the dashboard."""
    return (f'<path d="M{x-12} {y+10} a8 8 0 0 1 -1 -16 a11 11 0 0 1 21 -3 '
            f'a8 8 0 0 1 4 19 z" fill="none" stroke="{color}" stroke-width="2.2" '
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
                     f'<text x="{x}" y="60" text-anchor="middle" font-size="13" '
                     f'fill="#8a8984">{subtitle}</text>')
    return "".join(parts)


def build_node(x, y, layer, draw_icon, title, lines, palette, state=None):
    """Icon tile, title, up to two lines of detail and, when known, a status dot."""
    color = LAYER_COLORS[layer]
    half = TILE_SIZE / 2
    parts = [f'<rect x="{x-half}" y="{y-half}" width="{TILE_SIZE}" height="{TILE_SIZE}" '
             f'rx="16" fill="{palette["card"]}" stroke="{color}" stroke-width="1.5"/>',
             draw_icon(x, y, color),
             f'<text x="{x}" y="{y+half+22}" text-anchor="middle" font-size="16" '
             f'font-weight="700" fill="{palette["strong_text"]}">{html.escape(title)}</text>']
    for line_number, line in enumerate(lines[:2]):
        parts.append(f'<text x="{x}" y="{y+half+42+line_number*17}" text-anchor="middle" '
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
    return add_tooltip(
        f'<rect x="{x-width/2}" y="{y-11}" width="{width}" height="22" rx="6" '
        f'fill="{palette["card"]}" stroke="{color}" stroke-width="1"/>'
        f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="12" font-weight="700" '
        f'font-family="monospace" fill="{color}">{html.escape(text)}</text>',
        CHIP_TOOLTIPS.get(text))


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
    return add_tooltip(f'{dot}<text x="{x+12}" y="{y}" font-size="14" font-weight="700" '
                       f'fill="{palette["strong_text"]}">{html.escape(title)}</text>'
                       f'<text x="{x+12}" y="{y+18}" font-size="13" '
                       f'fill="{palette["text"]}">{html.escape(detail)}</text>',
                       TOOLTIPS.get(title))
# endregion


# region Diagram
def build_main_nodes(states, figures, palette):
    """The steps of the data, from the ODEPA files to the indicator database."""
    column = COLUMN_X
    return "".join([
        build_node(column["sources"], 250, "sources", draw_file_icon, "ODEPA mayorista",
                   ["precios diarios", figures["source_years"]], palette, states["sources"]),
        build_node(column["sources"], 420, "sources", draw_file_icon, "ODEPA consumidor",
                   ["precios semanales", figures["source_years"]], palette, states["sources"]),
        build_node(column["ingestion"], MAIN_ROW_Y, "ingestion", draw_download_icon,
                   "Agente de descarga", ["agent.py · reintentos", figures["last_run"]],
                   palette, states["download"]),
        build_node(column["bronze"], MAIN_ROW_Y, "bronze", draw_database_icon, "raw.db",
                   ["tal como viene", "hash por archivo"], palette),
        build_node(column["cleaning"], MAIN_ROW_Y, "processing", draw_funnel_icon,
                   "Limpieza", [figures["rows_read"], "tipos · textos · RN-11"],
                   palette, states["etl"]),
        build_node(column["rules"], MAIN_ROW_Y, "processing", draw_sliders_icon,
                   "Reglas de negocio", ["unidades · semanas", "atípicos RN-12"],
                   palette, states["etl"]),
        build_node(column["quality"], MAIN_ROW_Y, "quality", draw_shield_icon,
                   "Controles de carga", ["filas · semanas", "regiones · canales"],
                   palette, states["load"]),
        build_node(column["gold"], MAIN_ROW_Y, "gold", draw_database_icon, "datos.db",
                   [figures["weekly_prices"], figures["latest_week"]], palette, states["load"]),
    ])


def build_consumption_nodes(states, figures, palette):
    """Where the data is used: dashboard, weekly report and SQL queries."""
    x = COLUMN_X["consumption"]
    return "".join([
        build_node(x, 210, "consumption", draw_chart_icon, "Panel Streamlit",
                   ["esta página", figures["panel_time"]], palette, states["panel"]),
        build_node(x, 360, "consumption", draw_report_icon, "Informe semanal",
                   ["issue en GitHub", "alertas y estado"], palette, states["report"]),
        build_node(x, 510, "consumption", draw_code_icon, "Consultas SQL",
                   ["queries.sql", "una por indicador"], palette),
    ])


def build_links(palette, is_running):
    """Links between steps, each with the kind of data that travels through it.

    Dots travel along them only while a run is in progress.
    """
    column = COLUMN_X
    half = TILE_SIZE / 2
    gray = palette["text"]

    def right_of(name, y=MAIN_ROW_Y):
        return (column[name] + half, y)

    def left_of(name, y=MAIN_ROW_Y):
        return (column[name] - half, y)

    return "".join([
        build_link(right_of("sources", 250), left_of("ingestion"), LAYER_COLORS["sources"],
                   palette, "CSV", moving_dot=is_running),
        build_link(right_of("sources", 420), left_of("ingestion"), LAYER_COLORS["sources"],
                   palette, "CSV", moving_dot=is_running),
        build_link(right_of("ingestion"), left_of("bronze"), LAYER_COLORS["ingestion"],
                   palette, "manifest", moving_dot=is_running),
        build_link(right_of("bronze"), left_of("cleaning"), LAYER_COLORS["bronze"],
                   palette, "raw_*", moving_dot=is_running),
        build_link(right_of("cleaning"), left_of("rules"), LAYER_COLORS["processing"],
                   palette, "válidas", moving_dot=is_running),
        build_link(right_of("rules"), left_of("quality"), LAYER_COLORS["processing"],
                   palette, "plata", moving_dot=is_running),
        build_link(right_of("quality"), left_of("gold"), LAYER_COLORS["quality"],
                   palette, "OK", moving_dot=is_running),
        build_link(right_of("gold"), left_of("consumption", 210), LAYER_COLORS["gold"],
                   palette, "SQL", moving_dot=is_running),
        build_link(right_of("gold"), left_of("consumption", 360), LAYER_COLORS["gold"],
                   palette, "MD", moving_dot=is_running),
        build_link(right_of("gold"), left_of("consumption", 510), gray, palette,
                   moving_dot=False),
    ])


def build_quarantine(figures, palette):
    """Rejected rows go to the rejection table with their reason (RN-11)."""
    x = (COLUMN_X["cleaning"] + COLUMN_X["rules"]) / 2
    y = 520
    start = (COLUMN_X["cleaning"] + TILE_SIZE / 2, MAIN_ROW_Y + 14)
    path = (f"M{start[0]} {start[1]} C{x} {start[1]} {x} {start[1] + 60} {x} "
            f"{y - TILE_SIZE / 2}")
    return (f'<path class="journey-dashed" d="{path}" fill="none" '
            f'stroke="{LAYER_COLORS["quarantine"]}" stroke-width="1.6"/>'
            + build_chip(x, MAIN_ROW_Y + 128, "inválidas", LAYER_COLORS["quarantine"],
                         palette)
            + build_node(x, y, "quarantine", draw_warning_icon, "Rechazos",
                         ["tabla rejection", figures["rows_rejected"]], palette))


def build_orchestration(states, figures, palette):
    """Top band: who gives the orders. It never touches the data itself."""
    left = COLUMN_X["ingestion"] - 70
    width = COLUMN_X["gold"] + 70 - left
    parts = [build_band(left, 84, width, 70,
                        "ORQUESTACIÓN — da las órdenes; no toca los datos",
                        LAYER_COLORS["orchestration"], palette),
             build_band_item(left + 30, 128, "GitHub Actions",
                             f"cada martes · próxima {figures['next_run']}", palette,
                             states["workflow"]),
             build_band_item(left + 380, 128, "Pruebas automáticas",
                             "si fallan, no se guarda nada", palette, states["tests"]),
             build_band_item(left + 720, 128, "Secretos",
                             "clave y código del botón ejecutar", palette)]
    # Orders go down to the agent; they are commands, not data.
    agent_x = COLUMN_X["ingestion"]
    parts.append(f'<path class="journey-dashed" d="M{agent_x} 154 V{MAIN_ROW_Y - 34}" '
                 f'stroke="{LAYER_COLORS["orchestration"]}" stroke-width="1.4" fill="none"/>')
    parts.append(build_chip(agent_x, 230, "EJECUTA", LAYER_COLORS["orchestration"], palette))
    return "".join(parts)


def build_observability(states, figures, palette):
    """Bottom band: how we know what happened in each run."""
    left = COLUMN_X["bronze"] - 70
    width = COLUMN_X["gold"] + 70 - left
    return (build_band(left, 618, width, 72, "OBSERVABILIDAD — cómo sabemos qué pasó",
                       palette["text"], palette)
            + build_band_item(left + 30, 662, "etl_run", "una línea por carga", palette,
                              states.get("etl_run"))
            + build_band_item(left + 220, 662, "Logs del agente", "un archivo por ejecución",
                              palette)
            + build_band_item(left + 470, 662, "Correo de GitHub", "si el job semanal falla",
                              palette)
            + build_band_item(left + 690, 662, "Centro de control", "historial en vivo",
                              palette))


def build_container(palette):
    """Area that groups the transformation and storage steps."""
    left = COLUMN_X["bronze"] - 85
    width = COLUMN_X["gold"] + 85 - left
    return (f'<rect x="{left}" y="186" width="{width}" height="410" rx="18" fill="none" '
            f'stroke="{palette["card_border"]}" stroke-width="1.2"/>'
            f'<text x="{left + 18}" y="212" font-size="13" font-weight="700" '
            f'letter-spacing="1" fill="{palette["text"]}">TRANSFORMACIÓN Y ALMACENAMIENTO'
            f'</text>')


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
             build_column_headers(), build_container(palette),
             build_orchestration(states, figures, palette),
             build_links(palette, (states.get("workflow") == control.RUN_IN_PROGRESS if animate_flow is None else animate_flow)),
             build_quarantine(figures, palette), build_main_nodes(states, figures, palette),
             build_consumption_nodes(states, figures, palette),
             build_observability(states, figures, palette), "</svg>"]
    return "".join(parts)


def build_mini_journey_svg(states, figures, mode):
    """Five steps from ODEPA to the dashboard, with the real state and figures.

    states and figures are the same as for build_journey_svg.
    """
    palette = charts.get_palette(mode)
    steps = [("sources", draw_file_icon, "ODEPA", figures["source_years"], "sources"),
             ("ingestion", draw_download_icon, "Ingesta", figures["last_run"], "download"),
             ("processing", draw_funnel_icon, "ETL", figures["rows_read"], "etl"),
             ("gold", draw_database_icon, "Data warehouse", figures["weekly_prices"], "load"),
             ("consumption", draw_chart_icon, "Panel", figures["panel_time"], "panel")]
    is_running = states.get("workflow") == control.RUN_IN_PROGRESS
    half = TILE_SIZE / 2
    links = [build_link((MINI_COLUMN_X[position] + half, MINI_ROW_Y),
                        (MINI_COLUMN_X[position + 1] - half, MINI_ROW_Y),
                        LAYER_COLORS[steps[position][0]], palette, moving_dot=is_running)
             for position in range(len(steps) - 1)]
    nodes = [build_node(x, MINI_ROW_Y, layer, draw_icon, title, [figure], palette,
                        states.get(state_name))
             for x, (layer, draw_icon, title, figure, state_name) in zip(MINI_COLUMN_X, steps)]
    return "".join([f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'viewBox="0 0 {MINI_WIDTH} {MINI_HEIGHT}" role="img" '
                    f'aria-label="Estado real del pipeline, de ODEPA al panel" '
                    f'font-family="{charts.CHART_FONT}">', build_style(is_running), *links,
                    *nodes, "</svg>"])


def list_vertical_steps(states, figures):
    """(layer header, layer, icon, title, lines, state, chip to the next step), in order."""
    return [
        ("FUENTES", "sources", draw_file_icon, "ODEPA mayorista y consumidor",
         ["precios diarios y semanales", figures["source_years"]], states["sources"], "CSV"),
        ("INGESTA", "ingestion", draw_download_icon, "Agente de descarga",
         ["agent.py · reintentos", figures["last_run"]], states["download"], "manifest"),
        ("BRONCE", "bronze", draw_database_icon, "raw.db",
         ["tal como viene", "hash por archivo"], None, "raw_*"),
        ("LIMPIEZA", "processing", draw_funnel_icon, "Limpieza",
         [figures["rows_read"], f"inválidas → Rechazos · {figures['rows_rejected']}"],
         states["etl"], "válidas"),
        ("REGLAS", "processing", draw_sliders_icon, "Reglas de negocio",
         ["unidades · semanas", "atípicos RN-12"], states["etl"], "plata"),
        ("CALIDAD", "quality", draw_shield_icon, "Controles de carga",
         ["filas · semanas", "regiones · canales"], states["load"], "OK"),
        ("ORO", "gold", draw_database_icon, "datos.db",
         [figures["weekly_prices"], figures["latest_week"]], states["load"], None),
    ]


def build_vertical_node(y, header, layer, draw_icon, title, lines, palette, state):
    """One step of the vertical diagram: tile on the left, text on its right."""
    x = VERTICAL_TILE_X
    half = TILE_SIZE / 2
    color = LAYER_COLORS[layer]
    parts = [f'<rect x="{x-half}" y="{y-half}" width="{TILE_SIZE}" height="{TILE_SIZE}" '
             f'rx="16" fill="{palette["card"]}" stroke="{color}" stroke-width="1.5"/>',
             draw_icon(x, y, color)]
    text_x = x + half + 18
    if header:
        parts.append(f'<text x="{text_x}" y="{y-20}" font-size="12" font-weight="700" '
                     f'letter-spacing="1" fill="{color}">{header}</text>')
    parts.append(f'<text x="{text_x}" y="{y}" font-size="16" font-weight="700" '
                 f'fill="{palette["strong_text"]}">{html.escape(title)}</text>')
    for line_number, line in enumerate(lines[:2]):
        line_color = (LAYER_COLORS["quarantine"] if line.startswith("inválidas")
                      else palette["text"])
        parts.append(f'<text x="{text_x}" y="{y+19+line_number*17}" font-size="13" '
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
                     ("Pruebas automáticas", "si fallan, no se guarda nada", states["tests"])]
    parts = [build_vertical_band(24, "ORQUESTACIÓN — da las órdenes", orchestration, palette)]
    y = VERTICAL_FIRST_Y
    steps = list_vertical_steps(states, figures)
    for header, layer, draw_icon, title, lines, state, chip_text in steps:
        parts.append(build_vertical_node(y, header, layer, draw_icon, title, lines, palette,
                                         state))
        if chip_text:
            parts.append(build_vertical_link(y + half, y + VERTICAL_ROW - half,
                                             LAYER_COLORS[layer], palette, chip_text,
                                             is_running))
        y += VERTICAL_ROW
    # Consumption: three uses of datos.db, joined to it by one trunk on the left.
    gold_bottom = y - VERTICAL_ROW + half
    consumption = [(draw_chart_icon, "Panel Streamlit", ["esta página", figures["panel_time"]],
                    states["panel"]),
                   (draw_report_icon, "Informe semanal", ["issue en GitHub",
                                                          "alertas y estado"],
                    states["report"]),
                   (draw_code_icon, "Consultas SQL", ["queries.sql", "una por indicador"],
                    None)]
    trunk_x = VERTICAL_TILE_X - half - 12
    last_y = y + (len(consumption) - 1) * VERTICAL_ROW
    parts.append(f'<path d="M{VERTICAL_TILE_X} {gold_bottom} V{gold_bottom + 14} '
                 f'H{trunk_x} V{last_y}" fill="none" stroke="{LAYER_COLORS["gold"]}" '
                 f'stroke-width="1.6" opacity="0.85"/>')
    for position, (draw_icon, title, lines, state) in enumerate(consumption):
        row_y = y + position * VERTICAL_ROW
        parts.append(f'<path d="M{trunk_x} {row_y} H{VERTICAL_TILE_X - half}" '
                     f'stroke="{LAYER_COLORS["gold"]}" stroke-width="1.6" opacity="0.85"/>')
        parts.append(build_vertical_node(row_y, "CONSUMO" if position == 0 else None,
                                         "consumption", draw_icon, title, lines, palette,
                                         state))
    observability = [("etl_run", "una línea por carga", states.get("etl_run")),
                     ("Centro de control", "historial en vivo", None)]
    height = last_y + half + 150
    parts.append(build_vertical_band(last_y + half + 44, "OBSERVABILIDAD — qué pasó",
                                     observability, palette))
    return "".join([f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'viewBox="0 0 {VERTICAL_WIDTH} {height}" role="img" '
                    f'aria-label="Recorrido de los datos de ODEPA al panel" '
                    f'font-family="{charts.CHART_FONT}">', build_style(is_running), *parts,
                    "</svg>"])
# endregion


# region Infrastructure by platform
def build_platform_frame(x, y, width, height, title, subtitle, layer, palette):
    """A platform: a frame with its name in the layer color and what it is for."""
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="18" fill="none" '
            f'stroke="{palette["card_border"]}" stroke-width="1.4"/>'
            f'<text x="{x + 16}" y="{y + 24}" font-size="14">'
            f'<tspan font-weight="700" letter-spacing="1" fill="{LAYER_COLORS[layer]}">'
            f'{html.escape(title)}</tspan><tspan dx="10" fill="#8a8984">'
            f'{html.escape(subtitle)}</tspan></text>')


def build_component(x, y, layer, draw_icon, title, lines, palette, state=None):
    """A component inside a platform: icon on the left, name and two lines of detail,
    and a status dot only when its state is known."""
    color = LAYER_COLORS[layer]
    left, top = x - COMPONENT_WIDTH / 2, y - COMPONENT_HEIGHT / 2
    brand = {"Job semanal.yml": "github", "Caché de Actions": "github", "Issues": "github",
             "Repositorio": "git", "Pruebas (CI)": "pytest", "App Streamlit": "streamlit"}.get(title)
    icon = (brand_icons.logo(brand, left + 19, y - 15, color, 30)
            if brand else draw_icon(left + 34, y, color))
    parts = [f'<rect x="{left + 8}" y="{y - 26}" width="52" '
             f'height="52" rx="16" fill="{color}" fill-opacity=".08" '
             f'stroke="{color}" stroke-opacity=".35" stroke-width="1"/>',
             icon,
             f'<text x="{left + 66}" y="{y - 12}" font-size="15" font-weight="700" '
             f'fill="{palette["strong_text"]}">{html.escape(title)}</text>']
    for line_number, line in enumerate(lines[:2]):
        parts.append(f'<text x="{left + 66}" y="{y + 8 + line_number * 17}" font-size="12.5" '
                     f'fill="{palette["text"]}">{html.escape(line)}</text>')
    if has_real_state(state):
        pulse = ' class="journey-running"' if state == control.RUN_IN_PROGRESS else ""
        parts.append(f'<circle{pulse} cx="{left + COMPONENT_WIDTH - 4}" cy="{top + 4}" r="7" '
                     f'fill="{STATE_COLORS[state]}" stroke="{palette["card"]}" '
                     f'stroke-width="2.5"/>')
    return add_tooltip("".join(parts), TOOLTIPS.get(title))


def build_components(states, figures, palette):
    """Every running piece of the project, inside the platform that hosts it."""
    first, second, third = GITHUB_COLUMN_X
    return "".join([
        build_component(LEFT_COLUMN_X, TOP_ROW_Y, "sources", draw_file_icon,
                        "Datos abiertos", ["CSV por año · HTTPS", figures["source_years"]],
                        palette, states["sources"]),
        build_component(LEFT_COLUMN_X, MIDDLE_ROW_Y, "ingestion", draw_laptop_icon,
                        "VS Code · Claude Code", ["desarrollo y pruebas locales",
                                                  "pytest antes de cada commit"], palette),
        build_component(first, TOP_ROW_Y, "processing", draw_clock_icon, "Job semanal.yml",
                        [f"martes · próxima {figures['next_run']}", figures["week_prices"]],
                        palette, states["workflow"]),
        build_component(second, TOP_ROW_Y, "processing", draw_database_icon,
                        "Caché de Actions", ["CSV de años cerrados", "se guarda 7 días sin uso"],
                        palette),
        build_component(third, TOP_ROW_Y, "processing", draw_report_icon, "Issues",
                        ["informe semanal", "alertas y estado"], palette, states["report"]),
        build_component(first, MIDDLE_ROW_Y, "orchestration", draw_branch_icon,
                        "Repositorio", ["rama main · código",
                                        f"datos.db · {figures['database_size']}"], palette),
        build_component(second, MIDDLE_ROW_Y, "processing", draw_shield_icon, "Pruebas (CI)",
                        ["pruebas.yml · cada push", figures["test_functions"]], palette),
        build_component(third, MIDDLE_ROW_Y, "processing", draw_shield_icon,
                        "Permisos del job", ["contents: write", "issues: write"], palette),
        build_component(LEFT_COLUMN_X, BOTTOM_ROW_Y, "quality", draw_shield_icon, "Secretos",
                        ["token de GitHub y clave", "«Ejecutar ahora» → API"], palette),
        build_component(first, BOTTOM_ROW_Y, "quality", draw_cloud_icon, "App Streamlit",
                        ["bi/dashboard.py · solo lectura", figures["panel_time"]], palette,
                        states["panel"]),
        build_component(1248, BOTTOM_ROW_Y, "consumption", draw_chart_icon, "Visitantes",
                        ["navegador · enlace público", "autora: correo si falla"], palette),
    ])


def build_connection(points, color, palette, chip_text, chip_at, moving_dot=False):
    """A connection made of straight segments, with what travels through it."""
    path = "M" + " L".join(f"{x} {y}" for x, y in points)
    parts = [f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.6" '
             f'opacity="0.85"/>']
    if moving_dot:
        parts.append(f'<circle class="journey-flow" r="3.5" fill="{color}"><animateMotion dur="2.4s" '
                     f'repeatCount="indefinite" path="{path}"/></circle>')
    parts.append(build_chip(*chip_at, chip_text, color, palette))
    return "".join(parts)


def build_connections(palette, is_running):
    """How the pieces talk. Only the weekly data connections move, and only while the
    weekly job runs. None crosses another."""
    first, second, third = GITHUB_COLUMN_X
    half_width, half_height = COMPONENT_WIDTH / 2, COMPONENT_HEIGHT / 2
    left_edge = LEFT_COLUMN_X + half_width
    weekly = LAYER_COLORS["processing"]
    return "".join([
        build_connection([(left_edge, TOP_ROW_Y), (first - half_width, TOP_ROW_Y)],
                         LAYER_COLORS["sources"], palette, "HTTPS · CSV", (380, TOP_ROW_Y),
                         is_running),
        build_connection([(left_edge, MIDDLE_ROW_Y), (first - half_width, MIDDLE_ROW_Y)],
                         LAYER_COLORS["ingestion"], palette, "git push", (380, MIDDLE_ROW_Y)),
        build_connection([(first - 40, TOP_ROW_Y + half_height),
                          (first - 40, MIDDLE_ROW_Y - half_height)],
                         LAYER_COLORS["orchestration"], palette, "checkout · commit",
                         (first - 40, 300), is_running),
        build_connection([(first + half_width, TOP_ROW_Y), (second - half_width, TOP_ROW_Y)],
                         weekly, palette, "cache", (730, TOP_ROW_Y), is_running),
        build_connection([(first + 60, TOP_ROW_Y + half_height), (first + 60, 262),
                          (third, 262), (third, TOP_ROW_Y + half_height)],
                         weekly, palette, "gh issue create", (1070, 262), is_running),
        build_connection([(first + half_width, MIDDLE_ROW_Y),
                          (second - half_width, MIDDLE_ROW_Y)],
                         weekly, palette, "on: push", (730, MIDDLE_ROW_Y)),
        build_connection([(first, MIDDLE_ROW_Y + half_height),
                          (first, BOTTOM_ROW_Y - half_height)],
                         LAYER_COLORS["quality"], palette, "despliegue de main", (first, 472)),
        build_connection([(left_edge, BOTTOM_ROW_Y), (first - half_width, BOTTOM_ROW_Y)],
                         LAYER_COLORS["quality"], palette, "st.secrets", (380, BOTTOM_ROW_Y)),
        build_connection([(first + half_width, BOTTOM_ROW_Y),
                          (1248 - half_width, BOTTOM_ROW_Y)],
                         LAYER_COLORS["consumption"], palette, "HTTPS", (930, BOTTOM_ROW_Y)),
    ])


def build_devops_svg(states, figures, mode, animate_flow=None):
    """The infrastructure: each platform with its components and how they connect.

    states holds the state of: sources, workflow, report and panel. figures
    holds the texts of build_journey_svg plus database_size, test_functions and
    week_prices.
    """
    palette = charts.get_palette(mode)
    is_running = (states.get("workflow") == control.RUN_IN_PROGRESS
                  if animate_flow is None else animate_flow)
    frames = "".join(build_platform_frame(*platform, palette) for platform in PLATFORMS)
    height = PLATFORM_HEIGHT - PLATFORM_TOP
    return "".join([f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'viewBox="0 {PLATFORM_TOP} {PLATFORM_WIDTH} {height}" '
                    f'width="{PLATFORM_WIDTH}" height="{height}" role="img" '
                    f'aria-label="Arquitectura del proyecto por plataforma" '
                    f'font-family="{charts.CHART_FONT}">', build_style(is_running), frames,
                    build_connections(palette, is_running),
                    build_components(states, figures, palette), "</svg>"])
# endregion
