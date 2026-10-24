"""Calidad (live measures) and its audit controls, D-196 and D-220."""
import copy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from bi import charts, quality_live, quality_view, queries

needs_database = pytest.mark.skipif(not Path(queries.DATABASE_FILE).exists(), reason="datos.duckdb is not here")
NOW = datetime(2026, 10, 20, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def measures():
    return quality_live.read_measures()


@needs_database
def test_every_measure_is_judged_against_a_threshold_shown_with_it(measures):
    indicators = quality_live.build_indicators(measures, NOW)
    assert indicators and {row[0] for row in indicators} <= set(quality_live.ICONS)
    for dimension, label, value, reference, status, detail in indicators:
        assert status in quality_live.STATUS_WORDS and reference and detail, label
    kind, sentence = quality_live.build_verdict(indicators)
    assert kind in ("ok", "warn", "fail") and sentence


@needs_database
def test_a_degraded_measure_turns_its_indicator_and_the_verdict_red(measures):
    broken = copy.deepcopy(measures)
    broken["duplicates"] = 5
    broken["last"] = "2025-01-06"
    indicators = quality_live.build_indicators(broken, NOW)
    statuses = {row[1]: row[4] for row in indicators}
    assert "fail" in statuses.values() or "warn" in statuses.values()
    kind, sentence = quality_live.build_verdict(indicators)
    assert kind != "ok" and "A revisar" in sentence


EVIDENCE = dict(rejections=201, run_id=5, run_started="19-10-2026", run_status="LOADED", run_ok=True,
                manifest_present=True, manifest_files=10, files_matching=0, files_total=10, files_failed=0,
                weeks=250, first_week="03-01-2022", last_week="12-10-2026",
                build=dict(models=16, tests=31, passing=31, ok=True, built_at="19-10-2026"),
                checks=dict(integrity_ok=True, foreign_keys=0, duplicates=0, invalid=0), parity=None)


def draw(measures, columns=()):
    indicators = quality_live.build_indicators(measures, NOW)
    return indicators, quality_live.build_page_html(charts.get_palette("Vantablack"), indicators, measures["runs"],
                                                    measures["rejections"], measures["flags"], columns)


@needs_database
def test_d256_the_page_follows_the_data_six_dimensions_three_gates_what_was_set_aside_and_the_controls(measures):
    columns = quality_view.build_columns(EVIDENCE)
    indicators, page = draw(measures, columns)
    # the six dimensions around healthy data, then the three gates, then the lists, then the controls
    assert "Datos sanos" in page and [name for _, name, _, _ in quality_live.HUB] == [
        "Exactitud", "Validez", "Unicidad", "Actualidad", "Completitud", "Consistencia"]
    order = ["Las seis dimensiones", "Las tres puertas", "Lo que se apartó", "Controles de auditoría"]
    assert [page.index(text) for text in order] == sorted(page.index(text) for text in order)
    for number in "1234":
        assert f"<b>{number}</b>" in page
    # every indicator is under the gate that watches it, each gate with what it stops
    assert page.count('<div class="gate"') == len(quality_live.GATE_VIEW) == len(quality_live.GATES) == 3
    assert {key for _, _, keys in quality_live.GATE_VIEW for key in keys} == set(quality_live.ICONS)
    for _, label, value, *_ in indicators:
        assert label in page and value in page, label
    assert page.count("Detiene:") == 3 and "<script" not in page
    for title, stops, outcome, where, evidence in quality_live.GATES:
        assert title in page and stops[:30] in page
        for path in [part.strip() for part in evidence.split(",") if part.strip().startswith("tests/")]:
            assert (Path(__file__).resolve().parent / path.split("/", 1)[1]).exists(), path


@needs_database
def test_d256_the_figures_of_what_was_set_aside_are_the_database_ones(measures):
    indicators, page = draw(measures)
    by_label = {row[1]: row[2] for row in indicators}
    rejected = sum(count for _, _, count in measures["rejections"])
    flagged = sum(count for name, count in measures["flags"].items() if name != "SIN_MARCA")
    assert by_label["Filas rechazadas"] == quality_live.thousands(rejected)
    assert by_label["Precios apartados de los indicadores"] == quality_live.thousands(flagged)
    for reason, _, count in measures["rejections"]:
        assert reason in page and quality_live.thousands(count) in page
    assert page.count('class="tag s-fail">Rechazada') == len(measures["rejections"]) and "Marcada" in page
    last = measures["runs"][-1]
    assert f"{quality_live.thousands(last[3])}" in page and "Últimas cargas" in page


@needs_database
def test_d256_accuracy_is_the_audit_controls_of_the_results_and_a_pending_one_is_said(measures):
    columns = quality_view.build_columns(EVIDENCE)
    indicators = quality_live.build_indicators(measures, NOW)
    status, headline = quality_live.hub_measure("exactitud", indicators, columns)
    results = dict(columns)[quality_live.RESULTS_STEP]
    kinds = [quality_view.classify(card[2]) for card in results]
    assert status == ("warn" if "pending" in kinds else "ok") and f"{kinds.count('ok')} de {len(kinds)} controles" in headline
    assert quality_live.hub_measure("exactitud", indicators, ())[0] == "info"  # without controls it claims nothing
    for key in ("validez", "unicidad", "actualidad", "completitud", "consistencia"):
        assert quality_live.hub_measure(key, indicators, columns)[0] in ("ok", "warn", "fail")


def test_the_audit_controls_are_rows_with_their_status():
    columns = quality_view.build_columns(EVIDENCE)
    page = quality_live.build_audit_html(columns)
    assert page.count('class="tag k-') == sum(len(cards) for _, cards in columns)
    assert 'class="tag k-pending"' in page  # the file hashes cannot be checked here: said, not hidden
