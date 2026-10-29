"""The quality report viewer (D-333): one numbered report as eight slides, in its own HTML document.

It is drawn in an iframe, so the arrows, the keyboard, full screen and «Descargar PDF» (the browser prints this
document only, faithful to the screen) work without touching the dashboard's DOM. Every figure comes from the reports
(docs/calidad/informes); every fixed text from docs/calidad/politica.json and docs/calidad/metas.json; the causes and
the actions from docs/calidad/no_conformidades.json; external incidents are only counted here, their detail is for the
author. The comparison slide compares any two reports, the previous one by default. Pure functions.
"""

from __future__ import annotations

import html
import json
from typing import Any

from bi import quality_metrics

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


def incidents_in(incidents: list[dict[str, Any]], start: str, end: str) -> int:
    return sum(1 for item in incidents if start < str(item.get("fecha", ""))[:10] <= end)


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


def build_viewer_html(
    reports: list[dict[str, Any]],
    number: int,
    goals: dict[str, Any],
    policy: dict[str, Any],
    nonconformities: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
    english: bool = False,
) -> str:
    """The whole viewer of report «number», a self-contained document."""
    report = next(item for item in reports if item["numero"] == number)
    texts = policy.get("diapositivas", {})
    word = lambda key: pick(texts.get(key, ["", ""]), english)  # noqa: E731
    title = f"Quality report No. {number}" if english else f"Informe de calidad N° {number}"
    within, nonconforming, measured = quality_metrics.report_counts(report)
    labels = (
        ("Date", "Data week", "Evaluated code", "Within the acceptable")
        if english
        else ("Fecha", "Semana de datos", "Código evaluado", "Dentro de lo aceptable")
    )
    cover = (
        f'<section class="slide cover" data-key="portada"><span class="kicker">GreenOcean</span><h1>{esc(title)}</h1>'
        f'<dl><dt>{labels[0]}</dt><dd>{esc(report["fecha"])}</dd><dt>{labels[1]}</dt><dd>{esc(report["semana"] or "—")}</dd>'
        f'<dt>{labels[2]}</dt><dd><code>{esc(report["codigo_evaluado"])}</code></dd>'
        f"<dt>{labels[3]}</dt><dd>{within} / {measured}</dd></dl>"
        f'<p class="muted">{esc(word("portada"))}</p></section>'
    )
    # 2. What we measure and why: the two qualities, their objective and their acceptables.
    qualities = []
    for kind in ("datos", "codigo"):
        quality = policy.get("calidades", {}).get(kind, {})
        items = "".join(
            f"<li>{esc(pick(row['nombre'], english))}: "
            f"<b>{esc(figure(row['falla_aceptable'], row['unidad_falla'], english))}</b></li>"
            for row in report["indicadores"]
            if row["tipo"] == kind
        )
        acceptable = "Acceptable failure" if english else "Falla aceptable"
        qualities.append(
            f'<div class="card"><h3>{esc(pick(quality.get("titulo", ["", ""]), english))}</h3>'
            f'<p>{esc(pick(quality.get("objetivo", ["", ""]), english))}</p>'
            f'<p class="muted">{acceptable}</p><ul>{items}</ul></div>'
        )
    measure = slide("que_medimos", word("que_medimos"), f'<div class="two">{"".join(qualities)}</div>')
    # 3. How it is measured.
    head = (
        ("Indicator", "What it measures", "How", "Acceptable", "Goal", "Frequency")
        if english
        else ("Indicador", "Qué mide", "Cómo", "Aceptable", "Meta", "Frecuencia")
    )
    method_rows = []
    for row in report["indicadores"]:
        goal, frozen = goals.get(row["clave"], {}), report["aceptables"].get(row["clave"], {})
        limit = frozen.get("max", frozen.get("min"))
        sign = "≤" if "max" in frozen else "≥"
        unit = quality_metrics.unit_text(row["unidad"], english)
        method_rows.append(
            f'<tr><td><b>{esc(pick(row["nombre"], english))}</b></td><td>{esc(pick(goal.get("que_mide", ""), english))}</td>'
            f'<td class="muted">{esc(pick(goal.get("como", ""), english))}</td>'
            f"<td>{sign} {esc(limit)} {esc(unit)}</td><td>{sign} {esc(frozen.get('meta', limit))} {esc(unit)}</td>"
            f'<td class="muted">{esc(pick(goal.get("frecuencia", ""), english))}</td></tr>'
        )
    method = slide(
        "como_se_mide",
        word("como_se_mide"),
        "<table><thead><tr>"
        + "".join(f"<th>{cell}</th>" for cell in head)
        + f'</tr></thead><tbody>{"".join(method_rows)}</tbody></table>',
    )
    results = slide("resultados", word("resultados"), results_rows(report, policy, english))
    # 5. Comparison: drawn by the script from the reports' own figures; the previous report by default.
    options = "".join(
        f'<option value="{item["numero"]}">N° {item["numero"]} · {esc(item["fecha"][:10])}</option>' for item in reports
    )
    compare_labels = ("Compare", "with") if english else ("Comparar", "con")
    comparison = slide(
        "comparacion",
        word("comparacion"),
        f'<div class="pickers"><label>{compare_labels[0]} <select id="cmp-a">{options}</select></label>'
        f'<label>{compare_labels[1]} <select id="cmp-b">{options}</select></label></div><div id="cmp"></div>',
    )
    # 6. What failed and what we do.
    failed = [row for row in report["indicadores"] if row["estado"] in ("urgente", "critico")]
    entries = []
    for row in sorted(failed, key=lambda item: item["estado"] != "critico"):
        record = next(
            (
                item
                for item in nonconformities
                if item.get("informe") == number and item.get("indicador") == row["clave"]
            ),
            {},
        )
        cause = record.get("causa") or word("causa_pendiente")
        action = record.get("accion") or pick(goals.get(row["clave"], {}).get("accion", ""), english)
        status = record.get("estado") or ("pending, the author's" if english else "pendiente del autor")
        labels6 = ("Cause", "Action", "State") if english else ("Causa", "Acción", "Estado")
        entries.append(
            f'<div class="card"><h3 style="color:{STATE_COLORS[row["estado"]]}">{esc(pick(row["nombre"], english))} · '
            f"{esc(pick(policy['estados'][row['estado']], english))}</h3>"
            f"<p><b>{labels6[0]}:</b> {esc(pick(cause, english))}</p><p><b>{labels6[1]}:</b> {esc(pick(action, english))}</p>"
            f'<p class="muted"><b>{labels6[2]}:</b> {esc(pick(status, english))}</p></div>'
        )
    what_failed = slide(
        "que_fallo", word("que_fallo"), "".join(entries) or f'<p class="big">{esc(word("sin_no_conformidades"))}</p>'
    )
    # 7. External incidents: only their count; the detail is the author's.
    start, end = period(reports, report)
    count = incidents_in(incidents, start, end)
    counted = (
        esc(word("sin_incidentes"))
        if not count
        else (
            f"{count} external incident{'s' if count > 1 else ''}"
            if english
            else f"{count} incidente{'s' if count > 1 else ''} externo{'s' if count > 1 else ''}"
        )
    )
    external = slide(
        "incidentes",
        word("incidentes"),
        f'<p class="big">{counted}</p><p class="muted">{esc(word("detalle_incidentes"))}</p>',
    )
    # 8. Technical annex.
    measurement = report["medicion"]
    ruff = measurement.get("ruff", {}).get("por_codigo", {})
    coverage = measurement.get("cobertura", {}).get("modulos", {})
    lowest = sorted(coverage.items(), key=lambda item: item[1])[:8]
    dbt = measurement.get("dbt", {}).get("ultima_construccion") or {}
    data = measurement.get("datos", {})
    annex_labels = (
        (
            "Ruff by rule",
            "Lowest covered modules",
            "Data validations",
            "dbt tests passed",
            "Rows read",
            "Rows rejected",
            "Prices with a valid comparison",
            "mypy errors",
        )
        if english
        else (
            "Ruff por regla",
            "Módulos menos cubiertos",
            "Validaciones de datos",
            "Pruebas dbt superadas",
            "Filas leídas",
            "Filas rechazadas",
            "Precios con comparación válida",
            "Errores de mypy",
        )
    )

    def num(value: Any) -> str:
        return (
            "—"
            if value is None
            else quality_metrics.number(value, 1 if isinstance(value, float) and value % 1 else 0, english)
        )

    validations = [
        (annex_labels[3], f"{num(dbt.get('pruebas_ok'))} / {num(dbt.get('pruebas_total'))}"),
        (annex_labels[4], num(data.get("filas_leidas"))),
        (annex_labels[5], num(data.get("filas_rechazadas"))),
        (annex_labels[6], f"{num(data.get('con_comparacion'))} / {num(data.get('precios_semana'))}"),
        (annex_labels[7], num(measurement.get("mypy", {}).get("errores"))),
    ]
    annex = slide(
        "anexo",
        word("anexo"),
        '<div class="three">'
        f'<div class="card"><h3>{annex_labels[0]}</h3><ul>'
        + (
            "".join(f"<li><code>{esc(code)}</code> {num(count)}</li>" for code, count in sorted(ruff.items()))
            or "<li>—</li>"
        )
        + f'</ul></div><div class="card"><h3>{annex_labels[1]}</h3><ul>'
        + ("".join(f"<li><code>{esc(name)}</code> {num(value)} %</li>" for name, value in lowest) or "<li>—</li>")
        + f'</ul></div><div class="card"><h3>{annex_labels[2]}</h3><ul>'
        + "".join(f"<li>{esc(label)}: <b>{esc(value)}</b></li>" for label, value in validations)
        + f'</ul></div></div><h3>{esc(word("reproducir"))}</h3><ul class="code">'
        + "".join(f"<li><code>{esc(line)}</code></li>" for line in policy.get("reproducir", []))
        + "</ul>",
    )
    slides = [cover, measure, method, results, comparison, what_failed, external, annex]
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
        "head": ["Indicator", "No.", "No.", "Change"] if english else ["Indicador", "N°", "N°", "Variación"],
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
        + "".join(slides)
        + "</div><script>const DATA="
        + json.dumps(data_for_script, ensure_ascii=False).replace("</", "<\\/")
        + ";"
        + SCRIPT
        + "</script></body></html>"
    )


CSS = f"""
*{{box-sizing:border-box}} html,body{{margin:0;background:{DEEP};color:#d7dee9;
font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.deck{{min-height:100vh;display:flex;flex-direction:column}}
.bar{{position:sticky;top:0;z-index:2;display:flex;align-items:center;gap:8px;padding:10px 18px;background:{DEEP};
border-bottom:1px solid color-mix(in srgb,{SKY} 35%,#1b2433)}}
.bar b{{color:#f3f7fc}} #pos{{color:{SKY};font-variant-numeric:tabular-nums}} .grow{{flex:1}}
button{{font:inherit;color:#e6edf6;background:#0d1320;border:1px solid #243046;border-radius:8px;padding:5px 12px;cursor:pointer}}
button:hover,button:focus-visible{{border-color:{SKY};outline:none}} button.primary{{background:{SKY};color:#04121c;border-color:{SKY};font-weight:600}}
.slide{{display:none;padding:22px 28px 30px;flex:1;overflow:auto}} .slide.active{{display:block}}
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
.state{{font-weight:700;white-space:nowrap}} .big{{font-size:22px;color:#f3f7fc;margin:30px 0 8px}}
.pickers{{display:flex;gap:18px;margin-bottom:14px}} select{{font:inherit;color:#e6edf6;background:#0d1320;border:1px solid #243046;border-radius:8px;padding:4px 8px}}
.pair{{display:grid;gap:3px}} .pair i{{display:block;height:6px;border-radius:3px}}
.up{{color:#f87171}} .down{{color:#34d399}}
@media (max-width:760px){{.two,.three{{grid-template-columns:1fr}}}}
@media print{{.bar{{display:none}} .slide{{display:block!important;page-break-after:always;min-height:auto}}
html,body{{background:{DEEP}!important}} @page{{margin:12mm}}}}
"""

SCRIPT = f"""
const slides=[...document.querySelectorAll('.slide')];let at=0;
const pos=document.getElementById('pos');
function show(i){{at=Math.max(0,Math.min(slides.length-1,i));slides.forEach((s,k)=>s.classList.toggle('active',k===at));
pos.textContent=(at+1)+' / '+slides.length;}}
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
[DATA.head[0],DATA.head[1]+' '+ra.n,DATA.head[2]+' '+rb.n,DATA.head[3]].forEach(h=>{{const th=document.createElement('th');th.textContent=h;head.appendChild(th);}});
const thead=document.createElement('thead');thead.appendChild(head);t.appendChild(thead);const body=document.createElement('tbody');
rb.rows.forEach(row=>{{const before=(ra.rows.find(x=>x[3]===row[3])||[])[1];const tr=document.createElement('tr');
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
a.onchange=compare;b.onchange=compare;compare();show(0);
"""
