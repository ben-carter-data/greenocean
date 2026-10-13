"""Tests for the live data journey diagram."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import architecture, charts, control  # noqa: E402

FIGURES = {"source_years": "año 2026", "last_run": "última 12-10 05:51",
           "rows_read": "397.814 filas leídas", "rows_rejected": "0 filas",
           "weekly_prices": "131.144 precios", "latest_week": "hasta 05-10-2026",
           "panel_time": "datos al 12-10 05:52", "next_run": "13-10 09:00"}
STATE_NAMES = ["sources", "download", "etl", "tests", "report", "workflow", "load", "panel"]


def make_states(state):
    return {name: state for name in STATE_NAMES}


def test_every_layer_and_step_is_drawn():
    svg = architecture.build_journey_svg(make_states(control.RUN_OK), FIGURES,
                                         charts.MODE_DARK)
    for text in ["FUENTES", "INGESTA", "BRONCE", "LIMPIEZA", "REGLAS", "CALIDAD", "ORO",
                 "CONSUMO", "raw.db", "datos.db", "Rechazos", "GitHub Actions",
                 "OBSERVABILIDAD"]:
        assert text in svg


def test_figures_from_the_data_appear_under_their_steps():
    svg = architecture.build_journey_svg(make_states(control.RUN_OK), FIGURES,
                                         charts.MODE_LIGHT)
    for figure in FIGURES.values():
        assert figure in svg


def test_status_dots_follow_the_real_state_and_only_running_steps_pulse():
    states = make_states(control.RUN_OK)
    states["etl"] = control.RUN_IN_PROGRESS
    svg = architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK)
    # The ETL state is shown on two steps: cleaning and business rules.
    assert svg.count('class="journey-running"') == 2
    states["load"] = control.RUN_FAILED
    svg = architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK)
    assert architecture.STATE_COLORS[control.RUN_FAILED] in svg


def test_text_from_the_data_is_escaped():
    figures = dict(FIGURES, rows_read="<b>397.814</b>")
    svg = architecture.build_journey_svg(make_states(control.RUN_OK), figures,
                                         charts.MODE_DARK)
    assert "<b>397.814</b>" not in svg
    assert "&lt;b&gt;397.814&lt;/b&gt;" in svg


def test_d043_dots_travel_along_the_arrows_only_while_a_run_is_in_progress():
    idle_svg = architecture.build_journey_svg(make_states(control.RUN_OK), FIGURES,
                                              charts.MODE_DARK)
    assert "animateMotion" not in idle_svg
    running_states = dict(make_states(control.RUN_OK), workflow=control.RUN_IN_PROGRESS)
    running_svg = architecture.build_journey_svg(running_states, FIGURES, charts.MODE_DARK)
    assert "animateMotion" in running_svg


def test_mini_journey_shows_real_figures_and_states():
    states = dict(make_states(control.RUN_OK), load=control.RUN_FAILED)
    svg = architecture.build_mini_journey_svg(states, FIGURES, charts.MODE_LIGHT)
    for figure in ["año 2026", "131.144 precios", "397.814 filas leídas"]:
        assert figure in svg
    assert architecture.STATE_COLORS[control.RUN_FAILED] in svg
    assert "animateMotion" not in svg


def test_only_real_states_get_a_dot_and_an_unknown_one_gets_none():
    states = dict(make_states(control.RUN_OK), report=architecture.STATE_UNKNOWN,
                  etl_run=control.RUN_FAILED)
    svg = architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK)
    grey = architecture.STATE_COLORS[architecture.STATE_UNKNOWN]
    # The grey of the column subtitles is text, not a dot: only circles count.
    assert f'r="7" fill="{grey}"' not in svg
    assert f'r="5" fill="{grey}"' not in svg
    # etl_run takes the state of the latest load.
    assert architecture.STATE_COLORS[control.RUN_FAILED] in svg
    # Items with no state to read (secrets, logs, mail) have no dot.
    item_without_state = architecture.build_band_item(0, 0, "Secretos", "clave",
                                                      charts.get_palette(charts.MODE_DARK))
    assert "<circle" not in item_without_state


def test_vertical_journey_has_every_step_figure_and_real_state():
    states = dict(make_states(control.RUN_OK), load=control.RUN_FAILED,
                  report=architecture.STATE_UNKNOWN)
    svg = architecture.build_vertical_journey_svg(states, FIGURES, charts.MODE_DARK)
    for text in ["FUENTES", "INGESTA", "BRONCE", "LIMPIEZA", "REGLAS", "CALIDAD", "ORO",
                 "CONSUMO", "raw.db", "datos.db", "Rechazos", "GitHub Actions",
                 "OBSERVABILIDAD", "Panel Streamlit", "Informe semanal", "Consultas SQL"]:
        assert text in svg
    for figure in FIGURES.values():
        assert figure in svg
    assert architecture.STATE_COLORS[control.RUN_FAILED] in svg
    grey = architecture.STATE_COLORS[architecture.STATE_UNKNOWN]
    assert f'r="7" fill="{grey}"' not in svg


def test_vertical_journey_moves_its_dots_only_while_a_run_is_in_progress():
    idle_svg = architecture.build_vertical_journey_svg(make_states(control.RUN_OK), FIGURES,
                                                       charts.MODE_LIGHT)
    assert "animateMotion" not in idle_svg
    running_states = dict(make_states(control.RUN_OK), workflow=control.RUN_IN_PROGRESS)
    assert "animateMotion" in architecture.build_vertical_journey_svg(
        running_states, FIGURES, charts.MODE_LIGHT)


def test_d051_diagram_stays_still_unless_a_run_is_in_progress():
    """Idle: no travelling dots and no moving dashes; only the status dots speak."""
    idle_states = make_states(control.RUN_OK)
    running_states = dict(idle_states, workflow=control.RUN_IN_PROGRESS)
    for build in [architecture.build_journey_svg, architecture.build_mini_journey_svg,
                  architecture.build_vertical_journey_svg]:
        idle_svg = build(idle_states, FIGURES, charts.MODE_DARK)
        assert "animateMotion" not in idle_svg
        assert "animation: journey-dash" not in idle_svg
        assert "animation: journey-dash" in build(running_states, FIGURES, charts.MODE_DARK)


DEVOPS_FIGURES = dict(FIGURES, database_size="33,9 MB", test_functions="180 funciones de prueba",
                      week_prices="semana 05-10: 4.211 precios")


def test_d054_infrastructure_draws_each_platform_its_components_and_figures():
    states = dict(make_states(control.RUN_OK), report=control.RUN_FAILED)
    svg = architecture.build_devops_svg(states, DEVOPS_FIGURES, charts.MODE_DARK)
    for text in ["ODEPA", "TU COMPUTADOR", "GITHUB", "STREAMLIT COMMUNITY CLOUD", "USUARIOS",
                 "Claude Code", "Repositorio", "Pruebas (CI)", "Job semanal.yml",
                 "Caché de Actions", "Issues", "Permisos del job", "Secretos",
                 "App Streamlit", "Visitantes", "HTTPS · CSV", "git push",
                 "checkout · commit", "gh issue create", "on: push", "despliegue de main",
                 "st.secrets"]:
        assert text in svg
    for figure in ["33,9 MB", "180 funciones de prueba", "semana 05-10: 4.211 precios",
                   FIGURES["source_years"], FIGURES["next_run"], FIGURES["panel_time"]]:
        assert figure in svg
    assert architecture.STATE_COLORS[control.RUN_FAILED] in svg


def test_d054_devops_diagram_moves_only_while_the_job_runs():
    idle_svg = architecture.build_devops_svg(make_states(control.RUN_OK), DEVOPS_FIGURES,
                                             charts.MODE_LIGHT)
    assert "animateMotion" not in idle_svg
    running_states = dict(make_states(control.RUN_OK), workflow=control.RUN_IN_PROGRESS)
    assert "animateMotion" in architecture.build_devops_svg(running_states, DEVOPS_FIGURES,
                                                            charts.MODE_LIGHT)


def test_every_piece_of_every_diagram_explains_itself_on_hover():
    """Each card, band item and link label carries a <title>: the browser shows it on
    hover. Acronyms are spelled out where they appear."""
    import re
    states = make_states(control.RUN_OK)
    for svg in [architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK),
                architecture.build_vertical_journey_svg(states, FIGURES, charts.MODE_DARK),
                architecture.build_devops_svg(states, DEVOPS_FIGURES, charts.MODE_DARK)]:
        titles = re.findall(r'font-weight="700" fill="[^"]+">([^<]+)</text>', svg)
        explained = set(re.findall(r"<title>([^<]+)</title>", svg))
        assert titles and len(explained) >= len(set(titles)) // 2
    devops = architecture.build_devops_svg(states, DEVOPS_FIGURES, charts.MODE_DARK)
    assert "CI = integración continua" in devops
    assert "HTTPS: conexión web cifrada" in devops
    journey = architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK)
    assert "ETL = extraer, transformar y cargar" in journey
    assert all(text in architecture.TOOLTIPS for text in ["Pruebas (CI)", "datos.db", "raw.db"])
