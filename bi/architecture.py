"""Live "data journey" diagram: how the data travels from ODEPA to the dashboard.

Layers from left to right (sources, ingestion, bronze, cleaning, rules, quality,
gold, consumption), an orchestration band on top, observability at the bottom,
and a quarantine for rejected rows. Each step carries a status dot with its real
state (latest pipeline run and current database); dots travel along the arrows
only while a run is in progress: every animation shows real data (D-043).
The result is a standalone SVG text, shown with st.image (st.html removes SVG).
Only steps that really exist in this project are drawn.
"""
import html

from bi import charts, control

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
MINI_HEIGHT = 200
MINI_ROW_Y = 64
MINI_COLUMN_X = [100, 300, 500, 700, 900]
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
# endregion


# region Pieces
def build_style():
    """Pulse for running steps; moving dashes on the dashed links."""
    return """<style>
    .journey-running { animation: journey-pulse 1.2s ease-in-out infinite; }
    .journey-dashed { stroke-dasharray: 5 5; animation: journey-dash 1.2s linear infinite; }
    @keyframes journey-pulse { 50% { opacity: 0.2; } }
    @keyframes journey-dash { to { stroke-dashoffset: -20; } }
    @media (prefers-reduced-motion: reduce) {
      .journey-running, .journey-dashed { animation: none; }
    }
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
    if state is not None:
        pulse = ' class="journey-running"' if state == control.RUN_IN_PROGRESS else ""
        parts.append(f'<circle{pulse} cx="{x+half-4}" cy="{y-half+4}" r="7" '
                     f'fill="{STATE_COLORS.get(state, STATE_COLORS[STATE_UNKNOWN])}" '
                     f'stroke="{palette["card"]}" stroke-width="2.5"/>')
    return "".join(parts)


def build_chip(x, y, text, color, palette):
    """Small label on a link that says what kind of data travels through it."""
    width = len(text) * 7.6 + 16
    return (f'<rect x="{x-width/2}" y="{y-11}" width="{width}" height="22" rx="6" '
            f'fill="{palette["card"]}" stroke="{color}" stroke-width="1"/>'
            f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="12" font-weight="700" '
            f'font-family="monospace" fill="{color}">{html.escape(text)}</text>')


def build_link(start, end, color, palette, chip_text=None, dashed=False, moving_dot=False):
    """Curved link between two points, with an optional chip and a travelling dot."""
    (x1, y1), (x2, y2) = start, end
    middle_x = (x1 + x2) / 2
    path = f"M{x1} {y1} C{middle_x} {y1} {middle_x} {y2} {x2} {y2}"
    dash_class = ' class="journey-dashed"' if dashed else ""
    parts = [f'<path{dash_class} d="{path}" fill="none" stroke="{color}" stroke-width="1.6" '
             f'opacity="0.85"/>']
    if moving_dot:
        parts.append(f'<circle r="3.5" fill="{color}"><animateMotion dur="2.4s" '
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
    """One item of a band: a status dot (or a neutral dot), a title and a detail."""
    dot_color = STATE_COLORS.get(state, palette["text"]) if state else palette["text"]
    pulse = ' class="journey-running"' if state == control.RUN_IN_PROGRESS else ""
    return (f'<circle{pulse} cx="{x}" cy="{y-4}" r="5" fill="{dot_color}"/>'
            f'<text x="{x+12}" y="{y}" font-size="14" font-weight="700" '
            f'fill="{palette["strong_text"]}">{html.escape(title)}</text>'
            f'<text x="{x+12}" y="{y+18}" font-size="13" fill="{palette["text"]}">'
            f'{html.escape(detail)}</text>')
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


def build_observability(figures, palette):
    """Bottom band: how we know what happened in each run."""
    left = COLUMN_X["bronze"] - 70
    width = COLUMN_X["gold"] + 70 - left
    return (build_band(left, 618, width, 72, "OBSERVABILIDAD — cómo sabemos qué pasó",
                       palette["text"], palette)
            + build_band_item(left + 30, 662, "etl_run", "una línea por carga", palette)
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


def build_journey_svg(states, figures, mode):
    """The whole live diagram, in the colors of the active mode.

    states holds the state of: sources, download, etl, load, panel, report,
    workflow and tests. figures holds the short texts shown under the steps.
    """
    palette = charts.get_palette(mode)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
             f'width="{WIDTH}" height="{HEIGHT}" role="img" '
             f'aria-label="Recorrido de los datos de ODEPA al panel" '
             f'font-family="{charts.CHART_FONT}">', build_style(),
             build_column_headers(), build_container(palette),
             build_orchestration(states, figures, palette),
             build_links(palette, states.get("workflow") == control.RUN_IN_PROGRESS),
             build_quarantine(figures, palette), build_main_nodes(states, figures, palette),
             build_consumption_nodes(states, figures, palette),
             build_observability(figures, palette), "</svg>"]
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
                    f'font-family="{charts.CHART_FONT}">', build_style(), *links, *nodes,
                    "</svg>"])
# endregion
