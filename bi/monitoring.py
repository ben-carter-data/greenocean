"""Monitoreo y observabilidad (D-249, D-275): how we know that something failed, signal by signal.

D-275: the signals hang from the weekly run, at the stage where each one is born. The run goes along the middle; above
it, what anyone sees in the panel; below it, what only the author sees (GitHub and email); at the bottom, the state and
log GitHub keeps of every step. Only signals that exist in the code are drawn; each names the file that produces it (a
test checks it). The observability band of the pipeline diagram sums up five of them; this view is their full detail.

build_monitoring_html() returns one HTML document for st.iframe (CSS only, no script).
"""

import html

from bi import charts, doc_views, static_files

# region Constants
# Signals: (key, origin mark, origin, signal, what it records, where it is read, who reads it, file that produces it).
SIGNALS = [
    (
        "etl_run",
        "python",
        "Carga semanal",
        "Tabla etl_run",
        "una fila por carga: estado, filas leídas, cargadas y rechazadas",
        "Controles de datos · Centro de operación",
        "panel",
        "etl/pipeline.py",
    ),
    (
        "dbt_result",
        "dbt",
        "dbt build",
        "Tabla dbt_result",
        "el resultado de cada modelo y cada prueba de dbt",
        "Controles de datos · Pipeline y linaje",
        "panel",
        "etl/pipeline.py",
    ),
    (
        "agent_log",
        "python",
        "Agente de descarga",
        "Log del agente",
        "una línea por archivo descargado y su resultado",
        "log del paso en GitHub Actions",
        "autor",
        "agent/agent.py",
    ),
    (
        "actions_log",
        "github",
        "GitHub Actions",
        "Estado y log de cada paso",
        "verde, rojo o en curso, con su salida",
        "Centro de operación · «Log del paso»",
        "autor",
        ".github/workflows/semanal.yml",
    ),
    (
        "email",
        "github",
        "GitHub Actions",
        "Correo «Run failed»",
        "llega solo si el job semanal falla",
        "correo del autor",
        "autor",
        ".github/workflows/semanal.yml",
    ),
    (
        "issue",
        "github",
        "Paso 10 · Informe",
        "Issue «Informe semanal»",
        "estado de la carga y alertas de precio (K6)",
        "GitHub Issues",
        "autor",
        "bi/report.py",
    ),
    (
        "token",
        "streamlit",
        "Panel",
        "Aviso de vencimiento",
        "GITHUB_TOKEN o GITHUB_READ_TOKEN vence en 15 días o menos",
        "Centro de operación, tras la clave",
        "autor",
        "bi/control.py",
    ),
    (
        "hashes",
        "streamlit",
        "Panel",
        "Aviso de huellas",
        "un CSV local no coincide con su SHA-256 en manifest.json",
        "Controles de datos",
        "panel",
        "bi/quality.py",
    ),
]
# The stages of the weekly run, in order: (key, logo, name, what runs there).
STAGES = [
    ("descarga", "python", "Descarga", "agent.py"),
    ("construccion", "dbt", "Construcción", "pipeline.py · dbt"),
    ("pruebas", "pytest", "Pruebas", "pytest"),
    ("publicacion", "github", "Publicación", "release · informe"),
    ("panel", "streamlit", "Panel", "se duerme sin visitas"),
]
# Where each signal is born. The step log is born at every stage: it is the band under the run.
STAGE_OF_SIGNAL = {
    "etl_run": "publicacion",
    "dbt_result": "construccion",
    "agent_log": "descarga",
    "email": "pruebas",
    "issue": "publicacion",
    "token": "panel",
    "hashes": "panel",
}
EVERY_STEP = "actions_log"
LANES = {"panel": "Lo ve el panel", "autor": "Solo el autor"}
# endregion


# region «Monitoreo y observabilidad»: how we know that something failed
def esc(value):
    return html.escape(str(value))


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    grid = f"color-mix(in srgb, {border} {'38' if dark else '45'}%, transparent)"
    surface = f"color-mix(in srgb, {card} 72%, #000)" if dark else card
    glow = (
        f"0 0 0 1px color-mix(in srgb, {accent} 35%, transparent), 0 0 22px -6px color-mix(in srgb, {accent} 70%, transparent)"
        if dark
        else "0 8px 18px -14px rgba(15,40,90,.35)"
    )
    panel, author = "#22b35a", "#d9a400"
    return static_files.style(
        "monitoring.css",
        {
            'var(--go-text)': text,
            'var(--go-border)': border,
            'var(--go-surface)': surface,
            'var(--go-grid)': grid,
            'var(--go-ink)': ink,
            'var(--go-muted)': muted,
            'var(--go-panel)': panel,
            'var(--go-author)': author,
            'var(--go-accent)': accent,
            'var(--go-card)': card,
            'var(--go-glow)': glow,
        },
    )


def column(stage):
    """The grid column of a stage: after the lane labels, a stage and an arrow, in turn."""
    return 2 + 2 * [key for key, *_ in STAGES].index(stage)


def build_card(signal, row, grid_column):
    key, _, origin, name, records, where, who, produced_by = signal
    note = f"{name}: {records}. Se lee en: {where}. Lo produce {produced_by} ({origin})."
    return (
        f'<div class="card {who}" id="signal-{key}" style="grid-row:{row}; grid-column:{grid_column}" title="{esc(note)}">'
        f'<b>{esc(name)}</b><small>{esc(records)}</small><em>→ {esc(where)}</em></div>'
    )


def build_monitoring_html(palette):
    """Every signal of the project, hanging from the stage of the weekly run where it is born."""
    parts = [
        f'<div class="lane panel" style="grid-row:1; grid-column:1">{esc(LANES["panel"])}</div>',
        '<div class="lane run" style="grid-row:3; grid-column:1">La carga semanal</div>',
        f'<div class="lane autor" style="grid-row:5 / 8; grid-column:1">{esc(LANES["autor"])}</div>',
    ]
    for index, (key, slug, name, runs) in enumerate(STAGES):
        logo = doc_views.disc_logo("brand", slug).replace('<svg class="logo" ', '<svg ', 1)
        parts.append(
            f'<div class="stage" style="grid-row:3; grid-column:{column(key)}">{logo}'
            f'<span><b>{esc(name)}</b><small>{esc(runs)}</small></span></div>'
        )
        if index < len(STAGES) - 1:
            parts.append(f'<i class="h" style="grid-row:3; grid-column:{column(key) + 1}"></i>')
    for signal in SIGNALS:
        key, who = signal[0], signal[6]
        if key == EVERY_STEP:
            continue
        grid_column = column(STAGE_OF_SIGNAL[key])
        row, link = (1, 2) if who == "panel" else (5, 4)
        parts.append(build_card(signal, row, grid_column))
        parts.append(
            f'<i class="v {who}{" up" if who == "panel" else ""}" style="grid-row:{link}; grid-column:{grid_column}"></i>'
        )
    every = next(signal for signal in SIGNALS if signal[0] == EVERY_STEP)
    parts.append(
        build_card(every, 7, f"{column(STAGES[0][0])} / {column(STAGES[-2][0]) + 1}").replace(
            'class="card ', 'class="card band ', 1
        )
    )
    shown = len(SIGNALS)
    head = (
        f'<div class="mo-head"><h2>Cómo sabemos qué pasó</h2><p>{shown} señales · dónde nace cada una y quién la lee · '
        'pasa el cursor por una para ver qué registra y qué archivo la produce</p></div>'
    )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        + build_css(palette)
        + f'</head><body><div class="mo" role="group" aria-label="Monitoreo y observabilidad">{head}'
        f'<div class="mo-grid">{"".join(parts)}</div></div></body></html>'
    )


# endregion
