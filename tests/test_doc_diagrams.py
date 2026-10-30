"""Diagrams of the PRD and the SAD (bi/doc_diagrams.py) and the markers that place them."""

import re
from pathlib import Path

import pytest

from bi import charts, doc_diagrams, doc_figures, doc_views

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DOCUMENTS = [
    "PRD.md",
    "SAD.md",
    "ADR.md",
    "PLAN_PRUEBAS.md",
    "MANUAL.md",
    "GLOSARIO.md",
    "INDICE_DECISIONES.md",
    "PLAN_DE_CALIDAD.md",
]
MARKER = re.compile(r"^\[\[diagrama:(\w+)\]\]\s*$", re.MULTILINE)


def read_markers():
    return {name: MARKER.findall((DOCS_DIR / name).read_text(encoding="utf-8")) for name in DOCUMENTS}


def test_every_marker_names_a_diagram_that_exists():
    known = set(doc_diagrams.DOC_DIAGRAMS)
    for name, markers in read_markers().items():
        assert set(markers) <= known, (name, set(markers) - known)


def test_no_diagram_appears_twice_across_the_documents():
    markers = [marker for found in read_markers().values() for marker in found]
    assert len(markers) == len(set(markers))


def test_every_document_diagram_is_used_by_a_document():
    used = {marker for found in read_markers().values() for marker in found}
    assert set(doc_diagrams.DOC_DIAGRAMS) <= used


@pytest.mark.parametrize("mode", [charts.MODE_LIGHT, charts.MODE_DARK])
@pytest.mark.parametrize("name", list(doc_diagrams.DOC_DIAGRAMS))
def test_d205_each_view_is_one_html_document_without_script(name, mode):
    page = doc_diagrams.DOC_DIAGRAMS[name](mode)
    assert page.startswith("<!doctype html>") and "<script" not in page
    assert "robot" not in page.lower() and name in doc_diagrams.HEIGHTS


def graph_lines(page):
    """The lines of an icon diagram (D-297), as lists of points."""
    return [
        [tuple(map(float, point.split())) for point in d[1:].split(" L")]
        for d in re.findall(r'<path d="(M[\d. L]+)" fill="none"', page)
    ]


def plain(page):
    """The words of a diagram in reading order, its wrapped lines joined."""
    return " ".join(part.strip() for part in re.findall(r">([^<>]+)<", page) if part.strip())


def assert_right_angles(page):
    """Every line moves only across or up and down: consecutive points share their x or their y."""
    lines = graph_lines(page)
    assert lines
    for points in lines:
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            assert ax == bx or ay == by, points


def test_d297_the_context_view_is_the_system_with_its_people_and_external_systems_as_icons():
    page = doc_diagrams.DOC_DIAGRAMS["contexto"](charts.MODE_DARK)
    for name in ("GreenOcean", "ODEPA", "INE", "GitHub", "Streamlit Community Cloud", "Visitante", "Administrador"):
        assert f">{name}<" in page, name
    assert "Python, SQLite, Parquet, dbt, DuckDB y Streamlit" in plain(
        page
    )  # the tools it is built with, in the order of the pipeline
    assert 'class="box"' not in page and 'class="system"' not in page  # no boxes, no cards
    assert len(graph_lines(page)) == 6
    assert_right_angles(page)


def test_d210_the_weak_views_are_gone():
    # D-289: the figures of bi/doc_figures.py joined the views; nothing else is a document diagram.
    from bi import doc_figures

    assert set(doc_diagrams.DOC_DIAGRAMS) == {"contexto", "contenedores", "casos", "mockups", "sop", "pruebas"} | set(
        doc_figures.FIGURES
    )


def test_doc_diagrams_does_not_depend_on_streamlit():
    for module in (doc_diagrams, doc_views):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "streamlit as st" not in source and "import streamlit" not in source


def test_d297_the_containers_view_is_c4_level_2_with_real_files_and_right_angle_links():
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    page = doc_diagrams.DOC_DIAGRAMS["contenedores"](charts.MODE_DARK)
    for name in ("Carga semanal", "Panel web", "Base servida", "Respaldo", "Archivos de trabajo"):
        assert f">{name}<" in page, name
    for path in ("agent/agent.py", "etl/etl.py", "etl/pipeline.py", "bi/dashboard.py"):
        assert path in page and (root / path).exists(), path
    assert len(graph_lines(page)) == 8
    assert_right_angles(page)


def test_d247_every_view_a_document_links_to_is_a_page_of_the_menu():
    from bi import dashboard

    for name in DOCUMENTS:
        text = (DOCS_DIR / name).read_text(encoding="utf-8")
        for label in re.findall(r"\[\[vista:([^\]]+)\]\]", text):
            assert dashboard.find_menu_page(label), (name, label)


def test_d258_each_security_case_points_to_a_test_that_exists_and_the_architecture_uses_them():
    from bi import security_map, security_plan

    root = Path(__file__).resolve().parent.parent
    text = (DOCS_DIR / "PLAN_PRUEBAS.md").read_text(encoding="utf-8")
    assert [case[0] for case in security_plan.CASES] == [f"S-{n:02d}" for n in range(1, 11)]
    for case_id, short, attack, expected, owasp, tests in security_plan.CASES:
        assert owasp in security_map.OWASP or owasp == "—", case_id
        assert tests, case_id
        for reference in tests:
            path, name = reference.split("::")
            assert re.search(rf"^def {re.escape(name)}\(", (root / path).read_text(encoding="utf-8"), re.MULTILINE), (
                reference
            )
    cases = {case[0] for case in security_plan.CASES}
    for threat in security_map.THREATS:
        assert set(threat[4]) <= cases, threat[0]
    assert "límite de intentos" in text and "riesgo aceptado" in text  # the accepted risk is written, not hidden
    # D-279: the plan carries its cases as a table again; test_documents checks it against security_plan.CASES.


def test_d258_the_ten_cases_open_their_attack_result_owasp_threat_and_test():
    from bi import security_plan

    page = doc_diagrams.DOC_DIAGRAMS["pruebas"](charts.MODE_DARK)
    for case_id, short, attack, expected, owasp, tests in security_plan.CASES:
        assert f'href="#c-{case_id}"' in page and f'id="c-{case_id}"' in page, case_id
        for text in (attack, expected, *tests):
            assert text.replace("&", "&amp;") in page or text in page, (case_id, text)
    assert page.count('class="modal"') == 10 and page.count("OWASP Top 10 (2021)") == 10 and "<script" not in page
    assert '<base href="about:srcdoc">' in page
    # the threat of a case is the one of the architecture that lists it
    assert security_plan.threat_of("S-01")[0] == "T1" and security_plan.threat_of("S-09") is None
    assert "T3 · " in page and "Ninguna en concreto" in page


def test_d297_the_procedure_is_a_cycle_of_five_steps_and_says_that_ci_warns_but_does_not_stop_main():
    page = doc_diagrams.DOC_DIAGRAMS["sop"](charts.MODE_DARK)
    for step in ("1 · Preparar", "2 · Ejecutar", "3 · Comprobar", "4 · Registrar", "5 · Decidir"):
        assert f">{step}<" in page, step
    assert "falla: se corrige y se repite desde el 2" in plain(page) and "pasa: el cambio queda verificado" in plain(
        page
    )
    assert "no detiene la publicación de main" in page and "<script" not in page
    assert_right_angles(page)


def test_d260_each_case_shows_the_logo_of_its_technology_and_every_line_turns_at_right_angles():
    from bi import security_plan

    page = doc_diagrams.DOC_DIAGRAMS["pruebas"](charts.MODE_DARK)
    assert set(security_plan.TECH) == set(security_plan.CASE_PLACES) == {case[0] for case in security_plan.CASES}
    for case_id, tech in security_plan.TECH.items():
        assert tech in doc_views.DISCS, case_id
        assert f"Tecnología</h4><p>{security_plan.TECH_NAMES[tech]}</p>" in page, case_id
        assert f"{case_id} · {security_plan.TECH_NAMES[tech]} · " in page, case_id
    assert page.count('<circle class="node"') == 10
    # no diagonal: every line of the diagram moves only horizontally or vertically
    assert "<line " not in page
    lines = re.findall(
        r'<path d="(M[^"]*)" fill="none" stroke="[^"]*" stroke-width="[\d.]+"[^>]*stroke-linejoin="miter"', page
    )
    assert lines
    for d in lines:
        assert re.fullmatch(r"M[\d.]+ [\d.]+( [HV][\d.]+)+", d), d


@pytest.mark.parametrize("name", sorted(doc_figures.FIGURES))
def test_d297_every_icon_diagram_turns_only_at_right_angles_and_has_no_cards(name):
    page = doc_diagrams.DOC_DIAGRAMS[name](charts.MODE_CORPORATE)
    assert 'class="col"' not in page and 'class="item"' not in page and 'class="root"' not in page
    if 'class="fig-title"' in page and "<path d=\"M" in page and " L" in page:
        assert_right_angles(page)


# D-280: the document diagrams have no background; they sit on the white sheet of the PDF and on every theme.
def filled_canvas_rects(page):
    """The rectangles that fill at least 95 % of the canvas of their SVG, with a fill that is not none."""
    found = []
    for svg in re.finditer(r'<svg[^>]*viewBox="[\d.-]+ [\d.-]+ ([\d.]+) ([\d.]+)"[^>]*>(.*?)</svg>', page, re.DOTALL):
        width, height = float(svg.group(1)), float(svg.group(2))
        for rect in re.finditer(r"<rect\b([^>]*)>", svg.group(3)):
            attributes = dict(re.findall(r'([\w-]+)="([^"]*)"', rect.group(1)))
            fill = attributes.get("fill", "black")
            try:
                size = float(attributes.get("width", 0)), float(attributes.get("height", 0))
            except ValueError:
                continue
            if fill not in ("none", "transparent") and size[0] >= 0.95 * width and size[1] >= 0.95 * height:
                found.append(rect.group(0))
    return found


@pytest.mark.parametrize("theme", charts.THEMES)
@pytest.mark.parametrize("name", sorted(doc_diagrams.DOC_DIAGRAMS))
def test_d280_no_document_diagram_has_a_background(name, theme):
    page = doc_diagrams.DOC_DIAGRAMS[name](theme)
    assert not filled_canvas_rects(page), name
    for rule in re.findall(r"html, ?body ?\{([^}]*)\}", page):
        assert "background:transparent" in rule.replace(" ", ""), (name, rule)


@pytest.mark.parametrize("name", ["contexto", "contenedores", "casos", "pruebas", "sop"])
def test_d280_the_document_logos_are_flat_marks_in_their_own_color(name):
    page = doc_diagrams.DOC_DIAGRAMS[name](charts.MODE_CORPORATE)
    assert 'fill="url(#disc-' not in page and "-actors" not in page, name


def test_d280_the_logo_files_have_no_background():
    for path in (Path(doc_views.__file__).with_name("assets") / "logos").glob("*.svg"):
        text = path.read_text(encoding="utf-8")
        assert "<rect" not in text and "background" not in text, path.name
    assert doc_views.flat_logo("brand", "github").count('fill="currentColor"') == 1  # black on white, white on dark


def test_d280_the_pdf_is_a_white_sheet_in_every_theme():
    from bi import dashboard

    for theme in charts.THEMES:
        button = dashboard.build_print_button_html(theme)
        light = dashboard.PRINT_THEME if dashboard.is_dark_theme(theme) else ""
        assert f'const light = "{light}";' in button, theme
    assert not dashboard.is_dark_theme(dashboard.PRINT_THEME)
    script = dashboard.AUTO_PRINT_SCRIPT.split("<script>")[1].split("</script>")[0]
    assert "window.print()" in script and "afterprint" in script and "<" not in script


def test_d280_on_paper_the_diagrams_have_no_shadows():
    for name, builder in doc_diagrams.DOC_DIAGRAMS.items():
        assert doc_diagrams.PRINT_STYLE in builder(charts.MODE_CORPORATE), name


def test_d205_the_mockups_are_real_captures_in_four_themes_and_devices():
    page = doc_diagrams.DOC_DIAGRAMS["mockups"](charts.MODE_DARK)
    assert (
        page.count("data:image/jpeg;base64,") == len(doc_views.MOCKUPS) == 6
    )  # D-299: the dashboard and the pipeline too
    # D-248: one capture per theme the panel offers today, retaken from the current pages.
    assert set(charts.THEMES) == {word for row in doc_views.MOCKUPS for word in charts.THEMES if word in row[2]}
    for file_name, *_ in doc_views.MOCKUPS:
        assert (doc_views.MOCKUP_DIR / file_name).exists(), file_name
    # D-269: each capture is a main page of the menu at the desktop size, one per profile of the PRD.
    from PIL import Image
    from bi import dashboard

    menu = {dashboard.SIDEBAR_LABELS.get(view, view) for view in [*dashboard.MENU_ORDER, *dashboard.DOOR_PAGES]}
    for file_name, title, _ in doc_views.MOCKUPS:
        assert title.split(" · ", 1)[1] in menu, title
        assert Image.open(doc_views.MOCKUP_DIR / file_name).size == (1440, 900), file_name
    for file_name, *_ in doc_views.MOCKUPS:
        assert (doc_views.MOCKUP_DIR / file_name).stat().st_size < 400_000
