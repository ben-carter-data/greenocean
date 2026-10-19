"""Lineage of the data warehouse as dbt built it (step 4 of the refonte).

etl/pipeline.py copies the manifest and the results of the last dbt build into the
serving database (tables dbt_node and dbt_result). This module turns them into:
- the DAG of the project, one column per layer (bronze → staging → intermediate → marts),
  each model with its materialization and the state of its tests;
- the matrix «business rule → dbt tests → state» of Calidad y auditoría;
- the one-line lineage badge at the foot of every page.
Nothing here is typed by hand: a new model or test appears on the next build.
"""
import html
import json
import re

import pandas as pd

from bi import architecture, brand_icons, charts, control, tech_glossary

LAYERS = [("bronze", "Bronce", "Parquet"), ("staging", "Staging", "vistas"),
          ("intermediate", "Intermedio", "tablas"), ("marts", "Marts", "servidas al panel")]
MATERIALIZED = {"view": "vista", "table": "tabla", "": "parquet"}
PASSING = {"pass", "success"}
# The colours, logos and pieces of the journey diagram (bi/architecture.py), so the
# lineage reads as its zoom: orange Parquet bronze, violet dbt models, pink tested marts
# and, at the end, the gold data warehouse they feed.
LAYER_COLORS = {"bronze": architecture.LAYER_COLORS["bronze"],
                "staging": architecture.LAYER_COLORS["processing"],
                "intermediate": architecture.LAYER_COLORS["processing"],
                "marts": architecture.LAYER_COLORS["quality"],
                "serving": architecture.LAYER_COLORS["gold"]}
# Glossary entries (bi/tech_glossary.py) shown on hover over each layer header, and
# over the materialization written under each model.
LAYER_KEYS = {"bronze": "bronze", "staging": "stg", "intermediate": "int", "marts": "marts"}
MATERIALIZED_KEYS = {"vista": "view", "tabla": "table", "parquet": "parquet"}
LAYER_LOGOS = {"bronze": "apacheparquet", "staging": "dbt", "intermediate": "dbt", "marts": "dbt",
               "serving": "duckdb"}
# Title and subtitle of each layer frame, as the journey names its columns.
FRAME_TITLES = {"bronze": ("BRONCE", "Parquet · {count} fuentes"),
                "staging": ("STAGING", "dbt · {count} vistas"),
                "intermediate": ("INTERMEDIO", "dbt · {count} tablas"),
                "marts": ("MARTS", "dbt · {count} modelos y pruebas"),
                "serving": ("ORO", "DuckDB · servida al panel")}
# The tile icon of each node, from the journey's own set: the Parquet and dbt logos
# for the files and the views, and a picture of what each table does after them.
NODE_ICONS = {"int_prices__validated": architecture.draw_funnel_icon,
              "int_prices__units_normalized": architecture.draw_sliders_icon,
              "int_prices__weekly": architecture.draw_clock_icon,
              "int_prices__outlier_flagged": architecture.draw_warning_icon,
              "weekly_price": architecture.draw_chart_icon,
              "dim_date": architecture.draw_clock_icon,
              "rejection": architecture.draw_warning_icon,
              "ipc_monthly": architecture.draw_report_icon,
              "ipc_weekly": architecture.draw_sliders_icon,
              "ine_ipc_source": architecture.draw_file_icon}
LAYER_ICONS = {"bronze": architecture.draw_parquet_icon, "staging": architecture.draw_dbt_icon,
               "intermediate": architecture.draw_dbt_icon, "marts": architecture.draw_database_icon}
# The chip of the links that leave each layer, as on the journey.
LAYER_CHIPS = {"bronze": "sources", "staging": "stg_*", "intermediate": "int_*", "marts": "OK"}

TILE = 48           # the journey's 64 px tile, at three quarters
PITCH = 66          # one row: a tile and the gap under it
TOP = 40            # above the frames: the dbt bracket, as the journey frames dbt
HEAD = 62           # frame title and subtitle, above the first row
PAD = 16            # inside a frame, around its nodes
GAP = 78            # between two frames: room for the links and their chip
SIDE = 14
NAME_SIZE = 14
SERVING_WIDTH = 200

# What each rule guarantees, in the words of the PRD. A singular test carries its rule
# in its name (rn14_…, rnf05_…, d155_…); generic tests are grouped by what they check.
RULES = {
    "RN-01": "Precios legibles y positivos",
    "RN-03 a RN-05": "Unidades normalizadas a kilo, unidad o litro",
    "RN-05 y RN-12": "Marcas de unidad no convertible y de precio atípico",
    "RN-11": "Cada rechazo con un motivo conocido",
    "RN-14": "Un solo precio por semana, producto, región, canal y unidad",
    "RNF-05": "Leídas = cargadas + rechazadas",
    "D-042": "Ninguna semana falta sin explicación",
    "D-155": "Un IPC por mes, un deflactor por semana",
    "Modelo estrella": "Claves únicas, no nulas y con su dimensión",
}
ACCEPTED_VALUES_RULES = {"normalized_unit": "RN-03 a RN-05", "flag": "RN-05 y RN-12", "reason": "RN-11",
                         "real_factor": "D-155"}


# region Reading
def read_tables(run_sql):
    """(nodes, results) from the serving database; empty frames before the first build."""
    try:
        nodes = run_sql("SELECT * FROM dbt_node")
        results = run_sql("SELECT * FROM dbt_result")
    except Exception:  # a database built before step 4 has no dbt tables
        return pd.DataFrame(), pd.DataFrame()
    nodes["depends_on"] = nodes["depends_on"].map(json.loads)
    return nodes, results


def rule_of_test(test):
    """The business rule a dbt test checks."""
    if test["test_type"] == "singular":
        match = re.match(r"(rnf|rn|d)(\d+)_", test["name"])
        if match:
            prefix, number = match.groups()
            code = f"{prefix.upper()}-{number}"
            if code == "D-155" or code in RULES:
                return code
    if test["test_type"] == "accepted_values" and test["column_name"] in ACCEPTED_VALUES_RULES:
        return ACCEPTED_VALUES_RULES[test["column_name"]]
    if any(model.endswith((".ipc_monthly", ".ipc_weekly")) for model in test["depends_on"]):
        return "D-155"
    return "Modelo estrella"


def tests_by_model(nodes, results):
    """{model unique_id: (tests, passing)}: a test counts for every model it reads."""
    status = dict(zip(results["unique_id"], results["status"])) if not results.empty else {}
    counts = {}
    for test in nodes[nodes["resource_type"] == "test"].to_dict("records"):
        for model in test["depends_on"]:
            total, passing = counts.get(model, (0, 0))
            counts[model] = (total + 1, passing + (status.get(test["unique_id"]) in PASSING))
    return counts
# endregion


# region Matrix and badge
def build_rule_matrix(nodes, results):
    """One row per rule: what it guarantees, how many dbt tests check it, their state."""
    if nodes.empty:
        return pd.DataFrame(columns=["Regla", "Qué garantiza", "Pruebas dbt", "Estado"])
    status = dict(zip(results["unique_id"], results["status"])) if not results.empty else {}
    rows = {}
    for test in nodes[nodes["resource_type"] == "test"].to_dict("records"):
        rule = rule_of_test(test)
        total, passing = rows.get(rule, (0, 0))
        rows[rule] = (total + 1, passing + (status.get(test["unique_id"]) in PASSING))
    order = list(RULES)
    return pd.DataFrame([{"Regla": rule, "Qué garantiza": RULES.get(rule, ""), "Pruebas dbt": total,
                          "Estado": "Superada" if passing == total else f"{total - passing} con falla"}
                         for rule, (total, passing) in sorted(rows.items(), key=lambda item: order.index(item[0])
                                                              if item[0] in order else len(order))])


def summarize_build(nodes, results):
    """{models, tests, passing, built_at, ok} of the last dbt build, or None without one."""
    if nodes.empty or results.empty:
        return None
    tests = nodes[nodes["resource_type"] == "test"]["unique_id"]
    test_results = results[results["unique_id"].isin(tests)]
    passing = int(test_results["status"].isin(PASSING).sum())
    models = int((nodes["resource_type"] == "model").sum())
    built = pd.Timestamp(results["generated_at"].max())
    return {"models": models, "tests": len(tests), "passing": passing, "built_at": built,
            "ok": passing == len(tests) and results["status"].isin(PASSING).all()}


def build_badge_html(summary):
    """«dbt · 16 modelos · 31/31 pruebas superadas», or the migration note before a build."""
    if summary is None:
        return '<span class="lineage-badge pending">Linaje dbt: en migración</span>'
    state = "ok" if summary["ok"] else "failed"
    return (f'<span class="lineage-badge {state}" title="Última construcción de dbt: '
            f'{summary["built_at"]:%d-%m-%Y %H:%M} UTC">dbt · {summary["models"]} modelos · '
            f'{summary["passing"]}/{summary["tests"]} pruebas superadas</span>')
# endregion


# region DAG
def tech_tip(svg_part, explanation):
    """A piece that explains its technology on hover (inner title: it wins over the node's)."""
    return architecture.add_tech_explanation(svg_part, explanation)


def order_layers(nodes):
    """{layer: [node records]}. Inside a column a model comes after the models of the
    same layer it reads (the intermediate chain reads top-down); otherwise by the mean
    row of its parents, so the edges between columns cross as little as possible."""
    columns = {layer: [] for layer, _, _ in LAYERS}
    for node in nodes[nodes["resource_type"].isin(["model", "source"])].to_dict("records"):
        if node["layer"] in columns:
            columns[node["layer"]].append(node)
    row = {}
    for layer, _, _ in LAYERS:
        same = {node["unique_id"]: node for node in columns[layer]}
        depth = {}
        def depth_of(node_id):
            if node_id not in depth:
                depth[node_id] = 1 + max((depth_of(parent) for parent in same[node_id]["depends_on"]
                                          if parent in same), default=-1)
            return depth[node_id]
        def weight(node):
            parents = [row[parent] for parent in node["depends_on"] if parent in row]
            return (depth_of(node["unique_id"]), sum(parents) / len(parents) if parents else 0, node["name"])
        columns[layer].sort(key=weight)
        for index, node in enumerate(columns[layer]):
            row[node["unique_id"]] = index
    return columns


def text_width(text, size):
    """Approximate width in SVG units of a bold label (Source Sans Pro)."""
    return len(text) * size * 0.5


def measure_pill(label, mark=None, slug=None):
    """Width of a pill: its label, plus its mark or its logo."""
    return 12 + len(label) * 5.6 + (9 if mark else 0) + (16 if slug else 0)


def build_pill(x, y, label, palette, explanation, mark=None, mark_color=None, slug=None):
    """A pill of the journey's technology row (architecture.build_stack_badge): the
    same field, border, logo and type, or a coloured mark before the label."""
    width = measure_pill(label, mark, slug)
    cursor = x + 6
    parts = [f'<rect x="{x:.1f}" y="{y - 8:.1f}" width="{width:.1f}" height="16" rx="8" '
             f'fill="{palette["field"]}" stroke="{palette["card_border"]}" stroke-width="1"/>']
    if slug:
        parts.append(brand_icons.logo(slug, cursor, y - 6.5, palette["text"], 13))
        cursor += 16
    if mark:
        parts.append(f'<text x="{cursor:.1f}" y="{y + 3.3:.1f}" font-size="9.5" font-weight="700" '
                     f'fill="{mark_color}">{mark}</text>')
        cursor += 9
    parts.append(f'<text x="{cursor:.1f}" y="{y + 3.3:.1f}" font-size="9.5" font-weight="600" '
                 f'fill="{palette["text"]}">{html.escape(label)}</text>')
    return tech_tip("".join(parts), explanation), width


def node_pills(kind, total, passing):
    """(label, mark, ok, logo) of the pills under a node: how it is stored, its tests."""
    pills = [(kind, None, None, "apacheparquet" if kind == "parquet" else "dbt")]
    if total:
        pills.append((f"{passing}/{total}", "✓" if passing == total else "✗", passing == total, None))
    return pills


def node_width(node, kind, total, passing):
    """Tile, name and pills of a node, from the tile's left edge to the end of its text."""
    pills = sum(measure_pill(label, mark, slug) + 5 for label, mark, _, slug in node_pills(kind, total, passing))
    return TILE + 10 + max(text_width(node["name"], NAME_SIZE), pills - 5)


def node_tooltip(node, kind, total, passing, reads):
    """What the model does (its dbt description), how it is stored, its tests, what it reads."""
    stored = {"vista": "vista de dbt (se calcula al leerla)", "tabla": "tabla de dbt",
              "parquet": "archivos Parquet de bronce, fuente de dbt"}.get(kind, kind)
    origin = ("los CSV del IPC que descarga etl/ine.py" if node["name"].startswith("ine")
              else "raw.db, con los CSV de ODEPA que descarga agent/agent.py")
    lines = [node["name"], (node["description"] or "").strip(), f"Materialización: {stored}",
             f"Pruebas: {passing} de {total} superadas" if total else "Pruebas: ninguna propia",
             f"Lee: {', '.join(reads) if reads else origin}"]
    return "\n".join(line for line in lines if line)


def build_frame(x, y, width, height, layer, count, palette):
    """A layer in the journey's dashed, tinted frame, with its logo, name and subtitle."""
    color = LAYER_COLORS[layer]
    title, subtitle = FRAME_TITLES[layer]
    subtitle = subtitle.format(count=count)
    center = x + width / 2
    title_width = len(title) * 13 * 0.62 + len(title)
    slug = LAYER_LOGOS[layer]
    logo = brand_icons.logo(slug, center - title_width / 2 - 24, y + 11, color, 18)
    explanation = tech_glossary.describe(LAYER_KEYS[layer]) if layer in LAYER_KEYS else TOOLTIPS_SERVING
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="14" '
            f'fill="{color}" fill-opacity=".07" stroke="{color}" stroke-opacity=".7" '
            f'stroke-width="1.4" stroke-dasharray="6 4"/>'
            + tech_tip(logo, tech_glossary.describe(tech_glossary.LOGO_KEYS[slug]))
            + tech_tip(f'<text x="{center:.1f}" y="{y + 25:.1f}" text-anchor="middle" font-size="13" '
                       f'font-weight="700" letter-spacing="1" fill="{color}">{title}</text>', explanation)
            + tech_tip(f'<text x="{center:.1f}" y="{y + 44:.1f}" text-anchor="middle" font-size="12" '
                       f'fill="{palette["text"]}">{html.escape(subtitle)}</text>',
                       tech_glossary.describe_words(subtitle)))


TOOLTIPS_SERVING = architecture.TOOLTIPS["datos.duckdb"]


def build_dbt_bracket(left, right, summary):
    """The journey's dbt frame label over the three dbt layers: these are the three
    steps of the journey that this view opens model by model."""
    color = architecture.LAYER_COLORS["processing"]
    label = "dbt CORE · staging → intermedio → marts"
    if summary:
        label += f" · {summary['models']} modelos · {summary['passing']}/{summary['tests']} pruebas"
    center = (left + right) / 2
    half = len(label) * 12 * 0.3 + 12
    y = TOP - 18
    line = (f'<path d="M{left + 14:.1f} {TOP:.1f} V{y:.1f} H{center - half:.1f} M{center + half:.1f} {y:.1f} '
            f'H{right - 14:.1f} V{TOP:.1f}" fill="none" stroke="{color}" stroke-opacity=".7" stroke-width="1.4" '
            f'stroke-dasharray="6 4"/>')
    text = (f'<text x="{center:.1f}" y="{y + 4:.1f}" text-anchor="middle" font-size="12" font-weight="700" '
            f'letter-spacing=".6" fill="{color}">{html.escape(label)}</text>')
    return line + tech_tip(text, tech_glossary.describe("dbt"))


def build_lineage_node(x, y, node, layer, kind, total, passing, reads, palette):
    """A model as a journey step: the tile with its icon and status dot, its name beside
    it and, under the name, the journey's pills (materialization, tests)."""
    color = LAYER_COLORS[layer]
    half = TILE / 2
    left = x - half
    draw_icon = NODE_ICONS.get(node["name"], LAYER_ICONS[layer])
    scale = TILE / architecture.TILE_SIZE
    parts = [f'<rect x="{left:.1f}" y="{y - half:.1f}" width="{TILE}" height="{TILE}" rx="12" '
             f'fill="{palette["card"]}" stroke="{color}" stroke-width="1.5"/>',
             f'<g transform="translate({x:.1f} {y:.1f}) scale({scale}) translate({-x:.1f} {-y:.1f})">'
             f'{architecture.draw_tile_icon(draw_icon, x, y, color)}</g>',
             f'<text x="{left + TILE + 10:.1f}" y="{y - 4:.1f}" font-size="{NAME_SIZE}" font-weight="700" '
             f'fill="{palette["strong_text"]}">{html.escape(node["name"])}</text>']
    cursor = left + TILE + 10
    for label, mark, ok, slug in node_pills(kind, total, passing):
        if mark:
            explanation = (f"Pruebas de dbt que leen {node['name']}: {passing} de {total} superadas "
                           "en la última construcción.")
            mark_color = architecture.STATE_COLORS[control.RUN_OK if ok else control.RUN_FAILED]
        else:
            explanation = tech_glossary.describe(MATERIALIZED_KEYS[label]) if label in MATERIALIZED_KEYS else ""
            mark_color = None
        pill, width = build_pill(cursor, y + 13, label, palette, explanation, mark, mark_color,
                                 None if mark else slug)
        parts.append(pill)
        cursor += width + 5
    # The journey's status dot: only a model with tests has a real state.
    if total:
        state = control.RUN_OK if passing == total else control.RUN_FAILED
        parts.append(f'<circle cx="{x + half - 4:.1f}" cy="{y - half + 4:.1f}" r="7" '
                     f'fill="{architecture.STATE_COLORS[state]}" stroke="{palette["card"]}" stroke-width="2.5"/>')
    return architecture.add_tooltip("".join(parts), node_tooltip(node, kind, total, passing, reads))


def flow_dot(path, color, index):
    """A dot travelling along a link, like the journey's (hidden with reduced motion)."""
    return (f'<circle class="journey-flow" r="3.5" fill="{color}"><animateMotion dur="2.4s" '
            f'begin="-{index * .37 % 2.4:.2f}s" repeatCount="indefinite" path="{path}"/></circle>')


def build_lineage_svg(nodes, results, mode):
    """The dbt part of the journey, model by model, in the journey's own language: one
    dashed frame per layer, each model as a tile with its icon and status dot, the
    journey's pills and chips, data flowing along the links, and the marts flowing
    into datos.duckdb, the gold node where the journey goes on."""
    palette = charts.get_palette(mode)
    columns = order_layers(nodes)
    counts = tests_by_model(nodes, results)
    names = dict(zip(nodes["unique_id"], nodes["name"]))
    by_id = {node["unique_id"]: node for items in columns.values() for node in items}
    layer_of = {node["unique_id"]: layer for layer, items in columns.items() for node in items}
    kind_of = {node_id: MATERIALIZED.get(node["materialized"], node["materialized"]) for node_id, node in by_id.items()}
    tallest = max((len(items) for items in columns.values()), default=1)
    centered = {layer: (tallest - len(items)) * PITCH / 2 for layer, items in columns.items()}
    # Bronze and staging sit a row and a half above the intermediate chain: the IPC
    # branch, which skips that chain, then runs clear above it instead of behind it.
    lifted = max(0, centered["intermediate"] - 1.5 * PITCH)
    frame_height = HEAD + tallest * PITCH - (PITCH - TILE) + 2 * PAD - 6
    first_row = TOP + HEAD + PAD - 6 + TILE / 2
    # One frame per layer, as wide as its widest model, then the gold column.
    frames, cursor = {}, SIDE
    for layer, _, _ in LAYERS:
        widths = [node_width(node, kind_of[node["unique_id"]], *counts.get(node["unique_id"], (0, 0)))
                  for node in columns[layer]] or [TILE]
        frames[layer] = (cursor, max(widths) + 2 * PAD)
        cursor += frames[layer][1] + GAP
    frames["serving"] = (cursor, SERVING_WIDTH)
    width = cursor + SERVING_WIDTH + SIDE
    height = TOP + frame_height + 14
    position = {}
    for layer, _, _ in LAYERS:
        offset = lifted if layer in ("bronze", "staging") else centered[layer]
        for row, node in enumerate(columns[layer]):
            position[node["unique_id"]] = (frames[layer][0] + PAD + TILE / 2, first_row + offset + row * PITCH)
    serving = (frames["serving"][0] + SERVING_WIDTH / 2, first_row + (tallest - 1) * PITCH / 2)
    ends = {node_id: x - TILE / 2 + node_width(by_id[node_id], kind_of[node_id], *counts.get(node_id, (0, 0))) + 8
            for node_id, (x, _) in position.items()}

    parts = [f'<svg viewBox="0 0 {width:.0f} {height:.0f}" width="100%" role="img" '
             f'aria-label="Linaje dbt: de bronce a marts" font-family="{charts.CHART_FONT}">',
             architecture.build_style(False),
             '<defs>' + "".join(
                 f'<marker id="lineage-arrow-{layer}" viewBox="0 0 6 6" refX="3" refY="5" markerWidth="6" '
                 f'markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L3,6 L6,0" fill="none" '
                 f'stroke="{color}" stroke-width="1.3"/></marker>' for layer, color in LAYER_COLORS.items()) + '</defs>']
    for layer, _, _ in LAYERS:
        x, frame_width = frames[layer]
        parts.append(build_frame(x, TOP, frame_width, frame_height, layer, len(columns[layer]), palette))
    parts.append(build_frame(frames["serving"][0], TOP, SERVING_WIDTH, frame_height, "serving", 1, palette))
    summary = summarize_build(nodes, results)
    parts.append(build_dbt_bracket(frames["staging"][0], sum(frames["marts"]), summary))

    # Links: out of a model along its row to the frame's edge, a curve across the gap
    # (straight through a frame it skips, above the intermediate chain), into the tile.
    links, chips, flow = [], {}, 0
    for node_id, (x, y) in position.items():
        for parent in by_id[node_id]["depends_on"]:
            if parent not in position:
                continue
            px, py = position[parent]
            color = LAYER_COLORS[layer_of[parent]]
            if layer_of[parent] == layer_of[node_id]:
                # Inside a column only the chain shows, as a short arrow to the tile
                # below; the relations among marts are the star of Modelo de datos.
                if abs(y - (py + PITCH)) < 1:
                    links.append(f'<path d="M{x:.1f},{py + TILE / 2 + 2:.1f} V{y - TILE / 2 - 3:.1f}" '
                                 f'stroke="{color}" stroke-width="1.6" marker-end="url(#lineage-arrow-{layer_of[parent]})"/>')
                continue
            target = x - TILE / 2
            gap_left = target - PAD - GAP
            gap_right = target - PAD
            middle = (gap_left + gap_right) / 2
            path = (f"M{ends[parent]:.1f} {py:.1f} H{gap_left:.1f} C{middle:.1f} {py:.1f} {middle:.1f} {y:.1f} "
                    f"{gap_right:.1f} {y:.1f} H{target:.1f}")
            links.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.6" opacity="0.85"/>'
                         + flow_dot(path, color, flow))
            flow += 1
            chips.setdefault(layer_of[parent], []).append((middle, (py + y) / 2, color))
    # The marts flow into the data warehouse, as on the journey after «Marts y pruebas».
    gold_left = serving[0] - architecture.TILE_SIZE / 2
    for node_id in [node["unique_id"] for node in columns["marts"]]:
        _, y = position[node_id]
        gap_left = frames["serving"][0] - GAP
        middle = gap_left + GAP / 2
        path = (f"M{ends[node_id]:.1f} {y:.1f} H{gap_left:.1f} C{middle:.1f} {y:.1f} {middle:.1f} {serving[1]:.1f} "
                f"{frames['serving'][0]:.1f} {serving[1]:.1f} H{gold_left:.1f}")
        color = LAYER_COLORS["marts"]
        links.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.6" opacity="0.85"/>'
                     + flow_dot(path, color, flow))
        flow += 1
    chips["marts"] = [(frames["serving"][0] - GAP / 2, serving[1], LAYER_COLORS["marts"])]
    parts.extend(links)
    # One chip per gap, on the link closest to the middle of its bundle, as the journey
    # names what travels between two steps.
    for layer, spots in chips.items():
        mean = sum(spot[1] for spot in spots) / len(spots)
        x, y, color = min(spots, key=lambda spot: abs(spot[1] - mean))
        parts.append(architecture.build_chip(x, y, LAYER_CHIPS[layer], color, palette))
    for node_id, (x, y) in position.items():
        total, passing = counts.get(node_id, (0, 0))
        reads = [names[parent] for parent in by_id[node_id]["depends_on"] if parent in names]
        parts.append(build_lineage_node(x, y, by_id[node_id], layer_of[node_id], kind_of[node_id],
                                        total, passing, reads, palette))
    state = None if summary is None else control.RUN_OK if summary["ok"] else control.RUN_FAILED
    detail = (f"{summary['passing']}/{summary['tests']} pruebas" if summary else "sin construcción")
    parts.append(architecture.build_node(serving[0], serving[1], "gold", architecture.draw_duckdb_icon,
                                         "datos.duckdb", ["capa oro · modelo estrella", detail], palette, state))
    parts.append("</svg>")
    return "".join(parts)
# endregion
