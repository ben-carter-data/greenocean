"""Tests for the K6 price alerts."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import alerts  # noqa: E402

# Thirteen weeks that go up and down 1 %, so twelve small variations.
STEADY_PRICES = [1000, 1010] * 6 + [1000]


def make_price_series(prices, first_week="2026-01-05"):
    """National weekly prices of one product, one row per consecutive week."""
    return pd.DataFrame(
        {
            "week_start": pd.date_range(first_week, periods=len(prices), freq="7D"),
            "product_group": "Hortalizas",
            "product": "Tomate",
            "variety": "Larga vida",
            "quality": "Primera",
            "channel": "Feria libre",
            "normalized_unit": "kilo",
            "national_price": prices,
        }
    )


def test_k6_weekly_variation_is_the_change_against_the_week_before():
    prices = alerts.add_weekly_variation(make_price_series([1000, 1100, 990]))
    assert pd.isna(prices["variation"].iloc[0])
    assert list(prices["variation"].iloc[1:].round(4)) == [0.1, -0.1]


def test_k6_jump_outside_two_deviations_is_an_alert():
    alert_rows = alerts.find_price_alerts(make_price_series(STEADY_PRICES + [1300]))
    assert len(alert_rows) == 1
    assert alert_rows.iloc[0]["national_price"] == 1300
    assert round(alert_rows.iloc[0]["variation"], 2) == 0.3


def test_k6_usual_movement_is_not_an_alert():
    alert_rows = alerts.find_price_alerts(make_price_series(STEADY_PRICES + [1010]))
    assert alert_rows.empty


def test_k6_series_with_less_than_twelve_previous_variations_is_not_judged():
    alert_rows = alerts.find_price_alerts(make_price_series([1000, 1010, 1000, 1300]))
    assert alert_rows.empty


def test_k6_change_across_a_week_without_data_is_not_a_weekly_variation():
    prices = make_price_series([1000, 1010, 1300])
    prices = prices[prices["national_price"] != 1010]
    assert alerts.add_weekly_variation(prices)["variation"].isna().all()


def test_k6_each_product_is_judged_with_its_own_history():
    steady_series = make_price_series(STEADY_PRICES + [1010])
    jumping_series = make_price_series(STEADY_PRICES + [1300]).assign(product="Palta")
    alert_rows = alerts.find_price_alerts(pd.concat([steady_series, jumping_series]))
    assert list(alert_rows["product"]) == ["Palta"]
