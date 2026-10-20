"""Where two databases meet (D-197): every crossing between stores, with how it happens,
what travels, what the two sides share and, where it can be measured here, the live check."""
import html

from bi import charts, database_map, queries

BACKUP_TABLES = ["dim_product", "dim_region", "dim_channel", "dim_date", "weekly_price", "rejection", "etl_run"]
RAW_NOTE = "no se puede comprobar aquí: raw.db no está en este servidor"

# (key, from (kind, slug), to (kind, slug), from label, to label, mechanism, what travels, what both share, check key)
CROSSINGS = [
    ("odepa_raw", ("source", "odepa"), ("brand", "sqlite"), "ODEPA", "raw.db", "descarga con Python",
     "Los CSV públicos de precios, una fila de texto por observación, sin cambiar un valor.",
     "El nombre del archivo y su huella SHA-256, anotada en manifest.json.", "raw"),
    ("raw_bronze", ("brand", "sqlite"), ("brand", "apacheparquet"), "raw.db", "Bronce", "lectura en solo lectura",
     "Todas las filas crudas, un Parquet por fuente y año, con las columnas como texto.",
     "La fuente y el año del archivo: cada Parquet es una carpeta file_year=AAAA.", "raw"),
    ("raw_backup", ("brand", "sqlite"), ("brand", "sqlite"), "raw.db", "datos.db", "ETL en Python (etl/etl.py)",
     "Las mismas filas crudas, validadas y llevadas a precio semanal por un camino independiente de dbt.",
     "Las mismas reglas de negocio: por eso su resultado debe dar las mismas cifras que la base servida.", "raw"),
    ("ine_bronze", ("source", "ine"), ("brand", "apacheparquet"), "INE", "Bronce", "directo, sin pasar por SQLite",
     "El índice de precios de alimentos, mensual. Por diseño no toca raw.db: no es una fuente de precios de ODEPA.",
     "El mes del índice, que dbt cruza luego con las semanas.", "ine"),
    ("bronze_work", ("brand", "apacheparquet"), ("brand", "dbt"), "Bronce", "Base de trabajo de dbt", "dbt lee los Parquet",
     "Las filas del bronce, ya con tipos, reglas de calidad y marcas. Aquí se cruzan ODEPA y el INE.",
     "La semana (week_start): ipc_weekly lleva el IPC de cada mes a cada semana de precios.", "work"),
    ("work_served", ("brand", "dbt"), ("brand", "duckdb"), "Base de trabajo", "datos.duckdb", "ATTACH en solo lectura y CREATE TABLE AS",
     "Las nueve tablas del modelo, más la traza de dbt y el registro de cargas.",
     "Los mismos nombres de tabla; la base servida se reemplaza entera al final, nunca a medias.", "served"),
    ("served_backup", ("brand", "duckdb"), ("brand", "sqlite"), "datos.duckdb", "datos.db", "comparación de tres cifras",
     "Nada se copia: solo se comparan las filas de weekly_price, las filas rechazadas y la suma de los precios.",
     "Las tablas del modelo estrella: el respaldo SQLite tiene siete de las doce.", "parity"),
    ("history", ("brand", "duckdb"), ("brand", "python"), "datos.duckdb", "Próxima carga", "etl_run arrastrado",
     "El historial de cargas: la carga nueva lo lee de la base servida y le agrega su fila. En la primera vez lo leyó de datos.db.",
     "El número de carga (run_id), que también guarda cada fila de rejection.", "history"),
]


def read_checks(database_file=queries.DATABASE_FILE, backup_file=None):
    """{crossing key: (status, text)} of what can be measured in this server."""
    from bi import quality
    checks = {key: ("pending", RAW_NOTE) for key in ("raw",)}
    checks["ine"] = ("info", "El IPC publicado se guarda también como ine_ipc_source, la copia cruda de los archivos del INE.")
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
                         f"{runs} cargas registradas; {rejection_runs} cargas de rechazos sin su fila en etl_run.")
    parity = quality.check_parity(**({"backup_file": backup_file} if backup_file else {}), database_file=database_file)
    if parity is None:
        checks["parity"] = ("pending", "datos.db no está en este servidor")
    else:
        text = (f"{database_map.thousands(parity['rows'][1])} filas y {database_map.thousands(parity['rejections'][1])} rechazos "
                f"en la base servida; {database_map.thousands(parity['rows'][0])} y "
                f"{database_map.thousands(parity['rejections'][0])} en el respaldo.")
        checks["parity"] = ("ok" if parity["ok"] else "fail", text)
    return checks


STATUS_WORDS = {"ok": "Comprobado ahora", "fail": "No coincide", "warn": "Revisar", "pending": "Pendiente", "info": "Dato"}
STAGE_WIDTH, STAGE_HEIGHT, LOGO = 1000, 590, 80
HALF = LOGO // 2
# The stores: (database_map node key for its tooltip, logo, label, file, (x, y)).
STORES = [
    ("odepa", ("source", "odepa"), "ODEPA", "CSV por año", (90, 300)),
    ("ine", ("source", "ine"), "INE · IPC", "CSV mensual", (90, 480)),
    ("raw", ("brand", "sqlite"), "raw.db", "SQLite · aterrizaje", (290, 300)),
    ("bronze", ("brand", "apacheparquet"), "Bronce", "Parquet", (490, 300)),
    ("dbt", ("brand", "dbt"), "Base de trabajo", "warehouse_build.duckdb", (690, 300)),
    ("served", ("brand", "duckdb"), "datos.duckdb", "la base servida", (890, 300)),
    ("backup", ("brand", "sqlite"), "datos.db", "SQLite · respaldo", (890, 80)),
]
# Each crossing on the stage: (crossing key, svg path, short label and its place, number place, dashed, both ways).
EDGES = {
    "odepa_raw": ("M138 300 H242", "descarga", (190, 286), (190, 300), False, False),
    "raw_bronze": ("M338 300 H442", "a Parquet", (390, 286), (390, 300), False, False),
    "raw_backup": ("M290 252 V80 H842", "ETL en Python", (560, 66), (560, 80), False, False),
    "ine_bronze": ("M138 480 H380 L458 336", "directo, sin SQLite", (260, 466), (300, 480), False, False),
    "bronze_work": ("M538 300 H642", "dbt lee", (590, 286), (590, 300), False, False),
    "work_served": ("M738 300 H842", "publica", (790, 286), (790, 300), False, False),
    "served_backup": ("M890 252 V186", "paridad", (935, 222), (890, 219), True, True),
    "history": ("M922 400 C 985 485, 795 485, 858 400", "etl_run → próxima carga", (890, 500), (890, 464), False, False),
}


def node_tip(key):
    """What the store holds and why, from the storage diagram, so both views say the same."""
    node = next((row for row in database_map.NODES if row[0] == key), None)
    if not node:
        return ""
    return f'<span class="tip{" start" if key in ("odepa", "ine") else " end" if key in ("served", "backup") else ""}" role="tooltip"><b>Qué guarda</b>{html.escape(node[5])}<b>Por qué</b>{html.escape(node[6])}</span>'


def endpoint(kind_slug, suffix):
    kind, slug = kind_slug
    return database_map.source_logo(slug) if kind == "source" else database_map.brand_logo(slug, suffix)


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    status = {"ok": "#22b35a", "fail": "#d03b3b", "warn": "#d97706", "pending": "#d97706", "info": "#8a94a6"}
    rules = "".join(f".s-{key} {{ --c:{value}; }}" for key, value in status.items())
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:300 14px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
{rules}
.stage {{ position:relative; width:100%; max-width:{STAGE_WIDTH}px; aspect-ratio:{STAGE_WIDTH}/{STAGE_HEIGHT}; margin:0 auto; }}
.stage > svg {{ position:absolute; inset:0; width:100%; height:100%; overflow:visible; }}
.arrow {{ fill:none; stroke:{accent}; stroke-width:2; stroke-linecap:round; }}
.arrow.dashed {{ stroke-dasharray:5 6; }}
.arrow-label {{ font-size:12.5px; fill:{muted}; text-anchor:middle; }}
.node {{ position:absolute; width:170px; margin-left:-85px; margin-top:-{HALF}px; display:flex; flex-direction:column; align-items:center;
  text-align:center; outline:none; }}
.logo {{ display:block; width:{LOGO}px; height:{LOGO}px; filter:drop-shadow(0 14px 12px {shadow}); transition:transform .25s ease; }}
.node:hover .logo, .node:focus .logo {{ transform:translateY(-5px) scale(1.05); }}
.label {{ margin-top:6px; font-weight:500; font-size:15px; color:{ink}; }}
.file {{ font:400 11.5px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; color:{muted}; }}
.x {{ position:absolute; z-index:3; transform:translate(-50%, -50%); width:24px; height:24px; border-radius:50%; display:grid; place-items:center;
  font-size:12px; font-weight:600; color:#fff; background:var(--c); box-shadow:0 0 0 3px {palette['background']}, 0 6px 12px {shadow};
  outline:none; cursor:default; }}
.x:hover, .x:focus {{ transform:translate(-50%, -50%) scale(1.15); }}
.tip {{ position:absolute; z-index:40; left:50%; top:calc(100% + 8px); width:300px; padding:12px 14px; border-radius:14px; text-align:left;
  background:{card}; border:1px solid {border}; box-shadow:0 18px 40px rgba(0,0,0,{'.5' if dark else '.18'}); color:{text};
  font-size:12.5px; font-weight:300; line-height:1.45; display:none; pointer-events:none; transform:translateX(-50%); }}
.tip b {{ display:block; margin:8px 0 2px; font-size:10px; font-weight:500; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip b:first-child {{ margin-top:0; }}
.tip strong {{ display:block; font-size:13.5px; font-weight:500; color:{ink}; }}
.tip em {{ font-style:normal; color:var(--c); font-weight:500; }}
.tip.start {{ left:0; transform:none; }} .tip.end {{ left:auto; right:0; transform:none; }} .tip.up {{ top:auto; bottom:calc(100% + 8px); }}
.node:hover .tip, .node:focus .tip, .x:hover .tip, .x:focus .tip {{ display:block; }}
.node:hover, .node:focus, .x:hover, .x:focus {{ z-index:50; }}
.legend {{ margin:4px 4px 0; font-size:11.5px; color:{muted}; text-align:center; }}
.legend i {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin:0 4px 0 12px; vertical-align:-1px; background:var(--c); }}
</style>"""


def build_crossings_html(palette, checks):
    """Every crossing between two stores as an arrow with its number; hovering the number tells how it
    happens, what travels, what both sides share and the check of now. Hovering a store tells what it holds."""
    marker = (f'<defs><marker id="head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
              f'orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>')
    arrows, numbers = [], []
    for number, (key, origin, target, from_label, to_label, how, travels, shared, check) in enumerate(CROSSINGS, start=1):
        path, label, (lx, ly), (nx, ny), dashed, both = EDGES[key]
        start = ' marker-start="url(#head)"' if both else ""
        arrows.append(f'<path class="arrow{" dashed" if dashed else ""}" d="{path}"{start} '
                      f'marker-end="url(#head)"/><text class="arrow-label" x="{lx}" y="{ly}">{html.escape(label)}</text>')
        status, text = checks.get(check, ("pending", "sin medir"))
        side = " end" if nx > 700 else " start" if nx < 250 else ""
        up = " up" if ny > 420 else ""
        numbers.append(f'<div class="x s-{status}" tabindex="0" style="left:{nx / STAGE_WIDTH * 100:.3f}%;top:{ny / STAGE_HEIGHT * 100:.3f}%">'
                       f'{number}<span class="tip{side}{up}" role="tooltip"><strong>{html.escape(from_label)} → {html.escape(to_label)}</strong>'
                       f'<b>Cómo pasa</b>{html.escape(how)}<b>Qué viaja</b>{html.escape(travels)}<b>Con qué se cruzan</b>{html.escape(shared)}'
                       f'<b>Comprobación</b><em>{STATUS_WORDS[status]}</em> · {html.escape(text)}</span></div>')
    nodes = []
    for key, logo, label, file, (x, y) in STORES:
        nodes.append(f'<div class="node" tabindex="0" style="left:{x / STAGE_WIDTH * 100:.3f}%;top:{y / STAGE_HEIGHT * 100:.3f}%">'
                     f'{node_tip(key)}{endpoint(logo, "-x" + key)}<div class="label">{html.escape(label)}</div>'
                     f'<div class="file">{html.escape(file)}</div></div>')
    legend = ('<p class="legend">Pasa el cursor por un número para ver el cruce, y por un logo para ver qué guarda.'
              '<span class="s-ok"><i></i></span>comprobado ahora<span class="s-pending"><i></i></span>no se puede comprobar aquí'
              '<span class="s-info"><i></i></span>dato</p>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body><div class="stage" aria-label="Cruces entre bases">'
            f'<svg viewBox="0 0 {STAGE_WIDTH} {STAGE_HEIGHT}" aria-hidden="true">{marker}{"".join(arrows)}</svg>'
            f'{"".join(nodes)}{"".join(numbers)}</div>{legend}</body></html>')
