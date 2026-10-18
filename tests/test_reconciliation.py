"""Reconciliation (T-47): the SQL versions of K6 and K5 give what Python gives.

Python is the version the dashboard uses; the SQL versions live in bi/queries.sql.
Both run on the real etl/datos.db, so every real edge case is compared.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import alerts, lag, queries  # noqa: E402

needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(),
                                    reason="etl/datos.db has not been built")
# Only rounding differences are accepted.
TOLERANCE = 1e-9
K5_SERIES_COLUMNS = ["product_group", "product", "variety", "quality",
                     "normalized_unit", "region", "channel"]


# region Python versions
def calculate_k6_in_python():
    """Weeks judged by K6 in bi/alerts.py, with their alert flag."""
    prices = alerts.add_usual_range(queries.run_query("k6_national_weekly_price"))
    judged = prices.dropna(subset=["variation", "usual_variation"]).copy()
    judged["is_alert"] = alerts.is_price_alert(judged).astype(int)
    return judged


def calculate_k5_variations_in_python():
    """Weekly changes of bi/lag.py for every K5 series with 26 weeks or more."""
    margins = queries.run_query("k1_margin")
    series_parts = [lag.add_weekly_variations(series_rows)
                    for _, series_rows in margins.groupby(K5_SERIES_COLUMNS)
                    if lag.has_enough_weeks(series_rows)]
    return pd.concat(series_parts, ignore_index=True)


def read_sql_version(query_name):
    rows = queries.run_query(query_name)
    rows["week_start"] = pd.to_datetime(rows["week_start"])
    return rows


def assert_columns_match(merged, python_column, sql_column):
    python_values = merged[python_column].to_numpy(dtype=float)
    sql_values = merged[sql_column].to_numpy(dtype=float)
    assert np.allclose(python_values, sql_values, rtol=0, atol=TOLERANCE, equal_nan=True)
# endregion


@needs_database
def test_k6_sql_and_python_judge_the_same_weeks_with_the_same_range():
    python_rows = calculate_k6_in_python()
    sql_rows = read_sql_version("k6_usual_range_sql")
    keys = alerts.SERIES_COLUMNS + ["week_start"]
    merged = python_rows.merge(sql_rows, on=keys, how="outer", suffixes=("", "_sql"),
                               indicator=True)
    assert (merged["_merge"] == "both").all()
    assert_columns_match(merged, "variation", "variation_sql")
    assert_columns_match(merged, "usual_variation", "usual_variation_sql")
    # SQL gives the sample variance; pandas gives its square root.
    merged["python_variance"] = merged["variation_deviation"] ** 2
    assert_columns_match(merged, "python_variance", "variation_variance")


@needs_database
def test_k6_sql_and_python_raise_the_same_alerts():
    python_rows = calculate_k6_in_python()
    sql_rows = read_sql_version("k6_usual_range_sql")
    keys = alerts.SERIES_COLUMNS + ["week_start"]
    merged = python_rows.merge(sql_rows, on=keys, suffixes=("", "_sql"))
    assert merged["is_alert"].sum() > 0
    assert (merged["is_alert"] == merged["is_alert_sql"]).all()


@needs_database
def test_k5_sql_and_python_give_the_same_series_and_weekly_changes():
    python_rows = calculate_k5_variations_in_python()
    sql_rows = read_sql_version("k5_weekly_variations_sql")
    keys = K5_SERIES_COLUMNS + ["week_start"]
    merged = python_rows.merge(sql_rows, on=keys, how="outer", suffixes=("", "_sql"),
                               indicator=True)
    assert (merged["_merge"] == "both").all()
    assert_columns_match(merged, "wholesale_variation", "wholesale_variation_sql")
    assert_columns_match(merged, "consumer_variation", "consumer_variation_sql")


def test_k5_sql_uses_the_same_minimum_of_weeks_as_python():
    assert f"HAVING COUNT(*) >= {lag.MINIMUM_WEEKS}" in queries.load_queries()[
        "k5_weekly_variations_sql"]
