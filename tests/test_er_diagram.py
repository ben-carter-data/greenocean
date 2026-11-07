"""Entity-relationship diagram (D-195): every table, key and relationship is real."""

import re
from pathlib import Path

import pytest

from bi import charts, er_diagram, queries

# region Variables
REPOSITORY = Path(__file__).resolve().parent.parent
needs_database = pytest.mark.skipif(not Path(queries.DATABASE_FILE).exists(), reason="datos.duckdb is not here")
# endregion


# region Entity-relationship diagram
@needs_database
def test_every_drawn_table_column_and_key_exists_in_the_database_with_its_real_type():
    schema = er_diagram.read_schema()
    assert set(schema) == set(er_diagram.TABLES)
    for table, keys in er_diagram.PRIMARY_KEYS.items():
        names = [name for name, _ in schema[table]]
        assert all(key in names for key in keys), table
    for child, column, parent, parent_column, *_ in er_diagram.RELATIONS:
        assert column in [name for name, _ in schema[child]], (child, column)
        assert parent_column in [name for name, _ in schema[parent]], (parent, parent_column)
    assert dict(schema["weekly_price"])["price"] == "DOUBLE" and dict(schema["etl_run"])["run_id"] == "INTEGER"


def test_the_foreign_keys_drawn_are_the_ones_dbt_tests():
    text = (REPOSITORY / "dbt" / "models" / "marts" / "schema.yml").read_text()
    tested = set(re.findall(r"to: ref\('(\w+)'\), field: (\w+)", text))
    drawn = {
        (parent, parent_column)
        for child, _, parent, parent_column, *_ in er_diagram.RELATIONS
        if child in ("weekly_price", "ipc_weekly")
    }
    assert drawn == tested  # nothing drawn that dbt does not test, nothing tested that is not drawn
    # The only relationship dbt does not test is checked by the quality page (D-171).
    assert [r[0] for r in er_diagram.RELATIONS if r[0] == "rejection"] == ["rejection"]


@needs_database
def test_no_relationship_is_broken_in_the_data():
    from bi import quality

    assert quality.check_database()["foreign_keys"] == 0
    assert quality.check_database()["duplicates"] == 0  # the composite primary key of weekly_price holds


@needs_database
def test_the_svg_has_every_table_with_its_rows_and_the_notation():
    schema = er_diagram.read_schema()
    counts = {"weekly_price": 814610, "dim_product": 1609}
    for mode in (charts.MODE_DARK, charts.MODE_CORPORATE):
        svg = er_diagram.build_er_svg(schema, counts, mode, {"weekly_price": "weekly_price · hechos"})
        for table in er_diagram.TABLES:
            assert f'class="er-table er-{table}"' in svg, table
        for table, columns in schema.items():
            assert all(f">{name}</text>" in svg for name, _ in columns), table
        assert "PK, FK" in svg and "814.610 filas" in svg and "mismo mes" in svg
        assert svg.count('class="er-link"') == len(er_diagram.RELATIONS) + 1  # plus the logical link
        assert "<script" not in svg and 'width="100%"' in svg
        assert "ine_ipc_source" in svg and 'class="er-table er-ine_ipc_source"' not in svg  # named as left out


def test_key_labels_follow_the_declared_keys():
    assert er_diagram.key_label("weekly_price", "product_id") == "PK, FK"
    assert er_diagram.key_label("weekly_price", "normalized_unit") == "PK"
    assert er_diagram.key_label("rejection", "run_id") == "FK"
    assert er_diagram.key_label("dim_product", "product") == ""
    assert er_diagram.key_label("ipc_weekly", "week_start") == "PK, FK"


def test_relations_route_without_leaving_the_drawing():
    schema = {table: [(name, "X") for name in ["a"] * 9] for table in er_diagram.TABLES}
    places = er_diagram.layout(schema)
    boxes = list(places.values())
    for index, (x, y, w, h) in enumerate(boxes):
        for x2, y2, w2, h2 in boxes[index + 1 :]:
            assert not (x < x2 + w2 and x2 < x + w and y < y2 + h2 and y2 < y + h)  # no two boxes overlap


@needs_database
def test_d474_every_table_of_the_database_is_drawn_or_named_outside_the_diagram():
    """No table of the DuckDB database goes missing from the E-R diagram: it is drawn, or its legend names it."""
    with queries.open_database(queries.DATABASE_FILE) as connection:
        tables = {row[0] for row in connection.execute("SELECT table_name FROM information_schema.tables").fetchall()}
    svg = er_diagram.build_er_svg(er_diagram.read_schema(), {}, charts.THEMES[0])
    legend = svg[svg.index("Fuera del diagrama") :]
    assert not {table for table in tables - set(er_diagram.TABLES) if table not in legend}


@needs_database
def test_d526_the_key_of_weekly_price_is_logical_and_the_legend_says_why_with_the_real_count():
    schema = er_diagram.read_schema()
    empty = er_diagram.read_empty_units()
    with queries.open_database(queries.DATABASE_FILE) as connection:
        counted = connection.execute("SELECT count(*) FROM weekly_price WHERE normalized_unit IS NULL").fetchone()[0]
    assert empty == counted > 0
    note = er_diagram.logical_key_note(empty)
    assert "clave lógica" in note and charts.format_thousands(empty) in note
    plain = er_diagram.build_er_svg(schema, {}, charts.MODE_DARK)
    svg = er_diagram.build_er_svg(schema, {}, charts.MODE_DARK, empty_units=empty)
    assert note in svg and note not in plain  # the legend grows by one line only when it has the figure
    assert svg.count("<text") == plain.count("<text") + 1
    assert height_of(svg) == height_of(plain) + 18
    assert er_diagram.key_label("weekly_price", "normalized_unit") == "PK"  # the column keeps its mark


def height_of(svg):
    return float(re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"', svg).group(1))


def test_d526_the_logical_key_reads_in_english(monkeypatch):
    from bi import i18n

    monkeypatch.setattr(i18n, "is_english", lambda: True)
    english = i18n.translate_html(f"<svg><text>{er_diagram.logical_key_note(12185)}</text></svg>")
    assert "weekly_price: logical key" in english and "rows and a strict primary key" in english
    assert "clave" not in english and "filas" not in english


# endregion
