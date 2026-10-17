"""Tests for the whole ETL run: raw tables in, indicator database out."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl  # noqa: E402
from tests.test_etl import make_raw_consumer_rows, make_raw_wholesale_rows  # noqa: E402


# region Helpers
def open_test_databases(tmp_path):
    raw_connection = etl.open_database(tmp_path / "raw.db")
    connection = etl.open_database(tmp_path / "datos.db", etl.SCHEMA_FILE)
    return raw_connection, connection


def replace_raw_rows(raw_connection, source, raw_row_frames):
    """Replace the content of one raw table by the given sample rows."""
    table = etl.RAW_TABLE_BY_SOURCE[source]
    with raw_connection:
        raw_connection.execute(f"DELETE FROM {table}")
        etl.insert_rows(raw_connection, table, pd.concat(raw_row_frames, ignore_index=True))


def fill_sample_raw_tables(raw_connection):
    """Two wholesale rows and two consumer rows of the same product and week."""
    replace_raw_rows(raw_connection, etl.SOURCE_WHOLESALE, [
        make_raw_wholesale_rows(price_date="2026-01-06"),
        make_raw_wholesale_rows(price_date="2026-01-08")])
    replace_raw_rows(raw_connection, etl.SOURCE_CONSUMER, [
        make_raw_consumer_rows(),
        make_raw_consumer_rows(sales_channel="Supermercado")])


def read_table(connection, table):
    return pd.read_sql(f"SELECT * FROM {table}", connection)
# endregion


# region Load
def test_run_loads_weekly_prices_dimensions_and_the_run_record(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    fill_sample_raw_tables(raw_connection)
    row_counts = etl.run_etl(raw_connection, connection)
    assert row_counts["rows_read"] == 4
    # One wholesale week, plus one consumer week per channel.
    assert len(read_table(connection, "weekly_price")) == 3
    assert len(read_table(connection, "dim_product")) == 1
    assert len(read_table(connection, "dim_region")) == 1
    assert set(read_table(connection, "dim_channel")["channel"]) == {
        etl.WHOLESALE_CHANNEL, "Feria libre", "Supermercado"}
    assert list(read_table(connection, "etl_run")["status"]) == [etl.STATUS_LOADED]
    # D-095: every load rebuilds dim_date, and each price week is in it.
    weeks = set(read_table(connection, "dim_date")["week_start"])
    assert set(read_table(connection, "weekly_price")["week_start"]) <= weeks


def test_rn11_rows_read_equal_rows_loaded_plus_rows_rejected(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    fill_sample_raw_tables(raw_connection)
    replace_raw_rows(raw_connection, etl.SOURCE_CONSUMER, [
        make_raw_consumer_rows(), make_raw_consumer_rows(avg_price="0")])
    row_counts = etl.run_etl(raw_connection, connection)
    assert row_counts["rows_read"] == (
        row_counts["rows_loaded"] + row_counts["rows_rejected"])
    # Every loaded row is counted in exactly one weekly price.
    observation_total = read_table(connection, "weekly_price")["observation_count"].sum()
    assert observation_total == row_counts["rows_loaded"]
    rejections = read_table(connection, "rejection")
    assert list(rejections["reason"]) == [etl.REASON_NON_POSITIVE_PRICE]


def test_rn14_running_twice_leaves_the_same_rows(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    fill_sample_raw_tables(raw_connection)
    etl.run_etl(raw_connection, connection)
    tables = ["weekly_price", "dim_product", "dim_region", "dim_channel"]
    first_run_tables = [read_table(connection, table) for table in tables]
    etl.run_etl(raw_connection, connection)
    for table, first_run_table in zip(tables, first_run_tables):
        pd.testing.assert_frame_equal(read_table(connection, table), first_run_table)
    # The run log is the only table that grows: one line per run.
    assert len(read_table(connection, "etl_run")) == 2
# endregion


# region Indicators
def test_k7_counts_consumer_keys_that_have_a_margin(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    fill_sample_raw_tables(raw_connection)
    # A second consumer key (another quality) that the wholesale source lacks.
    replace_raw_rows(raw_connection, etl.SOURCE_CONSUMER, [
        make_raw_consumer_rows(),
        make_raw_consumer_rows(product="Tomate|Larga vida|Segunda")])
    etl.run_etl(raw_connection, connection)
    assert etl.measure_match_coverage(connection) == (1, 2)


def test_rn06_no_margin_when_wholesale_and_consumer_units_differ(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    fill_sample_raw_tables(raw_connection)
    # Wholesale is in kilos (box of 18 kilos); the consumer sells by unit.
    replace_raw_rows(raw_connection, etl.SOURCE_CONSUMER, [
        make_raw_consumer_rows(unit="$/unidad")])
    etl.run_etl(raw_connection, connection)
    assert etl.measure_match_coverage(connection) == (0, 1)
# endregion


# region Quality checks
def fill_two_weeks_of_wholesale_rows(raw_connection, row_count_per_week):
    first_week = [make_raw_wholesale_rows(price_date="2026-01-06")] * row_count_per_week
    second_week = [make_raw_wholesale_rows(price_date="2026-01-13")] * row_count_per_week
    replace_raw_rows(raw_connection, etl.SOURCE_WHOLESALE, first_week + second_week)


def test_file_with_half_the_rows_stops_the_load_with_a_clear_message(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    fill_two_weeks_of_wholesale_rows(raw_connection, row_count_per_week=10)
    etl.run_etl(raw_connection, connection)
    weekly_prices_before = read_table(connection, "weekly_price")

    fill_two_weeks_of_wholesale_rows(raw_connection, row_count_per_week=5)
    row_counts = etl.run_etl(raw_connection, connection)

    assert row_counts["status"] == etl.STATUS_FAILED
    assert row_counts["message"] == (
        "TOO_FEW_ROWS: read 10 rows, the previous successful run read 20")
    pd.testing.assert_frame_equal(read_table(connection, "weekly_price"),
                                  weekly_prices_before)
    assert list(read_table(connection, "etl_run")["status"]) == [
        etl.STATUS_LOADED, etl.STATUS_FAILED]


def test_week_without_data_between_two_weeks_stops_the_load(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    replace_raw_rows(raw_connection, etl.SOURCE_WHOLESALE, [
        make_raw_wholesale_rows(price_date="2026-01-06"),
        make_raw_wholesale_rows(price_date="2026-01-20")])
    row_counts = etl.run_etl(raw_connection, connection)
    assert row_counts["status"] == etl.STATUS_FAILED
    assert row_counts["message"] == "MISSING_WEEKS: wholesale has no data for 2026-01-12"
    assert read_table(connection, "weekly_price").empty


def test_t28_known_source_gap_does_not_stop_the_load_but_other_gaps_do():
    weeks = pd.to_datetime(["2022-04-25", "2022-05-09", "2022-05-23"])
    assert etl.find_unexpected_missing_weeks(pd.Series(weeks), etl.SOURCE_CONSUMER) == [
        "2022-05-16"]
    # The same gap in the other source was never confirmed, so it still counts.
    assert etl.find_unexpected_missing_weeks(pd.Series(weeks), etl.SOURCE_WHOLESALE) == [
        "2022-05-02", "2022-05-16"]


def test_rn14_duplicate_weekly_price_key_stops_the_load():
    weekly_prices = etl.aggregate_weekly(etl.normalize_units(etl.clean(
        make_raw_consumer_rows(), etl.SOURCE_CONSUMER)))
    duplicated_prices = pd.concat([weekly_prices, weekly_prices], ignore_index=True)
    assert etl.check_quality(weekly_prices, 1, None) == []
    assert etl.check_quality(duplicated_prices, 1, None) == [
        "DUPLICATE_KEYS: 1 weekly prices share their key with another one"]


def test_unknown_region_and_channel_stop_the_load(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    replace_raw_rows(raw_connection, etl.SOURCE_CONSUMER, [
        make_raw_consumer_rows(region_id="99", sales_channel="Canal nuevo")])
    row_counts = etl.run_etl(raw_connection, connection)
    assert row_counts["status"] == etl.STATUS_FAILED
    assert "UNKNOWN_REGION: [99]" in row_counts["message"]
    assert "UNKNOWN_CHANNEL: ['Canal nuevo']" in row_counts["message"]
# endregion
