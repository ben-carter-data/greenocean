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


def test_d210_the_actors_view_follows_the_pipeline_standard():
    page = doc_diagrams.DOC_DIAGRAMS["actores"](charts.MODE_DARK)
    # 3D logos on lit discs, no tiles or zones; every logo and every chip explains itself.
    assert page.count('class="logo"') == 7 and "radialGradient" in page and 'class="zone"' not in page
    assert page.count('class="chip"') == len(doc_views.ACTOR_EDGES)
    assert page.count('role="tooltip"') == 7 + len(doc_views.ACTOR_EDGES)
    # Orthogonal arrows only: straight runs with right angles, never a curve.
    for path, *_ in doc_views.ACTOR_EDGES:
        assert re.fullmatch(r"M\d+ \d+( [HV]\d+)+", path), path
    assert {name for name in ("ODEPA", "INE", "GitHub Actions", "Repositorio", "Panel", "Visitante", "Administrador")
            if f"<b>{name}</b>" in page} == {"ODEPA", "INE", "GitHub Actions", "Repositorio", "Panel", "Visitante",
                                              "Administrador"}


def test_d210_the_weak_views_are_gone():
    assert set(doc_diagrams.DOC_DIAGRAMS) == {"actores", "mockups"}


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
