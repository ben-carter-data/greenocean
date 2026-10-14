"""Tests for the dashboard: profiles, pages, key figures and footer."""
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
from bi import charts, control, dashboard, explorer, project, queries  # noqa: E402

DASHBOARD_FILE = str(PROJECT_DIR / "bi" / "dashboard.py")
# These tests draw the real dashboard, so they need the committed database.
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(),
                                    reason="etl/datos.db has not been built")
ALL_PAGES = dashboard.PAGES


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
        match = re.search(r'class="compact-header"><h1[^>]*>([^<]+)</h1>', block.value)
        if match:
            return html.unescape(match.group(1))
    return None


def draw_page(title):
    """Draw one page alone, the way the navigation does."""
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              f"from bi import dashboard\ndashboard.render_page({title!r})\n")
    return AppTest.from_string(script, default_timeout=60).run()


def test_d065_six_windows_hold_every_view_once_and_charts_only_in_dashboard():
    assert list(dashboard.WINDOWS) == ["Dashboard", "Proyecto y negocio", "Arquitectura",
                                       "Datos y código", "Operación", "Documentación"]
    views = [view for window in dashboard.WINDOWS.values() for view in window]
    assert len(views) == len(set(views)) and set(views) == set(dashboard.SHOW_PAGE_BY_TITLE)
    assert dashboard.WINDOWS["Dashboard"] == [
        dashboard.HOME_PAGE, dashboard.PAGE_ANALYSIS, dashboard.PAGE_GAP, dashboard.PAGE_CHANNELS,
        dashboard.PAGE_ALERTS, dashboard.PAGE_SEASONALITY, dashboard.PAGE_3D]
    assert dashboard.WINDOWS["Arquitectura"] == [
        dashboard.PAGE_DIAGRAMS, dashboard.PAGE_ARCHITECTURE, dashboard.PAGE_DEVOPS]
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
def test_d065_the_profile_is_offered_once_and_is_not_required():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert not app.exception
    assert app.radio[0].label == "¿Quién consulta?"
    # The dashboard is drawn behind the offer: nothing waits for a profile.
    assert read_page_title(app) == "Precios de alimentos · Chile"
    app.button(key="previous_view").click().run()
    assert not app.exception and not app.radio
    assert app.session_state.get(dashboard.PROFILE_PARAMETER) is None


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


@needs_database
def test_d060_search_shows_form_summary_and_table():
    app = draw_page(dashboard.PAGE_DATA_AND_CODE)
    assert not app.exception
    labels = [box.label for box in app.selectbox]
    for field in explorer.SEARCH_FIELDS:
        assert explorer.FIELD_LABELS[field] in labels
    texts = " ".join(block.value for block in app.markdown)
    for state in explorer.ALERT_STATES:
        assert dashboard.ALERT_STATE_PUBLIC_LABELS[state] in texts
    assert "Grupo de alimentos" in texts
    assert "Mostrando 1 a 20 de" in texts
    assert len(app.dataframe) >= 1
    sql_details = next(expander for expander in app.expander
                       if expander.label.startswith("Cómo se construyó esta búsqueda"))
    assert sql_details.proto.expanded


@needs_database
def test_d060_a_summary_card_applies_its_filter_and_shows_a_chip():
    app = draw_page(dashboard.PAGE_DATA_AND_CODE)
    app.button(key=f"filter_state_{explorer.ALERT_OUT}").click().run()
    assert not app.exception
    assert app.session_state["search_applied"][explorer.FIELD_ALERT] == explorer.ALERT_OUT
    chip = app.button(key=f"chip_{explorer.FIELD_ALERT}")
    assert chip.label == (f"{explorer.FIELD_LABELS[explorer.FIELD_ALERT]}: "
                          f"{dashboard.ALERT_STATE_PUBLIC_LABELS[explorer.ALERT_OUT]} ✕")
    chip.click().run()
    assert app.session_state["search_applied"][explorer.FIELD_ALERT] == explorer.ALL


@needs_database
def test_gap_tab_shows_k5_with_its_descriptive_note():
    app = draw_page(dashboard.PAGE_GAP)
    assert not app.exception
    assert dashboard.LAG_NOTE in [caption.value for caption in app.caption]
    assert any("semanas" in block.value or "Sin relación clara" in block.value
               for block in app.markdown)


@needs_database
def test_dashboard_opens_with_data_and_diagrams_have_their_own_page():
    app = draw_page(dashboard.HOME_PAGE)
    assert not app.exception and not app.tabs
    texts = " ".join(block.value for block in app.markdown)
    assert "Top 8" in texts and "811.578" in texts
    assert 'class="zoom-frame' not in texts and "animateMotion" not in texts
    assert texts.index("Top 8 · cambios") < texts.index("¿Qué grupo subió más?")
    figures = [json.loads(chart.proto.spec) for chart in app.get("plotly_chart")]
    assert len(figures) == 2
    assert {trace["type"] for figure in figures for trace in figure["data"]} == {
        "heatmap", "scatter"}
    assert "scatter3d" not in {trace["type"] for figure in figures for trace in figure["data"]}
    assert texts.count('class="overview-metric"') == 4
    diagrams = draw_page(dashboard.PAGE_DIAGRAMS)
    texts = " ".join(block.value for block in diagrams.markdown)
    assert not diagrams.exception and not diagrams.tabs
    assert 'class="zoom-frame diagram-wide"' in texts
    assert 'class="zoom-frame diagram-narrow"' in texts
    assert "animateMotion" in texts
    assert "ilustra el recorrido" in " ".join(c.value for c in diagrams.caption)


@needs_database
def test_dashboard_territory_is_immediately_readable_without_a_3d_duplicate():
    app = draw_page(dashboard.HOME_PAGE)
    assert not app.exception
    figures = [json.loads(chart.proto.spec) for chart in app.get("plotly_chart")]
    assert len(figures) == 2
    types = {trace["type"] for figure in figures for trace in figure["data"]}
    assert "heatmap" in types and "scatter3d" not in types

@needs_database
def test_model_has_its_diagram_and_devops_links_to_the_single_infrastructure():
    app = draw_page(dashboard.PAGE_ARCHITECTURE)
    assert not app.exception and not app.tabs
    joined = " ".join(block.value for block in app.markdown)
    assert joined.count('class="star-model"') == 1
    app = draw_page(dashboard.PAGE_DEVOPS)
    assert not app.exception and not app.tabs
    joined = " ".join(block.value for block in app.markdown)
    assert joined.count('class="zoom-frame ') == 0
    assert 'aria-label="Ciclo DevOps del proyecto' in joined
    assert joined.count('class="technical-rows"') == len(dashboard.ARCHITECTURE_GROUPS)
    assert "Ver el pipeline y la arquitectura" in joined
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
def test_t57_queries_section_shows_the_real_count_and_each_query_open_by_its_part():
    """The number shown is the one of «-- name:» lines; each query under the part of the
    panel that uses it, in an expander open by default."""
    named_count = queries.QUERIES_FILE.read_text(encoding="utf-8").count("\n-- name: ")
    app = draw_page(dashboard.PAGE_QUERIES)
    texts = [block.value for block in app.markdown]
    assert f"### {named_count} consultas del proyecto" in texts
    catalog = project.list_named_queries()
    labels = {expander.label.rsplit("nombre técnico: ", 1)[-1]: expander
              for expander in app.expander if "nombre técnico: " in expander.label}
    for query in catalog + [{"name": project.MATCH_COVERAGE_QUERY_NAME}]:
        assert labels[query["name"]].proto.expanded, query["name"]
    parts = [text[5:].split(" · ")[0] for text in texts if text.startswith("#### ")]
    assert "Brecha de precio" in parts and parts[-1] == "Fuera de bi/queries.sql"
    assert not [text for text in texts if "Intermedio" in text or "Avanzado" in text]


@needs_database
def test_queries_tab_runs_a_query_when_asked():
    app = draw_page(dashboard.PAGE_QUERIES)
    app.button(key="preview_k1_margin").click().run()
    assert not app.exception
    assert any(len(frame.value) == 20 for frame in app.dataframe)


def test_kpi_link_opens_the_kpi_view_with_that_indicator():
    link = dashboard.build_kpi_link("K5")
    assert 'href="proyecto?kpi=K5&amp;vista=Indicadores+explicados"' in link
    assert ">K5<" not in link


def test_d065_a_place_named_in_a_document_opens_its_window_and_view():
    assert dashboard.build_place_address(dashboard.TAB_QUALITY) == "operacion"
    assert dashboard.build_place_address(dashboard.TAB_KPI) == (
        "proyecto?vista=Indicadores+explicados")
    assert dashboard.build_place_address(dashboard.PAGE_ANALYSIS) == "./?vista=Esta+semana"


def test_t52_every_link_of_the_project_points_to_a_window_that_exists():
    """The first window lives at './'; any other one at its own path."""
    paths = set(dashboard.WINDOW_PATHS.values())
    for journey in [dashboard.JOURNEY_MANAGER, dashboard.JOURNEY_ANALYST,
                    dashboard.JOURNEY_TECHNICAL]:
        for _, address in dashboard.list_journey_steps(journey):
            path = address.split("?")[0]
            assert path == "./" or path in paths, address
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


def test_t44_vantablack_is_the_default_theme():
    assert dashboard.get_mode() == charts.MODE_DARK


def test_t44_base_mode_switch_writes_streamlit_choice_and_tries_only_once():
    script = dashboard.build_base_mode_script(charts.BASE_LIGHT)
    assert '"stActiveTheme-" + page.location.pathname + "-v2"' in script
    assert 'const wanted = "Light"' in script
    # A second attempt on the same page and base is skipped: no endless reload.
    assert "current !== wanted && requested !== wanted" in script
    assert 'const wanted = "Dark"' in dashboard.build_base_mode_script(charts.BASE_DARK)
    graphite = dashboard.build_base_mode_script(charts.MODE_GRAPHITE)
    assert 'const wanted = "Dark"' in graphite
    assert 'address.searchParams.set("tema", "Grafito")' in graphite


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
              "dashboard.render_page(dashboard.PAGE_RUNS)\n")
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
def test_project_links_are_grouped_as_a_tree_with_descriptions():
    app = draw_page(dashboard.PAGE_LINKS)
    assert not app.exception
    links = "\n".join(block.value for block in app.markdown)
    assert 'class="resource-tree"' in links
    for link in project.PROJECT_LINKS:
        if link["url"]:
            assert f'href="{link["url"]}"' in links
            assert html.escape(link["description"]) in links
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
def test_d057_kpi_tab_shows_eight_cards_and_opens_the_asked_one_first():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "import streamlit as st\nst.query_params['kpi'] = 'K5'\n"
              "from bi import dashboard\ndashboard.show_kpi_tab(dashboard.charts.MODE_DARK)\n")
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    cards = " ".join(block.value for block in app.markdown if 'class="info-grid"' in block.value)
    assert cards.count('class="info-card"') == 8
    indicators = {row["ID"]: row["Indicador"]
                  for row in project.read_design_table(project.INDICATORS_HEADING)}
    assert cards.index(indicators["K5"]) < cards.index(indicators["K1"])
    assert 'info-label">K' not in cards
    assert "Fórmula:" in cards and "Ver en Brecha de precio" in cards
    assert [expander.label for expander in app.expander][0] == (
        f"Cómo se calcula «{indicators['K5']}»")
    assert "¿Cómo se calcula?" in dashboard.build_kpi_link("K7")
    assert ">K7<" not in dashboard.build_kpi_link("K7")


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
def test_d057_manual_tab_shows_every_section_of_the_manual():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "from bi import dashboard\ndashboard.show_manual_tab(dashboard.charts.MODE_DARK)\n")
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    texts = " ".join(block.value for block in app.markdown)
    assert texts.count("<li>") == 7
    # The automatic part and the four tasks of the author, one card each.
    tasks = [block.value for block in app.markdown if "Automáticas, sin intervención" in block.value]
    assert tasks[0].count('class="info-card"') == 5
    labels = " ".join(expander.label for expander in app.expander).lower()
    # Two sections take a plainer title in the panel; the glossary keeps its terms folded.
    shown_titles = {"Cómo leer un aviso rojo": "Si algo falla",
                    "Tareas de la autora y tareas automáticas": "Qué hace la autora",
                    "Glosario": "Glosario"}
    for heading, _ in project.split_sections(project.read_document(project.MANUAL_FILE)):
        title = shown_titles.get(heading, heading)
        assert f">{html.escape(title)}<" in texts or title.lower() in labels, heading


def test_d057_key_decisions_exist_and_the_rest_go_newest_first():
    numbers = {dashboard.split_decision_title(title)[0] for title, _ in project.list_decisions()}
    key_numbers = [number for _, _, group in dashboard.KEY_DECISIONS for number in group]
    assert len(key_numbers) == len(set(key_numbers)) == 12
    assert set(key_numbers) <= numbers
    assert dashboard.read_first_sentence("Uno. Dos.") == "Uno."


@needs_database
def test_d057_decisions_tab_shows_twelve_cards_and_folds_the_rest():
    script = (f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
              "from bi import dashboard\ndashboard.show_decisions_tab(dashboard.charts.MODE_DARK)\n")
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    cards = " ".join(block.value for block in app.markdown if 'class="info-grid"' in block.value)
    assert cards.count('class="info-card"') == 12
    folded = [expander.label for expander in app.expander if expander.label.startswith("D-")]
    folded_numbers = [int(label[2:5]) for label in folded]
    assert folded_numbers == sorted(folded_numbers, reverse=True)
    assert len(folded) == len(project.list_decisions()) - 12


def test_d057_every_theme_of_the_glossary_says_what_it_groups():
    themes = {row["Tema"] for row in project.read_guide_table("Glosario")}
    assert themes == set(dashboard.GLOSSARY_THEME_LEADS)


def test_d057_every_file_of_the_readme_falls_in_one_known_folder():
    folders = [folder for folder, _, _ in dashboard.FOLDER_PURPOSES]
    assert folders[:2] == ["", "agent/"] and folders[-1] == "docs/"
    paths = [path for path, _, _ in project.list_repository_files()]
    assert {dashboard.find_folder(path) for path in paths} <= set(folders)
    assert dashboard.find_folder("bi/zoom.py") == "bi/"
    assert "bi/zoom.py" in paths and "bi/star_model.py" in paths
    line = dashboard.build_file_line_html("bi/zoom.py", "zoom", "https://github.com/x")
    assert ">zoom.py</a> — zoom</li>" in line


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
    assert dashboard.build_place_address(dashboard.PAGE_LINKS) == (
        "documentacion?vista=Enlaces")
    groups = {link["group"] for link in project.PROJECT_LINKS}
    assert groups == {"Código y operación", "Fuentes de datos", "Documentos"}
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
        dashboard.PAGE_ANALYSIS: "Mayores variaciones de la semana",
        dashboard.PAGE_GAP: "Mayorista y consumidor, la última semana",
        dashboard.PAGE_CHANNELS: "Precio por región",
        dashboard.PAGE_SEASONALITY: "Calendario de precios",
        dashboard.PAGE_ALERTS: "Alertas de la semana",
    }
    for page, title in expected.items():
        app = draw_page(page)
        assert not app.exception and not app.tabs, page
        assert title in " ".join(block.value for block in app.markdown)

def test_d060_queries_are_grouped_by_the_part_of_the_panel_that_uses_them():
    parts = dashboard.group_queries_by_part(project.list_named_queries())
    assert sum(len(group) for group in parts.values()) == len(project.list_named_queries())
    assert any(part.startswith("Dashboard") for part in parts)
    assert all(" › " in part or part in dashboard.PAGES for part in parts)


@needs_database
def test_d060_every_query_shows_its_sql_without_unfolding_it():
    app = draw_page(dashboard.PAGE_QUERIES)
    assert not app.exception
    named_count = len(project.list_named_queries())
    # Every query card has its SQL as a code block in sight, not inside an expander.
    assert len([block for block in app.code if "SELECT" in block.value.upper()]) >= named_count


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
def test_code_walkthrough_is_visible_and_collapsible_with_real_sources():
    app = draw_page(dashboard.PAGE_CODE)
    assert not app.exception
    entries = project.list_code_walkthrough()
    for entry in entries:
        block = next(block for block in app.code if block.value.strip() == entry["source"].strip())
        assert block.value.startswith('"""')
        expander = next(expander for expander in app.expander if entry["path"] in expander.label)
        assert expander.proto.expanded
    assert any(block.language == "sql" for block in app.code)


@needs_database
def test_latest_gaps_keep_only_the_current_week_and_match_their_prices():
    rows = dashboard.read_cached_latest_gaps(dashboard.get_database_version())
    assert set(rows.week_start) == {dashboard.read_latest_week()}
    assert rows.margin.is_monotonic_decreasing and len(rows) <= 50
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
    for page in dashboard.PAGES:
        app = draw_page(page)
        assert not app.exception and not app.tabs, page
        texts = " ".join(block.value for block in app.markdown)
        assert ("Top 8 · cambios" in texts) == (page == dashboard.HOME_PAGE)
        assert ('class="zoom-frame diagram-wide"' in texts) == (page == dashboard.PAGE_DIAGRAMS)
        assert (">Arquitectura por plataforma<" in texts) == (page == dashboard.PAGE_DIAGRAMS)


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


def test_d065_previous_and_next_go_round_the_views_of_a_window():
    window = "Arquitectura"
    key = dashboard.window_view_key(window)
    dashboard.st.session_state[key] = dashboard.PAGE_DIAGRAMS
    dashboard.step_view(window, -1)
    assert dashboard.st.session_state[key] == dashboard.PAGE_DEVOPS
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
    assert read_page_title(app) == dashboard.PAGE_GAP
    assert "seccion" not in app.query_params


@needs_database
def test_old_section_links_can_redirect_with_a_bound_theme():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Analista BI"
    app.query_params["tema"] = "Corporativo"
    app.query_params["seccion"] = dashboard.TAB_GAP
    app.run()
    assert not app.exception
    assert read_page_title(app) == dashboard.PAGE_GAP


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
    assert dashboard.ATTRIBUTION_TEXT in [caption.value for caption in app.caption]


@needs_database
def test_a_kpi_link_opens_its_canonical_query_without_repeating_it():
    app = draw_page(dashboard.PAGE_KPI)
    assert not [block for block in app.code if block.language == "sql"]
    script = ("import streamlit as st\nst.query_params['consulta']='k7_match_coverage'\n"
              "from bi import dashboard\ndashboard.show_queries_tab(dashboard.charts.MODE_DARK)")
    catalog = AppTest.from_string(script, default_timeout=60).run()
    assert not catalog.exception
    assert catalog.expander[0].label.endswith("nombre técnico: k7_match_coverage")
    assert sum(expander.label.endswith("nombre técnico: k7_match_coverage")
               for expander in catalog.expander) == 1


def test_d066_each_profile_orders_the_same_windows_and_starts_at_the_first():
    for profile, order in dashboard.PROFILE_WINDOW_ORDER.items():
        assert sorted(order) == sorted(dashboard.WINDOWS), profile
    assert set(dashboard.PROFILE_WINDOW_ORDER) == set(dashboard.VISITOR_PROFILES)
    assert dashboard.order_windows("Sin perfil") == list(dashboard.WINDOWS)
    order = dashboard.order_windows("Ingeniería de datos")
    assert order[0] == "Arquitectura"
    assert dashboard.number_window("Dashboard", order) == "04 · Dashboard"


@needs_database
def test_d066_a_profile_reorders_the_menu_and_the_sidebar_does_not_show_it():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["perfil"] = "Ingeniería de datos"
    app.run()
    assert not app.exception
    # The visit starts at the first window of the profile: Arquitectura, its pipeline.
    assert read_page_title(app) == dashboard.PAGE_DIAGRAMS
    sidebar = " ".join(block.value for block in app.sidebar.markdown)
    assert "Ingeniería de datos" not in sidebar
    assert not [button for button in app.sidebar.button if "perfil" in button.label]


def test_d067_report_pages_use_a_compact_header_and_short_kpi_links():
    dashboard.st.session_state[dashboard.COMPACT_VIEW] = True
    try:
        compact_link = dashboard.build_kpi_link("K6")
        assert compact_link.count(">Cómo se calcula ↗<") == 1
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
    assert sentence == ("Esta semana subieron 214 precios y bajaron 180. 46 productos "
                        "subieron más de 10 %; la mayor alza fue Manzana en Mayorista (+55,6 %).")
    figures = dashboard.build_business_figures_html(summary, charts.MODE_DARK)
    assert "▲ 14 frente a la semana anterior (suben)" in figures
    assert "▼ 7 frente a la semana anterior" in figures
    assert "▼ 0,6 pts frente a la semana anterior" in figures
    assert "Observaciones históricas" not in figures
