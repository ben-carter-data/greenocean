"""Tests for the Centro de operación (D-165) and the phone layout (D-166)."""

import re
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts, control, dashboard, operation_center, project, queries  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
RUN = {"id": 7, "state": control.RUN_FAILED, "trigger": "Manual", "url": "https://github.com/x/y/actions/runs/7"}
JOB = {
    "html_url": "https://github.com/x/y/actions/runs/7/job/70",
    "steps": [
        {
            "name": "Set up job",
            "number": 1,
            "status": "completed",
            "conclusion": "success",
            "started_at": "2026-10-19T16:59:01Z",
            "completed_at": "2026-10-19T16:59:02Z",
        },
        {
            "name": "Download the ODEPA files",
            "number": 7,
            "status": "completed",
            "conclusion": "failure",
            "started_at": "2026-10-19T16:59:34Z",
            "completed_at": "2026-10-19T16:59:46Z",
        },
        {
            "name": "Run the ETL (SQLite backup)",
            "number": 8,
            "status": "completed",
            "conclusion": "skipped",
            "started_at": None,
            "completed_at": None,
        },
    ],
}


def test_d165_the_run_is_nine_steps_on_a_serpentine_of_three_rows():
    keys = [step["key"] for step in operation_center.STEPS]
    assert keys == ["launch", "odepa", "ine", "etl", "dbt", "tests", "save", "report", "panel"]
    places = [step["place"] for step in operation_center.STEPS]
    # Rows one and three run left to right, the middle one right to left.
    assert places == [(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (0, 1), (0, 2), (1, 2), (2, 2)]
    assert all(step["key"] in operation_center.LOGOS and step["hint"] for step in operation_center.STEPS)


def test_d165_each_step_links_to_its_own_log_line_in_github():
    details = control.describe_job_steps(JOB)
    assert details["Download the ODEPA files"] == {
        "state": control.RUN_FAILED,
        "seconds": 12.0,
        "url": "https://github.com/x/y/actions/runs/7/job/70#step:7:1",
    }
    assert details["Run the ETL (SQLite backup)"]["state"] == "skipped"
    assert details["Run the ETL (SQLite backup)"]["seconds"] is None


def test_d165_renamed_workflow_steps_have_their_spanish_names():
    assert control.STEP_NAMES["Run the ETL (SQLite backup)"] == control.STEP_NAMES["Run the ETL"]
    assert control.STEP_NAMES["Build the data warehouse with dbt"] == "Data warehouse con dbt"


def test_d165_a_failed_step_is_red_pinned_and_the_rest_did_not_run():
    states = operation_center.build_step_states(RUN, control.describe_job_steps(JOB), True)
    assert states["launch"] == (operation_center.STATE_OK, "Manual", RUN["url"])
    assert states["odepa"][0] == operation_center.STATE_FAILED
    assert states["odepa"][2].endswith("#step:7:1")
    assert states["etl"][0] == operation_center.STATE_SKIPPED
    # No dbt step in this job: its logo and the IPC's say so instead of guessing.
    assert states["dbt"][0] == states["ine"][0] == operation_center.STATE_UNKNOWN
    assert operation_center.pick_pinned_step(states) == "odepa"


def test_d165_while_a_run_is_in_progress_later_steps_wait():
    run = dict(RUN, state=control.RUN_IN_PROGRESS)
    details = {
        "Download the ODEPA files": {"state": control.RUN_OK, "seconds": 10, "url": "a"},
        "Build the data warehouse with dbt": {"state": control.RUN_IN_PROGRESS, "seconds": None, "url": "b"},
        "Run the tests against the new database": {"state": "queued", "seconds": None, "url": "c"},
    }
    states = operation_center.build_step_states(run, details, True)
    assert states["odepa"] == (operation_center.STATE_OK, "10 s", "a")
    assert states["dbt"][0] == states["ine"][0] == operation_center.STATE_RUNNING
    assert states["tests"][0] == operation_center.STATE_WAITING
    assert states["panel"][0] == operation_center.STATE_RUNNING
    assert operation_center.pick_pinned_step(states) == "ine"


def test_d165_old_runs_read_the_etl_step_under_its_former_name():
    details = {"Run the ETL": {"state": control.RUN_OK, "seconds": 61, "url": "u"}}
    states = operation_center.build_step_states(dict(RUN, state=control.RUN_OK), details, True)
    assert states["etl"] == (operation_center.STATE_OK, "1 min 01 s", "u")


def test_d165_private_addresses_show_only_after_the_control_code():
    states = operation_center.build_step_states(RUN, control.describe_job_steps(JOB), True)
    palette = charts.get_palette(charts.MODE_CORPORATE)
    public = operation_center.build_stage_html(palette, states)
    private = operation_center.build_stage_html(palette, states, unlocked=True)
    # The same rule as the administration links (T-54): only after the control code.
    for address in (project.TOKENS_URL, project.STREAMLIT_ADMIN_URL, project.WORKFLOW_PAGE_URL):
        assert address not in public and address in private
    assert project.WHOLESALE_SOURCE_URL in public
    assert 'href="https://github.com/x/y/actions/runs/7/job/70#step:7:1"' in public
    assert public.count('class="oc-node ') == 9
    assert 'class="oc-tip below pinned"' in public
    # Every address leaves the panel in a new tab.
    links = re.findall(r'<a [^>]*href="[^"]+"[^>]*>', private)
    assert links and all('target="_blank"' in link and 'rel="noopener noreferrer"' in link for link in links)


def test_d165_the_stage_follows_each_theme():
    states = operation_center.build_step_states(None, {}, True)
    for mode in charts.THEMES:
        palette = charts.get_palette(mode)
        markup = operation_center.build_stage_html(palette, states)
        assert palette["strong_text"] in markup and palette["card"] in markup


def test_d166_phones_upright_are_asked_to_turn_and_sideways_get_the_computer_layout():
    markup = dashboard.PHONE_LAYOUT_HTML
    assert "@media (max-width:600px) and (orientation:portrait)" in markup
    assert "Gira tu teléfono" in markup and 'class="go-rotate"' in markup
    assert "@media (orientation:landscape) and (max-height:500px)" in markup
    assert "transform:scale(.62)" in markup and "161.3vw" in markup
    # st.html strips SVG gradients: the phone is drawn with plain boxes.
    assert "<svg" not in markup
    assert 'matchMedia("(orientation: landscape) and (max-height: 500px)")' in dashboard.FOLD_SIDEBAR_SCRIPT


def test_d165_the_page_draws_the_stage_beside_the_facts_and_the_manual_run():
    if not queries.DATABASE_FILE.exists():
        return
    script = (
        f"import sys\nsys.path.insert(0, {str(PROJECT_DIR)!r})\n"
        "from bi import control, dashboard\n"
        "control.list_workflow_runs = lambda *args, **kwargs: []\n"
        "import streamlit as st\nst.session_state['runs_view'] = 'Operación'\n"  # D-360: only the chosen tab is drawn
        "dashboard.render_page(dashboard.PAGE_RUNS)\n"
    )
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception and app.get("iframe")
    text = " ".join(block.value for block in app.markdown)
    assert "Centro de operación" in text and "Próxima ejecución" in text
    assert "Datos publicados" in text and "Última carga" in text
    # D-202: the manual run waits behind «Acceso del autor».
    assert "runs_run_now" not in [button.key for button in app.button] and app.get("popover")


def test_d271_the_path_shrinks_with_its_stage_and_never_grows_past_its_size():
    from bi import charts

    css = operation_center.build_css(charts.get_palette(charts.MODE_DARK))
    assert "container-type:inline-size" in css
    assert "width:min(76px, calc(76 * var(--u)))" in css and "width:min(132px, calc(132 * var(--u)))" in css


def test_d366_the_states_a_run_in_progress_shows_have_their_english(monkeypatch):
    """The weekly load ran while its own run was in progress: «En curso…» and «Esperando la base» reached the English
    screen untranslated. Every state word of the operation path has its English."""
    from bi import i18n, operation_center

    monkeypatch.setattr(i18n, "is_english", lambda: True)
    words = list(operation_center.STATE_TEXTS.values())
    for text in words + ["Esperando la base", "Base al día", "Última carga falló", "En curso…"]:
        assert i18n.translate_any(text) != text, text
