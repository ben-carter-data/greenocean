"""D-403: every word the data brings (families, channels, qualities and units) has its English, used only to draw."""

import duckdb
import pytest

from bi import data_terms, home_mockup, i18n, queries

needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")


@needs_database
def test_d403_every_family_channel_quality_and_unit_of_the_database_has_its_english():
    with duckdb.connect(str(queries.DATABASE_FILE), read_only=True) as connection:
        values = {
            "familia": connection.execute("SELECT DISTINCT product_group FROM dim_product").fetchall(),
            "canal": connection.execute("SELECT DISTINCT channel FROM dim_channel").fetchall(),
            "calidad": connection.execute("SELECT DISTINCT quality FROM dim_product").fetchall(),
            "unidad": connection.execute(
                "SELECT DISTINCT normalized_unit FROM weekly_price WHERE normalized_unit IS NOT NULL"
            ).fetchall(),
        }
    missing = [(kind, value) for kind, rows in values.items() for (value,) in rows if not data_terms.english(value)]
    assert not missing, missing


def test_d403_the_words_change_only_for_an_english_visit_and_the_short_names_too(monkeypatch):
    assert data_terms.term("Frutas") == "Frutas" and data_terms.term(None) is None
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    assert data_terms.term("Frutas") == "Fruit" and data_terms.term("Calibre 120") == "Size 120"
    assert home_mockup.short_family("Carne de Cerdo - Ave - Cordero") == "Pork · Poultry · Lamb"
    assert data_terms.term("Tomate") == "Tomate"  # a product keeps its name
