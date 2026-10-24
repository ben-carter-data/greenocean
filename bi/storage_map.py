"""«Dónde viven los datos» (D-236): the storage architecture of the project, in one drawing.

Five zones, left to right: the external sources, the work zone (outside Git), the served
database (in Git), the repository and the published panel. Each store is a card with its
engine's cylinder or its folder, its file and its size; the 12 served tables hang inside the
DuckDB card in their three groups. Every line is a straight horizontal or vertical segment
with a head, labelled by what it does (copies, publishes, commits, deploys); the dashed
double-headed line is a check, not a flow. Hovering a card says what it stores, why, and
which file or workflow of the repository produces it.

It is the storage view, not the pipeline: the steps in order are in «Pipeline y linaje», and
the checks where two databases touch are in «Cruces entre bases». Nothing here reads data:
bi/dashboard.py hands over the row counts and file sizes. The page is a full HTML document for
st.iframe (CSS only, no script) whose SVG scales to the height the page gives it.
"""
import html

from bi import brand_icons, charts, database_map

WIDTH, HEIGHT = 1000, 620
CARD_HEIGHT = 88
ROWS = (146, 282, 418)
ZONE_TOP, ZONE_BOTTOM = 52, 484
SMALL = 12.5  # the smallest text, in drawing units: 11 px once the drawing is scaled to a 900 px window

# Card x ranges per column: (left, right). The lines between them are 64 units long.
SOURCES_X, WORK_X, SERVED_X, REPO_X = (28, 178), (242, 488), (552, 752), (816, 976)
ZONES = [
    ("sources", "Fuentes externas", "fuera del proyecto", (14, 192), "outside"),
    ("work", "Zona de trabajo", "fuera de Git · se rehace cada carga", (228, 502), "plain"),
    ("served", "Base servida", "el resultado de cada carga", (538, 766), "accent"),
    ("repo", "GitHub", "release y repositorio · público", (802, 990), "plain"),
]
# Stores: (key, kind, row, x range, mark, name, file).
STORES = [
    ("odepa", "source", 0, SOURCES_X, "odepa", "ODEPA", "CSV por año"),
    ("ine", "source", 1, SOURCES_X, "ine", "INE · IPC", "mensual"),
    ("raw", "cylinder", 0, WORK_X, "sqlite", "SQLite", "etl/raw.db"),
    ("bronze", "folder", 1, WORK_X, "apacheparquet", "Parquet", "capa bronce"),
    ("dbt", "cylinder", 2, WORK_X, "duckdb", "dbt + DuckDB", "warehouse_build.duckdb"),
    ("backup", "cylinder", 0, SERVED_X, "sqlite", "SQLite · respaldo", "etl/datos.db"),
]
# What each card says on hover, written once here: (what, why, produced by).
TIPS = {
    "odepa": ("Los precios que ODEPA publica cada semana, por región y canal: consumidor y mayorista (solo frutas "
              "y hortalizas), en archivos CSV por año.",
              "Es la fuente oficial. El agente los descarga y anota su huella SHA-256 en manifest.json.",
              "agent/agent.py"),
    "ine": ("El índice de precios de alimentos, un valor por mes.",
            "Pasa los precios a pesos reales. No pasa por SQLite: son CSV pequeños que se escriben directo en "
            "Parquet; si el INE no responde, se rehace desde ine_ipc_source.",
            "etl/ine.py"),
    "raw": (database_map.NODES[3][5], database_map.NODES[3][6], "etl/etl.py"),
    "bronze": (database_map.NODES[4][5], database_map.NODES[4][6], "etl/bronze.py"),
    "dbt": (database_map.NODES[5][5], database_map.NODES[5][6], "etl/pipeline.py"),
    "backup": (database_map.NODES[8][5], database_map.NODES[8][6], "etl/etl.py"),
    "served": (database_map.NODES[6][5], database_map.NODES[6][6], "etl/pipeline.py"),
    "github": ("Lo que la carga publica: la base servida, en el release «base-actual», con una sola copia que cada "
               "carga reemplaza; en la rama main, su puntero y el registro de las descargas (D-270).",
               database_map.NODES[7][6], ".github/workflows/semanal.yml"),
    "streamlit": ("El panel público, en Streamlit Community Cloud. Lee etl/datos.duckdb en solo lectura; no escribe "
                  "ninguna base.", "Se despliega solo desde la rama main: un cambio publicado en GitHub llega al "
                  "panel sin servidores que mantener.", "bi/dashboard.py"),
}
# What GitHub keeps, drawn as chips: (key, text, file path for the hover). The served file goes to the release
# (D-270): git keeps its pointer and the download record; the SQLite backup stays on the machine of each load.
REPO_FILES = [("repo_pointer", "etl/datos.version", "etl/datos.version"),
              ("repo_manifest", "manifest.json", "agent/downloads/manifest.json"),
              ("repo_served", "datos.duckdb", "bi/served_database.py")]
# Straight lines: (key, start, end, label, side of the label, dashed). Start and end are drawn so
# that each is a single horizontal or vertical segment.
LINES = [
    ("a_odepa", (SOURCES_X[1], ROWS[0]), (WORK_X[0], ROWS[0]), "descarga", "above", False),
    ("a_ine", (SOURCES_X[1], ROWS[1]), (WORK_X[0], ROWS[1]), "directo", "above", False),
    ("a_parquet", ((WORK_X[0] + WORK_X[1]) // 2, ROWS[0] + CARD_HEIGHT // 2),
     ((WORK_X[0] + WORK_X[1]) // 2, ROWS[1] - CARD_HEIGHT // 2), "copia a Parquet", "right", False),
    ("a_dbt", ((WORK_X[0] + WORK_X[1]) // 2, ROWS[1] + CARD_HEIGHT // 2),
     ((WORK_X[0] + WORK_X[1]) // 2, ROWS[2] - CARD_HEIGHT // 2), "dbt lee", "right", False),
    ("a_backup", (WORK_X[1], ROWS[0]), (SERVED_X[0], ROWS[0]), "ETL", "above", False),
    ("a_publish", (WORK_X[1], ROWS[2]), (SERVED_X[0], ROWS[2]), "publica", "above", False),
    ("a_release_served", (SERVED_X[1], ROWS[2]), (REPO_X[0], ROWS[2]), "release", "above", False),
]
SERVED_CARD = (312, 470)  # the DuckDB card is taller: it holds the twelve tables
PARITY_X = (SERVED_X[0] + SERVED_X[1]) // 2
PARITY = ((PARITY_X, ROWS[0] + CARD_HEIGHT // 2), (PARITY_X, SERVED_CARD[0]))
REPO_X_MID = (REPO_X[0] + REPO_X[1]) // 2
STREAMLIT_CARD = (REPO_X, (524, 604))
DEPLOY = ((REPO_X_MID, ZONE_BOTTOM), (REPO_X_MID, STREAMLIT_CARD[1][0]))
# Brand discs the other views use, plus Streamlit.
TIP_KEYS = [store[0] for store in STORES] + ["served", "streamlit"] + [key for key, *_ in REPO_FILES]
STREAMLIT_DISC = ("#ff8f98", "#e0303f", "#ffffff")


def esc(value):
    return html.escape(str(value))


def disc(slug, x, y, size, suffix):
    """A brand on a lit disc (the same marks as the other diagrams), placed at x, y."""
    if slug == "streamlit":
        top, bottom, glyph = STREAMLIT_DISC
        gradient = f"disc-streamlit{suffix}"
        return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 72 72" aria-hidden="true"><defs>'
                f'<radialGradient id="{gradient}" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="{top}"/>'
                f'<stop offset="1" stop-color="{bottom}"/></radialGradient></defs>'
                f'<circle cx="36" cy="36" r="31" fill="url(#{gradient})"/><ellipse cx="29" cy="19" rx="16" ry="8" '
                f'fill="#fff" opacity=".3"/><g fill="{glyph}" transform="translate(17 17) scale(1.58)">'
                f'{brand_icons.logo_body("streamlit")}</g></svg>')
    mark = database_map.brand_logo(slug, suffix)
    return mark.replace('<svg class="logo" ', f'<svg x="{x}" y="{y}" width="{size}" height="{size}" ', 1)


def source_mark(key, x, y, size):
    mark = database_map.source_logo(key)
    return mark.replace('<svg class="logo" ', f'<svg x="{x}" y="{y}" width="{size}" height="{size}" ', 1)


def cylinder(x, y, width, height, slug, key, mark=True, glyph_size=24):
    """The engine's database: a cylinder in the brand's colors with its mark in the middle."""
    top, bottom, glyph = database_map.BRANDS[slug]
    ry = 9
    gradient = f"cyl-{key}"
    mid = x + width / 2
    return (f'<defs><linearGradient id="{gradient}" x1="0" x2="1"><stop offset="0" stop-color="{bottom}"/>'
            f'<stop offset=".4" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>'
            f'<path d="M{x} {y + ry} V{y + height - ry} A{width / 2} {ry} 0 0 0 {x + width} {y + height - ry} '
            f'V{y + ry}" fill="url(#{gradient})"/>'
            f'<ellipse cx="{mid}" cy="{y + ry}" rx="{width / 2}" ry="{ry}" fill="{top}" stroke="{bottom}" stroke-width="1"/>'
            f'<path d="M{x} {y + ry + 14} A{width / 2} {ry} 0 0 0 {x + width} {y + ry + 14}" fill="none" '
            f'stroke="{glyph}" stroke-opacity=".22"/>'
            + (brand_icons.logo(slug, mid - glyph_size / 2, y + height / 2 - 2, glyph, glyph_size) if mark else ""))


def mini_mark(kind, slug, key):
    """A store's mark at the size of a table row: the same cylinder, folder or source logo of the map."""
    if kind == "source":
        body = source_mark(slug, 0, 3, 32)
    elif slug == "apacheparquet":
        body = folder(1, 3, 30, 30, slug)
    elif slug == "python":
        body = disc("python", 0, 2, 32, f"-{key}")
    else:
        body = cylinder(3, 2, 26, 32, slug, key, glyph_size=14)
    return f'<svg class="mark" width="32" height="36" viewBox="0 0 32 36" aria-hidden="true">{body}</svg>'


def folder(x, y, width, height, slug):
    """Parquet is files, not a database: three sheets in a stack with the format's mark."""
    top, bottom, glyph = database_map.BRANDS[slug]
    sheets = "".join(f'<rect x="{x + shift}" y="{y + 6 - shift}" width="{width - 12}" height="{height - 8}" rx="6" '
                     f'fill="{bottom}" opacity="{opacity}"/>' for shift, opacity in ((12, .35), (6, .6)))
    return (sheets + f'<rect x="{x}" y="{y + 6}" width="{width - 12}" height="{height - 8}" rx="6" fill="{top}" '
            f'stroke="{bottom}"/>' + brand_icons.logo(slug, x + (width - 12) / 2 - 12, y + height / 2 - 6, glyph, 24))


def card_box(x_range, row_y, height=CARD_HEIGHT):
    left, right = x_range
    return (left, row_y - height // 2, right - left, height)


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    shadow = "rgba(0,0,0,.5)" if dark else "rgba(15,39,71,.18)"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; height:100%; background:transparent; color:{text};
  font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
svg.map {{ display:block; width:100%; height:100vh; overflow:visible; }}
.zone {{ fill:{'rgba(255,255,255,.025)' if dark else 'rgba(15,39,71,.03)'}; stroke:{border}; stroke-width:1; }}
.zone.outside {{ stroke-dasharray:5 5; }}
.zone.accent {{ stroke:{accent}; stroke-opacity:.55; fill:color-mix(in srgb, {accent} 5%, transparent); }}
.zone-title {{ font-size:{SMALL}px; font-weight:600; letter-spacing:.1em; text-transform:uppercase; fill:{ink}; }}
.zone-sub {{ font-size:{SMALL}px; fill:{muted}; }}
.card {{ fill:{card}; stroke:{border}; stroke-width:1; filter:drop-shadow(0 8px 10px {shadow}); }}
.node {{ outline:none; cursor:default; }}
.node:hover .card, .node:focus .card {{ stroke:{accent}; }}
.name {{ font-size:15px; font-weight:600; fill:{ink}; }}
.file {{ font:400 {SMALL}px ui-monospace, SFMono-Regular, Menlo, monospace; fill:{muted}; }}
.size {{ font-size:{SMALL}px; font-weight:600; fill:{ink}; }}
.size-bg {{ fill:color-mix(in srgb, {accent} 14%, transparent); }}
.row-label {{ font-size:{SMALL}px; fill:{text}; }}
.row-count {{ font:600 {SMALL}px ui-monospace, SFMono-Regular, Menlo, monospace; fill:{ink}; }}
.divider {{ stroke:{border}; stroke-width:1; }}
.chip {{ fill:{card}; stroke:{border}; stroke-width:1; }}
.line {{ fill:none; stroke:{accent}; stroke-width:2; stroke-linecap:round; }}
.line.check {{ stroke-dasharray:5 5; }}
.line-label {{ font-size:{SMALL}px; fill:{ink}; text-anchor:middle; paint-order:stroke; stroke:{palette['background']}; stroke-width:5px; }}
.line-label.right {{ text-anchor:start; }}
.legend-text {{ font-size:{SMALL}px; fill:{muted}; }}
.tip {{ opacity:0; pointer-events:none; transition:opacity .15s ease; }}
.tip div {{ position:absolute; width:270px; padding:12px 14px; border-radius:14px; background:{card}; border:1px solid {border};
  box-shadow:0 18px 40px rgba(0,0,0,{'.55' if dark else '.2'}); color:{text}; font-size:12.5px; line-height:1.45; }}
.tip b {{ display:block; margin:8px 0 2px; font-size:11px; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip b:first-child {{ margin-top:0; }}
.tip code {{ font:400 12px ui-monospace, SFMono-Regular, Menlo, monospace; color:{ink}; }}
{"".join(f"svg:has(#n-{key}:hover, #n-{key}:focus) #t-{key} {{ opacity:1; }}" for key in TIP_KEYS)}
</style>"""


def build_tip(key, box, above, what, why, produced_by, tables=None):
    """The hover card: below the box, above it, or (for the long one, the twelve tables) to its left."""
    left, top, width, height = box
    if above == "left":
        x, y, anchor = max(left - 278, 8), top + height, "bottom:0"
    else:
        x = min(max(left + width / 2 - 135, 8), WIDTH - 278)
        y = top - 8 if above else top + height + 8
        anchor = "bottom:0" if above else "top:0"
    rows = ""
    if tables:
        rows = ("<b>Tablas</b>" + "".join(f"<code>{esc(name)}</code> {thousands(count)}<br>" for name, count in tables))
    return (f'<g class="tip" id="t-{key}"><foreignObject x="{x:.0f}" y="{y:.0f}" width="270" height="1" overflow="visible">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" style="{anchor}"><b>Qué guarda</b>{esc(what)}'
            f'<b>Por qué</b>{esc(why)}{rows}<b>Fuente</b><code>{esc(produced_by)}</code></div></foreignObject></g>')


def thousands(value):
    return database_map.thousands(value)


def build_store(key, kind, row, x_range, slug, name, file, size):
    """One store as a card: its mark on the left, its name, file and size on the right."""
    left, top, width, height = card_box(x_range, ROWS[row])
    parts = [f'<rect class="card" x="{left}" y="{top}" width="{width}" height="{height}" rx="14"/>']
    mark_x, mark_y = left + 14, top + height / 2
    if kind == "source":
        parts.append(source_mark(slug, left + 10, top + 24, 40))
        text_x = left + 58
    elif kind == "cylinder":
        parts.append(cylinder(mark_x, mark_y - 32, 44, 64, slug, key))
        text_x = left + 70
    else:
        parts.append(folder(mark_x, mark_y - 30, 52, 56, slug))
        text_x = left + 78
    parts.append(f'<text class="name" x="{text_x}" y="{top + 38}">{esc(name)}</text>'
                 f'<text class="file" x="{text_x}" y="{top + 58}">{esc(file)}</text>')
    if size:
        pill = len(size) * 7.4 + 16
        parts.append(f'<rect class="size-bg" x="{text_x}" y="{top + 65}" width="{pill:.0f}" height="18" rx="9"/>'
                     f'<text class="size" x="{text_x + 8}" y="{top + 78}">{esc(size)}</text>')
    return "".join(parts)


def build_served_card(counts, sizes):
    """The DuckDB file with its twelve tables in the three groups of who writes them."""
    left, right = SERVED_X
    top, bottom = SERVED_CARD
    parts = [f'<rect class="card" x="{left}" y="{top}" width="{right - left}" height="{bottom - top}" rx="14"/>',
             cylinder(left + 14, top + 12, 44, 64, "duckdb", "served"),
             f'<text class="name" x="{left + 70}" y="{top + 38}">DuckDB</text>'
             f'<text class="file" x="{left + 70}" y="{top + 58}">etl/datos.duckdb</text>']
    size = sizes.get("served", "")
    if size:
        pill = len(size) * 7.4 + 16
        parts.append(f'<rect class="size-bg" x="{left + 70}" y="{top + 65}" width="{pill:.0f}" height="18" rx="9"/>'
                     f'<text class="size" x="{left + 78}" y="{top + 78}">{esc(size)}</text>')
    parts.append(f'<line class="divider" x1="{left + 14}" x2="{right - 14}" y1="{top + 92}" y2="{top + 92}"/>')
    y = top + 112
    for _, label, _, names, *_ in database_map.ORIGINS:
        parts.append(f'<text class="row-label" x="{left + 16}" y="{y}">{esc(label)}</text>'
                     f'<text class="row-count" x="{right - 16}" y="{y}" text-anchor="end">{len(names)}</text>')
        y += 20
    return "".join(parts)


def build_line(key, start, end, label, side, dashed, both=False):
    (x1, y1), (x2, y2) = start, end
    assert x1 == x2 or y1 == y2, f"{key}: every line is horizontal or vertical"
    marks = ' marker-start="url(#head)" marker-end="url(#head)"' if both else ' marker-end="url(#head)"'
    path = f'<path class="line{" check" if dashed else ""}" d="M{x1} {y1} L{x2} {y2}"{marks}/>'
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    if side == "above":
        text = f'<text class="line-label" x="{mid_x}" y="{mid_y - 8}">{esc(label)}</text>'
    elif side == "right":
        text = f'<text class="line-label right" x="{mid_x + 10}" y="{mid_y + 4}">{esc(label)}</text>'
    else:
        text = f'<text class="line-label" x="{mid_x}" y="{mid_y + 4}">{esc(label)}</text>'
    return path + text


def build_zone(key, title, sub, x_range, style):
    left, right = x_range
    return (f'<rect class="zone {style}" x="{left}" y="{ZONE_TOP}" width="{right - left}" '
            f'height="{ZONE_BOTTOM - ZONE_TOP}" rx="18"/>'
            f'<text class="zone-title" x="{left + 16}" y="{ZONE_TOP + 24}">{esc(title)}</text>'
            f'<text class="zone-sub" x="{left + 16}" y="{ZONE_TOP + 41}">{esc(sub)}</text>')


def build_legend():
    y = 556
    return (f'<g transform="translate(12 {y})">'
            f'{cylinder(0, 0, 20, 28, "sqlite", "legend", mark=False)}<text class="legend-text" x="30" y="19">Base de datos</text>'
            f'{folder(150, 0, 30, 28, "apacheparquet")}<text class="legend-text" x="190" y="19">Archivos</text>'
            f'<path class="line" d="M290 14 L324 14" marker-end="url(#head)"/>'
            f'<text class="legend-text" x="334" y="19">escribe o copia</text>'
            f'<path class="line check" d="M450 14 L484 14" marker-start="url(#head)" marker-end="url(#head)"/>'
            f'<text class="legend-text" x="494" y="19">comprobación</text></g>'
            f'<text class="legend-text" x="12" y="606">Pasa el cursor por cada caja: qué guarda, por qué y qué archivo la produce.</text>')


def build_map_html(palette, counts, layers, tests, sizes=None):
    """The whole drawing as one HTML document. counts: {table: rows} of the served file;
    layers and tests: dbt's models per layer and its tests; sizes: {store key: "14 MB"}."""
    sizes = sizes or {}
    models = sum(layers.values())
    notes = {"dbt": f"Una base de trabajo con {models} modelos en tres capas (staging {layers.get('staging', 0)}, "
                    f"intermedio {layers.get('intermediate', 0)} y marts {layers.get('marts', 0)}) y {tests} pruebas "
                    "de datos de dbt.",
             "served": "La base que el panel lee: 12 tablas, agrupadas por quién las escribe."}
    nodes, tips = [], []
    for key, kind, row, x_range, slug, name, file in STORES:
        box = card_box(x_range, ROWS[row])
        nodes.append(f'<g class="node" id="n-{key}" tabindex="0">{build_store(key, kind, row, x_range, slug, name, file, sizes.get(key, ""))}</g>')
        what, why, produced_by = TIPS[key]
        tips.append(build_tip(key, box, row == 2, notes.get(key, what), why, produced_by))
    served_box = (SERVED_X[0], SERVED_CARD[0], SERVED_X[1] - SERVED_X[0], SERVED_CARD[1] - SERVED_CARD[0])
    nodes.append(f'<g class="node" id="n-served" tabindex="0">{build_served_card(counts, sizes)}</g>')
    what, why, produced_by = TIPS["served"]
    tables = [(name, counts.get(name)) for *_, names, _, _ in database_map.ORIGINS for name in names]
    tips.append(build_tip("served", served_box, "left", notes["served"], why, produced_by, tables))
    # GitHub: a title, then what it keeps as chips, the release at the height of the line that reaches it.
    left, right = REPO_X
    repo = []
    for (key, text, path), row in zip(REPO_FILES, range(3)):
        y = ROWS[row]
        repo.append(f'<g class="node" id="n-{key}" tabindex="0"><rect class="chip" x="{left}" y="{y - 22}" width="{right - left}" '
                    f'height="44" rx="12"/><text class="file" x="{left + 14}" y="{y + 5}">{esc(text)}</text></g>')
        tips.append(build_tip(key, (left, y - 22, right - left, 44), row == 2, TIPS["github"][0], TIPS["github"][1], path))
    streamlit_box = (REPO_X[0], STREAMLIT_CARD[1][0], REPO_X[1] - REPO_X[0], STREAMLIT_CARD[1][1] - STREAMLIT_CARD[1][0])
    sl, st_, sw, sh = streamlit_box
    streamlit = (f'<g class="node" id="n-streamlit" tabindex="0"><rect class="card" x="{sl}" y="{st_}" width="{sw}" '
                 f'height="{sh}" rx="14"/>{disc("streamlit", sl + 10, st_ + 18, 44, "-app")}'
                 f'<text class="name" x="{sl + 62}" y="{st_ + 36}">Streamlit</text>'
                 f'<text class="file" x="{sl + 62}" y="{st_ + 56}">solo lectura</text></g>')
    tips.append(build_tip("streamlit", streamlit_box, True, TIPS["streamlit"][0], TIPS["streamlit"][1], TIPS["streamlit"][2]))
    zones = "".join(build_zone(*zone) for zone in ZONES)
    lines = "".join(build_line(*line) for line in LINES)
    lines += build_line("parity", PARITY[0], PARITY[1], "paridad", "center", True, both=True)
    lines += build_line("deploy", DEPLOY[0], DEPLOY[1], "despliega", "right", False)
    head = (f'<defs><marker id="head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>')
    badge = disc("github", REPO_X[1] - 36, ZONE_TOP + 10, 24, "-repo")
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">' + build_css(palette)
            + f'</head><body><svg class="map" viewBox="0 0 {WIDTH} {HEIGHT}" preserveAspectRatio="xMidYMid meet" '
              f'role="img" aria-label="Dónde viven los datos">{head}{zones}{badge}{lines}{"".join(nodes)}'
              f'{"".join(repo)}{streamlit}{build_legend()}{"".join(tips)}</svg></body></html>')
