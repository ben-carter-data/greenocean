"""Control of the weekly pipeline from the dashboard, through the GitHub Actions API.

The pipeline runs as the workflow .github/workflows/semanal.yml. Reading its runs needs
no key because the repository is public; starting a run needs a token with
permission to run workflows, kept in the dashboard secrets, never in the code.
"""
from datetime import datetime, timedelta, timezone

import requests

# region Constants
REPOSITORY = "cben6514-boop/monitor-precios-hito1"
WORKFLOW_FILE = "semanal.yml"
BRANCH = "main"
API_URL = "https://api.github.com"
WORKFLOW_PAGE_URL = f"https://github.com/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE}"
REQUEST_TIMEOUT_SECONDS = 10

# Schedule of semanal.yml: Tuesdays at 12:00 UTC.
SCHEDULE_WEEKDAY = 1  # Monday is 0
SCHEDULE_HOUR_UTC = 12

RUN_OK = "ok"
RUN_FAILED = "failed"
RUN_IN_PROGRESS = "in_progress"
TRIGGER_NAMES = {"schedule": "Automática", "workflow_dispatch": "Manual"}
SIMULATED_FAILURE_STEP = "Simulate a failure"
# Workflow steps the reader cares about, in Spanish. Setup steps are left out.
STEP_NAMES = {
    "Restore the closed-year files": "Archivos de años cerrados (caché)",
    "Download the ODEPA files": "Descarga de ODEPA",
    "Run the ETL": "Limpieza y reglas de negocio",
    "Simulate a failure": "Falla simulada",
    "Run the tests against the new database": "Pruebas automáticas",
    "Save the updated database": "Guardar la base actualizada",
    "Publish the weekly report": "Publicar el informe semanal",
}
# endregion


# region Schedule and status
def calculate_next_scheduled_run(now_utc):
    """Next Tuesday 12:00 UTC strictly after now_utc (a timezone-aware datetime)."""
    days_ahead = (SCHEDULE_WEEKDAY - now_utc.weekday()) % 7
    candidate = (now_utc + timedelta(days=days_ahead)).replace(
        hour=SCHEDULE_HOUR_UTC, minute=0, second=0, microsecond=0)
    if candidate <= now_utc:
        candidate += timedelta(days=7)
    return candidate


def classify_run(status, conclusion):
    """Turn GitHub's status and conclusion into ok, failed or in progress."""
    if status != "completed":
        return RUN_IN_PROGRESS
    return RUN_OK if conclusion == "success" else RUN_FAILED


def parse_github_time(text):
    """'2026-10-12T08:52:08Z' -> timezone-aware datetime, or None."""
    if not text:
        return None
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def simplify_run(run):
    """Keep only what the dashboard shows from one GitHub run."""
    started_at = parse_github_time(run.get("run_started_at") or run.get("created_at"))
    finished_at = parse_github_time(run.get("updated_at"))
    state = classify_run(run["status"], run.get("conclusion"))
    duration = finished_at - started_at if state != RUN_IN_PROGRESS else None
    return {"id": run["id"], "state": state, "started_at": started_at,
            "duration": duration, "url": run["html_url"],
            "trigger": TRIGGER_NAMES.get(run["event"], run["event"])}


def simplify_steps(job):
    """Steps of one job as (Spanish name, state), only the ones the reader cares about."""
    steps = []
    for step in job.get("steps", []):
        # The failure test step only matters when someone asked for it.
        is_unused_failure_test = (step["name"] == SIMULATED_FAILURE_STEP
                                  and step.get("conclusion") == "skipped")
        if step["name"] in STEP_NAMES and not is_unused_failure_test:
            state = classify_run(step["status"], step.get("conclusion"))
            if step.get("conclusion") == "skipped":
                state = "skipped"
            steps.append((STEP_NAMES[step["name"]], state))
    return steps
# endregion


# region GitHub API
def build_headers(token=None):
    """Headers of every request; the token is only sent when there is one."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def list_workflow_runs(token=None, count=10):
    """Latest runs of the weekly workflow, newest first."""
    response = requests.get(
        f"{API_URL}/repos/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE}/runs",
        headers=build_headers(token), params={"per_page": count},
        timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return [simplify_run(run) for run in response.json()["workflow_runs"]]


def start_workflow_run(token):
    """Ask GitHub to start the workflow now. Raises an exception if GitHub refuses."""
    response = requests.post(
        f"{API_URL}/repos/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE}/dispatches",
        headers=build_headers(token),
        json={"ref": BRANCH, "inputs": {"simulate_failure": False}},
        timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()


def list_run_steps(run_id, token=None):
    """Steps of a run with their state, to follow its progress."""
    response = requests.get(f"{API_URL}/repos/{REPOSITORY}/actions/runs/{run_id}/jobs",
                            headers=build_headers(token), timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    jobs = response.json()["jobs"]
    return simplify_steps(jobs[0]) if jobs else []


def find_run_started_after(runs, requested_at):
    """The manual run created after the click, or None while GitHub has not listed it."""
    for run in runs:
        is_manual = run["trigger"] == TRIGGER_NAMES["workflow_dispatch"]
        # GitHub may record the start a few seconds before the request returns.
        if is_manual and run["started_at"] >= requested_at - timedelta(seconds=30):
            return run
    return None
# endregion
