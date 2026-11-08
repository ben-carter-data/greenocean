"""The panel's own diagrams for the documents (D-448): the SAD draws the same star schema, entity-relation, storage map,
database crossings, stack and deployment as the panel, from the same code, as a fixed picture without the live state.
D-455: the other documents too: the journey by layers, the interest map, CI/CD, monitoring, the security architecture,
the quality flow and «Cambios e incidentes»."""

import functools
import json
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from bi import (
    architecture,
    business_analysis,
    charts,
    control,
    database_crossings,
    deployment,
    devops,
    er_diagram,
    git_workflow,
    i18n,
    interest_map,
    lineage,
    monitoring,
    project,
    quality,
    quality_live,
    quality_view,
    queries,
    security_map,
    stack_page,
    star_model,
    storage_map,
    weeks,
)
from etl import etl


# region Constants
IPC_TABLE_DEFINITIONS = {
    "ipc_weekly": "el deflactor de cada semana: el IPC del mes de su lunes frente al último mes publicado, "
    "para expresar los precios en pesos reales",
    "ipc_monthly": "el IPC de alimentos del INE como una sola serie mensual, base 2023 = 100",
    "ine_ipc_source": "las filas del IPC tal como se leyeron del INE, para rehacer la capa bronce si el INE no responde",
}
TABLE_ROLES = {
    "weekly_price": "hechos",
    "dim_product": "dimensión",
    "dim_region": "dimensión",
    "dim_channel": "dimensión",
    "dim_date": "dimensión",
    "etl_run": "auditoría",
    "rejection": "auditoría",
    "ipc_weekly": "IPC",
    "ipc_monthly": "IPC",
    "ine_ipc_source": "IPC",
}
# raw.db is 665 MB on the author's computer and never in the repository (D-020); where the file is missing, the
# documented size is shown with an approximation sign.
RAW_DATABASE_SIZE_TEXT = "≈ 665 MB"
MANIFEST = queries.DATABASE_FILE.parent.parent / "agent" / "downloads" / "manifest.json"
# endregion


# region Reading what the diagrams show
def model_tooltips(row_counts):
    """{table: what shows on hover}: its role, its rows and its definition from the project guide."""
    definitions = project.parse_definitions(
        project.read_section(project.read_document(project.PROJECT_GUIDE_FILE), "Modelo de datos")
    )
    definitions = {**IPC_TABLE_DEFINITIONS, **definitions}
    return {
        table: f"{table} · {TABLE_ROLES[table]} · {charts.format_thousands(row_counts[table])} filas\n"
        f"{definitions.get(table, '')[:1].upper()}{definitions.get(table, '')[1:]}"
        for table in project.TABLE_NAMES + project.IPC_TABLE_NAMES
    }


def format_file_size(size):
    megabytes = size / 1_000_000
    return f"{megabytes:,.0f} MB".replace(",", ".") if megabytes >= 10 else f"{megabytes:.1f} MB".replace(".", ",")


def read_store_sizes():
    """{store key: size text} of the files of the storage diagram that exist here (D-191)."""
    sizes = {}
    for key, path in (("served", queries.DATABASE_FILE), ("backup", etl.BASE_DIR / "datos.db")):
        if path.exists():
            sizes[key] = format_file_size(path.stat().st_size)
    raw = etl.RAW_DATABASE_FILE
    sizes["raw"] = format_file_size(raw.stat().st_size) if raw.exists() else RAW_DATABASE_SIZE_TEXT
    return sizes


def read_database_map():
    """Rows of every served table, dbt models per layer and dbt tests, for the storage map (D-189)."""
    connection = queries.open_database()
    try:
        tables = [name for (name,) in connection.execute("SHOW TABLES").fetchall()]
        counts = {name: connection.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0] for name in tables}
        nodes = connection.execute("SELECT resource_type, layer, count(*) FROM dbt_node GROUP BY ALL").fetchall()
    finally:
        connection.close()
    layers = {layer: int(count) for kind, layer, count in nodes if kind == "model"}
    tests = sum(int(count) for kind, _, count in nodes if kind == "test")
    return counts, layers, tests


def page(body, css=""):
    """One document of its own, on a transparent sheet, like every document diagram (D-205, D-280)."""
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><style>'
        "html, body { margin:0; background:transparent; } svg { display:block; width:100%; height:auto; }"
        f"{css}</style></head><body>{body}</body></html>"
    )


# endregion


# region Data model and deployment
def build_star_html(mode):
    """[[diagrama:estrella]]: the star schema of «Modelo de datos» (D-147, D-229)."""
    row_counts = project.count_table_rows()
    columns = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
    return page(star_model.build_star_svg(columns, row_counts, mode, tooltips=model_tooltips(row_counts)))


def build_entity_relation_html(mode):
    """[[diagrama:entidad_relacion]]: the entity-relation diagram of «Modelo de datos» (D-195)."""
    row_counts = project.count_table_rows()
    return page(
        er_diagram.build_er_svg(
            er_diagram.read_schema(),
            row_counts,
            mode,
            model_tooltips(row_counts),
            empty_units=er_diagram.read_empty_units(),  # D-526: the same legend as the panel
        )
    )


def build_storage_html(mode):
    """[[diagrama:almacenamiento]]: «Dónde viven los datos» (D-189)."""
    counts, layers, tests = read_database_map()
    return storage_map.build_map_html(charts.get_palette(mode), counts, layers, tests, read_store_sizes())


def build_crossings_html(mode):
    """[[diagrama:cruces]]: «Cruces entre bases» (D-197), with the checks it can make here."""
    return database_crossings.build_crossings_html(charts.get_palette(mode), database_crossings.read_checks())


def build_stack_html(mode):
    """[[diagrama:herramientas]]: the tools of «Stack y evidencia» (D-221); on paper a tool is not a link."""
    addresses = {page_name: None for *_, page_name in stack_page.STACK}
    return page(stack_page.build_stack_html(charts.get_palette(mode), stack_page.read_figures(), addresses))


def build_deployment_html(mode):
    """[[diagrama:despliegue]]: the deployment diagram of «Centro de operación» (D-132), without the live dots."""
    latest_week = date.fromisoformat(str(queries.run_query("quality_week_range").iloc[0]["last_week"])[:10])
    week_prices = project.count_week_prices(f"{latest_week:%Y-%m-%d}")
    figures = {"week_prices": f"semana {weeks.week_range(latest_week)}: {charts.format_thousands(week_prices)} precios"}
    return deployment.build_deployment_html(charts.get_palette(mode), {}, figures, live=False)


# endregion


# region The weekly load's journey
def chile_time(started_at):
    """'2026-10-31T04:41:08' (UTC, as the ETL stores it) in Chilean time; a fixed UTC-3 without the time zone database."""
    moment = datetime.fromisoformat(str(started_at)).replace(tzinfo=timezone.utc)
    try:
        return moment.astimezone(ZoneInfo("America/Santiago"))
    except Exception:  # time zone database not installed
        return moment.astimezone(timezone(timedelta(hours=-3)))


def read_manifest():
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def build_journey_html(mode):
    """[[diagrama:recorrido]]: the journey by layers of «Pipeline y linaje» (D-136), with the state the latest published
    load proves and the same figures as the page; the live state of each step is on the page."""
    latest = queries.run_query("quality_runs").iloc[0]
    week_range = queries.run_query("quality_week_range").iloc[0]
    weekly_prices = int(queries.run_query("quality_flag_counts")["weekly_prices"].sum())
    loaded = latest["status"] == etl.STATUS_LOADED
    load_state = control.RUN_OK if loaded else control.RUN_FAILED
    # As the page does without an answer from GitHub (D-034): the saved load proves download, ETL and tests.
    states = {
        "sources": control.RUN_OK if read_manifest() else architecture.STATE_UNKNOWN,
        "download": load_state,
        "etl": load_state,
        "tests": load_state,
        "report": architecture.STATE_UNKNOWN,
        "workflow": architecture.STATE_UNKNOWN,
        "load": load_state,
        "etl_run": load_state,
        "panel": control.RUN_OK,
    }
    first, last = week_range["first_year"], week_range["last_year"]
    loaded_at = chile_time(latest["started_at"])
    next_run = control.calculate_next_scheduled_run(datetime.now(timezone.utc)).astimezone(loaded_at.tzinfo)
    figures = {
        "source_years": f"año {last}" if first == last else f"años {first} a {last}",
        "last_run": f"última {loaded_at:%d-%m %H:%M}",
        "rows_read": f"{charts.format_thousands(latest['rows_read'])} filas leídas",
        "rows_rejected": f"{charts.format_thousands(latest['rows_rejected'])} filas",
        "weekly_prices": f"{charts.format_thousands(weekly_prices)} precios",
        "latest_week": f"hasta {weeks.week_range(date.fromisoformat(str(week_range['last_week'])[:10]), year=True)}",
        "panel_time": f"datos al {loaded_at:%d-%m %H:%M}",
        "next_run": f"{next_run:%d-%m %H:%M}",
    }
    build = lineage.summarize_build(*lineage.read_tables(queries.run_sql))
    if build:
        figures["dbt"] = f"{build['models']} modelos · {build['passing']}/{build['tests']} pruebas"
    caption = (
        f"State of the latest published load, of {loaded_at:%Y-%m-%d %H:%M}; the live state of each step is in "
        "«Pipeline and lineage»."
        if i18n.is_english()
        else f"Estado de la última carga publicada, del {loaded_at:%d-%m-%Y %H:%M}; "
        "el estado en vivo de cada paso está en «Pipeline y linaje»."
    )
    return page(
        architecture.build_journey_svg(states, figures, mode, animate_flow=False) + f'<p class="cap">{caption}</p>',
        ".cap { margin:6px 0 0; text-align:center; font:12.5px/1.4 -apple-system, BlinkMacSystemFont, 'Segoe UI', "
        f"sans-serif; color:{charts.get_palette(mode)['text']}; }}",
    )


# endregion


# region DevOps and security
def build_cicd_html(mode):
    """[[diagrama:cicd]]: how a change reaches production, the «CI/CD» tab of «Centro de operación» (D-243, D-276)."""
    return devops.build_cicd_html(charts.get_palette(mode))


def build_monitoring_html(mode):
    """[[diagrama:monitoreo]]: how we know that something failed, the «Monitoreo» tab of «Centro de operación» (D-249)."""
    return monitoring.build_monitoring_html(charts.get_palette(mode))


def build_security_html(mode):
    """[[diagrama:seguridad]]: the trust zones, controls and threats of «Arquitectura de seguridad» (D-201)."""
    return security_map.build_security_html(charts.get_palette(mode))


# endregion


# region Quality and business
@functools.lru_cache(maxsize=2)
def read_quality(database_key):
    """The measures and the evidence of «Controles de datos», read once per database, as the page does (D-196)."""
    measures = quality_live.read_measures()
    manifest = read_manifest()
    run = queries.run_query("quality_runs").iloc[0]
    build = lineage.summarize_build(*lineage.read_tables(queries.run_sql))
    checks, files = quality.check_database(), quality.check_source_files(manifest, MANIFEST.parent)
    rejections = int(queries.run_sql("SELECT count(*) AS n FROM rejection").iloc[0, 0])
    evidence = quality_view.build_evidence(
        checks,
        files,
        manifest,
        run,
        build,
        quality.check_parity(),
        lambda value: f"{chile_time(value):%d-%m-%Y %H:%M}",
        rejections=rejections,
    )
    return measures, quality_view.build_columns(evidence)


def build_quality_html(mode):
    """[[diagrama:calidad]]: the quality flow of «Controles de datos» (D-220, D-257): each dimension under the pipeline
    stop where it is watched, measured on the published database."""
    stat = queries.DATABASE_FILE.stat()
    measures, columns = read_quality((stat.st_size, stat.st_mtime_ns))
    return quality_live.build_quality_html(
        charts.get_palette(mode), quality_live.build_indicators(measures), columns, measures
    )


def build_git_workflow_html(mode):
    """[[diagrama:git_workflow]]: the flowchart of «Cambios e incidentes» (D-449), as a picture: the side panel of each station
    lives on the page."""
    palette = charts.get_palette(mode)
    language = i18n.get_language()
    data = git_workflow.build_data(language, git_workflow.read_failures(), author=False)
    for station in data["stations"]:
        station["label"] = f'{data["labels"]["station"]} {station["n"]}: {station["title"]}'
    return page(
        git_workflow.build_svg(data, language),
        git_workflow.build_css(palette).removeprefix("<style>").removesuffix("</style>")
        + "html, body { background:transparent; padding:0; } .st { cursor:default; }"
        + " svg.ico { width:24px !important; height:24px !important; }",
    )


def build_interest_html(mode):
    """[[diagrama:interes]]: the interest map of «Interesados» (D-444), read from the PRD (3.4). It is drawn inline in the
    document, not in a frame, because its icons are letters of the panel's own icon font."""
    palette = charts.get_palette(mode)
    rows = business_analysis.read_interest()
    return interest_map.build_css(palette, fit_height=False) + interest_map.build_map_html(
        rows, palette, lambda row: (None, ""), i18n.tr
    )


# endregion
