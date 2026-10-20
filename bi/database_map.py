"""«Dónde viven los datos» (D-189, D-190): where the data is stored, why, and how the stores relate.

One diagram of floating logos, no cards, like the operation center: the sources, the SQLite
landing database, the bronze layer in Parquet, dbt over its work DuckDB, the served DuckDB
file with the three groups of its 12 tables, and GitHub, where the published files are kept.
Under the landing database, the SQLite backup and the parity check that compares it with the
served file. Every logo answers on hover what it stores and why. The pipeline's steps and the
panel are not repeated: they are in «Pipeline y linaje».

Nothing here reads data: bi/dashboard.py hands over the counts. The page is a full HTML
document for st.iframe (CSS only, no script), like the operation center.
"""
import html

from bi import brand_icons, charts, operation_center

STAGE_WIDTH = 1000
STAGE_HEIGHT = 640
MAIN_Y = 235
LOGO = 92
HALF = LOGO // 2
GAP = 8  # between a logo and the tip of an arrow
# Brand marks on a soft gradient disc: (top, bottom, glyph color).
BRANDS = {
    "sqlite": ("#5db7f2", "#0b6aa8", "#ffffff"),
    "apacheparquet": ("#5fd7a4", "#13825a", "#ffffff"),
    "dbt": ("#ff9a7a", "#e2431a", "#ffffff"),
    "duckdb": ("#ffe66d", "#e6b800", "#1f1f1f"),
    "python": ("#6fa8dc", "#2a5d96", "#ffffff"),
    "github": ("#59616b", "#1b1f24", "#ffffff"),
}
# The three origins of the 12 served tables: (key, label, brand, tables, what, why).
ORIGINS = [
    ("marts", "Modelos dbt", "dbt",
     ["weekly_price", "dim_product", "dim_region", "dim_channel", "dim_date", "rejection", "ipc_weekly",
      "ipc_monthly", "ine_ipc_source"],
     "Las nueve tablas del modelo: los precios semanales, sus dimensiones, las filas rechazadas y el IPC.",
     "dbt las construye y las prueba en cada carga; el pipeline las copia tal cual a la base servida."),
    ("log", "Registro de cargas", "python", ["etl_run"],
     "Una fila por ejecución real: cuándo empezó, qué leyó, qué cargó y qué rechazó.",
     "La escribe el pipeline en Python al terminar. Una reconstrucción local no la toca, para no inventar cargas."),
    ("trace", "Trazas de dbt", "dbt", ["dbt_node", "dbt_result"],
     "Cada modelo y prueba de dbt de la última construcción, con su resultado.",
     "El linaje y la página de calidad las leen para mostrar qué se probó. No son datos de precios."),
]
# The stores, left to right: (key, logo, label, file, place (x, y), what, why).
NODES = [
    ("odepa", "odepa", "ODEPA consumidor", "CSV por año", (95, MAIN_Y),
     "Los precios al consumidor que ODEPA publica cada semana, por región y canal, en archivos CSV por año.",
     "Es la fuente oficial. El agente los descarga y anota su huella SHA-256 en manifest.json."),
    ("wholesale", "odepa", "ODEPA mayorista", "CSV por año", (95, MAIN_Y + 165),
     "Los precios mayoristas que ODEPA publica cada semana, solo de frutas y hortalizas, en archivos CSV por año.",
     "Es la otra fuente oficial: permite comparar lo que paga el consumidor con lo que cuesta al por mayor."),
    ("ine", "ine", "INE · IPC", "índice mensual", (95, 52),
     "El índice de precios de alimentos, un valor por mes.",
     "Sirve para pasar los precios a pesos reales y separar la inflación de una subida de verdad."),
    ("raw", "sqlite", "SQLite", "etl/raw.db", (275, MAIN_Y),
     "Las filas de los CSV exactamente como se publican, sin limpiar. Es un archivo de unos 665 MB.",
     "Una copia fiel permite auditar y reconstruir todo desde el origen. No se sube a GitHub por su tamaño."),
    ("bronze", "apacheparquet", "Parquet", "capa bronce", (435, MAIN_Y),
     "Las mismas filas, más el IPC del INE, en archivos Parquet: uno por fuente y año.",
     "Parquet guarda los datos por columnas y comprimidos, y casi cualquier herramienta de datos lo lee. "
     "dbt parte de aquí."),
    ("dbt", "dbt", "dbt + DuckDB", "warehouse_build.duckdb", (595, MAIN_Y),
     "Una base de trabajo con las capas staging, intermedio y marts, más las pruebas de datos de dbt.",
     "Se construye y se prueba aparte. Si una prueba falla, la base publicada no se toca. No se sube a GitHub."),
    ("served", "duckdb", "DuckDB", "etl/datos.duckdb", (755, MAIN_Y),
     "La base que el panel lee: 12 tablas, agrupadas por quién las escribe (abajo).",
     "Es un solo archivo, rápido para consultas analíticas y de solo lectura para el panel."),
    ("github", "github", "GitHub", "el repositorio", (915, MAIN_Y),
     "Los dos archivos de base de datos publicados, con todo su historial.",
     "La carga semanal los sube con un commit: así quedan versionados y la app publicada los recibe."),
    ("backup", "sqlite", "SQLite · respaldo", "etl/datos.db", (275, 505),
     "Los mismos precios semanales, calculados otra vez por el ETL en Python (etl/etl.py), sin dbt.",
     "Es una segunda opinión independiente: si dbt y el ETL no coinciden, algo está mal. El panel no lo lee."),
]
# Arrows between stores, from the edge of one logo to the edge of the next: (from, to, label).
FLOW = [("odepa", "raw", "descarga"), ("raw", "bronze", "copia exacta"), ("bronze", "dbt", "a Parquet"),
        ("dbt", "served", "construye"), ("served", "github", "se publica")]
PLACES = {key: place for key, _, _, _, place, _, _ in NODES}


def build_arrows():
    """[(path, label, (x, y))] in stage coordinates, computed from the stores' places."""
    arrows = []
    for start, end, label in FLOW:
        (x1, y), (x2, _) = PLACES[start], PLACES[end]
        arrows.append((f"M{x1 + HALF + GAP} {y} H{x2 - HALF - GAP}", label, ((x1 + x2) / 2, y - 14)))
    ine_x, ine_y = PLACES["ine"]
    bronze_x, bronze_y = PLACES["bronze"]
    arrows.append((f"M{ine_x + HALF + GAP} {ine_y} H{bronze_x} V{bronze_y - HALF - 4}", "índice mensual",
                   ((ine_x + bronze_x) / 2, ine_y - 12)))
    wholesale_x, wholesale_y = PLACES["wholesale"]
    raw_edge = PLACES["raw"][0] - HALF - GAP
    arrows.append((f"M{wholesale_x + HALF + GAP} {wholesale_y} H{(wholesale_x + PLACES['raw'][0]) / 2 + 20} V{PLACES['raw'][1] + 14} "
                   f"H{raw_edge}", "descarga", (wholesale_x + HALF + GAP + 28, wholesale_y - 14)))
    raw_x, raw_y = PLACES["raw"]
    backup_y = PLACES["backup"][1]
    arrows.append((f"M{raw_x} {raw_y + 140} V{backup_y - HALF - 6}", "ETL en Python", (raw_x + 56, (raw_y + 140 + backup_y - HALF) / 2 + 4)))
    return arrows


ARROWS = build_arrows()
# The parity line: from the backup to the left end of the group's brace.
BRACE_Y = MAIN_Y + 142
# It goes round the left of the group of three and ends on the DuckDB file itself, under
# its size, so it points at the whole database and not at one of its table groups.
SERVED_BOTTOM = MAIN_Y + 128
PARITY_X = PLACES["served"][0] - 205
PARITY_PATH = (f"M{PLACES['backup'][0] + HALF + GAP} {PLACES['backup'][1]} H{PARITY_X} "
               f"V{SERVED_BOTTOM} H{PLACES['served'][0] - 52}")
PARITY_LABEL = (440, PLACES["backup"][1] - 13)


def thousands(value):
    return charts.format_thousands(value) if value is not None else "—"


def brand_logo(slug, suffix=""):
    """A real brand mark in white (or ink) on a lit disc, with a gloss and a drop shadow."""
    top, bottom, glyph = BRANDS[slug]
    gradient = f"disc-{slug}{suffix}"
    return (f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs>'
            f'<radialGradient id="{gradient}" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></radialGradient></defs>'
            f'<circle cx="36" cy="36" r="31" fill="url(#{gradient})"/>'
            f'<ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" opacity=".3"/>'
            f'<g fill="{glyph}" transform="translate(17 17) scale(1.58)">{brand_icons.logo_body(slug)}</g></svg>')


def source_logo(key):
    """ODEPA's and the INE's marks, the ones of the operation center."""
    return (f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs>{operation_center.LOGOS[key]}</svg>')


def tip(what, why, side=""):
    return (f'<span class="tip {side}" role="tooltip"><b>Qué guarda</b>{html.escape(what)}'
            f'<b>Por qué</b>{html.escape(why)}</span>')


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text};
  font:300 14px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
.stage {{ position:relative; width:100%; max-width:{STAGE_WIDTH}px; aspect-ratio:{STAGE_WIDTH}/{STAGE_HEIGHT}; margin:0 auto; }}
.stage > svg {{ position:absolute; inset:0; width:100%; height:100%; overflow:visible; }}
.arrow {{ fill:none; stroke:{accent}; stroke-width:2; stroke-linecap:round; }}
.arrow.dashed {{ stroke-dasharray:5 6; opacity:.85; }}
.arrow-label {{ font-size:12px; fill:{muted}; text-anchor:middle; }}
.node {{ position:absolute; width:156px; margin-left:-78px; margin-top:-{HALF}px; display:flex; flex-direction:column;
  align-items:center; text-align:center; outline:none; }}
.logo {{ display:block; width:{LOGO}px; height:{LOGO}px; filter:drop-shadow(0 16px 14px {shadow}); transition:transform .25s ease; }}
.node:hover .logo, .node:focus .logo, .mini:hover .logo, .mini:focus .logo {{ transform:translateY(-6px) scale(1.05); }}
.logo-wrap {{ position:relative; width:{LOGO}px; height:{LOGO}px; }}
.cyl {{ position:absolute; right:-9px; bottom:-4px; width:30px; height:35px; filter:drop-shadow(0 4px 4px {shadow}); transition:transform .25s ease; }}
.node:hover .cyl, .node:focus .cyl {{ transform:translateY(-4px); }}
.halo {{ width:70px; height:12px; border-radius:50%; margin-top:4px; filter:blur(4px);
  background:{'rgba(255,255,255,.12)' if dark else 'rgba(15,39,71,.16)'}; }}
.served .halo {{ background:rgba(244,208,63,.6); }}
.label {{ margin-top:8px; font-weight:500; font-size:15.5px; color:{ink}; }}
.file {{ margin-top:1px; font:400 12px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; color:{muted}; }}
.size {{ margin-top:3px; padding:1px 9px; border-radius:999px; font-size:11.5px; font-weight:500; color:{ink};
  background:color-mix(in srgb, {accent} 12%, transparent); }}
.tip {{ position:absolute; z-index:30; left:50%; top:calc(100% + 6px); width:272px; padding:12px 14px; border-radius:14px;
  text-align:left; background:{card}; border:1px solid {border}; box-shadow:0 18px 40px rgba(0,0,0,{'.5' if dark else '.18'});
  color:{text}; font-size:12.5px; line-height:1.45; opacity:0; pointer-events:none; transform:translate(-50%, 6px);
  transition:opacity .18s ease, transform .18s ease; }}
.tip b {{ display:block; margin:8px 0 2px; font-size:10px; font-weight:500; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip b:first-child {{ margin-top:0; }}
.tip.start {{ left:0; transform:translate(0, 6px); }} .tip.end {{ left:auto; right:0; transform:translate(0, 6px); }}
.tip.up {{ top:auto; bottom:calc(100% + 6px); }}
.tip.up.end {{ transform:translate(0, 6px); }}
.node:hover .tip, .node:focus .tip, .mini:hover .tip, .mini:focus .tip, .parity:hover .tip, .parity:focus .tip {{
  opacity:1; transform:translate(-50%, 0); }}
.node:hover .tip.start, .node:focus .tip.start, .node:hover .tip.end, .node:focus .tip.end {{ transform:translate(0, 0); }}
.node:hover, .node:focus, .mini:hover, .mini:focus, .parity:hover, .parity:focus {{ z-index:40; }}
.group {{ z-index:5; position:absolute; display:flex; gap:6px; left:{755 / STAGE_WIDTH * 100}%; top:{(MAIN_Y + 158) / STAGE_HEIGHT * 100}%;
  transform:translateX(-50%); }}
.mini {{ position:relative; width:124px; display:flex; flex-direction:column; align-items:center; text-align:center; outline:none; }}
.mini .logo {{ width:58px; height:58px; filter:drop-shadow(0 8px 8px {shadow}); }}
.mini b {{ margin-top:5px; font-weight:500; font-size:13.5px; color:{ink}; }}
.mini small {{ font-size:12px; color:{muted}; }}
.mini .tip {{ width:340px; }}
.mini .tip ul {{ margin:6px 0 0; padding:0; list-style:none; display:grid; grid-template-columns:1fr 1fr; gap:0 18px;
  font:400 11px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace; color:{ink}; }}
.mini .tip li {{ display:flex; justify-content:space-between; gap:10px; }}
.mini .tip li span {{ color:{muted}; }}
.brace {{ position:absolute; left:{755 / STAGE_WIDTH * 100}%; top:{BRACE_Y / STAGE_HEIGHT * 100}%; width:344px; height:8px;
  transform:translateX(-50%); border:1px solid {border}; border-bottom:0; border-radius:8px 8px 0 0; }}
.parity {{ position:absolute; left:{PARITY_LABEL[0] / STAGE_WIDTH * 100}%; top:{PARITY_LABEL[1] / STAGE_HEIGHT * 100}%;
  transform:translate(-50%, -50%); padding:3px 12px; border-radius:999px; border:1px solid {border}; background:{card};
  font-size:12.5px; color:{ink}; outline:none; cursor:default; z-index:2; }}
.parity .tip {{ top:auto; bottom:calc(100% + 8px); }}
.legend {{ margin:6px 4px 0; font-size:11.5px; color:{muted}; text-align:center; }}
</style>"""


# The stores that hold data in a database or a lake, which carry the cylinder (D-192).
STORES = ("raw", "bronze", "dbt", "served", "backup")
CYLINDER = ('<svg class="cyl" viewBox="0 0 24 28" aria-hidden="true"><defs><linearGradient id="cyl-body" x1="0" x2="1">'
            '<stop offset="0" stop-color="#9aa7b8"/><stop offset=".45" stop-color="#f4f7fb"/><stop offset="1" stop-color="#8794a6"/>'
            '</linearGradient></defs><path d="M2 6v16c0 2.2 4.5 4 10 4s10-1.8 10-4V6z" fill="url(#cyl-body)"/>'
            '<path d="M2 12.5c0 2.2 4.5 4 10 4s10-1.8 10-4M2 18.5c0 2.2 4.5 4 10 4s10-1.8 10-4" fill="none" '
            'stroke="#5b6b7f" stroke-width="1.2" opacity=".75"/><ellipse cx="12" cy="6" rx="10" ry="4" fill="#ffffff" '
            'stroke="#5b6b7f" stroke-width="1.2"/></svg>')


def build_node_html(key, logo, label, file, place, what, why, size=""):
    left, top = place[0] / STAGE_WIDTH * 100, place[1] / STAGE_HEIGHT * 100
    side = "start" if place[0] < 200 else "end" if place[0] > 850 else ""
    mark = source_logo(logo) if logo in ("odepa", "ine") else brand_logo(logo, "-" + key)
    return (f'<div class="node {key}" tabindex="0" style="left:{left:.3f}%;top:{top:.3f}%">'
            f'{tip(what, why, side)}<div class="logo-wrap">{mark}{CYLINDER if key in STORES else ""}</div><div class="halo"></div><div class="label">{html.escape(label)}</div>'
            f'<div class="file">{html.escape(file)}</div>'
            + (f'<div class="size">{html.escape(size)}</div>' if size else '') + '</div>')


def build_group_html(counts):
    """The three origins of the served tables, as small logos under the DuckDB file."""
    minis = []
    for position, (key, label, brand, names, what, why) in enumerate(ORIGINS):
        side = "up end" if position == len(ORIGINS) - 1 else "up"
        rows = "".join(f'<li>{html.escape(name)}<span>{thousands(counts.get(name))}</span></li>' for name in names)
        total = sum(counts.get(name, 0) for name in names)
        minis.append(f'<div class="mini" tabindex="0">{brand_logo(brand, "-" + key)}<b>{html.escape(label)}</b>'
                     f'<small>{len(names)} tabla{"s" if len(names) > 1 else ""} · {thousands(total)} filas</small>'
                     f'<span class="tip {side}" role="tooltip"><b>Qué guarda</b>{html.escape(what)}'
                     f'<b>Por qué</b>{html.escape(why)}<ul>{rows}</ul></span></div>')
    return f'<div class="brace"></div><div class="group">{"".join(minis)}</div>'


def build_map_html(palette, counts, layers, tests, sizes=None):
    """The whole diagram as one HTML document. counts: {table: rows} of the served file;
    layers: {"staging": n, "intermediate": n, "marts": n}; tests: dbt tests in the build;
    sizes: {store key: "14 MB"} of the files that exist, shown under each logo."""
    served_total = sum(counts.get(name, 0) for *_, names, _, _ in ORIGINS for name in names)
    models = sum(layers.values())
    notes = {
        "dbt": f"Una base de trabajo con {models} modelos en tres capas (staging {layers.get('staging', 0)}, intermedio "
               f"{layers.get('intermediate', 0)} y marts {layers.get('marts', 0)}) y {tests} pruebas de datos de dbt.",
        "served": f"La base que el panel lee: 12 tablas y {thousands(served_total)} filas, agrupadas por quién las escribe (abajo).",
    }
    nodes = "".join(build_node_html(key, logo, label, file, place, notes.get(key, what), why, (sizes or {}).get(key, ""))
                    for key, logo, label, file, place, what, why in NODES)
    marker = (f'<defs><marker id="head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
              f'orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>')
    arrows = "".join(f'<path class="arrow" d="{path}" marker-end="url(#head)"/>'
                     f'<text class="arrow-label" x="{x}" y="{y}">{html.escape(label)}</text>'
                     for path, label, (x, y) in ARROWS)
    parity = f'<path class="arrow dashed" d="{PARITY_PATH}" marker-start="url(#head)" marker-end="url(#head)"/>'
    parity_label = ('<div class="parity" tabindex="0">Paridad<span class="tip" role="tooltip"><b>Qué hace</b>'
                    'Compara el respaldo SQLite con DuckDB: mismos precios, mismos rechazos y misma suma.'
                    '<b>Por qué</b>Si dos caminos independientes dan lo mismo, la carga es confiable. La página '
                    'Calidad y auditoría lo comprueba en cada carga.</span></div>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">' + build_css(palette)
            + '</head><body><div class="stage" aria-label="Dónde viven los datos">'
              f'<svg viewBox="0 0 {STAGE_WIDTH} {STAGE_HEIGHT}" aria-hidden="true">{marker}{arrows}{parity}</svg>'
              f'{nodes}{build_group_html(counts)}{parity_label}</div>'
              '<p class="legend">Pasa el cursor por cada logo para ver qué guarda y por qué.</p></body></html>')
