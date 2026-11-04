"""The figures of the documents (D-289): sequences, layers, timelines, a fault tree, nodes, bars and before/after.

Every figure is one HTML document for st.iframe, drawn in the visual language of the other document views: no
background, flat brand logos, the colors of the theme and text that never shrinks below 12 px. The texts live here in
both languages (say(es, en)), so a figure reads in the language of the visit and its PDF too. The facts each figure
states are the ones of the code and the workflows; tests/test_doc_figures.py checks the files and steps they name.
"""

import html

from bi import charts, doc_views, i18n, queries


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


def edge_label(points, label, at_start, halo, width, left=False):
    """The label of a line, on its last stretch when it has room (the first may be shared by a fork), else on its
    longest; above a horizontal stretch, beside a vertical one. D-426: a label of several lines («\n») keeps its first
    line above a horizontal stretch and the rest under it, and stacks them beside a vertical one."""
    lines = label.split("\n")
    longest = max(len(line) for line in lines)
    stretches = list(zip(points, points[1:]))
    last = stretches[-1]
    if at_start:  # two lines that end on the same stretch: each label on its own start
        (ax, ay), (bx, by) = stretches[0]
    else:
        (ax, ay), (bx, by) = (
            last if stretch_length(last) >= max(70, longest * 6.2) else max(stretches, key=stretch_length)
        )
    style = f'font-size="11" stroke="{halo}" stroke-width="4" paint-order="stroke"'
    if ay == by:
        rows = [ay - 6] + [ay + 15 + 13 * index for index in range(len(lines) - 1)]
        return "".join(
            f'<text class="mut" x="{(ax + bx) / 2:.1f}" y="{y:.1f}" text-anchor="middle" {style}>{esc(line)}</text>'
            for line, y in zip(lines, rows)
        )
    # beside a vertical stretch: on its right, or on its left near the right edge of the figure
    on_left = left or ax + 7 + longest * 6.2 > width
    side = f'x="{ax - 7:.1f}" text-anchor="end"' if on_left else f'x="{ax + 7:.1f}"'
    top = (ay + by) / 2 + 4 - 6.5 * (len(lines) - 1)
    return "".join(
        f'<text class="mut" {side} y="{top + 13 * index:.1f}" {style}>{esc(line)}</text>'
        for index, line in enumerate(lines)
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
            at = where[0] if where else ""  # «start»: on its first stretch; «left»: beside a vertical one, on its left
            lines_svg.append(edge_label(points, label, at == "start", halo, width, left=at == "left"))
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
                250,
                20,
                "person:visitor",
                say("Usuario", "User"),
                say("ve el negocio, sin cuenta", "sees the business, no account"),
            ),
            "professional": (
                460,
                20,
                "person:professional",
                say("Profesional", "Professional"),
                say("ve todo el proyecto, sin cuenta", "sees the whole project, no account"),
            ),
            "admin": (
                670,
                20,
                "person:author",
                say("Autor", "Author"),
                say(
                    "lo mismo, y con la clave lanza la carga y mantiene el código",
                    "the same, and with the code launches the load and maintains the code",
                ),
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
                190,
                "source:odepa",
                "ODEPA",
                say("precios mayoristas y al consumidor", "wholesale and consumer prices"),
            ),
            "ine": (90, 330, "source:ine", "INE", say("IPC de alimentos", "food CPI")),
            "github": (
                830,
                190,
                "brand:github",
                "GitHub",
                say(
                    "aloja el código, ejecuta semanal.yml y guarda la Base DuckDB en el release «base-actual»",
                    "hosts the code, runs semanal.yml and keeps the DuckDB database in the «base-actual» release",
                ),
            ),
            "cloud": (
                830,
                330,
                "brand:streamlit",
                "Streamlit Community Cloud",
                say("publica el panel", "publishes the panel"),
            ),
        },
        [
            ("visitor", "system", say("lee", "reads"), "flow", "v"),
            ("professional", "system", say("lee", "reads"), "flow", "v"),
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
            "served": (
                560,
                175,
                "brand:duckdb",
                say("Base DuckDB · etl/datos.duckdb", "DuckDB database · etl/datos.duckdb"),
                say("en el release «base-actual»", "in the «base-actual» release"),
            ),
            "backup": (
                560,
                300,
                "brand:sqlite",
                say("Respaldo · etl/datos.db", "Backup · etl/datos.db"),
                say(
                    "los mismos precios sin dbt, para comprobar que dbt no cambió ninguna cifra",
                    "the same prices without dbt, to check that dbt changed no figure",
                ),
            ),
            "panel": (
                830,
                175,
                "brand:streamlit",
                say("Panel web", "Web panel"),
                say("Streamlit: bi/dashboard.py, en solo lectura", "Streamlit: bi/dashboard.py, read-only"),
            ),
            "github": (
                400,
                470,
                "brand:github",
                "GitHub",
                say(
                    "repositorio, Actions y el release «base-actual»",
                    "repository, Actions and the «base-actual» release",
                ),
            ),
            "user": (690, 20, "person:visitor", say("Usuario", "User"), say("ve el negocio", "sees the business")),
            "professional": (
                790,
                20,
                "person:professional",
                say("Profesional", "Professional"),
                say("ve todo", "sees it all"),
            ),
            "author": (
                890,
                20,
                "person:author",
                say("Autor", "Author"),
                say("con clave", "with the key"),
            ),
        },
        [
            ("load", "odepa", "HTTPS", "flow", "h"),
            ("load", "ine", "HTTPS", "flow", "h"),
            ("load", "work", say("lee y escribe", "reads and writes"), "flow", "h"),
            ("load", "served", say("publica", "publishes"), "flow", "h"),
            ("load", "backup", say("escribe", "writes"), "flow", "h"),
            # D-426: the panel downloads the DuckDB database from the release and reads it read-only
            (
                "panel",
                "served",
                say(
                    "la lee desde el release\n«base-actual», solo lectura",
                    "reads it from the release\n«base-actual», read-only",
                ),
                "flow",
                "h",
            ),
            ("user", "panel", "", "flow", "v"),
            ("professional", "panel", "", "flow", "v"),
            ("author", "panel", "", "order", "v"),
            ("github", "load", say("ejecuta cada martes", "runs every Tuesday"), "order", "hv"),
            # D-426: the load uploads the DuckDB database to the release; the panel acts on GitHub with its two tokens
            (
                "load",
                "github",
                say(
                    "sube la\nBase DuckDB\nal release\n«base-actual»",
                    "uploads the\nDuckDB database\nto the release\n«base-actual»",
                ),
                "flow",
                "hv",
                "left",
            ),
            (
                "panel",
                "github",
                say(
                    "lanza y cancela cargas (GITHUB_TOKEN)\nlee estado de workflows (GITHUB_READ_TOKEN)",
                    "launches and cancels loads (GITHUB_TOKEN)\nreads workflow state (GITHUB_READ_TOKEN)",
                ),
                "order",
                "vh",
            ),
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
                say("la Base DuckDB, en un archivo nuevo", "the DuckDB database, in a new file"),
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
                say(
                    "elige su vista: Usuario, Profesional o Autor (con clave)",
                    "chooses a view: User, Professional or Author (with a code)",
                ),
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
            (
                "control",
                "github",
                say("API: lanzar, leer estado y logs, cancelar", "API: start, read state and logs, cancel"),
                "order",
                "h",
            ),
            ("github", "served", say("descarga", "download"), "flow", "v"),
        ],
        size=42,
        limit=24,
    )


def scenario_css(palette):
    """D-425: the scenarios map, laid out as a grid so each actor sits on the row of the panel section it reaches. D-429:
    the Base DuckDB and GitHub Actions sit under the panel, so the panel takes the whole width and the map keeps the
    size of the other diagrams."""
    ink, text, muted, card, border = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
    )
    return f"""<style>
.sc {{ display:grid; grid-template-columns:84px 44px minmax(0, 1fr); column-gap:0; row-gap:6px; }}
.sc-frame {{ grid-column:3; grid-row:1 / 6; border:1.5px solid {border}; border-radius:16px; }}
.sc-head {{ grid-column:3; grid-row:1; display:flex; gap:9px; align-items:center; padding:7px 12px 0; }}
.sc-head b, .sc-head span {{ display:inline !important; }}
.sc-head span::before {{ content:" · "; }}
.sc-head svg {{ width:24px; height:24px; flex:none; }}
.sc-head b, .sc-db b, .sc-gh-title b {{ display:block; color:{ink}; font-size:13.5px; line-height:1.25; }}
.sc-head span, .sc-db span, .sc-gh-title span {{ display:block; font-size:11.5px; color:{text}; line-height:1.3; }}
.sc-sec {{ grid-column:3; margin:0 10px; padding:6px 9px 7px; border-radius:10px;
  border:1.3px solid color-mix(in srgb, var(--c) 55%, transparent); background:color-mix(in srgb, var(--c) 6%, transparent); }}
.sc-sec:last-of-type {{ margin-bottom:10px; }}
.sc-sec.all {{ border-style:dashed; border-color:{border}; background:transparent; }}
.sc-sec h4 {{ margin:0 0 4px; font-size:10.5px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--c); }}
.sc-sec.all h4 {{ color:{muted}; display:inline; margin-right:6px; }}
.sc-sec.all p {{ display:inline; }}
.sc-sec p {{ margin:0; font-size:11.5px; line-height:1.35; color:{text}; }}
.sc-grid {{ display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:4px; }}
.sc-grid.flow {{ display:flex; flex-wrap:wrap; }}
.sc-grid.flow > .sc-tile {{ flex:1 1 auto; }}
.sc-tile {{ padding:3px 7px 4px; border-radius:7px; font-size:11.5px; line-height:1.35; color:{text}; background:color-mix(in srgb, {card} 80%, transparent);
  border:1px solid color-mix(in srgb, {border} 60%, transparent); min-width:0; }}
.sc-tile b {{ color:{ink}; font-size:12px; font-weight:600; }}
.sc-tile > span {{ font-size:11.5px; color:{text}; }}
.sc-tile b .ref {{ color:{muted}; font-size:11px; font-weight:400; white-space:nowrap; }}
.sc-warn {{ margin-top:4px !important; color:var(--c) !important; }}
.sc-actor {{ grid-column:1; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; gap:2px; }}
.sc-actor svg {{ width:32px; height:32px; }}
.sc-actor b {{ color:{ink}; font-size:13px; line-height:1.2; }}
.sc-actor span {{ font-size:11px; line-height:1.25; color:{text}; }}
.sc-up {{ font-size:10.5px; line-height:1.3; color:{muted}; border:1px solid {border}; border-radius:999px; padding:0 7px; margin-bottom:4px; }}
.sc-arrow {{ align-self:center; position:relative; height:2px; background:var(--c); margin:0 10px 0 4px; }}
.sc-arrow.back {{ background:transparent; border-top:2px dashed var(--c); height:0; }}
.sc-arrow::after {{ content:""; position:absolute; top:-6px; border:6px solid transparent; }}
.sc-arrow.right::after {{ right:-8px; border-left:9px solid var(--c); border-right:0; }}
.sc-arrow.left::after {{ left:-8px; border-right:9px solid var(--c); border-left:0; }}
.sc-arrow.back::after {{ top:-8px; }}
.sc-arrow em {{ position:absolute; bottom:5px; left:-4px; right:-4px; text-align:center; font-style:normal; font-size:10.5px;
  color:var(--c); line-height:1.25; }}
.sc-arrow em.under {{ bottom:auto; top:7px; }}
.sc-conn {{ grid-column:3; grid-row:6; display:grid; grid-template-columns:200px 56px minmax(0, 1fr); height:40px; margin-top:-6px; }}
.sc-ups {{ position:relative; }}
.sc-ups > .sc-v {{ position:absolute; top:0; bottom:0; left:50%; }}
.sc-ups > .sc-v + .sc-v {{ left:54%; }}
.sc-ups > .sc-v:first-child:not(:last-child) {{ left:16%; }}
.sc-v {{ position:relative; width:0; border-left:2px solid var(--c); }}
.sc-v.back {{ border-left-style:dashed; }}
.sc-v::after {{ content:""; position:absolute; left:-7px; border:6px solid transparent; }}
.sc-v.up::after {{ top:-6px; border-bottom:9px solid var(--c); border-top:0; }}
.sc-v.down::after {{ bottom:-6px; border-top:9px solid var(--c); border-bottom:0; }}
.sc-v em {{ position:absolute; left:8px; top:50%; transform:translateY(-50%); width:max-content; max-width:180px; font-style:normal;
  font-size:10.5px; line-height:1.25; color:var(--c); }}
.sc-v em small {{ display:block; font-size:10px; }}
.sc-gh-title b, .sc-gh-title span {{ display:inline !important; }}
.sc-gh-title span::before {{ content:" · "; }}
.sc-bottom {{ grid-column:3; grid-row:7; display:grid; grid-template-columns:200px 56px minmax(0, 1fr); align-items:stretch; }}
.sc-db {{ display:flex; gap:8px; padding:7px 10px; border-radius:12px; align-self:start;
  border:1.5px solid var(--c); background:color-mix(in srgb, var(--c) 8%, transparent); }}
.sc-db svg, .sc-gh-title svg {{ width:22px; height:22px; flex:none; }}
.sc-gh {{ display:flex; flex-direction:column; gap:4px; padding:6px 8px 7px; border-radius:12px; border:1.5px dashed var(--c); }}
.sc-gh .sc-grid {{ grid-template-columns:1fr; gap:3px; }}
.sc-gh-title {{ display:flex; gap:8px; align-items:center; }}
.sc-pub {{ align-self:start; margin-top:14px; position:relative; height:0; border-top:2px solid var(--c); }}
.sc-pub::after {{ content:""; position:absolute; top:-7px; left:-6px; border:6px solid transparent; border-right:9px solid var(--c); border-left:0; }}
.sc-pub em {{ position:absolute; bottom:4px; left:0; right:0; text-align:center; font-style:normal; font-size:10.5px; color:var(--c); }}
.sc-legend {{ grid-column:1 / 3; grid-row:6 / 8; align-self:end; display:flex; flex-direction:column; gap:1px; font-size:11px; line-height:1.35; color:{text}; }}
.sc-legend i {{ display:inline-block; width:9px; height:9px; border-radius:50%; background:var(--c); margin-right:5px; }}
</style>"""


def sad_scenarios(mode):
    """D-425: who uses GreenOcean and what each one reaches, inside the panel and around it. Each profile inherits the
    one above it; the Base DuckDB and GitHub Actions sit outside the panel. Every name is the official one (the menu,
    the files, the secrets) with its PRD reference when it has one."""
    palette = charts.get_palette(mode)
    green, blue, amber, violet, sky = (
        doc_views.PERSON_DISCS["visitor"][1],
        doc_views.PERSON_DISCS["professional"][1],
        doc_views.PERSON_DISCS["author"][1],
        "#8b5cf6",
        palette["accent"],
    )

    def icon(name, color):
        return f'<svg viewBox="0 0 24 24">{mark(f"icon:{name}@{color}", 12, 12, 24, color)}</svg>'

    def person(name):
        return doc_views.flat_logo("person", name).replace('class="logo" ', "", 1)

    def tile(name, detail="", ref=""):
        reference = f' <span class="ref">{esc(ref)}</span>' if ref else ""
        body = f" <span>· {esc(detail)}</span>" if detail else ""
        return f'<div class="sc-tile"><b>{esc(name)}{reference}</b>{body}</div>'

    def section(row, actor, color, heading, tiles, extra="", layout=""):
        return (
            f'<section class="sc-sec" data-actor="{actor}" style="grid-row:{row};--c:{color}"><h4>{esc(heading)}</h4>'
            f'<div class="sc-grid {layout}">{"".join(tiles)}</div>{extra}</section>'
        )

    def arrow(row, color, label, direction="right", column=2):
        return (
            f'<div class="sc-arrow {direction}" style="grid-row:{row};grid-column:{column};--c:{color}">'
            f"<em>{esc(label)}</em></div>"
        )

    actors = [
        (3, "visitor", say("Usuario", "User"), say("Lee el negocio", "Reads the business"), "", ""),
        (
            4,
            "professional",
            say("Profesional", "Professional"),
            say("Lee el proyecto completo", "Reads the whole project"),
            "",
            say("↑ hereda todo · sin clave", "↑ inherits all · no key"),
        ),
        (
            5,
            "author",
            say("Autor", "Author"),
            say("Opera el sistema", "Operates the system"),
            "",
            say("↑ hereda todo · con clave", "↑ inherits all · with the key"),
        ),
    ]
    parts = ['<div class="sc-frame"></div>']
    parts.append(
        f'<div class="sc-head">{icon("chart", sky)}<div><b>{say("Panel web", "Web panel")} · Streamlit</b>'
        f"<span>{esc(say('Lee la Base DuckDB en solo lectura. Solo la entrada como Autor pide clave y se comprueba en el servidor; Usuario → Profesional es solo un filtro del menú.', 'Reads the DuckDB database read-only. Only the entry as the Author asks for a key and is checked on the server; User → Professional is only a menu filter.'))}</span></div></div>"
    )
    parts.append(
        f'<section class="sc-sec all" data-actor="todos" style="grid-row:2;--c:{sky}"><h4>'
        f'{esc(say("Lo que tienen todos", "What everyone has"))}</h4><p>'
        + esc(
            say(
                "«Elige tu vista» (RF-09) · «Vista: … · Cambiar» · menú lateral · «Volver» · Apariencia (4 temas) · "
                "ES/EN · Fuentes (ODEPA, INE) · enlace a GitHub · «← Anterior» y «Siguiente →»",
                "«Choose your view» (RF-09) · «View: … · Change» · side menu · «Back» · Appearance (4 themes) · "
                "ES/EN · Sources (ODEPA, INE) · link to GitHub · «← Previous» and «Next →»",
            )
        )
        + "</p></section>"
    )
    parts.append(
        section(
            3,
            "usuario",
            green,
            say("Usuario · Negocio · BA y BI · sin cuenta", "User · Business · BA and BI · no account"),
            [
                tile(
                    say("Semanal", "Weekly"),
                    say(
                        "región, canal, familia y alertas de precio", "region, channel, family and price alerts"
                    ),  # D-494
                    "P-1 · RF-05",
                ),
                # D-456: one page, in tabs, gathers the history and the former four pages of the section.
                tile(
                    say("Análisis BA y BI", "BA and BI analysis"),
                    say(
                        "Mensual · Histórico · Precios e inflación · Insights · Interesados · Método",
                        "Monthly · Historical · Prices and inflation · Insights · Stakeholders · Method",
                    ),
                    "P-4 · RF-04",
                ),
            ],
            f'<p class="sc-warn">{esc(say("Sin puerta a otra vista: «Vista: Usuario · Cambiar» reabre «Elige tu vista»", "No door to another view: «Vista: Usuario · Cambiar» reopens «Elige tu vista»"))}</p>',
            layout="flow",
        )
    )
    parts.append(
        section(
            4,
            "profesional",
            blue,
            say(
                "Profesional · el proyecto completo · sin cuenta · el rol solo ordena el menú",
                "Professional · the whole project · no account · the role only orders the menu",
            ),
            [
                tile(
                    say("Ingeniería de datos", "Data engineering"),
                    say(
                        "Pipeline y linaje · Modelo de datos · Consultas SQL sobre la Base DuckDB, solo lectura",
                        "Pipeline and lineage · Data model · SQL queries on the DuckDB database, read-only",
                    ),
                    "P-2 · P-3 · RF-06",
                ),
                tile(
                    say("Stack y evidencia", "Stack and evidence"),
                    say(
                        "«Flujo del sistema en vivo» · Mapa de la app · Arquitectura de seguridad, sin valores secretos",
                        "«Live system flow» · App map · Security architecture, no secret values",
                    ),
                ),
                tile(
                    say("Calidad", "Quality"),
                    say(
                        "Calidad y auditoría · Método y calidad (ISO 25012, ISO 25010) · Git workflow e incidentes",
                        "Quality and audit · Method and quality (ISO 25012, ISO 25010) · Git workflow and incidents",
                    ),
                    "P-5",
                ),
                tile(
                    say("Documentos", "Documents"),
                    say(
                        "PRD · SAD · ADR · Índice de decisiones · SQAP · Plan de pruebas · MANUAL · Glosario, cada uno con su PDF",
                        "PRD · SAD · ADR · Decision index · SQAP · Test plan · MANUAL · Glossary, each with its PDF",
                    ),
                ),
            ],
        )
    )
    parts.append(
        section(
            5,
            "autor",
            amber,
            say(
                "Autor · DevOps y seguridad · con clave, control en el servidor",
                "Author · DevOps and security · with the key, checked on the server",
            ),
            [
                tile(
                    say("Entrada", "Entry"),
                    say(
                        "la clave del Autor (secreto CONTROL_CODE) en «Elige tu vista» · espera tras 3 fallos · sesión de 30 min · sin ser Autor, estas páginas dicen «No tienes acceso»",
                        "the Author's key (CONTROL_CODE secret) in «Choose your view» · wait after 3 failures · 30 min session · without being the Author, these pages say «No access»",
                    ),
                    "RF-09",
                ),
                tile(
                    say("Centro de operación", "Operations center"),
                    say(
                        "«Ejecutar pipeline ahora» lanza semanal.yml · «Cancelar» con «¿Seguro?» · «Recargar datos» · «Cerrar acceso» · aviso de tokens a 15 días",
                        "«Run pipeline now» launches semanal.yml · «Cancel» with a confirmation · «Reload data» · «Close access» · token notice at 15 days",
                    ),
                    "RF-07",
                ),
                tile(
                    "GitHub Actions",
                    say(
                        "estado de cada workflow y sus logs, leídos con GITHUB_READ_TOKEN",
                        "state of each workflow and its logs, read with GITHUB_READ_TOKEN",
                    ),
                ),
                tile(
                    say("Configuración", "Settings"),
                    say(
                        "GITHUB_TOKEN y GITHUB_READ_TOKEN · última carga · último informe de calidad · pruebas · fuentes · mantenimiento",
                        "GITHUB_TOKEN and GITHUB_READ_TOKEN · last load · last quality report · tests · sources · maintenance",
                    ),
                ),
            ],
            f'<p class="sc-warn">{esc(say("Avisos solo para el Autor: «La carga del … falló» · «Acción requerida» (no conformidades e incidentes externos) · carga en curso", "Notices for the Author only: «The load of … failed» · «Action required» (nonconformities and external incidents) · load in progress"))}</p>'
            f'<p class="sc-warn">{esc(say("Fuera del panel: revisa el informe de calidad, que se fusiona solo si el código está en su aceptable, y cambia el código y los secretos", "Outside the panel: approves the pull request of the quality report and changes the code and the secrets"))}</p>',
        )
    )
    for row, name, label, caption, note, inherits in actors:
        parts.append(
            f'<div class="sc-actor" style="grid-row:{row}">'
            + (f'<span class="sc-up">{esc(inherits)}</span>' if inherits else "")
            + f"{person(name)}<b>{esc(label)}</b><span>{esc(caption)}</span>"
            + (f"<small>{esc(note)}</small>" if note else "")
            + "</div>"
        )
    parts += [
        arrow(3, green, say("ve", "sees")),
        arrow(4, blue, say("además ve", "also sees")),
        arrow(5, amber, say("además opera", "also operates")),
        f'<div class="sc-conn"><div class="sc-ups"><div class="sc-v up" style="--c:{sky}"><em>'
        f'{esc(say("lee", "reads"))}</em></div></div><span></span><div class="sc-ups">'
        f'<div class="sc-v down" style="--c:{amber}"><em>{esc(say("lanza y cancela", "launches and cancels"))}'
        f'<small>GITHUB_TOKEN · {esc(say("Autor", "Author"))}</small></em></div>'
        f'<div class="sc-v up back" style="--c:{violet}"><em>{esc(say("estado y logs", "state and logs"))}'
        f'<small>GITHUB_READ_TOKEN · {esc(say("logs, solo el Autor", "logs, the Author only"))}</small></em></div></div></div>',
    ]
    parts.append(
        f'<div class="sc-bottom"><div class="sc-db" style="--c:{sky}">{icon("database", sky)}<div><b>{say("Base DuckDB", "DuckDB database")}</b><span>'
        + esc(
            say(
                "datos.duckdb en el release «base-actual» · puntero datos.version en main",
                "datos.duckdb in the «base-actual» release · datos.version pointer on main",
            )
        )
        + "</span></div></div>"
        + f'<div class="sc-pub" style="--c:{violet}"><em>{esc(say("publica", "publishes"))}</em></div>'
    )
    parts.append(
        f'<div class="sc-gh" style="--c:{violet}">'
        f'<div class="sc-gh-title">{icon("calendar", violet)}<div><b>GitHub Actions</b>'
        f'<span>{esc(say("Automatización. No es un perfil.", "Automation. Not a profile."))}</span></div></div>'
        + '<div class="sc-grid">'
        + tile(
            "semanal.yml",
            say(
                "martes 12:07 UTC y desde «Centro de operación»: ODEPA e INE → dbt → pruebas; si todo pasa, publica la Base DuckDB y abre el «Informe semanal»",
                "Tuesdays 12:07 UTC and from «Operations center»: ODEPA and INE → dbt → tests; if everything passes, publishes the DuckDB database and opens the «Weekly report»",
            ),
            "RF-01 · RF-02 · RF-03 · RF-08",
        )
        + tile(
            "calidad.yml",
            say(
                "mide en cada push; tras una carga en verde propone el informe de calidad (pull request) y lo fusiona si el código está en su aceptable",
                "measures on every push; after a green load it proposes the quality report (pull request) and merges it if the code is in range",
            ),
        )
        + tile(
            "pruebas.yml",
            say(
                "en cada push: ruff, mypy, pytest y dbt parse; no toca la Base DuckDB",
                "on every push: ruff, mypy, pytest and dbt parse; does not touch the DuckDB database",
            ),
        )
        + "</div></div></div>"
    )
    legend = "".join(
        f'<span style="--c:{color}"><i></i>{esc(name)}</span>'
        for color, name in (
            (green, say("Usuario", "User")),
            (blue, say("Profesional", "Professional")),
            (amber, say("Autor", "Author")),
            (violet, "GitHub Actions"),
        )
    )
    parts.append(
        f'<div class="sc-legend">{legend}<span>{esc(say("P = pregunta", "P = question"))}</span>'
        f'<span>{esc(say("RF = requisito del PRD", "RF = PRD requirement"))}</span></div>'
    )
    title = say(
        "Escenarios clave: quién usa GreenOcean y a qué llega cada perfil",
        "Key scenarios: who uses GreenOcean and what each profile reaches",
    )
    body = f'<p class="fig-title">{esc(title)}</p>{scenario_css(palette)}<div class="sc">{"".join(parts)}</div>'
    return page(mode, body, title)


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
            ("actions", "semanal.yml", "brand:github"),
            ("agent", say("Agente", "Agent"), "brand:python"),
            ("sources", "ODEPA · INE", "source:odepa"),
            ("etl", "SQLite · Parquet", "brand:sqlite"),
            ("dbt", "dbt · DuckDB", "brand:dbt"),
            ("tests", "pytest", "brand:pytest"),
            ("release", say("Release y main", "Release and main"), "brand:git"),
        ],
        [
            ("actions", "agent", say("martes 12:07 UTC: inicia", "Tuesday 12:07 UTC: starts"), "order"),
            ("agent", "sources", say("descarga los CSV de ODEPA", "downloads the ODEPA CSV files"), "flow"),
            ("sources", "agent", say("archivos + huella SHA-256", "files + SHA-256 fingerprint"), "back"),
            ("agent", "etl", say("filas crudas → raw.db y bronce", "raw rows → raw.db and bronze"), "flow"),
            ("etl", "dbt", say("dbt build sobre el bronce", "dbt build on bronze"), "flow"),
            # D-445: the CPI is downloaded by etl/ine.py inside etl/pipeline.py, not by the agent
            ("dbt", "sources", say("etl/ine.py descarga el IPC del INE", "etl/ine.py downloads the INE's CPI"), "flow"),
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
            ("visitor", say("Lector", "Reader"), "person:visitor"),
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
            ("panel", "visitor", say("«Elige tu vista»", "«Choose your view»"), "back"),
            ("visitor", "panel", say("elige su vista", "chooses a view"), "flow"),
            ("panel", "duckdb", say("consulta en solo lectura", "queries read-only"), "flow"),
            ("duckdb", "panel", say("filas", "rows"), "back"),
            ("panel", "visitor", say("la página con sus cifras", "the page with its figures"), "back"),
        ],
        say(
            "La vista elegida (Usuario, Profesional o Autor, este con clave) decide qué páginas ve el lector. "
            "Si GitHub no responde, el panel sigue con la base que ya tiene.",
            "The chosen view (User, Professional or Author, the last with a code) decides which pages the reader sees. "
            "If GitHub does not respond, the panel goes on with the database it already has.",
        ),
    )


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
            (
                "01-11-2026" if not i18n.is_english() else "2026-11-01",
                say("Aceptable calibrado", "Calibrated acceptable"),
                ["ADR-36"],
            ),
        ],
    )


def adr_before_after(mode):
    return graph(
        mode,
        say("ADR-35: la Base DuckDB, antes y después", "ADR-35: the DuckDB database, before and after"),
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
        served_size_note(),
        limit=26,
    )


def served_size_note():
    """D-386: the «before» figures are history, measured when ADR-35 was decided; the size of today is measured now."""
    history = say(
        "Las cifras de «antes» se midieron el 24-10-2026, al decidir ADR-35.",
        "The «before» figures were measured on 2026-10-24, when ADR-35 was decided.",
    )
    if not queries.DATABASE_FILE.exists():
        return history
    megabytes = queries.DATABASE_FILE.stat().st_size / 1_000_000
    return (
        history
        + " "
        + say(
            f"Hoy la Base DuckDB pesa {megabytes:.1f} MB.".replace(".", ",", 1),
            f"Today the DuckDB database weighs {megabytes:.1f} MB.",
        )
    )


# endregion


# region Test plan (with security)
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
                say("lee GITHUB_TOKEN, que nunca se muestra", "reads GITHUB_TOKEN, which is never shown"),
                "flow",
            ),
            ("panel", "api", say("API REST: lanza la carga", "REST API: starts the load"), "order"),
            ("api", "workflow", say("inicia la carga", "starts the load"), "order"),
            (
                "workflow",
                "panel",
                say("API REST: estado y logs de cada paso", "REST API: state and logs of each step"),
                "back",
            ),
            ("panel", "author", say("progreso en el Centro de operación", "progress in the Operations center"), "back"),
        ],
        say(
            "Con la misma API, el Autor puede cancelar la carga. semanal.yml solo puede escribir contenido y crear issues: permisos mínimos.",
            "With the same API, the Author can cancel the load. semanal.yml can only write content and create issues: least privilege.",
        ),
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

    text = i18n.document_path("INDICE_DECISIONES.md").read_text(encoding="utf-8")
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
                    "el modelo estrella en la Base DuckDB, etl/datos.duckdb",
                    "the star schema in the DuckDB database, etl/datos.duckdb",
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
            "visitor": (860, 0, "person:visitor", say("Usuario", "User"), say("ve el negocio", "sees the business")),
            "professional": (
                860,
                110,
                "person:professional",
                say("Profesional", "Professional"),
                say("ve todo el proyecto", "sees the whole project"),
            ),
            "author": (
                860,
                220,
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
            ("streamlit", "professional", "", "flow", "h"),
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


def weekly_cycle(mode):
    """D-377: the weekly cycle as the business page tells it: load, tests, publication, the two reports and what gets
    fixed before the next Tuesday."""
    return graph(
        mode,
        say("Del dato al informe, cada semana", "From the data to the report, every week"),
        {
            "load": (
                90,
                30,
                "icon:calendar",
                say("Carga", "Load"),
                say("cada martes · semanal.yml", "every Tuesday · semanal.yml"),
            ),
            "tests": (
                300,
                30,
                "icon:check",
                say("Pruebas", "Tests"),
                say("dbt y las pruebas de datos", "dbt and the data tests"),
            ),
            "publish": (
                510,
                30,
                "icon:database",
                say("Publicación", "Publication"),
                say("la base nueva, solo si todo pasó", "the new database, only if all passed"),
            ),
            "report": (
                720,
                30,
                "icon:mail",
                say("Informe semanal", "Weekly report"),
                say("estado y alertas de la semana", "status and alerts of the week"),
            ),
            "quality": (
                720,
                200,
                "icon:files",
                say("Informe de calidad", "Quality report"),
                say(
                    "numerado · se fusiona si el código está en su aceptable",
                    "numbered · merged if the code is in range",
                ),
            ),
            "fix": (
                90,
                200,
                "icon:tool",
                say("Correcciones", "Fixes"),
                say("registro de fallas y decisiones", "failure register and decisions"),
            ),
        },
        [
            ("load", "tests", "", "flow", "h"),
            ("tests", "publish", say("si pasan", "if they pass"), "flow", "h"),
            ("publish", "report", "", "flow", "h"),
            ("report", "quality", "", "flow", "v"),
            ("quality", "fix", say("lo que hay que corregir", "what must be fixed"), "flow", "h"),
            ("fix", "load", say("la semana siguiente", "the next week"), "back", "v"),
        ],
    )


# endregion

FIGURES = {
    "ciclo_semanal": weekly_cycle,  # D-377: also the «Proceso» block of «Análisis de negocio y sistemas»
    "contexto": sad_context,
    "contenedores": sad_containers,
    "sop": tests_procedure,
    "componentes_carga": sad_components_load,
    "componentes_panel": sad_components_panel,
    "escenarios": sad_scenarios,
    "requisitos": prd_requirements,
    "secuencia_carga": sad_weekly_sequence,
    "secuencia_panel": sad_panel_sequence,
    "mapa_adr": adr_map,
    "tiempo_adr": adr_timeline,
    "antes_despues": adr_before_after,
    "secuencia_manual": tests_manual_sequence,
    "arbol_fallas": manual_fault_tree,
    "secuencia_recuperacion": manual_recovery_sequence,
    "temas": index_themes,
    "mapa_temas": index_map,
    "adr_decisiones": index_adr,
    "terminos_capas": glossary_layers,
    "terminos_actores": glossary_actors,
    "terminos_cifra": glossary_figure,
    "calidades": quality_qualities,
    "estados_calidad": quality_states,
}
