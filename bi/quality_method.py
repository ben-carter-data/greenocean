"""«Plan de calidad» (D-320, D-323, D-331, D-333, D-571): the archive of the numbered quality reports.

One line names the latest report: its date, how many of its indicators are within the acceptable and its
non-conformities. Under it, the reports of a series (docs/calidad/informes, D-331), newest first, each opening as a
document with its PDF. Today's state of the data lives in «Controles de datos» and the failures in «Cambios e
incidentes». The module also writes «Acción requerida», the author's alert from the latest report (D-335). Every figure
comes from a report; every text of an indicator from docs/calidad/metas.json and docs/calidad/politica.json. A
self-assessment, reviewed by the author. Pure functions: no Streamlit; bi/page_quality.py draws the page and
bi/app_frame.py the alert. Texts come in both languages.
"""

from __future__ import annotations

import html
from typing import Any

from bi import charts, i18n, quality_metrics, static_files

# region Constants
STATE_COLORS = {"cumple": "#199e70", "aviso": "#b8860b", "urgente": "#e07b22", "critico": None, "sin_medicion": None}
STALE_DAYS = 8
# endregion


# region Words and numbers
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
    return quality_metrics.report_name(report, i18n.is_english())  # D-431: the weekly series or C-1 to C-7


def failure_text(row: dict[str, Any], key: str = "falla") -> str:
    value = row[key]
    if value is None:
        return "—"
    decimals = quality_metrics.percent_decimals(value) if isinstance(value, float) and value % 1 else 0
    unit = quality_metrics.unit_text(row["unidad_falla"], i18n.is_english())
    return number(value, decimals) + (f" {unit}" if unit else "")


def state_word(state: str, policy: dict[str, Any]) -> str:
    return t(*policy.get("estados", {}).get(state, [state, state]))


# endregion


# region The latest report
def build_header(report: dict[str, Any] | None) -> str:
    """D-571: the page's first line names the latest report, its date, how many of its indicators are within the
    acceptable and its non-conformities; how the report is made, on hover (D-566)."""
    if not report:
        return f'<div class="qm-head">{html.escape(t("Todavía no hay informes.", "There are no reports yet."))}</div>'
    within, nonconforming, measured = quality_metrics.report_counts(report)
    day = str(report["fecha"])[:10]
    findings = (
        t("no conformidad", "non-conformity") if nonconforming == 1 else t("no conformidades", "non-conformities")
    )
    line = t(
        f"{report_title(report)} · {day} · {within} de {measured} dentro de lo aceptable · {nonconforming} {findings}",
        f"{report_title(report)} · {day} · {within} of {measured} within the acceptable · {nonconforming} {findings}",
    )
    process = t(
        "Autoevaluación automática, revisada y aprobada por el autor.",
        "Automatic self-assessment, reviewed and approved by the author.",
    )
    return f'<div class="qm-head" title="{html.escape(process)}">{html.escape(line)}</div>'


# endregion


# region The weekly reports
def report_summary(report: dict[str, Any]) -> str:
    """The one line of a report in the list: its number, date and how many indicators are within the acceptable."""
    within, _, measured = quality_metrics.report_counts(report)
    code = quality_metrics.report_code(report, i18n.is_english())
    return t(
        f"{code} · {report['fecha']} · {within} / {measured} dentro de lo aceptable",
        f"{code} · {report['fecha']} · {within} / {measured} within the acceptable",
    )


def build_report_detail(report: dict[str, Any], every: list[dict[str, Any]] | None = None) -> str:
    """What a report row shows when it opens: data week, evaluated code, non-conformities and the change against the
    report before it. «every» holds all the reports, so a filtered list still compares each one with its true
    predecessor."""
    within, nonconforming, _ = quality_metrics.report_counts(report)
    within_of = {item["numero"]: quality_metrics.report_counts(item)[0] for item in every or [report]}
    before = within_of.get(report["anterior"]) if report["anterior"] else None
    change = "—" if before is None else (f"+{within - before}" if within > before else str(within - before))
    rows = (
        (
            t("Semana de datos", "Data week"),
            html.escape(i18n.tr_week(report["semana"], True) if report["semana"] else "—"),
        ),
        (t("Código evaluado", "Evaluated code"), f"<code>{html.escape(str(report['codigo_evaluado']))}</code>"),
        (t("No conformidades", "Non-conformities"), str(nonconforming)),
        (t("Variación", "Change"), html.escape(change)),
    )
    body = "".join(f"<li><b>{html.escape(label)}:</b> {value}</li>" for label, value in rows)
    return f'<ul class="cr-detail qm-detail">{body}</ul>'


# endregion


# region Alerts
def record_of(report: dict[str, Any], row: dict[str, Any], nonconformities: list[dict[str, Any]]) -> dict[str, Any]:
    """The non-conformity of this indicator in this report, or {}."""
    return next(
        (
            item
            for item in nonconformities
            if quality_metrics.same_report(item, report) and item.get("indicador") == row["clave"]
        ),
        {},
    )


def open_rows(report: dict[str, Any], nonconformities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The indicators of a report out of their acceptable that are not resolved yet (D-419), the critical first."""
    return sorted(
        (
            row
            for row in report["indicadores"]
            if row["estado"] in ("urgente", "critico")
            and not quality_metrics.is_resolved(record_of(report, row, nonconformities))
        ),
        key=lambda row: row["estado"] != "critico",
    )


def build_alert(
    reports: list[dict[str, Any]],
    goals: dict[str, Any],
    policy: dict[str, Any],
    nonconformities: list[dict[str, Any]],
    link: Any = None,
    failed_load: str | None = None,
    today: Any = None,
    incidents: list[dict[str, Any]] | None = None,
) -> str:
    """«Acción requerida» (D-335), for the author only: every indicator of the latest report out of its acceptable,
    the critical ones first, each with its level, failure against the acceptable, why it matters, the automatic
    diagnosis, the suggested action and the report. It reads the report; it computes nothing of its own. Nothing here
    holds a key or an internal path: only what the public reports already show, plus the cause and the action.
    D-419: a non-conformity the author marked resolved does not appear; the cause of an indicator is, in order, the one
    the register writes, the external incident of its period, or the automatic diagnosis."""
    texts = policy.get("alerta", {})
    if not reports:
        return ""
    latest = reports[-1]
    out = open_rows(latest, nonconformities)
    day = str(latest["fecha"])[:10]
    parts = []
    # D-361: a report older than STALE_DAYS is an old picture, not today's state: it says so and loses its alarm colours.
    stale = is_stale(latest, today)
    if stale:
        parts.append(
            f'<p class="qm-alert-stale">{html.escape(t(*texts["antigua"]).format(dia=f"{day[8:10]}-{day[5:7]}"))}</p>'
        )
    if failed_load:
        parts.append(f'<p class="qm-alert-load">{html.escape(t(*texts["falla_carga"]).format(dia=failed_load))}</p>')
    for row in out:
        goal = goals.get(row["clave"], {})
        # D-419: recomputed from the report's own measurement, so each language reads its own words; the report keeps
        # its stored copy untouched (a report is never edited).
        diagnosis = quality_metrics.diagnose(row, latest, reports, policy)[1 if i18n.is_english() else 0]
        cause = record_of(latest, row, nonconformities).get("causa")
        incident = quality_metrics.incident_for(row, latest, reports, incidents or [])
        if cause:
            cause_line = t(*cause)
        elif incident:
            cause_line = t("Incidente externo de {} ({}): {}", "External incident of {} ({}): {}").format(
                incident.get("fuente", ""), incident.get("referencia", ""), t(*incident["causa"])
            )
        else:
            cause_line = diagnosis["origen"]
        action = t(*goal["accion"]) if goal.get("accion") else ""
        parts.append(
            f'<div class="qm-alert qm-{"antigua" if stale else row["estado"]}"><h4>{html.escape(state_word(row["estado"], policy))} · '
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
    href = html.escape(link(latest)) if link else "#"
    parts.append(
        f'<p class="qm-alert-foot">{html.escape(t(*texts["anotar"]))} · {html.escape(t("Última medición", "Last measurement"))}: '
        f'{html.escape(day)} · <a href="{href}" target="_self">{html.escape(t(*texts["ver_informe"]))} '
        f'{html.escape(quality_metrics.report_code(latest, i18n.is_english()))}</a></p>'
    )
    return '<div class="qm-alerts">' + "".join(parts) + "</div>"


def is_stale(report: dict[str, Any], today: Any = None) -> bool:
    """D-361: True when the report is more than STALE_DAYS old; the alert then reads it as an old measurement."""
    from datetime import date

    measured = date.fromisoformat(str(report["fecha"])[:10])
    return ((today or date.today()) - measured).days > STALE_DAYS


# endregion


# region Style
def build_css(palette: dict[str, str]) -> str:
    """The stylesheet of the page and of the alerts, with the colours of the theme; each state legible on a card."""
    card = palette["card"]
    colors = {state: charts.legible(color or palette["rise"], card) for state, color in STATE_COLORS.items()}
    colors["sin_medicion"] = charts.legible(palette["reference"], card)
    return static_files.style(
        "quality_method.css",
        {
            "var(--go-soft)": charts.legible(palette["reference"], palette["background"]),
            "var(--go-ink)": palette["strong_text"],
            "var(--go-border)": palette["card_border"],
            "var(--go-text)": palette["text"],
            "var(--go-states)": "".join(f".qm-{state} {{ color:{color}; }}\n" for state, color in colors.items()),
        },
    )


# endregion
