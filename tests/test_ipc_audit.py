"""IPC audit (D-155): the deflator the panel uses is recomputed from the INE rows.

The raw rows of both INE files are kept in ine_ipc_source exactly as published (text).
This test links the two series and builds the weekly factor again in plain Python,
without dbt, and compares it with ipc_monthly and ipc_weekly.
"""

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import queries  # noqa: E402

needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="etl/datos.duckdb has not been built")


def number(text):
    return float(text.replace(".", "").replace(",", "."))


def recompute_monthly():
    """{(year, month): food index in base 2023}, from the published text."""
    rows = queries.run_sql("SELECT file, year, month, index_value, monthly_change FROM ine_ipc_source")
    base, spliced, january_change = {}, {}, None
    for file, year, month, index_value, monthly_change in rows.itertuples(index=False):
        key = (int(year), int(month))
        if file == "base_2023":
            base[key] = number(index_value)
            if key == (2024, 1):
                january_change = number(monthly_change)
        else:
            spliced[key] = number(index_value)
    factor = base[(2024, 1)] / (1 + january_change / 100) / spliced[(2023, 12)]
    monthly = {key: value * factor for key, value in spliced.items() if key < (2024, 1)}
    monthly.update(base)
    return monthly


@needs_database
def test_monthly_index_matches_the_ine_rows():
    expected = recompute_monthly()
    published = {
        (row.year, row.month): row.food_index for row in queries.run_sql("SELECT * FROM ipc_monthly").itertuples()
    }
    assert published.keys() == expected.keys()
    for key, value in expected.items():
        assert published[key] == pytest.approx(value, rel=1e-12)


@needs_database
def test_months_are_consecutive_and_the_link_keeps_the_official_january_change():
    monthly = recompute_monthly()
    keys = sorted(monthly)
    for (year, month), (next_year, next_month) in zip(keys, keys[1:]):
        assert (next_year, next_month) == ((year, month + 1) if month < 12 else (year + 1, 1))
    assert monthly[(2024, 1)] / monthly[(2023, 12)] - 1 == pytest.approx(0.01, abs=5e-4)


@needs_database
def test_weekly_factor_uses_the_month_of_the_monday_and_the_last_published_month():
    monthly = recompute_monthly()
    reference = max(monthly)
    weeks = queries.run_sql("SELECT * FROM ipc_weekly ORDER BY week_start")
    calendar = queries.run_sql("SELECT COUNT(*) AS n FROM dim_date")["n"][0]
    assert len(weeks) == calendar
    for row in weeks.itertuples(index=False):
        monday = date.fromisoformat(row.week_start)
        assert monday.weekday() == 0
        month = (monday.year, monday.month)
        provisional = month not in monthly
        assert bool(row.provisional) == provisional
        used = reference if provisional else month
        assert (row.ipc_year, row.ipc_month) == used
        assert (row.reference_year, row.reference_month) == reference
        assert row.real_factor == pytest.approx(monthly[reference] / monthly[used], rel=1e-12)


@needs_database
def test_only_weeks_after_the_last_published_month_are_provisional():
    weeks = queries.run_sql("SELECT week_start, provisional FROM ipc_weekly ORDER BY week_start")
    flags = list(weeks["provisional"])
    first = flags.index(True) if True in flags else len(flags)
    assert all(flags[first:]) and not any(flags[:first])
