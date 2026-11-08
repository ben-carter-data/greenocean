"""D-500: a link to the author's repository on GitHub exists only for the Autor, whatever the page."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import constants, dashboard, live_flow, page_engineering, project, queries
from tests import i18n_audit

# region Variables
DASHBOARD_FILE = str(Path(__file__).resolve().parents[1] / "bi" / "dashboard.py")
REPOSITORY = project.GITHUB_URL.split("github.com/")[-1]
OWNER = REPOSITORY.split("/")[0]
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")
PROFILES = {"Usuario": "consulta", "Profesional": "profesional"}
# endregion


# region A link to the author's repository on GitHub exists only for the Autor, whatever the page
def screens():
    """Every screen anyone else can open: the Autor's own pages only say there is no access."""
    seen, kept = set(), []
    for view, state in i18n_audit.screens():
        state = {key: value for key, value in (state or {}).items() if key != dashboard.ADMIN_UNLOCKED}
        if state.get("visitor_profile", "") is None:
            continue  # the window «Elige tu vista» is drawn over a page already in the list
        state.pop("visitor_profile", None)
        key = (view, repr(sorted(state.items(), key=str)))
        if key not in seen:
            seen.add(key)
            kept.append((view, state))
    return kept + [(dashboard.PAGE_LINKS, {})]


def everything_drawn(app):
    pieces = [element.value for element in app.markdown]
    for kind in ("html", "iframe"):
        for element in app.get(kind):
            pieces += [str(getattr(element.proto, name, "") or "") for name in ("body", "srcdoc", "src")]
    for kind in ("button", "link_button", "page_link", "download_button"):
        pieces += [str(element.proto) for element in app.get(kind)]
    pieces += [element.value for element in app.caption]
    return " ".join(pieces)


def open_view(view, profile, state=None, query=None):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.query_params.update({"vista": view, **(query or {})})
    app.session_state["visitor_profile"] = profile
    app.session_state["quality_alert_seen"] = True
    for key, value in (state or {}).items():
        app.session_state[key] = value
    app.run()
    assert not app.exception, view
    return app


def draw_links_page(state):
    """The page drawn alone, as its own address opens it."""
    script = (
        f"import sys\nsys.path.insert(0, {str(Path(DASHBOARD_FILE).parents[1])!r})\nimport streamlit as st\n"
        "from bi import dashboard\n"
        + "".join(f"st.session_state[{key!r}] = {value!r}\n" for key, value in state.items())
        + "dashboard.render_page(dashboard.PAGE_LINKS)\n"
    )
    return AppTest.from_string(script, default_timeout=60).run()


@needs_database
@pytest.mark.parametrize("name", PROFILES)
def test_d500_no_screen_shows_the_repository_to_anyone_but_the_autor(name):
    for language in ({}, {"lang": "en"}):
        for view, state in screens():
            drawn = everything_drawn(open_view(view, PROFILES[name], state, language))
            assert REPOSITORY not in drawn and f"github.com/{OWNER}" not in drawn, (name, view, state, language)
            assert OWNER not in drawn, (name, view, state, language)
            assert 'class="sidebar-github' not in drawn, (name, view, state, language)


@needs_database
def test_d500_the_autor_keeps_the_button_the_page_and_the_links():
    author = {dashboard.ADMIN_UNLOCKED: True}
    app = open_view(dashboard.PAGE_ARCHITECTURE, "profesional", author)
    drawn = everything_drawn(app)
    assert 'class="sidebar-github' in drawn and "etl/schema.sql en GitHub" in drawn
    assert project.build_github_url("etl/schema.sql") in drawn
    manual = everything_drawn(open_view(dashboard.PAGE_MANUAL, "profesional", author))
    assert f"{project.GITHUB_URL}/actions" in manual
    assert "gh-page" in everything_drawn(draw_links_page(author))


@needs_database
def test_d500_the_links_page_says_there_is_no_access_at_its_own_address():
    app = draw_links_page({})
    assert "gh-page" not in everything_drawn(app) and any(dashboard.NO_ACCESS in block.value for block in app.info)


def test_d500_a_link_in_a_document_reads_as_plain_text(monkeypatch):
    monkeypatch.setattr(dashboard.st, "session_state", {})
    text = f"| [Actions]({project.GITHUB_URL}/actions) | [ODEPA](https://www.odepa.gob.cl) |"
    linked = dashboard.link_document_views(text)
    assert "| Actions |" in linked and "github.com" not in linked and "[ODEPA](https://www.odepa.gob.cl)" in linked
    monkeypatch.setattr(dashboard.st, "session_state", {constants.ADMIN_UNLOCKED: True})
    assert f"[Actions]({project.GITHUB_URL}/actions)" in dashboard.link_document_views(text)


def test_d500_the_live_flow_gives_the_link_of_the_run_only_to_the_autor(monkeypatch):
    run = {"url": f"{project.GITHUB_URL}/actions/runs/1", "state": "completed"}
    # D-541: the live flow is read in bi/page_engineering.py, so its stand-ins go there
    monkeypatch.setattr(page_engineering, "get_secret", lambda name: "")
    monkeypatch.setattr(page_engineering, "read_flow_without_token", lambda *_: ([run], [], ""))
    monkeypatch.setattr(page_engineering, "read_flow_facts", lambda *_: {})
    monkeypatch.setattr(live_flow, "build_model", lambda *_: {"run_url": run["url"]})
    monkeypatch.setattr(dashboard.st, "session_state", {})
    assert page_engineering.read_flow_model()[0]["run_url"] is None
    monkeypatch.setattr(dashboard.st, "session_state", {constants.ADMIN_UNLOCKED: True})
    assert page_engineering.read_flow_model()[0]["run_url"] == run["url"]


def test_d500_only_the_autor_gets_a_link_from_the_shared_builder(monkeypatch):
    monkeypatch.setattr(dashboard.st, "session_state", {})
    assert dashboard.build_repository_link_html("x en GitHub", project.GITHUB_URL) == ""
    assert not any(re.search(r"github\.com", file["github"]) for file in dashboard.read_folder_files())
    monkeypatch.setattr(dashboard.st, "session_state", {constants.ADMIN_UNLOCKED: True})
    assert project.GITHUB_URL in dashboard.build_repository_link_html("x en GitHub", project.GITHUB_URL)
    assert all(file["github"].startswith(project.GITHUB_URL) for file in dashboard.read_folder_files())


def report_viewer(state):
    """Everything the viewer of a weekly quality report draws, with `state` in the session."""
    script = (
        f"import sys\nsys.path.insert(0, {str(Path(DASHBOARD_FILE).parents[1])!r})\nimport streamlit as st\n"
        "from bi import dashboard\n"
        + "".join(f"st.session_state[{key!r}] = {value!r}\n" for key, value in state.items())
        + "dashboard.show_quality_report_dialog('C7')\n"
    )
    return everything_drawn(AppTest.from_string(script, default_timeout=60).run())


@needs_database
def test_d500_the_report_viewer_links_the_sqap_only_for_the_autor():
    assert "github.com" not in report_viewer({})
    assert project.GITHUB_URL in report_viewer({dashboard.ADMIN_UNLOCKED: True})


# endregion
