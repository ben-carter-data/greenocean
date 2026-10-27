"""«Método y calidad» (D-320, D-323): how the project is assessed against software and data quality standards.

A self-assessment, never a certification. Every measured number comes from a file: the last measurement
(docs/calidad/medicion.json, written by scripts/medir_calidad.py with its date and commit), the baseline before the
improvements (docs/calidad/linea_base.json) and the goals (docs/calidad/metas.json); the ISO/IEC 25010 grades come from
the author's manual review (docs/calidad/rubrica.json), dated. Nothing measured is typed here. Pure functions: no
Streamlit; bi/dashboard.py draws the HTML. Texts come in both languages, so the page never depends on the render-time
translation.
"""

from __future__ import annotations

import html
from typing import Any

from bi import charts, i18n, quality_metrics

SIDEBAR_LINE = "Evaluado según ISO/IEC 25010 · 25012"
# For a standard the words say how far it was applied (never «cumple la norma»); for a goal, where the measure falls.
STATES = {
    "ok": ("Aplicado", "Applied"),
    "partial": ("Parcial", "Partial"),
    "fail": ("No aplicado", "Not applied"),
    "unknown": ("No verificado", "Not verified"),
}
GOAL_STATES = {
    True: ("Cumple la meta", "Meets the goal"),
    False: ("Bajo la meta", "Below the goal"),
    None: ("No medido", "Not measured"),
}
GRADE_SCALE = [
    ("0", "no existe o no funciona", "absent or not working"),
    ("1", "existe pero es débil o está medido en contra", "exists but weak, or measured against"),
    ("2", "existe con huecos importantes", "exists with important gaps"),
    ("3", "sólido, con huecos menores medidos", "solid, with small measured gaps"),
    ("4", "sólido y verificado de punta a punta", "solid and verified end to end"),
]


def read_all() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """(baseline, measurement, goals, rubric) as the files say them."""
    return (
        quality_metrics.read(quality_metrics.BASELINE_FILE),
        quality_metrics.read(quality_metrics.REPORT_FILE),
        quality_metrics.read(quality_metrics.GOALS_FILE),
        quality_metrics.read(quality_metrics.RUBRIC_FILE),
    )


def t(spanish: str, english: str) -> str:
    return english if i18n.is_english() else spanish


def number(value: Any, decimals: int = 0) -> str:
    """A figure with the marks of the reader's language; «—» when it was not measured."""
    if value is None:
        return "—"
    text = f"{value:,}" if isinstance(value, int) and decimals == 0 else f"{float(value):,.{decimals}f}"
    return text if i18n.is_english() else text.replace(",", "§").replace(".", ",").replace("§", ".")


def show(value: Any, unit: str) -> str:
    if value is None:
        return "—"
    decimals = 2 if unit == "s" else 1 if unit == "%" else 0
    return number(value, decimals) + (f" {unit}" if unit else "")


def state_chip(key: str) -> str:
    spanish, english = STATES[key]
    return f'<span class="qm-state qm-{key}">{html.escape(t(spanish, english))}</span>'


def goal_chip(ok: bool | None) -> str:
    spanish, english = GOAL_STATES[ok]
    css = "ok" if ok else "unknown" if ok is None else "fail"
    return f'<span class="qm-state qm-{css}">{html.escape(t(spanish, english))}</span>'


def grade_chip(grade: int | None) -> str:
    if grade is None:
        return '<span class="qm-grade qm-unknown">n/v</span>'
    return f'<span class="qm-grade qm-g{grade}">{grade} / 4</span>'


def build_table(head: list[str], rows: list[tuple[str, ...]]) -> str:
    """A table whose cells are already HTML; keyboard users can scroll it (tabindex)."""
    columns = "".join(f"<th>{html.escape(cell)}</th>" for cell in head)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="qm-table" tabindex="0"><table><thead><tr>{columns}</tr></thead><tbody>{body}</tbody></table></div>'


def code_cell(command: str) -> str:
    return f'<code class="qm-code">{html.escape(command)}</code>'


def rubric_average(rubric: dict[str, Any]) -> float | None:
    grades = [item["nota"] for item in rubric.get("caracteristicas", []) if item.get("nota") is not None]
    return sum(grades) / len(grades) if grades else None


def build_header(report: dict[str, Any], rubric: dict[str, Any]) -> str:
    """Where the numbers come from: the automatic measurement with its date and commit, and the manual ISO review."""
    date, commit = report.get("generado", "—"), report.get("commit", "—")
    measured = t(
        f"Medición automática del {date} · commit {commit}", f"Automatic measurement of {date} · commit {commit}"
    )
    day = rubric.get("fecha", "—")
    review = t(
        f"Rúbrica ISO/IEC 25010: revisión manual del autor del {day}",
        f"ISO/IEC 25010 rubric: the author's manual review of {day}",
    )
    if rubric.get("estado") != "confirmada":
        review += t(" · borrador, pendiente de su confirmación", " · draft, awaiting confirmation")
    note = t(
        "Autoevaluación, no una certificación: las normas se usan como método y cada número sale de una herramienta.",
        "A self-assessment, not a certification: the standards are used as a method and every number comes from a tool.",
    )
    return (
        f'<div class="qm-head"><span>{html.escape(measured)}</span><span>{html.escape(review)}</span>'
        f"<em>{html.escape(note)}</em></div>"
    )


def build_summary(baseline: dict[str, Any], report: dict[str, Any], goals: dict[str, Any]) -> str:
    """Before → now → goal for each indicator, with the command that reproduces it."""
    head = [
        t("Indicador", "Indicator"),
        t("Antes", "Before"),
        t("Ahora", "Now"),
        t("Meta", "Goal"),
        t("Estado", "State"),
        t("Cómo reproducirlo", "How to reproduce it"),
    ]
    table_rows = quality_metrics.rows(baseline, report, goals)
    rows = [
        (
            f"<b>{html.escape(t(*row['label']))}</b>",
            show(row["before"], row["unit"]),
            f"<b>{show(row['now'], row['unit'])}</b>",
            html.escape(quality_metrics.goal_text(row["goal"]) + (f" {row['unit']}" if row["unit"] else "")),
            goal_chip(row["ok"]),
            code_cell(row["command"]),
        )
        for row in table_rows
    ]
    met, total = sum(1 for row in table_rows if row["ok"]), len(table_rows)
    lead = t(
        f"{met} de {total} indicadores cumplen su meta. «Antes» es la medición previa a las mejoras de D-323.",
        f"{met} of {total} indicators meet their goal. «Before» is the measurement before the improvements of D-323.",
    )
    return f'<p class="qm-note">{html.escape(lead)}</p>' + build_table(head, rows)


def build_iso(report: dict[str, Any], goals: dict[str, Any], rubric: dict[str, Any]) -> str:
    """The eight characteristics with the author's grade and evidence; the measurable gaps come from the indicators."""
    measurable = quality_metrics.gaps(report, goals)
    rows = []
    for item in rubric.get("caracteristicas", []):
        missing = [t(*gap) for gap in measurable.get(item["clave"], [])] + [t(*item["falta"])]
        rows.append(
            (
                f"<b>{html.escape(t(*item['nombre']))}</b>",
                grade_chip(item.get("nota")),
                html.escape(t(*item["evidencia"])),
                "<br>".join(html.escape(text) for text in missing),
            )
        )
    average = number(rubric_average(rubric), 1)
    scale = " · ".join(f"{grade}: {t(es, en)}" for grade, es, en in GRADE_SCALE)
    lead = t(
        f"Promedio de las {len(rows)} características: {average} de 4. Escala: {scale}.",
        f"Average of the {len(rows)} characteristics: {average} out of 4. Scale: {scale}.",
    )
    head = [
        t("Característica", "Characteristic"),
        t("Nota", "Grade"),
        t("Evidencia", "Evidence"),
        t("Qué falta", "What is missing"),
    ]
    return f'<p class="qm-note">{html.escape(lead)}</p>' + build_table(head, rows)


def measured_data_rows(data: dict[str, Any]) -> list[tuple[str, str, str]]:
    of = t("de", "of")
    return [
        (
            t("Precios de la última semana con comparación válida", "Prices of the last week with a valid comparison"),
            show(data.get("pct_comparacion"), "%"),
            f"{number(data.get('con_comparacion'))} {of} {number(data.get('precios_semana'))}",
        ),
        (
            t(
                "Series de las últimas 12 semanas con dato esta semana",
                "Series of the last 12 weeks with data this week",
            ),
            show(data.get("pct_series_con_dato"), "%"),
            f"{number(data.get('series_con_dato'))} {of} {number(data.get('series_activas'))}",
        ),
        (
            t("Días desde el fin de la última semana con datos", "Days since the end of the last week with data"),
            number(data.get("dias_desde_ultima_semana")),
            t(f"semana del {data.get('semana', '—')}", f"week of {data.get('semana', '—')}"),
        ),
        (
            t("Días desde la última carga", "Days since the last load"),
            number(data.get("dias_desde_ultima_carga")),
            t(f"medido el {data.get('medido', '—')}", f"measured on {data.get('medido', '—')}"),
        ),
    ]


def build_data_quality(report: dict[str, Any], indicators: list[tuple[Any, ...]], counts: Any) -> str:
    """ISO/IEC 25012: the measured data indicators, the live indicators of the loaded database and the declared limits."""
    measured = [
        (f"<b>{html.escape(a)}</b>", html.escape(b), html.escape(c))
        for a, b, c in measured_data_rows(report.get("datos", {}))
    ]
    status_key = {"ok": True, "warn": False, "fail": False}
    tr = i18n.tr
    live = [
        (
            f"<b>{html.escape(tr(dimension.capitalize()))}</b>",
            html.escape(tr(name)),
            html.escape(tr(value)),
            html.escape(tr(reference)),
            goal_chip(status_key.get(status)),
        )
        for dimension, name, value, reference, status, _ in indicators
    ]
    prices, weeks, regions, channels = (int(counts[key]) for key in ("prices", "weeks", "regions", "channels"))
    limits = [
        t(
            f"Cobertura: {number(prices)} precios semanales, {weeks} semanas, {regions} regiones y {channels} canales; ODEPA publica 9 de las 16 regiones.",
            f"Coverage: {number(prices)} weekly prices, {weeks} weeks, {regions} regions and {channels} channels; ODEPA publishes 9 of the 16 regions.",
        ),
        t(
            "Los precios son nominales; el precio real descuenta la inflación general de alimentos del INE.",
            "Prices are nominal; the real price discounts the INE's general food inflation.",
        ),
        t(
            "El margen entre mayorista y consumidor existe solo para frutas y verduras.",
            "The wholesale-to-consumer margin exists only for fruit and vegetables.",
        ),
    ]
    live_head = [
        t("Dimensión", "Dimension"),
        t("Indicador", "Indicator"),
        t("Valor", "Value"),
        t("Referencia", "Reference"),
        t("Estado", "State"),
    ]
    return (
        f'<h4>{html.escape(t("Medidos con el código del proyecto", "Measured with the project code"))}</h4>'
        + build_table([t("Indicador", "Indicator"), t("Valor", "Value"), t("Detalle", "Detail")], measured)
        + f'<h4>{html.escape(t("Indicadores en vivo de la carga actual", "Live indicators of the current load"))}</h4>'
        + build_table(live_head, live)
        + f'<h4>{html.escape(t("Límites declarados", "Declared limits"))}</h4><ul class="qm-list">'
        + "".join(f"<li>{html.escape(item)}</li>" for item in limits)
        + "</ul>"
    )


def build_browsers(report: dict[str, Any], goals: dict[str, Any]) -> str:
    """Load time and WCAG violations of every page, and the layout checks per browser."""
    browsers = report.get("navegadores", {})
    pages = browsers.get("paginas", {})
    if not pages:
        return f'<p class="qm-note">{html.escape(t("Sin medición en navegadores.", "No browser measurement."))}</p>'
    budget = goals.get("segundos_por_pagina", {}).get("max")
    page_rows = [
        (
            f"<b>{html.escape(i18n.tr(name))}</b>",
            show(page["seconds"], "s"),
            number(page["violations"]),
            goal_chip(page["seconds"] <= budget and page["violations"] == 0 if budget else None),
        )
        for name, page in pages.items()
    ]
    matrix = [
        (
            f"<b>{html.escape(name.capitalize())}</b>",
            f"{number(item['passed'])} / {number(item['checks'])}",
            html.escape(", ".join(f"{fail['page']} {fail['size']}" for fail in item["failed"]) or "—"),
        )
        for name, item in browsers.get("navegadores", {}).items()
    ]
    sizes = t(
        "Navegadores (1440 × 790, 1920 × 1000 y teléfono en horizontal)",
        "Browsers (1440 × 790, 1920 × 1000 and phone in landscape)",
    )
    return (
        build_table(
            [t("Página", "Page"), t("Carga", "Load"), t("Violaciones WCAG", "WCAG violations"), t("Estado", "State")],
            page_rows,
        )
        + f"<h4>{html.escape(sizes)}</h4>"
        + build_table(
            [t("Navegador", "Browser"), t("Comprobaciones superadas", "Checks passed"), t("Fallos", "Failures")], matrix
        )
    )


def build_standards(report: dict[str, Any]) -> str:
    """How each standard is used, with the measured indicator that backs it where there is one."""
    now = quality_metrics.values(report)
    coverage = show(now["cobertura_total"], "%")
    findings = number(now["ruff_avisos"])
    rows = [
        (
            "ISO/IEC 25010",
            t("Calidad del producto", "Product quality"),
            t("Rúbrica de ocho características, revisada a mano", "Eight-characteristic rubric, reviewed by hand"),
            "ok",
        ),
        (
            "ISO/IEC 25012 · ISO 8000",
            t("Calidad de los datos", "Data quality"),
            t(
                "Indicadores medidos desde la base y pruebas que recalculan las cifras",
                "Indicators measured from the database and tests that recompute figures",
            ),
            "ok",
        ),
        (
            "ISO/IEC 5055",
            t("Calidad del código", "Code quality"),
            t(f"Ruff ({findings} avisos), mypy, radon y Bandit", f"Ruff ({findings} findings), mypy, radon and Bandit"),
            "ok",
        ),
        (
            "ISO/IEC 29119",
            t("Pruebas", "Testing"),
            t(
                f"pytest con cobertura ({coverage}) y plan en docs/PLAN_PRUEBAS.md",
                f"pytest with coverage ({coverage}) and plan in docs/PLAN_PRUEBAS.md",
            ),
            "ok",
        ),
        (
            "WCAG 2.1 AA",
            t("Accesibilidad", "Accessibility"),
            t(
                "axe-core con Playwright en cada página y tema; sin revisión manual",
                "axe-core with Playwright on every page and theme; no manual review",
            ),
            "partial",
        ),
        (
            "ISO/IEC/IEEE 42010 · C4",
            t("Arquitectura", "Architecture"),
            t("docs/SAD.md por vistas", "docs/SAD.md by views"),
            "ok",
        ),
        (
            "ADR",
            t("Decisiones", "Decisions"),
            t("docs/ADR.md y docs/DECISIONES.md", "docs/ADR.md and docs/DECISIONES.md"),
            "ok",
        ),
        (
            "OWASP Top 10",
            t("Seguridad de aplicaciones", "Application security"),
            t("Revisión por categoría; sin prueba de penetración", "Review by category; no penetration test"),
            "partial",
        ),
        (
            "Twelve-Factor App",
            t("Aplicación desplegable", "Deployable application"),
            t("Revisión de los 12 factores en el informe", "Review of the 12 factors in the report"),
            "partial",
        ),
        (
            "CI/CD",
            t("Integración continua", "Continuous integration"),
            t(
                "Lint, mypy, pruebas con cobertura mínima y medición de calidad en cada push",
                "Lint, mypy, tests with minimum coverage and quality measurement on every push",
            ),
            "ok",
        ),
    ]
    head = [
        t("Estándar", "Standard"),
        t("Qué cubre", "What it covers"),
        t("Cómo se aplica", "How it is applied"),
        t("Resultado", "Result"),
    ]
    return build_table(
        head, [(f"<b>{html.escape(a)}</b>", html.escape(b), html.escape(c), state_chip(d)) for a, b, c, d in rows]
    )


def build_limits(report: dict[str, Any], goals: dict[str, Any]) -> str:
    measurable = [t(*gap) for items in quality_metrics.gaps(report, goals).values() for gap in items]
    judged = [
        t(
            "Es una autoevaluación del autor, no una auditoría externa: las notas ISO son un juicio apoyado en evidencia.",
            "It is a self-assessment by the author, not an external audit: the ISO grades are a judgement backed by evidence.",
        ),
        t(
            "La auditoría automática de accesibilidad no reemplaza recorrer cada página con teclado y lector de pantalla.",
            "The automatic accessibility audit does not replace walking each page with the keyboard and a screen reader.",
        ),
        t(
            "Los tiempos son de un equipo local, sin varias personas a la vez.",
            "The times are from a local machine, without several people at once.",
        ),
        t(
            "Seis funciones de páginas siguen sobre la complejidad 10: dividirlas exige más pruebas de la interfaz.",
            "Six page functions remain over complexity 10: splitting them needs more interface tests.",
        ),
    ]
    return '<ul class="qm-list">' + "".join(f"<li>{html.escape(text)}</li>" for text in measurable + judged) + "</ul>"


def build_css(palette: dict[str, str]) -> str:
    ink, text, muted, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card_border"],
        palette["accent"],
    )
    soft = charts.legible(muted, palette["background"])
    return f"""<style>
.qm-head {{ display:flex; flex-wrap:wrap; gap:4px 18px; align-items:baseline; margin:0 0 8px; font-size:12.5px; color:{text}; }}
.qm-head em {{ flex-basis:100%; font-style:normal; color:{soft}; font-size:12px; }}
.qm-table, .qm-list, .qm-note {{ color:{text}; }}
.qm-pane h4 {{ margin:12px 0 6px !important; padding:0 !important; font-size:12px !important; text-transform:uppercase;
  letter-spacing:.06em; color:{soft}; }}
.qm-table {{ overflow:auto; max-height:calc(100vh - 330px); border:1px solid {border}; border-radius:10px; margin:6px 0 12px; }}
.qm-table table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:12.5px; margin:0; }}
.qm-table thead th {{ position:sticky; top:0; z-index:1; background:{accent} !important; color:{charts.readable_on(accent)} !important;
  font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.05em; padding:7px 10px !important; text-align:left;
  border:0 !important; }}
.qm-table td {{ padding:6px 10px !important; vertical-align:top; line-height:1.45; border:0 !important;
  border-bottom:1px solid {border} !important; background:transparent !important; color:{text}; }}
.qm-table td:first-child {{ color:{ink}; }}
.qm-table tbody tr:nth-child(even) td {{ background:color-mix(in srgb, {accent} 5%, transparent) !important; }}
.qm-code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; color:{ink}; background:transparent; padding:0; }}
.qm-state, .qm-grade {{ display:inline-block; padding:1px 9px; border-radius:999px; font-size:11.5px; font-weight:600;
  white-space:nowrap; border:1px solid currentColor; }}
.qm-ok, .qm-g3, .qm-g4 {{ color:{charts.legible("#199e70", palette["card"])}; }}
.qm-partial, .qm-g2 {{ color:{charts.legible("#b8860b", palette["card"])}; }}
.qm-fail, .qm-g0, .qm-g1 {{ color:{charts.legible(palette["rise"], palette["card"])}; }}
.qm-unknown {{ color:{charts.legible(muted, palette["card"])}; }}
.qm-list {{ margin:4px 0 10px; padding-left:18px; font-size:13px; line-height:1.55; }}
.qm-note {{ font-size:12.5px; margin:2px 0 6px; }}
.qm-pane {{ max-height:calc(100vh - 250px); overflow:auto; padding-right:6px; }}
</style>"""
