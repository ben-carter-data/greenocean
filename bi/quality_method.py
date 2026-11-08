"""«Plan de calidad» (D-320, D-323, D-330, D-332): how the quality of the published data and of the code is managed.

Two tabs. «Resumen» says in two sentences what is measured and how it is going, and shows each indicator's failure
against its acceptable, data and code apart, with the insight of those out of their acceptable. «Informes» lists the
numbered reports (docs/calidad/informes, D-331), newest first. Every figure comes from a report; every text of an
indicator from docs/calidad/metas.json and docs/calidad/politica.json. A self-assessment, reviewed by the author.
Pure functions: no Streamlit; bi/dashboard.py draws the HTML. Texts come in both languages.
"""

from __future__ import annotations

import html
from typing import Any

from bi import charts, i18n, quality_metrics, static_files

# region Constants
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


# region The overview
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


def build_latest_failures(failures: list[dict[str, Any]], count: int = 3) -> str:
    """D-346: the latest failures of the register (newest first), compact: date, what happened and its solution. The
    diagnosis is the author's and stays in the Incident log."""
    if not failures:
        return ""
    items = "".join(
        f'<li><b>{html.escape(row["fecha"])} · {html.escape(row["id"])}</b>'
        f'<span>{html.escape(t(*row["ocurrencia"]))}</span>'
        f'<small>{html.escape(t("Solución", "Solution"))}: {html.escape(t(*row["solucion"]))}</small></li>'
        for row in failures[:count]
    )
    return (
        f'<div class="qm-failures"><h4>{html.escape(t("Últimas fallas", "Latest failures"))}</h4><ul>{items}</ul></div>'
    )


def build_overview(
    report: dict[str, Any] | None,
    goals: dict[str, Any],
    policy: dict[str, Any],
    failures: list[dict[str, Any]] | None = None,
) -> str:
    """«Resumen»: two sentences, the data and the code side by side, and the insights that need attention."""
    if not report:
        return ""
    rows = report["indicadores"]
    data = [row for row in rows if row["tipo"] == "datos"]
    code = [row for row in rows if row["tipo"] == "codigo"]
    within, nonconforming, measured = quality_metrics.report_counts(report)
    plural = ("no conformidad", "non-conformity") if nonconforming == 1 else ("no conformidades", "non-conformities")
    # D-475: the report says how many of the plan's indicators it measures; a closed report keeps the ones of its time.
    name, total = quality_metrics.report_code(report, i18n.is_english()), len(quality_metrics.INDICATORS)
    day = str(report["fecha"])[:10]
    lead = [
        t(
            f"El informe {name} mide {len(rows)} de los {total} indicadores del plan de calidad: {len(data)} de los datos "
            f"que publicamos y {len(code)} del código que los trata, cada uno contra un aceptable fijado por el autor.",
            f"Report {name} measures {len(rows)} of the {total} indicators of the quality plan: {len(data)} of the data "
            f"we publish and {len(code)} of the code that treats it, each against an acceptable set by the author.",
        )
        if code
        else t(
            f"El informe {name} mide los {len(rows)} indicadores de datos del plan de calidad, cada uno contra un "
            "aceptable fijado por el autor; el código se verifica en el CI de cada push.",
            f"Report {name} measures the {len(rows)} data indicators of the quality plan, each against an acceptable "
            "set by the author; the code is checked by the CI of every push.",
        ),
        # D-483: the report's own date, never «Hoy»: a closed report is read beside today's «Controles de datos»
        t(
            f"El {day}: {within} de {measured} medidos dentro de lo aceptable · {nonconforming} {plural[0]}.",
            f"On {day}: {within} of {measured} measured within the acceptable · {nonconforming} {plural[1]}.",
        ),
    ]
    if report.get("serie") != quality_metrics.SERIES_WEEKLY:
        lead.append(
            t(
                f"{name} es un registro cerrado de la serie de construcción, medido con las reglas de entonces, y no se "
                "reevalúa; el estado de los datos de hoy está en «Controles de datos».",
                f"{name} is a closed record of the construction series, measured with the rules of its time, and is not "
                "re-evaluated; today's state of the data is in «Data controls».",
            )
        )
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
        + build_latest_failures(failures or [])
        + "</div>"
    )


# endregion


# region The weekly reports
def report_summary(report: dict[str, Any]) -> str:
    """The one line of a report in «Informes»: its number, date and how many indicators are within the acceptable."""
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
    return static_files.style(
        "quality_method.css",
        {
            'var(--go-soft)': soft,
            'var(--go-ink)': ink,
            'var(--go-border)': border,
            'var(--go-card)': card,
            'var(--go-text)': text,
            'var(--go-sky)': SKY,
            'var(--go-states)': states,
            'var(--go-deep)': DEEP,
            'var(--go-deep-states)': deep_states,
        },
    )


# endregion
