"""Contexto del precio: is this week's price normal? (D-094)

Pure pandas functions, without Streamlit, so each rule can be tested on its own.
«Habitual» means the P25–P75 range of the same ISO week in previous years: the
current year never enters its own reference, and fewer than two previous years
is not enough history to classify a price.
"""
import math

import pandas as pd

MINIMUM_YEARS = 2
STATES = {"sobre": "sobre lo habitual", "dentro": "dentro de lo habitual",
          "bajo": "bajo lo habitual", "sin_historia": "sin historia suficiente"}
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]


def iso_week(week_start):
    """(ISO year, ISO week) of the Monday that starts a week."""
    calendar = pd.Timestamp(week_start).isocalendar()
    return calendar.year, calendar.week


def rango_habitual(rows, week_start):
    """(P25, P75, number of years) of the same ISO week in previous years, or None.

    rows: one price series (week_start, national_price). Only years before the ISO
    year of week_start count; a missing week in a year simply leaves that year out.
    """
    year, week = iso_week(week_start)
    if rows.empty:
        return None
    calendar = pd.to_datetime(rows["week_start"]).dt.isocalendar()
    same_week = rows[(calendar["week"].to_numpy() == week) & (calendar["year"].to_numpy() < year)]
    prices = same_week["national_price"].dropna()
    if prices.size < MINIMUM_YEARS:
        return None
    return float(prices.quantile(.25)), float(prices.quantile(.75)), int(prices.size)


def estado_precio(price, usual_range):
    """«sobre», «dentro», «bajo» or «sin_historia» for one price and its usual range."""
    if usual_range is None or price is None or not math.isfinite(float(price)):
        return "sin_historia"
    low, high = usual_range[0], usual_range[1]
    if price > high:
        return "sobre"
    if price < low:
        return "bajo"
    return "dentro"


def weekly_context(rows, last_week, weeks=52):
    """The last `weeks` weeks of one series with its usual band, one row per week.

    Weeks without a price keep a row with an empty price: the chart shows a gap,
    never an interpolated value.
    """
    last_week = pd.Timestamp(last_week)
    calendar = pd.date_range(end=last_week, periods=weeks, freq="7D")
    prices = rows.assign(week_start=pd.to_datetime(rows["week_start"])).set_index("week_start")["national_price"]
    records = []
    for week in calendar:
        usual = rango_habitual(rows, week)
        price = prices.get(week)
        price = float(price) if price is not None and pd.notna(price) else None
        records.append({"week_start": week, "price": price,
                        "p25": usual[0] if usual else None, "p75": usual[1] if usual else None,
                        "state": estado_precio(price, usual) if price is not None else None})
    return pd.DataFrame(records)


def brecha(feria, supermercado):
    """Weekly gap in %: (supermarket / street market − 1) × 100, only where both exist.

    feria, supermercado: series of one product (week_start, national_price).
    """
    joined = (feria[["week_start", "national_price"]]
              .merge(supermercado[["week_start", "national_price"]], on="week_start",
                     suffixes=("_feria", "_super")))
    joined = joined[(joined["national_price_feria"] > 0) & joined["national_price_super"].notna()]
    joined = joined.assign(week_start=pd.to_datetime(joined["week_start"]))
    joined["gap"] = (joined["national_price_super"] / joined["national_price_feria"] - 1) * 100
    return joined[["week_start", "gap"]].sort_values("week_start").reset_index(drop=True)


def brecha_habitual(gaps, week_start):
    """Median gap of the same calendar month in previous years, or None (< 2 years)."""
    week_start = pd.Timestamp(week_start)
    year = week_start.isocalendar().year
    month = (week_start + pd.Timedelta(days=3)).month
    moments = gaps["week_start"] + pd.Timedelta(days=3)
    years = gaps["week_start"].dt.isocalendar()["year"].to_numpy()
    previous = gaps[(moments.dt.month.to_numpy() == month) & (years < year)]
    if previous.empty or len(set(previous["week_start"].dt.isocalendar()["year"])) < MINIMUM_YEARS:
        return None
    return float(previous["gap"].median())


def patron_estacional(rows, current_year=None):
    """{month: index} with 100 = average of the year, from the seasonal index (K4).

    rows: K4 rows of one channel (week_start, price_year, seasonal_index). Each month
    of each year is averaged first, then the years: a year with more weeks does not
    weigh more. The current (incomplete) year stays out when previous years exist.
    """
    if rows.empty:
        return {}
    rows = rows.assign(year=rows["price_year"].astype(int),
                       month=(pd.to_datetime(rows["week_start"]) + pd.Timedelta(days=3)).dt.month)
    if current_year is not None and (rows["year"] < current_year).any():
        rows = rows[rows["year"] < current_year]
    monthly = rows.groupby(["year", "month"])["seasonal_index"].mean().groupby("month").mean()
    return {int(month): float(value) * 100 for month, value in monthly.items()}


def proximos_meses(pattern, month, count=2):
    """[(month, change in %)] from the current month to each of the next ones."""
    if month not in pattern:
        return []
    result = []
    for step in range(1, count + 1):
        following = (month - 1 + step) % 12 + 1
        if following in pattern and pattern[month]:
            result.append((following, (pattern[following] / pattern[month] - 1) * 100))
    return result


def describe_gap_comparison(current, usual, tolerance=2.0):
    """«mayor», «menor» or «similar»: this week's gap against the usual one."""
    if current is None or usual is None:
        return None
    if abs(current) - abs(usual) > tolerance:
        return "mayor"
    if abs(usual) - abs(current) > tolerance:
        return "menor"
    return "similar"


def answer_sentence(product, month, states, gap_word):
    """The sentence under the title, built only from computed facts.

    states: {channel label: state}; a channel without data is left out.
    """
    parts = []
    for index, (channel, state) in enumerate(states.items()):
        phrase = STATES[state] if state != "sin_historia" else "sin historia suficiente para compararlo"
        if index == 0:
            # «el precio de» avoids guessing the gender of each product name.
            parts.append(f"Esta semana, el precio de {product} en {channel.lower()} está {phrase}"
                         + (f" para {MONTHS[month - 1]}" if state != "sin_historia" else ""))
        else:
            parts.append(f"en {channel.lower()} está {phrase}")
    if not parts:
        return f"No hay precios de feria ni de supermercado para {product} esta semana."
    sentence = "; ".join(parts) + "."
    if gap_word:
        sentence += f" La diferencia entre ambos canales es {gap_word} que de costumbre."
    return sentence
