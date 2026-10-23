"""Diagrams of the PRD and the SAD (bi/doc_diagrams.py) and the markers that place them."""
import re
from pathlib import Path

import pytest

from bi import charts, doc_diagrams, doc_views

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DOCUMENTS = ["PRD.md", "SAD.md", "ADR.md", "SEGURIDAD.md"]
MARKER = re.compile(r"^\[\[diagrama:(\w+)\]\]\s*$", re.MULTILINE)


def read_markers():
    return {name: MARKER.findall((DOCS_DIR / name).read_text(encoding="utf-8")) for name in DOCUMENTS}


def test_every_marker_names_a_diagram_that_exists():
    known = set(doc_diagrams.DOC_DIAGRAMS) | set(doc_diagrams.LIVE_DIAGRAMS)
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


def test_d242_the_context_view_is_the_system_as_one_box_with_its_people_and_external_systems():
    page = doc_diagrams.DOC_DIAGRAMS["contexto"](charts.MODE_DARK)
    # 3D logos on lit discs; the system is one box and nothing of its inside is drawn.
    assert page.count('class="logo"') == 6 and "radialGradient" in page and 'class="zone"' not in page
    assert page.count('class="system"') == 1 and "<b>GreenOcean</b>" in page
    assert page.count('class="chip"') == len(doc_views.CONTEXT_EDGES) == 6
    assert page.count('role="tooltip"') == 6 + len(doc_views.CONTEXT_EDGES) + 1
    # Orthogonal arrows only, and every one touches the system box: the others are not drawn against each other.
    left, top, width, height = doc_views.SYSTEM_BOX
    for path, *_ in doc_views.CONTEXT_EDGES:
        assert re.fullmatch(r"M\d+ \d+( [HV]\d+)+", path), path
        x, y = map(int, path[1:].split(" ")[:2])
        ends_on_top = path.endswith(f"V{top}") and left <= x <= left + width  # a person reaches the top of the box
        leaves_a_side = x in (left, left + width) and top <= y <= top + height  # or the box reaches a source or a platform
        assert ends_on_top or leaves_a_side, path
    assert {name for name in ("ODEPA", "INE", "GitHub", "Streamlit Community Cloud", "Visitante", "Administrador")
            if f"<b>{name}</b>" in page} == {"ODEPA", "INE", "GitHub", "Streamlit Community Cloud", "Visitante",
                                              "Administrador"}
    # The delivery flow (Actions, repository, main) is the CI/CD diagram's, not the context's.
    for inside in ("GitHub Actions", "Repositorio", "git push"):
        assert f"<b>{inside}</b>" not in page and f">{inside}<" not in page


def test_d210_the_weak_views_are_gone():
    assert set(doc_diagrams.DOC_DIAGRAMS) == {"contexto", "casos", "mockups"}


def test_d205_the_mockups_are_real_captures_in_four_themes_and_devices():
    page = doc_diagrams.DOC_DIAGRAMS["mockups"](charts.MODE_DARK)
    assert page.count("data:image/jpeg;base64,") == 4
    assert {"Vantablack", "Claro", "Corporativo", "Blue Light"} <= {word for row in doc_views.MOCKUPS for word in
                                                                    ["Vantablack", "Claro", "Corporativo", "Blue Light"] if word in row[2]}
    assert any(row[3] == "phone" for row in doc_views.MOCKUPS)
    for file_name, *_ in doc_views.MOCKUPS:
        assert (doc_views.MOCKUP_DIR / file_name).stat().st_size < 400_000


def test_doc_diagrams_does_not_depend_on_streamlit():
    for module in (doc_diagrams, doc_views):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "streamlit as st" not in source and "import streamlit" not in source
