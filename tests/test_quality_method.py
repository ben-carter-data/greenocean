"""«Método y calidad» (D-320): every number of the page comes from docs/calidad/medicion.json, the report quotes the same
numbers, the wording never claims certification, and the line under the logo opens the page in both languages."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import i18n, quality_method

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


def every_text(report):
    pieces = [
        quality_method.build_intro(report),
        quality_method.build_standards(report),
        quality_method.build_iso(report),
        quality_method.build_code(report),
        quality_method.build_verify(report),
        quality_method.build_limits(report),
    ]
    return " ".join(pieces).lower()


def test_d320_the_page_quotes_the_numbers_of_the_measurement_and_never_claims_certification(monkeypatch):
    report = quality_method.read_report()
    for language in (False, True):
        monkeypatch.setattr(i18n, "is_english", lambda language=language: language)
        figures = quality_method.figures(report)
        assert figures["ruff"] == quality_method.number(report["ruff"]["errores"])
        assert figures["cov"] == quality_method.number(report["cobertura"]["total"], 1)
        text = every_text(report)
        assert not any(word in text for word in FORBIDDEN), language
        assert figures["ruff"].lower() in text and figures["tests"].lower() in text


def test_d320_the_grades_are_integers_from_0_to_4_and_a_missing_measure_is_not_graded():
    report = quality_method.read_report()
    grades = [grade for _, grade, _, _ in quality_method.iso_characteristics(report)]
    assert all(grade is None or grade in range(5) for grade in grades) and None in grades
    assert len(grades) == 8  # the eight characteristics of ISO/IEC 25010


def test_d320_the_report_has_the_same_figures_as_the_page():
    report = quality_method.read_report()
    figures = quality_method.figures(report)
    text = (ROOT / "docs" / "calidad" / "INFORME.md").read_text(encoding="utf-8")
    for key in ("ruff", "tests", "cov", "commits"):
        assert figures[key] in text, key
    assert "ninguna de estas mejoras se ha aplicado" in text.lower() and "autoevaluación, no una certificación" in text


@pytest.mark.parametrize("language", ["es", "en"])
def test_d320_the_line_under_the_logo_opens_the_page_in_both_languages(language):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params.update({"perfil": "profesional", "lang": language})
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.sidebar.markdown)
    expected = "Assessed against ISO/IEC 25010 · 25012" if language == "en" else "Evaluado según ISO/IEC 25010 · 25012"
    assert expected in markup and 'class="' not in expected
    page = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    page.query_params.update({"perfil": "profesional", "lang": language, "vista": "Método y calidad"})
    page.run()
    assert not page.exception and len(page.tabs) == 7
    content = " ".join(block.value for block in page.markdown if "qm-pane" in block.value)
    assert content and not re.search(r"month_start|>None<|\bnan\b", content)
