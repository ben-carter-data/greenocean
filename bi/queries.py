"""Read-only access to the indicator database through the named queries.

Shared by the dashboard, the alerts and the weekly report.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

import re
from pathlib import Path

import duckdb

# region Constants
SAME_PACKAGE_TABLE = "weekly_same_package"
SAME_PACKAGE_BEFORE_THE_RULE = """(
    SELECT now.week_start, now.product_id, now.region_id, now.channel_id, now.normalized_unit,
           now.price AS price_now, before.price AS price_before,
           now.observation_count AS quotes_now, before.observation_count AS quotes_before,
           CAST(NULL AS VARCHAR) AS packages
    FROM weekly_price AS now
    JOIN weekly_price AS before
      ON before.product_id = now.product_id AND before.channel_id = now.channel_id
     AND before.normalized_unit = now.normalized_unit AND before.region_id = now.region_id
     AND before.week_start = strftime(CAST(now.week_start AS DATE) - 7, '%Y-%m-%d')
    WHERE now.flag IS NULL AND before.flag IS NULL
)"""
# endregion


# region Variables
BASE_DIR = Path(__file__).resolve().parent
# The data warehouse the panel reads: DuckDB, built by dbt (D-154). The engine is
# chosen here and nowhere else; etl/datos.db (SQLite) is kept only as a backup.
DATABASE_FILE = BASE_DIR.parent / "etl" / "datos.duckdb"
QUERIES_FILE = BASE_DIR / "queries.sql"
# Each query of queries.sql starts with a line "-- name: query_name".
QUERY_NAME_PATTERN = re.compile(r"^-- name: (\w+)\n", re.MULTILINE)
# A product key: what the dashboard filters choose (D-050).
KEY_COLUMNS = ["product_group", "product", "variety", "quality", "normalized_unit"]
# endregion


# region Data access
def load_queries(queries_file: Path = QUERIES_FILE) -> dict[str, str]:
    """Read queries.sql and return a dictionary {query name: SQL text}."""
    text = queries_file.read_text(encoding="utf-8")
    # split() returns [text before the first name, name, sql, name, sql, ...].
    parts = QUERY_NAME_PATTERN.split(text)
    return dict(zip(parts[1::2], parts[2::2]))


def open_database(database_file: Path = DATABASE_FILE) -> duckdb.DuckDBPyConnection:
    """Open the indicator database in read-only mode."""
    return duckdb.connect(str(database_file), read_only=True)


def read_dataframe(connection: duckdb.DuckDBPyConnection, sql: str, parameters: Any = ()) -> pd.DataFrame:
    """Rows of a query on an open connection, as a DataFrame."""
    return connection.execute(sql, list(parameters)).df()


def run_query(query_name: str, database_file: Path = DATABASE_FILE, parameters: Any = ()) -> pd.DataFrame:
    """Run one named query and return its rows as a DataFrame."""
    return run_sql(load_queries()[query_name], database_file, parameters)


def resolve_same_package(connection: duckdb.DuckDBPyConnection, sql: str) -> str:
    """D-522: a base published before the rule has no weekly_same_package, and the app can run on it until the next load
    replaces it: the same columns come then from weekly_price, comparing the whole week, as before the rule."""
    if SAME_PACKAGE_TABLE not in sql:
        return sql
    found = connection.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [SAME_PACKAGE_TABLE]
    ).fetchone()
    return sql if found and found[0] else sql.replace(SAME_PACKAGE_TABLE, SAME_PACKAGE_BEFORE_THE_RULE)


def run_sql(sql: str, database_file: Path = DATABASE_FILE, parameters: Any = ()) -> pd.DataFrame:
    """Run a query text on the read-only connection and return its rows."""
    connection = open_database(database_file)
    try:
        return read_dataframe(connection, resolve_same_package(connection, sql), parameters)
    finally:
        connection.close()


def read_query_body(query_name: str) -> str:
    """A named query without its final semicolon, so it can be used as a subquery."""
    return load_queries()[query_name].strip().rstrip(";")


def run_query_for_region(query_name: str, region: str, database_file: Path = DATABASE_FILE) -> pd.DataFrame:
    """Rows of one named query for a single region (D-499); the database filters them, as in run_query_for_key."""
    return run_sql(f"SELECT * FROM (\n{read_query_body(query_name)}\n) WHERE region = ?", database_file, [region])


def run_query_for_key(query_name: str, key: dict[str, Any], database_file: Path = DATABASE_FILE) -> pd.DataFrame:
    """Rows of one named query for a single product key (D-050).

    The database filters the rows, so the dashboard receives a few thousand rows
    instead of the whole indicator. The key values travel as parameters.
    """
    conditions = " AND ".join(f"{column} = ?" for column in KEY_COLUMNS)
    sql = f"SELECT * FROM (\n{read_query_body(query_name)}\n) WHERE {conditions}"
    return run_sql(sql, database_file, [key[column] for column in KEY_COLUMNS])


# endregion
