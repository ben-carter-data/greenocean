"""Tests for the dashboard: profiles, pages, key figures and footer."""
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from bi import charts, control, dashboard, project, queries  # noqa: E402

DASHBOARD_FILE = str(PROJECT_DIR / "bi" / "dashboard.py")
# These tests draw the real dashboard, so they need the committed database.
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(),
                                    reason="etl/datos.db has not been built")
ALL_PAGES = dashboard.PAGES


def draw_page(title):
    """Draw one page alone, the way the navigation does."""
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              f"from bi import dashboard\ndashboard.render_page({title!r})\n")
    return AppTest.from_string(script, default_timeout=60).run()


def test_d056_one_menu_of_five_entries_by_type_of_content():
    assert dashboard.PAGES == ["Inicio", "Análisis", "Arquitectura", "Datos y código",
                               "Operaciones"]
    assert dashboard.HOME_PAGE == dashboard.PAGES[0]
    assert set(dashboard.TABS_BY_PAGE) == set(dashboard.PAGES)
    # A tab name belongs to one page only, so a place name always has one address.
    every_tab = [tab for tabs in dashboard.TABS_BY_PAGE.values() for tab in tabs]
    assert len(every_tab) == len(set(every_tab)) == len(dashboard.PAGE_OF_TAB)
    assert dashboard.TABS_BY_PAGE[dashboard.PAGE_ANALYSIS] == [
        "Esta semana", "Brecha de precio", "Canales y regiones", "Estacionalidad", "Alertas"]
    assert dashboard.TABS_BY_PAGE[dashboard.PAGE_ARCHITECTURE] == [
        "Pipeline", "Modelo de datos", "DevOps y seguridad"]


def test_d056_old_addresses_open_their_new_tab():
    assert set(dashboard.OLD_PATHS).isdisjoint(dashboard.PAGE_PATHS.values())
    for path in ["panel", "margenes", "canales-y-regiones", "estacionalidad", "alertas",
                 "consultas", "centro-de-control", "calidad-de-datos", "pipeline",
                 "el-proyecto"]:
        page, tab = dashboard.OLD_PATHS[path]
        assert tab is None or tab in dashboard.TABS_BY_PAGE[page]
    assert set(dashboard.OLD_HOME_TABS.values()) <= set(dashboard.PAGE_OF_TAB)
    assert set(dashboard.OLD_HOME_TABS).isdisjoint(
        dashboard.TABS_BY_PAGE[dashboard.HOME_PAGE])


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
    # One menu for everyone: the only selector of the sidebar is the theme.
    assert [box.label for box in app.sidebar.selectbox] == ["Tema"]


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
        assert page in dashboard.PAGE_OF_TAB or state == "pending"


@needs_database
@pytest.mark.parametrize("view", ["Precios semanales", "Márgenes", "Alertas"])
def test_consultas_page_draws_every_view_as_table_and_as_chart(view):
    app = draw_page(dashboard.PAGE_DATA_AND_CODE)
    app.radio(key="explorer_view").set_value(view).run()
    assert not app.exception
    assert len(app.dataframe) == 1
    app.toggle(key="explorer_chart").set_value(True).run()
    assert not app.exception
    assert not app.dataframe


@needs_database
def test_consultas_page_refuses_week_and_month_together():
    app = draw_page(dashboard.PAGE_DATA_AND_CODE)
    app.checkbox(key="explorer_group_Precios semanales_Semana").check().run()
    app.checkbox(key="explorer_group_Precios semanales_Mes").check().run()
    assert not app.exception
    assert "Elige semana o mes, no los dos a la vez." in [warning.value
                                                         for warning in app.warning]


@needs_database
def test_gap_tab_shows_k5_with_its_descriptive_note():
    app = draw_page(dashboard.PAGE_ANALYSIS)
    assert not app.exception
    assert dashboard.LAG_NOTE in [caption.value for caption in app.caption]
    assert any("semanas" in block.value or "Sin relación clara" in block.value
               for block in app.markdown)


@needs_database
def test_d056_home_is_short_and_documents_in_tabs():
    app = draw_page(dashboard.HOME_PAGE)
    assert not app.exception
    assert [tab.label for tab in app.tabs] == dashboard.TABS_BY_PAGE[dashboard.HOME_PAGE]
    # The page style names every class; only the drawn blocks count.
    texts = " ".join(block.value for block in app.markdown if "<style" not in block.value)
    assert "Estado de la última ejecución (" in texts
    assert "se actualiza al recargar la página" in texts
    # The five steps only on phones; the whole diagram only in Arquitectura.
    assert 'class="diagram-fit phone-only"' in texts
    for absent in ["diagram-wide", "diagram-narrow", "zoom-frame",
                   "Ver la arquitectura completa", ">DevOps<"]:
        assert absent not in texts
    assert "Sigla o término" in texts


@needs_database
def test_d056_architecture_draws_each_diagram_once():
    app = draw_page(dashboard.PAGE_ARCHITECTURE)
    assert not app.exception
    assert [tab.label for tab in app.tabs] == dashboard.TABS_BY_PAGE[
        dashboard.PAGE_ARCHITECTURE]
    joined = " ".join(block.value for block in app.markdown)
    # Pipeline (wide and vertical), star and infrastructure: four zoomable frames.
    assert joined.count('class="zoom-frame ') == 4
    assert joined.count('class="zoom-frame diagram-wide"') == 1
    assert joined.count('class="zoom-frame diagram-narrow"') == 1
    assert joined.count('class="star-model"') == 1
    assert not app.get("graphviz_chart")
    assert any("diagramZoomReady" in block.proto.body for block in app.get("html"))
    for heading in ["DevOps", "Seguridad", "Observabilidad", "Informes"]:
        assert f">{heading}<" in joined


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


@needs_database
def test_t57_queries_section_shows_the_real_count_and_each_query_in_its_group():
    """The number shown is the one of «-- name:» lines; each query under its level."""
    named_count = queries.QUERIES_FILE.read_text(encoding="utf-8").count("\n-- name: ")
    app = draw_page(dashboard.PAGE_DATA_AND_CODE)
    texts = [block.value for block in app.markdown]
    assert f"### {named_count} queries del proyecto" in texts
    shown_group = {}
    group = None
    for text in texts:
        if text.startswith("#### "):
            group = text[5:].split(" · ")[0]
        elif text.startswith("**") and group:
            shown_group.setdefault(text[2:].split("**")[0], group)
    levels = {query["name"]: query["level"] for query in project.list_named_queries()}
    assert len(levels) == named_count
    assert {name: shown_group.get(name) for name in levels} == levels
    assert shown_group[project.MATCH_COVERAGE_QUERY_NAME] == "Fuera de bi/queries.sql"


@needs_database
def test_queries_tab_runs_a_query_when_asked():
    app = draw_page(dashboard.PAGE_DATA_AND_CODE)
    app.button(key="preview_k1_margin").click().run()
    assert not app.exception
    assert any(len(frame.value) == 20 for frame in app.dataframe)


def test_kpi_link_opens_the_kpi_tab_with_that_indicator():
    link = dashboard.build_kpi_link("K5")
    assert 'href="./?seccion=KPI+y+c%C3%A1lculos&amp;kpi=K5"' in link


def test_d056_a_place_named_in_a_document_opens_its_page_and_tab():
    assert dashboard.build_place_address(dashboard.TAB_QUALITY) == (
        "operaciones?seccion=Calidad+de+datos")
    assert dashboard.build_place_address(dashboard.TAB_KPI) == "./?seccion=KPI+y+c%C3%A1lculos"
    assert dashboard.build_place_address(dashboard.PAGE_ANALYSIS) == "analisis"


def test_t52_every_link_of_the_project_points_to_a_page_that_exists():
    """The home page lives at './'; any other page at its own path (A1)."""
    other_paths = {path for title, path in dashboard.PAGE_PATHS.items()
                   if title != dashboard.HOME_PAGE}
    for journey in [dashboard.JOURNEY_MANAGER, dashboard.JOURNEY_ANALYST,
                    dashboard.JOURNEY_TECHNICAL]:
        for _, address in dashboard.list_journey_steps(journey):
            path = address.split("?")[0]
            assert path == "./" or path in other_paths, address
    assert dashboard.build_page_address(dashboard.HOME_PAGE) == "./"
    assert dashboard.build_page_address(dashboard.PAGE_ANALYSIS) == "analisis"


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


def test_t44_vantablack_is_the_default_theme():
    assert dashboard.get_mode() == charts.MODE_DARK


def test_t44_base_mode_switch_writes_streamlit_choice_and_tries_only_once():
    script = dashboard.build_base_mode_script(charts.BASE_LIGHT)
    assert '"stActiveTheme-" + page.location.pathname + "-v2"' in script
    assert 'JSON.stringify("Light")' in script
    # A second attempt on the same page and base is skipped: no endless reload.
    assert "if (!page.sessionStorage.getItem(attempt))" in script
    assert 'JSON.stringify("Dark")' in dashboard.build_base_mode_script(charts.BASE_DARK)


# region Administration (T-54)
ADMIN_ADDRESSES = [link["url"] for link in dashboard.ADMIN_LINKS]
FAKE_TOKEN = "github_pat_FAKE_SECRET_123"


def draw_control_page(secrets):
    """The Operaciones page with GitHub replaced by fixed answers, no network."""
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "from datetime import datetime, timezone\n"
              "from bi import control, dashboard\n"
              "control.list_workflow_runs = lambda *args, **kwargs: []\n"
              "control.read_token_expiration = lambda token: datetime(2026, 10, 20, "
              "tzinfo=timezone.utc)\n"
              "dashboard.render_page(dashboard.PAGE_OPERATIONS)\n")
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


@needs_database
def test_t54_administration_is_hidden_without_the_control_code():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN})
    assert not app.exception
    text = read_page_text(app)
    assert "Requiere clave de control" in text
    assert not [address for address in ADMIN_ADDRESSES if address in text]
    app.text_input[0].input("equivocada").run()
    [button for button in app.button if button.label == "Desbloquear"][0].click().run()
    assert not [address for address in ADMIN_ADDRESSES if address in read_page_text(app)]


@needs_database
def test_t54_the_right_code_opens_administration_and_never_shows_the_token():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN})
    app.text_input[0].input("clave").run()
    [button for button in app.button if button.label == "Desbloquear"][0].click().run()
    assert not app.exception
    text = read_page_text(app)
    assert all(address in text for address in ADMIN_ADDRESSES)
    assert "Tu token vence en" in text
    assert FAKE_TOKEN not in text
    assert FAKE_TOKEN[-6:] not in text


@needs_database
def test_d056_project_links_live_only_in_operaciones_and_never_as_text():
    for title in ALL_PAGES:
        texts = [element.proto.body for element in draw_page(title).get("html")]
        links = "\n".join(texts)
        for link in project.PROJECT_LINKS:
            if link["url"]:
                shown = f'href="{link["url"]}"' in links
                assert shown == (title == dashboard.PAGE_OPERATIONS), (title, link["name"])
                # The address lives only in the link, never as visible text.
                assert f'>{link["url"]}<' not in links
# endregion


def test_architecture_tables_show_file_names_not_long_links():
    cell = dashboard.format_architecture_cell(".github/workflows/semanal.yml")
    assert cell == '<code title=".github/workflows/semanal.yml">semanal.yml</code>'
    assert "<a " in dashboard.format_architecture_cell(dashboard.TAB_QUALITY)


def test_d057_cards_escape_their_text_and_keep_bold_and_code():
    card = dashboard.build_info_card_html("<b>Título</b>", "Texto con **negrita** y `datos.db`",
                                          label="P1", note="nota")
    assert "<b>Título</b>" not in card and "&lt;b&gt;Título&lt;/b&gt;" in card
    assert "<strong>negrita</strong>" in card and "<code>datos.db</code>" in card
    assert 'class="info-label">P1<' in card


def test_d057_links_say_where_they_go():
    link = dashboard.build_place_link(dashboard.TAB_GAP)
    assert ">Ver en Análisis › Brecha de precio<" in link
    assert ">Ir a Operaciones › Calidad de datos<" in dashboard.build_place_link(
        dashboard.TAB_QUALITY, "Ir a")
    steps = dashboard.build_steps_html([("Nombres", "se separan"), ("Unidades", "a kilo")])
    assert steps.count("<li>") == 2 and steps.startswith('<ol class="steps">')
