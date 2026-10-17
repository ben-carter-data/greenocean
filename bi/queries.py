"""Read-only access to the indicator database through the named queries.

Shared by the dashboard, the alerts and the weekly report.
"""
import re
import sqlite3
import time
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


# region SQL console (D-126)
CONSOLE_ROW_LIMIT = 1000
CONSOLE_TIMEOUT_SECONDS = 10
# Only reading is allowed, on top of the read-only connection: no ATTACH (it could
# open another file), no PRAGMA, no write, no schema change.
CONSOLE_ALLOWED_ACTIONS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                           sqlite3.SQLITE_RECURSIVE}


class ConsoleError(ValueError):
    """A console query that cannot run, with a message for the reader."""


def prepare_console_sql(sql):
    """The query of a visitor, cleaned: one statement, starting with SELECT or WITH."""
    text = re.sub(r"--[^\n]*", "", sql or "")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL).strip().rstrip(";").strip()
    if not text:
        raise ConsoleError("Escribe una consulta para ejecutarla.")
    if ";" in text:
        raise ConsoleError("Ejecuta una sola consulta a la vez (sin «;» en medio).")
    if not re.match(r"(?is)^(select|with)\b", text):
        raise ConsoleError("Solo se permiten consultas de lectura: deben empezar con SELECT o WITH.")
    return text


def run_console_sql(sql, database_file=DATABASE_FILE, limit=CONSOLE_ROW_LIMIT,
                    timeout_seconds=CONSOLE_TIMEOUT_SECONDS):
    """Run a visitor's query safely: read-only, one statement, at most limit rows and
    timeout_seconds of work. Returns (rows, truncated, milliseconds)."""
    text = prepare_console_sql(sql)
    connection = open_database(database_file)
    connection.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK
                              if action in CONSOLE_ALLOWED_ACTIONS else sqlite3.SQLITE_DENY)
    started = time.monotonic()
    connection.set_progress_handler(
        lambda: int(time.monotonic() - started > timeout_seconds), 10_000)
    try:
        rows = pd.read_sql(f"SELECT * FROM (\n{text}\n) LIMIT {limit + 1}", connection)
    except Exception as error:  # sqlite3 and pandas wrap SQL errors differently
        message = str(error.__cause__ or error)
        if "interrupted" in message:
            raise ConsoleError(f"La consulta superó {timeout_seconds} s y se detuvo.") from error
        if "not authorized" in message:
            raise ConsoleError("Esa operación no está permitida: la consola es de solo lectura.") from error
        raise ConsoleError(f"Error de SQLite: {message}") from error
    finally:
        connection.close()
    milliseconds = (time.monotonic() - started) * 1000
    return rows.head(limit), len(rows) > limit, milliseconds


def list_tables(database_file=DATABASE_FILE):
    """[(table, row count)] of the indicator database, for the console's explorer."""
    names = run_sql("SELECT name FROM sqlite_master WHERE type = 'table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name", database_file)["name"]
    return [(name, int(run_sql(f'SELECT COUNT(*) AS n FROM "{name}"', database_file)["n"].iloc[0]))
            for name in names]
# endregion
