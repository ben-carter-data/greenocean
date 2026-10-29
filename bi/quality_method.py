"""«Método y calidad» (D-320, D-323, D-330, D-332): how the quality of the published data and of the code is managed.

Two tabs. «Resumen» says in two sentences what is measured and how it is going, and shows each indicator's failure
against its acceptable, data and code apart, with the insight of those out of their acceptable. «Informes» lists the
numbered reports (docs/calidad/informes, D-331), newest first. Every figure comes from a report; every text of an
indicator from docs/calidad/metas.json and docs/calidad/politica.json. A self-assessment, reviewed by the author.
Pure functions: no Streamlit; bi/dashboard.py draws the HTML. Texts come in both languages.
"""

from __future__ import annotations

import html
from typing import Any

from bi import charts, i18n, quality_metrics

# The five counts that are almost always zero share one line when they all meet their acceptable (D-332).
COUNTS = {
    "ruff_avisos": ("Ruff", "Ruff"),
    "mypy_errores": ("mypy", "mypy"),
    "bandit_altos": ("Bandit", "Bandit"),
    "pip_audit_vulnerabilidades": ("pip-audit", "pip-audit"),
    "secretos_sin_clasificar": ("secretos", "secrets"),
}
STATE_COLORS = {"cumple": "#199e70", "aviso": "#b8860b", "urgente": "#e07b22", "critico": None, "sin_medicion": None}
SKY = "#38bdf8"  # the sky-blue accent of the reports, on deep black (D-332)
DEEP = "#05070b"


def t(spanish: str, english: str) -> str:
    return english if i18n.is_english() else spanish


def number(value: Any, decimals: int = 0) -> str:
    """A figure with the marks of the reader's language; «—» when it was not measured."""
    return quality_metrics.number(value, decimals, i18n.is_english())


def read_page() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """(reports oldest first, goals, policy) as the files say them."""
    return (
        quality_metrics.read_reports(),
        quality_metrics.read(quality_metrics.GOALS_FILE),
        quality_metrics.read(quality_metrics.POLICY_FILE),
    )


def report_title(report: dict[str, Any]) -> str:
    return t(f"Informe de calidad N° {report['numero']}", f"Quality report No. {report['numero']}")


def sidebar_line(reports: list[dict[str, Any]]) -> str:
    """The line under the logo (D-332): it promises only what the page shows, the latest report."""
    if not reports:
        return t("Autoevaluación de calidad", "Quality self-assessment")
    return t(
        f"Autoevaluación de calidad · Informe N° {reports[-1]['numero']}",
        f"Quality self-assessment · Report No. {reports[-1]['numero']}",
    )


def failure_text(row: dict[str, Any], key: str = "falla") -> str:
    value = row[key]
    if value is None:
        return "—"
    decimals = 1 if isinstance(value, float) and value % 1 else 0
    unit = quality_metrics.unit_text(row["unidad_falla"], i18n.is_english())
    return number(value, decimals) + (f" {unit}" if unit else "")


def state_word(state: str, policy: dict[str, Any]) -> str:
    return t(*policy.get("estados", {}).get(state, [state, state]))


def build_header(report: dict[str, Any] | None) -> str:
    """Where the figures come from: the latest report, its date and the code it evaluated."""
    if not report:
        return f'<div class="qm-head">{html.escape(t("Todavía no hay informes.", "There are no reports yet."))}</div>'
    line = t(
        f"Autoevaluación automática, revisada y aprobada por el autor · {report_title(report)} · {report['fecha']} · "
        f"código {report['codigo_evaluado']}",
        f"Automatic self-assessment, reviewed and approved by the author · {report_title(report)} · {report['fecha']} · "
        f"code {report['codigo_evaluado']}",
    )
    return f'<div class="qm-head">{html.escape(line)}</div>'


def indicator_row(row: dict[str, Any], goals: dict[str, Any], policy: dict[str, Any]) -> str:
    """One indicator: its failure as a bar, the mark of its acceptable, the figure and the state; the rest on hover."""
    goal = goals.get(row["clave"], {})
    hint = " ".join(t(*goal[field]) for field in ("que_mide", "por_que") if field in goal) + " " + t(*row["insight"])
    failure, acceptable = row["falla"], row["falla_aceptable"]
    if failure is None:
        bar = f'<span class="qm-bar qm-empty">{html.escape(t("sin medición", "not measured"))}</span>'
    else:
        span = max(failure, acceptable or 0) * 1.3 or 1
        bar = (
            f'<span class="qm-bar"><i style="width:{min(100, failure / span * 100):.1f}%"></i>'
            f'<b style="left:{min(100, (acceptable or 0) / span * 100):.1f}%"></b></span>'
        )
    acceptable_text = t("aceptable", "acceptable") + " " + failure_text(row, "falla_aceptable")
    return (
        f'<div class="qm-row" title="{html.escape(hint.strip())}">'
        f'<span class="qm-name">{html.escape(t(*row["nombre"]))}</span>'
        f'{bar}<span class="qm-value">{html.escape(failure_text(row))}</span>'
        f'<span class="qm-limit">{html.escape(acceptable_text)}</span>'
        f'<span class="qm-state qm-{row["estado"]}">{html.escape(state_word(row["estado"], policy))}</span></div>'
    )


def counts_row(rows: list[dict[str, Any]], policy: dict[str, Any]) -> str:
    """The five counts in one line, when all of them meet their acceptable."""
    names = " · ".join(t(*COUNTS[row["clave"]]) for row in rows)
    figures = " · ".join(failure_text(row) for row in rows)
    hint = t(
        "Hallazgos de Ruff, errores de mypy, hallazgos altos de Bandit, vulnerabilidades y posibles secretos: "
        "todos en su aceptable.",
        "Ruff findings, mypy errors, high Bandit findings, vulnerabilities and possible secrets: "
        "all within their acceptable.",
    )
    return (
        f'<div class="qm-row" title="{html.escape(hint)}"><span class="qm-name">{html.escape(names)}</span>'
        f'<span class="qm-bar"><b style="left:0%"></b></span><span class="qm-value">{html.escape(figures)}</span>'
        f'<span class="qm-limit">{html.escape(t("aceptable 0", "acceptable 0"))}</span>'
        f'<span class="qm-state qm-cumple">{html.escape(state_word("cumple", policy))}</span></div>'
    )


def build_overview(report: dict[str, Any] | None, goals: dict[str, Any], policy: dict[str, Any]) -> str:
    """«Resumen»: two sentences, the data and the code side by side, and the insights that need attention."""
    if not report:
        return ""
    rows = report["indicadores"]
    data = [row for row in rows if row["tipo"] == "datos"]
    code = [row for row in rows if row["tipo"] == "codigo"]
    within, nonconforming, measured = quality_metrics.report_counts(report)
    plural = ("no conformidad", "non-conformity") if nonconforming == 1 else ("no conformidades", "non-conformities")
    lead = [
        t(
            f"Medimos {len(rows)} indicadores: {len(data)} de los datos que publicamos y {len(code)} del código que "
            "los trata, cada uno contra un aceptable fijado por el autor.",
            f"We measure {len(rows)} indicators: {len(data)} of the data we publish and {len(code)} of the code that "
            "treats it, each against an acceptable set by the author.",
        ),
        t(
            f"Hoy: {within} de {measured} medidos dentro de lo aceptable · {nonconforming} {plural[0]}.",
            f"Today: {within} of {measured} measured within the acceptable · {nonconforming} {plural[1]}.",
        ),
    ]
    counted = [row for row in code if row["clave"] in COUNTS]
    grouped = len(counted) == len(COUNTS) and all(row["estado"] == "cumple" for row in counted)
    code_rows = "".join(
        indicator_row(row, goals, policy) for row in code if not (grouped and row["clave"] in COUNTS)
    ) + (counts_row(counted, policy) if grouped else "")
    attention = sorted(
        (row for row in rows if row["estado"] in ("urgente", "critico")), key=lambda row: row["estado"] != "critico"
    )
    insights = "".join(
        f'<li class="qm-{row["estado"]}"><b>{html.escape(t(*row["nombre"]))} · '
        f'{html.escape(state_word(row["estado"], policy))}</b><span>{html.escape(t(*row["insight"]))}</span></li>'
        for row in attention
    )
    return (
        '<div class="qm-overview"><p class="qm-lead">'
        + " ".join(f"<span>{html.escape(text)}</span>" for text in lead)
        + f'</p><p class="qm-help">{html.escape(t(*policy.get("resumen", {}).get("como_leerlo", ["", ""])))}</p>'
        + '<div class="qm-groups">'
        + f'<section class="qm-group"><h4>{html.escape(t("Datos que publicamos", "Data we publish"))}</h4>'
        + "".join(indicator_row(row, goals, policy) for row in data)
        + f'</section><section class="qm-group"><h4>{html.escape(t("Código que los trata", "Code that treats them"))}</h4>'
        + code_rows
        + "</section></div>"
        + (f'<ul class="qm-insights">{insights}</ul>' if insights else "")
        + "</div>"
    )


def build_reports_table(
    reports: list[dict[str, Any]], every: list[dict[str, Any]] | None = None, link: Any = None
) -> str:
    """«Informes»: one row per report, newest first, with what it found and the change against the one before. The
    number opens the report; so does the PDF icon, whose viewer prints it (D-333). «every» holds all the reports, so
    a filtered list still compares each one with its true predecessor."""
    if not reports:
        return f'<p class="qm-note">{html.escape(t("Ningún informe coincide.", "No report matches."))}</p>'
    within_of = {report["numero"]: quality_metrics.report_counts(report)[0] for report in every or reports}
    body = []
    for report in sorted(reports, key=lambda item: -item["numero"]):
        within, nonconforming, measured = quality_metrics.report_counts(report)
        before = within_of.get(report["anterior"]) if report["anterior"] else None
        change = "—" if before is None else (f"+{within - before}" if within > before else str(within - before))
        href = html.escape(link(report["numero"])) if link else "#"
        pdf = t(f"Descargar el informe N° {report['numero']} en PDF", f"Download report No. {report['numero']} as PDF")
        body.append(
            f'<tr><td><a class="qm-open" href="{href}" target="_self"><b>{html.escape(t("N°", "No."))} {report["numero"]}</b></a></td>'
            f'<td>{html.escape(str(report["fecha"]))}</td><td>{html.escape(str(report["semana"] or "—"))}</td>'
            f'<td><code>{html.escape(str(report["codigo_evaluado"]))}</code></td>'
            f"<td>{within} / {measured}</td><td>{nonconforming}</td><td>{html.escape(change)}</td>"
            f'<td><a class="qm-pdf" href="{href}" target="_self" title="{html.escape(pdf)}" aria-label="{html.escape(pdf)}">PDF ↓</a></td></tr>'
        )
    head = [
        t("Informe", "Report"),
        t("Fecha", "Date"),
        t("Semana de datos", "Data week"),
        t("Código evaluado", "Evaluated code"),
        t("Dentro de lo aceptable", "Within the acceptable"),
        t("No conformidades", "Non-conformities"),
        t("Variación", "Change"),
        "PDF",
    ]
    columns = "".join(f"<th>{html.escape(cell)}</th>" for cell in head)
    return (
        f'<div class="qm-reports" tabindex="0"><table><thead><tr>{columns}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def build_report_view(report: dict[str, Any], policy: dict[str, Any]) -> str:
    """One report, as the dialog shows it: its identity and every indicator with its reading."""
    within, nonconforming, measured = quality_metrics.report_counts(report)
    week = report["semana"] or "—"
    identity = t(
        f"{report['fecha']} · semana de datos {week} · código {report['codigo_evaluado']} · "
        f"{within} de {measured} dentro de lo aceptable · {nonconforming} no conformidades",
        f"{report['fecha']} · data week {week} · code {report['codigo_evaluado']} · "
        f"{within} of {measured} within the acceptable · {nonconforming} non-conformities",
    )
    rows = "".join(
        f'<tr><td><b>{html.escape(t(*row["nombre"]))}</b></td>'
        f"<td>{html.escape(t('Datos', 'Data') if row['tipo'] == 'datos' else t('Código', 'Code'))}</td>"
        f"<td>{html.escape(failure_text(row))}</td><td>{html.escape(failure_text(row, 'falla_aceptable'))}</td>"
        f'<td><span class="qm-state qm-{row["estado"]}">{html.escape(state_word(row["estado"], policy))}</span></td>'
        f"<td>{html.escape(t(*row['insight']))}</td></tr>"
        for row in report["indicadores"]
    )
    head = [
        t("Indicador", "Indicator"),
        t("Tipo", "Type"),
        t("Falla", "Failure"),
        t("Aceptable", "Acceptable"),
        t("Estado", "State"),
        t("Lectura", "Reading"),
    ]
    columns = "".join(f"<th>{html.escape(cell)}</th>" for cell in head)
    return (
        f'<div class="qm-report"><h3>{html.escape(report_title(report))}</h3><p>{html.escape(identity)}</p>'
        f'<div class="qm-reports"><table><thead><tr>{columns}</tr></thead><tbody>{rows}</tbody></table></div></div>'
    )


def build_alert(
    reports: list[dict[str, Any]],
    goals: dict[str, Any],
    policy: dict[str, Any],
    nonconformities: list[dict[str, Any]],
    link: Any = None,
    failed_load: str | None = None,
) -> str:
    """«Acción requerida» (D-335), for the author only: every indicator of the latest report out of its acceptable,
    the critical ones first, each with its level, failure against the acceptable, why it matters, the automatic
    diagnosis, the suggested action and the report. It reads the report; it computes nothing of its own. Nothing here
    holds a key or an internal path: only what the public reports already show, plus the cause and the action."""
    texts = policy.get("alerta", {})
    if not reports:
        return ""
    latest = reports[-1]
    out = sorted(
        (row for row in latest["indicadores"] if row["estado"] in ("urgente", "critico")),
        key=lambda row: row["estado"] != "critico",
    )
    day = str(latest["fecha"])[:10]
    parts = []
    if failed_load:
        parts.append(f'<p class="qm-alert-load">{html.escape(t(*texts["falla_carga"]).format(dia=failed_load))}</p>')
    for row in out:
        goal = goals.get(row["clave"], {})
        diagnosis = row.get("diagnostico") or quality_metrics.diagnose(row, latest, reports, policy)
        diagnosis = diagnosis[1 if i18n.is_english() else 0]
        record = next(
            (
                item
                for item in nonconformities
                if item.get("informe") == latest["numero"] and item.get("indicador") == row["clave"]
            ),
            {},
        )
        cause = record.get("causa")
        cause_line = t(*cause) if cause else diagnosis["origen"]
        action = t(*goal["accion"]) if goal.get("accion") else ""
        parts.append(
            f'<div class="qm-alert qm-{row["estado"]}"><h4>{html.escape(state_word(row["estado"], policy))} · '
            f'{html.escape(t(*row["nombre"]))}</h4>'
            f'<p class="qm-alert-figure">{html.escape(t("Falla", "Failure"))} {html.escape(failure_text(row))} · '
            f'{html.escape(t("aceptable", "acceptable"))} {html.escape(failure_text(row, "falla_aceptable"))}</p>'
            f'<p><b>{html.escape(t("Por qué importa", "Why it matters"))}:</b> {html.escape(t(*goal["por_que"]))}</p>'
            f'<p><b>{html.escape(t("Qué falló", "What failed"))}:</b> {html.escape(diagnosis["donde"])} '
            f'{html.escape(diagnosis["desde"])}</p>'
            f'<p><b>{html.escape(t("Causa", "Cause"))}:</b> {html.escape(cause_line)}</p>'
            f'<p><b>{html.escape(t("Acción sugerida", "Suggested action"))}:</b> {html.escape(action)}</p></div>'
        )
    if not parts:
        return ""
    href = html.escape(link(latest["numero"])) if link else "#"
    parts.append(
        f'<p class="qm-alert-foot">{html.escape(t(*texts["anotar"]))} · {html.escape(t("Última medición", "Last measurement"))}: '
        f'{html.escape(day)} · <a href="{href}" target="_self">{html.escape(t(*texts["ver_informe"]))} '
        f'{html.escape(t("N°", "No."))} {latest["numero"]}</a></p>'
    )
    return '<div class="qm-alerts">' + "".join(parts) + "</div>"


def build_css(palette: dict[str, str]) -> str:
    ink, text, muted, border, card = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card_border"],
        palette["card"],
    )
    soft = charts.legible(muted, palette["background"])
    colors = {state: charts.legible(color or palette["rise"], card) for state, color in STATE_COLORS.items()}
    colors["sin_medicion"] = charts.legible(muted, card)
    on_deep = {state: charts.legible(color or "#ef4444", DEEP) for state, color in STATE_COLORS.items()}
    on_deep["sin_medicion"] = charts.legible("#9aa4b2", DEEP)
    states = "".join(f".qm-{state} {{ color:{color}; }}\n" for state, color in colors.items())
    deep_states = "".join(f".qm-reports .qm-{state} {{ color:{color}; }}\n" for state, color in on_deep.items())
    return f"""<style>
.qm-head {{ margin:0 0 10px; font-size:12.5px; color:{soft}; }}
.qm-lead {{ margin:0 0 14px !important; font-size:15px !important; line-height:1.5 !important; color:{ink}; max-width:920px; }}
.qm-help {{ margin:-8px 0 14px !important; max-width:920px; font-size:11.5px !important; line-height:1.4 !important; color:{soft}; }}
.qm-groups {{ display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:14px; }}
.qm-group {{ border:1px solid {border}; border-radius:14px; background:{card}; padding:12px 16px 10px; min-width:0; }}
.qm-group h4 {{ margin:0 0 8px !important; padding:0 !important; font-size:11px !important; letter-spacing:.08em;
  text-transform:uppercase; color:{soft}; }}
.qm-row {{ display:grid; grid-template-columns:minmax(0, 1.5fr) minmax(60px, 1fr) auto auto auto; gap:10px; align-items:center;
  padding:7px 0; border-top:1px solid color-mix(in srgb, {border} 60%, transparent); font-size:13px; color:{text}; cursor:help; }}
.qm-group h4 + .qm-row {{ border-top:0; }}
.qm-name {{ color:{ink}; font-weight:600; min-width:0; }}
.qm-bar {{ position:relative; height:6px; border-radius:3px; background:color-mix(in srgb, {border} 70%, transparent); }}
.qm-bar i {{ position:absolute; left:0; top:0; bottom:0; border-radius:3px; background:{SKY}; }}
.qm-bar b {{ position:absolute; top:-4px; width:2px; height:14px; background:{ink}; border-radius:1px; }}
.qm-bar.qm-empty {{ height:auto; background:none; font-size:11.5px; color:{soft}; }}
.qm-value {{ font-variant-numeric:tabular-nums; color:{ink}; text-align:right; white-space:nowrap; }}
.qm-limit {{ font-size:11.5px; color:{soft}; white-space:nowrap; }}
.qm-state {{ font-size:11.5px; font-weight:700; white-space:nowrap; }}
{states}.qm-insights {{ list-style:none; margin:14px 0 0; padding:0; }}
.qm-insights li {{ display:flex; flex-wrap:wrap; gap:4px 10px; padding:9px 12px; margin-bottom:6px; border-radius:10px;
  border:1px solid currentColor; background:color-mix(in srgb, currentColor 7%, transparent); font-size:13px; }}
.qm-insights li span {{ color:{text}; }}
.qm-note {{ font-size:13px; color:{text}; }}
.st-key-quality_filters {{ gap:10px !important; flex-wrap:wrap !important; margin-bottom:8px; }}
.st-key-quality_filters > div {{ flex:0 1 180px !important; min-width:130px; }}
.qm-reports {{ overflow:auto; max-height:calc(100vh - 300px); border-radius:14px; background:{DEEP};
  border:1px solid color-mix(in srgb, {SKY} 35%, #1b2433); box-shadow:0 0 28px -14px {SKY}; }}
.qm-reports table {{ width:100%; border-collapse:separate; border-spacing:0; margin:0; font-size:13px; }}
.qm-reports thead th {{ position:sticky; top:0; z-index:1; background:{DEEP} !important; color:{SKY} !important; font-size:11px;
  font-weight:700; text-transform:uppercase; letter-spacing:.07em; text-align:left; padding:10px 14px !important; border:0 !important;
  border-bottom:1px solid color-mix(in srgb, {SKY} 40%, transparent) !important; }}
.qm-reports td {{ padding:9px 14px !important; color:#d7dee9; border:0 !important; vertical-align:top;
  border-bottom:1px solid #141b27 !important; background:transparent !important; }}
.qm-reports td b {{ color:#f3f7fc; }} .qm-reports code {{ color:{SKY}; background:transparent; }}
.qm-reports a.qm-open {{ text-decoration:none !important; }} .qm-reports a.qm-open b {{ color:{SKY}; text-decoration:underline; }}
.qm-reports a.qm-pdf {{ color:{SKY} !important; text-decoration:none !important; border:1px solid color-mix(in srgb, {SKY} 50%, transparent);
  border-radius:6px; padding:1px 8px; font-size:11.5px; white-space:nowrap; }}
.qm-reports tbody tr:hover td {{ background:color-mix(in srgb, {SKY} 7%, transparent) !important; }}
{deep_states}.qm-report h3 {{ margin:0 0 4px !important; font-size:20px !important; }}
.qm-report p {{ margin:0 0 12px !important; font-size:12.5px; color:{soft}; }}
/* D-336: the × of the report and alert dialogs sits in the top right corner with a face of its own, readable over the
   viewer's black and over any theme; it used to float at the top center and stick out of its card. */
div[data-testid="stDialog"] [role="dialog"] button[aria-label="Close"] {{ position:absolute !important; right:14px; top:14px;
  z-index:30; width:30px; height:30px; min-height:0; padding:0; border-radius:50%; background:#0d1320 !important;
  border:1px solid #243046 !important; }}
div[data-testid="stDialog"] [role="dialog"] button[aria-label="Close"] svg, div[data-testid="stDialog"] [role="dialog"] button[aria-label="Close"] [data-testid="stIconMaterial"] {{
  color:#e6edf6 !important; fill:#e6edf6 !important; }}
.qm-alerts {{ max-height:60vh; overflow:auto; }}
.qm-alert {{ border:1px solid currentColor; border-radius:12px; padding:10px 14px 4px; margin-bottom:10px;
  background:color-mix(in srgb, currentColor 6%, transparent); }}
.qm-alert h4 {{ margin:0 0 4px !important; padding:0 !important; font-size:14px !important; color:inherit; }}
.qm-alert p {{ margin:0 0 6px !important; font-size:13px; color:{text}; }} .qm-alert p b {{ color:{ink}; }}
.qm-alert p.qm-alert-figure {{ font-variant-numeric:tabular-nums; color:{ink}; }}
.qm-alert-load {{ font-size:13px; color:{text}; }} .qm-alert-foot {{ font-size:12px; color:{soft}; }}
@media (max-width:1100px) {{ .qm-groups {{ grid-template-columns:minmax(0, 1fr); }} }}
</style>"""
