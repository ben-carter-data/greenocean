"""GitHub Actions, read-only (D-339): the latest runs of the three workflows and, for the latest one that failed, what
failed: the job, the step, the names of the failing tests and the last lines of the log.

It only sends GET requests: nothing here starts, cancels or re-runs anything. The token (GITHUB_READ_TOKEN, or
GITHUB_TOKEN when that one is missing) is sent in the Authorization header and nowhere else; every text that leaves
this module has gone through `redact`, so neither the token nor anything shaped like one reaches the screen, not even
if a log printed it. Without a token only the states are read (they are public); the logs need the token.
Pure functions apart from `get`, which tests replace.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import requests

from bi import control
from bi.i18n import tr

WORKFLOWS = (("pruebas", "pruebas.yml"), ("semanal", "semanal.yml"), ("calidad", "calidad.yml"))
RUNS_PER_WORKFLOW = 8
LOG_LINES = 60
MAX_LINE = 300
MAX_TESTS = 50
CACHE_SECONDS = 120  # the page asks GitHub again after two minutes, to spare the request limit

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z ?")
FAILED_TEST = re.compile(r"^(?:FAILED|ERROR) (\S+)")
SECRET_SHAPES = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,}|[Bb]earer\s+[A-Za-z0-9._~+/=-]{16,})"
)


def pick_token(read_token: str | None, token: str | None) -> str | None:
    """The read-only token when there is one; otherwise the app's usual one. Either is only ever used to read."""
    return read_token or token or None


def get(path: str, token: str | None, params: dict[str, Any] | None = None) -> requests.Response:
    """One GET to the GitHub API; raises on an error status. The only function of this module that touches the network."""
    response = requests.get(
        f"{control.API_URL}{path}",
        headers=control.build_headers(token),
        params=params,
        timeout=control.REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response


def redact(text: str, secrets: tuple[str | None, ...] = ()) -> str:
    """The text without the secrets given and without anything shaped like a GitHub token."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, "***")
    return SECRET_SHAPES.sub("***", text)


def simplify_run(run: dict[str, Any]) -> dict[str, Any]:
    """What the page shows of one run: state, date, commit, duration and the link to open it in GitHub."""
    started = control.parse_github_time(run.get("run_started_at") or run.get("created_at"))
    updated = control.parse_github_time(run.get("updated_at"))
    state = control.classify_run(run["status"], run.get("conclusion"))
    seconds = (updated - started).total_seconds() if state != control.RUN_IN_PROGRESS and started and updated else None
    message = ((run.get("head_commit") or {}).get("message") or "").splitlines()
    return {
        "id": run["id"],
        "state": state,
        "conclusion": run.get("conclusion"),
        "started_at": started,
        "seconds": seconds,
        "sha": run.get("head_sha", ""),
        "message": message[0][:90] if message else "",
        "branch": run.get("head_branch") or "",
        "event": run.get("event") or "",
        "url": run["html_url"],
    }


def list_runs(workflow_file: str, token: str | None, count: int = RUNS_PER_WORKFLOW) -> list[dict[str, Any]]:
    """The latest runs of one workflow, newest first. Public: it needs no token."""
    answer = get(f"/repos/{control.REPOSITORY}/actions/workflows/{workflow_file}/runs", token, {"per_page": count})
    return [simplify_run(run) for run in answer.json()["workflow_runs"]]


def list_failed_jobs(run_id: int, token: str | None) -> list[dict[str, Any]]:
    """The jobs of a run that did not succeed, each with the steps that failed."""
    answer = get(f"/repos/{control.REPOSITORY}/actions/runs/{run_id}/jobs", token, {"per_page": 30})
    jobs = []
    for job in answer.json().get("jobs", []):
        if job.get("conclusion") in ("failure", "timed_out", "cancelled"):
            steps = [step["name"] for step in job.get("steps", []) if step.get("conclusion") == "failure"]
            jobs.append({"id": job["id"], "name": job["name"], "steps": steps, "url": job.get("html_url") or ""})
    return jobs


def job_annotations(job_id: int, token: str | None) -> list[str]:
    """The failure annotations of a job: usually only «Process completed with exit code 1»."""
    answer = get(f"/repos/{control.REPOSITORY}/check-runs/{job_id}/annotations", token)
    return [
        item["message"][:MAX_LINE]
        for item in answer.json()
        if item.get("annotation_level") == "failure" and item.get("message")
    ]


def job_log(job_id: int, token: str | None) -> str:
    """The plain text log of a job. GitHub answers with a redirect to a temporary address; it needs the token."""
    return get(f"/repos/{control.REPOSITORY}/actions/jobs/{job_id}/logs", token).text


def clean_log(text: str, secrets: tuple[str | None, ...] = ()) -> list[str]:
    """The log as lines without colors or time stamps, without secrets, each line no longer than MAX_LINE."""
    lines = []
    for raw in text.splitlines():
        line = TIMESTAMP.sub("", ANSI.sub("", raw)).rstrip()
        lines.append(redact(line, secrets)[:MAX_LINE])
    return lines


def failed_tests(lines: list[str]) -> list[str]:
    """The names of the failing tests: the ids pytest prints on its «FAILED …» and «ERROR …» lines, once each."""
    found: list[str] = []
    for line in lines:
        match = FAILED_TEST.match(line)
        if match and match.group(1) not in found:
            found.append(match.group(1))
    return found[:MAX_TESTS]


def token_expiration(token: str) -> datetime | None:
    """When the token expires, from the header GitHub puts on every answer; None if it never does. Only the date leaves."""
    answer = get("/rate_limit", token)  # /rate_limit does not count against the hourly limit
    return control.parse_token_expiration(answer.headers.get(control.TOKEN_EXPIRATION_HEADER))


def explain(error: Exception, what: str = "") -> str:
    """What to do about a failed request, in the reader's language. Only the HTTP code, never the token or the headers."""
    response = getattr(error, "response", None)
    code = getattr(response, "status_code", None)
    rate_limited = code in (403, 429) and response is not None and response.headers.get("X-RateLimit-Remaining") == "0"
    if code == 401:
        return tr(
            "El token venció o no es válido. Crea otro en GitHub (Settings, Developer settings, Fine-grained tokens) "
            "con permiso «Actions: Read» sobre este repositorio y guárdalo como GITHUB_READ_TOKEN en los secretos "
            "de Streamlit."
        )
    if code == 403 and not rate_limited:
        return tr(
            "El token no tiene permiso para leer los logs. Necesita «Actions: Read» sobre este repositorio; "
            "créalo así y guárdalo como GITHUB_READ_TOKEN en los secretos de Streamlit."
        )
    if code in (404, 410) and what == "log":
        return tr("El log ya no existe (GitHub los borra a los 90 días) o el job sigue corriendo.")
    return control.describe_github_error(error)


def failure_detail(run: dict[str, Any], token: str, secrets: tuple[str | None, ...]) -> dict[str, Any]:
    """What failed in a run: each failed job with its steps, its annotations, the failing tests and the log's tail.
    A job whose log cannot be read says why, in its own «log_error»; the rest of the page still shows."""
    detail: dict[str, Any] = {"run": run["id"], "url": run["url"], "jobs": [], "error": None}
    try:
        jobs = list_failed_jobs(run["id"], token)
    except requests.RequestException as error:
        detail["error"] = redact(explain(error), secrets)
        return detail
    for job in jobs:
        entry: dict[str, Any] = {
            "name": job["name"],
            "steps": job["steps"],
            "url": job["url"],
            "annotations": [],
            "tests": [],
            "tail": [],
            "log_error": None,
        }
        try:
            entry["annotations"] = [redact(text, secrets) for text in job_annotations(job["id"], token)]
        except requests.RequestException:
            pass  # the annotations are a nicety; the log below says more
        try:
            lines = clean_log(job_log(job["id"], token), secrets)
            entry["tests"] = failed_tests(lines)
            entry["tail"] = lines[-LOG_LINES:]
        except requests.RequestException as error:
            entry["log_error"] = redact(explain(error, "log"), secrets)
        detail["jobs"].append(entry)
    return detail


def build_model(read_token: str | None, token: str | None, now: datetime | None = None) -> dict[str, Any]:
    """Everything the page draws: per workflow its latest runs and, for the latest one that failed, what failed.
    Without a token only the runs are read; with one, the logs too, and when the token expires. No write request."""
    secret = pick_token(read_token, token)
    secrets = (read_token, token)
    model: dict[str, Any] = {"token": bool(secret), "expiration": None, "token_error": None, "workflows": []}
    if secret:
        try:
            model["expiration"] = token_expiration(secret)
        except requests.RequestException as error:
            model["token_error"] = redact(explain(error), secrets)
    for name, file in WORKFLOWS:
        entry: dict[str, Any] = {"name": name, "file": file, "runs": [], "error": None, "failure": None}
        try:
            entry["runs"] = list_runs(file, secret)
        except requests.RequestException as error:
            entry["error"] = redact(explain(error), secrets)
        failed = next((run for run in entry["runs"] if run["state"] == control.RUN_FAILED), None)
        if secret and failed and not model["token_error"]:
            entry["failure"] = failure_detail(failed, secret, secrets)
        model["workflows"].append(entry)
    model["read_at"] = now or datetime.now(timezone.utc)
    return model
