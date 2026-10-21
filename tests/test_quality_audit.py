"""Calidad (live measures) and its audit controls, D-196 and D-220."""
import copy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from bi import audit_trace, charts, quality_live, queries

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


@needs_database
def test_quality_page_renders_every_dimension_and_escapes_nothing_unsafe(measures):
    indicators = quality_live.build_indicators(measures, NOW)
    html = quality_live.build_page_html(charts.get_palette(next(iter(charts.PALETTES))),
                                        indicators, measures["runs"], measures["rejections"], measures["flags"])
    for title in quality_live.TITLES.values():
        assert title in html
    assert "<script" not in html


@needs_database
def test_quality_view_hangs_each_dimension_from_the_pipeline_without_cards(measures):
    indicators = quality_live.build_indicators(measures, NOW)
    page = quality_live.build_page_html(charts.get_palette("Vantablack"), indicators, measures["runs"],
                                        measures["rejections"], measures["flags"])
    assert page.count('class="cell spine"') == len(quality_live.SPINE) == 4
    assert set(quality_live.PLACES) == set(quality_live.ICONS)
    assert 'class="group' not in page and "Qué se apartó" in page and "Cargas" in page
    # D-220: one column per stop, its dimensions stacked under it, in the pipeline's order.
    assert page.count('class="gates"') == 4
    for keys in quality_live.COLUMNS:
        titles = [quality_live.TITLES[key] for key in keys]
        assert [page.index(title) for title in titles] == sorted(page.index(title) for title in titles)
    assert page.index('class="cell spine"') < page.index('class="gates"') < page.index('class="bottom"')


@needs_database
def test_d220_the_audit_controls_close_the_quality_view_without_a_filter(measures):
    indicators = quality_live.build_indicators(measures, NOW)
    page = quality_live.build_page_html(charts.get_palette("Vantablack"), indicators, measures["runs"],
                                        measures["rejections"], measures["flags"], '<div class="controls">x</div>')
    assert "Controles de auditoría" in page and page.index('class="bottom"') < page.index('class="audit"')
    assert not hasattr(audit_trace, "read_trace") and not hasattr(audit_trace, "find_series")


def test_the_audit_controls_are_small_icons_with_their_status():
    from bi import quality_view
    evidence = dict(rejections=201, run_id=5, run_started="19-10-2026", run_status="LOADED", run_ok=True,
                    manifest_present=True, manifest_files=10, files_matching=0, files_total=10, files_failed=0,
                    weeks=250, first_week="03-01-2022", last_week="12-10-2026",
                    build=dict(models=16, tests=31, passing=31, ok=True, built_at="19-10-2026"),
                    checks=dict(integrity_ok=True, foreign_keys=0, duplicates=0, invalid=0), parity=None)
    controls = quality_view.build_columns(evidence)
    html = audit_trace.build_controls_html(controls)
    assert html.count('class="ctl s-') == sum(len(cards) for _, cards in controls)
    assert 'class="ctl s-pending"' in html  # the file hashes cannot be checked here: said, not hidden
