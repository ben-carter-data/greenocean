"""Monitoreo y observabilidad (D-249, D-275): how we know that something failed, signal by signal.

D-275: the signals hang from the weekly run, at the stage where each one is born. The run goes along the middle; above
it, what anyone sees in the panel; below it, what only the author sees (GitHub and email); at the bottom, the state and
log GitHub keeps of every step. Only signals that exist in the code are drawn; each names the file that produces it (a
test checks it). The observability band of the pipeline diagram sums up five of them; this view is their full detail.

build_monitoring_html() returns one HTML document for st.iframe (CSS only, no script).
"""
import html

from bi import charts, doc_views

# Signals: (key, origin mark, origin, signal, what it records, where it is read, who reads it, file that produces it).
SIGNALS = [
    ("etl_run", "python", "Carga semanal", "Tabla etl_run", "una fila por carga: estado, filas leídas, cargadas y rechazadas",
     "Calidad y auditoría · Centro de operación", "panel", "etl/pipeline.py"),
    ("dbt_result", "dbt", "dbt build", "Tabla dbt_result", "el resultado de cada modelo y cada prueba de dbt",
     "Calidad y auditoría · Pipeline y linaje", "panel", "etl/pipeline.py"),
    ("agent_log", "python", "Agente de descarga", "Log del agente", "una línea por archivo descargado y su resultado",
     "log del paso en GitHub Actions", "autor", "agent/agent.py"),
    ("actions_log", "github", "GitHub Actions", "Estado y log de cada paso", "verde, rojo o en curso, con su salida",
     "Centro de operación · «Log del paso»", "autor", ".github/workflows/semanal.yml"),
    ("email", "github", "GitHub Actions", "Correo «Run failed»", "llega solo si el job semanal falla",
     "correo del autor", "autor", ".github/workflows/semanal.yml"),
    ("issue", "github", "Paso 9 · Informe", "Issue «Informe semanal»", "estado de la carga y alertas de precio (K6)",
     "GitHub Issues", "autor", "bi/report.py"),
    ("token", "streamlit", "Panel", "Aviso de vencimiento", "el token de GitHub vence en menos de 14 días",
     "Centro de operación, tras la clave", "autor", "bi/control.py"),
    ("hashes", "streamlit", "Panel", "Aviso de huellas", "un CSV local no coincide con su SHA-256 en manifest.json",
     "Calidad y auditoría", "panel", "bi/quality.py"),
]
# The stages of the weekly run, in order: (key, logo, name, what runs there).
STAGES = [("descarga", "python", "Descarga", "agent.py"), ("construccion", "dbt", "Construcción", "pipeline.py · dbt"),
          ("pruebas", "pytest", "Pruebas", "pytest"), ("publicacion", "github", "Publicación", "release · informe"),
          ("panel", "streamlit", "Panel", "siempre en línea")]
# Where each signal is born. The step log is born at every stage: it is the band under the run.
STAGE_OF_SIGNAL = {"etl_run": "publicacion", "dbt_result": "construccion", "agent_log": "descarga", "email": "pruebas",
                   "issue": "publicacion", "token": "panel", "hashes": "panel"}
EVERY_STEP = "actions_log"
LANES = {"panel": "Lo ve el panel", "autor": "Solo el autor"}


def esc(value):
    return html.escape(str(value))


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    grid = f"color-mix(in srgb, {border} {'38' if dark else '45'}%, transparent)"
    surface = f"color-mix(in srgb, {card} 72%, #000)" if dark else card
    glow = (f"0 0 0 1px color-mix(in srgb, {accent} 35%, transparent), 0 0 22px -6px color-mix(in srgb, {accent} 70%, transparent)"
            if dark else "0 8px 18px -14px rgba(15,40,90,.35)")
    panel, author = "#22b35a", "#d9a400"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:400 14px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.mo {{ padding:11px 20px 13px; border:1px solid {border}; border-radius:18px; background-color:{surface};
  background-image:linear-gradient({grid} 1px, transparent 1px), linear-gradient(90deg, {grid} 1px, transparent 1px); background-size:30px 30px; }}
.mo-head {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:2px 14px; margin-bottom:6px; }}
.mo-head h2 {{ margin:0; font-size:20px; font-weight:700; color:{ink}; }}
.mo-head p {{ margin:0; font:400 12.5px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; color:{muted}; }}
.mo-grid {{ display:grid; align-items:stretch;
  grid-template-columns:74px minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr);
  grid-template-rows:auto 20px auto 20px auto 12px auto; }}
.mo .lane {{ align-self:center; padding-right:8px; font:700 10px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace;
  letter-spacing:.14em; text-transform:uppercase; color:var(--c); }}
.mo .lane.panel {{ --c:{panel}; }} .mo .lane.autor {{ --c:{author}; }} .mo .lane.run {{ --c:{accent}; }}
.mo .card {{ padding:8px 10px 9px; border:1px solid {border}; border-left:3px solid var(--c); border-radius:12px;
  background:color-mix(in srgb, {card} 92%, transparent); cursor:default; }}
.mo .card.panel {{ --c:{panel}; }} .mo .card.autor {{ --c:{author}; }}
.mo .card b {{ display:block; font-size:14px; font-weight:700; line-height:1.25; color:{ink}; }}
/* What a signal records is on hover: the card says what it is and where it is read. The band keeps it, on its one line. */
.mo .card small {{ display:none; }}
.mo .card.band small {{ display:inline; margin:0; font-size:12px; color:{muted}; }}
.mo .card em {{ display:block; margin-top:4px; font-style:normal; font-size:12px; line-height:1.3; color:var(--c); }}
.mo .card:hover {{ border-color:var(--c); }}
.mo .stage {{ display:flex; align-items:center; gap:7px; padding:8px 8px; border:1px solid {accent}; border-radius:14px;
  background:color-mix(in srgb, {card} 92%, transparent); box-shadow:{glow}; }}
.mo .stage svg {{ flex:none; width:26px; height:26px; }}
.mo .stage span {{ min-width:0; }}
.mo .stage b {{ display:block; font-size:14px; font-weight:700; color:{ink}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.mo .stage small {{ display:block; font:400 11px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; color:{muted}; }}
.mo .h {{ position:relative; align-self:center; height:12px; }}
.mo .h::before {{ content:""; position:absolute; left:3px; right:8px; top:5px; border-top:2px dashed {accent}; opacity:.85; }}
.mo .h::after {{ content:""; position:absolute; right:1px; top:1px; border:5px solid transparent; border-left:8px solid {accent}; }}
.mo .v {{ position:relative; }}
.mo .v::before {{ content:""; position:absolute; left:50%; top:2px; bottom:8px; border-left:2px dashed var(--c); opacity:.9; }}
.mo .v::after {{ content:""; position:absolute; left:calc(50% - 4px); bottom:0; border:5px solid transparent; border-top:8px solid var(--c); }}
.mo .v.up::before {{ top:8px; bottom:2px; }}
.mo .v.up::after {{ top:-2px; bottom:auto; border-top-color:transparent; border-bottom:8px solid var(--c); }}
.mo .v.panel {{ --c:{panel}; }} .mo .v.autor {{ --c:{author}; }}
.mo .band {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:2px 10px; }}
.mo .band b {{ display:inline; }} .mo .band em {{ display:inline; margin:0; }}
@media (max-width:760px) {{
  .mo-grid {{ grid-template-columns:minmax(0, 1fr); grid-template-rows:none; row-gap:8px; }}
  .mo-grid > * {{ grid-column:1 !important; grid-row:auto !important; }}
  .mo .h, .mo .v {{ display:none; }} .mo .lane {{ padding-top:6px; }}
}}
</style>"""


def column(stage):
    """The grid column of a stage: after the lane labels, a stage and an arrow, in turn."""
    return 2 + 2 * [key for key, *_ in STAGES].index(stage)


def build_card(signal, row, grid_column):
    key, _, origin, name, records, where, who, produced_by = signal
    note = f"{name}: {records}. Se lee en: {where}. Lo produce {produced_by} ({origin})."
    return (f'<div class="card {who}" id="signal-{key}" style="grid-row:{row}; grid-column:{grid_column}" title="{esc(note)}">'
            f'<b>{esc(name)}</b><small>{esc(records)}</small><em>→ {esc(where)}</em></div>')


def build_monitoring_html(palette):
    """Every signal of the project, hanging from the stage of the weekly run where it is born."""
    parts = [f'<div class="lane panel" style="grid-row:1; grid-column:1">{esc(LANES["panel"])}</div>',
             '<div class="lane run" style="grid-row:3; grid-column:1">La carga semanal</div>',
             f'<div class="lane autor" style="grid-row:5 / 8; grid-column:1">{esc(LANES["autor"])}</div>']
    for index, (key, slug, name, runs) in enumerate(STAGES):
        logo = doc_views.disc_logo("brand", slug).replace('<svg class="logo" ', '<svg ', 1)
        parts.append(f'<div class="stage" style="grid-row:3; grid-column:{column(key)}">{logo}'
                     f'<span><b>{esc(name)}</b><small>{esc(runs)}</small></span></div>')
        if index < len(STAGES) - 1:
            parts.append(f'<i class="h" style="grid-row:3; grid-column:{column(key) + 1}"></i>')
    for signal in SIGNALS:
        key, who = signal[0], signal[6]
        if key == EVERY_STEP:
            continue
        grid_column = column(STAGE_OF_SIGNAL[key])
        row, link = (1, 2) if who == "panel" else (5, 4)
        parts.append(build_card(signal, row, grid_column))
        parts.append(f'<i class="v {who}{" up" if who == "panel" else ""}" style="grid-row:{link}; grid-column:{grid_column}"></i>')
    every = next(signal for signal in SIGNALS if signal[0] == EVERY_STEP)
    parts.append(build_card(every, 7, f"{column(STAGES[0][0])} / {column(STAGES[-2][0]) + 1}").replace('class="card ', 'class="card band ', 1))
    shown = len(SIGNALS)
    head = (f'<div class="mo-head"><h2>Cómo sabemos qué pasó</h2><p>{shown} señales · dónde nace cada una y quién la lee · '
            'pasa el cursor por una para ver qué registra y qué archivo la produce</p></div>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body><div class="mo" role="group" aria-label="Monitoreo y observabilidad">{head}'
            f'<div class="mo-grid">{"".join(parts)}</div></div></body></html>')
