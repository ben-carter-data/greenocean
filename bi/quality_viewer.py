"""The quality report viewer (D-333, D-431): one numbered report as four slides, in its own HTML document.

It is drawn in an iframe, so the arrows, the keyboard, full screen and «Descargar PDF» (the browser prints this
document only, faithful to the screen) work without touching the dashboard's DOM. Every figure comes from the reports
(docs/calidad/informes); every fixed text from docs/calidad/politica.json and docs/calidad/metas.json; the causes and
the actions from docs/calidad/no_conformidades.json and docs/calidad/incidentes_externos.json. The method is the SQAP's:
the cover names its version. The comparison slide compares any two reports of the same series, the previous one by
default, and warns when they do not measure the same indicators. D-571: every figure is written as the rest of the app
writes it, and the results say once how to read their bars, now that «Plan de calidad» is only the archive of reports.
Pure functions.
"""

from __future__ import annotations

import html
import json
from typing import Any

from bi import quality_metrics, static_files, weeks

# region Constants
SKY = "#38bdf8"
DEEP = "#05070b"
BEFORE = "#a78bfa"  # the earlier report of a comparison: violet, apart from the sky blue of the later one
STATE_COLORS = {
    "cumple": "#34d399",
    "aviso": "#fbbf24",
    "urgente": "#fb923c",
    "critico": "#f87171",
    "sin_medicion": "#94a3b8",
}
# endregion

# region Variables
CSS = static_files.fill(
    "quality_viewer.css",
    {
        'var(--go-deep)': DEEP,
        'var(--go-sky)': SKY,
    },
)
SCRIPT = static_files.fill(
    "quality_viewer.js",
    {
        '__GO_BEFORE__': BEFORE,
        '__GO_SKY__': SKY,
    },
)
# endregion


# region Pieces
def esc(value: Any) -> str:
    return html.escape(str(value))


def pick(pair: Any, english: bool) -> str:
    return pair[1 if english else 0] if isinstance(pair, list) else str(pair)


def figure(value: Any, unit: str, english: bool) -> str:
    """D-571: a figure as the rest of the app writes it (bi/quality_method.failure_text): a fraction keeps the decimals
    of quality_metrics.percent_decimals, so 0.008 reads «0,01 %» and 0.25 «0,25 %», never rounded to one decimal."""
    if value is None:
        return "—"
    decimals = quality_metrics.percent_decimals(value) if isinstance(value, float) and value % 1 else 0
    return quality_metrics.number(value, decimals, english) + (
        f" {quality_metrics.unit_text(unit, english)}" if unit else ""
    )


def period(reports: list[dict[str, Any]], report: dict[str, Any]) -> tuple[str, str]:
    """(from, to) of the period a report covers: from the previous report's date to its own."""
    previous = next((item for item in reports if item["numero"] == report["anterior"]), None)
    return (previous["fecha"][:10] if previous else "", report["fecha"][:10])


def slide(key: str, title: str, body: str) -> str:
    return f'<section class="slide" data-key="{key}"><h2>{esc(title)}</h2>{body}</section>'


# endregion


# region Rows of the report
def results_rows(report: dict[str, Any], policy: dict[str, Any], english: bool) -> str:
    rows = []
    for row in report["indicadores"]:
        fail, acceptable = row["falla"], row["falla_aceptable"]
        span = max(fail or 0, acceptable or 0) * 1.3 or 1
        bar = (
            '<span class="bar empty"></span>'
            if fail is None
            else f'<span class="bar"><i style="width:{min(100, fail / span * 100):.1f}%"></i>'
            f'<b style="left:{min(100, (acceptable or 0) / span * 100):.1f}%"></b></span>'
        )
        state = row["estado"]
        rows.append(
            f'<tr><td><b>{esc(pick(row["nombre"], english))}</b></td><td>{bar}</td>'
            f'<td class="num">{esc(figure(fail, row["unidad_falla"], english))}</td>'
            f'<td class="num muted">{esc(figure(acceptable, row["unidad_falla"], english))}</td>'
            f'<td><span class="state" style="color:{STATE_COLORS[state]}">'
            f"{esc(pick(policy['estados'][state], english))}</span></td>"
            f'<td class="muted">{esc(pick(row["insight"], english))}</td></tr>'
        )
    head = (
        ("Indicator", "Failure", "", "Acceptable", "State", "Reading")
        if english
        else ("Indicador", "Falla", "", "Aceptable", "Estado", "Lectura")
    )
    return (
        f'<table><thead><tr><th>{head[0]}</th><th>{head[1]}</th><th class="num"></th><th class="num">{head[3]}</th>'
        f'<th>{head[4]}</th><th>{head[5]}</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
    )


def table_rows(
    report: dict[str, Any],
    reports: list[dict[str, Any]],
    goals: dict[str, Any],
    policy: dict[str, Any],
    nonconformities: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
    english: bool,
) -> list[tuple[str, str, str, str, str]]:
    """D-431: the one table of non-conformities and incidents: (indicator, state, cause, disposition, date). The
    non-conformities of this report and the ones of earlier reports of its series still open, then the external
    incidents of its period."""
    names = {row["clave"]: pick(row["nombre"], english) for item in reports for row in item["indicadores"]}
    earlier = {item["numero"] for item in reports if item["numero"] <= report["numero"]}
    rows = []
    for record in nonconformities:
        if record.get("serie", quality_metrics.SERIES_BUILD) != report.get("serie", quality_metrics.SERIES_BUILD):
            continue
        mine = quality_metrics.same_report(record, report)
        if not mine and (record.get("informe") not in earlier or quality_metrics.is_resolved(record)):
            continue
        key = record.get("indicador", "")
        state = record.get("estado") or ("pending, the author's" if english else "pendiente del autor")
        cause = record.get("causa") or texts_of(policy, "causa_pendiente", english)
        disposition = record.get("accion") or pick(goals.get(key, {}).get("accion", ""), english)
        rows.append(
            (
                names.get(key, key),
                pick(state, english),
                pick(cause, english),
                pick(disposition, english),
                str(record.get("fecha", "")),
            )
        )
    start, end = period(reports, report)
    for item in incidents:
        if start < str(item.get("fecha", ""))[:10] <= end:
            source = item.get("fuente", "")
            rows.append(
                (
                    names.get(item.get("indicador", ""), item.get("indicador", "")),
                    f"{'External incident' if english else 'Incidente externo'} · {source}",
                    pick(item.get("causa", ""), english),
                    pick(item.get("respuesta", ""), english),
                    str(item.get("fecha", "")),
                )
            )
    return rows


def texts_of(policy: dict[str, Any], key: str, english: bool) -> str:
    return pick(policy.get("diapositivas", {}).get(key, ["", ""]), english)


# endregion


# region The viewer
def build_viewer_html(
    reports: list[dict[str, Any]],
    number: int,
    goals: dict[str, Any],
    policy: dict[str, Any],
    nonconformities: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
    english: bool = False,
    sqap_url: str = "",
) -> str:
    """The whole viewer of report «number» of one series, a self-contained document. D-431: four slides, one page
    each: the cover with the SQAP it was measured by, the results, the comparison and the non-conformities and
    incidents; the method lives in the SQAP only."""
    report = next(item for item in reports if item["numero"] == number)
    word = lambda key: texts_of(policy, key, english)  # noqa: E731
    title = quality_metrics.report_name(report, english)
    within, nonconforming, measured = quality_metrics.report_counts(report)
    labels = (
        ("Date", "Data week", "Evaluated code", "Within the acceptable", "Measured by")
        if english
        else ("Fecha", "Semana de datos", "Código evaluado", "Dentro de lo aceptable", "Medido según")
    )
    version = report.get("sqap")
    sqap = (
        f"SQAP v{esc(version)}"
        if version
        else ("SQAP (version not recorded)" if english else "SQAP (versión no registrada)")
    )
    sqap_html = f'<a href="{esc(sqap_url)}" target="_blank" rel="noopener">{sqap}</a>' if sqap_url else sqap
    series_note = (
        ""
        if report.get("serie") == quality_metrics.SERIES_WEEKLY
        else f'<p class="muted">{esc(word("serie_construccion"))}</p>'
    )
    cover = (
        f'<section class="slide cover" data-key="portada"><span class="kicker">GreenOcean</span><h1>{esc(title)}</h1>'
        f'<dl><dt>{labels[0]}</dt><dd>{esc(report["fecha"])}</dd><dt>{labels[1]}</dt><dd>{esc(weeks.week_range(report["semana"], True, english) if report["semana"] else "—")}</dd>'
        f'<dt>{labels[2]}</dt><dd><code>{esc(report["codigo_evaluado"])}</code></dd>'
        f"<dt>{labels[3]}</dt><dd>{within} / {measured}</dd><dt>{labels[4]}</dt><dd>{sqap_html}</dd></dl>"
        f'<p class="muted">{esc(word("portada"))}</p>{series_note}</section>'
    )
    # The figures behind the data indicators, under the results.
    data = report["medicion"].get("datos", {})
    dbt = report["medicion"].get("dbt", {}).get("ultima_construccion") or {}

    of = "of" if english else "de"
    figures = (
        ("dbt tests passed", "Rows rejected", "Prices with a valid comparison")
        if english
        else ("Pruebas dbt superadas", "Filas rechazadas", "Precios con comparación válida")
    )
    behind = " · ".join(
        f"{label}: {value}"
        for label, value in (
            (
                figures[0],
                f"{figure(dbt.get('pruebas_ok'), '', english)} {of} {figure(dbt.get('pruebas_total'), '', english)}",
            ),
            (
                figures[1],
                f"{figure(data.get('filas_rechazadas'), '', english)} {of} {figure(data.get('filas_leidas'), '', english)}",
            ),
            (
                figures[2],
                f"{figure(data.get('con_comparacion'), '', english)} {of} {figure(data.get('precios_semana'), '', english)}",
            ),
        )
    )
    # D-571: how to read the bars and ticks, once, under the table: the page «Plan de calidad» no longer says it.
    how = pick(policy.get("resumen", {}).get("como_leerlo", ""), english)
    results = slide(
        "resultados",
        word("resultados"),
        results_rows(report, policy, english)
        + (f'<p class="muted small">{esc(how)}</p>' if how else "")
        + f'<p class="muted small">{esc(behind)}</p>',
    )
    # The comparison: any two reports of the same series, the previous one by default.
    options = "".join(
        f'<option value="{item["numero"]}">{esc(quality_metrics.report_code(item, english))} · {esc(item["fecha"][:10])}</option>'
        for item in reports
    )
    compare_labels = ("Compare", "with") if english else ("Comparar", "con")
    comparison = slide(
        "comparacion",
        word("comparacion"),
        f'<div class="pickers"><label>{compare_labels[0]} <select id="cmp-a">{options}</select></label>'
        f'<label>{compare_labels[1]} <select id="cmp-b">{options}</select></label></div>'
        f'<p class="warn" id="cmp-warn" hidden></p><div id="cmp"></div>',
    )
    # The non-conformities and incidents: one compact table.
    head = (
        ("Indicator", "State", "Cause", "Disposition", "Date")
        if english
        else ("Indicador", "Estado", "Causa", "Disposición", "Fecha")
    )
    entries = table_rows(report, reports, goals, policy, nonconformities, incidents, english)
    issues = slide(
        "incidencias",
        word("incidencias"),
        (
            "<table class='issues'><thead><tr>"
            + "".join(f"<th>{cell}</th>" for cell in head)
            + "</tr></thead><tbody>"
            + "".join(
                f"<tr><td><b>{esc(name)}</b></td><td>{esc(state)}</td><td>{esc(cause)}</td>"
                f'<td>{esc(disposition)}</td><td class="num muted">{esc(day)}</td></tr>'
                for name, state, cause, disposition, day in entries
            )
            + "</tbody></table>"
        )
        if entries
        else f'<p class="big">{esc(word("sin_no_conformidades"))}</p>',
    )
    slides = [cover, results, comparison, issues]
    data_for_script = {
        "reports": [
            {
                "n": item["numero"],
                # D-571: the failure's text comes written as on the results, so both slides write it the same
                "rows": [
                    [
                        pick(row["nombre"], english),
                        row["falla"],
                        row["unidad_falla"],
                        row["clave"],
                        figure(row["falla"], row["unidad_falla"], english),
                    ]
                    for row in item["indicadores"]
                ],
            }
            for item in reports
        ],
        "a": report["anterior"] or number,
        "b": number,
        "lang": "en-US" if english else "es-CL",
        "units": {"días": "days"} if english else {},
        "head": ["Indicator", "", "", "Change"] if english else ["Indicador", "", "", "Variación"],
        "codes": {item["numero"]: quality_metrics.report_code(item, english) for item in reports},
        "warn": (
            "The two reports do not measure the same indicators; only the ones in both are compared."
            if english
            else "Los dos informes no miden los mismos indicadores; solo se comparan los que están en ambos."
        ),
    }
    buttons = (
        ("Previous", "Next", "Full screen", "Download PDF")
        if english
        else ("Anterior", "Siguiente", "Pantalla completa", "Descargar PDF")
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(title)}</title><style>{CSS}</style></head><body><div class='deck'>"
        f"<header class='bar'><b>{esc(title)}</b><span id='pos'></span><span class='grow'></span>"
        f"<button id='prev' aria-label='{buttons[0]}'>←</button><button id='next' aria-label='{buttons[1]}'>→</button>"
        f"<button id='full'>{buttons[2]}</button><button id='print' class='primary'>{buttons[3]}</button></header>"
        + "<div class='main'><nav class='thumbs' id='thumbs' aria-label='"
        + ("Slides" if english else "Diapositivas")
        + "'></nav><div class='stage' id='stage'><div class='canvas' id='canvas'>"
        + "".join(slides)
        + "</div></div></div></div><script>const DATA="
        + json.dumps(data_for_script, ensure_ascii=False).replace("</", "<\\/")
        + ";"
        + SCRIPT
        + "</script></body></html>"
    )


# endregion
