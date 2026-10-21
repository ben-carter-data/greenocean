"""«Stack y evidencia» (D-211): logos, links and figures read, never typed."""
import duckdb

from bi import charts, queries, stack_page


def test_the_figures_come_from_the_database_and_the_repository():
    figures = stack_page.read_figures()
    with duckdb.connect(str(queries.DATABASE_FILE), read_only=True) as connection:
        assert figures["prices"] == connection.sql("SELECT count(*) FROM weekly_price").fetchone()[0]
        assert figures["loads"] == connection.sql("SELECT count(*) FROM etl_run").fetchone()[0]
        dbt_tests = connection.sql("SELECT count(*) FROM dbt_node WHERE resource_type = 'test'").fetchone()[0]
    assert figures["tests"] == stack_page.count_pytest_tests() + dbt_tests
    assert stack_page.count_pytest_tests() > 300


def test_the_stack_is_nine_3d_logos_in_every_theme():
    addresses = {page: f"./{index}" for index, (*_, page) in enumerate(stack_page.STACK)}
    assert [name for _, name, *_ in stack_page.STACK] == ["Python", "SQLite", "Parquet", "dbt", "SQL", "DuckDB",
                                                          "pytest", "GitHub Actions", "Streamlit"]
    for mode in charts.THEMES:
        page = stack_page.build_stack_html(charts.get_palette(mode), {"prices": 1, "tests": 2, "loads": 3}, addresses)
        assert page.count('class="logo"') == 9 and page.count("data:image/svg+xml;base64,") == 9
    assert all("<radialGradient" in stack_page.disc_svg(key) for key, *_ in stack_page.STACK)


def test_d212_the_hover_band_keeps_the_figures_clear():
    page = stack_page.build_stack_html(charts.get_palette(charts.MODE_DARK), {"prices": 1, "tests": 2, "loads": 3},
                                       {page: "./" for *_, page in stack_page.STACK})
    assert page.index('class="stack"') < page.index('class="hint"') < page.index('class="evidence"')
    assert ".stack:has(a:hover) + .hint" in page
