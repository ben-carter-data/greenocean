"""The diagrams of the project documents (D-205), drawn like the pipeline: floating 3D logos,
few or no boxes, arrows that say what travels, and an explanation on hover.

Each build_* function returns one HTML document for st.iframe (gradients and hover tips do
not survive st.markdown). Positions are in a fixed stage that scales with the width.
"""
import html
import re

from bi import brand_icons, charts, operation_center, quality_view

# Disc colors per brand mark: (top, bottom, glyph).
BRANDS = {
    "sqlite": ("#5db7f2", "#0b6aa8", "#ffffff"),
    "apacheparquet": ("#5fd7a4", "#13825a", "#ffffff"),
    "dbt": ("#ff9a7a", "#e2431a", "#ffffff"),
    "duckdb": ("#ffe66d", "#e6b800", "#1f1f1f"),
    "python": ("#6fa8dc", "#2a5d96", "#ffffff"),
    "github": ("#59616b", "#1b1f24", "#ffffff"),
    "git": ("#ffa36b", "#d84a1b", "#ffffff"),
    "pytest": ("#d29cf0", "#7b2fa8", "#ffffff"),
    "streamlit": ("#ff8a8a", "#e0313b", "#ffffff"),
}
PEOPLE = {"visitor": ("#7fe0b0", "#1d8a5b"), "author": ("#ffd27a", "#c47f12"), "team": ("#9fb3c8", "#3d4f66")}
LAYER = {"source": "#22b35a", "flow": "#38bdf8", "build": "#a78bfa", "ops": "#f59e0b", "serve": "#f472b6"}


def esc(value):
    return html.escape(str(value))


def brand(slug, suffix):
    top, bottom, glyph = BRANDS[slug]
    gradient = f"g-{slug}-{suffix}"
    return (f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs><radialGradient id="{gradient}" cx="35%" '
            f'cy="28%" r="85%"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></radialGradient>'
            f'</defs><circle cx="36" cy="36" r="31" fill="url(#{gradient})"/><ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" '
            f'opacity=".3"/><g fill="{glyph}" transform="translate(17 17) scale(1.58)">{brand_icons.logo_body(slug)}</g></svg>')


def person(kind, suffix):
    top, bottom = PEOPLE[kind]
    gradient = f"p-{kind}-{suffix}"
    return (f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs><radialGradient id="{gradient}" cx="35%" '
            f'cy="28%" r="85%"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></radialGradient>'
            f'</defs><circle cx="36" cy="36" r="31" fill="url(#{gradient})"/><ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" '
            f'opacity=".3"/><circle cx="36" cy="29" r="8" fill="#fff"/><path d="M21 52c2-9 8-13 15-13s13 4 15 13z" fill="#fff"/></svg>')


def mark(key):
    """The operation center's 3D marks (odepa, ine, etl, report, panel, tests, save, launch, dbt)."""
    return f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs>{operation_center.LOGOS[key]}</svg>'


def icon(name):
    return quality_view.build_icon_svg(name).replace('class="qa-icon"', 'class="logo"')


def logo(spec, suffix):
    kind, name = spec
    suffix = re.sub(r"[^A-Za-z0-9]", "", str(suffix))  # a gradient id with spaces breaks url(#…)
    return {"brand": lambda: brand(name, suffix), "person": lambda: person(name, suffix),
            "mark": lambda: mark(name), "icon": lambda: icon(name)}[kind]()


def build_css(palette, width, height, logo_size):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border = (palette["strong_text"], palette["text"], palette["reference"],
                                      palette["card"], palette["card_border"])
    shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:300 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
.stage {{ position:relative; width:100%; max-width:{width}px; aspect-ratio:{width}/{height}; margin:0 auto; }}
.stage > svg {{ position:absolute; inset:0; width:100%; height:100%; overflow:visible; }}
.edge {{ fill:none; stroke-width:2; stroke-linecap:round; opacity:.9; }}
.edge.dashed {{ stroke-dasharray:5 6; }}
.edge-label {{ font:500 11.5px ui-monospace, SFMono-Regular, Menlo, monospace; text-anchor:middle; }}
.edge-chip {{ fill:{palette['background']}; }}
.zone {{ fill:none; stroke:{border}; stroke-width:1.4; stroke-dasharray:6 6; }}
.zone-title {{ font:600 11px -apple-system, sans-serif; letter-spacing:.12em; fill:{muted}; }}
.node {{ position:absolute; width:150px; margin-left:-75px; margin-top:-{logo_size // 2}px; display:flex; flex-direction:column;
  align-items:center; text-align:center; outline:none; }}
.node.wide {{ width:190px; margin-left:-95px; }}
.node .logo {{ display:block; width:{logo_size}px; height:{logo_size}px; filter:drop-shadow(0 12px 10px {shadow}); transition:transform .25s ease; }}
.node.small .logo {{ width:{int(logo_size * .78)}px; height:{int(logo_size * .78)}px; }}
.node.big .logo {{ width:{int(logo_size * 1.3)}px; height:{int(logo_size * 1.3)}px; }}
.node:hover .logo, .node:focus .logo {{ transform:translateY(-5px) scale(1.05); }}
.node b {{ margin-top:6px; font-weight:500; font-size:13.5px; color:{ink}; line-height:1.2; }}
.node small {{ color:{muted}; font-size:11.5px; line-height:1.25; }}
.node code {{ color:{muted}; font:400 11px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; }}
.node.row {{ flex-direction:row; width:280px; margin-left:-30px; text-align:left; gap:10px; align-items:center; }}
.node.row div {{ display:flex; flex-direction:column; }}
.node.row b {{ margin-top:0; }}
.tip {{ position:absolute; z-index:40; left:50%; top:calc(100% + 6px); width:280px; padding:11px 13px; border-radius:14px; text-align:left;
  background:{card}; border:1px solid {border}; box-shadow:0 18px 40px rgba(0,0,0,{'.5' if dark else '.18'}); color:{text};
  font-size:12.5px; line-height:1.45; display:none; pointer-events:none; transform:translateX(-50%); }}
.tip i {{ display:block; margin:7px 0 2px; font:500 10px/1 sans-serif; font-style:normal; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip i:first-child {{ margin-top:0; }}
.tip.start {{ left:0; transform:none; }} .tip.end {{ left:auto; right:0; transform:none; }} .tip.up {{ top:auto; bottom:calc(100% + 6px); }}
.node:hover .tip, .node:focus .tip {{ display:block; }}
.node:hover, .node:focus {{ z-index:50; }}
.legend {{ margin:4px 4px 0; font-size:11.5px; color:{muted}; text-align:center; }}
</style>"""


def build_node(spec, x, y, title, subtitle, what, why="", style="", suffix="", width=1000, height=600, code=False):
    side = " start" if x < width * .2 else " end" if x > width * .8 else ""
    up = " up" if y > height * .62 else ""
    sub = f"<code>{esc(subtitle)}</code>" if code else f"<small>{esc(subtitle)}</small>"
    tip = f'<span class="tip{side}{up}" role="tooltip"><i>Qué hace</i>{esc(what)}' + (f'<i>Por qué</i>{esc(why)}' if why else "") + "</span>"
    body = (f'{logo(spec, suffix or title)}<div><b>{esc(title)}</b>{sub}</div>' if "row" in style
            else f'{logo(spec, suffix or title)}<b>{esc(title)}</b>{sub}')
    return (f'<div class="node {style}" tabindex="0" style="left:{x / width * 100:.3f}%;top:{y / height * 100:.3f}%">'
            f'{tip}{body}</div>')


def build_edge(path, color, label="", at=None, dashed=False, both=False):
    start = f' marker-start="url(#h-{color[1:]})"' if both else ""
    parts = [f'<path class="edge{" dashed" if dashed else ""}" d="{path}" stroke="{color}"{start} marker-end="url(#h-{color[1:]})"/>']
    if label and at:
        width = len(label) * 7.2 + 14
        parts.append(f'<rect class="edge-chip" x="{at[0] - width / 2}" y="{at[1] - 10}" width="{width}" height="20" rx="6" '
                     f'stroke="{color}" stroke-width="1"/><text class="edge-label" x="{at[0]}" y="{at[1] + 4}" fill="{color}">'
                     f'{esc(label)}</text>')
    return "".join(parts)


def markers():
    return "<defs>" + "".join(
        f'<marker id="h-{color[1:]}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="{color}"/></marker>' for color in LAYER.values()) + "</defs>"


def build_page(palette, width, height, logo_size, svg, nodes, legend, label):
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette, width, height, logo_size) + f'</head><body>{quality_view.DEFS}<div class="stage" aria-label="{esc(label)}">'
            f'<svg viewBox="0 0 {width} {height}" aria-hidden="true">{markers()}{svg}</svg>{nodes}</div>'
            f'<p class="legend">{esc(legend)}</p></body></html>')


# region Actors and use cases (PRD)
USE_CASES = [
    ("icon", "chart", "Qué se movió esta semana", "Resumen semanal · alertas", "visitor"),
    ("icon", "calendar", "¿Es normal para la época?", "Precios e inflación · nominal o real", "visitor"),
    ("icon", "parity", "Consumidor frente a mayorista", "brecha de precio por canal", "visitor"),
    ("icon", "database", "Consultar con SQL", "Consultas SQL · descarga CSV", "visitor"),
    ("icon", "shield", "Revisar calidad y documentos", "Ingeniería de datos · PRD, SAD, ADR", "visitor"),
    ("icon", "gear", "Lanzar una carga manual", "Centro de operación · clave de control", "author"),
    ("icon", "files", "Mantener código y secretos", "git push · secretos del panel", "author"),
]


def build_actors_html(mode):
    palette = charts.get_palette(mode)
    width, height = 1000, 600
    rows = [95 + index * 72 for index in range(len(USE_CASES))]
    visitor, author = (95, sum(rows[:5]) / 5), (95, (rows[5] + rows[6]) / 2)
    nodes = [build_node(("person", "visitor"), *visitor, "Visitante", "analista, compras, gerencia",
                        "Abre el enlace público: no necesita cuenta ni clave.", "El panel es de solo lectura.", width=width, height=height),
             build_node(("person", "author"), *author, "El autor", "opera y mantiene el sistema",
                        "Mantiene el código, los secretos y puede lanzar una carga fuera del martes.", width=width, height=height)]
    svg = [f'<rect class="zone" x="300" y="30" width="400" height="{rows[-1] + 50 - 30}" rx="18"/>'
           f'<text class="zone-title" x="318" y="52">GREENOCEAN · PANEL Y PIPELINE</text>']
    for (kind, name, title, subtitle, actor), y in zip(USE_CASES, rows):
        nodes.append(build_node((kind, name), 345, y + 6, title, subtitle, f"Caso de uso: {title}. Dónde: {subtitle}.",
                                style="row small", width=width, height=height))
        sx, sy = visitor if actor == "visitor" else author
        color = LAYER["source"] if actor == "visitor" else LAYER["ops"]
        svg.append(f'<path class="edge" d="M{sx + 40} {sy} C {sx + 140} {sy}, {290 - 70} {y + 6}, {316} {y + 6}" stroke="{color}" '
                   f'opacity=".55" marker-end="url(#h-{color[1:]})"/>')
    systems = [(("mark", "odepa"), "ODEPA", "precios mayorista y consumidor", "CSV", LAYER["source"],
                "Publica los CSV de precios que el pipeline descarga cada martes."),
               (("mark", "ine"), "INE", "IPC de alimentos", "IPC", LAYER["source"], "Publica el índice para expresar precios reales."),
               (("brand", "github"), "GitHub Actions", "workflow semanal y de pruebas", "martes", LAYER["build"],
                "Ejecuta la carga cada martes y las pruebas en cada push."),
               (("brand", "git"), "Repositorio GitHub", "código, base e informes", "commit", LAYER["ops"],
                "Guarda el código, la base servida y los informes semanales."),
               (("brand", "streamlit"), "Streamlit Cloud", "publica el panel", "despliegue", LAYER["serve"],
                "Publica el panel cada vez que cambia la rama main.")]
    for index, (spec, title, subtitle, label, color, what) in enumerate(systems):
        y = 90 + index * 108
        nodes.append(build_node(spec, 880, y, title, subtitle, what, width=width, height=height))
        svg.append(build_edge(f"M842 {y} H708", color, label, (775, y)))
    return build_page(palette, width, height, 60, "".join(svg), "".join(nodes),
                      "Quién usa GreenOcean, para qué, y con qué sistemas se conecta. Pasa el cursor por cada logo.",
                      "Actores y casos de uso")
# endregion


# region System context (SAD, C4 level 1)
def build_context_html(mode):
    palette = charts.get_palette(mode)
    width, height = 1000, 520
    center = (500, 285)
    nodes = [
        build_node(("mark", "panel"), *center, "GreenOcean", "pipeline semanal y panel de solo lectura",
                   "Descarga los precios, los transforma y prueba con dbt, y los publica en un panel.", style="big wide",
                   width=width, height=height),
        build_node(("person", "visitor"), 380, 70, "Visitante", "analista, compras, gerencia",
                   "Consulta el panel desde el navegador, sin cuenta.", width=width, height=height),
        build_node(("person", "author"), 620, 70, "El autor", "operador", "Mantiene el código y puede lanzar una carga manual.",
                   width=width, height=height),
        build_node(("mark", "odepa"), 110, 200, "ODEPA", "datos abiertos de precios",
                   "Precios mayoristas diarios y al consumidor semanales, en CSV.", width=width, height=height),
        build_node(("mark", "ine"), 110, 380, "INE", "IPC de alimentos", "Índice mensual para deflactar los precios.",
                   width=width, height=height),
        build_node(("brand", "github"), 890, 200, "GitHub", "Actions · repositorio · issues",
                   "Corre el workflow semanal, guarda la base y publica el informe.", width=width, height=height),
        build_node(("brand", "streamlit"), 890, 380, "Streamlit Cloud", "publica el panel",
                   "Sirve el panel y guarda sus secretos.", width=width, height=height),
    ]
    svg = "".join([
        build_edge("M380 128 C 380 200, 430 228, 462 240", LAYER["source"], "HTTPS", (390, 185)),
        build_edge("M620 128 C 620 200, 570 228, 538 240", LAYER["ops"], "carga manual", (610, 185)),
        build_edge("M152 200 C 260 200, 330 250, 418 268", LAYER["source"], "CSV", (275, 220)),
        build_edge("M152 380 C 260 380, 330 320, 418 302", LAYER["source"], "IPC", (275, 360)),
        build_edge("M848 200 C 740 200, 670 250, 582 268", LAYER["build"], "workflow · commit", (725, 220), both=True),
        build_edge("M848 380 C 740 380, 670 320, 582 302", LAYER["serve"], "despliegue", (725, 360), both=True),
    ])
    return build_page(palette, width, height, 70, svg, "".join(nodes),
                      "Contexto (C4, nivel 1): GreenOcean y lo que lo rodea. Pasa el cursor por cada logo.", "Contexto del sistema")
# endregion


# region Containers (SAD, C4 level 2)
def build_containers_html(mode):
    palette = charts.get_palette(mode)
    width, height = 1200, 600
    main_y, top_y, low_y = 300, 95, 485
    columns = [70, 210, 355, 500, 645, 790, 935, 1090]
    flow = [(("mark", "odepa"), "ODEPA", "CSV por año", "Fuente externa: precios mayoristas y al consumidor."),
            (("brand", "python"), "Ingesta", "agent/agent.py", "Descarga los CSV por HTTPS y anota su huella SHA-256."),
            (("brand", "sqlite"), "Aterrizaje", "etl/raw.db", "Las filas tal como llegan. No se sube al repositorio."),
            (("brand", "apacheparquet"), "Bronce", "etl/bronze/", "Copia exacta en Parquet, por fuente y año."),
            (("brand", "dbt"), "dbt Core", "dbt/ · 16 modelos", "Staging, intermedio y marts, con sus pruebas."),
            (("brand", "duckdb"), "Base servida", "etl/datos.duckdb", "La única base que lee el panel. Se reemplaza entera."),
            (("brand", "streamlit"), "Panel", "bi/dashboard.py", "Lee la base en solo lectura."),
            (("person", "visitor"), "Visitante", "navegador", "Consulta el panel por HTTPS.")]
    nodes = [build_node(spec, x, main_y, title, sub, what, code=index not in (0, 7), width=width, height=height, suffix=f"c{index}")
             for index, ((spec, title, sub, what), x) in enumerate(zip(flow, columns))]
    labels = ["HTTPS", "CSV", "Parquet", "sources", "publica", "SQL", "HTTPS"]
    colors = [LAYER["source"], LAYER["flow"], LAYER["flow"], LAYER["build"], LAYER["build"], LAYER["serve"], LAYER["serve"]]
    svg = []
    for index, (label, color) in enumerate(zip(labels, colors)):
        left, right = columns[index] + 40, columns[index + 1] - 40
        svg.append(build_edge(f"M{left} {main_y} H{right}", color, label, ((left + right) / 2, main_y - 16)))
    # Orchestration above: the weekly workflow runs the flow and commits the base; each push runs
    # the tests, which read the base; the panel is deployed from the repository.
    nodes += [build_node(("brand", "github"), 355, top_y, "Workflow semanal", ".github/workflows/semanal.yml",
                         "Cada martes: descarga, ETL, dbt, pruebas, commit e informe.", code=True, width=width, height=height),
              build_node(("brand", "pytest"), 645, top_y, "Workflow de pruebas", ".github/workflows/pruebas.yml",
                         "En cada push: dbt parse y pytest sobre la base.", code=True, width=width, height=height),
              build_node(("brand", "git"), 935, top_y, "Repositorio", "GitHub · main",
                         "Guarda el código y la base servida; Streamlit publica desde aquí.", width=width, height=height)]
    svg += [build_edge(f"M355 145 V{main_y - 45}", LAYER["ops"], "ejecuta", (355, 195), dashed=True),
            build_edge("M400 70 C 520 22, 770 22, 890 70", LAYER["ops"], "commit", (645, 34)),
            build_edge(f"M890 {top_y} H690", LAYER["build"], "on: push", (790, top_y)),
            build_edge(f"M665 145 L772 {main_y - 40}", LAYER["build"], "pytest", (718, 195), dashed=True),
            build_edge(f"M935 145 V{main_y - 45}", LAYER["serve"], "despliegue", (935, 195))]
    # Below: the INE file joins the bronze layer directly; the SQLite backup is compared with the served base.
    nodes += [build_node(("mark", "ine"), 70, low_y, "INE", "IPC mensual", "Fuente externa: índice de precios de alimentos.",
                         width=width, height=height),
              build_node(("brand", "python"), 210, low_y, "Ingesta IPC", "etl/ine.py", "Descarga los dos CSV del IPC.",
                         code=True, width=width, height=height, suffix="ine"),
              build_node(("brand", "sqlite"), 790, low_y, "Respaldo", "etl/datos.db",
                         "ETL en Python por un camino independiente: debe dar las mismas cifras.", code=True, width=width,
                         height=height, suffix="backup")]
    svg += [build_edge(f"M110 {low_y} H170", LAYER["source"], "HTTPS", (140, low_y - 16)),
            build_edge(f"M250 {low_y} H500 V{main_y + 84}", LAYER["flow"], "directo", (380, low_y - 16)),
            build_edge(f"M790 {main_y + 84} V{low_y - 42}", LAYER["serve"], "paridad", (790, (main_y + 84 + low_y - 42) / 2), dashed=True, both=True)]
    return build_page(palette, width, height, 62, "".join(svg), "".join(nodes),
                      "Contenedores (C4, nivel 2): cada pieza que corre, con su archivo. Pasa el cursor por cada logo.",
                      "Contenedores")
# endregion


# region Weekly run as a sequence (SAD)
SEQUENCE_LANES = [
    ("actions", ("brand", "github"), "GitHub Actions", "semanal.yml", LAYER["ops"], "Ejecuta el workflow cada martes a las 12:00 UTC."),
    ("agent", ("brand", "python"), "Agente", "agent/agent.py", LAYER["flow"], "Descarga los CSV de ODEPA y valida su encabezado."),
    ("sources", ("mark", "odepa"), "ODEPA · INE", "CSV · HTTPS", LAYER["source"], "Las fuentes oficiales."),
    ("ine", ("brand", "python"), "Ingesta IPC", "etl/ine.py", LAYER["flow"], "Descarga las dos series del IPC."),
    ("pipeline", ("brand", "python"), "Orquestador", "etl/pipeline.py", LAYER["build"], "Bronce, IPC, dbt build, control de volumen y publicación."),
    ("dbt", ("brand", "dbt"), "dbt build", "dbt Core · DuckDB", LAYER["build"], "Modelos y pruebas de datos en la base de trabajo."),
    ("serving", ("brand", "duckdb"), "Base servida", "datos.duckdb", LAYER["serve"], "La base que lee el panel; se reemplaza de una vez."),
    ("pytest", ("brand", "pytest"), "Pruebas", "pytest -q", LAYER["serve"], "La suite contra la base nueva, con la paridad."),
    ("repo", ("brand", "git"), "Repositorio", "GitHub · main", LAYER["ops"], "Recibe el commit de la base y el informe."),
]
SEQUENCE_STEPS = [
    ("actions", "actions", "cron · martes 12:00 UTC", False, "Restaura de la caché los CSV de años cerrados."),
    ("actions", "agent", "python agent/agent.py", False, "Primer paso de datos."),
    ("agent", "sources", "descarga los CSV", False, "El año en curso y lo que falte en la caché."),
    ("sources", "agent", "encabezado validado", True, "Un encabezado distinto detiene el workflow."),
    ("actions", "actions", "etl/etl.py · respaldo SQLite", False, "Reconstruye raw.db y el respaldo datos.db."),
    ("actions", "pipeline", "python etl/pipeline.py", False, "La carga con dbt."),
    ("pipeline", "pipeline", "raw.db → bronce Parquet", False, "Copia literal por fuente y año."),
    ("pipeline", "ine", "actualiza el IPC", False, "Llama a etl/ine.py."),
    ("ine", "sources", "descarga el IPC", False, "Las dos series oficiales del INE."),
    ("sources", "ine", "alimentos → bronce", True, "Si el INE no responde, se usa el IPC ya publicado."),
    ("pipeline", "dbt", "dbt build", False, "Modelos y pruebas en warehouse_build.duckdb."),
    ("dbt", "pipeline", "todo en verde", True, "Si algo falla, queda en etl_run y la base no cambia."),
    ("pipeline", "pipeline", "control de volumen ≥ 90 %", False, "Menos filas que el 90 % de la última carga detiene todo."),
    ("pipeline", "serving", "reemplazo de una vez", False, "Archivo temporal y reemplazo atómico."),
    ("actions", "pytest", "pytest -q", False, "La suite completa contra la base nueva."),
    ("pytest", "serving", "lee la base · paridad", True, "Paridad entre DuckDB y el respaldo SQLite."),
    ("actions", "repo", "git commit · push", False, "datos.duckdb, datos.db y el registro de descargas."),
    ("actions", "repo", "gh issue create", False, "Publica el issue «Informe semanal»."),
]


def build_sequence_html(mode):
    palette = charts.get_palette(mode)
    first_x, spacing = 90, 145
    x_of = {lane[0]: first_x + index * spacing for index, lane in enumerate(SEQUENCE_LANES)}
    width = first_x * 2 + spacing * (len(SEQUENCE_LANES) - 1)
    head_y, first_y, step = 55, 150, 30
    last_y = first_y + step * (len(SEQUENCE_STEPS) - 1)
    height = last_y + 70
    color_of = {lane[0]: lane[4] for lane in SEQUENCE_LANES}
    nodes, svg = [], []
    for key, spec, title, subtitle, color, what in SEQUENCE_LANES:
        x = x_of[key]
        nodes.append(build_node(spec, x, head_y, title, subtitle, what, style="small", code=True, width=width,
                                height=height, suffix="s" + key))
        svg.append(f'<path d="M{x} 118 V{last_y + 14}" stroke="{color}" stroke-width="1.2" stroke-dasharray="4 5" opacity=".5"/>')
    for number, (source, target, label, back, why) in enumerate(SEQUENCE_STEPS, 1):
        y = first_y + (number - 1) * step
        x1, x2 = x_of[source], x_of[target]
        color = color_of[source]
        dash = ' stroke-dasharray="5 4"' if back else ""
        if x1 == x2:
            path, lx, anchor = f"M{x1} {y - 7} h26 v14 h-24", x1 + 34, "start"
        else:
            offset = 4 if x2 > x1 else -4
            path, lx, anchor = f"M{x1 + offset} {y} H{x2 - offset}", (x1 + x2) / 2, "middle"
        ly = y + 4 if x1 == x2 else y - 6
        svg.append(f'<g><title>{esc(why)}</title><circle cx="22" cy="{y}" r="9" fill="{color}"/><text x="22" y="{y + 4}" '
                   f'font-size="10" font-weight="700" text-anchor="middle" fill="#fff">{number}</text>'
                   f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="url(#h-{color[1:]})"/>'
                   f'<text x="{lx}" y="{ly}" font-size="11.5" text-anchor="{anchor}" fill="{palette["strong_text"]}" '
                   f'paint-order="stroke" stroke="{palette["background"]}" stroke-width="4">{esc(label)}</text></g>')
    svg.append(f'<text x="{width / 2}" y="{last_y + 48}" text-anchor="middle" font-size="12.5" font-weight="600" fill="#ef4444">'
               'Si cualquier paso falla, el workflow se detiene: no hay commit, la base publicada no cambia y GitHub avisa al autor.</text>')
    return build_page(palette, width, height, 56, "".join(svg), "".join(nodes),
                      "El martes automático, paso a paso. Pasa el cursor por un logo o por un paso.", "Secuencia del martes")
# endregion
