"""The diagrams of the project documents (D-205, D-210), drawn like the pipeline: 3D logos
on lit discs, no boxes, orthogonal arrows with a chip that says what travels, and an
explanation on hover of every logo and every chip.

Each build_* function returns one HTML document for st.iframe (gradients and hover tips do
not survive st.markdown). Positions are in a fixed stage that scales with the width.
"""
import base64
import html
from pathlib import Path

from bi import brand_icons, charts, database_map

# Disc colors (light top, dark bottom, glyph) of the brands the actors view needs, as in
# database_map.BRANDS.
DISCS = dict(database_map.BRANDS, git=("#ff9b7d", "#d6402a", "#ffffff"),
             streamlit=("#ff8f98", "#e0303f", "#ffffff"))
PERSON_DISCS = {"visitor": ("#7ee2b0", "#14855a"), "author": ("#ffcf70", "#c98500")}
WIDTH, HEIGHT, LOGO = 1000, 470, 76


def esc(value):
    return html.escape(str(value))


def disc_logo(kind, name):
    """A brand, a person or a source as a 3D mark: lit disc, gloss and drop shadow."""
    if kind == "brand":
        if name in database_map.BRANDS:
            return database_map.brand_logo(name, "-actors")
        return _disc(name, *DISCS[name], brand_icons.logo_body(name))
    if kind == "source":
        return database_map.source_logo(name)
    top, bottom = PERSON_DISCS[name]
    person = ('<circle cx="18" cy="12" r="6"/><path d="M6 31c1-8 6-12 12-12s11 4 12 12z"/>')
    return _disc(name, top, bottom, "#ffffff", person, scale=1.0)


def _disc(name, top, bottom, glyph, body, scale=1.58):
    gradient = f"disc-{name}-actors"
    offset = 17 if scale > 1.2 else 18
    return (f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs>'
            f'<radialGradient id="{gradient}" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></radialGradient></defs>'
            f'<circle cx="36" cy="36" r="31" fill="url(#{gradient})"/>'
            f'<ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" opacity=".3"/>'
            f'<g fill="{glyph}" transform="translate({offset} {offset}) scale({scale})">{body}</g></svg>')


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border = (palette["strong_text"], palette["text"], palette["reference"],
                                      palette["card"], palette["card_border"])
    shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:300 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
.stage {{ position:relative; width:100%; max-width:{WIDTH}px; aspect-ratio:{WIDTH}/{HEIGHT}; margin:0 auto; }}
.stage > svg {{ position:absolute; inset:0; width:100%; height:100%; overflow:visible; }}
.edge {{ fill:none; stroke-width:2; stroke-linejoin:miter; opacity:.9; }}
.node, .chip {{ position:absolute; outline:none; }}
.node {{ width:130px; margin-left:-65px; margin-top:-{LOGO // 2}px; display:flex; flex-direction:column; align-items:center; text-align:center; }}
.logo {{ display:block; width:{LOGO}px; height:{LOGO}px; filter:drop-shadow(0 14px 12px {shadow}); transition:transform .25s ease; }}
.node:hover .logo, .node:focus .logo {{ transform:translateY(-5px) scale(1.05); }}
.node b {{ margin-top:4px; font-weight:600; font-size:14px; color:{ink}; line-height:1.2; }}
.chip {{ transform:translate(-50%,-50%); padding:2px 8px; border-radius:7px; background:{card}; border:1px solid currentColor;
  font:700 11.5px/1.35 ui-monospace, SFMono-Regular, Menlo, monospace; white-space:nowrap; cursor:default; }}
.tip {{ position:absolute; z-index:40; left:50%; top:calc(100% + 8px); width:260px; padding:10px 12px; border-radius:12px; text-align:left;
  background:{card}; border:1px solid {border}; box-shadow:0 18px 40px rgba(0,0,0,{'.5' if dark else '.18'}); color:{text};
  font:400 12.5px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; white-space:normal; display:none; pointer-events:none; transform:translateX(-50%); }}
.tip i {{ display:block; margin:7px 0 2px; font:500 10px/1 sans-serif; font-style:normal; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip i:first-child {{ margin-top:0; }}
.tip.start {{ left:0; transform:none; }} .tip.end {{ left:auto; right:0; transform:none; }} .tip.up {{ top:auto; bottom:calc(100% + 8px); }}
.node:hover .tip, .node:focus .tip, .chip:hover .tip, .chip:focus .tip {{ display:block; }}
.node:hover, .node:focus, .chip:hover, .chip:focus {{ z-index:50; }}
.legend {{ margin:2px 4px 0; font-size:11.5px; color:{muted}; text-align:center; }}
</style>"""


def tip_html(x, y, parts):
    side = " start" if x < WIDTH * .2 else " end" if x > WIDTH * .8 else ""
    up = " up" if y > HEIGHT * .6 else ""
    return (f'<span class="tip{side}{up}" role="tooltip">'
            + "".join(f"<i>{esc(head)}</i>{esc(text)}" for head, text in parts) + "</span>")


def build_node(kind, name, x, y, title, parts):
    return (f'<div class="node" tabindex="0" style="left:{x / WIDTH * 100:.3f}%;top:{y / HEIGHT * 100:.3f}%">'
            f'{tip_html(x, y, parts)}{disc_logo(kind, name)}<b>{esc(title)}</b></div>')


def build_chip(x, y, label, color, parts):
    return (f'<span class="chip" tabindex="0" style="left:{x / WIDTH * 100:.3f}%;top:{y / HEIGHT * 100:.3f}%;color:{color}">'
            f'{esc(label)}{tip_html(x, y, parts)}</span>')


# region Actors and use cases (PRD)
USE_CASES = {
    "visitor": ["Qué se movió esta semana (Resumen semanal)", "¿Es normal para la época? (Precios e inflación)",
                "Consumidor frente a mayorista (brecha por canal)", "Revisar calidad y documentos"],
    "author": ["Consultas SQL a pedido, respondidas con un CSV", "Lanzar una carga manual con la clave de control",
               "Mantener el código y los secretos"],
}
ROW_TOP, ROW_MID, ROW_LOW, ROW_ROUTE = 110, 225, 340, 440
COLUMNS = (90, 300, 500, 700, 910)
COLORS = {"source": "#22b35a", "flow": "#3987e5", "build": "#9085e9", "ops": "#c98500", "serve": "#199e70"}
# (kind, name, column, row, title, what, why)
ACTOR_NODES = [
    ("source", "odepa", 0, ROW_TOP, "ODEPA", "Publica los CSV de precios mayoristas y al consumidor.",
     "Es la fuente oficial y abierta de estos precios."),
    ("source", "ine", 0, ROW_LOW, "INE", "Publica el IPC de alimentos.", "Permite expresar los precios en pesos de hoy."),
    ("brand", "github", 1, ROW_MID, "GitHub Actions", "Ejecuta el pipeline cada martes y las pruebas en cada push.",
     "Orquestación gratuita, sin servidor que mantener."),
    ("brand", "git", 2, ROW_MID, "Repositorio", "Guarda el código, la base servida y los informes semanales.",
     "Es la fuente de verdad del proyecto."),
    ("brand", "streamlit", 3, ROW_MID, "Panel", "Publica el panel de solo lectura desde la rama main.",
     "Streamlit Community Cloud lo sirve con un enlace público."),
]
# (path, color, chip x, chip y, label, what travels)
ACTOR_EDGES = [
    ("M128 110 H205 V210 H255", "source", 167, 110, "CSV", "Los archivos anuales de ODEPA, descargados por HTTPS."),
    ("M128 340 H205 V240 H255", "source", 167, 340, "IPC", "Las series del IPC de alimentos del INE, por HTTPS."),
    ("M345 225 H455", "build", 400, 225, "commit", "La base servida y el informe de la semana, si todo pasó."),
    ("M545 225 H655", "ops", 600, 225, "main", "Cada cambio de main vuelve a publicar el panel."),
    ("M745 210 H790 V110 H865", "serve", 828, 110, "HTTPS", "El visitante lee el panel; no necesita cuenta ni clave."),
    ("M865 340 H790 V240 H745", "ops", 828, 340, "clave", "Con la clave de control, el autor lanza una carga manual."),
    ("M910 405 V440 H500 V292", "ops", 705, 440, "git push", "El autor cambia el código y los secretos del panel."),
]


def build_actors_html(mode):
    """Who uses GreenOcean and the systems it depends on, read from left to right."""
    palette = charts.get_palette(mode)
    nodes = [build_node(kind, name, COLUMNS[column], row, title, [("Qué hace", what), ("Por qué", why)])
             for kind, name, column, row, title, what, why in ACTOR_NODES]
    for person, row, title in (("visitor", ROW_TOP, "Visitante"), ("author", ROW_LOW, "El autor")):
        nodes.append(build_node("person", person, COLUMNS[4], row, title,
                                [("Para qué usa el panel", " · ".join(USE_CASES[person]))]))
    edges, chips = [], []
    for path, layer, x, y, label, what in ACTOR_EDGES:
        color = COLORS[layer]
        edges.append(f'<path class="edge" d="{path}" stroke="{color}" marker-end="url(#a-{layer})"/>')
        chips.append(build_chip(x, y, label, color, [("Qué viaja", what)]))
    markers = "".join(f'<marker id="a-{layer}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                      f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{color}"/></marker>' for layer, color in COLORS.items())
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body><div class="stage" aria-label="Actores y sistemas">'
            f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" aria-hidden="true"><defs>{markers}</defs>{"".join(edges)}</svg>'
            + "".join(nodes) + "".join(chips) + '</div><p class="legend">Quién usa GreenOcean y de qué sistemas depende. '
            'Pasa el cursor por cada logo y cada flecha.</p></body></html>')
# endregion


MOCKUP_DIR = Path(__file__).resolve().parent.parent / "docs" / "img"
MOCKUPS = [
    ("m1-resumen-vantablack.jpg", "M-1 · Resumen semanal", "tema Vantablack · computador", "laptop"),
    ("m2-precios-claro.jpg", "M-2 · Precios e inflación", "tema Claro · computador", "laptop"),
    ("m3-sql-corporativo.jpg", "M-3 · Consultas SQL", "tema Corporativo · computador", "laptop"),
    ("m4-telefono-bluelight.jpg", "M-4 · Resumen semanal", "tema Blue Light · teléfono horizontal", "phone"),
]


def build_mockups_html(mode):
    """The four captures in a computer or phone frame, two per row."""
    palette = charts.get_palette(mode)
    figures = []
    for file_name, title, detail, device in MOCKUPS:
        data = base64.b64encode((MOCKUP_DIR / file_name).read_bytes()).decode()
        image = f'<img src="data:image/jpeg;base64,{data}" alt="{esc(title)}">'
        frame = (f'<div class="screen">{image}</div><div class="base"></div>' if device == "laptop"
                 else f'<div class="phone">{image}</div>')
        figures.append(f'<figure class="{device}">{frame}<figcaption><b>{esc(title)}</b> · {esc(detail)}</figcaption></figure>')
    css = f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; font:300 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:{palette['text']}; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:26px 30px; align-items:end; padding:6px 4px; }}
figure {{ margin:0; text-align:center; }}
figcaption {{ margin-top:10px; color:{palette['reference']}; }} figcaption b {{ color:{palette['strong_text']}; font-weight:500; }}
.screen {{ width:88%; margin:0 auto; border:9px solid #1d2229; border-bottom-width:11px; border-radius:12px 12px 3px 3px;
  background:#000; box-shadow:0 22px 40px rgba(0,0,0,.45); }}
.screen img {{ display:block; width:100%; }}
.base {{ width:100%; height:11px; background:linear-gradient(#c3c9d2,#7d8590); border-radius:0 0 14px 14px; }}
.phone {{ width:92%; margin:0 auto; padding:9px 26px; background:#111418; border:2px solid #2f353d; border-radius:34px;
  box-shadow:0 22px 40px rgba(0,0,0,.45); }}
.phone img {{ display:block; width:100%; border-radius:18px; }}
@media (max-width:640px) {{ .grid {{ grid-template-columns:1fr; }} }}
</style>"""
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + css + '</head><body><div class="grid">' + "".join(figures) + "</div></body></html>")
# endregion

# The document views by marker, with the height of their frame in the page.
VIEWS = {"actores": (build_actors_html, 500), "mockups": (build_mockups_html, 720)}
