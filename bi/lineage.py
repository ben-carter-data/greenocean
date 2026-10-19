"""Lineage of the data warehouse as dbt built it (step 4 of the refonte).

etl/pipeline.py copies the manifest and the results of the last dbt build into the
serving database (tables dbt_node and dbt_result). This module turns them into:
- the DAG of the project, one column per layer (bronze → staging → intermediate → marts
  → the gold datos.duckdb), each model as a tile with its materialization and the state
  of its tests, the links routed along buses between the columns; hovering a model
  follows only its inputs and outputs (LINEAGE_SCRIPT), a click pins them;
- the matrix «business rule → dbt tests → state» of Calidad y auditoría;
- the one-line lineage badge at the foot of every page.
Nothing here is typed by hand: a new model or test appears on the next build.
"""
import colorsys
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
# Title and subtitle of each column, as the journey names its steps.
FRAME_TITLES = {"bronze": ("FUENTES", "Parquet · {count} tablas"),
                "staging": ("STAGING", "dbt · {count} vistas"),
                "intermediate": ("INTERMEDIO", "dbt · {count} tablas"),
                "marts": ("MARTS", "dbt · {count} modelos y pruebas"),
                "serving": ("SERVING", "DuckDB · servida al panel")}
# The explanation of each column title: the bronze column holds the dbt sources.
HEADER_KEYS = dict(LAYER_KEYS, bronze="sources")
# The medallion containers, left to right: (key, its columns, what it holds, left, right).
# Bronze is the Parquet copy, silver the dbt staging and intermediate models, gold the
# marts and the datos.duckdb they are copied to. Each is named on a tab on its top edge.
MEDALLION = [("bronze", ("bronze",), "Parquet", 12, 220),
             ("silver", ("staging", "intermediate"), "Transformación dbt", 232, 1000),
             ("gold", ("marts", "serving"), "Marts → datos.duckdb", 1012, 1588)]
MEDALLION_TOP = 44
MEDALLION_BOTTOM = 748
# The tile icon of each node, from the journey's own set: the dbt logo for the views,
# and a picture of what each table does after them.
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

# Geometry of the drawing (SVG units): five columns, the marts set the rows.
WIDTH = 1600
HEIGHT = 800
SIDE = 18
SUBTITLE_Y = 21        # the line «dbt Core · staging → intermedio → marts · …»
HEADER_Y = 80          # baseline of a column title; its subtitle goes 19 below
FIRST_ROW = 156        # centre of the highest model
LAST_ROW = 700         # lowest centre a model may take
MART_PITCH = 70
LEGEND_Y = 772
TILE = 54
GOLD = 92
NAME_SIZE = 14
PORT = 9               # intermediate links run over the tile's name, 9 above its centre
COLUMN_X = {"bronze": 92, "staging": 352, "intermediate": 604, "marts": 1114, "serving": 1494}
HEADER_X = {"bronze": 40, "staging": 304, "intermediate": 562, "marts": 1074, "serving": 1392}
DIVIDERS = [478, 1378]  # inside silver and gold, between their two columns
STAGING_BUS = 524      # where the staging views meet before the intermediate chain
MART_LANE = 1046       # where a model turns down or up to its marts
GOLD_BUS = 1346        # where the marts meet before datos.duckdb
LANE_STEP = 14
MIN_GAP = {"bronze": 190, "staging": 190, "intermediate": 116}
BELOW = ("bronze", "staging")   # name under the tile; the dbt tables carry it beside
LIT = {"dark": "#ff5ca8", "light": "#d6337a"}
FLOW_SECONDS = 3.6
HINT = ("Pasa el mouse por un modelo para seguir únicamente sus entradas y salidas. "
        "Haz clic para fijar el recorrido.")
GOLD_ID = "datos.duckdb"

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


GENERIC_TEST_PREFIXES = ("not_null_", "unique_", "relationships_", "accepted_values_")


def owner_of_test(test, models):
    """The one model a test belongs to, so each test counts once and the badges add up
    to the total of the build. A generic test belongs to the model of its column, which
    dbt writes in its name (relationships_weekly_price_week_start__… → weekly_price);
    a singular test to its only model, or to weekly_price, the fact it guards, or else to
    the first model it reads (rnf05 → int_prices__validated). Sources never own a test."""
    reads = [node for node in test["depends_on"] if node in models]
    name = test["name"]
    for prefix in GENERIC_TEST_PREFIXES:
        if name.startswith(prefix):
            rest = name[len(prefix):]
            owners = [node for node in reads if rest.startswith(models[node] + "_")]
            if owners:
                return max(owners, key=lambda node: len(models[node]))
    fact = [node for node in reads if models[node] == "weekly_price"]
    return (reads[0] if len(reads) == 1 else fact[0] if fact else reads[0]) if reads else None


def tests_by_model(nodes, results):
    """{model unique_id: (tests, passing)}: each test counts once, for its own model."""
    status = dict(zip(results["unique_id"], results["status"])) if not results.empty else {}
    models = dict(zip(nodes.loc[nodes["resource_type"] == "model", "unique_id"],
                      nodes.loc[nodes["resource_type"] == "model", "name"]))
    counts = {}
    for test in nodes[nodes["resource_type"] == "test"].to_dict("records"):
        model = owner_of_test(test, models)
        if model is None:
            continue
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


def depth_in_layer(columns):
    """{node id: how many models of its own layer it reads through} (0 for the first)."""
    depth = {}
    for items in columns.values():
        same = {node["unique_id"]: node for node in items}

        def depth_of(node_id):
            if node_id not in depth:
                depth[node_id] = 1 + max((depth_of(parent) for parent in same[node_id]["depends_on"]
                                          if parent in same), default=-1)
            return depth[node_id]
        for node_id in same:
            depth_of(node_id)
    return depth


def order_layers(nodes):
    """{layer: [node records]}. Inside a column a model comes after the models of the
    same layer it reads (the intermediate chain reads top-down); otherwise by the mean
    row of its parents, so the edges between columns cross as little as possible."""
    columns = {layer: [] for layer, _, _ in LAYERS}
    for node in nodes[nodes["resource_type"].isin(["model", "source"])].to_dict("records"):
        if node["layer"] in columns:
            columns[node["layer"]].append(node)
    depth = depth_in_layer(columns)
    row = {}
    for layer, _, _ in LAYERS:
        def weight(node):
            parents = [row[parent] for parent in node["depends_on"] if parent in row]
            return depth[node["unique_id"]], sum(parents) / len(parents) if parents else 0, node["name"]
        columns[layer].sort(key=weight)
        for index, node in enumerate(columns[layer]):
            row[node["unique_id"]] = index
    return columns


def place_rows(ids, wishes, gap):
    """Centres of one column, in order: each as close to its wish (the mean row of what it
    feeds) as the gap to the one above allows, all inside the drawing."""
    rows = []
    for node_id in ids:
        wish = wishes.get(node_id)
        if not rows:
            rows.append(max(FIRST_ROW, wish if wish is not None else FIRST_ROW))
        else:
            rows.append(max(rows[-1] + gap, wish if wish is not None else rows[-1] + gap))
    for index in range(len(rows) - 1, -1, -1):  # too low: slide back up, keeping the gap
        rows[index] = min(rows[index], LAST_ROW - (len(rows) - 1 - index) * gap)
    return dict(zip(ids, rows))


def lay_out(columns):
    """{node id: (x, y)}. The marts set the rows; every other column sits level with what
    it feeds, so most links run straight. Twice: the marts then follow their parents."""
    layer_of = {node["unique_id"]: layer for layer, items in columns.items() for node in items}
    children = {node_id: [] for node_id in layer_of}
    for items in columns.values():
        for node in items:
            for parent in node["depends_on"]:
                if parent in children:
                    children[parent].append(node["unique_id"])
    depth = depth_in_layer(columns)
    marts = [node["unique_id"] for node in columns["marts"]]
    y = {}
    for _ in range(2):
        pitch = min(MART_PITCH, (LAST_ROW - FIRST_ROW) / max(1, len(marts) - 1))
        y.update({node_id: FIRST_ROW + index * pitch for index, node_id in enumerate(marts)})
        for layer in ("intermediate", "staging", "bronze"):
            ids = [node["unique_id"] for node in columns[layer]]
            wishes = {}
            for node_id in ids:
                fed = [y[child] for child in children[node_id] if layer_of[child] != layer and child in y]
                if fed:
                    wishes[node_id] = sum(fed) / len(fed) + (PORT if layer == "intermediate" else 0)
            y.update(place_rows(ids, wishes, MIN_GAP[layer]))
        parents_of = {node["unique_id"]: [y[parent] for parent in node["depends_on"]
                                          if parent in y and layer_of[parent] != "marts"]
                      for node in columns["marts"]}
        before = {node_id: index for index, node_id in enumerate(marts)}
        marts.sort(key=lambda node_id: (depth[node_id], sum(parents_of[node_id]) / len(parents_of[node_id])
                                        if parents_of[node_id] else LAST_ROW, before[node_id]))
    return {node_id: (COLUMN_X[layer_of[node_id]], y[node_id]) for node_id in layer_of}


def text_width(text, size):
    """Approximate width in SVG units of a bold label (Source Sans Pro or its fallback)."""
    return len(text) * size * 0.56


def mix(color, other, share):
    """color moved share of the way towards other (both #rrggbb)."""
    first = [int(color[index:index + 2], 16) for index in (1, 3, 5)]
    second = [int(other[index:index + 2], 16) for index in (1, 3, 5)]
    return "#" + "".join(f"{round(a + (b - a) * share):02x}" for a, b in zip(first, second))


def measure_pill(label, mark=None, slug=None):
    """Width of a pill: its label, plus its mark or its logo."""
    return 14 + len(label) * 5.9 + (10 if mark else 0) + (17 if slug else 0)


def build_pill(x, y, label, palette, explanation, mark=None, mark_color=None, slug=None):
    """A pill of the journey's technology row (architecture.build_stack_badge): the
    same field, border, logo and type, or a coloured mark before the label."""
    width = measure_pill(label, mark, slug)
    cursor = x + 7
    parts = [f'<rect x="{x:.1f}" y="{y - 9:.1f}" width="{width:.1f}" height="18" rx="9" '
             f'fill="{palette["field"]}" stroke="{palette["card_border"]}" stroke-width="1"/>']
    if slug:
        parts.append(brand_icons.logo(slug, round(cursor, 1), round(y - 6.5, 1), palette["strong_text"], 13))
        cursor += 17
    if mark:
        parts.append(f'<text x="{cursor:.1f}" y="{y + 3.6:.1f}" font-size="10.5" font-weight="700" '
                     f'fill="{mark_color}">{mark}</text>')
        cursor += 10
    parts.append(f'<text x="{cursor:.1f}" y="{y + 3.6:.1f}" font-size="10" font-weight="600" '
                 f'fill="{palette["strong_text"]}">{html.escape(label)}</text>')
    return tech_tip("".join(parts), explanation), width


def node_pills(kind, total, passing):
    """(label, mark, ok, logo) of the pills under a node: how it is stored, its tests."""
    pills = [(kind, None, None, "apacheparquet" if kind == "parquet" else "dbt")]
    if total:
        pills.append((f"{passing}/{total}", "✓" if passing == total else "✗", passing == total, None))
    return pills


def pills_width(kind, total, passing):
    return sum(measure_pill(label, mark, slug) + 6 for label, mark, _, slug in node_pills(kind, total, passing)) - 6


def node_width(node, kind, total, passing):
    """Name or pills, whichever is wider."""
    return max(text_width(node["name"], NAME_SIZE), pills_width(kind, total, passing))


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


TOOLTIPS_SERVING = architecture.TOOLTIPS["datos.duckdb"]
TILE_KEYS = {"bronze": "bronze", "staging": "dbt", "intermediate": "dbt", "marts": "marts", "serving": "gold"}
TILE_COLORS = {"bronze": LAYER_COLORS["bronze"], "dbt": LAYER_COLORS["staging"],
               "marts": LAYER_COLORS["marts"], "gold": LAYER_COLORS["serving"]}
# The violet and pink tiles shine less than the journey's flat tiles would: 18 % less
# saturation and 10 % less light, and an 18 % softer glow on dark themes.
TONED = ("dbt", "marts")
TONE_SATURATION = .82
TONE_LIGHTNESS = .9
GLOW = {"opacity": .55, "blur": 9}
TONED_GLOW = {"opacity": .45, "blur": 8}
# Links stay quiet until a selection lights its own path.
EDGE_WIDTH = 1.3
EDGE_OPACITY = {"dark": .5, "light": .58}
LIT_WIDTH = 2.4


def is_dark(palette):
    return palette.get("base") == charts.BASE_DARK


def tone(color):
    """color with less saturation and light (TONE_SATURATION, TONE_LIGHTNESS)."""
    red, green, blue = (int(color[index:index + 2], 16) / 255 for index in (1, 3, 5))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    rgb = colorsys.hls_to_rgb(hue, lightness * TONE_LIGHTNESS, saturation * TONE_SATURATION)
    return "#" + "".join(f"{round(value * 255):02x}" for value in rgb)


def tile_color(key):
    """The face colour of a tile: violet and pink toned down, bronze and gold as they are."""
    return tone(TILE_COLORS[key]) if key in TONED else TILE_COLORS[key]


def build_defs(suffix, palette):
    """Gradients of the glossy tiles, their glow (dark themes) or soft shadow (light
    themes), and one arrowhead per link colour."""
    dark = is_dark(palette)
    parts = ['<defs>',
             f'<linearGradient id="lin-gloss-{suffix}" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="#ffffff" stop-opacity=".62"/>'
             '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>']
    for key in TILE_COLORS:
        color = tile_color(key)
        glow = TONED_GLOW if key in TONED else GLOW
        highlight = .3 if key in TONED else .38
        parts.append(f'<linearGradient id="lin-face-{key}-{suffix}" x1="0" y1="0" x2="1" y2="1">'
                     f'<stop offset="0" stop-color="{mix(color, "#ffffff", highlight)}"/>'
                     f'<stop offset=".5" stop-color="{color}"/>'
                     f'<stop offset="1" stop-color="{mix(color, "#000000", .42)}"/></linearGradient>')
        if dark:
            parts.append(f'<filter id="lin-glow-{key}-{suffix}" x="-60%" y="-60%" width="220%" height="220%">'
                         f'<feGaussianBlur in="SourceAlpha" stdDeviation="{glow["blur"]}" result="blur"/>'
                         f'<feFlood flood-color="{color}" flood-opacity="{glow["opacity"]}"/>'
                         '<feComposite in2="blur" operator="in" result="glow"/>'
                         '<feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
        else:
            parts.append(f'<filter id="lin-glow-{key}-{suffix}" x="-40%" y="-40%" width="180%" height="190%">'
                         '<feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#0f172a" '
                         'flood-opacity=".16"/></filter>')
    gold = TILE_COLORS["gold"]
    parts.append(f'<linearGradient id="lin-barrel-{suffix}" x1="0" y1="0" x2="1" y2="0">'
                 f'<stop offset="0" stop-color="{mix(gold, "#000000", .38)}"/>'
                 f'<stop offset=".32" stop-color="{mix(gold, "#ffffff", .42)}"/>'
                 f'<stop offset=".62" stop-color="{gold}"/>'
                 f'<stop offset="1" stop-color="{mix(gold, "#000000", .5)}"/></linearGradient>')
    for key, color in arrow_colors(palette).items():
        size = 9 if key == "lit" else 7
        parts.append(f'<marker id="lin-arrow-{key}-{suffix}" viewBox="0 0 10 10" refX="8.5" refY="5" '
                     f'markerWidth="{size}" markerHeight="{size}" markerUnits="userSpaceOnUse" orient="auto">'
                     f'<path d="M0,0.6 L10,5 L0,9.4 z" fill="{color}"/></marker>')
    parts.append('</defs>')
    return "".join(parts)


def arrow_colors(palette):
    """The colour of each kind of link: the layer it leaves, and the two states of a selection."""
    return {"bronze": LAYER_COLORS["bronze"], "dbt": tile_color("dbt"), "marts": tile_color("marts"),
            "lit": LIT["dark" if is_dark(palette) else "light"], "dim": palette["reference"]}


def build_style(suffix, palette):
    """How a selection looks: its models and links lit, everything else dimmed. The
    classes are toggled by LINEAGE_SCRIPT."""
    lit, dim = arrow_colors(palette)["lit"], arrow_colors(palette)["dim"]
    graph = f".lin-{suffix}"
    halo = "0 0 3px rgba({}, .6)" if is_dark(palette) else "0 0 2px rgba({}, .35)"
    halo = halo.format(", ".join(str(int(lit[index:index + 2], 16)) for index in (1, 3, 5)))
    return f"""<style>
    {graph} .lin-node, {graph} .lin-edge, {graph} .lin-joint {{ transition: opacity .18s ease, stroke .18s ease, fill .18s ease; }}
    {graph} .lin-node {{ cursor: pointer; }}
    {graph} .lin-node:focus {{ outline: none; }}
    {graph} .lin-edge.lin-extra, {graph} .lin-joint.lin-extra {{ opacity: 0; }}
    {graph}.lin-active .lin-node {{ opacity: .2; }}
    {graph}.lin-active .lin-node.lin-on {{ opacity: 1; }}
    {graph}.lin-active .lin-edge {{ stroke: {dim}; opacity: .2; marker-end: url(#lin-arrow-dim-{suffix}); }}
    {graph}.lin-active .lin-edge.lin-on {{ stroke: {lit}; opacity: 1; stroke-width: {LIT_WIDTH};
                                          marker-end: url(#lin-arrow-lit-{suffix}); filter: drop-shadow({halo}); }}
    {graph}.lin-active .lin-joint {{ fill: {dim}; opacity: .2; }}
    {graph}.lin-active .lin-joint.lin-on {{ fill: {lit}; opacity: 1; r: 3.4px; }}
    {graph}.lin-active .lin-extra:not(.lin-on) {{ opacity: 0; }}
    {graph}.lin-active .lin-flow {{ display: none; }}
    {graph}.lin-active .lin-flow.lin-on {{ display: inline; fill: {lit}; opacity: 1; }}
    {graph} .lin-node.lin-focus .lin-face {{ stroke: {lit}; stroke-width: 2.4; stroke-opacity: 1; }}
    @media (prefers-reduced-motion: reduce) {{
      {graph} .lin-flow {{ display: none !important; }}
      {graph} .lin-node, {graph} .lin-edge, {graph} .lin-joint {{ transition: none; }}
    }}
    </style>"""


def build_subtitle(summary, palette):
    """«dbt Core · staging → intermedio → marts · 16 modelos · 31/31 pruebas»."""
    rest = " · staging → intermedio → marts"
    rest += (f" · {summary['models']} modelos · {summary['passing']}/{summary['tests']} pruebas"
             if summary else " · sin construcción")
    text = (f'<text x="{SIDE}" y="{SUBTITLE_Y}" font-size="14"><tspan font-weight="700" '
            f'fill="{LAYER_COLORS["staging"]}">dbt Core</tspan><tspan fill="{palette["text"]}">'
            f'{html.escape(rest)}</tspan></text>')
    return tech_tip(text, tech_glossary.describe("dbt"))


def build_header(layer, count, palette):
    """A column's logo, name in its layer colour and subtitle, as the journey heads its steps."""
    color = LAYER_COLORS[layer]
    ink = color if is_dark(palette) else mix(color, "#000000", .22)
    title, subtitle = FRAME_TITLES[layer]
    subtitle = subtitle.format(count=count)
    x = HEADER_X[layer]
    slug = LAYER_LOGOS[layer]
    explanation = tech_glossary.describe(HEADER_KEYS[layer]) if layer in HEADER_KEYS else TOOLTIPS_SERVING
    logo = brand_icons.logo(slug, x, HEADER_Y - 22, color, 30)
    return (tech_tip(logo, tech_glossary.describe(tech_glossary.LOGO_KEYS[slug]))
            + tech_tip(f'<text x="{x + 40}" y="{HEADER_Y}" font-size="16" font-weight="700" '
                       f'letter-spacing="1.3" fill="{ink}">{title}</text>', explanation)
            + tech_tip(f'<text x="{x + 40}" y="{HEADER_Y + 19}" font-size="12.5" '
                       f'fill="{palette["text"]}">{html.escape(subtitle)}</text>',
                       tech_glossary.describe_words(subtitle)))


def build_dividers(palette):
    """Subtle vertical lines between the columns, no heavy frames."""
    color = palette["card_border"] if is_dark(palette) else palette["grid"]
    return "".join(f'<path d="M{x} {MEDALLION_TOP + 18} V{MEDALLION_BOTTOM - 14}" stroke="{color}" '
                   f'stroke-width="1" stroke-dasharray="3 5" opacity=".7"/>' for x in DIVIDERS)


def build_medallion(palette):
    """Bronze, silver and gold as three sober containers behind the columns, each named
    on a small tab centred on its top edge: «SILVER · Transformación dbt»."""
    parts = []
    for key, _, detail, left, right in MEDALLION:
        color = architecture.medallion_color(key, palette)
        middle = (left + right) / 2
        width = len(key) * 8.4 + (len(detail) + 3) * 6.2 + 22
        parts.append(architecture.build_medallion_band(left, MEDALLION_TOP, right - left,
                                                       MEDALLION_BOTTOM - MEDALLION_TOP, key, palette, 16))
        parts.append(f'<rect x="{middle - width / 2:.1f}" y="{MEDALLION_TOP - 10}" width="{width:.1f}" '
                     f'height="20" rx="10" fill="{palette["card"]}" stroke="{color}" stroke-opacity=".5" '
                     f'stroke-width="1"/>')
        parts.append(architecture.build_medallion_label(middle, MEDALLION_TOP + 4, key, detail, palette))
    return f'<g class="lin-medallion">{"".join(parts)}</g>'


def draw_tile(x, y, key, suffix, palette, size=TILE):
    """A glossy, raised tile: a darker side under it, the face lit from the top left, a
    gloss over its top and a glow (dark themes) or a soft shadow (light themes)."""
    color = TILE_COLORS[key]
    half = size / 2
    return (f'<g filter="url(#lin-glow-{key}-{suffix})">'
            f'<rect x="{x - half + 3:.1f}" y="{y - half + 5:.1f}" width="{size}" height="{size}" rx="13" '
            f'fill="{mix(color, "#000000", .55)}"/>'
            f'<rect class="lin-face" x="{x - half:.1f}" y="{y - half:.1f}" width="{size}" height="{size}" rx="13" '
            f'fill="url(#lin-face-{key}-{suffix})" stroke="{mix(color, "#ffffff", .5)}" stroke-opacity=".75" '
            f'stroke-width="1.2"/>'
            f'<rect x="{x - half + 3:.1f}" y="{y - half + 3:.1f}" width="{size - 6}" height="{size * .44:.1f}" '
            f'rx="10" fill="url(#lin-gloss-{suffix})" opacity=".55"/></g>')


def draw_stack(x, y, suffix):
    """Bronze: four glossy Parquet slabs, one on the other."""
    color = TILE_COLORS["bronze"]
    parts = [f'<g filter="url(#lin-glow-bronze-{suffix})">']
    for level in range(4):
        middle = y + 14 - level * 10
        side = (f"M{x - 26} {middle - 1} L{x} {middle + 9} L{x + 26} {middle - 1} V{middle + 5} "
                f"L{x} {middle + 15} L{x - 26} {middle + 5} Z")
        top = f"M{x} {middle - 11} L{x + 26} {middle - 1} L{x} {middle + 9} L{x - 26} {middle - 1} Z"
        face = ' class="lin-face"' if level == 3 else ""
        parts.append(f'<path d="{side}" fill="{mix(color, "#000000", .4)}"/>'
                     f'<path{face} d="{top}" fill="url(#lin-face-bronze-{suffix})" '
                     f'stroke="{mix(color, "#ffffff", .55)}" stroke-width="1" stroke-opacity=".8"/>')
    top = y + 14 - 30
    parts.append(f'<path d="M{x - 13} {top - 6} L{x + 13} {top + 4} M{x - 13} {top + 4} L{x + 13} {top - 6}" '
                 f'stroke="#ffffff" stroke-opacity=".35" stroke-width="1"/></g>')
    return "".join(parts)


def draw_barrel(x, y, suffix):
    """The gold datos.duckdb: a glossy cylinder with the DuckDB logo on its front."""
    color = TILE_COLORS["gold"]
    rx, ry, top, bottom = 42, 13, y - 32, y + 32
    body = f"M{x - rx} {top} V{bottom} A{rx} {ry} 0 0 0 {x + rx} {bottom} V{top} Z"
    logo = brand_icons.logo("duckdb", x - 18, y - 12, mix(color, "#000000", .72), 36)
    return (f'<g filter="url(#lin-glow-gold-{suffix})">'
            f'<path d="{body}" fill="url(#lin-barrel-{suffix})" stroke="{mix(color, "#ffffff", .35)}" '
            f'stroke-width="1.2"/>'
            f'<path d="M{x - rx} {y + 2} A{rx} {ry} 0 0 0 {x + rx} {y + 2}" fill="none" '
            f'stroke="{mix(color, "#000000", .3)}" stroke-opacity=".5" stroke-width="1"/>'
            f'<ellipse class="lin-face" cx="{x}" cy="{top}" rx="{rx}" ry="{ry}" fill="{mix(color, "#ffffff", .45)}" '
            f'stroke="{mix(color, "#ffffff", .7)}" stroke-width="1.2"/>'
            f'<ellipse cx="{x}" cy="{top}" rx="{rx - 9}" ry="{ry - 4}" fill="{mix(color, "#000000", .12)}" '
            f'opacity=".55"/>'
            f'<rect x="{x - 30}" y="{top + 8}" width="7" height="{bottom - top - 2}" rx="3.5" fill="#ffffff" '
            f'opacity=".28"/></g>'
            + tech_tip(logo, tech_glossary.describe(tech_glossary.LOGO_KEYS["duckdb"])))


def draw_status(x, y, ok, palette):
    """The journey's status dot: green when every test passes, red otherwise."""
    color = architecture.STATE_COLORS[control.RUN_OK if ok else control.RUN_FAILED]
    halo = (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="{color}" opacity=".28"/>'
            if is_dark(palette) else "")
    return halo + (f'<circle class="lin-status" cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="{color}" '
                   f'stroke="{palette["card"]}" stroke-width="2.5"/>')


def build_pill_row(x, y, kind, total, passing, node, palette, centered):
    """Materialization and tests, side by side; centred on x or starting at it."""
    cursor = x - pills_width(kind, total, passing) / 2 if centered else x
    parts = []
    for label, mark, ok, slug in node_pills(kind, total, passing):
        if mark:
            explanation = (f"Pruebas de dbt que leen {node['name']}: {passing} de {total} superadas "
                           "en la última construcción.")
            mark_color = architecture.STATE_COLORS[control.RUN_OK if ok else control.RUN_FAILED]
        else:
            explanation = tech_glossary.describe(MATERIALIZED_KEYS[label]) if label in MATERIALIZED_KEYS else ""
            mark_color = None
        pill, width = build_pill(cursor, y, label, palette, explanation, mark, mark_color, None if mark else slug)
        parts.append(pill)
        cursor += width + 6
    return "".join(parts)


def node_attributes(node_id, up, down):
    """What LINEAGE_SCRIPT reads: the node and its direct inputs and outputs."""
    return (f'class="lin-node" tabindex="0" data-node="{html.escape(node_id)}" '
            f'data-up="{html.escape(" ".join(up))}" data-down="{html.escape(" ".join(down))}"')


def build_lineage_node(x, y, node, layer, kind, total, passing, reads, up, down, palette, suffix):
    """A model: its glossy tile with an icon and status dot, its name (under the tile for
    bronze and staging, beside it for the dbt tables) and its pills."""
    half = TILE / 2
    if layer == "bronze":
        tile = draw_stack(x, y, suffix)
        dot = (x + 26, y - 22)
    else:
        draw_icon = NODE_ICONS.get(node["name"], LAYER_ICONS[layer])
        icon = architecture.draw_tile_icon(draw_icon, x, y, "#ffffff")
        scale = .84 if draw_icon in architecture.ICON_LOGO_SLUG else .8
        tile = (draw_tile(x, y, TILE_KEYS[layer], suffix, palette)
                + f'<g transform="translate({x} {y}) scale({scale}) translate({-x} {-y})" '
                  f'opacity=".96">{icon}</g>')
        dot = (x + half - 1, y - half + 1)
    width = node_width(node, kind, total, passing)
    if layer in BELOW:
        name = (f'<text x="{x}" y="{y + half + 24}" text-anchor="middle" font-size="{NAME_SIZE}" '
                f'font-weight="700" fill="{palette["strong_text"]}">{html.escape(node["name"])}</text>')
        pills = build_pill_row(x, y + half + 44, kind, total, passing, node, palette, True)
        box = (x - width / 2 - 6, y - half - 8, width + 12, TILE + 64)
    else:
        left = x + half + 16
        name_y, pills_y = (y + 15, y + 38) if layer == "intermediate" else (y - 5, y + 16)
        name = (f'<text x="{left}" y="{name_y}" font-size="{NAME_SIZE}" font-weight="700" '
                f'fill="{palette["strong_text"]}">{html.escape(node["name"])}</text>')
        pills = build_pill_row(left, pills_y, kind, total, passing, node, palette, False)
        box = (x - half - 6, y - half - 6, half + 22 + width + 6, max(TILE + 14, pills_y + 12 - (y - half - 6)))
    hit = (f'<rect x="{box[0]:.1f}" y="{box[1]:.1f}" width="{box[2]:.1f}" height="{box[3]:.1f}" rx="10" '
           f'fill="#000" fill-opacity="0"/>')
    status = draw_status(*dot, passing == total, palette) if total else ""
    return (f'<g {node_attributes(node["unique_id"], up, down)}>'
            f'<title>{html.escape(node_tooltip(node, kind, total, passing, reads))}</title>'
            f'{hit}{tile}{status}{name}{pills}</g>')


def build_gold_node(x, y, marts, summary, palette, suffix):
    """datos.duckdb, the gold node where the journey goes on: what every mart feeds."""
    half = GOLD / 2
    detail = f"{summary['passing']}/{summary['tests']} pruebas" if summary else "sin construcción"
    pill, width = build_pill(x - measure_pill("DuckDB", slug="duckdb") / 2, y + half + 40, "DuckDB", palette,
                             tech_glossary.describe(tech_glossary.LOGO_KEYS["duckdb"]), slug="duckdb")
    status = (draw_status(x + 38, y - 40, summary["ok"], palette) if summary else "")
    lines = "".join(f'<text x="{x}" y="{y + half + 70 + index * 18}" text-anchor="middle" font-size="13" '
                    f'fill="{palette["text"]}">{html.escape(line)}</text>'
                    for index, line in enumerate(["capa oro · modelo estrella", detail]))
    hit = (f'<rect x="{x - 92}" y="{y - half - 8}" width="184" height="{GOLD + 108}" rx="12" '
           f'fill="#000" fill-opacity="0"/>')
    return (f'<g {node_attributes(GOLD_ID, marts, [])}><title>{html.escape(TOOLTIPS_SERVING)}</title>{hit}'
            f'{draw_barrel(x, y, suffix)}{status}'
            f'<text x="{x}" y="{y + half + 20}" text-anchor="middle" font-size="16" font-weight="700" '
            f'fill="{palette["strong_text"]}">datos.duckdb</text>{pill}{lines}</g>')


def allocate_lanes(spans, base):
    """{key: x}: one vertical lane per key, its span (top, bottom) never overlapping
    another on the same lane; lanes step left of base."""
    lanes, taken = {}, []
    for key, (top, bottom) in sorted(spans.items(), key=lambda item: item[1]):
        index = 0
        while any(lane == index and top < used_bottom + 12 and bottom > used_top - 12
                  for lane, used_top, used_bottom in taken):
            index += 1
        taken.append((index, top, bottom))
        lanes[key] = base - index * LANE_STEP
    return lanes


def route_edges(position, by_id, layer_of, ends, gold):
    """Every link as orthogonal segments: bronze straight into staging, staging along a
    bus into the intermediate chain, the chain down its column, elbows into the marts and
    the marts along a bus into datos.duckdb. A link inside the marts is drawn only when a
    selection includes it. [(from, to, path, colour key, joints, extra)]."""
    half = TILE / 2

    def port(node_id):
        x, y = position[node_id]
        return y - PORT if layer_of[node_id] == "intermediate" else y

    def out_x(node_id):
        x, _ = position[node_id]
        return ends[node_id] + 8 if layer_of[node_id] == "marts" else x + half + 4

    links = [(parent, node["unique_id"]) for node in by_id.values() for parent in node["depends_on"]
             if parent in position]
    color_key = {"bronze": "bronze", "staging": "dbt", "intermediate": "dbt", "marts": "marts"}
    to_int = {}
    to_marts = {}
    for parent, child in links:
        if layer_of[child] == "intermediate" and layer_of[parent] != "intermediate":
            to_int.setdefault(child, []).append(port(parent))
        if layer_of[child] == "marts" and layer_of[parent] != "marts":
            to_marts.setdefault(parent, []).append(position[child][1])
    int_lanes = allocate_lanes({child: (min(ys + [port(child)]), max(ys + [port(child)]))
                                for child, ys in to_int.items()}, STAGING_BUS)
    mart_lanes = allocate_lanes({parent: (min(ys + [port(parent)]), max(ys + [port(parent)]))
                                 for parent, ys in to_marts.items()}, MART_LANE)
    edges = []
    for parent, child in links:
        (px, _), (cx, cy) = position[parent], position[child]
        start_y, end_y = port(parent), port(child)
        start_x, end_x = out_x(parent), cx - half - 3
        source, target = layer_of[parent], layer_of[child]
        joints, extra = [], False
        if source == target == "intermediate" and position[child][1] > position[parent][1]:
            path = f"M{px} {position[parent][1] + half + 8} V{cy - half - 3}"
        elif source == target:
            # Inside the marts (a fact reading its dimensions): a bracket left of the tiles.
            bulge = 22 + abs(cy - position[parent][1]) / MART_PITCH * 5
            left = px - half - 4
            path = (f"M{left} {position[parent][1] + 6} C{left - bulge} {position[parent][1] + 6} "
                    f"{left - bulge} {cy - 6} {left} {cy - 6}")
            extra = True
        elif target == "intermediate":
            lane = int_lanes[child]
            path = f"M{start_x} {start_y} H{lane} V{end_y} H{end_x}"
            joints = [(lane, start_y), (lane, end_y)] if abs(start_y - end_y) > 1 else []
        elif target == "marts":
            lane = mart_lanes[parent]
            path = f"M{start_x} {start_y} H{lane} V{end_y} H{end_x}"
            joints = [(lane, start_y), (lane, end_y)] if abs(start_y - end_y) > 1 else []
        elif abs(start_y - end_y) < 1:
            path = f"M{start_x} {start_y} H{end_x}"
        else:
            middle = (start_x + end_x) / 2
            path = f"M{start_x} {start_y} H{middle} V{end_y} H{end_x}"
        edges.append((parent, child, path, color_key[source], joints, extra))
    gold_x, gold_y = gold
    for node_id, (x, y) in position.items():
        if layer_of[node_id] == "marts":
            path = f"M{out_x(node_id)} {y} H{GOLD_BUS} V{gold_y} H{gold_x - GOLD / 2 - 10}"
            edges.append((node_id, GOLD_ID, path, "marts", [(GOLD_BUS, y), (GOLD_BUS, gold_y)], False))
    return edges


def build_edges(edges, palette, suffix):
    """Paths (data-from, data-to), their junction dots and, unless the reader asked for
    less motion, one dot of data travelling along each."""
    colors = arrow_colors(palette)
    opacity = EDGE_OPACITY["dark" if is_dark(palette) else "light"]
    paths, joints, flows = [], [], []
    for index, (source, target, path, key, points, extra) in enumerate(edges):
        ends = f'data-from="{html.escape(source)}" data-to="{html.escape(target)}"'
        extra_class = " lin-extra" if extra else ""
        dash = ' stroke-dasharray="4 3"' if extra else ""
        paths.append(f'<path class="lin-edge{extra_class}" {ends} d="{path}" fill="none" stroke="{colors[key]}" '
                     f'stroke-width="{EDGE_WIDTH}" stroke-linejoin="round"{dash} opacity="{opacity}" '
                     f'marker-end="url(#lin-arrow-{key}-{suffix})"/>')
        for x, y in points:
            joints.append(f'<circle class="lin-joint{extra_class}" {ends} cx="{x:.1f}" cy="{y:.1f}" r="2.6" '
                          f'fill="{colors[key]}" opacity="{opacity}"/>')
        if not extra:
            flows.append(f'<circle class="lin-flow" {ends} r="2.2" fill="{colors[key]}" opacity=".6">'
                         f'<animateMotion dur="{FLOW_SECONDS}s" begin="-{index * .53 % FLOW_SECONDS:.2f}s" '
                         f'repeatCount="indefinite" path="{path}"/></circle>')
    return (f'<g class="lin-edges">{"".join(paths)}</g><g class="lin-joints">{"".join(joints)}</g>'
            f'<g class="lin-flows">{"".join(flows)}</g>')


def build_legend(palette, suffix):
    """The hint on the left; what a green dot, a pink and a grey arrow mean on the right."""
    colors = arrow_colors(palette)
    y = LEGEND_Y
    pointer = (f'<path d="M{SIDE + 2} {y - 9} L{SIDE + 2} {y + 7} L{SIDE + 6} {y + 3} L{SIDE + 9} {y + 9} '
               f'L{SIDE + 11.5} {y + 8} L{SIDE + 8.5} {y + 2} L{SIDE + 14} {y + 2} Z" '
               f'fill="{palette["strong_text"]}" opacity=".85"/>')
    hint = (f'<text x="{SIDE + 26}" y="{y + 4.5}" font-size="13" fill="{palette["text"]}">'
            f'{html.escape(HINT)}</text>')
    items = [("dot", "Pruebas superadas"), ("lit", "Dependencia (seleccionada)"), ("dim", "Fuera de la selección")]
    widths = [(14 if kind == "dot" else 40) + text_width(label, 12.5) * .92 for kind, label in items]
    total = sum(widths) + 26 * (len(items) - 1) + 36
    left = WIDTH - SIDE - total
    parts = [f'<rect x="{left:.1f}" y="{y - 17}" width="{total:.1f}" height="34" rx="17" '
             f'fill="{palette["card"]}" fill-opacity=".6" stroke="{palette["card_border"]}"/>']
    cursor = left + 18
    for (kind, label), width in zip(items, widths):
        if kind == "dot":
            parts.append(f'<circle cx="{cursor + 5}" cy="{y}" r="5.5" '
                         f'fill="{architecture.STATE_COLORS[control.RUN_OK]}"/>')
            text_x = cursor + 16
        else:
            parts.append(f'<path d="M{cursor} {y} H{cursor + 30}" stroke="{colors[kind]}" stroke-width="2.2" '
                         f'marker-end="url(#lin-arrow-{kind}-{suffix})"/>')
            text_x = cursor + 40
        parts.append(f'<text x="{text_x:.1f}" y="{y + 4.2}" font-size="12.5" fill="{palette["text"]}">'
                     f'{html.escape(label)}</text>')
        cursor += width + 26
    return f'<g class="lin-legend">{pointer}{hint}{"".join(parts)}</g>'


def build_lineage_svg(nodes, results, mode):
    """The dbt part of the journey, model by model: five columns (bronze, staging,
    intermediate, marts, gold), each model a glossy tile with its icon, status dot and
    pills, the links routed along buses between columns into datos.duckdb. Each node
    carries data-node, data-up and data-down and each link data-from and data-to, so
    LINEAGE_SCRIPT can follow a model's inputs and outputs on hover."""
    palette = charts.get_palette(mode)
    suffix = re.sub(r"[^a-z0-9]", "", str(mode).lower()) or "mode"
    columns = order_layers(nodes)
    counts = tests_by_model(nodes, results)
    names = dict(zip(nodes["unique_id"], nodes["name"]))
    by_id = {node["unique_id"]: node for items in columns.values() for node in items}
    layer_of = {node["unique_id"]: layer for layer, items in columns.items() for node in items}
    kind_of = {node_id: MATERIALIZED.get(node["materialized"], node["materialized"]) for node_id, node in by_id.items()}
    position = lay_out(columns)
    marts = [node_id for node_id in position if layer_of[node_id] == "marts"]
    mart_rows = [position[node_id][1] for node_id in marts] or [(FIRST_ROW + LAST_ROW) / 2]
    gold = (COLUMN_X["serving"], (min(mart_rows) + max(mart_rows)) / 2 - 20)
    ends = {node_id: x + TILE / 2 + 16 + node_width(by_id[node_id], kind_of[node_id], *counts.get(node_id, (0, 0)))
            for node_id, (x, _) in position.items()}
    up = {node_id: [parent for parent in by_id[node_id]["depends_on"] if parent in position] for node_id in position}
    down = {node_id: [] for node_id in position}
    for node_id, parents in up.items():
        for parent in parents:
            down[parent].append(node_id)
    for node_id in marts:
        down[node_id].append(GOLD_ID)
    summary = summarize_build(nodes, results)

    parts = [f'<svg class="lin-graph lin-{suffix}" viewBox="0 0 {WIDTH} {HEIGHT}" width="100%" role="img" '
             f'aria-label="Linaje dbt: de bronce a marts" font-family="{charts.CHART_FONT}">',
             build_style(suffix, palette), build_defs(suffix, palette), build_subtitle(summary, palette),
             build_medallion(palette), build_dividers(palette)]
    for layer, _, _ in LAYERS:
        parts.append(build_header(layer, len(columns[layer]), palette))
    parts.append(build_header("serving", 1, palette))
    parts.append(build_edges(route_edges(position, by_id, layer_of, ends, gold), palette, suffix))
    parts.append('<g class="lin-nodes">')
    for node_id, (x, y) in position.items():
        total, passing = counts.get(node_id, (0, 0))
        reads = [names[parent] for parent in by_id[node_id]["depends_on"] if parent in names]
        parts.append(build_lineage_node(x, y, by_id[node_id], layer_of[node_id], kind_of[node_id], total, passing,
                                        reads, up[node_id], down[node_id], palette, suffix))
    parts.append(build_gold_node(*gold, marts, summary, palette, suffix))
    parts.append('</g>')
    parts.append(build_legend(palette, suffix))
    parts.append("</svg>")
    return "".join(parts)


# Hovering a model lights only its upstream and downstream paths (models and links) and
# dims the rest; a click pins that selection, a click on empty space or Escape clears it.
# One script for the whole page, listening on document, so diagrams Streamlit draws
# later work too. It builds no markup: it only toggles classes (st.html drops a script
# whose strings look like tags). bi/zoom.py TIP_SCRIPT may answer the same click with
# the node's card; both are meant to.
LINEAGE_SCRIPT = r"""<script>
(() => {
if (window.lineageReady) { return; }
window.lineageReady = true;
const GRAPH = 'svg[aria-label="Linaje dbt: de bronce a marts"]';
const split = (text) => (text || "").split(" ").filter(Boolean);

// The graph of one drawing, read once from its data attributes.
const graphOf = (svg) => {
    if (svg.lineageGraph) { return svg.lineageGraph; }
    const up = new Map();
    const down = new Map();
    svg.querySelectorAll("[data-node]").forEach((node) => {
        up.set(node.dataset.node, split(node.dataset.up));
        down.set(node.dataset.node, split(node.dataset.down));
    });
    svg.lineageGraph = {up, down};
    return svg.lineageGraph;
};
// Every node reachable from start along links (transitive inputs or outputs).
const reach = (start, links) => {
    const seen = new Set([start]);
    const queue = [start];
    while (queue.length) {
        for (const next of links.get(queue.pop()) || []) {
            if (!seen.has(next)) { seen.add(next); queue.push(next); }
        }
    }
    return seen;
};

const light = (svg, id) => {
    const graph = graphOf(svg);
    const before = reach(id, graph.up);
    const after = reach(id, graph.down);
    svg.classList.add("lin-active");
    svg.querySelectorAll("[data-node]").forEach((node) => {
        const name = node.dataset.node;
        node.classList.toggle("lin-on", before.has(name) || after.has(name));
        node.classList.toggle("lin-focus", name === id);
    });
    const lit = [];
    svg.querySelectorAll("[data-from]").forEach((part) => {
        const from = part.dataset.from;
        const to = part.dataset.to;
        const on = (before.has(from) && before.has(to)) || (after.has(from) && after.has(to));
        part.classList.toggle("lin-on", on);
        if (on && part.classList.contains("lin-edge")) { lit.push(part); }
    });
    // Lit links over the dimmed ones that share their buses.
    // Nodes never move: Streamlit (React) owns this markup and must find it where it left it.
};
const clear = (svg) => {
    svg.classList.remove("lin-active");
    svg.querySelectorAll(".lin-on, .lin-focus").forEach((part) => part.classList.remove("lin-on", "lin-focus"));
};
const nodeOf = (element) => (element && element.closest ? element.closest("[data-node]") : null);
const graphAround = (element) => (element && element.closest ? element.closest(GRAPH) : null);

document.addEventListener("pointerover", (event) => {
    const node = nodeOf(event.target);
    const svg = graphAround(node);
    if (svg && !svg.dataset.lineagePinned) { light(svg, node.dataset.node); }
});
document.addEventListener("pointerout", (event) => {
    const node = nodeOf(event.target);
    const svg = graphAround(node);
    if (!svg || svg.dataset.lineagePinned) { return; }
    const next = nodeOf(event.relatedTarget);
    if (next && svg.contains(next)) { return; }
    clear(svg);
});
document.addEventListener("click", (event) => {
    const svg = graphAround(event.target);
    if (!svg) { return; }
    const node = nodeOf(event.target);
    if (!node) {
        delete svg.dataset.lineagePinned;
        clear(svg);
    } else if (svg.dataset.lineagePinned === node.dataset.node) {
        delete svg.dataset.lineagePinned;
        light(svg, node.dataset.node);
    } else {
        svg.dataset.lineagePinned = node.dataset.node;
        light(svg, node.dataset.node);
    }
});
// The keyboard: Tab onto a model lights it, Enter pins it, Escape clears.
document.addEventListener("focusin", (event) => {
    const node = nodeOf(event.target);
    const svg = graphAround(node);
    if (svg && !svg.dataset.lineagePinned) { light(svg, node.dataset.node); }
});
document.addEventListener("focusout", (event) => {
    const svg = graphAround(nodeOf(event.target));
    if (svg && !svg.dataset.lineagePinned) { clear(svg); }
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        const node = nodeOf(event.target);
        const svg = graphAround(node);
        if (svg) { svg.dataset.lineagePinned = node.dataset.node; light(svg, node.dataset.node); }
    }
    if (event.key === "Escape") {
        document.querySelectorAll(GRAPH).forEach((svg) => { delete svg.dataset.lineagePinned; clear(svg); });
    }
});

// Streamlit draws the page in steps and redraws it on every rerun: a new drawing
// starts unselected, and its graph is read again on first use.
const prepare = () => document.querySelectorAll(GRAPH).forEach((svg) => {
    if (svg.dataset.lineageReady) { return; }
    svg.dataset.lineageReady = "yes";
    delete svg.lineageGraph;
    clear(svg);
});
prepare();
new MutationObserver(prepare).observe(document.body, {childList: true, subtree: true});
})();
</script>"""
# endregion
