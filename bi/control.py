"""Control of the weekly pipeline from the dashboard, through the GitHub Actions API.

The pipeline runs as the workflow .github/workflows/semanal.yml. Reading its runs needs
no key because the repository is public; starting a run needs a token with
permission to run workflows, kept in the dashboard secrets, never in the code.
"""
from datetime import datetime, timedelta, timezone

import hmac
import threading
import time

import requests

# region Constants
REPOSITORY = "cben6514-boop/monitor-precios-hito1"
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
    "Download the ODEPA files": "Descarga de ODEPA",
    "Run the ETL": "Limpieza y reglas de negocio",
    # D-154 renamed the ETL step and added dbt; the old name stays for older runs.
    "Run the ETL (SQLite backup)": "Limpieza y reglas de negocio",
    "Build the data warehouse with dbt": "Data warehouse con dbt",
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


def describe_job_steps(job):
    """{workflow step name: state, seconds and the address of its own log} (D-165).

    GitHub opens a job's log on one step with #step:<number>:1, unfolded."""
    details = {}
    for step in job.get("steps", []):
        state = classify_run(step["status"], step.get("conclusion"))
        if step.get("conclusion") == "skipped":
            state = "skipped"
        started_at = parse_github_time(step.get("started_at"))
        finished_at = parse_github_time(step.get("completed_at"))
        seconds = ((finished_at - started_at).total_seconds()
                   if started_at and finished_at and state != "skipped" else None)
        details[step["name"]] = {"state": state, "seconds": seconds,
                                 "url": f"{job['html_url']}#step:{step['number']}:1"}
    return details


def list_run_step_details(run_id, token=None):
    """Every step of a run with its state, duration and log address; {} without a job."""
    response = requests.get(f"{API_URL}/repos/{REPOSITORY}/actions/runs/{run_id}/jobs",
                            headers=build_headers(token), timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    jobs = response.json()["jobs"]
    return describe_job_steps(jobs[0]) if jobs else {}


def is_simulated_failure(steps):
    """True when the run failed only because the failure test step was asked for."""
    return (STEP_NAMES[SIMULATED_FAILURE_STEP], RUN_FAILED) in steps


def mark_simulated_failures(runs, token=None):
    """Mark the failed runs whose failure was a requested test, so nobody worries.

    Only failed runs are asked for their steps: they are few.
    """
    for run in runs:
        if run["state"] == RUN_FAILED and is_simulated_failure(list_run_steps(run["id"], token)):
            run["state"] = RUN_SIMULATED_FAILURE
    return runs


def parse_token_expiration(text):
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


def read_token_expiration(token):
    """When the token expires, from GitHub's answer header; None if it never does.

    /rate_limit does not count against the hourly limit. Only the date leaves
    this function: never the token, the headers or the answer.
    """
    response = requests.get(f"{API_URL}/rate_limit", headers=build_headers(token),
                            timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return parse_token_expiration(response.headers.get(TOKEN_EXPIRATION_HEADER))


def describe_token_expiration(expiration, now):
    """(sentence, is_urgent) about the token: «Tu token vence en X días»."""
    if expiration is None:
        return "Tu token no tiene fecha de vencimiento.", False
    days = (expiration - now).days
    if days < 0:
        return "Tu token venció: crea uno nuevo y cámbialo en los secretos del panel.", True
    return (f"Tu token vence en {days} días ({expiration:%d-%m-%Y}).",
            days < TOKEN_WARNING_DAYS)


def describe_github_error(error, now=None):
    """Why GitHub did not answer, in plain Spanish, with its HTTP code when there is one.

    Only the code, the reason and the reset time of the request limit are used:
    never the token, the headers or the address with its parameters.
    """
    if isinstance(error, requests.Timeout):
        return f"GitHub no respondió en {REQUEST_TIMEOUT_SECONDS} s"
    if isinstance(error, requests.ConnectionError):
        return "no hubo conexión con GitHub"
    response = getattr(error, "response", None)
    if response is None:
        # Not a GitHub answer: a bug or an unexpected payload. Its class names it.
        return f"error inesperado al consultar GitHub ({type(error).__name__})"
    code = response.status_code
    if code in (403, 429) and response.headers.get("X-RateLimit-Remaining") == "0":
        limit = response.headers.get("X-RateLimit-Limit")
        reason = ("se agotó el límite de consultas sin clave (60 por hora)"
                  if limit == "60" else "se agotó el límite de consultas")
        try:
            reset = datetime.fromtimestamp(int(response.headers["X-RateLimit-Reset"]),
                                           timezone.utc)
            minutes = max(0, round((reset - (now or datetime.now(timezone.utc)))
                                   .total_seconds() / 60))
        except (KeyError, ValueError, OverflowError, OSError):
            return f"GitHub respondió {code}: {reason}"
        return f"GitHub respondió {code}: {reason}; se renueva en {minutes} min"
    reasons = {401: "la clave no es válida o venció", 403: "acceso denegado",
               404: "no se encontró el workflow", 500: "error interno de GitHub",
               502: "GitHub no está disponible", 503: "GitHub no está disponible"}
    return f"GitHub respondió {code}: {reasons.get(code, 'error al consultar GitHub')}"


def find_run_started_after(runs, requested_at):
    """The manual run created after the click, or None while GitHub has not listed it."""
    for run in runs:
        is_manual = run["trigger"] == TRIGGER_NAMES["workflow_dispatch"]
        # GitHub may record the start a few seconds before the request returns.
        if is_manual and run["started_at"] >= requested_at - timedelta(seconds=30):
            return run
    return None
# endregion


# The control code (D-199): compared in constant time, as bytes so any character works, and
# guarded against guessing. The count is shared by every visitor, so opening new sessions
# does not reset it; while it is locked, the pipeline still runs from GitHub.
LOGIN_MAX_FAILURES = 5
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_LOCK_SECONDS = 15 * 60
LOGIN_FAILURE_DELAY_SECONDS = 1.0


class LoginGuard:
    """At most LOGIN_MAX_FAILURES wrong codes in LOGIN_WINDOW_SECONDS, then a lock."""

    def __init__(self, clock=time.time, sleep=time.sleep):
        self.clock, self.sleep = clock, sleep
        self.failures, self.locked_until = [], 0.0
        self.lock = threading.Lock()

    def seconds_locked(self):
        return max(0.0, self.locked_until - self.clock())

    def check(self, typed, expected):
        """(ok, message in Spanish). A locked guard refuses even the right code."""
        with self.lock:
            now = self.clock()
            if now < self.locked_until:
                minutes = int((self.locked_until - now) // 60) + 1
                return False, f"Demasiados intentos. Vuelve a intentarlo en {minutes} min."
            if expected and hmac.compare_digest((typed or "").encode("utf-8"), str(expected).encode("utf-8")):
                self.failures.clear()
                return True, ""
            self.failures = [moment for moment in self.failures if now - moment < LOGIN_WINDOW_SECONDS] + [now]
            if len(self.failures) >= LOGIN_MAX_FAILURES:
                self.locked_until, self.failures = now + LOGIN_LOCK_SECONDS, []
                return False, (f"Clave incorrecta. Demasiados intentos: el acceso queda bloqueado "
                               f"{LOGIN_LOCK_SECONDS // 60} min.")
            left = LOGIN_MAX_FAILURES - len(self.failures)
        self.sleep(LOGIN_FAILURE_DELAY_SECONDS)  # slows a script down, outside the lock
        return False, f"Clave incorrecta. Quedan {left} intento{'s' if left != 1 else ''}."
