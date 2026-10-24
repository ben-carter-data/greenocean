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
    return indicators, quality_live.build_quality_html(charts.get_palette("Vantablack"), indicators, columns)


@needs_database
def test_d257_the_diagram_is_the_page_and_every_piece_opens_its_popup(measures):
    columns = quality_view.build_columns(EVIDENCE)
    indicators, page = draw(measures, columns)
    assert "Datos sanos" in page and [name for _, name, _, _ in quality_live.HUB] == [
        "Exactitud", "Validez", "Unicidad", "Actualidad", "Completitud", "Consistencia"]
    # each dimension, each gate and the centre is a link to a pop-up that exists, and closing it needs no script
    targets = [f"d-{key}" for key, *_ in quality_live.HUB] + [f"g-{index}" for index in range(3)] + ["d-todos"]
    for target in targets:
        assert f'href="#{target}"' in page and f'id="{target}"' in page, target
    assert page.count('class="modal"') == len(targets) and page.count('class="close"') == len(targets)
    assert "<script" not in page and '<base href="about:srcdoc">' in page
    # every indicator is in the pop-up of its dimension and of its gate, with its value and how it is measured
    for _, label, value, reference, status, detail in indicators:
        assert label in page and value in page and reference in page, label
    for title, stops, outcome, where, evidence in quality_live.GATES:
        assert title in page and stops in page and outcome in page
        for path in [part.strip() for part in evidence.split(",") if part.strip().startswith("tests/")]:
            assert (Path(__file__).resolve().parent / path.split("/", 1)[1]).exists(), path
    # the main view stays short: the lists of what was set aside and the controls live in their own tabs
    assert "NON_POSITIVE_PRICE" not in page and "Controles de auditoría" not in page


@needs_database
def test_d257_what_was_set_aside_and_the_loads_are_the_database_ones(measures):
    indicators = quality_live.build_indicators(measures, NOW)
    page = quality_live.build_tables_html(charts.get_palette("Vantablack"), measures["runs"], measures["rejections"], measures["flags"])
    by_label = {row[1]: row[2] for row in indicators}
    rejected = sum(count for _, _, count in measures["rejections"])
    flagged = sum(count for name, count in measures["flags"].items() if name != "SIN_MARCA")
    assert by_label["Filas rechazadas"] == quality_live.thousands(rejected)
    assert by_label["Precios apartados de los indicadores"] == quality_live.thousands(flagged)
    for reason, _, count in measures["rejections"]:
        assert reason in page and quality_live.thousands(count) in page
    assert page.count('class="tag s-fail">Rechazada') == len(measures["rejections"]) and "Marcada" in page
    assert quality_live.thousands(measures["runs"][-1][3]) in page and "Últimas cargas" in page


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
    page = quality_live.build_audit_page_html(charts.get_palette("Vantablack"), columns)
    assert page.count('class="tag k-') == sum(len(cards) for _, cards in columns)
    assert 'class="tag k-pending"' in page  # the file hashes cannot be checked here: said, not hidden


def test_d257_a_query_in_a_popup_spans_the_whole_row_and_not_the_dot_column():
    css = quality_live.build_css(charts.get_palette("Vantablack"))
    assert ".qp .ind pre {" in css and "grid-column:2 / 4" in css.split(".qp .ind pre {")[1].split("}")[0]


@needs_database
def test_d257_the_number_of_the_verdict_opens_the_list_of_all_the_indicators(measures):
    indicators, page = draw(measures)
    kind, sentence = quality_live.build_verdict(indicators)
    modal = page.split('id="d-todos"')[1]
    centre = page.split('href="#d-todos"')[1].split("</a>")[0]  # the count sits in the middle of the diagram and opens the list
    assert f"Los {len(indicators)} indicadores" in modal and f"{len(indicators)} indicadores" in centre and "Datos sanos" in centre
    assert page.count('href="#d-todos"') == 1 and "<u>" not in page  # one door only: the centre, not a hidden link on the side
    assert all(row[1] in modal and row[2] in modal for row in indicators)
    assert str(len([row for row in indicators if row[4] != "info"])) in sentence  # the 11 of the sentence are the 11 of the list
