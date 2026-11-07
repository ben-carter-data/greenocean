"""D-510: a figure read from the base carries the mark «en vivo»; a drawing that measures nothing carries none."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import charts, dashboard, live_mark, page_bar, queries, quality_live, stack_page

# region Variables
DASHBOARD_FILE = str(Path(__file__).resolve().parents[1] / "bi" / "dashboard.py")
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")
LIVE_PAGES = [
    dashboard.PAGE_ARCHITECTURE,
    dashboard.PAGE_DIAGRAMS,
    dashboard.PAGE_OPERATIONS,
    dashboard.PAGE_STACK,
    dashboard.PAGE_BA,
]
STILL_PAGES = [dashboard.PAGE_APP_MAP, dashboard.PAGE_SECURITY, dashboard.PAGE_GIT, dashboard.PAGE_METHOD]
# endregion


# region A figure read from the base carries the mark «en vivo»
def drawn(app):
    pieces = [block.value for block in app.markdown]
    for kind in ("html", "iframe"):
        for element in app.get(kind):
            pieces += [str(getattr(element.proto, name, "") or "") for name in ("body", "srcdoc")]
    return " ".join(pieces)


def open_page(view, **state):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    app.session_state["quality_alert_seen"] = True
    for key, value in state.items():
        app.session_state[key] = value
    app.query_params[dashboard.VIEW_PARAMETER] = view
    app.run()
    assert not app.exception, view
    return app


def test_d510_the_mark_beats_once_a_second_and_rests_when_the_reader_asks_for_less_motion():
    markup = live_mark.build_html("SELECT count(*) FROM weekly_price")
    assert 'class="live-mark"' in markup and live_mark.TEXT in markup
    assert 'title="SELECT count(*) FROM weekly_price"' in markup and "<i aria-hidden" in markup
    for dark in (True, False):
        css = live_mark.build_css(dark)
        assert "animation:live-mark-beat 1s ease-in-out infinite" in css
        assert "prefers-reduced-motion: reduce" in css and "animation:none" in css
        assert (live_mark.GREEN_DARK if dark else live_mark.GREEN_LIGHT) in css
    # the mark travels with the bar, the stack and the quality drawing, each with its own stylesheet
    for css in (
        page_bar.build_css(charts.get_palette(charts.MODE_DARK)),
        stack_page.build_css(charts.get_palette(charts.MODE_DARK)),
        quality_live.build_css(charts.get_palette(charts.MODE_DARK)),
    ):
        assert "@keyframes live-mark-beat" in css


def test_d510_the_bar_row_adds_the_mark_only_when_told_what_was_read():
    assert "live-mark" not in page_bar.build_info_html("T", "d", [("<b>1</b>", "one")])
    row = page_bar.build_info_html("T", "d", [("<b>1</b>", "one")], live="etl_run")
    assert row.index('class="page-chip"') < row.index('class="live-mark"') and 'title="etl_run"' in row


@needs_database
@pytest.mark.parametrize("view", LIVE_PAGES)
def test_d510_every_page_whose_figures_come_from_the_base_shows_the_mark(view):
    markup = drawn(open_page(view))
    assert live_mark.TEXT in markup, view


@needs_database
@pytest.mark.parametrize("view", STILL_PAGES)
def test_d510_a_drawing_that_measures_nothing_shows_no_mark(view):
    markup = drawn(open_page(view, admin_unlocked=view in dashboard.AUTHOR_ONLY_PAGES))
    assert live_mark.TEXT not in markup, view


@needs_database
def test_d510_the_mark_reads_in_english():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    app.session_state["quality_alert_seen"] = True
    app.query_params.update({dashboard.VIEW_PARAMETER: dashboard.PAGE_ARCHITECTURE, "lang": "en"})
    app.run()
    assert not app.exception
    markup = drawn(app)
    assert "live · read from the database on opening" in markup and live_mark.TEXT not in markup


# endregion
