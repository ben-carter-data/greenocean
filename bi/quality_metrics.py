"""The quality indicators of GreenOcean (D-323): what each one is, how it is read from a measurement, its goal and the
command that reproduces it. Shared by the page «Método y calidad» and scripts/verificar_calidad.py, so the page and the
check never disagree. Pure functions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FOLDER = Path(__file__).resolve().parent.parent / "docs" / "calidad"
GOALS_FILE = FOLDER / "metas.json"
BASELINE_FILE = FOLDER / "linea_base.json"
REPORT_FILE = FOLDER / "medicion.json"
RUBRIC_FILE = FOLDER / "rubrica.json"
HISTORY_FILE = FOLDER / "historial.json"

# (key, Spanish label, English label, unit, ISO/IEC 25010 characteristic, command that reproduces it)
INDICATORS = [
    ("pruebas_fallidas", "Pruebas que fallan", "Failing tests", "", "fiabilidad", "pytest -q"),
    ("cobertura_total", "Cobertura total", "Total coverage", "%", "fiabilidad", "pytest -q --cov"),
    (
        "cobertura_por_modulo",
        "Cobertura del módulo más bajo",
        "Coverage of the lowest module",
        "%",
        "fiabilidad",
        "pytest -q --cov --cov-report=term",
    ),
    (
        "ruff_avisos",
        "Avisos de Ruff (E, F y W; el largo de línea, aparte)",
        "Ruff findings (E, F and W; line length apart)",
        "",
        "mantenibilidad",
        "ruff check .",
    ),
    (
        "archivos_sin_formatear",
        "Archivos sin formatear",
        "Unformatted files",
        "",
        "mantenibilidad",
        "ruff format --check .",
    ),
    (
        "funciones_con_tipos_pct",
        "Funciones con tipos (módulos principales)",
        "Typed functions (main modules)",
        "%",
        "mantenibilidad",
        "mypy",
    ),
    ("mypy_errores", "Errores de mypy", "mypy errors", "", "mantenibilidad", "mypy"),
    (
        "complejidad_sobre_10",
        "Funciones con complejidad sobre 10",
        "Functions over complexity 10",
        "",
        "mantenibilidad",
        "ruff check bi etl agent --select C901",
    ),
    ("bandit_altos", "Hallazgos altos de Bandit", "High Bandit findings", "", "seguridad", "bandit -r bi etl agent"),
    (
        "pip_audit_vulnerabilidades",
        "Vulnerabilidades en dependencias",
        "Vulnerable dependencies",
        "",
        "seguridad",
        "pip-audit -r requirements.txt",
    ),
    (
        "secretos_sin_clasificar",
        "Posibles secretos sin revisar",
        "Unreviewed possible secrets",
        "",
        "seguridad",
        "detect-secrets scan $(git ls-files)",
    ),
    (
        "segundos_por_pagina",
        "Carga de la página más lenta",
        "Load of the slowest page",
        "s",
        "eficiencia",
        "node tests/medicion/calidad.cjs",
    ),
    (
        "segundos_por_consulta",
        "Consulta más lenta",
        "Slowest query",
        "s",
        "eficiencia",
        "pytest -q tests/test_rendimiento.py",
    ),
    (
        "violaciones_wcag",
        "Violaciones WCAG 2.1 AA",
        "WCAG 2.1 AA violations",
        "",
        "usabilidad",
        "node tests/medicion/calidad.cjs",
    ),
    (
        "comprobaciones_navegador_fallidas",
        "Comprobaciones fallidas en Chromium, Firefox y WebKit",
        "Failed checks in Chromium, Firefox and WebKit",
        "",
        "compatibilidad",
        "node tests/medicion/calidad.cjs",
    ),
]


# What is measured by itself and what the author reviews by hand, and how often: (what, how, when), each in both languages.
SCHEDULE = [
    (
        (
            "Los 15 indicadores de la tabla «Antes → ahora → meta»",
            "The 15 indicators of the «Before → now → goal» table",
        ),
        ("Automático: workflow «calidad» (scripts/medir_calidad.py)", "Automatic: «calidad» workflow"),
        (
            "En cada push; una vez por semana cuando el autor lo active",
            "On every push; once a week when the author turns it on",
        ),
    ),
    (
        ("Calidad de los datos servidos", "Quality of the served data"),
        (
            "Automático: el código del proyecto lee la base servida",
            "Automatic: the project code reads the served database",
        ),
        ("En cada push", "On every push"),
    ),
    (
        ("Tiempos, WCAG 2.1 AA y diseño en tres navegadores", "Times, WCAG 2.1 AA and layout in three browsers"),
        ("Automático: Playwright y axe-core (tests/medicion/calidad.cjs)", "Automatic: Playwright and axe-core"),
        ("En cada push", "On every push"),
    ),
    (
        ("Comparación con las metas", "Comparison with the goals"),
        (
            "Automático: scripts/verificar_calidad.py; el CI falla y dice cuál indicador bajó",
            "Automatic: scripts/verificar_calidad.py; CI fails naming the indicator",
        ),
        ("En cada push", "On every push"),
    ),
    (
        ("Publicar una medición en esta página", "Publishing a measurement on this page"),
        (
            "Manual: el autor fusiona el pull request «Actualizar medición de calidad»",
            "Manual: the author merges the pull request «Actualizar medición de calidad»",
        ),
        ("Cada vez que el workflow lo abre", "Each time the workflow opens one"),
    ),
    (
        ("Rúbrica ISO/IEC 25010", "ISO/IEC 25010 rubric"),
        ("Manual: el autor revisa y confirma docs/calidad/rubrica.json", "Manual: the author reviews and confirms it"),
        ("Una vez por versión", "Once per version"),
    ),
    (
        ("OWASP Top 10 y Twelve-Factor App", "OWASP Top 10 and Twelve-Factor App"),
        ("Manual: revisión por categoría en el informe", "Manual: review by category in the report"),
        ("Una vez por versión", "Once per version"),
    ),
    (
        ("Posibles secretos y hallazgos medios de Bandit", "Possible secrets and medium Bandit findings"),
        (
            "Manual: cada candidato nuevo se revisa y se anota en .secrets.baseline",
            "Manual: each new candidate is reviewed and noted in .secrets.baseline",
        ),
        ("Cuando aparece uno nuevo", "When a new one appears"),
    ),
    (
        ("Las metas", "The goals"),
        (
            "Manual: decisión del autor en docs/calidad/metas.json",
            "Manual: the author's decision in docs/calidad/metas.json",
        ),
        ("Cuando el autor lo decide", "When the author decides"),
    ),
    (
        ("Recorrido con teclado y lector de pantalla", "Walk-through with keyboard and screen reader"),
        ("Manual", "Manual"),
        ("Pendiente: aún no se ha hecho", "Pending: not done yet"),
    ),
]


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def number(value: Any, decimals: int = 0, english: bool = False) -> str:
    """A figure with the marks of the language (1.234,5 or 1,234.5); «—» when it was not measured."""
    if value is None:
        return "—"
    text = f"{value:,}" if isinstance(value, int) and decimals == 0 else f"{float(value):,.{decimals}f}"
    return text if english else text.replace(",", "§").replace(".", ",").replace("§", ".")


def show(value: Any, unit: str, english: bool = False) -> str:
    if value is None:
        return "—"
    decimals = 2 if unit == "s" else 1 if unit == "%" else 0
    return number(value, decimals, english) + (f" {unit}" if unit else "")


def values(report: dict[str, Any]) -> dict[str, Any]:
    """{indicator: value} read from a measurement; None when that part could not run."""
    coverage = report.get("cobertura", {})
    mypy = report.get("mypy", {})
    browsers = report.get("navegadores", {})
    pages = browsers.get("paginas", {})
    queries = report.get("consultas", {}).get("consultas", {})
    audit = report.get("pip_audit", {}).get("archivos", {})
    audited = [item["vulnerabilidades"] for item in audit.values() if item.get("vulnerabilidades") is not None]
    tests = report.get("pruebas", {}).get("pruebas")
    passed = coverage.get("pruebas_ok")
    skipped = coverage.get("pruebas_omitidas") or 0
    matrix = browsers.get("navegadores")
    ruff = report.get("ruff", {})
    return {
        # The same rules before and after: the baseline counted E501 inside, which pyproject.toml leaves out (D-323).
        "ruff_avisos": ruff.get("errores_sin_largo_de_linea", ruff.get("errores")),
        "archivos_sin_formatear": ruff.get("formato", {}).get("por_reformatear"),
        "cobertura_total": coverage.get("total"),
        "cobertura_por_modulo": min(coverage["modulos"].values()) if coverage.get("modulos") else None,
        "mypy_errores": mypy.get("errores"),
        "funciones_con_tipos_pct": (
            round(mypy["con_tipo_de_retorno"] / mypy["funciones"] * 100, 1) if mypy.get("funciones") else None
        ),
        "complejidad_sobre_10": report.get("complejidad", {}).get("funciones_sobre_10"),
        "bandit_altos": report.get("bandit", {}).get("alta"),
        "pip_audit_vulnerabilidades": sum(audited) if audited else None,
        "secretos_sin_clasificar": report.get("secretos", {}).get("sin_clasificar"),
        "pruebas_fallidas": tests - passed - skipped if tests is not None and passed is not None else None,
        "segundos_por_pagina": max(page["seconds"] for page in pages.values()) if pages else None,
        "segundos_por_consulta": max(queries.values()) if queries else None,
        "violaciones_wcag": browsers.get("violaciones_wcag"),
        "comprobaciones_navegador_fallidas": sum(len(item["failed"]) for item in matrix.values()) if matrix else None,
    }


def meets(value: Any, goal: dict[str, Any]) -> bool | None:
    """True or False against the goal; None when the value was not measured."""
    if value is None or not goal:
        return None
    return value <= goal["max"] if "max" in goal else value >= goal["min"]


def goal_text(goal: dict[str, Any], english: bool = False) -> str:
    if not goal:
        return "—"
    sign, limit = ("≤", goal["max"]) if "max" in goal else ("≥", goal["min"])
    return f"{sign} {number(limit, 1 if isinstance(limit, float) else 0, english)}"


def rows(baseline: dict[str, Any], report: dict[str, Any], goals: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per indicator: before (the baseline), now (the last measurement), goal, whether it meets it, command."""
    return rows_of_values(values(baseline), values(report), goals)


def rows_of_values(before: dict[str, Any], now: dict[str, Any], goals: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "label": (spanish, english),
            "unit": unit,
            "iso": iso,
            "command": command,
            "before": before.get(key),
            "now": now.get(key),
            "goal": goals.get(key, {}),
            "ok": meets(now.get(key), goals.get(key, {})),
        }
        for key, spanish, english, unit, iso, command in INDICATORS
    ]


def gaps(report: dict[str, Any], goals: dict[str, Any]) -> dict[str, list[tuple[str, str]]]:
    """{ISO characteristic: [(Spanish, English)]}: the measurable gaps, the indicators under their goal."""
    found: dict[str, list[tuple[str, str]]] = {}
    for row in rows({}, report, goals):
        if row["ok"] is False:
            spanish, english = row["label"]
            unit = f" {row['unit']}" if row["unit"] else ""
            found.setdefault(row["iso"], []).append(
                (
                    f"{spanish}: {show(row['now'], row['unit'])} (meta {goal_text(row['goal'])}{unit})",
                    f"{english}: {show(row['now'], row['unit'], True)} (goal {goal_text(row['goal'], True)}{unit})",
                )
            )
    return found


def met(now: dict[str, Any], goals: dict[str, Any]) -> tuple[int, int]:
    """(indicators that meet their goal, indicators measured) for one set of values."""
    states = [meets(now.get(key), goals.get(key, {})) for key, *_ in INDICATORS]
    return sum(1 for state in states if state), sum(1 for state in states if state is not None)


def history_entry(report: dict[str, Any]) -> dict[str, Any]:
    return {"generado": report.get("generado"), "commit": report.get("commit"), "valores": values(report)}


def add_to_history(history: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """The history with this measurement last; a measurement of a commit already there replaces it."""
    entries = [entry for entry in history.get("mediciones", []) if entry["commit"] != report.get("commit")]
    return {**history, "mediciones": entries + [history_entry(report)]}
