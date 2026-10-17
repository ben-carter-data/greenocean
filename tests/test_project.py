"""Tests for the content of the project page (T-43): documents, SQL, files, examples."""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import requests
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts, project, queries  # noqa: E402
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


def test_t57_level_is_the_highest_one_of_the_clauses_detected():
    simple = project.describe_query("SELECT a, COUNT(*) FROM t WHERE b = 1 GROUP BY a")
    assert (simple["level"], simple["level_reasons"]) == (project.LEVEL_SIMPLE, [])
    assert "Agregados" in simple["clauses"]
    dated = project.describe_query("SELECT strftime('%Y', week_start) FROM t")
    assert (dated["level"], dated["level_reasons"]) == (project.LEVEL_INTERMEDIATE,
                                                        ["Funciones de fecha"])
    grouped = project.describe_query("SELECT a FROM t JOIN u ON u.a = t.a GROUP BY a "
                                     "HAVING COUNT(*) > 2")
    assert (grouped["level"], grouped["level_reasons"]) == (project.LEVEL_ADVANCED, ["HAVING"])
    reconciled = project.describe_query("SELECT a FROM t", has_python_version=True)
    assert reconciled["level_reasons"] == [project.PYTHON_RECONCILIATION]


def test_t57_auto_join_needs_the_same_table_under_two_aliases():
    assert "Auto-join" in project.detect_sql_clauses(
        "SELECT 1 FROM price AS consumer JOIN price AS wholesale ON 1 = 1")
    assert "Auto-join" not in project.detect_sql_clauses(
        "SELECT 1 FROM price AS consumer JOIN dim_product AS product ON 1 = 1")
    assert "Auto-join" not in project.detect_sql_clauses(
        "WITH n AS (SELECT a FROM price) SELECT 1 FROM price JOIN n ON 1 = 1")


def test_t57_every_named_query_is_in_exactly_the_group_of_its_level():
    named_count = queries.QUERIES_FILE.read_text(encoding="utf-8").count("\n-- name: ")
    catalog = project.list_named_queries()
    groups = project.group_queries_by_level(catalog)
    assert list(groups) == [project.LEVEL_SIMPLE, project.LEVEL_INTERMEDIATE,
                            project.LEVEL_ADVANCED]
    grouped_names = [query["name"] for group in groups.values() for query in group]
    assert sorted(grouped_names) == sorted(queries.load_queries())
    assert len(grouped_names) == named_count
    for level, group in groups.items():
        assert all(query["level"] == level for query in group)
    # The two queries checked against Python are the advanced ones (D-049).
    assert {query["name"] for query in groups[project.LEVEL_ADVANCED]} == set(
        project.PYTHON_VERSIONS)


@needs_database
def test_t57_k7_query_of_the_etl_runs_read_only():
    rows = project.run_preview(etl.MATCH_COVERAGE_QUERY)
    assert 0 < len(rows) <= project.PREVIEW_ROW_COUNT


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


# region Project links (T-54)
def test_t54_project_links_have_the_agreed_names_and_hide_what_does_not_exist():
    names = [link["name"] for link in project.PROJECT_LINKS]
    # Names shortened (D-116): the page itself is titled «GitHub» and each GitHub
    # link now carries the real brand mark, so the words «en GitHub» / «Ver» /
    # «Abrir» no longer need repeating on every single link.
    assert names == ["Código", "Ejecuciones", "Informes semanales", "Historial de cambios",
                     "ODEPA: precios mayoristas", "ODEPA: precios al consumidor",
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
