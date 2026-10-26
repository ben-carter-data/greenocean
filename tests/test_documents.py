"""The project documents (D-210, D-248): what each one carries, the figures it states, and the print of its page.

The downloadable document is the page itself printed by the browser (D-248), so the PDF has by construction the same
text, diagrams and order as the page; these tests check the documents and the print stylesheet that makes it so."""
import re
from pathlib import Path

import pytest

from bi import dashboard

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
DOCUMENTS = ["PRD.md", "SAD.md", "ADR.md", "PLAN_PRUEBAS.md"]
# The reading documents of the project (D-279): every one has a header, an index, a glossary and a version history.
# D-290: the scalability plan and the data dictionary live in the SAD; the security plan, in the test plan.
READING = DOCUMENTS + ["MANUAL.md", "GLOSARIO.md", "INDICE_DECISIONES.md"]
MERGED = {"PLAN_PRUEBAS.md": ["SEGURIDAD.md"], "SAD.md": ["ESCALABILIDAD.md", "DICCIONARIO_DATOS.md"]}


@pytest.mark.parametrize("name", DOCUMENTS)
def test_documents_have_no_code_blocks_and_use_the_project_vocabulary(name):
    text = (DOCS_DIR / name).read_text(encoding="utf-8")
    assert "```" not in text and "~~~" not in text
    assert "robot" not in text.lower()


def test_each_document_carries_the_diagrams_its_kind_of_document_needs():
    """D-290: every document, in its reading order, with at least three diagrams; the SAD with at least five."""
    names = {name: re.findall(r"^\[\[diagrama:(\w+)\]\]\s*$", (DOCS_DIR / name).read_text(encoding="utf-8"),
                              re.MULTILINE) for name in READING}
    assert names == {
        "PRD.md": ["valor", "casos", "requisitos", "mockups"],
        "SAD.md": ["contexto", "escenarios", "contenedores", "componentes_carga", "componentes_panel", "secuencia_carga",
                   "secuencia_panel", "capas", "despliegue"],
        "ADR.md": ["mapa_adr", "tiempo_adr", "antes_despues"],
        "PLAN_PRUEBAS.md": ["niveles", "actores", "pruebas", "sop", "secuencia_manual", "secuencia_ci"],
        "MANUAL.md": ["calendario", "arbol_fallas", "secuencia_recuperacion"],
        "GLOSARIO.md": ["terminos_cifra", "terminos_capas", "terminos_actores"],
        "INDICE_DECISIONES.md": ["temas", "mapa_temas", "adr_decisiones"]}
    for name, markers in names.items():
        assert len(markers) >= (5 if name == "SAD.md" else 3) and len(set(markers)) == len(markers), name
    assert {marker for markers in names.values() for marker in markers} <= set(dashboard.doc_diagrams.DOC_DIAGRAMS)


def test_d290_the_merged_documents_are_gone_and_their_addresses_open_the_document_that_holds_them():
    for name, old in MERGED.items():
        for gone in old:
            assert not (DOCS_DIR / gone).exists() and not (DOCS_DIR / "en" / gone).exists(), gone
    assert len(dashboard.FOLDER_DOCUMENTS) == 7
    for path, page in (("escalabilidad", dashboard.PAGE_SAD), ("diccionario-de-datos", dashboard.PAGE_SAD),
                       ("plan-de-pruebas-de-seguridad", dashboard.PAGE_TEST_PLAN)):
        assert dashboard.OLD_PATHS[path] == (page, None)
    for title, page in (("Escalabilidad", dashboard.PAGE_SAD), ("Diccionario de datos", dashboard.PAGE_SAD),
                        ("Plan de pruebas de seguridad", dashboard.PAGE_TEST_PLAN),
                        ("Plan de pruebas", dashboard.PAGE_TEST_PLAN)):
        assert dashboard.RETIRED_VIEWS[title] == page


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
    sad = (DOCS_DIR / "SAD.md").read_text(encoding="utf-8")
    # D-299: the base grows a little every Tuesday; the round size of the SAD holds within 2 MB, so no load stops on it.
    stated = int(re.search(r"Unos (\d+) MB en la base servida", sad)[1])
    assert abs(stated - served) <= 2, (stated, served)


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
        # D-299: the PRD states the figures of one dated load; a newer load (every Tuesday) must never fail on that text,
        # or pytest in semanal.yml stops the publication. The figures are compared when the database is that load.
        stated = re.search(r"Con la carga del (\d{2})-(\d{2})-(\d{4})", text)
        assert stated, "the PRD names the load its figures come from"
        last = connection.execute("SELECT started_at FROM etl_run ORDER BY run_id DESC LIMIT 1").fetchone()[0]
        if last[:10] != f"{stated[3]}-{stated[2]}-{stated[1]}":
            pytest.skip(f"the database holds a newer load ({last[:10]}) than the one the PRD states")
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
    menu = {dashboard.SIDEBAR_LABELS.get(view, view) for view in [*dashboard.MENU_ORDER, *dashboard.DOOR_PAGES]}
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
        log = []
        for source in [name] + MERGED.get(name, []):  # a merged document keeps the history of the ones it absorbed
            log += subprocess.run(["git", "log", "--follow", "--date=short", "--format=%ad", "--", f"docs/{source}"],
                                  cwd=ROOT, capture_output=True, text=True).stdout.split()
        changed = {"-".join(reversed(day.split("-"))) for day in log} | {date.today().strftime("%d-%m-%Y")}
        history = (DOCS_DIR / name).read_text(encoding="utf-8").split("Historial de versiones")[-1]
        for day in re.findall(r"^\| [\d.]+ \| (\d{2}-\d{2}-\d{4}) \|", history, re.MULTILINE):
            assert day in changed, (name, day)


def test_d279_the_security_plan_carries_the_threats_and_cases_of_the_code():
    from bi import security_map, security_plan
    text = (DOCS_DIR / "PLAN_PRUEBAS.md").read_text(encoding="utf-8")
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
    text = (DOCS_DIR / "SAD.md").read_text(encoding="utf-8")
    with duckdb.connect(str(queries.DATABASE_FILE), read_only=True) as connection:
        columns = connection.execute("SELECT table_name, column_name, data_type FROM information_schema.columns "
                                     "WHERE table_schema = 'main'").fetchall()
    tables = {table for table, *_ in columns}
    documented = set(re.findall(r"^### (\w+)$", text, re.MULTILINE))
    assert documented == tables
    for table, column, data_type in columns:
        section = text.split(f"### {table}\n", 1)[1].split("\n### ", 1)[0]
        assert f"| `{column}` | {data_type} |" in section, (table, column)


# D-288: each document opens with its cover, read from its header table.
@pytest.mark.parametrize("name", READING)
def test_d288_each_document_has_a_cover_with_its_version_date_status_owner_and_audience(name):
    from bi import documents_folder
    text = (DOCS_DIR / name).read_text(encoding="utf-8")
    cover = documents_folder.build_cover_html(text, "")
    header = documents_folder.read_header(text)
    for field in ("Versión", "Fecha", "Estado", "Responsable"):
        assert f"<dd>{header[field]}</dd>" in cover.replace("&#x27;", "'"), (name, field)
    assert header["Audiencia"] in cover
    assert documents_folder.read_title(text) in cover
    assert "| Campo |" not in documents_folder.strip_header_table(text)


def test_adr04_the_raw_data_is_not_in_git():
    import subprocess
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert not [path for path in tracked if path.endswith(".csv") and path.startswith("agent/downloads/")]
    assert "etl/raw.db" not in tracked and "etl/datos.duckdb" not in tracked


def test_adr31_no_cloud_warehouse_is_a_dependency():
    """ADR-31: the served database is a DuckDB file; a cloud warehouse is only a commented option of dbt."""
    for path in ("requirements.txt", "requirements-pipeline.txt"):
        text = (ROOT / path).read_text(encoding="utf-8").lower()
        for cloud in ("bigquery", "snowflake", "redshift", "databricks"):
            assert cloud not in text, (path, cloud)
    active = [line for line in (ROOT / "dbt" / "profiles.yml").read_text(encoding="utf-8").splitlines()
              if "type:" in line and not line.strip().startswith("#")]
    assert active and all("duckdb" in line for line in active)


def test_d300_each_adr_names_the_test_that_confirms_it_and_the_test_exists():
    for name, word in (("ADR.md", "**Confirmación:**"), ("en/ADR.md", "**Confirmation:**")):
        text = (DOCS_DIR / name).read_text(encoding="utf-8")
        entries = [entry for entry in re.split(r"^## ", text, flags=re.MULTILINE)[1:] if entry.startswith("ADR-")]
        assert len(entries) == 11
        for entry in entries:
            line = next(line for line in entry.splitlines() if word in line)
            path, test = re.search(r"`([^`]+)::([^`]+)`", line).groups()
            assert re.search(rf"^def {re.escape(test)}\(", (ROOT / path).read_text(encoding="utf-8"), re.MULTILINE), (entry[:6], test)
