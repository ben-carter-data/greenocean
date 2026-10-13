"""Star model of datos.db drawn as a real star (T-59).

A four-pointed star in the background, the fact table weekly_price in the
middle and one dimension on each point: the week on top, products on the left,
regions on the right and channels at the bottom. Each card lists the real
columns of etl/schema.sql, with primary and foreign keys in cyan; the measures
of the fact table sit apart at its foot.

Below the star, a panel explains the table under the mouse (or the one tapped
on a phone) and shows how it joins the fact table. It needs no JavaScript:
each table is focusable and the page CSS uses :has() to choose the panel.
The result is HTML for st.markdown, which keeps inline SVG (st.html drops it).
"""
import html

from bi import charts, zoom

# region Constants
CYAN = "#22d3ee"
# On a white card the light cyan is too pale for text: a darker one of the same hue.
CYAN_ON_LIGHT = "#0e7490"
VANTABLACK_CARD = "#000000"
VANTABLACK_FRAME = "#0b0b0d"
MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

WIDTH = 960
HEIGHT = 800
CENTER_X = WIDTH / 2
CENTER_Y = 405
ROW_HEIGHT = 27
# The measures of the fact table: what the indicators analyze.
MEASURES = ["price", "volume", "observation_count"]
WEEK_CARD = "week"
# (table, left x, top y, width): one card per table, measured in the viewBox.
CARDS = {
    WEEK_CARD: (350, 20, 260),
    "dim_product": (20, 300, 240),
    "dim_region": (700, 336, 240),
    "weekly_price": (320, 236, 320),
    "dim_channel": (350, 630, 260),
}
WEEK_TITLE = "Semana"
WEEK_LINES = ["week_start", "mejora: dim_date"]
# The four points of the star and the inner corners between them.
STAR_POINTS = [(CENTER_X, 70), (CENTER_X + 95, CENTER_Y - 95), (WIDTH - 40, CENTER_Y),
               (CENTER_X + 95, CENTER_Y + 95), (CENTER_X, 760),
               (CENTER_X - 95, CENTER_Y + 95), (40, CENTER_Y), (CENTER_X - 95, CENTER_Y - 95)]
# endregion


# region Colors
def get_colors(mode):
    """Card, frame, cyan and text colors of the active theme."""
    palette = charts.get_palette(mode)
    if mode == charts.MODE_DARK:
        return {"card": VANTABLACK_CARD, "frame": VANTABLACK_FRAME, "cyan": CYAN,
                "text": palette["text"], "strong_text": palette["strong_text"],
                "line": palette["card_border"]}
    return {"card": palette["card"], "frame": palette["background"], "cyan": CYAN_ON_LIGHT,
            "text": palette["text"], "strong_text": palette["strong_text"],
            "line": palette["card_border"]}
# endregion


# region Cards
def list_fact_lines(columns):
    """(keys and attributes, measures) of weekly_price: foreign keys first."""
    attributes = [column for column in columns if column[0] not in MEASURES]
    attributes.sort(key=lambda column: column[1] != "FK")
    return attributes, [column for column in columns if column[0] in MEASURES]


def build_column_text(x, y, name, kind, colors, size=17):
    """One column line: keys and measures in cyan, with their (PK) or (FK) mark."""
    is_cyan = kind in ("PK", "MEASURE")
    label = f"{name} ({kind})" if kind in ("PK", "FK") else name
    color = colors["cyan"] if is_cyan else colors["strong_text"]
    return (f'<text x="{x}" y="{y}" font-family="{MONO_FONT}" font-size="{size}" '
            f'fill="{color}">{html.escape(label)}</text>')


def build_card_frame(table, height, colors, dashed=False, is_fact=False):
    """Focusable group with the card background: hover or tap chooses the panel."""
    x, y, width = CARDS[table]
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    stroke_width = 2.6 if is_fact else 1.4
    return (f'<g class="star-table star-{table}" tabindex="0" role="button" '
            f'aria-label="{html.escape(table)}">'
            f'<rect class="star-card" x="{x}" y="{y}" width="{width}" height="{height}" '
            f'rx="16" fill="{colors["card"]}" stroke="{colors["cyan"]}" '
            f'stroke-width="{stroke_width}"{dash}/>')


def build_card_title(table, title, colors, subtitle=None):
    """Card heading and the line under it; returns (svg, y of the first row)."""
    x, y, width = CARDS[table]
    middle = x + width / 2
    color = colors["cyan"] if subtitle else colors["strong_text"]
    parts = [f'<text x="{middle}" y="{y + 34}" text-anchor="middle" font-size="21" '
             f'font-weight="700" fill="{color}">{html.escape(title)}</text>']
    line_y = y + 52
    if subtitle:
        parts.append(f'<text x="{middle}" y="{y + 58}" text-anchor="middle" font-size="15" '
                     f'fill="{colors["text"]}">{html.escape(subtitle)}</text>')
        line_y = y + 74
    parts.append(f'<path d="M{x + 18} {line_y} H{x + width - 18}" '
                 f'stroke="{colors["line"]}" stroke-width="1"/>')
    return "".join(parts), line_y + 28


def build_dimension_card(table, columns, colors):
    """A dimension: its name and every column, the primary key in cyan."""
    x, y, _ = CARDS[table]
    height = 52 + 28 + len(columns) * ROW_HEIGHT + 4
    title, first_y = build_card_title(table, table, colors)
    rows = "".join(build_column_text(x + 20, first_y + position * ROW_HEIGHT, name, kind,
                                     colors)
                   for position, (name, kind) in enumerate(columns))
    return build_card_frame(table, height, colors) + title + rows + "</g>"


def build_week_card(colors):
    """The week: not a table yet, a column of the fact table (dashed border)."""
    x, _, _ = CARDS[WEEK_CARD]
    height = 52 + 28 + len(WEEK_LINES) * ROW_HEIGHT + 4
    title, first_y = build_card_title(WEEK_CARD, WEEK_TITLE, colors)
    rows = (build_column_text(x + 20, first_y, WEEK_LINES[0], "", colors)
            + f'<text x="{x + 20}" y="{first_y + ROW_HEIGHT}" font-size="16" '
              f'fill="{colors["text"]}">{html.escape(WEEK_LINES[1])}</text>')
    return build_card_frame(WEEK_CARD, height, colors, dashed=True) + title + rows + "</g>"


def build_fact_card(columns, row_count, colors):
    """weekly_price: its keys and attributes, then the measures apart, in cyan."""
    x, y, width = CARDS["weekly_price"]
    attributes, measures = list_fact_lines(columns)
    subtitle = f"hechos · {charts.format_thousands(row_count)} filas"
    title, first_y = build_card_title("weekly_price", "weekly_price", colors, subtitle)
    rows = [build_column_text(x + 20, first_y + position * ROW_HEIGHT, name, kind, colors)
            for position, (name, kind) in enumerate(attributes)]
    divider_y = first_y + len(attributes) * ROW_HEIGHT - 10
    rows.append(f'<path d="M{x + 18} {divider_y} H{x + width - 18}" '
                f'stroke="{colors["line"]}" stroke-width="1"/>')
    rows += [build_column_text(x + 20, divider_y + 28 + position * ROW_HEIGHT, name,
                               "MEASURE", colors)
             for position, (name, _) in enumerate(measures)]
    height = divider_y + 28 + len(measures) * ROW_HEIGHT - y - 4
    return (build_card_frame("weekly_price", height, colors, is_fact=True) + title
            + "".join(rows) + "</g>")
# endregion


# region Star
def build_star_background(colors):
    """The four-pointed star behind the cards, in cyan at 7 %."""
    points = " ".join(f"{x},{y}" for x, y in STAR_POINTS)
    return (f'<polygon points="{points}" fill="{CYAN}" fill-opacity="0.07" '
            f'stroke="{colors["cyan"]}" stroke-opacity="0.25" stroke-width="1"/>')


def build_connectors(colors):
    """Dashed cyan lines from the fact table to each point."""
    lines = [(CENTER_X, 160, CENTER_X, 236), (260, CENTER_Y, 320, CENTER_Y),
             (640, CENTER_Y, 700, CENTER_Y), (CENTER_X, 580, CENTER_X, 630)]
    return "".join(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{colors["cyan"]}" '
                   f'stroke-width="1.4" stroke-dasharray="5 5"/>'
                   for x1, y1, x2, y2 in lines)


def build_star_svg(columns_by_table, row_counts, mode):
    """The whole star: background, connectors, the week and the four tables."""
    colors = get_colors(mode)
    cards = [build_week_card(colors),
             *[build_dimension_card(table, columns_by_table[table], colors)
               for table in ["dim_product", "dim_region", "dim_channel"]],
             build_fact_card(columns_by_table["weekly_price"], row_counts["weekly_price"],
                             colors)]
    return "".join([f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
                    f'width="100%" role="img" aria-label="Modelo estrella de datos.db" '
                    f'font-family="{charts.CHART_FONT}">', build_star_background(colors),
                    build_connectors(colors), *cards, "</svg>"])
# endregion


# region Panel
def build_panel(table, title, text, join_sql, figures, colors):
    """The explanation of one table: what it holds, its JOIN and its real figures."""
    join_html = html.escape(join_sql).replace("\n", "<br>")
    return (f'<div class="star-panel star-panel-{table}">'
            f'<div class="star-panel-title">{html.escape(title)}</div>'
            f'<div>{html.escape(text)}</div>'
            f'<code class="star-join">{join_html}</code>'
            f'<div class="star-figures">{html.escape(figures)}</div></div>')


def build_star_css(colors):
    """Frame, panel and the choice of panel: by default the fact table; under the
    mouse or after a tap, the table touched."""
    tables = list(CARDS)
    rules = "".join(
        f".star-model:has(.star-{table}:hover) .star-panel, "
        f".star-model:has(.star-{table}:focus) .star-panel {{ display: none; }}"
        f".star-model:has(.star-{table}:hover) .star-panel-{table}, "
        f".star-model:has(.star-{table}:focus) .star-panel-{table} {{ display: block; }}"
        for table in tables)
    return f"""<style>
    .star-model {{ background: {colors["frame"]}; border-radius: 18px; padding: 12px; }}
    .star-table {{ cursor: pointer; outline: none; }}
    .star-table:hover .star-card, .star-table:focus .star-card {{ stroke-width: 3; }}
    .star-panel {{ display: none; min-height: 150px; margin-top: 8px; padding: 14px 18px;
                   border-radius: 14px; border: 1px solid {colors["cyan"]};
                   background: {colors["card"]}; color: {colors["strong_text"]};
                   line-height: 1.5; }}
    .star-panel-weekly_price {{ display: block; }}
    .star-panel-title {{ color: {colors["cyan"]}; font-size: 1.2rem; font-weight: 700;
                         margin-bottom: 4px; }}
    .star-join {{ display: block; margin-top: 8px; white-space: pre-wrap;
                  color: {colors["cyan"]}; background: transparent; padding: 0; }}
    .star-figures {{ margin-top: 6px; color: {colors["text"]}; font-family: {MONO_FONT}; }}
    .star-note {{ margin-top: 10px; color: {colors["text"]}; }}
    .star-note strong {{ color: {colors["strong_text"]}; font-weight: 500; }}
    {rules}
    </style>"""


def build_star_model_html(columns_by_table, row_counts, panels, note, mode):
    """The star, its panels and the note on the run tables, ready for st.markdown.

    panels: [(table, title, text, join_sql, figures)], with the fact table first.
    """
    colors = get_colors(mode)
    panel_html = "".join(build_panel(*panel, colors) for panel in panels)
    return (build_star_css(colors) + '<div class="star-model">'
            + zoom.build_zoom_frame_html(build_star_svg(columns_by_table, row_counts, mode))
            + panel_html
            + f'<div class="star-note">{note}</div></div>')
# endregion
