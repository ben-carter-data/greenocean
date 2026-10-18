"""Read-only access to the indicator database through the named queries.

Shared by the dashboard, the alerts and the weekly report.
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

# region Variables
BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR.parent / "etl" / "datos.db"
QUERIES_FILE = BASE_DIR / "queries.sql"
# Each query of queries.sql starts with a line "-- name: query_name".
QUERY_NAME_PATTERN = re.compile(r"^-- name: (\w+)\n", re.MULTILINE)
# A product key: what the dashboard filters choose (D-050).
KEY_COLUMNS = ["product_group", "product", "variety", "quality", "normalized_unit"]
# endregion


# region Data access
def load_queries(queries_file=QUERIES_FILE):
    """Read queries.sql and return a dictionary {query name: SQL text}."""
    text = queries_file.read_text(encoding="utf-8")
    # split() returns [text before the first name, name, sql, name, sql, ...].
    parts = QUERY_NAME_PATTERN.split(text)
    return dict(zip(parts[1::2], parts[2::2]))


def open_database(database_file=DATABASE_FILE):
    """Open the indicator database in read-only mode."""
    return sqlite3.connect(f"file:{database_file}?mode=ro", uri=True)


def run_query(query_name, database_file=DATABASE_FILE, parameters=()):
    """Run one named query and return its rows as a DataFrame."""
    return run_sql(load_queries()[query_name], database_file, parameters)


def run_sql(sql, database_file=DATABASE_FILE, parameters=()):
    """Run a query text on the read-only connection and return its rows."""
    connection = open_database(database_file)
    rows = pd.read_sql(sql, connection, params=list(parameters))
    connection.close()
    return rows


def read_query_body(query_name):
    """A named query without its final semicolon, so it can be used as a subquery."""
    return load_queries()[query_name].strip().rstrip(";")


def run_query_for_key(query_name, key, database_file=DATABASE_FILE):
    """Rows of one named query for a single product key (D-050).

    SQLite filters the rows, so the dashboard receives a few thousand rows
    instead of the whole indicator. The key values travel as parameters.
    """
    conditions = " AND ".join(f"{column} = ?" for column in KEY_COLUMNS)
    sql = f"SELECT * FROM (\n{read_query_body(query_name)}\n) WHERE {conditions}"
    return run_sql(sql, database_file, [key[column] for column in KEY_COLUMNS])


def list_query_keys(query_name, database_file=DATABASE_FILE):
    """Product keys present in one named query, with how many rows each one has."""
    columns = ", ".join(KEY_COLUMNS)
    sql = (f"SELECT {columns}, COUNT(*) AS row_count FROM (\n{read_query_body(query_name)}\n) "
           f"GROUP BY {columns}")
    return run_sql(sql, database_file)
# endregion


