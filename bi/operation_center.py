"""Centro de operación (D-165): the weekly run as a path of floating logos.

The nine steps of the run, from the launch to the panel, lie on one serpentine of
three rows (launch and download, transform and test, publish), so the page reads
left to right and down. Each logo shows the state of its step in the latest run by
the light under it; hovering it explains what the step does and gives the address
where to act or read its log, and clicking it opens that address. The pipeline is
its own guide: there is no other text.

One self-contained HTML document for st.iframe: st.markdown and st.html strip the
SVG gradients and the hover bubbles (see the GitHub page). Every address points out
of the panel and opens in a new tab.
"""
import html

from bi import control, project

# region Constants
# The stage is drawn on a 740 x 640 grid and scales with the width of the column.
STAGE_WIDTH = 740
STAGE_HEIGHT = 640
COLUMNS = [120, 370, 620]
ROWS = [100, 320, 540]
# Three straight rows joined by half circles: the middle row runs right to left.
TRACK = "M120 100 H620 A110 110 0 0 1 620 320 H120 A110 110 0 0 0 120 540 H620"
PHASES = ["Lanzar y descargar", "Transformar y probar", "Publicar"]
# The phase names start right of the half circle on the left, which reaches x = 10.
PHASE_LEFT = 30

STATE_OK = "ok"
STATE_FAILED = "fail"
STATE_RUNNING = "run"
STATE_SKIPPED = "skip"
STATE_WAITING = "wait"
STATE_UNKNOWN = "none"
STATE_TEXTS = {STATE_FAILED: "Falló", STATE_RUNNING: "En curso…", STATE_SKIPPED: "No corrió",
               STATE_WAITING: "En espera", STATE_UNKNOWN: "Sin dato"}

LOCK_ICON = ('<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
             'stroke-width="2.4" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"/>'
             '<path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>')

# The logos, drawn like the GitHub page's: gradients, a highlight and a soft shadow.
LOGOS = {
    "launch": '<radialGradient id="g-launch" cx="35%" cy="28%" r="80%"><stop offset="0" stop-color="#9cc0ff"/><stop offset=".55" stop-color="#3d74f0"/><stop offset="1" stop-color="#1739a8"/></radialGradient></defs><circle cx="36" cy="36" r="30" fill="url(#g-launch)"/><ellipse cx="29" cy="20" rx="15" ry="8" fill="#fff" opacity=".35"/><path d="M36 22v14M27.5 27.5a12 12 0 1 0 17 0" fill="none" stroke="#fff" stroke-width="4.2" stroke-linecap="round"/>',
    "odepa": '<linearGradient id="g-odepa" x1="0" y1="0" x2=".4" y2="1"><stop offset="0" stop-color="#7ef0c2"/><stop offset="1" stop-color="#0a8f5f"/></linearGradient></defs><path d="M18 8h26l14 14v38a6 6 0 0 1-6 6H18a6 6 0 0 1-6-6V14a6 6 0 0 1 6-6z" fill="url(#g-odepa)"/><path d="M44 8v10a4 4 0 0 0 4 4h10z" fill="#c9fbe5"/><rect x="18" y="13" width="18" height="4" rx="2" fill="#fff" opacity=".35"/><text x="35" y="50" text-anchor="middle" font-family="sans-serif" font-weight="700" font-size="15" fill="#fff">CSV</text>',
    "ine": '<linearGradient id="g-ine-a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fda4af"/><stop offset="1" stop-color="#d61f45"/></linearGradient><linearGradient id="g-ine-b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#93c5fd"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient><linearGradient id="g-ine-c" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fde68a"/><stop offset="1" stop-color="#d97706"/></linearGradient></defs><ellipse cx="36" cy="60" rx="27" ry="6" fill="#dbe3ee" opacity=".7"/><rect x="13" y="34" width="13" height="26" rx="4" fill="url(#g-ine-b)"/><rect x="29.5" y="16" width="13" height="44" rx="4" fill="url(#g-ine-a)"/><rect x="46" y="26" width="13" height="34" rx="4" fill="url(#g-ine-c)"/><rect x="31" y="18" width="4" height="30" rx="2" fill="#fff" opacity=".35"/>',
    "etl": '<linearGradient id="g-etl" x1="0" y1="0" x2=".3" y2="1"><stop offset="0" stop-color="#c4b5fd"/><stop offset="1" stop-color="#6d28d9"/></linearGradient></defs><path d="M10 14h52a3 3 0 0 1 2.2 5L44 42v16a3 3 0 0 1-1.6 2.7l-9 4.6A3 3 0 0 1 29 62.6V42L7.8 19A3 3 0 0 1 10 14z" fill="url(#g-etl)"/><path d="M14 18h40" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".45"/><circle cx="28" cy="26" r="3" fill="#fff" opacity=".7"/><circle cx="40" cy="29" r="2.4" fill="#fff" opacity=".6"/><circle cx="35" cy="35" r="2" fill="#fff" opacity=".55"/>',
    "dbt": '<linearGradient id="g-dbt-a" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffb08a"/><stop offset="1" stop-color="#e2541f"/></linearGradient><linearGradient id="g-dbt-b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffd2bd"/><stop offset="1" stop-color="#ff8a57"/></linearGradient></defs><path d="M36 50 8 38l28-12 28 12z" fill="#c2410c" opacity=".55"/><path d="M36 42 8 30l28-12 28 12z" fill="url(#g-dbt-a)"/><path d="M36 30 12 20 36 10l24 10z" fill="url(#g-dbt-b)"/><path d="M36 58 8 46v-6l28 12 28-12v6z" fill="#9a3412" opacity=".5"/><text x="36" y="35" text-anchor="middle" font-family="sans-serif" font-weight="700" font-size="11" fill="#fff">dbt</text>',
    "tests": '<linearGradient id="g-tests" x1="0" y1="0" x2=".3" y2="1"><stop offset="0" stop-color="#86efac"/><stop offset="1" stop-color="#15803d"/></linearGradient></defs><path d="M36 6 60 15v18c0 15-10 26-24 32C22 59 12 48 12 33V15z" fill="url(#g-tests)"/><path d="M36 10 56 18v6C46 21 30 22 16 30V18z" fill="#fff" opacity=".22"/><path d="M25 35l8 8 15-16" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>',
    "save": '<linearGradient id="g-save" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5b8def"/><stop offset=".5" stop-color="#9dbcff"/><stop offset="1" stop-color="#2f5fd0"/></linearGradient></defs><path d="M12 18v36c0 5 11 9 24 9s24-4 24-9V18z" fill="url(#g-save)"/><ellipse cx="36" cy="18" rx="24" ry="9" fill="#c7d8ff"/><path d="M12 32c0 5 11 9 24 9s24-4 24-9M12 45c0 5 11 9 24 9s24-4 24-9" fill="none" stroke="#fff" stroke-width="2" opacity=".5"/><path d="M36 26v-10M31 20l5-5 5 5" fill="none" stroke="#1e3a8a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>',
    "report": '<linearGradient id="g-report" x1="0" y1="0" x2=".3" y2="1"><stop offset="0" stop-color="#a5f3fc"/><stop offset="1" stop-color="#0e7490"/></linearGradient></defs><rect x="12" y="8" width="48" height="58" rx="8" fill="url(#g-report)"/><rect x="18" y="14" width="22" height="4" rx="2" fill="#fff" opacity=".45"/><rect x="20" y="44" width="7" height="12" rx="2" fill="#fff"/><rect x="32.5" y="34" width="7" height="22" rx="2" fill="#fff"/><rect x="45" y="39" width="7" height="17" rx="2" fill="#fff"/><path d="M19 30l11-6 9 4 13-8" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" opacity=".8"/>',
    "panel": '<linearGradient id="g-panel" x1="0" y1="0" x2=".3" y2="1"><stop offset="0" stop-color="#ff9a9a"/><stop offset="1" stop-color="#e02f3c"/></linearGradient></defs><rect x="6" y="10" width="60" height="40" rx="7" fill="url(#g-panel)"/><rect x="11" y="15" width="50" height="30" rx="4" fill="#fff" opacity=".92"/><path d="M15 38l9-8 7 5 10-11 8 6 8-7" fill="none" stroke="#e02f3c" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M30 50h12l3 10H27z" fill="#c9cfd8"/><rect x="22" y="59" width="28" height="5" rx="2.5" fill="#aab3c0"/>',
}

# The run in order. «workflow»: the semanal.yml steps whose state is this logo's;
# the IPC of the INE is prepared inside the dbt step (etl/pipeline.py), so it shares
# that state. «links»: (text, address, private); a private one only shows once the
# control code was typed. «log» adds the step's own log first.
STEPS = [
    {"key": "launch", "label": "Lanzar", "title": "Lanzar el pipeline", "place": (0, 0),
     "workflow": [], "log": False,
     "hint": "Corre solo cada martes a las 12:00 UTC (09:00 en Chile en verano, 08:00 en invierno). Para adelantarlo: «Ejecutar pipeline "
             "ahora», a la derecha, con tu clave de control, o «Run workflow» en GitHub.",
     "links": [("Run workflow", project.WORKFLOW_PAGE_URL, True),
               ("Tokens de GitHub", project.TOKENS_URL, True)]},
    {"key": "odepa", "label": "ODEPA", "title": "Descarga de ODEPA", "place": (1, 0),
     "workflow": ["Download the ODEPA files"], "log": True,
     "hint": "Baja los precios mayoristas y al consumidor del año en curso; los años "
             "cerrados salen de la caché. Si falla, el log dice qué archivo y por qué.",
     "links": [("Precios mayoristas", project.WHOLESALE_SOURCE_URL, False),
               ("Precios al consumidor", project.CONSUMER_SOURCE_URL, False)]},
    {"key": "ine", "label": "IPC · INE", "title": "IPC de alimentos · INE", "place": (2, 0),
     "workflow": ["Build the data warehouse with dbt"], "log": True,
     "hint": "Baja el IPC para mostrar precios sin inflación; corre al comienzo del paso de "
             "dbt. Si el INE no responde, usa el último publicado y la carga sigue.",
     "links": [("Sitio del INE", project.INE_IPC_SOURCE_URL, False)]},
    {"key": "etl", "label": "Limpieza", "title": "Limpieza (ETL)", "place": (2, 1),
     "workflow": ["Run the ETL (SQLite backup)", "Run the ETL"], "log": True,
     "hint": "Lleva cada precio a kilo o unidad y a su semana, valida cada fila y aparta "
             "las que no sirven, con su motivo.",
     "links": []},
    {"key": "dbt", "label": "dbt", "title": "Data warehouse con dbt", "place": (1, 1),
     "workflow": ["Build the data warehouse with dbt"], "log": True,
     "hint": "Construye staging, intermedio y marts en DuckDB y corre sus 31 pruebas de "
             "datos. Si una falla, se detiene aquí y la base publicada no cambia.",
     "links": []},
    {"key": "tests", "label": "Pruebas", "title": "Pruebas automáticas", "place": (0, 1),
     "workflow": ["Run the tests against the new database"], "log": True,
     "hint": "pytest recalcula las cifras desde la fuente. Si una prueba falla, la base "
             "publicada no se toca; el final del log nombra la prueba con FAILED.",
     "links": []},
    {"key": "save", "label": "Publicar", "title": "Publicar la base", "place": (0, 2),
     "workflow": ["Publish the database", "Save the updated database"], "log": True,
     "hint": "Reemplaza la base en el release «base-actual» y sube su puntero a main con el "
             "commit «Weekly data update». Solo ocurre si todo lo anterior pasó.",
     "links": [("Release", project.RELEASE_URL, False), ("Commits", project.COMMITS_URL, False)]},
    {"key": "report", "label": "Informe", "title": "Informe semanal", "place": (1, 2),
     "workflow": ["Publish the weekly report"], "log": True,
     "hint": "Publica el informe de la semana como issue en GitHub, con sus alertas; GitHub "
             "avisa por correo.",
     "links": [("Informes", project.ISSUES_URL, False)]},
    {"key": "panel", "label": "Panel", "title": "Panel en Streamlit", "place": (2, 2),
     "workflow": [], "log": False,
     "hint": "Lee la base nueva en uno o dos minutos; si no la ves, «Recargar datos», "
             "a la derecha. Registros, secretos y reinicio están en Streamlit.",
     "links": [("Administrar la app", project.STREAMLIT_ADMIN_URL, True)]},
]
# endregion


# region States
def to_step_state(github_state):
    """A GitHub step state (control.RUN_*, «skipped», queued) as a logo state."""
    return {control.RUN_OK: STATE_OK, control.RUN_FAILED: STATE_FAILED,
            control.RUN_IN_PROGRESS: STATE_RUNNING, "skipped": STATE_SKIPPED}.get(
                github_state, STATE_UNKNOWN)


def format_seconds(seconds):
    if seconds is None:
        return ""
    seconds = round(seconds)
    return f"{seconds} s" if seconds < 60 else f"{seconds // 60} min {seconds % 60:02d} s"


def build_step_states(run, details, load_ok):
    """{step key: (state, short text, log address or None)} for the latest run.

    run: the latest run (control.simplify_run) or None; details: its steps
    (control.list_run_step_details), {} when GitHub did not answer; load_ok: the
    latest load in etl_run passed. While a run is in progress, steps GitHub has not
    started yet are waiting, not skipped."""
    in_progress = bool(run) and run["state"] == control.RUN_IN_PROGRESS
    states = {}
    for step in STEPS:
        if step["key"] == "launch":
            if not run:
                states["launch"] = (STATE_UNKNOWN, STATE_TEXTS[STATE_UNKNOWN], None)
            else:
                states["launch"] = (STATE_OK, run["trigger"], run["url"])
            continue
        if step["key"] == "panel":
            state = STATE_RUNNING if in_progress else STATE_OK if load_ok else STATE_FAILED
            text = "Esperando la base" if in_progress else "Base al día" if load_ok else "Última carga falló"
            states["panel"] = (state, text, None)
            continue
        found = next((details[name] for name in step["workflow"] if name in details), None)
        if found is None:
            states[step["key"]] = (STATE_UNKNOWN, STATE_TEXTS[STATE_UNKNOWN], None)
            continue
        state = to_step_state(found["state"])
        if state == STATE_UNKNOWN and in_progress:
            state = STATE_WAITING
        text = format_seconds(found["seconds"]) if state == STATE_OK else STATE_TEXTS[state]
        states[step["key"]] = (state, text or "OK", found["url"])
    return states


def pick_pinned_step(states):
    """The step whose bubble stays open: the one that failed, else the one running."""
    for wanted in (STATE_FAILED, STATE_RUNNING):
        for step in STEPS:
            if states[step["key"]][0] == wanted:
                return step["key"]
    return None
# endregion


# region Markup
def build_css(palette):
    dark = palette["base"] == "dark"
    shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    return f"""<style>
* {{box-sizing:border-box;}}
body {{margin:0; background:transparent; color:{palette['text']};
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;}}
a {{color:{palette['accent']}; text-decoration:none;}} a:hover {{text-decoration:underline;}}
.oc-stage {{position:relative; width:100%; max-width:{STAGE_WIDTH}px; aspect-ratio:{STAGE_WIDTH}/{STAGE_HEIGHT};
  margin:0 auto;}}
.oc-stage > svg {{position:absolute; inset:0; width:100%; height:100%;}}
.oc-phase {{position:absolute; left:{PHASE_LEFT / STAGE_WIDTH * 100:.2f}%; font-size:11px; font-weight:600; letter-spacing:1.4px;
  text-transform:uppercase; color:{palette['reference']};}}
.oc-phase b {{color:{palette['accent']}; margin-right:6px;}}
.oc-node {{position:absolute; width:132px; margin-left:-66px; margin-top:-38px; display:flex;
  flex-direction:column; align-items:center; text-align:center;}}
.oc-node > a {{display:block; border-radius:50%;}}
.oc-node > a:focus-visible {{outline:2px solid {palette['accent']}; outline-offset:4px;}}
.oc-logo {{display:block; width:76px; height:76px; filter:drop-shadow(0 16px 14px {shadow});
  transition:transform .25s ease;}}
.oc-node:hover .oc-logo {{transform:translateY(-6px) scale(1.04);}}
.oc-halo {{width:62px; height:12px; border-radius:50%; margin-top:4px; filter:blur(4px);
  background:{'rgba(255,255,255,.12)' if dark else 'rgba(15,39,71,.16)'};}}
.ok .oc-halo {{background:rgba(34,179,90,.6);}}
.fail .oc-halo {{background:rgba(220,38,38,.7);}}
.run .oc-halo {{background:rgba(59,130,246,.75); animation:oc-pulse 1.3s ease-in-out infinite;}}
.skip .oc-logo, .wait .oc-logo, .none .oc-logo {{opacity:.4; filter:grayscale(1) drop-shadow(0 12px 12px {shadow});}}
@keyframes oc-pulse {{0%,100% {{opacity:.35; transform:scaleX(.8);}} 50% {{opacity:1; transform:scaleX(1.15);}}}}
.oc-label {{margin-top:8px; font-weight:600; font-size:14px; color:{palette['strong_text']};}}
.oc-state {{margin-top:1px; font-size:12px; color:{palette['reference']};}}
.fail .oc-state {{color:#e5484d; font-weight:600;}}
.run .oc-state {{color:#3b82f6; font-weight:600;}}
.oc-tip {{position:absolute; bottom:calc(100% + 4px); left:50%; width:276px; padding:14px 16px 12px;
  border-radius:14px; background:{palette['card']}; border:1px solid {palette['card_border']};
  box-shadow:0 18px 40px rgba(0,0,0,{'.45' if dark else '.18'}); text-align:left; z-index:5;
  opacity:0; pointer-events:none; transform:translate(-50%,8px); transition:opacity .18s ease, transform .18s ease;}}
.oc-tip.below {{bottom:auto; top:calc(100% + 4px);}}
.oc-tip.start {{left:0; transform:translate(0,8px);}}
.oc-tip.end {{left:auto; right:0; transform:translate(0,8px);}}
.oc-stage:hover .oc-tip.pinned {{opacity:0; pointer-events:none;}}
.oc-tip.pinned, .oc-node:hover .oc-tip, .oc-node:focus-within .oc-tip {{opacity:1; pointer-events:auto; transform:translate(-50%,0);}}
.oc-node:hover .oc-tip.start, .oc-node:focus-within .oc-tip.start, .oc-tip.start.pinned,
.oc-node:hover .oc-tip.end, .oc-node:focus-within .oc-tip.end, .oc-tip.end.pinned {{transform:translate(0,0);}}
.oc-tip h4 {{margin:0 0 4px; font-size:14px; color:{palette['strong_text']};}}
.oc-tip p {{margin:0; font-size:13px; line-height:1.45;}}
.oc-links {{display:flex; flex-wrap:wrap; gap:4px 14px; margin-top:10px; font-size:12.5px; font-weight:600;}}
.oc-lock {{color:{palette['reference']};}} .oc-lock svg {{vertical-align:-2px; margin-right:3px;}}
</style>"""


def build_links_html(step, log_url, unlocked):
    links = []
    if step["log"] and log_url:
        links.append(("Log del paso", log_url, False))
    elif step["key"] == "launch" and log_url:
        links.append(("Ver la ejecución", log_url, False))
    links += [link for link in step["links"] if unlocked or not link[2]]
    # Python 3.11 (GitHub Actions) allows no backslash inside an f-string expression.
    lock_class = 'class="oc-lock" '
    return "".join(
        f'<a {lock_class if private else ""}href="{html.escape(url, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">{LOCK_ICON if private else ""}'
        f'{html.escape(text)} ↗</a>'
        for text, url, private in links)


def build_node_html(step, state, text, log_url, pinned, unlocked):
    column, row = step["place"]
    left = COLUMNS[column] / STAGE_WIDTH * 100
    top = ROWS[row] / STAGE_HEIGHT * 100
    tip_classes = ["oc-tip"]
    if row == 0:
        tip_classes.append("below")
    if column == 0:
        tip_classes.append("start")
    elif column == len(COLUMNS) - 1:
        tip_classes.append("end")
    if pinned:
        tip_classes.append("pinned")
    # The logo opens its step's log or, without one, the step's first address.
    visible_links = [link for link in step["links"] if unlocked or not link[2]]
    target = log_url or (visible_links[0][1] if visible_links else None)
    logo = (f'<svg class="oc-logo" viewBox="0 0 72 72" aria-hidden="true"><defs>'
            f'{LOGOS[step["key"]]}</svg>')
    logo_html = (f'<a href="{html.escape(target, quote=True)}" target="_blank" '
                 f'rel="noopener noreferrer" aria-label="{html.escape(step["title"], quote=True)}">{logo}</a>'
                 if target else f'<span>{logo}</span>')
    return (f'<div class="oc-node {state}" data-step="{step["key"]}" style="left:{left:.3f}%;top:{top:.3f}%">'
            f'<div class="{" ".join(tip_classes)}" role="tooltip"><h4>{html.escape(step["title"])}</h4>'
            f'<p>{html.escape(step["hint"])}</p>'
            f'<div class="oc-links">{build_links_html(step, log_url, unlocked)}</div></div>'
            f'{logo_html}<div class="oc-halo"></div>'
            f'<div class="oc-label">{html.escape(step["label"])}</div>'
            f'<div class="oc-state">{html.escape(text)}</div></div>')


def build_stage_html(palette, states, unlocked=False):
    """The whole stage: track, phase names and the nine logos, as one HTML document."""
    pinned = pick_pinned_step(states)
    phases = "".join(
        f'<div class="oc-phase" style="top:{(ROWS[index] - 78) / STAGE_HEIGHT * 100:.3f}%">'
        f'<b>{index + 1}</b>{html.escape(name)}</div>'
        for index, name in enumerate(PHASES))
    track = (f'<svg viewBox="0 0 {STAGE_WIDTH} {STAGE_HEIGHT}" aria-hidden="true"><defs>'
             '<linearGradient id="oc-track" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5eead4"/>'
             '<stop offset=".5" stop-color="#93c5fd"/><stop offset="1" stop-color="#c4b5fd"/></linearGradient></defs>'
             f'<path d="{TRACK}" fill="none" stroke="url(#oc-track)" stroke-width="10" stroke-linecap="round" opacity=".25"/>'
             f'<path d="{TRACK}" fill="none" stroke="{palette["reference"]}" stroke-width="1.6" '
             'stroke-dasharray="2 7" stroke-linecap="round" opacity=".7"/></svg>')
    nodes = "".join(build_node_html(step, *states[step["key"]], step["key"] == pinned, unlocked)
                    for step in STEPS)
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + '</head><body>'
            f'<div class="oc-stage" aria-label="Recorrido del pipeline semanal">{track}{phases}{nodes}</div>'
            '</body></html>')
# endregion
