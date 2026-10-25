"""D-283: Spanish and English for the whole panel and its documents."""
import re
from collections import Counter
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import dashboard, documents_folder, i18n

ROOT = Path(__file__).resolve().parent.parent
BI_DIR = ROOT / "bi"
DOCS_DIR = ROOT / "docs"
EN_DIR = DOCS_DIR / "en"
DASHBOARD_FILE = str(BI_DIR / "dashboard.py")
FOLDER_FILES = [dashboard.PROJECT_DOCUMENTS[page][0] for page in dashboard.FOLDER_ORDER]
TR_CALL = re.compile(r"""\btr\(\s*(?:f?"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)')\s*\)""")
IDENTIFIER = re.compile(r"\b(?:RF|RNF|P|ADR|S|D|RN|K)-\d+\b|\bT\d\b")
ENGLISH_FIELDS = ("Project", "Document type", "Version", "Date", "Status", "Owner", "Purpose", "Audience",
                  "Related documents")


def read(path):
    return path.read_text(encoding="utf-8")


def test_d283_every_text_given_to_tr_has_its_english():
    missing = []
    for path in BI_DIR.glob("*.py"):
        for double, single in TR_CALL.findall(read(path)):
            text = (double or single).replace('\\"', '"')
            if "{" in text and text not in i18n.EN:
                continue  # an f-string: its parts are checked where they are built
            if text not in i18n.EN:
                missing.append((path.name, text))
    assert not missing, missing
    assert all(isinstance(value, str) and value.strip() for value in i18n.EN.values())


def test_d283_the_menu_the_documents_and_the_frame_have_their_english():
    texts = {title for _, title, _ in dashboard.MENU_BLOCKS}
    texts |= {dashboard.SIDEBAR_LABELS.get(view, view) for view in dashboard.MENU_ORDER + dashboard.FOLDER_ORDER}
    texts |= {lead for _, lead in dashboard.PROJECT_DOCUMENTS.values()}
    texts |= {name for name, _ in dashboard.SOURCE_LINKS} | {dashboard.ATTRIBUTION_TEXT, dashboard.PAGE_FOLDER}
    texts |= {documents_folder.VIEW_GRID, documents_folder.VIEW_LIST}
    assert not texts - set(i18n.EN), sorted(texts - set(i18n.EN))


def headings(text):
    return re.findall(r"^## (.+)$", text, re.MULTILINE)


def canonical_numbers(text, language):
    """Every figure of a document, written the same way in both languages."""
    text = re.sub(r"\]\([^)]*\)", "]", text)  # links point to anchors in their own language
    if language == i18n.SPANISH:
        text = re.sub(r"\b(\d{2})-(\d{2})-(\d{4})\b", r"\3-\2-\1", text)
        text = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", text)
        text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    else:
        text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    return Counter(re.findall(r"\d+(?:\.\d+)?", text))


@pytest.mark.parametrize("filename", FOLDER_FILES)
def test_d283_each_document_exists_in_english_with_the_same_structure_identifiers_and_figures(filename):
    spanish, english = read(DOCS_DIR / filename), read(EN_DIR / filename)
    assert len(headings(spanish)) == len(headings(english)), filename
    assert re.findall(r"^\[\[diagrama:(\w+)\]\]$", spanish, re.MULTILINE) == \
        re.findall(r"^\[\[diagrama:(\w+)\]\]$", english, re.MULTILINE)
    assert len(re.findall(r"\[\[vista:", spanish)) == len(re.findall(r"\[\[vista:", english))
    assert set(IDENTIFIER.findall(spanish)) == set(IDENTIFIER.findall(english)), filename
    assert canonical_numbers(spanish, i18n.SPANISH) == canonical_numbers(english, i18n.ENGLISH), filename
    assert spanish.count("```") == english.count("```") == 0


@pytest.mark.parametrize("filename", FOLDER_FILES)
def test_d283_each_english_document_has_its_header_contents_glossary_and_history(filename):
    text = read(EN_DIR / filename)
    header = text.split("## ", 1)[0]
    for field in ENGLISH_FIELDS:
        assert f"| {field} |" in header, (filename, field)
    assert "| Owner | The author |" in header and "## Contents" in text and "Version history" in text
    assert filename == "GLOSARIO.md" or "[Glossary](GLOSARIO.md)" in text
    version = re.search(r"\| Version \| ([\d.]+) \|", header).group(1)
    date = re.search(r"\| Date \| (\d{4}-\d{2}-\d{2}) \|", header).group(1)
    last = re.findall(r"^\| ([\d.]+) \| (\d{4}-\d{2}-\d{2}) \|", text.split("Version history")[-1], re.MULTILINE)[-1]
    assert last == (version, date)
    spanish = documents_folder.describe(read(DOCS_DIR / filename))
    assert (version, date) == (spanish["version"], documents_folder.sortable(spanish["date"]))


# Forms that do not belong in a professional document, in English.
FORBIDDEN = [r"\bprompt\b", r"\bClaude\b", r"\bTODO\b", r"lorem", r"\bnote:", r"\byou\b", r"\byour\b", r"\brobot\b"]


@pytest.mark.parametrize("filename", FOLDER_FILES)
def test_d283_every_english_document_is_written_as_a_professional_document(filename):
    text = read(EN_DIR / filename)
    for pattern in FORBIDDEN:
        assert not re.search(pattern, text, 0 if pattern == r"\bTODO\b" else re.IGNORECASE), (filename, pattern)


@pytest.mark.parametrize("filename", FOLDER_FILES)
def test_d283_every_english_link_and_contents_entry_reaches_its_heading(filename):
    text = read(EN_DIR / filename)
    anchors = {dashboard.heading_anchor(heading) for heading in re.findall(r"^#{2,4} (.+)$", text, re.MULTILINE)}
    for target in re.findall(r"\]\(#([^)]+)\)", text.split("## Contents", 1)[1].split("\n## ", 1)[0]):
        assert target in anchors, (filename, target)
    for other, anchor in re.findall(r"\]\(([A-Z_]+\.md)(?:#([^)]+))?\)", text):
        assert (EN_DIR / other).exists(), (filename, other)
        if anchor:
            other_headings = re.findall(r"^#{2,4} (.+)$", read(EN_DIR / other), re.MULTILINE)
            assert anchor in {dashboard.heading_anchor(heading) for heading in other_headings}, (filename, other, anchor)
    for label in re.findall(r"\[\[vista:([^\]]+)\]\]", text):
        assert dashboard.find_menu_page(label), (filename, label)


def test_d283_every_acronym_of_the_english_documents_is_in_the_english_glossary():
    glossary = read(EN_DIR / "GLOSARIO.md")
    table = glossary[glossary.index("| Acronym or term"):].split("\n\n", 1)[0]
    defined = set(re.findall(r"[A-Za-z0-9]+", " ".join(line.split(" | ")[0] for line in table.splitlines()[2:])))
    words = {"MB", "GB", "YYYY", "MM", "DD", "VARCHAR", "BIGINT", "INTEGER", "DOUBLE", "BOOLEAN"}
    for filename in FOLDER_FILES:
        if filename == "GLOSARIO.md":
            continue
        text = re.sub(r"\]\([^)]*\)", "]", re.sub(r"`[^`]*`", "", read(EN_DIR / filename)))
        missing = set(re.findall(r"\b[A-Z]{2,}[0-9]*\b", text)) - defined - words
        assert not missing, (filename, sorted(missing))


def test_d283_the_english_glossary_names_only_english_pages_and_tabs():
    menu = {i18n.EN[dashboard.SIDEBAR_LABELS.get(view, view)] for view in dashboard.MENU_ORDER}
    tabs = {"Operations", "Deployment", "CI/CD", "Monitoring"}
    glossary = read(EN_DIR / "GLOSARIO.md")
    table = glossary[glossary.index("| Acronym or term"):].split("\n\n", 1)[0]
    for row in [line.split(" | ") for line in table.splitlines()[2:]]:
        for place in [] if row[2] == "—" else row[2].split(", "):
            page, _, tab = place.partition(" (")
            assert page in menu, (row[0], page)
            assert not tab or tab.rstrip(")") in tabs, (row[0], tab)


def test_d283_the_language_follows_the_address_and_spanish_keeps_addresses_as_they_were():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["lang"] = "en"
    app.run()
    assert not app.exception
    labels = [link.proto.label for link in app.sidebar.get("page_link")]
    assert "Weekly summary" in labels and "Documents folder" in labels and "Resumen semanal" not in labels
    toggles = [button.label for button in app.sidebar.button if str(button.key).startswith("nav_toggle_")]
    assert toggles[:2] == ["Business · BI", "Data engineering"]
    assert [button.proto.type for button in app.sidebar.button if str(button.key).startswith("language_")] == \
        ["secondary", "primary"]
    spanish = AppTest.from_file(DASHBOARD_FILE, default_timeout=60).run()
    assert "lang" not in spanish.query_params and "Resumen semanal" in [l.proto.label for l in spanish.sidebar.get("page_link")]


@pytest.mark.parametrize("page", ["SAD · Arquitectura", "Glosario", "Documentos"])
def test_d283_a_document_and_the_folder_open_in_english(page):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params.update({"lang": "en", "vista": page})
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    if page == "Documentos":
        assert "Software Architecture Document (SAD)" in markup and "documents · last change" in markup
        assert "lang=en" in markup  # Open, PDF and the path keep the language
    else:
        assert "| Field | Value |" in markup and "| Campo |" not in markup
        assert "docs/en/" in " ".join(block.value for block in app.markdown)
        assert ">Documents</a>" in markup
