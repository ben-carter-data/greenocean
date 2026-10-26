"""«Dashboard» (D-296): the macro view of the whole project, one screen per tab, in the manner of a BI tool.

Three tabs: the market (what prices did this week and the weeks before), inflation (which families rose more than the
food CPI) and the data and its operation (the loads, the flags, the quality). Each tab has a row of scorecards with
their trend and four charts: a combined bar and line chart, a donut, ranked bars and a heat table.

Every figure is computed with the same definitions as the page it summarizes, so the dashboard and the Resumen, the
Precios e inflación page and Calidad y auditoría never disagree: the weekly change of a series compares the same regions
in both weeks (D-144), a family moves by the median of its series, «sin cambio» is below 0.05 % and a family is «al
ritmo de la inflación» within ±2 points of the CPI. Pure functions: no Streamlit.
"""
import base64
import html

import altair as alt
import pandas as pd

from bi import charts, home_mockup, inflation_view

# A change smaller than this, as a fraction, reads «sin cambio», as in the Resumen.
STILL = 0.0005
MARKET_WEEKS = 26
HEAT_WEEKS = 8


# region Data
def comparable(variations):
    """The weekly changes that can be read: a number, not infinite."""
    return variations[variations["variation"].notna() & variations["variation"].abs().lt(float("inf"))]


def market_weeks(variations, alerts, weeks=MARKET_WEEKS, family=None):
    """One row per week: prices with a value, those with a valid comparison, the typical change (median, in %) and the
    alerts. With a family, only its series."""
    if family:
        variations = variations[variations["product_group"] == family]
        alerts = alerts[alerts["product_group"] == family]
    last = sorted(variations["week_start"].unique())[-weeks:]
    rows = variations[variations["week_start"].isin(last)]
    valid = comparable(rows)
    frame = pd.DataFrame({"week_start": last})
    frame["prices"] = frame["week_start"].map(rows.groupby("week_start").size()).fillna(0).astype(int)
    frame["comparable"] = frame["week_start"].map(valid.groupby("week_start").size()).fillna(0).astype(int)
    frame["typical"] = frame["week_start"].map(valid.groupby("week_start")["variation"].median() * 100)
    frame["alerts"] = frame["week_start"].map(alerts.groupby("week_start").size()).fillna(0).astype(int)
    return frame


def family_moves(variations, week):
    """The families of one week: median change in %, prices, comparisons and their state, as in the Resumen."""
    rows = variations[variations["week_start"] == week]
    valid = comparable(rows)
    frame = valid.groupby("product_group")["variation"].median().mul(100).rename("change").reset_index()
    frame["prices"] = frame["product_group"].map(rows.groupby("product_group").size()).astype(int)
    frame["comparable"] = frame["product_group"].map(valid.groupby("product_group").size()).astype(int)
    frame["state"] = frame["change"].map(state)
    frame["family"] = frame["product_group"].map(home_mockup.short_family)
    return frame.sort_values("change", ascending=False).reset_index(drop=True)


def state(change):
    """«Subió», «Bajó» or «Sin cambio» for a change in %."""
    return "Subió" if change >= STILL * 100 else "Bajó" if change <= -STILL * 100 else "Sin cambio"


def family_heat(variations, weeks=HEAT_WEEKS):
    """Families by week: the median change in % of the last weeks, for the heat table."""
    last = sorted(variations["week_start"].unique())[-weeks:]
    valid = comparable(variations[variations["week_start"].isin(last)])
    frame = valid.groupby(["product_group", "week_start"])["variation"].median().mul(100).rename("change").reset_index()
    frame["family"] = frame["product_group"].map(home_mockup.short_family)
    return frame


def family_years(rows, last):
    """Families and the CPI by calendar year: the change of the monthly index from December to December (the first
    year from January 2022, the last one to the last published month), for the heat table of the inflation tab."""
    out = []
    for family, series in rows.groupby("product_group"):
        index = series.set_index(["year", "month"])["index"]
        for year in range(inflation_view.BASE_YEAR, last[0] + 1):
            start = (year, 1) if year == inflation_view.BASE_YEAR else (year - 1, 12)
            end = (year, 12) if year < last[0] else last
            if start in index and end in index:
                out.append({"product_group": family, "year": str(year) if year < last[0] else f"{year}*",
                            "change": (index[end] / index[start] - 1) * 100})
    frame = pd.DataFrame(out)
    frame["family"] = frame["product_group"].map(lambda name: home_mockup.short_family(name) if name != inflation_view.IPC_NAME
                                                 else "IPC alimentos")
    return frame


def ipc_twelve_months(rows):
    """The food CPI's change against the same month a year before, in %, month by month."""
    ipc = rows[rows["product_group"] == inflation_view.IPC_NAME].sort_values("month_start").set_index("month_start")["index"]
    frame = ((ipc / ipc.shift(12) - 1) * 100).dropna().rename("change").reset_index()
    return frame
# endregion


# region Scorecards
def sparkline(values, color, width=96, height=26):
    """A small trend line as an image (st.html drops inline SVG)."""
    values = [float(v) for v in values if pd.notna(v)]
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    span = high - low or 1
    step = width / (len(values) - 1)
    points = " ".join(f"{i * step:.1f},{height - 3 - (v - low) / span * (height - 6):.1f}" for i, v in enumerate(values))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
           f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round" '
           f'stroke-linecap="round"/></svg>')
    return f'<img class="ov-spark" alt="" src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}">'


def build_scorecards_html(cards, palette):
    """A row of scorecards: [(label, value, note, trend values or None, tone)] with tone rise, fall or neutral."""
    tone_color = {"rise": palette["rise"], "fall": palette["fall"], "neutral": palette["accent"]}
    items = []
    for label, value, note, trend, tone in cards:
        spark = sparkline(trend, tone_color.get(tone, palette["accent"])) if trend is not None else ""
        items.append(f'<div class="ov-score"><span class="ov-score-label">{html.escape(label)}</span>'
                     f'<span class="ov-score-value">{html.escape(value)}</span>'
                     f'<span class="ov-score-foot"><span class="ov-score-note ov-{tone}">{html.escape(note)}</span>{spark}</span>'
                     '</div>')
    return f'<div class="ov-scores">{"".join(items)}</div>'


def build_css(palette):
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    return f"""<style>
.ov-scores {{ display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:10px; margin:0 0 2px; }}
.ov-score {{ display:flex; flex-direction:column; gap:2px; padding:9px 14px 8px; border-radius:10px; background:{card};
  border:1px solid {border}; min-width:0; }}
.ov-score-label {{ font-size:11.5px; font-weight:500; color:{muted}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ov-score-value {{ font-size:23px; font-weight:600; color:{ink}; letter-spacing:-.01em; line-height:1.15; white-space:nowrap; }}
.ov-score-foot {{ display:flex; align-items:center; justify-content:space-between; gap:8px; min-height:26px; }}
.ov-score-note {{ font-size:11.5px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ov-rise {{ color:{palette['rise']}; }} .ov-fall {{ color:{palette['fall']}; }} .ov-neutral {{ color:{text}; }}
.ov-spark {{ display:block; flex:none; }}
[class*="st-key-ov_card_"] {{ background:{card}; border:1px solid {border} !important; border-radius:10px !important;
  padding:10px 14px 6px !important; gap:2px !important; }}
.ov-card-title {{ margin:0; font-size:13px; font-weight:600; color:{ink}; }}
.ov-card-note {{ margin:0 0 2px; font-size:11.5px; color:{muted}; }}
.st-key-ov_tabs [data-baseweb="tab-list"] {{ gap:4px; }}
.st-key-ov_tabs [data-baseweb="tab"] p {{ font-size:13.5px; font-weight:600; }}
@media (max-width:1100px) {{ .ov-scores {{ grid-template-columns:repeat(3, minmax(0, 1fr)); }} }}
</style>"""
# endregion


# region Charts
def style(chart, mode, height):
    return charts.apply_chart_style(chart.properties(width="container", height=height), mode)


def combo_chart(weeks, mode, height=210):
    """Bars: the prices with a valid comparison each week; line: the typical change, on its own axis."""
    palette = charts.get_palette(mode)
    base = alt.Chart(weeks).encode(x=alt.X("week_start:T", title=None, axis=alt.Axis(format="%d %b", labelAngle=0,
                                                                                      tickCount=8)))
    tooltip = [alt.Tooltip("week_start:T", title="Semana", format="%d-%m-%Y"),
               alt.Tooltip("comparable:Q", title="Precios comparables", format=",d"),
               alt.Tooltip("typical:Q", title="Cambio típico (%)", format="+.2f"),
               alt.Tooltip("alerts:Q", title="Alertas", format=",d")]
    bars = base.mark_bar(color=palette["accent"], opacity=.55, cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        y=alt.Y("comparable:Q", title="Precios comparables", axis=alt.Axis(titleFontSize=11, tickCount=4)), tooltip=tooltip)
    line = base.mark_line(color=palette["rise"], strokeWidth=2, point=alt.OverlayMarkDef(size=26, filled=True)).encode(
        y=alt.Y("typical:Q", title="Cambio típico (%)", axis=alt.Axis(titleFontSize=11, tickCount=4, orient="right")),
        tooltip=tooltip)
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=palette["reference"], strokeDash=[3, 3], opacity=.6).encode(
        y=alt.Y("y:Q", axis=None))
    return style(alt.layer(bars, alt.layer(line, zero)).resolve_scale(y="independent"), mode, height)


def donut(frame, category, value, mode, colors=None, selected=None, height=210, name="pick"):
    """A donut of `value` by `category`; a click picks a category (the selection is named `name`)."""
    palette = charts.get_palette(mode)
    names = list(frame[category])
    scale = alt.Scale(domain=names, range=[colors.get(n, palette["accent"]) for n in names]) if colors else alt.Scale()
    pick = alt.selection_point(name=name, fields=[category], on="click", clear="dblclick")
    opacity = (alt.condition(alt.datum[category] == selected, alt.value(1), alt.value(.35)) if selected
               else alt.condition(pick, alt.value(1), alt.value(.4)))
    total = frame[value].sum()
    frame = frame.assign(share=frame[value] / total * 100 if total else 0)
    chart = alt.Chart(frame).mark_arc(innerRadius=58, outerRadius=92, padAngle=.012, cornerRadius=3).encode(
        theta=alt.Theta(f"{value}:Q", stack=True),
        color=alt.Color(f"{category}:N", scale=scale, sort=names,
                        legend=alt.Legend(title=None, orient="right", labelFontSize=11.5, symbolType="circle",
                                          symbolSize=90, labelLimit=150)),
        opacity=opacity, order=alt.Order(f"{value}:Q", sort="descending"),
        tooltip=[alt.Tooltip(f"{category}:N", title="Grupo"), alt.Tooltip(f"{value}:Q", title="Cantidad", format=",d"),
                 alt.Tooltip("share:Q", title="Participación (%)", format=".1f")]).add_params(pick)
    center = alt.Chart(pd.DataFrame({"t": [f"{total:,}".replace(",", ".")]})).mark_text(
        fontSize=20, fontWeight=600, color=palette["strong_text"]).encode(text="t:N")
    return style(alt.layer(chart, center), mode, height)


def ranked_bars(frame, label, value, mode, height=190, percent=True, reference=None, name="rank", selected=None):
    """Horizontal bars ranked by value: red above zero (or the reference), blue below, with the value at the end."""
    palette = charts.get_palette(mode)
    cut = reference if reference is not None else 0
    frame = frame.assign(_tone=["rise" if v > cut else "fall" for v in frame[value]],
                         _text=[f"{v:+.1f} %".replace(".", ",") if percent else f"{v:,.0f}".replace(",", ".") for v in frame[value]])
    order = list(frame.sort_values(value, ascending=False)[label])
    pick = alt.selection_point(name=name, fields=[label], on="click", clear="dblclick")
    opacity = (alt.condition(alt.datum[label] == selected, alt.value(1), alt.value(.35)) if selected
               else alt.condition(pick, alt.value(1), alt.value(.45)))
    y = alt.Y(f"{label}:N", sort=order, title=None, axis=alt.Axis(labelLimit=160, labelFontSize=11.5, ticks=False, domain=False))
    bars = alt.Chart(frame).mark_bar(cornerRadius=2, height={"band": .62}).encode(
        y=y, x=alt.X(f"{value}:Q", title=None, axis=alt.Axis(labels=False, ticks=False, grid=False, domain=False)),
        color=alt.Color("_tone:N", scale=alt.Scale(domain=["rise", "fall"], range=[palette["rise"], palette["fall"]]), legend=None),
        opacity=opacity, tooltip=[alt.Tooltip(f"{label}:N", title="Grupo"), alt.Tooltip("_text:N", title="Valor")]).add_params(pick)
    text = alt.Chart(frame).mark_text(align="left", dx=5, fontSize=11.5, fontWeight=600, color=palette["text"]).encode(
        y=y, x=alt.X(f"{value}:Q"), text="_text:N")
    layers = [bars, text]
    if reference is not None:
        layers.append(alt.Chart(pd.DataFrame({"r": [reference]})).mark_rule(color=palette["strong_text"], strokeDash=[4, 3]).encode(x="r:Q"))
    else:
        layers.append(alt.Chart(pd.DataFrame({"r": [0]})).mark_rule(color=palette["reference"], opacity=.7).encode(x="r:Q"))
    return style(alt.layer(*layers).properties(padding={"right": 36}), mode, height)


def heat_table(frame, row, column, value, mode, height=190, column_format=None, row_sort=None):
    """A table whose cells are colored by their value: red rises, blue falls, the value written inside."""
    palette = charts.get_palette(mode)
    limit = max(1.0, float(frame[value].abs().quantile(.9))) if not frame.empty else 1.0
    frame = frame.assign(_text=[f"{v:+.1f}".replace(".", ",") for v in frame[value]])
    x = (alt.X(f"{column}:T", title=None, axis=alt.Axis(format=column_format or "%d %b", labelAngle=0, orient="top",
                                                          ticks=False, domain=False))
         if column_format is not False and str(frame[column].dtype).startswith("datetime")
         else alt.X(f"{column}:O", title=None, axis=alt.Axis(labelAngle=0, orient="top", ticks=False, domain=False)))
    y = alt.Y(f"{row}:N", title=None, sort=row_sort, axis=alt.Axis(labelLimit=150, labelFontSize=11.5, ticks=False, domain=False))
    cells = alt.Chart(frame).mark_rect(cornerRadius=3, stroke=palette["card"], strokeWidth=2).encode(
        x=x, y=y, color=alt.Color(f"{value}:Q", legend=None, scale=alt.Scale(
            domain=[-limit, 0, limit], range=[palette["fall"], palette["card"], palette["rise"]], clamp=True)),
        tooltip=[alt.Tooltip(f"{row}:N", title="Grupo"), alt.Tooltip(f"{value}:Q", title="Cambio (%)", format="+.2f")])
    text = alt.Chart(frame).mark_text(fontSize=11, color=palette["strong_text"]).encode(x=x, y=y, text="_text:N")
    return style(alt.layer(cells, text), mode, height)


def line_chart(frame, x, y, mode, height=190, title_y="", fmt="+.1f", color=None):
    palette = charts.get_palette(mode)
    color = color or palette["accent"]
    chart = alt.Chart(frame).mark_area(line={"color": color, "strokeWidth": 2}, color=alt.Gradient(
        gradient="linear", stops=[alt.GradientStop(color=color, offset=0), alt.GradientStop(color=palette["card"], offset=1)],
        x1=1, x2=1, y1=0, y2=1), opacity=.35).encode(
        x=alt.X(f"{x}:T", title=None, axis=alt.Axis(format="%Y", tickCount=5, labelAngle=0)),
        y=alt.Y(f"{y}:Q", title=title_y or None, axis=alt.Axis(tickCount=4, titleFontSize=11)),
        tooltip=[alt.Tooltip(f"{x}:T", title="Mes", format="%m-%Y"), alt.Tooltip(f"{y}:Q", title="Valor", format=fmt)])
    zero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color=palette["reference"], opacity=.6).encode(y="z:Q")
    return style(alt.layer(chart, zero), mode, height)


def stacked_runs(runs, mode, height=190):
    """The loads: rows loaded per load, with the rejected ones on their own axis."""
    palette = charts.get_palette(mode)
    runs = runs.assign(label=[f"#{r} · {d[8:10]}-{d[5:7]}" for r, d in zip(runs["run_id"], runs["started_at"])])
    base = alt.Chart(runs).encode(x=alt.X("label:N", title=None, sort=list(runs["label"]), axis=alt.Axis(labelAngle=0)))
    tooltip = [alt.Tooltip("label:N", title="Carga"), alt.Tooltip("rows_read:Q", title="Filas leídas", format=",d"),
               alt.Tooltip("rows_loaded:Q", title="Filas cargadas", format=",d"),
               alt.Tooltip("rows_rejected:Q", title="Filas rechazadas", format=",d")]
    bars = base.mark_bar(color=palette["accent"], opacity=.6, cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        y=alt.Y("rows_loaded:Q", title="Filas cargadas", axis=alt.Axis(format="~s", tickCount=4, titleFontSize=11)), tooltip=tooltip)
    line = base.mark_line(color=palette["rise"], strokeWidth=2, point=alt.OverlayMarkDef(size=30, filled=True)).encode(
        y=alt.Y("rows_rejected:Q", title="Filas rechazadas", axis=alt.Axis(orient="right", tickCount=4, titleFontSize=11)),
        tooltip=tooltip)
    return style(alt.layer(bars, line).resolve_scale(y="independent"), mode, height)
# endregion
