"""Tests for bi/queries.sql (K1 to K4, K8). The SQL K5 and K6: test_reconciliation."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import queries  # noqa: E402
from etl import etl  # noqa: E402
from tests.test_etl import make_raw_consumer_rows, make_raw_wholesale_rows  # noqa: E402
from tests.test_etl_run import open_test_databases, replace_raw_rows  # noqa: E402

VALPARAISO = {"region_id": "5", "region": "Región de Valparaíso"}


@pytest.fixture
def database_file(tmp_path):
    """Indicator database built by the ETL from a few hand-made rows.

    Wholesale tomato: 9000 per box of 18 kilos = 500 per kilo, in two weeks.
    Consumer tomato in the RM, week 1: street market 1000, supermarket 1500.
    Consumer tomato in Valparaíso, week 1: street market 1500.
    Consumer tomato in the RM, week 2: street market 3000.
    """
    raw_connection, connection = open_test_databases(tmp_path)
    replace_raw_rows(raw_connection, etl.SOURCE_WHOLESALE, [
        make_raw_wholesale_rows(price_date="2026-01-06", avg_price="9000,0000"),
        make_raw_wholesale_rows(price_date="2026-01-13", avg_price="9000,0000")])
    replace_raw_rows(raw_connection, etl.SOURCE_CONSUMER, [
        make_raw_consumer_rows(avg_price="1000,000000", max_price="4000"),
        make_raw_consumer_rows(avg_price="1500,000000", max_price="4000",
                               sales_channel="Supermercado"),
        make_raw_consumer_rows(avg_price="1500,000000", max_price="4000", **VALPARAISO),
        make_raw_consumer_rows(avg_price="3000,000000", max_price="4000",
                               week_start="2026-01-12", week_end="2026-01-16")])
    etl.run_etl(raw_connection, connection)
    connection.close()
    return tmp_path / "datos.db"


def select_rows(rows, **conditions):
    for column, value in conditions.items():
        rows = rows[rows[column] == value]
    return rows


def test_queries_file_has_one_named_query_per_indicator():
    assert set(queries.load_queries()) == {
        "k1_margin", "k2_channel_gap", "k3_regional_index", "k4_seasonal_index",
        "k6_national_weekly_price", "k8_rejected_rows", "quality_runs",
        "quality_flag_counts", "quality_outliers", "k6_usual_range_sql",
        "k5_weekly_variations_sql", "quality_week_range", "quality_rejected_rows",
        "quality_unconvertible_units"}


def test_k1_margin_is_consumer_minus_wholesale_over_wholesale(database_file):
    margins = queries.run_query("k1_margin", database_file)
    first_week = select_rows(margins, week_start="2026-01-05",
                             region="Región Metropolitana de Santiago")
    margin_by_channel = dict(zip(first_week["channel"], first_week["margin"]))
    # (1000 - 500) / 500 = 1 and (1500 - 500) / 500 = 2.
    assert margin_by_channel == {"Feria libre": 1.0, "Supermercado": 2.0}


def test_rn06_k1_has_no_margin_without_wholesale_price_in_the_region(database_file):
    margins = queries.run_query("k1_margin", database_file)
    assert select_rows(margins, region="Región de Valparaíso").empty


def test_k2_channel_gap_is_price_over_reference_price_minus_one(database_file):
    gaps = queries.run_query("k2_channel_gap", database_file)
    gap = select_rows(gaps, channel="Supermercado", reference_channel="Feria libre")
    assert list(gap["gap"]) == [0.5]  # 1500 / 1000 - 1


def test_k3_regional_index_is_region_price_over_national_average(database_file):
    indexes = queries.run_query("k3_regional_index", database_file)
    street_market = select_rows(indexes, channel="Feria libre", week_start="2026-01-05")
    index_by_region = dict(zip(street_market["region"], street_market["regional_index"]))
    # National average of 1000 and 1500 is 1250.
    assert index_by_region == {"Región Metropolitana de Santiago": 0.8,
                               "Región de Valparaíso": 1.2}


def test_k4_seasonal_index_is_week_price_over_year_average(database_file):
    indexes = queries.run_query("k4_seasonal_index", database_file)
    street_market = select_rows(indexes, channel="Feria libre")
    index_by_week = dict(zip(street_market["week_start"], street_market["seasonal_index"]))
    # Week 1 national price: (1000 + 1500) / 2 = 1250. Week 2: 3000. Year: 2125.
    assert index_by_week == {"2026-01-05": pytest.approx(1250 / 2125),
                             "2026-01-12": pytest.approx(3000 / 2125)}


def test_k4_week_starting_in_december_belongs_to_the_next_year(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    replace_raw_rows(raw_connection, etl.SOURCE_CONSUMER, [
        make_raw_consumer_rows(week_start="2025-12-29", week_end="2026-01-02")])
    etl.run_etl(raw_connection, connection)
    connection.close()
    indexes = queries.run_query("k4_seasonal_index", tmp_path / "datos.db")
    assert list(indexes["price_year"]) == ["2026"]


def test_k8_rejected_rows_are_counted_by_reason_over_rows_read(tmp_path):
    raw_connection, connection = open_test_databases(tmp_path)
    replace_raw_rows(raw_connection, etl.SOURCE_CONSUMER, [
        make_raw_consumer_rows(), make_raw_consumer_rows(), make_raw_consumer_rows(),
        make_raw_consumer_rows(avg_price="0")])
    etl.run_etl(raw_connection, connection)
    connection.close()
    rejections = queries.run_query("k8_rejected_rows", tmp_path / "datos.db")
    assert rejections.to_dict("records") == [{
        "source": etl.SOURCE_CONSUMER, "reason": etl.REASON_NON_POSITIVE_PRICE,
        "rejected_rows": 1, "rejected_share": 0.25}]


def test_d050_rows_of_one_product_key_are_filtered_by_sqlite(database_file):
    key = {"product_group": "Hortalizas", "product": "Tomate", "variety": "Larga vida",
           "quality": "Primera", "normalized_unit": "kilo"}
    rows = queries.run_query_for_key("k1_margin", key, database_file)
    assert len(rows) == len(queries.run_query("k1_margin", database_file))
    other_key = dict(key, variety="Cherry")
    assert queries.run_query_for_key("k1_margin", other_key, database_file).empty


def test_d050_key_options_count_the_rows_of_each_key(database_file):
    options = queries.list_query_keys("k1_margin", database_file)
    assert options[queries.KEY_COLUMNS].to_dict("records") == [
        {"product_group": "Hortalizas", "product": "Tomate", "variety": "Larga vida",
         "quality": "Primera", "normalized_unit": "kilo"}]
    assert options["row_count"].iloc[0] == len(queries.run_query("k1_margin", database_file))


def test_week_range_gives_the_years_really_loaded(database_file):
    week_range = queries.run_query("quality_week_range", database_file).iloc[0]
    assert (week_range["first_week"], week_range["last_week"]) == ("2026-01-05", "2026-01-12")
    assert (week_range["first_year"], week_range["last_year"]) == ("2026", "2026")


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="the served database is not here")
@pytest.mark.parametrize("query_name", sorted(queries.load_queries()))
def test_every_named_query_runs_read_only_on_the_served_database(query_name):
    # D-244: every named query the panel uses still runs on the database it reads.
    rows = queries.run_sql(f"SELECT * FROM ({queries.read_query_body(query_name)}) LIMIT 20")
    assert list(rows.columns)


def test_every_github_link_of_the_panel_points_to_a_file_in_the_repository():
    # D-244: a literal path given to build_github_url must exist, so no link of the panel is broken.
    root = Path(__file__).resolve().parent.parent
    paths = set()
    for source in (root / "bi").glob("*.py"):
        paths |= set(re.findall(r'build_github_url\(\s*"([^"{}]+)"', source.read_text(encoding="utf-8")))
    assert paths
    for path in paths:
        assert (root / path).exists(), path
    for name in ("PRD.md", "SAD.md", "ADR.md", "SEGURIDAD.md", "DECISIONES.md"):
        assert (root / "docs" / name).exists(), name
