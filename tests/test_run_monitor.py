"""The manual run followed from the panel (D-351): live log, time limit, cancellation, indicator and copy."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from streamlit.testing.v1 import AppTest

from bi import control, run_monitor

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = str(ROOT / "bi" / "dashboard.py")
TOKEN = "github_pat_" + "FAKE0123456789ABCDEFGHIJKLMNOP"
NOW = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)


def running_data():
    step = {"name": "Run the ETL", "status": "in_progress", "conclusion": None, "started_at": "2026-10-30T12:00:00Z"}
    job = {"id": 70, "name": "weekly-load", "status": "in_progress", "conclusion": None, "steps": [step]}
    return {"status": "in_progress", "conclusion": None, "url": "https://github.com/x/y/actions/runs/7", "jobs": [job]}


def test_d351_the_window_stops_asking_after_the_workflow_timeout_and_points_to_github(monkeypatch):
    monkeypatch.setattr(run_monitor, "find_run", lambda token, requested_at: {"id": 7, "url": "https://x/runs/7"})
    monkeypatch.setattr(run_monitor, "fetch_run", lambda run_id, token: running_data())
    watch = run_monitor.new_watch(NOW)
    run_monitor.refresh(watch, TOKEN, NOW + timedelta(minutes=5))
    assert watch["phase"] == run_monitor.RUNNING and run_monitor.indicator(watch).endswith(
        "Limpieza y reglas de negocio"
    )
    run_monitor.refresh(watch, TOKEN, NOW + timedelta(minutes=run_monitor.MAX_MINUTES, seconds=1))
    assert watch["phase"] == run_monitor.TIMEOUT and run_monitor.indicator(watch) == "Sigue en GitHub"
    asked = []
    monkeypatch.setattr(run_monitor, "fetch_run", lambda run_id, token: asked.append(run_id))
    run_monitor.refresh(watch, TOKEN, NOW + timedelta(minutes=30))
    assert not asked  # once final it asks nothing more
    workflow = (ROOT / ".github" / "workflows" / "semanal.yml").read_text(encoding="utf-8")
    assert f"timeout-minutes: {run_monitor.MAX_MINUTES}" in workflow  # GitHub cuts it at the same minute


def test_d351_a_run_github_never_shows_is_reported_and_a_failed_question_is_kept_not_raised(monkeypatch):
    monkeypatch.setattr(run_monitor, "find_run", lambda token, requested_at: None)
    watch = run_monitor.new_watch(NOW)
    run_monitor.refresh(watch, TOKEN, NOW + timedelta(seconds=30))
    assert watch["phase"] == run_monitor.STARTING
    run_monitor.refresh(watch, TOKEN, NOW + timedelta(seconds=run_monitor.CONFIRM_SECONDS + 1))
    assert watch["phase"] == run_monitor.UNCONFIRMED
    import requests

    def broken(token, requested_at):
        raise requests.ConnectionError(TOKEN)

    monkeypatch.setattr(run_monitor, "find_run", broken)
    again = run_monitor.new_watch(NOW)
    run_monitor.refresh(again, TOKEN, NOW)
    assert again["error"] and TOKEN not in again["error"] and again["phase"] == run_monitor.STARTING


def test_d351_the_log_and_the_copy_button_never_carry_the_token():
    watch = run_monitor.new_watch(NOW)
    watch["steps"] = [
        {"job": "j", "name": "Run the ETL", "state": "ok", "started": NOW, "seconds": 65.0},
        {"job": "j", "name": "Publish the database", "state": "in_progress", "started": NOW, "seconds": None},
    ]
    watch["jobs"] = {70: "weekly-load"}
    watch["tails"] = {70: ["token is " + TOKEN, "Authorization: Bearer " + TOKEN]}
    log = run_monitor.build_log(watch)
    assert "Limpieza y reglas de negocio (65 s)" in log and "Publicar la base (—)" in log
    assert TOKEN not in log and "FAKE0123456789" not in log
    page = run_monitor.build_copy_html(log, "Copiar", "Copiado", "Seleccionado")
    assert "clipboard.writeText" in page and TOKEN not in page and "Copiar" in page


def test_d351_cancelling_is_the_only_write_and_the_read_only_module_still_has_none():
    source = (ROOT / "bi" / "github_actions.py").read_text(encoding="utf-8")
    assert "requests.post" not in source and source.count("requests.get(") == 1
    assert "actions/runs/{run_id}/cancel" in (ROOT / "bi" / "control.py").read_text(encoding="utf-8")
    monitor = (ROOT / "bi" / "run_monitor.py").read_text(encoding="utf-8")
    assert (
        "requests.post" not in monitor and "requests.get" not in monitor
    )  # it goes through control and github_actions
    assert "no tiene permiso para cancelar" in control.describe_cancel_error(_http(403))
    assert "ya había terminado" in control.describe_cancel_error(_http(409))


def _http(code):
    import requests

    response = requests.Response()
    response.status_code = code
    return requests.HTTPError(response=response)


def test_d351_a_minimized_run_shows_an_indicator_that_reopens_the_window():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.session_state["visitor_profile"] = "profesional"
    app.session_state["admin_unlocked"] = True
    app.session_state["quality_alert_seen"] = True
    watch = run_monitor.new_watch(NOW)
    watch.update(phase=run_monitor.RUNNING, run_id=7, url="https://x/runs/7", minimized=True)
    watch["steps"] = [{"job": "j", "name": "Run the ETL", "state": "in_progress", "started": NOW, "seconds": None}]
    app.session_state["run_watch"] = watch
    app.run()
    assert not app.exception
    indicator = [button for button in app.sidebar.button if button.key == "run_indicator"]
    assert indicator and indicator[0].label == "Ejecución en curso · Limpieza y reglas de negocio"
    indicator[0].click().run()
    assert app.session_state["run_watch"]["minimized"] is False and app.get("dialog")
    visitor = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    visitor.session_state["visitor_profile"] = "profesional"
    visitor.session_state["run_watch"] = watch | {"minimized": True}
    visitor.run()
    assert not [button for button in visitor.sidebar.button if button.key == "run_indicator"]  # only the author's


def failing_job_log():
    lines = ["##[group]Run actions/checkout@v4", "checking out", "##[endgroup]"]
    lines += ['##[group]Run pytest -q -m "datos and not rendimiento"', "##[endgroup]"]
    lines += ["FAILED tests/test_a.py::test_one - AssertionError", "FAILED tests/test_b.py::test_two - AssertionError"]
    lines += [f"        True,  # diff line {n}" for n in range(80)]
    lines += ["2 failed, 1115 passed in 245.83s", "##[error]Process completed with exit code 1."]
    lines += ["Post job cleanup.", "[command]/usr/bin/git version", "Cleaning up orphan processes"]
    return "\n".join(f"2026-10-30T23:00:00.0000000Z {line}" for line in lines)


def test_d367_a_failed_job_shows_the_log_of_its_failed_step_with_the_failing_tests_first(monkeypatch):
    monkeypatch.setattr(run_monitor.github_actions, "job_log", lambda job_id, token: failing_job_log())
    tail = run_monitor.read_tail({"id": 1, "conclusion": "failure"}, TOKEN)
    assert tail[0] == '##[group]Run pytest -q -m "datos and not rendimiento"'  # the step, named by its command
    assert tail[1].startswith("FAILED tests/test_a.py::test_one") and tail[2].startswith("FAILED tests/test_b.py")
    assert tail[-1].endswith("Process completed with exit code 1.") and "Post job cleanup." not in tail
    watch = run_monitor.new_watch(NOW)
    watch.update(jobs={1: "weekly-load"}, tails={1: tail})
    log = run_monitor.build_log(watch)
    assert "weekly-load · paso que falló: Run pytest" in log and "ERROR: Process completed" in log
    success = run_monitor.read_tail({"id": 1, "conclusion": "success"}, TOKEN)
    assert success[-1] == "Cleaning up orphan processes"  # a job that passed keeps its last lines
