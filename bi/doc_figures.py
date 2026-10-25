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
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
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
    return (f'<!doctype html><html lang="{i18n.get_language()}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">{css}</head>'
            f'<body><div class="fig" role="img" aria-label="{esc(label)}">{body}</div></body></html>')


def logo(mark, x, y, size=30):
    """A flat logo (brand, person or source) placed in an SVG."""
    kind, name = mark.split(":")
    svg = doc_views.flat_logo(kind, name)
    return svg.replace('<svg class="logo" ', f'<svg x="{x - size / 2:.1f}" y="{y - size / 2:.1f}" width="{size}" height="{size}" ', 1)


# region Builders
def sequence(mode, title, actors, steps, note=""):
    """A sequence diagram: the actors along the top, their lifelines, and each step as an arrow in order.

    actors: [(key, label, mark)]; steps: [(from, to, label, kind)] with kind flow, back, check, order or stop;
    a step whose from is «gate» is a band across the lifelines (a gate that can stop the sequence)."""
    width, top, row, margin = 920, 78, 40, 34
    gap = (width - margin) / len(actors)
    x = {key: margin + gap * (index + .5) for index, (key, _, _) in enumerate(actors)}
    height = top + 20 + row * len(steps) + 10
    parts = []
    for key, label, mark in actors:
        cx = x[key]
        parts.append(f'<rect class="box" x="{cx - gap / 2 + 6:.1f}" y="2" width="{gap - 12:.1f}" height="64" rx="12"/>')
        parts.append(logo(mark, cx, 22, 26))
        parts.append(f'<text class="ink" x="{cx:.1f}" y="54" text-anchor="middle" font-size="12.5" font-weight="600">{esc(label)}</text>')
        parts.append(f'<line class="life" x1="{cx:.1f}" y1="68" x2="{cx:.1f}" y2="{height:.1f}"/>')
    number = 0
    for index, (source, target, label, kind) in enumerate(steps):
        y = top + 26 + row * index
        if source == "gate":
            parts.append(f'<rect class="gate" x="12" y="{y - 15}" width="{width - 24}" height="30" rx="8"/>')
            parts.append(f'<text x="{width / 2}" y="{y + 4}" text-anchor="middle" font-size="12.5" font-weight="600" '
                         f'fill="#e5484d">{esc(label)}</text>')
            continue
        number += 1
        color = KIND_COLORS[kind]
        dash = ' stroke-dasharray="6 5"' if kind == "back" else ""
        x1, x2 = x[source], x[target]
        # The number of the step sits in its own column on the left, so it never covers a label.
        parts.append(f'<circle cx="14" cy="{y}" r="10" fill="{color}"/><text x="14" y="{y + 4}" text-anchor="middle" '
                     f'font-size="10.5" font-weight="700" fill="#fff">{number}</text>'
                     f'<line x1="26" y1="{y}" x2="{min(x1, x2) - 4:.1f}" y2="{y}" stroke="{color}" stroke-opacity=".18" stroke-width="1"/>')
        if x1 == x2:
            parts.append(f'<path d="M{x1 + 4} {y - 8} h28 v16 h-26" fill="none" stroke="{color}" stroke-width="1.8"{dash} '
                         f'marker-end="url(#h-{kind})"/>')
            # On the right half, the label goes to the left of the loop, so it stays inside the figure.
            side = (f'x="{x1 + 38}" text-anchor="start"' if x1 < width * .6 else f'x="{x1 - 8}" text-anchor="end"')
            parts.append(f'<text class="txt" {side} y="{y + 4}" font-size="12">{esc(label)}</text>')
        else:
            direction = 1 if x2 > x1 else -1
            parts.append(f'<line x1="{x1 + 6 * direction:.1f}" y1="{y}" x2="{x2 - 8 * direction:.1f}" y2="{y}" stroke="{color}" '
                         f'stroke-width="1.8"{dash} marker-end="url(#h-{kind})"/>')
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
    markers = "".join(f'<marker id="h-{kind}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                      f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{color}"/></marker>' for kind, color in KIND_COLORS.items())
    body = (f'<p class="fig-title">{esc(title)}</p><svg viewBox="0 0 {width} {height:.0f}" aria-hidden="true">'
            f'<defs>{markers}</defs>{"".join(parts)}</svg>' + (f'<p class="fig-note">{esc(note)}</p>' if note else ""))
    return page(mode, body, title)


def columns(mode, title, cols, note="", arrows=True):
    """Columns left to right, each with its color and its items: [(heading, color, [(name, detail)])]."""
    template = " auto ".join(["minmax(0, 1fr)"] * len(cols)) if arrows else f"repeat({len(cols)}, minmax(0, 1fr))"
    cells = []
    for index, (heading, color, items) in enumerate(cols):
        if index and arrows:
            cells.append('<div class="arrow" aria-hidden="true">→</div>')
        content = "".join(f'<div class="item"><b>{esc(name)}</b>{f"<span>{esc(detail)}</span>" if detail else ""}</div>'
                          for name, detail in items)
        cells.append(f'<div class="col" style="--c:{color}"><h4>{esc(heading)}</h4>{content}</div>')
    body = (f'<p class="fig-title">{esc(title)}</p><div class="cols" style="grid-template-columns:{template}">'
            + "".join(cells) + "</div>" + (f'<p class="fig-note">{esc(note)}</p>' if note else ""))
    return page(mode, body, title)


def timeline(mode, title, events, note=""):
    """A horizontal timeline: [(date, heading, [lines])], evenly spaced."""
    width = 920
    gap = width / len(events)
    height = 70 + 22 * max(len(lines) for _, _, lines in events) + 20
    parts = [f'<line x1="10" y1="40" x2="{width - 10}" y2="40" stroke="#3987e5" stroke-width="2.5"/>']
    for index, (date, heading, lines) in enumerate(events):
        cx = gap * (index + .5)
        parts.append(f'<circle cx="{cx:.1f}" cy="40" r="8" fill="#3987e5"/><circle cx="{cx:.1f}" cy="40" r="3.5" fill="#fff"/>')
        parts.append(f'<text class="mut" x="{cx:.1f}" y="22" text-anchor="middle" font-size="12" font-weight="600">{esc(date)}</text>')
        parts.append(f'<text class="ink" x="{cx:.1f}" y="68" text-anchor="middle" font-size="13" font-weight="700">{esc(heading)}</text>')
        for line_index, line in enumerate(lines):
            parts.append(f'<text class="txt" x="{cx:.1f}" y="{90 + 20 * line_index}" text-anchor="middle" font-size="12">{esc(line)}</text>')
    body = (f'<p class="fig-title">{esc(title)}</p><svg viewBox="0 0 {width} {height}" aria-hidden="true">{"".join(parts)}</svg>'
            + (f'<p class="fig-note">{esc(note)}</p>' if note else ""))
    return page(mode, body, title)


def tree(mode, title, root, branches, note=""):
    """A fault tree: the root on the left; each branch «if … → then …»."""
    rows = "".join(f'<div class="branch"><div class="when">{esc(condition)}</div><div class="then"><b>{esc(action)}</b>'
                   f'{f"<br>{esc(detail)}" if detail else ""}</div></div>' for condition, action, detail in branches)
    body = (f'<p class="fig-title">{esc(title)}</p><div class="tree"><div class="root">{esc(root)}</div>'
            f'<div class="branches">{rows}</div></div>' + (f'<p class="fig-note">{esc(note)}</p>' if note else ""))
    return page(mode, body, title)


def bars(mode, title, rows, note=""):
    """Horizontal bars: [(label, value, color)]."""
    top = max(value for _, value, _ in rows) or 1
    cells = "".join(f'<b>{esc(label)}</b><div class="bar" style="--c:{color};width:{value / top * 100:.1f}%"></div>'
                    f'<em>{value}</em>' for label, value, color in rows)
    body = (f'<p class="fig-title">{esc(title)}</p><div class="bars">{cells}</div>'
            + (f'<p class="fig-note">{esc(note)}</p>' if note else ""))
    return page(mode, body, title)


def compare(mode, title, before, after, note=""):
    """Before and after: two columns and an arrow between them: (heading, color, [(name, detail)])."""
    def panel(heading, color, items):
        content = "".join(f'<div class="item"><b>{esc(name)}</b><span>{esc(detail)}</span></div>' for name, detail in items)
        return f'<div class="col" style="--c:{color}"><h4>{esc(heading)}</h4>{content}</div>'
    body = (f'<p class="fig-title">{esc(title)}</p><div class="compare">{panel(*before)}'
            f'<div class="arrow" aria-hidden="true">→</div>{panel(*after)}</div>'
            + (f'<p class="fig-note">{esc(note)}</p>' if note else ""))
    return page(mode, body, title)
# endregion


BLUE, GREEN, AMBER, VIOLET, RED, GREY = "#3987e5", "#199e70", "#c98500", "#8b5cf6", "#e5484d", "#8b8fa3"


# region PRD
def prd_value(mode):
    return columns(mode, say("Del dato a la decisión", "From data to decision"), [
        (say("Fuentes oficiales", "Official sources"), GREEN,
         [("ODEPA", say("precios mayoristas y al consumidor, cada semana", "wholesale and consumer prices, every week")),
          ("INE", say("IPC de alimentos, cada mes", "food CPI, every month"))]),
        (say("GreenOcean", "GreenOcean"), BLUE,
         [(say("Carga semanal", "Weekly load"), say("descarga, limpia y calcula cada martes", "downloads, cleans and computes every Tuesday")),
          (say("Puertas de calidad", "Quality gates"), say("nada se publica si algo falla", "nothing is published if something fails"))]),
        (say("Panel", "Panel"), VIOLET,
         [("P-1", say("¿qué cambió esta semana?", "what changed this week?")),
          ("P-2 · P-3", say("¿es normal el precio? ¿cuánto se paga sobre el mayorista?", "is the price normal? how much over wholesale?")),
          ("P-4 · P-5", say("¿qué subió más que la inflación? ¿son confiables las cifras?", "what rose more than inflation? are the figures reliable?"))]),
        (say("Decisiones", "Decisions"), AMBER,
         [(say("Pricing", "Pricing"), say("precio de hoy frente a la época y la inflación", "today's price against the season and inflation")),
          (say("Compras", "Purchasing"), say("margen entre mayorista y consumidor", "margin between wholesale and consumer")),
          (say("Gerencia", "Management"), say("qué se movió y qué es inusual", "what moved and what is unusual"))]),
    ], say("Cada cifra del panel se puede seguir hasta el archivo original de la fuente.",
           "Every figure of the panel can be traced back to the original file of the source."))


def prd_requirements(mode):
    return columns(mode, say("Los requisitos, por área", "The requirements, by area"), [
        (say("Carga", "Load"), BLUE, [("RF-01", say("cada martes, sola", "every Tuesday, by itself")),
                                      ("RF-02", say("ninguna fila se pierde", "no row is lost")),
                                      ("RF-03", say("solo se publica una carga válida", "only a valid load is published"))]),
        (say("Datos", "Data"), GREEN, [("RF-04", say("precios reales junto a los nominales", "real prices next to nominal ones")),
                                       ("RF-05", say("alertas de cambios inusuales", "alerts on unusual changes")),
                                       ("RNF-02", say("cada cifra se puede comprobar", "every figure can be checked"))]),
        (say("Panel", "Panel"), VIOLET, [("RF-06", say("SQL abierto y de solo lectura", "open, read-only SQL")),
                                         ("RF-08", say("informe semanal", "weekly report")),
                                         ("RNF-05 · RNF-06", say("legible en todo tamaño, en una pantalla", "readable at any size, on one screen"))]),
        (say("Seguridad y costo", "Security and cost"), AMBER, [("RF-07", say("carga manual protegida con clave", "manual load protected by a code")),
                                                               ("RNF-03", say("ningún secreto en el repositorio", "no secret in the repository")),
                                                               ("RNF-01 · RNF-04", say("costo cero; calidad vigilada en cada cambio", "zero cost; quality watched on every change"))]),
    ], arrows=False)
# endregion


# region SAD
def sad_weekly_sequence(mode):
    return sequence(mode, say("Secuencia de la carga semanal", "Sequence of the weekly load"), [
        ("actions", "GitHub Actions", "brand:github"), ("agent", say("Agente", "Agent"), "brand:python"),
        ("sources", "ODEPA · INE", "source:odepa"), ("etl", "SQLite · Parquet", "brand:sqlite"),
        ("dbt", "dbt · DuckDB", "brand:dbt"), ("tests", "pytest", "brand:pytest"),
        ("release", say("Release y main", "Release and main"), "brand:git"),
    ], [
        ("actions", "agent", say("martes 12:00 UTC: inicia", "Tuesday 12:00 UTC: starts"), "order"),
        ("agent", "sources", say("descarga los CSV y el IPC", "downloads the CSV files and the CPI"), "flow"),
        ("sources", "agent", say("archivos + huella SHA-256", "files + SHA-256 fingerprint"), "back"),
        ("agent", "etl", say("filas crudas → raw.db y bronce", "raw rows → raw.db and bronze"), "flow"),
        ("etl", "dbt", say("dbt build sobre el bronce", "dbt build on bronze"), "flow"),
        ("dbt", "dbt", say("modelos y pruebas de datos", "models and data tests"), "check"),
        ("gate", "", say("Puerta de publicación: si una prueba falla o la carga lee menos del 90 %, se detiene aquí",
                         "Publication gate: if a test fails or the load reads less than 90 %, it stops here"), "stop"),
        ("dbt", "tests", say("base nueva", "new database"), "flow"),
        ("tests", "tests", say("pytest y paridad con el respaldo", "pytest and parity with the backup"), "check"),
        ("tests", "release", say("publica datos.duckdb en «base-actual»", "publishes datos.duckdb in «base-actual»"), "flow"),
        ("release", "actions", say("puntero a main · informe semanal", "pointer to main · weekly report"), "back"),
    ], say("Si un paso falla, los siguientes no corren y la base publicada no cambia.",
           "If a step fails, the following ones do not run and the published database does not change."))


def sad_panel_sequence(mode):
    return sequence(mode, say("Secuencia al abrir el panel", "Sequence when the panel opens"), [
        ("visitor", say("Visitante", "Visitor"), "person:visitor"), ("panel", "Streamlit", "brand:streamlit"),
        ("main", say("Puntero en main", "Pointer on main"), "brand:git"), ("release", "Release", "brand:github"),
        ("duckdb", "DuckDB", "brand:duckdb"),
    ], [
        ("visitor", "panel", say("abre una página", "opens a page"), "flow"),
        ("panel", "main", say("lee etl/datos.version", "reads etl/datos.version"), "flow"),
        ("main", "panel", say("huella, tamaño y fecha", "fingerprint, size and date"), "back"),
        ("panel", "release", say("si la base local es más antigua: descarga", "if the local database is older: downloads"), "flow"),
        ("release", "panel", "datos.duckdb", "back"),
        ("panel", "panel", say("comprueba la huella SHA-256", "checks the SHA-256 fingerprint"), "check"),
        ("panel", "duckdb", say("consulta en solo lectura", "queries read-only"), "flow"),
        ("duckdb", "panel", say("filas", "rows"), "back"),
        ("panel", "visitor", say("la página con sus cifras", "the page with its figures"), "back"),
    ], say("Si GitHub no responde, el panel sigue con la base que ya tiene.",
           "If GitHub does not respond, the panel goes on with the database it already has."))


def sad_layers(mode):
    return columns(mode, say("Capas de los datos", "Data layers"), [
        (say("Aterrizaje", "Landing"), GREY, [("etl/raw.db", say("las filas de ODEPA tal como llegan (SQLite)", "the ODEPA rows as they arrive (SQLite)"))]),
        (say("Bronce", "Bronze"), AMBER, [("etl/bronze/", say("copia literal en Parquet, por fuente y año", "literal copy in Parquet, by source and year"))]),
        (say("Plata", "Silver"), BLUE, [("staging", say("tipos y textos de cada fuente", "types and text of each source")),
                                        (say("intermedio", "intermediate"), say("reglas de negocio, semanas, rechazos y marcas", "business rules, weeks, rejections and flags"))]),
        (say("Oro", "Gold"), GREEN, [("marts", say("el modelo estrella, el IPC y la auditoría", "the star schema, the CPI and the audit")),
                                     ("etl/datos.duckdb", say("la base servida que lee el panel", "the served database the panel reads"))]),
    ], say("El respaldo etl/datos.db calcula los mismos precios sin dbt, para la prueba de paridad.",
           "The backup etl/datos.db computes the same prices without dbt, for the parity test."))


def sad_deployment(mode):
    return columns(mode, say("Dónde corre cada pieza", "Where each piece runs"), [
        (say("Computador del autor", "The author's computer"), GREY,
         [(say("Desarrollo", "Development"), say("el código y las pruebas antes de cada push", "the code and the tests before each push")),
          ("etl/raw.db", say("el aterrizaje, fuera de git", "the landing database, outside git"))]),
        ("GitHub", BLUE,
         [(say("Repositorio, rama main", "Repository, main branch"), say("el código y el puntero de la base", "the code and the database pointer")),
          (say("Release «base-actual»", "«base-actual» release"), say("una sola copia de la base servida", "a single copy of the served database"))]),
        ("GitHub Actions", AMBER,
         [(say("Máquina efímera (Ubuntu)", "Ephemeral machine (Ubuntu)"), say("la carga de cada martes y las pruebas de cada push", "each Tuesday's load and each push's tests")),
          (say("Caché", "Cache"), say("los CSV de los años cerrados", "the CSV files of the closed years"))]),
        ("Streamlit Community Cloud", RED,
         [(say("Panel", "Panel"), say("publicado desde main, en solo lectura", "published from main, read-only")),
          (say("Secretos", "Secrets"), say("el token de GitHub y la clave de control", "the GitHub token and the control code"))]),
    ], arrows=False)
# endregion


# region ADR
def adr_map(mode):
    return columns(mode, say("Dónde actúa cada decisión", "Where each decision acts"), [
        (say("Fuentes", "Sources"), GREEN, [("ADR-01", say("solo archivos oficiales", "only official files"))]),
        (say("Carga", "Load"), BLUE, [("ADR-04", say("datos crudos fuera del repositorio", "raw data outside the repository")),
                                      ("ADR-10", say("rehacer todo en cada carga", "rebuild everything on each load")),
                                      ("ADR-11", say("publicar solo si pasan las pruebas", "publish only if the tests pass"))]),
        (say("Datos", "Data"), VIOLET, [("ADR-19", say("modelo estrella", "star schema")),
                                        ("ADR-30", say("Parquet, dbt y DuckDB", "Parquet, dbt and DuckDB")),
                                        ("ADR-33", say("precios reales con el IPC", "real prices with the CPI")),
                                        ("ADR-34", say("tres bases separadas", "three separate databases"))]),
        (say("Publicación y costo", "Publication and cost"), AMBER, [("ADR-02", say("GitHub Actions y Streamlit Cloud", "GitHub Actions and Streamlit Cloud")),
                                                                    ("ADR-31", say("sin nube de pago", "no paid cloud")),
                                                                    ("ADR-35", say("la base en un release", "the database in a release"))]),
    ])


def adr_timeline(mode):
    return timeline(mode, say("Cuándo se tomó cada decisión", "When each decision was taken"), [
        ("11-10-2026" if not i18n.is_english() else "2026-10-11", say("Primera versión", "First version"),
         ["ADR-01 · ADR-02 · ADR-04", "ADR-10 · ADR-11 · ADR-19"]),
        ("19-10-2026" if not i18n.is_english() else "2026-10-19", say("Data warehouse con dbt", "Data warehouse with dbt"),
         ["ADR-30 · ADR-31", "ADR-33 · ADR-34"]),
        ("24-10-2026" if not i18n.is_english() else "2026-10-24", say("Base en un release", "Database in a release"),
         ["ADR-35"]),
    ])


def adr_before_after(mode):
    return compare(mode, say("ADR-35: la base servida, antes y después", "ADR-35: the served database, before and after"),
                   (say("Antes", "Before"), RED,
                    [(say("Cada carga hacía un commit de la base", "Each load committed the database"), say("unos 48 MB por carga", "about 48 MB per load")),
                     (say("Git guardaba cada versión", "Git kept every version"), say("cerca de 1 GB más por año", "about 1 GB more per year"))]),
                   (say("Después", "After"), GREEN,
                    [(say("Un release reemplazado por cada carga", "A release replaced by each load"), say("una sola copia publicada", "a single published copy")),
                     (say("Git guarda solo el puntero", "Git keeps only the pointer"), say("huella, tamaño y fecha", "fingerprint, size and date"))]),
                   say("Medidas del 24-10-2026.", "Measurements of 2026-10-24."))
# endregion


# region Test plan (with security)
def tests_levels(mode):
    return columns(mode, say("Qué se prueba y cuándo", "What is tested and when"), [
        (say("En cada carga", "On each load"), BLUE,
         [(say("Pruebas de dbt", "dbt tests"), say("claves, valores, relaciones y conciliación", "keys, values, relationships and reconciliation")),
          (say("Puerta de publicación", "Publication gate"), say("no publica una carga incompleta", "does not publish an incomplete load")),
          (say("Paridad", "Parity"), say("dbt y el ETL en Python dan lo mismo", "dbt and the Python ETL give the same"))]),
        (say("En cada push", "On every push"), GREEN,
         [(say("Auditoría de cifras", "Figure audit"), say("cada cifra se recalcula desde la fuente", "each figure is recomputed from the source")),
          (say("Panel", "Panel"), say("cada página se dibuja sin errores", "each page draws without errors")),
          (say("Seguridad", "Security"), say("los diez ataques S-01 a S-10", "the ten attacks S-01 to S-10"))]),
        (say("Antes de un cambio visual", "Before a visual change"), AMBER,
         [(say("Medición de pantallas", "Screen measurement"), say("cada página en una pantalla", "each page on one screen")),
          (say("Impresión", "Printing"), say("cada documento impreso igual a su página", "each printed document equal to its page"))]),
    ], arrows=False)


def tests_manual_sequence(mode):
    return sequence(mode, say("Secuencia de una carga manual con la clave", "Sequence of a manual load with the code"), [
        ("author", say("Autor", "Author"), "person:author"), ("panel", say("Panel", "Panel"), "brand:streamlit"),
        ("secrets", say("Secretos", "Secrets"), "brand:streamlit"), ("api", say("API de GitHub", "GitHub API"), "brand:github"),
        ("workflow", "semanal.yml", "brand:github"),
    ], [
        ("author", "panel", say("escribe la clave de control", "types the control code"), "flow"),
        ("panel", "secrets", say("lee CONTROL_CODE", "reads CONTROL_CODE"), "flow"),
        ("panel", "panel", say("compara en tiempo constante", "compares in constant time"), "check"),
        ("gate", "", say("Clave incorrecta: «Clave incorrecta.» y el botón no aparece", "Wrong code: «Clave incorrecta.» and the button does not appear"), "stop"),
        ("panel", "author", say("aparece «Ejecutar pipeline ahora»", "«Run pipeline now» appears"), "back"),
        ("author", "panel", say("clic", "click"), "flow"),
        ("panel", "secrets", say("lee el token, que nunca se muestra", "reads the token, which is never shown"), "flow"),
        ("panel", "api", "workflow_dispatch", "order"),
        ("api", "workflow", say("inicia la carga", "starts the load"), "order"),
        ("workflow", "panel", say("estado de cada paso", "status of each step"), "back"),
        ("panel", "author", say("progreso en el Centro de operación", "progress in the Operations center"), "back"),
    ], say("El workflow solo puede escribir contenido y crear issues: permisos mínimos.",
           "The workflow can only write content and create issues: least privilege."))


def tests_ci_sequence(mode):
    return sequence(mode, say("Secuencia de un cambio de código", "Sequence of a code change"), [
        ("author", say("Autor", "Author"), "person:author"), ("repo", say("GitHub, main", "GitHub, main"), "brand:git"),
        ("ci", "pruebas.yml", "brand:pytest"), ("cloud", "Streamlit Cloud", "brand:streamlit"),
    ], [
        ("author", "author", say("pruebas en su computador", "tests on their computer"), "check"),
        ("author", "repo", "git push", "flow"),
        ("repo", "ci", say("lanza pruebas.yml", "launches pruebas.yml"), "order"),
        ("ci", "ci", say("dbt parse y pytest", "dbt parse and pytest"), "check"),
        ("ci", "repo", say("verde o rojo junto al commit", "green or red next to the commit"), "back"),
        ("repo", "cloud", say("despliega main", "deploys main"), "flow"),
    ], say("El resultado avisa, pero no detiene el despliegue: un riesgo aceptado y declarado.",
           "The result warns, but it does not stop the deployment: an accepted and declared risk."))


def tests_actors(mode):
    return columns(mode, say("Quién participa en la seguridad", "Who takes part in security"), [
        (say("Visitante", "Visitor"), GREEN, [(say("Sin cuenta", "No account"), say("lee el panel y usa el SQL de solo lectura", "reads the panel and uses read-only SQL"))]),
        (say("Autor", "Author"), AMBER, [(say("Clave de control", "Control code"), say("abre el botón de la carga manual", "opens the manual load button")),
                                         (say("Inicio de sesión", "Sign-in"), say("GitHub y Streamlit, con dos pasos", "GitHub and Streamlit, two-step"))]),
        ("Streamlit", RED, [(say("Secretos del panel", "Panel secrets"), say("token y clave, fuera del código", "token and code, outside the code")),
                            (say("Base en solo lectura", "Read-only database"), say("ninguna página cambia un dato", "no page changes a value"))]),
        ("GitHub", BLUE, [(say("Repositorio público", "Public repository"), say("sin ningún secreto", "with no secret")),
                          (say("Workflow con permisos mínimos", "Workflow with least privilege"), say("solo contenido e issues", "only content and issues"))]),
    ], arrows=False)
# endregion


# region Runbook
def manual_fault_tree(mode):
    return tree(mode, say("Qué hacer cuando algo falla", "What to do when something fails"),
                say("Llegó el correo «Run failed» o un paso está en rojo", "The «Run failed» email arrived or a step is red"), [
        (say("Falló la descarga de ODEPA", "The ODEPA download failed"), say("Esperar unas horas y volver a lanzar", "Wait a few hours and launch again"),
         say("Con UNEXPECTED_HEADER, revisar el archivo y adaptar el agente.", "With UNEXPECTED_HEADER, check the file and adapt the agent.")),
        (say("Falló el ETL de respaldo", "The backup ETL failed"), say("Revisar el archivo en ODEPA", "Check the file at ODEPA"),
         say("Una región o un canal nuevos se agregan a las listas del ETL.", "A new region or channel is added to the lists of the ETL.")),
        (say("Falló dbt o TOO_FEW_ROWS", "dbt or TOO_FEW_ROWS failed"), say("Leer en el log qué modelo o prueba falló", "Read in the log which model or test failed"),
         say("Suele nombrar la tabla y la regla.", "It usually names the table and the rule.")),
        (say("Falló pytest", "pytest failed"), say("Leer qué prueba falló", "Read which test failed"),
         say("Suele indicar el producto o la semana.", "It usually names the product or the week.")),
        (say("Falló la publicación", "Publication failed"), say("Revisar los permisos del workflow", "Check the workflow permissions"),
         say("Settings → Actions → Workflow permissions: «Read and write».", "Settings → Actions → Workflow permissions: «Read and write».")),
    ], say("Mientras tanto, el panel muestra la última carga válida.", "Meanwhile, the panel shows the last valid load."))


def manual_calendar(mode):
    return timeline(mode, say("Tareas periódicas", "Periodic tasks"), [
        (say("Cada martes", "Every Tuesday"), say("Revisar el resultado", "Check the result"),
         [say("Centro de operación o correo", "Operations center or email")]),
        (say("Cada enero", "Every January"), say("Año nuevo de ODEPA", "ODEPA's new year"),
         [say("dos líneas en agent/input.csv", "two lines in agent/input.csv")]),
        (say("Periódicamente", "Periodically"), say("Copiar las descargas", "Copy the downloads"),
         [say("agent/downloads a otro disco", "agent/downloads to another disk")]),
        (say("Antes del vencimiento", "Before it expires"), say("Renovar el token", "Renew the token"),
         [say("el panel avisa 14 días antes", "the panel warns 14 days before")]),
    ])


def manual_recovery_sequence(mode):
    return sequence(mode, say("Secuencia de recuperación si el release pierde su archivo", "Recovery sequence if the release loses its file"), [
        ("author", say("Autor", "Author"), "person:author"), ("local", say("Computador", "Computer"), "brand:python"),
        ("tests", "pytest", "brand:pytest"), ("github", say("GitHub: release y main", "GitHub: release and main"), "brand:github"),
        ("panel", say("Panel", "Panel"), "brand:streamlit"),
    ], [
        ("author", "local", "python etl/pipeline.py --local", "order"),
        ("local", "tests", say("suite completa", "full suite"), "check"),
        ("tests", "author", say("en verde", "green"), "back"),
        ("author", "github", say("sube datos.duckdb a «base-actual»", "uploads datos.duckdb to «base-actual»"), "flow"),
        ("author", "local", "python bi/served_database.py --pointer", "order"),
        ("local", "github", say("push del puntero a main", "push of the pointer to main"), "flow"),
        ("panel", "github", say("ve el puntero nuevo, descarga y comprueba la huella", "sees the new pointer, downloads and checks the fingerprint"), "check"),
    ])
# endregion


# region Decision index
INDEX_THEMES = [("Fuentes e ingesta", "Sources and ingestion", GREEN), ("Modelo y reglas de datos", "Data model and rules", VIOLET),
                ("Pipeline y publicación", "Pipeline and publication", BLUE), ("Calidad y auditoría", "Quality and audit", GREEN),
                ("Seguridad", "Security", RED), ("Operación y observabilidad", "Operations and observability", AMBER),
                ("Panel", "Panel", BLUE), ("Documentación", "Documentation", GREY)]


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
    return bars(mode, say("Decisiones por tema", "Decisions by theme"), count_decisions(),
                say("Contadas en las tablas de este índice.", "Counted in the tables of this index."))


def index_map(mode):
    return columns(mode, say("Dónde actúa cada tema en el sistema", "Where each theme acts in the system"), [
        (say("Datos", "Data"), GREEN, [(say("Fuentes e ingesta", "Sources and ingestion"), say("qué se descarga y cómo", "what is downloaded and how")),
                                       (say("Modelo y reglas", "Model and rules"), say("cómo se calcula cada precio", "how each price is computed"))]),
        (say("Carga", "Load"), BLUE, [(say("Pipeline y publicación", "Pipeline and publication"), say("cuándo se publica", "when it is published")),
                                      (say("Calidad y auditoría", "Quality and audit"), say("qué la detiene", "what stops it"))]),
        (say("Operación", "Operations"), AMBER, [(say("Seguridad", "Security"), say("quién puede hacer qué", "who can do what")),
                                                (say("Operación", "Operations"), say("cómo se sabe qué pasó", "how we know what happened"))]),
        (say("Lectura", "Reading"), VIOLET, [(say("Panel", "Panel"), say("cómo se ve en una pantalla", "how it looks on one screen")),
                                            (say("Documentación", "Documentation"), say("cómo se explica", "how it is explained"))]),
    ])


def index_adr(mode):
    return tree(mode, say("Cómo llega una decisión a este índice", "How a decision reaches this index"),
                say("Cada cambio de comportamiento queda en el registro de decisiones", "Each change of behavior is kept in the decision log"), [
        (say("Cambia la arquitectura", "It changes the architecture"), say("Este índice y un registro ADR", "This index and an ADR record"),
         say("El ADR explica el contexto, las alternativas y las consecuencias.", "The ADR explains the context, the alternatives and the consequences.")),
        (say("Cambia uno de los ocho temas", "It changes one of the eight themes"), say("Este índice", "This index"),
         say("Una fila con lo que se decidió, en su tema.", "One row with what was decided, in its theme.")),
        (say("Es un ajuste menor", "It is a minor adjustment"), say("Solo el registro completo", "Only the full log"),
         say("En docs/DECISIONES.md, en orden cronológico.", "In docs/DECISIONES.md, in chronological order.")),
    ], say("Cada decisión lleva sus pruebas, que corren en cada cambio.", "Each decision carries its tests, which run on every change."))
# endregion


# region Glossary
def glossary_layers(mode):
    return columns(mode, say("Los términos de los datos, en orden", "The data terms, in order"), [
        (say("Fuente", "Source"), GREEN, [("CSV", say("el archivo que publica ODEPA", "the file ODEPA publishes")), ("SHA-256", say("su huella", "its fingerprint"))]),
        (say("Aterrizaje y bronce", "Landing and bronze"), AMBER, [(say("Aterrizaje", "Landing"), "etl/raw.db"), ("Parquet", say("copia exacta", "exact copy"))]),
        (say("Plata", "Silver"), BLUE, [("dbt", "staging · " + say("intermedio", "intermediate")), ("RN", say("reglas de negocio", "business rules"))]),
        (say("Oro", "Gold"), VIOLET, [(say("Modelo estrella", "Star schema"), say("hechos y dimensiones", "facts and dimensions")),
                                       (say("Base servida", "Served database"), "etl/datos.duckdb")]),
    ])


def glossary_actors(mode):
    return columns(mode, say("Actores y sistemas", "Actors and systems"), [
        (say("Fuentes", "Sources"), GREEN, [("ODEPA", say("precios", "prices")), ("INE", say("IPC", "CPI"))]),
        (say("Plataformas", "Platforms"), BLUE, [("GitHub", say("código, release e issues", "code, release and issues")),
                                                 ("GitHub Actions", say("la carga y las pruebas", "the load and the tests")),
                                                 ("Streamlit Cloud", say("el panel", "the panel"))]),
        (say("Personas", "People"), AMBER, [(say("Visitante", "Visitor"), say("lee el panel", "reads the panel")),
                                            (say("Autor", "Author"), say("mantiene el proyecto", "maintains the project"))]),
    ], arrows=False)


def glossary_figure(mode):
    return columns(mode, say("De la fuente a la cifra", "From the source to the figure"), [
        (say("Fila", "Row"), GREY, [(say("Una cotización", "A quote"), say("tal como llega", "as it arrives"))]),
        (say("Validación", "Validation"), RED, [("RN-11", say("se carga o se rechaza", "loaded or rejected"))]),
        (say("Precio semanal", "Weekly price"), BLUE, [(say("Por producto, región y canal", "By product, region and channel"), say("un lunes por semana", "one Monday per week"))]),
        (say("Indicador", "Indicator"), VIOLET, [("KPI", say("el cambio, el margen, el precio real", "the change, the margin, the real price"))]),
        (say("Alerta", "Alert"), AMBER, [(say("Alerta de precio", "Price alert"), say("cambio inusual de al menos 10 %", "unusual change of at least 10 %"))]),
    ])
# endregion


# Marker → builder. The heights are automatic: each frame takes the height of its figure.
FIGURES = {
    "valor": prd_value, "requisitos": prd_requirements,
    "secuencia_carga": sad_weekly_sequence, "secuencia_panel": sad_panel_sequence, "capas": sad_layers,
    "despliegue": sad_deployment,
    "mapa_adr": adr_map, "tiempo_adr": adr_timeline, "antes_despues": adr_before_after,
    "niveles": tests_levels, "secuencia_manual": tests_manual_sequence, "secuencia_ci": tests_ci_sequence,
    "actores": tests_actors,
    "arbol_fallas": manual_fault_tree, "calendario": manual_calendar, "secuencia_recuperacion": manual_recovery_sequence,
    "temas": index_themes, "mapa_temas": index_map, "adr_decisiones": index_adr,
    "terminos_capas": glossary_layers, "terminos_actores": glossary_actors, "terminos_cifra": glossary_figure,
}
