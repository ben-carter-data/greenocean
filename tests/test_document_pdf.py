"""PRD, SAD and ADR as downloadable PDF files (step 6 of the refonte)."""
import base64
import re
import zlib
from datetime import date
from pathlib import Path

import pytest

from bi import document_pdf

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DOCUMENTS = {
    "PRD.md": ("Documento de requisitos del producto", "PRD · Qué resuelve, para quién y cómo se verifica"),
    "SAD.md": ("Documento de arquitectura de software", "SAD · Contexto, contenedores, componentes y linaje"),
    "ADR.md": ("Registros de decisiones de arquitectura", "ADR · Una ficha por decisión"),
    "SEGURIDAD.md": ("Plan de pruebas de seguridad", "Puertas, barreras y pruebas"),
}


def count_pages(pdf_bytes):
    return len(re.findall(rb"/Type /Page[^s]", pdf_bytes))


def page_text(pdf_bytes):
    """The drawn text of every page: reportlab's content streams, ASCII85 then Flate."""
    texts = []
    for stream in re.findall(rb"stream\r?\n(.*?)\s*endstream", pdf_bytes, re.DOTALL):
        data = stream.strip()
        try:
            if data.endswith(b"~>"):
                data = base64.a85decode(data[:-2])
            texts.append(zlib.decompress(data).decode("latin-1"))
        except (ValueError, zlib.error):
            continue  # fonts and images
    return "\n".join(texts)


@pytest.fixture(scope="module")
def pdfs():
    return {name: document_pdf.build_pdf((DOCS_DIR / name).read_text(encoding="utf-8"), title, subtitle,
                                         issued=date(2026, 10, 19))
            for name, (title, subtitle) in DOCUMENTS.items()}


@pytest.mark.parametrize("name", DOCUMENTS)
def test_d210_each_document_fits_two_pages_with_its_title_band(pdfs, name):
    pdf = pdfs[name]
    assert pdf.startswith(b"%PDF")
    assert 1 <= count_pages(pdf) <= 2
    text = page_text(pdf)
    assert "GREENOCEAN" in text and "Contenido" not in text and "19 de octubre de 2026" in text
    assert f"de {count_pages(pdf)})" in text  # «Página n de N» in the footer


@pytest.mark.parametrize("name", DOCUMENTS)
def test_markdown_never_leaks_into_the_pdf(pdfs, name):
    text = page_text(pdfs[name])
    drawn = " ".join(re.findall(r"\((.*?)\) Tj", text))
    assert drawn, "the PDF should draw text"
    assert "|" not in drawn and "**" not in drawn and "`" not in drawn and "[[diagrama" not in drawn


def test_diagram_markers_become_a_note():
    pdf = document_pdf.build_pdf("# T\n\n## Uno\n\nTexto.\n\n[[diagrama:pipeline]]\n", "T", "S")
    assert document_pdf.DIAGRAM_NOTE in page_text(pdf)


def test_tables_lists_and_inline_marks_are_parsed():
    blocks = document_pdf.parse_blocks(
        "## Título\n\n| A | B |\n|---|---|\n| **x** | `y` |\n\n- uno\n- dos\n\n1. tres\n\nTexto *suave*.")
    kinds = [kind for kind, _ in blocks]
    assert kinds == ["heading", "table", "bullets", "numbers", "paragraph"]
    assert blocks[1][1] == (["A", "B"], [["**x**", "`y`"]])
    markup = document_pdf.inline_markup("**negrita**, *cursiva* y `código` con 10⁻¹² y 3 − 1 < 4")
    assert "<b>negrita</b>" in markup and "<i>cursiva</i>" in markup and 'name="Courier"' in markup
    assert "<super>-12</super>" in markup and "&lt;" in markup and "−" not in markup


def test_build_pdf_does_not_depend_on_streamlit():
    source = Path(document_pdf.__file__).read_text(encoding="utf-8")
    assert "streamlit" not in source


@pytest.mark.parametrize("name", DOCUMENTS)
def test_documents_have_no_code_blocks_and_use_the_project_vocabulary(name):
    text = (DOCS_DIR / name).read_text(encoding="utf-8")
    assert "```" not in text and "~~~" not in text
    assert "robot" not in text.lower()


def test_each_document_carries_the_diagrams_its_kind_of_document_needs():
    """PRD: actors and the real screens. SAD: only the live diagrams (D-210). ADR: none."""
    names = {name: re.findall(r"^\[\[diagrama:(\w+)\]\]\s*$", (DOCS_DIR / name).read_text(encoding="utf-8"),
                              re.MULTILINE) for name in DOCUMENTS}
    assert names == {"PRD.md": ["actores", "mockups"], "SAD.md": ["pipeline", "plataforma", "modelo"],
                     "ADR.md": [], "SEGURIDAD.md": ["seguridad"]}


def test_d205_the_prd_pdf_carries_the_four_real_screens():
    pdf = document_pdf.build_pdf((DOCS_DIR / "PRD.md").read_text(encoding="utf-8"), "PRD", "x")
    assert pdf.count(b"/Subtype /Image") >= 4


def test_d210_the_adr_is_one_table_of_the_ten_decisions_that_weigh_most():
    text = (DOCS_DIR / "ADR.md").read_text(encoding="utf-8")
    assert "| ADR | Decisión | Motivo | Alternativa descartada |" in text
    rows = re.findall(r"^\| (ADR-\d+) \|(.*)\|$", text, flags=re.MULTILINE)
    assert len(rows) == 10 and len({number for number, _ in rows}) == 10
    for number, row in rows:
        assert len(row.split("|")) == 3 and all(cell.strip() for cell in row.split("|")), number
        assert re.search(r"D-\d{3}", row), number


def test_d210_the_prd_figures_match_the_served_database():
    import duckdb
    text = (DOCS_DIR / "PRD.md").read_text(encoding="utf-8")
    database = Path(__file__).resolve().parent.parent / "etl" / "datos.duckdb"
    with duckdb.connect(str(database), read_only=True) as connection:
        prices, weeks = connection.sql("SELECT count(*), count(DISTINCT week_start) FROM weekly_price").fetchone()
        read, loaded, rejected = connection.sql(
            "SELECT rows_read, rows_loaded, rows_rejected FROM etl_run ORDER BY run_id DESC LIMIT 1").fetchone()
        products = connection.sql("SELECT count(*) FROM dim_product").fetchone()[0]
        months = connection.sql("SELECT count(*) FROM ipc_monthly").fetchone()[0]
    for value, unit in ((prices, "precios semanales"), (weeks, "semanas"), (products, "claves de producto"),
                        (months, "meses del IPC")):
        assert f"{value:,}".replace(",", ".") + " " + unit in text, unit
    for value in (read, loaded, rejected):
        assert f"{value:,}".replace(",", ".") in text
