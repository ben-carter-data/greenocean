"""D-515: the relationships between the views of «Consultas SQL», as the entity-relationship diagram a SQL client shows.

The views (bi/sql_explorer.py) hide the keys of the data warehouse behind readable names, so a reader cannot guess
which columns join them. This drawing says it: one box per view with its real columns and types (DESCRIBE on the
views), the columns that identify a row, and each join as a line in the notation of bi/er_diagram.py, with the ON
clause ready to copy under the drawing. Which joins exist is declared once here and checked against the views by
the tests.
"""

import html

from bi import er_diagram, i18n, sql_explorer

# region Constants
HEADER, ROW, BOX, MARGIN = 32, 24, 255, er_diagram.MARGIN
# D-516: four columns, so the drawing is wider than tall and all of it fits one look at the window. Each view beside the
# view it joins; the gaps leave room for the lines that pass between two columns.
COLUMNS = (
    ("productos", "modelos_dbt"),
    ("precios",),
    ("semanas", "ipc_semanal"),
    ("ipc_mensual", "cargas", "rechazos"),
)
COLUMN_GAPS, BOX_GAP, BRACKET = (86, 100, 140), 26, 34
BRACKET_ON_THE_RIGHT = {"ipc_semanal"}  # precios already reaches semanas by its left edge
FONT, MONO = er_diagram.FONT, er_diagram.MONO
VIEWS = ["productos", "precios", "semanas", "ipc_semanal", "cargas", "rechazos", "ipc_mensual", "modelos_dbt"]
# The columns that identify one row of a view, as er_diagram.PRIMARY_KEYS says of its table with the ids written as
# names (D-519); the tests check that they do. A view with none is read by its whole row.
KEYS = {
    "precios": ["semana", "familia", "producto", "variedad", "calidad", "canal", "region", "unidad"],
    "semanas": ["semana"],
    "productos": ["familia", "producto", "variedad", "calidad"],
    "ipc_semanal": ["semana"],
    "ipc_mensual": ["anio", "mes"],
    "cargas": ["inicio"],
    "rechazos": [],
    "modelos_dbt": [],
}
# (child view, child column, parent view, parent column, child end, parent end, what it says)
RELATIONS = [
    ("precios", "semana", "semanas", "semana", "many0", "one", "cada precio es de una semana del calendario"),
    ("ipc_semanal", "semana", "semanas", "semana", "zero_one", "one", "cada semana tiene a lo más un factor real"),
    (
        "precios",
        "producto",
        "productos",
        "producto",
        "many0",
        "one",
        "cada precio es de un producto del catálogo: se une por familia, producto, variedad y calidad",
    ),
    ("rechazos", "inicio_carga", "cargas", "inicio", "many0", "one", "cada fila rechazada pertenece a una carga"),
]
# Not a key: the same month, read by two views.
LOGICAL = (
    "ipc_mensual",
    "anio",
    "ipc_semanal",
    "anio_ipc",
    "mismo mes",
    "ipc_semanal toma el IPC del mes de su lunes (anio_ipc, mes_ipc) de ipc_mensual (anio, mes)",
)
# The line to the catalogue meets one column, but its key is four: all four are foreign keys of precios.
FOREIGN = {(child, column) for child, column, *_ in RELATIONS} | {("precios", column) for column in KEYS["productos"]}
# D-517: the views that join among themselves, each group with its colour and what it holds. All eight live in the same
# Base DuckDB and the same load writes them: the colour says what they record, not where they are.
GROUP_COLORS = {"amber": ("#f5b84b", "#a16207"), "pink": ("#ff7ab8", "#c2337a")}  # (on a dark card, on a light one)
GROUPS = (
    (
        "accent",
        ("productos", "precios", "semanas", "ipc_semanal", "ipc_mensual"),
        "Datos: los precios de ODEPA y el IPC de alimentos del INE",
    ),
    ("amber", ("cargas", "rechazos"), "Registro de cargas: cada carga de etl_run y las filas que rechazó"),
    ("pink", ("modelos_dbt",), "dbt Core: los modelos y las pruebas que construyen la Base DuckDB"),
)
# The joins, as they are written, each with its comment in the language of the visit (D-443); the reader copies the
# line that serves. A blank line separates the statements.
JOIN_LINES = [
    ("", "Cómo se unen las vistas (copia la línea que te sirva)"),
    ("FROM precios AS p", ""),
    ("JOIN semanas AS s ON s.semana = p.semana", "el calendario: año, mes, semana ISO, estación"),
    ("LEFT JOIN ipc_semanal AS i ON i.semana = p.semana", "precio × i.factor_real = precio real"),
    ("JOIN productos AS pr ON pr.familia = p.familia AND pr.producto = p.producto", ""),
    ("                    AND pr.variedad = p.variedad AND pr.calidad = p.calidad", ""),
    (None, None),
    ("FROM rechazos AS r", ""),
    ("JOIN cargas AS c ON c.inicio = r.inicio_carga", "la carga que rechazó la fila"),
    (None, None),
    ("FROM ipc_semanal AS i", ""),
    ("JOIN semanas AS s ON s.semana = i.semana", "el calendario de esa semana"),
    ("JOIN ipc_mensual AS m ON m.anio = i.anio_ipc AND m.mes = i.mes_ipc", "el mes del IPC de cada semana"),
]
# endregion


# region The relationships between the views of «Consultas SQL»
def build_joins():
    """The joins as one SQL text, the comments in the language of the visit, aligned in a column."""
    width = max(len(sql) for sql, _ in JOIN_LINES if sql) + 2
    lines = []
    for sql, comment in JOIN_LINES:
        if sql is None:
            lines.append("")
        elif not sql:
            lines.append(f"-- {i18n.tr(comment)}")
        elif comment:
            lines.append(f"{sql.ljust(width)}-- {i18n.tr(comment)}")
        else:
            lines.append(sql)
    return "\n".join(lines)


def read_schema(database_file=None):
    """{view: [(column, type)]} and {view: rows}, read from the views themselves."""
    connection = (
        sql_explorer.open_explorer_connection(database_file)
        if database_file
        else sql_explorer.open_explorer_connection()
    )
    try:
        schema = {
            view: [(row[0], row[1]) for row in connection.execute(f"DESCRIBE {view}").fetchall()] for view in VIEWS
        }
        counts = {view: connection.execute(f"SELECT count(*) FROM {view}").fetchone()[0] for view in VIEWS}
    finally:
        connection.close()
    return schema, counts


def key_label(view, column):
    primary = column in KEYS[view]
    foreign = (view, column) in FOREIGN
    return "PK, FK" if primary and foreign else "PK" if primary else "FK" if foreign else ""


def group_color(name, mode):
    palette = er_diagram.charts.get_palette(mode)
    if name == "accent":
        return palette["accent"]
    return GROUP_COLORS[name][0 if palette["base"] == er_diagram.charts.BASE_DARK else 1]


def layout(schema):
    """{view: (x, y, width, height)}: the columns of COLUMNS from left to right, each view under the one before."""
    places, x = {}, MARGIN
    for views, gap in zip(COLUMNS, (*COLUMN_GAPS, 0)):
        y = MARGIN
        for view in views:
            height = HEADER + len(schema[view]) * ROW
            places[view] = (x, y, BOX, height)
            y += height + BOX_GAP
        x += BOX + gap
    return places


def row_y(places, view, column, schema):
    _, y, _, _ = places[view]
    index = [name for name, _ in schema[view]].index(column)
    return y + HEADER + index * ROW + ROW / 2


def build_view(view, schema, places, counts, shade, descriptions):
    x, y, width, height = places[view]
    rows = []
    for index, (column, kind) in enumerate(schema[view]):
        base = y + HEADER + index * ROW
        rows.append(
            f'<text x="{x + 10}" y="{base + 16}" font-size="11" font-weight="600" fill="{shade["accent"]}">'
            f"{key_label(view, column)}</text>"
            f'<text translate="no" x="{x + 50}" y="{base + 16}" font-family="{MONO}" font-size="{FONT}" '
            f'fill="{shade["ink"]}">'
            f"{html.escape(column)}</text>"
            f'<text x="{x + width - 10}" y="{base + 16}" text-anchor="end" font-family="{MONO}" font-size="11" '
            f'fill="{shade["muted"]}">{html.escape(kind)}</text>'
        )
    rule = ""
    if KEYS[view] and [name for name, _ in schema[view]][: len(KEYS[view])] == KEYS[view]:  # only keys that come first
        rule_y = y + HEADER + len(KEYS[view]) * ROW
        rule = f'<path d="M{x} {rule_y} H{x + width}" stroke="{shade["line"]}" stroke-width="1.2"/>'
    count = (
        f'<text x="{x + width - 10}" y="{y + 21}" text-anchor="end" font-size="10.5" fill="{shade["muted"]}">'
        f"{er_diagram.charts.format_thousands(counts[view])} filas</text>"
        if counts.get(view) is not None
        else ""
    )
    return (
        f'<g class="er-table er-{view}"><title>{html.escape(descriptions.get(view, view))}</title>'
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="6" fill="{shade["card"]}" '
        f'stroke="{shade["line"]}" stroke-width="1.4"/>'
        f'<path d="M{x} {y + HEADER} V{y + 6} Q{x} {y} {x + 6} {y} H{x + width - 6} Q{x + width} {y} {x + width} {y + 6} '
        f'V{y + HEADER} Z" fill="{shade["accent"]}" fill-opacity="{shade["header_opacity"]}"/>'
        f'<text translate="no" x="{x + 10}" y="{y + 21}" font-size="14" font-weight="600" '
        f'fill="{shade["ink"]}">{html.escape(view)}</text>'
        f'{count}{rule}{"".join(rows)}</g>'
    )


def route(places, child, parent, y_child, y_parent):
    """The path between the facing edges of two boxes: straight at one height, an elbow otherwise; a bracket when one
    is under the other, out of the edge that no other line uses."""
    c, p = places[child], places[parent]
    if c[0] == p[0]:
        if child in BRACKET_ON_THE_RIGHT:
            edge = c[0] + c[2]
            return f"M{edge} {y_child} H{edge + BRACKET} V{y_parent} H{edge}", "right", "right"
        return f"M{c[0]} {y_child} H{c[0] - BRACKET} V{y_parent} H{p[0]}", "left", "left"
    child_edge, parent_edge = ("left", "right") if p[0] + p[2] <= c[0] else ("right", "left")
    (xc, _), (xp, _) = er_diagram.attach(c, child_edge), er_diagram.attach(p, parent_edge)
    if y_child == y_parent:
        return f"M{xc} {y_child} H{xp}", child_edge, parent_edge
    middle = (xc + xp) / 2
    return f"M{xc} {y_child} H{middle} V{y_parent} H{xp}", child_edge, parent_edge


def build_relation(places, schema, relation, shade):
    child, child_column, parent, parent_column, child_end, parent_end, meaning = relation
    y_child, y_parent = row_y(places, child, child_column, schema), row_y(places, parent, parent_column, schema)
    path, child_edge, parent_edge = route(places, child, parent, y_child, y_parent)
    (xc, child_arrival), (xp, parent_arrival) = (
        er_diagram.attach(places[child], child_edge),
        er_diagram.attach(places[parent], parent_edge),
    )
    return (
        f'<g class="er-link"><title>{child}.{child_column} → {parent}.{parent_column} · {html.escape(meaning)}</title>'
        f'<path d="{path}" fill="none" stroke="{shade["accent"]}" stroke-width="1.6"/>'
        f'{er_diagram.crow(xc, y_child, child_arrival, child_end, shade["accent"], shade["card"])}'
        f'{er_diagram.crow(xp, y_parent, parent_arrival, parent_end, shade["accent"], shade["card"])}</g>'
    )


def build_svg(schema, counts, mode, descriptions=None):
    """The whole drawing: the eight views in the colour of their group, the four joins, the logical link of the IPC and
    the legend."""
    shade = er_diagram.colors(mode)
    places = layout(schema)
    descriptions = descriptions or {}
    width = max(x + w for x, _, w, _ in places.values()) + MARGIN
    bottom = max(y + h for _, y, _, h in places.values()) + MARGIN
    shades = {view: {**shade, "accent": group_color(name, mode)} for name, views, _ in GROUPS for view in views}
    links = "".join(build_relation(places, schema, relation, shades[relation[0]]) for relation in RELATIONS)
    child, child_column, parent, parent_column, label, meaning = LOGICAL
    y_a, y_b = row_y(places, child, child_column, schema), row_y(places, parent, parent_column, schema)
    path, _, _ = route(places, child, parent, y_a, y_b)
    # the name of the link over its first stretch, between the box and the turn
    label_x = places[child][0] - COLUMN_GAPS[-1] / 4
    logical = (
        f'<g class="er-link"><title>{html.escape(meaning)}</title>'
        f'<path d="{path}" stroke="{shade["muted"]}" stroke-width="1.4" stroke-dasharray="5 5" fill="none"/>'
        f'<text x="{label_x}" y="{y_a - 5}" text-anchor="middle" font-size="11" fill="{shade["muted"]}">'
        f"{html.escape(label)}</text></g>"
    )
    tables = "".join(build_view(view, schema, places, counts, shades[view], descriptions) for view in VIEWS)
    lines = (
        *(text for _, _, text in GROUPS),
        "Las ocho vistas están en la misma Base DuckDB · etl/datos.duckdb; el color dice qué guarda cada grupo.",
        "PK: las columnas que identifican una fila · FK: una columna que apunta a otra vista",
        "Pata de gallo: muchas filas · doble barra: una · círculo: puede no haber · línea punteada: mismo mes, sin clave",
        "precios: sus ocho columnas PK juntas identifican una fila; unidad queda vacía si no se pudo convertir.",
    )
    # in the free corner at the bottom left, the last line level with the end of the tallest column
    legend_y = bottom - MARGIN - 18 * (len(lines) - 1)
    legend = "".join(
        f'<text x="{MARGIN + 16 if index < len(GROUPS) else MARGIN}" y="{legend_y + 18 * index}" font-size="12" '
        f'fill="{shade["muted"]}">{html.escape(line)}</text>'
        for index, line in enumerate(lines)
    )
    # the colour of each group beside its words, never the colour alone
    legend += "".join(
        f'<rect class="er-group" x="{MARGIN}" y="{legend_y + 18 * index - 9}" width="10" height="10" rx="2" '
        f'fill="{group_color(name, mode)}"/>'
        for index, (name, _, _) in enumerate(GROUPS)
    )
    height = bottom
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Relaciones entre las vistas de Consultas SQL" font-family="{er_diagram.charts.CHART_FONT}">'
        f"{links}{logical}{tables}{legend}</svg>"
    )


# endregion
