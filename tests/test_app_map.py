"""D-285: «Mapa de la app», the whole system in one view (bi/app_map.py)."""

import re
import subprocess
from pathlib import Path

import pytest

from bi import app_map, app_map_detail, charts, dashboard, i18n

ROOT = Path(__file__).resolve().parent.parent
FILE = re.compile(r"\b(?:bi|etl|agent|tests|dbt|docs)/[\w./*-]*\w")


def all_texts():
    texts = []
    for name, _, _, _, what, role, when, _, group in app_map.NODES.values():
        texts += [name, what, role, when] + [f"{tool} {text}" for tool, text in group]
    return texts + [what for _, _, _, what, *_ in app_map.LINKS]


def test_d285_every_dependency_of_the_project_is_on_the_map():
    named = " ".join(all_texts()).lower()
    for path in ("requirements.txt", "requirements-pipeline.txt"):
        for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if not line or line.startswith("-r"):
                continue
            package = re.split(r"[<>=!~ ]", line)[0].lower()
            assert package.replace("-core", " core") in named or package in named, package


def is_ignored(path):
    # A directory pattern («etl/bronze/») only matches a path that ends in a slash when the folder is not there.
    return any(
        subprocess.run(["git", "check-ignore", "-q", name], cwd=ROOT).returncode == 0 for name in (path, path + "/")
    )


def test_d285_every_file_and_module_the_map_names_exists():
    for text in all_texts():
        for path in FILE.findall(text):
            if "*" in path:
                continue
            # A file git ignores (the landing database, the SQLite backup) only exists where the load runs: the map may
            # name it, but it must be one the repository ignores on purpose.
            assert (ROOT / path).exists() or is_ignored(path), path
    for workflow in ("semanal.yml", "pruebas.yml", "calidad.yml"):
        assert (ROOT / ".github" / "workflows" / workflow).exists()


def test_d285_every_line_joins_two_nodes_and_no_node_is_alone():
    kinds = {kind for kind, _ in app_map.LINE_KINDS}
    themes = {key for key, _ in app_map.THEMES}
    rhythms = {key for key, _ in app_map_detail.RHYTHMS}
    for source, target, kind, what, line_themes, rhythm, travels, returns in app_map.LINKS:
        assert source in app_map.NODES and target in app_map.NODES and kind in kinds and what, (source, target)
        assert line_themes and set(line_themes) <= themes, (source, target)
        # D-441: each line says how often it moves, what travels and what comes back.
        assert rhythm in rhythms and travels and returns, (source, target)
    linked = {key for source, target, *_ in app_map.LINKS for key in (source, target)}
    assert linked == set(app_map.NODES)


def test_d285_every_hover_text_has_its_four_parts_read_from_the_lines():
    for key in app_map.NODES:
        tip = app_map.build_tip(key)
        for part in ("Qué es", "Rol en GreenOcean", "Cuándo actúa", "Se conecta con"):
            assert f"<i>{part}</i>" in tip, (key, part)
        for line in app_map.connections(key):
            assert app_map.esc(line) in tip, (key, line)
    assert app_map.connections("dbt") == [
        "→ DuckDB: marts",
        "← Parquet: fuentes",
        "← Puerta de publicación: pruebas y filas",
    ]


def test_d285_small_tools_live_in_the_node_of_their_function():
    tools = {tool for node in app_map.NODES.values() for tool, _ in node[8]}
    for expected in (
        "requests",
        "certifi y la raíz emSign",
        "pyarrow",
        "dbt-duckdb",
        "pandas",
        "hmac.compare_digest",
        "Playwright",
        "pytest",
        "cron del martes",
        "caché de Actions",
    ):
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
    assert markup.count('class="am-node"') == len(app_map.NODES)
    # D-441: each logo is written once, in a sheet of CSS variables, however many pieces and insides use it.
    logos = re.findall(r"data:image/svg\+xml;base64,[\w+/=]+", markup)
    assert logos and len(logos) == len(set(logos))
    assert markup.count('class="am-filter"') == len(app_map.THEMES)
    assert "<" not in script.split("</script>")[0]  # st.html drops a script whose text holds a tag


def test_d285_the_map_sits_next_to_the_stack_and_the_menu_opens_it():
    stack_block = next(pages for key, _, pages in dashboard.MENU_BLOCKS if key == "stack")
    # D-343: the method moved to «Calidad»; D-420: security joined the stack, for the Profesional
    assert stack_block == [dashboard.PAGE_STACK, dashboard.PAGE_APP_MAP, dashboard.PAGE_SECURITY]
    assert dashboard.PAGE_APP_MAP in dashboard.BAR_VIEWS and dashboard.PAGE_APP_MAP in dashboard.COMPACT_FOOTER_VIEWS
    source = (ROOT / "bi" / "dashboard.py").read_text(encoding="utf-8")
    stack = source[source.index("def show_stack_page") : source.index("def show_app_map_page")]
    # D-398: the header of «Stack y evidencia» no longer links to the map; the menu's next line does.
    assert not re.search(r"PAGE_APP_MAP,\s*build_page_address\(PAGE_APP_MAP\)", stack)


def test_d291_each_filter_lights_every_actor_and_link_of_its_theme():
    """Security is not only the author: the control code goes through Streamlit and its secrets, the token reaches GitHub
    Actions, the repository holds no secret, the database is read-only and the professional's SQL has limits."""

    def lit(theme):
        nodes = {key for key in app_map.NODES if theme in app_map.node_themes(key)}
        links = {(source, target) for source, target, _, _, themes, *_ in app_map.LINKS if theme in themes}
        return nodes, links

    nodes, links = lit("seguridad")
    assert {
        "author",
        "streamlit",
        "secrets",
        "semanal",
        "devops",
        "github",
        "duckdb",
        "professional",
        "security",
    } <= nodes
    assert {
        ("author", "devops"),
        ("devops", "secrets"),
        ("streamlit", "secrets"),
        ("devops", "semanal"),
        ("security", "github"),
        ("security", "semanal"),
        ("security", "duckdb"),
    } <= links
    nodes, links = lit("orquestacion")
    assert {"github", "semanal", "pruebas", "calidad", "ci", "agent", "release", "author", "devops"} <= nodes
    nodes, _ = lit("calidad")
    assert {"gates", "parity", "ci", "dbt", "sqlite", "duckdb", "release", "measurement"} <= nodes
    nodes, _ = lit("observabilidad")
    assert {"monitoring", "semanal", "duckdb", "github", "author", "streamlit"} <= nodes
    for theme, _ in app_map.THEMES:
        nodes, links = lit(theme)
        assert links and all(source in nodes and target in nodes for source, target in links), theme


def test_d291_without_a_filter_only_the_data_flow_is_drawn_and_each_line_carries_its_label():
    css = app_map.build_css(charts.get_palette(charts.THEMES[0]))
    assert ".am-line {{ fill:none; stroke-width:1.6; opacity:0;".replace("{{", "{") in css
    assert ".am-line.base { opacity:.6; }" in css and ".am[data-filter] .am-line.show" in css
    assert app_map.is_base("flow", ["datos"]) and app_map.is_base("access", ["seguridad"])
    assert not app_map.is_base("order", ["datos"]) and not app_map.is_base("flow", ["calidad"])
    # D-441: the English layer translates a whole string of a script; none of the map's strings may be one of its texts,
    # or the lines change in English (the theme «datos» became «data» and the data flow vanished).
    strings = {match.group(2) for match in i18n.JS_STRING.finditer(app_map.SCRIPT)}
    assert not [text for text in strings if i18n.lookup(text) not in (None, text)]
    assert (
        'label.textContent = whats[index];' in app_map.SCRIPT
        and 'class="am-whats" hidden' in app_map.build_map_html(charts.get_palette(charts.THEMES[0]), {})
    )


def test_d293_every_line_names_where_it_happens_and_that_code_really_does_it():
    """The map is the real system: each line points to the file that does it, and that file holds the code; a line no
    file can show is done by a platform (GitHub or Streamlit Cloud) and says so."""
    assert set(app_map.LINK_EVIDENCE) == {(source, target) for source, target, *_ in app_map.LINKS}
    for (source, target), (place, detail) in app_map.LINK_EVIDENCE.items():
        if place == app_map.PLATFORM:
            assert detail in ("GitHub", "Streamlit Cloud"), (source, target)
            continue
        assert detail in (ROOT / place).read_text(encoding="utf-8"), (source, target, place, detail)
    tip = app_map.build_tip("semanal")
    assert '<code class="am-src">semanal.yml</code>' in tip and '<code class="am-src">control.py</code>' in tip


def test_d293_the_description_of_a_node_moves_off_its_own_lines():
    assert "const dodge = (item) =>" in app_map.SCRIPT and "dodge(item);" in app_map.SCRIPT
    # D-441: it covers neither the node nor any node it connects with.
    assert "const ends = [center(item)].concat(links" in app_map.SCRIPT


def test_d285_every_click_opens_a_page_of_the_menu_and_every_theme_has_its_filter():
    themes = {key for key, _ in app_map.THEMES}
    for key, (name, logo, node_themes, place, *_rest) in app_map.NODES.items():
        page = app_map.NODES[key][7]
        assert page in dashboard.MENU_ORDER or page in dashboard.DOOR_PAGES, (key, page)
        assert set(node_themes) <= themes and node_themes, key
        assert logo.split(":")[0] in ("brand", "source", "person", "icon"), key
    assert {theme for node in app_map.NODES.values() for theme in node[2]} == themes


DATABASE = ROOT / "etl" / "datos.duckdb"
PEOPLE = {"visitor", "professional", "author"}
# The insides the author asked for: the three workflows, dbt, the publication gate, the backup and its parity, the panel,
# the operation pages, DuckDB, GitHub and each source with its ingestion.
INSIDES_ASKED = {
    "semanal", "calidad", "pruebas", "dbt", "gates", "parity", "streamlit", "devops", "duckdb", "github",
    "odepa", "odepa_consumer", "ine", "agent",
}  # fmt: skip
# The tools whose magnifier shows how the tool itself works.
TOOLS = {"duckdb", "dbt", "sqlite", "parquet", "streamlit", "github", "pypi", "ci", "charts"}
# The Tuesday in its real order: the trigger, PyPI, the download, the landing, bronze, dbt, the tests, the quality
# report, the panel and the readers.
WALK = ["semanal", "pypi", "agent", "sqlite", "parquet", "dbt", "ci", "calidad", "streamlit", "visitor"]


@pytest.fixture(scope="module")
def facts():
    return app_map_detail.read_facts(DATABASE if DATABASE.exists() else None)


def test_d441_each_piece_says_who_owns_it_and_the_boxes_hold_exactly_those_pieces():
    owners = {key: app_map_detail.CARDS[key][0] for key in app_map.NODES}
    assert set(app_map_detail.CARDS) == set(app_map.NODES) and set(owners.values()) <= set(app_map_detail.OWNERS)
    assert {key for key, owner in owners.items() if owner == "fuente"} == {"odepa", "odepa_consumer", "ine"}
    assert {key for key, owner in owners.items() if owner == "plataforma"} == {"github", "pypi", "stcloud"}
    assert {key for key, owner in owners.items() if owner == "persona"} == PEOPLE
    for key, (_, _, _, (row, column), *_rest) in app_map.NODES.items():
        boxes = [
            owner
            for owner, rows, columns, _ in app_map.OWNER_BOXES
            if int(rows.split("/")[0]) <= app_map.ROWS[row] < int(rows.split("/")[1])
            and int(columns.split("/")[0]) <= column < int(columns.split("/")[1])
        ]
        # A piece sits in the box of its owner; the pieces of the support row («Lo que vigila») stay outside the boxes.
        assert boxes in ([owners[key]], []), (key, boxes)


def test_d441_a_logo_names_one_piece_and_every_line_shows_its_direction():
    """The logo tells the piece, not the company: GitHub's logo is on GitHub only (the workflows and the release have
    their own icons); only pieces of one kind share an icon: the two ODEPA sources and the three workflows. Every line
    ends in a head and its label shows on its own line, never all of a node's at once."""
    logos = [node[1] for node in app_map.NODES.values()]
    repeated = {logo for logo in logos if logos.count(logo) > 1}
    assert repeated == {"source:odepa", "icon:workflow"}
    assert app_map.NODES["github"][1] == "brand:github"
    # A short name on the map never hides the full one: it stays in the piece's description (aria-label) and its card.
    for key, short in app_map.SHORT_NAMES.items():
        markup = app_map.build_node(key, charts.get_palette(charts.THEMES[0]))
        assert (
            f'aria-label="{app_map.esc(app_map.NODES[key][0])}"' in markup
            and f'class="am-name">{app_map.esc(short)}' in markup
        )
    assert "part.head = arrow(part.svg, part.path);" in app_map.SCRIPT
    # D-469: nothing answers to the cursor: no line nor piece reacts on hover, only an «i» or a magnifier on a click
    assert '"mouseenter"' not in app_map.SCRIPT and "playSeq(mine, light);" not in app_map.SCRIPT
    css = app_map.build_css(charts.get_palette(charts.THEMES[0]))
    # Several lines never show at once: a piece, a theme or a rhythm plays its lines one at a time, with labels.
    assert ".am.has-focus .am-label.on { opacity:1; }" in css


def test_d441_lines_are_orthogonal_and_each_has_a_colour_of_its_own_in_every_theme():
    """Like an entity-relationship diagram: the lines are routed on a grid around the pieces, with straight runs and
    right-angle turns, never a curve; and each line has its own colour, distinct from the others and at 3:1 on the
    background of every theme (WCAG 2.1 for graphics)."""
    assert "const route = (stage, pairs, only) =>" in app_map.SCRIPT and "curve(" not in app_map.SCRIPT
    # Only the lines in view are routed, so they never go round hidden ones; and the map can take the whole window.
    assert "if (key !== laid) { laid = key; layout(wanted); }" in app_map.SCRIPT
    # At rest a label shows only where it touches nothing; hidden, it wins over every other rule.
    assert "const tight = best.clash > 0 && labels.length > 1;" in app_map.SCRIPT
    assert ".am .am-main .am-label.tight { opacity:0 !important; }" in app_map.build_css(
        charts.get_palette(charts.THEMES[0])
    )
    assert 'class="am-fullbtn"' in app_map.build_map_html(charts.get_palette(charts.THEMES[0]), {})
    # A description never covers the drawing: beside the map, in the corner clear of the piece and its partners, or, on
    # the whole screen, in a column of its own.
    assert "if (window.innerWidth - box.right - room * 2 >= width)" in app_map.SCRIPT
    assert ".am.am-full::after {" in app_map.build_css(charts.get_palette(charts.THEMES[0]))
    # A narrow window (a tablet, a phone) keeps the same drawing, scaled down: no layout of its own.
    assert (
        "const DESIGN = 820;" in app_map.SCRIPT
        and "grid-template-columns:1fr 1fr !important" not in app_map.build_css(charts.get_palette(charts.THEMES[0]))
    )
    # Parallel lines keep apart, and a head always lands on the logo (a side or its top), never under a name.
    assert "near[axis][n] ? NEAR : 0" in app_map.SCRIPT and "whole.bottom" not in app_map.SCRIPT
    markup = app_map.build_map_html(charts.get_palette(charts.THEMES[0]), {})
    # D-467: no owner boxes and no shaded bands, whose edges crossed the lines; a row keeps only its name
    assert 'class="am-shade' not in markup and 'class="am-own' not in markup and markup.count('class="am-band"') == 2
    assert " C" not in app_map.SCRIPT.split("const smooth")[1].split("};")[0]
    for theme in charts.THEMES:
        palette = charts.get_palette(theme)
        colors = app_map.line_colors(palette)
        assert len(colors) == len(app_map.LINKS) == len(set(colors)), theme
        assert min(charts.contrast_ratio(color, palette["background"]) for color in colors) >= 3, theme
        markup = app_map.build_map_html(palette, {})
        assert all(color in markup for color in colors), theme


def test_d441_every_card_has_its_five_parts_and_a_decision_that_exists(facts):
    without = set()
    for key in app_map.NODES:
        owner, rhythm, fail, why, decisions = app_map_detail.CARDS[key]
        # A person does not fail: its card says how it gets in.
        assert (fail or owner == "persona") and why and rhythm in {key for key, _ in app_map_detail.RHYTHMS} | {""}, key
        for reference in decisions:
            assert app_map_detail.read_decision(reference), (key, reference)
        if not decisions:
            without.add(key)
        card = app_map.build_card(key, facts, {})
        for part in ("Qué hace", "Por qué lo hice así") + (() if owner == "persona" else ("Si algo falla",)):
            assert part in card, (key, part)
        for label, value, command in app_map_detail.numbers_of(key, facts):
            assert label and value and command, (key, label)
    # The pieces with no decision of their own say so on the card instead of borrowing one.
    assert without == {"web", "charts", "ai"}


def test_d441_every_piece_but_a_person_has_an_inside_and_its_lines_join_its_pieces(facts):
    assert INSIDES_ASKED <= set(app_map_detail.INSIDES) <= set(app_map.NODES) - PEOPLE
    for key in app_map_detail.INSIDES:
        for state in (facts, dict(facts, database=None)):  # without the database it still draws: «no verificado aquí»
            inside = app_map_detail.INSIDES[key](state)
            ids = [item["id"] for _, items in inside["columns"] for item in items]
            assert ids and len(ids) == len(set(ids)), key
            assert all(a in ids and b in ids for a, b, _, _ in inside["links"]), key
        assert f'data-inside="{key}"' in app_map.build_inside(key, facts, charts.get_palette(charts.THEMES[0]))


def test_d441_the_magnifier_of_a_tool_shows_how_the_tool_itself_works(facts):
    """A tool's magnifier opens on how the tool works (DuckDB's engine, dbt's graph…), with GreenOcean's figures, and
    keeps a second view with what it does here; its pieces form one chain, so the order reads left to right."""
    assert set(app_map_detail.ENGINES) == TOOLS
    palette = charts.get_palette(charts.THEMES[0])
    for key in TOOLS:
        for state in (facts, dict(facts, database=None)):
            inside = app_map_detail.ENGINES[key](state)
            ids = [item["id"] for _, items in inside["columns"] for item in items]
            assert len(ids) == len(set(ids)) and all(a in ids and b in ids for a, b, _, _ in inside["links"]), key
            heads = [items[0]["id"] for _, items in inside["columns"]]
            assert [(a, b) for a, b, _, dash in inside["links"] if not dash] == list(zip(heads, heads[1:])), key
        views = [view for view, _, _ in app_map.inside_views(key, facts)]
        assert views[0] == "engine", key
        markup = app_map.build_inside(key, facts, palette)
        assert ('class="am-vbtn on" data-view="engine"' in markup) == (len(views) > 1), key
    # The magnifier sits on every piece that has an inside, so it is found without opening the card first.
    for key in app_map.NODES:
        has_inside = bool(app_map.inside_views(key, facts))
        markup = app_map.build_node(key, palette)
        assert (f'class="am-lupa" data-inside="{key}"' in markup) == has_inside, key
        assert f'class="am-info" data-card="{key}"' in markup, key  # and the «i» of its card, on every piece
    from bi import sql_explorer

    duckdb_engine = app_map.build_inside("duckdb", facts, palette)
    assert f"{sql_explorer.TIMEOUT_SECONDS} s" in duckdb_engine and "read_only=True" in duckdb_engine


def test_d441_a_workflow_inside_follows_its_file_and_every_line_runs_straight(facts):
    for name in ("semanal.yml", "calidad.yml"):
        inside = app_map_detail.inside_workflow(facts, name)
        place = {
            item["id"]: (column, item["row"])
            for column, (_, items) in enumerate(inside["columns"])
            for item in items
            if "row" in item
        }
        steps = [step for _, found in facts["workflows"][name]["jobs"] for step in found]
        assert len(inside["links"]) == len(steps)  # the trigger, then each step after the one before
        for a, b, _, _ in inside["links"]:
            assert place[a][0] == place[b][0] or place[a][1] == place[b][1], (name, a, b)
    # pruebas.yml: its two jobs run side by side, each from the trigger.
    inside = app_map_detail.inside_pruebas(facts)
    assert [b for a, b, _, _ in inside["links"] if a == "on"] == [items[0]["id"] for _, items in inside["columns"][1:]]
    # The steps of semanal.yml carry the same Spanish names as the CI/CD diagram.
    names = [item["name"] for _, items in app_map_detail.inside_semanal(facts)["columns"] for item in items]
    assert "dbt build" in names and "Publicar" in names and "Publish the database" not in names


def test_d441_each_rhythm_moves_its_own_chain_and_the_people_lines_never_cross():
    rhythms = {key for key, _ in app_map_detail.RHYTHMS}
    assert {link[5] for link in app_map.LINKS} == rhythms
    assert set(app_map_detail.RHYTHM_OWNER) == rhythms and set(app_map_detail.RHYTHM_OWNER.values()) <= set(
        app_map.NODES
    )
    # Each person sits on the row of the piece it reaches, so the access lines run straight across.
    for person in PEOPLE:
        targets = [target for source, target, *_ in app_map.LINKS if source == person and target != "github"]
        row = app_map.NODES[person][3][0]
        assert targets and all(app_map.NODES[target][3][0] in (row, "flow") for target in targets), person
    rows = [app_map.ROWS[app_map.NODES[person][3][0]] for person in ("visitor", "professional", "author")]
    assert rows == sorted(rows)
    # «Cada martes» has too many lines to move at once: it moves in the steps of the walk, and every one of its lines has
    # its step, once.
    phases = app_map.rhythm_phases()
    week = sorted(index for step in phases["week"] for index in step)
    assert week == [index for index, link in enumerate(app_map.LINKS) if link[5] == "week"]
    assert all(phases[rhythm] == [] for rhythm in rhythms - {"week"})


def test_d441_the_tuesday_walk_follows_the_real_sequence(facts):
    steps = app_map.tour_steps(facts)
    assert len(steps) == len(app_map.TOUR) and all(text and nodes for text, nodes, _ in steps)
    for _, nodes, links in steps:
        assert set(nodes) <= set(app_map.NODES) and all(0 <= index < len(app_map.LINKS) for index in links)
    first = [next(number for number, (_, nodes, _) in enumerate(steps) if node in nodes) for node in WALK]
    assert first == sorted(first) and len(set(first)) == len(first)
    if facts["database"]:
        assert str(app_map_detail.count_kind(facts, "test")) in " ".join(text for text, _, _ in steps)


def test_d467_the_data_travels_its_real_way_one_line_at_a_time_and_a_description_opens_on_its_i():
    """D-467, D-468: at rest the map tells the weekly load in the order semanal.yml really runs, one line at a time, each
    line blinking on its turn with what it does under the map (no moving dot); the description of a piece opens with a
    click on its «i», never under the cursor, and while it is open nothing moves. The «i» and the magnifier sit on the
    logo's corners."""
    steps = app_map.story_steps()
    pairs = [app_map.LINKS[index][:2] for index, _ in steps]
    # D-469: it starts where the load starts: GitHub Actions runs semanal.yml on Tuesday
    assert pairs[:4] == [("github", "semanal"), ("pypi", "semanal"), ("release", "semanal"), ("semanal", "agent")]
    assert pairs[-2:] == [("visitor", "streamlit"), ("professional", "streamlit")]
    order = [pair for pair in pairs]
    position = order.index
    assert position(("odepa", "agent")) < position(("agent", "sqlite")) < position(("sqlite", "parquet"))
    assert position(("sqlite", "parquet")) < position(("ine", "agent")) < position(("parquet", "dbt"))
    assert position(("dbt", "duckdb")) < position(("semanal", "ci")) < position(("duckdb", "release"))
    # D-470: the gate of etl/pipeline.py (late sources, too few rows) runs right after dbt, before the database is written
    assert position(("gates", "dbt")) < position(("gates", "release")) < position(("dbt", "duckdb"))
    assert position(("duckdb", "release")) < position(("semanal", "calidad")) < position(("github", "stcloud"))
    assert position(("github", "stcloud")) < position(("release", "streamlit")) < position(("visitor", "streamlit"))
    script, css = app_map.SCRIPT, app_map.build_css(charts.get_palette(charts.THEMES[0]))
    assert "else { on = !!told && told[0] === index; }" in script  # one line at a time
    assert ".am-msg { display:none !important; }" in css and "animation:am-blink" in css  # it shows, nothing travels
    # D-469: at rest one line at a time: it shows, it goes, a pause, and the next
    assert (
        ".am.telling .am-main .am-line:not(.blink)" in css
        and "else { show = !!state.story && state.story[0] === index; }" in script
    )
    assert "setTimeout(tell, tale.at === 0 ? 1600 : 450)" in script
    assert ".am-node.tipped .am-tip { display:grid; }" in css and ":hover .am-tip" not in css
    assert "svg.pauseAnimations()" in script and "!state.tip" in script
    assert ".am-info { position:absolute; top:3px; right:calc(50% + 7px);" in css
    markup = app_map.build_map_html(charts.get_palette(charts.THEMES[0]), {})
    assert "data-story=" in markup
