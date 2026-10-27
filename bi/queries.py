"""Read-only access to the indicator database through the named queries.

Shared by the dashboard, the alerts and the weekly report.
"""

import re
from pathlib import Path

import duckdb

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
def load_queries(queries_file=QUERIES_FILE):
    """Read queries.sql and return a dictionary {query name: SQL text}."""
    text = queries_file.read_text(encoding="utf-8")
    # split() returns [text before the first name, name, sql, name, sql, ...].
    parts = QUERY_NAME_PATTERN.split(text)
    return dict(zip(parts[1::2], parts[2::2]))


def open_database(database_file=DATABASE_FILE):
    """Open the indicator database in read-only mode."""
    return duckdb.connect(str(database_file), read_only=True)


def read_dataframe(connection, sql, parameters=()):
    """Rows of a query on an open connection, as a DataFrame."""
    return connection.execute(sql, list(parameters)).df()


def run_query(query_name, database_file=DATABASE_FILE, parameters=()):
    """Run one named query and return its rows as a DataFrame."""
    return run_sql(load_queries()[query_name], database_file, parameters)


def run_sql(sql, database_file=DATABASE_FILE, parameters=()):
    """Run a query text on the read-only connection and return its rows."""
    connection = open_database(database_file)
    try:
        return read_dataframe(connection, sql, parameters)
    finally:
        connection.close()


def read_query_body(query_name):
    """A named query without its final semicolon, so it can be used as a subquery."""
    return load_queries()[query_name].strip().rstrip(";")


def run_query_for_key(query_name, key, database_file=DATABASE_FILE):
    """Rows of one named query for a single product key (D-050).

    The database filters the rows, so the dashboard receives a few thousand rows
    instead of the whole indicator. The key values travel as parameters.
    """
    conditions = " AND ".join(f"{column} = ?" for column in KEY_COLUMNS)
    sql = f"SELECT * FROM (\n{read_query_body(query_name)}\n) WHERE {conditions}"
    return run_sql(sql, database_file, [key[column] for column in KEY_COLUMNS])


# endregion
