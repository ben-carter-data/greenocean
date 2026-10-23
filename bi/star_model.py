"""Star model of datos.duckdb drawn as a real star (T-59, redesigned for D-097, D-190).

A soft four-pointed star behind the cards, the fact table weekly_price in the
middle and one dimension on each point: dim_date on top, dim_product on the
left, dim_region on the right and dim_channel at the bottom. Each card lists
every real column of etl/schema.sql, with primary and foreign keys in cyan;
the measures of the fact table sit apart at its foot. Below and to the right,
separated from the star, a small group shows the audit trail of a load:
etl_run → rejection. At the top left, a second group shows the food IPC of the INE
(ine_ipc_source → ipc_monthly → ipc_weekly), joined to dim_date by week_start (D-190).

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

WIDTH = 1000
MARGIN = 20
# Vertical gap between two cards of a column; horizontal gap between the columns.
GAP = 26
COLUMN_GAP = 60
# The measures of the fact table: what the indicators analyze.
MEASURES = ["price", "volume", "observation_count"]
ROW_HEIGHT = 24
TITLE_HEIGHT = 50       # from the card top to the divider line under a plain title
TITLE_HEIGHT_SUBTITLE = 66  # same, when the title also carries a subtitle
FIRST_ROW_GAP = 26      # from the divider line to the first content row

STAR_TABLE = "weekly_price"
DATE_TABLE = "dim_date"
RIGHT_DIMENSIONS = ("dim_product", "dim_region", "dim_channel")
DIMENSION_WIDTH = 250
FACT_WIDTH = 340
AUDIT_TABLES = ("etl_run", "rejection")
BOX_WIDTH = DIMENSION_WIDTH
BOX_HEIGHT = 52
AUDIT_GAP = 24
# The food IPC, above dim_date: source rows → monthly series → weekly deflator (D-190).
IPC_TABLES = ("ine_ipc_source", "ipc_monthly", "ipc_weekly")
IPC_GAP = 20
IPC_LABEL_HEIGHT = 26
IPC_NOTES = {"ine_ipc_source": "tal como las publica", "ipc_monthly": "base 2023 = 100",
             "ipc_weekly": "week_start → dim_date"}
# endregion


# region Colors
def get_colors(mode):
    """Card, frame, cyan and text colors of the active theme."""
    palette = charts.get_palette(mode)
    if mode == charts.MODE_DARK:
        return {"card": VANTABLACK_CARD, "frame": VANTABLACK_FRAME, "cyan": CYAN,
                "text": palette["text"], "strong_text": palette["strong_text"],
                "line": palette["card_border"]}
    # Dark Grey keeps the bright cyan; the light themes take the darker one.
    cyan = CYAN if palette["base"] == charts.BASE_DARK else CYAN_ON_LIGHT
    return {"card": palette["card"], "frame": palette["background"], "cyan": cyan,
            "text": palette["text"], "strong_text": palette["strong_text"],
            "line": palette["card_border"]}
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


def ipc_group_height():
    return IPC_LABEL_HEIGHT + len(IPC_TABLES) * BOX_HEIGHT + (len(IPC_TABLES) - 1) * IPC_GAP


def audit_group_height():
    return IPC_LABEL_HEIGHT + len(AUDIT_TABLES) * BOX_HEIGHT + (len(AUDIT_TABLES) - 1) * AUDIT_GAP


def compute_layout(columns_by_table):
    """({table: (x, y, width, height)} for the five star cards, positions of the two side groups, height).

    Three columns, so the drawing is wider than tall and fills its card: the IPC chain over dim_date on the
    left; the fact table in the middle with the load audit under it; dim_product, dim_region and dim_channel
    on the right. Heights come straight from each table's real column count, so nothing overlaps."""
    attributes, measures = list_fact_lines(columns_by_table[STAR_TABLE])
    fact_height = fact_card_height(len(attributes), len(measures))
    left_x = MARGIN
    fact_x = (WIDTH - FACT_WIDTH) / 2
    right_x = WIDTH - MARGIN - DIMENSION_WIDTH

    ipc_top = MARGIN
    date_height = dimension_card_height(len(columns_by_table[DATE_TABLE]))
    date_y = ipc_top + ipc_group_height() + 2 * GAP
    layout = {DATE_TABLE: (left_x, date_y, DIMENSION_WIDTH, date_height)}

    y = MARGIN
    for table in RIGHT_DIMENSIONS:
        card_height = dimension_card_height(len(columns_by_table[table]))
        layout[table] = (right_x, y, DIMENSION_WIDTH, card_height)
        y += card_height + GAP
    right_bottom = y - GAP

    fact_y = MARGIN
    layout[STAR_TABLE] = (fact_x, fact_y, FACT_WIDTH, fact_height)
    audit_top = fact_y + fact_height + 2 * GAP
    groups = {"ipc": (left_x, ipc_top), "audit": ((WIDTH - BOX_WIDTH) / 2, audit_top)}
    bottom = max(right_bottom, date_y + date_height, audit_top + audit_group_height())
    return layout, groups, bottom + MARGIN
# endregion


# region Cards
def build_column_text(x, y, name, kind, colors, size=17):
    """One column line: keys and measures in cyan, with their (PK) or (FK) mark."""
    is_cyan = kind in ("PK", "MEASURE")
    label = f"{name} ({kind})" if kind in ("PK", "FK") else name
    color = colors["cyan"] if is_cyan else colors["strong_text"]
    return (f'<text x="{x}" y="{y}" font-family="{MONO_FONT}" font-size="{size}" '
            f'fill="{color}">{html.escape(label)}</text>')


def build_card_frame(table, rect, colors, is_fact=False, selected=False, tooltip=None):
    """Card background; its explanation shows on hover (D-147)."""
    x, y, width, height = rect
    stroke_width = 3 if selected else 2.6 if is_fact else 1.4
    glow = f' filter="drop-shadow(0 0 5px {colors["cyan"]})"' if selected else ""
    title = f'<title>{html.escape(tooltip)}</title>' if tooltip else ""
    return (f'<g class="star-table star-{table}"{glow}>{title}'
            f'<rect class="star-card" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" '
            f'height="{height:.1f}" rx="16" fill="{colors["card"]}" '
            f'stroke="{colors["cyan"]}" stroke-width="{stroke_width}"/>')


def build_card_title(rect, title, colors, subtitle=None):
    """Card heading and the line under it; returns (svg, y of the first row)."""
    x, y, width, _ = rect
    middle = x + width / 2
    color = colors["cyan"] if subtitle else colors["strong_text"]
    parts = [f'<text x="{middle:.1f}" y="{y + 34:.1f}" text-anchor="middle" font-size="21" '
             f'font-weight="700" fill="{color}">{html.escape(title)}</text>']
    line_y = y + (TITLE_HEIGHT_SUBTITLE if subtitle else TITLE_HEIGHT)
    if subtitle:
        parts.append(f'<text x="{middle:.1f}" y="{y + 56:.1f}" text-anchor="middle" font-size="15" '
                     f'fill="{colors["text"]}">{html.escape(subtitle)}</text>')
    parts.append(f'<path d="M{x + 18:.1f} {line_y:.1f} H{x + width - 18:.1f}" '
                 f'stroke="{colors["line"]}" stroke-width="1"/>')
    return "".join(parts), line_y + FIRST_ROW_GAP


def build_dimension_card(table, rect, columns, colors, selected=False, tooltip=None):
    """A dimension: its name and every real column, the primary key in cyan."""
    x, y, _, _ = rect
    title, first_y = build_card_title(rect, table, colors)
    rows = "".join(build_column_text(x + 20, first_y + position * ROW_HEIGHT, name, kind, colors)
                   for position, (name, kind) in enumerate(columns))
    return build_card_frame(table, rect, colors, selected=selected, tooltip=tooltip) + title + rows + "</g>"


def build_fact_card(rect, columns, row_count, colors, selected=False, tooltip=None):
    """weekly_price: its keys and attributes, then the measures apart, in cyan."""
    x, y, width, _ = rect
    attributes, measures = list_fact_lines(columns)
    subtitle = f"hechos · {charts.format_thousands(row_count)} filas"
    title, first_y = build_card_title(rect, "weekly_price", colors, subtitle)
    rows = [build_column_text(x + 20, first_y + position * ROW_HEIGHT, name, kind, colors)
            for position, (name, kind) in enumerate(attributes)]
    divider_y = first_y + len(attributes) * ROW_HEIGHT - 10
    rows.append(f'<path d="M{x + 18:.1f} {divider_y:.1f} H{x + width - 18:.1f}" '
                f'stroke="{colors["line"]}" stroke-width="1"/>')
    rows += [build_column_text(x + 20, divider_y + FIRST_ROW_GAP + position * ROW_HEIGHT, name,
                               "MEASURE", colors)
             for position, (name, _) in enumerate(measures)]
    return (build_card_frame(STAR_TABLE, rect, colors, is_fact=True, selected=selected, tooltip=tooltip) + title
            + "".join(rows) + "</g>")
# endregion


# region Star
def build_star_background(colors, center_x, center_y, spread):
    """A soft four-pointed star behind the fact table, purely decorative."""
    points = [(center_x, center_y - spread), (center_x + spread * .5, center_y),
              (center_x, center_y + spread), (center_x - spread * .5, center_y)]
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points) + "Z"
    return (f'<path d="{path}" fill="{CYAN}" fill-opacity="0.06" '
            f'stroke="{colors["cyan"]}" stroke-opacity="0.2" stroke-width="1"/>')


def build_connector(colors, fact_rect, card_rect, side):
    """A dashed cyan line from the facing edge of the fact table to a dimension."""
    fx, fy, fw, fh = fact_rect
    cx, cy, cw, ch = card_rect
    if side == "left":
        x1, y1, x2, y2 = fx, fy + fh / 2, cx + cw, cy + ch / 2
    else:
        x1, y1, x2, y2 = fx + fw, fy + fh / 2, cx, cy + ch / 2
    return (f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="{colors["cyan"]}" '
            f'stroke-width="1.4" stroke-dasharray="5 5"/>')


def build_chain(tables, row_counts, colors, x, top, label, gap, notes=None, tooltips=None, dashed_arrow="audit-arrow",
                arrow_note=None):
    """A group of dashed boxes in a vertical chain, under a small label."""
    parts = [f'<text x="{x:.1f}" y="{top + 14:.1f}" font-size="13" font-weight="700" letter-spacing=".04em" '
             f'fill="{colors["text"]}">{html.escape(label)}</text>']
    y = top + IPC_LABEL_HEIGHT
    for index, table in enumerate(tables):
        tooltip = (tooltips or {}).get(table)
        note = f" · {html.escape(notes[table])}" if notes and table in notes else ""
        parts.append((f'<g><title>{html.escape(tooltip)}</title>' if tooltip else '<g>')
                     + f'<rect x="{x:.1f}" y="{y:.1f}" width="{BOX_WIDTH}" height="{BOX_HEIGHT}" rx="12" '
                     f'fill="{colors["card"]}" stroke="{colors["cyan"]}" stroke-width="1.4" stroke-dasharray="4 4"/>'
                     f'<text x="{x + 16:.1f}" y="{y + 22:.1f}" font-family="{MONO_FONT}" font-size="15" '
                     f'fill="{colors["strong_text"]}">{html.escape(table)}</text>'
                     f'<text x="{x + 16:.1f}" y="{y + 41:.1f}" font-size="13" fill="{colors["text"]}">'
                     f'{charts.format_thousands(row_counts[table])} filas{note}</text></g>')
        if index < len(tables) - 1:
            arrow_y = y + BOX_HEIGHT
            parts.append(f'<path d="M{x + BOX_WIDTH / 2:.1f} {arrow_y:.1f} L{x + BOX_WIDTH / 2:.1f} '
                         f'{arrow_y + gap - 6:.1f}" stroke="{colors["cyan"]}" stroke-width="1.4" '
                         f'marker-end="url(#{dashed_arrow})"/>')
            if arrow_note and index == 0:
                parts.append(f'<text x="{x + BOX_WIDTH / 2 + 8:.1f}" y="{arrow_y + gap / 2 + 4:.1f}" font-size="12" '
                             f'fill="{colors["text"]}">{html.escape(arrow_note)}</text>')
        y += BOX_HEIGHT + gap
    return "".join(parts)


def build_audit_group(row_counts, colors, x, top, tooltips=None):
    """weekly_price's load trail, apart from the star: etl_run → rejection."""
    return build_chain(AUDIT_TABLES, row_counts, colors, x, top, "AUDITORÍA DE CARGAS", AUDIT_GAP,
                       tooltips=tooltips, arrow_note="run_id (FK)")


def build_ipc_group(row_counts, colors, x, top, date_rect, tooltips=None):
    """The food IPC over dim_date: three dashed boxes in a chain and a dashed link from ipc_weekly
    down to dim_date (D-190). Drawn only when the counts of its tables are known."""
    if not all(table in row_counts for table in IPC_TABLES):
        return ""
    chain = build_chain(IPC_TABLES, row_counts, colors, x, top, "IPC DE ALIMENTOS (INE)", IPC_GAP,
                        notes=IPC_NOTES, tooltips=tooltips)
    last_bottom = top + IPC_LABEL_HEIGHT + len(IPC_TABLES) * BOX_HEIGHT + (len(IPC_TABLES) - 1) * IPC_GAP
    dx, dy, dw, _ = date_rect
    link = (f'<path d="M{x + BOX_WIDTH / 2:.1f} {last_bottom:.1f} L{dx + dw / 2:.1f} {dy:.1f}" '
            f'stroke="{colors["cyan"]}" stroke-width="1.4" stroke-dasharray="5 5"/>')
    return chain + link


def build_star_svg(columns_by_table, row_counts, mode, selected=None, tooltips=None):
    """The whole diagram: background, connectors, five cards, the IPC chain and the audit trail.
    tooltips: {table: text shown on hover}."""
    tooltips = tooltips or {}
    colors = get_colors(mode)
    layout, groups, height = compute_layout(columns_by_table)
    fact_rect = layout[STAR_TABLE]
    center_x, center_y = fact_rect[0] + fact_rect[2] / 2, fact_rect[1] + fact_rect[3] / 2

    cards = [build_dimension_card(table, layout[table], columns_by_table[table], colors,
                                  selected=selected == table, tooltip=tooltips.get(table))
             for table in (DATE_TABLE,) + RIGHT_DIMENSIONS]
    cards.append(build_fact_card(fact_rect, columns_by_table[STAR_TABLE], row_counts[STAR_TABLE],
                                 colors, selected=selected == STAR_TABLE, tooltip=tooltips.get(STAR_TABLE)))
    connectors = "".join([build_connector(colors, fact_rect, layout[DATE_TABLE], "left")]
                         + [build_connector(colors, fact_rect, layout[table], "right") for table in RIGHT_DIMENSIONS])
    audit = build_audit_group(row_counts, colors, groups["audit"][0], groups["audit"][1], tooltips)
    ipc = build_ipc_group(row_counts, colors, groups["ipc"][0], groups["ipc"][1], layout[DATE_TABLE], tooltips)
    defs = (f'<defs><marker id="audit-arrow" viewBox="0 0 10 10" refX="8" refY="5" '
            f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M0 0 L10 5 L0 10 Z" fill="{colors["cyan"]}"/></marker></defs>')
    return ''.join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height:.0f}" '
        f'width="100%" role="img" aria-label="Modelo estrella de datos.duckdb" '
        f'font-family="{charts.CHART_FONT}">', defs,
        build_star_background(colors, center_x, center_y, 190),
        connectors, audit, ipc, *cards, "</svg>"])
# endregion
