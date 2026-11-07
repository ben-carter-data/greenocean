"""The thin header bar of the main pages (D-267) and the reading of an enlarged family."""

import re
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

# region Constants and variables
PROJECT_DIR = Path(__file__).resolve().parent.parent
# endregion
# region The thin header bar of the main pages and the reading of an enlarged family
sys.path.insert(0, str(PROJECT_DIR))
from bi import charts, dashboard, inflation_view, page_bar, queries  # noqa: E402
from tests.test_dashboard import DASHBOARD_FILE, draw_page, needs_database  # noqa: E402

MAIN_PAGES = [
    dashboard.PAGE_BA,  # D-456: with «Precios e inflación» as one of its tabs
    dashboard.PAGE_DIAGRAMS,
    dashboard.PAGE_ARCHITECTURE,
    dashboard.PAGE_OPERATIONS,
    dashboard.PAGE_SQL,
    dashboard.PAGE_RULES,
    dashboard.PAGE_RUNS,
    dashboard.PAGE_SECURITY,
    dashboard.PAGE_STACK,
]


def test_d398_the_bar_says_only_where_the_page_is_and_the_rest_is_content():
    bar = page_bar.build_bar_html("Ingeniería de datos › Modelo de datos", "Cómo se organizan.")
    assert 'aria-label="Página actual: Ingeniería de datos › Modelo de datos"' in bar
    assert 'Ingeniería de datos › <b role="heading" aria-level="1">Modelo de datos</b>' in bar
    assert 'title="Cómo se organizan."' in bar and "<a" not in bar and "page-chip" not in bar
    info = page_bar.build_info_html("¿Qué subió?", "La respuesta.", [("<b>+1 %</b>", "Uno por ciento")])
    assert 'role="heading" aria-level="2" title="La respuesta.">¿Qué subió?</span>' in info
    assert '<span class="page-chip" title="Uno por ciento"><b>+1 %</b></span>' in info
    assert "¿Qué subió?" not in page_bar.build_info_html("¿Qué subió?", "", show_title=False)


def test_every_theme_styles_the_bar():
    for mode in charts.THEMES:
        css = page_bar.build_css(charts.get_palette(mode))
        assert ".st-key-page_bar" in css and ".st-key-page_info" in css and ".page-bar-terms" in css


@needs_database
@pytest.mark.parametrize("view", MAIN_PAGES)
def test_d267_each_main_page_has_one_bar_and_no_other_header(view):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["vista"] = view
    if view in dashboard.AUTHOR_ONLY_PAGES:  # D-420: the Autor's pages, as the Autor sees them
        app.session_state["admin_unlocked"] = True
        app.session_state["quality_alert_seen"] = True
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert markup.count('class="page-bar-main"') == 1 and markup.count('class="page-bar-updated"') == 1
    assert 'class="compact-header"' not in markup and 'class="app-brand"' not in markup
    assert [str(button.key) for button in app.button].count("return_to_previous") == 1
    assert f'aria-label="Página actual: {dashboard.build_view_path(dashboard.WINDOW_OF_VIEW[view], view)}"' in markup


@needs_database
def test_d267_inflation_bar_counts_the_answer_and_names_its_kpi_and_metric():
    app = draw_page(dashboard.PAGE_SEASONALITY)
    markup = " ".join(block.value for block in app.markdown)
    rows, last, summary, ipc_total, ipc_year = dashboard.read_family_inflation(dashboard.get_database_version())
    above = (summary["verdict"] == "más que la inflación").sum()
    below = (summary["verdict"] == "menos que la inflación").sum()
    assert f'<b class="rise">{above} más</b><b class="fall">{below} menos</b>' in markup
    assert f"<em>IPC</em><b>{charts.format_signed_percent(ipc_total)}</b>" in markup
    assert "<em>KPI</em>" in markup and "<em>Métrica</em>" in markup
    assert 'class="ctx-answer"' not in markup  # the long answer lives on the title's hover


@pytest.fixture(scope="module")
def inflation():
    rows, last = inflation_view.build_family_index(
        queries.run_sql(inflation_view.SERIES_SQL), queries.run_sql("SELECT year, month, food_index FROM ipc_monthly")
    )
    summary, ipc_total, ipc_year = inflation_view.summarize_families(rows, last)
    return rows, last, summary, ipc_total, ipc_year


@needs_database
def test_d267_the_reading_of_a_family_is_recomputed_from_its_index(inflation):
    rows, last, summary, ipc_total, ipc_year = inflation
    for row in summary.itertuples():
        reading = dict(inflation_view.family_insights(rows, summary, row.family, last))
        first = reading["Desde enero 2022"]
        assert first.startswith(f"Subió {charts.format_signed_percent(row.total)}")
        gap = round(row.total, 1) - round(ipc_total, 1)
        assert inflation_view.points(gap) in first and row.verdict in first
        series = rows[rows["product_group"] == row.family]
        peak = series.loc[series["index"].idxmax()]
        assert inflation_view.month_name(int(peak["year"]), int(peak["month"])) in reading["Máximo"]
        assert f"{int(series['series'].max())} series" in reading["Base del cálculo"]
        assert charts.format_signed_percent(series["real"].iloc[-1] - 100) in reading["Sin inflación"]


@needs_database
def test_d267_without_inflation_the_reading_follows_the_line_the_chart_draws(inflation):
    rows, last, summary, *_ = inflation
    family = summary["family"].iloc[0]
    reading = dict(inflation_view.family_insights(rows, summary, family, last, real=True))
    series = rows[rows["product_group"] == family]
    peak = series.loc[series["real"].idxmax()]
    assert f"{peak['real']:.1f}".replace(".", ",") in reading["Máximo (sin inflación)"]
    ipc = dict(inflation_view.family_insights(rows, summary, inflation_view.IPC_NAME, last, real=True))
    assert not any(label.startswith("Mayor movimiento") for label in ipc)  # the flat 100 line has no move
    counts = summary["verdict"].value_counts()
    assert re.match(rf"{counts.get('más que la inflación', 0)} subieron más", ipc["Frente a las familias"])


@needs_database
def test_d267_ampliar_shows_the_chart_beside_its_reading():
    app = draw_page(dashboard.PAGE_SEASONALITY, state={dashboard.FAMILY_FOCUS_KEY: "Hortalizas"})
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert 'class="inf-insights"' in markup and "Lectura de los datos" in markup
    assert len(app.get("vega_lite_chart")) == 1


def test_d398_nothing_overlaps_the_path_gives_way_and_the_content_row_wraps():
    css = page_bar.build_css(charts.get_palette(charts.MODE_DARK))
    # the bar keeps one line: the path is cut with «…» before it could reach the time
    assert "flex-wrap:nowrap !important" in css and "text-overflow:ellipsis" in css
    assert "display:none" not in css  # the path never disappears
    # the row of the content wraps instead of overlapping
    assert ".stApp .st-key-page_info { gap:4px 8px !important; flex-wrap:wrap !important;" in css


def test_d268_the_sql_filters_and_status_bar_fit_a_narrow_window():
    from bi import sql_explorer

    css = sql_explorer.build_css(charts.get_palette(charts.MODE_DARK))
    # D-511: the filters are pills on the tab's line; under 1300 px they take a second line, whole
    assert ".st-key-sqlx_tabrow {{ flex-wrap:wrap !important".replace("{{", "{") in css
    assert ".st-key-sqlx_pill_anio_filtro [data-testid=\"stSelectbox\"] { width:84px !important; }" in css
    assert ".sqlx-status span:nth-child(4) { display:none; }" in css


def test_d391_the_inflation_page_sits_in_its_menu_section():
    # D-456: «Precios e inflación» is a tab of «Análisis», a page of «Negocio · BA y BI»; its address opens it
    view = dashboard.PAGE_BA
    path = dashboard.build_view_path(dashboard.WINDOW_OF_VIEW[view], view)
    assert path == "Negocio · BA y BI › Análisis" and "Dashboard" not in path
    address = dashboard.build_page_address(dashboard.PAGE_SEASONALITY)
    assert "pestana=Precios+e+inflaci%C3%B3n" in address and "Contexto" not in address


BAR_KEYS = ("page_bar", "home_bar")


def bar_elements(app):
    """Every element drawn inside the header of the page: the container keyed page_bar or home_bar."""
    found = []

    def walk(node, inside):
        here = inside or str(getattr(node, "key", "") or "") in BAR_KEYS
        if here:
            found.append(node)
        for child in getattr(node, "children", {}).values():
            walk(child, here)

    walk(app._tree, False)
    return found


@needs_database
@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("view", [dashboard.HOME_PAGE, *MAIN_PAGES, dashboard.PAGE_CHANNELS, dashboard.PAGE_INSIGHTS])
def test_d398_the_header_has_no_link_to_another_page(view, language):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.query_params.update({"vista": view, "lang": language})
    app.session_state["visitor_profile"] = "profesional"
    if view in dashboard.AUTHOR_ONLY_PAGES:  # D-420: the Autor's pages, as the Autor sees them
        app.session_state["admin_unlocked"] = True
        app.session_state["quality_alert_seen"] = True
    app.run()
    assert not app.exception
    starts = ('<div class="page-bar-main"', '<div class="greenocean-mockup home-bar-main"')
    bars = [block.value for block in app.markdown if block.value.lstrip().startswith(starts)]
    assert len(bars) == 1, view
    assert "<a " not in bars[0] and "href" not in bars[0]  # the bar's own HTML links nowhere
    # and no Streamlit element of the header opens another page or does something: only «Volver»
    buttons = [str(node.key) for node in bar_elements(app) if type(node).__name__ == "Button"]
    assert buttons == ["return_to_previous"], (view, buttons)
    assert not [
        node for node in bar_elements(app) if type(node).__name__ in ("PageLink", "SegmentedControl", "Selectbox")
    ]


def test_d407_one_screen_down_to_1280_by_800_and_1024_by_768_scrolls_without_cuts():
    # RNF-06 adds 1280 x 800; the measurement scripts check that size by default
    prd = (PROJECT_DIR / "docs" / "negocio" / "PRD.md").read_text(encoding="utf-8")
    assert "(1440 × 790 útiles), a 1280 × 800 y a 1920 × 1000" in prd
    assert "En 1024 × 768 se acepta el desplazamiento vertical, sin cortes" in prd
    for script in ("medir.cjs", "desbordes.cjs"):
        assert "1440x790,1280x800," in (PROJECT_DIR / "tests" / "medicion" / script).read_text(encoding="utf-8")
    # the Dashboard bar keeps one line, and under 860 px of height its family rows get thinner
    css = (PROJECT_DIR / "bi" / "home_mockup.css").read_text(encoding="utf-8")
    assert ".stApp .st-key-home_bar {flex-wrap:nowrap!important;}" in css
    assert "@media (max-height:860px) and (min-width:901px)" in css  # D-496: a tablet keeps the columns
    # the pages sized by the window leave room for the content row of D-398
    model_css = dashboard.build_architecture_css(charts.MODE_DARK)  # D-503: the star takes what the window leaves
    assert "max-height:calc(100vh - 331px)" in model_css and "max-height:calc(100vh - 350px)" in model_css


def open_as_professional():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    return app


@needs_database
def test_d423_volver_goes_back_to_the_previous_page_of_the_visit_with_its_state():
    app = open_as_professional()
    # the Dashboard with its steps done and the search already used (D-372)
    app.session_state["home_region_done"] = app.session_state["home_family_done"] = True
    app.session_state["home_searched"] = True
    app.run()
    assert not app.exception
    # another page of the menu; the Dashboard's state changes meanwhile
    app.query_params["vista"] = dashboard.PAGE_ARCHITECTURE
    app.run()
    assert [step["window"] for step in app.session_state[dashboard.PAGE_HISTORY]] == [
        dashboard.WINDOW_OF_VIEW[dashboard.PAGE_HOME],
        dashboard.WINDOW_OF_VIEW[dashboard.PAGE_ARCHITECTURE],
    ]
    app.session_state["home_searched"] = False
    app.button(key="return_to_previous").click().run()
    assert not app.exception
    # back on the Dashboard, in this same session (the view is kept), with the steps as they were
    markup = " ".join(block.value for block in app.markdown)
    assert "Página actual: Ingeniería de datos › Modelo de datos" not in markup
    assert "Mapa de Chile con la dirección dominante de los precios por región" in markup
    assert app.session_state["home_searched"] is True
    assert app.session_state[dashboard.PROFILE_STATE] == dashboard.PROFILE_PROFESSIONAL
    assert dashboard.VIEW_PARAMETER not in app.query_params
    assert len(app.session_state[dashboard.PAGE_HISTORY]) == 1
    # no page reload: the button walks the session's history, there is no script that changes the address
    assert not hasattr(dashboard, "RETURN_ACTION_SCRIPT")


@needs_database
def test_d423_with_no_page_before_volver_opens_choose_your_view():
    app = open_as_professional()
    app.query_params["vista"] = dashboard.PAGE_ARCHITECTURE
    app.run()
    assert not app.exception and len(app.session_state[dashboard.PAGE_HISTORY]) == 1
    app.button(key="return_to_previous").click().run()
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert "Elige tu vista" in markup and app.session_state[dashboard.CHANGE_VIEW] is True


def test_d423_the_history_kept_across_a_reload_takes_only_well_formed_steps(monkeypatch):
    state = {}
    monkeypatch.setattr(dashboard.st, "session_state", state)
    good = {
        "window": "Negocio",
        "params": {"vista": dashboard.PAGE_CHANNELS},
        "state": {"home_region_done@ODEPA": True},
    }
    sneaky = {"window": "Negocio", "params": {}, "state": {"admin_unlocked": True}}
    dashboard.restore_kept_history({"p": "profesional", "h": [good, sneaky, "x", {"window": 3}]})
    assert state[dashboard.PAGE_HISTORY] == [good]
    # the page the reload opened, already recorded in the new session, follows the steps kept
    opened = {"window": "Negocio", "params": {"vista": dashboard.PAGE_CHANNELS, "canal": "Mayorista"}, "state": {}}
    state[dashboard.PAGE_HISTORY] = [opened]
    dashboard.restore_kept_history({"p": "profesional", "h": [good]})
    assert state[dashboard.PAGE_HISTORY] == [good, opened]


# endregion
