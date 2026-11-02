"""Weeks as their Monday-to-Sunday range (D-374): «19–25 oct», «26 oct – 1 nov», in Spanish and in English; the next
week in the Dashboard's header; no screen names a week by its Monday alone."""

import re
from datetime import date
from pathlib import Path

import pytest

from bi import home_mockup, i18n, queries, weeks

ROOT = Path(__file__).resolve().parent.parent
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")


def test_d374_a_week_inside_one_month_reads_as_its_range():
    assert weeks.week_range("2026-10-19") == "19–25 oct"
    assert weeks.week_range(date(2026, 10, 19), year=True) == "19–25 oct 2026"
    assert weeks.week_range("2026-10-19", english=True) == "Oct 19–25"
    assert weeks.week_range("2026-10-19", year=True, english=True) == "Oct 19–25, 2026"
    assert i18n.localize_date("19–25 oct") == "Oct 19–25"
    assert weeks.monday("2026-10-19 00:00:00") == date(2026, 10, 19)  # inside, the week is still its Monday


def test_d374_a_week_that_crosses_into_the_next_month_names_both_months():
    assert weeks.week_range("2026-10-26") == "26 oct – 1 nov"
    assert weeks.week_range("2026-10-26", english=True) == "Oct 26 – Nov 1"
    assert weeks.week_range("2025-12-29", year=True) == "29 dic – 4 ene 2026"
    assert weeks.week_range("2025-12-29", year=True, english=True) == "Dec 29 – Jan 4, 2026"
    # The English the page translation writes is the same as the one the code writes.
    for value in ("2026-10-26", "2025-12-29", "2026-09-28", "2026-10-05"):
        for year in (False, True):
            assert i18n.localize_date(weeks.week_range(value, year)) == weeks.week_range(value, year, english=True)


def test_d374_the_next_week_is_worked_out_from_the_week_shown():
    assert weeks.next_week("2026-10-19") == date(2026, 10, 26)
    upcoming = weeks.week_range(weeks.next_week("2026-10-19"))
    bar = home_mockup.dashboard_bar(
        "Negocio · BA y BI › Dashboard", "19–25 oct 2026", [], [], None, next_label=upcoming
    )
    assert '>19–25 oct<' in bar and '<span class="home-next-week"' in bar
    assert "Próxima semana: 26 oct – 1 nov" in bar
    assert i18n.lookup("Próxima semana: 26 oct – 1 nov") == "Next week: Oct 26 – Nov 1"
    assert i18n.lookup("Próxima semana: 19–25 oct") == "Next week: Oct 19–25"


def test_d374_the_notices_tables_and_reports_name_the_week_by_its_range():
    from bi import dashboard, quality_view

    assert dashboard.describe_late_sources("SOURCE_LATE: wholesale 2026-10-26") == (
        "ODEPA aún no publica la semana 26 oct – 1 nov (mayorista)"
    )
    assert (
        i18n.lookup("ODEPA aún no publica la semana 26 oct – 1 nov")
        == "ODEPA has not published the week of Oct 26 – Nov 1 yet"
    )
    assert quality_view.format_week("2026-10-12") == "12–18 oct 2026"
    page = home_mockup.products_table([], "12–18 oct", "5–11 oct")
    assert "Precio medio<br>5–11 oct" in page and "Precio medio<br>12–18 oct" in page
    # No screen writes a week as «semana del 19-10» any more; the data keep the Monday as the week's key.
    for path in sorted((ROOT / "bi").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"[Ss]emana del (\{|\d)", text), path.name


@needs_database
def test_d374_the_panorama_shows_its_week_and_the_next_one_as_ranges_in_both_languages():
    from streamlit.testing.v1 import AppTest

    from bi import dashboard

    week = dashboard.read_latest_week()
    following = weeks.next_week(week)
    for language, english in (("es", False), ("en", True)):
        app = AppTest.from_file(str(ROOT / "bi" / "dashboard.py"), default_timeout=90)
        app.session_state["visitor_profile"] = "consulta"
        app.query_params.update({"vista": dashboard.HOME_PAGE, "lang": language})
        app.run()
        assert not app.exception
        markup = " ".join(block.value for block in app.markdown)
        assert f">{weeks.week_range(week, english=english)}<" in markup
        upcoming = ("Next week: " if english else "Próxima semana: ") + weeks.week_range(following, english=english)
        assert upcoming in markup, language


def test_d375_the_next_week_never_widens_the_bar_and_the_section_name_gives_way_first():
    from bi import charts

    bar = home_mockup.dashboard_bar(
        "Negocio · BA y BI › Dashboard",
        "19–25 oct 2026",
        [],
        [],
        "Región de Arica y Parinacota",
        next_label="26 oct – 1 nov",
    )
    path = bar[bar.index('class="home-bar-path"') : bar.index('class="home-bar-title"')]
    assert '<span class="home-bar-section">Negocio · BA y BI › </span><b>Dashboard</b>' in path
    assert 'class="home-next-week"' in path  # under the page's name, beside the chip: it never widens the chip
    assert (
        '<span class="home-chip-week">19–25 oct</span><span class="home-chip-place"> · Arica y Parinacota</span>' in bar
    )
    css = home_mockup.style(charts.THEMES[0], charts.get_palette(charts.THEMES[0]))
    for rule in (
        "container-type:inline-size",
        "@container (max-width:400px) {.home-bar-section {display:none;}}",
        ".home-bar-where {display:grid;grid-template-columns:minmax(0,auto) auto;",
        "grid-template-columns:auto minmax(0,auto)",
        ".stApp .st-key-home_bar {flex-wrap:nowrap!important;}",  # D-407: one line at any width
    ):
        assert rule in css, rule
