"""Crossings between databases (D-197)."""
import re
from pathlib import Path

import pytest

from bi import charts, database_crossings, queries
from etl import etl

needs_database = pytest.mark.skipif(not Path(queries.DATABASE_FILE).exists(), reason="datos.duckdb is not here")


def test_every_crossing_names_how_what_travels_and_what_both_sides_share():
    keys = [row[0] for row in database_crossings.CROSSINGS]
    assert len(keys) == len(set(keys)) == 7
    for row in database_crossings.CROSSINGS:
        assert all(str(part).strip() for part in row), row[0]


def test_ine_skips_sqlite_and_the_backup_is_only_compared():
    rows = {row[0]: row for row in database_crossings.CROSSINGS}
    assert rows["ine_bronze"][3:5] == ("INE", "Bronce") and "sin pasar por SQLite" in rows["ine_bronze"][5]
    assert "Nada se copia" in rows["served_backup"][6]


@needs_database
def test_the_live_checks_hold_on_the_real_database_and_say_what_cannot_be_measured():
    checks = database_crossings.read_checks()
    assert checks["parity"][0] in ("ok", "pending")
    assert checks["work"][0] == "ok" and checks["served"][0] == "ok" and checks["history"][0] == "ok"
    if not Path(etl.RAW_DATABASE_FILE).exists():
        assert checks["raw"][0] == "pending" and "no se puede comprobar" in checks["raw"][1]
    html = database_crossings.build_crossings_html(charts.get_palette(next(iter(charts.PALETTES))), checks)
    assert len(re.findall(r'class="row"', html)) == 7 and "<script" not in html
