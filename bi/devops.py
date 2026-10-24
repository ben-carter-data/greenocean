"""CI/CD and orchestration of the project (D-243, D-246, D-276): how a change reaches production, from the workflows.

Every box is a step of a real workflow in .github/workflows/:
  CI, continuous integration (pruebas.yml): every push and pull request is tested alone, on one row.
  CD, continuous delivery (semanal.yml): every Tuesday the load is built, tested against the new database and, only if
      everything passed, published: the database replaces the one in the release «base-actual» and its pointer is
      committed (D-270). D-276: its ten named steps are grouped in four phases on one row (prepare, ingest, build and
      test, publish), each step a line of its phase, numbered in the workflow's order, so the view fits one screen.
  Publication: the release, and the panel in Streamlit Community Cloud served from main (a setting of that platform,
      drawn dashed because it is not in the repository).
Nothing is drawn that the workflows do not do. Each step tells on hover what it does and on which line of its workflow
it is. The page is one HTML document for st.iframe (CSS only, no script); DEFINITION says what CI and CD are.
"""
import html
from pathlib import Path

from bi import brand_icons, charts, database_map

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
# Steps: (key, lane, mark, name, detail, what it does, where, marker in the workflow, kind).
# kind: "gate" (nothing passes if it fails), "optional" (runs only when asked), "platform" (not in the repository).
STEPS = [
    ("ci_change", "ci", "git", "Cambio", "push o pull request",
     "Alguien sube un cambio al repositorio o abre un pull request.", "on: push, pull_request", "pruebas.yml::pull_request:", ""),
    ("ci_actions", "ci", "github", "GitHub Actions", "lanza el job pytest",
     "GitHub arranca una máquina limpia con Python 3.11 e instala las dependencias.", "job pytest", "pruebas.yml::pip install", ""),
    ("ci_parse", "ci", "dbt", "dbt parse", "el proyecto compila",
     "Comprueba que los modelos, las pruebas y las fuentes de dbt compilan.", "dbt parse", "pruebas.yml::dbt parse", ""),
    ("ci_pytest", "ci", "pytest", "pytest", "toda la batería",
     "Corre todas las pruebas de tests/; si una falla, el job se detiene.", "pytest -vv -x", "pruebas.yml::pytest -vv -x", "gate"),
    ("ci_result", "ci", "check", "Resultado", "pasa o falla",
     "GitHub deja el resultado junto al commit: verde si todo pasó, rojo si no. Avisa, pero no detiene la publicación: Streamlit publica main sin esperarlo.", "estado del commit en GitHub",
     "pruebas.yml::name: pruebas", ""),
    ("cd_trigger", "cd", "github", "Disparo", "martes o a mano",
     "El cron lo lanza cada martes a las 12:00 UTC (09:00 en Chile en horario de verano, 08:00 en invierno). También se lanza a mano: desde el "
     "Centro de operación, con la clave de control, por la API de GitHub; o desde GitHub, donde se puede pedir una falla simulada.",
     "on: schedule, workflow_dispatch", "semanal.yml::0 12 * * 2", ""),
    ("cd_year", "cd", "github", "1 · Año vigente", "clave de la caché",
     "Calcula el año en curso: la caché de los años cerrados se renueva cuando cambia el año.", "Find the current year",
     "semanal.yml::Find the current year", ""),
    ("cd_cache", "cd", "github", "2 · Caché", "años cerrados",
     "Restaura de la caché de Actions los CSV de los años cerrados, que ya no cambian.", "Restore the closed-year files",
     "semanal.yml::Restore the closed-year files", ""),
    ("cd_base", "cd", "duckdb", "3 · Base publicada", "la de la semana pasada",
     "Descarga del release «base-actual» la base que se publicó la semana anterior y comprueba su huella: de ella salen "
     "el historial de cargas y la comparación del 90 %.", "Get the published database",
     "semanal.yml::Get the published database", ""),
    ("cd_download", "cd", "python", "4 · Descarga", "ODEPA (agent.py)",
     "Descarga los CSV de ODEPA que faltan o cambiaron, y anota su huella en manifest.json.", "Download the ODEPA files",
     "semanal.yml::Download the ODEPA files", ""),
    ("cd_etl", "cd", "sqlite", "5 · ETL", "respaldo SQLite",
     "Construye en esta máquina el respaldo en SQLite (datos.db), con un camino independiente de dbt, para la prueba de "
     "paridad. No se publica.", "Run the ETL (SQLite backup)", "semanal.yml::Run the ETL (SQLite backup)", ""),
    ("cd_dbt", "cd", "dbt", "6 · dbt build", "31 pruebas",
     "Escribe el bronce en Parquet y dbt construye y prueba todos los modelos; solo si todo pasa se reemplaza datos.duckdb.",
     "Build the data warehouse with dbt", "semanal.yml::Build the data warehouse with dbt", "gate"),
    ("cd_fail", "cd", "fail", "7 · Falla simulada", "solo si se pide",
     "Solo corre cuando una ejecución manual desde GitHub pide simulate_failure: corta el job para probar que la base "
     "publicada no cambia. El botón del panel nunca la pide.", "Simulate a failure", "semanal.yml::Simulate a failure", "optional"),
    ("cd_pytest", "cd", "pytest", "8 · pytest", "contra la base nueva",
     "Corre las pruebas contra la base nueva, incluida la paridad SQLite ↔ DuckDB. Si falla, no se publica nada.",
     "Run the tests against the new database", "semanal.yml::Run the tests against the new database", "gate"),
    ("cd_publish", "cd", "github", "9 · Publicar", "release y puntero",
     "Reemplaza datos.duckdb en el release «base-actual» y después sube a main su puntero (etl/datos.version) y "
     "manifest.json. El historial de Git no guarda la base.", "Publish the database", "semanal.yml::Publish the database", ""),
    ("cd_report", "cd", "github", "10 · Informe", "issue semanal",
     "Publica el informe de la semana como un issue de GitHub.", "Publish the weekly report",
     "semanal.yml::Publish the weekly report", ""),
    ("pub_release", "pub", "github", "Release", "base-actual",
     "Guarda una sola copia de la base servida: cada carga reemplaza la anterior.", "gh release upload del paso 9",
     "semanal.yml::gh release upload", ""),
    ("pub_streamlit", "pub", "streamlit", "Streamlit Cloud", "panel desde main",
     "Streamlit Community Cloud publica el panel desde main, una configuración de esa plataforma. Cuando el puntero cambia, "
     "el panel descarga la base nueva del release y comprueba su huella (bi/served_database.py).",
     "declarado por el autor; no verificable en el repositorio", None, "platform"),
]
# The four phases of the weekly load, each with its steps in the workflow's order: (key, name, logo, steps).
PHASES = [("preparar", "Preparar", "github", ["cd_year", "cd_cache", "cd_base"]),
          ("ingerir", "Ingerir", "python", ["cd_download", "cd_etl"]),
          ("probar", "Construir y probar", "dbt", ["cd_dbt", "cd_fail", "cd_pytest"]),
          ("publicar", "Publicar", "github", ["cd_publish", "cd_report"])]
CI_FLOW = ["ci_change", "ci_actions", "ci_parse", "ci_pytest", "ci_result"]
TAGS = {"gate": "puerta", "optional": "opcional", "platform": "plataforma"}
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
    grid = f"color-mix(in srgb, {border} {'38' if dark else '45'}%, transparent)"
    surface = f"color-mix(in srgb, {card} 72%, #000)" if dark else card
    glow = (f"0 0 0 1px color-mix(in srgb, {accent} 35%, transparent), 0 0 22px -6px color-mix(in srgb, {accent} 70%, transparent)"
            if dark else "0 8px 18px -14px rgba(15,40,90,.35)")
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:400 14px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.cc {{ padding:11px 20px 14px; border:1px solid {border}; border-radius:18px; background-color:{surface};
  background-image:linear-gradient({grid} 1px, transparent 1px), linear-gradient(90deg, {grid} 1px, transparent 1px); background-size:30px 30px; }}
.cc-head h2 {{ margin:0 0 2px; font-size:20px; font-weight:700; color:{ink}; }}
.lane {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:2px 12px; margin:10px 0 6px; }}
.lane .kicker {{ font:700 11px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.14em; text-transform:uppercase; color:{accent}; }}
.lane span {{ font-size:12.5px; color:{text}; }}
.lane small {{ font:400 11.5px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; color:{muted}; }}
.note {{ grid-column:1 / 6; margin:0; align-self:center; padding-right:14px; font-size:12.5px; line-height:1.45; color:{muted}; }}
.note b {{ color:{ink}; font-weight:600; }}
.row {{ display:grid; align-items:stretch;
  grid-template-columns:minmax(0, 1fr) 26px minmax(0, 1fr) 26px minmax(0, 1fr) 26px minmax(0, 1fr) 26px minmax(0, 1fr); }}
/* The weekly load: the trigger is one short box, so its four phases get the width their steps need. */
.row.cd, .down {{ grid-template-columns:minmax(0, .72fr) 26px minmax(0, 1.12fr) 26px minmax(0, 1.12fr) 26px minmax(0, 1.12fr) 26px minmax(0, 1.12fr); }}
.box {{ position:relative; padding:9px 10px; border:1px solid {border}; border-radius:14px; background:color-mix(in srgb, {card} 92%, transparent);
  color:{ink}; outline:none; cursor:default; }}
.box:hover, .box:focus {{ border-color:{accent}; }}
.step {{ display:flex; align-items:center; gap:9px; }}
.step svg {{ flex:none; width:30px; height:30px; }}
.step b {{ display:block; font-size:14px; font-weight:700; line-height:1.2; }}
.step small {{ display:block; font-size:12px; color:{muted}; }}
.gate {{ border-color:{accent}; box-shadow:{glow}; }}
.dashed {{ border-style:dashed; }}
.step.gate, .step.dashed {{ padding-top:17px; }}
.tag {{ position:absolute; top:5px; right:9px; font:700 9.5px/1 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.12em;
  text-transform:uppercase; color:{accent}; }}
.phase .kicker {{ display:flex; align-items:center; gap:7px; margin-bottom:5px; font:700 10.5px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
  letter-spacing:.14em; text-transform:uppercase; color:{muted}; }}
.phase .kicker svg {{ width:20px; height:20px; }}
.srow {{ display:flex; align-items:baseline; gap:7px; padding:2px 6px; margin:0 -6px; border-radius:8px; outline:none; cursor:default; }}
.srow:hover, .srow:focus {{ background:color-mix(in srgb, {accent} 12%, transparent); }}
.srow i {{ flex:none; min-width:20px; font:700 11.5px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; font-style:normal; color:{accent}; }}
.srow b {{ font-size:13.5px; font-weight:600; line-height:1.4; }}
.srow em {{ margin-left:auto; padding:0 6px; border:1px solid currentColor; border-radius:6px; font:700 9px/1.6 ui-monospace, SFMono-Regular, Menlo, monospace;
  font-style:normal; letter-spacing:.1em; text-transform:uppercase; color:{accent}; white-space:nowrap; }}
.srow.k-optional em {{ color:{muted}; }} .srow.k-optional b {{ color:{muted}; font-weight:500; }}
.h {{ position:relative; align-self:center; height:12px; }}
.h::before {{ content:""; position:absolute; left:3px; right:8px; top:5px; border-top:2px dashed {accent}; opacity:.85; }}
.h::after {{ content:""; position:absolute; right:1px; top:1px; border:5px solid transparent; border-left:8px solid {accent}; }}
.h.left::before {{ left:8px; right:3px; }} .h.left::after {{ right:auto; left:1px; border-left-color:transparent; border-right:8px solid {accent}; }}
.down {{ display:grid; height:28px; }}
.down i {{ position:relative; grid-column:9; }}
.down i::before {{ content:""; position:absolute; left:50%; top:2px; bottom:8px; border-left:2px dashed {accent}; opacity:.85; }}
.down i::after {{ content:""; position:absolute; left:calc(50% - 4px); bottom:0; border:5px solid transparent; border-top:8px solid {accent}; }}
.down span {{ grid-column:7 / 9; align-self:center; text-align:right; padding-right:8px; font:400 11.5px/1 ui-monospace, SFMono-Regular, Menlo, monospace; color:{muted}; }}
@media (max-width:760px) {{
  .row, .down {{ grid-template-columns:minmax(0, 1fr); row-gap:8px; }} .note {{ order:9; }}
  .row > *, .down > * {{ grid-column:1 !important; }} .h, .down {{ display:none; }}
  .lane small {{ margin-left:0; }}
}}
</style>"""


def describe(step):
    """What a step does and where it is, for its hover."""
    key, lane, mark, name, detail, what, where, marker, kind = step
    line = workflow_line(marker)
    return f"Qué hace: {what}\nDónde está: {where}" + (f" · {line}" if line else "")


def build_step(step, column=None):
    """A step on its own: its logo, its name and what it is; a gate and an optional step say so."""
    key, lane, mark, name, detail, what, where, marker, kind = step
    classes = "box step" + (" gate" if kind == "gate" else "") + (" dashed" if kind in ("optional", "platform") else "")
    place = f' style="grid-column:{column}"' if column else ""
    tag = f'<span class="tag">{TAGS[kind]}</span>' if kind else ""
    return (f'<div class="{classes}" id="s-{key}" tabindex="0" title="{esc(describe(step))}"{place}>{tag}'
            f'{disc(mark, 0, 0, 30, key)}<span><b>{esc(name)}</b><small>{esc(detail)}</small></span></div>')


def build_phase(phase, steps):
    """A phase of the weekly load: its name and its steps, one line each, numbered as in the workflow."""
    key, name, mark, keys = phase
    lines = []
    for step in (steps[k] for k in keys):
        number, _, title = step[3].partition(" · ")
        kind = step[8]
        lines.append(f'<div class="srow k-{kind or "step"}" id="s-{step[0]}" tabindex="0" title="{esc(step[4])}. {esc(describe(step))}">'
                     f'<i>{esc(number)}</i><b>{esc(title)}</b>{f"<em>{TAGS[kind]}</em>" if kind else ""}</div>')
    gate = any(steps[k][8] == "gate" for k in keys)
    return (f'<div class="box phase{" gate" if gate else ""}"><span class="kicker">{disc(mark, 0, 0, 20, key)}{esc(name)}</span>'
            + "".join(lines) + "</div>")


def build_cicd_html(palette):
    """CI on one row, the weekly load in four phases on another, and its publication under the last phase."""
    steps = {step[0]: step for step in STEPS}
    arrow = '<i class="h"></i>'
    ci = arrow.join(build_step(steps[key]) for key in CI_FLOW)
    cd = build_step(steps["cd_trigger"]) + arrow + arrow.join(build_phase(phase, steps) for phase in PHASES)
    publication = (f'<p class="note"><b>Puerta:</b> un control que detiene la carga. {esc(ROW_NOTE)}</p>'
                   + build_step(steps["pub_streamlit"], column=7) + '<i class="h left" style="grid-column:8"></i>'
                   + build_step(steps["pub_release"], column=9))
    (ci_term, ci_text), (cd_term, cd_text) = DEFINITION
    body = (f'<div class="cc-head"><h2>Del cambio a producción</h2></div>'
            f'<div class="lane"><span class="kicker">{esc(ci_term)}</span><small>pruebas.yml</small><span>{esc(ci_text)}</span></div>'
            f'<div class="row">{ci}</div>'
            f'<div class="lane"><span class="kicker">{esc(cd_term)}</span><small>semanal.yml</small><span>{esc(cd_text)}</span></div>'
            f'<div class="row cd">{cd}</div><div class="down"><span>gh release upload</span><i></i></div>'
            f'<div class="row cd">{publication}</div>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body><div class="cc" role="group" aria-label="CI/CD del proyecto">{body}</div></body></html>')
