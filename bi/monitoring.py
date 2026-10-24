"""Monitoreo y observabilidad (D-249): how we know that something failed, signal by signal.

Each row is one signal, read from left to right: where it starts, what it leaves and where, and where it is read and by
whom. Only signals that exist in the code are drawn; each names the file that produces it (a test checks it). The
observability band of the pipeline diagram shows the same signals along the run; this view is their full detail.

build_monitoring_html() returns one HTML document for st.iframe (CSS only, no script).
"""
import html

from bi import charts, doc_views, quality_view

WIDTH, HEIGHT = 1000, 600
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
COLUMNS = (("Origen", 20), ("Señal", 268), ("Qué registra", 508), ("Dónde se lee", 772))
# Card x ranges per column, from COLUMNS.
CARD_X = {"origin": (20, 220), "signal": (268, 212), "records": (508, 236), "where": (772, 216)}
ROW_TOP, ROW_HEIGHT, ROW_GAP = 44, 60, 8


def esc(value):
    return html.escape(str(value))


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    shadow = "rgba(0,0,0,.4)" if dark else "rgba(15,39,71,.14)"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
svg.mon {{ display:block; width:100%; height:auto; overflow:visible; }}
.col {{ font-size:12.5px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; fill:{ink}; }}
.card {{ fill:{card}; stroke:{border}; stroke-width:1.1; filter:drop-shadow(0 6px 8px {shadow}); }}
.signal .card {{ stroke:{accent}; }}
.title {{ font-size:13.5px; font-weight:600; fill:{ink}; }}
.detail {{ font-size:12.5px; fill:{muted}; }}
.file {{ font:400 12px ui-monospace, SFMono-Regular, Menlo, monospace; fill:{muted}; }}
.who {{ font-size:12px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }}
.who.panel {{ fill:#22b35a; }} .who.autor {{ fill:#d9a400; }}
.line {{ fill:none; stroke:{accent}; stroke-width:1.8; }}
</style>"""


def mark(slug, x, y, size):
    return doc_views.disc_logo("brand", slug).replace(
        '<svg class="logo" ', f'<svg x="{x}" y="{y}" width="{size}" height="{size}" ', 1)


def text_lines(css_class, x, top, lines, first=None):
    """One or two lines centred in a 60-unit card, or starting at `first` when a label sits above them."""
    start = first if first is not None else top + (35 if len(lines) == 1 else 27)
    return "".join(f'<text class="{css_class}" x="{x}" y="{start + 16 * k}">{esc(line)}</text>' for k, line in enumerate(lines))


def build_row(index, signal):
    key, slug, origin, name, records, where, who, produced_by = signal
    top = ROW_TOP + index * (ROW_HEIGHT + ROW_GAP)
    middle = top + ROW_HEIGHT / 2
    (ox, ow), (sx, sw), (rx, rw), (wx, ww) = (CARD_X[k] for k in ("origin", "signal", "records", "where"))
    parts = [f'<rect class="card" x="{ox}" y="{top}" width="{ow}" height="{ROW_HEIGHT}" rx="12"/>' + mark(slug, ox + 8, top + 14, 32)
             + f'<text class="title" x="{ox + 48}" y="{top + 26}">{esc(origin)}</text>'
             f'<text class="file" x="{ox + 48}" y="{top + 44}">{esc(produced_by.rsplit("/", 1)[-1])}</text>',
             f'<g class="signal"><rect class="card" x="{sx}" y="{top}" width="{sw}" height="{ROW_HEIGHT}" rx="12"/>'
             + quality_view.build_icon_svg("chart").replace('<svg class="qa-icon" ', f'<svg x="{sx + 8}" y="{top + 14}" width="32" height="32" ', 1)
             + text_lines("title", sx + 48, top, doc_views.wrap(name, 20)[:2]) + '</g>',
             f'<rect class="card" x="{rx}" y="{top}" width="{rw}" height="{ROW_HEIGHT}" rx="12"/>'
             + text_lines("detail", rx + 12, top, doc_views.wrap(records, 34)[:2]),
             f'<rect class="card" x="{wx}" y="{top}" width="{ww}" height="{ROW_HEIGHT}" rx="12"/>'
             f'<text class="who {who}" x="{wx + 12}" y="{top + 19}">{"panel" if who == "panel" else "autor"}</text>'
             + text_lines("detail", wx + 12, top, doc_views.wrap(where, 30)[:2], first=top + 36)]
    for (left, width), (right, _) in ((CARD_X["origin"], CARD_X["signal"]), (CARD_X["signal"], CARD_X["records"]),
                                      (CARD_X["records"], CARD_X["where"])):
        parts.append(f'<path class="line" d="M{left + width} {middle} L{right - 2} {middle}" marker-end="url(#mon-head)"/>')
    return f'<g id="signal-{key}">{"".join(parts)}</g>'


def build_monitoring_html(palette):
    """Every signal of the project, from where it starts to where it is read."""
    head = (f'<defs><marker id="mon-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>')
    columns = "".join(f'<text class="col" x="{x}" y="28">{esc(name)}</text>' for name, x in COLUMNS)
    rows = "".join(build_row(index, signal) for index, signal in enumerate(SIGNALS))
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body>{quality_view.DEFS}<svg class="mon" viewBox="0 0 {WIDTH} {HEIGHT}" '
            f'preserveAspectRatio="xMidYMid meet" role="img" aria-label="Monitoreo y observabilidad">{head}{columns}{rows}'
            '</svg></body></html>')
