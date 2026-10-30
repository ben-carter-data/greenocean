"""D-356: a source that is late. The load publishes up to the last week complete in both sources and never fills a week
in; a recent week one source has not published yet does not stop it, a hole in the middle or a source more than two
weeks behind does."""

import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from etl import etl, pipeline  # noqa: E402

RUN_DATE = date(2026, 10, 30)  # a Thursday: the last complete week starts on 2026-10-19


def prices(weeks_by_source):
    rows = [
        {
            "source": source,
            "week_start": pd.Timestamp(week),
            "region_id": 13,
            "channel": "Feria libre",
            "product_group": "Frutas",
            "product": "Manzana",
            "variety": "Fuji",
            "quality": "Primera",
            "normalized_unit": "$/kilo",
        }
        for source, weeks in weeks_by_source.items()
        for week in weeks
    ]
    return pd.DataFrame(rows)


def test_d356_a_recent_week_one_source_has_not_published_does_not_stop_the_load_and_waits():
    weekly = prices(
        {
            etl.SOURCE_CONSUMER: ["2026-10-05", "2026-10-12", "2026-10-19"],
            etl.SOURCE_WHOLESALE: ["2026-10-05", "2026-10-12"],
        }
    )
    last = etl.last_week_by_source(weekly)
    assert etl.published_until(last) == "2026-10-12"  # nothing after the week complete in both
    assert etl.late_source_problems(last, RUN_DATE) == []  # one week behind: allowed
    assert etl.held_back_notice(last) == f"{etl.NOTICE_SOURCE_LATE}: {etl.SOURCE_WHOLESALE} 2026-10-19"
    kept = weekly[weekly["week_start"] <= pd.Timestamp(etl.published_until(last))]
    assert not [problem for problem in etl.check_quality(kept, 1, None, RUN_DATE, last) if "LATE" in problem]


def test_d356_a_hole_in_the_middle_of_the_data_stops_the_load():
    weekly = prices(
        {
            etl.SOURCE_CONSUMER: ["2026-09-28", "2026-10-12", "2026-10-19"],  # 2026-10-05 is missing
            etl.SOURCE_WHOLESALE: ["2026-09-28", "2026-10-05", "2026-10-12", "2026-10-19"],
        }
    )
    problems = etl.check_quality(weekly, 1, None, RUN_DATE, etl.last_week_by_source(weekly))
    assert any(problem.startswith(etl.PROBLEM_MISSING_WEEKS) and "2026-10-05" in problem for problem in problems)


def test_d356_a_source_more_than_two_weeks_behind_stops_the_load_with_an_urgent_reason():
    last = {etl.SOURCE_CONSUMER: "2026-10-19", etl.SOURCE_WHOLESALE: "2026-09-28"}
    assert etl.weeks_behind("2026-09-28", RUN_DATE) == 3 and etl.weeks_behind("2026-10-05", RUN_DATE) == 2
    (problem,) = etl.late_source_problems(last, RUN_DATE)
    assert problem.startswith(etl.PROBLEM_LATE_SOURCE) and etl.SOURCE_WHOLESALE in problem and "3 weeks" in problem
    assert etl.late_source_problems({**last, etl.SOURCE_WHOLESALE: "2026-10-05"}, RUN_DATE) == []  # exactly 2: allowed


def test_d356_the_pipeline_refuses_a_late_source_and_names_the_held_week_on_a_good_load(tmp_path, monkeypatch):
    import sqlite3

    raw = tmp_path / "raw.db"
    sqlite3.connect(raw).close()
    monkeypatch.setattr(etl, "RAW_DATABASE_FILE", raw)
    monkeypatch.setattr(pipeline.bronze, "export_source", lambda connection, source: None)
    monkeypatch.setattr(pipeline, "prepare_ipc", lambda: None)
    monkeypatch.setattr(
        pipeline, "read_run_history", lambda: [(5, "2026-10-13T12:00:00", etl.STATUS_LOADED, 10, 10, 0, "")]
    )
    monkeypatch.setattr(pipeline, "run_dbt", lambda run_id, command=None: (True, "ok"))
    monkeypatch.setattr(pipeline, "count_rows", lambda: (10, 10, 0))
    monkeypatch.setattr(pipeline, "date", type("Day", (), {"today": staticmethod(lambda: RUN_DATE)}))
    calls = {"written": [], "failed": []}
    monkeypatch.setattr(pipeline, "write_serving_database", lambda history, run, *a, **k: calls["written"].append(run))
    monkeypatch.setattr(pipeline, "record_failed_run", lambda history, run, *a: calls["failed"].append(run))
    monkeypatch.setattr(pipeline, "read_last_weeks", lambda: {"consumer": "2026-10-19", "wholesale": "2026-09-28"})
    assert pipeline.main(load_raw=False) == 1 and not calls["written"]
    assert calls["failed"][0][6].startswith(etl.PROBLEM_LATE_SOURCE)
    monkeypatch.setattr(pipeline, "read_last_weeks", lambda: {"consumer": "2026-10-19", "wholesale": "2026-10-12"})
    monkeypatch.setattr(
        pipeline,
        "SERVING_DATABASE_FILE",
        type("F", (), {"name": "x", "stat": lambda self: type("S", (), {"st_size": 1})()})(),
    )
    assert pipeline.main(load_raw=False) == 0
    assert calls["written"][-1][6] == f"{etl.NOTICE_SOURCE_LATE}: wholesale 2026-10-19"


def test_d356_dbt_publishes_up_to_the_week_complete_in_both_sources():
    model = (ROOT / "dbt" / "models" / "intermediate" / "int_prices__outlier_flagged.sql").read_text(encoding="utf-8")
    assert "where week_start <= (" in model and "min(last_week)" in model and "group by source" in model
    assert "D-356" in (ROOT / "dbt" / "tests" / "d042_no_unexpected_missing_week.sql").read_text(encoding="utf-8")


def test_d356_the_panorama_says_which_week_a_source_has_not_published_and_nothing_else():
    from bi import dashboard

    message = f"{etl.NOTICE_SOURCE_LATE}: wholesale 2026-10-19"
    assert dashboard.describe_late_sources(message) == "ODEPA aún no publica la semana del 19-10 (mayorista)"
    assert dashboard.describe_late_sources("") == "" and dashboard.describe_late_sources("dbt build: x") == ""
