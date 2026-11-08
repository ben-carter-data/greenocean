"""«Mapa de la app» as a BPMN diagram (D-562): the whole system in one view, on one horizontal sheet.

Above, the external participants as collapsed pools (black boxes: ODEPA, INE, GitHub, PyPI and Streamlit Community
Cloud). In the middle, the pool «Carga semanal» with four lanes (ingestion, transformation, quality control and
publication): a timer start event every Tuesday, the collapsed subprocesses with their logos, the data stores, the
exclusive gateway of the publication gate and its two end events. Below, the pool «Integración continua», started by
a message (a push), the readers as collapsed pools and a BPMN group with what watches and supports the system. The
grey sequence flow joins the steps and dotted associations join them to their stores. A legend names every symbol.
The sheet is a fixed mid grey in every theme, so the diagram reads as a document. Pure functions: no Streamlit.
"""

import base64
import html

from bi import brand_icons, charts, database_map, doc_views, i18n, static_files

# region Constants
WIDTH, HEIGHT = 1440, 778
INK, MUTED, LINE, CARD = "#1f2328", "#454c56", "#98a0ab", "#f5f6f8"
GREEN, RED, AMBER, SHEET = "#1a7f37", "#cf222e", "#8a5a00", "#c3c9d1"
LANE_SHADES = ["#d3d8de", "#c9cfd6"]
TASK_W, TASK_H = 118, 76
# The logo of each piece (the same as «Stack y evidencia»): a brand, a source, a person or a thin line icon.
LOGOS = {
    "odepa": "source:odepa",
    "odepa_consumer": "source:odepa",
    "ine": "source:ine",
    "agent": "brand:python",
    "sqlite": "brand:sqlite",
    "parquet": "brand:apacheparquet",
    "dbt": "brand:dbt",
    "duckdb": "brand:duckdb",
    "gates": "icon:gate",
    "release": "icon:tag",
    "streamlit": "brand:streamlit",
    "visitor": "person:visitor",
    "professional": "person:professional",
    "author": "person:author",
    "github": "brand:github",
    "pypi": "icon:box",
    "stcloud": "icon:cloud",
    "pruebas": "icon:workflow",
    "ci": "brand:pytest",
    "calidad": "icon:workflow",
}
# Thin line icons for the pieces that are not a brand, drawn in the accent of the light theme (24-unit grid).
LINE_ICONS = {
    "workflow": '<circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><rect x="14.5" y="9.5" width="6" '
    'height="5" rx="1.2"/><path d="M6 8.5v7"/><path d="M8.5 6h2.5a2.5 2.5 0 0 1 2.5 2.5V12h1"/>',
    "tag": '<path d="M3.5 12.5V4.5a1 1 0 0 1 1-1h8l8.5 8.5-9 9z"/><circle cx="8" cy="8" r="1.6"/>',
    "gate": '<path d="M4 21V5"/><path d="M20 21V5"/><path d="M4 9h16"/><path d="M4 14h16"/><path d="m8 9 4 5m0-5 4 5"/>',
    "shield": '<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "code": '<path d="m8 8-4 4 4 4"/><path d="m16 8 4 4-4 4"/><path d="m13.5 5-3 14"/>',
    "chart": '<path d="M4 20V4"/><path d="M4 20h16"/><path d="m7 15 4-5 3 3 5-7"/>',
    "parity": '<path d="M4 8h13"/><path d="m14 5 3 3-3 3"/><path d="M20 16H7"/><path d="m10 13-3 3 3 3"/>',
    "pulse": '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
    "files": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/>',
    "ruler": '<rect x="3" y="8" width="18" height="8" rx="1.5"/><path d="M7 8v3M11 8v4M15 8v3M19 8v4"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9"/><path d="m16 7 3 3"/><path d="m14 9 2 2"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4"/><path d="m6.5 6.5 2.5 2.5M15 15l2.5 2.5M17.5 6.5 15 9M9 15l-2.5 2.5"/>',
    "box": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4 7.5 8 4.5 8-4.5"/><path d="M12 12v9"/>',
    "cloud": '<path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.2 9.5 4.3 4.3 0 0 0 7 18z"/>',
    "console": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3"/><path d="M12 15h5"/>',
}
# The light theme's logos: they keep their colour on the grey sheet in every theme.
LOGO_THEME = charts.MODE_LIGHT
# The participants outside the process: (id, node keys of its logos, label, x, y, width, height).
BLACK_BOXES = [
    ("odepa", ("odepa", "odepa_consumer"), "ODEPA · precios", 80, 14, 250, 40),
    ("ine", ("ine",), "INE · IPC de alimentos", 340, 14, 200, 40),
    ("github", ("github",), "GitHub · repositorio y Actions", 550, 14, 240, 40),
    ("pypi", ("pypi",), "PyPI · paquetes", 800, 14, 150, 40),
    ("stcloud", ("stcloud",), "Streamlit Community Cloud · alojamiento", 960, 14, 300, 40),
    ("visitor", ("visitor",), "Usuario", 80, 660, 170, 34),
    ("professional", ("professional",), "Profesional", 260, 660, 170, 34),
    ("author", ("author",), "Autor · administrador", 440, 660, 190, 34),
]
# The weekly load: its pool, its lanes (top, height, name) and the pool of the continuous integration.
LOAD_POOL = (40, 70, 1360, 440, "Carga semanal")
LOAD_LANES = [
    (70, 110, "Ingesta"),
    (180, 110, "Transformación"),
    (290, 110, "Control de calidad"),
    (400, 110, "Publicación"),
]
CI_POOL = (40, 520, 1360, 126, "Integración continua")
# Collapsed subprocesses: (node key, x, y, label); a «+» says each groups several steps.
TASKS = [
    ("agent", 260, 125, "Ingesta de ODEPA\ne INE"),
    ("dbt", 590, 235, "Transformación\ndbt Core"),
    ("gates", 820, 345, "Puerta de\npublicación"),
    ("release", 1060, 455, "Publicar release\n«base-actual»"),
    ("streamlit", 1210, 455, "Actualizar\nPanel web"),
    ("pruebas", 290, 575, "Pruebas en grupos\npruebas.yml"),
    ("ci", 450, 575, "Pruebas\npytest"),
    ("calidad", 610, 575, "Medición de calidad\ncalidad.yml"),
]
# Data stores: (node key, x, y, label, where the label goes); Parquet keeps its label at its right, clear of the
# association that goes down to dbt.
STORES = [
    ("sqlite", 430, 125, "SQLite · raw.db", "below"),
    ("parquet", 590, 125, "Parquet · bronce", "right"),
    ("duckdb", 730, 235, "DuckDB · datos.duckdb", "below"),
]
# Events: (id, x, y, kind, marker, label).
EVENTS = [
    ("start", 130, 125, "start", "timer", "Temporizador\nmartes 12:07 UTC"),
    ("stop", 1060, 345, "error", "error", "Fin de error\nnada se publica"),
    ("end", 1330, 455, "end", "", "Fin\npanel actualizado"),
    ("pstart", 130, 575, "start", "message", "Mensaje\npush a GitHub"),
    ("pend", 760, 575, "end", "", "Fin\nCI en verde"),
]
GATEWAY = ("gw", 950, 345, "¿Pruebas y filas\ncompletas?")
# The sequence flow, always drawn: (from, to, label).
FLOW = [
    ("start", "agent", ""),
    ("agent", "dbt", ""),
    ("dbt", "gates", ""),
    ("gates", "gw", ""),
    ("gw", "stop", "no"),
    ("gw", "release", "sí"),
    ("release", "streamlit", ""),
    ("streamlit", "end", ""),
    ("pstart", "pruebas", ""),
    ("pruebas", "ci", ""),
    ("ci", "calidad", ""),
    ("calidad", "pend", ""),
]
# Data associations between the subprocesses and their stores (dotted).
ASSOCIATIONS = [("agent", "sqlite"), ("sqlite", "parquet"), ("parquet", "dbt"), ("dbt", "duckdb")]
# A text annotation, joined to the error end by a dotted association: (x of its bracket, y of the end, text).
ANNOTATION = (
    1132,
    345,
    "Anotación: la puerta bloquea si falla una prueba\nde dbt, si falta una semana o si llegan\nmenos del 90 % de las filas",
)
# A BPMN group: the pieces that watch and support the system, outside the flow of the data.
GROUP = (650, 656, 750, 60, "Grupo · vigilancia y soporte")
GROUP_PIECES = [
    ("semanal", "icon:workflow", "semanal.yml"),
    ("secrets", "icon:key", "Secretos del panel"),
    ("devops", "icon:console", "DevOps y seguridad"),
    ("web", "icon:code", "HTML · CSS · JavaScript"),
    ("charts", "icon:chart", "Altair · Vega-Lite"),
    ("parity", "icon:parity", "Respaldo y paridad"),
    ("security", "icon:shield", "Seguridad"),
    ("monitoring", "icon:pulse", "Observabilidad"),
    ("docs", "icon:files", "Documentos"),
    ("measurement", "icon:ruler", "Medición de pantallas"),
    ("ai", "icon:spark", "Apoyo con IA"),
]
# The marker that gives the page's frame the height the window leaves (as «Modelo de datos» does, D-236).
FIT = static_files.read("app_bpmn_fit.html")
LEGEND = [
    ("box", "Pool contraído: participante externo, caja negra"),
    ("task", "Subproceso contraído: agrupa varios pasos"),
    ("store", "Almacén de datos"),
    ("start", "Evento de inicio (temporizador o mensaje)"),
    ("gateway", "Compuerta exclusiva"),
    ("end", "Evento de fin (en rojo, fin de error)"),
    ("sequence", "Flujo de secuencia"),
    ("association", "Asociación: lee o escribe un almacén"),
]
# endregion


# region Text and logos
def say(text):
    """A text of the sheet in the reader's language (D-284): the whole label, or else each of its lines."""
    return i18n.translate_text(text)


def text(x, y, value, size=11, color=INK, anchor="middle", weight=400):
    """An SVG text in the reader's language, one line per «\\n»."""
    lines = say(value).split("\n")
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if index == 0 else size + 2}">{html.escape(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{spans}</text>'


def logo_data(spec, palette):
    """A logo as a data address, in its own colour."""
    kind, name = spec.split(":")
    if kind == "brand":
        color = (
            palette["strong_text"]
            if name in ("github", "git")
            else doc_views.DISCS.get(name, ("", palette["accent"]))[1]
        )
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{color}">{brand_icons.logo_body(name)}</svg>'
    elif kind == "source":
        svg = database_map.source_logo(name).replace(
            '<svg class="logo" ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1
        )
    elif kind == "person":
        color = doc_views.PERSON_DISCS[name][1]
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" fill="{color}">'
            '<circle cx="18" cy="12" r="6"/><path d="M6 31c1-8 6-12 12-12s11 4 12 12z"/></svg>'
        )
    else:
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{palette["accent"]}" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{LINE_ICONS[name]}</svg>'
        )
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"


def logo(spec, x, y, size):
    """A logo (the same as «Stack y evidencia»), centred on (x, y)."""
    href = logo_data(spec, charts.get_palette(LOGO_THEME))
    return f'<image href="{href}" x="{x - size / 2}" y="{y - size / 2}" width="{size}" height="{size}"/>'


# endregion


# region The BPMN symbols
def draw_pool(x, y, width, height, title, lanes=()):
    """A pool: its name on a vertical strip at the left, then its lanes, each in its own grey."""
    parts = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{LANE_SHADES[0]}" stroke="{LINE}"/>',
        f'<line x1="{x + 26}" y1="{y}" x2="{x + 26}" y2="{y + height}" stroke="{LINE}"/>',
        f'<text transform="translate({x + 17} {y + height / 2}) rotate(-90)" fill="{INK}" font-size="10.5" '
        f'text-anchor="middle" font-weight="600">{html.escape(say(title))}</text>',
    ]
    for index, (top, lane_height, name) in enumerate(lanes):
        parts.append(
            f'<rect x="{x + 26}" y="{top}" width="{width - 26}" height="{lane_height}" fill="{LANE_SHADES[index % 2]}"/>'
            f'<line x1="{x + 26}" y1="{top}" x2="{x + width}" y2="{top}" stroke="{LINE}"/>'
            f'<line x1="{x + 52}" y1="{top}" x2="{x + 52}" y2="{top + lane_height}" stroke="{LINE}"/>'
            f'<text transform="translate({x + 43} {top + lane_height / 2}) rotate(-90)" fill="{MUTED}" '
            f'font-size="9.5" text-anchor="middle">{html.escape(say(name))}</text>'
        )
    return "".join(parts)


def draw_black_box(box_id, keys, label, x, y, width, height):
    """A collapsed pool: an external participant, a black box."""
    logos = "".join(logo(LOGOS[key], x + 22 + index * 30, y + height / 2, 22) for index, key in enumerate(keys))
    return (
        f'<g class="bp-piece" id="bp-{box_id}">'
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" fill="{CARD}" stroke="{MUTED}"/>'
        + logos
        + text(x + 22 + len(keys) * 30, y + height / 2 + 4, label, 11.5, INK, "start")
        + "</g>"
    )


def draw_task(key, x, y, label):
    """A collapsed subprocess: a rounded task with its logo, its name and the «+» that says it groups several steps."""
    left, top = x - TASK_W / 2, y - TASK_H / 2
    return (
        f'<g class="bp-piece" id="bp-{key}">'
        f'<rect x="{left}" y="{top}" width="{TASK_W}" height="{TASK_H}" rx="10" fill="{CARD}" stroke="{INK}" stroke-width="1.3"/>'
        + logo(LOGOS[key], x, y - 16, 26)
        + text(x, y + 9, label, 10.5)
        + f'<rect x="{x - 6}" y="{top + TASK_H - 12}" width="12" height="12" fill="none" stroke="{MUTED}"/>'
        + text(x, top + TASK_H - 2.5, "+", 11, MUTED)
        + "</g>"
    )


def draw_store(key, x, y, label, side):
    """A data store, the BPMN cylinder, with the logo of its technology and its name below it or at its right."""
    name = text(x, y + 34, label, 10, MUTED) if side == "below" else text(x + 30, y + 4, label, 10, MUTED, "start")
    return (
        f'<g class="bp-piece" id="bp-{key}">'
        f'<path d="M{x - 22} {y - 18} v32 a22 7 0 0 0 44 0 v-32" fill="{CARD}" stroke="{MUTED}"/>'
        f'<ellipse cx="{x}" cy="{y - 18}" rx="22" ry="7" fill="{CARD}" stroke="{MUTED}"/>'
        + logo(LOGOS[key], x, y + 2, 20)
        + name
        + "</g>"
    )


def event_marker(x, y, marker, color):
    """What starts or ends an event, drawn inside its ring: a clock, an envelope or a lightning bolt."""
    if marker == "timer":
        return (
            f'<circle cx="{x}" cy="{y}" r="9" fill="none" stroke="{color}"/>'
            f'<path d="M{x} {y - 6} V{y} L{x + 4} {y + 3}" stroke="{color}" fill="none"/>'
        )
    if marker == "message":
        return (
            f'<rect x="{x - 8}" y="{y - 5}" width="16" height="11" fill="none" stroke="{color}"/>'
            f'<path d="M{x - 8} {y - 5} L{x} {y + 1} L{x + 8} {y - 5}" fill="none" stroke="{color}"/>'
        )
    if marker == "error":
        return (
            f'<path d="M{x - 6} {y + 6} L{x - 2} {y - 6} L{x + 2} {y + 2} L{x + 6} {y - 6}" fill="none" '
            f'stroke="{color}" stroke-width="1.6"/>'
        )
    return ""


def draw_event(event_id, x, y, kind, marker, label):
    """A start event (thin ring), an end event (thick ring) or an end of error (red), with its trigger."""
    color = RED if kind == "error" else GREEN
    width = 1.6 if kind == "start" else 3.5
    return (
        f'<g class="bp-shape" id="bp-{event_id}"><circle cx="{x}" cy="{y}" r="14" fill="{CARD}" stroke="{color}" '
        f'stroke-width="{width}"/>' + event_marker(x, y, marker, color) + text(x, y + 30, label, 9.5, MUTED) + "</g>"
    )


def draw_gateway(gateway_id, x, y, label):
    """The exclusive gateway: a diamond with an «×», its question above."""
    return (
        f'<g class="bp-shape" id="bp-{gateway_id}">'
        f'<path d="M{x} {y - 20} L{x + 20} {y} L{x} {y + 20} L{x - 20} {y} Z" fill="{CARD}" stroke="{AMBER}" stroke-width="1.6"/>'
        f'<path d="M{x - 7} {y - 7} L{x + 7} {y + 7} M{x + 7} {y - 7} L{x - 7} {y + 7}" stroke="{AMBER}" stroke-width="2"/>'
        + text(x, y - 42, label, 9.5, MUTED)
        + "</g>"
    )


def draw_annotation(x, y, note):
    """A text annotation: an open bracket with its text, joined by a dotted association to the error end at its left."""
    return (
        f'<path d="M{x} {y - 27} h-8 v54 h8" fill="none" stroke="{MUTED}"/>'
        f'<path d="M{x - 8} {y} H{x - 56}" stroke="{MUTED}" stroke-dasharray="2 3"/>'
        + text(x + 8, y - 13, note, 9.5, MUTED, "start")
    )


def draw_group():
    """The BPMN group (dashed and dotted): what watches and supports the system, each piece with its logo."""
    x, y, width, height, title = GROUP
    step = (width - 20) / len(GROUP_PIECES)
    pieces = "".join(
        f'<g class="bp-piece" id="bp-{key}"><rect x="{x + 10 + index * step}" y="{y + 18}" '
        f'width="{step - 6}" height="{height - 24}" rx="6" fill="{CARD}" stroke="{LINE}"/>'
        + logo(spec, x + 10 + index * step + (step - 6) / 2, y + height / 2 + 6, 22)
        + f"<title>{html.escape(say(name))}</title></g>"
        for index, (key, spec, name) in enumerate(GROUP_PIECES)
    )
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="none" stroke="{MUTED}" '
        f'stroke-dasharray="8 3 2 3"/>' + text(x + 10, y + 12, title, 9.5, MUTED, "start") + pieces
    )


# endregion


# region The flow and the legend
def centers():
    """Where each piece of the flow sits: (x, y, width, height)."""
    found = {key: (x, y, TASK_W, TASK_H) for key, x, y, _ in TASKS}
    found.update({key: (x, y, 44, 50) for key, x, y, *_ in STORES})
    found.update({event_id: (x, y, 28, 28) for event_id, x, y, *_ in EVENTS})
    found[GATEWAY[0]] = (GATEWAY[1], GATEWAY[2], 40, 40)
    return found


def orthogonal(a, b, places):
    """The straight or right-angled path from one piece to the next: straight when they share a column or a row, else
    down and across."""
    ax, ay, aw, ah = places[a]
    bx, by, bw, bh = places[b]
    if abs(ax - bx) < 2:
        step = 1 if by > ay else -1
        return [(ax, ay + step * ah / 2), (bx, by - step * bh / 2)]
    if abs(ay - by) < 2:
        step = 1 if bx > ax else -1
        return [(ax + step * aw / 2, ay), (bx - step * bw / 2, by)]
    return [(ax, ay + (ah / 2 if by > ay else -ah / 2)), (ax, by), (bx - (bw / 2 if bx > ax else -bw / 2), by)]


def path_of(points):
    """The SVG path through some points."""
    return "M" + " L".join(f"{x:g} {y:g}" for x, y in points)


def draw_flow():
    """The grey sequence flow with its arrows and its «sí» and «no», and the dotted associations with the stores."""
    places, parts = centers(), []
    for source, target, label in FLOW:
        points = orthogonal(source, target, places)
        parts.append(
            f'<path d="{path_of(points)}" fill="none" stroke="{MUTED}" stroke-width="1.4" marker-end="url(#bp-arrow)"/>'
        )
        if label:
            x, y = points[1] if len(points) > 2 else ((points[0][0] + points[1][0]) / 2, points[0][1])
            parts.append(text(x + 6, y - 5, label, 10, MUTED, "start"))
    for source, target in ASSOCIATIONS:
        parts.append(
            f'<path d="{path_of(orthogonal(source, target, places))}" fill="none" stroke="{MUTED}" '
            'stroke-width="1.3" stroke-dasharray="2 3"/>'
        )
    return "".join(parts)


def legend_symbol(kind, x, y):
    """The small symbol of one entry of the legend."""
    return {
        "box": f'<rect x="{x}" y="{y - 5}" width="16" height="10" fill="none" stroke="{MUTED}"/>',
        "task": f'<rect x="{x}" y="{y - 7}" width="16" height="13" rx="3" fill="none" stroke="{INK}"/>',
        "store": f'<ellipse cx="{x + 8}" cy="{y - 5}" rx="7" ry="2.5" fill="none" stroke="{MUTED}"/>'
        f'<path d="M{x + 1} {y - 5} v9 a7 2.5 0 0 0 14 0 v-9" fill="none" stroke="{MUTED}"/>',
        "start": f'<circle cx="{x + 8}" cy="{y}" r="6" fill="none" stroke="{GREEN}"/>',
        "gateway": f'<path d="M{x + 8} {y - 7} l7 7 l-7 7 l-7 -7z" fill="none" stroke="{AMBER}"/>',
        "end": f'<circle cx="{x + 8}" cy="{y}" r="6" fill="none" stroke="{GREEN}" stroke-width="2.5"/>',
        "sequence": f'<path d="M{x} {y} h16" stroke="{MUTED}" marker-end="url(#bp-arrow)"/>',
        "association": f'<path d="M{x} {y} h16" stroke="{MUTED}" stroke-width="1.3" stroke-dasharray="2 3"/>',
    }[kind]


def draw_legend():
    """The legend in two rows below the sheet, each entry after the width of the one before."""
    parts, x, y = [], 40, 738
    for index, (kind, label) in enumerate(LEGEND):
        if index == 4:
            x, y = 40, 758
        parts.append(legend_symbol(kind, x, y) + text(x + 22, y + 4, label, 9.5, MUTED, "start"))
        x += 22 + len(say(label)) * 5.1 + 18
    return "".join(parts)


# endregion


# region The sheet
def build_svg():
    """The whole BPMN sheet as one SVG, scaled to the window by its viewBox so it always fits one view."""
    defs = (
        f'<defs><marker id="bp-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto"><path d="M0 0L10 5L0 10z" fill="{MUTED}"/></marker></defs>'
    )
    body = [
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="{SHEET}"/>',
        draw_pool(*LOAD_POOL, LOAD_LANES),
        draw_pool(*CI_POOL),
        draw_flow(),
        *(draw_black_box(*box) for box in BLACK_BOXES),
        *(draw_task(*task) for task in TASKS),
        *(draw_store(*store) for store in STORES),
        *(draw_event(*event) for event in EVENTS),
        draw_gateway(*GATEWAY),
        draw_annotation(*ANNOTATION),
        draw_group(),
        draw_legend(),
    ]
    return (
        f'<svg class="bp-sheet" viewBox="0 0 {WIDTH} {HEIGHT}" preserveAspectRatio="xMidYMid meet" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(say("Mapa de la app en BPMN"))}">'
        + defs
        + "".join(body)
        + "</svg>"
    )


# endregion


# region The page
def build_view():
    """The document of the page's frame: its stylesheet and the sheet. Streamlit cleans an SVG drawn in the page
    itself, so the sheet lives in its own frame, as the other diagrams do; `FIT` gives that frame the window's height."""
    return static_files.style("app_bpmn.css") + '<div class="bp">' + build_svg() + "</div>"


# endregion
