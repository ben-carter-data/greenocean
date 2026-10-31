"""The pages of business and systems analysis (D-376, D-377) read their text from the project documents, in the
reader's language: the panel and the documents never say two different things, and nothing is written twice."""

from __future__ import annotations

import re
from typing import Any

from bi import i18n

VIEW_MARK = re.compile(r"\[\[vista:([^\]]+)\]\]")
# D-376: one icon per stakeholder, in the order of the PRD's table (Material Symbols).
STAKEHOLDER_ICONS = ["family_restroom", "restaurant", "agriculture", "newspaper", "engineering"]


def read_section(document: str, number: str, language: str | None = None) -> str:
    """The text of the section numbered `number` («3.1», «6») of a document of docs/, without its heading, up to the
    next heading of the same level or above."""
    text = (i18n.documents_dir(language) / document).read_text(encoding="utf-8")
    level = 3 if "." in number else 2
    start = re.search(rf"^{'#' * level} {re.escape(number)}\.? .*$", text, re.MULTILINE)
    if start is None:
        raise KeyError(f"{document} has no section {number}")
    end = re.compile(rf"^#{{1,{level}}} ", re.MULTILINE).search(text, start.end())
    return text[start.end() : end.start() if end else len(text)].strip()


def read_table(text: str) -> list[dict[str, str]]:
    """The first Markdown table of a text, one dict per row, keyed by the header."""
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return []
    cells = [[cell.strip() for cell in line.strip("|").split("|")] for line in lines]
    header = cells[0]
    return [dict(zip(header, row)) for row in cells[2:]]


def views_in(text: str) -> list[str]:
    """The pages a cell links with [[vista:…]], in their order."""
    return VIEW_MARK.findall(text)


def read_stakeholders(language: str | None = None) -> list[dict[str, Any]]:
    """PRD 3.1: each stakeholder with who they are, what they ask, the decision the answer helps them make and the
    pages that answer it. The keys are the columns' places, the same in both languages."""
    rows = read_table(read_section("PRD.md", "3.1", language))
    stakeholders = []
    for row, icon in zip(rows, STAKEHOLDER_ICONS):
        name, who, question, decision, where = list(row.values())
        stakeholders.append(
            {
                "name": name,
                "who": who,
                "question": question,
                "decision": decision,
                "pages": views_in(where),
                "icon": icon,
            }
        )
    return stakeholders
