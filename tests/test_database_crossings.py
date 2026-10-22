"""Crossings between databases (D-197, D-237): eight rows, read top to bottom, each complete."""
import re
from pathlib import Path

import pytest

from bi import charts, database_crossings, queries
from etl import etl

needs_database = pytest.mark.skipif(not Path(queries.DATABASE_FILE).exists(), reason="datos.duckdb is not here")


def test_every_crossing_names_how_what_travels_and_what_both_sides_share():
    keys = [row[0] for row in database_crossings.CROSSINGS]
    assert len(keys) == len(set(keys)) == 8
    for row in database_crossings.CROSSINGS:
        assert all(str(part).strip() for part in row), row[0]
        assert len(row[6]) <= 40 and len(row[7]) <= 40, row[0]  # the short texts are read in the row


def test_the_eight_crossings_come_in_four_moments_in_the_order_of_the_story():
    assert [phase[2] for phase in database_crossings.PHASES] == [3, 2, 2, 1]
    assert sum(phase[2] for phase in database_crossings.PHASES) == len(database_crossings.CROSSINGS)
    order = [row[0] for row in database_crossings.CROSSINGS]
    assert order == ["odepa_raw", "ine_bronze", "raw_bronze", "bronze_work", "work_served", "raw_backup",
                     "served_backup", "history"]


def test_ine_skips_sqlite_and_the_backup_is_only_compared():
    rows = {row[0]: row for row in database_crossings.CROSSINGS}
    assert rows["ine_bronze"][3:5] == ("INE · IPC", "Bronce") and "sin pasar por SQLite" in rows["ine_bronze"][5]
    assert "Nada se copia" in rows["served_backup"][8]


def build(checks=None):
    checks = checks or {key: ("ok", "ok") for key in ("raw", "ine", "work", "served", "parity", "history")}
    return database_crossings.build_crossings_html(charts.get_palette(charts.MODE_DARK), checks)


def test_each_row_is_complete_without_a_hover_and_the_page_says_what_each_column_is():
    markup = build()
    assert markup.count('class="row ') == 8 and markup.count('class="phase"') == 4
    text = re.sub(r"<[^>]+>", " ", markup)
    for heading in ("Qué viaja", "Se cruzan por", "Comprobación ahora", "Entra el dato", "Se recuerda"):
        assert heading in text, heading
    for row in database_crossings.CROSSINGS:
        assert row[5] in text and row[6] in text and row[7] in text, row[0]  # mechanism, what travels, shared key
        assert row[8] in text  # the full text, on hover, is in the page too
    # One straight line per row; only the parity check points both ways and is dashed.
    assert markup.count('class="link') == 8 and markup.count('class="link both"') == 1


def test_the_stores_use_the_same_marks_as_the_storage_map():
    markup = build()
    for brand in ("sqlite", "duckdb", "apacheparquet", "python"):
        assert f'id="cyl-c' in markup or f'id="disc-{brand}' in markup, brand
    assert markup.count('class="mark"') == 16  # two stores in each of the eight rows


def test_the_only_script_is_the_fixed_zoom_to_fit():
    markup = build()
    assert markup.count("<script") == 1 and database_crossings.FIT_SCRIPT in markup


@needs_database
def test_the_live_checks_hold_on_the_real_database_and_say_what_cannot_be_measured():
    checks = database_crossings.read_checks()
    assert checks["parity"][0] in ("ok", "pending")
    assert checks["work"][0] == "ok" and checks["served"][0] == "ok" and checks["history"][0] == "ok"
    if not Path(etl.RAW_DATABASE_FILE).exists():
        assert checks["raw"][0] == "pending" and "no se puede comprobar" in checks["raw"][1]
    html = build(checks)
    assert len(re.findall(r'class="row s-', html)) == 8


def test_the_python_etl_and_the_parity_are_two_different_crossings_of_the_backup():
    rows = {row[0]: row for row in database_crossings.CROSSINGS}
    assert rows["raw_backup"][3:5] == ("raw.db", "datos.db")
    assert rows["served_backup"][3:5] == ("datos.duckdb", "datos.db")
