"""The project documents (D-210, D-248): what each one carries, the figures it states, and the print of its page.

The downloadable document is the page itself printed by the browser (D-248), so the PDF has by construction the same
text, diagrams and order as the page; these tests check the documents and the print stylesheet that makes it so."""
import re
from pathlib import Path

import pytest

from bi import dashboard

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
DOCUMENTS = ["PRD.md", "SAD.md", "ADR.md", "SEGURIDAD.md"]
# The reading documents of the project (D-279): every one has a header, an index, a glossary and a version history.
READING = DOCUMENTS + ["MANUAL.md", "ESCALABILIDAD.md", "PLAN_PRUEBAS.md", "DICCIONARIO_DATOS.md", "GLOSARIO.md",
                      "INDICE_DECISIONES.md"]


@pytest.mark.parametrize("name", DOCUMENTS)
def test_documents_have_no_code_blocks_and_use_the_project_vocabulary(name):
    text = (DOCS_DIR / name).read_text(encoding="utf-8")
    assert "```" not in text and "~~~" not in text
    assert "robot" not in text.lower()


def test_each_document_carries_the_diagrams_its_kind_of_document_needs():
    """PRD: the use cases and the real screens. SAD: its own views, context and containers; the rest is linked (D-247)."""
    names = {name: re.findall(r"^\[\[diagrama:(\w+)\]\]\s*$", (DOCS_DIR / name).read_text(encoding="utf-8"),
                              re.MULTILINE) for name in DOCUMENTS}
    assert names == {"PRD.md": ["casos", "mockups"], "SAD.md": ["contexto", "contenedores"],
                     "ADR.md": [], "SEGURIDAD.md": ["sop", "pruebas"]}
    for name in READING:
        assert not re.findall(r"^\[\[diagrama:", (DOCS_DIR / name).read_text(encoding="utf-8"), re.MULTILINE) \
            or name in DOCUMENTS, name


def test_d248_each_adr_has_the_standard_parts_and_points_to_its_decision():
    text = (DOCS_DIR / "ADR.md").read_text(encoding="utf-8")
    entries = [entry for entry in re.split(r"^## ", text, flags=re.MULTILINE)[1:] if entry.startswith("ADR-")]
    numbers = [entry.split(" ", 1)[0] for entry in entries]
    assert len(numbers) == 11 and len(set(numbers)) == 11 and all(re.fullmatch(r"ADR-\d{2}", n) for n in numbers)
    decisions = (DOCS_DIR / "DECISIONES.md").read_text(encoding="utf-8")
    for entry in entries:
        for part in ("**Estado:**", "**Fecha:**", "**Contexto:**", "**Decisión:**", "**Opciones consideradas:**",
                     "**Consecuencias:**"):
            assert part in entry, (entry[:8], part)
        cited = re.findall(r"D-\d{3}", entry.split("**Estado:**", 1)[1].split("\n", 1)[0])
        assert cited, entry[:8]
        for decision in cited:
            assert f"## {decision} " in decisions, decision


def test_d248_the_file_sizes_the_documents_state_are_the_real_ones():
    adr = (DOCS_DIR / "ADR.md").read_text(encoding="utf-8")
    largest = max((path.stat().st_size for path in (ROOT / "agent" / "downloads").glob("*.csv")), default=None)
    if largest:
        assert f"hasta unos {round(largest / 5e6) * 5} MB" in adr  # rounded to 5 MB
    served = (ROOT / "etl" / "datos.duckdb").stat().st_size / 1e6
    scalability = (DOCS_DIR / "ESCALABILIDAD.md").read_text(encoding="utf-8")
    assert f"Unos {served:.0f} MB en la base servida" in scalability


def test_d248_the_print_stylesheet_keeps_the_document_and_drops_only_the_navigation():
    css = dashboard.PRINT_DOCUMENT_CSS
    assert "@media print" in css and "print-color-adjust: exact" in css
    hidden = css.split("{ display: none !important; }")[0]
    for chrome in ('[data-testid="stSidebar"]', ".st-key-app_header", ".st-key-doc_actions", ".st-key-compact_footer"):
        assert chrome in hidden, chrome
    for content in ("project_document", "stIFrame", "h2", "table"):
        assert content not in hidden, content  # the document, its diagrams, headings and tables always print
    assert "overflow: visible" in css and "height: auto" in css  # the whole page runs on, not only the first screen
    assert "window.print()" in dashboard.PRINT_BUTTON_HTML and "<" not in dashboard.PRINT_BUTTON_HTML.split("<script>")[1].split("</script>")[0]


def test_d210_the_prd_figures_match_the_served_database():
    import duckdb
    text = (DOCS_DIR / "PRD.md").read_text(encoding="utf-8")
    database = Path(__file__).resolve().parent.parent / "etl" / "datos.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        prices, weeks = connection.execute("SELECT count(*), count(DISTINCT week_start) FROM weekly_price").fetchone()
        read, loaded, rejected = connection.execute(
            "SELECT rows_read, rows_loaded, rows_rejected FROM etl_run ORDER BY run_id DESC LIMIT 1").fetchone()
        products = connection.execute("SELECT count(*) FROM dim_product").fetchone()[0]
        months = connection.execute("SELECT count(*) FROM ipc_monthly").fetchone()[0]
    for value, unit in ((prices, "precios semanales"), (weeks, "semanas"), (products, "claves de producto"),
                        (months, "meses del IPC")):
        assert f"{value:,}".replace(",", ".") + " " + unit in text, unit
    for value in (read, loaded, rejected):
        assert f"{value:,}".replace(",", ".") in text


def test_d252_the_glossary_names_only_pages_and_tabs_that_exist():
    menu = {dashboard.SIDEBAR_LABELS.get(view, view) for view in dashboard.MENU_ORDER}
    tabs = {"Operación", "Despliegue", "CI/CD", "Monitoreo"}
    text = (DOCS_DIR / "GLOSARIO.md").read_text(encoding="utf-8")
    table = text[text.index("| Sigla o término"):].split("\n\n", 1)[0]
    rows = [line.split(" | ") for line in table.splitlines()[2:] if line.startswith("| ")]
    assert len(rows) > 20
    for row in rows:
        for place in [] if row[2] == "—" else row[2].split(", "):
            page, _, tab = place.partition(" (")
            assert page in menu, f"{row[0]}: «{page}» is not a page of the menu"
            assert not tab or tab.rstrip(")") in tabs, f"{row[0]}: «{tab}» is not a tab"


def test_d252_the_security_plan_counts_the_attacks_its_tests_run():
    from bi import security_plan
    from tests import test_security
    attacks = {case[0]: case[2] for case in security_plan.CASES}
    assert attacks["S-01"].startswith(f"{len(test_security.FILE_ATTACKS)} consultas SQL")
    assert attacks["S-02"].startswith(f"{len(test_security.ENGINE_ATTACKS)} órdenes directas")


def test_d269_the_documents_count_the_quality_indicators_and_dimensions_the_panel_measures():
    from bi import quality_live, quality_view
    from tests.test_quality_audit import EVIDENCE
    indicators = quality_live.build_indicators(quality_live.read_measures())
    # D-279: the dbt tests count with consistency, as in the panel; accuracy is the sixth dimension, measured by controls.
    count = len(indicators)
    dimensions = len({"consistencia" if row[0] == "pruebas" else row[0] for row in indicators})
    controls = len(dict(quality_view.build_columns(EVIDENCE))[quality_live.RESULTS_STEP])
    words = {4: "cuatro", 5: "cinco", 6: "seis", 11: "Once"}
    sad = (DOCS_DIR / "SAD.md").read_text(encoding="utf-8")
    assert f"{words[count]} indicadores, en {words[dimensions]} dimensiones" in sad
    assert f"la sexta dimensión, se mide con {words[controls]} controles" in sad
    assert f"los {count} indicadores de calidad" in (DOCS_DIR / "PRD.md").read_text(encoding="utf-8")


def test_d269_the_documents_say_where_a_failed_load_is_recorded():
    """A failed load stops before the commit: etl_run keeps only published loads, GitHub Actions keeps the failures."""
    for name in ("PRD.md", "ADR.md"):
        text = (DOCS_DIR / name).read_text(encoding="utf-8")
        assert "queda registrada como fallida" not in text, name
        assert "avisa al autor por correo" in text, name


# D-279: forms that do not belong in a professional document.
FORBIDDEN = [r"\bprompt\b", r"de verdad", r"\bTODO\b", r"lorem", r"\bnota:", r"como pidió", r"para el autor",
             r"\bClaude\b", r"\btú\b", r"\bvos\b", r"esto se hizo para"]


@pytest.mark.parametrize("name", READING)
def test_d279_every_reading_document_is_written_as_a_professional_document(name):
    text = (DOCS_DIR / name).read_text(encoding="utf-8")
    for pattern in FORBIDDEN:
        assert not re.search(pattern, text, re.IGNORECASE if pattern != r"\bTODO\b" else 0), (name, pattern)
    assert "```" not in text and "robot" not in text.lower()


@pytest.mark.parametrize("name", READING)
def test_d279_every_reading_document_has_its_header_index_glossary_and_history(name):
    text = (DOCS_DIR / name).read_text(encoding="utf-8")
    header = text.split("## ", 1)[0]
    for field in ("Proyecto", "Tipo de documento", "Versión", "Fecha", "Estado", "Responsable", "Propósito", "Audiencia",
                  "Documentos relacionados"):
        assert f"| {field} |" in header, (name, field)
    assert "| Responsable | El autor |" in header
    assert "## Índice" in text and "Historial de versiones" in text
    assert name == "GLOSARIO.md" or "[Glosario](GLOSARIO.md)" in text
    # The version and date of the header are those of the last row of the history.
    version = re.search(r"\| Versión \| ([\d.]+) \|", header).group(1)
    date = re.search(r"\| Fecha \| (\d{2}-\d{2}-\d{4}) \|", header).group(1)
    history = text.split("Historial de versiones")[-1]
    last = re.findall(r"^\| ([\d.]+) \| (\d{2}-\d{2}-\d{4}) \|", history, re.MULTILINE)[-1]
    assert last == (version, date), name


@pytest.mark.parametrize("name", READING)
def test_d279_every_index_entry_points_to_a_heading_and_every_link_to_a_document_that_exists(name):
    from bi import dashboard
    text = (DOCS_DIR / name).read_text(encoding="utf-8")
    anchors = {dashboard.heading_anchor(heading) for heading in re.findall(r"^#{2,4} (.+)$", text, re.MULTILINE)}
    index = text.split("## Índice", 1)[1].split("\n## ", 1)[0]
    for target in re.findall(r"\]\(#([^)]+)\)", index):
        assert target in anchors, (name, target)
    for filename, anchor in re.findall(r"\]\(([A-Z_]+\.md)(?:#([^)]+))?\)", text):
        other = DOCS_DIR / filename
        assert other.exists(), (name, filename)
        if anchor:
            headings = re.findall(r"^#{2,4} (.+)$", other.read_text(encoding="utf-8"), re.MULTILINE)
            assert anchor in {dashboard.heading_anchor(heading) for heading in headings}, (name, filename, anchor)


def test_d279_the_history_dates_are_dates_the_file_really_changed():
    import subprocess
    from datetime import date
    shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT, capture_output=True, text=True)
    if shallow.stdout.strip() != "false":
        pytest.skip("the history is not here (a shallow clone)")
    for name in DOCUMENTS + ["MANUAL.md"]:
        log = subprocess.run(["git", "log", "--follow", "--date=short", "--format=%ad", "--", f"docs/{name}"], cwd=ROOT,
                             capture_output=True, text=True).stdout.split()
        changed = {"-".join(reversed(day.split("-"))) for day in log} | {date.today().strftime("%d-%m-%Y")}
        history = (DOCS_DIR / name).read_text(encoding="utf-8").split("Historial de versiones")[-1]
        for day in re.findall(r"^\| [\d.]+ \| (\d{2}-\d{2}-\d{4}) \|", history, re.MULTILINE):
            assert day in changed, (name, day)


def test_d279_the_security_plan_carries_the_threats_and_cases_of_the_code():
    from bi import security_map, security_plan
    text = (DOCS_DIR / "SEGURIDAD.md").read_text(encoding="utf-8")
    for identifier, title, owasp, *_ in security_map.THREATS:
        assert f"| {identifier} | {title} | {owasp} |" in text, identifier
    for identifier, name, attack, expected, owasp, tests in security_plan.CASES:
        row = next(line for line in text.splitlines() if line.startswith(f"| {identifier} |"))
        assert name in row and attack in row and owasp in row, identifier
        assert all(test in row for test in tests), identifier


def test_d279_the_data_dictionary_describes_every_table_and_column_of_the_served_database():
    import duckdb
    from bi import queries
    if not queries.DATABASE_FILE.exists():
        pytest.skip("datos.duckdb is not here")
    text = (DOCS_DIR / "DICCIONARIO_DATOS.md").read_text(encoding="utf-8")
    with duckdb.connect(str(queries.DATABASE_FILE), read_only=True) as connection:
        columns = connection.execute("SELECT table_name, column_name, data_type FROM information_schema.columns "
                                     "WHERE table_schema = 'main'").fetchall()
    tables = {table for table, *_ in columns}
    documented = set(re.findall(r"^### (\w+)$", text, re.MULTILINE))
    assert documented == tables
    for table, column, data_type in columns:
        section = text.split(f"### {table}\n", 1)[1].split("\n### ", 1)[0]
        assert f"| `{column}` | {data_type} |" in section, (table, column)
