"""Tests for the indicator database schema (T-07)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl  # noqa: E402

EXPECTED_TABLES = {"dim_product", "dim_region", "dim_channel", "weekly_price",
                   "etl_run", "rejection"}


def test_database_is_created_from_scratch(tmp_path):
    connection = etl.open_database(tmp_path / "datos.db", etl.SCHEMA_FILE)
    table_names = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert table_names == EXPECTED_TABLES
