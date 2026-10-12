"""Tests for the dashboard: profiles, views and footer."""
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import dashboard, queries  # noqa: E402

DASHBOARD_FILE = str(Path(dashboard.__file__))
# These tests draw the real dashboard, so they need the committed database.
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(),
                                    reason="etl/datos.db has not been built")


def run_dashboard(profile=None, view=None):
    """Draw the dashboard, optionally choosing a profile and a view first."""
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    if profile is not None:
        app.sidebar.selectbox[0].select(profile).run()
    if view is not None:
        app.sidebar.radio[0].set_value(view).run()
    return app


def get_captions(app):
    return [caption.value for caption in app.caption]


def test_each_profile_has_its_own_views():
    assert dashboard.VIEWS_BY_PROFILE[dashboard.PROFILE_ANALYST] == [
        dashboard.VIEW_MARGINS, dashboard.VIEW_CHANNELS_AND_REGIONS,
        dashboard.VIEW_SEASONALITY, dashboard.VIEW_ALERTS]
    assert dashboard.VIEWS_BY_PROFILE[dashboard.PROFILE_DATA_TEAM] == [
        dashboard.VIEW_DATA_QUALITY]


def test_every_view_has_a_function_that_draws_it():
    views = [view for views in dashboard.VIEWS_BY_PROFILE.values() for view in views]
    assert set(views) == set(dashboard.SHOW_VIEW_BY_NAME)


@needs_database
def test_changing_the_profile_changes_the_visible_views():
    app = run_dashboard()
    assert list(app.sidebar.radio[0].options) == (
        dashboard.VIEWS_BY_PROFILE[dashboard.PROFILE_ANALYST])
    app = run_dashboard(profile=dashboard.PROFILE_DATA_TEAM)
    assert list(app.sidebar.radio[0].options) == [dashboard.VIEW_DATA_QUALITY]


@needs_database
@pytest.mark.parametrize("profile, view", [
    (profile, view)
    for profile, views in dashboard.VIEWS_BY_PROFILE.items() for view in views])
def test_every_view_draws_without_errors_and_shows_the_attribution(profile, view):
    app = run_dashboard(profile, view)
    assert not app.exception
    assert [header.value for header in app.header] != []
    assert dashboard.ATTRIBUTION_TEXT in get_captions(app)
