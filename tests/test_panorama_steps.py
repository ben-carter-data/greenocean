"""The reading order of the Dashboard (D-352, D-372): numbered panels, «Todo Chile», locks in every view, the search,
trends and the basket."""

import re
import statistics
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import charts, dashboard, home_mockup, queries

PROJECT_DIR = Path(__file__).resolve().parent.parent
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")
LINK = (
    "ORIGINAL_COMPONENT = st.components.v2.component\n"
    "st.components.v2.component = lambda name, js=None: (\n"
    "    lambda key=None, on_link_change=None: __import__('types').SimpleNamespace(link={link!r}))\n"
)  # the stub is undone at the end of the script: AppTest runs in this process and the module is shared


def draw(profile, link=None, query=None, state=None):
    script = (
        f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\nimport streamlit as st\nfrom bi import dashboard\n"
        f"st.session_state['visitor_profile'] = {profile!r}\n"
        + "".join(f"st.session_state[{key!r}] = {value!r}\n" for key, value in (state or {}).items())
        + "".join(f"st.query_params[{key!r}] = {value!r}\n" for key, value in (query or {}).items())
        + (LINK.format(link=link) if link else "")
        + "try:\n"
        + f"    dashboard.render_page({dashboard.PAGE_HOME!r})\n"
        + "finally:\n"
        + ("    st.components.v2.component = ORIGINAL_COMPONENT\n" if link else "    pass\n")
    )
    return AppTest.from_string(script, default_timeout=90).run()


def page(app):
    return " ".join(block.value for block in app.markdown)


@needs_database
def test_d352_in_the_user_view_panels_two_and_three_start_locked_with_no_region_or_family_chosen():
    app = draw("consulta")
    text = page(app)
    assert not app.exception
    for step in (  # D-494: the channel, optional, is step 2
        "1</b><span>Elige una región",
        "2</b><span>Elige un canal",
        "3</b><span>Elige una familia",
        "4</b><span>Productos",
    ):
        assert step in text, step
    assert (
        "Elige primero una región" in text and "Elige primero una familia" in text
    )  # both phrases, with their padlock
    assert text.count('class="mock-lock"') == 2  # D-494: the channels wait dimmed; the families' padlock says why
    assert ".st-key-home_channels" in text and ".st-key-home_families" in text and ".st-key-home_products" in text
    assert "saturate(.4)" in text
    assert re.search(r'mock-movement-row (rise|fall|neutral) selected', text) is None  # no family preselected
    assert "Clic en una región o en <b>Todo Chile</b>" in text and 'class="mock-all-chile"' in text
    assert all(box.disabled for box in app.text_input if box.key == "home_products_search")  # nothing to type yet


@needs_database
def test_d352_todo_chile_opens_step_two_a_family_opens_step_three_and_an_open_step_never_locks_again():
    region = draw("consulta", link="?_home_region=Todas&_home_week=2026-10-12&_home_step=region")
    text = page(region)
    assert region.session_state["home_region_done"] and "Elige primero una región" not in text
    assert "Elige primero una familia" in text  # step 3 still waits
    assert "mock-unlock" not in text or region.session_state.get("home_flash") is None  # the light is shown once
    family = draw("consulta", link="?_home_region=Todas&_home_week=2026-10-12&familia=Frutas&_home_step=family")
    text = page(family)
    assert family.session_state["home_family_done"] and "Elige primero" not in text
    assert 'class="mock-lock"' not in text  # D-446: the Dashboard keeps the three panels, nothing folds
    assert re.search(r"mock-movement-row (rise|fall|neutral) selected", text) and 'class="mock-chosen"' not in text
    # Changing the region afterwards keeps both open: the flags stay in the session.
    again = draw(
        "consulta",
        state={"home_region_done": True, "home_family_done": True},
        query={"_home_region": "Región Metropolitana de Santiago"},
    )
    assert 'class="mock-lock"' not in page(again) and not again.exception


@needs_database
def test_d372_the_professional_and_the_author_wait_for_each_step_like_the_user():
    for state in ({}, {"admin_unlocked": True, "quality_alert_seen": True}):
        app = draw("profesional", state=state)
        text = page(app)
        assert not app.exception and "1</b><span>Elige una región" in text and "4</b><span>Productos" in text
        assert text.count('class="mock-lock"') == 2 and "Elige primero una región" in text and "saturate(.4)" in text
        assert all(box.disabled for box in app.text_input if box.key == "home_products_search")
        assert re.search(r"mock-movement-row (rise|fall|neutral) selected", text) is None  # no family preselected
    done = draw("profesional", state={"home_region_done": True, "home_family_done": True})
    assert 'class="mock-lock"' not in page(done)
    assert not any(box.disabled for box in done.text_input if box.key == "home_products_search")


def test_d372_each_step_opens_with_its_number_in_a_big_circle_and_a_readable_text():
    from bi import i18n_en

    assert home_mockup.step_chip(3) == '<span class="mock-step"><b>3</b><span>Elige una familia</span></span>'
    css = home_mockup.style(charts.THEMES[0], charts.get_palette(charts.THEMES[0]))
    assert "width:30px;height:30px;border-radius:50%" in css and "font-size:13px;font-weight:500" in css
    for text in home_mockup.STEP_TEXTS.values():
        assert text in i18n_en.PAGES, text


def test_d450_the_search_glows_in_fluorescent_green_apart_from_the_blue_of_falls():
    for theme in charts.THEMES:
        palette = charts.get_palette(theme)
        css = home_mockup.style(theme, palette)
        light = home_mockup.SEARCH_DARK if palette["base"] == "dark" else home_mockup.SEARCH_LIGHT
        assert light.lower() in {"#39ff14", "#00a83a"}  # D-450: fluorescent green, deeper on white
        assert light.lower() not in {"#0868c5", "#83baff", palette["fall"].lower()}  # never the blue of «bajó»
        assert f'[data-testid="stTextInputRootElement"] {{border:2px solid {light}!important;min-height:38px;' in css
        assert f"{{color:{light}!important;fill:{light}!important;font-size:20px!important;}}" in css  # the magnifier
        assert "animation:mock-search-glow 2.4s ease-in-out infinite" in css
        assert (
            ':focus-within [data-testid="stTextInputRootElement"]' in css and "input:not(:placeholder-shown)" in css
        )  # click, letter
        assert (
            '@media (prefers-reduced-motion:reduce) {.st-key-home_families,.st-key-home_products,'
            '.st-key-home_products_search [data-testid="stTextInputRootElement"] {animation:none!important;}}' in css
        )
    palette = charts.get_palette(charts.THEMES[0])
    stopped = '.st-key-home_products_search [data-testid="stTextInputRootElement"] {animation:none!important;}'
    assert stopped in dashboard.build_steps_css(palette, True, True, None, searched=True)
    assert stopped not in dashboard.build_steps_css(palette, True, True, None)


def test_d450_the_whole_basket_row_is_the_median_of_every_comparable_price_and_is_ticked_like_a_box():
    rows = [
        {"product_group": "Frutas", "variation": 0.04},
        {"product_group": "Frutas", "variation": -0.02},
        {"product_group": "Verduras", "variation": 0.01},
        {"product_group": "Verduras", "variation": None},
        {"product_group": "Carnes", "variation": float("nan")},
    ]
    assert home_mockup.basket_median(rows) == statistics.median([0.04, -0.02, 0.01])
    assert home_mockup.basket_median([]) is None
    html = home_mockup.family_movement(
        rows, lambda family: "#" + family, None, "todo Chile", basket=(0.01, [1.0, 2.0, 3.0]), basket_link="#Todas"
    )
    basket = html[html.index("mock-basket") :]
    assert "Toda la canasta" in html and basket.index("Toda la canasta") < basket.index("mock-movement-row rise")
    row = html[html.rindex("<", 0, html.index("mock-basket")) : html.index("Toda la canasta")]
    # D-450: a box to tick, which chooses every family at once and opens the products
    assert row.startswith("<a") and 'href="#Todas"' in row and 'role="checkbox" aria-checked="false"' in row
    assert html.count("mock-spark") >= 1 and "<polyline" in html
    ticked = home_mockup.family_movement(
        rows,
        lambda family: "#" + family,
        home_mockup.ALL_FAMILIES,
        "todo Chile",
        basket=(0.01, [1.0, 2.0]),
        basket_link="#",
    )
    assert 'aria-checked="true"' in ticked and 'mock-basket-art checked' in ticked


@needs_database
def test_d450_ticking_the_whole_basket_opens_every_product_of_the_week():
    app = draw("consulta", link="?_home_region=Todas&_home_week=2026-10-12&familia=Todas&_home_step=family")
    text = page(app)
    assert not app.exception and app.session_state["home_family_done"] and 'class="mock-lock"' not in text
    assert '<span class="mock-products-family">Toda la canasta</span>' in text
    families = set(re.findall(r'<a class="mock-movement-row (?:rise|fall|neutral)', text))
    assert families and 'aria-checked="true"' in text


@needs_database
def test_d352_the_trends_are_calculated_from_the_weekly_variations_last_eight_weeks():
    version = dashboard.get_database_version()
    variations = dashboard.read_cached_all_variations(version)
    week = str(max(variations["week_start"]).date())
    by_family, basket = dashboard.read_home_trends(version, week)
    weeks = sorted(variations["week_start"].unique())[-8:]
    assert 2 <= len(basket) <= 8 and by_family
    valid = dashboard.overview.comparable(variations[variations["week_start"] == weeks[-1]])
    assert basket[-1] == pytest.approx(valid["variation"].median() * 100)  # the last point is this week's basket median
    group = next(iter(by_family))
    last = valid[valid["product_group"] == group]["variation"]
    if len(last):
        assert by_family[group][-1] == pytest.approx(last.median() * 100)
    assert all(len(series) <= 8 for series in by_family.values())
    app = draw("profesional")
    assert page(app).count('class="mock-spark') >= len(by_family)  # one little line per family, plus the basket's


FAMILY_CLICK = "?_home_region=Todas&_home_week=2026-10-12&familia=Frutas&_home_step=family"


@needs_database
def test_d446_the_dashboard_never_folds_its_steps_when_a_family_is_chosen():
    # D-408 folds the steps only on a channel page; the Dashboard keeps the map, the families and the table together.
    app = draw("profesional", state={"home_region_done": True, "home_family_done": True}, link=FAMILY_CLICK)
    text = page(app)
    assert not app.exception
    assert 'class="mock-chile-map"' in text and re.search(r"mock-movement-row (rise|fall|neutral) selected", text)
    assert 'class="mock-products-table"' in text and 'class="mock-chosen"' not in text
    assert not {"home_change_region", "home_change_family"} & {str(button.key) for button in app.button}


def test_d447_the_dashboard_table_has_a_one_line_header_and_scrolls_inside_one_screen():
    table = home_mockup.products_table([], "26 oct – 1 nov", "19–25 oct")
    header = table.split("<thead>", 1)[1].split("</thead>", 1)[0]
    assert "<br>" not in header and "mock-two-lines" not in header  # one line, the panel's own word hidden
    assert '<span class="mock-th-word">Precio</span> 19–25 oct' in header and "Regiones ↑ / ↓</th>" in header
    css = home_mockup.style(charts.THEMES[0], charts.get_palette(charts.THEMES[0]))
    # One screen (D-309): the table fills the products panel down to the bottom of the window and scrolls by itself,
    # with no figure fixed in advance, so a channel with two families fills it too (D-452). Measured with Playwright at
    # 1440 x 790, 1280 x 800, 1440 x 900 and 1920 x 1000 on the Dashboard and on a channel.
    assert ".st-key-home_overview {height:auto!important;min-height:calc(100vh - 136px);}" in css
    assert (
        ".st-key-home_overview .mock-products-table {flex:1 1 0;min-height:110px!important;max-height:none!important;}"
        in css
    )
    assert ".st-key-home_overview .mock-th-word {display:none;}" in css


def test_d450_the_products_head_is_one_thin_line_and_the_families_stay_inside_their_panel():
    css = home_mockup.style(charts.THEMES[0], charts.get_palette(charts.THEMES[0]))
    # Measured with Playwright at 1280 x 684 and 1440 x 790: no family row passes the panel's edge.
    assert (
        ".stApp .st-key-home_overview .greenocean-mockup .mock-movement-row {grid-template-columns:42px minmax(140px,1.3fr)"
        in css
    )
    assert (
        ".st-key-home_overview .mock-products-slim .mock-kicker,.st-key-home_overview .mock-products-slim h2 {display:none!important;}"
        in css
    )
    assert 'min-height:28px!important;height:28px;' in css  # the search, the height of the selectors


def test_d451_the_panels_explain_themselves_behind_a_small_i_next_to_their_step():
    rows = [{"product_group": "Frutas", "variation": 0.04}, {"product_group": "Verduras", "variation": -0.01}]
    families = home_mockup.family_movement(rows, lambda family: "#" + family, None, "todo Chile", step=2)
    head = families.split('<div class="mock-movement-row', 1)[0]
    assert '<div class="mock-step-row">' in head and 'class="mock-hint" tabindex="0"' in head
    assert '<span class="mock-hint-body" role="tooltip">' in head and "<h2>" not in head and "mock-kicker" not in head
    assert "¿Qué familias subieron y cuáles bajaron?" in head  # the same words, now on hover or focus
    css = home_mockup.style(charts.THEMES[0], charts.get_palette(charts.THEMES[0]))
    assert ".mock-hint:hover .mock-hint-body,.mock-hint:focus .mock-hint-body {display:block;}" in css
