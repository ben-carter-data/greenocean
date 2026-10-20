"""Entity-relationship diagram of the served database (D-195), in the classic notation.

One box per table with its real columns and DuckDB types, the primary and foreign keys in
a left column, the primary-key rows set apart by a rule, and the relationships as lines with
crow's feet (many), bars (one) and circles (zero). Which tables, columns, keys and
relationships exist is read or declared once here and checked against the database by the
tests: the types come from DESCRIBE, the relationships are the ones dbt tests
(dbt/models/marts/schema.yml) plus the one the quality page checks (rejection → etl_run).

The result is one static SVG, no script; each table and relationship explains itself on
hover through its <title>.
"""
import html

from bi import charts, queries

MARGIN = 20
HEADER = 34
ROW = 26
BOX_WIDTH = 250
LOWER_WIDTH = 215
# Gaps between the four boxes of the lower band: room for the crow's feet of the first pair
# and for the label of the logical link between the last two.
LOWER_GAPS = (46, 36, 74)
# The two boxes with the longest names beside their types need a little more room.
LOWER_WIDTHS = {"etl_run": 235, "ipc_weekly": 240}
FONT = 12.5
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# The tables of the model, in the order they are drawn. The dbt trace (dbt_node, dbt_result)
# and ine_ipc_source (a raw copy of the INE files) are not part of the model.
TABLES = ["dim_product", "dim_channel", "weekly_price", "dim_date", "dim_region",
          "etl_run", "rejection", "ipc_monthly", "ipc_weekly"]
PRIMARY_KEYS = {
    "dim_product": ["product_id"], "dim_region": ["region_id"], "dim_channel": ["channel_id"],
    "dim_date": ["week_start"],
    "weekly_price": ["week_start", "product_id", "region_id", "channel_id", "normalized_unit"],
    "etl_run": ["run_id"], "rejection": [], "ipc_weekly": ["week_start"], "ipc_monthly": ["year", "month"],
}
# (child table, child column, parent table, parent column, child end, parent end, what it says)
RELATIONS = [
    ("weekly_price", "week_start", "dim_date", "week_start", "many0", "one", "cada precio es de una semana"),
    ("weekly_price", "product_id", "dim_product", "product_id", "many0", "one", "cada precio es de un producto"),
    ("weekly_price", "region_id", "dim_region", "region_id", "many0", "one", "cada precio es de una región"),
    ("weekly_price", "channel_id", "dim_channel", "channel_id", "many0", "one", "cada precio es de un canal"),
    ("rejection", "run_id", "etl_run", "run_id", "many0", "one", "cada fila rechazada pertenece a una carga"),
    ("ipc_weekly", "week_start", "dim_date", "week_start", "zero_one", "one", "cada semana tiene a lo más un deflactor"),
]
# Not a foreign key: the same month, read by two tables.
LOGICAL = ("ipc_monthly", "month", "ipc_weekly", "ipc_year", "mismo mes",
           "ipc_weekly toma el IPC del mes de su lunes (ipc_year, ipc_month) de ipc_monthly (year, month)")
FOREIGN_KEYS = {(child, column) for child, column, *_ in RELATIONS}


def read_schema(database_file=queries.DATABASE_FILE):
    """{table: [(column, type)]} from DESCRIBE, for the tables of the model."""
    with queries.open_database(database_file) as connection:
        return {table: [(row[0], row[1]) for row in connection.execute(f'DESCRIBE main."{table}"').fetchall()]
                for table in TABLES}


def key_label(table, column):
    primary = column in PRIMARY_KEYS[table]
    foreign = (table, column) in FOREIGN_KEYS
    return "PK, FK" if primary and foreign else "PK" if primary else "FK" if foreign else ""


def layout(schema):
    """{table: (x, y, width, height)}: the star on top, the load trail and the IPC below."""
    height = {table: HEADER + len(schema[table]) * ROW for table in TABLES}
    left, center, right = MARGIN, MARGIN + BOX_WIDTH + 150, MARGIN + 2 * (BOX_WIDTH + 150) - 20
    top = MARGIN
    weekly_y = top + 40
    places = {
        "dim_product": (left, top, BOX_WIDTH, height["dim_product"]),
        "dim_channel": (left, top + height["dim_product"] + 50, BOX_WIDTH, height["dim_channel"]),
        "weekly_price": (center, weekly_y, BOX_WIDTH, height["weekly_price"]),
        "dim_date": (right, top, BOX_WIDTH, height["dim_date"]),
        "dim_region": (right, top + height["dim_date"] + 50, BOX_WIDTH, height["dim_region"]),
    }
    band = max(y + h for _, y, _, h in places.values()) + 70
    x = MARGIN
    for index, table in enumerate(("etl_run", "rejection", "ipc_monthly", "ipc_weekly")):
        width = LOWER_WIDTHS.get(table, LOWER_WIDTH)
        places[table] = (x, band, width, height[table])
        x += width + (LOWER_GAPS[index] if index < len(LOWER_GAPS) else 0)
    return places


def row_y(places, table, column, schema):
    _, y, _, _ = places[table]
    index = [name for name, _ in schema[table]].index(column)
    return y + HEADER + index * ROW + ROW / 2


def colors(mode):
    palette = charts.get_palette(mode)
    dark = palette["base"] == charts.BASE_DARK
    return dict(card=palette["card"], line=palette["card_border"], ink=palette["strong_text"], text=palette["text"],
                muted=palette["reference"], accent=palette["accent"], frame=palette["background"],
                header_opacity=".28" if dark else ".22")


def crow(x, y, direction, kind, color, fill):
    """The end of a relationship at a box edge; direction +1 when the line arrives moving right."""
    sign = -direction
    stroke = f'stroke="{color}" stroke-width="1.6" fill="none"'
    if kind == "many0":
        return (f'<path d="M{x + sign * 14} {y} L{x} {y - 8} M{x + sign * 14} {y} L{x} {y} M{x + sign * 14} {y} L{x} {y + 8}" {stroke}/>'
                f'<circle cx="{x + sign * 21}" cy="{y}" r="4.5" fill="{fill}" {stroke}/>')
    if kind == "zero_one":
        return (f'<circle cx="{x + sign * 18}" cy="{y}" r="4.5" fill="{fill}" {stroke}/>'
                f'<path d="M{x + sign * 9} {y - 7} V{y + 7}" {stroke}/>')
    return f'<path d="M{x + sign * 8} {y - 7} V{y + 7} M{x + sign * 14} {y - 7} V{y + 7}" {stroke}/>'


def build_table(table, schema, places, counts, tooltips, shade):
    x, y, width, height = places[table]
    rows = []
    primary = PRIMARY_KEYS[table]
    for index, (column, kind) in enumerate(schema[table]):
        base = y + HEADER + index * ROW
        rows.append(f'<text x="{x + 10}" y="{base + 17}" font-size="11" font-weight="600" fill="{shade["accent"]}">'
                    f'{key_label(table, column)}</text>'
                    f'<text x="{x + 50}" y="{base + 17}" font-family="{MONO}" font-size="{FONT}" fill="{shade["ink"]}">{html.escape(column)}</text>'
                    f'<text x="{x + width - 10}" y="{base + 17}" text-anchor="end" font-family="{MONO}" font-size="11" '
                    f'fill="{shade["muted"]}">{html.escape(kind)}</text>')
    rule = ""
    if primary:
        rule_y = y + HEADER + len(primary) * ROW
        rule = f'<path d="M{x} {rule_y} H{x + width}" stroke="{shade["line"]}" stroke-width="1.2"/>'
    count = counts.get(table)
    count_text = (f'<text x="{x + width - 10}" y="{y + 22}" text-anchor="end" font-size="10.5" fill="{shade["muted"]}">'
                  f'{charts.format_thousands(count)} filas</text>') if count is not None else ""
    title = f'<title>{html.escape(tooltips.get(table, table))}</title>'
    return (f'<g class="er-table er-{table}">{title}'
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="6" fill="{shade["card"]}" stroke="{shade["line"]}" stroke-width="1.4"/>'
            f'<path d="M{x} {y + HEADER} V{y + 6} Q{x} {y} {x + 6} {y} H{x + width - 6} Q{x + width} {y} {x + width} {y + 6} V{y + HEADER} Z" '
            f'fill="{shade["accent"]}" fill-opacity="{shade["header_opacity"]}"/>'
            f'<text x="{x + 10}" y="{y + 22}" font-size="14" font-weight="600" fill="{shade["ink"]}">{html.escape(table)}</text>'
            f'{count_text}{rule}{"".join(rows)}</g>')


def attach(box, edge):
    """(x, arrival) where a line meets a box: on its left or right edge. The arrival is +1
    when the line comes from the left (it meets the left edge) and -1 from the right."""
    x, _, width, _ = box
    return (x, 1) if edge == "left" else (x + width, -1)


def route(places, relation, y_child, y_parent):
    """The path of a relationship and the edge it meets on each box."""
    child, _, parent, *_ = relation
    c, p = places[child], places[parent]
    if c[1] == p[1]:  # side by side on one band: a straight line between the facing edges
        child_edge, parent_edge = ("left", "right") if p[0] < c[0] else ("right", "left")
        (xc, _), (xp, _) = attach(c, child_edge), attach(p, parent_edge)
        return f"M{xc} {y_child} H{xp}", child_edge, parent_edge
    if child == "ipc_weekly":  # both on the right: round the right margin, up to dim_date
        xc, xp = c[0] + c[2], p[0] + p[2]
        far = max(xc, xp) + 22
        return f"M{xc} {y_child} H{far} V{y_parent} H{xp}", "right", "right"
    child_edge, parent_edge = ("left", "right") if p[0] + p[2] <= c[0] else ("right", "left")
    (xc, _), (xp, _) = attach(c, child_edge), attach(p, parent_edge)
    middle = (xc + xp) / 2
    return f"M{xc} {y_child} H{middle} V{y_parent} H{xp}", child_edge, parent_edge


def build_relation(places, schema, relation, shade):
    child, child_column, parent, parent_column, child_end, parent_end, meaning = relation
    y_child = row_y(places, child, child_column, schema)
    y_parent = row_y(places, parent, parent_column, schema)
    path, child_edge, parent_edge = route(places, relation, y_child, y_parent)
    (xc, child_arrival), (xp, parent_arrival) = attach(places[child], child_edge), attach(places[parent], parent_edge)
    title = f'<title>{child}.{child_column} → {parent}.{parent_column} · {html.escape(meaning)}</title>'
    return (f'<g class="er-link">{title}<path d="{path}" fill="none" stroke="{shade["accent"]}" stroke-width="1.6"/>'
            f'{crow(xc, y_child, child_arrival, child_end, shade["accent"], shade["card"])}'
            f'{crow(xp, y_parent, parent_arrival, parent_end, shade["accent"], shade["card"])}</g>')


def build_er_svg(schema, counts, mode, tooltips=None):
    """The diagram: tables, relationships and the legend, as one SVG."""
    shade = colors(mode)
    places = layout(schema)
    tooltips = tooltips or {}
    width = max(x + w for x, _, w, _ in places.values()) + 52
    bottom = max(y + h for _, y, _, h in places.values()) + MARGIN
    links = "".join(build_relation(places, schema, relation, shade) for relation in RELATIONS)
    child, child_column, parent, parent_column, label, meaning = LOGICAL
    y_a = row_y(places, child, child_column, schema)
    logical = (f'<g class="er-link"><title>{html.escape(meaning)}</title>'
               f'<path d="M{places[child][0] + places[child][2]} {y_a} H{places[parent][0]}" stroke="{shade["muted"]}" '
               f'stroke-width="1.4" stroke-dasharray="5 5" fill="none"/>'
               f'<text x="{(places[child][0] + places[child][2] + places[parent][0]) / 2}" y="{y_a - 8}" text-anchor="middle" '
               f'font-size="11" fill="{shade["muted"]}">{html.escape(label)}</text></g>')
    tables = "".join(build_table(table, schema, places, counts, tooltips, shade) for table in TABLES)
    legend_y = bottom + 16
    legend = (f'<text x="{MARGIN}" y="{legend_y}" font-size="12" fill="{shade["muted"]}">PK clave primaria · FK clave foránea · '
              f'pata de gallo: muchas filas · doble barra: una · círculo: puede no haber · línea punteada: relación lógica, sin clave foránea</text>'
              f'<text x="{MARGIN}" y="{legend_y + 18}" font-size="12" fill="{shade["muted"]}">Fuera del diagrama: ine_ipc_source '
              f'(copia cruda del INE), dbt_node y dbt_result (la traza de dbt).</text>')
    total = bottom + 56
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total}" width="100%" role="img" '
            f'aria-label="Modelo entidad-relación de datos.duckdb" font-family="{charts.CHART_FONT}">'
            f'{links}{logical}{tables}{legend}</svg>')
