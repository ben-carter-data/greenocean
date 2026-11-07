"""Consultas SQL page: example queries, read-only guard, timeout and rendering."""

import re
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from bi import charts, dashboard, i18n, queries, sql_explorer

# region Constants
REPOSITORY = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = str(REPOSITORY / "bi" / "dashboard.py")
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="etl/datos.duckdb is not built")
# endregion


# region Queries allowed and refused
@needs_database
@pytest.mark.parametrize("example", sql_explorer.EXAMPLES, ids=[e[0] for e in sql_explorer.EXAMPLES])
def test_every_example_query_returns_rows(example):
    result = sql_explorer.run_user_query(example[2])
    assert len(result.rows) > 0
    # The full table (D-185) holds every price: it shows the latest 5.000 rows by design.
    assert not result.truncated or example[0] == "Tabla completa"
    assert not [column for column in result.rows.columns if column.endswith("_id")]


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO dim_region VALUES (99, 'x')",
        "DROP TABLE weekly_price",
        "ATTACH 'otra.db' AS otra",
        "COPY weekly_price TO 'salida.csv'",
        "PRAGMA version",
        "SET enable_external_access = true",
        "SELECT 1; SELECT 2",
        "SELECT 1; DROP TABLE weekly_price",
        "SELECT * FROM read_csv('http://example.com/datos.csv')",
        "SELECT * FROM read_parquet('etl/bronze/*.parquet')",
        "SELECT * FROM 'https://example.com/datos.csv'",
        "WITH a AS (SELECT 1) DELETE FROM dim_region",
        "CREATE TABLE t AS SELECT 1",
        "INSTALL httpfs",
        "EXPORT DATABASE 'copia'",
        "-- solo un comentario",
        "",
    ],
)
def test_forbidden_statements_are_rejected(sql):
    with pytest.raises(sql_explorer.QueryRejected) as error:
        sql_explorer.validate_query(sql)
    assert str(error.value)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1;",
        "-- comentario\nWITH a AS (SELECT 1 AS x) SELECT x FROM a; -- fin",
        "/* bloque */ select '--no es comentario' AS texto",
        "DESCRIBE precios",
        "SHOW TABLES",
        "SUMMARIZE ipc_mensual",
    ],
)
def test_read_only_statements_are_accepted(sql):
    assert sql_explorer.validate_query(sql)


@needs_database
def test_external_access_is_disabled_at_the_engine():
    connection = sql_explorer.open_explorer_connection()
    try:
        with pytest.raises(Exception):
            connection.execute("SELECT * FROM read_csv('etl/schema.sql')").fetchall()
        with pytest.raises(Exception):
            connection.execute("SET enable_external_access = true")
    finally:
        connection.close()


@needs_database
def test_slow_query_is_interrupted():
    # count(*) over range() is answered from metadata, so the slow query sums values.
    with pytest.raises(sql_explorer.QueryTimeout):
        sql_explorer.run_user_query("SELECT sum(range % 7) FROM range(10_000_000_000)", timeout=1)


@needs_database
def test_result_is_limited_and_flagged():
    result = sql_explorer.run_user_query("SELECT * FROM precios", row_limit=50)
    assert len(result.rows) == 50 and result.truncated


@needs_database
def test_downloads_produce_files():
    rows = sql_explorer.run_user_query(sql_explorer.EXAMPLES[0][2]).rows
    assert sql_explorer.to_parquet_bytes(rows)[:4] == b"PAR1"
    assert sql_explorer.to_csv_bytes(rows).startswith(b"\xef\xbb\xbf")
    for _, _, sql in sql_explorer.EXPORTS[1:]:
        assert len(sql_explorer.export_csv(sql)) > 10


@needs_database
def test_page_renders_and_runs_an_example():
    from streamlit.testing.v1 import AppTest

    script = (
        f"import sys; sys.path.insert(0, {str(REPOSITORY)!r})\n"
        "from bi import sql_explorer\n"
        "sql_explorer.show_sql_explorer_page('Claro')\n"
    )
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    assert app.text_area[0].value == sql_explorer.EXAMPLES[0][2]
    app.button(key="sqlx_chip_2").click().run()
    assert app.text_area[0].value == sql_explorer.EXAMPLES[2][2]
    app.button(key="sqlx_run").click().run()
    assert not app.exception
    assert len(app.dataframe) == 1 and len(app.dataframe[0].value) > 0
    app.text_area[0].input("DROP TABLE weekly_price").run()
    app.button(key="sqlx_run").click().run()
    assert app.error and "Solo se permiten" in app.error[0].value
    page_text = " ".join(str(element.value) for element in app.markdown).lower()
    assert "robot" not in page_text


def test_d185_every_query_runs_with_and_without_filters():
    chosen = {
        "familia": "Frutas",
        "region": "Región del Maule",
        "periodo": 2025,
        "anio_filtro": 2026,
        "producto_filtro": "Naranja",
        "canal_filtro": "Feria libre",
    }
    for index, (title, _, _, names) in enumerate(sql_explorer.TEMPLATES):
        for values in (None, chosen):
            sql = sql_explorer.render_example(index, values)
            assert "{" not in sql, title
            assert not sql_explorer.run_user_query(sql).rows.empty, title
        # A filter never leaks into a query that does not offer it.
        if "region" not in names:
            assert "Región del Maule" not in sql_explorer.render_example(index, chosen), title


def test_d185_the_full_table_comes_first_and_the_council_picks_follow():
    assert [title for title, *_ in sql_explorer.TEMPLATES] == [
        "Tabla completa",
        "Precio vs. época",
        "Canal más barato",
        "Inflación vs IPC",
        "Brecha mayorista",
        "Calendario de compra",
    ]
    rows = sql_explorer.run_user_query(sql_explorer.EXAMPLES[0][2]).rows
    for column in ("familia", "producto", "variedad", "calidad", "canal", "region", "precio", "precio_real"):
        assert column in rows.columns
    filtered = sql_explorer.render_example(0, {"familia": "Carne bovina", "anio_filtro": 2026})
    assert "WHERE p.familia = 'Carne bovina'\n  AND year(p.semana) = 2026" in filtered
    # Every decision query ends with a reading in words, and compares real pesos where it compares time.
    for index in range(1, len(sql_explorer.TEMPLATES)):
        sql = sql_explorer.EXAMPLES[index][2]
        assert "lectura" in sql or "mes_mas_barato" in sql or "ahorro_pct" in sql
    assert "factor_real" in sql_explorer.EXAMPLES[1][2] and "factor_real" in sql_explorer.EXAMPLES[5][2]


@needs_database
def test_d185_one_click_writes_the_sql_and_a_filter_narrows_it():
    from streamlit.testing.v1 import AppTest

    script = (
        f"import sys; sys.path.insert(0, {str(REPOSITORY)!r})\n"
        "from bi import sql_explorer\n"
        "sql_explorer.show_sql_explorer_page('Claro')\n"
    )
    app = AppTest.from_string(script, default_timeout=60).run()
    app.button(key="sqlx_chip_0").click().run()
    assert not app.exception and len(app.dataframe) == 1
    app.selectbox(key="sqlx_param_familia").select("Carne bovina").run()
    assert not app.exception
    assert "p.familia = 'Carne bovina'" in app.text_area[0].value
    assert set(app.dataframe[0].value["familia"]) == {"Carne bovina"}


def test_d182_the_explorer_lists_the_real_tables_and_one_opens():
    tables = {name: count for name, count, _ in sql_explorer.describe_tables()}
    assert {"weekly_price", "dim_product", "dim_region", "dim_channel", "dim_date"} <= set(tables)
    assert tables["weekly_price"] > 100_000
    rows = sql_explorer.run_user_query("SELECT *\nFROM main.dim_region\nLIMIT 100").rows
    assert "region_id" in rows.columns and len(rows) == tables["dim_region"]
    tab = sql_explorer.build_tab_html(1)
    assert "precio_vs_epoca.sql" in tab and "sqlx-info" in tab and sql_explorer.EXAMPLES[1][1] in tab


def test_d516_the_grid_takes_what_the_window_leaves_and_a_few_rows_keep_their_height():
    long_sql, short_sql = sql_explorer.EXAMPLES[0][2], "SELECT 1"
    assert sql_explorer.results_height(100) == "stretch"
    assert sql_explorer.results_height(2) == sql_explorer.GRID_ROW * 3 + 3
    for sql in (short_sql, long_sql):
        offset = sql_explorer.AROUND_GRID + sql_explorer.editor_height(sql)
        css = sql_explorer.build_grid_css(sql)
        assert f"calc(100vh - {offset}px)" in css and f"{sql_explorer.GRID_FLOOR}px" in css
    assert sql_explorer.editor_height(short_sql) < sql_explorer.editor_height(long_sql)
    # the fixed height that left a band empty under the grid is gone
    assert "698px" not in sql_explorer.build_css(charts.get_palette(charts.MODE_DARK))


def english_page(**state):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    app.query_params.update({dashboard.VIEW_PARAMETER: dashboard.PAGE_SQL, "lang": "en"})
    for key, value in state.items():
        app.session_state[key] = value
    app.run()
    assert not app.exception
    return app


def test_d516_every_comment_of_every_query_has_its_english(monkeypatch):
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    for index, (title, _, template, _) in enumerate(sql_explorer.TEMPLATES):
        spanish = sql_explorer.COMMENT_PATTERN.findall(template)
        assert spanish, title
        for comment in spanish:
            assert comment.rstrip("\n") in i18n.EN, comment
        written = sql_explorer.render_example(index)
        comments = sql_explorer.COMMENT_PATTERN.findall(written)
        assert not re.search(r"[áéíóúñ¿¡]| (de|del|la|el|que|por|cada|en) ", " ".join(comments)), comments
        # only the comments change: without them the query is the same one
        strip = lambda sql: sql_explorer.COMMENT_PATTERN.sub("", sql)  # noqa: E731
        assert strip(written) == strip(sql_explorer.EXAMPLES[index][2]), title
    assert "since January 2022" in sql_explorer.render_example(3, {"periodo": sql_explorer.SINCE_2022})
    assert "year 2025" in sql_explorer.render_example(3, {"periodo": 2025})


def test_d516_the_list_of_examples_never_freezes_the_language_of_the_first_visit(monkeypatch):
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    frozen = [
        (title, question, sql_explorer.render_example(index, read=str))
        for index, (title, question, _, _) in enumerate(sql_explorer.TEMPLATES)
    ]
    assert frozen == sql_explorer.EXAMPLES
    assert sql_explorer.EXAMPLES[0][2].startswith("-- Tabla completa")


@needs_database
def test_d516_the_page_in_english_writes_comments_summary_and_messages_in_english():
    # the result in the session, as a run leaves it: AppTest cannot rerun a page with translated selectors
    app = english_page(sqlx_result=sql_explorer.run_user_query(sql_explorer.EXAMPLES[0][2]))
    assert app.text_area[0].value.startswith("-- Full table: one weekly price")
    written = " ".join(block.value for block in app.caption)
    assert re.search(r"[\d,]+ rows · \d+ columns · [\d,]+ ms · showing the first 5,000", written), written
    markup = " ".join(block.value for block in app.markdown)
    assert "query.sql" in markup or "full_table.sql" in markup
    assert "filas" not in written and "columnas" not in written


@needs_database
def test_d516_the_grid_shows_the_names_the_query_wrote_and_the_week_as_a_date():
    app = english_page(sqlx_result=sql_explorer.run_user_query(sql_explorer.EXAMPLES[0][2]))
    columns = list(app.dataframe[0].value.columns)
    assert columns[:3] == ["semana", "familia", "producto"], columns  # never a half-translated «week»
    assert app.text_area[0].value.count("p.semana") >= 1


def test_d516_a_message_of_a_rejected_query_reads_in_english(monkeypatch):
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    for sql, expected in (
        ("", "Write a SELECT query"),
        ("DROP TABLE precios", "Only read queries are allowed"),
        ("SELECT 1; SELECT 2", "Run one query at a time"),
        ("SELECT * FROM read_csv('a.csv')", "Queries work only on the tables"),
    ):
        assert expected in sql_explorer.outcome_of(sql), sql
    assert sql_explorer.outcome_of("SELECT no_such FROM nothing").startswith("DuckDB returned an error")


def test_d516_every_text_of_the_templates_and_the_views_reads_in_english(monkeypatch):
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    for title, question, *_ in sql_explorer.TEMPLATES:
        assert i18n.translate_text(question) != question, question
        assert i18n.translate_text(title) != title, title
    for name, description, _ in sql_explorer.VIEWS:
        assert i18n.translate_text(description) != description, name
    for script in sql_explorer.SCRIPT_NAMES.values():
        assert i18n.tr(script) != script, script


# endregion


# region The answers of the PRD, recomputed another way (D-244)
def example_sql(title):
    return next(sql for name, _, sql in sql_explorer.EXAMPLES if name == title)


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


@needs_database
def test_p3_the_wholesale_gap_query_matches_a_recomputation_in_pandas():
    """P-3: the consumer over the wholesale price, paired by product, unit, region and week."""
    result = sql_explorer.run_user_query(example_sql("Brecha mayorista")).rows
    assert not result.empty
    latest = pd.Timestamp(
        sql_explorer.read_view("SELECT max(semana) AS s FROM precios WHERE fuente = 'mayorista'")["s"][0]
    )
    for row in result.head(3).itertuples():
        key = " AND ".join(
            f"{column} = {literal(getattr(row, column))}"
            for column in ("familia", "producto", "variedad", "calidad", "unidad")
        )
        prices = sql_explorer.read_view(
            f"SELECT region, semana, fuente, precio FROM precios WHERE {key} AND marca = 'SIN_MARCA'"
        )
        prices["semana"] = pd.to_datetime(prices["semana"])
        consumer = prices[prices["fuente"] == "consumidor"]
        wholesale = prices[prices["fuente"] == "mayorista"]
        pairs = consumer.merge(wholesale, on=["region", "semana"], suffixes=("_c", "_m"))
        gap = pairs["precio_c"] / pairs["precio_m"] - 1
        now = pairs["semana"] > latest - pd.Timedelta(days=28)
        year_ago = pairs["semana"].between(latest - pd.Timedelta(days=392), latest - pd.Timedelta(days=364))
        assert row.regiones == pairs.loc[now, "region"].nunique()
        assert abs(row.brecha_actual_pct - gap[now].median() * 100) <= 0.051
        assert abs(row.brecha_hace_un_anio_pct - gap[year_ago].median() * 100) <= 0.051


@needs_database
def test_p2_the_price_for_the_season_query_matches_a_recomputation_in_pandas():
    """P-2: the last four ISO weeks against the same weeks of earlier years, series by series, in real pesos."""
    result = sql_explorer.run_user_query(example_sql("Precio vs. época")).rows
    assert not result.empty
    weeks = sql_explorer.read_view("SELECT semana, anio_iso, semana_iso FROM semanas")
    weeks["semana"] = pd.to_datetime(weeks["semana"])
    latest = pd.Timestamp(
        sql_explorer.read_view("SELECT max(semana) AS s FROM precios WHERE fuente = 'consumidor'")["s"][0]
    )
    latest_year = int(weeks.loc[weeks["semana"] == latest, "anio_iso"].iloc[0])
    season = set(weeks.loc[weeks["semana"].between(latest - pd.Timedelta(days=21), latest), "semana_iso"])
    factors = sql_explorer.read_view("SELECT semana, factor_real FROM ipc_semanal")
    factors["semana"] = pd.to_datetime(factors["semana"])
    for row in result.head(3).itertuples():
        key = " AND ".join(
            f"{column} = {literal(getattr(row, column))}"
            for column in ("familia", "producto", "variedad", "calidad", "unidad")
        )
        prices = sql_explorer.read_view(
            f"SELECT canal, region, semana, precio FROM precios WHERE {key} AND fuente = 'consumidor' AND marca = 'SIN_MARCA'"
        )
        prices["semana"] = pd.to_datetime(prices["semana"])
        prices = prices.merge(weeks, on="semana").merge(factors, on="semana")
        prices = prices[prices["semana_iso"].isin(season)]
        prices["real"] = prices["precio"] * prices["factor_real"]
        series = []
        for _, group in prices.groupby(["canal", "region"]):
            now = group.loc[group["anio_iso"] == latest_year, "real"]
            before = group[group["anio_iso"] < latest_year]
            if len(now) and before["anio_iso"].nunique() >= 2:
                series.append(now.mean() / before["real"].mean() - 1)
        assert row.series_comparadas == len(series)
        assert abs(row.diferencia_real_pct - pd.Series(series).median() * 100) <= 0.051


# endregion


# region Views and their columns
@needs_database
def test_views_have_readable_columns_and_real_counts():
    catalog = {
        name: (count, [column for column, _ in columns]) for name, _, count, columns in sql_explorer.describe_views()
    }
    assert set(catalog) == set(sql_explorer.VIEW_NAMES)
    count, columns = catalog["precios"]
    assert count == queries.run_sql("SELECT count(*) AS n FROM weekly_price")["n"][0]
    assert not [column for column in columns if column.endswith("_id")]
    for expected in [
        "semana",
        "familia",
        "producto",
        "variedad",
        "calidad",
        "canal",
        "region",
        "unidad",
        "precio",
        "observaciones",
        "marca",
    ]:
        assert expected in columns
    for _, (_, view_columns) in catalog.items():
        assert not [column for column in view_columns if column.endswith("_id")]


# endregion
