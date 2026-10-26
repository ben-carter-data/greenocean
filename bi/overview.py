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
# A state that passes (every test, every indicator in its threshold): green, never the blue of a fall.
GOOD = "#199e70"
MARKET_WEEKS = 26
HEAT_WEEKS = 8


# region Data
def comparable(variations):
    """The weekly changes that can be read: a number, not infinite."""
    return variations[variations["variation"].notna() & variations["variation"].abs().lt(float("inf"))]


def market_weeks(prices, variations, alerts, weeks=MARKET_WEEKS, family=None):
    """One row per week: the prices with a value (every national series of the week), those with a valid comparison,
    the typical change (median, in %) and the alerts. With a family, only its series."""
    if family:
        prices = prices[prices["product_group"] == family]
        variations = variations[variations["product_group"] == family]
        alerts = alerts[alerts["product_group"] == family]
    last = sorted(variations["week_start"].unique())[-weeks:]
    rows = prices[prices["week_start"].isin(last)]
    valid = comparable(variations[variations["week_start"].isin(last)])
    frame = pd.DataFrame({"week_start": last})
    frame["prices"] = frame["week_start"].map(rows.groupby("week_start").size()).fillna(0).astype(int)
    frame["comparable"] = frame["week_start"].map(valid.groupby("week_start").size()).fillna(0).astype(int)
    frame["typical"] = frame["week_start"].map(valid.groupby("week_start")["variation"].median() * 100)
    frame["alerts"] = frame["week_start"].map(alerts.groupby("week_start").size()).fillna(0).astype(int)
    return frame


def family_moves(prices, variations, week):
    """The families of one week: median change in %, prices, comparisons and their state, as in the Resumen."""
    rows = prices[prices["week_start"] == week]
    valid = comparable(variations[variations["week_start"] == week])
    frame = valid.groupby("product_group")["variation"].median().mul(100).rename("change").reset_index()
    frame["prices"] = frame["product_group"].map(rows.groupby("product_group").size()).astype(int)
    frame["comparable"] = frame["product_group"].map(valid.groupby("product_group").size()).astype(int)
    frame["state"] = frame["change"].map(state)
    frame["family"] = frame["product_group"].map(home_mockup.short_family)
    return frame.sort_values("change", ascending=False).reset_index(drop=True)


def directions(variations, week, family=None):
    """How the comparable prices of one week moved: how many rose, fell or stayed (below 0.05 %), as in the Resumen."""
    rows = comparable(variations[variations["week_start"] == week])
    if family:
        rows = rows[rows["product_group"] == family]
    values = rows["variation"]
    return pd.DataFrame({"direction": ["Subieron", "Bajaron", "Sin cambio"],
                         "prices": [int((values >= STILL).sum()), int((values <= -STILL).sum()),
                                    int((values.abs() < STILL).sum())]})


# North to south, by the official number of each region.
REGION_ORDER = [15, 1, 2, 3, 4, 5, 13, 6, 7, 16, 8, 9, 14, 10, 11, 12]


def region_moves(regions, region_ids):
    """The regions of the week, north to south: the share of their comparable prices that rose and that fell."""
    frame = pd.DataFrame(regions)
    frame = frame[frame["total"] > 0].copy()
    frame["up_share"] = frame["up"] / frame["total"] * 100
    frame["down_share"] = -frame["down"] / frame["total"] * 100
    frame["order"] = frame["region"].map(lambda name: REGION_ORDER.index(region_ids[name]) if region_ids.get(name) in REGION_ORDER else 99)
    frame["label"] = frame["region"].map(home_mockup.short_region)
    return frame.sort_values("order").reset_index(drop=True)


def state(change):
    """«Subió», «Bajó» or «Sin cambio» for a change in %."""
    return "Subió" if change >= STILL * 100 else "Bajó" if change <= -STILL * 100 else "Sin cambio"


def family_heat(variations, weeks=HEAT_WEEKS):
    """Families by week: the median change in % of the last weeks, for the heat table."""
    last = sorted(variations["week_start"].unique())[-weeks:]
    valid = comparable(variations[variations["week_start"].isin(last)])
    frame = valid.groupby(["product_group", "week_start"])["variation"].median().mul(100).rename("change").reset_index()
    frame["family"] = frame["product_group"].map(home_mockup.short_family)
    months = charts.CHILE_LOCALE["time"]["shortMonths"]
    frame["week"] = [f"{w.day:02d} {months[w.month - 1].lower()}" for w in frame["week_start"]]
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
def sparkline(values, color, width=70, height=24):
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
    tone_color = {"rise": palette["rise"], "fall": palette["fall"], "neutral": palette["accent"], "good": GOOD}
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
.ov-good {{ color:{GOOD}; }}
.ov-spark {{ display:block; flex:none; }}
[class*="st-key-ov_card_"] {{ background:{card}; border:1px solid {border} !important; border-radius:12px !important;
  padding:12px 16px 8px !important; gap:2px !important; height:max(calc((100vh - 318px) / 2), 196px) !important;
  min-height:max(calc((100vh - 318px) / 2), 196px) !important; }}
[class*="st-key-ov_card_"] [data-testid="stElementContainer"]:has([data-testid="stVegaLiteChart"]) {{
  flex:1 1 0; min-height:0; display:flex; flex-direction:column; }}
[class*="st-key-ov_card_"] [data-testid="stFullScreenFrame"], [class*="st-key-ov_card_"] [data-testid="stFullScreenFrame"] > div,
[class*="st-key-ov_card_"] [data-testid="stVegaLiteChart"] {{ flex:1 1 auto; height:100%; min-height:0; }}
[class*="st-key-ov_card_"] [data-testid="stElementToolbar"] {{ display:none !important; }}
.st-key-ov_tabs {{ margin-top:-14px; }}
.st-key-ov_tabs [data-testid="stTabs"] [role="tabpanel"] {{ padding-top:10px; }}
[class*="st-key-ov_head_"] {{ align-items:center; justify-content:space-between; }}
[class*="st-key-ov_head_"] [data-testid="stSlider"] {{ padding:0 4px; }}
.ov-card-title {{ margin:0 !important; font-size:14px !important; font-weight:600; color:{ink} !important; line-height:1.3 !important; }}
[class*="st-key-ov_card_"] [data-testid="stElementContainer"]:has(.ov-card-title) {{ margin-bottom:14px !important; }}
[class*="st-key-ov_card_"] [data-testid="stMarkdown"] {{ margin-bottom:0 !important; }}
.ov-card-note {{ margin:0 !important; font-size:11.5px !important; color:{muted} !important; line-height:1.35 !important;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.st-key-ov_tabs [data-baseweb="tab-list"] {{ gap:4px; }}
.st-key-ov_tabs [data-baseweb="tab"] p {{ font-size:13.5px; font-weight:600; }}
@media (max-width:1100px) {{ .ov-scores {{ grid-template-columns:repeat(3, minmax(0, 1fr)); }} }}
</style>"""
# endregion


# region Charts
def style(chart, mode, height=None):
    """Width and height from the card: the charts grow with the window (D-296)."""
    return charts.apply_chart_style(chart.properties(width="container", height=height or "container"), mode)


def combo_chart(weeks, mode, height=None):
    """Bars: the price alerts of each week; line: the typical change, on its own axis."""
    palette = charts.get_palette(mode)
    base = alt.Chart(weeks).encode(x=alt.X("week_start:T", title=None, axis=alt.Axis(format="%d %b", labelAngle=0,
                                                                                      tickCount=8)))
    tooltip = [alt.Tooltip("week_start:T", title="Semana", format="%d-%m-%Y"),
               alt.Tooltip("alerts:Q", title="Alertas", format=",d"),
               alt.Tooltip("typical:Q", title="Cambio típico (%)", format="+.2f"),
               alt.Tooltip("comparable:Q", title="Precios comparables", format=",d")]
    bars = base.mark_bar(color=palette["accent"], opacity=.55, cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        y=alt.Y("alerts:Q", title="Alertas", axis=alt.Axis(titleFontSize=11, tickCount=4, format="d")), tooltip=tooltip)
    line = base.mark_line(color=palette["rise"], strokeWidth=2, point=alt.OverlayMarkDef(size=26, filled=True)).encode(
        y=alt.Y("typical:Q", title="Cambio típico (%)", axis=alt.Axis(titleFontSize=11, tickCount=4, orient="right")),
        tooltip=tooltip)
    return style(alt.layer(bars, line).resolve_scale(y="independent"), mode, height)


def donut(frame, category, value, mode, colors=None, selected=None, height=None, name="pick"):
    """A donut of `value` by `category`; a click picks a category (the selection is named `name`)."""
    palette = charts.get_palette(mode)
    names = list(frame[category])
    scale = alt.Scale(domain=names, range=[colors.get(n, palette["accent"]) for n in names]) if colors else alt.Scale()
    pick = alt.selection_point(name=name, fields=[category], on="click", clear="dblclick")
    opacity = (alt.condition(alt.datum[category] == selected, alt.value(1), alt.value(.35)) if selected
               else alt.condition(pick, alt.value(1), alt.value(.4)))
    total = frame[value].sum()
    frame = frame.assign(share=frame[value] / total * 100 if total else 0)
    chart = alt.Chart(frame).mark_arc(innerRadius=50, outerRadius=78, padAngle=.012, cornerRadius=3).encode(
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


def ranked_bars(frame, label, value, mode, height=None, percent=True, reference=None, name="rank", selected=None):
    """Horizontal bars ranked by value: red above zero (or the reference), blue below, with the value at the end."""
    palette = charts.get_palette(mode)
    cut = reference if reference is not None else 0
    frame = frame.assign(_tone=(["rise" if v > cut else "fall" for v in frame[value]] if percent else ["count"] * len(frame)),
                         _text=[f"{v:+.1f} %".replace(".", ",") if percent else f"{v:,.0f}".replace(",", ".") for v in frame[value]])
    order = list(frame.sort_values(value, ascending=False)[label])
    pick = alt.selection_point(name=name, fields=[label], on="click", clear="dblclick")
    opacity = (alt.condition(alt.datum[label] == selected, alt.value(1), alt.value(.35)) if selected
               else alt.condition(pick, alt.value(1), alt.value(.45)))
    y = alt.Y(f"{label}:N", sort=order, title=None, axis=alt.Axis(labelLimit=160, labelFontSize=11.5, ticks=False, domain=False))
    bars = alt.Chart(frame).mark_bar(cornerRadius=2, height={"band": .62}).encode(
        y=y, x=alt.X(f"{value}:Q", title=None, axis=alt.Axis(labels=False, ticks=False, grid=False, domain=False)),
        color=alt.Color("_tone:N", scale=alt.Scale(domain=["rise", "fall", "count"],
                                                   range=[palette["rise"], palette["fall"], palette["accent"]]), legend=None),
        opacity=opacity, tooltip=[alt.Tooltip(f"{label}:N", title="Grupo"), alt.Tooltip("_text:N", title="Valor")]).add_params(pick)
    # The value sits past the end of its bar: to the right of a rise, to the left of a fall.
    ahead = alt.Chart(frame[frame[value] >= 0]).mark_text(align="left", dx=5, fontSize=11.5, fontWeight=600,
                                                          color=palette["text"]).encode(y=y, x=alt.X(f"{value}:Q"), text="_text:N")
    behind = alt.Chart(frame[frame[value] < 0]).mark_text(align="right", dx=-5, fontSize=11.5, fontWeight=600,
                                                          color=palette["text"]).encode(y=y, x=alt.X(f"{value}:Q"), text="_text:N")
    layers = [bars, ahead, behind]
    if reference is not None:
        layers.append(alt.Chart(pd.DataFrame({"r": [reference]})).mark_rule(color=palette["strong_text"], strokeDash=[4, 3]).encode(x="r:Q"))
    else:
        layers.append(alt.Chart(pd.DataFrame({"r": [0]})).mark_rule(color=palette["reference"], opacity=.7).encode(x="r:Q"))
    low, high = float(min(0, frame[value].min())), float(max(0, frame[value].max()))
    span = (high - low) or 1
    for layer in layers[:3]:
        layer.encoding.x.scale = alt.Scale(domain=[low - span * (.28 if low < 0 else 0), high + span * .28])
    return style(alt.layer(*layers), mode, height)


def region_bars(frame, mode, height=None):
    """Each region, north to south: to the right the share of its prices that rose, to the left the share that fell."""
    palette = charts.get_palette(mode)
    order = list(frame["label"])
    long = pd.concat([frame.assign(share=frame["up_share"], kind="Subieron"),
                      frame.assign(share=frame["down_share"], kind="Bajaron")])
    long["text"] = [f"{abs(v):.0f} %" for v in long["share"]]
    y = alt.Y("label:N", sort=order, title=None, axis=alt.Axis(labelFontSize=11.5, ticks=False, domain=False, labelLimit=120))
    limit = max(60.0, float(long["share"].abs().max()) + 24)
    x = alt.X("share:Q", title=None, scale=alt.Scale(domain=[-limit, limit]),
              axis=alt.Axis(labels=False, ticks=False, grid=False, domain=False))
    bars = alt.Chart(long).mark_bar(cornerRadius=2, height={"band": .6}).encode(
        y=y, x=x, color=alt.Color("kind:N", scale=alt.Scale(domain=["Subieron", "Bajaron"], range=[palette["rise"], palette["fall"]]),
                                  legend=None),
        tooltip=[alt.Tooltip("region:N", title="Región"), alt.Tooltip("kind:N", title="Dirección"),
                 alt.Tooltip("text:N", title="De sus precios comparables"), alt.Tooltip("total:Q", title="Comparables")])
    right = alt.Chart(long[long["share"] >= 0]).mark_text(fontSize=11, color=palette["text"], align="left", dx=4).encode(
        y=y, x=x, text="text:N")
    left = alt.Chart(long[long["share"] < 0]).mark_text(fontSize=11, color=palette["text"], align="right", dx=-4).encode(
        y=y, x=x, text="text:N")
    axis = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color=palette["reference"], opacity=.7).encode(x="z:Q")
    return style(alt.layer(bars, right, left, axis), mode, height)


def heat_table(frame, row, column, value, mode, height=None, column_order=None, row_sort=None):
    """A table whose cells are colored by their value: red rises, blue falls, the value written inside."""
    palette = charts.get_palette(mode)
    limit = max(1.0, float(frame[value].abs().quantile(.9))) if not frame.empty else 1.0
    frame = frame.assign(_text=[f"{v:+.1f}".replace(".", ",") for v in frame[value]])
    x = alt.X(f"{column}:O", title=None, sort=column_order, axis=alt.Axis(labelAngle=0, orient="top", ticks=False,
                                                                           domain=False, labelFontSize=11))
    y = alt.Y(f"{row}:N", title=None, sort=row_sort, axis=alt.Axis(labelLimit=150, labelFontSize=11.5, ticks=False, domain=False))
    frame = frame.assign(_tone=["rise" if v >= STILL * 100 else "fall" if v <= -STILL * 100 else "still" for v in frame[value]],
                         _size=frame[value].abs())
    cells = alt.Chart(frame).mark_rect(cornerRadius=3, stroke=palette["card"], strokeWidth=2).encode(
        x=x, y=y, color=alt.Color("_tone:N", legend=None, scale=alt.Scale(
            domain=["rise", "fall", "still"], range=[palette["rise"], palette["fall"], palette["card_border"]])),
        opacity=alt.Opacity("_size:Q", legend=None, scale=alt.Scale(domain=[0, limit], range=[.18, .95], clamp=True)),
        tooltip=[alt.Tooltip(f"{row}:N", title="Grupo"), alt.Tooltip(f"{value}:Q", title="Cambio (%)", format="+.2f")])
    text = alt.Chart(frame).mark_text(fontSize=11, color=palette["strong_text"]).encode(x=x, y=y, text="_text:N")
    return style(alt.layer(cells, text), mode, height)


def line_chart(frame, x, y, mode, height=None, title_y="", fmt="+.1f", color=None):
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


def stacked_runs(runs, mode, height=None):
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
