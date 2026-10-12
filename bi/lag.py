"""K5: how many weeks the consumer price takes to follow the wholesale price.

It is descriptive (D-011): the lag with the highest correlation between the
weekly changes of both prices, not a proof that one price causes the other.
One series is one product key, unit, region and consumer channel, taken from
the pairs of the k1_margin query (same week, region and unit), see D-048.
"""
import math

import pandas as pd

# region Constants
MAXIMUM_LAG_WEEKS = 8
# K5 is shown only for series with at least 26 weeks with both prices.
MINIMUM_WEEKS = 26
DAYS_IN_A_WEEK = 7
# A correlation needs at least three pairs of changes to mean something.
MINIMUM_PAIRS = 3
# A correlation is told apart from zero when it exceeds 2 / sqrt(pairs), the usual
# approximation of 95 % confidence. Below it, the highest correlation is noise.
SIGNIFICANCE_FACTOR = 2
VARIATION_COLUMNS = {"wholesale_price": "wholesale_variation",
                     "consumer_price": "consumer_variation"}
# endregion


# region Lag
def add_weekly_variations(series_rows):
    """Add the change of each price against the week before, as a fraction.

    A change measured across a gap of several weeks is not a weekly change,
    so it stays empty, as in the K6 alerts.
    """
    rows = series_rows.assign(week_start=pd.to_datetime(series_rows["week_start"]))
    rows = rows.sort_values("week_start")
    is_consecutive_week = rows["week_start"].diff().dt.days == DAYS_IN_A_WEEK
    for price_column, variation_column in VARIATION_COLUMNS.items():
        variation = rows[price_column] / rows[price_column].shift(1) - 1
        rows[variation_column] = variation.where(is_consecutive_week)
    return rows


def has_enough_weeks(series_rows):
    """True when the series has the 26 weeks with both prices that K5 needs."""
    return series_rows["week_start"].nunique() >= MINIMUM_WEEKS


def pair_variations(rows, lag_weeks):
    """Consumer change of each week next to the wholesale change lag_weeks before."""
    consumer = rows.set_index("week_start")["consumer_variation"]
    wholesale = rows.set_index("week_start")["wholesale_variation"]
    # Moving the wholesale dates forward puts the change of week t - lag on week t.
    wholesale.index = wholesale.index + pd.Timedelta(weeks=lag_weeks)
    return pd.concat([consumer, wholesale], axis=1, join="inner").dropna()


def correlate_by_lag(series_rows):
    """Correlation of the two weekly changes for each lag from 0 to 8 weeks.

    Returns one row per lag: lag_weeks, correlation (empty with too few pairs)
    and pair_count.
    """
    rows = add_weekly_variations(series_rows)
    results = []
    for lag_weeks in range(MAXIMUM_LAG_WEEKS + 1):
        pairs = pair_variations(rows, lag_weeks)
        correlation = (pairs["consumer_variation"].corr(pairs["wholesale_variation"])
                       if len(pairs) >= MINIMUM_PAIRS else float("nan"))
        results.append({"lag_weeks": lag_weeks, "correlation": correlation,
                        "pair_count": len(pairs)})
    return pd.DataFrame(results)


def find_lag(correlations):
    """K5: (lag in weeks, correlation, pairs) of the highest correlation, or None."""
    correlations = correlations.dropna(subset=["correlation"])
    if correlations.empty:
        return None
    best = correlations.loc[correlations["correlation"].idxmax()]
    return int(best["lag_weeks"]), float(best["correlation"]), int(best["pair_count"])


def is_clear_relation(correlation, pair_count):
    """True when the correlation is told apart from zero (above 2 / sqrt(pairs))."""
    return correlation > SIGNIFICANCE_FACTOR / math.sqrt(pair_count)
# endregion
