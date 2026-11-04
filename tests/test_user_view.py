"""D-502: the Usuario view holds only its two dashboards and «Fuentes»; nothing of the other views."""

import re
from pathlib import Path
from urllib.parse import unquote_plus

import pytest
from streamlit.testing.v1 import AppTest

from bi import dashboard, queries

DASHBOARD_FILE = str(Path(__file__).resolve().parents[1] / "bi" / "dashboard.py")
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")
MINE = {dashboard.PAGE_HOME, dashboard.PAGE_BA}


def open_user(view=None, **parameters):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PUBLIC
    app.query_params.update({**({dashboard.VIEW_PARAMETER: view} if view else {}), **parameters})
    app.session_state[dashboard.scoped(dashboard.HOME_REGION_DONE)] = True
    app.run()
    assert not app.exception, view
    return app


def everything(app):
    pieces = [element.value for element in app.markdown]
    for kind in ("html", "iframe"):
        for element in app.get(kind):
            pieces += [str(getattr(element.proto, name, "") or "") for name in ("body", "srcdoc")]
    for kind in ("button", "link_button", "page_link", "download_button"):
        pieces += [str(element.proto) for element in app.get(kind)]
    pieces += [element.value for element in app.caption]
    return " ".join(pieces)


def foreign_views(markup):
    """Every «vista=…» of the markup that is not one of the Usuario's own two pages."""
    names = {unquote_plus(value) for value in re.findall(r"vista=([^&\"'\s<>]+)", markup)}
    return {name for name in names if name not in MINE}


@needs_database
@pytest.mark.parametrize("language", [{}, {"lang": "en"}])
def test_d502_no_page_of_the_user_view_leads_anywhere_else(language):
    screens = [
        (dashboard.PAGE_HOME, {"_home_region": dashboard.ALL_VALUES, "familia": "Frutas"}),
        (dashboard.PAGE_HOME, {"_home_region": dashboard.ALL_VALUES, "familia": "Frutas", "alerta": dashboard.RISE}),
    ] + [(dashboard.PAGE_BA, {dashboard.BA_TAB_PARAMETER: tab}) for tab in dashboard.BA_TABS]
    for view, parameters in screens:
        markup = everything(open_user(view, **parameters, **language))
        assert not foreign_views(markup), (view, parameters, language, foreign_views(markup))
        assert "profile_unlock" not in markup and "Ver todo el proyecto" not in markup


@needs_database
def test_d502_an_address_of_another_view_opens_semanal():
    for view in (dashboard.PAGE_DIAGRAMS, dashboard.PAGE_ARCHITECTURE, dashboard.PAGE_RUNS, dashboard.PAGE_PRD):
        app = open_user(view)
        markup = everything(app)
        assert 'class="mock-chile-map"' in markup, view  # «Semanal», not the page it asked for
        assert dashboard.NO_ACCESS not in markup, view
        assert app.query_params.get(dashboard.VIEW_PARAMETER) in (None, dashboard.PAGE_HOME), view


@needs_database
def test_d502_the_user_table_keeps_its_figures_without_the_two_links():
    markup = everything(open_user(dashboard.PAGE_HOME, _home_region=dashboard.ALL_VALUES, familia="Frutas"))
    assert "Cobertura" in markup and "Precios nominales de ODEPA" in markup
    assert ">Calidad</a>" not in markup and ">Metodología</a>" not in markup


@needs_database
def test_d502_the_professional_view_keeps_every_page_and_both_links():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    app.query_params.update({"_home_region": dashboard.ALL_VALUES, "familia": "Frutas"})
    app.run()
    assert not app.exception
    labels = {link.proto.label for link in app.sidebar.get("page_link")}
    assert dashboard.SIDEBAR_LABELS.get(dashboard.PAGE_DIAGRAMS, dashboard.PAGE_DIAGRAMS) in labels
    markup = everything(app)
    assert ">Calidad</a>" in markup and ">Metodología</a>" in markup
