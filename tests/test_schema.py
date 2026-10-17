"""Tests for the indicator database schema (T-07)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl  # noqa: E402

EXPECTED_TABLES = {"dim_product", "dim_region", "dim_channel", "dim_date", "weekly_price",
                   "etl_run", "rejection"}


def test_database_is_created_from_scratch(tmp_path):
    connection = etl.open_database(tmp_path / "datos.db", etl.SCHEMA_FILE)
    table_names = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert table_names == EXPECTED_TABLES


def test_d046_old_unique_index_is_removed_from_existing_databases(tmp_path):
    database_file = tmp_path / "datos.db"
    connection = etl.open_database(database_file, etl.SCHEMA_FILE)
    connection.execute("CREATE UNIQUE INDEX ux_weekly_price_key ON weekly_price"
                       " (week_start, product_id, region_id, channel_id, normalized_unit)")
    connection.close()
    connection = etl.open_database(database_file, etl.SCHEMA_FILE)
    index_names = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index'")]
    assert "ux_weekly_price_key" not in index_names
