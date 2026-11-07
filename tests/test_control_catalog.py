"""D-524: «Catálogo de controles» lists every control of the project, and the new sale units do not pile up in silence."""

import pandas as pd
import pytest

from bi import charts, control_catalog, queries, report, transformation_rules, unit_review

# region Variables
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")
PALETTE = charts.get_palette(charts.MODE_DARK)
# endregion


# region Control catalog
def units(*rows):
    return pd.DataFrame(rows, columns=["source", "unit", "normalized_unit", "unit_quantity", "row_count", "first_date"])


def summary(new):
    frame = unit_review.find_unclassified(new) if len(new) else []
    return {
        "reviewed": 199,
        "known": True,
        "seen": 199,
        "new": frame.to_dict("records") if len(new) else frame,
    }


def test_d524_every_control_says_what_it_protects_when_it_runs_and_what_happens():
    controls = control_catalog.read_controls()
    assert len(controls) >= 20
    for control in controls:
        assert control["momento"] in control_catalog.MOMENTS, control["control"]
        assert control["cuando"] in control_catalog.WHEN, control["control"]
        assert control["si_falla"] in control_catalog.OUTCOMES, control["control"]
        for field in ("control", "protege"):
            spanish, english = control[field]
            assert spanish and english and spanish != english, control["control"]
        for reference in control["codigo"]:
            assert transformation_rules.locate(reference["archivo"], reference["ancla"]), reference


def test_d524_the_catalog_names_the_control_of_the_new_units_and_its_consequence():
    controls = {control["control"][0]: control for control in control_catalog.read_controls()}
    units_control = controls["Unidad nueva con precio que se puede leer de dos maneras"]
    assert units_control["si_falla"] == "detiene" and "D-524" in units_control["respaldo"]
    assert controls["Precios atípicos"]["si_falla"] == "marca"


def test_d524_a_new_unit_is_told_apart_by_what_it_can_do():
    new = unit_review.find_unclassified(
        units(
            ("wholesale", "$/caja 18 kilos", "kilo", 18.0, 100, "2022-01-03"),  # already reviewed: not new
            ("wholesale", "$/caja 111 unidades", "unidad", 111.0, 3, "2026-11-02"),  # a plain package
            ("wholesale", "$/docena de cajas 4 kilos", "kilo", 4.0, 2, "2026-11-02"),  # can be read two ways
            ("wholesale", "$/ristra", None, None, 5, "2026-11-02"),  # no price: harmless
        )
    ).set_index("unit")
    assert set(new.index) == {"$/caja 111 unidades", "$/docena de cajas 4 kilos", "$/ristra"}
    assert not new.loc["$/caja 111 unidades", "stops_the_load"]
    assert new.loc["$/docena de cajas 4 kilos", "stops_the_load"]
    assert not new.loc["$/ristra", "stops_the_load"] and not new.loc["$/ristra", "priced"]


def test_d524_the_page_lists_the_new_units_and_says_when_there_are_none():
    new = units(("wholesale", "$/docena de cajas 4 kilos", "kilo", 4.0, 2, "2026-11-02"))
    markup = control_catalog.build_units_html(summary(new), "es")
    assert "1 sin clasificar" in markup and "$/docena de cajas 4 kilos" in markup and "÷ 4 = $/kilo" in markup
    assert 'class="tag stop"' in markup and "2026-11-02" in markup
    none = control_catalog.build_units_html(summary(units()), "es")
    assert "Ninguna unidad nueva sin clasificar" in none and "<table" not in none
    assert "199 revisadas a mano" in none
    older = control_catalog.build_units_html({"reviewed": 199, "known": False, "seen": None, "new": []}, "es")
    assert "próxima carga" in older  # a base published before the table
    english = control_catalog.build_units_html(summary(new), "en")
    assert "1 not classified" in english and "sin clasificar" not in english


def test_d524_the_weekly_report_names_them_too(monkeypatch):
    monkeypatch.setattr(unit_review, "summarize", lambda *_: {"new": [{"unit": "$/ristra"}]})
    lines = report.build_units_section(None)
    assert "## Unidades de venta sin clasificar (1)" in lines and any("`$/ristra`" in line for line in lines)
    monkeypatch.setattr(unit_review, "summarize", lambda *_: {"new": []})
    assert report.build_units_section(None) == []  # nothing to say, no section


def test_d524_only_the_author_gets_links_to_the_repository():
    assert "github.com" not in control_catalog.build_controls_html("es", False)
    assert "github.com" in control_catalog.build_controls_html("es", True)


def test_d524_the_page_reads_in_english():
    page = control_catalog.build_controls_html("en", False)
    for word in ("Qué protege", "Cuándo corre", "Si falla", "Detiene la carga", "Al descargar"):
        assert word not in page, word
    assert "What it protects" in page and "Stops the load" in page


@needs_database
def test_d524_every_unit_of_the_last_load_was_reviewed():
    summary_now = unit_review.summarize()
    if not summary_now["known"]:
        pytest.skip("The published base is older than the table")
    assert summary_now["seen"] > 150 and summary_now["new"] == []
    page = control_catalog.build_page_html(PALETTE, "es", False)
    assert "Ninguna unidad nueva sin clasificar" in page


# endregion
