"""«Dónde viven los datos» (D-190): where each store is, what it holds and why."""
import re

from bi import charts, database_map

COUNTS = {"weekly_price": 814610, "dim_product": 1609, "dim_region": 9, "dim_channel": 8, "dim_date": 250,
          "rejection": 201, "ipc_weekly": 250, "ipc_monthly": 202, "ine_ipc_source": 202, "etl_run": 5,
          "dbt_node": 50, "dbt_result": 47}


def build(mode=charts.MODE_DARK, layers=None, tests=31):
    return database_map.build_map_html(charts.get_palette(mode), COUNTS,
                                       layers or {"staging": 3, "intermediate": 4, "marts": 9}, tests)


def test_every_store_is_a_logo_with_what_it_holds_and_why_and_there_are_no_cards():
    markup = build()
    text = re.sub(r"<[^>]+>", " ", markup)
    for store in ("etl/raw.db", "capa bronce", "warehouse_build.duckdb", "etl/datos.duckdb", "etl/datos.db"):
        assert store in text, store
    # One brand mark per store, and for each one a «Qué guarda» and a «Por qué».
    assert markup.count('class="node ') == len(database_map.NODES) == 8
    assert markup.count("Qué guarda") >= len(database_map.NODES) + len(database_map.ORIGINS)
    assert markup.count("Por qué") >= len(database_map.NODES) + len(database_map.ORIGINS)
    for brand in ("sqlite", "apacheparquet", "dbt", "duckdb", "github", "python"):
        assert f'id="disc-{brand}' in markup, brand
    assert "<script" not in markup and "card" not in markup.split("</style>")[1]
    # The pipeline's steps and the panel are not repeated here.
    assert "Consumo" not in text and "Panel GreenOcean" not in text


def test_the_twelve_served_tables_come_in_three_groups_with_their_rows():
    markup = build()
    assert sum(len(names) for *_, names, _, _ in database_map.ORIGINS) == 12
    for table in COUNTS:
        assert f"<li>{table}<span>" in markup, table
    text = re.sub(r"<[^>]+>", " ", markup)
    for group in ("Modelos dbt", "Registro de cargas", "Trazas de dbt"):
        assert group in text
    assert "817.341 filas" in text and "814.610" in text
    assert "3 en tres capas" not in text and "9 modelos" not in text
    assert "staging 3, intermedio 4 y marts 9" in text and "31 pruebas" in text


def test_sqlite_appears_twice_with_different_jobs_and_the_parity_links_the_backup():
    markup = build()
    assert markup.count("Paridad") >= 1 and "Compara el respaldo SQLite con DuckDB" in markup
    assert "ETL en Python" in markup and "No se sube a GitHub" in markup
    assert "PARITY_PATH" not in markup and database_map.PARITY_PATH in markup


def test_the_light_themes_draw_too():
    markup = build(charts.MODE_CORPORATE, layers={"staging": 0, "intermediate": 0, "marts": 0}, tests=0)
    assert "etl/datos.duckdb" in markup and "0 modelos" in markup
