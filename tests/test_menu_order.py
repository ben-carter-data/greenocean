"""The section «Negocio · BA y BI» in a visitor's reading order (D-378): who it is for and the analysis first (BA and BSA),
then the prices (BI); the app map lists the same pages in the same order."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import app_map, dashboard, i18n, queries

DASHBOARD_FILE = str(Path(dashboard.__file__))
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")
ORDER = [
    dashboard.PAGE_STAKEHOLDERS,
    dashboard.PAGE_ANALYSIS,
    dashboard.PAGE_CHANNELS,
    dashboard.PAGE_SEASONALITY,  # D-398
    dashboard.PAGE_INSIGHTS,
]


def draw(profile, view, language="es"):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.session_state["visitor_profile"] = profile
    app.query_params.update({"vista": view, "lang": language})
    return app.run()


def test_d378_the_section_lists_who_it_is_for_and_the_analysis_before_the_prices():
    # D-442: the Dashboard leads the menu as a tile of its own; the section follows it.
    assert dashboard.MENU_BLOCKS[0] == ("dashboard", "Dashboard", [dashboard.HOME_PAGE])
    assert dashboard.MENU_BLOCKS[1][0] == "negocio" and dashboard.MENU_BLOCKS[1][1] == "Negocio · BA y BI"
    assert dashboard.MENU_BLOCKS[1][2] == ORDER
    assert dashboard.MENU_ORDER[:6] == [dashboard.HOME_PAGE] + ORDER  # the path and the footer follow it (D-250)
    labels = [dashboard.SIDEBAR_LABELS.get(view, view) for view in ORDER]
    assert labels == [
        "Interesados",
        "Análisis de negocio y sistemas",
        "Último dato por canal",
        "Precios e inflación",
        "Insights",
    ]
    for label in labels:
        assert i18n.EN[label] or i18n.PAGES[label], label


@needs_database
def test_d378_every_view_reads_the_section_in_that_order_and_the_user_view_has_only_it():
    for language, expected in (
        (
            "es",
            [
                "Dashboard",
                "Interesados",
                "Análisis de negocio y sistemas",
                "Último dato por canal",
                "Precios e inflación",
                "Insights",
            ],
        ),
        (
            "en",
            [
                "Dashboard",
                "Stakeholders",
                "Business and systems analysis",
                "Latest data by channel",
                "Prices and inflation",
                "Insights",
            ],
        ),
    ):
        user = draw("consulta", dashboard.PAGE_STAKEHOLDERS, language)
        assert not user.exception
        assert [
            link.proto.label for link in user.sidebar.get("page_link")
        ] == expected  # the user view: only this block
        professional = draw("profesional", dashboard.PAGE_STAKEHOLDERS, language)
        assert not professional.exception
        # D-442: the Dashboard tile first, then the section
        assert [link.proto.label for link in professional.sidebar.get("page_link")][:6] == expected


@needs_database
def test_d378_the_main_pages_of_the_section_have_no_route_footer_and_the_next_section_follows_the_last_one():
    def footer(view):
        app = draw("profesional", view)
        assert not app.exception
        return [
            link.proto.label for link in app.main.get("page_link") if link.proto.label.startswith(("←", "Siguiente"))
        ]

    for view in ORDER:  # a main page is one screen with one thin bar (D-264, D-267): the menu is its route
        assert view in dashboard.OVERVIEW_CLASS_BY_VIEW and footer(view) == [], view
    # The next section still follows the last page of this one, so the previous/next footers of the rest do not change.
    assert dashboard.MENU_ORDER[5:7] == [dashboard.PAGE_INSIGHTS, dashboard.PAGE_DIAGRAMS]
    assert footer(dashboard.HOME_PAGE) == []


@needs_database
def test_d378_choosing_a_view_opens_the_dashboard():
    assert dashboard.MENU_ORDER[0] == dashboard.HOME_PAGE  # D-442: the Dashboard leads the menu
    app = draw(None, dashboard.PAGE_INSIGHTS)
    assert app.get("dialog")
    app.button(key="profile_choose_consulta").click().run()
    assert not app.exception and not app.get("dialog")
    assert [
        box for box in app.selectbox if box.key == "home_products_channel"
    ]  # D-371: the Dashboard, not the first link


def test_d378_the_app_map_names_the_menu_pages_in_the_menu_order():
    pages = next(text for tool, text in app_map.NODES["streamlit"][8] if tool == "Páginas")
    menu = [
        view
        for view in dashboard.MENU_ORDER
        if view not in dashboard.AUTHOR_ONLY_PAGES and view != dashboard.PAGE_FOLDER
    ]
    expected = [
        dashboard.SIDEBAR_LABELS.get(view, view) for view in menu
    ]  # D-398: «Precios e inflación» is in the menu
    positions = [pages.index(label) for label in expected]
    assert positions == sorted(positions), expected  # every page is named, in the menu's order
    assert pages in i18n.PAGES  # and the map's sentence has its English


def test_d387_the_readme_lists_every_page_of_the_menu_in_the_menu_order():
    readme = (Path(dashboard.__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
    line = next(line for line in readme.splitlines() if line.startswith("Páginas del panel"))
    labels = [
        dashboard.SIDEBAR_LABELS.get(view, view)
        for key, _, pages in dashboard.MENU_BLOCKS
        if key not in ("fuentes", "documentos")
        for view in pages
    ]
    positions = [line.index(label) for label in labels]
    assert positions == sorted(positions), labels
    assert "carpeta de documentos" in line and "Precios e inflación" in line


DEVOPS = [view for key, _, pages in dashboard.MENU_BLOCKS if key == "devops" for view in pages]
DEVOPS_LABELS = [dashboard.SIDEBAR_LABELS.get(view, view) for view in DEVOPS]


@pytest.mark.parametrize("profile", ["consulta", "profesional"])
def test_d420_no_page_of_devops_is_reached_by_the_user_or_the_professional(profile):
    assert (
        set(DEVOPS)
        == {dashboard.PAGE_RUNS, dashboard.PAGE_ACTIONS, dashboard.PAGE_CONFIG}
        == (dashboard.AUTHOR_ONLY_PAGES)
    )
    for view in DEVOPS:  # by the address: the page says there is no access and draws nothing of its own
        app = AppTest.from_file(str(DASHBOARD_FILE), default_timeout=90)
        app.session_state["visitor_profile"] = profile
        app.query_params.update({"vista": view})
        app.run()
        assert not app.exception
        assert [item.value for item in app.info] == [dashboard.NO_ACCESS], view
        markup = " ".join(block.value for block in app.main.markdown)
        assert 'class="page-bar-main"' not in markup and 'class="cf-card' not in markup, view  # no page of its own
        assert not {"runs_run_now", "runs_reload", "author_access_close"} & {str(b.key) for b in app.button}, view
        labels = [link.proto.label for link in app.sidebar.get("page_link")]  # and the menu has no DevOps
        assert not set(DEVOPS_LABELS) & set(labels) and "DevOps y seguridad" not in [
            button.label for button in app.sidebar.button
        ]
    if profile == "profesional":  # security reads in «Stack y evidencia», with no secret value
        app = AppTest.from_file(str(DASHBOARD_FILE), default_timeout=90)
        app.session_state["visitor_profile"] = profile
        app.query_params.update({"vista": dashboard.PAGE_SECURITY})
        app.run()
        markup = " ".join(block.value for block in app.markdown)
        assert not app.exception and "Stack y evidencia › Arquitectura de seguridad" in markup
        assert dashboard.SIDEBAR_LABELS.get(dashboard.PAGE_SECURITY, dashboard.PAGE_SECURITY) in [
            link.proto.label for link in app.sidebar.get("page_link")
        ]


def test_d420_the_author_sees_the_whole_devops_section():
    app = AppTest.from_file(str(DASHBOARD_FILE), default_timeout=90)
    app.session_state["visitor_profile"] = "profesional"
    app.session_state["admin_unlocked"] = True
    app.session_state["quality_alert_seen"] = True
    app.query_params.update({"vista": dashboard.PAGE_HOME})
    app.run()
    labels = [link.proto.label for link in app.sidebar.get("page_link")]
    assert [label for label in labels if label in DEVOPS_LABELS] == [
        "Centro de operación",
        "GitHub Actions",
        "Configuración",
    ]
