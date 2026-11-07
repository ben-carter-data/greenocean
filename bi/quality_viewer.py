"""The quality report viewer (D-333, D-431): one numbered report as four slides, in its own HTML document.

It is drawn in an iframe, so the arrows, the keyboard, full screen and «Descargar PDF» (the browser prints this
document only, faithful to the screen) work without touching the dashboard's DOM. Every figure comes from the reports
(docs/calidad/informes); every fixed text from docs/calidad/politica.json and docs/calidad/metas.json; the causes and
the actions from docs/calidad/no_conformidades.json and docs/calidad/incidentes_externos.json. The method is the SQAP's:
the cover names its version. The comparison slide compares any two reports of the same series, the previous one by
default, and warns when they do not measure the same indicators. Pure functions.
"""

from __future__ import annotations

import html
import json
from typing import Any

from bi import quality_metrics, weeks

# region Constants
SKY = "#38bdf8"
DEEP = "#05070b"
BEFORE = "#a78bfa"  # the earlier report of a comparison: violet, apart from the sky blue of the later one
STATE_COLORS = {
    "cumple": "#34d399",
    "aviso": "#fbbf24",
    "urgente": "#fb923c",
    "critico": "#f87171",
    "sin_medicion": "#94a3b8",
}
# endregion


# region The quality report viewer
def esc(value: Any) -> str:
    return html.escape(str(value))


def pick(pair: Any, english: bool) -> str:
    return pair[1 if english else 0] if isinstance(pair, list) else str(pair)


def figure(value: Any, unit: str, english: bool) -> str:
    if value is None:
        return "—"
    decimals = 1 if isinstance(value, float) and value % 1 else 0
    return quality_metrics.number(value, decimals, english) + (
        f" {quality_metrics.unit_text(unit, english)}" if unit else ""
    )


def period(reports: list[dict[str, Any]], report: dict[str, Any]) -> tuple[str, str]:
    """(from, to) of the period a report covers: from the previous report's date to its own."""
    previous = next((item for item in reports if item["numero"] == report["anterior"]), None)
    return (previous["fecha"][:10] if previous else "", report["fecha"][:10])


def slide(key: str, title: str, body: str) -> str:
    return f'<section class="slide" data-key="{key}"><h2>{esc(title)}</h2>{body}</section>'


def results_rows(report: dict[str, Any], policy: dict[str, Any], english: bool) -> str:
    rows = []
    for row in report["indicadores"]:
        fail, acceptable = row["falla"], row["falla_aceptable"]
        span = max(fail or 0, acceptable or 0) * 1.3 or 1
        bar = (
            '<span class="bar empty"></span>'
            if fail is None
            else f'<span class="bar"><i style="width:{min(100, fail / span * 100):.1f}%"></i>'
            f'<b style="left:{min(100, (acceptable or 0) / span * 100):.1f}%"></b></span>'
        )
        state = row["estado"]
        rows.append(
            f'<tr><td><b>{esc(pick(row["nombre"], english))}</b></td><td>{bar}</td>'
            f'<td class="num">{esc(figure(fail, row["unidad_falla"], english))}</td>'
            f'<td class="num muted">{esc(figure(acceptable, row["unidad_falla"], english))}</td>'
            f'<td><span class="state" style="color:{STATE_COLORS[state]}">'
            f"{esc(pick(policy['estados'][state], english))}</span></td>"
            f'<td class="muted">{esc(pick(row["insight"], english))}</td></tr>'
        )
    head = (
        ("Indicator", "Failure", "", "Acceptable", "State", "Reading")
        if english
        else ("Indicador", "Falla", "", "Aceptable", "Estado", "Lectura")
    )
    return (
        f'<table><thead><tr><th>{head[0]}</th><th>{head[1]}</th><th class="num"></th><th class="num">{head[3]}</th>'
        f'<th>{head[4]}</th><th>{head[5]}</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
    )


def table_rows(
    report: dict[str, Any],
    reports: list[dict[str, Any]],
    goals: dict[str, Any],
    policy: dict[str, Any],
    nonconformities: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
    english: bool,
) -> list[tuple[str, str, str, str, str]]:
    """D-431: the one table of non-conformities and incidents: (indicator, state, cause, disposition, date). The
    non-conformities of this report and the ones of earlier reports of its series still open, then the external
    incidents of its period."""
    names = {row["clave"]: pick(row["nombre"], english) for item in reports for row in item["indicadores"]}
    earlier = {item["numero"] for item in reports if item["numero"] <= report["numero"]}
    rows = []
    for record in nonconformities:
        if record.get("serie", quality_metrics.SERIES_BUILD) != report.get("serie", quality_metrics.SERIES_BUILD):
            continue
        mine = quality_metrics.same_report(record, report)
        if not mine and (record.get("informe") not in earlier or quality_metrics.is_resolved(record)):
            continue
        key = record.get("indicador", "")
        state = record.get("estado") or ("pending, the author's" if english else "pendiente del autor")
        cause = record.get("causa") or texts_of(policy, "causa_pendiente", english)
        disposition = record.get("accion") or pick(goals.get(key, {}).get("accion", ""), english)
        rows.append(
            (
                names.get(key, key),
                pick(state, english),
                pick(cause, english),
                pick(disposition, english),
                str(record.get("fecha", "")),
            )
        )
    start, end = period(reports, report)
    for item in incidents:
        if start < str(item.get("fecha", ""))[:10] <= end:
            source = item.get("fuente", "")
            rows.append(
                (
                    names.get(item.get("indicador", ""), item.get("indicador", "")),
                    f"{'External incident' if english else 'Incidente externo'} · {source}",
                    pick(item.get("causa", ""), english),
                    pick(item.get("respuesta", ""), english),
                    str(item.get("fecha", "")),
                )
            )
    return rows


def texts_of(policy: dict[str, Any], key: str, english: bool) -> str:
    return pick(policy.get("diapositivas", {}).get(key, ["", ""]), english)


def _viewer_number(english, value: Any) -> str:
    return (
        "—"
        if value is None
        else quality_metrics.number(value, 1 if isinstance(value, float) and value % 1 else 0, english)
    )


def build_viewer_html(
    reports: list[dict[str, Any]],
    number: int,
    goals: dict[str, Any],
    policy: dict[str, Any],
    nonconformities: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
    english: bool = False,
    sqap_url: str = "",
) -> str:
    """The whole viewer of report «number» of one series, a self-contained document. D-431: four slides, one page
    each: the cover with the SQAP it was measured by, the results, the comparison and the non-conformities and
    incidents; the method lives in the SQAP only."""
    report = next(item for item in reports if item["numero"] == number)
    word = lambda key: texts_of(policy, key, english)  # noqa: E731
    title = quality_metrics.report_name(report, english)
    within, nonconforming, measured = quality_metrics.report_counts(report)
    labels = (
        ("Date", "Data week", "Evaluated code", "Within the acceptable", "Measured by")
        if english
        else ("Fecha", "Semana de datos", "Código evaluado", "Dentro de lo aceptable", "Medido según")
    )
    version = report.get("sqap")
    sqap = (
        f"SQAP v{esc(version)}"
        if version
        else ("SQAP (version not recorded)" if english else "SQAP (versión no registrada)")
    )
    sqap_html = f'<a href="{esc(sqap_url)}" target="_blank" rel="noopener">{sqap}</a>' if sqap_url else sqap
    series_note = (
        ""
        if report.get("serie") == quality_metrics.SERIES_WEEKLY
        else f'<p class="muted">{esc(word("serie_construccion"))}</p>'
    )
    cover = (
        f'<section class="slide cover" data-key="portada"><span class="kicker">GreenOcean</span><h1>{esc(title)}</h1>'
        f'<dl><dt>{labels[0]}</dt><dd>{esc(report["fecha"])}</dd><dt>{labels[1]}</dt><dd>{esc(weeks.week_range(report["semana"], True, english) if report["semana"] else "—")}</dd>'
        f'<dt>{labels[2]}</dt><dd><code>{esc(report["codigo_evaluado"])}</code></dd>'
        f"<dt>{labels[3]}</dt><dd>{within} / {measured}</dd><dt>{labels[4]}</dt><dd>{sqap_html}</dd></dl>"
        f'<p class="muted">{esc(word("portada"))}</p>{series_note}</section>'
    )
    # The figures behind the data indicators, under the results.
    data = report["medicion"].get("datos", {})
    dbt = report["medicion"].get("dbt", {}).get("ultima_construccion") or {}

    of = "of" if english else "de"
    figures = (
        ("dbt tests passed", "Rows rejected", "Prices with a valid comparison")
        if english
        else ("Pruebas dbt superadas", "Filas rechazadas", "Precios con comparación válida")
    )
    behind = " · ".join(
        f"{label}: {value}"
        for label, value in (
            (
                figures[0],
                f"{_viewer_number(english, dbt.get('pruebas_ok'))} {of} {_viewer_number(english, dbt.get('pruebas_total'))}",
            ),
            (
                figures[1],
                f"{_viewer_number(english, data.get('filas_rechazadas'))} {of} {_viewer_number(english, data.get('filas_leidas'))}",
            ),
            (
                figures[2],
                f"{_viewer_number(english, data.get('con_comparacion'))} {of} {_viewer_number(english, data.get('precios_semana'))}",
            ),
        )
    )
    results = slide(
        "resultados",
        word("resultados"),
        results_rows(report, policy, english) + f'<p class="muted small">{esc(behind)}</p>',
    )
    # The comparison: any two reports of the same series, the previous one by default.
    options = "".join(
        f'<option value="{item["numero"]}">{esc(quality_metrics.report_code(item, english))} · {esc(item["fecha"][:10])}</option>'
        for item in reports
    )
    compare_labels = ("Compare", "with") if english else ("Comparar", "con")
    comparison = slide(
        "comparacion",
        word("comparacion"),
        f'<div class="pickers"><label>{compare_labels[0]} <select id="cmp-a">{options}</select></label>'
        f'<label>{compare_labels[1]} <select id="cmp-b">{options}</select></label></div>'
        f'<p class="warn" id="cmp-warn" hidden></p><div id="cmp"></div>',
    )
    # The non-conformities and incidents: one compact table.
    head = (
        ("Indicator", "State", "Cause", "Disposition", "Date")
        if english
        else ("Indicador", "Estado", "Causa", "Disposición", "Fecha")
    )
    entries = table_rows(report, reports, goals, policy, nonconformities, incidents, english)
    issues = slide(
        "incidencias",
        word("incidencias"),
        (
            "<table class='issues'><thead><tr>"
            + "".join(f"<th>{cell}</th>" for cell in head)
            + "</tr></thead><tbody>"
            + "".join(
                f"<tr><td><b>{esc(name)}</b></td><td>{esc(state)}</td><td>{esc(cause)}</td>"
                f'<td>{esc(disposition)}</td><td class="num muted">{esc(day)}</td></tr>'
                for name, state, cause, disposition, day in entries
            )
            + "</tbody></table>"
        )
        if entries
        else f'<p class="big">{esc(word("sin_no_conformidades"))}</p>',
    )
    slides = [cover, results, comparison, issues]
    data_for_script = {
        "reports": [
            {
                "n": item["numero"],
                "rows": [
                    [pick(row["nombre"], english), row["falla"], row["unidad_falla"], row["clave"]]
                    for row in item["indicadores"]
                ],
            }
            for item in reports
        ],
        "a": report["anterior"] or number,
        "b": number,
        "lang": "en-US" if english else "es-CL",
        "units": {"días": "days"} if english else {},
        "head": ["Indicator", "", "", "Change"] if english else ["Indicador", "", "", "Variación"],
        "codes": {item["numero"]: quality_metrics.report_code(item, english) for item in reports},
        "warn": (
            "The two reports do not measure the same indicators; only the ones in both are compared."
            if english
            else "Los dos informes no miden los mismos indicadores; solo se comparan los que están en ambos."
        ),
    }
    buttons = (
        ("Previous", "Next", "Full screen", "Download PDF")
        if english
        else ("Anterior", "Siguiente", "Pantalla completa", "Descargar PDF")
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(title)}</title><style>{CSS}</style></head><body><div class='deck'>"
        f"<header class='bar'><b>{esc(title)}</b><span id='pos'></span><span class='grow'></span>"
        f"<button id='prev' aria-label='{buttons[0]}'>←</button><button id='next' aria-label='{buttons[1]}'>→</button>"
        f"<button id='full'>{buttons[2]}</button><button id='print' class='primary'>{buttons[3]}</button></header>"
        + "<div class='main'><nav class='thumbs' id='thumbs' aria-label='"
        + ("Slides" if english else "Diapositivas")
        + "'></nav><div class='stage' id='stage'><div class='canvas' id='canvas'>"
        + "".join(slides)
        + "</div></div></div></div><script>const DATA="
        + json.dumps(data_for_script, ensure_ascii=False).replace("</", "<\\/")
        + ";"
        + SCRIPT
        + "</script></body></html>"
    )


CSS = f"""
*{{box-sizing:border-box}} html,body{{margin:0;background:{DEEP};color:#d7dee9;
font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.deck{{height:100vh;display:flex;flex-direction:column}}
.main{{flex:1;min-height:0;display:grid;grid-template-columns:168px minmax(0,1fr)}}
.thumbs{{overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:8px;border-right:1px solid #141b27;background:#070a10}}
.thumb{{position:relative;flex:none;width:100%;aspect-ratio:16/9;padding:0;overflow:hidden;border:2px solid #1d2738;border-radius:6px;background:{DEEP}}}
.thumb.current{{border-color:{SKY};box-shadow:0 0 0 1px {SKY}}}
.thumb .mini{{position:absolute;left:0;top:0;width:960px;height:540px;transform-origin:0 0;pointer-events:none}}
.thumb .mini .slide{{opacity:1;visibility:visible;overflow:hidden}}
.thumb i{{position:absolute;left:4px;bottom:3px;font:600 10px/1 ui-monospace,Menlo,monospace;font-style:normal;color:#f3f7fc;background:rgba(5,7,11,.8);padding:2px 4px;border-radius:3px}}
.stage{{position:relative;overflow:hidden;background:#04060a}}
.canvas{{position:absolute;left:50%;top:50%;width:960px;height:540px;margin:-270px 0 0 -480px;transform-origin:center;background:{DEEP};
box-shadow:0 0 0 1px #1d2738,0 12px 40px rgba(0,0,0,.5)}}
.bar{{position:sticky;top:0;z-index:2;display:flex;align-items:center;gap:8px;padding:10px 56px 10px 18px;background:{DEEP};
border-bottom:1px solid color-mix(in srgb,{SKY} 35%,#1b2433)}}
.bar b{{color:#f3f7fc}} #pos{{color:{SKY};font-variant-numeric:tabular-nums}} .grow{{flex:1}}
button{{font:inherit;color:#e6edf6;background:#0d1320;border:1px solid #243046;border-radius:8px;padding:5px 12px;cursor:pointer}}
button:hover,button:focus-visible{{border-color:{SKY};outline:none}} button.primary{{background:{SKY};color:#04121c;border-color:{SKY};font-weight:600}}
.slide{{position:absolute;inset:0;padding:20px 28px 24px;overflow:auto;opacity:0;visibility:hidden;transition:opacity .35s ease,visibility .35s}}
.slide.active{{opacity:1;visibility:visible}}
@media (prefers-reduced-motion:reduce){{.slide{{transition:none}}}}
h1{{font-size:34px;margin:6px 0 18px;color:#f3f7fc}} h2{{font-size:22px;margin:0 0 14px;color:{SKY};letter-spacing:.01em}}
h3{{font-size:14px;margin:0 0 8px;color:#f3f7fc}} .kicker{{color:{SKY};font-size:12px;letter-spacing:.14em;text-transform:uppercase}}
.cover{{padding-top:60px}} .cover dl{{display:grid;grid-template-columns:max-content 1fr;gap:6px 22px;margin:0 0 22px}}
.cover dt{{color:#8b97aa}} .cover dd{{margin:0;color:#f3f7fc}}
.muted{{color:#8b97aa}} code{{color:{SKY};font-family:ui-monospace,Menlo,monospace;font-size:12.5px}}
.card{{border:1px solid #1d2738;border-radius:12px;padding:14px 16px;margin-bottom:12px;background:#0a0f18}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} .three{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
ul{{margin:4px 0 0;padding-left:18px}} ul.code{{list-style:none;padding:0}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;color:{SKY};font-size:11px;text-transform:uppercase;letter-spacing:.06em;padding:8px 10px;
border-bottom:1px solid color-mix(in srgb,{SKY} 40%,transparent)}}
td{{padding:8px 10px;border-bottom:1px solid #141b27;vertical-align:top}} td b{{color:#f3f7fc}} .num{{text-align:right;white-space:nowrap}}
.bar{{}} .bar{{position:relative}} span.bar{{display:block;position:relative;height:6px;min-width:110px;margin-top:7px;border-radius:3px;background:#1d2738}}
span.bar i{{position:absolute;left:0;top:0;bottom:0;border-radius:3px;background:{SKY}}}
span.bar b{{position:absolute;top:-4px;width:2px;height:14px;background:#f3f7fc}} span.bar.empty{{background:none}}
.state{{font-weight:700;white-space:nowrap}} .small{{font-size:12px;margin-top:10px}}
.warn{{color:#fbbf24;margin:0 0 10px}} table.issues td{{font-size:12px}} a{{color:{SKY}}} .big{{font-size:22px;color:#f3f7fc;margin:30px 0 8px}}
.pickers{{display:flex;gap:18px;margin-bottom:14px}} select{{font:inherit;color:#e6edf6;background:#0d1320;border:1px solid #243046;border-radius:8px;padding:4px 8px}}
.pair{{display:grid;gap:3px}} .pair i{{display:block;height:6px;border-radius:3px}}
.up{{color:#f87171}} .down{{color:#34d399}}
@media (max-width:760px){{.main{{grid-template-columns:minmax(0,1fr);grid-template-rows:minmax(0,1fr) auto}}
.stage{{order:1}} .thumbs{{order:2;flex-direction:row;overflow-x:auto;overflow-y:hidden;border-right:0;border-top:1px solid #141b27;padding:8px}}
.thumb{{width:112px}} .bar button#full{{display:none}} .bar{{padding-right:56px;flex-wrap:wrap}}}}
@media print{{.bar,.thumbs{{display:none}} .deck{{height:auto}} .main{{display:block}} .stage{{overflow:visible;background:none}}
.canvas{{position:static;width:auto;height:auto;margin:0;transform:none!important;box-shadow:none}}
.slide{{position:static;opacity:1!important;visibility:visible!important;display:block;page-break-after:always;overflow:visible;transition:none}}
html,body{{background:{DEEP}!important}} @page{{margin:12mm}}
table{{font-size:11.5px}} th{{padding:5px 8px}} td{{padding:4px 8px}} .slide{{padding:14px 20px 16px}} h2{{margin-bottom:8px}}}}
"""

SCRIPT = f"""
const slides=[...document.querySelectorAll('.slide')];let at=0;
const pos=document.getElementById('pos');
const thumbs=document.getElementById('thumbs'),stage=document.getElementById('stage'),canvas=document.getElementById('canvas');
let tiles=[];
function show(i){{at=Math.max(0,Math.min(slides.length-1,i));slides.forEach((s,k)=>s.classList.toggle('active',k===at));
tiles.forEach((t,k)=>t.classList.toggle('current',k===at));
if(tiles[at])tiles[at].scrollIntoView({{block:'nearest',inline:'nearest'}});
pos.textContent=(at+1)+' / '+slides.length;}}
function fit(){{const s=Math.min(stage.clientWidth/960,stage.clientHeight/540);canvas.style.transform='scale('+s+')';
tiles.forEach(t=>{{t.firstChild.style.transform='scale('+(t.clientWidth/960)+')';}});}}
document.getElementById('prev').onclick=()=>show(at-1);document.getElementById('next').onclick=()=>show(at+1);
document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight'||e.key==='PageDown')show(at+1);
if(e.key==='ArrowLeft'||e.key==='PageUp')show(at-1);if(e.key==='Home')show(0);if(e.key==='End')show(slides.length-1);}});
const full=document.getElementById('full');
if(!document.fullscreenEnabled){{full.style.display='none';}}
full.onclick=()=>{{document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();}};
document.getElementById('print').onclick=()=>window.print();
const fmt=v=>v===null||v===undefined?'—':Number(v).toLocaleString(DATA.lang,{{maximumFractionDigits:2}});
const unit=u=>u?' '+(DATA.units[u]||u):'';
const a=document.getElementById('cmp-a'),b=document.getElementById('cmp-b'),out=document.getElementById('cmp');
a.value=DATA.a;b.value=DATA.b;
function compare(){{const ra=DATA.reports.find(r=>r.n==a.value),rb=DATA.reports.find(r=>r.n==b.value);
const top=Math.max(1,...ra.rows.concat(rb.rows).map(r=>r[1]||0));
const t=document.createElement('table');const head=document.createElement('tr');
[DATA.head[0],DATA.codes[ra.n],DATA.codes[rb.n],DATA.head[3]].forEach(h=>{{const th=document.createElement('th');th.textContent=h;head.appendChild(th);}});
const thead=document.createElement('thead');thead.appendChild(head);t.appendChild(thead);const body=document.createElement('tbody');
const keys=r=>r.rows.filter(x=>x[1]!==null).map(x=>x[3]).sort().join();const warn=document.getElementById('cmp-warn');
warn.hidden=keys(ra)===keys(rb);warn.textContent=DATA.warn;
rb.rows.filter(row=>ra.rows.some(x=>x[3]===row[3])).forEach(row=>{{const before=(ra.rows.find(x=>x[3]===row[3])||[])[1];const tr=document.createElement('tr');
const name=document.createElement('td');const strong=document.createElement('b');strong.textContent=row[0];name.appendChild(strong);
const bars=document.createElement('div');bars.className='pair';
[[before,'{BEFORE}'],[row[1],'{SKY}']].forEach(([v,c])=>{{const i=document.createElement('i');i.style.background=c;
i.style.width=(v===null||v===undefined?0:Math.max(2,v/top*100))+'%';bars.appendChild(i);}});name.appendChild(bars);
const ca=document.createElement('td');ca.className='num';ca.textContent=fmt(before)+unit(row[2]);
const cb=document.createElement('td');cb.className='num';cb.textContent=fmt(row[1])+unit(row[2]);
const d=document.createElement('td');d.className='num';
if(before===null||before===undefined||row[1]===null){{d.textContent='—';}}else{{const diff=row[1]-before;
d.textContent=(diff>0?'+':'')+fmt(diff)+unit(row[2]);d.className='num '+(diff>0?'up':diff<0?'down':'');}}
[name,ca,cb,d].forEach(c=>tr.appendChild(c));body.appendChild(tr);}});t.appendChild(body);out.replaceChildren(t);}}
a.onchange=compare;b.onchange=compare;compare();
slides.forEach((s,k)=>{{const tile=document.createElement('button');tile.className='thumb';tile.setAttribute('aria-label',(k+1)+' / '+slides.length);
const mini=document.createElement('div');mini.className='mini';const copy=s.cloneNode(true);
copy.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));copy.setAttribute('aria-hidden','true');copy.classList.add('active');
mini.appendChild(copy);const number=document.createElement('i');number.textContent=k+1;tile.append(mini,number);
tile.onclick=()=>show(k);thumbs.appendChild(tile);tiles.push(tile);}});
new ResizeObserver(fit).observe(stage);new ResizeObserver(fit).observe(thumbs);fit();show(0);
"""
# endregion
