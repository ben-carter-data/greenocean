"""Tests for the weekly report."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import report  # noqa: E402
from etl import etl  # noqa: E402
from tests.test_etl import make_raw_consumer_rows  # noqa: E402
from tests.test_etl_run import open_test_databases, replace_raw_rows  # noqa: E402

# region Constants
# Thirteen steady weekly prices: twelve small variations.
STEADY_PRICES = [1000, 1010] * 6 + [1000]
# endregion


# region Tests for the weekly report
def build_database(tmp_path, weekly_prices):
    """Indicator database with one consumer price per consecutive week, quoted by two
    markets: a K6 alert needs at least two quotes in each week (D-158)."""
    raw_connection, connection = open_test_databases(tmp_path)
    mondays = pd.date_range("2026-01-05", periods=len(weekly_prices), freq="7D")
    raw_rows = [
        make_raw_consumer_rows(
            week_start=str(monday.date()),
            week_end=str((monday + pd.Timedelta(days=4)).date()),
            max_price="2000",
            avg_price=f"{price},000000",
            sector=sector,
        )
        for monday, price in zip(mondays, weekly_prices)
        for sector in ("Santiago", "Ñuñoa")
    ]
    replace_raw_rows(raw_connection, etl.SOURCE_CONSUMER, raw_rows)
    etl.run_etl(raw_connection, connection)
    connection.close()
    return tmp_path / "datos.db"


def test_numbers_are_written_as_in_chile():
    assert report.format_count(397814) == "397.814"
    assert report.format_percent(0.123) == "+12,3 %"
    assert report.format_percent(-0.05) == "-5,0 %"


def test_report_shows_the_load_status_and_the_alert_of_the_week(tmp_path):
    database_file = build_database(tmp_path, STEADY_PRICES + [1300])
    report_text = report.build_report(database_file)
    assert "Última ejecución: **LOADED**" in report_text
    assert "Filas leídas: 28" in report_text
    assert "Alertas de la semana 6–12 abr 2026" in report_text
    expected_line = "| Tomate | Larga vida | Primera | Feria libre | 1.300 | +30,0 % |"
    assert expected_line in report_text
    # D-477: a rise goes to the sharp rises; a week with a drop would list it apart, under «Bajas fuertes»
    assert "### Alzas fuertes: 1" in report_text and "Bajas fuertes" not in report_text


def test_d477_a_sharp_drop_goes_to_its_own_table(tmp_path):
    database_file = build_database(tmp_path, STEADY_PRICES + [700])
    report_text = report.build_report(database_file)
    assert "### Bajas fuertes: 1" in report_text and "Alzas fuertes" not in report_text
    assert "| Tomate | Larga vida | Primera | Feria libre | 700 | -30,0 % |" in report_text


def test_report_says_so_when_no_product_is_out_of_range(tmp_path):
    database_file = build_database(tmp_path, STEADY_PRICES + [1010])
    report_text = report.build_report(database_file)
    assert "Ningún producto se movió fuera de su rango habitual." in report_text


# endregion
