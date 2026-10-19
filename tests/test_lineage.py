"""The dbt lineage is the zoom of the journey: same pieces, every model explained by dbt."""
import re
import sys
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
    marts = (nodes["layer"] == "marts").sum()
    # One link from each mart into the gold tile, in the marts' colour.
    assert len(re.findall(r'<path d="M[^"]*" fill="none" stroke="#d55181"', svg)) >= marts
    for chip in ["sources", "stg_*", "int_*", "OK"]:
        assert f">{chip}</text>" in svg


def test_status_dots_and_layout_follow_the_journey(build):
    nodes, results = build
    svg = lineage.build_lineage_svg(nodes, results, charts.MODE_LIGHT)
    counts = lineage.tests_by_model(nodes, results)
    tested = sum(1 for node_id in drawn_nodes(nodes)["unique_id"] if counts.get(node_id, (0, 0))[0])
    dots = re.findall(r'<circle cx="[\d.]+" cy="[\d.]+" r="7" fill="(#[0-9a-f]+)"', svg)
    assert len(dots) == tested + 1  # every tested model, and datos.duckdb
    width, height = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
    assert 1000 <= width <= 1560 and height <= 760
    for title in ["BRONCE", "STAGING", "INTERMEDIO", "MARTS", "ORO"]:
        assert f">{title}</text>" in svg
    assert "journey-flow" in svg and "stroke-dasharray=\"6 4\"" in svg
