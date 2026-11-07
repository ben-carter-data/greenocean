"""D-515: «Relaciones» in «Consultas SQL» draws how the views join, and every join it draws is real."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import charts, dashboard, er_diagram, i18n, queries, sql_explorer, sql_relations

# region Variables
DASHBOARD_FILE = str(Path(__file__).resolve().parents[1] / "bi" / "dashboard.py")
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")
# endregion


# region «Relaciones» in «Consultas SQL» draws how the views join, and every join it draws is real
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
        for statement in sql_relations.build_joins().split("\n\n"):
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
    assert sql_relations.key_label("productos", "familia") == "PK"
    assert sql_relations.key_label("precios", "semana") == sql_relations.key_label("precios", "calidad") == "PK, FK"
    assert (
        sql_relations.key_label("ipc_semanal", "semana") == "PK, FK"
        and sql_relations.key_label("precios", "anio") == ""
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


def contrast(first, second):
    def luminance(color):
        red, green, blue = (int(color[index : index + 2], 16) / 255 for index in (1, 3, 5))
        linear = [part / 12.92 if part <= 0.03928 else ((part + 0.055) / 1.055) ** 2.4 for part in (red, green, blue)]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_d517_a_colour_is_a_group_of_views_that_join_among_themselves():
    """The colours say something true: the groups are exactly the islands of the drawing."""
    joined = {view: {view} for view in sql_relations.VIEWS}
    links = [(child, parent) for child, _, parent, *_ in sql_relations.RELATIONS]
    links.append((sql_relations.LOGICAL[0], sql_relations.LOGICAL[2]))
    for first, second in links:
        merged = joined[first] | joined[second]
        for view in merged:
            joined[view] = merged
    islands = {frozenset(group) for group in joined.values()}
    assert islands == {frozenset(views) for _, views, _ in sql_relations.GROUPS}


@pytest.mark.parametrize(
    "mode",
    [charts.MODE_DARK, charts.MODE_CORPORATE, charts.MODE_BLUE_LIGHT, charts.MODE_GRAPHITE, charts.MODE_LIGHT],
)
def test_d517_each_colour_reads_on_its_card_and_differs_from_the_others(mode):
    card = charts.get_palette(mode)["card"]
    colors = [sql_relations.group_color(name, mode) for name, _, _ in sql_relations.GROUPS]
    assert len(set(colors)) == len(sql_relations.GROUPS)
    for color in colors:
        assert contrast(color, card) >= 4.5, (mode, color)
    assert charts.get_palette(mode)["rise"] not in colors  # red already means a price going up


@needs_database
def test_d517_the_drawing_paints_each_group_and_names_it_in_both_languages(monkeypatch):
    schema, counts = sql_relations.read_schema()
    svg = sql_relations.build_svg(schema, counts, charts.MODE_DARK)
    assert svg.count('class="er-group"') == len(sql_relations.GROUPS)
    assert sql_relations.GROUP_COLORS["amber"][0] in svg and sql_relations.GROUP_COLORS["pink"][0] in svg
    for _, _, text in sql_relations.GROUPS:
        assert f">{text}</text>" in svg
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    english = i18n.translate_html(svg)
    for text in ("Data: the ODEPA prices", "Load log: each load of etl_run", "dbt Core: the models and tests"):
        assert text in english, text
    assert "The eight views are in the same DuckDB database" in english and "Las ocho vistas" not in english


# The view that reads each table of the data warehouse, to compare «Relaciones» with «Modelo de datos».
TABLE_OF_VIEW = {
    "precios": "weekly_price",
    "semanas": "dim_date",
    "productos": "dim_product",
    "ipc_semanal": "ipc_weekly",
    "ipc_mensual": "ipc_monthly",
    "cargas": "etl_run",
    "rechazos": "rejection",
}


def test_d519_every_line_is_a_relation_of_the_entity_relationship_diagram():
    drawn = {(TABLE_OF_VIEW[child], TABLE_OF_VIEW[parent]) for child, _, parent, *_ in sql_relations.RELATIONS}
    assert drawn == {
        (child, parent)
        for child, _, parent, *_ in er_diagram.RELATIONS
        # no view of its own: the region and the channel are written inside precios
        if parent not in ("dim_region", "dim_channel")
    }
    ends = {(child, parent): (first, second) for child, _, parent, _, first, second, _ in er_diagram.RELATIONS}
    for child, _, parent, _, first, second, _ in sql_relations.RELATIONS:
        assert ends[(TABLE_OF_VIEW[child], TABLE_OF_VIEW[parent])] == (first, second), (child, parent)


@needs_database
def test_d519_every_key_identifies_a_row_and_each_view_has_the_rows_of_its_table():
    connection = sql_explorer.open_explorer_connection()
    try:
        for view, keys in sql_relations.KEYS.items():
            if keys:
                columns = ", ".join(keys)
                total, distinct = connection.execute(
                    f"SELECT count(*), (SELECT count(*) FROM (SELECT DISTINCT {columns} FROM {view})) FROM {view}"
                ).fetchone()
                assert total == distinct, view
        for view, table in TABLE_OF_VIEW.items():
            counted = [connection.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in (view, table)]
            assert counted[0] == counted[1], view
        # the catalogue joins by its four columns, and no price stays out
        orphans = connection.execute(
            "SELECT count(*) FROM precios AS p LEFT JOIN productos AS pr ON pr.familia = p.familia "
            "AND pr.producto = p.producto AND pr.variedad = p.variedad AND pr.calidad = p.calidad "
            "WHERE pr.producto IS NULL"
        ).fetchone()[0]
        assert orphans == 0
    finally:
        connection.close()


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


# endregion
