"""Tests for the query builder of the Consultas page (T-42)."""
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import explorer  # noqa: E402
from etl import etl  # noqa: E402


# region Sample data
def make_price_rows():
    """Four weekly prices: two weeks of March, one of April, two channels."""
    return pd.DataFrame({
        "week_start": pd.to_datetime(["2026-03-02", "2026-03-09", "2026-04-06",
                                      "2026-03-02"]),
        "product": ["Tomate", "Tomate", "Tomate", "Tomate"],
        "region": ["Región de Valparaíso"] * 4,
        "channel": ["Feria libre", "Feria libre", "Feria libre", "Supermercado"],
        "normalized_unit": ["kilo"] * 4,
        "value": [1000.0, 1200.0, 900.0, 2000.0],
    })


def build_sample_database(database_file):
    """A small datos.db with two weekly prices and one flagged outlier."""
    connection = etl.open_database(database_file, etl.SCHEMA_FILE)
    with connection:
        connection.execute("INSERT INTO dim_product VALUES (1, 'Hortalizas', 'Tomate', "
                           "'Larga vida', 'Primera')")
        connection.execute("INSERT INTO dim_region VALUES (5, 'Región de Valparaíso')")
        connection.execute("INSERT INTO dim_channel VALUES (1, 'Feria libre', 'consumer')")
        connection.executemany(
            "INSERT INTO weekly_price VALUES (?, 1, 5, 1, 'kilo', ?, NULL, 1, ?)",
            [("2026-03-02", 1000.0, None), ("2026-03-09", 1200.0, None),
             ("2026-03-16", 9.0, etl.FLAG_OUTLIER)])
    connection.close()
# endregion


# region Allowlist
def test_unknown_view_grouping_measure_or_filter_is_rejected():
    with pytest.raises(ValueError):
        explorer.validate_choices("Clientes", [], "Promedio", {})
    with pytest.raises(ValueError):
        explorer.validate_choices(explorer.VIEW_PRICES, ["product; DROP TABLE"],
                                  "Promedio", {})
    with pytest.raises(ValueError):
        explorer.validate_choices(explorer.VIEW_PRICES, [], "SUM", {})
    with pytest.raises(ValueError):
        explorer.validate_choices(explorer.VIEW_PRICES, [], "Promedio", {"price": [1]})


def test_alerts_have_no_region_because_they_are_national():
    with pytest.raises(ValueError):
        explorer.validate_choices(explorer.VIEW_ALERTS, [explorer.GROUP_REGION],
                                  "Promedio", {})


def test_week_and_month_cannot_be_grouped_together():
    with pytest.raises(ValueError):
        explorer.validate_choices(explorer.VIEW_MARGINS,
                                  [explorer.GROUP_WEEK, explorer.GROUP_MONTH],
                                  "Promedio", {})


def test_prices_are_always_grouped_by_unit():
    assert explorer.list_group_columns(explorer.VIEW_PRICES, [explorer.GROUP_PRODUCT]) == [
        "product", explorer.UNIT_COLUMN]
    assert explorer.list_group_columns(explorer.VIEW_MARGINS, [explorer.GROUP_PRODUCT]) == [
        "product"]
# endregion


# region SQL parameters
def test_chosen_values_travel_as_parameters_never_inside_the_sql():
    dangerous_value = "Tomate'); DROP TABLE weekly_price; --"
    sql, parameters = explorer.build_price_query({
        explorer.FILTER_PRODUCTS: [dangerous_value, "Palta"],
        explorer.FILTER_FIRST_WEEK: date(2026, 3, 1)})
    assert dangerous_value not in sql
    assert "dim_product.product IN (?, ?)" in sql
    assert "weekly_price.week_start >= ?" in sql
    assert parameters == [dangerous_value, "Palta", "2026-03-01"]


def test_price_rows_leave_flagged_prices_out_and_apply_date_filters(tmp_path):
    database_file = tmp_path / "datos.db"
    build_sample_database(database_file)
    rows = explorer.read_price_rows({explorer.FILTER_FIRST_WEEK: date(2026, 3, 9)},
                                    database_file)
    assert rows["value"].to_list() == [1200.0]


def test_price_options_come_from_the_database(tmp_path):
    database_file = tmp_path / "datos.db"
    build_sample_database(database_file)
    options = explorer.read_price_options(database_file)
    assert options[explorer.FILTER_PRODUCTS] == ["Tomate"]
    assert options[explorer.FILTER_FIRST_WEEK] == date(2026, 3, 2)
    assert options[explorer.FILTER_LAST_WEEK] == date(2026, 3, 16)
# endregion


# region Filters, grouping and measure
def test_filters_by_list_and_by_date_range():
    rows = explorer.filter_rows(make_price_rows(), {
        explorer.FILTER_CHANNELS: ["Feria libre"],
        explorer.FILTER_FIRST_WEEK: date(2026, 3, 9),
        explorer.FILTER_LAST_WEEK: date(2026, 4, 30)})
    assert rows["value"].to_list() == [1200.0, 900.0]


def test_grouping_by_month_uses_the_monday_of_each_week():
    result = explorer.build_result(explorer.VIEW_PRICES, make_price_rows(),
                                   [explorer.GROUP_CHANNEL, explorer.GROUP_MONTH],
                                   "Promedio", {})
    feria = result[result["channel"] == "Feria libre"]
    assert feria["month"].to_list() == ["2026-03", "2026-04"]
    assert feria["value"].to_list() == [1100.0, 900.0]
    assert feria[explorer.COUNT_COLUMN].to_list() == [2, 1]


def test_each_measure_summarizes_the_group():
    rows = make_price_rows()
    measured = {measure: explorer.build_result(explorer.VIEW_PRICES, rows, [], measure,
                                               {})["value"].iloc[0]
                for measure in explorer.MEASURES}
    assert measured == {"Promedio": 1275.0, "Mediana": 1100.0, "Mínimo": 900.0,
                        "Máximo": 2000.0}


def test_a_combination_without_rows_gives_an_empty_result():
    result = explorer.build_result(explorer.VIEW_PRICES, make_price_rows(),
                                   [explorer.GROUP_PRODUCT], "Promedio",
                                   {explorer.FILTER_PRODUCTS: ["Papaya"]})
    assert result.empty


def test_at_most_one_thousand_rows_are_shown():
    result = pd.DataFrame({"value": range(1500)})
    shown, is_truncated = explorer.limit_rows(result)
    assert len(shown) == 1000
    assert is_truncated
    assert explorer.limit_rows(result.head(10))[1] is False
# endregion


# region Views and chart data
def test_margins_and_alerts_are_measured_in_percent():
    margins = explorer.prepare_margin_rows(pd.DataFrame({"margin": [0.601]}))
    alerts = explorer.prepare_alert_rows(pd.DataFrame({"variation": [-0.145]}))
    assert margins["value"].iloc[0] == pytest.approx(60.1)
    assert alerts["value"].iloc[0] == pytest.approx(-14.5)


def test_reader_sees_spanish_column_titles():
    result = explorer.build_result(explorer.VIEW_PRICES, make_price_rows(),
                                   [explorer.GROUP_PRODUCT], "Mediana", {})
    titled = explorer.name_columns_for_reader(result, explorer.VIEW_PRICES, "Mediana")
    assert titled.columns.to_list() == ["Producto", "Unidad", "Mediana · precio ($)",
                                        "Precios semanales"]


def test_line_chart_has_one_series_per_group():
    result = explorer.build_result(explorer.VIEW_PRICES, make_price_rows(),
                                   [explorer.GROUP_CHANNEL, explorer.GROUP_WEEK],
                                   "Promedio", {})
    line_rows = explorer.prepare_line_rows(result)
    assert set(line_rows["channel"]) == {"Feria libre · kilo", "Supermercado · kilo"}


def test_bar_chart_shows_the_largest_values_first():
    result = explorer.build_result(explorer.VIEW_PRICES, make_price_rows(),
                                   [explorer.GROUP_CHANNEL], "Promedio", {})
    bar_rows = explorer.prepare_bar_rows(result)
    assert bar_rows["label"].to_list() == ["Supermercado · kilo", "Feria libre · kilo"]
# endregion
