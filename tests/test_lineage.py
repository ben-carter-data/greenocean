"""The dbt lineage is the zoom of the journey: every model explained by dbt, its graph\nencoded for LINEAGE_SCRIPT (hover follows inputs and outputs, a click pins them)."""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import architecture, charts, lineage, queries  # noqa: E402
from tests.test_tech_glossary import nearest_title, parse, tag  # noqa: E402


@pytest.fixture(scope="module")
def build():
    nodes, results = lineage.read_tables(queries.run_sql)
    if nodes.empty:
        pytest.skip("the serving database has no dbt build yet")
    return nodes, results


def drawn_nodes(nodes):
    return nodes[nodes["resource_type"].isin(["model", "source"])]


def test_every_model_and_source_is_described_in_dbt(build):
    nodes, _ = build
    drawn = drawn_nodes(nodes)
    assert len(drawn) == 19
    assert all(description.strip() for description in drawn["description"]), \
        drawn[drawn["description"].str.strip() == ""]["name"].tolist()
    assert not any("robot" in description.lower() for description in drawn["description"])


@pytest.mark.parametrize("mode", [charts.MODE_LIGHT, charts.MODE_DARK])
def test_every_node_explains_what_it_does_its_storage_tests_and_inputs(build, mode):
    nodes, results = build
    svg = lineage.build_lineage_svg(nodes, results, mode)
    assert 'aria-label="Linaje dbt: de bronce a marts"' in svg
    root, parents = parse(svg)
    counts = lineage.tests_by_model(nodes, results)
    for node in drawn_nodes(nodes).to_dict("records"):
        name = next(element for element in root.iter() if tag(element) == "text" and element.text == node["name"])
        title, _ = nearest_title(name, parents)
        assert title.startswith(node["name"]) and node["description"] in title, node["name"]
        assert "Materialización:" in title and "Lee:" in title
        total, passing = counts.get(node["unique_id"], (0, 0))
        if total:
            assert f"Pruebas: {passing} de {total} superadas" in title


def test_the_marts_flow_into_the_journey_gold_node(build):
    nodes, results = build
    svg = lineage.build_lineage_svg(nodes, results, charts.MODE_DARK)
    root, parents = parse(svg)
    gold = next(element for element in root.iter() if tag(element) == "text" and element.text == "datos.duckdb")
    assert nearest_title(gold, parents)[0] == architecture.TOOLTIPS["datos.duckdb"]
    marts = set(nodes[nodes["layer"] == "marts"]["unique_id"])
    into_gold = {edge.get("data-from") for edge in root.iter()
                 if tag(edge) == "path" and edge.get("data-to") == lineage.GOLD_ID}
    assert into_gold == marts  # one link from each mart into the gold tile
    summary = lineage.summarize_build(nodes, results)
    assert f"{summary['passing']}/{summary['tests']} pruebas" in svg and "capa oro · modelo estrella" in svg


@pytest.mark.parametrize("mode", list(charts.PALETTES))
def test_every_node_and_edge_carries_the_graph_for_the_script(build, mode):
    nodes, results = build
    root, _ = parse(lineage.build_lineage_svg(nodes, results, mode))
    groups = {element.get("data-node"): element for element in root.iter() if element.get("data-node")}
    drawn = set(drawn_nodes(nodes)["unique_id"])
    assert set(groups) == drawn | {lineage.GOLD_ID}
    for node_id, group in groups.items():
        assert tag(group) == "g" and group.get("data-up") is not None and group.get("data-down") is not None
        for other in group.get("data-up").split() + group.get("data-down").split():
            assert other in groups, (node_id, other)
    edges = [element for element in root.iter() if tag(element) == "path" and "lin-edge" in element.get("class", "")]
    assert len(edges) >= len(drawn)
    for edge in edges:
        source, target = edge.get("data-from"), edge.get("data-to")
        assert source in groups and target in groups
        assert source in groups[target].get("data-up").split()
        assert target in groups[source].get("data-down").split()
    # Every dependency read by a drawn model is a link of the graph.
    pairs = {(edge.get("data-from"), edge.get("data-to")) for edge in edges}
    for node in drawn_nodes(nodes).to_dict("records"):
        for parent in node["depends_on"]:
            if parent in drawn:
                assert (parent, node["unique_id"]) in pairs


def test_layout_subtitle_headers_and_legend(build):
    nodes, results = build
    svg = lineage.build_lineage_svg(nodes, results, charts.MODE_LIGHT)
    counts = lineage.tests_by_model(nodes, results)
    tested = sum(1 for node_id in drawn_nodes(nodes)["unique_id"] if counts.get(node_id, (0, 0))[0])
    assert svg.count('class="lin-status"') == tested + 1  # every tested model, and datos.duckdb
    width, height = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
    assert 1450 <= width <= 1600 and height <= 820
    for title in ["BRONCE", "STAGING", "INTERMEDIO", "MARTS", "ORO"]:
        assert f">{title}</text>" in svg
    summary = lineage.summarize_build(nodes, results)
    assert (f"staging → intermedio → marts · {summary['models']} modelos · "
            f"{summary['passing']}/{summary['tests']} pruebas") in svg
    for label in ["Pruebas superadas", "Dependencia (seleccionada)", "Fuera de la selección", lineage.HINT]:
        assert f">{label}</text>" in svg
    assert "lin-flow" in svg and "prefers-reduced-motion" in svg


def test_nodes_do_not_overlap(build):
    nodes, results = build
    root, _ = parse(lineage.build_lineage_svg(nodes, results, charts.MODE_DARK))
    boxes = []
    for group in root.iter():
        if group.get("data-node"):
            hit = next(child for child in group if tag(child) == "rect")
            boxes.append((group.get("data-node"), *(float(hit.get(key)) for key in ("x", "y", "width", "height"))))
    for index, (name, x, y, w, h) in enumerate(boxes):
        assert 0 <= x and x + w <= lineage.WIDTH and y + h <= lineage.LEGEND_Y - 16, name
        for other, x2, y2, w2, h2 in boxes[index + 1:]:
            assert x + w <= x2 or x2 + w2 <= x or y + h <= y2 or y2 + h2 <= y, (name, other)


def test_lineage_script_is_one_valid_script_without_markup():
    script = lineage.LINEAGE_SCRIPT
    assert script.startswith("<script>") and script.count("<script") == 1
    body = script[len("<script>"):-len("</script>")]
    assert not re.search(r"<[a-zA-Z/!]", body)  # st.html drops scripts that look like markup
    assert "window.lineageReady" in body and "MutationObserver" in body
    assert 'svg[aria-label="Linaje dbt: de bronce a marts"]' in body
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(body)
    result = subprocess.run([node, "--check", handle.name], capture_output=True, text=True)
    Path(handle.name).unlink()
    assert result.returncode == 0, result.stderr
