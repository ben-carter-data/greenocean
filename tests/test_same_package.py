"""D-522, RN-15: a change of price compares only the packages sold in both weeks, in everything that shows a variation."""

import sqlite3

import duckdb
import pandas as pd
import pytest

from bi import channel_latest, home_mockup, price_export, queries
from etl import etl

# region Constants and variables
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")
needs_raw = pytest.mark.skipif(not etl.RAW_DATABASE_FILE.exists(), reason="etl/raw.db is not in the repository")
KEYS = ["product", "channel", "region"]
# endregion


# region Same package
def has_the_table():
    with queries.open_database() as connection:
        return connection.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = 'weekly_same_package'"
        ).fetchone()[0]


def test_d522_a_price_that_only_changed_package_leaves_the_comparison():
    now = pd.DataFrame(
        [
            ("Kiwi", "Mayorista", "Metropolitana", 2273.0, 7),
            ("Kiwi", "Mayorista", "Maule", 1900.0, 1),
            ("Kiwi", "Mayorista", "Los Lagos", 1850.0, 3),
        ],
        columns=[*KEYS, "price", "observation_count"],
    )
    before = pd.DataFrame(
        [
            ("Kiwi", "Mayorista", "Metropolitana", 1978.0, 7),
            ("Kiwi", "Mayorista", "Maule", 1111.0, 1),  # bandeja 18 kilos: this week it sold bandeja 10 kilos
            ("Kiwi", "Mayorista", "Los Lagos", 1705.0, 2),
            ("Kiwi", "Mayorista", "Biobío", 1500.0, 2),  # not sold this week: out, as it was
        ],
        columns=[*KEYS, "price", "observation_count"],
    )
    changes = pd.DataFrame(
        [
            (
                "Kiwi",
                "Mayorista",
                "Metropolitana",
                2237.0,
                2050.0,
                7,
                6,
                "$/bandeja 10 kilos · $/kilo (en bins de 450 kilos)",
            ),
            ("Kiwi", "Mayorista", "Los Lagos", 1850.0, 1705.0, 3, 2, "$/caja 15 kilos"),
        ],
        columns=[*KEYS, "price_now", "price_before", "quotes_now", "quotes_before", "packages"],
    )
    current, previous = home_mockup.same_package_pair(now, before, changes, KEYS)
    assert list(previous["region"]) == [
        "Metropolitana",
        "Los Lagos",
        "Biobío",
    ]  # the package change leaves; the unsold stays
    prices = current.set_index("region")["price"]
    assert (
        prices["Metropolitana"] == 2237.0 and prices["Maule"] == 1900.0
    )  # the price sold stays where nothing compares
    assert previous.set_index("region")["price"]["Metropolitana"] == 2050.0
    compared = current.merge(previous, on=KEYS, suffixes=("_now", "_before"))
    assert set(compared["region"]) == {"Metropolitana", "Los Lagos"}
    change = compared["price_now"].mean() / compared["price_before"].mean() - 1
    assert change == pytest.approx(0.0884, abs=1e-3)  # +8.8 %, not the +25.6 % a change of package made
    assert home_mockup.same_package_pair(now, before, None, KEYS) == (now, before)  # a base older than the rule


def test_d522_the_row_names_the_package_it_compares():
    assert home_mockup.package_label("$/caja 15 kilos") == "caja 15 kilos"
    assert home_mockup.package_label(None) == ""
    assert home_mockup.join_packages(["$/a · $/b", "$/b", None]) == "$/a · $/b"
    assert home_mockup.join_packages([None]) is None
    note = home_mockup.package_note({"_packages": "$/bandeja 18 kilos", "normalized_unit": "kilo"})
    assert "Envase comparado: bandeja 18 kilos" in note and "Consultas SQL" in note
    assert home_mockup.package_note({"_packages": "$/kilo", "normalized_unit": "kilo"}) == ""  # nothing new to say
    assert home_mockup.package_note({"normalized_unit": "kilo"}) == ""
    assert ("Envase comparado", "text") in price_export.COLUMNS


def test_d522_a_channel_page_compares_the_same_way():
    matched = pd.DataFrame(
        {
            "price": [10.0, 20.0],
            "price_before": [9.0, 15.0],
            "same_package_now": [11.0, None],
            "same_package_before": [10.0, None],
        }
    )
    kept = channel_latest.same_package_matches(matched)
    assert list(kept["price"]) == [11.0] and list(kept["price_before"]) == [10.0]
    older = matched.drop(columns=["same_package_now", "same_package_before"])
    assert channel_latest.same_package_matches(older).equals(older)  # a base older than the rule


def test_d522_a_base_published_before_the_rule_still_answers():
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE weekly_price AS SELECT * FROM (VALUES "
        "('2026-10-19', 1, 1, 1, 'kilo', 100.0, 2, NULL), ('2026-10-26', 1, 1, 1, 'kilo', 110.0, 3, NULL)) "
        "AS t(week_start, product_id, region_id, channel_id, normalized_unit, price, observation_count, flag)"
    )
    sql = queries.resolve_same_package(connection, "SELECT price_now, price_before FROM weekly_same_package")
    assert connection.execute(sql).fetchall() == [(110.0, 100.0)]
    connection.execute("CREATE TABLE weekly_same_package (price_now DOUBLE, price_before DOUBLE)")
    plain = "SELECT price_now, price_before FROM weekly_same_package"
    assert queries.resolve_same_package(connection, plain) == plain
    connection.close()


@needs_database
def test_d522_the_kiwi_of_the_26th_of_october_rose_what_its_package_rose():
    if not has_the_table():
        pytest.skip("The published base is older than the rule")
    rows = queries.run_sql(
        "SELECT * FROM (" + queries.read_query_body("same_package_changes") + ") WHERE week_start = '2026-10-26' "
        "AND product = 'Kiwi' AND variety = 'Hayward' AND quality = 'Especial' AND channel = 'Mayorista'"
    )
    assert "Región del Maule" not in set(rows["region"])  # it changed from bandeja 18 kilos to bandeja 10 kilos
    assert rows["price_now"].mean() / rows["price_before"].mean() - 1 == pytest.approx(0.088, abs=1e-3)


@needs_raw
@needs_database
def test_d522_the_changes_are_rebuilt_from_the_raw_rows_of_odepa():
    """Without dbt: the rows of ODEPA, read package by package, for the last week published."""
    if not has_the_table():
        pytest.skip("The published base is older than the rule")
    week = queries.run_sql("SELECT max(week_start) AS week FROM weekly_same_package")["week"].iloc[0]
    monday = pd.Timestamp(week)
    days = [f"{monday + pd.Timedelta(days=day - 7):%Y-%m-%d}" for day in range(14)]
    connection = sqlite3.connect(f"file:{etl.RAW_DATABASE_FILE}?mode=ro", uri=True)
    try:
        raw = pd.read_sql(
            f"SELECT price_date, region_id, product, variety, quality, sale_unit, avg_price, volume FROM raw_wholesale "
            f"WHERE price_date IN ({','.join('?' * len(days))})",
            connection,
            params=days,
        )
    finally:
        connection.close()
    for column in ("avg_price", "volume"):
        raw[column] = pd.to_numeric(raw[column].str.replace(",", ".", regex=False), errors="coerce")
    raw = raw[(raw["avg_price"] > 0) & (raw["volume"] > 0)]
    raw["sale_unit"] = raw["sale_unit"].map(etl.normalize_text)
    for column in ("product", "variety", "quality"):
        raw[column] = raw[column].map(etl.normalize_text)
    raw["normalized_unit"] = raw["sale_unit"].map(lambda unit: etl.convert_unit(unit)[0])
    raw["quantity"] = raw["sale_unit"].map(lambda unit: etl.convert_unit(unit)[1])
    raw = raw[raw["quantity"].notna()]
    raw["price"] = raw["avg_price"] / raw["quantity"]
    raw["week"] = pd.to_datetime(raw["price_date"]).map(lambda day: day - pd.Timedelta(days=day.dayofweek))
    keys = ["region_id", "product", "variety", "quality", "normalized_unit", "sale_unit"]
    raw["amount"] = raw["price"] * raw["volume"]
    packages = raw.groupby([*keys, "week"], as_index=False)[["amount", "volume"]].sum()
    packages["price"] = packages["amount"] / packages["volume"]
    now = packages[packages["week"] == monday]
    before = packages[packages["week"] == monday - pd.Timedelta(days=7)]
    common = now.merge(before, on=keys, suffixes=("_now", "_before"))
    expected = common.groupby(keys[:5], as_index=False)[["price_now", "price_before"]].mean()
    shown = queries.run_sql(
        "SELECT c.region_id, p.product, p.variety, p.quality, c.normalized_unit, c.price_now, c.price_before "
        "FROM weekly_same_package c "
        "JOIN dim_product p USING (product_id) JOIN dim_channel h USING (channel_id) "
        "WHERE h.source = 'wholesale' AND c.week_start = ?",
        parameters=[week],
    )
    shown["region_id"] = shown["region_id"].astype(str)
    expected["region_id"] = pd.to_numeric(expected["region_id"]).astype(int).astype(str)
    merged = shown.merge(expected, on=keys[:5], suffixes=("", "_raw"))
    assert len(merged) == len(shown) > 300  # every row of the table comes from the raw rows
    assert (merged["price_now"] - merged["price_now_raw"]).abs().max() < 1e-6
    assert (merged["price_before"] - merged["price_before_raw"]).abs().max() < 1e-6


# endregion
