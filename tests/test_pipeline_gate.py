"""RF-03 (D-245): only a valid load is published. etl/pipeline.py never replaces datos.duckdb when dbt fails or the
load reads far fewer rows than the last good one; it records the failed run instead.

Nothing here touches the real databases: the steps that read files or write the served database are replaced."""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl, pipeline  # noqa: E402

HISTORY = [(5, "2026-10-13T12:00:00", etl.STATUS_LOADED, 2_500_000, 2_499_800, 200, "")]


@pytest.fixture
def steps(tmp_path, monkeypatch):
    """Every side effect of main() captured; raw.db is an empty stand-in."""
    raw = tmp_path / "raw.db"
    sqlite3.connect(raw).close()
    monkeypatch.setattr(etl, "RAW_DATABASE_FILE", raw)
    monkeypatch.setattr(pipeline.bronze, "export_source", lambda connection, source: None)
    monkeypatch.setattr(pipeline, "prepare_ipc", lambda: None)
    monkeypatch.setattr(pipeline, "read_run_history", lambda: list(HISTORY))
    calls = {"written": [], "failed": []}
    monkeypatch.setattr(pipeline, "write_serving_database", lambda *args, **kwargs: calls["written"].append(args))
    monkeypatch.setattr(pipeline, "record_failed_run", lambda history, run, *args: calls["failed"].append(run))
    return calls, monkeypatch


def test_rf03_a_failed_dbt_build_records_the_failure_and_never_replaces_the_served_database(steps):
    calls, monkeypatch = steps
    monkeypatch.setattr(pipeline, "run_dbt", lambda run_id, command=None: (False, "1 test failed"))
    assert pipeline.main(load_raw=False) == 1
    assert calls["written"] == []
    (run,) = calls["failed"]
    assert run[0] == 6 and run[2] == etl.STATUS_FAILED and "dbt build" in run[6]


def test_rf03_a_load_with_far_fewer_rows_than_the_last_good_one_is_refused(steps):
    calls, monkeypatch = steps
    monkeypatch.setattr(pipeline, "run_dbt", lambda run_id, command=None: (True, "ok"))
    monkeypatch.setattr(
        pipeline, "count_rows", lambda: (1_000_000, 999_900, 100)
    )  # under 90 % of the last good load (MINIMUM_ROWS_RATIO)
    assert pipeline.main(load_raw=False) == 1
    assert calls["written"] == [] and calls["failed"][0][2] == etl.STATUS_FAILED


def test_rf03_a_good_load_is_the_only_one_that_replaces_the_served_database(steps):
    calls, monkeypatch = steps
    monkeypatch.setattr(pipeline, "run_dbt", lambda run_id, command=None: (True, "ok"))
    monkeypatch.setattr(pipeline, "count_rows", lambda: (2_521_012, 2_520_811, 201))
    monkeypatch.setattr(
        pipeline,
        "SERVING_DATABASE_FILE",
        type("Size", (), {"name": "datos.duckdb", "stat": lambda self: type("S", (), {"st_size": 1})()})(),
    )
    assert pipeline.main(load_raw=False) == 0
    assert calls["failed"] == [] and len(calls["written"]) == 1
    run = calls["written"][0][1]
    assert run[2] == etl.STATUS_LOADED and run[3] == run[4] + run[5]  # read = loaded + rejected
