"""The pages of business and systems analysis (D-376, D-377) read their text from the project documents, in the
reader's language: the panel and the documents never say two different things, and nothing is written twice."""

from __future__ import annotations

import re
from typing import Any

from bi import i18n

# region Constants
VIEW_MARK = re.compile(r"\[\[vista:([^\]]+)\]\]")
# D-376: one icon per stakeholder, in the order of the PRD's table (Material Symbols).
STAKEHOLDER_ICONS = ["family_restroom", "restaurant", "agriculture", "newspaper", "engineering"]
# endregion


# region Business analysis
def read_section(document: str, number: str, language: str | None = None) -> str:
    """The text of the section numbered `number` («3.1», «6») of a document of docs/, without its heading, up to the
    next heading of the same level or above."""
    text = i18n.document_path(document, language).read_text(encoding="utf-8")
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


# D-444: the interest map of PRD 3.4: the ring of each stakeholder, read from the PRD in the reader's language.
INTEREST_LEVELS = {"alto": 0, "high": 0, "medio": 1, "medium": 1, "bajo": 2, "low": 2}
INTEREST_ICONS = [
    "restaurant",
    "agriculture",
    "newspaper",
    "family_restroom",
    "engineering",
    "account_balance",
    "query_stats",
]


def read_interest(language: str | None = None) -> list[dict[str, Any]]:
    """PRD 3.4: each stakeholder with its ring (0 high, 1 medium, 2 low), why it sits there and the page it opens."""
    rows = read_table(read_section("PRD.md", "3.4", language))
    found = []
    for row, icon in zip(rows, INTEREST_ICONS):
        name, level, why, where = list(row.values())
        found.append(
            {
                "name": name,
                "level": INTEREST_LEVELS[level.strip().lower()],
                "why": why,
                "pages": views_in(where),
                "icon": icon,
            }
        )
    return found


# D-377: the blocks of «Análisis de negocio y sistemas», in the reading order of a case.
BLOCKS = [
    "El problema",
    "Interesados",
    "Qué escuchamos",
    "Requisitos",
    "Alcance",
    "Proceso",
    "KPIs",
    "Decisiones de sistema",
    "Evaluación",
    "Del feedback al cambio",
]
QUALITY_PLAN = "PLAN_DE_CALIDAD.md"
# D-377: the system decisions (BSA): a title, the parts of its line and the page that holds the rest («sqap» or «git»).
# Each part is read from one section of the SQAP: (section, words that pick the paragraph in both languages or None for
# the first one, «start» for the paragraph's opening, «sentence» for the sentence holding those words, «bullet» for the
# first sentence of the section's first bullet, and a short label the page puts in front of the part, or None).
SYSTEM_DECISIONS = [
    (
        "Qué medimos y qué no, y por qué",
        (("3", None, "start", None), ("5", None, "bullet", "No medimos")),
        "sqap",
    ),
    ("Umbrales aceptables", (("6", None, "start", None),), "sqap"),
    ("Pruebas que bloquean y pruebas que informan", (("7", None, "start", None),), "sqap"),
    ("Fuentes retrasadas", (("10", ("D-356",), "start", None),), "sqap"),
    ("Registro de fallas con su historial", (("9", None, "start", None),), "git"),
    ("Alertas al Autor", (("10", ("aviso urgente", "urgent alert"), "sentence", None),), "sqap"),
]


def paragraphs(text: str) -> list[str]:
    """The paragraphs of a section's text: no tables, no diagram markers, no headings."""
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text)]
    return [" ".join(block.split()) for block in blocks if block and not block.startswith(("|", "[[diagrama:", "#"))]


def plain(text: str) -> str:
    """A text without its Markdown marks: bold, code, links and view markers."""
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return VIEW_MARK.sub(r"\1", text)


def sentences(text: str) -> list[str]:
    return [piece for piece in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ«(])", text) if piece]


def opening(text: str, minimum: int = 90) -> str:
    """The first sentence of a paragraph, with the next one while the first alone says too little."""
    pieces = sentences(text)
    line = pieces[0]
    for piece in pieces[1:]:
        if len(line) >= minimum:
            break
        line += " " + piece
    return line


def read_rows(document: str, number: str, language: str | None = None) -> list[list[str]]:
    """The rows of the first table of a section, as lists of plain cells, without the header."""
    text = read_section(document, number, language)
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    rows = [[plain(cell.strip()) for cell in line.strip("|").split("|")] for line in lines]
    return rows[2:]


def read_problem(language: str | None = None) -> list[str]:
    """PRD 2: the problem, paragraph by paragraph."""
    return [plain(paragraph) for paragraph in paragraphs(read_section("PRD.md", "2", language))]


def read_heard(language: str | None = None) -> str:
    """PRD 3.3: what real users said, in one sentence; nothing else is claimed."""
    return plain(paragraphs(read_section("PRD.md", "3.3", language))[0])


def read_feedback(language: str | None = None) -> list[list[str]]:
    """PRD 3.3: [review, what we heard, what changed, decision] per row."""
    return read_rows("PRD.md", "3.3", language)


def read_requirements(language: str | None = None) -> list[list[str]]:
    """PRD 5: the functional requirements, each with its measurable criterion: [id, requirement, criterion]."""
    return [row[:3] for row in read_rows("PRD.md", "5", language) if row[0].startswith("RF-")]


def read_scope(language: str | None = None) -> list[list[str]]:
    """PRD 6: [includes, why, excludes, why] per row."""
    return read_rows("PRD.md", "6", language)


def read_acceptance(language: str | None = None) -> list[list[str]]:
    """PRD 10: [criterion, how it is verified] per row."""
    return read_rows("PRD.md", "10", language)


def read_evaluation(language: str | None = None) -> str:
    """SQAP 4: how the quality is measured."""
    return plain(paragraphs(read_section(QUALITY_PLAN, "4", language))[0])


def read_decision_part(part: tuple[str, tuple[str, ...] | None, str, str | None], language: str | None = None) -> str:
    """One part of a system decision, read from the SQAP without a bold label in front («Fuentes retrasadas (D-356).»)."""
    number, words, scope, _ = part
    found = paragraphs(read_section(QUALITY_PLAN, number, language))
    if words:
        found = [paragraph for paragraph in found if any(word in paragraph for word in words)] or found
    first = found[0]
    if scope == "bullet":
        first = first.split(" - ")[0].removeprefix("- ")  # the paragraph is the section's bullet list on one line
    paragraph = plain(re.sub(r"^\*\*[^*]+\*\*\s*", "", first)) if scope != "bullet" else plain(first)
    if scope == "sentence" and words:
        return next(piece for piece in sentences(paragraph) if any(word in piece for word in words))
    return sentences(paragraph)[0] if scope == "bullet" else opening(paragraph)


def system_decisions(language: str | None = None) -> list[dict[str, Any]]:
    """D-377: the BSA decisions, each as its title, the parts of its line read from the SQAP and the page that holds the
    rest."""
    decisions = []
    for title, parts, page in SYSTEM_DECISIONS:
        lines = [read_decision_part(part, language) for part in parts]
        labels = [part[3] for part in parts]
        decisions.append({"title": title, "parts": lines, "labels": labels, "line": " ".join(lines), "page": page})
    return decisions


# endregion
