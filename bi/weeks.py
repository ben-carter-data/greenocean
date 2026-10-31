"""How the app names a week (D-374): its Monday-to-Sunday range with the month's abbreviation, «19–25 oct» or
«26 oct – 1 nov», never its Monday alone. Inside, the data keeps the Monday (week_start) as the week's key.

Only the standard library: the weekly report of the load (bi/report.py) uses it too, and the load installs neither
Streamlit nor Altair.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def monday(value: Any) -> date:
    """The Monday a week starts on, from a date, a timestamp or an ISO text («2026-10-19»)."""
    return date.fromisoformat(str(value)[:10])


def week_range(value: Any, year: bool = False, english: bool = False) -> str:
    """«19–25 oct», «26 oct – 1 nov»; in English «Oct 19–25», «Oct 26 – Nov 1». With the year, at the end: «19–25 oct
    2026», «Oct 19–25, 2026»."""
    start = monday(value)
    end = start + timedelta(days=6)
    if english:
        first, last = MONTHS_EN[start.month - 1], MONTHS_EN[end.month - 1]
        text = f"{first} {start.day}–{end.day}" if first == last else f"{first} {start.day} – {last} {end.day}"
        return f"{text}, {end.year}" if year else text
    first, last = MONTHS[start.month - 1], MONTHS[end.month - 1]
    text = f"{start.day}–{end.day} {last}" if first == last else f"{start.day} {first} – {end.day} {last}"
    return f"{text} {end.year}" if year else text


def next_week(value: Any) -> date:
    """The Monday of the week after this one."""
    return monday(value) + timedelta(days=7)
