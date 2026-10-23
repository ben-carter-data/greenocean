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
WIDTH, HEIGHT, LOGO = 1000, 480, 76


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
.system {{ position:absolute; z-index:2; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px;
  padding:16px 26px; text-align:center; border-radius:22px; border:2px solid {palette['accent']}; background:{card};
  box-shadow:0 18px 36px {shadow}; outline:none; cursor:default; }}
.system b {{ font-size:26px; font-weight:600; letter-spacing:-.02em; color:{ink}; }}
.system span {{ font-size:13.5px; line-height:1.45; color:{text}; }}
.system:hover .tip, .system:focus .tip {{ display:block; }}
.system:hover, .system:focus {{ z-index:50; }}
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


# region Context (SAD, D-242)
# The system as one box, the people who use it and the external systems it depends on. Nothing inside the box is
# drawn here (the pipeline, the platform and the data model are the next views), and an arrow goes from the one
# that uses to the one that is used.
COLORS = {"source": "#22b35a", "flow": "#3987e5", "build": "#9085e9", "ops": "#c98500", "serve": "#199e70"}
SYSTEM_BOX = (330, 190, 340, 230)
PEOPLE_Y, SIDE_Y = 55, (225, 365)
# (kind, name, x, y, title, what it is, relation with GreenOcean)
CONTEXT_NODES = [
    ("source", "odepa", 90, SIDE_Y[0], "ODEPA", "Publica cada semana los CSV de precios mayoristas y al consumidor.",
     "GreenOcean los descarga cada martes. Es la fuente oficial y abierta de estos precios."),
    ("source", "ine", 90, SIDE_Y[1], "INE", "Publica el IPC de alimentos.",
     "GreenOcean lo descarga para expresar los precios en pesos de hoy."),
    ("brand", "github", 910, SIDE_Y[0], "GitHub", "Guarda el código, la base publicada y los informes semanales, y ejecuta la carga con Actions.",
     "GreenOcean vive ahí: cada cambio se prueba y cada martes se carga sin servidor propio."),
    ("brand", "streamlit", 910, SIDE_Y[1], "Streamlit Community Cloud", "Sirve el panel con un enlace público.",
     "GreenOcean se publica ahí desde la rama main y guarda sus secretos en esa plataforma."),
    ("person", "visitor", 430, PEOPLE_Y, "Visitante", "Analista de pricing, compras y abastecimiento, gerencia o revisor técnico.",
     "Lee el panel de solo lectura; no necesita cuenta ni clave."),
    ("person", "author", 570, PEOPLE_Y, "Administrador", "Quien mantiene el proyecto.",
     "Cambia el código y los secretos, responde consultas SQL puntuales y puede lanzar una carga manual con la clave de control."),
]
# (path, color, chip x, chip y, label, what it says)
CONTEXT_EDGES = [
    ("M330 225 H142", "source", 236, 225, "CSV", "GreenOcean descarga los archivos anuales de ODEPA, por HTTPS."),
    ("M330 365 H142", "source", 236, 365, "IPC", "GreenOcean descarga las series del IPC de alimentos del INE, por HTTPS."),
    ("M430 124 V190", "serve", 430, 157, "lee", "El visitante lee el panel por HTTPS."),
    ("M570 124 V190", "ops", 570, 157, "mantiene", "El administrador cambia el código y los secretos, y con la clave lanza una carga."),
    ("M670 225 H868", "build", 724, 225, "aloja", "GreenOcean guarda su código, la base publicada y los informes en GitHub, y GitHub Actions los ejecuta."),
    ("M670 365 H868", "flow", 724, 365, "publica", "GreenOcean publica el panel en Streamlit Community Cloud desde la rama main."),
]


def build_context_html(mode):
    """The whole system in one box, with the people who use it and the systems it depends on."""
    palette = charts.get_palette(mode)
    nodes = [build_node(kind, name, x, y, title, [("Qué es", what), ("Relación con GreenOcean", relation)])
             for kind, name, x, y, title, what, relation in CONTEXT_NODES]
    left, top, width, height = SYSTEM_BOX
    system = (f'<div class="system" tabindex="0" style="left:{left / WIDTH * 100:.3f}%;top:{top / HEIGHT * 100:.3f}%;'
              f'width:{width / WIDTH * 100:.3f}%;height:{height / HEIGHT * 100:.3f}%">'
              f'{tip_html(left + width / 2, top + height / 2, [("Qué es", "Un pipeline semanal y un panel de BI sobre los precios de alimentos de Chile."), ("Qué hace", "Integra los precios de ODEPA con el IPC del INE, revisa su calidad y publica un panel de solo lectura donde cada cifra se puede seguir hasta el archivo original.")])}'
              '<b>GreenOcean</b><span>Pipeline semanal y panel de BI sobre los precios de alimentos de Chile</span></div>')
    edges, chips = [], []
    for path, layer, x, y, label, what in CONTEXT_EDGES:
        color = COLORS[layer]
        edges.append(f'<path class="edge" d="{path}" stroke="{color}" marker-end="url(#a-{layer})"/>')
        chips.append(build_chip(x, y, label, color, [("Qué dice", what)]))
    markers = "".join(f'<marker id="a-{layer}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                      f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{color}"/></marker>' for layer, color in COLORS.items())
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body><div class="stage" aria-label="Contexto del sistema">'
            f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" aria-hidden="true"><defs>{markers}</defs>{"".join(edges)}</svg>'
            + system + "".join(nodes) + "".join(chips) + '</div><p class="legend">La flecha va de quien usa a quien es usado. '
            'Lo que hay dentro de GreenOcean está en las vistas siguientes. Pasa el cursor por cada logo y cada flecha.</p></body></html>')
# endregion


# region Use cases (PRD, D-240)
# Each case is read from the PRD: the four profiles of «3. Usuarios» with the question each one asks («4. Preguntas
# de negocio»), the administrator's duties and the automatic load (RF-01 to RF-04). The screen of each case is
# a page of the menu; the one case that is not a screen of the panel says so.
USE_CASE_ROWS = (96, 216, 336, 456)
# (actor, row, case, PRD id, screen)
USER_CASES = [
    ("Gerencia", 0, "Revisar qué se movió en la semana y qué es inusual", "P-1", "Resumen semanal"),
    ("Analista de pricing", 1, "Saber si el precio de hoy es normal para la época", "P-2", "Consultas SQL · Precio vs. época"),
    ("Compras y abastecimiento", 2, "Ver cuánto paga el consumidor sobre el mayorista", "P-3", "Consultas SQL · Brecha mayorista"),
    ("Revisor técnico", 3, "Comprobar la calidad, las pruebas, el linaje y la documentación", "", "Calidad y auditoría"),
]
SYSTEM_CASES = [
    ("GitHub Actions", 0, "Cargar y publicar cada martes", "RF-01 a RF-04", "Centro de operación"),
    ("Administrador", 1, "Responder consultas SQL puntuales", "", "Consultas SQL"),
    ("Administrador", 2, "Lanzar una carga manual con la clave de control", "", "Centro de operación"),
    ("Administrador", 3, "Mantener el código y los secretos", "", "GitHub, fuera del panel"),
]
USE_WIDTH, USE_HEIGHT = 1000, 520
LEFT_ACTOR_X, RIGHT_ACTOR_X = 66, 934
OVAL = {"left": 344, "right": 668, "rx": 126, "ry": 46}
BOUNDARY = (176, 18, 648, 484)


def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


def build_use_case(side, row, case, identifier, screen, ink, muted, accent, card):
    cx, cy = OVAL[side], USE_CASE_ROWS[row]
    lines = wrap(case, 30)
    top = cy - 6 - 8 * (len(lines) - 1)
    text = "".join(f'<text x="{cx}" y="{top + 15 * index}" text-anchor="middle" font-size="13" font-weight="600" '
                   f'fill="{ink}">{esc(line)}</text>' for index, line in enumerate(lines))
    tag = f"{identifier} · " if identifier else ""
    detail = f'<text x="{cx}" y="{top + 15 * len(lines) + 4}" text-anchor="middle" font-size="12" fill="{muted}">{esc(tag + screen)}</text>'
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{OVAL["rx"]}" ry="{OVAL["ry"]}" fill="{card}" stroke="{accent}" stroke-width="1.6"/>'
            + text + detail)


def build_use_cases_html(mode):
    """Who does what with GreenOcean: the actors of the PRD, the cases inside the system and, under each, the
    screen of the menu that serves it. Straight lines only."""
    palette = charts.get_palette(mode)
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    parts = [f'<rect x="{BOUNDARY[0]}" y="{BOUNDARY[1]}" width="{BOUNDARY[2]}" height="{BOUNDARY[3]}" rx="22" fill="none" '
             f'stroke="{border}" stroke-width="1.4" stroke-dasharray="6 6"/>'
             f'<text x="{BOUNDARY[0] + 20}" y="{BOUNDARY[1] + 26}" font-size="13" font-weight="700" letter-spacing=".1em" '
             f'fill="{ink}">GREENOCEAN</text>']
    # Left: the four profiles, each on the row of its case.
    actors = []
    for actor, row, *_ in USER_CASES:
        y = USE_CASE_ROWS[row]
        parts.append(f'<path d="M{LEFT_ACTOR_X + 32} {y} H{OVAL["left"] - OVAL["rx"]}" stroke="{accent}" stroke-width="1.8"/>')
        actors.append(f'<g>{actor_figure(LEFT_ACTOR_X, y, "visitor", actor, ink, muted)}</g>')
    # Right: GitHub Actions on its row; the administrator on the third, with a bus to his three cases.
    bus_x = RIGHT_ACTOR_X - 78
    admin_rows = [row for actor, row, *_ in SYSTEM_CASES if actor == "Administrador"]
    parts.append(f'<path d="M{OVAL["right"] + OVAL["rx"]} {USE_CASE_ROWS[0]} H{RIGHT_ACTOR_X - 32}" stroke="{accent}" stroke-width="1.8"/>')
    parts.append(f'<path d="M{bus_x} {USE_CASE_ROWS[admin_rows[0]]} V{USE_CASE_ROWS[admin_rows[-1]]}" stroke="{accent}" stroke-width="1.8"/>')
    for row in admin_rows:
        parts.append(f'<path d="M{OVAL["right"] + OVAL["rx"]} {USE_CASE_ROWS[row]} H{bus_x}" stroke="{accent}" stroke-width="1.8"/>')
    parts.append(f'<path d="M{bus_x} {USE_CASE_ROWS[2]} H{RIGHT_ACTOR_X - 32}" stroke="{accent}" stroke-width="1.8"/>')
    actors.append(f'<g>{actor_figure(RIGHT_ACTOR_X, USE_CASE_ROWS[0], "github", "GitHub Actions", ink, muted, brand=True)}</g>')
    actors.append(f'<g>{actor_figure(RIGHT_ACTOR_X, USE_CASE_ROWS[2], "author", "Administrador", ink, muted)}</g>')
    cases = [build_use_case("left", row, case, identifier, screen, ink, muted, accent, card)
             for _, row, case, identifier, screen in USER_CASES]
    cases += [build_use_case("right", row, case, identifier, screen, ink, muted, accent, card)
              for _, row, case, identifier, screen in SYSTEM_CASES]
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<style>*{{box-sizing:border-box}}html,body{{margin:0;height:100%;background:transparent;color:{text};'
            f'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}}'
            f'svg.uc{{display:block;width:100%;height:100vh}}</style></head><body>'
            f'<svg class="uc" viewBox="0 0 {USE_WIDTH} {USE_HEIGHT}" preserveAspectRatio="xMidYMid meet" role="img" '
            f'aria-label="Casos de uso">{"".join(parts)}{"".join(cases)}{"".join(actors)}</svg></body></html>')


def actor_figure(x, y, name, label, ink, muted, brand=False):
    """An actor: its mark and its name under it."""
    mark = disc_logo("brand" if brand else "person", name).replace('<svg class="logo" ', f'<svg x="{x - 30}" y="{y - 42}" width="60" height="60" ', 1)
    lines = wrap(label, 16)
    names = "".join(f'<text x="{x}" y="{y + 32 + 14 * index}" text-anchor="middle" font-size="12.5" font-weight="600" '
                    f'fill="{ink}">{esc(line)}</text>' for index, line in enumerate(lines))
    return mark + names
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
VIEWS = {"contexto": (build_context_html, 520), "casos": (build_use_cases_html, 520),
         "mockups": (build_mockups_html, 720)}
