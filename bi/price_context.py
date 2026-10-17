"""Contexto del precio: is this week's price normal? (D-094, D-098)

Pure pandas functions, without Streamlit, so each rule can be tested on its own.
«Habitual» means the P25–P75 range of a ±1 ISO-week window (the target week and
its immediate neighbours, up to three weeks) in previous years: the current year
never enters its own reference, and fewer than two previous years with a price
in that window is not enough history to classify a price (D-098).
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


def read_calendar(rows):
    """(ISO year, ISO week, month) columns: from dim_date when joined, computed otherwise."""
    if {"iso_year", "iso_week", "month"} <= set(rows.columns):
        return rows["iso_year"].to_numpy(), rows["iso_week"].to_numpy(), rows["month"].to_numpy()
    days = pd.to_datetime(rows["week_start"])
    calendar = days.dt.isocalendar()
    return calendar["year"].to_numpy(), calendar["week"].to_numpy(), days.dt.month.to_numpy()


def nearby_mask(weeks, years, week, year):
    """Rows within ±1 ISO week of (year, week), strictly before it (D-098).

    At the edges of the calendar (week 1, or a year's last week) the window has
    only two weeks instead of three: a neighbouring week number that never
    exists (0, or 53/54) simply matches nothing, rather than guessing another
    year's week count.
    """
    return (weeks >= week - 1) & (weeks <= week + 1) & (years < year)


def rango_habitual(rows, week_start, iso=None):
    """(P25, P75, number of previous years) of a ±1 ISO-week window, or None.

    rows: one price series (week_start, national_price, and the dim_date columns when
    available). iso: (ISO year, ISO week) of week_start from dim_date. Only years before
    that ISO year count; a missing week in a year simply leaves that year out.
    """
    year, week = iso or iso_week(week_start)
    if rows.empty:
        return None
    years, weeks, _ = read_calendar(rows)
    nearby = nearby_mask(weeks, years, week, year)
    prices = rows.loc[nearby, "national_price"].dropna()
    distinct_years = len(set(years[nearby]))
    if distinct_years < MINIMUM_YEARS:
        return None
    return float(prices.quantile(.25)), float(prices.quantile(.75)), distinct_years


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


def weekly_context(rows, last_week, weeks=52, dates=None):
    """The last `weeks` weeks of one series with its usual band, one row per week.

    Weeks without a price keep a row with an empty price: the chart shows a gap,
    never an interpolated value. dates: dim_date indexed by week_start, if any.
    """
    last_week = pd.Timestamp(last_week)
    calendar = pd.date_range(end=last_week, periods=weeks, freq="7D")
    def iso(week):
        if dates is not None and week in dates.index:
            return int(dates.at[week, "iso_year"]), int(dates.at[week, "iso_week"])
        return None
    prices = rows.assign(week_start=pd.to_datetime(rows["week_start"])).set_index("week_start")["national_price"]
    records = []
    for week in calendar:
        usual = rango_habitual(rows, week, iso(week))
        price = prices.get(week)
        price = float(price) if price is not None and pd.notna(price) else None
        records.append({"week_start": week, "price": price,
                        "p25": usual[0] if usual else None, "p75": usual[1] if usual else None,
                        "state": estado_precio(price, usual) if price is not None else None})
    return pd.DataFrame(records)


def brecha(feria, supermercado):
    """Weekly gap in %: (supermarket / street market − 1) × 100, only where both exist.

    feria, supermercado: series of one product (week_start, national_price, and the
    dim_date columns when available, which the result keeps).
    """
    calendar = [column for column in ("iso_year", "iso_week", "month") if column in feria]
    joined = (feria[["week_start", "national_price"] + calendar]
              .merge(supermercado[["week_start", "national_price"]], on="week_start",
                     suffixes=("_feria", "_super")))
    joined = joined[(joined["national_price_feria"] > 0) & joined["national_price_super"].notna()]
    joined = joined.assign(week_start=pd.to_datetime(joined["week_start"]))
    joined["gap"] = (joined["national_price_super"] / joined["national_price_feria"] - 1) * 100
    return joined[["week_start", "gap"] + calendar].sort_values("week_start").reset_index(drop=True)


def brecha_rango_habitual(gaps, week_start, iso=None):
    """(P25, P75, number of previous years) of the gap, over the same ±1-week window.

    Mirrors rango_habitual, so «is this week's gap usual?» follows the identical
    P25–P75 rule as a price, instead of a separate tolerance (D-098).
    """
    year, week = iso or iso_week(week_start)
    if gaps.empty:
        return None
    years, weeks, _ = read_calendar(gaps)
    nearby = nearby_mask(weeks, years, week, year)
    values = gaps.loc[nearby, "gap"].dropna()
    distinct_years = len(set(years[nearby]))
    if distinct_years < MINIMUM_YEARS:
        return None
    return float(values.quantile(.25)), float(values.quantile(.75)), distinct_years


def patron_estacional(rows, current_year=None):
    """{month: index} with 100 = average of the year, from the seasonal index (K4).

    rows: K4 rows of one channel (week_start, price_year, seasonal_index). Each month
    of each year is averaged first, then the years: a year with more weeks does not
    weigh more. The current (incomplete) year stays out when previous years exist.
    """
    if rows.empty:
        return {}
    # The month comes from dim_date when joined: the month of week_start.
    rows = rows.assign(year=rows["price_year"].astype(int),
                       month=rows["month"] if "month" in rows else pd.to_datetime(rows["week_start"]).dt.month)
    if current_year is not None and (rows["year"] < current_year).any():
        rows = rows[rows["year"] < current_year]
    monthly = rows.groupby(["year", "month"])["seasonal_index"].mean().groupby("month").mean()
    return {int(month): float(value) * 100 for month, value in monthly.items()}


def proximos_meses(pattern, month, count=3):
    """[(month, change in %)] from the current month to each of the next ones."""
    if month not in pattern:
        return []
    result = []
    for step in range(1, count + 1):
        following = (month - 1 + step) % 12 + 1
        if following in pattern and pattern[month]:
            result.append((following, (pattern[following] / pattern[month] - 1) * 100))
    return result


def answer_sentence(product, month, states, gap_word, wrap=None):
    """The sentence under the title, built only from computed facts.

    states: {channel label: state}; a channel without data is left out. gap_word
    is «mayor»/«menor» only when this week's gap sits outside its own P25–P75
    window, or None to leave the gap out of the sentence entirely (D-098). wrap,
    when given, receives (channel, phrase) and returns the phrase to use — the
    caller's hook to colour each channel's state, e.g. with inline HTML.
    """
    wrap = wrap or (lambda channel, phrase: phrase)
    parts = []
    for index, (channel, state) in enumerate(states.items()):
        if state == "sin_historia":
            phrase = "sin historia suficiente para compararlo"
        else:
            phrase = wrap(channel, STATES[state])
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
