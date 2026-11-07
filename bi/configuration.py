"""«Configuración» (D-409), the author's console on one screen: the state of what keeps the app running, what to do in
each case and the maintenance tasks.

The cases, their steps and the links are read from the runbook (MANUAL 8 and 8.1) in the reader's language, so the
page and the runbook never say two different things. Pure: no Streamlit and no network. No token reaches this module:
only whether a token exists and the date GitHub gives for it.
"""

from __future__ import annotations

import csv
import html
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from bi import business_analysis, charts, control, i18n, quality_method, quality_metrics, static_files

# region Constants
OK, WARN, FAIL, UNKNOWN = "ok", "warn", "fail", "unknown"
STATE_COLORS = {
    OK: charts.STATUS_COLORS["good"],
    WARN: charts.STATUS_COLORS["warning"],
    FAIL: charts.STATUS_COLORS["critical"],
    UNKNOWN: charts.STATUS_COLORS["unknown"],
}
MANUAL = "MANUAL.md"
# One icon per case of MANUAL 8.1, in its order (Material Symbols).
CASE_ICONS = ["error", "assignment", "key", "schedule", "sync_problem"]
LOAD_DAYS = 8  # a weekly load older than this is late, like a report (D-361)
REPORT_BRANCH = "informe-calidad/"
INPUT_LIST = Path(__file__).resolve().parent.parent / "agent" / "input.csv"
MARKDOWN_LINK = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)$")
VIEW_LINK = re.compile(r"^\[\[vista:([^\]]+)\]\]$")
CODE = re.compile(r"`([^`]+)`")
INLINE_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
# endregion


# region Words and cards
def t(spanish: str, english: str) -> str:
    return english if i18n.is_english() else spanish


def day_text(moment: date | datetime) -> str:
    """A date as each language writes it in the documents: 17-01-2027 or 2027-01-17."""
    return f"{moment:%Y-%m-%d}" if i18n.is_english() else f"{moment:%d-%m-%Y}"


TOKEN_LABELS = {
    "GITHUB_TOKEN": ("token de lanzamiento", "launch token"),
    "GITHUB_READ_TOKEN": ("token de solo lectura", "read-only token"),
}


def token_label(name: str) -> str:
    """The name of a token's secret as the reader says it: «token de lanzamiento», never its value."""
    return t(*TOKEN_LABELS[name])


def card(key: str, icon: str, label: str, state: str, value: str, detail: str = "") -> dict[str, str]:
    return {"key": key, "icon": icon, "label": label, "state": state, "value": value, "detail": detail}


# endregion


# region The six states


def token_card(
    key: str, label: str, present: bool, expiration: datetime | None, error: str | None, now: datetime
) -> dict[str, str]:
    """A token by its date only: days left and the day it expires, amber at TOKEN_WARNING_DAYS or fewer, red when it
    expired or is missing. Never its value."""
    if not present:
        return card(key, "key", label, FAIL, t("Falta", "Missing"), t("No está en los secretos", "Not in the secrets"))
    if error:
        return card(key, "key", label, UNKNOWN, t("Sin leer", "Not read"), error)
    if expiration is None:
        return card(key, "key", label, OK, t("Sin vencimiento", "No expiry"))
    days = (expiration - now).days
    if days < 0:
        return card(key, "key", label, FAIL, t("Venció", "Expired"), t("el {}", "on {}").format(day_text(expiration)))
    state = WARN if days <= control.TOKEN_WARNING_DAYS else OK
    return card(
        key,
        "key",
        label,
        state,
        t("{} días", "{} days").format(days),
        t("vence el {}", "expires on {}").format(day_text(expiration)),
    )


def load_card(loaded_at: datetime, failed_at: datetime | None, now: datetime) -> dict[str, str]:
    """The latest published load; red when a later run failed (the panel keeps the last valid one), amber past
    LOAD_DAYS."""
    label = t("Última carga", "Latest load")
    if failed_at and failed_at > loaded_at:
        return card(
            "load",
            "database",
            label,
            FAIL,
            t("Falló el {}", "Failed on {}").format(day_text(failed_at)),
            t("El panel muestra la del {}", "The panel shows the one of {}").format(day_text(loaded_at)),
        )
    days = (now - loaded_at).days
    return card(
        "load",
        "database",
        label,
        WARN if days > LOAD_DAYS else OK,
        day_text(loaded_at),
        t("hace {} días", "{} days ago").format(days) if days != 1 else t("hace 1 día", "1 day ago"),
    )


def report_card(report: dict[str, Any] | None, today: date) -> dict[str, str]:
    """The latest quality report: amber when it is more than 8 days old (D-361) or has an urgent indicator, red with a
    critical one. It reads the report; it computes nothing."""
    label = t("Último informe", "Latest report")
    if not report:
        return card("report", "assignment", label, UNKNOWN, t("Sin informes", "No reports"))
    measured = date.fromisoformat(str(report["fecha"])[:10])
    states = [row["estado"] for row in report["indicadores"]]
    out = sum(state in ("urgente", "critico") for state in states)
    stale = quality_method.is_stale(report, today)
    state = WARN if stale else FAIL if "critico" in states else WARN if out else OK
    detail = (
        t("{} · {} fuera de su aceptable", "{} · {} past its acceptable").format(day_text(measured), out)
        if out
        else day_text(measured)
    )
    return card("report", "assignment", label, state, quality_metrics.report_code(report, i18n.is_english()), detail)


def ci_card(runs: list[dict[str, Any]], error: str | None) -> dict[str, str]:
    """The latest run of the tests workflow on main (Ruff, mypy and pytest)."""
    label = t("Pruebas del CI en main", "CI tests on main")
    if error:
        return card("ci", "fact_check", label, UNKNOWN, t("Sin leer", "Not read"), error)
    run = next((run for run in runs if run["branch"] == "main"), None)
    if run is None:
        return card("ci", "fact_check", label, UNKNOWN, t("Sin ejecuciones", "No runs"))
    words = {
        control.RUN_OK: (OK, t("En verde", "Green")),
        control.RUN_FAILED: (FAIL, t("Fallaron", "Failed")),
        control.RUN_IN_PROGRESS: (UNKNOWN, t("En curso", "Running")),
    }
    state, value = words[run["state"]]
    when = day_text(run["started_at"]) if run["started_at"] else ""
    return card("ci", "fact_check", label, state, value, f'{when} · {run["sha"][:7]}'.strip(" ·"))


def sources_card(notice: str) -> dict[str, str]:
    """D-356: a source that has not published the latest week yet is a notice, not a failure."""
    label = t("Fuentes", "Sources")
    if not notice:
        return card("sources", "cloud_download", label, OK, t("Al día", "Up to date"))
    return card("sources", "cloud_download", label, WARN, t("Atrasada", "Late"), notice)


def token_alert(label: str, expiration: datetime | None, now: datetime) -> dict[str, Any] | None:
    """D-410: a token at TOKEN_WARNING_DAYS or fewer from its expiry, or already expired, for the author's alert; None
    otherwise. The same rule as its card."""
    if expiration is None:
        return None
    days = (expiration - now).days
    if days > control.TOKEN_WARNING_DAYS:
        return None
    return {"label": label, "days": days, "date": day_text(expiration), "expired": days < 0}


def build_token_alerts_html(alerts: list[dict[str, Any]]) -> str:
    """The tokens of «Acción requerida» (D-410), in the look of its indicators: what expires, when, and where its steps
    are. Only the date, never the value."""
    if not alerts:
        return ""
    case = t("Un token vence o falta", "A token expires or is missing")
    parts = []
    for alert in alerts:
        title = (
            t("{} · venció el {}", "{} · expired on {}").format(alert["label"].capitalize(), alert["date"])
            if alert["expired"]
            else t("{} · vence en {} días", "{} · expires in {} days").format(
                alert["label"].capitalize(), alert["days"]
            )
        )
        action = t(
            "Renuévalo antes del {}: los pasos están en «Configuración», en «{}».",
            "Renew it before {}: the steps are in «Settings», under «{}».",
        ).format(alert["date"], case)
        parts.append(
            f'<div class="qm-alert qm-{"critico" if alert["expired"] else "urgente"}"><h4>{esc(title)}</h4>'
            f"<p>{esc(action)}</p></div>"
        )
    return '<div class="qm-alerts">' + "".join(parts) + "</div>"


# endregion


# region The runbook: cases, links and maintenance


def read_link(cell: str) -> dict[str, str] | None:
    """A cell of the runbook as a link: a page of the panel ([[vista:…]]), an address, or nothing («—»)."""
    cell = cell.strip()
    view = VIEW_LINK.match(cell)
    if view:
        return {"kind": "view", "text": view.group(1), "target": view.group(1)}
    link = MARKDOWN_LINK.match(cell)
    if link:
        return {"kind": "url", "text": link.group(1), "target": link.group(2)}
    return None


def read_cases(language: str | None = None) -> list[dict[str, Any]]:
    """MANUAL 8.1: each case with its steps in order, each step automatic or manual, with its link. The columns are
    read by their place, the same in both languages."""
    rows = business_analysis.read_table(business_analysis.read_section(MANUAL, "8.1", language))
    cases: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        name, step, kind, text, link = list(row.values())
        cases.setdefault(name, []).append(
            {
                "step": int(step),
                "automatic": kind.lower().startswith("autom"),
                "kind": kind,
                "text": text,
                "link": read_link(link),
            }
        )
    return [{"name": name, "icon": icon, "steps": steps} for (name, steps), icon in zip(cases.items(), CASE_ICONS)]


def read_guide(language: str | None = None) -> list[dict[str, str]]:
    """MANUAL 8, «Guía de GitHub»: each link with its task and what it is for."""
    rows = business_analysis.read_table(business_analysis.read_section(MANUAL, "8", language))
    links = []
    for row in rows:
        task, cell, purpose, *_ = list(row.values())
        link = read_link(cell)
        if link:
            links.append({"task": task, "text": link["text"], "url": link["target"], "purpose": purpose})
    return links


def read_schedule(language: str | None = None) -> list[dict[str, str]]:
    """MANUAL 3, «Qué se revisa y cuándo»: when, what and where."""
    rows = business_analysis.read_table(business_analysis.read_section(MANUAL, "3", language))
    return [dict(zip(("when", "what", "where"), list(row.values()))) for row in rows]


def years_listed(path: Path = INPUT_LIST) -> dict[str, set[int]]:
    """The years each source has a line for in agent/input.csv."""
    years: dict[str, set[int]] = {}
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            years.setdefault(row["source"], set()).add(int(row["year"]))
    return years


def maintenance(
    tokens: list[tuple[str, bool, datetime | None]],
    branches: int | None,
    schedule: list[dict[str, str]],
    today: date,
    listed: dict[str, set[int]],
) -> list[dict[str, str]]:
    """The tasks with a date: renew each token before it expires (its date read from GitHub, never written by hand),
    the old report branches counted on GitHub, and the runbook's yearly and periodic tasks (MANUAL 3)."""
    items = []
    for label, present, expiration in tokens:
        if not present:
            items.append(
                {"what": t("Crear el {}", "Create the {}").format(label), "when": t("ahora", "now"), "state": FAIL}
            )
        elif expiration is not None:
            days = (expiration.date() - today).days
            state = FAIL if days < 0 else WARN if days <= control.TOKEN_WARNING_DAYS else OK
            items.append(
                {
                    "what": t("Renovar el {}", "Renew the {}").format(label),
                    "when": t("antes del {}", "before {}").format(day_text(expiration)),
                    "state": state,
                }
            )
    if branches is None:
        when, state = t("sin leer", "not read"), UNKNOWN
    else:
        when, state = (
            (t("{} en GitHub", "{} on GitHub").format(branches), WARN) if branches else (t("ninguna", "none"), OK)
        )
    items.append(
        {
            "what": t("Borrar las ramas viejas de informes", "Delete the old report branches"),
            "when": when,
            "state": state,
        }
    )
    for row in schedule:
        where = row["where"]
        if "agent/input.csv" in where:
            year = today.year if today.month == 1 else today.year + 1
            done = all(year in years for years in listed.values()) and len(listed) >= 2
            due = date(year, 1, 31)
            late = today.month == 1 and not done
            items.append(
                {
                    "what": row["what"],
                    "when": t("hecho para {}", "done for {}").format(year)
                    if done
                    else t("antes del {}", "before {}").format(day_text(due)),
                    "state": FAIL if late else OK,
                }
            )
        elif "agent/downloads" in row["what"]:
            items.append({"what": row["what"], "when": row["when"].lower(), "state": UNKNOWN})
    return items


# endregion


# region HTML


def esc(value: Any) -> str:
    return html.escape(str(value))


def rich(text: str) -> str:
    """Runbook text, escaped, with its `code` as code."""
    return CODE.sub(r"<code>\1</code>", esc(text))


def icon(name: str) -> str:
    return f'<span class="cf-icon" aria-hidden="true">{esc(name)}</span>'


def build_cards_html(cards: list[dict[str, str]]) -> str:
    words = {
        OK: t("Bien", "Fine"),
        WARN: t("Atención", "Attention"),
        FAIL: t("Acción", "Action"),
        UNKNOWN: t("Sin dato", "No data"),
    }
    return (
        '<div class="cf-cards">'
        + "".join(
            f'<div class="cf-card cf-{item["state"]}" title="{esc(item["detail"])}">'
            f'<div class="cf-card-head">{icon(item["icon"])}<span>{esc(item["label"])}</span>'
            f'<em>{esc(words[item["state"]])}</em></div>'
            f'<b>{esc(item["value"])}</b><small>{esc(item["detail"]) or "&nbsp;"}</small></div>'
            for item in cards
        )
        + "</div>"
    )


def build_step_html(step: dict[str, Any]) -> str:
    """One step of a case: its number, automatic or manual, what to do and, when it is an address, its link (a new
    tab). A page of the panel is linked by the page itself, so it opens in the same visit (a reload would close the
    author's session)."""
    link = step["link"]
    anchor = (
        f'<a href="{esc(link["target"])}" target="_blank" rel="noopener noreferrer">{esc(link["text"])} ↗</a>'
        if link and link["kind"] == "url"
        else ""
    )
    kind = "auto" if step["automatic"] else "manual"
    return (
        f'<div class="cf-step cf-{kind}"><b>{step["step"]}</b><span class="cf-kind">{esc(step["kind"])}</span>'
        f'<p>{rich(step["text"])}</p>{anchor}</div>'
    )


def short(text: str) -> tuple[str, str]:
    """A runbook sentence for one line: its first clause, up to «:», «, » or « (»; and the whole of it, without its links,
    for the hover."""
    plain = INLINE_LINK.sub(r"\1", text)
    cut = min((plain.find(mark) for mark in (": ", ", ", " (") if mark in plain), default=len(plain))
    return plain[:cut], CODE.sub(r"\1", plain)


def build_maintenance_html(items: list[dict[str, str]]) -> str:
    rows = []
    for item in items:
        line, whole = short(item["what"])
        rows.append(
            f'<li class="cf-{item["state"]}" title="{esc(whole)}"><i></i><span>{rich(line)}</span>'
            f'<b>{esc(item["when"])}</b></li>'
        )
    return '<ul class="cf-tasks">' + "".join(rows) + "</ul>"


def build_guide_html(links: list[dict[str, str]]) -> str:
    """The runbook's GitHub guide as compact links grouped by task; each opens in a new tab and asks for its own login."""
    groups: dict[str, list[dict[str, str]]] = {}
    for link in links:
        groups.setdefault(link["task"], []).append(link)
    return (
        '<div class="cf-guide">'
        + "".join(
            f'<div class="cf-guide-row"><span>{esc(task)}</span>'
            + "".join(
                f'<a href="{esc(link["url"])}" target="_blank" rel="noopener noreferrer" title="{esc(link["purpose"])}">'
                f'{esc(link["text"])} ↗</a>'
                for link in items
            )
            + "</div>"
            for task, items in groups.items()
        )
        + "</div>"
    )


def build_css(palette: dict[str, str]) -> str:
    border, card_bg, text, strong, accent = (
        palette["card_border"],
        palette["card"],
        palette["text"],
        palette["strong_text"],
        palette["accent"],
    )
    states = "".join(
        f".cf-card.cf-{state} {{border-top-color:{color};}} .cf-card.cf-{state} em {{color:{color};"
        f"background:color-mix(in srgb,{color} 14%,transparent);}} .cf-tasks li.cf-{state} i {{background:{color};}}"
        for state, color in STATE_COLORS.items()
    )
    return static_files.style(
        "configuration.css",
        {
            'var(--go-text)': text,
            'var(--go-accent)': accent,
            'var(--go-border)': border,
            'var(--go-card-bg)': card_bg,
            'var(--go-strong)': strong,
            'var(--go-states)': states,
            'var(--go-charts-status-colors-running)': charts.STATUS_COLORS["running"],
            'var(--go-charts-status-colors-warning)': charts.STATUS_COLORS["warning"],
        },
    )


# endregion
