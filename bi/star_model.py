"""Star model of datos.duckdb drawn as a real star (T-59, redesigned for D-097, D-190, D-503).

A soft four-pointed star behind the cards, the fact table weekly_price in the
middle and two dimensions on each side (D-503, landscape, so the drawing fills
its panel): dim_date and dim_product stacked on the left, dim_region and
dim_channel on the right, each joined to the fact table by a right-angled
connector. Each card lists every real column of etl/schema.sql, with primary
and foreign keys in cyan; the measures of the fact table sit apart at its foot.
Closing the right column, separated from the star, a small group shows the audit
trail of a load: etl_run → rejection. In the leftmost column, beside dim_date, a
second group shows the food IPC of the INE (ine_ipc_source → ipc_monthly →
ipc_weekly), joined to dim_date by week_start (D-190).

Positions are computed from the real column counts of each table, so the
diagram never overlaps even if a table gains or loses a column. The result is
one static SVG (no pan, no zoom, no JavaScript): which table it explains is
chosen in Streamlit, not by hovering the diagram.
"""

import html

from bi import charts

# region Constants
CYAN = "#22d3ee"
# On a white card the light cyan is too pale for text: a darker one of the same hue.
CYAN_ON_LIGHT = "#0e7490"
VANTABLACK_CARD = "#000000"
VANTABLACK_FRAME = "#0b0b0d"
MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

MARGIN = 20
# Horizontal gap between the fact table and each dimension column; vertical gap between the
# cards stacked in a column (D-503).
GAP = 40
# The measures of the fact table: what the indicators analyze.
MEASURES = ["price", "volume", "observation_count"]
ROW_HEIGHT = 27
TITLE_HEIGHT = 52  # from the card top to the divider line under a plain title
TITLE_HEIGHT_SUBTITLE = 66  # same, when the title also carries a subtitle
FIRST_ROW_GAP = 28  # from the divider line to the first content row

STAR_TABLE = "weekly_price"
# D-503: two dimensions on each side of the fact table, each column top to bottom.
LEFT_DIMENSIONS = ("dim_date", "dim_product")
RIGHT_DIMENSIONS = ("dim_region", "dim_channel")
IPC_DIMENSION = "dim_date"  # the dimension the IPC group hangs from (D-190)
DIMENSION_WIDTH = 250
FACT_WIDTH = 300
AUDIT_TABLES = ("etl_run", "rejection")
AUDIT_WIDTH = 230
AUDIT_HEIGHT = 56
AUDIT_GAP = 34
GROUP_LABEL_HEIGHT = 22  # the small heading above the audit and IPC groups
# The food IPC, leftmost column: source rows → monthly series → weekly deflator (D-190).
IPC_TABLES = ("ine_ipc_source", "ipc_monthly", "ipc_weekly")
IPC_GAP = 26
IPC_COLUMN_GAP = 30  # between the IPC column and dim_date
IPC_NOTES = {
    "ine_ipc_source": "tal como las publica",
    "ipc_monthly": "base 2023 = 100",
    "ipc_weekly": "week_start → dim_date",
}

# The columns, left to right: the IPC group, two dimensions, the fact table, two dimensions
# (D-503). The drawing is about twice as wide as tall, the proportion of its panel.
IPC_X = MARGIN
LEFT_X = IPC_X + AUDIT_WIDTH + IPC_COLUMN_GAP
FACT_X = LEFT_X + DIMENSION_WIDTH + GAP
RIGHT_X = FACT_X + FACT_WIDTH + GAP
WIDTH = RIGHT_X + DIMENSION_WIDTH + MARGIN
AUDIT_GROUP_HEIGHT = GROUP_LABEL_HEIGHT + 2 * AUDIT_HEIGHT + AUDIT_GAP
IPC_GROUP_HEIGHT = GROUP_LABEL_HEIGHT + 3 * AUDIT_HEIGHT + 2 * IPC_GAP
# endregion


# region Colors
def get_colors(mode):
    """Card, frame, cyan and text colors of the active theme."""
    palette = charts.get_palette(mode)
    if mode == charts.MODE_DARK:
        return {
            "card": VANTABLACK_CARD,
            "frame": VANTABLACK_FRAME,
            "cyan": CYAN,
            "text": palette["text"],
            "strong_text": palette["strong_text"],
            "line": palette["card_border"],
        }
    # Dark Grey keeps the bright cyan; the light themes take the darker one.
    cyan = CYAN if palette["base"] == charts.BASE_DARK else CYAN_ON_LIGHT
    return {
        "card": palette["card"],
        "frame": palette["background"],
        "cyan": cyan,
        "text": palette["text"],
        "strong_text": palette["strong_text"],
        "line": palette["card_border"],
    }


# endregion


# region Layout
def list_fact_lines(columns):
    """(keys and attributes, measures) of weekly_price: foreign keys first."""
    attributes = [column for column in columns if column[0] not in MEASURES]
    attributes.sort(key=lambda column: column[1] != "FK")
    return attributes, [column for column in columns if column[0] in MEASURES]


def dimension_card_height(column_count):
    """Height of a dimension card: title, divider and one row per real column."""
    return TITLE_HEIGHT + FIRST_ROW_GAP + column_count * ROW_HEIGHT + 4


def fact_card_height(attribute_count, measure_count):
    """Height of the fact card: title with subtitle, keys, a divider, then measures."""
    return TITLE_HEIGHT_SUBTITLE + FIRST_ROW_GAP + 18 + (attribute_count + measure_count) * ROW_HEIGHT


def compute_layout(columns_by_table):
    """{table: (x, y, width, height)} for the five star cards, never overlapping (D-503).

    weekly_price sits in the middle; dim_date and dim_product are stacked on its
    left, dim_region and dim_channel on its right, with the audit group closing
    the right column. Every column is centred on the tallest one, and heights
    come straight from each table's real column count.
    """
    attributes, measures = list_fact_lines(columns_by_table[STAR_TABLE])
    fact_height = fact_card_height(len(attributes), len(measures))
    left_heights = [dimension_card_height(len(columns_by_table[table])) for table in LEFT_DIMENSIONS]
    right_heights = [dimension_card_height(len(columns_by_table[table])) for table in RIGHT_DIMENSIONS]
    left_total = sum(left_heights) + GAP * (len(LEFT_DIMENSIONS) - 1)
    right_total = sum(right_heights) + GAP * len(RIGHT_DIMENSIONS) + AUDIT_GROUP_HEIGHT
    content = max(left_total, right_total, fact_height, IPC_GROUP_HEIGHT)

    layout = {STAR_TABLE: (FACT_X, MARGIN + (content - fact_height) / 2, FACT_WIDTH, fact_height)}
    for x, tables, heights, total in (
        (LEFT_X, LEFT_DIMENSIONS, left_heights, left_total),
        (RIGHT_X, RIGHT_DIMENSIONS, right_heights, right_total),
    ):
        y = MARGIN + (content - total) / 2
        for table, card_height in zip(tables, heights):
            layout[table] = (x, y, DIMENSION_WIDTH, card_height)
            y += card_height + GAP
    return layout, MARGIN + content + MARGIN


def audit_rect(layout):
    """Where the audit group sits: closing the right column, under its last dimension (D-503)."""
    x, y, _, card_height = layout[RIGHT_DIMENSIONS[-1]]
    return (x, y + card_height + GAP, AUDIT_WIDTH, AUDIT_GROUP_HEIGHT)


def ipc_rect(layout):
    """Where the IPC group sits: the leftmost column, centred on dim_date, never above the margin."""
    _, date_y, _, date_height = layout[IPC_DIMENSION]
    return (IPC_X, max(MARGIN, date_y + (date_height - IPC_GROUP_HEIGHT) / 2), AUDIT_WIDTH, IPC_GROUP_HEIGHT)


# endregion


# region Cards
def build_column_text(x, y, name, kind, colors, size=17):
    """One column line: keys and measures in cyan, with their (PK) or (FK) mark."""
    is_cyan = kind in ("PK", "MEASURE")
    label = f"{name} ({kind})" if kind in ("PK", "FK") else name
    color = colors["cyan"] if is_cyan else colors["strong_text"]
    return (
        f'<text x="{x}" y="{y}" font-family="{MONO_FONT}" font-size="{size}" fill="{color}">{html.escape(label)}</text>'
    )


def build_card_frame(table, rect, colors, is_fact=False, selected=False, tooltip=None):
    """Card background; its explanation shows on hover (D-147)."""
    x, y, width, height = rect
    stroke_width = 3 if selected else 2.6 if is_fact else 1.4
    glow = f' filter="drop-shadow(0 0 5px {colors["cyan"]})"' if selected else ""
    title = f'<title>{html.escape(tooltip)}</title>' if tooltip else ""
    return (
        f'<g class="star-table star-{table}"{glow}>{title}'
        f'<rect class="star-card" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" '
        f'height="{height:.1f}" rx="16" fill="{colors["card"]}" '
        f'stroke="{colors["cyan"]}" stroke-width="{stroke_width}"/>'
    )


def build_card_title(rect, title, colors, subtitle=None):
    """Card heading and the line under it; returns (svg, y of the first row)."""
    x, y, width, _ = rect
    middle = x + width / 2
    color = colors["cyan"] if subtitle else colors["strong_text"]
    parts = [
        f'<text x="{middle:.1f}" y="{y + 34:.1f}" text-anchor="middle" font-size="21" '
        f'font-weight="700" fill="{color}">{html.escape(title)}</text>'
    ]
    line_y = y + (TITLE_HEIGHT_SUBTITLE if subtitle else TITLE_HEIGHT)
    if subtitle:
        parts.append(
            f'<text x="{middle:.1f}" y="{y + 56:.1f}" text-anchor="middle" font-size="15" '
            f'fill="{colors["text"]}">{html.escape(subtitle)}</text>'
        )
    parts.append(
        f'<path d="M{x + 18:.1f} {line_y:.1f} H{x + width - 18:.1f}" stroke="{colors["line"]}" stroke-width="1"/>'
    )
    return "".join(parts), line_y + FIRST_ROW_GAP


def build_dimension_card(table, rect, columns, colors, selected=False, tooltip=None):
    """A dimension: its name and every real column, the primary key in cyan."""
    x, y, _, _ = rect
    title, first_y = build_card_title(rect, table, colors)
    rows = "".join(
        build_column_text(x + 20, first_y + position * ROW_HEIGHT, name, kind, colors)
        for position, (name, kind) in enumerate(columns)
    )
    return build_card_frame(table, rect, colors, selected=selected, tooltip=tooltip) + title + rows + "</g>"


def build_fact_card(rect, columns, row_count, colors, selected=False, tooltip=None):
    """weekly_price: its keys and attributes, then the measures apart, in cyan."""
    x, y, width, _ = rect
    attributes, measures = list_fact_lines(columns)
    subtitle = f"hechos · {charts.format_thousands(row_count)} filas"
    title, first_y = build_card_title(rect, "weekly_price", colors, subtitle)
    rows = [
        build_column_text(x + 20, first_y + position * ROW_HEIGHT, name, kind, colors)
        for position, (name, kind) in enumerate(attributes)
    ]
    divider_y = first_y + len(attributes) * ROW_HEIGHT - 10
    rows.append(
        f'<path d="M{x + 18:.1f} {divider_y:.1f} H{x + width - 18:.1f}" stroke="{colors["line"]}" stroke-width="1"/>'
    )
    rows += [
        build_column_text(x + 20, divider_y + FIRST_ROW_GAP + position * ROW_HEIGHT, name, "MEASURE", colors)
        for position, (name, _) in enumerate(measures)
    ]
    return (
        build_card_frame(STAR_TABLE, rect, colors, is_fact=True, selected=selected, tooltip=tooltip)
        + title
        + "".join(rows)
        + "</g>"
    )


# endregion


# region Star
def build_star_background(colors, center_x, center_y, spread_x, spread_y):
    """A soft four-pointed star behind the cards, purely decorative; its side points reach
    the dimension columns (D-503: wider than tall, like the drawing)."""
    points = [
        (center_x, center_y - spread_y),
        (center_x + spread_x, center_y),
        (center_x, center_y + spread_y),
        (center_x - spread_x, center_y),
    ]
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points) + "Z"
    return (
        f'<path d="{path}" fill="{CYAN}" fill-opacity="0.06" '
        f'stroke="{colors["cyan"]}" stroke-opacity="0.2" stroke-width="1"/>'
    )


def build_dashed_elbow(colors, x1, y1, x2, y2):
    """A dashed cyan link with right angles: across to the middle of the gap, up or down,
    then across again (D-503). On one level it is a straight line."""
    middle_x = (x1 + x2) / 2
    return (
        f'<path d="M{x1:.1f} {y1:.1f} H{middle_x:.1f} V{y2:.1f} H{x2:.1f}" fill="none" '
        f'stroke="{colors["cyan"]}" stroke-width="1.4" stroke-dasharray="5 5"/>'
    )


def build_connector(colors, fact_rect, card_rect, side, position):
    """The link from a dimension to the fact table: from the middle of the dimension's facing
    edge to the fact's edge at `position` (a fraction of its height), with right angles."""
    fx, fy, fw, fh = fact_rect
    cx, cy, cw, ch = card_rect
    fact_y = fy + fh * position
    if side == "left":
        return build_dashed_elbow(colors, cx + cw, cy + ch / 2, fx, fact_y)
    return build_dashed_elbow(colors, fx + fw, fact_y, cx, cy + ch / 2)


def build_audit_group(row_counts, colors, rect, tooltips=None):
    """weekly_price's load trail, apart from the star: etl_run → rejection."""
    x, top = rect[0], rect[1] + GROUP_LABEL_HEIGHT
    label = (
        f'<text x="{x:.1f}" y="{top - 10:.1f}" font-size="13" font-weight="700" '
        f'letter-spacing=".04em" fill="{colors["text"]}">AUDITORÍA DE CARGAS</text>'
    )
    boxes = []
    y = top
    for index, table in enumerate(AUDIT_TABLES):
        tooltip = (tooltips or {}).get(table)
        boxes.append(
            (f'<g><title>{html.escape(tooltip)}</title>' if tooltip else '<g>')
            + f'<rect x="{x:.1f}" y="{y:.1f}" width="{AUDIT_WIDTH}" height="{AUDIT_HEIGHT}" '
            f'rx="12" fill="{colors["card"]}" stroke="{colors["cyan"]}" stroke-width="1.4" '
            f'stroke-dasharray="4 4"/>'
            f'<text x="{x + 16:.1f}" y="{y + 23:.1f}" font-family="{MONO_FONT}" font-size="15" '
            f'fill="{colors["strong_text"]}">{html.escape(table)}</text>'
            f'<text x="{x + 16:.1f}" y="{y + 42:.1f}" font-size="12" fill="{colors["text"]}">'
            f'{charts.format_thousands(row_counts[table])} filas</text></g>'
        )
        if index == 0:
            arrow_y = y + AUDIT_HEIGHT
            boxes.append(
                f'<path d="M{x + AUDIT_WIDTH / 2:.1f} {arrow_y:.1f} '
                f'L{x + AUDIT_WIDTH / 2:.1f} {arrow_y + AUDIT_GAP - 8:.1f}" '
                f'stroke="{colors["cyan"]}" stroke-width="1.4" marker-end="url(#audit-arrow)"/>'
                f'<text x="{x + AUDIT_WIDTH / 2 + 8:.1f}" y="{arrow_y + AUDIT_GAP / 2 + 4:.1f}" '
                f'font-size="11" fill="{colors["text"]}">run_id (FK)</text>'
            )
        y += AUDIT_HEIGHT + AUDIT_GAP
    return label + "".join(boxes)


def build_ipc_group(row_counts, colors, rect, date_rect, tooltips=None):
    """The food IPC beside dim_date: three dashed boxes in a chain and a dashed link from
    ipc_weekly to dim_date (D-190). Drawn only when the counts of its tables are known."""
    if not all(table in row_counts for table in IPC_TABLES):
        return ""
    x, top = rect[0], rect[1] + GROUP_LABEL_HEIGHT
    parts = [
        f'<text x="{x:.1f}" y="{top - 12:.1f}" font-size="13" font-weight="700" letter-spacing=".04em" '
        f'fill="{colors["text"]}">IPC DE ALIMENTOS (INE)</text>'
    ]
    y = top
    for index, table in enumerate(IPC_TABLES):
        tooltip = (tooltips or {}).get(table)
        parts.append(
            (f'<g><title>{html.escape(tooltip)}</title>' if tooltip else '<g>')
            + f'<rect x="{x:.1f}" y="{y:.1f}" width="{AUDIT_WIDTH}" height="{AUDIT_HEIGHT}" rx="12" '
            f'fill="{colors["card"]}" stroke="{colors["cyan"]}" stroke-width="1.4" stroke-dasharray="4 4"/>'
            f'<text x="{x + 16:.1f}" y="{y + 23:.1f}" font-family="{MONO_FONT}" font-size="15" '
            f'fill="{colors["strong_text"]}">{html.escape(table)}</text>'
            f'<text x="{x + 16:.1f}" y="{y + 42:.1f}" font-size="12" fill="{colors["text"]}">'
            f'{charts.format_thousands(row_counts[table])} filas · {html.escape(IPC_NOTES[table])}</text></g>'
        )
        if index < len(IPC_TABLES) - 1:
            arrow_y = y + AUDIT_HEIGHT
            parts.append(
                f'<path d="M{x + AUDIT_WIDTH / 2:.1f} {arrow_y:.1f} L{x + AUDIT_WIDTH / 2:.1f} '
                f'{arrow_y + IPC_GAP - 6:.1f}" stroke="{colors["cyan"]}" stroke-width="1.4" '
                f'marker-end="url(#audit-arrow)"/>'
            )
        y += AUDIT_HEIGHT + IPC_GAP
    weekly_y = top + 2 * (AUDIT_HEIGHT + IPC_GAP) + AUDIT_HEIGHT / 2
    dx, dy, _, dh = date_rect
    # The link meets dim_date on the level of ipc_weekly when that level is on the card; if not
    # (a short dim_date), it bends to the middle of the card.
    date_y = weekly_y if dy + 12 <= weekly_y <= dy + dh - 12 else dy + dh / 2
    parts.append(build_dashed_elbow(colors, x + AUDIT_WIDTH, weekly_y, dx, date_y))
    return "".join(parts)


def build_star_svg(columns_by_table, row_counts, mode, selected=None, tooltips=None):
    """The whole diagram: background, connectors, five cards and the audit trail.
    tooltips: {table: text shown on hover}."""
    tooltips = tooltips or {}
    colors = get_colors(mode)
    layout, height = compute_layout(columns_by_table)
    fact_rect = layout[STAR_TABLE]
    center_x, center_y = fact_rect[0] + fact_rect[2] / 2, fact_rect[1] + fact_rect[3] / 2
    spread_x = FACT_WIDTH / 2 + GAP + DIMENSION_WIDTH / 2
    spread_y = fact_rect[3] / 2 + 36

    cards = [
        build_dimension_card(
            table,
            layout[table],
            columns_by_table[table],
            colors,
            selected=selected == table,
            tooltip=tooltips.get(table),
        )
        for table in LEFT_DIMENSIONS + RIGHT_DIMENSIONS
    ]
    cards.append(
        build_fact_card(
            fact_rect,
            columns_by_table[STAR_TABLE],
            row_counts[STAR_TABLE],
            colors,
            selected=selected == STAR_TABLE,
            tooltip=tooltips.get(STAR_TABLE),
        )
    )
    # D-503: the upper dimension of each column meets the fact table at a third of its height,
    # the lower one at two thirds, so the two links of a side never share a segment.
    connectors = "".join(
        build_connector(colors, fact_rect, layout[table], side, (index + 1) / (len(tables) + 1))
        for side, tables in (("left", LEFT_DIMENSIONS), ("right", RIGHT_DIMENSIONS))
        for index, table in enumerate(tables)
    )
    audit = build_audit_group(row_counts, colors, audit_rect(layout), tooltips)
    ipc = build_ipc_group(row_counts, colors, ipc_rect(layout), layout[IPC_DIMENSION], tooltips)
    defs = (
        f'<defs><marker id="audit-arrow" viewBox="0 0 10 10" refX="8" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0 0 L10 5 L0 10 Z" fill="{colors["cyan"]}"/></marker></defs>'
    )
    return ''.join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height:.0f}" '
            f'width="100%" role="img" aria-label="Modelo estrella de datos.duckdb" '
            f'font-family="{charts.CHART_FONT}">',
            defs,
            build_star_background(colors, center_x, center_y, spread_x, spread_y),
            connectors,
            audit,
            ipc,
            *cards,
            "</svg>",
        ]
    )


# endregion
