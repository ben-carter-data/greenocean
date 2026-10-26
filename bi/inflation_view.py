"""Precios e inflación (D-163): which food families rose more than the food IPC.

The big picture of the page that used to be «Contexto del precio». For every family,
one monthly index (January 2022 = 100) of the consumer prices ODEPA publishes, set
against the food IPC of the INE on the same base:
- a series (product key, consumer channel, unit) counts only when it has a price in the
  base month and in the last month the INE has published, so the index compares the same
  products from start to end, never a changing mix;
- each month, the series' index is its monthly average price over its base price, and a
  family's index is the median of its series;
- «sin inflación» divides each index by the IPC: 100 means «rose exactly like the food
  basket of the INE».
The IPC is itself computed from food prices, so a family moving with it is not proof
that inflation moved it: the comparison says «more or less than the food basket».
"""
import math

import altair as alt
import pandas as pd

from bi import charts

BASE_YEAR, BASE_MONTH = 2022, 1
IPC_NAME = "IPC alimentos (INE)"
# A family within ±2 points of the IPC rose «al ritmo de la inflación».
SAME_PACE_POINTS = 2.0
FAMILY_COLORS = {
    "Hortalizas": "#16a34a", "Frutas": "#e11d48", "Carne bovina": "#b45309",
    "Carne de Cerdo - Ave - Cordero": "#f97316", "Lácteos - Huevos - Margarinas": "#0ea5e9",
    "Pan": "#ca8a04", "Abarrotes y otros": "#8b5cf6",
}
SERIES_SQL = """
WITH national AS (
    SELECT wp.week_start, p.product_group, wp.product_id, wp.channel_id, wp.normalized_unit,
           AVG(wp.price) AS price
    FROM weekly_price wp
    JOIN dim_product p USING (product_id)
    JOIN dim_channel ch USING (channel_id)
    WHERE wp.flag IS NULL AND ch.source = 'consumer'
    GROUP BY wp.week_start, p.product_group, wp.product_id, wp.channel_id, wp.normalized_unit
)
SELECT product_group, product_id, channel_id, normalized_unit,
       year(CAST(week_start AS DATE)) AS year, month(CAST(week_start AS DATE)) AS month,
       AVG(price) AS price
FROM national
GROUP BY product_group, product_id, channel_id, normalized_unit, year, month
"""


def build_family_index(series, ipc):
    """(index, last) where index has product_group, month_start, index, real — one row per
    family and month from the base month to the last IPC month, plus the IPC itself
    (product_group = IPC_NAME) — and last is (year, month) of that last month."""
    ipc = ipc.sort_values(["year", "month"])
    last = tuple(int(value) for value in ipc.iloc[-1][["year", "month"]])
    series = series.assign(key=series["product_id"].astype(str) + "|" + series["channel_id"].astype(str)
                           + "|" + series["normalized_unit"].astype(str))
    in_window = (series["year"] * 100 + series["month"]).between(BASE_YEAR * 100 + BASE_MONTH,
                                                                   last[0] * 100 + last[1])
    series = series[in_window]
    base = series[(series["year"] == BASE_YEAR) & (series["month"] == BASE_MONTH)].set_index("key")["price"]
    ends = set(series.loc[(series["year"] == last[0]) & (series["month"] == last[1]), "key"])
    kept = series[series["key"].isin(set(base.index) & ends)].copy()
    kept["index"] = kept["price"] / kept["key"].map(base) * 100
    families = kept.groupby(["product_group", "year", "month"], as_index=False).agg(
        index=("index", "median"), series=("key", "nunique"))
    ipc = ipc[(ipc["year"] * 100 + ipc["month"]) >= BASE_YEAR * 100 + BASE_MONTH]
    base_ipc = float(ipc.loc[(ipc["year"] == BASE_YEAR) & (ipc["month"] == BASE_MONTH), "food_index"].iloc[0])
    reference = ipc.assign(product_group=IPC_NAME, index=ipc["food_index"] / base_ipc * 100, series=None)
    rows = pd.concat([families, reference[["product_group", "year", "month", "index", "series"]]],
                     ignore_index=True)
    rows["month_start"] = pd.to_datetime(dict(year=rows["year"], month=rows["month"], day=1))
    deflator = reference.set_index(["year", "month"])["index"]
    rows["real"] = rows["index"] / [deflator[(year, month)] for year, month in zip(rows["year"], rows["month"])] * 100
    return rows.sort_values(["product_group", "month_start"]).reset_index(drop=True), last


def change(rows, family, start, end):
    """Change in % of one family's index between two (year, month), or None."""
    values = rows[rows["product_group"] == family].set_index(["year", "month"])["index"]
    if start not in values.index or end not in values.index:
        return None
    return (values[end] / values[start] - 1) * 100


def summarize_families(rows, last):
    """One row per family: change since the base and in 12 months, beside the IPC's, and
    whether it rose more, as much as, or less than the food basket."""
    year_ago = (last[0] - 1, last[1])
    base = (BASE_YEAR, BASE_MONTH)
    ipc_total, ipc_year = change(rows, IPC_NAME, base, last), change(rows, IPC_NAME, year_ago, last)
    result = []
    for family in sorted(set(rows["product_group"]) - {IPC_NAME}):
        total, yearly = change(rows, family, base, last), change(rows, family, year_ago, last)
        gap = None if total is None else total - ipc_total
        verdict = ("sin datos" if gap is None else "más que la inflación" if gap > SAME_PACE_POINTS
                   else "menos que la inflación" if gap < -SAME_PACE_POINTS else "al ritmo de la inflación")
        series = rows.loc[rows["product_group"] == family, "series"].max()
        result.append({"family": family, "total": total, "yearly": yearly, "gap": gap,
                       "verdict": verdict, "series": int(series) if pd.notna(series) else 0})
    summary = pd.DataFrame(result).sort_values("gap", ascending=False).reset_index(drop=True)
    return summary, ipc_total, ipc_year


def family_domain(rows, real=False, step=10):
    """The shared y range of the family cards: every family and the IPC fit in it, so
    the cards compare at a glance; rounded outward to the nearest step."""
    values = rows["real" if real else "index"].dropna()
    if values.empty:
        return [90, 110]
    low = math.floor(values.min() / step) * step
    high = math.ceil(values.max() / step) * step
    return [low, high if high > low else low + step]


def draw_family_card(rows, family, mode, real=False, domain=None, height=186):
    """One family against the food IPC (dashed), for a card of the grid (D-174): the
    chart fills its card and shares the y domain with the other cards. Real: the IPC
    is the flat 100 line and a family above it rose more than the basket."""
    return charts.apply_chart_style(family_lines(rows, family, mode, real, domain).properties(
        width="container", height=height), mode)


def family_lines(rows, family, mode, real=False, domain=None):
    """The two lines of a family card, without style or size, so the enlarged chart can add its layers."""
    palette = charts.get_palette(mode)
    value = "real" if real else "index"
    panel = rows[rows["product_group"].isin([family, IPC_NAME])]
    names = [family, IPC_NAME] if family != IPC_NAME else [IPC_NAME]
    colors = [FAMILY_COLORS.get(family, "#94a3b8"), palette["strong_text"]][-len(names):]
    dashes = [[1, 0], [5, 4]][-len(names):]
    scale = alt.Scale(zero=False, domain=domain) if domain else alt.Scale(zero=False)
    chart = alt.Chart(panel).mark_line(interpolate="monotone", strokeWidth=2.2).encode(
        x=alt.X("month_start:T", title=None, axis=alt.Axis(format="%Y", tickCount=5, labelPadding=4)),
        y=alt.Y(f"{value}:Q", title=None, scale=scale, axis=alt.Axis(labelFontSize=10, tickCount=4)),
        color=alt.Color("product_group:N", scale=alt.Scale(domain=names, range=colors), legend=None),
        strokeDash=alt.StrokeDash("product_group:N", scale=alt.Scale(domain=names, range=dashes), legend=None),
        opacity=alt.condition(alt.datum.product_group == IPC_NAME, alt.value(.7), alt.value(1)),
        tooltip=[alt.Tooltip("product_group:N", title="Serie"),
                 alt.Tooltip("month_start:T", title="Mes", format="%m-%Y"),
                 alt.Tooltip(f"{value}:Q", title="Índice", format=",.1f")])
    return chart



def draw_family_focus(rows, family, mode, real=False, domain=None, height=420):
    """The enlarged family (D-294): the card's lines plus what a large chart owes its reader. The last value of each
    line at its end, the family's peak marked with its value (the «Máximo» of the reading beside it) and, under the
    cursor, a rule with the month, both values and their difference in points. Every number is a value of the drawn
    series."""
    palette = charts.get_palette(mode)
    value = "real" if real else "index"
    lines = family_lines(rows, family, mode, real, domain).encode(
        x=alt.X("month_start:T", title=None, axis=alt.Axis(  # D-316: the years under the chart, small and soft, in the gridline's place
            format="%Y", tickCount=5, labelPadding=8, labelFontSize=11, labelColor=palette["reference"], labelFlush=False)))
    panel = rows[rows["product_group"].isin([family, IPC_NAME])].sort_values("month_start")
    names = [family, IPC_NAME] if family != IPC_NAME else [IPC_NAME]
    colors = [FAMILY_COLORS.get(family, "#94a3b8"), palette["strong_text"]][-len(names):]
    color = alt.Color("product_group:N", scale=alt.Scale(domain=names, range=colors), legend=None)
    x = alt.X("month_start:T", title=None)
    y = alt.Y(f"{value}:Q", title=None)
    ends = panel.groupby("product_group", as_index=False).tail(1)
    end_labels = alt.Chart(ends).mark_text(align="left", dx=7, fontSize=12, fontWeight=600).encode(
        x=x, y=y, color=color, text=alt.Text(f"{value}:Q", format=",.1f"))
    layers = [lines, end_labels]
    series = panel[panel["product_group"] == family]
    if family != IPC_NAME and not series.empty:
        peak = series.loc[[series[value].idxmax()]]
        if peak.index[0] != series.index[-1]:  # a peak in the last month already carries the end label
            layers += [alt.Chart(peak).mark_point(filled=True, size=46, color=colors[0]).encode(x=x, y=y),
                       alt.Chart(peak).mark_text(dy=-11, fontSize=11.5, fontWeight=600, color=colors[0]).encode(
                           x=x, y=y, text=alt.Text(f"{value}:Q", format=",.1f"))]
    # One row per month with both values, for the rule under the cursor.
    wide = panel.pivot_table(index="month_start", columns="product_group", values=value).reset_index()
    tooltip = [alt.Tooltip("month_start:T", title="Mes", format="%B %Y")]
    if family != IPC_NAME:
        wide = wide.rename(columns={family: "family", IPC_NAME: "ipc"})
        wide["gap"] = wide["family"] - wide["ipc"]
        tooltip += [alt.Tooltip("family:Q", title=family, format=",.1f"),
                    alt.Tooltip("ipc:Q", title=IPC_NAME, format=",.1f"),
                    alt.Tooltip("gap:Q", title="Diferencia en puntos", format="+,.1f")]
    else:
        wide = wide.rename(columns={IPC_NAME: "ipc"})
        tooltip += [alt.Tooltip("ipc:Q", title=IPC_NAME, format=",.1f")]
    hover = alt.selection_point(name="month", fields=["month_start"], nearest=True, on="pointerover",
                                clear="pointerout", empty=False)
    rule = alt.Chart(wide).mark_rule(color=palette["reference"], strokeWidth=1).encode(
        x=x, opacity=alt.condition(hover, alt.value(.75), alt.value(0)), tooltip=tooltip).add_params(hover)
    dots = alt.Chart(panel).mark_point(filled=True, size=40).encode(
        x=x, y=y, color=color, opacity=alt.condition(hover, alt.value(1), alt.value(0)))
    layers += [rule, dots]
    chart = alt.layer(*layers).properties(width="container", height=height, padding={"right": 44, "bottom": 18})
    return charts.apply_chart_style(chart, mode)

def month_name(year, month):
    return f"{charts.CHILE_LOCALE['time']['months'][month - 1]} {year}"


def points(value):
    return f"{abs(value):.1f}".replace(".", ",") + (" punto" if round(abs(value), 1) == 1 else " puntos")


def family_insights(rows, summary, family, last, real=False):
    """The reading of one family when its card is enlarged (D-267): [(label, sentence)], every number recomputed
    from the same monthly index the chart draws, so the text always matches the line. With real, the peak and the
    biggest monthly move are read on the line without inflation, the one the chart then draws."""
    base, year_ago = (BASE_YEAR, BASE_MONTH), (last[0] - 1, last[1])
    ipc_total, ipc_year = change(rows, IPC_NAME, base, last), change(rows, IPC_NAME, year_ago, last)
    series = rows[rows["product_group"] == family].sort_values("month_start")
    if series.empty or ipc_total is None:
        return []
    percent = charts.format_signed_percent
    since = f"Desde {month_name(*base)}"
    line = "real" if real else "index"
    note = " (sin inflación)" if real else ""
    monthly = series.assign(step=series[line].pct_change() * 100).dropna(subset=["step"])
    jump = monthly.loc[monthly["step"].abs().idxmax()] if not monthly.empty else None
    jump_text = (None if jump is None else
                 (f"Mayor movimiento mensual{note}", f"{percent(jump['step'])} en {month_name(int(jump['year']), int(jump['month']))}."))
    if family == IPC_NAME and real:
        jump_text = None  # without inflation the IPC is the flat 100 line: it has no move of its own
    if family == IPC_NAME:
        counts = summary["verdict"].value_counts()
        insights = [(since, f"La canasta de alimentos del INE subió {percent(ipc_total)}."),
                    ("Últimos 12 meses", f"{percent(ipc_year)}."),
                    ("Frente a las familias", f"{counts.get('más que la inflación', 0)} subieron más que ella, "
                                              f"{counts.get('menos que la inflación', 0)} menos y "
                                              f"{counts.get('al ritmo de la inflación', 0)} a su ritmo "
                                              f"(± {points(SAME_PACE_POINTS)}).")]
        return insights + ([jump_text] if jump_text else [])
    total, yearly = change(rows, family, base, last), change(rows, family, year_ago, last)
    gap = total - ipc_total
    verdict = ("más que" if gap > SAME_PACE_POINTS else "menos que" if gap < -SAME_PACE_POINTS else "al ritmo de")
    # The difference of the two rounded rises, so it adds up with the figures the cards show.
    shown_gap = round(total, 1) - round(ipc_total, 1)
    insights = [(since, f"Subió {percent(total)}: {points(shown_gap)} {'más' if shown_gap >= 0 else 'menos'} que el IPC de "
                        f"alimentos ({percent(ipc_total)}). Subió {verdict} la inflación.")]
    if yearly is not None and ipc_year is not None:
        pace = "más rápido" if yearly > ipc_year else "más lento" if yearly < ipc_year else "igual"
        insights.append(("Últimos 12 meses", f"{percent(yearly)} frente a {percent(ipc_year)} del IPC: hoy sube {pace} "
                                             "que la canasta." if pace != "igual" else
                                             f"{percent(yearly)}, igual que el IPC."))
    peak = series.loc[series[line].idxmax()]
    latest = series.iloc[-1]
    peak_month = month_name(int(peak["year"]), int(peak["month"]))
    if (int(peak["year"]), int(peak["month"])) == last:
        insights.append((f"Máximo{note}", f"El último mes, {peak_month}, es su punto más alto (índice "
                                          f"{peak[line]:.1f}".replace(".", ",") + ")."))
    else:
        below = (latest[line] / peak[line] - 1) * 100
        insights.append((f"Máximo{note}", f"Índice {peak[line]:.1f}".replace(".", ",") + f" en {peak_month}; hoy está "
                                   + f"{abs(below):.1f} % bajo ese punto.".replace(".", ",", 1)))
    if jump_text:
        insights.append(jump_text)
    real = (latest["real"] - 100)
    insights.append(("Sin inflación", f"Descontado el IPC, vale {percent(real)} frente a {month_name(*base)}."))
    count = int(series["series"].max()) if series["series"].notna().any() else 0
    insights.append(("Base del cálculo", f"{count} series de consumidor con precio en {month_name(*base)} y en "
                                         f"{month_name(*last)}; cada mes, la mediana de sus índices."))
    return insights
