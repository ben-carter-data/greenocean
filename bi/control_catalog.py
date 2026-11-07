"""«Catálogo de controles» (D-524): every control of the project, what it protects, when it runs and what happens if it
fails, read from docs/calidad/catalogo_controles.json; and, first, the sale units nobody has classified yet."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from bi import charts, transformation_rules, unit_review

# region Constants and variables
CATALOG_FILE = Path(__file__).resolve().parent.parent / "docs" / "calidad" / "catalogo_controles.json"
MOMENTS = {
    "descarga": ("Al descargar", "When downloading"),
    "transformacion": ("Al transformar", "When transforming"),
    "publicacion": ("Antes de publicar", "Before publishing"),
    "despues": ("Después de publicar", "After publishing"),
}
WHEN = {
    "carga": ("Cada carga", "Each load"),
    "tras_carga": ("Tras cada carga en verde", "After each green load"),
    "panel": ("Al abrir el panel", "When the panel opens"),
    "push": ("Cada push", "Each push"),
    "local": ("En cada revisión local", "In each local review"),
}
# (what it does, its colour): the load stops and the published database stays, or the data is marked and the load goes on
OUTCOMES = {
    "detiene": (("Detiene la carga", "Stops the load"), "stop"),
    "conserva": (("Conserva lo anterior", "Keeps the previous one"), "keep"),
    "marca": (("Marca el dato y sigue", "Flags the data and goes on"), "mark"),
    "registra": (("Lo registra y sigue", "Records it and goes on"), "mark"),
    "avisa": (("Avisa", "Warns"), "warn"),
}
TEXTS = {
    "units": ("Unidades de venta de ODEPA", "ODEPA sale units"),
    "reviewed": ("{} revisadas a mano", "{} reviewed by hand"),
    "none_new": ("Ninguna unidad nueva sin clasificar", "No new unit without classification"),
    "some_new": ("{} sin clasificar", "{} not classified"),
    "unknown": (
        "Se sabrá con la próxima carga: la base publicada todavía no guarda sus unidades.",
        "It will be known with the next load: the published database does not keep its units yet.",
    ),
    "units_why": (
        "Cada unidad se lee como se revisó a mano. Una unidad nueva sin clasificar no detiene la carga si es un envase "
        "simple o no recibe precio, pero queda aquí y en el «Informe semanal» hasta que alguien la revise.",
        "Each unit is read as it was reviewed by hand. A new unit does not stop the load if it is a plain package or gets "
        "no price, but it stays here and in the «Informe semanal» until someone reviews it.",
    ),
    "unit": ("Unidad", "Unit"),
    "reading": ("Cómo se lee hoy", "How it reads today"),
    "no_reading": ("sin precio", "no price"),
    "rows": ("Filas", "Rows"),
    "since": ("Desde", "Since"),
    "risk": ("Detiene la carga", "Stops the load"),
    "control": ("Control", "Control"),
    "protects": ("Qué protege", "What it protects"),
    "when": ("Cuándo corre", "When it runs"),
    "fails": ("Si falla", "If it fails"),
    "backing": ("Respaldo", "Backing"),
}
# endregion


# region «Catálogo de controles»
def pick(pair: Any, language: str) -> str:
    return pair[1] if language == "en" else pair[0]


def read_controls() -> list[dict[str, Any]]:
    return json.loads(CATALOG_FILE.read_text(encoding="utf-8"))["controles"]


def describe_reading(unit: dict[str, Any], language: str) -> str:
    if not unit["priced"]:
        return pick(TEXTS["no_reading"], language)
    quantity = float(unit["unit_quantity"])
    written = f"{quantity:g}" if language == "en" else f"{quantity:g}".replace(".", ",")
    return f'÷ {written} = $/{unit["normalized_unit"]}'


def build_units_html(summary: dict[str, Any], language: str) -> str:
    say = {key: pick(pair, language) for key, pair in TEXTS.items()}
    reviewed = say["reviewed"].format(summary["reviewed"])
    if not summary["known"]:
        state, kind = say["unknown"], "keep"
    elif summary["new"]:
        state, kind = say["some_new"].format(len(summary["new"])), "warn"
    else:
        state, kind = say["none_new"], "ok"
    rows = "".join(
        f'<tr><td><code>{html.escape(unit["unit"])}</code></td><td>{html.escape(describe_reading(unit, language))}</td>'
        f'<td class="num">{int(unit["row_count"])}</td><td>{html.escape(str(unit["first_date"])[:10])}</td>'
        f'<td>{f"""<span class="tag stop">{html.escape(say["risk"])}</span>""" if unit["stops_the_load"] else ""}</td></tr>'
        for unit in summary["new"]
    )
    table = (
        f'<table class="new"><thead><tr><th>{html.escape(say["unit"])}</th><th>{html.escape(say["reading"])}</th>'
        f'<th class="num">{html.escape(say["rows"])}</th><th>{html.escape(say["since"])}</th><th></th></tr></thead>'
        f"<tbody>{rows}</tbody></table>"
        if rows
        else ""
    )
    return (
        f'<section class="units"><p class="line"><b>{html.escape(say["units"])}</b> · {html.escape(reviewed)} · '
        f'<span class="tag {kind}">{html.escape(state)}</span></p>'
        f'<p class="why">{html.escape(say["units_why"])}</p>{table}</section>'
    )


def build_controls_html(language: str, author: bool) -> str:
    say = {key: pick(pair, language) for key, pair in TEXTS.items()}
    rows, moment = [], None
    for control in read_controls():
        if control["momento"] != moment:
            moment = control["momento"]
            rows.append(f'<tr class="step"><td colspan="5">{html.escape(pick(MOMENTS[moment], language))}</td></tr>')
        outcome, kind = OUTCOMES[control["si_falla"]]
        references = [transformation_rules.code_reference(reference, author) for reference in control["codigo"]]
        code = " · ".join(
            f'<a href="{html.escape(item["href"], quote=True)}" target="_blank" rel="noopener"><code>{html.escape(item["text"])}</code></a>'
            if "href" in item
            else f'<code>{html.escape(item["text"])}</code>'
            for item in references
        )
        backing = "".join(f"{html.escape(code_name)} · " for code_name in control["respaldo"])
        rows.append(
            f'<tr><td class="name">{html.escape(pick(control["control"], language))}</td>'
            f'<td>{html.escape(pick(control["protege"], language))}</td>'
            f'<td class="when">{html.escape(pick(WHEN[control["cuando"]], language))}</td>'
            f'<td><span class="tag {kind}">{html.escape(pick(outcome, language))}</span></td>'
            f'<td class="backing">{backing}{code}</td></tr>'
        )
    return (
        f'<div class="scroll"><table class="catalog"><thead><tr><th>{html.escape(say["control"])}</th>'
        f'<th>{html.escape(say["protects"])}</th><th>{html.escape(say["when"])}</th><th>{html.escape(say["fails"])}</th>'
        f'<th>{html.escape(say["backing"])}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    )


def build_css(palette: dict[str, str]) -> str:
    dark = palette["base"] == charts.BASE_DARK
    green, amber, red = ("#3dd68c", "#f5b84b", "#ff8775") if dark else ("#1f8f5f", "#a16207", "#c23b2b")
    muted = charts.legible(palette["reference"], palette["background"])
    return f"""<style>
:root{{--bg:{palette["background"]};--panel:{palette["card"]};--fg:{palette["strong_text"]};--text:{palette["text"]};
  --muted:{muted};--line:{palette["card_border"]};--accent:{palette["accent"]};--green:{green};--amber:{amber};--red:{red};
  color-scheme:{"dark" if dark else "light"}}}
*{{box-sizing:border-box}}
html,body{{height:100%;margin:0}}
body{{background:var(--bg);color:var(--text);font:12.5px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;display:flex;flex-direction:column;gap:8px;padding:0 2px 4px}}
code{{font:11px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--muted)}}
a code{{color:var(--accent)}}
.units{{flex:none;border:1px solid var(--line);border-radius:10px;background:var(--panel);padding:8px 12px}}
.line{{margin:0;color:var(--text)}} .line b{{color:var(--fg);font-weight:600}}
.why{{margin:3px 0 0;font-size:11.5px;color:var(--muted)}}
.scroll{{flex:1;min-height:0;overflow:auto;scrollbar-width:thin;scrollbar-color:var(--line) transparent}}
table{{width:100%;border-collapse:collapse}}
th{{position:sticky;top:0;background:var(--bg);text-align:left;font-weight:500;font-size:11px;color:var(--muted);padding:4px 8px;border-bottom:1px solid var(--line);z-index:1}}
td{{padding:3px 8px;border-bottom:1px solid color-mix(in srgb,var(--line) 55%,transparent);vertical-align:top}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.new{{margin-top:6px}} .new th{{background:var(--panel)}}
.step td{{padding-top:9px;font-size:11px;color:var(--muted);border-bottom:1px solid var(--line)}}
.name{{color:var(--fg)}} .when{{white-space:nowrap;color:var(--muted)}}
.backing{{font-size:11px;color:var(--muted)}}
.tag{{display:inline-block;white-space:nowrap;font-size:11px;padding:0 7px;border-radius:9px;border:1px solid currentColor}}
.tag.stop{{color:var(--red)}} .tag.keep{{color:var(--accent)}} .tag.mark{{color:var(--amber)}} .tag.warn{{color:var(--amber)}} .tag.ok{{color:var(--green)}}
@media (max-width:760px){{html,body{{height:auto}}.scroll{{overflow:visible}}.when{{white-space:normal}}}}
</style>"""


def build_page_html(palette: dict[str, str], language: str, author: bool) -> str:
    return (
        f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"{build_css(palette)}</head><body>{build_units_html(unit_review.summarize(), language)}"
        f"{build_controls_html(language, author)}</body></html>"
    )


# endregion
