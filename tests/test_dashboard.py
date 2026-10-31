"""Tests for the dashboard: navigation, appearance, key figures and evidence."""

import html
import re
import json
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from bi import github_page, charts, control, dashboard, project, queries, stack_page  # noqa: E402

DASHBOARD_FILE = str(PROJECT_DIR / "bi" / "dashboard.py")
# These tests draw the real dashboard, so they need the committed database.
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="etl/datos.db has not been built")
ALL_PAGES = [p for views in dashboard.WINDOWS.values() for p in views]


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
            match = re.search(r'<span class="(?:home|page)-bar-title" role="heading"[^>]*>([^<]+)</span>', block.value)
        if not match:
            match = re.search(r'<h1 class="qa-h1">([^<]+)</h1>', block.value)
        if match:
            return html.unescape(match.group(1))
    return None


def draw_page(title, state=None, query=None):
    """Draw one page alone, the way the navigation does; state: session values set first;
    query: address parameters, as a link would carry them."""
    script = (
        f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\nimport streamlit as st\n"
        f"from bi import dashboard\n"
        + "".join(f"st.session_state[{key!r}] = {value!r}\n" for key, value in (state or {}).items())
        + "".join(f"st.query_params[{key!r}] = {value!r}\n" for key, value in (query or {}).items())
        + f"dashboard.render_page({title!r})\n"
    )
    return AppTest.from_string(script, default_timeout=60).run()


# The home page opens on the latest week and its most moved family, both of which
# change every Tuesday; tests that read figures pin the week of 2026-10-05.
PINNED_HOME = {"_home_region": "Todas", "_home_week": "2026-10-05", "familia": "Hortalizas"}


def test_d070_the_route_holds_every_view_once_and_charts_only_in_dashboard():
    # D-151: the route ends in the project's documents.
    assert dashboard.ROUTE == ["Dashboard", "Ingeniería de datos", "Seguridad", "Documentación"]  # D-201
    assert list(dashboard.WINDOWS) == dashboard.ROUTE + [
        dashboard.SECTION_PROJECT,
        dashboard.SECTION_RESOURCES,
        dashboard.SECTION_KPI,
    ]
    views = [view for window in dashboard.WINDOWS.values() for view in window]
    assert len(views) == len(set(views)) and set(views) == set(dashboard.SHOW_PAGE_BY_TITLE)
    assert dashboard.WINDOWS["Dashboard"] == [
        dashboard.HOME_PAGE,
        dashboard.PAGE_INSIGHTS,
        dashboard.PAGE_SEASONALITY,
        dashboard.PAGE_SQL,
        dashboard.PAGE_CHANNELS,
    ]
    assert dashboard.WINDOWS["Ingeniería de datos"][0] == dashboard.PAGE_DIAGRAMS
    # Old addresses of the retired windows and of the 3D view still open something.
    for path in ["operacion", "documentacion", "vista-3d"]:
        assert dashboard.OLD_PATHS[path][0] in views
    assert dashboard.PAGE_OF_TAB[dashboard.TAB_PIPELINE] == dashboard.PAGE_DIAGRAMS


def test_every_page_has_a_function_an_icon_and_an_address():
    assert set(ALL_PAGES) == set(dashboard.SHOW_PAGE_BY_TITLE)
    assert set(ALL_PAGES) == set(dashboard.PAGE_ICONS) == set(dashboard.PAGE_PATHS)


def test_product_description_leaves_out_unspecified_parts():
    assert (
        dashboard.describe_product({"product": "Tomate", "variety": "Larga vida", "quality": "Primera"})
        == "Tomate Larga vida · Primera"
    )
    assert (
        dashboard.describe_product(
            {"product": "Marraqueta", "variety": dashboard.UNSPECIFIED, "quality": dashboard.UNSPECIFIED}
        )
        == "Marraqueta"
    )


@needs_database
def test_d295_a_first_visit_chooses_its_profile_before_anything_else():
    """D-295 replaces the open entry: an address with a retired profile is cleaned and the profile dialog asks, on top
    of the Resumen and with no way to close it but choosing."""
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Reclutamiento"
    app.run()
    assert not app.exception and app.get("dialog")
    assert "perfil" not in app.query_params
    assert not [box for box in app.selectbox if box.label in ("Perfil", "Tema")]
    assert app.radio(key="theme_field").value == dashboard.DEFAULT_THEME
    assert read_page_title(app) == "¿Qué familias de alimentos subieron y bajaron?"
    assert "Ingeniería de datos" not in " ".join(block.value for block in app.markdown)


def test_hover_hint_is_plain_text_and_escaped():
    icon = dashboard.build_hint_icon('**1,46** = "más caro"')
    assert "**" not in icon
    assert 'data-hint="1,46 = &quot;más caro&quot;"' in icon


@needs_database
def test_dashboard_opens_with_data_and_diagrams_have_their_own_page():
    app = draw_page(dashboard.HOME_PAGE, query=PINNED_HOME)
    assert not app.exception and not app.tabs
    texts = " ".join(block.value for block in app.markdown)
    assert (
        'Detalle de productos</span><span class="mock-products-family">Hortalizas' in texts
        and 'Producto seleccionado' not in texts
    )
    assert 'Precio medio<br>28-09' in texts and 'Precio medio<br>05-10' in texts and 'Variación' in texts  # D-327
    assert 'class="zoom-frame' not in texts and 'animateMotion' not in texts
    assert texts.index('¿Qué familias subieron y cuáles bajaron?') < texts.index('¿Qué productos explican el cambio?')
    # The search, the order and the table replace the old «Explorar…» drop-down (D-093).
    assert not app.expander and not app.slider
    # Map, movement by family and products of the selected family, on one screen (D-092).
    assert texts.count('<a class="mock-movement-row ') == 7
    assert texts.count('<a class="mock-movement-row rise selected"') == 1
    assert 'class="mock-products-table"' in texts and '¿Qué productos explican el cambio?' in texts
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
    pipeline_header = next(block.value for block in diagrams.markdown if 'class="page-bar-main"' in block.value)
    # D-267: the page bar, like the Resumen's: the title and the figures of the latest build, the time of the load.
    assert '>Pipeline y linaje</span>' in pipeline_header and 'page-bar-updated' in texts
    assert (
        'pruebas dbt superadas en el último build' in pipeline_header
        and 'modelos dbt, de staging a marts' in pipeline_header
    )
    assert not diagrams.toggle
    assert 'Animar el recorrido de los datos' not in texts
    assert 'ODEPA → indicadores · recorrido y plataformas' not in texts
    for label in ["ODEPA mayorista", "ODEPA consumidor", "Informe semanal", "Consultas SQL", "OBSERVABILIDAD"]:
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


@needs_database
def test_dashboard_territory_is_immediately_readable_without_a_3d_duplicate():
    app = draw_page(dashboard.HOME_PAGE)
    assert not app.exception
    figures = [json.loads(chart.proto.spec) for chart in app.get("plotly_chart")]
    types = {trace["type"] for figure in figures for trace in figure["data"]}
    assert "scatter3d" not in types
    texts = " ".join(block.value for block in app.markdown)
    # D-264: the week and three figures are chips of the bar; the place is in the week's hover.
    assert texts.count('class="home-chip"') == 1 and "Todo Chile" in texts
    assert "Mapa en proporción real" in texts


@needs_database
def test_d189_model_page_opens_on_the_star_model_and_the_storage_map_comes_third():
    app = draw_page(dashboard.PAGE_ARCHITECTURE)
    assert not app.exception and not app.tabs
    # D-236: the star first, then the entity-relation, then where the data lives; the storage
    # drawing is in an iframe behind its view.
    joined = " ".join(block.value for block in app.markdown)
    assert 'aria-label="Modelo estrella de datos.duckdb"' in joined
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


def test_kpi_link_opens_the_kpi_view_with_that_indicator():
    link = dashboard.build_kpi_link("K5")
    # El proyecto starts the route, so it lives at the root of the app.
    assert 'href="kpis?kpi=K5"' in link
    assert ">K5<" not in link


def test_without_github_the_states_come_from_the_latest_saved_load():
    latest_load = {"status": "LOADED", "started_at": "2026-10-12T22:17:01"}
    states = dashboard.build_journey_states({}, None, latest_load, {"file": {"year": 2026}})
    assert [states[step] for step in ["download", "etl", "tests", "load", "etl_run"]] == [control.RUN_OK] * 5
    # What a saved load cannot prove stays unknown, and is drawn without a dot.
    assert states["report"] == dashboard.architecture.STATE_UNKNOWN
    assert states["workflow"] == dashboard.architecture.STATE_UNKNOWN
    assert dashboard.describe_state_source("GitHub respondió 403", {}, latest_load) == (
        "GitHub no respondió (GitHub respondió 403); los estados salen de la última carga "
        "guardada en la base (12-10-2026 19:17)."
    )


def test_d071_four_themes_and_vantablack_is_the_default():
    assert charts.THEMES == ["Corporativo", "Vantablack", "Blue Light", "Dark Grey"]
    assert (
        dashboard.get_mode() == charts.MODE_DARK
        and charts.get_palette(dashboard.get_mode())["base"] == charts.BASE_DARK
    )
    # Shared links with retired names still open the closest theme.
    assert dashboard.RETIRED_THEMES["Grafito"] == "Dark Grey"
    for theme in charts.THEMES:
        palette = charts.get_palette(theme)
        assert theme in charts.HEAT_RAMPS and palette["base"] in (charts.BASE_DARK, charts.BASE_LIGHT)


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


def draw_control_page(secrets, run_state="ok", dialog=False, cancel_error=None):
    """The Operaciones page with GitHub replaced by fixed answers, no network. A manual
    run is accepted; GitHub answers that it is «run_state» (ok, failed or in_progress) with one
    job whose log ends in a line that prints the token. With dialog, the script opens the manual-run
    dialog itself: in a browser the dialog reruns alone (a fragment), which AppTest
    does not reproduce."""
    script = (
        f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
        "from datetime import datetime, timedelta, timezone\n"
        "from bi import control, dashboard, run_monitor\n"
        # AppTest runs in this process: what the script replaces is put back at its end, or later tests see the stubs.
        "SAVED = [(module, name, getattr(module, name)) for module, name in ((control, 'list_workflow_runs'),"
        " (control, 'read_token_expiration'), (control, 'start_workflow_run'), (control, 'cancel_workflow_run'),"
        " (run_monitor, 'find_run'), (run_monitor, 'fetch_run'), (run_monitor, 'read_tail'))]\n"
        "control.list_workflow_runs = lambda *args, **kwargs: []\n"
        # Relative to today: a fixed date made this test fail the day it arrived.
        "control.read_token_expiration = lambda token: datetime.now(timezone.utc) + timedelta(days=60)\n"
        "control.start_workflow_run = lambda token: None\n"
        "run_monitor.find_run = lambda token, requested_at: {'id': 7, 'url': 'https://github.com/x/y/actions/runs/7'}\n"
        f"STATE = {run_state!r}\n"
        "def fetch(run_id, token):\n"
        "    done = STATE != 'in_progress'\n"
        "    step = {'name': 'Run the ETL', 'status': 'completed' if done else 'in_progress',\n"
        "            'conclusion': ('success' if STATE == 'ok' else 'failure') if done else None,\n"
        "            'started_at': '2026-10-30T12:00:00Z', 'completed_at': '2026-10-30T12:01:05Z' if done else None}\n"
        "    job = {'id': 70, 'name': 'weekly-load', 'status': 'completed' if done else 'in_progress',\n"
        "           'conclusion': step['conclusion'], 'steps': [step]}\n"
        "    return {'status': 'completed' if done else 'in_progress', 'conclusion': step['conclusion'],\n"
        "            'url': 'https://github.com/x/y/actions/runs/7', 'jobs': [job]}\n"
        "run_monitor.fetch_run = fetch\n"
        "run_monitor.read_tail = lambda job, token: ['line one', 'Authorization: Bearer ' + token, 'last line']\n"
        + (
            "def refuse(run_id, token):\n    import requests\n    r = requests.Response()\n"
            f"    r.status_code = {cancel_error}\n    raise requests.HTTPError(response=r)\n"
            "control.cancel_workflow_run = refuse\n"
            if cancel_error
            else "control.cancel_workflow_run = lambda run_id, token: None\n"
        )
        + "try:\n"
        + (
            "    dashboard.show_run_now_dialog(dashboard.get_secret('GITHUB_TOKEN'), "
            "dashboard.get_secret('CONTROL_CODE'))\n"
            if dialog
            else "    dashboard.render_page(dashboard.PAGE_RUNS)\n"
        )
        + "finally:\n    for module, name, value in SAVED:\n        setattr(module, name, value)\n"
    )
    app = AppTest.from_string(script, default_timeout=60)
    for name, value in secrets.items():
        app.secrets[name] = value
    return app.run()


def read_page_text(app):
    """Every text the page sends to the browser: Markdown, HTML, notes and fields."""
    parts = [
        str(element.proto)
        for kind in ["markdown", "html", "caption", "info", "warning", "error", "text_input"]
        for element in app.get(kind)
    ]
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
    assert (
        app.text_input(key="author_access_code").proto.type != app.text_input(key="author_access_code").proto.PASSWORD
    )
    assert "-webkit-text-security:disc" in dashboard.build_runs_css(charts.MODE_DARK)
    assert not [address for address in ADMIN_ADDRESSES if address in read_page_text(app)]
    text = open_author_access(app, "equivocada")
    assert not app.exception and "Clave incorrecta" in text and "runs_run_now" not in button_keys(app)
    text = open_author_access(app, "clave")
    assert not app.exception
    assert (
        app.button(key="runs_run_now").label == "Ejecutar pipeline ahora"
        and not app.button(key="runs_run_now").disabled
    )
    assert all(address in read_page_text(app) for address in ADMIN_ADDRESSES)
    app.button(key="author_access_close").click().run()
    assert "runs_run_now" not in button_keys(app)
    # The dialog itself still asks for the code when the session is not open (defense in depth).
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, dialog=True)
    text = open_run_dialog(app, "equivocada")
    assert not app.exception and "Clave incorrecta" in text


@needs_database
def test_d249_the_code_box_survives_any_character_and_never_locks():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, dialog=True)
    text = open_run_dialog(app, "contraseña ñ")
    assert not app.exception and "Clave incorrecta" in text
    for attempt in range(6):  # D-249: no limit of attempts, by the author's decision
        text = open_run_dialog(app, f"intento{attempt}")
        assert "Clave incorrecta" in text and "bloqueado" not in text and "Demasiados" not in text


@needs_database
def test_d201_security_has_its_own_section_with_the_view_and_the_test_plan():
    assert dashboard.SIDEBAR_TOP_LABELS[dashboard.SECTION_SECURITY] == "Seguridad"
    assert dashboard.WINDOWS[dashboard.SECTION_SECURITY] == [dashboard.PAGE_SECURITY, dashboard.PAGE_TEST_PLAN]
    app = draw_control_page({})
    assert not app.exception and list(app.get("segmented_control")[0].options) == [
        "Despliegue",
        "Operación",
        "CI/CD",
        "Monitoreo",
    ]
    for page in (dashboard.PAGE_SECURITY, dashboard.PAGE_TEST_PLAN):
        app = draw_page(page)
        assert not app.exception and read_page_title(app) == dashboard.SIDEBAR_LABELS.get(page, page)
    assert "S-01" in " ".join(block.value for block in app.markdown)


def run_window_text(app):
    return read_page_text(app) + " ".join(str(element.proto) for element in app.get("success") + app.get("info"))


@needs_database
def test_d149_a_successful_run_says_so_shows_the_real_log_and_never_shows_the_token():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="ok", dialog=True)
    open_run_dialog(app, "clave")
    app.run()  # the window asks GitHub again by itself; here, one more turn
    text = run_window_text(app)
    code = " ".join(block.value for block in app.code)
    assert not app.exception and "Ejecución completada" in text and "Tu token vence en" in text
    assert "Run the ETL" in code or "Limpieza y reglas de negocio" in code  # a line per step
    assert "line one" in code and "last line" in code  # the job's last real lines
    assert FAKE_TOKEN not in text + code and FAKE_TOKEN[-6:] not in text + code and "Bearer github_pat" not in code
    assert "run_close" in button_keys(app) and "run_cancel" not in button_keys(app)  # «Cancelar» became «Cerrar»


@needs_database
def test_d149_a_failed_run_says_it_did_not_complete_and_can_be_closed():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="failed", dialog=True)
    open_run_dialog(app, "clave")
    app.run()
    assert not app.exception and "La ejecución falló" in run_window_text(app) + " ".join(
        str(element.proto) for element in app.get("error")
    )
    assert "run_close" in button_keys(app)


@needs_database
def test_d351_the_window_cannot_be_dismissed_minimizing_does_not_cancel_and_cancel_asks_first():
    import inspect

    assert (
        "dismissible=False"
        in inspect.getsource(dashboard).split("def show_run_now_dialog")[0].rsplit("@st.dialog", 1)[1]
    )
    cancelled = []
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="in_progress", dialog=True)
    open_run_dialog(app, "clave")
    app.run()
    keys = button_keys(app)
    assert "run_minimize" in keys and "run_cancel" in keys and "run_close" not in keys  # the two actions
    assert "Ejecución en curso" in run_window_text(app)
    app.button(
        key="run_cancel"
    ).click().run().run()  # asks first: nothing is cancelled yet (AppTest redraws the fragment on a second turn)
    assert "¿Seguro que quieres cancelar? Esto detiene la ejecución en GitHub." in read_page_text(app) + " ".join(
        str(element.proto) for element in app.get("warning")
    )
    assert "run_cancel_yes" in button_keys(app) and "run_cancel_no" in button_keys(app)
    app.button(key="run_cancel_no").click().run().run()
    assert "run_cancel" in button_keys(app) and not app.session_state["run_watch"]["confirming"]
    app.button(key="run_minimize").click().run()  # minimizing never cancels
    watch = app.session_state["run_watch"]
    assert watch["minimized"] and watch["phase"] == "running" and not cancelled


@needs_database
def test_d351_confirming_cancels_and_says_cancelled_and_a_refusal_keeps_the_run_with_its_reason():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="in_progress", dialog=True)
    open_run_dialog(app, "clave")
    app.run()
    app.button(key="run_cancel").click().run().run()
    app.button(key="run_cancel_yes").click().run().run()
    watch = app.session_state["run_watch"]
    assert watch["phase"] == "cancelled" and "run_close" in button_keys(app)
    refused = draw_control_page(
        {"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="in_progress", dialog=True, cancel_error=403
    )
    open_run_dialog(refused, "clave")
    refused.run()
    refused.button(key="run_cancel").click().run().run()
    refused.button(key="run_cancel_yes").click().run().run()
    watch = refused.session_state["run_watch"]
    assert watch["phase"] == "running" and "no tiene permiso para cancelar" in " ".join(
        str(element.proto) for element in refused.get("error")
    )
    assert FAKE_TOKEN not in str(refused.get("error"))


@needs_database
def test_d149_without_secrets_the_run_is_disabled_and_reload_confirms():
    app = draw_control_page({})
    assert "runs_run_now" not in button_keys(app) and not [
        box for box in app.text_input if box.key == "author_access_code"
    ]
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


def test_d057_cards_escape_their_text_and_keep_bold_and_code():
    card = dashboard.build_info_card_html(
        "<b>Título</b>", "Texto con **negrita** y `datos.db`", label="P1", note="nota"
    )
    assert "<b>Título</b>" not in card and "&lt;b&gt;Título&lt;/b&gt;" in card
    assert "<strong>negrita</strong>" in card and "<code>datos.db</code>" in card
    assert 'class="info-label">P1<' in card


@needs_database
def test_d090_kpi_module_reads_left_to_right_and_keeps_sql_behind_a_click():
    script = (
        f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
        "import streamlit as st\n"
        "from bi import dashboard\ndashboard.show_kpi_tab(dashboard.charts.MODE_DARK)\n"
    )
    app = AppTest.from_string(script, default_timeout=60)
    app.query_params["kpi"] = "K5"
    app.run()
    assert not app.exception
    # Question on top, then the whole path at once: three nodes on one line, three cards,
    # the dense context behind tabs, and no «continue» step.
    assert app.selectbox(key='kpi_register_selection').value == 'K5'
    assert [tab.label for tab in app.tabs] == ["Alcance", "Lógica", "Límites"]
    assert not app.expander and not app.code
    assert [button.label for button in app.button] == ["Desplegar SQL"]
    markup = ' '.join(block.value for block in app.markdown)
    assert markup.count('class="kpi-node"') == 3 and 'class="kpi-figure' in markup
    for title in ("Resultado", "Contexto", "Consulta"):
        assert f'</span>{title}</div>' in markup
    assert 'k5_weekly_variations_sql' in markup
    app.selectbox(key='kpi_register_selection').set_value('K1').run()
    assert not app.exception and app.query_params['kpi'] == 'K1'
    markup = ' '.join(block.value for block in app.markdown)
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


@needs_database
def test_manual_is_a_procedural_document_without_presentation_cards():
    # D-279: the manual is a runbook drawn as the other documents, from docs/MANUAL.md.
    app = draw_page(dashboard.PAGE_MANUAL)
    assert not app.exception
    text = " ".join(block.value for block in app.markdown)
    for heading in ("## 2. Qué ocurre automáticamente", "## 4. Fallas de la carga semanal", "## 10. Límites conocidos"):
        assert heading in text
    assert 'class="info-card"' not in text
    assert '.github/workflows/semanal.yml' in text.replace("\u200b", "")  # D-297: code breaks only at its separators


def test_d057_every_rejection_reason_of_the_etl_is_explained():
    from etl import etl

    reasons = {value for name, value in vars(etl).items() if name.startswith("REASON_")}
    assert reasons == set(dashboard.REASON_TEXTS)


def test_d057_rejected_rows_show_readable_spanish_columns():
    rows = pd.DataFrame(
        {
            "source": ["wholesale"],
            "reason": ["NON_POSITIVE_PRICE"],
            "original_row": [
                '{"file_hash": "abc", "price_date": "2025-01-01", "product": "Ají", "avg_price": "0,0000"}'
            ],
        }
    )
    table = dashboard.build_rejected_rows_table(rows)
    assert list(table.columns) == ["Fuente", "Motivo", "Fecha", "Producto", "Precio promedio"]
    assert table.iloc[0]["Fuente"] == "Mayorista"
    assert table.iloc[0]["Motivo"] == "Precio cero o negativo"


@needs_database
def test_d057_quality_tab_explains_what_was_left_out_and_shows_it():
    script = (
        f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
        "from bi import dashboard\ndashboard.show_quality_tab(dashboard.charts.MODE_DARK)\n"
    )
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    cards = " ".join(block.value for block in app.markdown if 'class="info-grid"' in block.value)
    for label in ["RN-11 · no se cargan", "RN-12 · fuera de los indicadores", "RN-05 · sin precio comparable"]:
        assert label in cards
    assert "0,008 %" in cards
    assert not [
        column
        for frame in app.dataframe
        for column in frame.value.columns
        if column in ("source", "reason", "rejected_rows", "rejected_share")
    ]


def test_d057_the_menu_folds_once_on_narrow_screens_only():
    script = dashboard.FOLD_SIDEBAR_SCRIPT
    assert f"window.innerWidth >= {dashboard.NARROW_SCREEN_WIDTH}" in script
    assert dashboard.NARROW_SCREEN_WIDTH == 1024
    # Folded once per visit: a reader who opens it again keeps it open.
    assert 'sessionStorage.getItem("sidebarFolded")' in script


@needs_database
def test_analysis_sections_are_direct_destinations_without_tabs():
    expected = {
        dashboard.PAGE_SEASONALITY: "Índice mensual por familia, enero 2022 = 100",
    }
    for page, title in expected.items():
        app = draw_page(page)
        assert not app.exception, page
        if page != dashboard.PAGE_KPI:
            assert not app.tabs, page
        assert title in " ".join(block.value for block in app.markdown)


def test_status_text_is_readable_on_light_themes():
    def contrast(first, second):
        def luminance(color):
            channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
            channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
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
    tabbed = {
        dashboard.PAGE_KPI,
        dashboard.PAGE_OPERATIONS,
        dashboard.PAGE_RUNS,
        dashboard.PAGE_SQL,
        dashboard.PAGE_METHOD,
        dashboard.PAGE_GIT,
    }  # D-296: the dashboard's three tabs, one screen each
    for page in dashboard.PAGES:
        app = draw_page(page)
        assert not app.exception, page
        if page not in tabbed:
            assert not app.tabs, page
        texts = " ".join(block.value for block in app.markdown)
        assert (">¿Qué familias de alimentos subieron y bajaron?</span>" in texts) == (page == dashboard.HOME_PAGE)
        # The journey lives only in Pipeline y linaje; the SAD links to it (D-247).
        assert ('aria-label="Recorrido de los datos de ODEPA al panel"' in texts) == (page == dashboard.PAGE_DIAGRAMS)
        # The lineage is the switch's second view, never drawn by default (step 4).
        assert 'aria-label="Linaje dbt: de bronce a marts"' not in texts


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
    assert read_page_title(app) == "Consultas SQL"
    assert "seccion" not in app.query_params


@needs_database
def test_old_section_links_can_redirect_with_a_bound_theme():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Analista BI"
    app.query_params["tema"] = "Corporativo"
    app.query_params["seccion"] = dashboard.TAB_GAP
    app.run()
    assert not app.exception
    assert read_page_title(app) == "Consultas SQL"


def test_d056_old_addresses_open_their_new_tab():
    assert set(dashboard.OLD_PATHS).isdisjoint(dashboard.PAGE_PATHS.values())
    for path in [
        "panel",
        "margenes",
        "canales-y-regiones",
        "consultas",
        "centro-de-control",
        "calidad-de-datos",
        "pipeline",
        "el-proyecto",
    ]:
        page, tab = dashboard.OLD_PATHS[path]
        assert tab is None or dashboard.PAGE_OF_TAB[tab] == page
    assert set(dashboard.OLD_HOME_TABS.values()) <= set(dashboard.PAGE_OF_TAB)
    assert set(dashboard.OLD_HOME_TABS).isdisjoint(dashboard.TABS_BY_PAGE[dashboard.HOME_PAGE])


@needs_database
@pytest.mark.parametrize("title", ALL_PAGES)
def test_every_page_draws_without_errors_and_shows_the_attribution(title):
    app = draw_page(title)
    assert not app.exception
    assert dashboard.ATTRIBUTION_TEXT in [caption.value for caption in app.caption]


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
            assert dashboard.read_window_views(window, profile) == list(views)
    assert dashboard.WINDOW_OF_VIEW[dashboard.PAGE_LINKS] == dashboard.SECTION_RESOURCES
    assert dashboard.WINDOW_OF_VIEW[dashboard.PAGE_MANUAL] == dashboard.SECTION_LINKS


@needs_database
def test_d070_a_profile_starts_its_visit_and_the_sidebar_does_not_show_it():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Ingeniería de datos"
    app.run()
    assert not app.exception
    # The visit starts at the section of the profile: «Detalle técnico», its pipeline.
    assert read_page_title(app) == "¿Qué familias de alimentos subieron y bajaron?"
    sidebar = " ".join(block.value for block in app.sidebar.markdown)
    assert "Ingeniería de datos" not in sidebar
    assert not [button for button in app.sidebar.button if "perfil" in button.label]


@needs_database
def test_d069_map_scope_replaces_permanent_selectors_and_context_holds_across_views():
    dashboard_bar = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    dashboard_bar.query_params["perfil"] = "Analista BI"
    dashboard_bar.run()
    assert not dashboard_bar.exception
    # Only the two filters of the products table: no permanent selectors (D-092).
    assert {box.key for box in dashboard_bar.main.selectbox} == {'home_products_channel', 'home_products_order'}
    # The page has one text field; the profile door's key field (D-335) is not a selector of the page.
    assert [box.key for box in dashboard_bar.text_input if not box.key.startswith('profile_')] == [
        'home_products_search'
    ]
    dashboard_bar.session_state['dashboard_group'] = 'Frutas'
    dashboard_bar.run()
    assert dashboard_bar.session_state["dashboard_group"] == "Frutas"
    dashboard_bar.query_params["vista"] = dashboard.PAGE_HOME
    dashboard_bar.run()
    assert not dashboard_bar.exception
    assert dashboard_bar.session_state["dashboard_group"] == "Frutas"


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
    assert app.query_params["tema"] == "Vantablack"  # D-349: dark unless the address says otherwise
    app.radio(key="theme_field").set_value("Dark Grey").run()
    assert not app.exception
    assert app.session_state[dashboard.THEME_STATE] == "Dark Grey"
    assert app.query_params["tema"] == "Dark Grey"
    app.query_params["vista"] = dashboard.PAGE_HOME
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


@needs_database
def test_dashboard_explains_its_graphs_and_collapses_family_tables():
    app = draw_page(dashboard.PAGE_HOME)
    assert not app.exception
    text = ' '.join(block.value for block in app.markdown)
    assert 'En palabras simples:' not in text
    assert 'Variación por familia' in ' '.join(block.value for block in app.markdown)
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


@needs_database
def test_d250_the_path_and_the_footer_follow_the_menu():
    order = dashboard.MENU_ORDER
    assert len(order) == len(set(order)) and order[0] == dashboard.HOME_PAGE
    assert dashboard.PAGE_SAD not in dashboard.MENU_BLOCK_OF_VIEW and dashboard.PAGE_SAD in dashboard.FOLDER_ORDER
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['vista'] = dashboard.PAGE_RUNS
    app.run()
    assert not app.exception
    markup = ' '.join(block.value for block in app.markdown)
    assert 'DevOps y seguridad › Centro de operación' in markup
    footer = app.main.get('page_link')
    assert [link.proto.label for link in footer] == [
        '← Anterior: Consultas SQL',
        'Siguiente: Arquitectura de seguridad →',
    ]
    assert [link.proto.icon for link in footer] == [
        dashboard.SIDEBAR_ICONS[dashboard.PAGE_SQL],
        dashboard.SIDEBAR_ICONS[dashboard.PAGE_SECURITY],
    ]


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

    payload = base64.b64encode(
        json.dumps(
            {
                "dashboard_group": "Frutas",
                "dashboard_top_n": 8,
                "admin_token": "not-a-selection",
                "dashboard_product": {"bad": "shape"},
            }
        ).encode()
    ).decode()
    script = (
        f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
        "import streamlit as st\nfrom bi import dashboard\n"
        f"st.query_params['_ctx'] = {payload!r}\ndashboard.restore_return_context()\n"
    )
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
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.session_state["home_region_done"] = app.session_state["home_family_done"] = True  # D-372: steps 1 and 2 done
    app.run()
    assert not app.exception
    assert app.selectbox(key='home_products_order').options == list(dashboard.PRODUCT_ORDERS)

    def rows():
        markup = ' '.join(block.value for block in app.markdown)
        table = re.search(r'<div class="mock-products-table".*?</table>', markup).group(0)
        return [
            ('1 cotización' in row, float(value.replace('−', '-').replace(',', '.')))
            for row in table.split('<tr')[2:]
            for value in re.findall(r'<td class="num (?:rise|fall|neutral)"><b>([+−]?[\d,]+) %</b>', row)
        ]

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
    # D-257: the diagram, the audit controls and what was set aside each have their own tab. D-360: only the tab in
    # sight is drawn, so there is one frame at a time.
    bars = app.get('segmented_control')
    assert (
        not app.selectbox and len(bars) == 1 and list(bars[0].options) == ["Calidad", "Auditoría", "Rechazos y cargas"]
    )
    assert len(app.get('iframe')) == 1
    for tab in ("Auditoría", "Rechazos y cargas"):
        app.segmented_control(key="quality_audit_view").set_value(tab).run()
        assert not app.exception and len(app.get('iframe')) == 1


@needs_database
def test_d171_a_card_opens_its_evidence_with_the_rows_the_method_and_a_recheck():
    script = (
        f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\nimport streamlit as st\n"
        "from bi import dashboard\n"
        "st.session_state[dashboard.QUALITY_OPEN_KEY] = 'Pruebas dbt de la última construcción'\n"
        "dashboard.render_page(dashboard.PAGE_OPERATIONS)\n"
    )
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
    # Step 4 of the refonte: «Ingeniería de datos», four pages; DevOps joined «Ejecuciones».
    assert 'DevOps y seguridad' not in labels
    for child in [
        'Panorama de precios',
        'Pipeline y linaje',
        'Modelo de datos',
        'Calidad y auditoría',
        'Centro de operación',
        'Arquitectura de seguridad',
        'Documentos',
    ]:
        assert child in labels
    # D-282: the documents live in their folder, not in the menu.
    for document in ['Plan de pruebas y seguridad', 'PRD · Requisitos del producto', 'SAD · Arquitectura']:
        assert document not in labels
    sidebar_markup = " ".join(block.value for block in app.sidebar.markdown)
    assert 'class="sidebar-github' in sidebar_markup and 'aria-label="GitHub del proyecto"' in sidebar_markup
    for retired in ['Archivos del proyecto', 'Descripción general', 'Manual', 'Glosario', 'Fuentes y enlaces']:
        assert retired not in labels
    folder_buttons = [button for button in app.sidebar.button if str(button.key).startswith('nav_toggle_')]
    toggles = {button.label for button in folder_buttons}
    # «Fuentes» (D-118): the two ODEPA datasets, a folder like every other section.
    # D-201: security has its own folder.
    assert toggles == set(MENU_BLOCKS)
    assert all(not button.help for button in folder_buttons)
    assert 'border-left' not in dashboard.build_section_colors_css(True)  # no tree indent: a flat list
    # D-231: the wordmark keeps the brand green that suits its surface; the rows are neutral text.
    for mode in charts.THEMES:
        dark = dashboard.is_dark_surface(charts.get_palette(mode)['sidebar'])
        expected = dashboard.BRAND_GREEN_DARK if dark else dashboard.BRAND_GREEN_LIGHT
        assert expected in dashboard.build_greenocean_logo(mode, sidebar=True)
        assert f'color:{expected} !important;' not in dashboard.build_sidebar_css(mode)
        assert f'color:{dashboard.MENU_INK[dark][0]} !important;' in dashboard.build_sidebar_css(mode)


@needs_database
def test_d102_a_folder_row_really_folds_like_vs_code():
    """Folders start open (D-139); a click folds one and a second click opens it."""
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['ver'] = 'ingenieria'
    app.run()
    toggle = next(b for b in app.sidebar.button if str(b.key) == 'nav_toggle_ingenieria')
    assert toggle.label == 'Ingeniería de datos'
    assert 'Pipeline y linaje' in [link.proto.label for link in app.sidebar.get('page_link')]
    toggle.click().run()
    assert not app.exception
    toggle = next(b for b in app.sidebar.button if str(b.key) == 'nav_toggle_ingenieria')
    assert toggle.label == 'Ingeniería de datos'
    assert 'Pipeline y linaje' not in [link.proto.label for link in app.sidebar.get('page_link')]
    toggle.click().run()
    assert not app.exception
    assert 'Pipeline y linaje' in [link.proto.label for link in app.sidebar.get('page_link')]


def test_d113_the_global_click_handler_only_forces_internal_links():
    script = dashboard.build_visit_history_script()
    assert "anchor.hostname === location.hostname" in script
    assert "anchor.target = '_self'" in script


@needs_database
def test_d118_sources_is_its_own_folder_with_two_external_children():
    """ODEPA is not GitHub: the sources have their own place. D-287: a large tile in the footer, beside the documents
    folder, whose floating panel holds the official files as external links."""
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not any(str(button.key) == 'nav_toggle_fuentes' for button in app.sidebar.button)
    assert [
        element.label for element in app.sidebar.get('popover') if getattr(element, 'label', '') == 'Fuentes'
    ] or 'Fuentes' in str([element.proto for element in app.sidebar.get('popover')])
    markup = " ".join(block.value for block in app.sidebar.markdown)
    for name, url in dashboard.SOURCE_LINKS:
        assert f'href="{html.escape(url, quote=True)}"' in markup and name in markup
    assert markup.count('target="_blank" rel="noopener noreferrer"') >= len(dashboard.SOURCE_LINKS)


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
    github_links = [
        link for link in project.PROJECT_LINKS if link["url"] and link["url"].startswith(project.GITHUB_URL)
    ]
    assert github_links == [link for link in project.PROJECT_LINKS if link["url"]]
    assert len(github_links) >= 5
    assert dashboard.architecture.brand_icons.logo_body("github") in markup
    assert markup.count('target="_blank"') >= len(github_links) + 1


@needs_database
def test_d102_the_current_window_also_starts_open_and_can_be_toggled():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.run()
    toggle = next(b for b in app.sidebar.button if str(b.key) == 'nav_toggle_negocio')
    assert not toggle.disabled
    assert toggle.label == 'Negocio · BI'
    assert 'Panorama de precios' in [link.proto.label for link in app.sidebar.get('page_link')]
    toggle.click().run()
    assert not app.exception
    assert next(b for b in app.sidebar.button if str(b.key) == 'nav_toggle_negocio').label == 'Negocio · BI'
    assert 'Panorama de precios' not in [link.proto.label for link in app.sidebar.get('page_link')]


@needs_database
def test_d100_alert_dialog_is_styled_from_every_page_not_only_the_summary():
    """The trigger moved into the shared sidebar footer (D-096); its CSS must follow (D-100)."""
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['vista'] = dashboard.PAGE_ARCHITECTURE
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    app.run()
    assert not app.exception
    # D-169: the trigger lives on top of the Resumen only; other pages carry neither it
    # nor the dialog's stylesheet.
    assert not [button for button in app.button if str(button.key) == 'home_alert_trigger']
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    app.run()
    markup = ' '.join(block.value for block in app.get('html')) + ' '.join(c.value for c in app.markdown)
    assert '.home-alert-gallery-legend' in markup and '[class*="st-key-home_alert_card_"]' in markup
    app.button(key='home_alert_trigger').click().run()
    assert not app.exception
    markup = ' '.join(block.value for block in app.get('html')) + ' '.join(c.value for c in app.markdown)
    assert 'home-alert-overview-marker' in markup


def test_movement_ring_parts_cover_comparable_series_not_the_top_n():
    rows = pd.DataFrame({'variation': [0.2] * 12 + [-0.1] * 4 + [0.0] * 4 + [float('nan')]})
    parts = dashboard.build_movement_proportions(rows)
    assert parts['value'].tolist() == [12, 4, 4]
    assert parts['share'].tolist() == [60.0, 20.0, 20.0]
    assert parts['value'].sum() == 20
    empty = dashboard.build_movement_proportions(rows.iloc[:0])
    assert empty['value'].sum() == 0 and empty['share'].sum() == 0


def test_d094_old_history_links_open_the_new_page():
    assert dashboard.RETIRED_VIEWS['Histórico y estacionalidad'] == dashboard.PAGE_SEASONALITY == 'Contexto del precio'


def test_business_header_order_and_retired_views_are_not_in_the_menu():
    views = dashboard.read_window_views(dashboard.REPORT_WINDOW)
    for retired in (
        "Datos",
        "Esta semana",
        "Brecha de precio",
        "Canales y regiones",
        "Alertas",
        "Portada",
        "Definición del proyecto",
        "Reglas de calidad",
        "DevOps y seguridad",
    ):  # D-318: they left, and their addresses open the page that holds them
        assert retired not in views and dashboard.RETIRED_VIEWS[retired] in dashboard.SHOW_PAGE_BY_TITLE


@needs_database
def test_d128_the_price_alert_closes_the_list_in_red_away_from_the_github_mark():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not app.exception
    alert = app.button(key="home_alert_trigger")
    assert re.fullmatch(r"▲ \d+", alert.label) and "Alertas de precio" in alert.help
    # D-169: the trigger sits on top of the Resumen, out of the sidebar.
    assert alert not in app.sidebar.button
    css = " ".join(block.value for block in app.sidebar.markdown)
    assert ".st-key-home_alert_trigger button" in css
    # The footer keeps only Apariencia and the GitHub mark.
    assert 'class="sidebar-github' in css


@needs_database
def test_d165_the_operation_centre_reads_like_the_dashboard():
    # D-165 replaced the strip of four figures and the history table (D-129) by the
    # path of the run beside three facts and the latest runs.
    app = draw_page(dashboard.PAGE_RUNS, state={"runs_view": "Operación"})  # D-360: the tab drawn is the one chosen
    assert not app.exception and app.get("iframe")
    text = " ".join(block.value for block in app.markdown)
    assert 'class="page-bar-title"' in text and text.count('class="oc-fact"') == 3
    assert "Ver historial de ejecuciones" not in [expander.label for expander in app.expander]
    assert "runs_reload" in [str(button.key) for button in app.button]


def test_d129_the_github_page_names_actions_so_it_is_not_confused_with_ejecuciones():
    names = [link["name"] for link in project.PROJECT_LINKS]
    assert "GitHub Actions" in names and "Ejecuciones" not in names


@needs_database
def test_d151_documentation_is_the_prd_sad_and_adr_without_code():
    assert dashboard.WINDOWS[dashboard.SECTION_LINKS][:4] == [
        dashboard.PAGE_FOLDER,
        dashboard.PAGE_PRD,
        dashboard.PAGE_SAD,
        dashboard.PAGE_ADR,
    ]
    # D-205: the document views in their own frame, the live panel diagrams inline.
    for page, framed, inline in (
        (dashboard.PAGE_PRD, 4, 0),
        (dashboard.PAGE_SAD, 9, 0),
        (dashboard.PAGE_ADR, 3, 0),
        (dashboard.PAGE_TEST_PLAN, 6, 0),
    ):
        app = draw_page(page)
        assert not app.exception and not app.code
        text = " ".join(block.value for block in app.markdown)
        assert "[[diagrama:" not in text and text.count('class="doc-diagram"') == inline, page
        assert len(app.get("iframe")) == framed, page
    for path, page in (("documentacion-bi", dashboard.PAGE_PRD), ("documentacion-it", dashboard.PAGE_SAD)):
        assert dashboard.OLD_PATHS[path] == (page, None)


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
    for gone in [
        'Rango habitual',
        'Qué suele pasar',
        'con precio fuera de lo habitual para la época',
        'Desde enero 2022, frente a la inflación',
        'toda su historia',
    ]:
        assert gone not in text


@needs_database
def test_d163_without_inflation_the_ipc_is_the_flat_reference_and_the_pesos_are_named():
    script = (
        f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\nimport streamlit as st\n"
        "from bi import dashboard\nst.session_state[dashboard.CONTEXT_BASIS_KEY] = dashboard.BASIS_REAL\n"
        "dashboard.render_page(dashboard.PAGE_SEASONALITY)\n"
    )
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    assert 'Sin inflación: la línea punteada es la canasta del INE (100)' in ' '.join(b.value for b in app.markdown)


def test_d191_file_sizes_for_the_storage_diagram():
    sizes = dashboard.read_store_sizes()
    assert sizes["served"].endswith("MB") and "MB" in sizes["raw"]
    # D-270: the backup is not published; where it was built, its size is shown too.
    assert sizes["backup"].endswith("MB") if (dashboard.etl.BASE_DIR / "datos.db").exists() else "backup" not in sizes
    assert dashboard.format_file_size(18_624_512) == "19 MB" and dashboard.format_file_size(2_500_000) == "2,5 MB"


@needs_database
def test_d195_the_model_page_has_three_views_and_the_third_is_the_entity_relationship_diagram():
    assert dashboard.MODEL_VIEWS == [
        "Modelo estrella",
        "Entidad-relación",
        "Dónde viven los datos",
        "Cruces entre bases",
    ]
    app = draw_page(dashboard.PAGE_ARCHITECTURE, state={dashboard.MODEL_VIEW_KEY: "Entidad-relación"})
    assert not app.exception and not app.tabs
    joined = " ".join(block.value for block in app.markdown)
    assert 'aria-label="Modelo entidad-relación de datos.duckdb"' in joined
    assert joined.count('class="er-table ') == 9 and "PK, FK" in joined
    assert 'aria-label="Modelo estrella de datos.duckdb"' not in joined  # one view at a time


MENU_BLOCKS = {
    'Negocio · BI': ['Panorama de precios', 'Último dato por canal', 'Insights'],
    'Ingeniería de datos': ['Pipeline y linaje', 'Modelo de datos', 'Consultas SQL'],
    'DevOps y seguridad': ['Centro de operación', 'Arquitectura de seguridad'],
    'Stack y evidencia': ['Stack y evidencia', 'Mapa de la app'],
    'Calidad': ['Calidad y auditoría', 'Método y calidad', 'Git workflow'],
}


@needs_database
def test_d213_the_menu_is_flat_sections_open_by_default_with_every_page_once():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not app.exception
    assert not app.sidebar.selectbox
    toggles = [b.label for b in app.sidebar.button if str(b.key).startswith('nav_toggle_')]
    assert toggles == list(MENU_BLOCKS)
    labels = [link.proto.label for link in app.sidebar.get('page_link')]
    # D-286: the documents folder closes the menu as a larger tile in the footer, always in sight.
    assert labels == [page for pages in MENU_BLOCKS.values() for page in pages] + ['Documentos']
    assert all(link.proto.icon for link in app.sidebar.get('page_link')[:-1])
    markup = " ".join(block.value for block in app.sidebar.markdown)
    assert 'class="nav-source-link"' not in markup  # the sources are a tile with a floating panel (D-287)
    # D-231: a flat menu: no card background, border, radius or shadow on the sections, only a hairline;
    # the current page has a faint fill and an accent bar; every page has its own sidebar glyph.
    for dark in (True, False):
        css = dashboard.build_section_colors_css(dark)
        section = css.split('}')[0]
        assert 'background:transparent !important' in section and 'border-radius:0' in section
        assert 'box-shadow:none' in section and 'linear-gradient' not in css
        assert dashboard.MENU_INK[dark][6] in css and 'a::before' in css
        assert 'font-size:.9375rem' in css  # 15 px rows
    assert 'linear-gradient' not in dashboard.build_sidebar_css(charts.MODE_DARK)
    assert set(dashboard.SIDEBAR_ICONS) == {
        page for _, _, pages in dashboard.MENU_BLOCKS if pages is not dashboard.SOURCE_LINKS for page in pages
    }
    icons = [link.proto.icon for link in app.sidebar.get('page_link')]
    assert len(set(icons)) == len(icons)


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
    # D-266: nine tools as links, two sources and one explanation per arrow.
    assert page.count('<a class="sk-node"') == 9
    assert page.count('role="tooltip"') == 9 + len(stack_page.SOURCES) + len(stack_page.EDGES)
    for key, name, what, target in stack_page.STACK:
        assert target in dashboard.WINDOW_OF_VIEW, target
        assert html.escape(what) in page
    assert "vista=Consultas+SQL" in page
    for value in stack_page.read_figures().values():
        assert stack_page.format_number(value) in page


@needs_database
def test_d264_the_resumen_has_one_thin_bar_with_the_path_the_figures_and_the_alerts():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    # the bar replaces the shared header on this page: one path, one Volver
    assert 'class="app-brand"' not in markup
    assert "Negocio · BI › <b>Panorama de precios</b>" in markup
    assert app.button(key="return_to_previous").label == "Volver"
    assert read_page_title(app) == "¿Qué familias de alimentos subieron y bajaron?"
    # each chip says in full what it counts, and the alerts are the week's national ones
    assert (
        markup.count('class="home-chip"') == 1
    )  # D-316: the header keeps the week and the place; the counts live in the panels
    for note in ("Sin cambio claro", "Sin dato"):  # the map's legend says what its greys mean
        assert note in markup, note
    week = dashboard.read_latest_week()
    count = int((dashboard.read_price_alerts()["week_start"] == week).sum())
    assert app.button(key="home_alert_trigger").label == f"▲ {count}"
    assert 'class="home-bar-updated"' in markup


# D-282: one folder holds every document.
@needs_database
def test_d282_the_folder_shows_every_document_with_the_version_and_date_of_its_file():
    from bi import documents_folder

    app = draw_page(dashboard.PAGE_FOLDER)
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert markup.count('class="df-file"') == len(dashboard.FOLDER_DOCUMENTS) == 8
    assert "GreenOcean <i>/</i> <b>docs</b>" in markup and "8 documentos" in markup
    for page in dashboard.FOLDER_ORDER:
        filename = dashboard.PROJECT_DOCUMENTS[page][0]
        text = (PROJECT_DIR / "docs" / filename).read_text(encoding="utf-8")
        header = documents_folder.read_header(text)
        assert f"<span>v{header['Versión']}</span><span>{header['Fecha']}</span>" in markup, filename
        assert documents_folder.read_title(text) in markup, filename
        assert project.build_github_url(f"docs/{filename}") in markup, filename
    assert markup.count('class="go-icon go-icon-print"') == 8 and markup.count('class="df-preview"') == 8


def test_d282_every_document_of_docs_is_in_the_folder_and_nowhere_else_in_the_menu():
    reading = {path.name for path in (PROJECT_DIR / "docs").glob("*.md")} - {
        "DECISIONES.md",
        "PROYECTO.md",
        "DISENO.md",
    }
    assert {dashboard.PROJECT_DOCUMENTS[page][0] for page in dashboard.FOLDER_ORDER} == reading
    assert not set(dashboard.FOLDER_ORDER) & set(dashboard.MENU_ORDER)
    assert [pages for key, _, pages in dashboard.MENU_BLOCKS if key == "documentos"] == [[dashboard.PAGE_FOLDER]]
    assert all(pages for _, _, pages in dashboard.MENU_BLOCKS)  # no empty section is left


@needs_database
@pytest.mark.parametrize("page", ["PRD · Requisitos del producto", "Glosario", "Plan de pruebas y seguridad"])
def test_d282_a_document_opens_its_page_with_its_path_its_pdf_and_its_neighbours(page):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params['vista'] = page
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert '<nav class="doc-path"' in markup and f'target="_self">{dashboard.PAGE_FOLDER}</a>' in markup
    assert any("doc-print" in block.proto.body for block in app.get("html"))
    position = dashboard.FOLDER_ORDER.index(page)
    labels = [link.proto.label for link in app.main.get("page_link")]
    expected = [
        f"← Anterior: {dashboard.SIDEBAR_LABELS.get(p, p)}"
        for p in dashboard.FOLDER_ORDER[position - 1 : position]
        if position > 0
    ] + [
        f"Siguiente: {dashboard.SIDEBAR_LABELS.get(p, p)} →"
        for p in dashboard.FOLDER_ORDER[position + 1 : position + 2]
    ]
    assert labels == expected


def test_d282_the_old_addresses_of_the_documents_still_open_them():
    for page in dashboard.FOLDER_ORDER:
        window = dashboard.WINDOW_OF_VIEW[page]
        assert page in dashboard.read_window_views(window), page
    assert dashboard.WINDOW_OF_VIEW[dashboard.PAGE_TEST_PLAN] == dashboard.SECTION_SECURITY  # «seguridad?vista=…»
    assert dashboard.OLD_PATHS["documentacion-bi"] == (dashboard.PAGE_PRD, None)


def test_d282_the_pdf_action_prints_the_document_on_a_white_sheet():
    address = dashboard.build_print_address(dashboard.PAGE_SAD)
    assert "imprimir=" in address and "vista=SAD" in address


def test_d282_every_preview_shows_the_index_of_its_document():
    from bi import documents_folder

    for page in dashboard.FOLDER_ORDER:
        text = (PROJECT_DIR / "docs" / dashboard.PROJECT_DOCUMENTS[page][0]).read_text(encoding="utf-8")
        index = documents_folder.read_index(text)
        assert len(index) >= 2, page
        assert all(entry.split(" · ")[0] in text for entry in index), page


@needs_database
def test_d295_the_user_view_sees_the_business_pages_and_unlocks_the_rest_only_with_the_key():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.secrets["CONTROL_CODE"] = "clave-larga"
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PUBLIC
    app.run()
    assert not app.exception and not app.get("dialog")
    labels = {link.proto.label for link in app.sidebar.get("page_link")}
    business = next(pages for key, _, pages in dashboard.MENU_BLOCKS if key == "negocio")
    assert {dashboard.SIDEBAR_LABELS.get(view, view) for view in business} <= labels
    assert dashboard.SIDEBAR_LABELS.get(dashboard.PAGE_DIAGRAMS, dashboard.PAGE_DIAGRAMS) not in labels
    assert "Documentos" not in labels  # the folder tile is for the professional view
    app.query_params["perfil"] = dashboard.PROFILE_PROFESSIONAL  # the address cannot change a chosen view
    app.run()
    assert app.query_params["perfil"] == dashboard.PROFILE_PUBLIC
    app.text_input(key="profile_unlock_code").set_value("otra")
    app.button(key="profile_unlock").click().run()
    assert app.query_params["perfil"] == dashboard.PROFILE_PUBLIC and app.error
    app.text_input(key="profile_unlock_code").set_value("clave-larga")
    app.button(key="profile_unlock").click().run()
    assert app.query_params["perfil"] == dashboard.PROFILE_PROFESSIONAL
    labels = {link.proto.label for link in app.sidebar.get("page_link")}
    assert dashboard.SIDEBAR_LABELS.get(dashboard.PAGE_DIAGRAMS, dashboard.PAGE_DIAGRAMS) in labels
    assert not [button for button in app.button if str(button.key) == "profile_change"]  # no going back


def test_d295_each_professional_profile_reads_the_menu_like_its_portfolio(monkeypatch):
    state = {}
    monkeypatch.setattr(dashboard.st, "session_state", state)
    state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    firsts = {}
    for role in dashboard.ROLES:
        state[dashboard.ROLE_STATE] = role
        blocks = [key for key, *_ in dashboard.visible_menu_blocks()]
        assert blocks[:5] == dashboard.ROLE_ORDER[role] and blocks[5:] == ["fuentes", "documentos"], role
        firsts[role] = dashboard.visible_menu_order()[0]
    assert firsts["data"] == dashboard.PAGE_DIAGRAMS and firsts["bi"] == dashboard.HOME_PAGE
    assert firsts["seguridad"] == dashboard.PAGE_SECURITY and firsts["devops"] == dashboard.PAGE_RUNS
    source = (PROJECT_DIR / "bi" / "dashboard.py").read_text(encoding="utf-8")
    assert source.count("profile_parameters()") >= 3  # page addresses, the menu and the neighbours keep the view


@needs_database
def test_d298_a_failed_load_shows_its_alert_in_the_menu_of_every_page(monkeypatch):
    from datetime import datetime, timezone
    import streamlit as st
    from bi import control

    failed = {
        "id": 99,
        "state": control.RUN_FAILED,
        "started_at": datetime(2026, 10, 27, 12, tzinfo=timezone.utc),
        "duration": None,
        "url": "https://github.com",
        "trigger": "Automática",
    }
    monkeypatch.setattr(control, "list_workflow_runs", lambda token=None, count=10: [dict(failed)])
    monkeypatch.setattr(control, "mark_simulated_failures", lambda runs, token=None: runs)
    st.cache_data.clear()
    try:
        for view in (dashboard.PAGE_HOME, dashboard.PAGE_SQL):
            app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
            app.query_params.update({"vista": view, "perfil": dashboard.PROFILE_PROFESSIONAL})
            app.run()  # D-308: without the author's key, no failure is shown
            assert "La carga del 27-10 falló" not in " ".join(block.value for block in app.sidebar.markdown)
            app.session_state[dashboard.ADMIN_UNLOCKED] = True
            app.run()
            markup = " ".join(block.value for block in app.sidebar.markdown)
            assert not app.exception and "La carga del 27-10 falló" in markup, view
            assert any(link.proto.label == "Ver qué paso falló" for link in app.sidebar.get("page_link"))
    finally:
        st.cache_data.clear()


def test_d349_a_visit_with_no_parameters_opens_dark_also_the_entry_window_and_the_address_still_rules():
    plain = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not plain.exception and plain.get("dialog")  # the entry window is open
    assert plain.session_state[dashboard.THEME_STATE] == "Vantablack" and plain.query_params["tema"] == "Vantablack"
    assert 'base = "dark"' in (PROJECT_DIR / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    light = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    light.query_params["tema"] = "Corporativo"
    light.run()
    assert light.session_state[dashboard.THEME_STATE] == "Corporativo"
