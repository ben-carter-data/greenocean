"""«Dónde viven los datos» (D-236): the storage architecture, its stores, lines and sources."""
import re
from pathlib import Path

from bi import charts, database_map, storage_map

ROOT = Path(__file__).resolve().parent.parent
COUNTS = {"weekly_price": 814610, "dim_product": 1609, "dim_region": 9, "dim_channel": 8, "dim_date": 250,
          "rejection": 201, "ipc_weekly": 250, "ipc_monthly": 202, "ine_ipc_source": 202, "etl_run": 5,
          "dbt_node": 50, "dbt_result": 47}
SIZES = {"raw": "≈ 665 MB", "served": "19 MB", "backup": "34 MB"}


def build(mode=charts.MODE_DARK, layers=None, tests=31, sizes=SIZES):
    return storage_map.build_map_html(charts.get_palette(mode), COUNTS,
                                      layers or {"staging": 3, "intermediate": 4, "marts": 9}, tests, sizes)


def test_every_store_is_a_card_with_its_file_and_a_hover_that_says_what_why_and_where_from():
    markup = build()
    text = re.sub(r"<[^>]+>", " ", markup)
    for store in ("etl/raw.db", "capa bronce", "warehouse_build.duckdb", "etl/datos.duckdb", "etl/datos.db",
                  "CSV por año", "Streamlit"):
        assert store in text, store
    for key in storage_map.TIP_KEYS:
        assert f'id="t-{key}"' in markup, key
    for heading in ("Qué guarda", "Por qué", "Fuente"):
        assert markup.count(f"<b>{heading}</b>") == len(storage_map.TIP_KEYS), heading
    assert "<script" not in markup


def test_the_cylinders_are_the_databases_and_the_files_are_not():
    markup = build()
    # SQLite twice (landing and backup) and DuckDB twice (work and served) are databases; Parquet is files.
    for key in ("raw", "backup", "dbt", "served"):
        assert f'id="cyl-{key}"' in markup, key
    assert 'id="cyl-bronze"' not in markup and 'id="cyl-odepa"' not in markup


def test_every_line_is_one_straight_horizontal_or_vertical_segment_with_a_head():
    markup = build()
    paths = re.findall(r'<path class="line[^"]*" d="M(\S+) (\S+) L(\S+) (\S+)"', markup)
    assert len(paths) >= len(storage_map.LINES) + 2  # plus the parity check and the deploy
    for x1, y1, x2, y2 in paths:
        assert x1 == x2 or y1 == y2, (x1, y1, x2, y2)
    assert markup.count('marker-end="url(#head)"') == len(paths)
    assert markup.count('marker-start="url(#head)"') == 2  # the parity check and its legend point both ways
    assert 'class="line check"' in markup


def test_the_twelve_served_tables_hang_inside_the_duckdb_card_in_three_groups():
    markup = build()
    assert sum(len(names) for *_, names, _, _ in database_map.ORIGINS) == 12
    text = re.sub(r"<[^>]+>", " ", markup)
    for group, count in (("Modelos dbt", 9), ("Registro de cargas", 1), ("Trazas de dbt", 2)):
        assert re.search(rf"{group}\s+{count}\s", text), group
    for table in COUNTS:  # the hover lists every table with its rows
        assert f"<code>{table}</code>" in markup, table
    assert "814.610" in text and "12 tablas" in text
    assert "staging 3, intermedio 4 y marts 9" in text and "31 pruebas" in text


def test_the_sizes_come_from_the_files_and_none_is_invented():
    markup = build()
    for size in ("≈ 665 MB", "19 MB", "34 MB"):
        assert f">{size}</text>" in markup
    assert markup.count('class="size"') == 3
    assert 'class="size"' not in build(sizes={})


def test_every_box_names_a_source_file_that_exists_in_the_repository():
    for key, (what, why, produced_by) in storage_map.TIPS.items():
        assert what and why, key
        assert (ROOT / produced_by).exists(), (key, produced_by)
    for _, _, path in storage_map.REPO_FILES:
        assert (ROOT / path).exists(), path


def test_the_drawing_scales_to_its_window_and_the_smallest_text_stays_readable():
    markup = build()
    assert 'viewBox="0 0 1000 620"' in markup and 'preserveAspectRatio="xMidYMid meet"' in markup
    sizes = [float(size) for size in re.findall(r"font-size:([\d.]+)px", markup.split("</style>")[0])]
    assert min(size for size in sizes if size > 11) >= 12.5  # a 900 px window shows it at 11 px or more
    for _, _, _, x_range, _ in storage_map.ZONES:  # nothing leaves the drawing
        assert 0 <= x_range[0] < x_range[1] <= storage_map.WIDTH


def test_the_light_themes_draw_too_and_the_hover_cards_follow_the_theme():
    for mode in (charts.MODE_CORPORATE, charts.MODE_BLUE_LIGHT):
        markup = build(mode, layers={"staging": 0, "intermediate": 0, "marts": 0}, tests=0)
        assert "etl/datos.duckdb" in markup and "0 modelos" in markup
