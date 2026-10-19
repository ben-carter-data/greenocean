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

from bi import charts

LAYERS = [("bronze", "Bronce", "Parquet"), ("staging", "Staging", "vistas"),
          ("intermediate", "Intermedio", "tablas"), ("marts", "Marts", "servidas al panel")]
MATERIALIZED = {"view": "vista", "table": "tabla", "": "parquet"}
PASSING = {"pass", "success"}

WIDTH = 1000
TOP = 58
CARD_WIDTH = 200
CARD_HEIGHT = 40
CARD_GAP = 12
SIDE = 20

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


def build_lineage_svg(nodes, results, mode):
    """The DAG: four columns of cards joined by curves, each model with its tests."""
    palette = charts.get_palette(mode)
    columns = order_layers(nodes)
    tallest = max((len(items) for items in columns.values()), default=1)
    height = TOP + tallest * (CARD_HEIGHT + CARD_GAP) + 10
    step = (WIDTH - 2 * SIDE - CARD_WIDTH) / (len(LAYERS) - 1)
    counts = tests_by_model(nodes, results)
    position = {}
    pitch = CARD_HEIGHT + CARD_GAP
    centered = {layer: (tallest - len(items)) * pitch / 2 for layer, items in columns.items()}
    # Bronze and staging sit a row and a half above the intermediate chain: the IPC
    # branch, which skips that chain, then runs clear above it instead of behind it.
    lifted = max(0, centered["intermediate"] - 1.5 * pitch)
    for index, (layer, _, _) in enumerate(LAYERS):
        items = columns[layer]
        offset = lifted if layer in ("bronze", "staging") else centered[layer]
        for row, node in enumerate(items):
            position[node["unique_id"]] = (SIDE + index * step, TOP + offset + row * (CARD_HEIGHT + CARD_GAP))
    accent, line, card, text = palette["accent"], palette["card_border"], palette["card"], palette["text"]
    strong = palette["strong_text"]
    good, bad = charts.STATUS_COLORS["good"], charts.STATUS_COLORS["serious"]
    parts = [f'<svg viewBox="0 0 {WIDTH} {height:.0f}" width="100%" role="img" '
             f'aria-label="Linaje dbt: de bronce a marts" style="font-family:inherit">'
             f'<defs><marker id="lineage-arrow" viewBox="0 0 6 6" refX="3" refY="5" markerWidth="6" '
             f'markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L3,6 L6,0" fill="none" '
             f'stroke="{palette["accent"]}" stroke-width="1.2"/></marker></defs>']
    for index, (_, title, note) in enumerate(LAYERS):
        x = SIDE + index * step + CARD_WIDTH / 2
        parts.append(f'<text x="{x:.0f}" y="22" text-anchor="middle" font-size="14" font-weight="700" '
                     f'fill="{strong}">{title}</text><text x="{x:.0f}" y="40" text-anchor="middle" '
                     f'font-size="11" fill="{text}">{note} · {len(columns[LAYERS[index][0]])}</text>')
    layer_of = {node["unique_id"]: layer for layer, items in columns.items() for node in items}
    for node_id, (x, y) in position.items():
        node = nodes[nodes["unique_id"] == node_id].iloc[0]
        for parent in node["depends_on"]:
            if parent in position and layer_of[parent] == layer_of[node_id]:
                # Inside a column only the chain shows, as a short arrow to the card
                # below; the relations among marts are the star of Modelo de datos.
                px, py = position[parent]
                if abs(y - (py + CARD_HEIGHT + CARD_GAP)) < 1:
                    center = x + CARD_WIDTH / 2
                    parts.append(f'<path d="M{center:.1f},{py + CARD_HEIGHT + 1:.1f} V{y - 2:.1f}" '
                                 f'stroke="{accent}" stroke-width="1.6" marker-end="url(#lineage-arrow)"/>')
            elif parent in position:
                px, py = position[parent]
                x1, y1, x2, y2 = px + CARD_WIDTH, py + CARD_HEIGHT / 2, x, y + CARD_HEIGHT / 2
                middle = (x1 + x2) / 2
                parts.append(f'<path d="M{x1:.1f},{y1:.1f} C{middle:.1f},{y1:.1f} {middle:.1f},{y2:.1f} '
                             f'{x2:.1f},{y2:.1f}" fill="none" stroke="{accent}" stroke-opacity=".35" '
                             'stroke-width="1.3"/>')
    for node_id, (x, y) in position.items():
        node = nodes[nodes["unique_id"] == node_id].iloc[0]
        total, passing = counts.get(node_id, (0, 0))
        kind = MATERIALIZED.get(node["materialized"], node["materialized"])
        chip = ""
        if total:
            color = good if passing == total else bad
            chip = (f'<text x="{x + CARD_WIDTH - 10:.1f}" y="{y + 25:.1f}" text-anchor="end" font-size="11" '
                    f'font-weight="700" fill="{color}">{"✓" if passing == total else "✗"} {passing}/{total}</text>')
        tooltip = html.escape(node["description"] or f"{node['name']} · {kind}")
        parts.append(f'<g><title>{tooltip}</title><rect x="{x:.1f}" y="{y:.1f}" width="{CARD_WIDTH}" '
                     f'height="{CARD_HEIGHT}" rx="9" fill="{card}" stroke="{line}"/>'
                     f'<text x="{x + 10:.1f}" y="{y + 17:.1f}" font-size="11.5" font-weight="600" '
                     f'fill="{strong}">{html.escape(node["name"])}</text>'
                     f'<text x="{x + 10:.1f}" y="{y + 31:.1f}" font-size="10" fill="{text}">{kind}</text>'
                     f'{chip}</g>')
    parts.append("</svg>")
    return "".join(parts)
# endregion
