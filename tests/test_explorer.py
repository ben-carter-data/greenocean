"""Tests for the search of «Consulta por clics» (D-060)."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import explorer  # noqa: E402
from etl import etl  # noqa: E402


# region Sample data
def build_sample_database(database_file):
    """A small datos.db: tomato in Valparaíso, wholesale and street market, one outlier
    and one week missing in the street market series."""
    connection = etl.open_database(database_file, etl.SCHEMA_FILE)
    with connection:
        connection.execute("INSERT INTO dim_product VALUES (1, 'Hortalizas', 'Tomate', "
                           "'Larga vida', 'Primera')")
        connection.execute("INSERT INTO dim_region VALUES (5, 'Región de Valparaíso')")
        connection.execute("INSERT INTO dim_channel VALUES (1, 'Mayorista', 'wholesale')")
        connection.execute("INSERT INTO dim_channel VALUES (2, 'Feria libre', 'consumer')")
        connection.executemany(
            "INSERT INTO weekly_price VALUES (?, 1, 5, ?, 'kilo', ?, NULL, 1, ?)",
            [("2026-03-02", 1, 500.0, None), ("2026-03-09", 1, 600.0, None),
             ("2026-03-02", 2, 1000.0, None), ("2026-03-09", 2, 1200.0, None),
             ("2026-03-16", 2, 9.0, etl.FLAG_OUTLIER), ("2026-03-23", 2, 1300.0, None)])
    connection.close()


def make_filters(**values):
    """A search over everything, from the first to the last sample week."""
    filters = {field: explorer.ALL for field in explorer.LIST_FIELD_COLUMNS}
    filters.update({explorer.FIELD_FIRST_WEEK: "2026-03-02",
                    explorer.FIELD_LAST_WEEK: "2026-03-23", explorer.FIELD_ALERT: explorer.ALL})
    filters.update(values)
    return filters


@pytest.fixture
def database_file(tmp_path):
    database_file = tmp_path / "datos.db"
    build_sample_database(database_file)
    return database_file
# endregion


# region Allowlist and parameters
def test_unknown_field_is_rejected():
    with pytest.raises(ValueError):
        explorer.build_search_query(make_filters(price_above="100"))


def test_chosen_values_travel_as_parameters_never_inside_the_sql():
    sql, parameters = explorer.build_search_query(make_filters(product="Tomate'; DROP TABLE x"))
    assert "DROP TABLE" not in sql
    assert "Tomate'; DROP TABLE x" in parameters
    assert "dim_product.product = ?" in sql


def test_the_week_before_the_first_one_is_read_to_measure_its_change():
    _, parameters = explorer.build_search_query(make_filters(first_week="2026-03-09"))
    assert parameters[0] == "2026-03-02" and parameters[-1] == "2026-03-09"
# endregion


# region Rows, changes and gaps
def test_search_leaves_flagged_prices_out_and_keeps_the_week_range(database_file):
    rows = explorer.read_search_rows(make_filters(first_week="2026-03-09"), database_file)
    assert sorted(rows["week_start"].dt.strftime("%Y-%m-%d").unique()) == [
        "2026-03-09", "2026-03-23"]
    assert 9.0 not in rows["price"].to_list()


def test_change_is_against_the_week_right_before_and_gap_over_wholesale(database_file):
    rows = explorer.read_search_rows(make_filters(), database_file)
    street = rows[rows["channel"] == "Feria libre"]
    street = street.set_index(street["week_start"].dt.strftime("%Y-%m-%d"))
    assert street.loc["2026-03-09", "variation"] == pytest.approx(0.2)
    assert street.loc["2026-03-09", "gap"] == pytest.approx(1.0)
    # The week of 16 March is an outlier: 23 March has no week right before it.
    assert pd.isna(street.loc["2026-03-23", "variation"])
    wholesale = rows[rows["channel"] == "Mayorista"]
    assert wholesale["gap"].isna().all()


def test_a_list_field_filters_by_its_value(database_file):
    rows = explorer.read_search_rows(make_filters(source="wholesale"), database_file)
    assert set(rows["channel"]) == {"Mayorista"}


def test_options_and_history_come_from_the_database(database_file):
    options = explorer.read_search_options(database_file)
    assert options[explorer.FIELD_CHANNEL] == ["Feria libre", "Mayorista"]
    assert options["weeks"][0] == "2026-03-23"
    row = explorer.read_search_rows(make_filters(), database_file).iloc[0]
    history = explorer.read_series_history(row, weeks=12, database_file=database_file)
    assert history["week_start"].is_monotonic_increasing
    assert history["week_start"].max() == row["week_start"]
# endregion


# region Alert states, summary and pages
def test_alert_state_follows_the_k6_distance():
    assert explorer.classify_alert_state(1.0) == explorer.ALERT_NORMAL
    assert explorer.classify_alert_state(1.8) == explorer.ALERT_ATTENTION
    assert explorer.classify_alert_state(2.5) == explorer.ALERT_OUT
    assert explorer.classify_alert_state(float("nan")) == explorer.ALERT_UNKNOWN


def test_a_price_without_a_usual_range_is_without_data(database_file):
    rows = explorer.read_search_rows(make_filters(), database_file)
    states = pd.DataFrame(columns=explorer.alerts.SERIES_COLUMNS
                          + ["week_start", "alert_state", "alert_distance"])
    states["week_start"] = pd.to_datetime(states["week_start"])
    rows = explorer.add_alert_states(rows, states)
    assert set(rows["alert_state"]) == {explorer.ALERT_UNKNOWN}
    assert explorer.summarize_latest_week(rows)[explorer.ALERT_UNKNOWN] == 1
    assert list(explorer.summarize_groups(rows).columns) == explorer.ALERT_STATES
    assert len(explorer.keep_alert_state(rows, explorer.ALERT_OUT)) == 0


def test_pages_say_which_rows_they_show():
    rows = pd.DataFrame({"value": range(45)})
    shown, first, last, total = explorer.take_page(rows, 20, 3)
    assert (len(shown), first, last, total) == (5, 41, 45, 45)
    assert explorer.take_page(rows, 20, 9)[1:3] == (41, 45)
    assert explorer.take_page(rows.head(0), 20, 1)[1:] == (0, 0, 0)
# endregion
