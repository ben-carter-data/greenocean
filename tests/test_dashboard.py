"""Tests for the dashboard: navigation, appearance, key figures and evidence."""
import html
import re
import json
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
import html

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from bi import github_page, charts, control, dashboard, project, queries, stack_page  # noqa: E402

DASHBOARD_FILE = str(PROJECT_DIR / "bi" / "dashboard.py")
# These tests draw the real dashboard, so they need the committed database.
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(),
                                    reason="etl/datos.db has not been built")
ALL_PAGES = [p for views in dashboard.WINDOWS.values() for p in views]


@pytest.fixture(autouse=True)
def reset_login_guard():
    """The control-code guard is shared by every session (D-199): each test starts clean."""
    dashboard.get_login_guard.clear()
    yield
    dashboard.get_login_guard.clear()


@pytest.fixture(autouse=True)
def fixed_github_answers(monkeypatch):
    monkeypatch.setattr(control, "list_workflow_runs", lambda *args, **kwargs: [])
    dashboard.fetch_pipeline_runs.clear()
    dashboard.get_last_github_answers.clear()
    yield


def read_page_title(app):
    """The title of the page: st.title, or the one-line header of a report page (D-067)."""
    if app.title:
        return app.title[0].value
    for block in app.markdown:
        match = re.search(r'class="(?:compact-header|report-title)"><h1[^>]*>([^<]+)</h1>', block.value)
        if not match:
            match=re.search(r'<header class="mock-intro"><div><h1>([^<]+)',block.value)
        if not match:
            match = re.search(r'<h1 class="qa-h1">([^<]+)</h1>', block.value)
        if match:
            return html.unescape(match.group(1))
    return None


def draw_page(title, state=None, query=None):
    """Draw one page alone, the way the navigation does; state: session values set first;
    query: address parameters, as a link would carry them."""
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\nimport streamlit as st\n"
              f"from bi import dashboard\n"
              + "".join(f"st.session_state[{key!r}] = {value!r}\n" for key, value in (state or {}).items())
              + "".join(f"st.query_params[{key!r}] = {value!r}\n" for key, value in (query or {}).items())
              + f"dashboard.render_page({title!r})\n")
    return AppTest.from_string(script, default_timeout=60).run()


# The home page opens on the latest week and its most moved family, both of which
# change every Tuesday; tests that read figures pin the week of 2026-10-05.
PINNED_HOME = {"_home_region": "Todas", "_home_week": "2026-10-05", "familia": "Hortalizas"}


def test_d070_the_route_holds_every_view_once_and_charts_only_in_dashboard():
    # D-151: the route ends in the project's documents.
    assert dashboard.ROUTE == ["Dashboard", "Ingeniería de datos", "Seguridad", "Documentación"]  # D-201
    assert list(dashboard.WINDOWS) == dashboard.ROUTE + [dashboard.SECTION_PROJECT, dashboard.SECTION_RESOURCES,
                                                         dashboard.SECTION_KPI]
    views = [view for window in dashboard.WINDOWS.values() for view in window]
    assert len(views) == len(set(views)) and set(views) == set(dashboard.SHOW_PAGE_BY_TITLE)
    assert dashboard.WINDOWS["Dashboard"] == [
        dashboard.HOME_PAGE, dashboard.PAGE_DATA, dashboard.PAGE_ANALYSIS, dashboard.PAGE_GAP, dashboard.PAGE_CHANNELS,
        dashboard.PAGE_ALERTS, dashboard.PAGE_SEASONALITY, dashboard.PAGE_SQL]
    assert dashboard.WINDOWS["Ingeniería de datos"][0] == dashboard.PAGE_DIAGRAMS
    # Old addresses of the retired windows and of the 3D view still open something.
    for path in ["operacion", "documentacion", "vista-3d"]:
        assert dashboard.OLD_PATHS[path][0] in views
    assert dashboard.PAGE_OF_TAB[dashboard.TAB_PIPELINE] == dashboard.PAGE_DIAGRAMS


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
def test_direct_entry_opens_corporate_dashboard_without_profile_dialog():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Reclutamiento"
    app.run()
    assert not app.exception and not app.get("dialog")
    assert "perfil" not in app.query_params
    assert not [box for box in app.selectbox if box.label in ("Perfil", "Tema")]
    assert app.radio(key="theme_field").value == dashboard.DEFAULT_THEME
    assert read_page_title(app) == "¿Qué familias de alimentos subieron y bajaron?"
    assert "Ingeniería de datos" not in " ".join(block.value for block in app.markdown)


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
        assert page in dashboard.PAGE_OF_TAB or state == "pending"


def test_business_questions_float_without_repetitive_card_backgrounds():
    showcase = dashboard.build_question_showcase_html()

    assert showcase.count('class="question-item"') == len(dashboard.BUSINESS_QUESTIONS)
    assert 'class="info-card' not in showcase
    for number in range(1, len(dashboard.BUSINESS_QUESTIONS) + 1):
        assert f"Pregunta {number} · Disponible" in showcase
    for symbol in ["gap", "channels", "region", "calendar", "lag", "alert"]:
        assert f'data-kind="{symbol}"' in showcase


def test_c03_the_catalog_covers_every_stored_query_once():
    """Every named query of bi/queries.sql, plus K7 (etl/etl.py), is one question."""
    names = [entry["name"] for entry in dashboard.CATALOG]
    assert len(names) == len(set(names))
    assert set(names) == set(queries.load_queries()) | {project.MATCH_COVERAGE_QUERY_NAME}
    for entry in dashboard.CATALOG:
        assert entry["question"].startswith("¿") and entry["compares"] and entry["reading"]


@needs_database
def test_c03_every_result_is_read_only_and_runs_only_stored_queries(monkeypatch):
    """Each result opens the database in read-only mode and runs a stored query, wrapped
    only by fixed filter columns whose values travel as parameters."""
    import duckdb
    opened = []
    original = queries.open_database

    def spy(database_file=queries.DATABASE_FILE):
        connection = original(database_file)
        # D-154: DuckDB opened read-only refuses any write.
        with pytest.raises(duckdb.Error, match="read-only"):
            connection.execute("CREATE TABLE written_by_catalog (x INTEGER)")
        opened.append(connection)
        return connection
    monkeypatch.setattr(queries, "open_database", spy)
    dashboard.read_cached_catalog_rows.clear()
    for entry in dashboard.CATALOG:
        result = entry["build"](dashboard.charts.MODE_CORPORATE)
        assert not result["rows"].empty, entry["name"]
        sql, parameters = dashboard.build_catalog_sql(entry["name"], result["filters"])
        stored = project.strip_sql_comments(dashboard.read_catalog_sql(entry["name"]))
        assert stored.strip().rstrip(";") in sql
        assert len(parameters) == sql.count("?")
    assert opened
    dashboard.read_cached_catalog_rows.clear()


def test_d143_the_consoles_left_and_their_old_addresses_open_the_summary():
    assert dashboard.SECTION_QUERIES not in dashboard.WINDOWS
    assert dashboard.SECTION_PYTHON not in dashboard.WINDOWS
    # D-148: «Código Python y SQL» left as well; its address opens the GitHub page.
    assert dashboard.SECTION_CODE not in dashboard.WINDOWS
    assert dashboard.OLD_PATHS["codigo"] == (dashboard.PAGE_LINKS, None)
    for path in ["datos-y-codigo", "consultas", "preguntas-y-resultados", "analisis-python"]:
        assert dashboard.OLD_PATHS[path] == (dashboard.PAGE_HOME, None)
    assert dashboard.PAGE_OF_TAB[dashboard.TAB_EXPLORER] == dashboard.PAGE_HOME
    assert not hasattr(dashboard.queries, "run_console_sql")
    assert dashboard.build_query_address("k1_margin").startswith("https://github.com/")


@needs_database
def test_gap_tab_shows_k5_with_its_descriptive_note():
    app = draw_page(dashboard.PAGE_GAP)
    assert not app.exception
    assert dashboard.LAG_NOTE in [caption.value for caption in app.caption]
    assert any("semanas" in block.value or "Sin relación clara" in block.value
               for block in app.markdown)


@needs_database
def test_dashboard_opens_with_data_and_diagrams_have_their_own_page():
    app = draw_page(dashboard.HOME_PAGE, query=PINNED_HOME)
    assert not app.exception and not app.tabs
    texts = " ".join(block.value for block in app.markdown)
    assert 'Productos · Hortalizas' in texts and 'Producto seleccionado' not in texts
    assert 'Precio 28-09' in texts and 'Precio 05-10' in texts and 'Variación' in texts
    assert 'class="zoom-frame' not in texts and 'animateMotion' not in texts
    assert texts.index('¿Qué familias de alimentos subieron y bajaron?') < texts.index('Productos · Hortalizas')
    # The search, the order and the table replace the old «Explorar…» drop-down (D-093).
    assert not app.expander and not app.slider
    # Map, movement by family and products of the selected family, on one screen (D-092).
    assert texts.count('<a class="mock-movement-row ') == 7
    assert texts.count('<a class="mock-movement-row rise selected"') == 1
    assert 'class="mock-products-table"' in texts and 'Productos · Hortalizas' in texts
    assert '¿Qué estamos comparando?' not in texts and 'class="mock-family-tile ' not in texts
    assert 'id="pulso-regional"' in texts
    assert 'Registros históricos' not in texts
    lineage_view = draw_page(dashboard.PAGE_DIAGRAMS, {"pipeline_view": dashboard.PIPELINE_LINEAGE})
    texts = " ".join(block.value for block in lineage_view.markdown)
    # Step 4 of the refonte: the dbt lineage, read from the build, is the zoom of the journey.
    assert 'aria-label="Linaje dbt: de bronce a marts"' in texts and 'stg_odepa__wholesale' in texts
    diagrams = draw_page(dashboard.PAGE_DIAGRAMS)
    texts = " ".join(block.value for block in diagrams.markdown)
    assert not diagrams.exception and not diagrams.tabs
    # The page opens on the whole journey, with the dbt steps framed and named.
    assert 'dbt CORE · staging → intermedio → marts · 16 modelos' in texts
    pipeline_header = next(block.value for block in diagrams.markdown
                           if 'class="compact-header"' in block.value and '<h1' in block.value and 'Pipeline' in block.value)
    # D-150: the same one-line header as every technical page, freshness included.
    assert '>Pipeline y linaje</h1>' in pipeline_header and 'page-freshness' in pipeline_header
    assert 'Pruebas dbt' in texts and 'Modelos dbt' in texts
    assert not diagrams.toggle
    assert 'Animar el recorrido de los datos' not in texts
    assert 'ODEPA → indicadores · recorrido y plataformas' not in texts
    for label in ["ODEPA mayorista", "ODEPA consumidor", "Informe semanal",
                  "Consultas SQL", "OBSERVABILIDAD"]:
        assert label in texts
    assert 'aria-label="Actualización semanal"' not in texts
    assert "animateMotion" in texts


@needs_database
def test_d136_devops_shows_the_whole_platform_architecture_and_pipeline_only_the_journey():
    pipeline = draw_page(dashboard.PAGE_DIAGRAMS)
    texts = " ".join(block.value for block in pipeline.markdown)
    assert not pipeline.exception
    assert 'aria-label="Recorrido de los datos de ODEPA al panel"' in texts
    assert 'aria-label="Arquitectura del proyecto por plataforma"' not in texts
    assert 'aria-label="Estado real del pipeline, de ODEPA al panel"' not in texts
    assert "Ampliar" not in texts and "diagrama=" not in texts
    devops = draw_page(dashboard.PAGE_DEVOPS)
    texts = " ".join(block.value for block in devops.markdown)
    assert not devops.exception
    assert texts.count('aria-label="Arquitectura del proyecto por plataforma"') == 1
    assert "Ciclo DevOps" not in texts and "Ver el pipeline" not in texts


@needs_database
def test_dashboard_territory_is_immediately_readable_without_a_3d_duplicate():
    app = draw_page(dashboard.HOME_PAGE)
    assert not app.exception
    figures = [json.loads(chart.proto.spec) for chart in app.get("plotly_chart")]
    types = {trace["type"] for figure in figures for trace in figure["data"]}
    assert "scatter3d" not in types
    texts = " ".join(block.value for block in app.markdown)
    # D-150: four KPI tiles of equal width; the selected region sits in the subtitle.
    assert texts.count('class="mock-kpi"') == 4 and "Todo Chile" in texts
    assert "Mapa en proporción real" in texts

@needs_database
def test_d189_model_page_opens_on_the_database_map():
    app = draw_page(dashboard.PAGE_ARCHITECTURE)
    assert not app.exception and not app.tabs
    # The map is drawn in an iframe; the star model waits behind the view selector.
    joined = " ".join(block.value for block in app.markdown)
    assert 'aria-label="Modelo estrella de datos.db"' not in joined
    counts, layers, tests = dashboard.read_database_map(dashboard.get_database_version())
    assert len(counts) == 12 and counts["weekly_price"] > 100_000
    assert layers == {"staging": 3, "intermediate": 4, "marts": 9} and tests > 0


@needs_database
def test_d097_model_page_is_one_panoramic_diagram():
    app = draw_page(dashboard.PAGE_ARCHITECTURE, state={dashboard.MODEL_VIEW_KEY: "Modelo estrella"})
    assert not app.exception and not app.tabs and not app.expander
    joined = " ".join(block.value for block in app.markdown)
    assert joined.count('aria-label="Modelo estrella de datos.duckdb"') == 1
    assert "<script" not in joined
    assert joined.count("Auditoría de cargas".upper()) == 1
    # D-147: one panoramic diagram; no table picker and no SQL. Each table explains
    # itself on hover, with its role and its rows.
    assert not app.radio and not app.code
    for table in dashboard.project.TABLE_NAMES:
        assert f"<title>{table} · " in joined
    assert "una fila por semana" in joined.lower()
    assert "etl/schema.sql en GitHub" in joined

    app = draw_page(dashboard.PAGE_DEVOPS)
    assert not app.exception
    # One screen (D-132): no toggle, no tabs; each layer is a tile that opens a dialog.
    assert not app.tabs and not app.expander and not app.toggle
    keys = [str(button.key) for button in app.button]
    for heading in [group[0] for group in dashboard.ARCHITECTURE_GROUPS] + ["Coste y capacidad"]:
        assert f"devops_layer_{heading}" in keys
    joined = " ".join(block.value for block in app.markdown)
    assert joined.count('class="zoom-frame diagram-devops"') == 1
    # A tile opens its layer's detail; only then are its rows drawn.
    assert 'class="technical-rows layer-cards"' not in joined
    app.button(key="devops_layer_Seguridad").click().run()
    assert not app.exception
    joined = " ".join(block.value for block in app.markdown)
    assert joined.count('class="technical-rows layer-cards"') == 1 and "Base en solo lectura" in joined
    assert joined.count('class="layer-card"') == 4 and 'class="layer-logo"' in joined

@needs_database
def test_d056_analysis_filters_show_once_and_hold_in_every_tab():
    app = draw_page(dashboard.PAGE_ANALYSIS)
    assert not app.exception
    assert [tab.label for tab in app.tabs] == dashboard.TABS_BY_PAGE[dashboard.PAGE_ANALYSIS]
    assert [box.label for box in app.selectbox].count("Producto") == 1
    assert [box.label for box in app.multiselect] == ["Canal"]
    region = [box for box in app.selectbox if box.label == "Región"][0]
    other_region = [option for option in region.options if option != region.value][0]
    region.set_value(other_region).run()
    assert not app.exception
    assert app.session_state["analysis_region"] == other_region


def test_kpi_link_opens_the_kpi_view_with_that_indicator():
    link = dashboard.build_kpi_link("K5")
    # El proyecto starts the route, so it lives at the root of the app.
    assert 'href="kpis?kpi=K5"' in link
    assert ">K5<" not in link


def test_d065_a_place_named_in_a_document_opens_its_window_and_view():
    assert dashboard.build_place_address(dashboard.TAB_QUALITY) == (
        "arquitectura-y-operacion?vista=Monitoreo")
    assert dashboard.build_place_address(dashboard.TAB_KPI) == (
        "kpis")
    assert dashboard.build_place_address(dashboard.PAGE_ANALYSIS) == (
        "./")


def test_t52_every_link_of_the_project_points_to_a_window_that_exists():
    """The first window lives at './'; any other one at its own path."""
    paths = set(dashboard.WINDOW_PATHS.values())
    for journey in [dashboard.JOURNEY_MANAGER, dashboard.JOURNEY_ANALYST,
                    dashboard.JOURNEY_TECHNICAL]:
        for _, address in dashboard.list_journey_steps(journey):
            path = address.split("?")[0]
            assert path == "./" or path in paths, address
    assert dashboard.build_page_address(dashboard.PAGE_COVER) == "proyecto"
    assert dashboard.build_page_address(dashboard.PAGE_BUSINESS).startswith("proyecto?")
    assert dashboard.build_page_address(dashboard.HOME_PAGE) == "./"


def test_t52_each_channel_gap_says_how_many_regions_stand_behind_it():
    rows = pd.DataFrame({"channel": ["Supermercado"] * 3 + ["Mercado Minorista"] * 2,
                         "region": ["Región de Arica y Parinacota", "Región del Maule",
                                    "Región del Maule", "Región de Arica y Parinacota",
                                    "Región de Arica y Parinacota"]})
    assert dashboard.describe_gap_basis(rows) == [
        "Mercado Minorista: 1 región (Arica y Parinacota), 2 semanas",
        "Supermercado: 2 regiones, 3 comparaciones"]
    assert dashboard.list_channels_without_pairs(
        rows, ["Supermercado", "Mercado Minorista", "Supermercado en Línea", "Feria libre"],
        "Feria libre") == ["Supermercado en Línea"]


def test_t52_pipeline_summary_shows_its_worst_real_state():
    states = {name: control.RUN_OK for name in ["sources", "download", "etl", "load", "panel"]}
    assert dashboard.summarize_journey_state(states) == ("OK", "ok")
    states["etl"] = control.RUN_FAILED
    assert dashboard.summarize_journey_state(states) == ("con falla", "failed")


def test_t52_a_bar_resting_on_one_or_two_regions_names_them_next_to_it():
    assert dashboard.label_channel_with_its_regions(
        "Supermercado", ["Región de Arica y Parinacota"]) == (
        "Supermercado · solo Arica y Parinacota")
    assert dashboard.label_channel_with_its_regions(
        "Supermercado", ["Región del Maule", "Región de Ñuble", "Región del Biobío"]) == (
        "Supermercado")


def test_without_github_the_states_come_from_the_latest_saved_load():
    latest_load = {"status": "LOADED", "started_at": "2026-10-12T22:17:01"}
    states = dashboard.build_journey_states({}, None, latest_load, {"file": {"year": 2026}})
    assert [states[step] for step in ["download", "etl", "tests", "load", "etl_run"]] == [
        control.RUN_OK] * 5
    # What a saved load cannot prove stays unknown, and is drawn without a dot.
    assert states["report"] == dashboard.architecture.STATE_UNKNOWN
    assert states["workflow"] == dashboard.architecture.STATE_UNKNOWN
    assert dashboard.describe_state_source("GitHub respondió 403", {}, latest_load) == (
        "GitHub no respondió (GitHub respondió 403); los estados salen de la última carga "
        "guardada en la base (12-10-2026 19:17).")


def test_d071_four_themes_and_corporativo_is_the_default():
    assert charts.THEMES == ["Corporativo", "Vantablack", "Blue Light", "Dark Grey"]
    assert dashboard.get_mode() == charts.MODE_CORPORATE
    # Shared links with retired names still open the closest theme.
    assert dashboard.RETIRED_THEMES["Grafito"] == "Dark Grey"
    for theme in charts.THEMES:
        palette = charts.get_palette(theme)
        assert theme in charts.HEAT_RAMPS and palette["base"] in (charts.BASE_DARK,
                                                                  charts.BASE_LIGHT)


def test_t44_base_mode_switch_writes_streamlit_choice_and_tries_only_once():
    script = dashboard.build_base_mode_script(charts.BASE_LIGHT)
    assert '"stActiveTheme-" + page.location.pathname + "-v2"' in script
    assert 'const wanted = "Light"' in script
    # A second attempt on the same page and base is skipped: no endless reload.
    assert "!baseMatches && requested !== wanted" in script
    assert "getComputedStyle(page.document.body).color" in script
    assert "sessionStorage.removeItem(attempt)" in script
    assert 'const wanted = "Dark"' in dashboard.build_base_mode_script(charts.BASE_DARK)
    graphite = dashboard.build_base_mode_script(charts.MODE_GRAPHITE)
    assert 'const wanted = "Dark"' in graphite
    assert 'address.searchParams.set("tema", "Dark Grey")' in graphite


# region Administration (T-54)
ADMIN_ADDRESSES = [link["url"] for link in dashboard.ADMIN_LINKS]
FAKE_TOKEN = "github_pat_FAKE_SECRET_123"


def draw_control_page(secrets, run_state="ok", dialog=False):
    """The Operaciones page with GitHub replaced by fixed answers, no network. A manual
    run is accepted and ends in run_state. With dialog, the script opens the manual-run
    dialog itself: in a browser the dialog reruns alone (a fragment), which AppTest
    does not reproduce."""
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "from datetime import datetime, timedelta, timezone\n"
              "from bi import control, dashboard\n"
              "control.list_workflow_runs = lambda *args, **kwargs: []\n"
              # Relative to today: a fixed date made this test fail the day it arrived.
              "control.read_token_expiration = lambda token: datetime.now(timezone.utc) + timedelta(days=60)\n"
              "control.start_workflow_run = lambda token: None\n"
              "dashboard.wait_for_manual_run = lambda requested_at, token: {'id': 1}\n"
              f"dashboard.follow_run_progress = lambda run_id, token, area: {run_state!r}\n"
              + ("dashboard.show_run_now_dialog(dashboard.get_secret('GITHUB_TOKEN'), "
                 "dashboard.get_secret('CONTROL_CODE'))\n" if dialog else
                 "dashboard.render_page(dashboard.PAGE_RUNS)\n"))
    app = AppTest.from_string(script, default_timeout=60)
    for name, value in secrets.items():
        app.secrets[name] = value
    return app.run()


def read_page_text(app):
    """Every text the page sends to the browser: Markdown, HTML, notes and fields."""
    parts = [str(element.proto) for kind in ["markdown", "html", "caption", "info",
                                              "warning", "error", "text_input"]
             for element in app.get(kind)]
    return "\n".join(parts)


def open_run_dialog(app, code):
    app.text_input(key="run_now_code").input(code).run()
    app.button(key="run_now_confirm").click().run()
    return read_page_text(app) + " ".join(str(element.proto) for element in app.get("success"))


def button_keys(app):
    return [button.key for button in app.button]


def open_author_access(app, code):
    """D-203: Enter in the field opens the door; there is no «Abrir» button."""
    app.text_input(key="author_access_code").input(code).run()
    return read_page_text(app)


@needs_database
def test_d202_the_manual_run_and_the_links_appear_only_behind_the_code():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN})
    assert not app.exception
    # Before the code: no run button and no administration address, only the door.
    assert "runs_run_now" not in button_keys(app) and app.text_input(key="author_access_code")
    assert "author_access_open" not in button_keys(app)
    # D-207: a plain field shown as dots; a password field makes the browser offer to create one.
    assert app.text_input(key="author_access_code").proto.type != app.text_input(key="author_access_code").proto.PASSWORD
    assert "-webkit-text-security:disc" in dashboard.build_runs_css(charts.MODE_DARK)
    assert not [address for address in ADMIN_ADDRESSES if address in read_page_text(app)]
    text = open_author_access(app, "equivocada")
    assert not app.exception and "Clave incorrecta" in text and "runs_run_now" not in button_keys(app)
    text = open_author_access(app, "clave")
    assert not app.exception
    assert app.button(key="runs_run_now").label == "Ejecutar pipeline ahora" and not app.button(key="runs_run_now").disabled
    assert all(address in read_page_text(app) for address in ADMIN_ADDRESSES)
    app.button(key="author_access_close").click().run()
    assert "runs_run_now" not in button_keys(app)
    # The dialog itself still asks for the code when the session is not open (defense in depth).
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, dialog=True)
    text = open_run_dialog(app, "equivocada")
    assert not app.exception and "Clave incorrecta" in text


@needs_database
def test_d199_the_code_box_survives_any_character_and_locks_after_five_wrong_codes():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, dialog=True)
    text = open_run_dialog(app, "contraseña ñ")
    assert not app.exception and "Clave incorrecta" in text
    for attempt in range(control.LOGIN_MAX_FAILURES - 1):
        text = open_run_dialog(app, f"intento{attempt}")
    assert "bloqueado" in text
    text = open_run_dialog(app, "clave")
    assert not app.exception and "Demasiados intentos" in text and "Se ejecutó" not in text


@needs_database
def test_d201_security_has_its_own_section_with_the_view_and_the_test_plan():
    assert dashboard.SIDEBAR_TOP_LABELS[dashboard.SECTION_SECURITY] == "Seguridad"
    assert dashboard.WINDOWS[dashboard.SECTION_SECURITY] == [dashboard.PAGE_SECURITY, dashboard.PAGE_SECURITY_PLAN]
    app = draw_control_page({})
    assert not app.exception and [tab.label for tab in app.tabs][:2] == ["Operación", "Plataforma"]
    for page in (dashboard.PAGE_SECURITY, dashboard.PAGE_SECURITY_PLAN):
        app = draw_page(page)
        assert not app.exception and read_page_title(app) == page
    assert "S-01" in " ".join(block.value for block in app.markdown)


@needs_database
def test_d149_a_successful_run_says_so_and_never_shows_the_token():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="ok", dialog=True)
    text = open_run_dialog(app, "clave")
    assert not app.exception
    assert "Se ejecutó correctamente" in text and "Tu token vence en" in text
    assert FAKE_TOKEN not in text and FAKE_TOKEN[-6:] not in text


@needs_database
def test_d149_a_failed_run_says_it_did_not_complete():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="failed", dialog=True)
    text = open_run_dialog(app, "clave")
    assert not app.exception and "No se ejecutó completamente" in text


@needs_database
def test_d149_without_secrets_the_run_is_disabled_and_reload_confirms():
    app = draw_control_page({})
    assert "runs_run_now" not in button_keys(app) and not [box for box in app.text_input if box.key == "author_access_code"]
    assert "Se activa cuando el autor guarda la clave" in read_page_text(app)
    app.button(key="runs_reload").click().run()
    assert not app.exception
    assert any("Datos recargados" in str(toast.proto) for toast in app.get("toast"))


@needs_database
def test_project_links_are_grouped_as_a_tree_with_descriptions():
    app = draw_page(dashboard.PAGE_LINKS)
    assert not app.exception
    # The GitHub page is one hero and a tree of three uses (bi/github_page.py), drawn in
    # its own frame because st.html sanitises its SVG; the frame holds this markup.
    assert app.get('iframe')
    links = github_page.build_github_page_html(dashboard.get_mode())
    assert 'class="gh-page' in links
    for category in ("AUTOMATIZACIÓN", "TRAZABILIDAD", "DOCUMENTACIÓN"):
        assert category in links.upper()
    for link in project.PROJECT_LINKS:
        if link["url"]:
            assert f'href="{link["url"]}"' in links
            assert f'>{link["url"]}<' not in links

# endregion


def test_architecture_cards_show_file_names_and_named_links():
    note = dashboard.format_architecture_note("Archivo", ".github/workflows/semanal.yml")
    assert note == 'Archivo: <code title=".github/workflows/semanal.yml">semanal.yml</code>'
    assert ">Ver en Monitoreo<" in dashboard.format_architecture_note(
        "Dónde se ve", dashboard.TAB_QUALITY)
    assert [group[0] for group in dashboard.ARCHITECTURE_GROUPS] == [
        "Seguridad", "DevOps", "Observabilidad", "Informes"]


def test_d057_cards_escape_their_text_and_keep_bold_and_code():
    card = dashboard.build_info_card_html("<b>Título</b>", "Texto con **negrita** y `datos.db`",
                                          label="P1", note="nota")
    assert "<b>Título</b>" not in card and "&lt;b&gt;Título&lt;/b&gt;" in card
    assert "<strong>negrita</strong>" in card and "<code>datos.db</code>" in card
    assert 'class="info-label">P1<' in card


def test_d057_links_say_where_they_go():
    link = dashboard.build_place_link(dashboard.TAB_GAP)
    assert ">Ver en Brecha de precio<" in link
    assert ">Ir a Monitoreo<" in dashboard.build_place_link(
        dashboard.TAB_QUALITY, "Ir a")
    steps = dashboard.build_steps_html([("Nombres", "se separan"), ("Unidades", "a kilo")])
    assert steps.count("<li>") == 2 and steps.startswith('<ol class="steps">')


@needs_database
def test_d090_kpi_module_reads_left_to_right_and_keeps_sql_behind_a_click():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "import streamlit as st\n"
              "from bi import dashboard\ndashboard.show_kpi_tab(dashboard.charts.MODE_DARK)\n")
    app = AppTest.from_string(script, default_timeout=60)
    app.query_params["kpi"] = "K5"
    app.run()
    assert not app.exception
    # Question on top, then the whole path at once: three nodes on one line, three cards,
    # the dense context behind tabs, and no «continue» step.
    assert app.selectbox(key='kpi_register_selection').value=='K5'
    assert [tab.label for tab in app.tabs] == ["Alcance", "Lógica", "Límites"]
    assert not app.expander and not app.code
    assert [button.label for button in app.button] == ["Desplegar SQL"]
    markup=' '.join(block.value for block in app.markdown)
    assert markup.count('class="kpi-node"') == 3 and 'class="kpi-figure' in markup
    for title in ("Resultado", "Contexto", "Consulta"):
        assert f'</span>{title}</div>' in markup
    assert 'k5_weekly_variations_sql' in markup
    app.selectbox(key='kpi_register_selection').set_value('K1').run()
    assert not app.exception and app.query_params['kpi']=='K1'
    markup=' '.join(block.value for block in app.markdown)
    assert 'k1_margin' in markup and dashboard.KPI_QUESTIONS['K1'] not in markup
    # The SQL opens on demand, in a layer, read from the same stored query.
    app.button(key='kpi_query_open').click().run()
    assert not app.exception
    assert [block.value for block in app.code] == [dashboard.read_catalog_sql('k1_margin')]


def test_d090_kpi_nodes_sit_on_the_centre_of_their_cards():
    assert sum(dashboard.KPI_COLUMNS) + 2 * dashboard.KPI_GAP == 100
    assert dashboard.kpi_node_positions() == [15.0, 51.0, 86.0]
    path = dashboard.build_kpi_path_html()
    for x, y in zip(dashboard.kpi_node_positions(), dashboard.KPI_NODE_HEIGHTS):
        assert f'left:{x}%;top:{y}px' in path


def test_d090_kpi_figure_splits_numbers_from_their_unit():
    assert dashboard.split_kpi_figure("+13,2 %") == ("+13,2 %", "")
    assert dashboard.split_kpi_figure("43 alertas") == ("43", "alertas")
    assert dashboard.split_kpi_figure("1,23") == ("1,23", "")
    assert dashboard.split_kpi_figure("la misma semana") == ("", "la misma semana")
    html_text = dashboard.build_kpi_impact_html("K1", {"Resultado observado": "<b>1</b>"}, "ok", "hoy")
    assert "<b>1</b>" not in html_text


def test_d057_every_rule_has_one_stage_in_the_order_of_the_etl():
    rules = [rule for _, _, stage_rules, _ in dashboard.RULE_STAGES for rule in stage_rules]
    assert sorted(rules) == [f"RN-{number:02d}" for number in range(1, 15)]
    assert [stage for stage, _, _, _ in dashboard.RULE_STAGES][:6] == [
        "Limpieza", "Validación", "Unidades", "Semanas", "Atípicos", "Carga"]


@needs_database
def test_d057_rules_tab_keeps_the_long_rejected_row_out_of_the_cards():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "from bi import dashboard\ndashboard.show_rules_tab(dashboard.charts.MODE_DARK)\n")
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    cards = " ".join(block.value for block in app.markdown if 'class="info-grid"' in block.value)
    assert cards.count('class="info-card"') == 14
    assert "file_hash" not in cards
    assert len(app.expander) == len(dashboard.RULE_STAGES)


@needs_database
def test_manual_is_a_procedural_document_without_presentation_cards():
    app = draw_page(dashboard.PAGE_MANUAL)
    assert not app.exception
    text = " ".join(block.value for block in app.markdown)
    titles = [heading.value for heading in app.subheader]
    assert "Qué pasa cada martes" in titles and "Límites conocidos" in titles
    assert "Recorrido del proyecto" in titles
    assert 'class="info-card"' not in text
    assert '.github/workflows/semanal.yml' in text


def test_d057_key_decisions_exist_and_the_rest_go_newest_first():
    numbers = {dashboard.split_decision_title(title)[0] for title, _ in project.list_decisions()}
    key_numbers = [number for _, _, group in dashboard.KEY_DECISIONS for number in group]
    assert len(key_numbers) == len(set(key_numbers)) == 12
    assert set(key_numbers) <= numbers
    assert dashboard.read_first_sentence("Uno. Dos.") == "Uno."


@needs_database
def test_decisions_are_not_a_public_section_and_old_links_open_documentation():
    assert dashboard.PAGE_DECISIONS not in [p for views in dashboard.WINDOWS.values() for p in views]
    assert dashboard.PAGE_DECISIONS not in dashboard.SHOW_PAGE_BY_TITLE
    assert dashboard.OLD_PATHS["decisiones"] == (dashboard.PAGE_DOCUMENTATION, None)
    app = draw_page(dashboard.PAGE_DOCUMENTATION)
    assert not app.exception
    assert "Registro de decisiones" not in " ".join(block.value for block in app.markdown)
    assert project.list_decisions()  # The source engineering history is preserved.


def test_d057_every_theme_of_the_glossary_says_what_it_groups():
    themes = {row["Tema"] for row in project.read_guide_table("Glosario")}
    assert themes == set(dashboard.GLOSSARY_THEME_LEADS)


def test_d057_every_rejection_reason_of_the_etl_is_explained():
    from etl import etl
    reasons = {value for name, value in vars(etl).items() if name.startswith("REASON_")}
    assert reasons == set(dashboard.REASON_TEXTS)


def test_d057_rejected_rows_show_readable_spanish_columns():
    rows = pd.DataFrame({"source": ["wholesale"], "reason": ["NON_POSITIVE_PRICE"],
                         "original_row": ['{"file_hash": "abc", "price_date": "2025-01-01", '
                                          '"product": "Ají", "avg_price": "0,0000"}']})
    table = dashboard.build_rejected_rows_table(rows)
    assert list(table.columns) == ["Fuente", "Motivo", "Fecha", "Producto", "Precio promedio"]
    assert table.iloc[0]["Fuente"] == "Mayorista"
    assert table.iloc[0]["Motivo"] == "Precio cero o negativo"


@needs_database
def test_d057_quality_tab_explains_what_was_left_out_and_shows_it():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "from bi import dashboard\ndashboard.show_quality_tab(dashboard.charts.MODE_DARK)\n")
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    cards = " ".join(block.value for block in app.markdown if 'class="info-grid"' in block.value)
    for label in ["RN-11 · no se cargan", "RN-12 · fuera de los indicadores",
                  "RN-05 · sin precio comparable"]:
        assert label in cards
    assert "0,008 %" in cards
    assert not [column for frame in app.dataframe for column in frame.value.columns
                if column in ("source", "reason", "rejected_rows", "rejected_share")]


def test_d058_the_old_links_tab_opens_the_links_view():
    assert dashboard.OLD_TAB_PAGES[(dashboard.PAGE_OPERATIONS, "Enlaces")] == dashboard.PAGE_LINKS
    assert dashboard.build_place_address(dashboard.PAGE_LINKS) == "enlaces"
    groups = {link["group"] for link in project.PROJECT_LINKS}
    # ODEPA moved out to its own sidebar folder, «Fuentes»: not a GitHub-page group
    # any more (D-118).
    assert groups == {"Código y operación", "Documentos"}
    assert set(dashboard.LINK_GROUP_LEADS) == groups


def test_d057_the_menu_folds_once_on_narrow_screens_only():
    script = dashboard.FOLD_SIDEBAR_SCRIPT
    assert f"window.innerWidth >= {dashboard.NARROW_SCREEN_WIDTH}" in script
    assert dashboard.NARROW_SCREEN_WIDTH == 1024
    # Folded once per visit: a reader who opens it again keeps it open.
    assert 'sessionStorage.getItem("sidebarFolded")' in script


def test_d059_alert_levels_go_from_moderate_to_very_high_with_icon_and_label():
    assert dashboard.find_alert_level(2.5) == ("Moderada", "●", "warning")
    assert dashboard.find_alert_level(3.2) == ("Alta", "▲", "serious")
    assert dashboard.find_alert_level(11) == ("Muy alta", "◆", "critical")
    rows = pd.DataFrame({"product": ["Tomate"], "variety": ["Larga vida"], "quality": ["Primera"],
                         "channel": ["Feria libre"], "variation": [0.25],
                         "usual_variation": [0.01], "variation_deviation": [0.06]})
    item = dashboard.build_alert_list_html(rows, charts.MODE_LIGHT)
    assert "▲ Alta" not in item and "◆ Muy alta" in item and "▲ +25,0 %" in item
    assert 'class="alert-limit"' in item


@needs_database
def test_analysis_sections_are_direct_destinations_without_tabs():
    expected = {
        dashboard.PAGE_ANALYSIS: "¿Qué precios subieron más?",
        dashboard.PAGE_GAP: "Mayorista y consumidor, la última semana",
        dashboard.PAGE_CHANNELS: "Precio por región",
        dashboard.PAGE_SEASONALITY: "Índice mensual por familia, enero 2022 = 100",
        dashboard.PAGE_ALERTS: "Alertas de la semana",
    }
    for page, title in expected.items():
        app = draw_page(page)
        assert not app.exception, page
        if page != dashboard.PAGE_KPI:
            assert not app.tabs, page
        assert title in " ".join(block.value for block in app.markdown)

def test_c03_the_catalog_opens_a_query_on_github_at_its_line():
    for entry in dashboard.CATALOG:
        path, line = dashboard.find_catalog_line(entry["name"])
        lines = (PROJECT_DIR / path).read_text(encoding="utf-8").splitlines()
        assert entry["name"] in lines[line - 1] or "MATCH_COVERAGE_QUERY" in lines[line - 1]


def test_status_text_is_readable_on_light_themes():
    def contrast(first, second):
        def luminance(color):
            channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                        for c in channels]
            return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
        lighter, darker = sorted([luminance(first), luminance(second)], reverse=True)
        return (lighter + 0.05) / (darker + 0.05)
    for status in charts.STATUS_TEXT_ON_LIGHT:
        assert contrast(charts.get_status_text_color(status, charts.MODE_LIGHT), "#ffffff") >= 4.5
        assert charts.get_status_text_color(status, charts.MODE_DARK) == charts.STATUS_COLORS[status]


def test_streamlit_file_watcher_never_overlays_the_report():
    css = dashboard.build_theme_css(charts.get_palette(charts.MODE_DARK))

    assert '[data-testid="stStatusWidget"]' in css
    assert "display: none !important" in css


def test_market_ranking_handles_both_directions_missing_values_and_top_n():
    rows = pd.DataFrame({"variation": [0.1, -0.8, 0.4, float("nan"), float("inf")]})
    assert dashboard.rank_weekly_movements(rows, 2).variation.tolist() == [-0.8, 0.4]
    assert dashboard.rank_weekly_movements(rows, 2, "Alzas").variation.tolist() == [0.4, 0.1]
    assert dashboard.rank_weekly_movements(rows, 2, "Bajas").variation.tolist() == [-0.8]


@needs_database
def test_latest_gaps_keep_only_the_current_week_and_match_their_prices():
    rows = dashboard.read_cached_latest_gaps(dashboard.get_database_version())
    assert set(rows.week_start) == {dashboard.read_latest_week()}
    assert rows.margin.is_monotonic_decreasing
    assert ((rows.consumer_price / rows.wholesale_price - 1) - rows.margin).abs().max() < 1e-12


def test_mobile_rankings_keep_full_labels_and_signed_values_without_injecting_html():
    rows = pd.DataFrame({"label": ["<script>Tomate</script>", "Lechuga"], "value": [-25.0, 50.0]})
    html_text = dashboard.build_mobile_ranking_html(rows, charts.MODE_DARK, True)
    assert "<script>" not in html_text and "&lt;script&gt;Tomate&lt;/script&gt;" in html_text
    assert "-25,0 %" in html_text and "+50,0 %" in html_text
    assert 'left:25.000%;width:25.000%' in html_text


@needs_database
def test_displayed_source_blocks_are_unique_across_the_portfolio():
    seen = {}
    for title in dashboard.PAGES:
        app = draw_page(title)
        assert not app.exception, title
        for block in app.code:
            identity = (block.language, block.value.strip())
            assert identity not in seen, (seen.get(identity), title, block.language)
            seen[identity] = title


@needs_database
def test_dashboard_diagrams_and_queries_have_unique_direct_destinations():
    # Tabs are allowed only where they replace a long scroll (D-120, D-121, D-122) and
    # in the SQL studio, whose Resultados / Mensajes tabs are the client's own (D-173).
    tabbed = {dashboard.PAGE_KPI, dashboard.PAGE_DEVOPS, dashboard.PAGE_OPERATIONS, dashboard.PAGE_RUNS,
              dashboard.PAGE_SQL}
    for page in dashboard.PAGES:
        app = draw_page(page)
        assert not app.exception, page
        if page not in tabbed:
            assert not app.tabs, page
        texts = " ".join(block.value for block in app.markdown)
        assert ("<h1>¿Qué familias de alimentos subieron y bajaron?</h1>" in texts) == (page == dashboard.HOME_PAGE)
        # The journey lives in Pipeline y linaje and, since D-205, also in the SAD.
        assert ('aria-label="Recorrido de los datos de ODEPA al panel"' in texts) == (page in (dashboard.PAGE_DIAGRAMS,
                                                                                              dashboard.PAGE_SAD))
        # The lineage is the switch's second view, never drawn by default (step 4).
        assert 'aria-label="Linaje dbt: de bronce a marts"' not in texts


@needs_database
def test_business_definition_has_a_mission_vision_scope_and_acceptance_criteria():
    app = draw_page(dashboard.PAGE_BUSINESS)
    assert not app.exception
    text = " ".join(block.value for block in app.markdown)
    for heading in ["Misión", "Visión", "Alcance", "Fuera de alcance", "Criterios de aceptación",
                    "Requisitos de negocio", "Stakeholders y usuarios"]:
        assert heading in text
    assert 'data-component-kind="mission"' in text
    assert 'data-component-kind="scope"' in text


@needs_database
def test_c01_the_cover_names_the_project_reads_real_figures_and_links_every_step():
    assert dashboard.WINDOWS["El proyecto"][:2] == [dashboard.PAGE_COVER, dashboard.PAGE_BUSINESS]
    assert dashboard.OLD_PATHS["el-proyecto"][0] == dashboard.PAGE_COVER
    app = draw_page(dashboard.PAGE_COVER)
    assert not app.exception
    assert read_page_title(app) == "GreenOcean"
    text = " ".join(block.value for block in app.markdown)
    weekly_prices = dashboard.read_indicator("quality_flag_counts")["weekly_prices"].sum()
    assert dashboard.charts.format_thousands(weekly_prices) in text
    for words in ["Precios de alimentos en Chile", "El problema", "Trabajo desarrollado", "Para quién",
                  "Trazabilidad y operación", "Límites claros", "no mide ganancias"]:
        assert words in text
    # Every way out of the cover stays in the same window and names its destination.
    for view in [dashboard.PAGE_HOME, dashboard.PAGE_DIAGRAMS, dashboard.PAGE_RULES,
                 dashboard.PAGE_KPI, dashboard.PAGE_RUNS, dashboard.PAGE_BUSINESS]:
        assert f'href="{html.escape(dashboard.build_page_address(view))}" target="_self"' in text
    # The full definition keeps its own view, untouched.
    assert "Misión" not in text


def test_d065_previous_and_next_go_round_the_views_of_a_window():
    window = "Ingeniería de datos"
    key = dashboard.window_view_key(window)
    dashboard.st.session_state[key] = dashboard.PAGE_DIAGRAMS
    dashboard.step_view(window, -1)
    assert dashboard.st.session_state[key] == dashboard.read_window_views(window)[-1]
    dashboard.step_view(window, 1)
    assert dashboard.st.session_state[key] == dashboard.PAGE_DIAGRAMS


def test_security_and_database_have_distinct_functional_symbols():
    security = dashboard.build_info_card_html("Seguridad", "Control de acceso")
    database = dashboard.build_info_card_html("Base de datos", "Precios semanales")
    assert 'data-component-kind="security"' in security
    assert 'data-component-kind="database"' in database
    assert '<svg' in security and '<ellipse' in database


@needs_database
def test_d065_an_old_section_link_opens_its_view_inside_the_dashboard():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Analista BI"
    app.query_params["seccion"] = dashboard.TAB_GAP
    app.run()
    assert not app.exception
    assert read_page_title(app) == "Explorar datos de precios"
    assert "seccion" not in app.query_params


@needs_database
def test_old_section_links_can_redirect_with_a_bound_theme():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Analista BI"
    app.query_params["tema"] = "Corporativo"
    app.query_params["seccion"] = dashboard.TAB_GAP
    app.run()
    assert not app.exception
    assert read_page_title(app) == "Explorar datos de precios"


def test_d056_old_addresses_open_their_new_tab():
    assert set(dashboard.OLD_PATHS).isdisjoint(dashboard.PAGE_PATHS.values())
    for path in ["panel", "margenes", "canales-y-regiones",
                 "consultas", "centro-de-control", "calidad-de-datos", "pipeline",
                 "el-proyecto"]:
        page, tab = dashboard.OLD_PATHS[path]
        assert tab is None or dashboard.PAGE_OF_TAB[tab] == page
    assert set(dashboard.OLD_HOME_TABS.values()) <= set(dashboard.PAGE_OF_TAB)
    assert set(dashboard.OLD_HOME_TABS).isdisjoint(
        dashboard.TABS_BY_PAGE[dashboard.HOME_PAGE])


@needs_database
@pytest.mark.parametrize("title", ALL_PAGES)
def test_every_page_draws_without_errors_and_shows_the_attribution(title):
    app = draw_page(title)
    assert not app.exception
    # D-222: one line; the full notes open on hover.
    assert html.escape(dashboard.ATTRIBUTION_TEXT, quote=True) in " ".join(block.value for block in app.markdown)


@needs_database
def test_a_kpi_link_opens_its_canonical_query_without_repeating_it():
    app = draw_page(dashboard.PAGE_KPI)
    assert not [block for block in app.code if block.language == "sql"]
    # The query lives in GitHub (D-143): the link lands on its line there.
    path, line = dashboard.find_catalog_line("k7_match_coverage")
    assert dashboard.build_query_address("k7_match_coverage").endswith(f"{path}#L{line}")


def test_retired_profiles_do_not_change_the_public_route():
    for profile in (None, "Reclutamiento", "Ingeniería de datos", "Analista BI"):
        assert dashboard.start_window(profile) == dashboard.REPORT_WINDOW
        for window, views in dashboard.WINDOWS.items():
            assert dashboard.read_window_views(window, profile) == [v for v in views if v not in (dashboard.PAGE_ANALYSIS,dashboard.PAGE_GAP,dashboard.PAGE_CHANNELS)]
    assert dashboard.WINDOW_OF_VIEW[dashboard.PAGE_LINKS] == dashboard.SECTION_RESOURCES
    assert dashboard.WINDOW_OF_VIEW[dashboard.PAGE_MANUAL] == dashboard.SECTION_LINKS


@needs_database
def test_d070_a_profile_starts_its_visit_and_the_sidebar_does_not_show_it():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Ingeniería de datos"
    app.run()
    assert not app.exception
    # The visit starts at the section of the profile: Detalle técnico, its pipeline.
    assert read_page_title(app) == "¿Qué familias de alimentos subieron y bajaron?"
    sidebar = " ".join(block.value for block in app.sidebar.markdown)
    assert "Ingeniería de datos" not in sidebar
    assert not [button for button in app.sidebar.button if "perfil" in button.label]


def test_d067_report_pages_use_a_compact_header_and_short_kpi_links():
    dashboard.st.session_state[dashboard.COMPACT_VIEW] = True
    try:
        compact_link = dashboard.build_kpi_link("K6")
        assert compact_link.count(">Cómo se calcula →<") == 1
        assert ">K6" not in compact_link
    finally:
        dashboard.st.session_state[dashboard.COMPACT_VIEW] = False
    assert "¿Cómo se calcula?" in dashboard.build_kpi_link("K6")
    ranked = pd.DataFrame({"product_group": ["Frutas"], "product": ["Manzana"],
                           "variety": ["Cripps Pink"], "quality": ["Calibre 80"],
                           "channel": ["Mayorista"], "normalized_unit": ["kilo"],
                           "week_start": [pd.Timestamp("2026-10-05")],
                           "national_price": [1555.5556], "variation": [0.555556]})
    table = dashboard.format_ranking_table(ranked)
    assert table.iloc[0]["Semana"] == "05-10-2026"
    assert table.iloc[0]["Precio nacional"] == "$ 1.556"
    assert table.iloc[0]["Variación"] == "+55,6 %"


def test_d068_gaps_above_300_percent_are_a_packed_format_and_leave_the_ranking():
    gaps = pd.DataFrame({"product": ["Frutilla", "Tomate"], "margin": [8.36, 0.52]})
    comparable, excluded = dashboard.split_comparable_gaps(gaps)
    assert comparable["product"].tolist() == ["Tomate"]
    assert excluded["product"].tolist() == ["Frutilla"]
    assert dashboard.MAXIMUM_COMPARABLE_GAP == 3.0


def test_d068_short_labels_stay_unique_and_the_detail_goes_to_the_tooltip():
    rows = pd.DataFrame({"product": ["Naranja", "Naranja"], "channel": ["Supermercado"] * 2,
                         "variety": ["Lane Late", "Navel Late"], "quality": ["Primera"] * 2})
    labels = dashboard.build_short_labels(rows, lambda row: f"{row['product']} · {row['channel']}")
    assert labels[0] == "Naranja · Supermercado" and len(set(labels)) == 2
    assert labels[1].strip("\u200b") == labels[0]
    spec = str(charts.draw_horizontal_bars(pd.DataFrame(
        {"label": labels, "value": [1, 2], "value_label": ["1", "2"], "detail": ["a", "b"]}),
        "x", charts.MODE_DARK).to_dict())
    assert "'title': 'Detalle'" in spec


def test_d068_the_map_hides_channels_and_regions_almost_without_data():
    points = pd.DataFrame({"channel": ["A", "A", "A", "B"], "region": ["R1", "R2", "R3", "R1"],
                           "regional_index": [1.0, 1.1, 0.9, 1.2]})
    kept = dashboard.keep_covered_cells(points)
    assert set(kept["channel"]) == {"A"}


def test_d068_the_summary_sentence_and_figures_read_real_weekly_data():
    summary = {"latest": {"rises": 214, "falls": 180, "typical_change": 0.4, "median_gap": 61,
                          "alerts": 43},
               "previous": {"rises": 200, "falls": 190, "typical_change": 1.0,
                            "median_gap": 58, "alerts": 50},
               "strong_rises": 46, "week": pd.Timestamp("2026-10-05"),
               "top_rise": {"product": "Manzana", "channel": "Mayorista", "variation": 0.556}}
    sentence = dashboard.build_summary_sentence(summary)
    assert sentence == ("Esta semana subieron 214 series de precios y bajaron 180. 46 productos "
                        "subieron más de 10 %; la mayor alza fue Manzana en Mayorista (+55,6 %).")
    # D-072: the business figures became the summary's strip, as in the mockup.
    run = pd.Series({"status": dashboard.etl.STATUS_LOADED,
                     "started_at": "2026-10-13T18:35:00+00:00"})
    strip = dashboard.build_kpi_strip_html(summary, (219, 257), run)
    assert ">43<" in strip and "▼ 7 vs. semana anterior" in strip
    assert "85,2 %" in strip and "219 de 257" in strip and "Carga correcta" in strip
    assert "no son errores confirmados" in strip
    assert "Revisar alertas →" in strip and "Ver cobertura →" in strip
    assert strip.index("Alertas semanales") < strip.index(">43<")
    assert "Una alerta invita a revisar; no explica la causa." in strip
    assert "Observaciones históricas" not in strip


def test_d069_a_product_filter_keeps_its_key_channel_and_a_short_name():
    row = {"product_group": "Frutas", "product": "Manzana", "variety": "Cripps Pink",
           "quality": "Calibre 80", "normalized_unit": "kilo", "channel": "Mayorista"}
    product = dashboard.build_product_filter(row)
    assert product["name"] == "Manzana Cripps Pink" and product["channel"] == "Mayorista"
    rows = pd.DataFrame([row, dict(row, product="Pera")])
    assert dashboard.keep_product(rows, product)["product"].tolist() == ["Manzana"]
    assert len(dashboard.keep_product(rows, None)) == 2


def test_d069_clickable_bars_carry_a_selection_and_the_map_too():
    rows = pd.DataFrame({"label": ["A", "B"], "value": [5.0, -2.0], "pick": ["0", "1"]})
    spec = charts.draw_variation_bars(rows, charts.MODE_DARK, select_field="pick").to_dict()
    assert "'name': 'pick'" in str(spec) and "'fields': ['pick']" in str(spec)
    points = pd.DataFrame({"region": ["Región del Maule"], "channel": ["Feria libre"],
                           "regional_index": [1.2], "detail": ["x"]})
    spec = str(charts.draw_region_channel_map(points, charts.MODE_DARK, "Región del Maule")
               .to_dict())
    assert "'fields': ['region']" in spec and "120" in spec


@needs_database
def test_d069_map_scope_replaces_permanent_selectors_and_context_holds_across_views():
    dashboard_bar = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    dashboard_bar.query_params["perfil"] = "Analista BI"
    dashboard_bar.run()
    assert not dashboard_bar.exception
    # Only the two filters of the products table: no permanent selectors (D-092).
    assert {box.key for box in dashboard_bar.main.selectbox} == {'home_products_channel', 'home_products_order'}
    assert [box.key for box in dashboard_bar.text_input] == ['home_products_search']
    dashboard_bar.session_state['dashboard_group'] = 'Frutas'
    dashboard_bar.run()
    assert dashboard_bar.session_state["dashboard_group"] == "Frutas"
    dashboard_bar.query_params["vista"] = dashboard.PAGE_ANALYSIS
    dashboard_bar.run()
    assert not dashboard_bar.exception
    assert dashboard_bar.session_state["dashboard_group"] == "Frutas"


def test_d069_a_whole_row_takes_the_click_not_only_its_bar():
    rows = pd.DataFrame({"label": ["A", "B"], "value": [1.2, -0.1], "pick": ["A", "B"]})
    layers = charts.draw_variation_bars(rows, charts.MODE_DARK, select_field="pick").to_dict()
    # Altair lifts the selection to the top and names the layer that carries it.
    [selection] = [param for param in layers["params"] if param["name"] == "pick"]
    [target] = [layer for layer in layers["layer"] if layer.get("name") in selection["views"]]
    # That layer is an almost invisible band as wide as the chart.
    assert target["mark"]["opacity"] < 0.01 and "x2" in target["encoding"]


@needs_database
def test_d069_a_click_filter_reaches_the_bar_and_the_map_starts_with_two_regions():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Analista BI"
    app.session_state["dashboard_group"] = "Frutas"
    app.run()
    assert not app.exception
    assert {box.key for box in app.main.selectbox} == {'home_products_channel', 'home_products_order'}
    assert app.session_state['dashboard_group'] == 'Frutas'
    texts = " ".join(block.value for block in app.markdown)
    assert "tiene precio en una sola región" not in texts


def read_product_names(app):
    """Product cells of the products table, in display order."""
    markup = ' '.join(block.value for block in app.markdown)
    table = re.search(r'<div class="mock-products-table".*?</table>', markup).group(0)
    return re.findall(r'<td><strong>([^<]+)</strong>', table)


@needs_database
def test_d093_search_ignores_case_and_accents_and_matches_the_start_of_any_word():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params.update(PINNED_HOME)
    app.run()
    assert not app.exception
    every = read_product_names(app)
    app.text_input(key="home_products_search").set_value("LECH").run()
    lettuces = read_product_names(app)
    assert lettuces and len(lettuces) < len(every)
    assert all(name.lower().startswith("lechuga") for name in lettuces)
    # «esp» starts the variety «Española»; it does not match inside a word.
    app.text_input(key="home_products_search").set_value("esp").run()
    assert "Lechuga · Española" in read_product_names(app)
    app.text_input(key="home_products_search").set_value("echuga").run()
    assert not read_product_names(app)
    assert "Ningún producto empieza por «echuga»" in " ".join(block.value for block in app.markdown)
    assert dashboard.matches_product_search({"product": "Ají", "variety": "Cacho de cabra"}, "AJI cab")


@needs_database
def test_d071_a_theme_chosen_in_the_header_holds_for_the_whole_visit():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Reclutamiento"
    app.run()
    assert not app.exception
    assert app.query_params["tema"] == "Corporativo"
    app.radio(key="theme_field").set_value(
        "Dark Grey").run()
    assert not app.exception
    assert app.session_state[dashboard.THEME_STATE] == "Dark Grey"
    assert app.query_params["tema"] == "Dark Grey"
    app.query_params["vista"] = dashboard.PAGE_ANALYSIS
    app.run()
    assert app.session_state[dashboard.THEME_STATE] == "Dark Grey"


@needs_database
def test_appearance_change_preserves_report_filters_without_a_profile_selector():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['perfil'] = 'Analista BI'
    app.run()
    app.session_state['dashboard_group'] = 'Frutas'
    app.run()
    app.radio(key='theme_field').set_value('Dark Grey').run()
    assert not app.exception
    assert app.session_state['dashboard_group'] == 'Frutas'
    assert app.query_params['tema'] == 'Dark Grey'
    assert 'perfil' not in app.query_params
    assert not [box for box in app.selectbox if box.label == 'Perfil']


def test_old_combined_code_and_technical_addresses_keep_their_destinations():
    assert dashboard.OLD_PATHS['codigo-y-resultados'][0] == dashboard.PAGE_HOME
    assert dashboard.OLD_PATHS['detalle-tecnico'][0] == dashboard.PAGE_DIAGRAMS


def test_plain_ranking_answer_keeps_the_direction_and_real_percentage():
    base = {'product': 'Tomate', 'channel': 'Feria libre', 'variation': .125}
    assert 'subió 12,5 %' in dashboard.describe_ranking_change(base)
    assert 'frente a la semana anterior' in dashboard.describe_ranking_change(base)
    assert 'bajó 12,5 %' in dashboard.describe_ranking_change(base | {'variation': -.125})
    assert 'no cambió' in dashboard.describe_ranking_change(base | {'variation': 0})


def test_plain_regional_answer_distinguishes_above_below_and_average():
    base = {'region': 'Región de Valparaíso', 'channel': 'Feria libre', 'regional_index': 1.15}
    assert '15,0 % por encima' in dashboard.describe_regional_comparison(base)
    assert 'por debajo' in dashboard.describe_regional_comparison(base | {'regional_index': .83})
    assert 'igual al promedio' in dashboard.describe_regional_comparison(base | {'regional_index': 1})


@needs_database
def test_dashboard_explains_its_graphs_and_collapses_family_tables():
    app = draw_page(dashboard.PAGE_HOME)
    assert not app.exception
    text = ' '.join(block.value for block in app.markdown)
    assert 'En palabras simples:' not in text
    assert 'Movimiento por familia' in ' '.join(block.value for block in app.markdown)
    assert 'Variación' in text and 'Regiones ↑ / ↓' in text
    # The coverage note moved under the products table, with its two references.
    assert 'sin comparación válida' in text and '>Calidad</a>' in text and '>Metodología</a>' in text
    assert not app.expander
    for page in [dashboard.PAGE_OPERATIONS]:
        detail = draw_page(page)
        assert not detail.exception
        assert all(not block.proto.expanded for block in detail.expander)


@needs_database
def test_historical_root_link_keeps_the_requested_project_view_after_route_change():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params.update({'perfil': 'Reclutamiento', 'vista': dashboard.PAGE_KPI, 'kpi': 'K5'})
    app.run()
    assert not app.exception
    assert read_page_title(app) == dashboard.SECTION_KPI
    assert app.query_params['kpi'] == 'K5'
    assert 'perfil' not in app.query_params


def test_smart_criteria_cover_each_kpi_without_inventing_goals():
    for identifier in dashboard.KPI_PRESENTATION:
        detail = dashboard.build_kpi_smart_html(identifier)
        for criterion in ("S · Específico", "M · Medible", "A · Alcanzable", "R · Relevante", "T · Temporal"):
            assert criterion in detail
        assert "metas que todavía no se han acordado" in detail
        assert "No hay meta acordada" in detail
        assert "El plazo de una meta se define" in detail
    assert "26 semanas" in dashboard.build_kpi_smart_html("K5")
    assert "12 semanas" in dashboard.build_kpi_smart_html("K6")
    assert "histórico disponible" in dashboard.build_kpi_smart_html("K7")


@needs_database
def test_d096_header_shows_the_current_path_without_a_tab_bar():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['vista'] = dashboard.PAGE_ARCHITECTURE
    app.run()
    assert not app.exception
    assert 'graph-navigation' not in ' '.join(block.value for block in app.markdown)
    markup = ' '.join(block.value for block in app.get('html')) + ' '.join(c.value for c in app.markdown)
    assert 'Ingeniería de datos › Modelo de datos' in markup
    assert app.button(key='return_to_previous').label == 'Volver'


def test_return_context_restores_only_supported_selection_fields():
    import base64
    payload = base64.b64encode(json.dumps({"dashboard_group": "Frutas", "dashboard_top_n": 8,
        "admin_token": "not-a-selection", "dashboard_product": {"bad": "shape"}}).encode()).decode()
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "import streamlit as st\nfrom bi import dashboard\n"
              f"st.query_params['_ctx'] = {payload!r}\ndashboard.restore_return_context()\n")
    app = AppTest.from_string(script).run()
    assert not app.exception
    assert app.session_state['dashboard_group'] == 'Frutas'
    assert app.session_state['dashboard_top_n'] == 8
    assert '_ctx' not in app.query_params
    with pytest.raises(KeyError):
        app.session_state['admin_token']
    with pytest.raises(KeyError):
        app.session_state['dashboard_product']


@needs_database
def test_summary_ranking_orders_change_rows_and_keep_real_prices_visible():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not app.exception
    assert app.selectbox(key='home_products_order').options == list(dashboard.PRODUCT_ORDERS)
    def rows():
        markup = ' '.join(block.value for block in app.markdown)
        table = re.search(r'<div class="mock-products-table".*?</table>', markup).group(0)
        return [('1 cotización' in row, float(value.replace('−', '-').replace(',', '.')))
                for row in table.split('<tr')[2:]
                for value in re.findall(r'<td class="num (?:rise|fall|neutral)"><b>([+−]?[\d,]+) %</b>', row)]
    def changes():
        return [value for _, value in rows()]
    # D-146: changes resting on one quote go after the others; each group is sorted.
    shown = rows()
    flags = [thin for thin, _ in shown]
    assert flags == sorted(flags)
    for group in (True, False):
        values = [abs(value) for thin, value in shown if thin == group]
        assert values == sorted(values, reverse=True)
    largest = changes()
    app.selectbox(key='home_products_order').set_value('Bajadas').run()
    assert not app.exception
    for group in (True, False):
        values = [value for thin, value in rows() if thin == group]
        assert values == sorted(values)
    # «Inusuales» keeps only national alerts.
    app.selectbox(key='home_products_order').set_value('Inusuales').run()
    assert not app.exception and len(changes()) < len(largest)
    app.query_params['_home_region'] = 'Región de Coquimbo'
    app.run()
    assert 'Inusuales' not in app.selectbox(key='home_products_order').options


def test_regional_changes_match_region_channel_and_require_previous_week_price():
    common = {column: "same" for column in dashboard.queries.KEY_COLUMNS}
    current = pd.DataFrame([{**common, "region": "A", "channel": "X", "price": 120},
                            {**common, "region": "B", "channel": "X", "price": 100}])
    previous = pd.DataFrame([{**common, "region": "A", "channel": "X", "price": 100},
                             {**common, "region": "B", "channel": "Y", "price": 50}])
    result = dashboard.regional_week_changes(current, previous)
    assert result.iloc[0]["weekly_change"] == pytest.approx(20)
    assert pd.isna(result.iloc[1]["weekly_change"])


@needs_database
def test_all_kpi_observations_have_real_results_and_explicit_periods():
    for identifier in dashboard.KPI_PRESENTATION:
        observation = dict(dashboard.read_kpi_observation(dashboard.get_database_version(), identifier))
        assert "Resultado observado" in observation, identifier
        assert "Periodo del resultado" in observation, identifier
        assert any(label in observation for label in ("Comparación", "Referencia de cálculo")), identifier


@needs_database
def test_d220_quality_and_audit_are_one_view_without_pickers():
    app = draw_page(dashboard.PAGE_OPERATIONS)
    assert not app.exception
    assert read_page_title(app) == 'Calidad y auditoría'
    assert not app.selectbox and not app.get('segmented_control')
    assert len(app.get('iframe')) == 1


@needs_database
def test_d171_a_card_opens_its_evidence_with_the_rows_the_method_and_a_recheck():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\nimport streamlit as st\n"
              "from bi import dashboard\n"
              "st.session_state[dashboard.QUALITY_OPEN_KEY] = 'Pruebas dbt de la última construcción'\n"
              "dashboard.render_page(dashboard.PAGE_OPERATIONS)\n")
    app = AppTest.from_string(script, default_timeout=90).run()
    assert not app.exception
    assert 'RN-14' in list(app.dataframe[0].value['Regla'])
    assert any(block.value.startswith('SELECT') for block in app.code)
    assert app.button(key='qa_recheck')


@needs_database
def test_d096_sidebar_is_a_flat_explorer_with_every_section_open_by_default():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['vista'] = dashboard.PAGE_ARCHITECTURE
    app.query_params['ver'] = 'ingenieria'
    app.run()
    assert not app.exception
    # Every section, including the current one, starts closed. Top-level rows are
    # folders because each one exposes at least one real destination.
    assert not app.sidebar.expander
    raw_labels = [link.proto.label for link in app.sidebar.get('page_link')]
    labels = [label.removeprefix('›  ') for label in raw_labels]
    # «El proyecto» and the old «Documentación» folder of six pages are now three
    # profile views — BI, BA, IT — behind one folder, the same pattern as every
    # other section (D-105, D-110). «Código» merges into «GitHub», a single
    # destination: nobody browses source files in the sidebar when the real
    # repository is one link away (D-106). GitHub itself shows its own mark, not
    # the word, as a markdown link rather than a page_link (D-117).
    # Every folder starts open (D-139): the whole map of the app at a glance.
    # Step 4 of the refonte: Ingeniería de datos, four pages; DevOps joined Ejecuciones.
    assert 'DevOps y seguridad' not in labels
    for child in ['Resumen semanal', 'Pipeline y linaje', 'Modelo de datos', 'Calidad y auditoría',
                  'Centro de operación', 'Mapa de seguridad', 'Plan de pruebas de seguridad',
                  'PRD · Requisitos del producto', 'SAD · Arquitectura', 'ADR · Decisiones de arquitectura']:
        assert child in labels
    sidebar_markup = " ".join(block.value for block in app.sidebar.markdown)
    assert 'class="sidebar-github' in sidebar_markup and 'aria-label="GitHub del proyecto"' in sidebar_markup
    for retired in ['Archivos del proyecto', 'Descripción general', 'Manual', 'Glosario',
                    'Fuentes y enlaces']:
        assert retired not in labels
    assert dashboard.PAGE_ALERTS not in labels
    folder_buttons = [button for button in app.sidebar.button if str(button.key).startswith('nav_toggle_')]
    toggles = {button.label for button in folder_buttons}
    # «Fuentes» (D-118): the two ODEPA datasets, a folder like every other section.
    # D-201: security has its own folder.
    assert toggles == {'⌄  ' + title for title in MENU_BLOCKS} | {'⌄  Fuentes'}
    assert all(not button.help for button in folder_buttons)
    css = ' '.join(block.value for block in app.sidebar.markdown)
    assert '[class*="st-key-nav_child_"] {margin-left:0; padding-left:0; border-left:0;}' in css
    assert f'color:{dashboard.BRAND_GREEN_DARK} !important;' in dashboard.build_sidebar_css(charts.MODE_DARK)
    # Corporativo's page is light, but its navy sidebar uses the same luminous
    # green as the wordmark. Blue Light keeps the darker green on its light sidebar.
    assert f'color:{dashboard.BRAND_GREEN_DARK} !important;' in dashboard.build_sidebar_css(charts.MODE_CORPORATE)
    assert f'color:{dashboard.BRAND_GREEN_LIGHT} !important;' in dashboard.build_sidebar_css(charts.MODE_BLUE_LIGHT)
    for mode in charts.THEMES:
        expected = (dashboard.BRAND_GREEN_DARK if
                    dashboard.is_dark_surface(charts.get_palette(mode)['sidebar']) else
                    dashboard.BRAND_GREEN_LIGHT)
        assert expected in dashboard.build_greenocean_logo(mode, sidebar=True)
        assert f'color:{expected} !important;' in dashboard.build_sidebar_css(mode)
    assert 'background:transparent !important; border-color:transparent; box-shadow:none !important;' in css


@needs_database
def test_d102_a_folder_row_really_folds_like_vs_code():
    """Folders start open (D-139); a click folds one and a second click opens it."""
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['ver'] = 'ingenieria'
    app.run()
    toggle = next(b for b in app.sidebar.button if str(b.key) == 'nav_toggle_ingenieria')
    assert toggle.label == '⌄  Ingeniería de datos'
    assert 'Pipeline y linaje' in [link.proto.label for link in app.sidebar.get('page_link')]
    toggle.click().run()
    assert not app.exception
    toggle = next(b for b in app.sidebar.button if str(b.key) == 'nav_toggle_ingenieria')
    assert toggle.label == '›  Ingeniería de datos'
    assert 'Pipeline y linaje' not in [link.proto.label for link in app.sidebar.get('page_link')]
    toggle.click().run()
    assert not app.exception
    assert 'Pipeline y linaje' in [link.proto.label for link in app.sidebar.get('page_link')]


def test_d113_the_github_link_opens_a_new_tab_with_its_mark():
    link = dashboard.build_github_link_html("Ver el registro completo de decisiones",
                                            "https://github.com/example/example")
    assert 'target="_blank"' in link and 'rel="noopener noreferrer"' in link
    assert '<svg' in link and 'doc-github-icon' in link
    app = draw_page(dashboard.PAGE_PRD)
    text = " ".join(block.value for block in app.markdown)
    assert 'docs/PRD.md en GitHub' in text and 'target="_blank"' in text


def test_d113_the_global_click_handler_only_forces_internal_links():
    script = dashboard.build_visit_history_script()
    assert "anchor.hostname === location.hostname" in script
    assert "anchor.target = '_self'" in script


@needs_database
def test_d118_sources_is_its_own_folder_with_two_external_children():
    """ODEPA is not GitHub: it gets its own sidebar folder, «Fuentes», with the
    two datasets as external children in the same green as every other child."""
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    toggle = next(button for button in app.sidebar.button if str(button.key) == 'nav_toggle_fuentes')
    # D-209: Fuentes starts folded; a click opens it.
    assert toggle.label == '⌄  Fuentes'
    markup = " ".join(block.value for block in app.sidebar.markdown)
    for name, url in dashboard.SOURCE_LINKS:
        assert f'class="nav-source-link" href="{url}"' in markup
        assert name in markup
    assert markup.count('target="_blank"') >= 2
    assert 'nav-source-icon' in markup
    next(button for button in app.sidebar.button
         if str(button.key) == 'nav_toggle_fuentes').click().run()


@needs_database
def test_d117_the_sidebar_github_entry_is_a_logo_not_a_word():
    # Since D-124 the mark sits in the sidebar footer on a light pill, not in the list.
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    markup = " ".join(block.value for block in app.sidebar.markdown)
    assert markup.count('class="sidebar-github') == 1
    assert 'nav_toggle_enlaces' not in [str(button.key) for button in app.sidebar.button]
    assert dashboard.architecture.brand_icons.logo_body("github") in markup
    assert '>GitHub<' not in markup
    assert 'href="enlaces' in markup and 'target="_self"' in markup


@needs_database
def test_d116_every_github_link_shows_the_real_mark_and_opens_a_new_tab():
    """Every PROJECT_LINKS entry points at GitHub and opens a new tab; the real
    GitHub mark crowns the page. ODEPA moved to «Fuentes» (D-118)."""
    app = draw_page(dashboard.PAGE_LINKS)
    assert not app.exception and app.get('iframe')
    markup = github_page.build_github_page_html(dashboard.get_mode())
    github_links = [link for link in project.PROJECT_LINKS
                    if link["url"] and link["url"].startswith(project.GITHUB_URL)]
    assert github_links == [link for link in project.PROJECT_LINKS if link["url"]]
    assert len(github_links) >= 5
    assert dashboard.architecture.brand_icons.logo_body("github") in markup
    assert markup.count('target="_blank"') >= len(github_links) + 1


def test_d111_the_weekly_run_sentence_never_ends_on_a_dangling_colon():
    sentence = dashboard.describe_weekly_run()
    assert sentence.endswith('.') and not sentence.rstrip('.').endswith(':')
    assert 'Hace, en orden' not in sentence


@needs_database
def test_d102_the_current_window_also_starts_open_and_can_be_toggled():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.run()
    toggle = next(b for b in app.sidebar.button if str(b.key) == 'nav_toggle_negocio')
    assert not toggle.disabled
    assert toggle.label == '⌄  Negocio · BI'
    assert 'Resumen semanal' in [link.proto.label for link in app.sidebar.get('page_link')]
    toggle.click().run()
    assert not app.exception
    assert next(b for b in app.sidebar.button if str(b.key) == 'nav_toggle_negocio').label == '›  Negocio · BI'
    assert 'Resumen semanal' not in [link.proto.label for link in app.sidebar.get('page_link')]


@needs_database
def test_d100_alert_dialog_is_styled_from_every_page_not_only_the_summary():
    """The trigger moved into the shared sidebar footer (D-096); its CSS must follow (D-100)."""
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['vista'] = dashboard.PAGE_ARCHITECTURE
    app.run()
    assert not app.exception
    # D-169: the trigger lives on top of the Resumen only; other pages carry neither it
    # nor the dialog's stylesheet.
    assert not [button for button in app.button if str(button.key) == 'home_alert_trigger']
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    markup = ' '.join(block.value for block in app.get('html')) + ' '.join(c.value for c in app.markdown)
    assert '.home-alert-gallery-legend' in markup and '[class*="st-key-home_alert_card_"]' in markup
    app.button(key='home_alert_trigger').click().run()
    assert not app.exception
    markup = ' '.join(block.value for block in app.get('html')) + ' '.join(c.value for c in app.markdown)
    assert 'home-alert-overview-marker' in markup


@needs_database
def test_gap_screen_starts_with_all_product_ranking_and_exposes_only_exact_top_sample():
    app = draw_page(dashboard.PAGE_GAP)
    assert not app.exception
    assert dashboard.TOP_N_RANGE == (1, 100)
    assert any(slider.key == 'dashboard_top_n' for slider in app.slider)
    text = ' '.join(block.value for block in app.markdown)
    assert text.index('¿Dónde es mayor la brecha esta semana?') < text.index('Muestra del gráfico')
    assert 'chart-sample' in text and 'Mayorista' in text and 'Consumidor' in text
    assert '&lt;span class=' not in text
    assert any(item.value == 'Detalle de un producto' for item in app.subheader)
    comparable, _ = dashboard.read_report_gaps(dashboard.read_report_week(), dashboard.read_filter('group'), dashboard.read_filter('region'), None)
    assert dashboard.charts.format_signed_percent(comparable.iloc[0]['margin'] * 100) in text


@needs_database
def test_ranking_click_updates_detail_without_narrowing_the_overview():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "import streamlit as st\nfrom bi import dashboard\n"
              "st.session_state['dashboard_group'] = dashboard.ALL_VALUES\n"
              "rows, _ = dashboard.read_report_gaps(dashboard.read_report_week(), dashboard.ALL_VALUES, dashboard.ALL_VALUES, None)\n"
              "dashboard.select_ranked_product(rows.iloc[0], detail=True)\n")
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    product = app.session_state['dashboard_product']
    assert app.session_state['analysis_product'] == product['key']['product']
    assert app.session_state['analysis_group'] == product['key']['product_group']
    assert app.session_state['analysis_channels'] == [product['channel']]
    assert app.session_state['dashboard_group'] == dashboard.ALL_VALUES


@needs_database
def test_alert_sample_preserves_displayed_severity_order():
    rows = dashboard.read_price_alerts()
    rows = rows[rows['week_start'] == rows['week_start'].max()]
    distance = (rows['variation'] - rows['usual_variation']).abs() / rows['variation_deviation']
    ranked = rows.loc[distance.sort_values(ascending=False).index].head(8)
    sample = dashboard.format_alerts(ranked, keep_order=True)
    assert sample['Producto'].tolist() == [dashboard.describe_product(row) for row in ranked.to_dict('records')]
    assert sample['Variación'].iloc[0] == dashboard.charts.format_signed_percent(ranked.iloc[0]['variation'] * 100)


def test_movement_ring_parts_cover_comparable_series_not_the_top_n():
    rows = pd.DataFrame({'variation': [0.2] * 12 + [-.1] * 4 + [0.] * 4 + [float('nan')]})
    parts = dashboard.build_movement_proportions(rows)
    assert parts['value'].tolist() == [12, 4, 4]
    assert parts['share'].tolist() == [60., 20., 20.]
    assert parts['value'].sum() == 20
    empty = dashboard.build_movement_proportions(rows.iloc[:0])
    assert empty['value'].sum() == 0 and empty['share'].sum() == 0


def test_d094_old_history_links_open_the_new_page():
    assert dashboard.RETIRED_VIEWS['Histórico y estacionalidad'] == dashboard.PAGE_SEASONALITY == 'Contexto del precio'


def test_business_header_order_and_retired_views_are_not_in_the_menu():
    views=dashboard.read_window_views(dashboard.REPORT_WINDOW)
    assert not set([dashboard.PAGE_ANALYSIS,dashboard.PAGE_GAP,dashboard.PAGE_CHANNELS]) & set(views)
    assert 'datos_modo=brecha' in dashboard.build_page_address(dashboard.PAGE_GAP)


@needs_database
def test_data_browser_pages_then_resets_on_filter_change():
    app=draw_page(dashboard.PAGE_DATA)
    assert not app.exception
    assert len(app.dataframe[0].value)==100
    first=app.dataframe[0].value.copy()
    app.button(key='data_next').click().run()
    assert not app.exception and app.session_state['data_page']==1
    assert not first.equals(app.dataframe[0].value)
    app.selectbox(key='data_filter_region').set_value('Región de Coquimbo').run()
    assert not app.exception and app.session_state['data_page']==0
    assert set(app.dataframe[0].value['Región'])=={'Región de Coquimbo'}
    app.radio(key='data_mode').set_value(dashboard.data_browser.MODES[2]).run()
    assert not app.exception and 'Mayorista ($)' in app.dataframe[0].value


@needs_database
def test_alert_top_n_has_its_own_8_to_100_control_and_previous_prices():
    app=draw_page(dashboard.PAGE_ALERTS)
    assert not app.exception
    slider=app.slider(key='alerts_top_n')
    assert slider.value==20 and slider.min==8 and slider.max==100
    slider.set_value(100).run()
    assert not app.exception
    assert 'Precio anterior' in ' '.join(block.value for block in app.markdown)


@needs_database
def test_d128_the_price_alert_closes_the_list_in_red_away_from_the_github_mark():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not app.exception
    alert = app.button(key="home_alert_trigger")
    assert alert.label.startswith("▲  Alerta de precio · ")
    # D-169: the trigger sits on top of the Resumen, out of the sidebar.
    assert alert not in app.sidebar.button
    css = " ".join(block.value for block in app.sidebar.markdown)
    assert ".st-key-home_alert_bar" in css
    # The footer keeps only Apariencia and the GitHub mark.
    assert 'class="sidebar-github' in css


@needs_database
def test_d165_the_operation_centre_reads_like_the_dashboard():
    # D-165 replaced the strip of four figures and the history table (D-129) by the
    # path of the run beside three facts and the latest runs.
    app = draw_page(dashboard.PAGE_RUNS)
    assert not app.exception and app.get("iframe")
    text = " ".join(block.value for block in app.markdown)
    assert 'class="compact-header"' in text and text.count('class="oc-fact"') == 3
    assert "Ver historial de ejecuciones" not in [expander.label for expander in app.expander]
    assert "runs_reload" in [str(button.key) for button in app.button]


def test_d129_the_github_page_names_actions_so_it_is_not_confused_with_ejecuciones():
    names = [link["name"] for link in project.PROJECT_LINKS]
    assert "GitHub Actions" in names and "Ejecuciones" not in names


@needs_database
def test_d151_documentation_is_the_prd_sad_and_adr_without_code():
    assert dashboard.WINDOWS[dashboard.SECTION_LINKS][:3] == [dashboard.PAGE_PRD, dashboard.PAGE_SAD, dashboard.PAGE_ADR]
    # D-205: the document views in their own frame, the live panel diagrams inline.
    for page, framed, inline in ((dashboard.PAGE_PRD, 2, 0), (dashboard.PAGE_SAD, 0, 3), (dashboard.PAGE_ADR, 0, 0),
                                 (dashboard.PAGE_SECURITY_PLAN, 1, 0)):
        app = draw_page(page)
        assert not app.exception and not app.code
        text = " ".join(block.value for block in app.markdown)
        assert "[[diagrama:" not in text and text.count('class="doc-diagram"') == inline, page
        assert len(app.get("iframe")) == framed, page
    for path, page in (("documentacion-bi", dashboard.PAGE_PRD), ("documentacion-it", dashboard.PAGE_SAD)):
        assert dashboard.OLD_PATHS[path] == (page, None)


@needs_database
def test_d160_the_ipc_itself_has_a_chart_with_its_real_figures():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "from bi import dashboard\ndashboard.show_ipc_dialog('Claro')\n")
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    captions = ' '.join(c.value for c in app.caption)
    assert 'base 2023 = 100' in captions and 'en los últimos 12 meses' in captions
    assert app.get('arrow_vega_lite_chart') or app.get('vega_lite_chart')


def test_d161_a_yearly_change_splits_into_inflation_and_own_part():
    weeks = pd.to_datetime(["2025-10-06", "2026-10-05"])
    rows = pd.DataFrame({"week_start": weeks, "national_price": [1000.0, 1150.0]})
    ipc = pd.DataFrame({"week_start": weeks, "real_factor": [1.10, 1.0]})
    split = dashboard.split_yearly_change(rows, ipc, "2026-10-05")
    assert split["change"] == pytest.approx(150)
    assert split["inflation"] == pytest.approx(100)  # the old price risen with a +10 % food IPC
    assert split["own"] == pytest.approx(50)
    assert dashboard.split_yearly_change(rows.iloc[1:], ipc, "2026-10-05") is None


@needs_database
def test_d163_the_page_answers_one_question_with_families_against_the_ipc():
    app = draw_page(dashboard.PAGE_SEASONALITY)
    assert not app.exception and not app.expander and not app.tabs
    text = ' '.join(block.value for block in app.markdown)
    for expected in ['¿Qué alimentos subieron más que la inflación?', 'Índice mensual por familia, enero 2022 = 100']:
        assert expected in text, expected
    assert 'la canasta de alimentos del INE subió' in text
    # D-167 / D-174: one card per family, the same chart size and the same y scale.
    charts_drawn = app.get('vega_lite_chart')
    assert len(charts_drawn) == 8  # seven families and the IPC basket itself
    domains = {json.dumps(json.loads(chart.proto.spec)['encoding']['y']['scale']['domain']) for chart in charts_drawn}
    assert len(domains) == 1
    heads = [block.value for block in app.markdown if block.value.startswith('<div class="inf-panel-head">')]
    assert len(heads) == 8 and sum('inflación' in head for head in heads) == 7
    assert 'la canasta de referencia' in heads[-1]
    # Retired as noise: the usual-range band, the next-months strip, the outlier table,
    # the ranking card and the product history (D-167).
    for gone in ['Rango habitual', 'Qué suele pasar', 'con precio fuera de lo habitual para la época',
                 'Desde enero 2022, frente a la inflación', 'toda su historia']:
        assert gone not in text


@needs_database
def test_d163_without_inflation_the_ipc_is_the_flat_reference_and_the_pesos_are_named():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\nimport streamlit as st\n"
              "from bi import dashboard\nst.session_state[dashboard.CONTEXT_BASIS_KEY] = dashboard.BASIS_REAL\n"
              "dashboard.render_page(dashboard.PAGE_SEASONALITY)\n")
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    assert 'Sin inflación: la línea punteada es la canasta del INE (100)' in ' '.join(b.value for b in app.markdown)


def test_d191_file_sizes_for_the_storage_diagram():
    sizes = dashboard.read_store_sizes()
    assert sizes["served"].endswith("MB") and sizes["backup"].endswith("MB") and "MB" in sizes["raw"]
    assert dashboard.format_file_size(18_624_512) == "19 MB" and dashboard.format_file_size(2_500_000) == "2,5 MB"


@needs_database
def test_d195_the_model_page_has_three_views_and_the_third_is_the_entity_relationship_diagram():
    assert dashboard.MODEL_VIEWS == ["Dónde viven los datos", "Modelo estrella", "Entidad-relación", "Cruces entre bases"]
    app = draw_page(dashboard.PAGE_ARCHITECTURE, state={dashboard.MODEL_VIEW_KEY: "Entidad-relación"})
    assert not app.exception and not app.tabs
    joined = " ".join(block.value for block in app.markdown)
    assert 'aria-label="Modelo entidad-relación de datos.duckdb"' in joined
    assert joined.count('class="er-table ') == 9 and "PK, FK" in joined
    assert 'aria-label="Modelo estrella de datos.duckdb"' not in joined  # one view at a time


MENU_BLOCKS = {
    'Negocio · BI': ['Resumen semanal', 'Precios e inflación'],
    'Ingeniería de datos': ['Pipeline y linaje', 'Modelo de datos', 'Calidad y auditoría', 'Consultas SQL',
                            'SAD · Arquitectura'],
    'DevOps y seguridad': ['Centro de operación', 'Mapa de seguridad', 'Plan de pruebas de seguridad'],
    'Stack y evidencia': ['Stack y evidencia'],
    'Análisis de negocio · BA': ['PRD · Requisitos del producto', 'ADR · Decisiones de arquitectura', 'Escalabilidad'],
}


@needs_database
def test_d213_the_menu_is_colored_blocks_open_by_default_with_every_page_once():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not app.exception
    assert not app.sidebar.selectbox
    toggles = [b.label for b in app.sidebar.button if str(b.key).startswith('nav_toggle_')]
    assert toggles == [f'⌄  {title}' for title in list(MENU_BLOCKS) + ['Fuentes']]
    labels = [link.proto.label for link in app.sidebar.get('page_link')]
    assert labels == [page for pages in MENU_BLOCKS.values() for page in pages]
    assert all(link.proto.icon for link in app.sidebar.get('page_link'))
    markup = " ".join(block.value for block in app.sidebar.markdown)
    assert markup.count('class="nav-source-link"') == len(dashboard.SOURCE_LINKS)
    # D-215: every block is a card in one of the four tones, with its own accent and corner brackets.
    # D-223: one grey scale, darkest on top, each card a different step; no colored accents.
    tones = [tone for _, _, tone, _ in dashboard.MENU_BLOCKS]
    assert tones == sorted(tones) and len(set(tones)) == len(tones)
    for background, text, title in dashboard.CARD_TONES:
        red, green, blue = (int(background[i:i + 2], 16) for i in (1, 3, 5))
        assert max(red, green, blue) - min(red, green, blue) <= 12  # a grey, not a color
    for key, *_ in dashboard.MENU_BLOCKS:
        assert f'.st-key-nav_group_{key} button p' in markup and f'.st-key-nav_block_{key} {{' in markup


@needs_database
def test_d213_an_old_profile_address_still_opens_its_page():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['ver'] = 'reclutador'
    app.query_params['vista'] = dashboard.PAGE_RUNS
    app.run()
    assert not app.exception
    assert 'ver' not in app.query_params


@needs_database
def test_d211_stack_page_shows_every_logo_linked_to_its_page_and_real_figures():
    app = draw_page(dashboard.PAGE_STACK)
    assert not app.exception
    page = " ".join(block.proto.body for block in app.get("html"))
    assert page.count('class="stack-item"') == 9 and page.count('role="tooltip"') == 9
    for key, name, what, target in stack_page.STACK:
        assert target in dashboard.WINDOW_OF_VIEW, target
        assert html.escape(what) in page
    assert "vista=Consultas+SQL" in page
    for value in stack_page.read_figures().values():
        assert stack_page.format_number(value) in page


def test_d222_every_page_fits_the_window_with_a_readable_floor():
    script = dashboard.FIT_SCREEN_SCRIPT
    assert script.startswith("<script>") and script.count("<script") == 1
    assert str(dashboard.FIT_MIN_ZOOM) in script and 0.6 <= dashboard.FIT_MIN_ZOOM < 1
    # Phones keep their own layout (D-166); the folded menu is read from data-collapsed.
    assert "innerHeight <= 500" in script
    assert 'aria-expanded' not in dashboard.build_sidebar_css(charts.MODE_DARK)


def test_d223_the_folded_menu_pushes_the_page_under_the_logo():
    import inspect
    source = inspect.getsource(dashboard.show_app_header)
    assert '[data-testid="stSidebar"][data-collapsed="true"]) [data-testid="stMain"] {{padding-top:52px' in source
