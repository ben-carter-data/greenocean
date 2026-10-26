"""Tests for the ETL business rules. Each test names the rule (RN) it covers."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl  # noqa: E402

NON_BREAKING_SPACE = chr(160)


# region Sample rows
def make_raw_wholesale_rows(**changes):
    """One valid raw wholesale row (all text, as stored in raw_wholesale)."""
    row = {
        "file_year": 2026, "file_hash": "hash", "price_date": "2026-01-06",
        "region_id": "13", "region": "Región Metropolitana de Santiago",
        "market": "Lo Valledor", "subsector": "Hortalizas y tubérculos",
        "product": "Tomate", "variety": "Larga vida", "quality": "Primera",
        "sale_unit": "$/caja 18 kilos", "origin": "RM", "volume": "100",
        "min_price": "9000,0000", "max_price": "10000,0000", "avg_price": "9500,5000",
    }
    row.update(changes)
    return pd.DataFrame([row])


def make_raw_consumer_rows(**changes):
    """One valid raw consumer row (all text, as stored in raw_consumer)."""
    row = {
        "file_year": 2026, "file_hash": "hash", "year": "2026", "month": "1",
        "week": "2", "week_start": "2026-01-05", "week_end": "2026-01-09",
        "region_id": "13", "region": "Región Metropolitana de Santiago",
        "sector": "Santiago", "sales_channel": "Feria libre",
        "product_group": "Hortalizas", "product": "Tomate|Larga vida|Primera",
        "unit": "$/kilo", "min_price": "900", "max_price": "1100",
        "avg_price": "1000,500000",
    }
    row.update(changes)
    return pd.DataFrame([row])
# endregion


# region Clean
def test_rn01_decimal_comma_text_becomes_number():
    numbers = etl.convert_decimal_text(pd.Series(["9500,5000", "1000", "sin dato"]))
    assert numbers[0] == 9500.5
    assert numbers[1] == 1000
    assert pd.isna(numbers[2])


def test_rn01_clean_converts_the_three_prices():
    clean_row = etl.clean(make_raw_wholesale_rows(), etl.SOURCE_WHOLESALE).iloc[0]
    assert (clean_row["min_price"], clean_row["max_price"], clean_row["avg_price"]) == (
        9000, 10000, 9500.5)


def test_rn02_product_with_separator_is_split_in_three():
    assert etl.split_consumer_product("Tomate|Larga vida|Primera") == (
        "Tomate", "Larga vida", "Primera")


def test_rn02_product_without_separator_has_unspecified_variety_and_quality():
    assert etl.split_consumer_product("Pan Marraqueta") == (
        "Pan Marraqueta", etl.UNSPECIFIED, etl.UNSPECIFIED)


def test_rn02_clean_splits_the_consumer_product():
    clean_row = etl.clean(make_raw_consumer_rows(), etl.SOURCE_CONSUMER).iloc[0]
    assert (clean_row["product"], clean_row["variety"], clean_row["quality"]) == (
        "Tomate", "Larga vida", "Primera")


def test_rn13_repeated_and_non_breaking_spaces_are_removed():
    messy_text = " Pavo  Pechuga" + NON_BREAKING_SPACE + "s/hueso "
    assert etl.normalize_text(messy_text) == "Pavo Pechuga s/hueso"


def test_rn13_letter_case_is_not_changed():
    assert etl.normalize_text("PALTA Hass") == "PALTA Hass"


def test_both_sources_share_the_same_product_key():
    wholesale_row = etl.clean(make_raw_wholesale_rows(), etl.SOURCE_WHOLESALE).iloc[0]
    consumer_row = etl.clean(make_raw_consumer_rows(), etl.SOURCE_CONSUMER).iloc[0]
    key_columns = ["product_group", "product", "variety", "quality", "region_id"]
    assert list(wholesale_row[key_columns]) == list(consumer_row[key_columns])
# endregion


# region Validation
def get_rejection_reason(raw_rows, source):
    return etl.validate_rows(etl.clean(raw_rows, source)).iloc[0]


def test_rn11_valid_rows_have_no_rejection_reason():
    assert get_rejection_reason(make_raw_wholesale_rows(), etl.SOURCE_WHOLESALE) == ""
    assert get_rejection_reason(make_raw_consumer_rows(), etl.SOURCE_CONSUMER) == ""


def test_rn11_price_zero_or_negative_is_rejected():
    for price in ["0", "-5,0000"]:
        raw_rows = make_raw_wholesale_rows(min_price=price)
        assert get_rejection_reason(raw_rows, etl.SOURCE_WHOLESALE) == (
            etl.REASON_NON_POSITIVE_PRICE)


def test_rn11_minimum_above_maximum_is_rejected():
    raw_rows = make_raw_consumer_rows(min_price="1200", max_price="1100")
    assert get_rejection_reason(raw_rows, etl.SOURCE_CONSUMER) == (
        etl.REASON_MINIMUM_ABOVE_MAXIMUM)


def test_rn11_date_outside_the_file_year_is_rejected():
    raw_rows = make_raw_wholesale_rows(price_date="2025-06-03")
    assert get_rejection_reason(raw_rows, etl.SOURCE_WHOLESALE) == (
        etl.REASON_DATE_OUTSIDE_FILE_YEAR)


def test_rn11_first_consumer_week_starting_in_december_is_accepted():
    raw_rows = make_raw_consumer_rows(week_start="2025-12-29", week_end="2026-01-02")
    assert get_rejection_reason(raw_rows, etl.SOURCE_CONSUMER) == ""


def test_rn11_unreadable_price_or_date_is_rejected():
    for changes in [{"avg_price": "sin dato"}, {"price_date": "no es fecha"}]:
        raw_rows = make_raw_wholesale_rows(**changes)
        assert get_rejection_reason(raw_rows, etl.SOURCE_WHOLESALE) == (
            etl.REASON_UNREADABLE_VALUE)


def test_rn11_wholesale_row_without_volume_is_rejected():
    raw_rows = make_raw_wholesale_rows(volume="0")
    assert get_rejection_reason(raw_rows, etl.SOURCE_WHOLESALE) == (
        etl.REASON_NON_POSITIVE_VOLUME)


def test_rn11_rows_read_equal_valid_plus_rejected_and_keep_the_original_row():
    raw_rows = pd.concat([make_raw_wholesale_rows(),
                          make_raw_wholesale_rows(min_price="0"),
                          make_raw_wholesale_rows(price_date="2025-06-03")],
                         ignore_index=True)
    reasons = etl.validate_rows(etl.clean(raw_rows, etl.SOURCE_WHOLESALE))
    rejections = etl.build_rejections(raw_rows, reasons, etl.SOURCE_WHOLESALE)
    assert len(raw_rows) == (reasons == "").sum() + len(rejections)
    assert list(rejections["reason"]) == [etl.REASON_NON_POSITIVE_PRICE,
                                          etl.REASON_DATE_OUTSIDE_FILE_YEAR]
    assert '"min_price": "0"' in rejections["original_row"][0]
# endregion


# region Units
def load_expected_unit_conversions():
    """The 147 wholesale units of the 2026 file with their reviewed conversion."""
    table_file = Path(__file__).resolve().parent / "fixtures" / "wholesale_units_2026.csv"
    return pd.read_csv(table_file, dtype=str, keep_default_na=False)


def test_rn03_unit_that_declares_kilos_is_divided_by_them():
    assert etl.convert_unit("$/caja 25 kilos") == (etl.UNIT_KILO, 25)
    assert etl.convert_unit("$/bins (400 kilos)") == (etl.UNIT_KILO, 400)
    assert etl.convert_unit("$/kilo") == (etl.UNIT_KILO, 1)
    assert etl.convert_unit("$/kilo (en caja de 17 kilos)") == (etl.UNIT_KILO, 1)


def test_rn04_unit_that_declares_units_is_divided_by_them():
    assert etl.convert_unit("$/caja 15 unidades") == (etl.UNIT_EACH, 15)
    assert etl.convert_unit("$/unidad") == (etl.UNIT_EACH, 1)
    assert etl.convert_unit("$/paquete 20 unidades (volumen en unidades)") == (
        etl.UNIT_EACH, 20)


def test_rn05_unit_with_range_or_without_quantity_is_not_convertible():
    for unit in ["$/atado 1,5 a 2 kilos", "$/docena de atados", "$/caja 36 atados",
                 "$/atado 300 a 500 gramos", "$/bandeja 12 canastillos 125 gramos"]:
        assert etl.convert_unit(unit) == (None, None)


def test_rn03_grams_become_kilos_and_milliliters_become_liters():
    assert etl.convert_unit("$/bolsa 800 grs") == (etl.UNIT_KILO, 0.8)
    assert etl.convert_unit("$/pote 500 gramos") == (etl.UNIT_KILO, 0.5)
    assert etl.convert_unit("$/botella 900 ml") == (etl.UNIT_LITER, 0.9)
    assert etl.convert_unit("$/Caja de 1 Litro") == (etl.UNIT_LITER, 1)
    assert etl.convert_unit("$/litro") == (etl.UNIT_LITER, 1)


def test_rn03_rn04_rn05_the_147_units_of_2026_convert_as_reviewed():
    expected_conversions = load_expected_unit_conversions()
    assert len(expected_conversions) == 147
    for expected in expected_conversions.to_dict("records"):
        normalized_unit, quantity = etl.convert_unit(expected["unit"])
        assert (normalized_unit or "") == expected["expected_unit"], expected["unit"]
        if expected["expected_quantity"]:
            assert quantity == float(expected["expected_quantity"]), expected["unit"]


def test_rn03_normalized_price_is_price_divided_by_kilos():
    clean_rows = etl.clean(make_raw_wholesale_rows(avg_price="9000,0000"),
                           etl.SOURCE_WHOLESALE)
    normalized_row = etl.normalize_units(clean_rows).iloc[0]
    assert normalized_row["normalized_unit"] == etl.UNIT_KILO
    assert normalized_row["normalized_price"] == 500  # 9000 / 18 kilos


def test_rn05_not_convertible_row_is_kept_without_normalized_price():
    clean_rows = etl.clean(make_raw_wholesale_rows(sale_unit="$/docena de atados"),
                           etl.SOURCE_WHOLESALE)
    normalized_rows = etl.normalize_units(clean_rows)
    assert len(normalized_rows) == 1
    assert pd.isna(normalized_rows.iloc[0]["normalized_price"])
    assert pd.isna(normalized_rows.iloc[0]["normalized_unit"])
# endregion


# region Weekly aggregation
def build_weekly_prices(raw_wholesale_rows=None, raw_consumer_rows=None):
    """Run clean and the business rules over the given raw rows."""
    clean_parts = []
    if raw_wholesale_rows is not None:
        clean_parts.append(etl.clean(raw_wholesale_rows, etl.SOURCE_WHOLESALE))
    if raw_consumer_rows is not None:
        clean_parts.append(etl.clean(raw_consumer_rows, etl.SOURCE_CONSUMER))
    return etl.apply_business_rules(pd.concat(clean_parts, ignore_index=True))


def test_rn07_weekly_wholesale_price_is_weighted_by_volume():
    # Tuesday: 100 boxes at 9000 (500 per kilo). Thursday: 300 boxes at 12600 (700).
    raw_rows = pd.concat([
        make_raw_wholesale_rows(price_date="2026-01-06", volume="100",
                                avg_price="9000,0000", max_price="13000,0000"),
        make_raw_wholesale_rows(price_date="2026-01-08", volume="300",
                                avg_price="12600,0000", max_price="13000,0000")],
        ignore_index=True)
    weekly_prices = build_weekly_prices(raw_wholesale_rows=raw_rows)
    assert len(weekly_prices) == 1
    # (500 * 100 + 700 * 300) / 400 = 650, not the plain average 600.
    assert weekly_prices.iloc[0]["price"] == pytest.approx(650)
    assert weekly_prices.iloc[0]["volume"] == 400
    assert weekly_prices.iloc[0]["observation_count"] == 2


def test_rn08_wholesale_date_is_assigned_to_the_monday_of_the_consumer_week():
    # 2026-01-08 is a Thursday; its week starts on Monday 2026-01-05.
    weekly_prices = build_weekly_prices(
        raw_wholesale_rows=make_raw_wholesale_rows(price_date="2026-01-08"),
        raw_consumer_rows=make_raw_consumer_rows(week_start="2026-01-05"))
    assert list(weekly_prices["week_start"].dt.strftime("%Y-%m-%d")) == [
        "2026-01-05", "2026-01-05"]


def test_rn09_weekly_consumer_price_is_the_average_by_region_and_channel():
    raw_rows = pd.concat([
        make_raw_consumer_rows(sector="Santiago", avg_price="1000,000000"),
        make_raw_consumer_rows(sector="Maipú", avg_price="1100,000000"),
        make_raw_consumer_rows(sales_channel="Supermercado", avg_price="1500,000000",
                               max_price="1600")],
        ignore_index=True)
    weekly_prices = build_weekly_prices(raw_consumer_rows=raw_rows)
    price_by_channel = dict(zip(weekly_prices["channel"], weekly_prices["price"]))
    assert price_by_channel == {"Feria libre": 1050, "Supermercado": 1500}


def test_rn10_consumer_wholesale_market_is_a_channel_of_the_consumer_source():
    weekly_prices = build_weekly_prices(
        raw_wholesale_rows=make_raw_wholesale_rows(),
        raw_consumer_rows=make_raw_consumer_rows(sales_channel="Mercado Mayorista"))
    channels = set(zip(weekly_prices["source"], weekly_prices["channel"]))
    assert channels == {(etl.SOURCE_WHOLESALE, etl.WHOLESALE_CHANNEL),
                        (etl.SOURCE_CONSUMER, "Mercado Mayorista")}


def test_rn05_not_convertible_week_is_kept_with_its_reason_and_no_price():
    weekly_prices = build_weekly_prices(
        raw_wholesale_rows=make_raw_wholesale_rows(sale_unit="$/docena de atados"))
    assert len(weekly_prices) == 1
    assert weekly_prices.iloc[0]["flag"] == etl.FLAG_UNIT_NOT_CONVERTIBLE
    assert pd.isna(weekly_prices.iloc[0]["price"])


def test_rn06_kilo_and_unit_prices_of_one_product_stay_in_separate_rows():
    raw_rows = pd.concat([make_raw_wholesale_rows(sale_unit="$/caja 18 kilos"),
                          make_raw_wholesale_rows(sale_unit="$/caja 15 unidades")],
                         ignore_index=True)
    weekly_prices = build_weekly_prices(raw_wholesale_rows=raw_rows)
    assert set(weekly_prices["normalized_unit"]) == {etl.UNIT_KILO, etl.UNIT_EACH}
# endregion


# region Outliers
def make_weekly_prices(prices):
    """Weekly prices of one product in one week, one row per price."""
    return pd.DataFrame({
        "week_start": pd.Timestamp("2026-01-05"), "source": etl.SOURCE_CONSUMER,
        "product_group": "Hortalizas", "product": "Tomate",
        "normalized_unit": etl.UNIT_KILO, "price": prices, "flag": None})


def test_rn12_price_above_five_times_the_median_is_flagged_and_kept():
    # Median 1050, upper limit 5250.
    weekly_prices = etl.flag_outliers(make_weekly_prices([900, 1000, 1100, 5300]))
    assert len(weekly_prices) == 4
    assert list(weekly_prices["flag"]) == [None, None, None, etl.FLAG_OUTLIER]


def test_rn12_price_below_one_fifth_of_the_median_is_flagged():
    # Median 950, lower limit 190.
    weekly_prices = etl.flag_outliers(make_weekly_prices([900, 1000, 1100, 180]))
    assert list(weekly_prices["flag"]) == [None, None, None, etl.FLAG_OUTLIER]


def test_rn12_price_exactly_at_the_limit_is_not_flagged():
    # Median of 1000, 1000 and 5000 is 1000; 5000 is 5 times, not more than 5 times.
    weekly_prices = etl.flag_outliers(make_weekly_prices([1000, 1000, 5000]))
    assert list(weekly_prices["flag"]) == [None, None, None]


def test_rn12_wholesale_and_consumer_prices_are_not_compared_with_each_other():
    # Retail at 6 times the wholesale price is a margin, not an outlier.
    weekly_prices = make_weekly_prices([1000, 1000, 1000, 6000, 6000])
    weekly_prices["source"] = [etl.SOURCE_WHOLESALE] * 3 + [etl.SOURCE_CONSUMER] * 2
    assert list(etl.flag_outliers(weekly_prices)["flag"]) == [None] * 5
# endregion
