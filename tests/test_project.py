"""Tests for the content of the project page (T-43): documents, SQL, files, examples."""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts, project, queries  # noqa: E402

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


def test_every_decision_of_the_register_is_listed():
    text = project.read_document(project.DECISIONS_FILE)
    assert len(project.list_decisions()) == text.count("\n## D-")
# endregion


# region SQL catalog
def test_clauses_are_detected_only_when_really_used():
    sql = ("-- a comment with JOIN and HAVING\nWITH national AS (SELECT a FROM t)\n"
           "SELECT a, LAG(a) OVER (ORDER BY a) FROM national GROUP BY a")
    assert project.detect_sql_clauses(sql) == ["WITH", "SELECT", "GROUP BY", "ORDER BY",
                                               "Funciones de ventana", "LAG"]
    assert "Subconsultas" in project.detect_sql_clauses("SELECT (SELECT 1) AS one")


def test_catalog_shows_as_many_queries_as_named_in_queries_sql():
    catalog = project.list_named_queries()
    assert [query["name"] for query in catalog] == list(queries.load_queries())


def test_queries_with_a_python_version_carry_its_source():
    catalog = {query["name"]: query for query in project.list_named_queries()}
    assert "def add_usual_range" in "".join(catalog["k6_usual_range_sql"]["python"])
    assert "def add_weekly_variations" in "".join(
        catalog["k5_weekly_variations_sql"]["python"])
    assert catalog["k1_margin"]["python"] == []


@needs_database
@pytest.mark.parametrize("query_name", list(queries.load_queries()))
def test_every_named_query_runs_read_only_with_at_most_20_rows(query_name):
    rows = project.run_preview(queries.load_queries()[query_name])
    assert len(rows) <= project.PREVIEW_ROW_COUNT


@needs_database
def test_explorer_example_runs_with_its_parameters():
    sql, parameters = project.build_explorer_example()
    rows = project.run_preview(sql, parameters)
    assert set(rows["product"]) <= {"Tomate"}
# endregion


# region Files
def list_tracked_files():
    """Files Git keeps, including new ones not committed yet but not ignored."""
    output = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                            cwd=project.PROJECT_DIR, capture_output=True, text=True,
                            check=True).stdout
    return output.splitlines()


def test_every_github_link_points_to_a_file_in_the_repository():
    tracked_files = list_tracked_files()
    for path, _, address in project.list_repository_files():
        if address is None:
            continue
        if path.endswith("/"):
            assert any(tracked.startswith(path) for tracked in tracked_files), path
        else:
            assert path in tracked_files, path


def test_files_kept_out_of_the_repository_have_no_link():
    addresses = {path: address for path, _, address in project.list_repository_files()}
    assert addresses["etl/raw.db"] is None
# endregion


# region KPI examples
@needs_database
def test_k1_example_is_the_margin_formula_on_a_real_row():
    margins = queries.run_query("k1_margin")
    margins["week_start"] = pd.to_datetime(margins["week_start"])
    rows = project.select_example_rows(margins)
    row = rows.loc[rows["week_start"].idxmax()]
    steps = project.build_k1_example(margins)
    expected_margin = (row["consumer_price"] - row["wholesale_price"]) / row["wholesale_price"]
    assert steps[-1].endswith(f"= {charts.format_percent(expected_margin * 100)}.")


@needs_database
def test_k7_example_uses_the_coverage_of_the_database():
    keys_with_margin, consumer_keys = project.read_match_coverage()
    steps = project.build_k7_example(keys_with_margin, consumer_keys)
    assert f"{keys_with_margin} / {consumer_keys}" in steps[-1]


@needs_database
def test_rule_evidence_has_a_sentence_for_each_rule_it_measures():
    evidence = project.read_rule_evidence()
    assert set(evidence) == set(project.RULE_EVIDENCE)
    assert evidence["RN-14"].endswith("0 claves repetidas en weekly_price.")
# endregion
