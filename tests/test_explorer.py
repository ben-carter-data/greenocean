"""Tests for the search of «Consulta por clics» (D-060)."""
import sys
from pathlib import Path

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


# endregion


# endregion


# endregion
