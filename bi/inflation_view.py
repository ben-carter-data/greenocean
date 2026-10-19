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


def draw_family_chart(rows, mode, real=False, height=360):
    """Each family against the food IPC since January 2022. Real: the IPC is the flat 100
    line and a family above it rose more than the food basket."""
    palette = charts.get_palette(mode)
    value = "real" if real else "index"
    domain = [family for family in FAMILY_COLORS if family in set(rows["product_group"])] + [IPC_NAME]
    colors = [FAMILY_COLORS[family] for family in domain[:-1]] + [palette["strong_text"]]
    x = alt.X("month_start:T", title=None, axis=alt.Axis(format="%b %Y", tickCount=10, labelPadding=6))
    y = alt.Y(f"{value}:Q", title="Índice (enero 2022 = 100)" if not real else "Frente a la inflación (100 = igual)",
              scale=alt.Scale(zero=False))
    color = alt.Color("product_group:N", scale=alt.Scale(domain=domain, range=colors),
                      legend=alt.Legend(title=None, orient="bottom", columns=4, symbolStrokeWidth=3))
    tooltip = [alt.Tooltip("product_group:N", title="Familia"),
               alt.Tooltip("month_start:T", title="Mes", format="%m-%Y"),
               alt.Tooltip(f"{value}:Q", title="Índice", format=",.1f")]
    families = alt.Chart(rows[rows["product_group"] != IPC_NAME]).mark_line(
        strokeWidth=2, interpolate="monotone", opacity=.9).encode(x=x, y=y, color=color, tooltip=tooltip)
    reference = alt.Chart(rows[rows["product_group"] == IPC_NAME]).mark_line(
        strokeWidth=3.4, strokeDash=[7, 4], interpolate="monotone").encode(x=x, y=y, color=color, tooltip=tooltip)
    return charts.apply_chart_style(alt.layer(families, reference).properties(height=height), mode)


def draw_product_chart(rows, mode, real=False, height=280):
    """One product, its whole weekly series, one line per channel: today's pesos or
    pesos of the last IPC month."""
    value = "real_price" if real else "national_price"
    domain = [channel for channel in charts.CONTEXT_CHANNELS if channel in set(rows["channel"])]
    color = alt.Color("channel:N", scale=alt.Scale(domain=domain, range=[charts.CONTEXT_CHANNELS[c] for c in domain]),
                      legend=alt.Legend(title=None, orient="top"))
    chart = alt.Chart(rows).mark_line(strokeWidth=2, interpolate="monotone").encode(
        x=alt.X("week_start:T", title=None, axis=alt.Axis(format="%b %Y", tickCount=10)),
        y=alt.Y(f"{value}:Q", title="$ por unidad", scale=alt.Scale(zero=False),
                axis=alt.Axis(format=charts.MONEY_AXIS_FORMAT)),
        color=color,
        tooltip=[alt.Tooltip("week_start:T", title="Semana", format="%d-%m-%Y"),
                 alt.Tooltip("channel:N", title="Canal"),
                 alt.Tooltip(f"{value}:Q", title="Precio", format=",.0f")])
    return charts.apply_chart_style(chart.properties(height=height), mode)
