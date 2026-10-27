"""Compares a measurement with the goals of docs/calidad/metas.json (D-323).

    python scripts/verificar_calidad.py [docs/calidad/medicion.json]

Prints every indicator with its value and its goal, and exits with 1 naming the ones below their goal. It never
changes the code: a goal that is not met is for the author to fix.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOALS = ROOT / "docs" / "calidad" / "metas.json"


def indicators(report):
    """{indicator: value} read from a measurement; None when the measurement could not run."""
    coverage = report.get("cobertura", {})
    mypy = report.get("mypy", {})
    browsers = report.get("navegadores", {})
    pages = browsers.get("paginas", {})
    queries = report.get("consultas", {}).get("consultas", {})
    audit = report.get("pip_audit", {}).get("archivos", {})
    audited = [item.get("vulnerabilidades") for item in audit.values() if "vulnerabilidades" in item]
    tests = report.get("pruebas", {}).get("pruebas")
    passed = coverage.get("pruebas_ok")
    skipped = coverage.get("pruebas_omitidas") or 0
    return {
        "ruff_avisos": report.get("ruff", {}).get("errores"),
        "archivos_sin_formatear": report.get("ruff", {}).get("formato", {}).get("por_reformatear"),
        "cobertura_total": coverage.get("total"),
        "cobertura_por_modulo": min(coverage["modulos"].values()) if coverage.get("modulos") else None,
        "mypy_errores": mypy.get("errores"),
        "funciones_con_tipos_pct": round(mypy["con_tipo_de_retorno"] / mypy["funciones"] * 100, 1)
        if mypy.get("funciones")
        else None,
        "complejidad_sobre_10": report.get("complejidad", {}).get("funciones_sobre_10"),
        "bandit_altos": report.get("bandit", {}).get("alta"),
        "pip_audit_vulnerabilidades": sum(audited) if audited else None,
        "secretos_sin_clasificar": report.get("secretos", {}).get("sin_clasificar"),
        "pruebas_fallidas": tests - passed - skipped if tests is not None and passed is not None else None,
        "segundos_por_pagina": max(page["seconds"] for page in pages.values()) if pages else None,
        "segundos_por_consulta": max(queries.values()) if queries else None,
        "violaciones_wcag": browsers.get("violaciones_wcag"),
        "comprobaciones_navegador_fallidas": (
            sum(len(item["failed"]) for item in browsers["navegadores"].values())
            if browsers.get("navegadores")
            else None
        ),
    }


def check(report, goals):
    """[(indicator, value, goal, ok)]; ok is None when the indicator was not measured."""
    rows = []
    for name, value in indicators(report).items():
        goal = goals.get(name, {})
        if value is None:
            rows.append((name, value, goal, None))
        elif "max" in goal:
            rows.append((name, value, goal, value <= goal["max"]))
        else:
            rows.append((name, value, goal, value >= goal["min"]))
    return rows


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "calidad" / "medicion.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    goals = json.loads(GOALS.read_text(encoding="utf-8"))
    failed = []
    for name, value, goal, ok in check(report, goals):
        limit = f"≤ {goal['max']}" if "max" in goal else f"≥ {goal.get('min')}"
        state = "no medido" if ok is None else "cumple" if ok else "NO CUMPLE"
        print(f"{name:36s} {str(value):>10s}  meta {limit:8s}  {state}")
        if ok is False:
            failed.append(name)
    if failed:
        print("\nBajo su meta: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
