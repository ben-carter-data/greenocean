"""«Análisis BA y BI» · «Tendencias» (D-456): the history of food prices for one period and one family, as a report of
KPI cards, three charts and a table by family. How much prices moved and against the food IPC, how much the consumer
pays over the wholesale price, how many price alerts there were and which months are cheaper. Every figure comes from
the queries and rules the rest of the panel uses: the monthly index of «Precios e inflación» (D-163), K1 (the margin),
K4 (the season) and K6 (the alerts). Nothing here is typed: each number is computed from the published database."""

from __future__ import annotations

import html
from typing import Any

import altair as alt
import pandas as pd

from bi import charts, home_mockup, i18n, inflation_view, weeks

BASKET = inflation_view.BASKET_NAME
IPC = inflation_view.IPC_NAME
BASE = (inflation_view.BASE_YEAR, inflation_view.BASE_MONTH)
LAST_YEAR = "Últimos 12 meses"
SINCE_BASE = "Desde ene 2022"


def say(spanish: str, english: str) -> str:
    """The text in the reader's language; in English, its figures written the English way (31,354 and 3.2 %)."""
    return i18n.localize_figures(english) if i18n.is_english() else spanish


def month_name(month: int) -> str:
    return (weeks.MONTHS_EN if i18n.is_english() else weeks.MONTHS)[month - 1]


def month_label(pair: tuple[int, int]) -> str:
    return f"{month_name(pair[1])} {pair[0]}"


# region Period
def periods(last: tuple[int, int]) -> list[str]:
    """The periods a reader can choose: the last 12 months, the whole history and each year, the latest first."""
    return [LAST_YEAR, SINCE_BASE] + [str(year) for year in range(last[0], BASE[0] - 1, -1)]


def bounds(period: str, last: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    """(start, end) months of a period. A change is measured from start to end, as «Precios e inflación» does: the last
    12 months go from the same month a year before; a year, from the December before (January 2022 for 2022)."""
    if period == SINCE_BASE:
        return BASE, last
    if period == LAST_YEAR:
        return (last[0] - 1, last[1]), last
    year = int(period)
    start = (year - 1, 12) if year > BASE[0] else BASE
    return start, (year, 12) if year < last[0] else last


def counted_months(start: tuple[int, int], end: tuple[int, int]) -> tuple[int, int]:
    """(first, last) as year * 100 + month: the months whose weeks a period counts. They are the months after its
    start, and the base month too when the period starts there."""
    if start == BASE:
        first = start
    else:
        first = (start[0] + 1, 1) if start[1] == 12 else (start[0], start[1] + 1)
    return first[0] * 100 + first[1], end[0] * 100 + end[1]


def add_month_key(frame: pd.DataFrame) -> pd.DataFrame:
    """The weekly rows with the month of their week as year * 100 + month, computed once."""
    stamp = pd.to_datetime(frame["week_start"])
    return frame.assign(month_key=stamp.dt.year * 100 + stamp.dt.month)


def month_domain(start: tuple[int, int], end: tuple[int, int], counted: bool = False) -> list[str]:
    """The time axis of a chart: the whole period, so every chart starts at its start month even where it has no data
    (no alert can be raised in the first 12 weeks of the history). counted: from the first month whose weeks count."""
    first = counted_months(start, end)[0] if counted else start[0] * 100 + start[1]
    if counted:  # bars fill their month, so the axis runs to the end of the last one
        last = (end[0] + 1, 1) if end[1] == 12 else (end[0], end[1] + 1)
    else:
        last = end
    return [f"{first // 100}-{first % 100:02d}-01", f"{last[0]}-{last[1]:02d}-01"]


def within(frame: pd.DataFrame, start: tuple[int, int], end: tuple[int, int], family: str) -> pd.DataFrame:
    """The weekly rows of a period and a family (every family for the whole basket)."""
    if frame.empty:
        return frame
    if "month_key" not in frame.columns:
        frame = add_month_key(frame)
    first, last = counted_months(start, end)
    chosen = frame[frame["month_key"].between(first, last)]
    return chosen if family == BASKET else chosen[chosen["product_group"] == family]


# endregion


# region Figures
def season(seasonal: pd.DataFrame) -> pd.DataFrame:
    """K4 by calendar month: the median of the weekly seasonal index (price over the average of its year), as a % over
    or under that average, with the weeks behind each month and the years they come from (D-456: a month of the calendar
    gathers its weeks of every year of the period, so the chart says which)."""
    if seasonal.empty:
        return pd.DataFrame(columns=["month", "change", "weeks", "years"])
    if "month_key" not in seasonal.columns:
        seasonal = add_month_key(seasonal)
    grouped = seasonal.assign(month=seasonal["month_key"] % 100, year=seasonal["month_key"] // 100).groupby("month")
    result = grouped["seasonal_index"].median().sub(1).mul(100).rename("change").to_frame()
    result["weeks"] = grouped["week_start"].nunique()
    first, last = grouped["year"].min(), grouped["year"].max()
    result["years"] = [str(a) if a == b else f"{a}–{b}" for a, b in zip(first, last)]
    return result.reset_index()


def summarize(
    rows: pd.DataFrame,
    margins: pd.DataFrame,
    seasonal: pd.DataFrame,
    alerts: pd.DataFrame,
    family: str,
    start: tuple[int, int],
    end: tuple[int, int],
) -> dict[str, Any]:
    """The figures of one family (or the whole basket) in one period."""
    change = inflation_view.change(rows, family, start, end)
    ipc = inflation_view.change(rows, IPC, start, end)
    gap = None if change is None or ipc is None else change - ipc
    pace = inflation_view.SAME_PACE_POINTS
    verdict = (
        None
        if gap is None
        else say("más que la inflación", "more than inflation")
        if gap > pace
        else say("menos que la inflación", "less than inflation")
        if gap < -pace
        else say("al ritmo de la inflación", "in step with inflation")
    )
    margin_rows = within(margins, start, end, family)
    alert_rows = within(alerts, start, end, family)
    profile = season(within(seasonal, start, end, family))
    cheapest = profile.loc[profile["change"].idxmin()] if not profile.empty else None
    dearest = profile.loc[profile["change"].idxmax()] if not profile.empty else None
    return {
        "family": family,
        "change": change,
        "ipc": ipc,
        "gap": gap,
        "verdict": verdict,
        "margin": None if margin_rows.empty else float(margin_rows["margin"].median() * 100),
        "pairs": len(margin_rows),
        "alerts": len(alert_rows),
        "rises": int((alert_rows["variation"] > 0).sum()) if not alert_rows.empty else 0,
        "falls": int((alert_rows["variation"] < 0).sum()) if not alert_rows.empty else 0,
        "cheapest": None if cheapest is None else (int(cheapest["month"]), float(cheapest["change"])),
        "dearest": None if dearest is None else (int(dearest["month"]), float(dearest["change"])),
        "profile": profile,
    }


def families(rows: pd.DataFrame) -> list[str]:
    return sorted(set(rows["product_group"]) - {IPC, BASKET})


# endregion


# region Drawing
def percent(value: float | None) -> str:
    return "—" if value is None or pd.isna(value) else charts.format_signed_percent(value)


def points(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return charts.format_signed_percent(value).replace(" %", "") + " pts"


def card(label: str, value: str, note: str, hint: str, tone: str = "") -> str:
    """One KPI card: what it measures, its figure, one line under it and, on hover, how it is computed."""
    return (
        f'<div class="ba-card" tabindex="0" title="{html.escape(hint, quote=True)}"><span class="ba-card-label">'
        f'{html.escape(label)}</span><b class="ba-card-value {tone}">{html.escape(value)}</b>'
        f'<span class="ba-card-note">{html.escape(note)}</span></div>'
    )


def build_cards(figures: dict[str, Any], start: tuple[int, int], end: tuple[int, int]) -> str:
    """The five KPI cards of a family and a period."""
    span = say(f"de {month_label(start)} a {month_label(end)}", f"from {month_label(start)} to {month_label(end)}")
    tone = lambda value: "" if value is None else "rise" if value > 0.05 else "fall" if value < -0.05 else ""  # noqa: E731
    cheapest, dearest = figures["cheapest"], figures["dearest"]
    cards = [
        card(
            say("Cambio de precios", "Price change"),
            percent(figures["change"]),
            span,
            say(
                "Índice mensual de los precios de consumidor de ODEPA (mediana de las series con precio en enero 2022 y "
                "en el último mes), del primer al último mes del período: el mismo de «Precios e inflación».",
                "Monthly index of ODEPA's consumer prices (median of the series priced in January 2022 and in the last "
                "month), from the first to the last month of the period: the same as «Prices and inflation».",
            ),
            tone(figures["change"]),
        ),
        card(
            say("Frente al IPC", "Against the CPI"),
            points(figures["gap"]),
            figures["verdict"] or "—",
            say(
                f"Diferencia, en puntos, entre el cambio de precios y el del IPC de alimentos del INE en los mismos meses "
                f"({percent(figures['ipc'])}). A más de {inflation_view.SAME_PACE_POINTS:.0f} puntos, subió más o "
                "menos que la inflación.",
                f"Difference, in points, between the price change and that of the INE food CPI in the same months "
                f"({percent(figures['ipc'])}). Beyond {inflation_view.SAME_PACE_POINTS:.0f} points, it rose more or less "
                "than inflation.",
            ),
            tone(figures["gap"]),
        ),
        card(
            say("Brecha consumidor–mayorista", "Consumer–wholesale gap"),
            "—" if figures["margin"] is None else charts.format_percent(figures["margin"]),
            say("sin precio mayorista que comparar", "no wholesale price to compare")
            if figures["margin"] is None
            else say(
                f"mediana de {charts.format_thousands(figures['pairs'])} pares",
                f"median of {charts.format_thousands(figures['pairs'])} pairs",
            ),
            say(
                "K1: cuánto más paga el consumidor que el precio mayorista del mismo producto, semana, región y unidad. "
                "No mide ganancia ni descuenta costos.",
                "K1: how much more the consumer pays than the wholesale price of the same product, week, region and "
                "unit. It does not measure profit or discount costs.",
            ),
        ),
        card(
            say("Alertas de precio", "Price alerts"),
            charts.format_thousands(figures["alerts"]),
            say(
                f"{charts.format_thousands(figures['rises'])} subidas · {charts.format_thousands(figures['falls'])} bajadas",
                f"{charts.format_thousands(figures['rises'])} rises · {charts.format_thousands(figures['falls'])} falls",
            ),
            say(
                "K6: semanas en que un producto cambió fuera de su rango habitual (promedio ± 2 desviaciones de sus 12 "
                "semanas previas), en al menos 10 % y con dos cotizaciones por semana. Son los valores atípicos.",
                "K6: weeks in which a product changed outside its usual range (average ± 2 deviations of its 12 previous "
                "weeks), by at least 10 % and with two quotes per week. They are the outliers.",
            ),
        ),
        card(
            say("Mes más barato", "Cheapest month"),
            "—" if cheapest is None else month_name(cheapest[0]),
            "—"
            if cheapest is None
            else say(
                f"{percent(cheapest[1])} · el más caro: {month_name(dearest[0])}",
                f"{percent(cheapest[1])} · the dearest: {month_name(dearest[0])}",
            ),
            say(
                "K4: el precio de cada semana sobre el promedio de su año; la mediana por mes del calendario dice qué "
                "meses suelen estar más baratos o más caros.",
                "K4: each week's price over the average of its year; the median by calendar month says which months "
                "tend to be cheaper or dearer.",
            ),
        ),
    ]
    return '<div class="ba-cards">' + "".join(cards) + "</div>"


def trend_chart(rows: pd.DataFrame, family: str, start: tuple[int, int], end: tuple[int, int], mode: str) -> Any:
    """«Precio mes a mes»: the family (or the basket) and the food IPC, both at 100 on the first month of the period."""
    palette = charts.get_palette(mode)
    key = rows["year"] * 100 + rows["month"]
    panel = rows[
        rows["product_group"].isin([family, IPC]) & key.between(start[0] * 100 + start[1], end[0] * 100 + end[1])
    ]
    first = panel[(panel["year"] == start[0]) & (panel["month"] == start[1])].set_index("product_group")["index"]
    panel = panel[panel["product_group"].isin(first.index)].assign(
        value=lambda frame: frame["index"] / frame["product_group"].map(first) * 100,
        serie=lambda frame: frame["product_group"].map(
            {family: home_mockup.short_family(family), IPC: say("IPC de alimentos", "Food CPI")}
        ),
    )
    names = [home_mockup.short_family(family), say("IPC de alimentos", "Food CPI")]
    color = inflation_view.FAMILY_COLORS.get(family, palette["accent"])
    chart = (
        alt.Chart(panel)
        .mark_line(interpolate="monotone", strokeWidth=2.4)
        .encode(
            x=alt.X(
                "month_start:T",
                title=None,
                scale=alt.Scale(domain=month_domain(start, end)),
                axis=alt.Axis(format="%m-%Y", tickCount=6, labelFontSize=10),
            ),
            y=alt.Y("value:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(labelFontSize=10, tickCount=4)),
            color=alt.Color(
                "serie:N", scale=alt.Scale(domain=names, range=[color, palette["strong_text"]]), legend=None
            ),
            strokeDash=alt.StrokeDash("serie:N", scale=alt.Scale(domain=names, range=[[1, 0], [5, 4]]), legend=None),
            tooltip=[
                alt.Tooltip("serie:N", title=say("Serie", "Series")),
                alt.Tooltip("month_start:T", title=say("Mes", "Month"), format="%m-%Y"),
                alt.Tooltip("value:Q", title=say("Índice (inicio = 100)", "Index (start = 100)"), format=",.1f"),
            ],
        )
        .properties(width="container", height=165)
    )
    return charts.apply_chart_style(chart, mode)


def season_chart(profile: pd.DataFrame, mode: str) -> Any:
    """«Temporada»: each calendar month against the average of its year (K4); the cheapest and the dearest stand out."""
    palette = charts.get_palette(mode)
    frame = profile.assign(
        mes=[month_name(month) for month in profile["month"]],
        tone=[say("más barato", "cheaper") if value < 0 else say("más caro", "dearer") for value in profile["change"]],
    )
    order = [month_name(month) for month in range(1, 13)]
    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("mes:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=10)),
            y=alt.Y(
                "change:Q",
                title=None,
                axis=alt.Axis(
                    labelFontSize=10, tickCount=4, labelExpr="datum.value > 0 ? '+' + datum.label : datum.label"
                ),
            ),
            color=alt.Color(
                "tone:N",
                scale=alt.Scale(
                    domain=[say("más barato", "cheaper"), say("más caro", "dearer")],
                    range=[palette["fall"], palette["rise"]],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("mes:N", title=say("Mes", "Month")),
                alt.Tooltip(
                    "change:Q", title=say("% frente al promedio del año", "% against the year's average"), format="+.1f"
                ),
                alt.Tooltip("years:N", title=say("Años", "Years")),
                alt.Tooltip("weeks:Q", title=say("Semanas", "Weeks")),
            ],
        )
        .properties(width="container", height=165)
    )
    return charts.apply_chart_style(chart, mode)


def alerts_chart(alerts: pd.DataFrame, start: tuple[int, int], end: tuple[int, int], mode: str) -> Any:
    """«Valores atípicos por mes»: the K6 alerts of each month, rises over falls, on the whole period's axis."""
    palette = charts.get_palette(mode)
    rises, falls = say("Subidas", "Rises"), say("Bajadas", "Falls")
    if alerts.empty:
        frame = pd.DataFrame(columns=["month_start", "kind", "alerts"])
    else:
        stamp = pd.to_datetime(alerts["week_start"])
        frame = (
            alerts.assign(
                month_start=stamp.dt.to_period("M").dt.to_timestamp(),
                kind=[rises if value > 0 else falls for value in alerts["variation"]],
            )
            .groupby(["month_start", "kind"], as_index=False)
            .size()
            .rename(columns={"size": "alerts"})
        )
    chart = (
        alt.Chart(frame)
        .mark_bar()
        .encode(
            x=alt.X(
                "month_start:T",
                timeUnit="yearmonth",
                title=None,
                scale=alt.Scale(domain=month_domain(start, end, counted=True)),
                axis=alt.Axis(format="%m-%Y", tickCount=6, labelFontSize=10),
            ),
            y=alt.Y("alerts:Q", title=None, stack="zero", axis=alt.Axis(labelFontSize=10, tickCount=4)),
            color=alt.Color(
                "kind:N", scale=alt.Scale(domain=[rises, falls], range=[palette["rise"], palette["fall"]]), legend=None
            ),
            tooltip=[
                alt.Tooltip("month_start:T", title=say("Mes", "Month"), format="%m-%Y"),
                alt.Tooltip("kind:N", title=say("Tipo", "Kind")),
                alt.Tooltip("alerts:Q", title=say("Alertas", "Alerts")),
            ],
        )
        .properties(width="container", height=165)
    )
    return charts.apply_chart_style(chart, mode)


def build_table(summaries: list[dict[str, Any]], chosen: str) -> str:
    """By family: the same five figures for each, the whole basket first and the family chosen lit."""
    head = [
        (say("Familia", "Family"), ""),
        (say("Cambio", "Change"), say("Cambio del índice en el período.", "Change of the index in the period.")),
        (
            say("Frente al IPC", "Against the CPI"),
            say("Puntos sobre o bajo el IPC de alimentos.", "Points over or under the food CPI."),
        ),
        (
            say("Brecha", "Gap"),
            say("Mediana de K1: consumidor sobre mayorista.", "Median of K1: consumer over wholesale."),
        ),
        (say("Alertas", "Alerts"), say("Alertas de precio (K6) del período.", "Price alerts (K6) of the period.")),
        (
            say("Mes más barato", "Cheapest month"),
            say("Mes con el menor K4 mediano.", "Month with the lowest median K4."),
        ),
    ]
    header = "".join(
        f'<th title="{html.escape(hint, quote=True)}">{html.escape(label)}</th>'
        if hint
        else f"<th>{html.escape(label)}</th>"
        for label, hint in head
    )
    body = []
    for item in summaries:
        lit = " class=\"ba-chosen\"" if item["family"] == chosen else ""
        gap = item["gap"]
        tone = (
            ""
            if gap is None
            else "rise"
            if gap > inflation_view.SAME_PACE_POINTS
            else "fall"
            if gap < -inflation_view.SAME_PACE_POINTS
            else ""
        )
        body.append(
            f"<tr{lit}><td>{html.escape(home_mockup.short_family(item['family']))}</td>"
            f"<td class=\"num\">{percent(item['change'])}</td><td class=\"num {tone}\">{points(gap)}</td>"
            f"<td class=\"num\">{'—' if item['margin'] is None else charts.format_percent(item['margin'])}</td>"
            f"<td class=\"num\">{charts.format_thousands(item['alerts'])}</td>"
            f"<td>{'—' if item['cheapest'] is None else month_name(item['cheapest'][0])}</td></tr>"
        )
    return f'<div class="ba-table"><table><thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def season_span(start: tuple[int, int], end: tuple[int, int]) -> tuple[str, str]:
    """The first and the last month whose weeks the season gathers, as month and year."""
    first = counted_months(start, end)[0]
    return month_label((first // 100, first % 100)), month_label(end)


def build_css(palette: dict[str, str]) -> str:
    ink, text, muted, card, border = (
        palette["strong_text"],
        palette["text"],
        charts.legible(palette["reference"], palette["background"]),
        palette["card"],
        palette["card_border"],
    )
    rise, fall, accent = palette["rise"], palette["fall"], palette["accent"]
    return f"""<style>
.ba-cards {{ display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:10px; margin:0 0 6px; }}
.st-key-ba_head {{ justify-content:space-between; gap:12px; flex-wrap:wrap; }}
.st-key-ba_filters [data-testid="stWidgetLabel"] p {{ font-size:12px !important; }}
.ba-card {{ display:flex; flex-direction:column; gap:2px; padding:10px 12px; border:1px solid {border}; border-radius:12px;
  background:{card}; cursor:help; outline:none; }}
.ba-card:hover, .ba-card:focus-visible {{ border-color:{accent}; }}
.ba-card-label {{ font-size:12px; line-height:1.25; color:{muted}; }}
.ba-card-value {{ font-size:24px; font-weight:700; color:{ink}; font-variant-numeric:tabular-nums; line-height:1.2; }}
.ba-card-value.rise {{ color:{rise}; }} .ba-card-value.fall {{ color:{fall}; }}
.ba-card-note {{ font-size:11.5px; color:{text}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ba-chart-title {{ margin:0 !important; font-size:13.5px !important; font-weight:600; color:{ink} !important; line-height:1.3 !important; }}
.ba-chart-title span {{ display:block; font-weight:400; color:{muted}; font-size:11.5px; }}
.ba-table table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
.ba-table th {{ text-align:left; font-weight:600; color:{muted}; padding:5px 8px; border-bottom:1px solid {border}; cursor:help; }}
.ba-table td {{ padding:3px 8px; border-bottom:1px solid {border}; color:{text}; }}
.ba-table td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.ba-table td.rise {{ color:{rise}; }} .ba-table td.fall {{ color:{fall}; }}
.ba-table tr.ba-chosen td {{ background:color-mix(in srgb, {accent} 10%, transparent); color:{ink}; font-weight:600; }}
@media (max-width:1100px) {{ .ba-cards {{ grid-template-columns:repeat(3, minmax(0, 1fr)); }} }}
</style>"""


# endregion
