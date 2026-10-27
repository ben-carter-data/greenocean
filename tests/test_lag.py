"""Tests for K5, the lag between the wholesale and the consumer price (T-29)."""

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import lag  # noqa: E402


def make_series(wholesale_prices, consumer_prices, first_week="2026-01-05"):
    """One series of consecutive weeks with both prices."""
    weeks = pd.date_range(first_week, periods=len(wholesale_prices), freq="7D")
    return pd.DataFrame({"week_start": weeks, "wholesale_price": wholesale_prices, "consumer_price": consumer_prices})


def make_follower_series(lag_weeks, week_count=40):
    """The consumer price repeats the wholesale price lag_weeks later (times 2)."""
    wholesale_prices = [100 + (week * 37) % 23 for week in range(week_count)]
    consumer_prices = [2 * wholesale_prices[max(week - lag_weeks, 0)] for week in range(week_count)]
    return make_series(wholesale_prices, consumer_prices)


def test_k5_weekly_variation_is_only_measured_between_consecutive_weeks():
    rows = pd.DataFrame(
        {
            "week_start": pd.to_datetime(["2026-01-05", "2026-01-12", "2026-01-26"]),
            "wholesale_price": [100.0, 110.0, 121.0],
            "consumer_price": [200.0, 200.0, 250.0],
        }
    )
    variations = lag.add_weekly_variations(rows)
    assert variations["wholesale_variation"].iloc[1] == pytest.approx(0.10)
    assert math.isnan(variations["wholesale_variation"].iloc[2])


@pytest.mark.parametrize("lag_weeks", [0, 2, 5])
def test_k5_finds_the_lag_of_a_price_that_follows_the_other(lag_weeks):
    correlations = lag.correlate_by_lag(make_follower_series(lag_weeks))
    found_lag, correlation, pair_count = lag.find_lag(correlations)
    assert found_lag == lag_weeks
    assert correlation == pytest.approx(1)
    assert lag.is_clear_relation(correlation, pair_count)


def test_k5_reports_each_lag_from_zero_to_eight_with_its_pairs():
    correlations = lag.correlate_by_lag(make_follower_series(0, week_count=30))
    assert correlations["lag_weeks"].to_list() == list(range(9))
    # 30 weeks give 29 changes; each week of lag leaves one pair out.
    assert correlations["pair_count"].to_list() == [29 - week for week in range(9)]


def test_k5_needs_26_weeks():
    assert lag.has_enough_weeks(make_follower_series(0, week_count=26))
    assert not lag.has_enough_weeks(make_follower_series(0, week_count=25))


def test_k5_without_enough_pairs_has_no_lag():
    correlations = lag.correlate_by_lag(make_series([100.0, 110.0], [200.0, 220.0]))
    assert lag.find_lag(correlations) is None


def test_k5_weak_correlation_is_not_a_clear_relation():
    # With 37 pairs the threshold is 2 / sqrt(37) = 0.33.
    assert not lag.is_clear_relation(0.14, 37)
    assert lag.is_clear_relation(0.66, 37)
    # With more data a smaller correlation is already told apart from zero.
    assert lag.is_clear_relation(0.20, 240)
