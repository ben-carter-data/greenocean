"""The section «Negocio · BA y BI» (D-378, D-456): its three dashboards as tiles, the Dashboard, «Último dato por canal»
and «Análisis BA y BI», which gathers the history of the prices and the former pages in its tabs; the app map lists the
same pages in the same order."""

import hashlib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import app_map, dashboard, i18n, queries

DASHBOARD_FILE = str(Path(dashboard.__file__))
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")
# D-456: the section is its three dashboards, as tiles; what were its other pages are tabs of the third.
TILES = [dashboard.HOME_PAGE, dashboard.PAGE_CHANNELS, dashboard.PAGE_BA]
TABS = ["Mensual", "Histórico", "Precios e inflación", "Insights", "Interesados", "Método"]  # D-457


def draw(profile, view, language="es"):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.session_state["visitor_profile"] = profile
    app.query_params.update({"vista": view, "lang": language})
    return app.run()


def test_d456_the_section_is_its_three_dashboards_and_the_analysis_gathers_the_rest_in_tabs():
    assert dashboard.MENU_BLOCKS[0] == ("negocio", "Negocio · BA y BI", TILES)
    assert dashboard.DASHBOARD_TILES == TILES
    assert dashboard.MENU_ORDER[:3] == TILES  # the path and the footer follow it (D-250)
    assert dashboard.BA_TABS == TABS
    # each former page opens its own tab, from its old address or from a link of a document
    assert dashboard.BA_TAB_OF_VIEW == {
        dashboard.PAGE_SEASONALITY: "Precios e inflación",
        dashboard.PAGE_INSIGHTS: "Insights",
        dashboard.PAGE_STAKEHOLDERS: "Interesados",
        dashboard.PAGE_ANALYSIS: "Método",
    }
    for label in TABS + [dashboard.PAGE_BA]:
        assert i18n.EN.get(label) or i18n.PAGES.get(label), label


@needs_database
def test_d378_every_view_reads_the_section_in_that_order_and_the_user_view_has_only_it():
    for language, expected in (
        ("es", ["Semanal", "Último dato por canal", "Análisis BA y BI"]),  # D-459
        ("en", ["Weekly", "Latest data by channel", "BA and BI analysis"]),
    ):
        user = draw("consulta", dashboard.PAGE_BA, language)
        assert not user.exception
        assert [
            link.proto.label for link in user.sidebar.get("page_link")
        ] == expected  # the user view: only this block
        professional = draw("profesional", dashboard.PAGE_BA, language)
        assert not professional.exception
        assert [link.proto.label for link in professional.sidebar.get("page_link")][:3] == expected


@needs_database
def test_d378_the_main_pages_of_the_section_have_no_route_footer_and_the_next_section_follows_the_last_one():
    def footer(view):
        app = draw("profesional", view)
        assert not app.exception
        return [
            link.proto.label for link in app.main.get("page_link") if link.proto.label.startswith(("←", "Siguiente"))
        ]

    for view in TILES:  # a main page is one screen with one thin bar (D-264, D-267): the menu is its route
        assert view in dashboard.OVERVIEW_CLASS_BY_VIEW and footer(view) == [], view
    # The next section still follows the last page of this one, so the previous/next footers of the rest do not change.
    assert dashboard.MENU_ORDER[2:4] == [dashboard.PAGE_BA, dashboard.PAGE_DIAGRAMS]


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
    ]  # D-456: «Análisis BA y BI» names its tabs beside it
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


@needs_database
def test_d459_the_three_dashboards_sit_under_their_title_and_the_old_address_opens_semanal():
    # The three pages of «Negocio · BA y BI» are dashboards: they go under the title «Dashboards», and the weekly one,
    # which was called «Dashboard» on its own, is «Semanal». An old address or bookmark still opens it.
    assert dashboard.PAGE_HOME == "Semanal" and dashboard.RETIRED_VIEWS["Dashboard"] == dashboard.HOME_PAGE
    assert i18n.EN["Semanal"] == "Weekly" and i18n.EN["Dashboards"] == "Dashboards"
    for language, labels, title in (
        ("es", ["Semanal", "Último dato por canal", "Análisis BA y BI"], "Dashboards"),
        ("en", ["Weekly", "Latest data by channel", "BA and BI analysis"], "Dashboards"),
    ):
        app = draw("profesional", "Dashboard", language)
        assert not app.exception
        assert [link.proto.label for link in app.sidebar.get("page_link")][:3] == labels
        assert f'<p class="nav-subtitle">{title}</p>' in " ".join(block.value for block in app.sidebar.markdown)
        assert f"<b>{labels[0]}</b>" in " ".join(block.value for block in app.main.markdown)  # the page it opened


@needs_database
def test_d462_a_dashboard_opens_with_the_menu_folded_and_its_button_beating_in_green():
    script = dashboard.DASHBOARD_FOLD_SCRIPT
    assert 'sidebar.dataset.collapsed === "false"' in script  # how Streamlit marks the menu today
    assert "window.__goFoldedView === view" in script  # once per page opened: a menu opened by hand stays open
    assert "<" not in script.replace("<script>", "").replace("</script>", "").replace("tries++ <", "")
    for view, folds in ((dashboard.HOME_PAGE, True), (dashboard.PAGE_BA, True), (dashboard.PAGE_DIAGRAMS, False)):
        app = draw("profesional", view)
        assert not app.exception
        scripts = [str(block.proto.body) for block in app.get("html") if "__goFoldedView" in str(block.proto.body)]
        key = hashlib.sha1(view.encode()).hexdigest()[:10]  # the page as a neutral key, not a Spanish name
        assert len(scripts) == 1 and f'const view = "{key}";' in scripts[0], view
        assert ('"yes" === "yes"' in scripts[0]) is folds, view
        beat = "animation:go-menu-beat" in " ".join(block.value for block in app.markdown)
        assert beat is folds, view
