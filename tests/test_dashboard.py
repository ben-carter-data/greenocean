"""Tests for the dashboard: profiles, pages, key figures and footer."""
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from bi import dashboard, queries  # noqa: E402

DASHBOARD_FILE = str(PROJECT_DIR / "bi" / "dashboard.py")
# These tests draw the real dashboard, so they need the committed database.
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(),
                                    reason="etl/datos.db has not been built")
ALL_PAGES = sorted({page for pages in dashboard.PAGES_BY_PROFILE.values() for page in pages})


def draw_page(title):
    """Draw one page alone, the way the navigation does."""
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              f"from bi import dashboard\ndashboard.render_page({title!r})\n")
    return AppTest.from_string(script, default_timeout=60).run()


def test_each_profile_has_its_own_pages():
    assert dashboard.PAGES_BY_PROFILE[dashboard.PROFILE_ANALYST] == [
        dashboard.PAGE_OVERVIEW, dashboard.PAGE_PROJECT, dashboard.PAGE_MARGINS,
        dashboard.PAGE_CHANNELS_AND_REGIONS, dashboard.PAGE_SEASONALITY,
        dashboard.PAGE_ALERTS, dashboard.PAGE_ARCHITECTURE, dashboard.PAGE_CONTROL]
    assert dashboard.PAGES_BY_PROFILE[dashboard.PROFILE_DATA_TEAM] == [
        dashboard.PAGE_OVERVIEW, dashboard.PAGE_PROJECT, dashboard.PAGE_ARCHITECTURE,
        dashboard.PAGE_CONTROL, dashboard.PAGE_DATA_QUALITY]


def test_every_page_has_a_function_an_icon_and_an_address():
    assert set(ALL_PAGES) == set(dashboard.SHOW_PAGE_BY_TITLE)
    assert set(ALL_PAGES) == set(dashboard.PAGE_ICONS) == set(dashboard.PAGE_PATHS)


def test_product_description_leaves_out_unspecified_parts():
    assert dashboard.describe_product({"product": "Tomate", "variety": "Larga vida",
                                       "quality": "Primera"}) == "Tomate Larga vida · Primera"
    assert dashboard.describe_product({"product": "Marraqueta",
                                       "variety": dashboard.UNSPECIFIED,
                                       "quality": dashboard.UNSPECIFIED}) == "Marraqueta"


def test_weekly_change_compares_the_last_two_weeks():
    weeks = pd.to_datetime(["2026-09-28", "2026-10-05"])
    latest, change = dashboard.calculate_weekly_change(pd.Series([1000.0, 1100.0], weeks))
    assert latest == 1100
    assert change == pytest.approx(10)


def test_change_chip_is_red_for_rises_and_blue_for_falls():
    assert "chip-rise" in dashboard.build_change_chip(5.8)
    assert "▲ +5,8 %" in dashboard.build_change_chip(5.8)
    assert "chip-fall" in dashboard.build_change_chip(-2.0)


def test_durations_are_written_for_people():
    assert dashboard.format_duration(pd.Timedelta(seconds=57)) == "57 s"
    assert dashboard.format_duration(pd.Timedelta(seconds=125)) == "2 min 5 s"


@needs_database
def test_the_whole_app_opens_without_errors():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not app.exception
    assert list(app.sidebar.selectbox[0].options) == list(dashboard.PAGES_BY_PROFILE)


@needs_database
@pytest.mark.parametrize("title", ALL_PAGES)
def test_every_page_draws_without_errors_and_shows_the_attribution(title):
    app = draw_page(title)
    assert not app.exception
    assert dashboard.ATTRIBUTION_TEXT in [caption.value for caption in app.caption]


def test_hover_hint_is_plain_text_and_escaped():
    icon = dashboard.build_hint_icon('**1,46** = "más caro"')
    assert "**" not in icon
    assert 'data-hint="1,46 = &quot;más caro&quot;"' in icon


def test_change_chip_explains_itself_when_the_mouse_passes_over_it():
    chip = dashboard.build_change_chip(-14.1, unit="pts")
    assert 'title="Bajó 14,1 puntos porcentuales frente a la semana anterior' in chip


def test_every_business_question_points_to_a_page_or_is_pending():
    for question, page, state, scope in dashboard.BUSINESS_QUESTIONS:
        assert state in dashboard.QUESTION_STATES
        assert page in dashboard.SHOW_PAGE_BY_TITLE or state == "pending"
