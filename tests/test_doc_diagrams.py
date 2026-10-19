"""Diagrams of the PRD and the SAD (bi/doc_diagrams.py) and the markers that place them."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from bi import charts, doc_diagrams

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DOCUMENTS = ["PRD.md", "SAD.md", "ADR.md"]
MARKER = re.compile(r"^\[\[diagrama:(\w+)\]\]\s*$", re.MULTILINE)
SVG = "{http://www.w3.org/2000/svg}"


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
def test_each_diagram_is_a_well_formed_svg_with_a_tooltip_on_its_boxes(name, mode):
    svg = doc_diagrams.DOC_DIAGRAMS[name](mode)
    root = ET.fromstring(svg)
    assert root.tag == SVG + "svg" and root.get("viewBox") and root.get("aria-label")
    assert len(root.findall(f".//{SVG}title")) >= 5
    assert "robot" not in svg.lower()


def test_the_diagrams_follow_the_theme():
    for function in doc_diagrams.DOC_DIAGRAMS.values():
        light, dark = function(charts.MODE_LIGHT), function(charts.MODE_DARK)
        assert charts.get_palette(charts.MODE_LIGHT)["card"] in light
        assert charts.get_palette(charts.MODE_DARK)["card"] in dark


def test_the_sequence_prints_the_dbt_counts_it_is_given():
    svg = doc_diagrams.build_sequence_svg(charts.MODE_DARK, {"dbt_models": 17, "dbt_tests": 33})
    assert "17 modelos y 33 pruebas" in svg


def test_doc_diagrams_does_not_depend_on_streamlit():
    source = Path(doc_diagrams.__file__).read_text(encoding="utf-8")
    assert "streamlit as st" not in source and "import streamlit" not in source
