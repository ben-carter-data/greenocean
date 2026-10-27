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
    ("ruff_avisos", "Avisos de Ruff", "Ruff findings", "", "mantenibilidad", "ruff check ."),
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


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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
    return {
        "ruff_avisos": report.get("ruff", {}).get("errores"),
        "archivos_sin_formatear": report.get("ruff", {}).get("formato", {}).get("por_reformatear"),
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


def goal_text(goal: dict[str, Any]) -> str:
    return f"≤ {goal['max']}" if "max" in goal else f"≥ {goal['min']}" if goal else "—"


def rows(baseline: dict[str, Any], report: dict[str, Any], goals: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per indicator: before (the baseline), now (the last measurement), goal, whether it meets it, command."""
    before, now = values(baseline), values(report)
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
            limit = goal_text(row["goal"])
            found.setdefault(row["iso"], []).append(
                (
                    f"{spanish}: {row['now']}{row['unit']} (meta {limit})",
                    f"{english}: {row['now']}{row['unit']} (goal {limit})",
                )
            )
    return found
