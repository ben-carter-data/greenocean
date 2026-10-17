"""dim_date (D-095): one row per week without gaps, ISO weeks, seasons and integrity."""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl  # noqa: E402

needs_database = pytest.mark.skipif(not etl.DATABASE_FILE.exists(), reason="Requires etl/datos.db")


def test_weeks_are_consecutive_mondays_without_gaps():
    weeks = etl.build_dim_date("2024-11-25", "2025-02-03")
    days = pd.to_datetime(weeks["week_start"])
    assert (days.diff().dropna() == pd.Timedelta(days=7)).all()
    assert (days.dt.weekday == 0).all()
    assert len(weeks) == 11 and list(weeks.columns) == etl.DIM_DATE_COLUMNS


def test_iso_week_at_the_turn_of_the_year():
    weeks = etl.build_dim_date("2024-12-23", "2026-01-05").set_index("week_start")
    assert tuple(weeks.loc["2024-12-30", ["iso_year", "iso_week", "year", "month"]]) == (2025, 1, 2024, 12)
    assert tuple(weeks.loc["2024-12-23", ["iso_year", "iso_week"]]) == (2024, 52)
    assert tuple(weeks.loc["2025-12-29", ["iso_year", "iso_week"]]) == (2026, 1)


@pytest.mark.parametrize("week, season, name", [
    ("2025-12-01", "verano", "diciembre"), ("2026-02-23", "verano", "febrero"),
    ("2026-03-02", "otoño", "marzo"), ("2026-05-25", "otoño", "mayo"),
    ("2026-06-01", "invierno", "junio"), ("2026-08-31", "invierno", "agosto"),
    ("2026-09-07", "primavera", "septiembre"), ("2026-11-30", "primavera", "noviembre")])
def test_southern_season_follows_the_month_of_week_start(week, season, name):
    row = etl.build_dim_date(week, week).iloc[0]
    assert (row["season"], row["month_name"]) == (season, name)


def test_old_database_gets_the_foreign_key_and_keeps_its_rows(tmp_path):
    database_file = tmp_path / "datos.db"
    connection = sqlite3.connect(database_file)
    # A weekly_price created before D-095, without the date reference.
    connection.executescript("""CREATE TABLE weekly_price (week_start TEXT NOT NULL, product_id INTEGER NOT NULL,
        region_id INTEGER NOT NULL, channel_id INTEGER NOT NULL, normalized_unit TEXT, price REAL, volume REAL,
        observation_count INTEGER NOT NULL, flag TEXT);
        INSERT INTO weekly_price VALUES ('2026-01-05', 1, 13, 1, 'kilo', 100.5, NULL, 3, NULL),
                                        ('2026-01-19', 1, 13, 1, 'kilo', 101.5, NULL, 2, 'ATIPICO');""")
    connection.close()
    connection = etl.open_database(database_file, etl.SCHEMA_FILE)
    with connection:
        assert etl.ensure_weekly_price_references_dim_date(connection)
        etl.refresh_dim_date(connection)
    assert not etl.ensure_weekly_price_references_dim_date(connection)
    assert connection.execute("SELECT * FROM weekly_price ORDER BY week_start").fetchall() == [
        ('2026-01-05', 1, 13, 1, 'kilo', 100.5, None, 3, None),
        ('2026-01-19', 1, 13, 1, 'kilo', 101.5, None, 2, 'ATIPICO')]
    # The week without prices in between is kept.
    assert [row[0] for row in connection.execute("SELECT week_start FROM dim_date ORDER BY 1")] == [
        "2026-01-05", "2026-01-12", "2026-01-19"]
    # Only the date reference: the other dimensions are empty in this small database.
    assert [row for row in connection.execute("PRAGMA foreign_key_check") if row[2] == "dim_date"] == []


@needs_database
def test_every_week_of_weekly_price_exists_in_dim_date():
    connection = sqlite3.connect(etl.DATABASE_FILE)
    references = {row[2] for row in connection.execute("PRAGMA foreign_key_list(weekly_price)")}
    assert "dim_date" in references
    orphans = connection.execute("""SELECT COUNT(*) FROM weekly_price w
        LEFT JOIN dim_date d ON d.week_start = w.week_start WHERE d.week_start IS NULL""").fetchone()[0]
    assert orphans == 0
    first, last, weeks = connection.execute(
        "SELECT MIN(week_start), MAX(week_start), COUNT(*) FROM dim_date").fetchone()
    assert (first, last) == connection.execute("SELECT MIN(week_start), MAX(week_start) FROM weekly_price").fetchone()
    assert weeks == (pd.Timestamp(last) - pd.Timestamp(first)).days // 7 + 1
