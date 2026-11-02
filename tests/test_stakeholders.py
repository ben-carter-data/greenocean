"""«Interesados» (D-376, D-444): the interest map read from the PRD (3.4) in the reader's language: three rings
around GreenOcean, each stakeholder on its ring with why it is there and the page it opens."""

import html
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import business_analysis, dashboard, queries

DASHBOARD_FILE = str(Path(dashboard.__file__))
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")


def test_d376_the_prd_names_five_stakeholders_in_both_languages_and_each_page_exists():
    spanish, english = business_analysis.read_stakeholders("es"), business_analysis.read_stakeholders("en")
    assert [row["name"] for row in spanish] == [
        "Personas y familias",
        "Restaurantes y almacenes",
        "Mayoristas, agricultores y feriantes",
        "Periodistas y economistas",
        "Equipos técnicos y reclutadores",
    ]
    assert len(english) == len(spanish) == len(business_analysis.STAKEHOLDER_ICONS)
    for one, other in zip(spanish, english):
        assert all(one[key] and other[key] for key in ("who", "question", "decision"))
        views = [dashboard.find_menu_page(name) for name in one["pages"]]
        assert None not in views and views == [dashboard.find_menu_page(name) for name in other["pages"]]
    assert [dashboard.find_menu_page(name) for name in spanish[3]["pages"]] == [
        dashboard.PAGE_SEASONALITY,  # «Precios e inflación» opens from the Dashboard
        dashboard.PAGE_INSIGHTS,
    ]
    # The usage profiles stay beside the stakeholders, as their own table.
    assert business_analysis.read_table(business_analysis.read_section("PRD.md", "3.2", "es"))[0]["Perfil"]


def draw(profile, language="es"):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.session_state["visitor_profile"] = profile
    app.query_params.update({"vista": dashboard.PAGE_STAKEHOLDERS, "lang": language})
    return app.run()


@needs_database
def test_d444_the_page_is_the_interest_map_read_from_the_prd():
    """Three rings around GreenOcean; each stakeholder is an icon and its name on its ring, with why it is there, and
    opens its page; a page the view's menu does not lead to says it opens in the Profesional view."""
    rows = business_analysis.read_interest("es")
    assert [row["level"] for row in rows] == [0, 0, 0, 1, 1, 2, 2]
    assert [row["name"] for row in rows if row["level"] == 2] == ["ODEPA", "INE"]
    app = draw("profesional")
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert markup.count('class="im-ring ') == 3 and markup.count('class="im-node"') == 7
    assert markup.count('<a class="im-node"') == 7  # the Profesional opens every page
    for row in rows:
        assert html.escape(row["name"]) in markup and html.escape(row["why"]) in markup
    assert "Interés alto" in markup and "cuánto depende su decisión de estos datos" in markup
    assert "stk-card" not in markup  # no cards, boxes or borders: icons and names
    user = " ".join(block.value for block in draw("consulta").markdown)
    assert user.count('<a class="im-node"') == 6 and "Se abre en la vista Profesional." in user  # the technical one


@needs_database
def test_d444_the_map_reads_in_english_and_keeps_its_places():
    app = draw("profesional", "en")
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert "Technical teams and recruiters" in markup and "High interest" in markup and "Interest map" in markup
    english = business_analysis.read_interest("en")
    assert [row["level"] for row in english] == [row["level"] for row in business_analysis.read_interest("es")]
    # every name sits on its ring, and no two names of the same ring share a place
    places = {(row["level"], dashboard.interest_place(row["level"], 0)) for row in english}
    assert (
        len(
            {
                dashboard.interest_place(level, order)
                for level, angles in enumerate(dashboard.INTEREST_ANGLES)
                for order in range(len(angles))
            }
        )
        == 7
    )
    assert places
