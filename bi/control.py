"""Control of the weekly pipeline from the dashboard, through the GitHub Actions API.

The pipeline runs as the workflow .github/workflows/semanal.yml. Reading its runs needs
no key because the repository is public; starting a run needs a token with
permission to run workflows, kept in the dashboard secrets, never in the code.
"""

from __future__ import annotations

from typing import Any, cast

from datetime import datetime, timedelta, timezone

import hmac

import requests

from bi.i18n import tr

# region Constants
REPOSITORY = "ben-carter-data/greenocean"
WORKFLOW_FILE = "semanal.yml"
BRANCH = "main"
API_URL = "https://api.github.com"
REQUEST_TIMEOUT_SECONDS = 10
# GitHub states when the token of a request expires in this answer header.
TOKEN_EXPIRATION_HEADER = "GitHub-Authentication-Token-Expiration"
TOKEN_WARNING_DAYS = 14

# Schedule of semanal.yml: Tuesdays at 12:00 UTC.
SCHEDULE_WEEKDAY = 1  # Monday is 0
SCHEDULE_HOUR_UTC = 12

RUN_OK = "ok"
RUN_FAILED = "failed"
RUN_IN_PROGRESS = "in_progress"
# A failure asked for on purpose with the «simulate failure» option (T-23).
RUN_SIMULATED_FAILURE = "simulated_failure"
TRIGGER_NAMES = {"schedule": "Automática", "workflow_dispatch": "Manual"}
SIMULATED_FAILURE_STEP = "Simulate a failure"
# Workflow steps the reader cares about, in Spanish. Setup steps are left out.
STEP_NAMES = {
    "Restore the closed-year files": "Archivos de años cerrados (caché)",
    "Get the published database": "Base publicada la semana anterior",
    "Download the ODEPA files": "Descarga de ODEPA",
    "Run the ETL": "Limpieza y reglas de negocio",
    # D-154 renamed the ETL step and added dbt; the old name stays for older runs.
    "Run the ETL (SQLite backup)": "Limpieza y reglas de negocio",
    "Build the data warehouse with dbt": "Data warehouse con dbt",
    "Simulate a failure": "Falla simulada",
    "Run the tests against the new database": "Pruebas automáticas",
    "Publish the database": "Publicar la base",
    # D-270 replaced the commit of the database by the release; the old name stays for older runs.
    "Save the updated database": "Guardar la base actualizada",
    "Publish the weekly report": "Publicar el informe semanal",
}
# endregion


# region Schedule and status
def calculate_next_scheduled_run(now_utc: datetime) -> datetime:
    """Next Tuesday 12:00 UTC strictly after now_utc (a timezone-aware datetime)."""
    days_ahead = (SCHEDULE_WEEKDAY - now_utc.weekday()) % 7
    candidate = (now_utc + timedelta(days=days_ahead)).replace(
        hour=SCHEDULE_HOUR_UTC, minute=0, second=0, microsecond=0
    )
    if candidate <= now_utc:
        candidate += timedelta(days=7)
    return candidate


def classify_run(status: str, conclusion: str | None) -> str:
    """Turn GitHub's status and conclusion into ok, failed or in progress."""
    if status != "completed":
        return RUN_IN_PROGRESS
    return RUN_OK if conclusion == "success" else RUN_FAILED


def parse_github_time(text: str | None) -> datetime | None:
    """'2026-10-12T08:52:08Z' -> timezone-aware datetime, or None."""
    if not text:
        return None
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def simplify_run(run: dict[str, Any]) -> dict[str, Any]:
    """Keep only what the dashboard shows from one GitHub run."""
    started_at = parse_github_time(run.get("run_started_at") or run.get("created_at"))
    finished_at = parse_github_time(run.get("updated_at"))
    state = classify_run(run["status"], run.get("conclusion"))
    duration = cast(datetime, finished_at) - cast(datetime, started_at) if state != RUN_IN_PROGRESS else None
    return {
        "id": run["id"],
        "state": state,
        "started_at": started_at,
        "duration": duration,
        "url": run["html_url"],
        "trigger": TRIGGER_NAMES.get(run["event"], run["event"]),
    }


def simplify_steps(job: dict[str, Any]) -> list[tuple[str, str]]:
    """Steps of one job as (Spanish name, state), only the ones the reader cares about."""
    steps = []
    for step in job.get("steps", []):
        # The failure test step only matters when someone asked for it.
        is_unused_failure_test = step["name"] == SIMULATED_FAILURE_STEP and step.get("conclusion") == "skipped"
        if step["name"] in STEP_NAMES and not is_unused_failure_test:
            state = classify_run(step["status"], step.get("conclusion"))
            if step.get("conclusion") == "skipped":
                state = "skipped"
            steps.append((STEP_NAMES[step["name"]], state))
    return steps


# endregion


# region GitHub API
def build_headers(token: str | None = None) -> dict[str, str]:
    """Headers of every request; the token is only sent when there is one."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def list_workflow_runs(token: str | None = None, count: int = 10) -> list[dict[str, Any]]:
    """Latest runs of the weekly workflow, newest first."""
    response = requests.get(
        f"{API_URL}/repos/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE}/runs",
        headers=build_headers(token),
        params={"per_page": count},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return [simplify_run(run) for run in response.json()["workflow_runs"]]


def start_workflow_run(token: str) -> None:
    """Ask GitHub to start the workflow now. Raises an exception if GitHub refuses."""
    response = requests.post(
        f"{API_URL}/repos/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE}/dispatches",
        headers=build_headers(token),
        json={"ref": BRANCH, "inputs": {"simulate_failure": False}},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def cancel_workflow_run(run_id: int, token: str) -> None:
    """Ask GitHub to cancel a run (D-351). A write: it uses the same token that starts the workflow. Raises if refused."""
    response = requests.post(
        f"{API_URL}/repos/{REPOSITORY}/actions/runs/{run_id}/cancel",
        headers=build_headers(token),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def describe_cancel_error(error: Exception) -> str:
    """Why GitHub did not cancel the run, in the reader's language. Only the HTTP code, never the token."""
    code = getattr(getattr(error, "response", None), "status_code", None)
    if code == 403:
        return tr(
            "El token no tiene permiso para cancelar. Necesita «Actions: Read and write» sobre este repositorio; "
            "la ejecución sigue como estaba."
        )
    if code == 409:
        return tr("La ejecución ya había terminado; no hay nada que cancelar.")
    return tr("No se pudo cancelar: {}. La ejecución sigue como estaba.").format(describe_github_error(error))


def list_run_steps(run_id: int, token: str | None = None) -> list[tuple[str, str]]:
    """Steps of a run with their state, to follow its progress."""
    response = requests.get(
        f"{API_URL}/repos/{REPOSITORY}/actions/runs/{run_id}/jobs",
        headers=build_headers(token),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    jobs = response.json()["jobs"]
    return simplify_steps(jobs[0]) if jobs else []


def describe_job_steps(job: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """{workflow step name: state, seconds and the address of its own log} (D-165).

    GitHub opens a job's log on one step with #step:<number>:1, unfolded."""
    details = {}
    for step in job.get("steps", []):
        state = classify_run(step["status"], step.get("conclusion"))
        if step.get("conclusion") == "skipped":
            state = "skipped"
        started_at = parse_github_time(step.get("started_at"))
        finished_at = parse_github_time(step.get("completed_at"))
        seconds = (
            (finished_at - started_at).total_seconds() if started_at and finished_at and state != "skipped" else None
        )
        details[step["name"]] = {
            "state": state,
            "seconds": seconds,
            "url": f"{job['html_url']}#step:{step['number']}:1",
        }
    return details


def list_run_step_details(run_id: int, token: str | None = None) -> dict[str, dict[str, Any]]:
    """Every step of a run with its state, duration and log address; {} without a job."""
    response = requests.get(
        f"{API_URL}/repos/{REPOSITORY}/actions/runs/{run_id}/jobs",
        headers=build_headers(token),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    jobs = response.json()["jobs"]
    return describe_job_steps(jobs[0]) if jobs else {}


def is_simulated_failure(steps: list[tuple[str, str]]) -> bool:
    """True when the run failed only because the failure test step was asked for."""
    return (STEP_NAMES[SIMULATED_FAILURE_STEP], RUN_FAILED) in steps


def mark_simulated_failures(runs: list[dict[str, Any]], token: str | None = None) -> list[dict[str, Any]]:
    """Mark the failed runs whose failure was a requested test, so nobody worries.

    Only failed runs are asked for their steps: they are few.
    """
    for run in runs:
        if run["state"] == RUN_FAILED and is_simulated_failure(list_run_steps(run["id"], token)):
            run["state"] = RUN_SIMULATED_FAILURE
    return runs


def latest_load_failure(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The newest finished run when it failed for real (not a requested test), else None (D-298): a run in progress
    does not hide the result of the one before it."""
    finished = [run for run in runs if run["state"] != RUN_IN_PROGRESS]
    return finished[0] if finished and finished[0]["state"] == RUN_FAILED else None


def parse_token_expiration(text: str | None) -> datetime | None:
    """'2026-12-31 12:00:00 UTC' (or with a -0300 offset) -> aware datetime, or None."""
    if not text:
        return None
    for pattern in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S %z"):
        try:
            moment = datetime.strptime(text.strip(), pattern)
        except ValueError:
            continue
        return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
    return None


def read_token_expiration(token: str) -> datetime | None:
    """When the token expires, from GitHub's answer header; None if it never does.

    /rate_limit does not count against the hourly limit. Only the date leaves
    this function: never the token, the headers or the answer.
    """
    response = requests.get(f"{API_URL}/rate_limit", headers=build_headers(token), timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return parse_token_expiration(response.headers.get(TOKEN_EXPIRATION_HEADER))


def describe_token_expiration(expiration: datetime | None, now: datetime) -> tuple[str, bool]:
    """(sentence, is_urgent) about the token: «Tu token vence en X días»."""
    if expiration is None:
        return "Tu token no tiene fecha de vencimiento.", False
    days = (expiration - now).days
    if days < 0:
        return "Tu token venció: crea uno nuevo y cámbialo en los secretos del panel.", True
    return (f"Tu token vence en {days} días ({expiration:%d-%m-%Y}).", days < TOKEN_WARNING_DAYS)


def describe_github_error(error: Exception, now: datetime | None = None) -> str:
    """Why GitHub did not answer, in plain Spanish, with its HTTP code when there is one.

    Only the code, the reason and the reset time of the request limit are used:
    never the token, the headers or the address with its parameters.
    """
    if isinstance(error, requests.Timeout):
        return tr("GitHub no respondió en {} s").format(REQUEST_TIMEOUT_SECONDS)
    if isinstance(error, requests.ConnectionError):
        return tr("no hubo conexión con GitHub")
    response = getattr(error, "response", None)
    if response is None:
        # Not a GitHub answer: a bug or an unexpected payload. Its class names it.
        return tr("error inesperado al consultar GitHub ({})").format(type(error).__name__)
    code = response.status_code
    if code in (403, 429) and response.headers.get("X-RateLimit-Remaining") == "0":
        limit = response.headers.get("X-RateLimit-Limit")
        reason = (
            tr("se agotó el límite de consultas sin clave (60 por hora)")
            if limit == "60"
            else tr("se agotó el límite de consultas")
        )
        try:
            reset = datetime.fromtimestamp(int(response.headers["X-RateLimit-Reset"]), timezone.utc)
            minutes = max(0, round((reset - (now or datetime.now(timezone.utc))).total_seconds() / 60))
        except (KeyError, ValueError, OverflowError, OSError):
            return tr("GitHub respondió {}: {}").format(code, reason)
        return tr("GitHub respondió {}: {}; se renueva en {} min").format(code, reason, minutes)
    reasons = {
        401: "la clave no es válida o venció",
        403: "acceso denegado",
        404: "no se encontró el workflow",
        500: "error interno de GitHub",
        502: "GitHub no está disponible",
        503: "GitHub no está disponible",
    }
    return tr("GitHub respondió {}: {}").format(code, tr(reasons.get(code, "error al consultar GitHub")))


def find_run_started_after(runs: list[dict[str, Any]], requested_at: datetime) -> dict[str, Any] | None:
    """The manual run created after the click, or None while GitHub has not listed it."""
    for run in runs:
        is_manual = run["trigger"] == TRIGGER_NAMES["workflow_dispatch"]
        # GitHub may record the start a few seconds before the request returns.
        if is_manual and run["started_at"] >= requested_at - timedelta(seconds=30):
            return run
    return None


# endregion


# The control code (D-199, D-249): compared in constant time and as bytes, so any character works. There is no
# limit of attempts: the code only keeps a visitor from launching the workflow by accident (the decision of the
# author), and the most the button can do is start the weekly workflow.
def check_control_code(typed: str | None, expected: str | None) -> tuple[bool, str]:
    """(ok, message in Spanish)."""
    if expected and hmac.compare_digest((typed or "").encode("utf-8"), str(expected).encode("utf-8")):
        return True, ""
    return False, "Clave incorrecta."
