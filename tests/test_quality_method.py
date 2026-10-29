"""«Método y calidad» (D-320, D-323): every measured number of the page comes from the files of docs/calidad, the ISO
grades come from the author's dated review, the measurable gaps from the indicators, the wording never claims
certification, and the line under the logo opens the page in both languages."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import i18n, quality_method, quality_metrics

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = str(ROOT / "bi" / "dashboard.py")
FORBIDDEN = (
    "certificado",
    "certificada",
    "cumple la norma",
    "cumple con la norma",
    "complies with the standard",
    "is certified",
)
REPORT = {
    "generado": "2026-10-27 12:00 UTC",
    "commit": "abc1234",
    "ruff": {"errores": 3, "formato": {"por_reformatear": 0}},
    "cobertura": {
        "total": 94.2,
        "modulos": {"bi/a.py": 88.0, "etl/b.py": 71.5},
        "pruebas_ok": 10,
        "pruebas_omitidas": 1,
    },
    "pruebas": {"pruebas": 11},
    "mypy": {"errores": 0, "funciones": 10, "con_tipo_de_retorno": 10},
    "complejidad": {"funciones_sobre_10": 6},
    "bandit": {"alta": 0},
    "pip_audit": {"archivos": {"requirements.txt": {"vulnerabilidades": 0}}},
    "secretos": {"sin_clasificar": 0},
    "consultas": {"consultas": {"k1": 0.2, "k3": 0.4}},
    "navegadores": {
        "paginas": {"Panorama de precios": {"seconds": 0.3, "violations": 0}},
        "violaciones_wcag": 0,
        "navegadores": {"chromium": {"checks": 3, "passed": 3, "failed": []}},
    },
}


def test_d323_the_indicators_are_read_from_the_measurement_and_checked_against_the_goals():
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    values = quality_metrics.values(REPORT)
    assert values["ruff_avisos"] == 3 and values["cobertura_por_modulo"] == 71.5 and values["pruebas_fallidas"] == 0
    assert "segundos_por_consulta" not in values and "complejidad_sobre_10" not in values  # D-330: out of scope
    rows = {row["key"]: row for row in quality_metrics.rows({}, REPORT, goals)}
    assert rows["ruff_avisos"]["ok"] is False and rows["cobertura_total"]["ok"] is True
    assert quality_metrics.gaps(REPORT, goals) == {
        "mantenibilidad": [
            (
                "Avisos de Ruff (E, F y W; el largo de línea, aparte): 3 (meta ≤ 0)",
                "Ruff findings (E, F and W; line length apart): 3 (goal ≤ 0)",
            )
        ]
    }


def test_d323_the_verifier_fails_naming_the_indicator_below_its_goal(tmp_path):
    report = tmp_path / "medicion.json"
    report.write_text(json.dumps(REPORT))
    done = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verificar_calidad.py"), str(report)], capture_output=True, text=True
    )
    assert done.returncode == 1 and "Peor que lo aceptable: ruff_avisos" in done.stdout
    report.write_text(json.dumps({**REPORT, "ruff": {"errores": 0, "formato": {"por_reformatear": 0}}}))
    assert (
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verificar_calidad.py"), str(report)], capture_output=True
        ).returncode
        == 0
    )


def test_d323_the_rubric_has_the_eight_characteristics_graded_0_to_4_with_a_date_and_a_state():
    rubric = quality_metrics.read(quality_metrics.RUBRIC_FILE)
    items = rubric["caracteristicas"]
    assert len(items) == 8 and all(item["nota"] in range(5) for item in items)
    assert {item["clave"] for item in items} >= {
        row[4] for row in quality_metrics.INDICATORS
    }  # every indicator has a home
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", rubric["fecha"]) and rubric["estado"] in ("borrador", "confirmada")
    header = quality_method.build_header(REPORT, rubric)
    assert rubric["fecha"] in header and "abc1234" in header
    assert ("pendiente de su confirmación" in header) == (rubric["estado"] != "confirmada")


def test_d323_ruff_counts_the_same_rules_before_and_after_and_a_zero_count_of_formatting_is_read():
    # The baseline counted E501 inside; the indicator compares E, F and W without it on both sides.
    assert quality_metrics.values({"ruff": {"errores": 1984, "errores_sin_largo_de_linea": 208}})["ruff_avisos"] == 208
    sys.path.insert(0, str(ROOT / "scripts"))
    import medir_calidad

    assert medir_calidad.count_formatting("145 files already formatted") == (0, 145)
    assert medir_calidad.count_formatting("2 files would be reformatted, 143 files already formatted") == (2, 143)
    assert medir_calidad.count_formatting("error: no files") == (None, None)


def test_d323_a_candidate_the_author_marked_as_not_secret_counts_as_reviewed():
    sys.path.insert(0, str(ROOT / "scripts"))
    import medir_calidad

    baseline = json.loads((ROOT / ".secrets.baseline").read_text())
    reviewed = medir_calidad.reviewed_secret_hashes()
    assert reviewed == {item["hashed_secret"] for items in baseline["results"].values() for item in items}
    found = {name: items for name, items in baseline["results"].items() if name == ".github/workflows/calidad.yml"}
    assert medir_calidad.classify_secret_candidates(found) == {"falsos_positivos": 1, "sin_clasificar": 0}


def test_d323_the_history_keeps_every_measurement_once_and_the_page_shows_it_newest_first(monkeypatch):
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    history = quality_metrics.add_to_history({}, {**REPORT, "commit": "old0001", "generado": "2026-10-20 10:00 UTC"})
    history = quality_metrics.add_to_history(history, REPORT)
    history = quality_metrics.add_to_history(history, REPORT)  # the same commit again replaces it
    assert [entry["commit"] for entry in history["mediciones"]] == ["old0001", "abc1234"]
    assert quality_metrics.met(history["mediciones"][-1]["valores"], goals) == (7, 8)  # 8 of code measured, Ruff fails
    monkeypatch.setattr(i18n, "is_english", lambda: False)
    page = quality_method.build_history(history, goals)
    assert page.index("abc1234") < page.index("old0001") and "7 / 8" in page
    assert all(what[0] in page for what, _, _ in quality_metrics.SCHEDULE)
    saved = quality_metrics.read(quality_metrics.HISTORY_FILE)["mediciones"]
    assert saved[-1]["commit"] == quality_metrics.read(quality_metrics.REPORT_FILE)["commit"]


def test_d323_the_report_and_the_pull_request_come_from_the_measurement_files():
    sys.path.insert(0, str(ROOT / "scripts"))
    import informe_calidad

    baseline, report, goals, rubric, history = quality_method.read_all()
    text = informe_calidad.build_report(baseline, report, goals, rubric, history)
    assert text == (ROOT / "docs" / "calidad" / "INFORME.md").read_text(encoding="utf-8")  # the file is up to date
    assert report["commit"] in text and "```" not in text
    assert not any(word in text.lower() for word in FORBIDDEN)
    body = informe_calidad.build_pull_request(baseline, report, goals)
    passed, measured = quality_metrics.met(quality_metrics.values(report), goals)
    assert f"{passed} de {measured} indicadores" in body and "pendiente de confirmación del autor" in body


def test_d323_the_page_quotes_the_files_and_never_claims_certification(monkeypatch):
    baseline, report, goals, rubric, history = quality_method.read_all()
    for english in (False, True):
        monkeypatch.setattr(i18n, "is_english", lambda english=english: english)
        text = " ".join(
            [
                quality_method.build_header(report, rubric),
                quality_method.build_summary(baseline, report, goals),
                quality_method.build_iso(report, goals, rubric),
                quality_method.build_browsers(report, goals),
                quality_method.build_standards(report),
                quality_method.build_history(history, goals),
                quality_method.build_limits(report, goals),
            ]
        ).lower()
        assert not any(word in text for word in FORBIDDEN), english
        average = quality_method.number(quality_method.rubric_average(rubric), 1)
        assert average.lower() in text


@pytest.mark.parametrize("language", ["es", "en"])
def test_d320_the_line_under_the_logo_opens_the_page_in_both_languages(language):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params.update({"perfil": "profesional", "lang": language})
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.sidebar.markdown)
    expected = "Assessed against ISO/IEC 25010 · 25012" if language == "en" else "Evaluado según ISO/IEC 25010 · 25012"
    assert expected in markup
    page = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    page.query_params.update({"perfil": "profesional", "lang": language, "vista": "Método y calidad"})
    page.run()
    assert not page.exception and len(page.tabs) == 7
    content = " ".join(block.value for block in page.markdown if "qm-pane" in block.value)
    assert content and not re.search(r"month_start|>None<|\bnan\b", content)


# region Acceptables, goals and insights (D-330)
def test_d330_metas_keeps_the_approved_twelve_indicators_with_their_explanation():
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    keys = [key for key, *_ in quality_metrics.INDICATORS]
    assert set(keys) == {key for key in goals if key != "nota"} and len(keys) == 12
    assert sum(goals[key]["tipo"] == "datos" for key in keys) == 4
    for key in keys:
        goal = goals[key]
        assert ("max" in goal) != ("min" in goal) and "meta" in goal and "margen_critico" in goal, key
        assert all(len(goal[field]) == 2 and all(goal[field]) for field in ("que_mide", "por_que", "como", "accion"))
    # The approved numbers (2026-10-29).
    assert goals["cobertura_total"]["min"] == 90 and goals["cobertura_por_modulo"]["min"] == 70
    assert goals["comparables_pct"]["min"] == 90 and goals["vigencia_dias"]["max"] == 8
    assert (
        goals["pip_audit_vulnerabilidades"]["max"] == 0 and goals["pip_audit_vulnerabilidades"]["margen_critico"] == 0
    )


def test_d330_the_state_says_meets_warning_urgent_or_critical():
    coverage = {"min": 90, "meta": 95, "margen_critico": 5}
    assert [quality_metrics.state(value, coverage) for value in (96, 92, 86, 84, None)] == [
        "cumple",
        "aviso",
        "urgente",
        "critico",
        "sin_medicion",
    ]
    ruff = {"max": 0, "meta": 0, "margen_critico": 5}
    assert [quality_metrics.state(value, ruff) for value in (0, 3, 6)] == ["cumple", "urgente", "critico"]
    secrets = {"max": 0, "meta": 0, "margen_critico": 0}
    assert quality_metrics.state(1, secrets) == "critico"  # any case is critical


def test_d330_the_failure_reads_against_the_acceptable_and_the_insight_comes_from_the_policy():
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    report = dict(REPORT, datos={"pct_comparacion": 85.0, "pct_rechazadas": 0.01, "dias_desde_ultima_carga": 7})
    rows = {row["clave"]: row for row in quality_metrics.evaluate(report, goals, policy)}
    comparables = rows["comparables_pct"]
    assert (comparables["falla"], comparables["falla_aceptable"], comparables["estado"]) == (15.0, 10.0, "urgente")
    assert not comparables["bloquea"] and "modo aviso" in comparables["insight"][0]  # data warns until approved
    ruff = rows["ruff_avisos"]
    assert ruff["estado"] == "urgente" and ruff["bloquea"] and goals["ruff_avisos"]["accion"][0] in ruff["insight"][0]
    assert rows["cobertura_total"]["insight"][0] == policy["insight"]["cumple"][0]
    assert rows["pruebas_dbt_pct"]["estado"] == "sin_medicion" and rows["pruebas_dbt_pct"]["valor"] is None
    # The change against the previous report, never a made-up one.
    later = quality_metrics.evaluate(dict(report, ruff={"errores": 0}), goals, policy, previous=report)
    assert {row["clave"]: row["variacion"] for row in later}["ruff_avisos"] == -3


# endregion
