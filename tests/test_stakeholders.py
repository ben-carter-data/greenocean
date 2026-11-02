"""«Interesados» (D-376): one card per stakeholder, read from the PRD (3.1) in the reader's language, with the pages
where the answer is; in the user view the technical card offers the professional view instead."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import business_analysis, dashboard, i18n, queries

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
def test_d376_the_professional_view_links_every_answer_and_the_user_view_offers_the_professional_one():
    app = draw("profesional")
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert markup.count('class="stk-card"') == 5 and "¿Qué alimentos están subiendo?" in markup
    links = [link.proto.label for link in app.main.get("page_link")]
    for label in (
        "Dashboard",
        "Último dato por canal",
        "Precios e inflación",
        "Insights",
        "Pipeline y linaje",
    ):
        assert label in links, label
    assert links.count("Dashboard") == 2  # people and families; restaurants and grocery stores
    assert not [button for button in app.button if str(button.key).startswith("stakeholders_switch_")]
    user = draw("consulta")
    switches = [button for button in user.button if str(button.key).startswith("stakeholders_switch_")]
    assert [button.key for button in switches] == ["stakeholders_switch_4"]  # only the technical card
    assert switches[0].label == "Cambiar a Profesional"
    switches[0].click().run()
    assert not user.exception and user.session_state["visitor_profile"] == "profesional"
    assert user.session_state["visitor_role"] == "data"


@needs_database
def test_d376_the_page_reads_in_english():
    app = draw("profesional", "en")
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert "Technical teams and recruiters" in markup and "Who they are" in markup
    assert i18n.EN["Interesados"] == "Stakeholders" and i18n.EN["Cambiar a Profesional"] == "Switch to Professional"
