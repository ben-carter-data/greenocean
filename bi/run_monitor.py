"""The manual run of the pipeline, followed from the panel (D-351): its steps live, the real log of each finished job,
a time limit, and the cancellation.

The run lives in GitHub; the panel only follows it. A «watch» (a dict kept in the session) says where the follow stands:
phase, run, steps, tails of the finished jobs. While a job runs GitHub gives no log of it, so the live log is one line per
step (time, state, duration); when a job ends its last LOG_LINES lines are read, without tokens. The one write is
`control.cancel_workflow_run`; everything else is a GET through `github_actions.get`.
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests

from bi import control, github_actions
from bi.i18n import tr

WATCH = "run_watch"
MAX_MINUTES = 20  # the workflow's own timeout-minutes (semanal.yml); past it the window stops asking
CONFIRM_SECONDS = 90  # how long GitHub may take to show the run it was asked to start
CHILE = ZoneInfo("America/Santiago")
STARTING, RUNNING, OK, FAILED, CANCELLED, TIMEOUT, UNCONFIRMED = (
    "starting",
    "running",
    "ok",
    "failed",
    "cancelled",
    "timeout",
    "unconfirmed",
)
FINAL = {OK, FAILED, CANCELLED, TIMEOUT, UNCONFIRMED}
STATE_WORDS = {
    "ok": "OK",
    "failed": "FALLÓ",
    "in_progress": "EN CURSO",
    "pending": "PENDIENTE",
    "skipped": "OMITIDO",
    "cancelled": "CANCELADO",
}
PHASE_LABELS = {
    STARTING: "Iniciando la ejecución en GitHub…",
    RUNNING: "Ejecución en curso",
    OK: "Ejecución completada",
    FAILED: "La ejecución falló",
    CANCELLED: "Cancelada",
    TIMEOUT: "Sigue en GitHub",
    UNCONFIRMED: "GitHub no confirmó el inicio",
}


def new_watch(now: datetime) -> dict[str, Any]:
    return {
        "phase": STARTING,
        "started": now,
        "run_id": None,
        "url": None,
        "steps": [],
        "jobs": {},
        "tails": {},
        "error": None,
        "cancel_error": None,
        "confirming": False,
        "minimized": False,
    }


def is_final(watch: dict[str, Any]) -> bool:
    return watch["phase"] in FINAL


def fetch_run(run_id: int, token: str) -> dict[str, Any]:
    """The run and its jobs as GitHub says them now (two GETs)."""
    run = github_actions.get(f"/repos/{control.REPOSITORY}/actions/runs/{run_id}", token).json()
    jobs = github_actions.get(f"/repos/{control.REPOSITORY}/actions/runs/{run_id}/jobs", token, {"per_page": 30}).json()
    return {
        "status": run["status"],
        "conclusion": run.get("conclusion"),
        "url": run["html_url"],
        "jobs": jobs.get("jobs", []),
    }


def find_run(token: str, requested_at: datetime) -> dict[str, Any] | None:
    return control.find_run_started_after(control.list_workflow_runs(token, 8), requested_at)


def read_steps(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every step of every job: job, name, state, start and seconds."""
    steps = []
    for job in jobs:
        for step in job.get("steps", []):
            state = control.classify_run(step["status"], step.get("conclusion"))
            if step.get("conclusion") == "skipped":
                state = "skipped"
            elif step.get("conclusion") == "cancelled":
                state = "cancelled"
            elif step["status"] == "queued":
                state = "pending"
            started = control.parse_github_time(step.get("started_at"))
            finished = control.parse_github_time(step.get("completed_at"))
            seconds = (finished - started).total_seconds() if started and finished else None
            steps.append(
                {"job": job["name"], "name": step["name"], "state": state, "started": started, "seconds": seconds}
            )
    return steps


def finish_phase(status: str, conclusion: str | None) -> str | None:
    if status != "completed":
        return None
    return {"success": OK, "cancelled": CANCELLED}.get(conclusion or "", FAILED)


def refresh(watch: dict[str, Any], token: str, now: datetime) -> dict[str, Any]:
    """Bring the watch up to date with GitHub. Never raises: a failed question is kept in «error» and asked again."""
    if is_final(watch):
        return watch
    elapsed = (now - watch["started"]).total_seconds()
    try:
        if watch["run_id"] is None:
            run = find_run(token, watch["started"])
            if run is None:
                if elapsed > CONFIRM_SECONDS:
                    watch["phase"] = UNCONFIRMED
                return watch
            watch.update(run_id=run["id"], url=run["url"], phase=RUNNING)
        data = fetch_run(watch["run_id"], token)
        watch["url"] = data["url"]
        watch["steps"] = read_steps(data["jobs"])
        for job in data["jobs"]:
            if job["status"] == "completed" and job["id"] not in watch["tails"]:
                watch["tails"][job["id"]] = read_tail(job, token)
                watch["jobs"][job["id"]] = job["name"]
        final = finish_phase(data["status"], data["conclusion"])
        if final:
            watch["phase"] = final
        elif elapsed > MAX_MINUTES * 60:
            watch["phase"] = TIMEOUT
        watch["error"] = None
    except requests.RequestException as error:
        watch["error"] = github_actions.redact(github_actions.explain(error), (token,))
        if elapsed > MAX_MINUTES * 60 and watch["run_id"] is not None:
            watch["phase"] = TIMEOUT
    return watch


def read_tail(job: dict[str, Any], token: str) -> list[str]:
    """The lines of a finished job's real log, without tokens; the reason when it cannot be read. D-367: when the job
    failed, the log of the step that failed (with the failing tests first), not the last lines of the whole job."""
    try:
        lines = github_actions.clean_log(github_actions.job_log(job["id"], token), (token,))
        if job.get("conclusion") == "failure":
            step = github_actions.failed_step(lines)
            if step:
                return step
        return lines[-github_actions.LOG_LINES :]
    except requests.RequestException as error:
        return [github_actions.redact(github_actions.explain(error, "log"), (token,))]


def cancel(watch: dict[str, Any], token: str) -> None:
    """Ask GitHub to cancel. On success the window says «Cancelada»; if GitHub refuses, the reason is kept and the run
    stays as it was."""
    watch["confirming"] = False
    try:
        control.cancel_workflow_run(watch["run_id"], token)
    except requests.RequestException as error:
        watch["cancel_error"] = github_actions.redact(control.describe_cancel_error(error), (token,))
        return
    watch["cancel_error"] = None
    watch["phase"] = CANCELLED


def current_step(watch: dict[str, Any]) -> str:
    running = next((step for step in watch["steps"] if step["state"] == "in_progress"), None)
    return control.STEP_NAMES.get(running["name"], running["name"]) if running else ""


def indicator(watch: dict[str, Any]) -> str:
    """The header's small text: «Ejecución en curso · paso» while it runs; the final result after."""
    label = tr(PHASE_LABELS[watch["phase"]])
    step = current_step(watch) if watch["phase"] == RUNNING else ""
    return f"{label} · {step}" if step else label


def build_log(watch: dict[str, Any]) -> str:
    """One line per step with time, state and duration; under each finished job, its real last lines."""
    lines = []
    for step in watch["steps"]:
        when = step["started"].astimezone(CHILE).strftime("%H:%M:%S") if step["started"] else "--:--:--"
        duration = f"{round(step['seconds'])} s" if step["seconds"] is not None else "—"
        name = control.STEP_NAMES.get(step["name"], step["name"])
        lines.append(f"{when}  {tr(STATE_WORDS[step['state']]):<10} {name} ({duration})")
    for job_id, tail in watch["tails"].items():
        lines.append("")
        name = watch["jobs"].get(job_id, "")
        if tail and tail[0].startswith("##[group]Run "):  # D-367: the step that failed, named by its command
            lines.append(f"── {name} · {tr('paso que falló')}: {tail[0][len('##[group]') :]} ──")
            tail = tail[1:]
        else:
            lines.append(f"── {name} · {tr('últimas {} líneas').format(len(tail))} ──")
        lines.extend(line.replace("##[error]", "ERROR: ") for line in tail)
    return github_actions.redact("\n".join(lines))


def build_copy_html(
    text: str, label: str, done: str, selected: str, ink: str = "#e8eef6", border: str = "#344256"
) -> str:
    """A small button that copies the log: the browser's clipboard, or the text selected when the page forbids it."""
    payload = json.dumps({"text": text, "done": done, "selected": selected}, ensure_ascii=False).replace("</", "<\\/")
    return (
        "<!doctype html><html><head><meta charset='utf-8'><style>body{margin:0;font:13px system-ui,sans-serif}"
        f"button{{font:inherit;padding:5px 12px;border-radius:8px;border:1px solid {border};background:transparent;color:{ink};"
        "cursor:pointer}pre{position:absolute;left:-9999px}</style></head><body>"
        f"<button id='copy'>{html.escape(label)}</button><pre id='text'></pre>"
        f"<script type='application/json' id='data'>{payload}</script>"
        "<script>const D=JSON.parse(document.getElementById('data').textContent);"
        "const b=document.getElementById('copy'),pre=document.getElementById('text'),name=b.textContent;pre.textContent=D.text;"
        "b.onclick=async()=>{try{await navigator.clipboard.writeText(D.text);b.textContent=D.done;}"
        "catch(e){const r=document.createRange();r.selectNodeContents(pre);const s=getSelection();s.removeAllRanges();s.addRange(r);"
        "b.textContent=D.selected;}setTimeout(()=>{b.textContent=name;},1500);};</script></body></html>"
    )
