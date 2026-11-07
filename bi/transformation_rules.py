"""«Reglas de transformación» (D-523): what the pipeline does to the data of ODEPA and the INE, and why.

Anyone reviewing the project reads here what each rule fixes in the source and what would happen without it, with
real examples; the RN and D numbers and the code are the backing, not the explanation. The rules live in
docs/arquitectura/reglas_transformacion.json, in both languages. A code reference is a text of the file, so its line
is worked out when the page is drawn and never goes stale; only the Autor gets it as a link to the repository (D-500).
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from bi import charts, doc_views, project, static_files

# region Constants and variables
ROOT = Path(__file__).resolve().parent.parent
RULES_FILE = ROOT / "docs" / "arquitectura" / "reglas_transformacion.json"
PIPELINE_TAB, CALCULATIONS_TAB = "pipeline", "calculos"
# (layer, tab, name, where it runs, logo kind and name, centre of the drawing, dots per row)
LAYERS: tuple[tuple[str, str, tuple[str, str], tuple[str, str], tuple[str, str], int, int], ...] = (
    (
        "ingesta",
        PIPELINE_TAB,
        ("Ingesta", "Ingestion"),
        ("etl/raw.db · bronce", "etl/raw.db · bronze"),
        ("brand", "python"),
        250,
        5,
    ),
    ("staging", PIPELINE_TAB, ("Staging", "Staging"), ("dbt Core", "dbt Core"), ("brand", "dbt"), 455, 5),
    ("intermedio", PIPELINE_TAB, ("Intermedio", "Intermediate"), ("dbt Core", "dbt Core"), ("brand", "dbt"), 680, 7),
    ("marts", PIPELINE_TAB, ("Marts", "Marts"), ("dbt Core", "dbt Core"), ("brand", "dbt"), 905, 5),
    (
        "publicacion",
        PIPELINE_TAB,
        ("Publicación", "Publication"),
        ("Base DuckDB · etl/datos.duckdb", "DuckDB database · etl/datos.duckdb"),
        ("brand", "duckdb"),
        1095,
        3,
    ),
    (
        "sql",
        CALCULATIONS_TAB,
        ("Indicadores en SQL", "SQL indicators"),
        ("bi/queries.sql", "bi/queries.sql"),
        ("brand", "duckdb"),
        400,
        5,
    ),
    (
        "panel",
        CALCULATIONS_TAB,
        ("Cálculos del panel", "Panel calculations"),
        ("Python", "Python"),
        ("brand", "python"),
        760,
        9,
    ),
)
# What stands at the two ends of each drawing, carrying no rule: (name, where, logo, centre).
ENDS: dict[str, tuple[tuple[tuple[str, str], tuple[str, str], tuple[str, str], int], ...]] = {
    PIPELINE_TAB: (
        (("ODEPA", "ODEPA"), ("precios", "prices"), ("source", "odepa"), 50),
        (("INE", "INE"), ("IPC de alimentos", "food CPI"), ("source", "ine"), 128),
        (("Panel web", "Web panel"), ("Streamlit", "Streamlit"), ("brand", "streamlit"), 1262),
    ),
    CALCULATIONS_TAB: (
        (("Base DuckDB", "DuckDB database"), ("etl/datos.duckdb", "etl/datos.duckdb"), ("brand", "duckdb"), 110),
        (
            ("Panel web", "Web panel"),
            ("«Semanal» · «Análisis» · Excel", "«Semanal» · «Análisis» · Excel"),
            ("brand", "streamlit"),
            1150,
        ),
    ),
}
WIDTH, ICON_Y, ICON, NAME_Y, WHERE_Y, DOTS_Y, ROW, PITCH, DOT = 1320, 34, 46, 80, 96, 118, 25, 25, 10.5
HEIGHT = DOTS_Y + 2 * ROW - 6
TEXTS = {
    "tab_pipeline": ("Reglas del pipeline", "Pipeline rules"),
    "tab_calculations": ("Cálculos e indicadores", "Calculations and indicators"),
    "problem": ("Qué problema resuelve", "What problem it solves"),
    "without": ("Si no existiera", "If it did not exist"),
    "example": ("En la práctica", "In practice"),
    "inference": ("Inferencia", "Inference"),
    "inference_note": (
        "Inferencia: una lectura que calza con los precios, pero que ODEPA no declara.",
        "Inference: a reading that fits the prices, but that ODEPA does not state.",
    ),
    "same_package_note": (
        "Regla del mismo envase: una variación compara solo los envases vendidos las dos semanas. Los precios que solo "
        "cambiaron de envase quedan fuera de la comparación.",
        "Same-package rule: a variation compares only the packages sold both weeks. Prices that only changed package "
        "are left out of the comparison.",
    ),
    "uses": ("Usa la regla del mismo envase", "Uses the same-package rule"),
    "uses_short": ("usa la regla", "uses the rule"),
    "not_uses": ("No usa la regla del mismo envase", "Does not use the same-package rule"),
    "not_uses_short": ("no la usa", "does not use it"),
    "backing": ("Respaldo", "Backing"),
    "where": ("Dónde actúa", "Where it acts"),
    "all": ("Ver todas", "See all"),
    "rule": ("Regla", "Rule"),
    "rules": ("reglas", "rules"),
}
# endregion


# region «Reglas de transformación»
def pick(pair: Any, language: str) -> str:
    return pair[1] if language == "en" else pair[0]


def read_rules() -> list[dict[str, Any]]:
    return json.loads(RULES_FILE.read_text(encoding="utf-8"))["reglas"]


def locate(path: str, anchor: str, root: Path = ROOT) -> int | None:
    """The line of a text in a file of the repository: references that move with the code."""
    file = root / path
    if not file.exists():
        return None
    for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
        if anchor in line:
            return number
    return None


def code_reference(reference: dict[str, str], author: bool) -> dict[str, str]:
    """D-500: everyone reads where the code is; only the Autor gets the link to the repository."""
    line = locate(reference["archivo"], reference["ancla"])
    text = f'{reference["archivo"]}:{line}' if line else reference["archivo"]
    found = {"text": text}
    if author:
        found["href"] = f'{project.GITHUB_URL}/blob/main/{reference["archivo"]}' + (f"#L{line}" if line else "")
    return found


def build_rules_data(language: str, author: bool) -> list[dict[str, Any]]:
    """The rules as the page reads them: one language, and the code with its current line."""
    built = []
    for rule in read_rules():
        layer = next(entry for entry in LAYERS if entry[0] == rule["capa"])
        built.append(
            {
                "n": rule["n"],
                "layer": rule["capa"],
                "tab": layer[1],
                "layerName": pick(layer[2], language),
                "title": pick(rule["titulo"], language),
                "problem": pick(rule["problema"], language),
                "without": pick(rule["sin_ella"], language),
                "example": pick(rule["ejemplo"], language) if rule.get("ejemplo") else None,
                "inference": pick(rule["inferencia"], language) if rule.get("inferencia") else None,
                "whyNot": pick(rule["por_que_no"], language) if rule.get("por_que_no") else None,
                "uses": rule.get("usa_mismo_envase"),
                "backing": rule["respaldo"],
                "code": [code_reference(reference, author) for reference in rule["codigo"]],
            }
        )
    return built


def place_logo(logo: tuple[str, str], x: float) -> str:
    """A mark of the app, without a background, centred at x on the row of the icons."""
    mark = doc_views.flat_logo(*logo)
    attributes = f'x="{x - ICON / 2}" y="{ICON_Y - ICON / 2}" width="{ICON}" height="{ICON}"'
    return re.sub(r'<svg class="logo"', f'<svg class="logo" {attributes}', mark, count=1)


def build_end(end: tuple[Any, ...], language: str) -> str:
    name, where, logo, x = end
    return (
        f'<g class="end">{place_logo(logo, x)}'
        f'<text class="name" x="{x}" y="{NAME_Y}" text-anchor="middle">{html.escape(pick(name, language))}</text>'
        f'<text class="where" x="{x}" y="{WHERE_Y}" text-anchor="middle">{html.escape(pick(where, language))}</text></g>'
    )


def build_layer(entry: tuple[Any, ...], rules: list[dict[str, Any]], language: str) -> str:
    key, _, name, where, logo, x, per_row = entry
    mine = [rule for rule in rules if rule["layer"] == key]
    dots = []
    for index, rule in enumerate(mine):
        row, column = divmod(index, per_row)
        in_row = min(per_row, len(mine) - row * per_row)
        cx = x + (column - (in_row - 1) / 2) * PITCH
        cy = DOTS_Y + row * ROW
        kind = "inferred" if rule["inference"] else "uses" if rule["uses"] else "plain" if rule["uses"] is False else ""
        dots.append(
            f'<g class="dot {kind}" data-rule="{rule["n"]}" tabindex="0" role="button">'
            f'<title>{rule["n"]} · {html.escape(rule["title"])}</title>'
            f'<circle cx="{cx}" cy="{cy}" r="{DOT}"/>'
            f'<text x="{cx}" y="{cy + 3.4}" text-anchor="middle">{rule["n"]}</text></g>'
        )
    return (
        f'<g class="layer" data-layer="{key}" tabindex="0" role="button">{place_logo(logo, x)}'
        f'<text class="name" x="{x}" y="{NAME_Y}" text-anchor="middle">{html.escape(pick(name, language))}</text>'
        f'<text class="where" x="{x}" y="{WHERE_Y}" text-anchor="middle">{html.escape(pick(where, language))}</text>'
        f'</g>{"".join(dots)}'
    )


def build_diagram(tab: str, rules: list[dict[str, Any]], language: str) -> str:
    """Where each rule acts: the marks in the order the data goes through them, joined by straight arrows, and under
    each layer its rules. A drawing that scales as a whole, so no text can reach another (D-440)."""
    layers = [entry for entry in LAYERS if entry[1] == tab]
    ends = ENDS[tab]
    stops = sorted([entry[5] for entry in layers] + [end[3] for end in ends])
    if tab == PIPELINE_TAB:  # ODEPA and the INE enter together
        stops = [stop for stop in stops if stop != ends[0][3]]
    arrows = "".join(
        f'<path class="arrow" d="M{start + ICON / 2 + 8} {ICON_Y} H{end - ICON / 2 - 12}" marker-end="url(#rule-head-{tab})"/>'
        for start, end in zip(stops, stops[1:])
    )
    return (
        f'<svg class="map" viewBox="0 0 {WIDTH} {HEIGHT}" role="group" aria-label="{html.escape(pick(TEXTS["where"], language))}">'
        f'<defs><marker id="rule-head-{tab}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="head"/></marker></defs>'
        f'{arrows}{"".join(build_end(end, language) for end in ends)}'
        f'{"".join(build_layer(entry, rules, language) for entry in layers)}</svg>'
    )


def build_css(palette: dict[str, str]) -> str:
    dark = palette["base"] == charts.BASE_DARK
    green, amber = ("#3dd68c", "#f5b84b") if dark else ("#1f8f5f", "#a16207")
    muted = charts.legible(palette["reference"], palette["background"])
    return f"""<style>
:root{{--bg:{palette['background']};--panel:{palette['card']};--fg:{palette['strong_text']};--text:{palette['text']};
  --muted:{muted};--line:{palette['card_border']};--accent:{palette['accent']};--green:{green};--amber:{amber};
  color-scheme:{'dark' if dark else 'light'}}}
*{{box-sizing:border-box}}
html,body{{height:100%;margin:0}}
body{{background:var(--bg);color:var(--text);font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;display:flex;flex-direction:column;gap:8px;padding:0 2px 6px}}
code{{font:11.5px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--fg)}}
.tabs{{display:flex;gap:18px;border-bottom:1px solid var(--line);flex:none}}
.tabs button{{all:unset;cursor:pointer;padding:5px 0;color:var(--muted);font-size:13px;border-bottom:2px solid transparent;margin-bottom:-1px}}
.tabs button:hover{{color:var(--fg)}}
.tabs button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.tabs button[aria-selected="true"]{{color:var(--fg);border-color:var(--accent)}}
section{{display:flex;flex-direction:column;gap:6px;flex:1;min-height:0}}
section[hidden]{{display:none}}
.map{{display:block;width:100%;height:auto;max-height:30vh;flex:none;overflow:visible}}
.map text{{font-family:inherit}}
.map .name{{font-size:13.5px;font-weight:600;fill:var(--fg)}}
.map .where{{font-size:10.5px;fill:var(--muted)}}
.map .arrow{{stroke:var(--muted);stroke-width:1.3;fill:none}}
.map .head{{fill:var(--muted)}}
.map .layer{{cursor:pointer;outline:none}}
.map .layer .logo{{transition:filter .15s}}
.map .layer:hover .name,.map .layer.on .name{{fill:var(--accent)}}
.map .layer.on .logo{{filter:drop-shadow(0 0 7px var(--accent))}}
.map .dot{{cursor:pointer;outline:none}}
.map .dot circle{{fill:var(--panel);stroke:var(--line);stroke-width:1.2;transition:fill .12s,stroke .12s}}
.map .dot text{{font-size:9.5px;font-weight:500;fill:var(--text);pointer-events:none}}
.map .dot:hover circle,.map .dot:focus-visible circle{{stroke:var(--accent)}}
.map .dot.inferred circle{{stroke:var(--amber);stroke-dasharray:3 2}}
.map .dot.uses circle{{stroke:var(--green)}}
.map .dot.uses text{{fill:var(--green)}}
.map .dot.plain text{{fill:var(--muted)}}
.map .dot.on circle{{fill:var(--accent);stroke:var(--accent)}}
.map .dot.on text{{fill:{palette['on_accent']};font-weight:600}}
.note{{margin:0;font-size:11.5px;color:var(--muted);flex:none}}
.note i{{font-style:normal;color:var(--amber)}}
.note b{{font-weight:500;color:var(--green)}}
.split{{display:flex;gap:16px;flex:1;min-height:0;border-top:1px solid var(--line);padding-top:8px}}
.list{{flex:0 0 38%;overflow:auto;scrollbar-width:thin;scrollbar-color:var(--line) transparent;padding-right:6px}}
.group{{display:flex;justify-content:space-between;gap:8px;margin:8px 0 2px;font-size:11px;color:var(--muted)}}
.group:first-child{{margin-top:0}}
.group button{{all:unset;cursor:pointer;color:var(--accent);font-size:11px}}
.item{{all:unset;box-sizing:border-box;display:flex;gap:8px;width:100%;cursor:pointer;padding:3px 7px;border-radius:6px;
  font-size:12.5px;line-height:1.35;color:var(--text)}}
.item:hover{{background:color-mix(in srgb,var(--accent) 9%,transparent)}}
.item:focus-visible{{outline:2px solid var(--accent)}}
.item[aria-current="true"]{{background:color-mix(in srgb,var(--accent) 16%,transparent);color:var(--fg)}}
.item .n{{flex:0 0 19px;text-align:right;color:var(--muted);font-variant-numeric:tabular-nums}}
.item .t{{flex:1}}
.item .m{{flex:none;font-size:10.5px}}
.item .m.inferred{{color:var(--amber)}}
.item .m.uses{{color:var(--green)}}
.item .m.plain{{color:var(--muted)}}
.detail{{flex:1;overflow:auto;scrollbar-width:thin;scrollbar-color:var(--line) transparent;padding:0 8px 8px 4px;min-width:0}}
.detail h2{{margin:0 0 1px;font-size:16px;font-weight:600;color:var(--fg);letter-spacing:-.005em}}
.detail .kicker{{margin:0 0 9px;font-size:11px;color:var(--muted)}}
.block{{margin:0 0 9px}}
.block h3{{margin:0 0 1px;font-size:11px;font-weight:500;color:var(--muted)}}
.block p{{margin:0;font-size:13.5px;color:var(--text);max-width:82ch}}
.block.inference{{border-left:2px solid var(--amber);padding-left:9px}}
.block.inference h3{{color:var(--amber)}}
.block.uses{{border-left:2px solid var(--green);padding-left:9px}}
.block.uses h3{{color:var(--green)}}
.block.plain{{border-left:2px solid var(--line);padding-left:9px}}
.backing{{margin:10px 0 0;padding-top:7px;border-top:1px solid var(--line);font-size:11px;color:var(--muted)}}
.backing a{{color:var(--accent)}}
.backing code{{font-size:10.5px;color:var(--muted)}}
.backing a code{{color:var(--accent)}}
@media (max-width:760px){{.map .where{{display:none}}}}
@media (max-width:820px){{html,body{{height:auto}}.split{{flex-direction:column}}.list{{flex:none;max-height:40vh}}.map{{max-height:none}}}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>"""


SCRIPT = static_files.read("transformation_rules.js")  # D-543: the code lives in bi/static/transformation_rules.js


def build_page_html(palette: dict[str, str], language: str, author: bool) -> str:
    """The whole page as one document for st.iframe: it changes rule and layer in the browser, without a rerun."""
    rules = build_rules_data(language, author)
    say = {key: pick(pair, language) for key, pair in TEXTS.items()}
    payload = {
        "rules": rules,
        "labels": {
            "problem": say["problem"],
            "without": say["without"],
            "example": say["example"],
            "inference": say["inference"],
            "uses": say["uses"],
            "notUses": say["not_uses"],
            "sameRule": say["same_package_note"],
            "backing": say["backing"],
            "where": say["where"],
            "all": say["all"],
        },
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return (
        f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"{build_css(palette)}</head><body>"
        '<nav class="tabs" role="tablist">'
        f'<button type="button" role="tab" aria-selected="true" data-tab="{PIPELINE_TAB}">{html.escape(say["tab_pipeline"])}</button>'
        f'<button type="button" role="tab" aria-selected="false" data-tab="{CALCULATIONS_TAB}">{html.escape(say["tab_calculations"])}</button>'
        "</nav>"
        f'<section data-tab="{PIPELINE_TAB}">{build_diagram(PIPELINE_TAB, rules, language)}'
        f'<p class="note"><i>◆</i> {html.escape(say["inference_note"])}</p>'
        '<div class="split"><div class="list"></div><article class="detail"></article></div></section>'
        f'<section data-tab="{CALCULATIONS_TAB}" hidden>{build_diagram(CALCULATIONS_TAB, rules, language)}'
        f'<p class="note"><b>●</b> {html.escape(say["uses_short"])} · ○ {html.escape(say["not_uses_short"])} · '
        f'{html.escape(say["same_package_note"])}</p>'
        '<div class="split"><div class="list"></div><article class="detail"></article></div></section>'
        f'<script type="application/json" id="data">{data}</script><script>{SCRIPT}</script></body></html>'
    )


# endregion
