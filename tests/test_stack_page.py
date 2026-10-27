"""«Stack y evidencia» (D-211, D-266): an architecture diagram whose logos, links and figures are read, never typed."""

import re

import duckdb

from bi import charts, project, queries, stack_page

FIGURES = {"prices": 1, "tests": 2, "loads": 3}


def build(mode=charts.MODE_DARK):
    return stack_page.build_stack_html(
        charts.get_palette(mode), FIGURES, {page: f"./{index}" for index, (*_, page) in enumerate(stack_page.STACK)}
    )


def test_the_figures_come_from_the_database_and_the_repository():
    figures = stack_page.read_figures()
    with duckdb.connect(str(queries.DATABASE_FILE), read_only=True) as connection:
        assert figures["prices"] == connection.execute("SELECT count(*) FROM weekly_price").fetchone()[0]
        assert figures["loads"] == connection.execute("SELECT count(*) FROM etl_run").fetchone()[0]
        dbt_tests = connection.execute("SELECT count(*) FROM dbt_node WHERE resource_type = 'test'").fetchone()[0]
    assert figures["tests"] == project.count_test_functions() + dbt_tests  # the same count as the CI/CD diagram
    assert project.count_test_functions() > 300


def test_the_stack_is_nine_3d_logos_plus_the_two_sources_in_every_theme():
    assert [name for _, name, *_ in stack_page.STACK] == [
        "Python",
        "SQLite",
        "Parquet",
        "dbt",
        "SQL",
        "DuckDB",
        "pytest",
        "GitHub Actions",
        "Streamlit",
    ]
    for mode in charts.THEMES:
        page = build(mode)
        assert page.count('class="logo"') == 11
        assert page.count("data:image/svg+xml;base64,") == 12  # eleven logos and the image of the lines
    assert all("<radialGradient" in stack_page.disc_svg(key) for key, *_ in stack_page.STACK)


def test_d266_every_tool_says_what_it_is_its_role_when_it_acts_and_what_it_is_connected_with():
    page = build()
    for key, name, definition, _ in stack_page.STACK:
        assert f"<b>{name}</b><small>{definition}</small>" in page
        assert stack_page.NODES[key][3] and stack_page.NODES[key][4] and stack_page.WHAT_IT_IS[key]
    assert (
        page.count("<i>Qué es</i>")
        == page.count("<i>Rol en GreenOcean</i>")
        == page.count("<i>Cuándo actúa</i>")
        == page.count("<i>Se conecta con</i>")
        == 11
    )


def test_d266_the_connections_are_read_from_the_arrows_and_every_node_has_one():
    keys = set(stack_page.NODES)
    assert keys == {key for key, *_ in stack_page.STACK} | {key for key, *_ in stack_page.SOURCES}
    for source, target, kind, *_ in stack_page.EDGES:
        assert source in keys and target in keys and kind in stack_page.COLORS
    for key in keys:
        assert stack_page.connections(key), key
    assert "→ SQLite: filas crudas" in stack_page.connections("python")
    assert "← Python: filas crudas" in stack_page.connections("sqlite")


def test_d266_every_line_bends_at_right_angles_and_ends_at_its_target():
    for source, target, _, path, *_ in stack_page.EDGES:
        assert re.fullmatch(r"M\d+ \d+( [HV]\d+)+", path), path  # only horizontal and vertical segments
        x, y = map(int, path[1:].split()[:2])
        for step in path.split()[2:]:
            x, y = (int(step[1:]), y) if step[0] == "H" else (x, int(step[1:]))
        target_x, target_y = stack_page.NODES[target][:2]
        half = (
            stack_page.SOURCE_LOGO if target in {key for key, *_ in stack_page.SOURCES} else stack_page.LOGO
        ) / 2 + 6
        # A line that arrives from below stops under the caption (name, what it is and stage).
        assert abs(x - target_x) <= half and -half <= y - target_y <= half + 64, (source, target)


def test_d266_the_explanations_stay_inside_the_stage():
    page = build()
    for key, (x, y, *_) in stack_page.NODES.items():
        assert 0 < x < stack_page.WIDTH and 0 < y < stack_page.HEIGHT
    # The lowest tool opens its explanation upward, so it never covers the legend or the figures.
    assert stack_page.tip_html(*stack_page.NODES["pytest"][:2], []).startswith('<span class="sk-tip up"')
    assert page.index('class="sk-stage"') < page.index('class="sk-legend"') < page.index('class="evidence"')
