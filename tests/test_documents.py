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
                     "ADR.md": [], "SEGURIDAD.md": ["sop"]}


def test_d248_each_adr_has_the_standard_parts_and_points_to_its_decision():
    text = (DOCS_DIR / "ADR.md").read_text(encoding="utf-8")
    entries = re.split(r"^## ", text, flags=re.MULTILINE)[1:]
    numbers = [entry.split(" ", 1)[0] for entry in entries]
    assert len(numbers) == 10 and len(set(numbers)) == 10 and all(re.fullmatch(r"ADR-\d{2}", n) for n in numbers)
    decisions = (DOCS_DIR / "DECISIONES.md").read_text(encoding="utf-8")
    for entry in entries:
        for part in ("**Estado:**", "**Contexto:**", "**Decisión:**", "**Alternativas:**", "**Consecuencias:**"):
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
    scalability = (DOCS_DIR / "DECISIONES.md").read_text(encoding="utf-8").split("### Escalabilidad", 1)[1]
    assert f"Unos {served:.0f} MB en la base de servicio" in scalability


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
