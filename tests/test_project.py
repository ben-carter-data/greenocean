"""Tests for the content of the project page (T-43): documents, SQL, files, examples."""

import ast
import re
import sys
from pathlib import Path

import pandas as pd
import requests
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import project, queries  # noqa: E402
from tests import code_shape  # noqa: E402

# region Constants
# Units, SQL types and the date pattern read as words, not acronyms to define.
NOT_ACRONYMS = {"MB", "GB", "AAAA", "MM", "DD", "VARCHAR", "BIGINT", "INTEGER", "DOUBLE", "BOOLEAN"}
SPLIT_PANEL = [
    "dashboard.py",
    "constants.py",
    "data_access.py",
    "app_style.py",
    "app_frame.py",
    "page_weekly.py",
    "page_analysis.py",
    "page_engineering.py",
    "page_quality.py",
    "page_devops.py",
    "page_documents.py",
]
# endregion


# region Documents
def test_markdown_table_keeps_escaped_pipes_inside_a_cell():
    rows = project.parse_markdown_table("| ID | Regla |\n|---|---|\n| RN-02 | usa `\\|` |\n")
    assert rows == [{"ID": "RN-02", "Regla": "usa `|`"}]


def test_project_guide_explains_every_rule_indicator_and_table():
    rules = {row["Regla"] for row in project.read_guide_table("Reglas de calidad")}
    assert rules == {f"RN-{number:02d}" for number in range(1, 16)}
    assert {row["KPI"] for row in project.read_guide_table("KPI")} == {f"K{number}" for number in range(1, 9)}
    definitions = project.parse_definitions(
        project.read_section(project.read_document(project.PROJECT_GUIDE_FILE), "Modelo de datos")
    )
    assert set(definitions) == set(project.TABLE_NAMES)


# endregion


# region Project links (T-54)
def test_t54_project_links_have_the_agreed_names_and_hide_what_does_not_exist():
    names = [link["name"] for link in project.PROJECT_LINKS]
    # Names shortened (D-116): the page itself is titled «GitHub» and each GitHub
    # link now carries the real brand mark, so the words «en GitHub» / «Ver» /
    # «Abrir» no longer need repeating on every single link. «Código» is retired
    # (the repo-header strip already opens it) and ODEPA moved to its own sidebar
    # folder, «Fuentes» (D-118).
    assert names == [
        "GitHub Actions",
        "Informes semanales",
        "Historial de cambios",
        "MANUAL",
        "DECISIONES",
        "Video",
        "Post de LinkedIn",
    ]
    for link in project.PROJECT_LINKS:
        assert link["description"] and link["icon"]
    unpublished = {link["name"] for link in project.PROJECT_LINKS if not link["url"]}
    assert unpublished == {"Video", "Post de LinkedIn"}


@pytest.mark.parametrize("link", [link for link in project.PROJECT_LINKS if link["url"]], ids=lambda link: link["name"])
def test_t54_every_public_link_answers(link):
    try:
        response = requests.get(
            link["url"], timeout=20, allow_redirects=True, headers={"User-Agent": "monitor-precios-tests"}
        )
    except (requests.ConnectionError, requests.Timeout):
        pytest.skip("no network")
    if response.status_code >= 500:  # D-567: GitHub is down, not the link: an outage never turns a push red
        pytest.skip(f"{link['name']}: the site answers {response.status_code}")
    assert response.status_code < 400, f"{link['name']}: {response.status_code}"


# endregion


# region Real figures of the diagrams
def test_d054_real_figures_of_the_devops_diagram(tmp_path):
    (tmp_path / "test_one.py").write_text(
        "x = 1\n\ndef test_a():\n    pass\n\n\ndef test_b():\n    pass\n", encoding="utf-8"
    )
    (tmp_path / "helper.py").write_text("\ndef test_not_counted():\n    pass\n", encoding="utf-8")
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


# endregion


# region The glossary and the READMEs
def test_d279_every_acronym_of_the_documents_is_in_the_glossary():
    """The terms are defined once, in docs/negocio/GLOSARIO.md, which the panel shows."""
    glossary = project.read_glossary()
    defined = set(re.findall(r"[A-Za-z0-9]+", " ".join(row["Sigla o término"] for row in glossary)))
    for path in sorted(project.DOCS_DIR.rglob("*.md")):
        if (
            "archivo" in path.parts
            or "privado" in path.parts
            or "en" in path.parts
            or "calidad" in path.parts
            and path.name in ("README.md", "INFORME.md")
        ):
            continue
        if path.name in ("DECISIONES.md", "PROYECTO.md", "DISENO.md", "GLOSARIO.md"):
            continue
        text = re.sub(r"\]\([^)]*\)", "]", re.sub(r"`[^`]*`", "", path.read_text(encoding="utf-8")))
        missing = set(re.findall(r"\b[A-Z]{2,}[0-9]*\b", text)) - defined - NOT_ACRONYMS
        assert not missing, (path.name, sorted(missing))
    assert all(row["Tema"] for row in glossary)


def test_d338_each_readme_links_to_the_other_and_the_english_one_stays_in_english():
    """The language rule (D-338): README.md is Spanish and README.en.md English; only their first line crosses over."""
    root = Path(__file__).resolve().parent.parent
    spanish = (root / "README.md").read_text(encoding="utf-8").splitlines()
    english = (root / "README.en.md").read_text(encoding="utf-8").splitlines()
    assert spanish[0] == "English version: README.en.md"
    assert english[0] == "Versión en español: README.md"
    body = "\n".join(english[1:])
    assert not any(letter in body for letter in "áéíóúñ¿¡"), "README.en.md must not mix in Spanish"
    # The same public address and the same four badges, so neither version points somewhere else.
    for needle in (
        "streamlit.app/",
        "workflows/pruebas.yml/badge.svg",
        "workflows/semanal.yml/badge.svg",
        "workflows/calidad.yml/badge.svg",
        "medicion.json",
    ):
        assert needle in "\n".join(spanish) and needle in body, needle


# endregion


# region The layout and the language of the code (R-001, R-002, R-003, D-338)
def test_d338_the_comments_of_the_code_stay_in_english():
    """Code and its comments are in English (CLAUDE.md, D-338). A comment may quote a text of the panel between « » (the
    panel is bilingual and its Spanish texts are data); anything else with a letter only Spanish uses is a comment in
    Spanish."""
    import io
    import tokenize

    root = Path(__file__).resolve().parent.parent
    offenders = []
    for folder in ("bi", "etl", "agent", "scripts", "tests"):
        for path in sorted((root / folder).glob("*.py")):
            tokens = tokenize.generate_tokens(io.StringIO(path.read_text(encoding="utf-8")).readline)
            for token in tokens:
                if token.type == tokenize.COMMENT:
                    outside = re.sub(r"«[^»]*»", "", token.string)
                    if any(letter in outside for letter in "áéíóúñ¿¡"):
                        offenders.append(f"{path.relative_to(root)}:{token.start[0]}")
    assert offenders == [], offenders


@pytest.mark.parametrize("name", SPLIT_PANEL)
def test_d541_every_file_of_the_split_panel_keeps_the_layout_of_the_agent(name):
    """R-001 of AKGRO.md, with agent/agent.py as the model: a docstring, the imports, then regions, each closed, and the
    constants and variables first. D-546: dashboard.py too keeps its imports above the regions, and that no function
    sits inside another is checked for every file of the project below."""
    path = Path(__file__).resolve().parent.parent / "bi" / name
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    assert ast.get_docstring(tree), name
    lines = text.split("\n")
    regions = [line for line in lines if line.startswith("# region ")]
    assert regions and len(regions) == sum(line == "# endregion" for line in lines), name
    first_region = lines.index(regions[0])
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(node.lineno <= first_region + 1 for node in imports), name
    titles = [line[len("# region ") :] for line in regions]
    present = [kind for kind in ("Constants", "Variables") if kind in titles]
    assert titles[: len(present)] == present, (name, titles)  # right after the imports, in this order


def test_d542_every_python_file_of_the_project_has_its_regions_closed_and_not_nested():
    """R-001 of AKGRO.md: every module of bi/, etl/, agent/, scripts/ and tests/ is laid out in regions, like
    agent/agent.py; each region closes before the next opens. D-546: every statement of a module sits in a region (only
    the docstring, the imports and the sys.path.insert that lets a script reach the project stay above them), no region
    joins «Constants and variables», and no assignment of the module comes after its first function. A package's
    __init__.py only marks the folder."""
    root = Path(__file__).resolve().parent.parent
    wrong = []
    for folder in ("bi", "etl", "agent", "scripts", "tests"):  # D-544: the tests too
        for path in sorted((root / folder).rglob("*.py")):
            if path.name == "__init__.py" or "__pycache__" in path.parts:
                continue
            name = str(path.relative_to(root))
            source = path.read_text(encoding="utf-8")
            depth, nested, opened, regions = 0, False, 0, []
            for number, line in enumerate(source.split("\n"), 1):
                if line.startswith("# region "):
                    nested |= depth > 0
                    depth += 1
                    opened = number
                    if re.search(r"constants?\s*(and|&|,)\s*variables?", line, re.IGNORECASE):
                        wrong.append(f"{name}:{number} one region for constants and variables")
                elif line == "# endregion":
                    depth -= 1
                    nested |= depth < 0
                    regions.append((opened, number))
            if not regions or depth or nested:
                wrong.append(f"{name}: a region is missing, left open or nested")
            tree = ast.parse(source)
            functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            first_function = min((node.decorator_list or [node])[0].lineno for node in functions) if functions else None
            for node in tree.body:
                start = (getattr(node, "decorator_list", None) or [node])[0].lineno
                docstring = node is tree.body[0] and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                bootstrap = isinstance(node, ast.Expr) and ast.unparse(node.value).startswith("sys.path.insert(")
                if not (docstring or bootstrap or isinstance(node, (ast.Import, ast.ImportFrom))):
                    if not any(top < start and node.end_lineno < bottom for top, bottom in regions):
                        wrong.append(f"{name}:{start} outside a region")
                if (
                    first_function
                    and start > first_function
                    and not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                ):
                    wrong += [
                        f"{name}:{item.lineno} assigned after the first function"
                        for item in ast.walk(node)
                        if isinstance(item, (ast.Assign, ast.AnnAssign, ast.AugAssign))
                    ]
    assert wrong == [], wrong


def test_d543_no_function_of_the_project_is_written_inside_another():
    """R-002 of AKGRO.md: functions are separate. What a function needs from another travels as a parameter, or with
    functools.partial where a callable is handed over; a one-line lambda Streamlit asks for is not a function of the
    module. D-546: the tests too, and a method of a class as much as a function."""
    root = Path(__file__).resolve().parent.parent
    nested = []
    for folder in ("bi", "etl", "agent", "scripts", "tests"):
        for path in sorted((root / folder).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            nested += [
                f"{path.relative_to(root)}: {top.name} > {node.name}"
                for top in ast.walk(tree)
                if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef))
                for node in ast.walk(top)
                if node is not top and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
    assert nested == [], nested


def test_d543_javascript_and_html_live_in_their_own_files():
    """R-003 of AKGRO.md: no script hides in a Python string, long or short (D-545); it lives in bi/static/ and the
    module reads it. A text with two marks of JavaScript (a listener, the page, an arrow function) is a script."""
    root = Path(__file__).resolve().parent.parent
    marks = re.compile(r"(addEventListener|document\.|window\.|=>|function\s*\(|querySelector|location\.)")
    scripts = []
    for folder in ("bi", "etl", "agent", "scripts"):
        for path in sorted((root / folder).glob("*.py")):
            for line, text, _ in code_shape.string_literals(path.read_text(encoding="utf-8")):
                if len(marks.findall(text)) >= 2 or text.count("\n") > 100:
                    scripts.append(f"{folder}/{path.name}:{line}")
    assert scripts == [], scripts
    assert {path.name for path in (root / "bi" / "static").iterdir()} >= {"lineage.js", "zoom.js", "sql_editor.html"}


def test_d544_no_stylesheet_is_written_inside_python():
    """R-003 of AKGRO.md: CSS lives in bi/static/; a function only fills the marks of its file with the theme's values
    (bi/static_files.py). A string of more than 300 characters that reads like CSS is a stylesheet in the wrong place."""
    root = Path(__file__).resolve().parent.parent
    css = re.compile(r"[{]{1,2}\s*[a-z-]+\s*:")
    # An SVG drawing built from computed coordinates is code that draws, not a fixed text of another language.
    drawing = re.compile(r"^[rf]*['\"]{1,3}\s*<(rect|svg|g|path|line|text|circle|polygon|tspan)\b")
    inside = []
    for folder in ("bi", "etl", "agent", "scripts"):
        for path in sorted((root / folder).glob("*.py")):
            for line, text, _ in code_shape.string_literals(path.read_text(encoding="utf-8")):
                if drawing.search(text):
                    continue
                if len(text) > 300 and css.search(text) and re.search(r"(px|!important|color|display)", text):
                    inside.append(f"{folder}/{path.name}:{line}")
    assert inside == [], inside


# endregion
