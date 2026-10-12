"""Tests for the pipeline control: schedule, run states and GitHub answers (faked)."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import control  # noqa: E402

GITHUB_RUN = {"id": 38226180308, "status": "completed", "conclusion": "success",
              "event": "workflow_dispatch", "run_started_at": "2026-10-12T08:51:00Z",
              "updated_at": "2026-10-12T08:51:57Z",
              "html_url": "https://github.com/x/y/actions/runs/38226180308"}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_next_run_is_the_coming_tuesday_at_noon_utc():
    monday = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)
    assert control.calculate_next_scheduled_run(monday) == datetime(
        2026, 10, 13, 12, 0, tzinfo=timezone.utc)


def test_next_run_after_tuesday_noon_is_the_following_week():
    tuesday_afternoon = datetime(2026, 10, 13, 12, 30, tzinfo=timezone.utc)
    assert control.calculate_next_scheduled_run(tuesday_afternoon) == datetime(
        2026, 10, 20, 12, 0, tzinfo=timezone.utc)


def test_run_states_are_ok_failed_or_in_progress():
    assert control.classify_run("completed", "success") == control.RUN_OK
    assert control.classify_run("completed", "failure") == control.RUN_FAILED
    assert control.classify_run("in_progress", None) == control.RUN_IN_PROGRESS


def test_a_github_run_is_simplified_for_the_dashboard():
    run = control.simplify_run(GITHUB_RUN)
    assert run["state"] == control.RUN_OK
    assert run["trigger"] == "Manual"
    assert run["duration"] == timedelta(seconds=57)


def test_runs_are_read_from_the_github_api(monkeypatch):
    def fake_get(url, **arguments):
        assert url.endswith("/actions/workflows/semanal.yml/runs")
        return FakeResponse({"workflow_runs": [GITHUB_RUN]})
    monkeypatch.setattr(control.requests, "get", fake_get)
    assert [run["id"] for run in control.list_workflow_runs()] == [38226180308]


def test_only_known_steps_are_shown_in_spanish():
    job = {"steps": [
        {"name": "Set up job", "status": "completed", "conclusion": "success"},
        {"name": "Download the ODEPA files", "status": "completed", "conclusion": "success"},
        {"name": "Run the ETL", "status": "in_progress", "conclusion": None},
        {"name": "Simulate a failure", "status": "completed", "conclusion": "skipped"},
        {"name": "Save the updated database", "status": "completed",
         "conclusion": "skipped"}]}
    # Step names copied from a real run of semanal.yml (12-10-2026).
    assert control.simplify_steps(job) == [
        ("Descarga de ODEPA", control.RUN_OK),
        ("Limpieza y reglas de negocio", control.RUN_IN_PROGRESS),
        ("Guardar la base actualizada", "skipped")]


def test_the_manual_run_started_after_the_click_is_found():
    clicked_at = datetime(2026, 10, 12, 8, 50, 50, tzinfo=timezone.utc)
    older_run = control.simplify_run({**GITHUB_RUN, "id": 1,
                                      "run_started_at": "2026-10-11T08:00:00Z"})
    new_run = control.simplify_run(GITHUB_RUN)
    assert control.find_run_started_after([new_run, older_run], clicked_at) == new_run
    assert control.find_run_started_after([older_run], clicked_at) is None


def test_the_token_is_only_sent_when_there_is_one():
    assert "Authorization" not in control.build_headers()
    assert control.build_headers("abc")["Authorization"] == "Bearer abc"


def test_failure_asked_for_on_purpose_is_marked_as_simulated(monkeypatch):
    simulated_steps = [("Limpieza y reglas de negocio", control.RUN_OK),
                       ("Falla simulada", control.RUN_FAILED)]
    real_failure_steps = [("Limpieza y reglas de negocio", control.RUN_FAILED)]
    assert control.is_simulated_failure(simulated_steps)
    assert not control.is_simulated_failure(real_failure_steps)
    steps_by_run = {1: simulated_steps, 2: real_failure_steps}
    monkeypatch.setattr(control, "list_run_steps",
                        lambda run_id, token=None: steps_by_run[run_id])
    runs = [{"id": 1, "state": control.RUN_FAILED}, {"id": 2, "state": control.RUN_FAILED},
            {"id": 3, "state": control.RUN_OK}]
    states = [run["state"] for run in control.mark_simulated_failures(runs)]
    assert states == [control.RUN_SIMULATED_FAILURE, control.RUN_FAILED, control.RUN_OK]
