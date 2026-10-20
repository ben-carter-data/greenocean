"""Calidad (live measures) and Auditoría (price trace), D-196."""
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


def test_the_file_check_is_honest_when_the_file_is_missing_or_altered(tmp_path):
    assert audit_trace.check_file("x.csv", {}, tmp_path)[0] == "pending"
    assert audit_trace.check_file("x.csv", {"hash": "abc"}, tmp_path)[0] == "pending"
    assert "no se puede comprobar" in audit_trace.check_file("x.csv", {"hash": "abc"}, tmp_path)[1]
    (tmp_path / "x.csv").write_bytes(b"hola")
    assert audit_trace.check_file("x.csv", {"hash": "abc"}, tmp_path)[0] == "fail"
    import hashlib
    good = hashlib.sha256(b"hola").hexdigest()
    assert audit_trace.check_file("x.csv", {"hash": good}, tmp_path)[0] == "ok"


@needs_database
def test_the_trace_follows_one_real_price_through_six_steps():
    series = audit_trace.find_series("Tomate", "Supermercado", "Región Metropolitana de Santiago")
    assert len(series)
    first = series.iloc[0]
    row = audit_trace.read_trace("Tomate", first["variety"], first["quality"], "Supermercado",
                                 "Región Metropolitana de Santiago", first["normalized_unit"])
    assert row and row["price"] > 0
    run = {"run_id": 1, "started_at": "2026-10-19", "rows_read": 10, "rows_loaded": 9, "rows_rejected": 1}
    steps = audit_trace.build_trace_steps(row, {}, run, None, ("pending", "no disponible"))
    assert len(steps) == 6
