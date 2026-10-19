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
    assert not result.truncated
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


def test_d180_every_template_runs_with_other_parameters():
    values = {"anio": 2025, "producto": "Asado Carnicero", "canal": "Carnicería"}
    for index, (title, _, template, names) in enumerate(sql_explorer.TEMPLATES):
        sql = sql_explorer.render_example(index, values)
        assert "{" not in sql, title
        assert not sql_explorer.run_user_query(sql).rows.empty, title
        if "anio" in names:
            assert "2025" in sql and "2026" not in sql, title


@needs_database
def test_d180_one_click_writes_the_sql_and_runs_it_with_the_chosen_product():
    from streamlit.testing.v1 import AppTest
    script = (f"import sys; sys.path.insert(0, {str(REPOSITORY)!r})\n"
              "from bi import sql_explorer\n"
              "sql_explorer.show_sql_explorer_page('Claro')\n")
    app = AppTest.from_string(script, default_timeout=60).run()
    ficha = next(i for i, t in enumerate(sql_explorer.TEMPLATES) if t[0] == "Ficha de un producto")
    app.button(key=f"sqlx_chip_{ficha}").click().run()
    assert not app.exception and len(app.dataframe) == 1
    app.selectbox(key="sqlx_param_producto").select("Asado Carnicero").run()
    assert not app.exception
    assert "'Asado Carnicero'" in app.text_area[0].value
    assert set(app.dataframe[0].value["canal"]) >= {"Carnicería"}


def test_d181_five_questions_and_the_season_compares_real_prices():
    assert [title for title, *_ in sql_explorer.TEMPLATES] == [
        "¿Está caro para la época?", "Más que la inflación este año", "Sobre la inflación desde 2022",
        "Ficha de un producto", "Más alzas que bajas del año"]
    sql = sql_explorer.render_example(0, {"producto": "Tomate"})
    assert "factor_real" in sql
    verdicts = set(sql_explorer.run_user_query(sql).rows["veredicto"])
    assert verdicts and verdicts <= {"Más caro que cualquier año anterior", "Más barato que cualquier año anterior",
                                     "Caro para la época", "Barato para la época", "Normal para la época"}
