"""Tests for the content of the project page (T-43): documents, SQL, files, examples."""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import requests
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import project, queries  # noqa: E402
from etl import etl  # noqa: E402

needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(),
                                    reason="etl/datos.db has not been built")


# region Documents
def test_markdown_table_keeps_escaped_pipes_inside_a_cell():
    rows = project.parse_markdown_table("| ID | Regla |\n|---|---|\n| RN-02 | usa `\\|` |\n")
    assert rows == [{"ID": "RN-02", "Regla": "usa `|`"}]


def test_design_document_gives_14_rules_8_indicators_and_6_questions():
    assert [row["ID"] for row in project.read_design_table(project.RULES_HEADING)] == [
        f"RN-{number:02d}" for number in range(1, 15)]
    assert [row["ID"] for row in project.read_design_table(project.INDICATORS_HEADING)] == [
        f"K{number}" for number in range(1, 9)]
    assert len(project.read_design_table(project.QUESTIONS_HEADING)) == 6


def test_project_guide_explains_every_rule_indicator_and_table():
    rules = {row["Regla"] for row in project.read_guide_table("Reglas de calidad")}
    assert rules == {f"RN-{number:02d}" for number in range(1, 15)}
    assert {row["KPI"] for row in project.read_guide_table("KPI")} == {
        f"K{number}" for number in range(1, 9)}
    definitions = project.parse_definitions(project.read_section(
        project.read_document(project.PROJECT_GUIDE_FILE), "Modelo de datos"))
    assert set(definitions) == set(project.TABLE_NAMES)


# endregion


# endregion


# region Files
def list_tracked_files():
    """Files Git keeps, including new ones not committed yet but not ignored."""
    output = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                            cwd=project.PROJECT_DIR, capture_output=True, text=True,
                            check=True).stdout
    return output.splitlines()


# endregion


@needs_database
def test_rule_evidence_has_a_sentence_for_each_rule_it_measures():
    evidence = project.read_rule_evidence()
    assert set(evidence) == set(project.RULE_EVIDENCE)
    assert evidence["RN-14"].endswith("0 claves repetidas en weekly_price.")
# endregion


# region Project links (T-54)
def test_t54_project_links_have_the_agreed_names_and_hide_what_does_not_exist():
    names = [link["name"] for link in project.PROJECT_LINKS]
    # Names shortened (D-116): the page itself is titled «GitHub» and each GitHub
    # link now carries the real brand mark, so the words «en GitHub» / «Ver» /
    # «Abrir» no longer need repeating on every single link. «Código» is retired
    # (the repo-header strip already opens it) and ODEPA moved to its own sidebar
    # folder, «Fuentes» (D-118).
    assert names == ["GitHub Actions", "Informes semanales", "Historial de cambios",
                     "MANUAL", "DECISIONES", "Video", "Post de LinkedIn"]
    for link in project.PROJECT_LINKS:
        assert link["description"] and link["icon"]
    unpublished = {link["name"] for link in project.PROJECT_LINKS if not link["url"]}
    assert unpublished == {"Video", "Post de LinkedIn"}


@pytest.mark.parametrize("link", [link for link in project.PROJECT_LINKS if link["url"]],
                         ids=lambda link: link["name"])
def test_t54_every_public_link_answers(link):
    try:
        response = requests.get(link["url"], timeout=20, allow_redirects=True,
                                headers={"User-Agent": "monitor-precios-tests"})
    except requests.ConnectionError:
        pytest.skip("no network")
    assert response.status_code < 400, f"{link['name']}: {response.status_code}"
# endregion


def test_d054_real_figures_of_the_devops_diagram(tmp_path):
    (tmp_path / "test_one.py").write_text("x = 1\n\ndef test_a():\n    pass\n\n\n"
                                          "def test_b():\n    pass\n", encoding="utf-8")
    (tmp_path / "helper.py").write_text("\ndef test_not_counted():\n    pass\n",
                                        encoding="utf-8")
    assert project.count_test_functions(tmp_path) == 2
    sized = tmp_path / "datos.db"
    sized.write_bytes(b"0" * 33_900_000)
    assert project.describe_file_size(sized) == "33,9 MB"


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="etl/datos.db has not been built")
def test_d054_week_prices_match_the_rows_of_that_week():
    connection = queries.open_database()
    rows = pd.read_sql_query("SELECT week_start FROM weekly_price", connection)
    connection.close()
    latest_week = rows["week_start"].max()
    assert project.count_week_prices(latest_week) == (rows["week_start"] == latest_week).sum()
    assert project.count_week_prices("1999-01-04") == 0


def test_d057_labeled_items_and_closing_paragraph_come_from_the_document():
    section = project.read_section(project.read_document(project.PROJECT_GUIDE_FILE),
                                   "Fuentes y cruces")
    assert [label for label, _ in project.parse_labeled_items(section)] == [
        "Precios mayoristas", "Precios al consumidor"]
    assert [label for label, _ in project.parse_labeled_items(section, numbered=True)] == [
        "Nombres", "Unidades", "Tiempo"]
    assert project.read_closing_paragraph(section).startswith("Solo hay margen")


def test_d057_every_term_of_the_manual_is_in_the_glossary_of_the_panel():
    """The panel shows the terms once, in Inicio › Glosario."""
    glossary = " ".join(f"{row['Sigla o término']} {row['Significado']}"
                        for row in project.read_guide_table("Glosario")).lower()
    manual_terms = project.parse_markdown_table(project.read_section(
        project.read_document(project.MANUAL_FILE), "Glosario"))
    for row in manual_terms:
        first_word = row["Término"].split(" / ")[0].split(" (")[0]
        assert first_word.lower() in glossary, first_word
    assert all(row["Tema"] for row in project.read_guide_table("Glosario"))
