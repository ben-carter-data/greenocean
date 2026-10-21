"""Consultas SQL page: example queries, read-only guard, timeout and rendering."""
from pathlib import Path

import pytest

from bi import queries, sql_explorer

REPOSITORY = Path(__file__).resolve().parent.parent
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(),
                                    reason="etl/datos.duckdb is not built")


@needs_database
@pytest.mark.parametrize("example", sql_explorer.EXAMPLES, ids=[e[0] for e in sql_explorer.EXAMPLES])
def test_every_example_query_returns_rows(example):
    result = sql_explorer.run_user_query(example[2])
    assert len(result.rows) > 0
    # The full table (D-185) holds every price: it shows the latest 5.000 rows by design.
    assert not result.truncated or example[0] == "Tabla completa"
    assert not [column for column in result.rows.columns if column.endswith("_id")]


@pytest.mark.parametrize("sql", [
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
])
def test_forbidden_statements_are_rejected(sql):
    with pytest.raises(sql_explorer.QueryRejected) as error:
        sql_explorer.validate_query(sql)
    assert str(error.value)


@pytest.mark.parametrize("sql", [
    "SELECT 1;",
    "-- comentario\nWITH a AS (SELECT 1 AS x) SELECT x FROM a; -- fin",
    "/* bloque */ select '--no es comentario' AS texto",
    "DESCRIBE precios",
    "SHOW TABLES",
    "SUMMARIZE ipc_mensual",
])
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
def test_views_have_readable_columns_and_real_counts():
    catalog = {name: (count, [column for column, _ in columns])
               for name, _, count, columns in sql_explorer.describe_views()}
    assert set(catalog) == set(sql_explorer.VIEW_NAMES)
    count, columns = catalog["precios"]
    assert count == queries.run_sql("SELECT count(*) AS n FROM weekly_price")["n"][0]
    assert not [column for column in columns if column.endswith("_id")]
    for expected in ["semana", "familia", "producto", "variedad", "calidad", "canal", "region",
                     "unidad", "precio", "observaciones", "marca"]:
        assert expected in columns
    for _, (_, view_columns) in catalog.items():
        assert not [column for column in view_columns if column.endswith("_id")]


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
    script = (f"import sys; sys.path.insert(0, {str(REPOSITORY)!r})\n"
              "from bi import sql_explorer\n"
              "sql_explorer.show_sql_explorer_page('Claro')\n")
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
    chosen = {"familia": "Frutas", "region": "Región del Maule", "periodo": 2025, "anio_filtro": 2026,
              "producto_filtro": "Naranja", "canal_filtro": "Feria libre"}
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
        "Tabla completa", "Precio vs. época", "Canal más barato", "Inflación vs IPC",
        "Brecha mayorista", "Calendario de compra"]
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
    script = (f"import sys; sys.path.insert(0, {str(REPOSITORY)!r})\n"
              "from bi import sql_explorer\n"
              "sql_explorer.show_sql_explorer_page('Claro')\n")
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


def test_editor_and_results_take_their_grid_cell_height():
    import inspect
    source = inspect.getsource(sql_explorer.show_sql_explorer_page)
    assert 'height="stretch"' in source
    assert 'height="stretch"' in inspect.getsource(sql_explorer.show_result)
