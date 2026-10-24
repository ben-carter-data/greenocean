"""The PRD says where each question is answered and how each requirement is checked (D-240).

Every screen, test and file the PRD names must exist, so the tables cannot go stale without a test failing.
"""
import re
from pathlib import Path

from bi import dashboard, doc_views, sql_explorer

ROOT = Path(__file__).resolve().parent.parent
PRD = (ROOT / "docs" / "PRD.md").read_text(encoding="utf-8")
REFERENCE = re.compile(r"`([^`]+)`")


def read_table(section):
    """The rows of the table under «## <section>» as lists of cells."""
    body = PRD.split(f"## {section}", 1)[1].split("\n## ", 1)[0]
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in body.splitlines() if line.startswith("|")]
    return rows[2:]  # header and separator


def menu_labels():
    return {dashboard.SIDEBAR_LABELS.get(view, view) for _, _, pages in dashboard.MENU_BLOCKS
            if pages is not dashboard.SOURCE_LINKS for view in pages}


def assert_reference_exists(reference):
    """A file, or a test as tests/file.py::test_name, or a command with a file in it."""
    path, _, test = reference.partition("::")
    if "/" not in path and not path.endswith((".md", ".py", ".yml", ".sql", ".cjs")):
        return  # a value such as a cron expression, not a file
    assert (ROOT / path).exists(), reference
    if test:
        assert re.search(rf"^def {re.escape(test)}\(", (ROOT / path).read_text(encoding="utf-8"), re.MULTILINE), reference


def test_every_business_question_names_a_screen_of_the_menu_and_evidence_that_exists():
    rows = read_table("5. Preguntas de negocio")
    assert [row[0] for row in rows] == ["P-1", "P-2", "P-3", "P-4", "P-5"]
    examples = {title for title, *_ in sql_explorer.EXAMPLES}
    for identifier, question, screen, evidence in rows:
        page, _, example = screen.partition(" · ")
        assert page in menu_labels(), (identifier, page)
        if example:
            assert example in examples, (identifier, example)  # an example query of the SQL studio
        references = REFERENCE.findall(evidence)
        assert references, identifier
        for reference in references:
            assert_reference_exists(reference)


def test_every_requirement_has_a_measurable_criterion_and_evidence_that_exists():
    rows = read_table("6. Requisitos")
    assert [row[0] for row in rows] == [f"RF-0{n}" for n in range(1, 9)] + [f"RNF-0{n}" for n in range(1, 7)]
    for identifier, requirement, criterion, evidence in rows:
        assert criterion and re.search(r"\d|=|≤|Ningún|Ninguna|cada", criterion), identifier
        references = REFERENCE.findall(evidence)
        assert references, identifier
        for reference in references:
            assert_reference_exists(reference)


def test_the_use_cases_follow_the_prd_and_each_points_to_a_real_screen():
    users = {row[0] for row in read_table("4. Usuarios")}
    actors = {actor for actor, *_ in doc_views.USER_CASES}
    assert actors == users  # the four profiles of «3. Usuarios», nothing else
    questions = {row[0]: row for row in read_table("5. Preguntas de negocio")}
    for actor, row, case, identifier, screen in doc_views.USER_CASES + doc_views.SYSTEM_CASES:
        page = screen.partition(" · ")[0]
        assert page in menu_labels() or page == "GitHub, fuera del panel", (case, page)
        if identifier.startswith("P-"):
            assert questions[identifier][2] == screen, identifier  # the same screen as in the table
    assert "administrador" in PRD.lower()
    ids = {identifier for *_, identifier, _ in doc_views.SYSTEM_CASES}
    assert "RF-01 a RF-04" in ids


def test_rf01_the_weekly_workflow_runs_on_tuesdays():
    workflow = (ROOT / ".github" / "workflows" / "semanal.yml").read_text(encoding="utf-8")
    assert re.search(r'cron:\s*"0 12 \* \* 2"', workflow)  # Tuesday, 12:00 UTC
