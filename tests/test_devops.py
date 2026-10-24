"""The CI/CD diagram (D-243): every box is a step of a real workflow, and nothing else is drawn."""
import re
from pathlib import Path

import pytest

from bi import charts, devops, tech_glossary

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def read_workflow(name):
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def test_every_box_that_names_a_workflow_step_points_to_text_that_exists_in_that_workflow():
    for step in devops.STEPS:
        marker = step[10]
        if marker is None:
            continue  # Streamlit Cloud: a setting of the platform, drawn dashed, not in the repository
        workflow, _, text = marker.partition("::")
        assert text in read_workflow(workflow), (step[0], marker)


def test_the_two_workflows_and_their_triggers_are_the_ones_drawn():
    pruebas, semanal = read_workflow("pruebas.yml"), read_workflow("semanal.yml")
    assert "push:" in pruebas and "pull_request:" in pruebas
    assert re.search(r'cron:\s*"0 12 \* \* 2"', semanal) and "workflow_dispatch:" in semanal
    assert {path.name for path in WORKFLOWS.glob("*.yml")} == {"pruebas.yml", "semanal.yml"}  # no other workflow


def test_the_steps_of_the_weekly_load_come_in_the_order_of_the_workflow_and_none_is_missing():
    semanal = read_workflow("semanal.yml")
    drawn = [step[10].partition("::")[2] for step in devops.STEPS if step[1] == "cd" and step[0] != "cd_trigger"]
    positions = [semanal.index(text) for text in drawn]
    assert positions == sorted(positions)
    # D-246: every named step of the weekly job is drawn, numbered in its order.
    named = re.findall(r"- name: (.+)", semanal)
    assert named == drawn
    numbers = [int(step[6].split(" · ")[0]) for step in devops.STEPS if step[1] == "cd" and step[0] != "cd_trigger"]
    assert numbers == list(range(1, len(named) + 1))
    # The gates: dbt and the tests against the new database run before it is saved.
    gates = [step[0] for step in devops.STEPS if step[11] == "gate"]
    assert gates == ["ci_pytest", "cd_dbt", "cd_pytest"]
    assert semanal.index("Run the tests against") < semanal.index("Publish the database")


def test_each_step_says_on_which_line_of_its_workflow_it_is():
    for step in devops.STEPS:
        if step[10] is None:
            continue
        name, _, text = step[10].partition("::")
        line = devops.workflow_line(step[10])
        number = int(line.rsplit(" ", 1)[1])
        assert text in read_workflow(name).splitlines()[number - 1], step[0]


def test_the_panel_never_asks_for_the_simulated_failure():
    control = (Path(__file__).resolve().parent.parent / "bi" / "control.py").read_text(encoding="utf-8")
    assert '"simulate_failure": False' in control
    fail = next(step for step in devops.STEPS if step[0] == "cd_fail")
    assert fail[11] == "optional" and "nunca" in fail[8]


def test_the_definition_says_what_ci_and_cd_are():
    terms = dict(devops.DEFINITION)
    assert "CI · integración continua" in terms and "CD · entrega continua" in terms
    assert "prueba" in terms["CI · integración continua"] and "producción" in terms["CD · entrega continua"]
    for acronym, expansion in (("ci", "Continuous Integration"), ("cd", "Continuous Delivery")):
        assert expansion in tech_glossary.describe(acronym)


@pytest.mark.parametrize("mode", charts.THEMES)
def test_the_diagram_has_one_card_and_one_hover_per_step_with_real_logos_and_no_script(mode):
    page = devops.build_cicd_html(charts.get_palette(mode))
    assert page.count('class="step') == len(devops.STEPS)
    assert page.count('class="tip"') == len(devops.STEPS)
    for logo in ("git", "github", "pytest", "dbt", "streamlit"):
        assert f'id="disc-{logo}-' in page, logo
    assert "<script" not in page and "robot" not in page.lower()
    assert page.count("<b>Dónde está</b>") == len(devops.STEPS)
    assert devops.ROW_NOTE in page


def test_the_lines_join_each_step_with_the_next_in_its_lane_and_the_load_with_the_release():
    for start, end in devops.LINKS:
        assert {start, end} <= {step[0] for step in devops.STEPS}
    # D-270: the load publishes the database in the release, and the panel takes it from there.
    assert ("cd_publish", "pub_release") in devops.LINKS and ("pub_release", "pub_streamlit") in devops.LINKS
    page = devops.build_cicd_html(charts.get_palette(charts.MODE_DARK))
    for x1, y1, x2, y2 in re.findall(r'd="M(\S+) (\S+) L(\S+) (\S+)"', page):
        assert x1 == x2 or y1 == y2  # straight, horizontal or vertical
    assert page.count('class="line dashed"') == 3  # into and out of the optional failure, and the platform's setting
