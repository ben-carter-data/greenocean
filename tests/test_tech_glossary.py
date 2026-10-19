"""Every technology shown in a diagram explains itself on hover (bi/tech_glossary.py)."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import architecture, charts, control, devops, lineage, queries, tech_glossary  # noqa: E402
from tests.test_architecture import DEVOPS_FIGURES, FIGURES, make_states  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"


def parse(svg):
    """The SVG tree and a {child: parent} map (ElementTree has no parent links)."""
    root = ET.fromstring(svg if "xmlns=" in svg.split(">", 1)[0]
                         else svg.replace("<svg ", f'<svg xmlns="{SVG[1:-1]}" ', 1))
    return root, {child: parent for parent in root.iter() for child in parent}


def tag(element):
    return element.tag.replace(SVG, "")


def nearest_title(element, parents):
    """The text of the <title> of the closest enclosing <g> that has one."""
    while element in parents:
        element = parents[element]
        if tag(element) == "g":
            title = next((child for child in element if tag(child) == "title"), None)
            if title is not None:
                return title.text, element
    return None, None


def journey_svgs():
    states = make_states(control.RUN_OK)
    return {"journey": architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK),
            "vertical": architecture.build_vertical_journey_svg(states, FIGURES, charts.MODE_DARK),
            "devops": architecture.build_devops_svg(states, DEVOPS_FIGURES, charts.MODE_DARK)}


def test_every_key_used_by_the_diagrams_has_a_complete_entry():
    used = set(tech_glossary.TECH_KEYS.get(tech_id, tech_id) for tech_id in architecture.TECH)
    used |= set(tech_glossary.CHIP_KEYS.values()) | set(tech_glossary.LABEL_KEYS.values())
    used |= set(tech_glossary.LOGO_KEYS.values()) | set(tech_glossary.WORD_KEYS.values())
    used |= set(architecture.COMPONENT_LOGO_KEYS.values()) | set(devops.STAGE_LOGO_KEYS.values())
    used |= set(lineage.LAYER_KEYS.values()) | set(lineage.MATERIALIZED_KEYS.values())
    used |= {tech_glossary.LOGO_KEYS[slug] for slug in architecture.ICON_LOGO_SLUG.values()}
    used |= {tech_glossary.LOGO_KEYS[slug] for _, _, _, slugs, *_ in devops.STAGES for slug in slugs}
    assert used <= set(tech_glossary.TECH_GLOSSARY)
    for key, entry in tech_glossary.TECH_GLOSSARY.items():
        assert set(entry) == {"nombre", "sigla", "que_es", "rol"}, key
        assert entry["nombre"] and entry["que_es"] and entry["rol"], key
        text = tech_glossary.describe(key)
        assert "robot" not in text.lower() and "Aquí:" in text
        assert len(text) < 360, key  # a hint, not a paragraph


def test_acronyms_are_spelled_out():
    for key, expansion in [("csv", "Comma-Separated Values"), ("sql", "Structured Query Language"),
                           ("etl", "Extract, Transform, Load"), ("ci", "Continuous Integration"),
                           ("odepa", "Oficina de Estudios y Políticas Agrarias"),
                           ("ine", "Instituto Nacional de Estadísticas"),
                           ("ipc", "Índice de Precios al Consumidor")]:
        assert expansion in tech_glossary.describe(key)


@pytest.mark.parametrize("name", ["journey", "vertical", "devops"])
def test_every_pill_logo_and_chip_of_the_architecture_diagrams_has_its_own_title(name):
    root, parents = parse(journey_svgs()[name])
    labels = {tech["label"] for tech in architecture.TECH.values()}
    checked = 0
    for element in root.iter():
        if tag(element) == "text" and element.text in labels and element.get("font-size") == "9.5":
            # A stack pill: its own group explains that technology, with cursor:help.
            title, group = nearest_title(element, parents)
            assert title and title.startswith(element.text), element.text
            assert "cursor:help" in group.get("style", "")
            checked += 1
        elif tag(element) == "text" and element.get("font-family") == "monospace":
            # A chip on a link: every technology chip carries its glossary entry.
            title, group = nearest_title(element, parents)
            assert title, element.text
            if element.text in tech_glossary.CHIP_KEYS:
                assert title == tech_glossary.describe(tech_glossary.CHIP_KEYS[element.text])
                assert "cursor:help" in group.get("style", "")
            checked += 1
        elif tag(element) == "svg" and element is not root:
            # A brand logo: always inside a group that names its technology.
            title, group = nearest_title(element, parents)
            assert title and " — " in title and "Aquí:" in title
            assert "cursor:help" in group.get("style", "")
            checked += 1
    assert checked >= 5


def test_a_pill_title_wins_over_the_title_of_its_step():
    root, parents = parse(journey_svgs()["journey"])
    pill = next(element for element in root.iter() if tag(element) == "text" and element.text == "pyarrow")
    title, group = nearest_title(pill, parents)
    assert title == tech_glossary.describe("pyarrow")
    # The step's own explanation is still there, one level up.
    outer, _ = nearest_title(group, parents)
    assert outer == architecture.TOOLTIPS["Parquet · bronce"]


def test_devops_cycle_logos_explain_their_tool():
    for mode in charts.THEMES:
        root, parents = parse(devops.build_svg({}, mode))
        logos = [element for element in root.iter() if tag(element) == "svg" and element is not root]
        assert len(logos) == sum(len(stage[3]) for stage in devops.STAGES)
        titles = [nearest_title(logo, parents)[0] for logo in logos]
        assert all(title and "Aquí:" in title for title in titles)
        assert tech_glossary.describe("github_actions") in titles
        assert tech_glossary.describe("github_issues") in titles


def test_lineage_layer_headers_and_materializations_explain_themselves():
    nodes, results = lineage.read_tables(queries.run_sql)
    if nodes.empty:
        pytest.skip("the serving database has no dbt build yet")
    root, parents = parse(lineage.build_lineage_svg(nodes, results, charts.MODE_DARK))
    titles = set()
    for element in root.iter():
        if tag(element) == "svg" and element is not root:
            titles.add(nearest_title(element, parents)[0])
        if tag(element) == "text" and element.text in lineage.MATERIALIZED_KEYS:
            title, group = nearest_title(element, parents)
            assert title == tech_glossary.describe(lineage.MATERIALIZED_KEYS[element.text])
            assert "cursor:help" in group.get("style", "")
    assert {tech_glossary.describe("parquet"), tech_glossary.describe("dbt")} <= titles
    for key in lineage.LAYER_KEYS.values():
        assert tech_glossary.describe(key) in {nearest_title(element, parents)[0] for element in root.iter()
                                               if tag(element) == "text"}
