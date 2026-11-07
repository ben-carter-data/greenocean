"""The PRD says where each question is answered and how each requirement is checked (D-240).

Every screen, test and file the PRD names must exist, so the tables cannot go stale without a test failing.
"""

import re
from pathlib import Path

from bi import business_analysis, dashboard, doc_views, sql_explorer, i18n

# region Constants and variables
ROOT = Path(__file__).resolve().parent.parent
PRD = i18n.document_path("PRD.md", "es").read_text(encoding="utf-8")
REFERENCE = re.compile(r"`([^`]+)`")
# endregion


# region The PRD says where each question is answered and how each requirement is checked
def read_table(section):
    """The rows of the table under «## <n>. <section>» as lists of cells, whatever the number of the section."""
    body = re.split(rf"^## \d+\. {re.escape(section)}$", PRD, flags=re.MULTILINE)[1].split("\n## ", 1)[0]
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in body.splitlines()
        if line.startswith("|")
    ]
    return rows[2:]  # header and separator


def assert_reference_exists(reference):
    """A file, or a test as tests/file.py::test_name, or a command with a file in it."""
    path, _, test = reference.partition("::")
    if "/" not in path and not path.endswith((".md", ".py", ".yml", ".sql", ".cjs")):
        return  # a value such as a cron expression, not a file
    assert (ROOT / path).exists(), reference
    if test:
        assert re.search(rf"^def {re.escape(test)}\(", (ROOT / path).read_text(encoding="utf-8"), re.MULTILINE), (
            reference
        )


def test_every_business_question_names_a_screen_of_the_menu_and_evidence_that_exists():
    rows = read_table("Preguntas de negocio")
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
    rows = read_table("Requisitos")
    # RF-09 since D-357.
    assert [row[0] for row in rows] == [f"RF-0{n}" for n in range(1, 10)] + [f"RNF-0{n}" for n in range(1, 7)]
    for identifier, requirement, criterion, evidence in rows:
        assert criterion and re.search(r"\d|=|≤|Ningún|Ninguna|cada", criterion), identifier
        references = REFERENCE.findall(evidence)
        assert references, identifier
        for reference in references:
            assert_reference_exists(reference)


def test_d455_the_usage_profiles_are_the_three_views_of_the_panel():
    """PRD 3.2 lists the profiles of «Elige tu vista», nothing else: the four invented profiles and their use cases left
    (D-455). Each page it names is a page of the menu."""
    for language, names in (("es", ["Usuario", "Profesional", "Autor"]), ("en", ["User", "Professional", "Author"])):
        rows = business_analysis.read_table(business_analysis.read_section("PRD.md", "3.2", language))
        assert [list(row.values())[0] for row in rows] == names, language
    rows = business_analysis.read_table(business_analysis.read_section("PRD.md", "3.2", "es"))
    named = [name for row in rows for name in re.findall(r"«([^»]+)»", list(row.values())[1])]
    for name in named:
        assert name in menu_labels() or name in ("Negocio · BA y BI", "Acción requerida"), name
    for page in (
        "Semanal",
        "Interesados",
        "Precios e inflación",
        "Insights",
        "Consultas SQL",
    ):
        assert page in rows[0]["Para qué lo usa"] + rows[1]["Para qué lo usa"], page
    assert "administrador" not in PRD.lower() and "| Autor |" in PRD  # D-382: the author is the Autor view
    assert "[[diagrama:casos]]" not in PRD and not hasattr(doc_views, "USER_CASES")


def test_rf01_the_weekly_workflow_runs_on_tuesdays():
    workflow = (ROOT / ".github" / "workflows" / "semanal.yml").read_text(encoding="utf-8")
    # D-487: Tuesday, every 15 minutes until 14:52 UTC, then every hour until 02:07 UTC on Wednesday
    for cron in (r"7,22,37,52 12-14 \* \* 2", r"7 15-23 \* \* 2", r"7 0-2 \* \* 3"):
        assert re.search(rf'cron:\s*"{cron}"', workflow)


def menu_labels():
    """The pages of the menu, and each tab of «Análisis» named «Análisis (Pestaña)» (D-456)."""
    return (
        {
            dashboard.SIDEBAR_LABELS.get(view, view)
            for _, _, pages in dashboard.MENU_BLOCKS
            if pages is not dashboard.SOURCE_LINKS
            for view in pages
        }
        | {dashboard.SIDEBAR_LABELS.get(view, view) for view in dashboard.DOOR_PAGES}
        | {f"{dashboard.PAGE_BA} ({tab})" for tab in dashboard.BA_TABS}
    )


def test_rf08_the_new_weekly_report_closes_the_previous_ones():
    """D-438: one weekly report stays open; the earlier ones are closed after the new one exists, pointing to it."""
    workflow = (ROOT / ".github" / "workflows" / "semanal.yml").read_text(encoding="utf-8")
    step = workflow.split("- name: Publish the weekly report")[1]
    assert step.index('new=$(gh issue create --title "Informe semanal') < step.index("gh issue close")
    assert 'startswith("Informe semanal ")' in step and 'grep -vx "${new##*/}"' in step  # never the new one
    assert '{ grep -vx "${new##*/}" || true; }' in step  # pipefail: no earlier report is not a failure
    assert "Reemplazado por el informe de esta semana: $new" in step
    assert "permissions:\n  contents: write\n  issues: write\n" in workflow  # no new permission


# endregion
