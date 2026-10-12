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


def run_query(query_name, database_file=DATABASE_FILE):
    """Run one named query and return its rows as a DataFrame."""
    connection = open_database(database_file)
    rows = pd.read_sql(load_queries()[query_name], connection)
    connection.close()
    return rows
# endregion
