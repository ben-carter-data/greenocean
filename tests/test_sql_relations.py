"""D-515: «Relaciones» in «Consultas SQL» draws how the views join, and every join it draws is real."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import charts, dashboard, i18n, queries, sql_explorer, sql_relations

DASHBOARD_FILE = str(Path(__file__).resolve().parents[1] / "bi" / "dashboard.py")
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")


@needs_database
def test_d515_every_view_key_and_join_column_exists_in_the_views():
    schema, counts = sql_relations.read_schema()
    assert set(schema) == set(sql_relations.VIEWS) == set(sql_explorer.VIEW_NAMES)
    columns = {view: {name for name, _ in rows} for view, rows in schema.items()}
    for view, keys in sql_relations.KEYS.items():
        assert set(keys) <= columns[view], view
    for child, child_column, parent, parent_column, *_ in sql_relations.RELATIONS:
        assert child_column in columns[child] and parent_column in columns[parent], (child, parent)
    child, child_column, parent, parent_column, *_ = sql_relations.LOGICAL
    assert child_column in columns[child] and parent_column in columns[parent]
    assert counts["precios"] > 100_000 and counts["semanas"] > 100


@needs_database
def test_d515_no_join_is_broken_in_the_data():
    connection = sql_explorer.open_explorer_connection()
    try:
        for child, child_column, parent, parent_column, _, parent_end, _ in sql_relations.RELATIONS:
            orphans = connection.execute(
                f"SELECT count(*) FROM {child} AS c LEFT JOIN {parent} AS p ON p.{parent_column} = c.{child_column} "
                f"WHERE p.{parent_column} IS NULL AND c.{child_column} IS NOT NULL"
            ).fetchone()[0]
            if parent_end == "one":
                assert orphans == 0, (child, parent)
        # the written joins run as they are, on the views
        for statement in sql_relations.build_joins().split("\n\n")[1:]:
            lines = [line.split("--")[0].rstrip() for line in statement.splitlines() if not line.startswith("--")]
            connection.execute("SELECT count(*) " + " ".join(lines))
    finally:
        connection.close()


@needs_database
def test_d515_the_drawing_has_every_view_every_join_and_the_legend():
    schema, counts = sql_relations.read_schema()
    svg = sql_relations.build_svg(schema, counts, charts.MODE_DARK)
    assert svg.count('class="er-table') == len(sql_relations.VIEWS)
    assert svg.count('class="er-link"') == len(sql_relations.RELATIONS) + 1  # plus the logical link
    for view in sql_relations.VIEWS:
        assert f">{view}</text>" in svg
    for child, child_column, parent, parent_column, *_ in sql_relations.RELATIONS:
        assert f"{child}.{child_column} → {parent}.{parent_column}" in svg
    assert "PK: las columnas que identifican una fila" in svg and 'width="100%"' in svg and "<script" not in svg
    assert (
        sql_relations.key_label("productos", "familia") == "PK" and sql_relations.key_label("precios", "semana") == "FK"
    )


@needs_database
def test_d516_the_drawing_is_landscape_with_no_box_on_another_and_no_line_through_a_box():
    schema, counts = sql_relations.read_schema()
    places = sql_relations.layout(schema)
    assert set(places) == set(sql_relations.VIEWS)
    width = max(x + w for x, _, w, _ in places.values()) + sql_relations.MARGIN
    height = max(y + h for _, y, _, h in places.values()) + sql_relations.MARGIN
    assert width / height > 2  # a window wider than tall shows it whole
    boxes = list(places.items())
    for index, (name, (x, y, w, h)) in enumerate(boxes):
        for other, (ox, oy, ow, oh) in boxes[index + 1 :]:
            assert x + w <= ox or ox + ow <= x or y + h <= oy or oy + oh <= y, (name, other)
    svg = sql_relations.build_svg(schema, counts, charts.MODE_DARK)
    assert f'viewBox="0 0 {width} {height}"' in svg
    # the two views one above the other are joined by a bracket, out of their left edges
    path, child_edge, parent_edge = sql_relations.route(places, "rechazos", "cargas", 400, 200)
    assert child_edge == parent_edge == "left" and f"H{places['rechazos'][0] - sql_relations.BRACKET}" in path


@needs_database
def test_d516_the_names_of_the_views_and_columns_stay_as_code_in_english(monkeypatch):
    schema, counts = sql_relations.read_schema()
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    svg = i18n.translate_html(sql_relations.build_svg(schema, counts, charts.MODE_DARK))
    for view in sql_relations.VIEWS:
        assert f">{view}</text>" in svg, view
    assert ">semana</text>" in svg and ">familia</text>" in svg and ">estado</text>" in svg
    assert ">prices</text>" not in svg and ">week</text>" not in svg and ">loads</text>" not in svg
    assert "PK: the columns that identify a row" in svg and "same month" in svg
    assert 'font-size="10.5"' in svg and " rows</text>" in svg and " filas</text>" not in svg


def test_d516_the_menu_folds_on_entering_the_sql_page_and_the_svg_never_passes_the_window():
    assert dashboard.PAGE_SQL in dashboard.FOLD_MENU_VIEWS
    css = sql_explorer.build_css(charts.get_palette(charts.MODE_DARK))
    assert ".sqlx-relations svg" in css and "max-height:calc(100vh - 230px)" in css


def test_d515_the_joins_name_every_relation_and_every_text_has_its_english():
    for child, _, parent, *_ in sql_relations.RELATIONS:
        joins = sql_relations.build_joins()
        assert f"JOIN {parent} AS" in joins and f"FROM {child} AS" in joins
    for *_, meaning in sql_relations.RELATIONS:
        assert f"{{}} · {meaning}" in i18n.PAGES, meaning
    assert sql_relations.LOGICAL[-1] in i18n.PAGES
    for text in ("Relaciones", "Relaciones entre las vistas"):
        assert text in i18n.EN, text
    for _, comment in sql_relations.JOIN_LINES:
        if comment:
            assert comment in i18n.EN, comment  # D-443: the comments read in English too


@needs_database
def test_d515_the_button_opens_the_window_with_the_drawing_and_the_joins():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    app.query_params[dashboard.VIEW_PARAMETER] = dashboard.PAGE_SQL
    app.run()
    assert not app.exception
    app.button(key="sqlx_relations").click().run()
    assert not app.exception and app.get("dialog")
    markup = " ".join(block.value for block in app.markdown)
    assert 'class="sqlx-relations"' in markup and "Relaciones entre las vistas de Consultas SQL" in markup
    assert [tab.label for tab in app.tabs][-2:] == ["Diagrama", "JOIN listos para copiar"]  # D-516
    assert any("JOIN semanas AS s ON s.semana = p.semana" in block.value for block in app.code)
