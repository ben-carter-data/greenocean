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
import json
from functools import lru_cache
from pathlib import Path

import altair as alt
import pandas as pd

from bi import charts, home_mockup, i18n, inflation_view

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
    many = len(last) > 8
    frame["week"] = [f"{w.day}/{w.month}" if many else f"{w.day:02d} {months[w.month - 1].lower()}" for w in frame["week_start"]]
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
                                                 else "Alimentos en general")
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
    """A row of scorecards: [(label, value, note, trend values or None, tone[, hint])] with tone rise, fall, neutral or
    good; the hint (D-301) opens on hover: what the number is, against what, and what it says."""
    tone_color = {"rise": palette["rise"], "fall": palette["fall"], "neutral": palette["accent"], "good": GOOD}
    items = []
    for label, value, note, trend, tone, *hint in cards:
        spark = sparkline(trend, tone_color.get(tone, palette["accent"])) if trend is not None else ""
        tip = f'<span class="ov-tip">{html.escape(hint[0])}</span>' if hint and hint[0] else ""
        items.append(f'<div class="ov-score" tabindex="0">{tip}<span class="ov-score-label">{html.escape(label)}</span>'
                     f'<span class="ov-score-value">{html.escape(value)}</span>'
                     f'<span class="ov-score-foot"><span class="ov-score-note ov-{tone}">{html.escape(note)}</span>{spark}</span>'
                     '</div>')
    return f'<div class="ov-scores">{"".join(items)}</div>'


def build_css(palette):
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    return f"""<style>
.ov-scores {{ display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:10px; margin:0 0 2px; }}
.ov-score {{ display:flex; flex-direction:column; gap:1px; padding:6px 12px 5px; border-radius:10px; background:{card};
  border:1px solid {border}; min-width:0; }}
.ov-score-label {{ font-size:11.5px; font-weight:500; color:{muted}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ov-score-value {{ font-size:20px; font-weight:600; color:{ink}; letter-spacing:-.01em; line-height:1.15; white-space:nowrap; }}
.ov-score-foot {{ display:flex; align-items:center; justify-content:space-between; gap:8px; min-height:22px; }}
.ov-score-note {{ font-size:11.5px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ov-rise {{ color:{palette['rise']}; }} .ov-fall {{ color:{palette['fall']}; }} .ov-neutral {{ color:{text}; }}
.ov-good {{ color:{GOOD}; }}
.ov-spark {{ display:block; flex:none; }}
.ov-score {{ position:relative; cursor:help; }}
.ov-tip {{ display:none; position:absolute; top:calc(100% + 6px); left:0; z-index:60; width:max(100%, 270px); max-width:330px;
  padding:9px 12px; border-radius:10px; background:{card}; border:1px solid {border}; color:{text};
  box-shadow:0 14px 34px -14px rgba(0,0,0,.45); font-size:12px; font-weight:400; line-height:1.45; text-align:left;
  white-space:normal; letter-spacing:0; text-transform:none; }}
.ov-score:nth-child(n+4) .ov-tip {{ left:auto; right:0; }}
.ov-score:hover .ov-tip, .ov-score:focus .ov-tip {{ display:block; }}
.ov-card-title {{ position:relative; cursor:help; }}
.ov-card-title .ov-info {{ display:inline-flex; align-items:center; justify-content:center; width:15px; height:15px; margin-left:6px;
  border-radius:50%; border:1px solid {muted}; color:{muted}; font-size:10px; font-weight:600; vertical-align:2px; }}
.ov-card-title .ov-tip {{ top:calc(100% + 4px); width:min(360px, 92%); max-width:none; }}
.ov-card-title:hover .ov-tip {{ display:block; }}
.ov-card-title:hover .ov-info {{ border-color:{accent}; color:{accent}; }}
[class*="st-key-ov_card_"] {{ background:{card}; border:1px solid {border} !important; border-radius:12px !important;
  padding:12px 16px 8px !important; gap:2px !important; height:max(calc((100vh - 318px) / 2), 196px) !important;
  min-height:max(calc((100vh - 318px) / 2), 196px) !important; }}
[class*="st-key-ov_card_"] [data-testid="stElementContainer"]:has([data-testid="stVegaLiteChart"]) {{
  flex:1 1 0; min-height:0; display:flex; flex-direction:column; }}
[class*="st-key-ov_card_"] [data-testid="stFullScreenFrame"], [class*="st-key-ov_card_"] [data-testid="stFullScreenFrame"] > div,
[class*="st-key-ov_card_"] [data-testid="stVegaLiteChart"] {{ flex:1 1 auto; height:100%; min-height:0; }}
[class*="st-key-ov_card_"] [data-testid="stElementToolbar"] {{ display:none !important; }}
.st-key-ov_tabs {{ margin-top:-14px; }}
[class*="st-key-ov_card_"][class*="_small"] {{ height:auto !important; min-height:0 !important; }}
[class*="st-key-ov_card_"][class*="_wide"] {{ height:auto !important; min-height:0 !important; max-height:max(calc(100vh - 500px), 236px); overflow:auto; }}
[class*="st-key-ov_card_"][class*="_wide"] [data-testid="stElementContainer"]:has(.ov-ht),
[class*="st-key-ov_card_"][class*="_wide"] [data-testid="stElementContainer"]:has(.ov-qt) {{ flex:0 0 auto; min-height:0; overflow:visible; }}
[class*="st-key-ov_card_"][class*="_wide"] [data-testid="stMarkdown"]:has(.ov-ht),
[class*="st-key-ov_card_"][class*="_wide"] [data-testid="stMarkdownContainer"]:has(.ov-ht) {{ height:100%; }}
.st-key-ov_tabs [data-testid="stTabs"] [role="tabpanel"] {{ padding-top:10px; }}
[class*="st-key-ov_head_"] {{ align-items:center; justify-content:space-between; }}
[class*="st-key-ov_head_"] [data-testid="stSlider"] {{ padding:0 4px; }}
[class*="st-key-ov_head_"] [data-testid="stSliderTickBar"], [class*="st-key-ov_head_"] [data-testid="stTooltipIcon"] {{
  display:none !important; }}
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


def donut(frame, category, value, mode, colors=None, selected=None, height=None, name="pick", legend="right"):
    """A donut of `value` by `category`; a click picks a category (the selection is named `name`)."""
    palette = charts.get_palette(mode)
    names = list(frame[category])
    scale = alt.Scale(domain=names, range=[colors.get(n, palette["accent"]) for n in names]) if colors else alt.Scale()
    pick = alt.selection_point(name=name, fields=[category], on="click", clear="dblclick")
    opacity = (alt.condition(alt.datum[category] == selected, alt.value(1), alt.value(.35)) if selected
               else alt.condition(pick, alt.value(1), alt.value(.4)))
    total = frame[value].sum()
    frame = frame.assign(share=frame[value] / total * 100 if total else 0)
    chart = alt.Chart(frame).mark_arc(outerRadius={"expr": "min(width, height) / 2 - 6"}, innerRadius={"expr": "(min(width, height) / 2 - 6) * .64"},
                                       padAngle=.012, cornerRadius=3).encode(
        theta=alt.Theta(f"{value}:Q", stack=True),
        color=alt.Color(f"{category}:N", scale=scale, sort=names,
                        legend=alt.Legend(title=None, orient=legend, labelFontSize=11.5, symbolType="circle",
                                          symbolSize=90, labelLimit=170, direction="vertical")),
        opacity=opacity, order=alt.Order(f"{value}:Q", sort="descending"),
        tooltip=[alt.Tooltip(f"{category}:N", title="Grupo"), alt.Tooltip(f"{value}:Q", title="Cantidad", format=",d"),
                 alt.Tooltip("share:Q", title="Participación (%)", format=".1f")]).add_params(pick)
    center = alt.Chart(pd.DataFrame({"t": [f"{total:,}".replace(",", ".")]})).mark_text(
        fontSize={"expr": "max(11, min(20, min(width, height) / 9))"}, fontWeight=600, color=palette["strong_text"]).encode(text="t:N")
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
    columns = frame[column].nunique()
    frame = frame.assign(_text=[f"{v:+.1f}".replace(".", ",") for v in frame[value]])
    size = 11 if columns <= 8 else 10
    x = alt.X(f"{column}:O", title=None, sort=column_order, axis=alt.Axis(labelAngle=0, orient="top", ticks=False,
                                                                           domain=False, labelFontSize=11 if columns <= 8 else 10,
                                                                           labelOverlap=False))
    y = alt.Y(f"{row}:N", title=None, sort=row_sort, axis=alt.Axis(labelLimit=150 if columns <= 8 else 118, labelFontSize=11.5,
                                                                    ticks=False, domain=False))
    frame = frame.assign(_tone=["rise" if v >= STILL * 100 else "fall" if v <= -STILL * 100 else "still" for v in frame[value]],
                         _size=frame[value].abs())
    cells = alt.Chart(frame).mark_rect(cornerRadius=3, stroke=palette["card"], strokeWidth=2).encode(
        x=x, y=y, color=alt.Color("_tone:N", legend=None, scale=alt.Scale(
            domain=["rise", "fall", "still"], range=[palette["rise"], palette["fall"], palette["card_border"]])),
        opacity=alt.Opacity("_size:Q", legend=None, scale=alt.Scale(domain=[0, limit], range=[.18, .95], clamp=True)),
        tooltip=[alt.Tooltip(f"{row}:N", title="Grupo"), alt.Tooltip(f"{value}:Q", title="Cambio (%)", format="+.2f")])
    text = alt.Chart(frame).mark_text(fontSize=size, color=palette["strong_text"]).encode(x=x, y=y, text="_text:N")
    return style(alt.layer(cells, text), mode, height)


def build_heat_table_html(frame, row, column, value, columns, rows, palette, logos=None):
    """D-301: the heat table as an HTML table that fills its card: one row per family with its picture, one column per
    period, each cell tinted by its change (red rises, blue falls, the stronger the darker) and its value written in it.
    On a narrow window the first column stays and the periods scroll."""
    cells = {(r, c): v for r, c, v in zip(frame[row], frame[column], frame[value])}
    limit = max(1.0, float(frame[value].abs().quantile(.9))) if not frame.empty else 1.0
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in columns)
    body = []
    for name in rows:
        picture = (logos or {}).get(name)
        full = next((family for family, short in home_mockup.FAMILY_SHORT_NAMES.items() if short == name), name)
        label = (f'<img src="{picture}" alt="">' if picture else '<span class="ov-ht-dot"></span>') + f"<span>{html.escape(name)}</span>"
        tds = []
        for c in columns:
            v = cells.get((name, c))
            if v is None:
                tds.append('<td class="ov-ht-empty">·</td>')
                continue
            tone = palette["rise"] if v >= STILL * 100 else palette["fall"] if v <= -STILL * 100 else None
            strength = min(1.0, abs(v) / limit)
            style = f' style="background:color-mix(in srgb, {tone} {12 + strength * 70:.0f}%, transparent)"' if tone else ""
            strong = " ov-ht-strong" if tone and strength > .6 else ""
            number = f"{v:+.1f}".replace(".", ",")
            tds.append(f'<td class="ov-ht-cell{strong}"{style}>{number}</td>')
        body.append(f'<tr><th scope="row" title="{html.escape(full, quote=True)}">{label}</th>{"".join(tds)}</tr>')
    return (f'<div class="ov-ht" style="--cols:{len(columns)}"><table><thead><tr><th></th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def heat_table_css(palette):
    ink, text, muted, border = palette["strong_text"], palette["text"], palette["reference"], palette["card_border"]
    return f"""<style>
.ov-ht {{ overflow-x:auto; }}
.ov-ht table {{ width:100%; min-width:calc(170px + var(--cols) * 64px); border-collapse:collapse; table-layout:fixed; margin:0; }}
.ov-ht th, .ov-ht td {{ border:1px solid {border} !important; }}
.ov-ht thead th {{ border-top:0 !important; }}
.ov-ht thead th {{ font-size:12px; font-weight:600; color:{muted}; text-align:center; padding:0 0 2px; background:transparent !important; }}
.ov-ht thead th:first-child, .ov-ht tbody th {{ width:24%; min-width:150px; }}
.ov-ht tbody th {{ text-align:left; font-weight:600; font-size:13px; color:{ink}; padding:0 8px 0 0; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; position:sticky; left:0; background:{palette['card']} !important; }}
.ov-ht tbody th img {{ width:20px; height:20px; vertical-align:middle; margin-right:8px; object-fit:contain; }}
.ov-ht tbody th span {{ vertical-align:middle; }}
.ov-ht-dot {{ display:inline-block; width:20px; height:20px; margin-right:8px; vertical-align:middle; }}
.ov-ht td {{ text-align:center; font-size:13px; line-height:1.2; font-variant-numeric:tabular-nums; color:{ink}; 
  background:color-mix(in srgb, {border} 30%, transparent); padding:0 2px; min-width:54px; }}
.ov-ht td.ov-ht-strong {{ color:#ffffff; font-weight:600; }}
.ov-ht td.ov-ht-empty {{ color:{muted}; }}
</style>"""


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
    runs = runs.assign(label=[f"{d[8:10]}-{d[5:7]}" for d in runs["started_at"]])
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


# region Insights (D-302)
# What the dashboard answers, the KPIs that answer it and why, and the insights of the current load.
KPIS = [
    ("Cambio típico", "Mediana de los cambios semanales de los precios comparables: los que tienen precio en las mismas "
     "regiones ambas semanas.", "La mediana no se mueve por un precio extremo, y comparar las mismas regiones evita "
     "confundir un cambio de cobertura con un cambio de precio."),
    ("Subieron y bajaron", "Precios comparables con un cambio de al menos +0,05 % (o −0,05 %), sobre el total de "
     "comparables.", "Dice si el movimiento es general o de unos pocos productos."),
    ("Dirección de una región", "Una región sube o baja solo si sus alzas y bajas difieren más de lo que da el azar "
     "(prueba de signo, p < 0,05).", "Un 52 % contra un 48 % no es una tendencia: es una moneda al aire."),
    ("Alerta de precio", "Un cambio fuera del promedio ± 2 desviaciones de sus 12 semanas previas, de al menos 10 % y con "
     "dos cotizaciones en cada semana.", "Separa lo inusual y material del ruido de cada semana."),
    ("Alza frente al IPC", "Índice de la familia (enero 2022 = 100, mediana de sus series de consumidor) frente al IPC de "
     "alimentos del INE; ± 2 puntos es «al ritmo».", "Dice si una familia se encareció o se abarató en términos reales."),
    ("Precio real", "Precio de la semana × IPC del último mes publicado ÷ IPC del mes de esa semana.",
     "Permite comparar precios de distintos años en pesos de hoy."),
    ("Brecha consumidor–mayorista", "(Precio al consumidor − precio mayorista) ÷ precio mayorista, mismo producto, "
     "región, unidad y semana.", "Muestra cuánto se agrega entre el mercado mayorista y la góndola."),
    ("Calidad de los datos", "11 indicadores en cinco dimensiones (completitud, actualidad, validez, unicidad y "
     "consistencia) más controles de exactitud.", "Una cifra solo vale si los datos de origen están completos y son "
     "válidos."),
]


def signed(value):
    """A change in %, with the decimal mark of the language: lists of names are not translated as a whole."""
    text = f"{value:+.1f} %"
    return text if i18n.is_english() else text.replace(".", ",")


def join(names):
    return i18n.join_names(list(names))


def best_drops(variations, week, count=3):
    """The largest weekly drops of the week, resting on two quotes in each week (as the Resumen ranks them)."""
    rows = comparable(variations[variations["week_start"] == week])
    if "same_region_quotes" in rows:
        rows = rows[(rows["same_region_quotes"] >= 2) & (rows["same_region_previous_quotes"] >= 2)]
    rows = rows[rows["variation"] < 0].nsmallest(count, "variation")
    return [(product, channel, value * 100) for product, channel, value in zip(rows["product"], rows["channel"], rows["variation"])]


def consumer_insights(moves, drops, summary, ipc_total, ipc_year):
    """For whoever buys food: what got cheaper this week and which families weigh more than inflation."""
    fell = moves[moves["state"] == "Bajó"]
    rose = moves[moves["state"] == "Subió"]
    above = summary[summary["verdict"] == "más que la inflación"]
    below = summary[summary["verdict"] == "menos que la inflación"]
    short = home_mockup.short_family
    lines = []
    if len(fell):
        lines.append(f"Esta semana bajaron {join(f'{short(f)} ({signed(c)})' for f, c in zip(fell['product_group'], fell['change']))}; "
                     f"subieron {join(f'{short(f)} ({signed(c)})' for f, c in zip(rose['product_group'], rose['change'])) or 'ninguna familia'}.")
    if drops:
        lines.append("Las mayores bajas, con al menos dos cotizaciones por semana: "
                     + join(f"{product} · {channel.lower()} ({signed(value)})" for product, channel, value in drops) + ".")
    if len(above):
        lines.append(f"Desde enero 2022, {join(short(f) for f in above['family'])} subieron más que el IPC de alimentos "
                     f"({signed(ipc_total)}): son las que más pesan hoy en la canasta. "
                     + (f"{join(short(f) for f in below['family'])} subieron menos: en términos reales, se abarataron." if len(below) else ""))
    lines.append(f"En los últimos 12 meses, los alimentos subieron {signed(ipc_year)}.")
    return lines


def architect_insights(latest, tests, green, indicators, database, flags, comparable_now, prices_now):
    """For whoever designs the data: what the load brought, how much of it reaches the indicators and where it is lost."""
    number = lambda value: f"{int(value):,}".replace(",", ".")
    day = f"{latest['started_at'][8:10]}-{latest['started_at'][5:7]}-{latest['started_at'][:4]}"
    total = int(flags["weekly_prices"].sum())
    by_flag = flags.groupby("flag")["weekly_prices"].sum()
    unconvertible, outliers = int(by_flag.get("UNIDAD_NO_CONVERTIBLE", 0)), int(by_flag.get("ATIPICO", 0))
    share = lambda part: f"{part / total * 100:.1f} %".replace(".", ",")
    lines = [
        f"La carga del {day} leyó {number(latest['rows_read'])} filas de los archivos de ODEPA y rechazó "
        f"{number(latest['rows_rejected'])} con su motivo; pasaron {tests[0]} de {tests[1]} pruebas de dbt y {green} de "
        f"{indicators} indicadores de calidad están en su umbral.",
        f"La base servida tiene {number(database['prices'])} precios semanales en {number(database['weeks'])} semanas sin "
        f"huecos, de {database['regions']} regiones y {database['channels']} canales.",
    ]
    if unconvertible or outliers:
        bigger = "las unidades que no se pueden convertir" if unconvertible >= outliers else "los precios atípicos"
        lines.append(f"{number(unconvertible)} precios ({share(unconvertible)}) quedan fuera de los indicadores por unidad no "
                     f"convertible y {number(outliers)} ({share(outliers)}) por atípicos: la mayor pérdida está en {bigger}, "
                     "donde una regla nueva sumaría más datos.")
    lines.append(f"Esta semana, {number(comparable_now)} de {number(prices_now)} precios tienen comparación con la anterior: "
                 "el resto no tiene precio la semana previa en las mismas regiones.")
    return lines
# endregion


def wholesale_insights(variations, week, margins):
    """For whoever buys wholesale (a shop, a restaurant): how the wholesale price moved this week, its biggest drops and
    the gap up to the consumer price. ODEPA's wholesale prices cover fruit and vegetables only."""
    short = home_mockup.short_family
    rows = comparable(variations[(variations["week_start"] == week) & (variations["channel"] == "Mayorista")])
    lines = []
    if not rows.empty:
        moves = rows.groupby("product_group")["variation"].median().mul(100)
        lines.append("En el mercado mayorista, el cambio típico de la semana fue "
                     + join(f"{short(f)} {signed(v)}" for f, v in moves.items()) + ".")
        drops = list({product: (product, channel, value) for product, channel, value
                      in reversed(best_drops(rows.assign(week_start=week), week, count=8))}.values())[::-1][:3]
        if drops:
            lines.append("Las mayores bajas mayoristas: " + join(f"{product} ({signed(value)})" for product, _, value in drops) + ".")
    week_margins = margins[margins["week_start"] == f"{week:%Y-%m-%d}"]
    if not week_margins.empty:
        gaps = week_margins.groupby("product_group")["margin"].median().mul(100)
        lines.append("Del precio mayorista al consumidor, el mismo producto sube típicamente "
                     + join(f"{short(f)} {signed(v)}" for f, v in gaps.items())
                     + ": es el margen que separa la compra por mayor de la góndola.")
    lines.append("ODEPA publica precios mayoristas solo de frutas y hortalizas.")
    return lines


# region Where to buy (D-306)
POINTS_FILE = Path(__file__).with_name("assets") / "points_of_sale.json"


def read_points():
    """{region: {wholesale, consumer, sectors}}: what exists in each region, from ODEPA's own files (no price)."""
    return json.loads(POINTS_FILE.read_text(encoding="utf-8"))


POINT_ICONS = {"person": "persona", "mercado": "mercado", "datos": "datos", "Supermercado": "supermercado", "Supermercado en Línea": "linea", "Feria libre": "feria", "Carnicería": "carniceria",
               "Panadería": "panaderia", "Mercado Minorista": "minorista", "Mercado Mayorista": "mercado"}
REGIONS_PER_VIEW = 3


@lru_cache(maxsize=None)
def point_icon(name):
    """An icon of the folder bi/assets/points as an image (st.html drops inline SVG)."""
    path = POINTS_FILE.parent / "points" / f"{POINT_ICONS.get(name, 'mercado')}.svg"
    return f'<img class="ov-icon" alt="" src="data:image/svg+xml;base64,{base64.b64encode(path.read_bytes()).decode()}">'


def ordered_regions(points, region_ids):
    return sorted(points, key=lambda name: REGION_ORDER.index(region_ids[name]) if region_ids.get(name) in REGION_ORDER else 99)


DETAIL_SHOP = "Comercio al detalle"


def build_region_card(region, data):
    """One region as a card: each wholesale market as a big house with its name and, in one more house, every kind of
    consumer point ODEPA records there, shown inside it by its own icon and named on hover."""
    markets = "".join(f'<li>{point_icon("Mercado Mayorista")}<span>{html.escape(name)}</span></li>' for name in data["wholesale"])
    kinds = [name for name in data["consumer"] if name != "Mercado Mayorista"]
    inside = "".join(f'<b class="ov-hint">{point_icon(name)}<em class="ov-hint-tip">{html.escape(i18n.tr(name))}</em></b>' for name in kinds)
    detail = (f'<li class="ov-common">{point_icon("Minorista")}<span>{html.escape(i18n.tr(DETAIL_SHOP))}</span>'
              f'<div class="ov-inside">{inside}</div></li>' if kinds else "")
    sectors = (f'<p class="ov-sectors">{html.escape(i18n.tr("Sectores de la ciudad"))}: {html.escape(", ".join(data["sectors"]))}</p>'
               if data["sectors"] else "")
    none = f'<p class="ov-none">{html.escape(i18n.tr("Sin mercado mayorista en los datos"))}</p>' if not markets else ""
    return (f'<div class="ov-rcard"><h5>{html.escape(home_mockup.short_region(region))}</h5>'
            f'<h6>{html.escape(i18n.tr("Dónde se compra"))}</h6><ul class="ov-markets">{markets}{detail}</ul>{none}{sectors}</div>')


def points_css(palette):
    ink, text, muted, border, accent, card = (palette["strong_text"], palette["text"], palette["reference"], palette["card_border"],
                                              palette["accent"], palette["card"])
    return f"""<style>
.ov-rcard {{ margin-bottom:1rem; min-height:calc(100vh - 190px); border-radius:18px; padding:18px 18px 14px; border:1px solid {border};
  background:linear-gradient(160deg, color-mix(in srgb, {accent} 9%, {card}), {card}); box-shadow:0 14px 30px -20px rgba(0,0,0,.55); }}
.ov-rcard h5 {{ margin:0 0 4px !important; padding:0 !important; font-size:22px !important; color:{ink}; }}
.ov-rcard h6 {{ margin:6px 0 14px !important; padding:0 !important; font-size:11px !important; font-weight:600; letter-spacing:.07em;
  text-transform:uppercase; color:{muted}; }}
.ov-rcard ul {{ list-style:none; margin:0; padding:0; display:flex; flex-wrap:wrap; gap:22px 10px; justify-content:center; }}
.ov-rcard li {{ position:relative; display:flex; flex-direction:column; align-items:center; gap:4px; width:46%; text-align:center;
  font-size:13.5px; font-weight:600; line-height:1.25; color:{ink}; }}
.ov-icon {{ width:112px; height:112px; display:block; filter:drop-shadow(0 12px 8px rgba(0,0,0,.3)); transition:transform .25s ease; }}
.ov-rcard li:hover > .ov-icon {{ transform:translateY(-5px) scale(1.05); }}
.ov-common {{ width:100% !important; }}
.ov-inside {{ display:flex; gap:10px; justify-content:center; margin-top:4px; }}
.ov-inside b {{ position:relative; cursor:help; }}
.ov-inside .ov-icon {{ width:34px; height:34px; filter:drop-shadow(0 4px 3px rgba(0,0,0,.25)); }}
.ov-hint-tip {{ display:none; position:absolute; z-index:20; bottom:100%; left:50%; transform:translateX(-50%); white-space:nowrap; padding:4px 8px;
  border-radius:8px; background:{ink}; color:{card}; font-size:11px; font-style:normal; font-weight:500; }}
.ov-hint:hover .ov-hint-tip {{ display:block; }}
.ov-sectors, .ov-none {{ margin:14px 0 0 !important; font-size:12.5px !important; color:{muted} !important; text-align:center; }}
</style>"""
# endregion
