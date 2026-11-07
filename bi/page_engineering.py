"""The data engineering pages (D-541): «Pipeline y linaje» with the weekly load step by step, «Modelo de datos»,
«Consultas SQL» and its catalog, «Stack y evidencia», and the indicators (KPI), with the DevOps diagrams the documents
and the operation pages also draw.
"""

import html
import re
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from bi import (
    app_diagrams,
    architecture,
    charts,
    control,
    database_crossings,
    deployment,
    devops,
    er_diagram,
    lag,
    lineage,
    monitoring,
    project,
    queries,
    sql_explorer,
    star_model,
    storage_map,
    weeks,
    zoom,
)
from bi.app_frame import build_chip, build_repository_link_html, describe_state_source, open_card, show_page_bar
from bi.app_style import build_runs_css
from bi.constants import (
    ARCHITECTURE_HINT,
    CATALOG_FILES,
    GITHUB_CACHE_SECONDS,
    KPI_PARAMETER,
    KPI_PRESENTATION,
    LINEAGE_HINT,
    PAGE_ARCHITECTURE,
    PAGE_DIAGRAMS,
    PIPELINE_JOURNEY,
    PIPELINE_LINEAGE,
    PIPELINE_VIEW_KEY,
    QUERIES_PATH,
    SECRET_GITHUB_TOKEN,
    SECTION_KPI,
    STEPS_PROVED_BY_A_SAVED_LOAD,
)
from bi.data_access import (
    describe_loaded_years,
    format_chile_time,
    get_database_version,
    get_last_github_answers,
    get_secret,
    parse_run_start,
    read_download_manifest,
    read_indicator,
    read_indicator_for_key,
    read_latest_run,
    read_latest_week,
    read_lineage,
    read_match_coverage,
    read_pipeline_runs,
    read_price_alerts,
    to_chile_time,
)
from etl import etl

# region Constants
# D-448: the tables' roles and definitions are shared with the SAD, which draws the same model.
IPC_TABLE_DEFINITIONS, TABLE_ROLES = app_diagrams.IPC_TABLE_DEFINITIONS, app_diagrams.TABLE_ROLES


MODEL_DESCRIPTION = "Cómo se organizan los datos: las tablas y sus claves, dónde viven y cómo se cruzan las bases."


MODEL_VIEWS = ["Modelo estrella", "Entidad-relación", "Dónde viven los datos", "Cruces entre bases"]


MODEL_VIEW_KEY = "model_view"


# D-448: the storage map of the panel and of the SAD reads the same sizes.
RAW_DATABASE_SIZE_TEXT = app_diagrams.RAW_DATABASE_SIZE_TEXT


KPI_LIMITS = {
    "K1": "Compara precios; no mide ganancia ni descuenta costos. Requiere pares comparables.",
    "K2": "Solo compara canales que tienen precios del mismo producto en semanas y regiones coincidentes.",
    "K3": "La referencia usa las regiones con datos. Una región sin precio no equivale a un precio cero.",
    "K4": "Describe patrones del histórico disponible; no es una predicción de precios.",
    "K5": "El rezago es descriptivo, no prueba causalidad. Necesita historia suficiente (26 semanas).",
    "K6": "Una alerta invita a revisar un cambio poco habitual; no demuestra un error ni explica su causa.",
    "K7": "Mide cobertura del cruce entre fuentes, no garantiza la exactitud de cada precio.",
    "K8": "Cero rechazos no implica que todos los precios sean utilizables: atípicos y unidades no convertibles se registran aparte.",
}


KPI_SMART_SCOPE = {
    "K1": (
        "Porcentaje de diferencia sobre el precio mayorista.",
        "Comparar precios de compra y venta sin confundir la brecha con ganancia.",
        "Misma semana, región, producto y unidad.",
    ),
    "K2": (
        "Porcentaje de diferencia entre dos canales.",
        "Identificar qué canal ofrece un precio más alto o más bajo.",
        "Misma semana y región para ambos canales.",
    ),
    "K3": (
        "Índice base 1: 1 representa el promedio de las regiones con datos.",
        "Identificar diferencias territoriales de precio.",
        "Semana seleccionada, dentro del mismo canal.",
    ),
    "K4": (
        "Razón entre el precio semanal y el promedio anual del producto.",
        "Reconocer patrones estacionales antes de comparar precios.",
        "Semana frente al año correspondiente del histórico disponible.",
    ),
    "K5": (
        "Semanas de desfase entre 0 y 8; correlación descriptiva de las variaciones.",
        "Explorar el desfase entre precios mayoristas y del consumidor, sin afirmar causalidad.",
        "Historia mínima de 26 semanas; desfases de 0 a 8 semanas.",
    ),
    "K6": (
        "Cambios fuera del rango de ±2 desviaciones estándar de las 12 semanas anteriores.",
        "Priorizar cambios de precio que merecen revisión.",
        "Revisión semanal con una referencia móvil de 12 semanas.",
    ),
    "K7": (
        "Porcentaje de claves del consumidor que tienen comparación mayorista.",
        "Conocer el alcance de las comparaciones entre las dos fuentes.",
        "Cobertura del histórico disponible, recalculada con cada carga.",
    ),
    "K8": (
        "Porcentaje de filas rechazadas sobre las filas leídas, por motivo.",
        "Localizar problemas de validación de la carga.",
        "Cada ejecución de carga; el ejemplo identifica la ejecución utilizada.",
    ),
}


KPI_QUESTIONS = {
    "K1": "¿Cuánto más cuesta al consumidor que al mayorista?",
    "K2": "¿Cuánto difiere el precio entre canales de venta?",
    "K3": "¿Cómo se compara el precio regional con el promedio del canal?",
    "K4": "¿En qué periodos el precio supera su promedio anual?",
    "K5": "¿Con qué desfase se relacionan cambios mayoristas y del consumidor?",
    "K6": "¿Qué productos cambiaron fuera de su rango habitual?",
    "K7": "¿Qué proporción de productos permite cruzar mayorista y consumidor?",
    "K8": "¿Qué proporción de filas rechazó la última carga?",
}


# The path of a KPI, seen at once from left to right: its result, its context, its query.
# Each node sits on the top edge of its card; the line joins them at three heights (D-090).
KPI_FIGURE = re.compile(r"^([+\-−]?[\d.,]+(?:\s?%)?)\s*(.*)$")


# Card columns in % of the path width, and the height of each node on the line, in px.
KPI_COLUMNS = (30, 36, 28)


KPI_GAP = 3


KPI_NODE_HEIGHTS = (44, 128, 44)


KPI_BAND_HEIGHT = 160


KPI_ICONS_SVG = {
    "trend": '<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "bars": '<path d="M5 19V11M10 19V6M15 19v-5M20 19V9"/>',
    "code": '<path d="M8 7l-5 5 5 5M16 7l5 5-5 5"/>',
}


CATALOG_TREND_WEEKS = 26


CATALOG_BAR_COUNT = 12


PRICE_THEME = "Precios"


QUALITY_THEME = "Calidad de datos"


LIMIT_NO_DATA = "Sin dato no significa precio cero: esa región, canal o semana no se informó."
# endregion


# region «Pipeline y linaje»
@st.cache_data(ttl=GITHUB_CACHE_SECONDS, show_spinner=False)
def fetch_run_steps(run_id):
    """Steps of one run from GitHub. A failure raises, and is not kept in the cache."""
    return dict(control.list_run_steps(run_id, get_secret(SECRET_GITHUB_TOKEN)))


def read_latest_pipeline_steps():
    """(state of each step by Spanish name, latest run, why GitHub failed or "").

    Without an answer from GitHub the steps are {} and the diagram takes its
    states from the database (build_journey_states).
    """
    runs, error_text = read_pipeline_runs()
    if not runs:
        return {}, None, error_text
    last_answers = get_last_github_answers()
    try:
        steps = fetch_run_steps(runs[0]["id"])
    except Exception as error:  # GitHub unreachable or refused
        steps = last_answers.get(("steps", runs[0]["id"]), {})
        return steps, runs[0], error_text or control.describe_github_error(error)
    last_answers[("steps", runs[0]["id"])] = steps
    return steps, runs[0], error_text


def get_step_state(step_states, workflow_step):
    """State of one workflow step, by its name in semanal.yml."""
    return step_states.get(control.STEP_NAMES[workflow_step], architecture.STATE_UNKNOWN)


def read_step_state(step_states, workflow_step, load_state):
    """State of one step: from GitHub, or from the latest saved load when GitHub did
    not answer (only for the steps a saved load proves passed)."""
    if step_states:
        return get_step_state(step_states, workflow_step)
    if workflow_step in STEPS_PROVED_BY_A_SAVED_LOAD:
        return load_state
    return architecture.STATE_UNKNOWN


def build_journey_states(step_states, pipeline_run, latest_load, manifest):
    """Real state of each step: from the latest pipeline run and the current database.

    Without an answer from GitHub, the latest load saved in etl_run stands in: the
    database is only saved after download, ETL and tests passed (D-034). What the
    database cannot tell (the report, the workflow itself) stays unknown, and an
    unknown state is drawn without a dot.
    """
    load_state = control.RUN_OK if latest_load["status"] == etl.STATUS_LOADED else control.RUN_FAILED
    return {
        "sources": control.RUN_OK if manifest else architecture.STATE_UNKNOWN,
        "download": read_step_state(step_states, "Download the ODEPA files", load_state),
        "etl": read_step_state(step_states, "Run the ETL", load_state),
        "tests": read_step_state(step_states, "Run the tests against the new database", load_state),
        "report": read_step_state(step_states, "Publish the weekly report", load_state),
        "workflow": pipeline_run["state"] if pipeline_run else architecture.STATE_UNKNOWN,
        "load": load_state,
        "etl_run": load_state,
        "panel": control.RUN_OK,
    }


def build_journey_figures(manifest, pipeline_run, latest_load):
    """Short texts shown under the steps, all from real data."""
    weekly_prices = read_indicator("quality_flag_counts")["weekly_prices"].sum()
    latest_week = read_latest_week()
    loaded_at = to_chile_time(parse_run_start(latest_load["started_at"]))
    next_run = control.calculate_next_scheduled_run(datetime.now(timezone.utc))
    last_run = (
        f"última {to_chile_time(pipeline_run['started_at']):%d-%m %H:%M}" if pipeline_run else "sin datos del workflow"
    )
    return {
        "source_years": describe_loaded_years(),
        "last_run": last_run,
        "rows_read": f"{charts.format_thousands(latest_load['rows_read'])} filas leídas",
        "rows_rejected": f"{charts.format_thousands(latest_load['rows_rejected'])} filas",
        "weekly_prices": f"{charts.format_thousands(weekly_prices)} precios",
        "latest_week": f"hasta {weeks.week_range(latest_week, year=True)}",
        "panel_time": f"datos al {loaded_at:%d-%m %H:%M}",
        "next_run": f"{to_chile_time(next_run):%d-%m %H:%M}",
    }


def read_journey():
    """(states, figures, pipeline run, latest load, GitHub error) of the live diagram."""
    with st.spinner("Consultando el estado del pipeline…"):
        step_states, pipeline_run, error_text = read_latest_pipeline_steps()
    latest_load = read_latest_run()
    manifest = read_download_manifest()
    states = build_journey_states(step_states, pipeline_run, latest_load, manifest)
    figures = build_journey_figures(manifest, pipeline_run, latest_load)
    build = lineage.summarize_build(*read_lineage(get_database_version()))
    if build:
        figures["dbt"] = f"{build['models']} modelos · {build['passing']}/{build['tests']} pruebas"
    error_note = describe_state_source(error_text, step_states, latest_load) if error_text else None
    return states, figures, pipeline_run, latest_load, error_note


def build_journey_legend_html():
    """What the colored dot of each step and the moving arrows mean."""
    # D-277: the four colours and what they mean share one line, so the page fits the window.
    return (
        f'<div class="kpi-note journey-legend">{build_chip("OK", "ok")} {build_chip("En curso", "running")} '
        f'{build_chip("Falla", "failed")} {build_chip("Sin datos", "neutral")} '
        '<span>Punto de color en cada '
        'paso: estado de la última ejecución del pipeline y de la base actual. '
        'El movimiento ilustrativo, no actividad en vivo, muestra el recorrido; '
        'el estado identifica la ejecución real.</span></div>'
    )


def build_pipeline_chips(summary):
    """The four real figures of the latest load and dbt build (D-253), as chips of the page bar (D-267), each number in
    the colour of its layer in the diagram."""
    run = read_latest_run()
    number = charts.format_thousands

    def color(layer):
        return f' style="color:{architecture.LAYER_COLORS[layer]}"'

    chips = [
        (
            f'<b{color("ingestion")}>{number(run["rows_read"])}</b><small>leídas</small>',
            f'{number(run["rows_read"])} filas leídas de ODEPA en la última carga',
        ),
        (
            f'<b{color("gold")}>{number(run["rows_loaded"])}</b><small>cargadas</small>',
            f'{number(run["rows_loaded"])} filas cargadas y {number(run["rows_rejected"])} rechazadas en la última carga',
        ),
    ]
    if summary:
        chips += [
            (
                f'<b{color("processing")}>{summary["models"]}</b><small>modelos</small>',
                f'{summary["models"]} modelos dbt, de staging a marts',
            ),
            (
                f'<b{color("quality")}>{summary["passing"]}/{summary["tests"]}</b><small>pruebas</small>',
                f'{summary["passing"]} de {summary["tests"]} pruebas dbt superadas en el último build',
            ),
        ]
    else:
        chips.append(("<b>—</b><small>linaje dbt en migración</small>", "El linaje de dbt todavía no está en la base."))
    return chips


def show_pipeline_page_header(summary):
    """The page bar (D-267), with the four figures of the latest load and build."""
    show_page_bar(
        PAGE_DIAGRAMS,
        "Pipeline y linaje",
        "El recorrido de los datos, de ODEPA y el INE al panel, y el linaje de dbt con el estado de sus pruebas.",
        build_pipeline_chips(summary),
        live="etl_run y dbt_result de la última carga se leen en la Base DuckDB al abrir la página.",
    )


def show_diagrams_page(mode):
    """Pipeline y linaje (step 4 of the refonte): the figures of the latest load and
    build, then one card with a switch. It opens on the whole journey by layers
    (D-136), with its dbt stretch framed; «Linaje dbt» opens that stretch model by
    model, from the build's own manifest."""
    states, figures, pipeline_run, latest_load, error_note = read_journey()
    nodes, results = read_lineage(get_database_version())
    summary = lineage.summarize_build(nodes, results)
    show_pipeline_page_header(summary)
    st.markdown(build_runs_css(mode), unsafe_allow_html=True)
    view = st.session_state.get(PIPELINE_VIEW_KEY, PIPELINE_JOURNEY) if summary else PIPELINE_JOURNEY
    lineage_view = view == PIPELINE_LINEAGE
    title = "Dentro del tramo dbt: modelo por modelo" if lineage_view else "Recorrido completo por capas"
    # D-277: the switch sits on the card's title row, which had room for it, instead of a row of its own.
    st.markdown(
        '<style>.st-key-card_pipeline_main {position:relative;} .st-key-card_pipeline_main .st-key-pipeline_view '
        '{position:absolute; top:18px; right:24px; z-index:3; width:auto !important;} '
        '.journey-legend {margin:0 !important; line-height:1.9;} .journey-legend span {margin-left:6px;}</style>',
        unsafe_allow_html=True,
    )
    with open_card("pipeline_main", title, hint=LINEAGE_HINT if lineage_view else ARCHITECTURE_HINT):
        if summary:
            st.segmented_control(
                "Vista",
                [PIPELINE_JOURNEY, PIPELINE_LINEAGE],
                default=PIPELINE_JOURNEY,
                key=PIPELINE_VIEW_KEY,
                label_visibility="collapsed",
            )
        if lineage_view:
            st.markdown(
                zoom.build_zoom_frame_html(lineage.build_lineage_svg(nodes, results, mode), "diagram-wide"),
                unsafe_allow_html=True,
            )
            if getattr(lineage, "LINEAGE_SCRIPT", ""):
                # Hovering a model follows only its inputs and outputs; a click pins them.
                st.html(lineage.LINEAGE_SCRIPT, unsafe_allow_javascript=True)
        else:
            # Inline SVG (not an image), so each piece shows its explanation on hover.
            st.markdown(
                zoom.build_zoom_frame_html(
                    architecture.build_journey_svg(states, figures, mode, animate_flow=True), "diagram-wide"
                )
                + zoom.build_zoom_frame_html(
                    architecture.build_vertical_journey_svg(states, figures, mode, animate_flow=True), "diagram-narrow"
                ),
                unsafe_allow_html=True,
            )
            st.markdown(build_journey_legend_html(), unsafe_allow_html=True)
        st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)
        st.html(zoom.TIP_SCRIPT, unsafe_allow_javascript=True)


# endregion


# region DevOps diagrams
def build_devops_figures(figures):
    """The pipeline figures plus the size of datos.db, the test functions and the
    prices of the latest week (what the weekly job added), all read now."""
    latest_week = read_latest_week()
    week_prices = project.count_week_prices(f"{latest_week:%Y-%m-%d}")
    return dict(
        figures,
        database_size=project.describe_file_size(queries.DATABASE_FILE),
        test_functions=f"{project.count_test_functions()} funciones de prueba",
        week_prices=(f"semana {weeks.week_range(latest_week)}: {charts.format_thousands(week_prices)} precios"),
    )


def show_cicd_tab(mode):
    """How a change reaches production (D-243, D-276): CI on one row, the weekly load in four phases, and what CI and CD
    mean in the headings of their rows, so the tab fits one screen."""
    st.iframe(devops.build_cicd_html(charts.get_palette(mode)), height="content")


def show_devops_tab(mode):
    """Where each piece runs (D-132, D-136): the deployment diagram, full width, with the live state of each piece.
    Security, CI/CD, monitoring and capacity have their own views (D-249), so they are not repeated here."""
    states, figures, *_ = read_journey()
    # D-277: the drawing keeps its proportion and is never taller than what the window leaves under the tabs.
    st.markdown(
        '<style>.st-key-dep_frame iframe {display:block; margin:0 auto; '
        f'max-width:calc((100vh - 346px) * {deployment.WIDTH} / {deployment.HEIGHT});}}</style>',
        unsafe_allow_html=True,
    )
    with st.container(key="dep_frame"):
        st.iframe(
            deployment.build_deployment_html(charts.get_palette(mode), states, build_devops_figures(figures)),
            height="content",
        )


def show_monitoring_tab(mode):
    """How we know that something failed (D-249): every signal, where it is left and who reads it."""
    # D-275: the sentence that introduced it is now the drawing's own subtitle, and the frame takes its height.
    st.iframe(monitoring.build_monitoring_html(charts.get_palette(mode)), height="content")


# endregion


# region «Modelo de datos»
@st.cache_data(show_spinner=False)
def read_crossing_checks(database_version):
    """The live checks of the «Cruces entre bases» view (D-197)."""
    return database_crossings.read_checks()


@st.cache_data(show_spinner=False)
def read_er_schema(database_version):
    """Columns and DuckDB types of the tables of the entity-relationship diagram (D-195)."""
    return er_diagram.read_schema()


@st.cache_data(show_spinner=False)
def read_er_empty_units(database_version):
    """D-526: the rows of weekly_price without a unit, for the legend that tells its logical key apart."""
    return er_diagram.read_empty_units()


@st.cache_data(show_spinner=False)
def read_database_map(database_version):
    """Rows of every served table, dbt models per layer and dbt tests, for the map (D-189)."""
    counts = {name: count for name, count, _ in sql_explorer.describe_tables()}
    nodes = queries.run_sql("SELECT resource_type, layer, count(*) AS n FROM dbt_node GROUP BY ALL")
    layers = {row.layer: int(row.n) for row in nodes.itertuples() if row.resource_type == "model"}
    tests = int(nodes.loc[nodes["resource_type"] == "test", "n"].sum())
    return counts, layers, tests


format_file_size, read_store_sizes = app_diagrams.format_file_size, app_diagrams.read_store_sizes


@st.cache_data
def count_cached_table_rows(database_version, tables):
    """Rows of each table of the data warehouse, counted once per database. The list of
    tables is part of the cache key: a table added by a deploy never meets an old count."""
    return project.count_table_rows()


def read_table_row_counts():
    return count_cached_table_rows(get_database_version(), tuple(project.TABLE_NAMES + project.IPC_TABLE_NAMES))


# endregion


# region «Consultas SQL»
def build_query_address(name):
    """The query in GitHub, the source of truth of the code (D-143)."""
    path, line = find_catalog_line(name)
    return f"{project.build_github_url(path)}#L{line}"


def read_catalog_sql(name):
    """The SQL of a catalog question, as it is written in its file."""
    if name == project.MATCH_COVERAGE_QUERY_NAME:
        return etl.MATCH_COVERAGE_QUERY.strip()
    return queries.load_queries()[name].strip()


def find_catalog_line(name):
    """(file, first line) of a query, so «Abrir archivo» lands on it on GitHub."""
    path = CATALOG_FILES.get(name, QUERIES_PATH)
    marker = "MATCH_COVERAGE_QUERY = " if name in CATALOG_FILES else f"-- name: {name}\n"
    text = (project.PROJECT_DIR / path).read_text(encoding="utf-8")
    return path, text[: text.index(marker)].count("\n") + 1


# endregion


# region «Stack y evidencia»
def build_architecture_chips(row_counts):
    """The real figures of the model (D-097), as chips of the page bar (D-267); the last load is the bar's own time."""
    number = charts.format_thousands
    return [
        (
            f"<em>weekly_price</em><b>{number(row_counts['weekly_price'])}</b><small>filas</small>",
            f"weekly_price, la tabla de hechos: {number(row_counts['weekly_price'])} filas",
        ),
        (
            f"<em>Registro de cargas</em><b>{number(row_counts['etl_run'])}</b><small>cargas ·</small>"
            f"<b>{number(row_counts['rejection'])}</b><small>rechazos</small>",
            f"Registro de cargas: {number(row_counts['etl_run'])} cargas registradas en etl_run y "
            f"{number(row_counts['rejection'])} filas rechazadas en rejection",
        ),
    ]


def build_fit_frame_html(svg, css_class):
    """A diagram in a zoom frame that keeps its own proportion (--ratio), so a page can
    size it by the height the window leaves (D-232)."""
    box = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    ratio = float(box.group(1)) / float(box.group(2)) if box else 1.45
    return zoom.build_zoom_frame_html(svg, css_class, f"--ratio:{ratio:.3f}")


def build_model_frame_html(svg):
    """The entity-relation diagram in a zoom frame that keeps its proportion."""
    return build_fit_frame_html(svg, "fit-modelo")


def build_architecture_css(mode):
    palette = charts.get_palette(mode)
    return f"""<style>
    .st-key-architecture_body [data-testid="stHorizontalBlock"] {{align-items:stretch; gap:14px;}}
    .st-key-architecture_diagram {{border:1px solid {palette['card_border']}; border-radius:14px;
        background:{palette['card']}; padding:14px 20px 18px;}}
    .st-key-architecture_diagram svg {{display:block; width:100%; height:auto;}}
    /* D-503: the star takes the height the window leaves. 331 px is what sits above and below it, measured:
       the header, the chips, the tabs and a one-line phrase (219 px), the legend and the panel's padding
       (60 px), the frame's two empty blocks and the page's padding (40 px), plus 12 px of margin. Under
       1320 px of window the phrase takes two lines (19 px more). */
    .st-key-architecture_diagram svg:not(.zoom-frame svg) {{max-height:calc(100vh - 331px);}}
    @media (max-width:1320px) {{
        .st-key-architecture_diagram svg:not(.zoom-frame svg) {{max-height:calc(100vh - 350px);}}
    }}
    /* The diagram always fits the window (D-232): the viewport is as wide as the height left
       allows, by the drawing's own proportion; the zoom buttons bring it closer inside the panel. */
    .fit-modelo {{position:relative;}}
    /* D-464: 287 px, what the header, the chips, the tabs, the phrase and the zoom buttons take today (427 px left 166 px empty). */
    .fit-modelo .zoom-viewport {{max-width:calc(max(100vh - 287px, 280px) * var(--ratio, 1.45)); margin:0 auto;}}
    .fit-modelo .zoom-buttons {{position:absolute; bottom:-46px; right:0; margin:0; z-index:2;}}
    .arch-legend {{display:flex; flex-wrap:wrap; gap:8px 22px; margin:12px 4px 0; padding-top:10px;
        border-top:1px solid {palette['card_border']}; font-size:12px; line-height:1.5; color:{palette['text']};}}
    .arch-phrase {{font-size:.85rem !important; line-height:1.4 !important; color:{palette['strong_text']}; margin:0 0 6px !important;}}
    .st-key-architecture_detail, .st-key-architecture_tables {{border:1px solid {palette['card_border']};
        border-radius:14px; background:{palette['card']}; padding:12px 16px 10px;}}
    .arch-detail-head {{display:flex; align-items:baseline; gap:10px; flex-wrap:wrap;}}
    .arch-detail-head code {{font-size:1.05rem; font-weight:600; color:{palette['accent']};}}
    .arch-detail-role {{font-size:11px; padding:2px 9px; border-radius:999px;
        background:{palette['field']}; color:{palette['text']};}}
    .arch-detail-rows {{margin-left:auto; font-size:12px; color:{palette['text']};}}
    .arch-detail-text {{font-size:.86rem; line-height:1.5; color:{palette['strong_text']}; margin:7px 0 9px;}}
    .st-key-architecture_tables_list label p {{font-size:.86rem !important;}}
    </style>"""


def show_architecture_page(mode):
    """The star model as one panoramic view (D-147): every table, column, key and row
    count is in the drawing; each table explains itself on hover. No table picker,
    no SQL."""
    row_counts = read_table_row_counts()
    columns = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
    tooltips = app_diagrams.model_tooltips(row_counts)  # D-448: the same explanations as the SAD's drawing
    st.markdown(build_architecture_css(mode), unsafe_allow_html=True)
    show_page_bar(
        PAGE_ARCHITECTURE,
        PAGE_ARCHITECTURE,
        MODEL_DESCRIPTION,
        build_architecture_chips(row_counts),
        live="Las filas de weekly_price, etl_run y rejection se cuentan en la Base DuckDB al abrir la página.",
    )
    # The views of the same database, from the model to where it lives (D-189, D-236): the star, the
    # entity-relation, the storage architecture and, last, where two databases touch.
    view = (
        st.segmented_control(
            "Vista del modelo", MODEL_VIEWS, default=MODEL_VIEWS[0], key=MODEL_VIEW_KEY, label_visibility="collapsed"
        )
        or MODEL_VIEWS[0]
    )
    if view == MODEL_VIEWS[2]:
        counts, layers, tests = read_database_map(get_database_version())
        # D-236: the drawing scales to the height the window leaves: the iframe right after this marker takes it.
        st.markdown(
            '<span class="fit-donde" aria-hidden="true"></span><style>'
            '[data-testid="stElementContainer"]:has(.fit-donde) + [data-testid="stElementContainer"],'
            '[data-testid="stElementContainer"]:has(.fit-donde) + [data-testid="stElementContainer"] iframe '
            '{height:max(calc(100vh - 235px), 380px) !important; flex:none !important; min-height:0 !important;}'
            '</style>',
            unsafe_allow_html=True,
        )
        st.iframe(
            storage_map.build_map_html(charts.get_palette(mode), counts, layers, tests, read_store_sizes()), height=600
        )
        return
    if view == MODEL_VIEWS[3]:
        st.markdown(
            '<p class="arch-phrase">Cada línea es un cruce: el punto donde dos bases se tocan, con lo que las une. '
            'El número muestra si se comprobó ahora; pasa el cursor por un número para ver el detalle.</p>',
            unsafe_allow_html=True,
        )
        # D-237: the page fits the height the window leaves: the iframe right after this marker takes it.
        st.markdown(
            '<span class="fit-cruces" aria-hidden="true"></span><style>'
            '[data-testid="stElementContainer"]:has(.fit-cruces) + [data-testid="stElementContainer"],'
            '[data-testid="stElementContainer"]:has(.fit-cruces) + [data-testid="stElementContainer"] iframe '
            '{height:max(calc(100vh - 249px), 380px) !important; flex:none !important; min-height:0 !important;}'
            '</style>',
            unsafe_allow_html=True,
        )
        st.iframe(
            database_crossings.build_crossings_html(
                charts.get_palette(mode), read_crossing_checks(get_database_version())
            ),
            height=600,
        )
        return
    if view == MODEL_VIEWS[1]:
        schema = read_er_schema(get_database_version())
        st.markdown(
            '<p class="arch-phrase">El modelo en la notación clásica: cada tabla con sus columnas y tipos, sus claves y las '
            'relaciones entre ellas. Los tipos se leen de la base.</p>',
            unsafe_allow_html=True,
        )
        with st.container(key="architecture_diagram"):
            st.markdown(
                build_model_frame_html(
                    er_diagram.build_er_svg(
                        schema, row_counts, mode, tooltips, empty_units=read_er_empty_units(get_database_version())
                    )
                ),
                unsafe_allow_html=True,
            )
            st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)
        return
    st.markdown(
        '<p class="arch-phrase">1 fila de weekly_price = un producto '
        '(variedad y calidad) × región × canal × unidad × semana. '
        'Pasa el mouse por una tabla para ver para qué sirve.</p>',
        unsafe_allow_html=True,
    )
    with st.container(key="architecture_diagram"):
        # D-251: the star stays as it was in D-229, by the author's decision: no frame, its own size.
        st.markdown(star_model.build_star_svg(columns, row_counts, mode, tooltips=tooltips), unsafe_allow_html=True)
        st.markdown(
            '<div class="arch-legend"><span><b>PK</b> clave primaria</span>'
            '<span><b>FK</b> clave foránea</span><span><b>cian</b> medida</span>'
            '<span>'
            + build_repository_link_html("etl/schema.sql en GitHub", project.build_github_url("etl/schema.sql"))
            + '</span></div>',
            unsafe_allow_html=True,
        )


# endregion


# region Indicators (KPI)
def select_kpi(identifier):
    st.session_state["selected_kpi"] = identifier
    st.query_params[KPI_PARAMETER] = identifier


@st.cache_data
def read_kpi_observation(database_version, identifier):
    """One explicitly scoped observation, never a fabricated global average or target."""
    if identifier in ("K1", "K2", "K3", "K4", "K5"):
        query = {
            "K1": "k1_margin",
            "K2": "k2_channel_gap",
            "K3": "k3_regional_index",
            "K4": "k4_seasonal_index",
            "K5": "k1_margin",
        }[identifier]
        rows = project.select_example_rows(
            read_indicator_for_key(query, project.EXAMPLE_KEY),
            region=None if identifier == "K4" else project.EXAMPLE_REGION,
            channel=project.EXAMPLE_OTHER_CHANNEL if identifier == "K2" else project.EXAMPLE_CHANNEL,
        )
        if identifier == "K2":
            rows = rows[rows["reference_channel"] == project.EXAMPLE_CHANNEL]
        if rows.empty:
            return [("Resultado observado", "Sin datos comparables para la serie de referencia.")]
        row = rows.loc[rows["week_start"].idxmax()]
        scope = " · ".join(str(project.EXAMPLE_KEY[c]) for c in queries.KEY_COLUMNS)
        scope += " · " + str(row["channel"])
        if "region" in row:
            scope += " · " + str(row["region"])
        result = [
            ("Serie de referencia", scope),
            ("Periodo del resultado", "Semana " + weeks.week_range(row["week_start"], year=True)),
        ]
        if identifier == "K5":
            rows = lag.attach_same_package_changes(  # D-522
                rows, queries.run_query_for_key("same_package_changes", project.EXAMPLE_KEY)
            )
            best = lag.find_lag(lag.correlate_by_lag(rows)) if lag.has_enough_weeks(rows) else None
            result[1] = (
                "Periodo del resultado",
                f"{weeks.week_range(rows['week_start'].min(), year=True)} → "
                f"{weeks.week_range(rows['week_start'].max(), year=True)}",
            )
            value = (
                "Sin historia suficiente"
                if best is None
                else (
                    charts.describe_weeks(best[0]) if lag.is_clear_relation(best[1], best[2]) else "Sin relación clara"
                )
            )
            return result + [
                ("Resultado observado", value),
                ("Comparación", "Cambios mayoristas frente a cambios del consumidor; desfases de 0 a 8 semanas."),
            ]
        field = {"K1": "margin", "K2": "gap", "K3": "regional_index", "K4": "seasonal_index"}[identifier]
        value = (
            charts.format_signed_percent(float(row[field]) * 100)
            if identifier in ("K1", "K2")
            else charts.format_index(row[field])
        )
        reference = {
            "K1": "Precio mayorista de la misma semana, región y unidad.",
            "K2": "Precio en " + str(row.get("reference_channel", "")) + ", misma semana, región y unidad.",
            "K3": "1 = promedio simple de las regiones con precio en ese canal y semana.",
            "K4": "1 = promedio de las semanas disponibles del mismo año; el año en curso es provisional.",
        }[identifier]
        prior = rows[rows["week_start"] == row["week_start"] - pd.Timedelta(days=7)]
        previous = (
            "No hay dato comparable en la semana anterior."
            if prior.empty
            else (
                charts.format_signed_percent(float(prior.iloc[0][field]) * 100)
                if identifier in ("K1", "K2")
                else charts.format_index(prior.iloc[0][field])
            )
        )
        return result + [
            ("Resultado observado", value),
            ("Referencia de cálculo", reference),
            ("Semana anterior · mismo indicador", previous),
        ]
    if identifier == "K6":
        rows = read_price_alerts()
        week = pd.Timestamp(read_latest_week())
        counts = [len(rows[rows["week_start"] == date]) for date in (week, week - pd.Timedelta(days=7))]
        return [
            ("Resultado observado", f"{counts[0]} alertas"),
            ("Periodo del resultado", "Semana " + weeks.week_range(week, year=True)),
            ("Comparación", f"{counts[1]} alertas en la semana anterior; diferencia: {counts[0] - counts[1]:+d}."),
            (
                "Alcance",
                "Todos los productos y canales; cambios fuera del rango habitual de las 12 semanas anteriores.",
            ),
        ]
    if identifier == "K7":
        matched, total = read_match_coverage()
        _, first, last = project.read_week_span()
        return [
            ("Resultado observado", charts.format_percent(matched / total * 100) if total else "Sin datos"),
            ("Comparación", f"{matched:,} claves con cruce de {total:,} claves del consumidor."),
            ("Periodo del resultado", f"Histórico: {first} a {last}"),
            ("Alcance", "Cobertura del cruce definida en el ETL; no representa ventas ni población."),
        ]
    run = read_latest_run()
    share = run["rows_rejected"] / run["rows_read"] * 100 if run["rows_read"] else None
    return [
        ("Resultado observado", charts.format_percent(share) if share is not None else "Sin filas leídas"),
        ("Periodo del resultado", str(run["started_at"])),
        (
            "Comparación",
            f"{run['rows_rejected']:,} filas rechazadas de {run['rows_read']:,} filas leídas en esta carga.",
        ),
        ("Alcance", "Última carga registrada; comparación de proporción, no contra una meta."),
    ]


def split_kpi_figure(result):
    """(figure, unit): «43 alertas» → («43», «alertas»); a sentence stays whole as unit."""
    match = KPI_FIGURE.match(result.strip())
    return (match.group(1), match.group(2).lstrip("· ")) if match else ("", result)


def build_kpi_icon(name):
    return (
        f'<svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{KPI_ICONS_SVG[name]}</svg>'
    )


def kpi_node_positions():
    """Horizontal centre of each card, in % of the path width."""
    left, centres = 0, []
    for width in KPI_COLUMNS:
        centres.append(left + width / 2)
        left += width + KPI_GAP
    return centres


def build_kpi_path_html():
    """The line from «Inicio» to «Detalle técnico» through the three nodes, drawn once."""
    (x1, x2, x3), (y1, y2, y3) = [x * 10 for x in kpi_node_positions()], KPI_NODE_HEIGHTS
    lead = f"M4 {y1} L{x1} {y1}"
    first = f"M{x1} {y1} C{x1 + 150} {y1},{x2 - 160} {y2},{x2} {y2}"
    second = f"M{x2} {y2} C{x2 + 170} {y2},{x3 - 150} {y3},{x3} {y3} L992 12"
    paths = "".join(
        f'<path class="{kind}" d="{d}" vector-effect="non-scaling-stroke"/>'
        for kind, d in (("kpi-line", lead), ("kpi-line", first), ("kpi-line kpi-line-next", second))
    )
    nodes = "".join(
        f'<span class="kpi-node" style="left:{x}%;top:{y}px">{number}</span>'
        for number, (x, y) in enumerate(zip(kpi_node_positions(), KPI_NODE_HEIGHTS), 1)
    )
    return (
        f'<div class="kpi-band" aria-hidden="true"><svg viewBox="0 0 1000 {KPI_BAND_HEIGHT}" '
        f'preserveAspectRatio="none">{paths}</svg>{nodes}<span class="kpi-start"><i></i>Inicio</span>'
        '<span class="kpi-end">Detalle técnico<i></i></span></div>'
    )


def build_kpi_card_head(number, title):
    return f'<div class="kpi-card-title"><span class="sr-only">{number}. </span>{html.escape(title)}</div>'


def build_kpi_impact_html(identifier, evidence, run_kind, freshness):
    """Card 1: the figure alone, large, with its meaning, the state of the data and the week."""
    result = evidence.get("Resultado observado", "Sin dato comparable")
    figure, unit = split_kpi_figure(result)
    if figure and not unit:
        unit = KPI_PRESENTATION[identifier][2]
    if identifier in ("K3", "K4") and figure:
        unit = "1 = " + ("promedio regional del canal" if identifier == "K3" else "promedio anual")
    comparison = evidence.get("Comparación", "")
    if "Semana anterior · mismo indicador" in evidence:
        comparison = "Semana anterior: " + evidence["Semana anterior · mismo indicador"]
    period = freshness if identifier == "K8" else evidence.get("Periodo del resultado", "")
    has_data = bool(figure) or result not in ("Sin datos", "Sin dato comparable")
    state, text = (
        (run_kind, "Carga correcta" if run_kind == "ok" else "Última carga con falla")
        if has_data
        else ("neutral", "Sin dato comparable")
    )
    number = (
        f'<div class="kpi-figure">{html.escape(figure)}</div>'
        if figure
        else f'<div class="kpi-figure kpi-figure-text">{html.escape(result)}</div>'
    )
    return (
        build_kpi_card_head(1, "Resultado")
        + number
        + (f'<div class="kpi-lead">{html.escape(unit)}</div>' if figure and unit else "")
        + f'<div class="kpi-rule"></div><div class="kpi-line-text kpi-status"><span class="kpi-state kpi-state-{state}">'
        f'<i></i>{html.escape(text)}</span><span>{html.escape(period)}</span></div>'
        + (f'<div class="kpi-line-text">{build_kpi_icon("trend")}{html.escape(comparison)}</div>' if comparison else "")
    )


def build_kpi_scope_html(evidence, period):
    """Context · Alcance: the reference series as chips, then what it is and its period."""
    series = evidence.get("Serie de referencia")
    if series:
        chips = "".join(f'<span>{html.escape(part)}</span>' for part in series.split(" · "))
        note = "Una serie de referencia identificada, no un promedio de todos los productos."
        body = f'<div class="kpi-chips">{chips}</div>'
    else:
        body, note = "", evidence.get("Alcance", "Sin alcance registrado.")
    return (
        body + '<div class="kpi-rule"></div>'
        f'<div class="kpi-line-text">{build_kpi_icon("info")}{html.escape(note)}</div>'
        f'<div class="kpi-line-text">{build_kpi_icon("bars")}{html.escape(period)}</div>'
    )


@st.dialog("Consulta SQL", width="large")
def show_kpi_query_dialog(name):
    """The stored query, on demand, in a layer above the module: nothing moves under it."""
    st.caption(f"{name} · solo lectura, tal como está en el repositorio.")
    st.code(read_catalog_sql(name), language="sql", wrap_lines=True)
    st.markdown(
        build_repository_link_html("Ver la consulta en GitHub", build_query_address(name)), unsafe_allow_html=True
    )


def build_kpi_module_css(mode):
    palette = charts.get_palette(mode)
    dark = palette['base'] == charts.BASE_DARK
    accent = palette['accent']
    glow = f"drop-shadow(0 0 6px {accent}) drop-shadow(0 0 14px {accent}66)" if dark else "none"
    sans = '-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",sans-serif'
    columns = " ".join(f"{width}%" for width in KPI_COLUMNS)
    # Columns start one flex gap (16 px) below the band: each top border crosses its node.
    offsets = [height - 16 for height in KPI_NODE_HEIGHTS]
    return f"""<style>
    .kpi-head .compact-header {{display:flex; align-items:baseline; flex-wrap:wrap; gap:6px 18px; margin:0 0 12px;}}
    .kpi-head h1 {{font-size:1.6rem !important; margin:0 !important; padding:0 !important;}}
    .kpi-head .kpi-sub {{color:{palette['text']}; font-size:.9rem;}}
    .kpi-head .page-freshness {{margin:0 0 0 auto; font-size:.82rem;}}
    .st-key-kpi_module {{border:1px solid {palette['card_border']}; border-radius:18px; padding:16px 22px 26px;
        background:{palette['card'] if not dark else f"radial-gradient(120% 90% at 50% 0%, {accent}14, transparent 60%), {palette['background']}"};}}
    .st-key-kpi_question [data-testid="stHorizontalBlock"] {{align-items:center; gap:12px;}}
    .kpi-question-label {{border:1px solid {palette['card_border']}; border-radius:10px; padding:9px 14px;
        font:500 .9rem {sans}; color:{palette['strong_text']}; text-align:center; white-space:nowrap;}}
    .st-key-kpi_path {{position:relative; margin-top:8px;}}
    .kpi-band {{position:absolute; left:0; right:0; top:0; height:{KPI_BAND_HEIGHT}px; pointer-events:none;}}
    .kpi-band svg {{position:absolute; inset:0; width:100%; height:100%; overflow:visible; filter:{glow};}}
    .kpi-line {{fill:none; stroke:{accent}; stroke-width:3; stroke-linecap:round;}}
    .kpi-line-next {{stroke-dasharray:7 9; stroke-width:2.4;}}
    .kpi-start, .kpi-end {{position:absolute; top:{KPI_NODE_HEIGHTS[0] - 40}px; display:flex; align-items:center; gap:8px;
        font:500 .78rem {sans}; color:{palette['strong_text']}; padding:4px 10px; border-radius:8px;
        border:1px solid {palette['card_border']}; background:{palette['card']};}}
    .kpi-start {{left:0;}} .kpi-end {{right:0; top:-8px;}}
    .kpi-start i, .kpi-end i {{width:9px; height:9px; border-radius:50%; border:2px solid {accent};}}
    .st-key-kpi_path > div > [data-testid="stHorizontalBlock"] {{display:grid !important;
        grid-template-columns:{columns}; column-gap:{KPI_GAP}%; align-items:start;}}
    .st-key-kpi_path [data-testid="stColumn"] {{width:auto !important; min-width:0;}}
    .st-key-kpi_card_1 {{margin-top:{offsets[0]}px;}} .st-key-kpi_card_2 {{margin-top:{offsets[1]}px;}}
    .st-key-kpi_card_3 {{margin-top:{offsets[2]}px;}}
    .st-key-kpi_card_1, .st-key-kpi_card_2, .st-key-kpi_card_3 {{position:relative; overflow:visible;
        border:1px solid {accent if dark else palette['card_border']}; border-color:{accent}55; border-radius:14px;
        padding:40px 22px 20px; background:{palette['card']};
        box-shadow:{f"0 0 0 1px {accent}12, 0 0 24px {accent}14" if dark else "0 10px 28px rgba(15,23,42,.07)"};}}
    .sr-only {{position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0);}}
    .kpi-node {{position:absolute; transform:translate(-50%,-50%); width:52px; height:52px;
        border-radius:50%; display:grid; place-items:center; z-index:2; font:600 1.35rem {sans};
        color:{palette['strong_text']}; background:{palette['card'] if not dark else palette['background']};
        border:3px solid {accent}; box-shadow:{f"0 0 14px {accent}, 0 0 30px {accent}55" if dark else f"0 0 0 5px {accent}22"};}}
    .kpi-card-title {{font:700 .95rem {sans}; letter-spacing:.06em; text-transform:uppercase;
        color:{palette['strong_text']}; margin-bottom:6px;}}
    .kpi-figure {{font:700 clamp(2.8rem,4.6vw,4.4rem)/1.05 {sans}; letter-spacing:-.035em; white-space:nowrap;
        color:{accent}; font-variant-numeric:tabular-nums; margin:4px 0 8px;
        text-shadow:{f"0 0 22px {accent}55" if dark else "none"};}}
    .kpi-figure-text {{white-space:normal; font-size:clamp(1.6rem,2.6vw,2.2rem);}}
    .kpi-lead {{font:400 1rem/1.4 {sans}; color:{palette['strong_text']};}}
    .kpi-rule {{height:1px; background:{palette['card_border']}; margin:14px 0 12px;}}
    .kpi-line-text {{display:flex; align-items:flex-start; gap:10px; font:400 .86rem/1.45 {sans};
        color:{palette['strong_text']}; margin:0 0 8px;}}
    .kpi-status {{flex-wrap:wrap; gap:4px 8px;}}
    .kpi-icon {{width:20px; height:20px; flex-shrink:0; stroke:{palette['text']};}}
    .kpi-state {{display:inline-flex; align-items:center; gap:8px; white-space:nowrap;}}
    .kpi-state i {{width:9px; height:9px; border-radius:50%; background:{palette['reference']};}}
    .kpi-state-ok {{color:#34c759;}} .kpi-state-ok i {{background:#34c759; box-shadow:0 0 8px #34c75999;}}
    .kpi-state-failed {{color:#ff9f0a;}} .kpi-state-failed i {{background:#ff9f0a;}}
    .st-key-kpi_card_2 [data-baseweb="tab-list"] {{gap:18px;}}
    .st-key-kpi_card_2 [data-baseweb="tab-panel"] {{padding-top:12px;}}
    .kpi-chips {{display:flex; flex-wrap:wrap; gap:8px;}}
    .kpi-chips span {{padding:5px 13px; border-radius:999px; font:400 .84rem {sans}; color:{palette['strong_text']};
        border:1px solid {palette['card_border']}; background:{palette['field']};}}
    .kpi-formula {{font:500 .84rem/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; padding:10px 12px;
        border-radius:10px; background:{palette['field']}; color:{palette['strong_text']};
        border:1px solid {palette['card_border']}; overflow-wrap:anywhere; margin-bottom:10px;}}
    .kpi-query-name {{font:500 .95rem ui-monospace,SFMono-Regular,Menlo,monospace; color:{palette['strong_text']};
        padding:11px 14px; border-radius:10px; background:{palette['field']}; border:1px solid {palette['card_border']};
        margin:6px 0 12px; overflow-wrap:anywhere;}}
    .st-key-kpi_query_open button {{width:100%; justify-content:flex-start; border:1.5px solid {accent} !important;
        color:{accent} !important; background:transparent !important; border-radius:10px; min-height:46px;
        font-weight:600;}}
    .st-key-kpi_query_open button p {{color:{accent} !important; font-weight:600;}}
    @media(max-width:900px) {{
        .kpi-band {{display:none;}}
        .st-key-kpi_path > div > [data-testid="stHorizontalBlock"] {{grid-template-columns:1fr; row-gap:14px;}}
        .st-key-kpi_card_1, .st-key-kpi_card_2, .st-key-kpi_card_3 {{margin-top:0; padding-top:20px;}}
        .kpi-card-title .sr-only {{position:static; width:auto; height:auto; clip:auto; color:{accent};}}
        .kpi-head .page-freshness {{margin-left:0;}}
        .kpi-card-title {{padding-left:0;}}
    }}
    </style>"""


def show_kpi_tab(mode):
    """The whole path of one KPI, in sight at once: result → context → query (D-090)."""
    st.markdown(build_kpi_module_css(mode), unsafe_allow_html=True)
    indicators = project.read_design_table(project.INDICATORS_HEADING)
    guide = {r['KPI']: r for r in project.read_guide_table('KPI')}
    by_id = {r['ID']: r for r in indicators}
    requested = st.query_params.get(KPI_PARAMETER, 'K1')
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    freshness = format_chile_time(parse_run_start(latest_run['started_at']))
    with st.container(key="kpi_module"):
        with st.container(key="kpi_question"):
            label, choice = st.columns([2, 8])
            label.markdown('<div class="kpi-question-label">Pregunta de negocio</div>', unsafe_allow_html=True)
            selected = choice.selectbox(
                "Pregunta de negocio",
                list(by_id),
                index=list(by_id).index(requested) if requested in by_id else 0,
                format_func=lambda k: f"{KPI_PRESENTATION[k][0]} — {KPI_QUESTIONS[k]}",
                key="kpi_register_selection",
                label_visibility="collapsed",
                on_change=lambda: select_kpi(st.session_state["kpi_register_selection"]),
            )
        evidence = dict(read_kpi_observation(get_database_version(), selected))
        query_name = guide[selected]['Consulta']
        measure, _, period = KPI_SMART_SCOPE[selected]
        reference = evidence.get("Referencia de cálculo")
        with st.container(key="kpi_path"):
            st.markdown(build_kpi_path_html(), unsafe_allow_html=True)
            result, context, query = st.columns(3)
            with result, st.container(key="kpi_card_1"):
                st.markdown(build_kpi_impact_html(selected, evidence, run_kind, freshness), unsafe_allow_html=True)
            with context, st.container(key="kpi_card_2"):
                st.markdown(build_kpi_card_head(2, "Contexto"), unsafe_allow_html=True)
                scope_tab, logic_tab, limits_tab = st.tabs(["Alcance", "Lógica", "Límites"])
                scope_tab.markdown(build_kpi_scope_html(evidence, period), unsafe_allow_html=True)
                logic_tab.markdown(
                    f'<div class="kpi-formula">{html.escape(by_id[selected]["Fórmula"])}</div>'
                    f'<div class="kpi-line-text">{build_kpi_icon("info")}{html.escape(measure)}</div>'
                    + (
                        f'<div class="kpi-line-text">{build_kpi_icon("bars")}{html.escape(reference)}</div>'
                        if reference
                        else ""
                    ),
                    unsafe_allow_html=True,
                )
                limits_tab.markdown(
                    f'<div class="kpi-line-text">{build_kpi_icon("info")}{html.escape(KPI_LIMITS[selected])}</div>'
                    f'<div class="kpi-line-text">{build_kpi_icon("bars")}Sin meta de negocio acordada: '
                    'el indicador describe o controla los datos.</div>',
                    unsafe_allow_html=True,
                )
            with query, st.container(key="kpi_card_3"):
                st.markdown(
                    build_kpi_card_head(3, "Consulta") + f'<div class="kpi-query-name">{html.escape(query_name)}</div>'
                    '<div class="kpi-line-text">Consulta guardada que produce este resultado, en solo lectura.</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Desplegar SQL", key="kpi_query_open", icon=":material/code:", use_container_width=True):
                    show_kpi_query_dialog(query_name)
                st.markdown(
                    build_repository_link_html("Ver en GitHub", build_query_address(query_name)), unsafe_allow_html=True
                )


def show_kpi_page(mode):
    """KPIs with a one-line header, so the whole path fits one screen."""
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    run_text = "Carga correcta" if run_kind == "ok" else "Última carga con falla"
    freshness = format_chile_time(parse_run_start(latest_run["started_at"]))
    st.markdown(
        f'<div class="kpi-head"><div class="compact-header"><h1>{html.escape(SECTION_KPI)}</h1>'
        '<span class="kpi-sub">Elige una pregunta y recorre su camino: resultado, contexto y consulta.</span>'
        f'<span class="page-freshness">Datos actualizados el {freshness} {build_chip(run_text, run_kind)}</span></div></div>',
        unsafe_allow_html=True,
    )
    show_kpi_tab(mode)


# endregion
