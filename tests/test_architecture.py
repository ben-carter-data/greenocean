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
