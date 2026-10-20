"""«Mapa de la base» (D-189): every served table, from its real origin."""
import re

from bi import charts, database_map

COUNTS = {"weekly_price": 814610, "dim_product": 1609, "dim_region": 9, "dim_channel": 8, "dim_date": 250,
          "rejection": 201, "ipc_weekly": 250, "ipc_monthly": 202, "ine_ipc_source": 202, "etl_run": 5,
          "dbt_node": 50, "dbt_result": 47}


def test_the_map_names_the_twelve_tables_their_three_origins_and_both_sqlite_files():
    markup = database_map.build_map_html(charts.get_palette(charts.MODE_DARK), COUNTS,
                                         {"staging": 3, "intermediate": 4, "marts": 9}, 31)
    text = re.sub(r"<[^>]+>", " ", markup)
    for table in COUNTS:
        assert f"<code>{table}</code>" in markup, table
    assert sum(len(names) for *_, names in database_map.ORIGINS) == 12
    for origin in ("Modelos dbt", "Registro de cargas", "Trazas de dbt"):
        assert origin in text
    for store in ("etl/raw.db", "etl/datos.db", "etl/datos.duckdb", "warehouse_build.duckdb"):
        assert store in text
    assert "814.610" in text and "817.443 filas" in text and "31" in text
    assert "<script" not in markup  # CSS-only hover, as the operation center


def test_the_map_reads_in_the_light_themes_too():
    markup = database_map.build_map_html(charts.get_palette(charts.MODE_CORPORATE), COUNTS, {}, 0)
    assert "etl/datos.duckdb" in markup and "0 modelos" in markup
