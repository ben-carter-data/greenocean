"""Crossings between databases (D-197, D-239): the databases as layers and the lines between their tables."""

import re
from pathlib import Path

import pytest

from bi import charts, database_crossings, project, queries
from etl import etl

ROOT = Path(__file__).resolve().parent.parent
needs_database = pytest.mark.skipif(not Path(queries.DATABASE_FILE).exists(), reason="datos.duckdb is not here")
CHECKS = {key: ("ok", "ok") for key in ("raw", "ine", "work", "served", "parity", "history")}


def build(checks=None, mode=charts.MODE_DARK):
    return database_crossings.build_crossings_html(charts.get_palette(mode), checks or CHECKS)


def test_every_crossing_names_how_what_travels_and_what_both_sides_share():
    keys = [row[0] for row in database_crossings.CROSSINGS]
    assert len(keys) == len(set(keys)) == 8
    assert keys == [
        "odepa_raw",
        "ine_bronze",
        "raw_bronze",
        "bronze_work",
        "work_served",
        "raw_backup",
        "served_backup",
        "history",
    ]
    for row in database_crossings.CROSSINGS:
        assert all(str(part).strip() for part in row), row[0]


def test_ine_skips_sqlite_and_the_backup_is_only_compared():
    rows = {row[0]: row for row in database_crossings.CROSSINGS}
    assert rows["ine_bronze"][3:5] == ("INE · IPC", "Bronce") and "sin pasar por SQLite" in rows["ine_bronze"][5]
    assert "Nada se copia" in rows["served_backup"][8]
    assert rows["raw_backup"][3:5] == ("raw.db", "datos.db") and rows["served_backup"][3:5] == (
        "datos.duckdb",
        "datos.db",
    )


def test_every_line_is_straight_and_each_crossing_but_the_history_has_its_lines():
    for key, lines in database_crossings.LINES.items():
        assert lines, key
        for (x1, y1), (x2, y2) in lines:
            assert x1 == x2 or y1 == y2, key
    assert set(database_crossings.LINES) == {row[0] for row in database_crossings.CROSSINGS} - {"history"}
    markup = build()
    paths = re.findall(r'<path class="line[^"]*" d="M(\S+) (\S+) L(\S+) (\S+)"', markup)
    assert paths
    for x1, y1, x2, y2 in paths:
        assert x1 == x2 or y1 == y2, (x1, y1, x2, y2)
    # The INE goes straight down from its source to the bronze layer, over raw.db without touching a table of it.
    ine_x = database_crossings.center("a")
    raw_tables = [chip for chip in database_crossings.CHIPS if chip[0] == "raw"]
    assert all(database_crossings.center(chip[2][0]) != ine_x for chip in raw_tables)


def test_the_layers_are_the_databases_and_they_hold_the_tables_that_cross():
    markup = build()
    text = re.sub(r"<[^>]+>", " ", markup)
    for layer in ("raw.db", "Bronce", "Base de trabajo", "datos.duckdb", "datos.db", "Fuentes externas"):
        assert layer in text, layer
    assert markup.count('class="chip"') >= len(database_crossings.CHIPS)
    assert "week_start" in text and "run_id" in text  # the keys the databases are joined on


def test_each_crossing_has_a_numbered_mark_coloured_by_its_check_and_a_card_with_the_detail():
    checks = {**CHECKS, "raw": ("pending", "no se puede comprobar aquí"), "ine": ("info", "dato")}
    markup = build(checks)
    assert markup.count('class="badge s-') == markup.count('class="tip s-') == 8
    assert 's-pending' in markup and 's-info' in markup and 's-ok' in markup
    for row in database_crossings.CROSSINGS:
        assert f'id="x-{row[0]}"' in markup and f'id="t-{row[0]}"' in markup, row[0]
        assert row[8] in markup and row[9] in markup  # what travels and what both sides share, in the hover card
    assert "No medible aquí" in markup and "Comprobado ahora" in markup
    assert "<script" not in markup


def test_the_drawing_scales_to_its_window_and_the_text_stays_readable():
    markup = build()
    assert f'viewBox="0 0 {database_crossings.WIDTH} {database_crossings.HEIGHT}"' in markup
    assert 'preserveAspectRatio="xMidYMid meet"' in markup
    sizes = [float(size) for size in re.findall(r"font-size:([\d.]+)px", markup.split("</style>")[0])]
    assert min(sizes) >= 11


def test_the_light_themes_draw_too():
    for mode in (charts.MODE_CORPORATE, charts.MODE_BLUE_LIGHT):
        assert "datos.duckdb" in build(mode=mode)


@needs_database
def test_the_live_checks_hold_on_the_real_database_and_say_what_cannot_be_measured():
    checks = database_crossings.read_checks()
    assert checks["parity"][0] in ("ok", "pending")
    assert checks["work"][0] == "ok" and checks["served"][0] == "ok" and checks["history"][0] == "ok"
    if not Path(etl.RAW_DATABASE_FILE).exists():
        assert checks["raw"][0] == "pending" and "no se puede comprobar" in checks["raw"][1]
    assert build(checks).count('class="badge s-') == 8


def test_every_table_drawn_exists_in_the_repository():
    sources = {
        "raw": (ROOT / "etl" / "etl.py").read_text(encoding="utf-8"),
        "bronze": (ROOT / "etl" / "bronze.py").read_text(encoding="utf-8"),
    }
    served = set(project.TABLE_NAMES + project.IPC_TABLE_NAMES)
    for layer, _, _, name in database_crossings.CHIPS:
        if layer == "raw":
            assert name in sources["raw"], name
        elif layer == "bronze":
            assert name.replace("odepa_", "odepa_") in sources["bronze"] or name == "ine_ipc", name
        elif layer == "work" and name.startswith("stg_"):
            assert list((ROOT / "dbt" / "models" / "staging").glob(f"{name}.sql")), name
        else:
            assert name in served or list((ROOT / "dbt" / "models").rglob(f"{name}.sql")), name
    assert set(database_crossings.BACKUP_CHIPS) | {"weekly_price"} == set(database_crossings.BACKUP_TABLES)
