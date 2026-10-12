"""Tests for the T-27 year profile: it must measure what the ETL would load."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl, profile_years  # noqa: E402
from tests.test_etl import make_raw_consumer_rows, make_raw_wholesale_rows  # noqa: E402


def test_t27_rejections_are_counted_by_reason():
    reasons = pd.Series(["", "NON_POSITIVE_PRICE", "NON_POSITIVE_PRICE", "UNREADABLE_VALUE"])
    assert profile_years.count_rejections(reasons) == {"NON_POSITIVE_PRICE": 2,
                                                       "UNREADABLE_VALUE": 1}


def test_t27_new_units_come_with_the_conversion_the_etl_applies():
    new_units = profile_years.find_new_units({"$/kilo", "$/bins (430 kilos)"}, {"$/kilo"})
    assert new_units == {"$/bins (430 kilos)": ("kilo", 430.0)}


def test_t27_unit_shares_follow_rn03_to_rn05():
    units = pd.Series(["$/caja 18 kilos", "$/caja 15 unidades", "$/docena de atados",
                       "$/kilo"])
    assert profile_years.measure_unit_shares(units) == {
        "kilo": 0.5, "unidad": 0.25, profile_years.NOT_CONVERTIBLE: 0.25}


def test_t27_profile_finds_a_missing_week_and_an_unknown_channel():
    raw_rows = pd.concat([make_raw_consumer_rows(),
                          make_raw_consumer_rows(week_start="2026-01-19",
                                                 week_end="2026-01-23",
                                                 sales_channel="Kiosko")],
                         ignore_index=True)
    profile = profile_years.profile_year(raw_rows, etl.SOURCE_CONSUMER)
    assert profile["rows_read"] == 2
    assert profile["missing_weeks"] == ["2026-01-12"]
    assert profile["unknown_channels"] == ["Kiosko"]


def test_t27_profile_counts_rejected_rows_and_keeps_valid_keys():
    raw_rows = pd.concat([make_raw_wholesale_rows(),
                          make_raw_wholesale_rows(avg_price="0,0000")], ignore_index=True)
    profile = profile_years.profile_year(raw_rows, etl.SOURCE_WHOLESALE)
    assert profile["rejections"] == {etl.REASON_NON_POSITIVE_PRICE: 1}
    assert profile["product_keys"] == {("Hortalizas", "Tomate", "Larga vida", "Primera")}
