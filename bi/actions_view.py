"""The page «GitHub Actions» (D-339): the HTML of its run tables and notices, from the model of bi/github_actions.py.

Pure: no Streamlit, no network. Everything it writes is escaped; the model it reads has already been redacted. The
log's last lines are drawn by the page itself as plain code, never as HTML.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from bi import charts, control, static_files
from bi.i18n import tr

# region Constants
CHILE = ZoneInfo("America/Santiago")
STATE_WORDS = {"ok": "Correcta", "failed": "Falló", "in_progress": "En curso"}
STATE_COLORS = {"ok": "#199e70", "failed": None, "in_progress": "#b8860b"}
WORKFLOW_NAMES = {"pruebas": "Pruebas", "semanal": "Carga semanal", "calidad": "Calidad"}
WORKFLOW_NOTES = {
    "pruebas": "Ruff, mypy y pytest en cada push.",
    "semanal": "La carga de cada martes: descarga, dbt y publicación.",
    "calidad": "La medición de calidad y su informe.",
}
EVENT_WORDS = {"schedule": "Automática", "workflow_dispatch": "Manual"}
NO_TOKEN_NOTICE = (
    "Falta el token de solo lectura. Sin él solo se ven los estados, sin logs: guárdalo como GITHUB_READ_TOKEN en "
    "los secretos de Streamlit."
)
# endregion


# region The page «GitHub Actions»
def esc(value: Any) -> str:
    return html.escape(str(value))


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    total = int(round(seconds))
    return f"{total} s" if total < 60 else f"{total // 60} min {total % 60:02d} s"


def format_time(moment: datetime | None) -> str:
    return "—" if moment is None else moment.astimezone(CHILE).strftime("%d-%m %H:%M")


def token_note(expiration: datetime | None, now: datetime | None = None) -> tuple[str, bool]:
    """(sentence, is_urgent) about when the token expires; urgent under the days the Operations center also warns at."""
    if expiration is None:
        return tr("El token no tiene fecha de vencimiento."), False
    days = (expiration - (now or datetime.now(timezone.utc))).days
    if days < 0:
        return tr("El token venció: crea otro y cámbialo en los secretos de Streamlit."), True
    text = tr("El token vence en {} días ({}).").format(days, expiration.astimezone(CHILE).strftime("%d-%m-%Y"))
    return text, days <= control.TOKEN_WARNING_DAYS


def workflow_summary(entry: dict[str, Any]) -> str:
    """The one line of a workflow: its name and its latest run (state, date, commit and duration)."""
    name = tr(WORKFLOW_NAMES[entry["name"]])
    if not entry["runs"]:
        return f"{name} · {tr('Todavía no hay ejecuciones.')}"
    run = entry["runs"][0]
    return (
        f"{name} · {tr(STATE_WORDS[run['state']])} · {format_time(run['started_at'])} · {run['sha'][:7]} · "
        f"{format_duration(run['seconds'])}"
    )


def build_workflow_note(entry: dict[str, Any]) -> str:
    """The file of a workflow and what it does, under its line when it opens."""
    return f'<p class="cr-detail"><code>{esc(entry["file"])}</code> · {esc(tr(WORKFLOW_NOTES[entry["name"]]))}</p>'


def build_runs_table(runs: list[dict[str, Any]]) -> str:
    """One row per run: state, date in Chile's time, commit (linked), how it started, duration and the link to GitHub."""
    if not runs:
        return f'<p class="ga-note">{esc(tr("Todavía no hay ejecuciones."))}</p>'
    rows = []
    for run in runs:
        state = run["state"]
        sha = run["sha"][:7]
        commit = (
            f'<a href="https://github.com/{control.REPOSITORY}/commit/{esc(run["sha"])}" target="_blank" '
            f'rel="noopener noreferrer"><code>{esc(sha)}</code></a> {esc(run["message"])}'
        )
        event = run["event"]
        rows.append(
            f'<tr><td><span class="ga-state ga-{state}">{esc(tr(STATE_WORDS[state]))}</span></td>'
            f"<td>{esc(format_time(run['started_at']))}</td><td>{commit}</td>"
            f"<td>{esc(tr(EVENT_WORDS[event]) if event in EVENT_WORDS else event)}</td>"
            f'<td class="ga-num">{esc(format_duration(run["seconds"]))}</td>'
            f'<td><a href="{esc(run["url"])}" target="_blank" rel="noopener noreferrer">'
            f"{esc(tr('Abrir en GitHub'))} ↗</a></td></tr>"
        )
    head = [tr("Estado"), tr("Fecha"), tr("Commit"), tr("Cómo empezó"), tr("Duración"), ""]
    columns = "".join(f"<th>{esc(cell)}</th>" for cell in head)
    return f'<div class="ga-table"><table><thead><tr>{columns}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def build_failure_summary(job: dict[str, Any]) -> str:
    """The job and the steps that failed, what GitHub's annotations say, and the names of the failing tests."""
    steps = ", ".join(job["steps"]) or "—"
    parts = [
        f'<p class="ga-job"><b>{esc(tr("Job"))}:</b> {esc(job["name"])} · <b>{esc(tr("Paso"))}:</b> {esc(steps)}</p>'
    ]
    if job["annotations"]:
        notes = "".join(f"<li>{esc(text)}</li>" for text in job["annotations"])
        parts.append(f'<p class="ga-label">{esc(tr("Anotaciones de GitHub"))}</p><ul>{notes}</ul>')
    if job["tests"]:
        tests = "".join(f"<li><code>{esc(name)}</code></li>" for name in job["tests"])
        parts.append(f'<p class="ga-label">{esc(tr("Pruebas que fallan"))} ({len(job["tests"])})</p><ul>{tests}</ul>')
    return "".join(parts)


def build_css(palette: dict[str, str]) -> str:
    ink, text, muted, border, card = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card_border"],
        palette["card"],
    )
    soft = charts.legible(muted, palette["background"])
    colors = {state: charts.legible(color or palette["rise"], card) for state, color in STATE_COLORS.items()}
    states = "".join(f".ga-state.ga-{state} {{ color:{color}; }}\n" for state, color in colors.items())
    return static_files.style(
        "actions_view.css",
        {
            'var(--go-soft)': soft,
            'var(--go-border)': border,
            'var(--go-card)': card,
            'var(--go-text)': text,
            'var(--go-states)': states,
            'var(--go-ink)': ink,
        },
    )


# endregion
