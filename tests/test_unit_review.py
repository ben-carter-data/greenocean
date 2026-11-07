"""D-520: every sale unit is read as it was reviewed by hand, the same by the ETL and by dbt.

etl/reviewed_units.csv holds every unit ODEPA has used, with the reading checked against the prices of the
same product. A reading is only as safe as this list. The weekly load runs this file (D-366), so it stops when a new
unit gets a price without being a plain package, the one case that can publish a wrong figure. A new plain package,
as «$/caja 110 unidades», or a new unit without a price cannot, and ODEPA adds about seven a year: those fail only in
tests/test_unit_catalog.py, which the load does not run, so they do not stop the data (F-01).
"""

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from bi import unit_review
from etl import etl

# region Variables
REPOSITORY = Path(__file__).resolve().parent.parent
REVIEWED_FILE = unit_review.REVIEWED_FILE
MODEL_FILE = REPOSITORY / "dbt" / "models" / "intermediate" / "int_prices__units_normalized.sql"
needs_raw = pytest.mark.skipif(not etl.RAW_DATABASE_FILE.exists(), reason="etl/raw.db is not in the repository")
PLAIN_PACKAGE = unit_review.PLAIN_PACKAGE
# endregion


# region Every sale unit is read as it was reviewed by hand, the same by the ETL and by dbt
def reviewed():
    return pd.read_csv(REVIEWED_FILE, dtype=str, keep_default_na=False)


def read_source_units():
    import sqlite3

    connection = sqlite3.connect(f"file:{etl.RAW_DATABASE_FILE}?mode=ro", uri=True)
    try:
        found = {row[0] for row in connection.execute("SELECT DISTINCT sale_unit FROM raw_wholesale")}
        found |= {row[0] for row in connection.execute("SELECT DISTINCT unit FROM raw_consumer")}
    finally:
        connection.close()
    return {etl.normalize_text(unit) for unit in found}


def test_d520_the_etl_reads_every_unit_as_it_was_reviewed():
    for row in reviewed().to_dict("records"):
        unit, quantity = etl.convert_unit(row["unit"])
        assert (unit or "") == row["expected_unit"], row["unit"]
        assert quantity == (pytest.approx(float(row["expected_quantity"])) if row["expected_quantity"] else None), row
        weighs = row["expected_volume_quantity"]
        assert etl.volume_quantity(row["unit"]) == (pytest.approx(float(weighs)) if weighs else None), row


def test_d520_dbt_reads_every_unit_like_the_etl():
    table = reviewed()
    model = MODEL_FILE.read_text(encoding="utf-8").replace(
        "{{ ref('int_prices__validated') }}", "(SELECT unit, 1000.0 AS avg_price, NULL AS reason FROM reviewed)"
    )
    connection = duckdb.connect()
    connection.register("reviewed_frame", table[["unit"]])
    connection.execute("CREATE TABLE reviewed AS SELECT unit FROM reviewed_frame")
    read = connection.execute(f"SELECT unit, normalized_unit, unit_quantity, volume_quantity FROM ({model})").fetchall()
    connection.close()
    assert len(read) == len(table)
    expected = {row["unit"]: row for row in table.to_dict("records")}
    for unit, normalized_unit, quantity, weighs in read:
        assert (normalized_unit or "") == expected[unit]["expected_unit"], unit
        wanted = expected[unit]["expected_quantity"]
        assert quantity == (pytest.approx(float(wanted)) if wanted else None), unit
        wanted = expected[unit]["expected_volume_quantity"]
        assert weighs == (pytest.approx(float(wanted)) if wanted else None), unit


def test_d520_only_what_can_be_read_two_ways_is_outside_the_plain_shape():
    """The priced units a person must look at: if the shape let one of these through, the load would not stop."""
    table = reviewed()
    priced = table[table["expected_unit"] != ""]["unit"]
    outside = {unit for unit in priced if not PLAIN_PACKAGE.match(unit.lower())}
    assert outside == {
        "$/bandeja 12 canastillos 125 gramos",
        "$/bandeja 12 canastillos 170 gramos",
        "$/cien",
        "$/cien en rama (volumen en unidades)",
        "$/cien unidades (volumen en unidades)",
        "$/docena de 3 kilos",
        "$/docena de atados (1 kilo)",
        "$/docena de atados (12 kilos)",
        "$/docena de atados (2 kilos)",
        "$/docena de atados (3 kilos)",
        "$/docena de atados (4 kilos)",
        "$/docena de atados (6 kilos)",
    }
    for unit in ("$/caja 110 unidades", "$/bins (500 kilos)", "$/caja 13 kilos granel", "$/kilo (en caja de 14 kilos)"):
        assert PLAIN_PACKAGE.match(unit)
    for unit in (
        "$/docena de paquetes 5 unidades",
        "$/bandeja 12 canastillos 125 gramos",
        "$/caja 12 paquetes 2 kilos",
    ):
        assert not PLAIN_PACKAGE.match(unit)


@needs_raw
def test_d520_no_new_unit_gets_a_price_without_review_unless_it_is_a_plain_package():
    known = set(reviewed()["unit"])
    risky = sorted(
        unit
        for unit in read_source_units() - known
        if etl.convert_unit(unit)[0] and not PLAIN_PACKAGE.match(unit.lower())
    )
    assert not risky, f"Add them to {REVIEWED_FILE.name} after checking the reading against the prices: {risky}"


# endregion
