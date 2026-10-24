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


def test_d242_the_context_view_is_the_system_as_one_box_with_its_people_and_external_systems():
    page = doc_diagrams.DOC_DIAGRAMS["contexto"](charts.MODE_DARK)
    # 3D logos on lit discs; the system is one box that names the tools it is built with (D-249), in the order of
    # its pipeline, but draws none of its parts: those are the next views.
    assert page.count('class="logo"') == 6 + len(doc_views.SYSTEM_TOOLS) and "radialGradient" in page and 'class="zone"' not in page
    assert [name for _, name in doc_views.SYSTEM_TOOLS] == ["Python", "SQLite", "Parquet", "dbt", "DuckDB", "Streamlit"]
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
    assert set(doc_diagrams.DOC_DIAGRAMS) == {"contexto", "contenedores", "casos", "mockups", "sop"}


def test_d205_the_mockups_are_real_captures_in_four_themes_and_devices():
    page = doc_diagrams.DOC_DIAGRAMS["mockups"](charts.MODE_DARK)
    assert page.count("data:image/jpeg;base64,") == 4
    # D-248: one capture per theme the panel offers today, retaken from the current pages.
    assert set(charts.THEMES) == {word for row in doc_views.MOCKUPS for word in charts.THEMES if word in row[2]}
    for file_name, *_ in doc_views.MOCKUPS:
        assert (doc_views.MOCKUP_DIR / file_name).exists(), file_name
    assert any(row[3] == "phone" for row in doc_views.MOCKUPS)
    for file_name, *_ in doc_views.MOCKUPS:
        assert (doc_views.MOCKUP_DIR / file_name).stat().st_size < 400_000


def test_doc_diagrams_does_not_depend_on_streamlit():
    for module in (doc_diagrams, doc_views):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "streamlit as st" not in source and "import streamlit" not in source


def test_d247_the_containers_view_is_c4_level_2_with_real_files_and_straight_links():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    page = doc_diagrams.DOC_DIAGRAMS["contenedores"](charts.MODE_DARK)
    kinds = {row[1] for row in doc_views.CONTAINERS}
    assert kinds == {"app", "store", "external", "person"}
    assert [row[6] for row in doc_views.CONTAINERS if row[1] == "app"] == ["Carga semanal", "Panel web"]
    for key, kind, *_, files, what in doc_views.CONTAINERS:
        assert what, key
        for path in [part.strip() for part in files.split("·") if part.strip()]:
            if path not in ("etl/raw.db", "etl/bronze/", "etl/warehouse_build.duckdb"):  # rebuilt on each load, not in Git
                assert (root / path).exists(), path
        assert f'id="c-{key}"' in page and f'id="ct-{key}"' in page
    for path, label, *_ in doc_views.C4_LINKS:  # (path, label, x, y, anchor)
        assert re.fullmatch(r"M\d+ \d+ [HV]\d+", path), path  # one straight segment
        assert label
    assert "<script" not in page and page.count('class="c4-line"') == len(doc_views.C4_LINKS)


def test_d247_every_view_a_document_links_to_is_a_page_of_the_menu():
    from bi import dashboard
    for name in DOCUMENTS:
        text = (DOCS_DIR / name).read_text(encoding="utf-8")
        for label in re.findall(r"\[\[vista:([^\]]+)\]\]", text):
            assert dashboard.find_menu_page(label), (name, label)


def test_d249_the_security_test_plan_points_each_case_to_a_test_that_exists_and_the_architecture_uses_them():
    from bi import security_map
    root = Path(__file__).resolve().parent.parent
    text = (DOCS_DIR / "SEGURIDAD.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (S-\d{2}) \|(.*)\|$", text, flags=re.MULTILINE)
    assert [case for case, _ in rows] == [f"S-{n:02d}" for n in range(1, 11)]
    for case, row in rows:
        references = re.findall(r"`([^`]+::[^`]+)`", row)
        assert references, case
        for reference in references:
            path, name = reference.split("::")
            assert re.search(rf"^def {re.escape(name)}\(", (root / path).read_text(encoding="utf-8"), re.MULTILINE), reference
    cases = {case for case, _ in rows}
    for threat in security_map.THREATS:
        assert set(threat[4]) <= cases, threat[0]
    assert "límite de intentos" in text and "riesgo aceptado" in text  # the accepted risk is written, not hidden


def test_d249_the_sop_has_five_steps_and_says_that_ci_warns_but_does_not_stop_main():
    page = doc_diagrams.DOC_DIAGRAMS["sop"](charts.MODE_DARK)
    assert [step[1] for step in doc_views.SOP_STEPS] == ["Preparar", "Ejecutar", "Comprobar", "Registrar", "Decidir"]
    for index in range(5):
        assert f'id="sop-{index}"' in page and f'id="sop-tip-{index}"' in page
    assert "no detiene la publicación de main" in page and "<script" not in page
