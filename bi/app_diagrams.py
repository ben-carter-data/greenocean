"""The panel's own diagrams for the documents (D-448): the SAD draws the same star schema, entity-relation, storage map,
database crossings, stack and deployment as the panel, from the same code, as a fixed picture without the live state."""

from datetime import date

from bi import (
    charts,
    database_crossings,
    deployment,
    er_diagram,
    project,
    queries,
    stack_page,
    star_model,
    storage_map,
    weeks,
)
from etl import etl

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


def build_star_html(mode):
    """[[diagrama:estrella]]: the star schema of «Modelo de datos» (D-147, D-229)."""
    row_counts = project.count_table_rows()
    columns = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
    return page(star_model.build_star_svg(columns, row_counts, mode, tooltips=model_tooltips(row_counts)))


def build_entity_relation_html(mode):
    """[[diagrama:entidad_relacion]]: the entity-relation diagram of «Modelo de datos» (D-195)."""
    row_counts = project.count_table_rows()
    return page(er_diagram.build_er_svg(er_diagram.read_schema(), row_counts, mode, model_tooltips(row_counts)))


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
