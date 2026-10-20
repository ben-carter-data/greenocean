"""Entity-relationship diagram (D-195): every table, key and relationship is real."""
import re
from pathlib import Path

import pytest

from bi import charts, er_diagram, queries

REPOSITORY = Path(__file__).resolve().parent.parent
needs_database = pytest.mark.skipif(not Path(queries.DATABASE_FILE).exists(), reason="datos.duckdb is not here")


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
    drawn = {(parent, parent_column) for child, _, parent, parent_column, *_ in er_diagram.RELATIONS
             if child in ("weekly_price", "ipc_weekly")}
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
        for x2, y2, w2, h2 in boxes[index + 1:]:
            assert not (x < x2 + w2 and x2 < x + w and y < y2 + h2 and y2 < y + h)  # no two boxes overlap
