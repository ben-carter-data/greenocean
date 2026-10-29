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
POLICY_FILE = FOLDER / "politica.json"
REPORTS_FOLDER = FOLDER / "informes"

# (key, Spanish label, English label, unit, ISO/IEC 25010 characteristic, command that reproduces it)
INDICATORS = [
    # Code (D-330): what treats the data.
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
    ("mypy_errores", "Errores de mypy", "mypy errors", "", "mantenibilidad", "mypy"),
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
    # Data (D-330): what we publish.
    ("pruebas_dbt_pct", "Pruebas de datos dbt superadas", "dbt data tests passed", "%", "fiabilidad", "dbt build"),
    (
        "comparables_pct",
        "Precios con comparación válida",
        "Prices with a valid comparison",
        "%",
        "adecuacion",
        "python scripts/medir_calidad.py",
    ),
    ("rechazadas_pct", "Filas rechazadas", "Rejected rows", "%", "adecuacion", "SELECT … FROM etl_run"),
    ("vigencia_dias", "Días desde la última carga", "Days since the last load", "días", "fiabilidad", "etl_run"),
]


# What is measured by itself and what the author reviews by hand, and how often: (what, how, when), each in both languages.
SCHEDULE = [
    (
        (
            "Los 12 indicadores: 8 de código y 4 de datos",
            "The 12 indicators: 8 of code and 4 of data",
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
        ("Comparación con las metas", "Comparison with the goals"),
        (
            "Automático: scripts/verificar_calidad.py; el CI falla si un indicador de código pasa lo aceptable",
            "Automatic: scripts/verificar_calidad.py; CI fails if a code indicator goes past its acceptable",
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


UNITS_EN = {"días": "days"}


def unit_text(unit: str, english: bool = False) -> str:
    """The unit in the reader's language («días» → «days»); «%» and «s» are the same in both."""
    return UNITS_EN.get(unit, unit) if english else unit


def show(value: Any, unit: str, english: bool = False) -> str:
    if value is None:
        return "—"
    decimals = 2 if unit == "s" else 1 if unit == "%" else 0
    return number(value, decimals, english) + (f" {unit_text(unit, english)}" if unit else "")


def values(report: dict[str, Any]) -> dict[str, Any]:
    """{indicator: value} read from a measurement; None when that part could not run or was not measured then."""
    coverage = report.get("cobertura", {})
    mypy = report.get("mypy", {})
    audit = report.get("pip_audit", {}).get("archivos", {})
    audited = [item["vulnerabilidades"] for item in audit.values() if item.get("vulnerabilidades") is not None]
    tests = report.get("pruebas", {}).get("pruebas")
    passed = coverage.get("pruebas_ok")
    skipped = coverage.get("pruebas_omitidas") or 0
    ruff = report.get("ruff", {})
    data = report.get("datos", {})
    dbt = report.get("dbt", {}).get("ultima_construccion")
    dbt = dbt if isinstance(dbt, dict) else {}
    return {
        # The same rules before and after: the baseline counted E501 inside, which pyproject.toml leaves out (D-323).
        "ruff_avisos": ruff.get("errores_sin_largo_de_linea", ruff.get("errores")),
        "cobertura_total": coverage.get("total"),
        "cobertura_por_modulo": min(coverage["modulos"].values()) if coverage.get("modulos") else None,
        "mypy_errores": mypy.get("errores"),
        "bandit_altos": report.get("bandit", {}).get("alta"),
        "pip_audit_vulnerabilidades": sum(audited) if audited else None,
        "secretos_sin_clasificar": report.get("secretos", {}).get("sin_clasificar"),
        "pruebas_fallidas": tests - passed - skipped if tests is not None and passed is not None else None,
        "pruebas_dbt_pct": (
            round(dbt["pruebas_ok"] / dbt["pruebas_total"] * 100, 1) if dbt.get("pruebas_total") else None
        ),
        "comparables_pct": data.get("pct_comparacion"),
        "rechazadas_pct": data.get("pct_rechazadas"),
        "vigencia_dias": data.get("dias_desde_ultima_carga"),
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
            english_unit = f" {unit_text(row['unit'], True)}" if row["unit"] else ""
            found.setdefault(row["iso"], []).append(
                (
                    f"{spanish}: {show(row['now'], row['unit'])} (meta {goal_text(row['goal'])}{unit})",
                    f"{english}: {show(row['now'], row['unit'], True)} (goal {goal_text(row['goal'], True)}{english_unit})",
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


STATES = ("cumple", "aviso", "urgente", "critico")


def state(value: Any, goal: dict[str, Any]) -> str:
    """cumple (the goal), aviso (worse than the goal, within the acceptable), urgente (over the acceptable by up to
    its critical margin) or critico (further); sin_medicion when there is no value."""
    if value is None or not goal:
        return "sin_medicion"
    margin = goal.get("margen_critico", 0)
    if "max" in goal:
        limit, aim = goal["max"], goal.get("meta", goal["max"])
        return (
            "cumple"
            if value <= aim
            else "aviso"
            if value <= limit
            else "urgente"
            if value <= limit + margin and margin
            else "critico"
        )
    limit, aim = goal["min"], goal.get("meta", goal["min"])
    return (
        "cumple"
        if value >= aim
        else "aviso"
        if value >= limit
        else "urgente"
        if value >= limit - margin and margin
        else "critico"
    )


def failure(key: str, value: Any, goal: dict[str, Any], report: dict[str, Any]) -> tuple[Any, Any, str]:
    """(failure, acceptable failure, unit): a compliance reads as 100 − value, a share that is already a failure as
    itself, a count over its total when it has one, days as days."""
    if value is None or not goal:
        return None, None, ""
    kind = goal.get("medida")
    if kind == "cumplimiento":
        return round(100 - value, 1), round(100 - goal["min"], 1), "%"
    if kind == "falla":
        return value, goal["max"], "%"
    if kind == "dias":
        return value, goal["max"], "días"
    tests = report.get("pruebas", {}).get("pruebas")
    if key == "pruebas_fallidas" and tests:
        return round(value / tests * 100, 2), goal["max"], "%"
    return value, goal["max"], ""


def evaluate(
    report: dict[str, Any], goals: dict[str, Any], policy: dict[str, Any], previous: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Every indicator of a measurement: value, failure against the acceptable, state, insight in both languages and
    the change against the previous report. Pure: it reads the files, it never writes a figure of its own."""
    now, before = values(report), values(previous or {})
    rows = []
    for key, spanish, english, unit, iso, command in INDICATORS:
        goal = goals.get(key, {})
        value = now.get(key)
        fail, acceptable, fail_unit = failure(key, value, goal, report)
        current = state(value, goal)
        warning_only = goal.get("tipo") == "datos" and policy.get("modo_datos") == "aviso"
        insight = []
        for language in (0, 1):
            template = policy.get("insight", {}).get(current, ["", ""])[language]
            action = goal.get("accion", ["", ""])[language]
            text = template.replace("{accion}", action)
            if current in ("urgente", "critico") and warning_only:
                text += " " + policy.get("modo_aviso", ["", ""])[language]
            insight.append(text.strip())
        previous_value = before.get(key)
        rows.append(
            {
                "clave": key,
                "nombre": [spanish, english],
                "tipo": goal.get("tipo"),
                "valor": value,
                "unidad": unit,
                "falla": fail,
                "falla_aceptable": acceptable,
                "unidad_falla": fail_unit,
                "estado": current,
                "bloquea": current in ("urgente", "critico") and not warning_only,
                "insight": insight,
                "variacion": (
                    round(value - previous_value, 3) if value is not None and previous_value is not None else None
                ),
            }
        )
    return rows


def read_reports(folder: Path = REPORTS_FOLDER) -> list[dict[str, Any]]:
    """Every numbered report (D-331), oldest first."""
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("informe-*.json"))]


def report_counts(report: dict[str, Any]) -> tuple[int, int, int]:
    """(within the acceptable, non-conformities, measured) of a report: «aviso» is within the acceptable."""
    states = [row["estado"] for row in report["indicadores"]]
    within = sum(state in ("cumple", "aviso") for state in states)
    nonconforming = sum(state in ("urgente", "critico") for state in states)
    return within, nonconforming, within + nonconforming


def where_text(key: str, measurement: dict[str, Any], row: dict[str, Any]) -> dict[str, str]:
    """The figures of «what failed and where» for one indicator, read from the measurement (D-335)."""
    tests = measurement.get("pruebas", {}).get("pruebas")
    coverage = measurement.get("cobertura", {}).get("modulos", {})
    lowest = sorted(coverage.items(), key=lambda item: item[1])[:3]
    dbt = measurement.get("dbt", {}).get("ultima_construccion")
    dbt = dbt if isinstance(dbt, dict) else {}
    data = measurement.get("datos", {})
    ruff = measurement.get("ruff", {}).get("por_codigo", {})
    detail = {
        "ruff_avisos": ", ".join(f"{code} ({count})" for code, count in sorted(ruff.items()) if code != "E501"),
        "cobertura_por_modulo": ", ".join(f"{name} ({value} %)" for name, value in lowest[:1]),
        "cobertura_total": ", ".join(f"{name} ({value} %)" for name, value in lowest),
        "pruebas_dbt_pct": f"{dbt.get('pruebas_ok')} de {dbt.get('pruebas_total')}",
        "comparables_pct": f"{data.get('con_comparacion')} de {data.get('precios_semana')}",
        "rechazadas_pct": f"{data.get('filas_rechazadas')} de {data.get('filas_leidas')}",
        "vigencia_dias": str(data.get("dias_desde_ultima_carga")),
    }.get(key, "")
    return {"valor": str(row.get("valor")), "total": str(tests), "detalle": detail}


def diagnose(
    row: dict[str, Any], report: dict[str, Any], reports: list[dict[str, Any]], policy: dict[str, Any]
) -> list[dict[str, str]]:
    """The automatic diagnosis of an indicator out of its acceptable (D-335): what failed and where, since when, and
    whether the cause is internal or may be the source's. Two languages, from the policy's templates and the
    measurement; the author writes only the action taken and its state. [{es, en}] lines, no secret, no internal path."""
    templates = policy.get("diagnostico", {})
    key = row["clave"]
    where = templates.get("donde", {}).get(key) or templates.get("donde", {}).get("otro", ["", ""])
    figures = where_text(key, report.get("medicion", {}), row)
    streak = report["numero"]
    by_number = {item["numero"]: item for item in reports}
    while streak - 1 in by_number:
        earlier = {r["clave"]: r["estado"] for r in by_number[streak - 1]["indicadores"]}
        if earlier.get(key) not in ("urgente", "critico"):
            break
        streak -= 1
    first = by_number.get(streak, report)
    since = templates.get("desde" if streak != report["numero"] else "primera_vez", ["", ""])
    origin = templates.get("origen_codigo" if row.get("tipo") == "codigo" else "origen_datos", ["", ""])
    lines = []
    for language in (0, 1):
        lines.append(
            {
                "donde": where[language].format(**figures),
                "desde": since[language].format(n=first["numero"], fecha=str(first["fecha"])[:10]),
                "origen": origin[language],
            }
        )
    return lines
