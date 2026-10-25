"""D-285: «Mapa de la app», the whole system in one view (bi/app_map.py)."""
import re
from pathlib import Path

import pytest

from bi import app_map, charts, dashboard

ROOT = Path(__file__).resolve().parent.parent
FILE = re.compile(r"\b(?:bi|etl|agent|tests|dbt|docs)/[\w./*-]*\w")


def all_texts():
    texts = []
    for name, _, _, _, what, role, when, _, group in app_map.NODES.values():
        texts += [name, what, role, when] + [f"{tool} {text}" for tool, text in group]
    return texts + [what for _, _, _, what, _ in app_map.LINKS]


def test_d285_every_dependency_of_the_project_is_on_the_map():
    named = " ".join(all_texts()).lower()
    for path in ("requirements.txt", "requirements-pipeline.txt"):
        for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if not line or line.startswith("-r"):
                continue
            package = re.split(r"[<>=!~ ]", line)[0].lower()
            assert package.replace("-core", " core") in named or package in named, package


def test_d285_every_file_and_module_the_map_names_exists():
    for text in all_texts():
        for path in FILE.findall(text):
            if "*" in path:
                continue
            assert (ROOT / path).exists(), path
    for workflow in ("semanal.yml", "pruebas.yml"):
        assert (ROOT / ".github" / "workflows" / workflow).exists()


def test_d285_every_line_joins_two_nodes_and_no_node_is_alone():
    kinds = {kind for kind, _ in app_map.LINE_KINDS}
    themes = {key for key, _ in app_map.THEMES}
    for source, target, kind, what, line_themes in app_map.LINKS:
        assert source in app_map.NODES and target in app_map.NODES and kind in kinds and what, (source, target)
        assert line_themes and set(line_themes) <= themes, (source, target)
    linked = {key for source, target, *_ in app_map.LINKS for key in (source, target)}
    assert linked == set(app_map.NODES)


def test_d285_every_click_opens_a_page_of_the_menu_and_every_theme_has_its_filter():
    themes = {key for key, _ in app_map.THEMES}
    for key, (name, logo, node_themes, place, *_rest) in app_map.NODES.items():
        page = app_map.NODES[key][7]
        assert page in dashboard.MENU_ORDER, (key, page)
        assert set(node_themes) <= themes and node_themes, key
        assert logo.split(":")[0] in ("brand", "source", "person", "icon"), key
    assert {theme for node in app_map.NODES.values() for theme in node[2]} == themes


def test_d285_every_hover_text_has_its_four_parts_read_from_the_lines():
    for key in app_map.NODES:
        tip = app_map.build_tip(key)
        for part in ("Qué es", "Rol en GreenOcean", "Cuándo actúa", "Se conecta con"):
            assert f"<i>{part}</i>" in tip, (key, part)
        for line in app_map.connections(key):
            assert app_map.esc(line) in tip, (key, line)
    assert app_map.connections("dbt") == ["→ DuckDB: marts", "← Parquet: fuentes", "← Puertas de calidad: puertas 2 y 3"]


def test_d285_small_tools_live_in_the_node_of_their_function():
    tools = {tool for node in app_map.NODES.values() for tool, _ in node[8]}
    for expected in ("requests", "certifi y la raíz emSign", "pyarrow", "dbt-duckdb", "pandas", "hmac.compare_digest",
                     "Playwright", "pytest", "cron del martes", "caché de Actions"):
        assert expected in tools, expected


def test_d285_the_ai_node_says_exactly_what_it_is_and_stays_out_of_the_data_flow():
    name, _, themes, _, what, role, when, _, group = app_map.NODES["ai"]
    assert "sin RAG" in role and "no hay base vectorial ni embeddings" in role and "CLAUDE.md" in role
    assert themes == ["apoyo"] and "nunca en la carga ni en el panel" in when
    assert all(kind == "support" for source, target, kind, *_ in app_map.LINKS if "ai" in (source, target))


@pytest.mark.parametrize("theme", charts.THEMES)
def test_d285_the_map_is_html_with_image_logos_and_a_script_without_html(theme):
    page = app_map.build_map_html(charts.get_palette(theme), {})
    markup, script = page.split("<script>")
    assert "<svg" not in markup  # st.html drops inline SVG: the logos are images
    assert markup.count('class="am-node"') == len(app_map.NODES) and markup.count("data:image/svg+xml;base64,") == len(app_map.NODES)
    assert markup.count('class="am-filter"') == len(app_map.THEMES)
    assert "<" not in script.split("</script>")[0]  # st.html drops a script whose text holds a tag


def test_d285_the_map_sits_next_to_the_stack_and_the_stack_links_to_it():
    stack_block = next(pages for key, _, pages in dashboard.MENU_BLOCKS if key == "stack")
    assert stack_block == [dashboard.PAGE_STACK, dashboard.PAGE_APP_MAP]
    assert dashboard.PAGE_APP_MAP in dashboard.BAR_VIEWS and dashboard.PAGE_APP_MAP in dashboard.COMPACT_FOOTER_VIEWS
    source = (ROOT / "bi" / "dashboard.py").read_text(encoding="utf-8")
    stack = source[source.index("def show_stack_page"):source.index("def show_app_map_page")]
    assert "PAGE_APP_MAP, build_page_address(PAGE_APP_MAP)" in stack


def test_d291_each_filter_lights_every_actor_and_link_of_its_theme():
    """Security is not only the author: the control code goes through Streamlit and its secrets, the token reaches GitHub
    Actions, the repository holds no secret, the database is read-only and the visitor's SQL has limits."""
    def lit(theme):
        nodes = {key for key in app_map.NODES if theme in app_map.node_themes(key)}
        links = {(source, target) for source, target, _, _, themes in app_map.LINKS if theme in themes}
        return nodes, links
    nodes, links = lit("seguridad")
    assert {"author", "streamlit", "secrets", "actions", "github", "duckdb", "visitor", "security", "ci"} <= nodes
    assert {("author", "streamlit"), ("streamlit", "secrets"), ("streamlit", "actions"), ("security", "github"),
            ("security", "actions"), ("security", "duckdb")} <= links
    nodes, links = lit("orquestacion")
    assert {"github", "actions", "ci", "agent", "release", "author", "streamlit"} <= nodes
    nodes, _ = lit("calidad")
    assert {"gates", "parity", "ci", "dbt", "sqlite", "duckdb", "release", "measurement"} <= nodes
    nodes, _ = lit("observabilidad")
    assert {"monitoring", "actions", "duckdb", "github", "author", "streamlit"} <= nodes
    for theme, _ in app_map.THEMES:
        nodes, links = lit(theme)
        assert links and all(source in nodes and target in nodes for source, target in links), theme


def test_d291_without_a_filter_only_the_data_flow_is_drawn_and_each_line_carries_its_label():
    css = app_map.build_css(charts.get_palette(charts.THEMES[0]))
    assert ".am-line {{ fill:none; stroke-width:1.6; opacity:0;".replace("{{", "{") in css
    assert ".am-line.k-flow { opacity:.6; }" in css and ".am[data-filter] .am-line.show" in css
    assert 'label.textContent = whats[index];' in app_map.SCRIPT and 'class="am-whats" hidden' in app_map.build_map_html(charts.get_palette(charts.THEMES[0]), {})
