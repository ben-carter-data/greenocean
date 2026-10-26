"""Where two databases meet (D-197, D-237, D-239): the databases drawn one over the other, and the crossings between them.

Each database of the project is a layer with the tables that take part in a crossing: the CSV sources
at the top, then raw.db, the bronze Parquet, dbt's work database and the served datos.duckdb, with the SQLite
backup datos.db at the right. A straight line joins a table of one layer with the table it feeds or is
compared with in another, labelled with what they share (the file and its SHA-256, the source and year,
week_start, run_id, the three figures of the parity). The numbered mark on each crossing is coloured by
its live check; hovering it says how the crossing happens, what travels, what both sides share and the check.

The stores are drawn with the same cylinders, folders and marks as «Dónde viven los datos», which shows
where each one lives; this view shows how their tables meet."""
import html

from bi import charts, database_map, queries, storage_map

BACKUP_TABLES = ["dim_product", "dim_region", "dim_channel", "dim_date", "weekly_price", "rejection", "etl_run"]

RAW_NOTE = "no se puede comprobar aquí: raw.db no está en este servidor"

# (key, from (kind, mark), to (kind, mark), from label, to label, mechanism, short: what travels, short: shared key,
#  full: what travels, full: what both sides share, check key). The short texts are read in the row; the full ones, on hover.
CROSSINGS = [
    ("odepa_raw", ("source", "odepa"), ("db", "sqlite"), "ODEPA", "raw.db", "descarga con Python",
     "CSV públicos, sin cambiar un valor", "archivo + SHA-256",
     "Los CSV públicos, una fila de texto por observación, sin cambiar un valor.",
     "El nombre del archivo y su huella SHA-256, anotada en manifest.json.", "raw"),
    ("ine_bronze", ("source", "ine"), ("files", "apacheparquet"), "INE · IPC", "Bronce", "directo, sin pasar por SQLite",
     "IPC de alimentos, mensual", "el mes del índice",
     "El índice de precios de alimentos, mensual. Por diseño no toca raw.db: no es una fuente de precios de ODEPA.",
     "El mes del índice, que dbt cruza luego con las semanas.", "ine"),
    ("raw_bronze", ("db", "sqlite"), ("files", "apacheparquet"), "raw.db", "Bronce", "lectura de solo lectura",
     "todas las filas, a Parquet", "fuente y año",
     "Todas las filas crudas, un Parquet por fuente y año, con las columnas como texto.",
     "La fuente y el año del archivo: cada Parquet es una carpeta file_year=AAAA.", "raw"),
    ("bronze_work", ("files", "apacheparquet"), ("db", "duckdb"), "Bronce", "Base de trabajo", "dbt lee los Parquet",
     "filas con tipos, reglas y marcas", "la semana (week_start)",
     "Las filas del bronce, ya con tipos, reglas de calidad y marcas. Aquí se cruzan ODEPA y el INE.",
     "La semana (week_start): ipc_weekly lleva el IPC de cada mes a cada semana de precios.", "work"),
    ("work_served", ("db", "duckdb"), ("db", "duckdb"), "Base de trabajo", "datos.duckdb", "ATTACH de solo lectura y CREATE TABLE AS",
     "las 12 tablas servidas", "los mismos nombres de tabla",
     "Las nueve tablas del modelo, más la traza de dbt y el registro de cargas.",
     "Los mismos nombres de tabla; la base servida se reemplaza entera al final, nunca a medias.", "served"),
    ("raw_backup", ("db", "sqlite"), ("db", "sqlite"), "raw.db", "datos.db", "ETL en Python (etl/etl.py)",
     "las mismas filas, sin dbt", "las mismas reglas de negocio",
     "Las mismas filas crudas, validadas y llevadas a precio semanal por un camino independiente de dbt.",
     "Las mismas reglas de negocio: por eso su resultado debe dar las mismas cifras que la base servida.", "raw"),
    ("served_backup", ("db", "duckdb"), ("db", "sqlite"), "datos.duckdb", "datos.db", "comparación de tres cifras",
     "nada se copia: se comparan", "filas, rechazos y suma",
     "Nada se copia: solo se comparan las filas de weekly_price, las filas rechazadas y la suma de los precios.",
     "Las tablas del modelo estrella: el respaldo SQLite tiene siete de las doce.", "parity"),
    ("history", ("db", "duckdb"), ("python", "python"), "datos.duckdb", "Próxima carga", "etl_run arrastrado",
     "el historial de cargas", "el número de carga (run_id)",
     "El historial de cargas: la carga nueva lo lee de la base servida y le agrega su fila. En la primera vez lo leyó de datos.db.",
     "El número de carga (run_id), que también guarda cada fila de rejection.", "history"),
]
STATUS_WORDS = {"ok": "Comprobado ahora", "fail": "No coincide", "warn": "Revisar", "pending": "No medible aquí",
                "info": "Dato"}
STATUS_COLORS = {"ok": "#22b35a", "fail": "#d03b3b", "warn": "#d97706", "pending": "#d97706", "info": "#8a94a6"}


def read_checks(database_file=queries.DATABASE_FILE, backup_file=None):
    """{crossing key: (status, text)} of what can be measured in this server."""
    from bi import quality
    checks = {key: ("pending", RAW_NOTE) for key in ("raw",)}
    checks["ine"] = ("info", "El IPC se guarda también crudo, como ine_ipc_source.")
    with queries.open_database(database_file) as connection:
        tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
        weeks = connection.execute("SELECT count(*) FROM ipc_weekly").fetchone()[0] if "ipc_weekly" in tables else 0
        unmatched = connection.execute("SELECT count(DISTINCT week_start) FROM weekly_price WHERE week_start NOT IN "
                                         "(SELECT week_start FROM ipc_weekly)").fetchone()[0] if "ipc_weekly" in tables else 0
        runs, rejection_runs = connection.execute(
            "SELECT (SELECT count(*) FROM etl_run), (SELECT count(DISTINCT run_id) FROM rejection "
            "WHERE run_id NOT IN (SELECT run_id FROM etl_run))").fetchone()
    checks["work"] = ("ok" if unmatched == 0 else "warn",
                      f"{database_map.thousands(weeks)} semanas con índice; {unmatched} semanas de precios sin índice.")
    checks["served"] = ("ok", f"{len(tables)} tablas en la base servida, publicadas de una vez.")
    checks["history"] = ("ok" if rejection_runs == 0 else "fail",
                         f"{runs} cargas registradas; {rejection_runs} rechazos sin su carga.")
    parity = quality.check_parity(**({"backup_file": backup_file} if backup_file else {}), database_file=database_file)
    if parity is None:
        # D-270: the backup is never published; each load compares it before publishing.
        checks["parity"] = ("pending", "el respaldo no se publica: cada carga lo compara antes de publicar")
    else:
        text = (f"{database_map.thousands(parity['rows'][1])} filas y {database_map.thousands(parity['rejections'][1])} rechazos "
                f"en la base servida; {database_map.thousands(parity['rows'][0])} y "
                f"{database_map.thousands(parity['rejections'][0])} en el respaldo.")
        checks["parity"] = ("ok" if parity["ok"] else "fail", text)
    return checks


WIDTH, HEIGHT = 1000, 614
SMALL = storage_map.SMALL
# Columns of the tables: A is the IPC chain, B the consumer prices, C the wholesale prices.
COLUMNS = {"a": (190, 350), "b": (416, 576), "c": (592, 752)}
LAYER_X = (20, 764)
BACKUP_X = (804, 988)
CHIP_HEIGHT = 32


def center(column):
    left, right = COLUMNS[column]
    return (left + right) // 2


# The layers, from the sources down to the served database: (key, name, file, mark, top, height).
LAYERS = [
    ("raw", "raw.db", "SQLite", ("db", "sqlite"), 90, 64),
    ("bronze", "Bronce", "Parquet", ("files", "apacheparquet"), 190, 64),
    ("work", "Base de trabajo", "dbt + DuckDB", ("db", "duckdb"), 290, 112),
    ("served", "datos.duckdb", "la base servida", ("db", "duckdb"), 438, 144),
]
SOURCE_Y = 14
# Table chips: (layer key, row, column or span, name). The row is the chip's top, from the layer's top.
CHIPS = [
    ("raw", 16, "b", "raw_consumer"), ("raw", 16, "c", "raw_wholesale"),
    ("bronze", 16, "a", "ine_ipc"), ("bronze", 16, "b", "odepa_consumer"), ("bronze", 16, "c", "odepa_wholesale"),
    ("work", 16, "a", "stg_ine__ipc_monthly"), ("work", 16, "b", "stg_odepa__consumer"),
    ("work", 16, "c", "stg_odepa__wholesale"),
    ("work", 64, "a", "ipc_weekly"), ("work", 64, "bc", "weekly_price"),
    ("served", 16, "a", "ipc_weekly"), ("served", 16, "bc", "weekly_price"),
    ("served", 62, "a", "etl_run"), ("served", 62, "b", "rejection"),
]
SOURCES = [("a", "source", "ine", "INE · IPC"), ("b", "source", "odepa", "ODEPA consumidor"),
           ("c", "source", "odepa", "ODEPA mayorista")]
OTHER_TABLES = ["+ dim_date, dim_product, dim_region, dim_channel", "+ ine_ipc_source, ipc_monthly, dbt_node, dbt_result"]
BACKUP_CHIPS = ["etl_run", "rejection", "dim_channel", "dim_region", "dim_product", "dim_date"]


def layer_top(key):
    return next(layer[4] for layer in LAYERS if layer[0] == key)


def chip_box(layer, row, column):
    left = COLUMNS[column[0]][0]
    right = COLUMNS[column[-1]][1]
    return (left, layer_top(layer) + row, right - left, CHIP_HEIGHT)


# The crossings on the drawing: (crossing key, [(from, to)] lines, number badge place, label, label place, dashed).
# A line is ((x1, y1), (x2, y2)), straight and either horizontal or vertical. Built from the chips below.
def build_lines():
    src_bottom = SOURCE_Y + 36
    lines = {}
    column_x = {"a": center("a"), "b": center("b"), "c": center("c")}
    lines["odepa_raw"] = [((column_x[c], src_bottom), (column_x[c], layer_top("raw") + 16)) for c in "bc"]
    lines["ine_bronze"] = [((column_x["a"], src_bottom), (column_x["a"], layer_top("bronze") + 16))]
    lines["raw_bronze"] = [((column_x[c], layer_top("raw") + 16 + CHIP_HEIGHT), (column_x[c], layer_top("bronze") + 16))
                           for c in "bc"]
    lines["bronze_work"] = [((column_x[c], layer_top("bronze") + 16 + CHIP_HEIGHT), (column_x[c], layer_top("work") + 16))
                            for c in "abc"]
    work_mid = (COLUMNS["b"][0] + COLUMNS["c"][1]) // 2
    lines["work_served"] = [((work_mid, layer_top("work") + 64 + CHIP_HEIGHT), (work_mid, layer_top("served") + 16)),
                            ((column_x["a"], layer_top("work") + 64 + CHIP_HEIGHT), (column_x["a"], layer_top("served") + 16))]
    etl_y = layer_top("raw") + 16 + CHIP_HEIGHT // 2
    lines["raw_backup"] = [((COLUMNS["c"][1], etl_y), (BACKUP_X[0], etl_y))]
    parity_y = layer_top("served") + 16 + CHIP_HEIGHT // 2
    lines["served_backup"] = [((COLUMNS["c"][1], parity_y), (BACKUP_X[0] + 12, parity_y))]
    return lines


LINES = build_lines()
# What each crossing is called on its line, and where its number sits (on the first line).
LABELS = {"odepa_raw": "descarga", "ine_bronze": "directo, sin SQLite", "raw_bronze": "fuente y año",
          "bronze_work": "dbt lee", "work_served": "publica", "raw_backup": "ETL", "served_backup": "paridad"}
JOIN_Y = {"work": layer_top("work") + 64 + CHIP_HEIGHT // 2, "served": layer_top("served") + 16 + CHIP_HEIGHT // 2}


def esc(value):
    return html.escape(str(value))


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    shadow = "rgba(0,0,0,.45)" if dark else "rgba(15,39,71,.15)"
    rules = "".join(f".s-{key} {{ --c:{value}; }}" for key, value in STATUS_COLORS.items())
    tips = "".join(f"svg:has(#x-{row[0]}:hover, #x-{row[0]}:focus) #t-{row[0]} {{ opacity:1; }}" for row in CROSSINGS)
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; height:100%; background:transparent; color:{text};
  font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
{rules}
svg.map {{ display:block; width:100%; height:100vh; overflow:visible; }}
.layer {{ fill:{'rgba(255,255,255,.03)' if dark else 'rgba(15,39,71,.035)'}; stroke:{border}; stroke-width:1; }}
.layer.served {{ stroke:{accent}; stroke-opacity:.55; fill:color-mix(in srgb, {accent} 5%, transparent); }}
.layer-name {{ font-size:14.5px; font-weight:600; fill:{ink}; }}
.layer-file {{ font-size:{SMALL}px; fill:{muted}; }}
.chip {{ fill:{card}; stroke:{border}; stroke-width:1; filter:drop-shadow(0 4px 6px {shadow}); }}
.chip-text {{ font:400 12.5px ui-monospace, SFMono-Regular, Menlo, monospace; fill:{ink}; text-anchor:middle; }}
.source .chip {{ stroke-dasharray:4 4; }}
.source-text {{ font-size:12.5px; font-weight:500; fill:{ink}; }}
.note {{ font-size:{SMALL}px; fill:{muted}; }}
.zone-label {{ font-size:{SMALL}px; font-weight:600; letter-spacing:.1em; text-transform:uppercase; fill:{muted}; }}
.line {{ fill:none; stroke:{accent}; stroke-width:2; stroke-linecap:round; }}
.line.check {{ stroke-dasharray:5 5; }}
.line.join {{ stroke-width:1.6; stroke:{ink}; opacity:.7; }}
.line-label {{ font-size:{SMALL}px; fill:{ink}; paint-order:stroke; stroke:{palette['background']}; stroke-width:5px; }}
.line-label.mid {{ text-anchor:middle; }}
.badge circle {{ fill:var(--c); stroke:{palette['background']}; stroke-width:3; }}
.badge text {{ font-size:12px; font-weight:700; fill:#fff; text-anchor:middle; }}
.badge {{ cursor:default; outline:none; }}
.badge:hover circle, .badge:focus circle {{ stroke:{accent}; }}
.tip {{ opacity:0; pointer-events:none; transition:opacity .15s ease; }}
.tip div {{ position:absolute; width:290px; padding:12px 14px; border-radius:14px; background:{card}; border:1px solid {border};
  box-shadow:0 18px 40px rgba(0,0,0,{'.55' if dark else '.2'}); color:{text}; font-size:12.5px; line-height:1.45; }}
.tip b {{ display:block; margin:8px 0 2px; font-size:11px; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip b:first-child {{ margin-top:0; }}
.tip em {{ font-style:normal; font-weight:600; color:var(--c); }}
{tips}
</style>"""


def build_chip(layer, row, column, name):
    x, y, w, h = chip_box(layer, row, column)
    return (f'<rect class="chip" x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/>'
            f'<text class="chip-text" x="{x + w / 2}" y="{y + h / 2 + 4.5}">{esc(name)}</text>')


def build_layer(key, name, file, mark, top, height):
    kind, brand = mark
    box = (f'<rect class="layer {"served" if key == "served" else ""}" x="{LAYER_X[0]}" y="{top}" '
           f'width="{LAYER_X[1] - LAYER_X[0]}" height="{height}" rx="16"/>')
    icon = storage_map.mini_mark(kind, brand, f"x{key}")
    return (box + f'<g transform="translate({LAYER_X[0] + 14} {top + 12})">{icon}</g>'
            f'<text class="layer-name" x="{LAYER_X[0] + 54}" y="{top + 26}">{esc(name)}</text>'
            f'<text class="layer-file" x="{LAYER_X[0] + 54}" y="{top + 44}">{esc(file)}</text>')


def build_line(start, end, label=None, label_side="right", dashed=False, both=False, join=False):
    (x1, y1), (x2, y2) = start, end
    assert x1 == x2 or y1 == y2, "every line is horizontal or vertical"
    marks = ' marker-start="url(#head)" marker-end="url(#head)"' if both else ' marker-end="url(#head)"'
    path = f'<path class="line{" check" if dashed else ""}{" join" if join else ""}" d="M{x1} {y1} L{x2} {y2}"{marks}/>'
    if not label:
        return path
    if label_side == "right":
        return path + f'<text class="line-label" x="{x1 + 20}" y="{(y1 + y2) / 2 + 4}">{esc(label)}</text>'
    return path + f'<text class="line-label mid" x="{(x1 + x2) / 2}" y="{y1 - 8}">{esc(label)}</text>'


def build_badge(number, key, x, y, status, tip):
    return (f'<g class="badge s-{status}" id="x-{key}" tabindex="0"><circle cx="{x}" cy="{y}" r="12"/>'
            f'<text x="{x}" y="{y + 4.5}">{number}</text></g>')


def build_tip(number, row, status, text, x, y):
    key, origin, target, from_label, to_label, how, short_travels, short_key, travels, shared, check = row
    above = y > 300
    left = min(max(x - 145, 8), WIDTH - 298)
    top = y - 18 if above else y + 18
    anchor = "bottom:0" if above else "top:0"
    return (f'<g class="tip s-{status}" id="t-{key}"><foreignObject x="{left:.0f}" y="{top:.0f}" width="290" height="1" overflow="visible">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" style="{anchor}"><b>{number} · {esc(from_label)} → {esc(to_label)}</b>'
            f'<b>Cómo pasa</b>{esc(how)}<b>Qué viaja</b>{esc(travels)}<b>Con qué se cruzan</b>{esc(shared)}'
            f'<b>Comprobación</b><em>{STATUS_WORDS[status]}</em> · {esc(text)}</div></foreignObject></g>')


def build_crossings_html(palette, checks):
    """The databases as layers with their tables, and the numbered crossings between them as straight lines."""
    head = (f'<defs><marker id="head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>')
    parts = [head, f'<text class="zone-label" x="{LAYER_X[0] + 16}" y="{SOURCE_Y + 22}">Fuentes externas</text>']
    for column, kind, slug, label in SOURCES:
        left, right = COLUMNS[column]
        parts.append(f'<g class="source"><rect class="chip" x="{left}" y="{SOURCE_Y}" width="{right - left}" height="36" rx="9"/>'
                     f'{storage_map.source_mark(slug, left + 6, SOURCE_Y + 4, 28)}'
                     f'<text class="source-text" x="{left + 38}" y="{SOURCE_Y + 23}">{esc(label)}</text></g>')
    parts.extend(build_layer(*layer) for layer in LAYERS)
    parts.extend(build_chip(*chip) for chip in CHIPS)
    parts.append(f'<text class="note" x="{COLUMNS["c"][0]}" y="{layer_top("served") + 62 + 21}">↻ la próxima carga lo lee</text>')
    for index, line in enumerate(OTHER_TABLES):
        parts.append(f'<text class="note" x="{COLUMNS["a"][0]}" y="{layer_top("served") + 118 + index * 16}">{esc(line)}</text>')
    # The SQLite backup, at the right: its tables, the weekly_price one level with the served one.
    backup_top, backup_bottom = 90, layer_top("served") + 144
    parts.append(f'<rect class="layer" x="{BACKUP_X[0]}" y="{backup_top}" width="{BACKUP_X[1] - BACKUP_X[0]}" '
                 f'height="{backup_bottom - backup_top}" rx="16"/>'
                 f'<g transform="translate({BACKUP_X[0] + 12} {backup_top + 10})">{storage_map.mini_mark("db", "sqlite", "xbackup")}</g>'
                 f'<text class="layer-name" x="{BACKUP_X[0] + 52}" y="{backup_top + 26}">datos.db</text>'
                 f'<text class="layer-file" x="{BACKUP_X[0] + 52}" y="{backup_top + 44}">SQLite · respaldo</text>')
    for position, name in enumerate(BACKUP_CHIPS):
        y = backup_top + 70 + position * 42
        parts.append(f'<rect class="chip" x="{BACKUP_X[0] + 12}" y="{y}" width="{BACKUP_X[1] - BACKUP_X[0] - 24}" height="30" rx="9"/>'
                     f'<text class="chip-text" x="{(BACKUP_X[0] + BACKUP_X[1]) / 2}" y="{y + 19.5}">{name}</text>')
    wy = layer_top("served") + 16
    parts.append(f'<rect class="chip" x="{BACKUP_X[0] + 12}" y="{wy}" width="{BACKUP_X[1] - BACKUP_X[0] - 24}" height="{CHIP_HEIGHT}" rx="9"/>'
                 f'<text class="chip-text" x="{(BACKUP_X[0] + BACKUP_X[1]) / 2}" y="{wy + 20.5}">weekly_price</text>')
    # The join of the two data sets, inside the work database and again in the served one.
    for layer, y in JOIN_Y.items():
        gap_left, gap_right = COLUMNS["a"][1], COLUMNS["b"][0]
        parts.append(build_line((gap_left + 2, y), (gap_right - 2, y), None, join=True, both=True)
                     + f'<text class="line-label mid" x="{(gap_left + gap_right) / 2}" y="{y - 8}">week_start</text>')
    # Short arrows inside the work database: each staging model feeds its mart.
    work_row2 = layer_top("work") + 64
    for column in "abc":
        parts.append(build_line((center(column), layer_top("work") + 16 + CHIP_HEIGHT), (center(column), work_row2)))
    parts.append(build_line((COLUMNS["a"][1], layer_top("served") + 62 + CHIP_HEIGHT // 2),
                            (COLUMNS["b"][0], layer_top("served") + 62 + CHIP_HEIGHT // 2), "run_id", "mid"))
    # The crossings: lines first, numbers on top, hover cards last so nothing covers them.
    badges, tips = [], []
    for number, row in enumerate(CROSSINGS, start=1):
        key = row[0]
        if key == "history":
            x, y = COLUMNS["a"][0] - 14, layer_top("served") + 62 + CHIP_HEIGHT // 2
            status, text = checks.get(row[10], ("pending", "sin medir"))
        else:
            status, text = checks.get(row[10], ("pending", "sin medir"))
            first = LINES[key][0]
            (x1, y1), (x2, y2) = first
            x, y = (x1, (y1 + y2) / 2) if x1 == x2 else ((x1 + x2) / 2, y1)
            both = key == "served_backup"
            for index, (start, end) in enumerate(LINES[key]):
                label = LABELS[key] if index == 0 else None
                side = "right" if start[0] == end[0] else "above"
                if key in ("raw_backup", "served_backup"):
                    parts.append(build_line(start, end, None, dashed=both, both=both))
                    parts.append(f'<text class="line-label mid" x="{(start[0] + end[0]) / 2}" y="{start[1] - 20}">{LABELS[key]}</text>')
                else:
                    parts.append(build_line(start, end, label, side))
        badges.append(build_badge(number, key, x, y, status, text))
        tips.append(build_tip(number, row, status, text, x, y))
    legend = (f'<text class="note" x="{LAYER_X[0] + 16}" y="{HEIGHT - 6}">Cada línea es un cruce entre dos bases y lleva lo que las une. '
              f'El número se colorea con su comprobación de ahora: verde comprobado, ámbar no medible aquí, gris dato.</text>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body><svg class="map" viewBox="0 0 {WIDTH} {HEIGHT}" preserveAspectRatio="xMidYMid meet" '
            f'role="img" aria-label="Cruces entre bases">{"".join(parts)}{"".join(badges)}{legend}{"".join(tips)}</svg></body></html>')
