"""CI/CD and orchestration of the project (D-243, D-246): how a change reaches production, from the workflows.

Three lanes, each box tied to a step of a real workflow in .github/workflows/:
  CI, continuous integration (pruebas.yml): every push and pull request is tested alone.
  CD, continuous delivery (semanal.yml): every Tuesday the load is built, tested against the new database and, only if
      everything passed, saved with a commit.
  Publication: the panel in Streamlit Community Cloud is served from main (a setting of that platform, drawn dashed
      because it is not in the repository).
Nothing is drawn that the workflows do not do. The page is one HTML document for st.iframe (CSS only, no script)
whose SVG keeps its proportion; the definition of CI/CD is in DEFINITION, shown over it by the page.
"""
import html
from pathlib import Path

from bi import brand_icons, charts, database_map

WIDTH, HEIGHT = 1000, 742
CARD_HEIGHT = 96
WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"
# What CI and CD mean, in two short sentences each (shown over the diagram and in the glossary).
DEFINITION = (
    ("CI · integración continua", "Cada vez que alguien sube un cambio, un servidor lo prueba solo. Si algo se rompe, "
     "se ve en el momento y no a fin de mes."),
    ("CD · entrega continua", "Lo que pasa todas las pruebas llega a producción sin pasos manuales. Aquí, la base de cada "
     "martes y el panel que la muestra."),
)
DISCS = dict(database_map.BRANDS, git=("#ff9b7d", "#d6402a", "#ffffff"), streamlit=("#ff8f98", "#e0303f", "#ffffff"),
             pytest=("#7fc4ff", "#1f6fb5", "#ffffff"), check=("#7ee2b0", "#14855a", "#ffffff"),
             fail=("#ffb3a7", "#c2410c", "#ffffff"))
# Lanes: (key, title, subtitle, band top, band height).
LANES = [
    ("ci", "CI · integración continua", "en cada push y pull request · pruebas.yml", 36, 174),
    ("cd", "CD · entrega continua y orquestación", "cada martes o a mano · semanal.yml, sus nueve pasos en orden", 230, 324),
    ("pub", "Publicación", "el panel, desde la rama main", 574, 156),
]
# Card tops per (lane, row). The weekly job runs left to right on its first row and right to left on its second.
CARD_TOPS = {("ci", 0): 96, ("cd", 0): 290, ("cd", 1): 426, ("pub", 0): 618}
# Steps: (key, lane, row, column, columns, mark, name, detail, what it does, where, marker in the workflow, kind).
# kind: "gate" (nothing passes if it fails), "optional" (runs only when asked), "platform" (not in the repository).
STEPS = [
    ("ci_change", "ci", 0, 0, 5, "git", "Cambio", "push o pull request",
     "Alguien sube un cambio al repositorio o abre un pull request.", "on: push, pull_request", "pruebas.yml::pull_request:", ""),
    ("ci_actions", "ci", 0, 1, 5, "github", "GitHub Actions", "lanza el job pytest",
     "GitHub arranca una máquina limpia con Python 3.11 e instala las dependencias.", "job pytest", "pruebas.yml::pip install", ""),
    ("ci_parse", "ci", 0, 2, 5, "dbt", "dbt parse", "el proyecto compila",
     "Comprueba que los modelos, las pruebas y las fuentes de dbt compilan.", "dbt parse", "pruebas.yml::dbt parse", ""),
    ("ci_pytest", "ci", 0, 3, 5, "pytest", "pytest", "toda la batería",
     "Corre todas las pruebas de tests/; si una falla, el job se detiene.", "pytest -vv -x", "pruebas.yml::pytest -vv -x", "gate"),
    ("ci_result", "ci", 0, 4, 5, "check", "Resultado", "pasa o falla",
     "GitHub deja el resultado junto al commit: verde si todo pasó, rojo si no.", "estado del commit en GitHub",
     "pruebas.yml::name: pruebas", ""),
    ("cd_trigger", "cd", 0, 0, 5, "github", "Disparo", "martes o a mano",
     "El cron lo lanza cada martes a las 12:00 UTC (09:00 en Chile, horario estándar). También se lanza a mano: desde el "
     "Centro de operación, con la clave de control, por la API de GitHub; o desde GitHub, donde se puede pedir una falla simulada.",
     "on: schedule, workflow_dispatch", "semanal.yml::0 12 * * 2", ""),
    ("cd_year", "cd", 0, 1, 5, "github", "1 · Año vigente", "clave de la caché",
     "Calcula el año en curso: la caché de los años cerrados se renueva cuando cambia el año.", "Find the current year",
     "semanal.yml::Find the current year", ""),
    ("cd_cache", "cd", 0, 2, 5, "github", "2 · Caché", "años cerrados",
     "Restaura de la caché de Actions los CSV de los años cerrados, que ya no cambian.", "Restore the closed-year files",
     "semanal.yml::Restore the closed-year files", ""),
    ("cd_download", "cd", 0, 3, 5, "python", "3 · Descarga", "ODEPA (agent.py)",
     "Descarga los CSV de ODEPA que faltan o cambiaron, y anota su huella en manifest.json.", "Download the ODEPA files",
     "semanal.yml::Download the ODEPA files", ""),
    ("cd_etl", "cd", 0, 4, 5, "sqlite", "4 · ETL", "respaldo SQLite",
     "Construye el respaldo en SQLite (datos.db) con un camino independiente de dbt.", "Run the ETL (SQLite backup)",
     "semanal.yml::Run the ETL (SQLite backup)", ""),
    ("cd_dbt", "cd", 1, 4, 5, "dbt", "5 · dbt build", "31 pruebas",
     "Escribe el bronce en Parquet y dbt construye y prueba todos los modelos; solo si todo pasa se reemplaza datos.duckdb.",
     "Build the data warehouse with dbt", "semanal.yml::Build the data warehouse with dbt", "gate"),
    ("cd_fail", "cd", 1, 3, 5, "fail", "6 · Falla simulada", "solo si se pide",
     "Solo corre cuando una ejecución manual desde GitHub pide simulate_failure: corta el job para probar que la base "
     "publicada no cambia. El botón del panel nunca la pide.", "Simulate a failure", "semanal.yml::Simulate a failure", "optional"),
    ("cd_pytest", "cd", 1, 2, 5, "pytest", "7 · pytest", "contra la base nueva",
     "Corre las pruebas contra la base nueva, incluida la paridad SQLite ↔ DuckDB. Si falla, no se guarda nada.",
     "Run the tests against the new database", "semanal.yml::Run the tests against the new database", "gate"),
    ("cd_save", "cd", 1, 1, 5, "git", "8 · Guardar", "commit de la base",
     "Hace un commit de datos.db, datos.duckdb y manifest.json en main.", "Save the updated database",
     "semanal.yml::Save the updated database", ""),
    ("cd_report", "cd", 1, 0, 5, "github", "9 · Informe", "issue semanal",
     "Publica el informe de la semana como un issue de GitHub.", "Publish the weekly report",
     "semanal.yml::Publish the weekly report", ""),
    ("pub_main", "pub", 0, 1, 5, "git", "Rama main", "la base nueva",
     "La rama main queda con el código y la base de esa semana.", "git push del paso 8", "semanal.yml::git push", ""),
    ("pub_streamlit", "pub", 0, 2, 5, "streamlit", "Streamlit Cloud", "panel desde main",
     "Streamlit Community Cloud publica el panel desde main. Es una configuración de esa plataforma, no del repositorio.",
     "declarado por el autor; no verificable en el repositorio", None, "platform"),
]
LINKS = [("ci_change", "ci_actions"), ("ci_actions", "ci_parse"), ("ci_parse", "ci_pytest"), ("ci_pytest", "ci_result"),
         ("cd_trigger", "cd_year"), ("cd_year", "cd_cache"), ("cd_cache", "cd_download"), ("cd_download", "cd_etl"),
         ("cd_etl", "cd_dbt"), ("cd_dbt", "cd_fail"), ("cd_fail", "cd_pytest"), ("cd_pytest", "cd_save"),
         ("cd_save", "cd_report"), ("cd_save", "pub_main"), ("pub_main", "pub_streamlit")]
ROW_NOTE = "Si un paso falla, los siguientes no corren y la base publicada no cambia."


def workflow_line(marker):
    """«semanal.yml, línea 46»: where the marker text is in its workflow, read from the file itself."""
    if not marker:
        return ""
    name, _, text = marker.partition("::")
    for number, line in enumerate((WORKFLOWS_DIR / name).read_text(encoding="utf-8").splitlines(), start=1):
        if text in line:
            return f"{name}, línea {number}"
    return name


def esc(value):
    return html.escape(str(value))


def card_box(lane, row, column, columns):
    width, gap = 150, 40
    left = (WIDTH - (columns * width + (columns - 1) * gap)) / 2 + column * (width + gap)
    return left, CARD_TOPS[(lane, row)], width, CARD_HEIGHT


def disc(slug, x, y, size, key):
    """A brand on a lit disc, placed at x, y; the check is a plain tick."""
    top, bottom, glyph = DISCS[slug]
    gradient = f"disc-{slug}-{key}"
    glyphs = {"check": '<path d="M7 12.5l3.2 3.2L17 8.8" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" '
                       'stroke-linejoin="round"/>',
              "fail": '<path d="M8 8l8 8M16 8l-8 8" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/>'}
    body = glyphs.get(slug) or brand_icons.logo_body(slug)
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 72 72" aria-hidden="true"><defs>'
            f'<radialGradient id="{gradient}" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></radialGradient></defs>'
            f'<circle cx="36" cy="36" r="31" fill="url(#{gradient})"/><ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" opacity=".3"/>'
            f'<g fill="{glyph}" transform="translate(17 17) scale(1.58)">{body}</g></svg>')


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    shadow = "rgba(0,0,0,.45)" if dark else "rgba(15,39,71,.15)"
    tips = "".join(f"svg:has(#s-{step[0]}:hover, #s-{step[0]}:focus) #t-{step[0]} {{ opacity:1; }}" for step in STEPS)
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; height:100%; background:transparent; color:{text};
  font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
svg.map {{ display:block; width:100%; height:100vh; overflow:visible; }}
.lane {{ fill:{'rgba(255,255,255,.03)' if dark else 'rgba(15,39,71,.035)'}; stroke:{border}; stroke-width:1; }}
.lane-title {{ font-size:12.5px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; fill:{ink}; }}
.lane-sub {{ font-size:12.5px; fill:{muted}; }}
.step {{ outline:none; cursor:default; }}
.card {{ fill:{card}; stroke:{border}; stroke-width:1; filter:drop-shadow(0 8px 10px {shadow}); }}
.gate .card {{ stroke:{accent}; stroke-width:2; }}
.dashed .card {{ stroke-dasharray:5 5; }}
.step:hover .card, .step:focus .card {{ stroke:{accent}; }}
.name {{ font-size:13.5px; font-weight:600; fill:{ink}; }}
.detail {{ font-size:12.5px; fill:{muted}; }}
.tag {{ font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; fill:{accent}; text-anchor:end; }}
.line {{ fill:none; stroke:{accent}; stroke-width:2; stroke-linecap:round; }}
.line.dashed {{ stroke-dasharray:5 5; }}
.line-label {{ font-size:12.5px; fill:{ink}; paint-order:stroke; stroke:{palette['background']}; stroke-width:5px; }}
.note {{ font-size:12.5px; fill:{muted}; }}
.tip {{ opacity:0; pointer-events:none; transition:opacity .15s ease; }}
.tip div {{ position:absolute; width:280px; padding:12px 14px; border-radius:14px; background:{card}; border:1px solid {border};
  box-shadow:0 18px 40px rgba(0,0,0,{'.55' if dark else '.2'}); color:{text}; font-size:12.5px; line-height:1.45; }}
.tip b {{ display:block; margin:8px 0 2px; font-size:11px; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip b:first-child {{ margin-top:0; }}
.tip code {{ font:400 12px ui-monospace, SFMono-Regular, Menlo, monospace; color:{ink}; }}
{tips}
</style>"""


def build_step(step):
    key, lane, row, column, columns, mark, name, detail, what, where, marker, kind = step
    left, top, width, height = card_box(lane, row, column, columns)
    classes = "step" + (" gate" if kind == "gate" else "") + (" dashed" if kind in ("optional", "platform") else "")
    tags = {"gate": "puerta", "optional": "opcional", "platform": "plataforma"}
    tag = f'<text class="tag" x="{left + width - 10}" y="{top + 20}">{tags[kind]}</text>' if kind else ""
    return (f'<g class="{classes}" id="s-{key}" tabindex="0"><rect class="card" x="{left}" y="{top}" width="{width}" '
            f'height="{height}" rx="14"/>{disc(mark, left + 10, top + 10, 38, key)}{tag}'
            f'<text class="name" x="{left + 12}" y="{top + 68}">{esc(name)}</text>'
            f'<text class="detail" x="{left + 12}" y="{top + 86}">{esc(detail)}</text></g>')


def build_tip(step):
    key, lane, row, column, columns, mark, name, detail, what, where, marker, kind = step
    left, top, width, height = card_box(lane, row, column, columns)
    above = lane == "pub" or row == 1
    x = min(max(left + width / 2 - 140, 8), WIDTH - 288)
    y = top - 8 if above else top + height + 8
    anchor = "bottom:0" if above else "top:0"
    line = workflow_line(marker)
    return (f'<g class="tip" id="t-{key}"><foreignObject x="{x:.0f}" y="{y:.0f}" width="280" height="1" overflow="visible">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" style="{anchor}"><b>Qué hace</b>{esc(what)}'
            f'<b>Dónde está</b><code>{esc(where)}</code>{f"<br>{esc(line)}" if line else ""}</div></foreignObject></g>')


def build_link(start_key, end_key):
    boxes = {step[0]: card_box(step[1], step[2], step[3], step[4]) for step in STEPS}
    dashed = end_key in ("pub_streamlit", "cd_fail") or start_key == "cd_fail"
    (x1, y1, w1, h1), (x2, y2, w2, h2) = boxes[start_key], boxes[end_key]
    label = ""
    if y1 == y2:  # along a row, either way
        path = f'M{x1 + w1} {y1 + h1 / 2} L{x2} {y2 + h2 / 2}' if x2 > x1 else f'M{x1} {y1 + h1 / 2} L{x2 + w2} {y2 + h2 / 2}'
    else:  # down to the card under it
        x = x1 + w1 / 2
        path = f'M{x} {y1 + h1} L{x} {y2}'
        if start_key == "cd_save":
            label = f'<text class="line-label" x="{x + 10}" y="{(y1 + h1 + y2) / 2 + 4}">git push</text>'
    return f'<path class="line{" dashed" if dashed else ""}" d="{path}" marker-end="url(#head)"/>' + label


def build_cicd_html(palette):
    """The three lanes of the CI/CD of the project, from the workflows."""
    head = (f'<defs><marker id="head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>')
    lanes = "".join(f'<rect class="lane" x="12" y="{top}" width="976" height="{height}" rx="18"/>'
                    f'<text class="lane-title" x="30" y="{top + 24}">{esc(title)}</text>'
                    f'<text class="lane-sub" x="30" y="{top + 42}">{esc(sub)}</text>'
                    for _, title, sub, top, height in LANES)
    note = f'<text class="note" x="970" y="{CARD_TOPS[("cd", 1)] + CARD_HEIGHT + 22}" text-anchor="end">{esc(ROW_NOTE)}</text>'
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body><svg class="map" viewBox="0 0 {WIDTH} {HEIGHT}" preserveAspectRatio="xMidYMid meet" '
            f'role="img" aria-label="CI/CD del proyecto">{head}{lanes}{note}'
            f'{"".join(build_link(*link) for link in LINKS)}{"".join(build_step(step) for step in STEPS)}'
            f'{"".join(build_tip(step) for step in STEPS)}</svg></body></html>')
