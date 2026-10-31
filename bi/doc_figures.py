"""The figures of the documents (D-289): sequences, layers, timelines, a fault tree, nodes, bars and before/after.

Every figure is one HTML document for st.iframe, drawn in the visual language of the other document views: no
background, flat brand logos, the colors of the theme and text that never shrinks below 12 px. The texts live here in
both languages (say(es, en)), so a figure reads in the language of the visit and its PDF too. The facts each figure
states are the ones of the code and the workflows; tests/test_doc_figures.py checks the files and steps they name.
"""

import html

from bi import charts, doc_views, i18n


def say(spanish, english):
    """The text in the language of the visit."""
    return english if i18n.is_english() else spanish


def esc(value):
    return html.escape(str(value), quote=True)


KIND_COLORS = {"flow": "#3987e5", "order": "#c98500", "check": "#199e70", "stop": "#e5484d", "back": "#8b8fa3"}


def page(mode, body, label):
    """One figure: transparent page, the colors of the theme."""
    palette = charts.get_palette(mode)
    ink, text, muted, card, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    css = f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:400 13px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
.fig {{ padding:4px 2px 8px; }}
.fig-title {{ margin:0 0 10px; font-size:11px; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:{muted}; }}
.fig-note {{ margin:8px 0 0; font-size:12px; color:{muted}; }}
svg {{ display:block; width:100%; height:auto; overflow:visible; }}
svg text {{ font-family:inherit; }}
.ink {{ fill:{ink}; }} .txt {{ fill:{text}; }} .mut {{ fill:{muted}; }}
.box {{ fill:color-mix(in srgb, {accent} 7%, transparent); stroke:color-mix(in srgb, {border} 90%, transparent); }}
.life {{ stroke:color-mix(in srgb, {border} 95%, transparent); stroke-dasharray:4 5; }}
.gate {{ fill:color-mix(in srgb, #e5484d 9%, transparent); stroke:#e5484d; stroke-dasharray:5 4; }}
.cols {{ display:grid; gap:10px; align-items:stretch; }}
.col {{ display:flex; flex-direction:column; gap:7px; padding:10px; border-radius:14px; min-width:0;
  border:1px solid color-mix(in srgb, {border} 90%, transparent); background:color-mix(in srgb, var(--c) 6%, transparent);
  border-top:3px solid var(--c); }}
.col h4 {{ margin:0 0 2px; font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--c); }}
.item {{ padding:7px 9px; border-radius:10px; background:color-mix(in srgb, {card} 70%, transparent);
  border:1px solid color-mix(in srgb, {border} 70%, transparent); }}
.item b {{ display:block; color:{ink}; font-weight:600; font-size:13px; }}
.item span {{ display:block; font-size:12px; color:{text}; }}
.arrow {{ align-self:center; color:{muted}; font-size:20px; text-align:center; }}
.bars {{ display:grid; grid-template-columns:minmax(120px, 30%) 1fr auto; gap:6px 12px; align-items:center; }}
.bar {{ height:14px; border-radius:7px; background:var(--c); opacity:.85; }}
.bars b {{ color:{ink}; font-weight:600; }} .bars em {{ font-style:normal; color:{ink}; font-weight:600; }}
.tree {{ display:grid; grid-template-columns:minmax(150px, 24%) 1fr; gap:10px 16px; align-items:start; }}
.root {{ padding:12px; border-radius:14px; border:2px solid {accent}; color:{ink}; font-weight:600;
  background:color-mix(in srgb, {accent} 8%, transparent); }}
.branches {{ display:flex; flex-direction:column; gap:8px; border-left:2px solid color-mix(in srgb, {accent} 45%, transparent);
  padding-left:14px; }}
.branch {{ display:grid; grid-template-columns:minmax(150px, 34%) 1fr; gap:10px; align-items:start; position:relative; }}
.branch::before {{ content:""; position:absolute; left:-15px; top:16px; width:12px; border-top:2px solid color-mix(in srgb, {accent} 45%, transparent); }}
.when {{ padding:7px 9px; border-radius:10px; border:1px solid color-mix(in srgb, #c98500 55%, transparent);
  background:color-mix(in srgb, #c98500 8%, transparent); color:{ink}; font-weight:600; font-size:12.5px; }}
.then {{ padding:7px 9px; border-radius:10px; border:1px solid color-mix(in srgb, {border} 80%, transparent); font-size:12.5px; }}
.then b {{ color:{ink}; }}
.compare {{ display:grid; grid-template-columns:1fr auto 1fr; gap:12px; align-items:stretch; }}
@media (max-width:640px) {{ .cols, .compare, .tree, .branch {{ grid-template-columns:1fr !important; }} .arrow {{ transform:rotate(90deg); }} }}
</style>"""
    return (
        f'<!doctype html><html lang="{i18n.get_language()}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">{css}</head>'
        f'<body><div class="fig" role="img" aria-label="{esc(label)}">{body}</div></body></html>'
    )


def logo(mark, x, y, size=30):
    """A flat logo (brand, person or source) placed in an SVG."""
    kind, name = mark.split(":")
    svg = doc_views.flat_logo(kind, name)
    return svg.replace(
        '<svg class="logo" ', f'<svg x="{x - size / 2:.1f}" y="{y - size / 2:.1f}" width="{size}" height="{size}" ', 1
    )


# region Builders
def sequence(mode, title, actors, steps, note=""):
    """A sequence diagram: the actors along the top, their lifelines, and each step as an arrow in order.

    actors: [(key, label, mark)]; steps: [(from, to, label, kind)] with kind flow, back, check, order or stop;
    a step whose from is «gate» is a band across the lifelines (a gate that can stop the sequence)."""
    width, top, row, margin = 920, 78, 40, 34
    gap = (width - margin) / len(actors)
    x = {key: margin + gap * (index + 0.5) for index, (key, _, _) in enumerate(actors)}
    height = top + 20 + row * len(steps) + 10
    parts = []
    for key, label, mark in actors:
        cx = x[key]
        parts.append(logo(mark, cx, 22, 26))
        parts.append(
            f'<text class="ink" x="{cx:.1f}" y="54" text-anchor="middle" font-size="12.5" font-weight="600">{esc(label)}</text>'
        )
        parts.append(f'<line class="life" x1="{cx:.1f}" y1="68" x2="{cx:.1f}" y2="{height:.1f}"/>')
    number = 0
    for index, (source, target, label, kind) in enumerate(steps):
        y = top + 26 + row * index
        if source == "gate":
            parts.append(f'<rect class="gate" x="12" y="{y - 15}" width="{width - 24}" height="30" rx="8"/>')
            parts.append(
                f'<text x="{width / 2}" y="{y + 4}" text-anchor="middle" font-size="12.5" font-weight="600" '
                f'fill="#e5484d">{esc(label)}</text>'
            )
            continue
        number += 1
        color = KIND_COLORS[kind]
        dash = ' stroke-dasharray="6 5"' if kind == "back" else ""
        x1, x2 = x[source], x[target]
        # The number of the step sits in its own column on the left, so it never covers a label.
        parts.append(
            f'<circle cx="14" cy="{y}" r="10" fill="{color}"/><text x="14" y="{y + 4}" text-anchor="middle" '
            f'font-size="10.5" font-weight="700" fill="#fff">{number}</text>'
            f'<line x1="26" y1="{y}" x2="{min(x1, x2) - 4:.1f}" y2="{y}" stroke="{color}" stroke-opacity=".18" stroke-width="1"/>'
        )
        if x1 == x2:
            parts.append(
                f'<path d="M{x1 + 4} {y - 8} h28 v16 h-26" fill="none" stroke="{color}" stroke-width="1.8"{dash} '
                f'marker-end="url(#h-{kind})"/>'
            )
            # On the right half, the label goes to the left of the loop, so it stays inside the figure.
            side = f'x="{x1 + 38}" text-anchor="start"' if x1 < width * 0.6 else f'x="{x1 - 8}" text-anchor="end"'
            parts.append(f'<text class="txt" {side} y="{y + 4}" font-size="12">{esc(label)}</text>')
        else:
            direction = 1 if x2 > x1 else -1
            parts.append(
                f'<line x1="{x1 + 6 * direction:.1f}" y1="{y}" x2="{x2 - 8 * direction:.1f}" y2="{y}" stroke="{color}" '
                f'stroke-width="1.8"{dash} marker-end="url(#h-{kind})"/>'
            )
            # A label wider than its arrow starts where the arrow starts and runs into the free space on its right,
            # instead of spilling over the column of step numbers.
            left, right = min(x1, x2), max(x1, x2)
            if len(label) * 6.4 <= right - left - 12:
                anchor = f'x="{(x1 + x2) / 2:.1f}" text-anchor="middle"'
            elif left + 8 + len(label) * 6.4 <= width - 4:
                anchor = f'x="{left + 8:.1f}" text-anchor="start"'
            else:
                anchor = f'x="{right - 8:.1f}" text-anchor="end"'
            parts.append(f'<text class="txt" {anchor} y="{y - 7}" font-size="12">{esc(label)}</text>')
    markers = "".join(
        f'<marker id="h-{kind}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{color}"/></marker>'
        for kind, color in KIND_COLORS.items()
    )
    body = (
        f'<p class="fig-title">{esc(title)}</p><svg viewBox="0 0 {width} {height:.0f}" aria-hidden="true">'
        f'<defs>{markers}</defs>{"".join(parts)}</svg>' + (f'<p class="fig-note">{esc(note)}</p>' if note else "")
    )
    return page(mode, body, title)


# Line icons on a 24-unit grid, drawn in one color with no background (the author's diagram style, D-297).
LINE_ICONS = {
    "shield": '<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9"/><path d="m16 7 3 3"/><path d="m14 9 2 2"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "warning": '<path d="M12 3 2 20h20z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
    "calendar": '<rect x="4" y="5" width="16" height="16" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "chart": '<path d="M4 20V4"/><path d="M4 20h16"/><path d="m7 15 4-5 3 3 5-7"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    "database": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "tool": '<path d="M14.5 6.5a4 4 0 0 0-5 5L4 17l3 3 5.5-5.5a4 4 0 0 0 5-5l-2.5 2.5-2.5-.5-.5-2.5z"/>',
    "ruler": '<rect x="3" y="8" width="18" height="8" rx="1.5"/><path d="M7 8v3M11 8v4M15 8v3M19 8v4"/>',
    "printer": '<path d="M7 9V3h10v6"/><rect x="4" y="9" width="16" height="8" rx="2"/><path d="M7 14h10v7H7z"/>',
    "pulse": '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
    "files": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/>',
    "star": '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    "cloud": '<path d="M7 18a4 4 0 0 1 0-8 5 5 0 0 1 9.6-1.5A4 4 0 1 1 17 18z"/><path d="m4 4 16 16"/>',
    "box": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4 7.5 8 4.5 8-4.5"/><path d="M12 12v9"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "arrows": '<path d="M4 8h13"/><path d="m14 5 3 3-3 3"/><path d="M20 16H7"/><path d="m10 13-3 3 3 3"/>',
    "commit": '<circle cx="12" cy="12" r="3.5"/><path d="M3 12h5.5M15.5 12H21"/>',
    "bell": '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 21h4"/>',
    "code": '<path d="m8 8-4 4 4 4"/><path d="m16 8 4 4-4 4"/><path d="m13.5 5-3 14"/>',
}


def mark(spec, x, y, size, accent):
    """A node's mark: a flat logo (brand, person, source) or a line icon («icon:name» or «icon:name@#color»)."""
    kind, _, name = spec.partition(":")
    if kind != "icon":
        return logo(spec, x, y, size)
    name, _, color = name.partition("@")
    return (
        f'<g transform="translate({x - size / 2:.1f} {y - size / 2:.1f}) scale({size / 24:.4f})" fill="none" '
        f'stroke="{color or accent}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{LINE_ICONS[name]}</g>'
    )


def wrap(text, limit=24):
    """A caption in lines of at most `limit` characters, cut between words."""
    lines, line = [], ""
    for word in str(text).split():
        if line and len(line) + 1 + len(word) > limit:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + ([line] if line else [])


def edge_points(route, start, end, r, source_bottom, target_bottom):
    """The corners of a line from one icon to another (D-297): «h» leaves by the side and turns once at mid-height, «v»
    leaves from below (or above) and turns once at mid-width, «hv» goes across and then down or up, «vh» down or up and
    then across. Every turn is a right angle."""
    (x1, y1), (x2, y2) = start, end
    right = x2 >= x1
    down = y2 >= y1
    if route == "h":
        sx, ex = (x1 + r, x2 - r) if right else (x1 - r, x2 + r)
        mid = (sx + ex) / 2
        return [(sx, y1), (mid, y1), (mid, y2), (ex, y2)] if y1 != y2 else [(sx, y1), (ex, y2)]
    if route == "v":
        sy, ey = (source_bottom, y2 - r) if down else (y1 - r, target_bottom)
        mid = (sy + ey) / 2
        return [(x1, sy), (x1, mid), (x2, mid), (x2, ey)] if x1 != x2 else [(x1, sy), (x2, ey)]
    if route == "hv":
        sx = x1 + r if right else x1 - r
        ey = y2 - r if down else target_bottom
        return [(sx, y1), (x2, y1), (x2, ey)]
    sy = source_bottom if down else y1 - r  # «vh»
    ex = x2 - r if right else x2 + r
    return [(x1, sy), (x1, y2), (ex, y2)]


def stretch_length(pair):
    return abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1])


def edge_label(points, label, at_start, halo, width):
    """The label of a line, on its last stretch when it has room (the first may be shared by a fork), else on its
    longest; above a horizontal stretch, beside a vertical one."""
    stretches = list(zip(points, points[1:]))
    last = stretches[-1]
    if at_start:  # two lines that end on the same stretch: each label on its own start
        (ax, ay), (bx, by) = stretches[0]
    else:
        (ax, ay), (bx, by) = (
            last if stretch_length(last) >= max(70, len(label) * 6.2) else max(stretches, key=stretch_length)
        )
    if ay == by:
        return (
            f'<text class="mut" x="{(ax + bx) / 2:.1f}" y="{ay - 6:.1f}" text-anchor="middle" font-size="11" '
            f'stroke="{halo}" stroke-width="4" paint-order="stroke">{esc(label)}</text>'
        )
    # beside a vertical stretch: on its right, or on its left near the right edge of the figure
    side = f'x="{ax - 7:.1f}" text-anchor="end"' if ax + 7 + len(label) * 6.2 > width else f'x="{ax + 7:.1f}"'
    return (
        f'<text class="mut" {side} y="{(ay + by) / 2 + 4:.1f}" font-size="11" '
        f'stroke="{halo}" stroke-width="4" paint-order="stroke">{esc(label)}</text>'
    )


def graph(mode, title, nodes, edges, note="", width=920, size=38, limit=22):
    """A diagram of icons and straight arrows (D-297): no boxes and no cards, lines that turn only at right angles.

    nodes: {key: (x, y, mark, label, caption)}; the mark is centred on (x, y) and the label and caption sit below it.
    edges: [(from, to, label, kind, route[, «start»])]: route «h» leaves by the side and turns once at mid-height, «v» leaves from
    below (or above) and turns once at mid-width, «hv» goes across and then down or up, «vh» goes down or up and then
    across. The label rides the longest straight stretch of its line."""
    palette = charts.get_palette(mode)
    halo = palette["card"]
    r = size / 2 + 6
    texts, bottoms = [], {}
    for key, (x, y, spec, label, caption) in nodes.items():
        texts.append(mark(spec, x, y, size, palette["accent"]))
        names = wrap(label, limit + 2)
        for index, line in enumerate(names):
            texts.append(
                f'<text class="ink" x="{x}" y="{y + size / 2 + 17 + 16 * index}" text-anchor="middle" font-size="13" '
                f'font-weight="600">{esc(line)}</text>'
            )
        top = y + size / 2 + 33 + 16 * (len(names) - 1)
        lines = wrap(caption, limit) if caption else []
        for index, line in enumerate(lines):
            texts.append(
                f'<text class="txt" x="{x}" y="{top + 15 * index}" text-anchor="middle" font-size="11.5">{esc(line)}</text>'
            )
        bottoms[key] = top - 11 + 15 * len(lines) + 4
    lines_svg = []
    for source, target, label, kind, route, *where in edges:
        points = edge_points(route, nodes[source][:2], nodes[target][:2], r, bottoms[source], bottoms[target])
        color = KIND_COLORS[kind]
        dash = ' stroke-dasharray="6 5"' if kind == "back" else (' stroke-dasharray="2 4"' if kind == "check" else "")
        path = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in points)
        lines_svg.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.7"{dash} marker-end="url(#g-{kind})"/>'
        )
        if label:
            lines_svg.append(edge_label(points, label, bool(where and where[0] == "start"), halo, width))
    height = max(bottoms.values()) + 6
    markers = "".join(
        f'<marker id="g-{kind}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{color}"/></marker>'
        for kind, color in KIND_COLORS.items()
    )
    body = (
        f'<p class="fig-title">{esc(title)}</p><svg viewBox="0 0 {width} {height:.0f}" aria-hidden="true">'
        f'<defs>{markers}</defs>{"".join(lines_svg)}{"".join(texts)}</svg>'
        + (f'<p class="fig-note">{esc(note)}</p>' if note else "")
    )
    return page(mode, body, title)


def timeline(mode, title, events, note=""):
    """A horizontal timeline: [(date, heading, [lines])], evenly spaced."""
    width = 920
    gap = width / len(events)
    height = 70 + 22 * max(len(lines) for _, _, lines in events) + 20
    parts = [f'<line x1="10" y1="40" x2="{width - 10}" y2="40" stroke="#3987e5" stroke-width="2.5"/>']
    for index, (date, heading, lines) in enumerate(events):
        cx = gap * (index + 0.5)
        parts.append(
            f'<circle cx="{cx:.1f}" cy="40" r="8" fill="#3987e5"/><circle cx="{cx:.1f}" cy="40" r="3.5" fill="#fff"/>'
        )
        parts.append(
            f'<text class="mut" x="{cx:.1f}" y="22" text-anchor="middle" font-size="12" font-weight="600">{esc(date)}</text>'
        )
        parts.append(
            f'<text class="ink" x="{cx:.1f}" y="68" text-anchor="middle" font-size="13" font-weight="700">{esc(heading)}</text>'
        )
        for line_index, line in enumerate(lines):
            parts.append(
                f'<text class="txt" x="{cx:.1f}" y="{90 + 20 * line_index}" text-anchor="middle" font-size="12">{esc(line)}</text>'
            )
    body = (
        f'<p class="fig-title">{esc(title)}</p><svg viewBox="0 0 {width} {height}" aria-hidden="true">{"".join(parts)}</svg>'
        + (f'<p class="fig-note">{esc(note)}</p>' if note else "")
    )
    return page(mode, body, title)


def bars(mode, title, rows, note=""):
    """Horizontal bars: [(label, value, color)]."""
    top = max(value for _, value, _ in rows) or 1
    cells = "".join(
        f'<b>{esc(label)}</b><div class="bar" style="--c:{color};width:{value / top * 100:.1f}%"></div><em>{value}</em>'
        for label, value, color in rows
    )
    body = f'<p class="fig-title">{esc(title)}</p><div class="bars">{cells}</div>' + (
        f'<p class="fig-note">{esc(note)}</p>' if note else ""
    )
    return page(mode, body, title)


# endregion


BLUE, GREEN, AMBER, VIOLET, RED, GREY = "#3987e5", "#199e70", "#c98500", "#8b5cf6", "#e5484d", "#8b8fa3"


# region C4 views and the procedure (D-297): the system context, its containers and the security procedure, drawn as
# icons and right-angle arrows instead of boxes.
def sad_context(mode):
    return graph(
        mode,
        say("Contexto del sistema (C4, nivel 1)", "System context (C4, level 1)"),
        {
            "visitor": (
                330,
                20,
                "person:visitor",
                say("Visitante", "Visitor"),
                say("lee el panel, sin cuenta", "reads the panel, no account"),
            ),
            "admin": (
                590,
                20,
                "person:author",
                say("Administrador", "Administrator"),
                say("el autor: mantiene el código y los secretos", "the author: maintains the code and the secrets"),
            ),
            "system": (
                460,
                190,
                "icon:box",
                "GreenOcean",
                say(
                    "pipeline semanal y panel de BI: Python, SQLite, Parquet, dbt, DuckDB y Streamlit",
                    "weekly pipeline and BI panel: Python, SQLite, Parquet, dbt, DuckDB and Streamlit",
                ),
            ),
            "odepa": (
                90,
                120,
                "source:odepa",
                "ODEPA",
                say("precios mayoristas y al consumidor", "wholesale and consumer prices"),
            ),
            "ine": (90, 290, "source:ine", "INE", say("IPC de alimentos", "food CPI")),
            "github": (
                830,
                120,
                "brand:github",
                "GitHub",
                say(
                    "aloja el código, ejecuta la carga y guarda la base",
                    "hosts the code, runs the load and keeps the database",
                ),
            ),
            "cloud": (
                830,
                290,
                "brand:streamlit",
                "Streamlit Community Cloud",
                say("publica el panel", "publishes the panel"),
            ),
        },
        [
            ("visitor", "system", say("lee", "reads"), "flow", "v"),
            ("admin", "system", say("mantiene", "maintains"), "order", "v"),
            ("system", "odepa", "CSV", "flow", "h"),
            ("system", "ine", say("IPC", "CPI"), "flow", "h"),
            ("system", "github", say("aloja", "hosts"), "order", "h"),
            ("system", "cloud", say("publica", "publishes"), "flow", "h"),
        ],
        say(
            "La flecha va de quien usa a quien es usado; lo que hay dentro de GreenOcean está en la vista siguiente.",
            "The arrow goes from who uses to what is used; what is inside GreenOcean is in the next view.",
        ),
        size=48,
        limit=26,
    )


def sad_containers(mode):
    return graph(
        mode,
        say("Contenedores (C4, nivel 2)", "Containers (C4, level 2)"),
        {
            "odepa": (70, 40, "source:odepa", "ODEPA", say("precios", "prices")),
            "ine": (70, 220, "source:ine", "INE", say("IPC de alimentos", "food CPI")),
            "load": (
                300,
                130,
                "brand:python",
                say("Carga semanal", "Weekly load"),
                say(
                    "Python, dbt Core y DuckDB: agent/agent.py, etl/etl.py, etl/pipeline.py, dbt/",
                    "Python, dbt Core and DuckDB: agent/agent.py, etl/etl.py, etl/pipeline.py, dbt/",
                ),
            ),
            "work": (
                560,
                20,
                "brand:apacheparquet",
                say("Archivos de trabajo", "Working files"),
                say(
                    "etl/raw.db, etl/bronze/ y la base de trabajo de dbt",
                    "etl/raw.db, etl/bronze/ and the dbt working database",
                ),
            ),
            "served": (560, 175, "brand:duckdb", say("Base servida", "Served database"), "etl/datos.duckdb"),
            "backup": (
                560,
                300,
                "brand:sqlite",
                say("Respaldo", "Backup"),
                say("etl/datos.db, sin dbt, para la paridad", "etl/datos.db, without dbt, for the parity"),
            ),
            "panel": (
                830,
                175,
                "brand:streamlit",
                say("Panel web", "Web panel"),
                say("Streamlit: bi/dashboard.py, en solo lectura", "Streamlit: bi/dashboard.py, read-only"),
            ),
            "github": (
                300,
                330,
                "brand:github",
                "GitHub",
                say(
                    "repositorio, Actions y el release de la base",
                    "repository, Actions and the release of the database",
                ),
            ),
            "people": (830, 20, "person:visitor", say("Visitante y administrador", "Visitor and administrator"), ""),
        },
        [
            ("load", "odepa", "HTTPS", "flow", "h"),
            ("load", "ine", "HTTPS", "flow", "h"),
            ("load", "work", say("lee y escribe", "reads and writes"), "flow", "h"),
            ("load", "served", say("publica", "publishes"), "flow", "h"),
            ("load", "backup", say("escribe", "writes"), "flow", "h"),
            ("panel", "served", say("solo lectura", "read-only"), "flow", "h"),
            ("people", "panel", say("consulta · lanza la carga", "reads · launches the load"), "order", "v"),
            ("github", "load", say("ejecuta cada martes", "runs every Tuesday"), "order", "v"),
        ],
        size=46,
        limit=24,
    )


def sad_components_load(mode):
    return graph(
        mode,
        say("Componentes de la carga semanal (C4, nivel 3)", "Components of the weekly load (C4, level 3)"),
        {
            "workflow": (
                70,
                130,
                "icon:calendar",
                "semanal.yml",
                say("ordena los pasos; si uno falla, se detiene", "orders the steps; if one fails, it stops"),
            ),
            "agent": (
                260,
                30,
                "brand:python",
                "agent/agent.py",
                say(
                    "descarga los CSV, revisa su encabezado y anota su huella",
                    "downloads the CSV files, checks their header and records their fingerprint",
                ),
            ),
            "etl": (
                260,
                250,
                "brand:sqlite",
                "etl/etl.py",
                say("el respaldo etl/datos.db, sin dbt", "the backup etl/datos.db, without dbt"),
            ),
            "pipeline": (
                470,
                30,
                "brand:apacheparquet",
                "etl/pipeline.py",
                say(
                    "raw.db → bronce (bronze.py, ine.py) → dbt build → puerta",
                    "raw.db → bronze (bronze.py, ine.py) → dbt build → gate",
                ),
            ),
            "dbt": (
                670,
                30,
                "brand:dbt",
                "dbt/models",
                say(
                    "staging (3) · intermedio (4) · marts (9) y 31 pruebas",
                    "staging (3) · intermediate (4) · marts (9) and 31 tests",
                ),
            ),
            "served": (
                838,
                30,
                "brand:duckdb",
                "etl/datos.duckdb",
                say("la base servida, en un archivo nuevo", "the served database, in a new file"),
            ),
            "tests": (
                470,
                250,
                "brand:pytest",
                "pytest",
                say("sobre la base nueva, con la paridad", "on the new database, with the parity"),
            ),
            "publish": (
                838,
                250,
                "brand:github",
                say("Publicación", "Publication"),
                say(
                    "release «base-actual», puntero en main e informe",
                    "«base-actual» release, pointer on main and report",
                ),
            ),
        },
        [
            ("workflow", "agent", "", "order", "h"),
            ("workflow", "etl", "", "order", "h"),
            ("agent", "pipeline", "CSV", "flow", "h"),
            ("pipeline", "dbt", say("bronce", "bronze"), "flow", "h"),
            ("dbt", "served", say("si todo pasa", "if all passes"), "flow", "h"),
            ("etl", "tests", say("respaldo", "backup"), "check", "h"),
            ("served", "tests", say("base nueva", "new database"), "check", "v"),
            ("tests", "publish", say("en verde: publica", "green: publishes"), "flow", "h"),
        ],
        size=42,
        limit=24,
    )


def sad_components_panel(mode):
    return graph(
        mode,
        say("Componentes del panel (C4, nivel 3)", "Components of the panel (C4, level 3)"),
        {
            "people": (
                70,
                180,
                "person:visitor",
                say("Lector", "Reader"),
                say("elige la vista de usuario o la profesional", "chooses the user or the professional view"),
            ),
            "dashboard": (
                260,
                180,
                "brand:streamlit",
                "bi/dashboard.py",
                say(
                    "navegación, perfiles, aviso de carga fallida e idioma (i18n.py)",
                    "navigation, profiles, failed-load notice and language (i18n.py)",
                ),
            ),
            "pages": (
                460,
                30,
                "icon:chart",
                say("Vistas", "Views"),
                say("overview.py, sql_explorer.py y las demás", "overview.py, sql_explorer.py and the rest"),
            ),
            "queries": (
                660,
                30,
                "icon:code",
                "bi/queries.py",
                say("las consultas de queries.sql, con caché", "the queries of queries.sql, cached"),
            ),
            "duckdb": (838, 30, "brand:duckdb", "etl/datos.duckdb", say("abierta en solo lectura", "opened read-only")),
            "served": (
                660,
                180,
                "icon:box",
                "bi/served_database.py",
                say("descarga la base y comprueba su huella", "downloads the database and checks its fingerprint"),
            ),
            "control": (
                460,
                330,
                "icon:key",
                "bi/control.py",
                say(
                    "clave en tiempo constante; ejecuciones y carga manual",
                    "code in constant time; runs and manual load",
                ),
            ),
            "github": (
                838,
                330,
                "brand:github",
                "GitHub",
                say("release «base-actual» y API de Actions", "«base-actual» release and Actions API"),
            ),
        },
        [
            ("people", "dashboard", "", "order", "h"),
            ("dashboard", "pages", "", "flow", "h"),
            ("dashboard", "served", say("al abrir", "on opening"), "flow", "h"),
            ("dashboard", "control", "", "order", "h"),
            ("pages", "queries", "SQL", "flow", "h"),
            ("queries", "duckdb", say("solo lectura", "read-only"), "flow", "h"),
            ("control", "github", "API", "order", "h"),
            ("github", "served", say("descarga", "download"), "flow", "v"),
        ],
        size=42,
        limit=24,
    )


def sad_scenarios(mode):
    rows = [
        (
            "person:visitor",
            say("Visitante", "Visitor"),
            "icon:chart",
            say("Ver qué cambió esta semana", "See what changed this week"),
            "P-1 · " + say("Resumen y Dashboard", "Summary and Dashboard"),
            say("Panel web y base servida", "Web panel and served database"),
        ),
        (
            "person:visitor",
            say("Visitante", "Visitor"),
            "icon:code",
            say("Consultar con SQL", "Query with SQL"),
            "P-2 · P-3 · RF-06",
            say("Panel web y DuckDB en solo lectura", "Web panel and read-only DuckDB"),
        ),
        (
            "icon:calendar",
            "GitHub Actions",
            "icon:box",
            say("Cargar y publicar cada martes", "Load and publish every Tuesday"),
            "RF-01 · RF-02 · RF-03",
            say("Carga semanal y release", "Weekly load and release"),
        ),
        (
            "person:author",
            say("Autor", "Author"),
            "icon:key",
            say("Lanzar una carga manual con la clave", "Launch a manual load with the code"),
            "RF-07",
            say("Panel web y API de GitHub", "Web panel and GitHub API"),
        ),
        (
            "person:author",
            say("Autor", "Author"),
            "icon:bell@#e5484d",
            say("Saber que una carga falló", "Know that a load failed"),
            say("aviso en el panel y correo", "notice in the panel and email"),
            say("Panel web y GitHub Actions", "Web panel and GitHub Actions"),
        ),
    ]
    nodes, edges = {}, []
    for index, (actor_mark, actor, mark, scenario, ref, where) in enumerate(rows):
        y = 20 + 95 * index
        nodes[f"a{index}"] = (90, y, actor_mark, actor, "")
        nodes[f"s{index}"] = (430, y, mark, scenario, ref)
        nodes[f"c{index}"] = (770, y, "icon:layers", say("Lo resuelve", "Realized by"), where)
        edges += [(f"a{index}", f"s{index}", "", "order", "h"), (f"s{index}", f"c{index}", "", "flow", "h")]
    return graph(
        mode,
        say(
            "Escenarios clave y los contenedores que los resuelven",
            "Key scenarios and the containers that realize them",
        ),
        nodes,
        edges,
        say(
            "Los casos de uso completos, con sus actores, están en el PRD.",
            "The full use cases, with their actors, are in the PRD.",
        ),
        size=34,
        limit=30,
    )


def tests_procedure(mode):
    return graph(
        mode,
        say("Procedimiento de las pruebas de seguridad", "Procedure of the security tests"),
        {
            "prepare": (
                80,
                30,
                "brand:git",
                say("1 · Preparar", "1 · Prepare"),
                say("copia limpia y secreto falso", "clean copy and fake secret"),
            ),
            "run": (
                300,
                30,
                "brand:pytest",
                say("2 · Ejecutar", "2 · Run"),
                say("los catorce casos con pytest", "the fourteen cases with pytest"),
            ),
            "check": (
                520,
                30,
                "icon:arrows",
                say("3 · Comprobar", "3 · Check"),
                say("contra el resultado esperado", "against the expected result"),
            ),
            "record": (
                740,
                30,
                "brand:github",
                say("4 · Registrar", "4 · Record"),
                say("la evidencia, junto al commit", "the evidence, next to the commit"),
            ),
            "decide": (
                740,
                220,
                "icon:shield@#199e70",
                say("5 · Decidir", "5 · Decide"),
                say("pasa: el cambio queda verificado", "passes: the change is verified"),
            ),
        },
        [
            ("prepare", "run", "", "flow", "h"),
            ("run", "check", "", "flow", "h"),
            ("check", "record", "", "flow", "h"),
            ("record", "decide", "", "flow", "v"),
            (
                "decide",
                "run",
                say("falla: se corrige y se repite desde el 2", "fails: it is fixed and repeated from 2"),
                "back",
                "hv",
            ),
        ],
        say(
            "En GitHub, pruebas.yml hace los pasos 2 a 4 en cada push; su resultado avisa, pero no detiene la publicación de main.",
            "On GitHub, pruebas.yml does steps 2 to 4 on every push; its result warns, but does not stop the publication of main.",
        ),
    )


# endregion


# region PRD
def prd_value(mode):
    return graph(
        mode,
        say("Del dato a la decisión", "From data to decision"),
        {
            "odepa": (
                70,
                30,
                "source:odepa",
                "ODEPA",
                say("precios mayoristas y al consumidor, cada semana", "wholesale and consumer prices, every week"),
            ),
            "ine": (70, 190, "source:ine", "INE", say("IPC de alimentos, cada mes", "food CPI, every month")),
            "load": (
                270,
                110,
                "icon:calendar",
                say("Carga semanal", "Weekly load"),
                say("descarga, limpia y calcula cada martes", "downloads, cleans and computes every Tuesday"),
            ),
            "gates": (
                455,
                110,
                "icon:shield@#199e70",
                say("Puertas de calidad", "Quality gates"),
                say("nada se publica si algo falla", "nothing is published if something fails"),
            ),
            "panel": (
                635,
                110,
                "brand:streamlit",
                say("Panel", "Panel"),
                say(
                    "P-1 a P-5: qué cambió, si es normal, la brecha, la inflación y la confianza",
                    "P-1 to P-5: what changed, whether it is normal, the gap, inflation and trust",
                ),
            ),
            "pricing": (
                835,
                20,
                "person:visitor",
                "Pricing",
                say("precio de hoy frente a la época y la inflación", "today's price against the season and inflation"),
            ),
            "buying": (
                835,
                140,
                "person:visitor",
                say("Compras", "Purchasing"),
                say("margen entre mayorista y consumidor", "margin between wholesale and consumer"),
            ),
            "board": (
                835,
                260,
                "person:visitor",
                say("Gerencia", "Management"),
                say("qué se movió y qué es inusual", "what moved and what is unusual"),
            ),
        },
        [
            ("odepa", "load", "CSV", "flow", "h"),
            ("ine", "load", say("IPC", "CPI"), "flow", "h"),
            ("load", "gates", "", "flow", "h"),
            ("gates", "panel", say("si todo pasa", "if all passes"), "flow", "h"),
            ("panel", "pricing", "", "flow", "h"),
            ("panel", "buying", "", "flow", "h"),
            ("panel", "board", "", "flow", "h"),
        ],
        say(
            "Cada cifra del panel se puede seguir hasta el archivo original de la fuente.",
            "Every figure of the panel can be traced back to the original file of the source.",
        ),
    )


def prd_requirements(mode):
    return graph(
        mode,
        say("Los requisitos, por área", "The requirements, by area"),
        {
            "product": (
                460,
                24,
                "icon:box",
                "GreenOcean",
                say("14 requisitos, cada uno con su prueba", "14 requirements, each with its test"),
            ),
            "load": (
                115,
                190,
                "icon:calendar",
                say("Carga", "Load"),
                say(
                    "RF-01 cada martes · RF-02 ninguna fila se pierde · RF-03 solo se publica una carga válida",
                    "RF-01 every Tuesday · RF-02 no row is lost · RF-03 only a valid load is published",
                ),
            ),
            "data": (
                345,
                190,
                "icon:database",
                say("Datos", "Data"),
                say(
                    "RF-04 precios reales · RF-05 alertas de cambios inusuales · RNF-02 cada cifra se puede comprobar",
                    "RF-04 real prices · RF-05 alerts on unusual changes · RNF-02 every figure can be checked",
                ),
            ),
            "panel": (
                575,
                190,
                "brand:streamlit",
                say("Panel", "Panel"),
                say(
                    "RF-06 SQL de solo lectura · RF-08 informe semanal · RNF-05 y RNF-06 legible, en una pantalla",
                    "RF-06 read-only SQL · RF-08 weekly report · RNF-05 and RNF-06 readable, on one screen",
                ),
            ),
            "safe": (
                805,
                190,
                "icon:lock",
                say("Seguridad y costo", "Security and cost"),
                say(
                    "RF-07 carga manual con clave · RNF-03 ningún secreto · RNF-01 costo cero · RNF-04 calidad vigilada",
                    "RF-07 manual load with a code · RNF-03 no secret · RNF-01 zero cost · RNF-04 quality watched",
                ),
            ),
        },
        [("product", area, "", "flow", "v") for area in ("load", "data", "panel", "safe")],
        limit=26,
    )


# endregion


# region SAD
def sad_weekly_sequence(mode):
    return sequence(
        mode,
        say("Secuencia de la carga semanal", "Sequence of the weekly load"),
        [
            ("actions", "GitHub Actions", "brand:github"),
            ("agent", say("Agente", "Agent"), "brand:python"),
            ("sources", "ODEPA · INE", "source:odepa"),
            ("etl", "SQLite · Parquet", "brand:sqlite"),
            ("dbt", "dbt · DuckDB", "brand:dbt"),
            ("tests", "pytest", "brand:pytest"),
            ("release", say("Release y main", "Release and main"), "brand:git"),
        ],
        [
            ("actions", "agent", say("martes 12:00 UTC: inicia", "Tuesday 12:00 UTC: starts"), "order"),
            ("agent", "sources", say("descarga los CSV y el IPC", "downloads the CSV files and the CPI"), "flow"),
            ("sources", "agent", say("archivos + huella SHA-256", "files + SHA-256 fingerprint"), "back"),
            ("agent", "etl", say("filas crudas → raw.db y bronce", "raw rows → raw.db and bronze"), "flow"),
            ("etl", "dbt", say("dbt build sobre el bronce", "dbt build on bronze"), "flow"),
            ("dbt", "dbt", say("modelos y pruebas de datos", "models and data tests"), "check"),
            (
                "gate",
                "",
                say(
                    "Puerta de publicación: si una prueba falla o la carga lee menos del 90 %, se detiene aquí",
                    "Publication gate: if a test fails or the load reads less than 90 %, it stops here",
                ),
                "stop",
            ),
            ("dbt", "tests", say("base nueva", "new database"), "flow"),
            ("tests", "tests", say("pytest y paridad con el respaldo", "pytest and parity with the backup"), "check"),
            (
                "tests",
                "release",
                say("publica datos.duckdb en «base-actual»", "publishes datos.duckdb in «base-actual»"),
                "flow",
            ),
            ("release", "actions", say("puntero a main · informe semanal", "pointer to main · weekly report"), "back"),
        ],
        say(
            "Si un paso falla, los siguientes no corren y la base publicada no cambia.",
            "If a step fails, the following ones do not run and the published database does not change.",
        ),
    )


def sad_panel_sequence(mode):
    return sequence(
        mode,
        say("Secuencia al abrir el panel", "Sequence when the panel opens"),
        [
            ("visitor", say("Visitante", "Visitor"), "person:visitor"),
            ("panel", "Streamlit", "brand:streamlit"),
            ("main", say("Puntero en main", "Pointer on main"), "brand:git"),
            ("release", "Release", "brand:github"),
            ("duckdb", "DuckDB", "brand:duckdb"),
        ],
        [
            ("visitor", "panel", say("abre una página", "opens a page"), "flow"),
            ("panel", "main", say("lee etl/datos.version", "reads etl/datos.version"), "flow"),
            ("main", "panel", say("huella, tamaño y fecha", "fingerprint, size and date"), "back"),
            (
                "panel",
                "release",
                say("si la base local es más antigua: descarga", "if the local database is older: downloads"),
                "flow",
            ),
            ("release", "panel", "datos.duckdb", "back"),
            ("panel", "panel", say("comprueba la huella SHA-256", "checks the SHA-256 fingerprint"), "check"),
            ("panel", "duckdb", say("consulta en solo lectura", "queries read-only"), "flow"),
            ("duckdb", "panel", say("filas", "rows"), "back"),
            ("panel", "visitor", say("la página con sus cifras", "the page with its figures"), "back"),
        ],
        say(
            "Si GitHub no responde, el panel sigue con la base que ya tiene.",
            "If GitHub does not respond, the panel goes on with the database it already has.",
        ),
    )


def sad_layers(mode):
    return graph(
        mode,
        say("Capas de los datos", "Data layers"),
        {
            "source": (
                65,
                30,
                "source:odepa",
                "ODEPA",
                say("los CSV tal como se publican", "the CSV files as published"),
            ),
            "landing": (
                215,
                30,
                "brand:sqlite",
                say("Aterrizaje", "Landing"),
                say("etl/raw.db: las filas tal como llegan", "etl/raw.db: the rows as they arrive"),
            ),
            "bronze": (
                370,
                30,
                "brand:apacheparquet",
                say("Bronce", "Bronze"),
                say("copia literal en Parquet, por fuente y año", "literal copy in Parquet, by source and year"),
            ),
            "silver": (
                530,
                30,
                "brand:dbt",
                say("Plata", "Silver"),
                say(
                    "staging e intermedio: tipos, reglas, semanas y rechazos",
                    "staging and intermediate: types, rules, weeks and rejections",
                ),
            ),
            "gold": (
                695,
                30,
                "brand:duckdb",
                say("Oro", "Gold"),
                say(
                    "marts: el modelo estrella, el IPC y la auditoría, en etl/datos.duckdb",
                    "marts: the star schema, the CPI and the audit, in etl/datos.duckdb",
                ),
            ),
            "panel": (
                855,
                30,
                "brand:streamlit",
                say("Panel", "Panel"),
                say("lee la base servida en solo lectura", "reads the served database read-only"),
            ),
        },
        [
            ("source", "landing", "", "flow", "h"),
            ("landing", "bronze", "", "flow", "h"),
            ("bronze", "silver", "", "flow", "h"),
            ("silver", "gold", "", "flow", "h"),
            ("gold", "panel", "", "flow", "h"),
        ],
        say(
            "El respaldo etl/datos.db calcula los mismos precios sin dbt, para la prueba de paridad.",
            "The backup etl/datos.db computes the same prices without dbt, for the parity test.",
        ),
        limit=20,
    )


def sad_deployment(mode):
    return graph(
        mode,
        say("Dónde corre cada pieza", "Where each piece runs"),
        {
            "author": (
                80,
                40,
                "person:author",
                say("Computador del autor", "The author's computer"),
                say(
                    "el código y las pruebas antes de cada push; etl/raw.db fuera de git",
                    "the code and the tests before each push; etl/raw.db outside git",
                ),
            ),
            "repo": (
                330,
                40,
                "brand:github",
                say("GitHub, rama main", "GitHub, main branch"),
                say("el código y el puntero de la base", "the code and the database pointer"),
            ),
            "actions": (
                330,
                230,
                "icon:calendar",
                "GitHub Actions",
                say(
                    "máquina efímera (Ubuntu): la carga de cada martes y las pruebas de cada push; caché de años cerrados",
                    "ephemeral machine (Ubuntu): each Tuesday's load and each push's tests; cache of closed years",
                ),
            ),
            "release": (
                600,
                230,
                "icon:box",
                say("Release «base-actual»", "«base-actual» release"),
                say("una sola copia de la base servida", "a single copy of the served database"),
            ),
            "cloud": (
                600,
                40,
                "brand:streamlit",
                "Streamlit Community Cloud",
                say("el panel, publicado desde main, en solo lectura", "the panel, published from main, read-only"),
            ),
            "secrets": (
                840,
                40,
                "icon:key",
                say("Secretos", "Secrets"),
                say("el token de GitHub y la clave de control", "the GitHub token and the control code"),
            ),
        },
        [
            ("author", "repo", "push", "order", "h"),
            ("repo", "actions", "", "order", "v"),
            ("actions", "release", say("publica la base", "publishes the database"), "flow", "h"),
            ("repo", "cloud", say("despliega main", "deploys main"), "order", "h"),
            ("release", "cloud", say("descarga y huella", "download and fingerprint"), "flow", "v"),
            ("cloud", "secrets", "", "check", "h"),
        ],
        limit=26,
    )


# endregion


# region ADR
def adr_map(mode):
    return graph(
        mode,
        say("Dónde actúa cada decisión", "Where each decision acts"),
        {
            "source": (
                70,
                30,
                "source:odepa",
                say("Fuentes", "Sources"),
                say("ADR-01 solo archivos oficiales", "ADR-01 only official files"),
            ),
            "load": (
                250,
                30,
                "icon:calendar",
                say("Carga", "Load"),
                say(
                    "ADR-04 crudos fuera del repositorio · ADR-10 rehacer todo en cada carga",
                    "ADR-04 raw data outside the repository · ADR-10 rebuild everything on each load",
                ),
            ),
            "data": (
                450,
                30,
                "brand:dbt",
                say("Datos", "Data"),
                say(
                    "ADR-30 Parquet, dbt y DuckDB · ADR-19 modelo estrella · ADR-33 precios reales con el IPC",
                    "ADR-30 Parquet, dbt and DuckDB · ADR-19 star schema · ADR-33 real prices with the CPI",
                ),
            ),
            "gate": (
                650,
                30,
                "icon:shield@#199e70",
                say("Puerta", "Gate"),
                say(
                    "ADR-11 publicar solo si pasan las pruebas · ADR-34 tres bases separadas",
                    "ADR-11 publish only if the tests pass · ADR-34 three separate databases",
                ),
            ),
            "publish": (
                850,
                30,
                "brand:streamlit",
                say("Publicación y costo", "Publication and cost"),
                say(
                    "ADR-35 la base en un release · ADR-02 Actions y Streamlit · ADR-31 sin nube de pago",
                    "ADR-35 the database in a release · ADR-02 Actions and Streamlit · ADR-31 no paid cloud",
                ),
            ),
        },
        [
            ("source", "load", "", "flow", "h"),
            ("load", "data", "", "flow", "h"),
            ("data", "gate", "", "flow", "h"),
            ("gate", "publish", "", "flow", "h"),
        ],
        limit=22,
    )


def adr_timeline(mode):
    return timeline(
        mode,
        say("Cuándo se tomó cada decisión", "When each decision was taken"),
        [
            (
                "11-10-2026" if not i18n.is_english() else "2026-10-11",
                say("Primera versión", "First version"),
                ["ADR-01 · ADR-02 · ADR-04", "ADR-10 · ADR-11 · ADR-19"],
            ),
            (
                "19-10-2026" if not i18n.is_english() else "2026-10-19",
                say("Data warehouse con dbt", "Data warehouse with dbt"),
                ["ADR-30 · ADR-31", "ADR-33 · ADR-34"],
            ),
            (
                "24-10-2026" if not i18n.is_english() else "2026-10-24",
                say("Base en un release", "Database in a release"),
                ["ADR-35"],
            ),
        ],
    )


def adr_before_after(mode):
    return graph(
        mode,
        say("ADR-35: la base servida, antes y después", "ADR-35: the served database, before and after"),
        {
            "load1": (
                90,
                30,
                "icon:calendar",
                say("Antes: cada carga", "Before: each load"),
                say("hacía un commit de la base, unos 48 MB", "committed the database, about 48 MB"),
            ),
            "git1": (
                460,
                30,
                "icon:commit@#e5484d",
                say("Historial de Git", "Git history"),
                say("guardaba cada versión: cerca de 1 GB más por año", "kept every version: about 1 GB more per year"),
            ),
            "panel1": (
                820,
                30,
                "brand:streamlit",
                say("Panel", "Panel"),
                say("leía la base del repositorio", "read the database from the repository"),
            ),
            "load2": (
                90,
                190,
                "icon:calendar",
                say("Después: cada carga", "After: each load"),
                say("reemplaza el archivo del release", "replaces the file of the release"),
            ),
            "release": (
                460,
                190,
                "icon:box@#199e70",
                say("Release «base-actual»", "«base-actual» release"),
                say(
                    "una sola copia publicada; en Git, solo el puntero",
                    "a single published copy; in Git, only the pointer",
                ),
            ),
            "panel2": (
                820,
                190,
                "brand:streamlit",
                say("Panel", "Panel"),
                say("descarga la base y comprueba su huella", "downloads the database and checks its fingerprint"),
            ),
        },
        [
            ("load1", "git1", "commit", "back", "h"),
            ("git1", "panel1", "", "back", "h"),
            ("load2", "release", say("reemplaza", "replaces"), "flow", "h"),
            ("release", "panel2", say("huella SHA-256", "SHA-256 fingerprint"), "flow", "h"),
        ],
        say("Medidas del 24-10-2026.", "Measurements of 2026-10-24."),
        limit=26,
    )


# endregion


# region Test plan (with security)
def tests_levels(mode):
    load, push, visual = (
        say("En cada carga", "On each load"),
        say("En cada push", "On every push"),
        say("Antes de un cambio visual", "Before a visual change"),
    )
    return graph(
        mode,
        say("Qué se prueba y cuándo", "What is tested and when"),
        {
            "load": (70, 30, "icon:calendar", load, say("semanal.yml, cada martes", "semanal.yml, every Tuesday")),
            "dbt": (
                270,
                30,
                "brand:dbt",
                say("Pruebas de dbt", "dbt tests"),
                say("claves, valores, relaciones y conciliación", "keys, values, relationships and reconciliation"),
            ),
            "gate": (
                470,
                30,
                "icon:shield@#199e70",
                say("Puerta de publicación", "Publication gate"),
                say("no publica una carga incompleta", "does not publish an incomplete load"),
            ),
            "parity": (
                670,
                30,
                "icon:arrows",
                say("Paridad", "Parity"),
                say("dbt y el ETL en Python dan lo mismo", "dbt and the Python ETL give the same"),
            ),
            "rebuild": (
                850,
                30,
                "brand:sqlite",
                say("Reconstrucción", "Rebuild"),
                say("cada precio, desde las filas crudas", "each price, from the raw rows"),
            ),
            "push": (70, 190, "icon:commit", push, say("pruebas.yml, en cada cambio", "pruebas.yml, on every change")),
            "audit": (
                270,
                190,
                "brand:pytest",
                say("Auditoría de cifras", "Figure audit"),
                say("las cifras del panel, contra la base", "the panel's figures, against the database"),
            ),
            "panel": (
                470,
                190,
                "brand:streamlit",
                say("Panel", "Panel"),
                say("cada página se dibuja sin errores", "each page draws without errors"),
            ),
            "security": (
                670,
                190,
                "icon:lock",
                say("Seguridad", "Security"),
                say("los catorce ataques S-01 a S-14", "the fourteen attacks S-01 to S-14"),
            ),
            "visual": (
                70,
                340,
                "icon:eye",
                visual,
                say("Playwright, fuera del proyecto", "Playwright, outside the project"),
            ),
            "measure": (
                270,
                340,
                "icon:ruler",
                say("Medición de pantallas", "Screen measurement"),
                say("cada página en una pantalla", "each page on one screen"),
            ),
            "print": (
                470,
                340,
                "icon:printer",
                say("Impresión", "Printing"),
                say("cada documento impreso igual a su página", "each printed document equal to its page"),
            ),
        },
        [
            ("load", "dbt", "", "check", "h"),
            ("dbt", "gate", "", "check", "h"),
            ("gate", "parity", "", "check", "h"),
            ("parity", "rebuild", "", "check", "h"),
            ("push", "audit", "", "check", "h"),
            ("audit", "panel", "", "check", "h"),
            ("panel", "security", "", "check", "h"),
            ("visual", "measure", "", "check", "h"),
            ("measure", "print", "", "check", "h"),
        ],
        limit=22,
    )


def tests_manual_sequence(mode):
    return sequence(
        mode,
        say("Secuencia de una carga manual con la clave", "Sequence of a manual load with the code"),
        [
            ("author", say("Autor", "Author"), "person:author"),
            ("panel", say("Panel", "Panel"), "brand:streamlit"),
            ("secrets", say("Secretos", "Secrets"), "brand:streamlit"),
            ("api", say("API de GitHub", "GitHub API"), "brand:github"),
            ("workflow", "semanal.yml", "brand:github"),
        ],
        [
            ("author", "panel", say("escribe la clave de control", "types the control code"), "flow"),
            ("panel", "secrets", say("lee CONTROL_CODE", "reads CONTROL_CODE"), "flow"),
            ("panel", "panel", say("compara en tiempo constante", "compares in constant time"), "check"),
            (
                "gate",
                "",
                say(
                    "Clave incorrecta: «Clave incorrecta.» y el botón no aparece",
                    "Wrong code: «Clave incorrecta.» and the button does not appear",
                ),
                "stop",
            ),
            ("panel", "author", say("aparece «Ejecutar pipeline ahora»", "«Run pipeline now» appears"), "back"),
            ("author", "panel", say("clic", "click"), "flow"),
            (
                "panel",
                "secrets",
                say("lee el token, que nunca se muestra", "reads the token, which is never shown"),
                "flow",
            ),
            ("panel", "api", "workflow_dispatch", "order"),
            ("api", "workflow", say("inicia la carga", "starts the load"), "order"),
            ("workflow", "panel", say("estado de cada paso", "status of each step"), "back"),
            ("panel", "author", say("progreso en el Centro de operación", "progress in the Operations center"), "back"),
        ],
        say(
            "El workflow solo puede escribir contenido y crear issues: permisos mínimos.",
            "The workflow can only write content and create issues: least privilege.",
        ),
    )


def tests_ci_sequence(mode):
    return sequence(
        mode,
        say("Secuencia de un cambio de código", "Sequence of a code change"),
        [
            ("author", say("Autor", "Author"), "person:author"),
            ("repo", say("GitHub, main", "GitHub, main"), "brand:git"),
            ("ci", "pruebas.yml", "brand:pytest"),
            ("cloud", "Streamlit Cloud", "brand:streamlit"),
        ],
        [
            ("author", "author", say("pruebas en su computador", "tests on their computer"), "check"),
            ("author", "repo", "git push", "flow"),
            ("repo", "ci", say("lanza pruebas.yml", "launches pruebas.yml"), "order"),
            ("ci", "ci", say("dbt parse y pytest", "dbt parse and pytest"), "check"),
            ("ci", "repo", say("verde o rojo junto al commit", "green or red next to the commit"), "back"),
            ("repo", "cloud", say("despliega main", "deploys main"), "flow"),
        ],
        say(
            "El resultado avisa, pero no detiene el despliegue: un riesgo aceptado y declarado.",
            "The result warns, but it does not stop the deployment: an accepted and declared risk.",
        ),
    )


def tests_actors(mode):
    return graph(
        mode,
        say("Quién participa en la seguridad", "Who takes part in security"),
        {
            "visitor": (
                90,
                20,
                "person:visitor",
                say("Visitante", "Visitor"),
                say(
                    "sin cuenta: lee el panel y usa el SQL de solo lectura",
                    "no account: reads the panel and uses the read-only SQL",
                ),
            ),
            "author": (
                90,
                230,
                "person:author",
                say("Autor", "Author"),
                say(
                    "su cuenta en GitHub y Streamlit, con dos pasos",
                    "their account on GitHub and Streamlit, with two steps",
                ),
            ),
            "panel": (
                370,
                125,
                "brand:streamlit",
                "Streamlit",
                say(
                    "compara la clave en tiempo constante; nunca muestra el token",
                    "compares the code in constant time; never shows the token",
                ),
            ),
            "duckdb": (
                640,
                20,
                "brand:duckdb",
                "DuckDB",
                say("base en solo lectura, sin archivos ni red", "read-only database, no files or network"),
            ),
            "secrets": (
                640,
                230,
                "icon:key",
                say("Secretos del panel", "Panel secrets"),
                say(
                    "CONTROL_CODE y GITHUB_TOKEN, fuera del repositorio",
                    "CONTROL_CODE and GITHUB_TOKEN, outside the repository",
                ),
            ),
            "repo": (
                835,
                20,
                "brand:github",
                say("Repositorio", "Repository"),
                say("público, sin ningún secreto", "public, with no secret"),
            ),
            "actions": (
                835,
                230,
                "icon:calendar",
                "GitHub Actions",
                say(
                    "workflow con permisos mínimos: contenido e issues",
                    "workflow with least privilege: content and issues",
                ),
            ),
        },
        [
            ("visitor", "panel", say("SQL con límites", "SQL with limits"), "order", "h", "start"),
            ("author", "panel", say("clave de control", "control code"), "order", "h", "start"),
            ("panel", "duckdb", say("solo lectura", "read-only"), "flow", "h"),
            ("panel", "secrets", say("lee", "reads"), "check", "h"),
            ("secrets", "actions", say("token: carga manual", "token: manual load"), "order", "h"),
            ("repo", "actions", say("workflow", "workflow"), "order", "v"),
        ],
        limit=24,
    )


def manual_fault_tree(mode):
    rows = [
        (
            say("Falló la descarga de ODEPA", "The ODEPA download failed"),
            say(
                "Esperar unas horas y volver a lanzar; con UNEXPECTED_HEADER, adaptar el agente",
                "Wait a few hours and launch again; with UNEXPECTED_HEADER, adapt the agent",
            ),
        ),
        (
            say("Falló el ETL de respaldo", "The backup ETL failed"),
            say(
                "Revisar el archivo en ODEPA; una región o un canal nuevos van a las listas del ETL",
                "Check the file at ODEPA; a new region or channel goes into the lists of the ETL",
            ),
        ),
        (
            say("Falló dbt o TOO_FEW_ROWS", "dbt or TOO_FEW_ROWS failed"),
            say(
                "Leer en el log qué modelo o prueba falló; nombra la tabla y la regla",
                "Read in the log which model or test failed; it names the table and the rule",
            ),
        ),
        (
            say("Falló pytest", "pytest failed"),
            say(
                "Leer qué prueba falló; indica el producto o la semana",
                "Read which test failed; it names the product or the week",
            ),
        ),
        (
            say("Falló la publicación", "Publication failed"),
            say(
                "Revisar Settings → Actions → Workflow permissions: «Read and write»",
                "Check Settings → Actions → Workflow permissions: «Read and write»",
            ),
        ),
    ]
    nodes = {
        "root": (
            90,
            200,
            "icon:mail@#e5484d",
            say("Llegó «Run failed»", "«Run failed» arrived"),
            say("o un paso está en rojo", "or a step is red"),
        )
    }
    edges = []
    for index, (when, then) in enumerate(rows):
        y = 20 + 95 * index
        nodes[f"w{index}"] = (380, y, "icon:warning@#c98500", when, "")
        nodes[f"t{index}"] = (720, y, "icon:tool", say("Qué hacer", "What to do"), then)
        edges += [("root", f"w{index}", "", "back", "h"), (f"w{index}", f"t{index}", "", "flow", "h")]
    return graph(
        mode,
        say("Qué hacer cuando algo falla", "What to do when something fails"),
        nodes,
        edges,
        say(
            "Mientras tanto, el panel muestra la última carga válida.",
            "Meanwhile, the panel shows the last valid load.",
        ),
        limit=40,
    )


def manual_calendar(mode):
    return timeline(
        mode,
        say("Tareas periódicas", "Periodic tasks"),
        [
            (
                say("Cada martes", "Every Tuesday"),
                say("Revisar el resultado", "Check the result"),
                [say("Centro de operación o correo", "Operations center or email")],
            ),
            (
                say("Cada enero", "Every January"),
                say("Año nuevo de ODEPA", "ODEPA's new year"),
                [say("dos líneas en agent/input.csv", "two lines in agent/input.csv")],
            ),
            (
                say("Periódicamente", "Periodically"),
                say("Copiar las descargas", "Copy the downloads"),
                [say("agent/downloads a otro disco", "agent/downloads to another disk")],
            ),
            (
                say("Antes del vencimiento", "Before it expires"),
                say("Renovar el token", "Renew the token"),
                [say("el panel avisa 14 días antes", "the panel warns 14 days before")],
            ),
        ],
    )


def manual_recovery_sequence(mode):
    return sequence(
        mode,
        say(
            "Secuencia de recuperación si el release pierde su archivo",
            "Recovery sequence if the release loses its file",
        ),
        [
            ("author", say("Autor", "Author"), "person:author"),
            ("local", say("Computador", "Computer"), "brand:python"),
            ("tests", "pytest", "brand:pytest"),
            ("github", say("GitHub: release y main", "GitHub: release and main"), "brand:github"),
            ("panel", say("Panel", "Panel"), "brand:streamlit"),
        ],
        [
            ("author", "local", "python etl/pipeline.py --local", "order"),
            ("local", "tests", say("suite completa", "full suite"), "check"),
            ("tests", "author", say("en verde", "green"), "back"),
            (
                "author",
                "github",
                say("sube datos.duckdb a «base-actual»", "uploads datos.duckdb to «base-actual»"),
                "flow",
            ),
            ("author", "local", "python bi/served_database.py --pointer", "order"),
            ("local", "github", say("push del puntero a main", "push of the pointer to main"), "flow"),
            (
                "panel",
                "github",
                say(
                    "ve el puntero nuevo, descarga y comprueba la huella",
                    "sees the new pointer, downloads and checks the fingerprint",
                ),
                "check",
            ),
        ],
    )


# endregion


# region Decision index
INDEX_THEMES = [
    ("Fuentes e ingesta", "Sources and ingestion", GREEN),
    ("Modelo y reglas de datos", "Data model and rules", VIOLET),
    ("Pipeline y publicación", "Pipeline and publication", BLUE),
    ("Calidad y auditoría", "Quality and audit", GREEN),
    ("Seguridad", "Security", RED),
    ("Operación y observabilidad", "Operations and observability", AMBER),
    ("Panel", "Panel", BLUE),
    ("Documentación", "Documentation", GREY),
]


def count_decisions():
    """[(theme, count)] read from the index itself, so the figure never disagrees with its tables."""
    import re

    text = (i18n.documents_dir() / "INDICE_DECISIONES.md").read_text(encoding="utf-8")
    counts = []
    for spanish, english, color in INDEX_THEMES:
        heading = english if i18n.is_english() else spanish
        section = re.split(rf"^## \d+\. {re.escape(heading)}$", text, flags=re.MULTILINE)
        body = section[1].split("\n## ", 1)[0] if len(section) > 1 else ""
        counts.append((heading, len(re.findall(r"\| D-\d+ \|$", body, re.MULTILINE)), color))
    return counts


def index_themes(mode):
    return bars(
        mode,
        say("Decisiones por tema", "Decisions by theme"),
        count_decisions(),
        say("Contadas en las tablas de este índice.", "Counted in the tables of this index."),
    )


def index_map(mode):
    return graph(
        mode,
        say("Dónde actúa cada tema en el sistema", "Where each theme acts in the system"),
        {
            "sources": (
                70,
                30,
                "source:odepa",
                say("Fuentes e ingesta", "Sources and ingestion"),
                say("qué se descarga y cómo", "what is downloaded and how"),
            ),
            "model": (
                250,
                30,
                "brand:dbt",
                say("Modelo y reglas", "Model and rules"),
                say("cómo se calcula cada precio", "how each price is computed"),
            ),
            "pipeline": (
                430,
                30,
                "icon:calendar",
                say("Pipeline y publicación", "Pipeline and publication"),
                say("cuándo se publica", "when it is published"),
            ),
            "quality": (
                610,
                30,
                "icon:shield@#199e70",
                say("Calidad y auditoría", "Quality and audit"),
                say("qué detiene una carga", "what stops a load"),
            ),
            "panel": (
                790,
                30,
                "brand:streamlit",
                say("Panel", "Panel"),
                say("cómo se lee en una pantalla", "how it reads on one screen"),
            ),
            "security": (
                430,
                190,
                "icon:lock",
                say("Seguridad", "Security"),
                say("quién puede hacer qué", "who can do what"),
            ),
            "ops": (
                610,
                190,
                "icon:pulse",
                say("Operación", "Operations"),
                say("cómo se sabe qué pasó", "how we know what happened"),
            ),
            "docs": (
                790,
                190,
                "icon:files",
                say("Documentación", "Documentation"),
                say("cómo se explica", "how it is explained"),
            ),
        },
        [
            ("sources", "model", "", "flow", "h"),
            ("model", "pipeline", "", "flow", "h"),
            ("pipeline", "quality", "", "flow", "h"),
            ("quality", "panel", "", "flow", "h"),
            ("security", "pipeline", "", "check", "v"),
            ("ops", "quality", "", "check", "v"),
            ("docs", "panel", "", "back", "v"),
        ],
        limit=20,
    )


def index_adr(mode):
    nodes = {
        "root": (
            100,
            120,
            "icon:files",
            say("Registro de decisiones", "Decision log"),
            say("cada cambio de comportamiento, con sus pruebas", "each change of behavior, with its tests"),
        )
    }
    rows = [
        (
            say("Cambia la arquitectura", "It changes the architecture"),
            "icon:star",
            say("Este índice y un registro ADR", "This index and an ADR record"),
            say("contexto, alternativas y consecuencias", "context, alternatives and consequences"),
        ),
        (
            say("Cambia uno de los ocho temas", "It changes one of the eight themes"),
            "icon:layers",
            say("Este índice", "This index"),
            say("una fila con lo que se decidió", "one row with what was decided"),
        ),
        (
            say("Es un ajuste menor", "It is a minor adjustment"),
            "icon:commit",
            say("Solo el registro completo", "Only the full log"),
            say("docs/DECISIONES.md, en orden cronológico", "docs/DECISIONES.md, in chronological order"),
        ),
    ]
    edges = []
    for index, (when, icon, where, detail) in enumerate(rows):
        y = 20 + 110 * index
        nodes[f"w{index}"] = (420, y, "icon:warning@#c98500", when, "")
        nodes[f"t{index}"] = (740, y, icon, where, detail)
        edges += [("root", f"w{index}", "", "flow", "h"), (f"w{index}", f"t{index}", "", "flow", "h")]
    return graph(
        mode, say("Cómo llega una decisión a este índice", "How a decision reaches this index"), nodes, edges, limit=30
    )


# endregion


# region Glossary
def glossary_layers(mode):
    return graph(
        mode,
        say("Los términos de los datos, en orden", "The data terms, in order"),
        {
            "csv": (
                70,
                30,
                "icon:file",
                "CSV",
                say(
                    "el archivo que publica ODEPA; su huella es el SHA-256",
                    "the file ODEPA publishes; its fingerprint is the SHA-256",
                ),
            ),
            "landing": (250, 30, "brand:sqlite", say("Aterrizaje", "Landing"), "etl/raw.db"),
            "bronze": (
                430,
                30,
                "brand:apacheparquet",
                say("Bronce", "Bronze"),
                say("copia exacta en Parquet", "exact copy in Parquet"),
            ),
            "silver": (
                610,
                30,
                "brand:dbt",
                say("Plata", "Silver"),
                say(
                    "staging e intermedio de dbt; las RN, reglas de negocio",
                    "dbt staging and intermediate; the RN, business rules",
                ),
            ),
            "gold": (
                790,
                30,
                "brand:duckdb",
                say("Oro", "Gold"),
                say(
                    "el modelo estrella en la base servida, etl/datos.duckdb",
                    "the star schema in the served database, etl/datos.duckdb",
                ),
            ),
        },
        [
            ("csv", "landing", "", "flow", "h"),
            ("landing", "bronze", "", "flow", "h"),
            ("bronze", "silver", "", "flow", "h"),
            ("silver", "gold", "", "flow", "h"),
        ],
        limit=22,
    )


def glossary_actors(mode):
    return graph(
        mode,
        say("Actores y sistemas", "Actors and systems"),
        {
            "odepa": (70, 30, "source:odepa", "ODEPA", say("precios", "prices")),
            "ine": (70, 180, "source:ine", "INE", say("IPC", "CPI")),
            "actions": (
                290,
                105,
                "icon:calendar",
                "GitHub Actions",
                say("la carga y las pruebas", "the load and the tests"),
            ),
            "github": (500, 105, "brand:github", "GitHub", say("código, release e issues", "code, release and issues")),
            "streamlit": (690, 105, "brand:streamlit", "Streamlit Cloud", say("el panel", "the panel")),
            "visitor": (860, 30, "person:visitor", say("Visitante", "Visitor"), say("lee el panel", "reads the panel")),
            "author": (
                860,
                180,
                "person:author",
                say("Autor", "Author"),
                say("mantiene el proyecto", "maintains the project"),
            ),
        },
        [
            ("odepa", "actions", "", "flow", "h"),
            ("ine", "actions", "", "flow", "h"),
            ("actions", "github", "", "flow", "h"),
            ("github", "streamlit", "", "flow", "h"),
            ("streamlit", "visitor", "", "flow", "h"),
            ("streamlit", "author", "", "flow", "h"),
        ],
        limit=20,
    )


def glossary_figure(mode):
    return graph(
        mode,
        say("De la fuente a la cifra", "From the source to the figure"),
        {
            "row": (
                70,
                30,
                "icon:file",
                say("Fila", "Row"),
                say("una cotización, tal como llega", "a quote, as it arrives"),
            ),
            "check": (
                250,
                30,
                "icon:check@#199e70",
                say("Validación", "Validation"),
                say("RN-11: se carga o se rechaza", "RN-11: loaded or rejected"),
            ),
            "week": (
                430,
                30,
                "icon:calendar",
                say("Precio semanal", "Weekly price"),
                say(
                    "por producto, región y canal; un lunes por semana",
                    "by product, region and channel; one Monday per week",
                ),
            ),
            "kpi": (
                610,
                30,
                "icon:chart",
                say("Indicador", "Indicator"),
                say("KPI: el cambio, el margen, el precio real", "KPI: the change, the margin, the real price"),
            ),
            "alert": (
                790,
                30,
                "icon:bell@#e5484d",
                say("Alerta de precio", "Price alert"),
                say("cambio inusual de al menos 10 %", "unusual change of at least 10 %"),
            ),
        },
        [
            ("row", "check", "", "flow", "h"),
            ("check", "week", "", "flow", "h"),
            ("week", "kpi", "", "flow", "h"),
            ("kpi", "alert", "", "flow", "h"),
        ],
        limit=22,
    )


# endregion


# Marker → builder. The heights are automatic: each frame takes the height of its figure.


# region The quality plan (D-355): the two qualities, how an indicator reads and the weekly cycle. Counts and words are
# read from docs/calidad, never written by hand.
def quality_qualities(mode):
    from bi import quality_metrics

    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    kinds = {
        kind: [key for key, *_ in quality_metrics.INDICATORS if goals.get(key, {}).get("tipo") == kind]
        for kind in ("datos", "codigo")
    }
    return graph(
        mode,
        say("Las dos calidades que medimos", "The two qualities we measure"),
        {
            "plan": (
                460,
                30,
                "icon:shield",
                say("Calidad", "Quality"),
                say("lo que el plan cuida", "what the plan looks after"),
            ),
            "data": (
                230,
                170,
                "icon:database",
                say("Datos que publicamos", "Data we publish"),
                say(
                    f"ISO/IEC 25012 · {len(kinds['datos'])} indicadores",
                    f"ISO/IEC 25012 · {len(kinds['datos'])} indicators",
                ),
            ),
            "code": (
                690,
                170,
                "icon:code",
                say("Código que los trata", "Code that treats them"),
                say(
                    f"ISO/IEC 25010 · {len(kinds['codigo'])} indicadores",
                    f"ISO/IEC 25010 · {len(kinds['codigo'])} indicators",
                ),
            ),
        },
        [("plan", "data", "", "flow", "vh"), ("plan", "code", "", "flow", "vh")],
    )


def quality_states(mode):
    from bi import quality_metrics

    policy = quality_metrics.read(quality_metrics.POLICY_FILE)["estados"]
    word = {key: say(*value) for key, value in policy.items()}
    return timeline(
        mode,
        say("Cómo se lee un indicador", "How an indicator reads"),
        [
            (say("en la meta", "at the goal"), word["cumple"], [say("o mejor", "or better")]),
            (
                say("entre meta y aceptable", "between goal and acceptable"),
                word["aviso"],
                [say("todavía se acepta", "still accepted")],
            ),
            (
                say("pasa el aceptable", "past the acceptable"),
                word["urgente"],
                [say("dentro del margen crítico", "within the critical margin")],
            ),
            (
                say("más allá del margen", "beyond the margin"),
                word["critico"],
                [say("se actúa de inmediato", "act at once")],
            ),
        ],
        say(
            "El autor fija la meta, el aceptable y el margen de cada indicador.",
            "The author sets the goal, the acceptable and the margin of each indicator.",
        ),
    )


def quality_cycle(mode):
    return graph(
        mode,
        say("El ciclo de cada semana", "The cycle of every week"),
        {
            "measure": (
                90,
                30,
                "icon:ruler",
                say("Medir", "Measure"),
                say("pruebas y herramientas en el CI", "tests and tools in the CI"),
            ),
            "check": (
                300,
                30,
                "icon:check",
                say("Comparar", "Compare"),
                say("cada indicador con su aceptable", "each indicator with its acceptable"),
            ),
            "report": (
                510,
                30,
                "icon:file",
                say("Informe numerado", "Numbered report"),
                say("no se edita después", "never edited afterwards"),
            ),
            "approve": (
                720,
                30,
                "icon:eye",
                say("Aprobación", "Approval"),
                say("el autor lo revisa y lo acepta", "the author reviews and accepts it"),
            ),
            "register": (
                510,
                200,
                "icon:warning",
                say("Registro de fallas", "Failure register"),
                say("una línea por campo", "one line per field"),
            ),
            "improve": (
                90,
                200,
                "icon:tool",
                say("Mejorar", "Improve"),
                say("la causa se corrige, no se oculta", "the cause is fixed, never hidden"),
            ),
        },
        [
            ("measure", "check", "", "flow", "h"),
            ("check", "report", "", "flow", "h"),
            ("report", "approve", "", "flow", "h"),
            ("approve", "register", say("si algo falló", "if something failed"), "check", "vh"),
            ("register", "improve", "", "flow", "h"),
            ("improve", "measure", say("la semana siguiente", "the next week"), "back", "v"),
        ],
    )


# endregion

FIGURES = {
    "contexto": sad_context,
    "contenedores": sad_containers,
    "sop": tests_procedure,
    "componentes_carga": sad_components_load,
    "componentes_panel": sad_components_panel,
    "escenarios": sad_scenarios,
    "valor": prd_value,
    "requisitos": prd_requirements,
    "secuencia_carga": sad_weekly_sequence,
    "secuencia_panel": sad_panel_sequence,
    "capas": sad_layers,
    "despliegue": sad_deployment,
    "mapa_adr": adr_map,
    "tiempo_adr": adr_timeline,
    "antes_despues": adr_before_after,
    "niveles": tests_levels,
    "secuencia_manual": tests_manual_sequence,
    "secuencia_ci": tests_ci_sequence,
    "actores": tests_actors,
    "arbol_fallas": manual_fault_tree,
    "calendario": manual_calendar,
    "secuencia_recuperacion": manual_recovery_sequence,
    "temas": index_themes,
    "mapa_temas": index_map,
    "adr_decisiones": index_adr,
    "terminos_capas": glossary_layers,
    "terminos_actores": glossary_actors,
    "terminos_cifra": glossary_figure,
    "calidades": quality_qualities,
    "estados_calidad": quality_states,
    "ciclo_calidad": quality_cycle,
}
