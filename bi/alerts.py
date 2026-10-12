"""K6: products whose weekly price change is outside their usual range."""
import pandas as pd

# region Constants
# One price series per product key, channel and unit (national weekly price).
SERIES_COLUMNS = ["product_group", "product", "variety", "quality", "channel",
                  "normalized_unit"]
# K6: the usual range comes from the 12 weekly variations before the week judged.
ALERT_WINDOW_WEEKS = 12
ALERT_DEVIATIONS = 2
DAYS_IN_A_WEEK = 7
# endregion


# region Alerts
def add_weekly_variation(prices):
    """Add the price change of each week against the week before, as a fraction."""
    prices = prices.sort_values(SERIES_COLUMNS + ["week_start"]).copy()
    prices["week_start"] = pd.to_datetime(prices["week_start"])
    series = prices.groupby(SERIES_COLUMNS)
    previous_price = series["national_price"].shift(1)
    previous_week = series["week_start"].shift(1)
    days_since_previous_week = (prices["week_start"] - previous_week).dt.days
    # A change measured across a gap of several weeks is not a weekly change.
    is_consecutive_week = days_since_previous_week == DAYS_IN_A_WEEK
    variation = prices["national_price"] / previous_price - 1
    prices["variation"] = variation.where(is_consecutive_week)
    return prices


def calculate_previous_average(variation):
    """Average of the 12 variations before each week (the week itself excluded)."""
    return variation.shift(1).rolling(ALERT_WINDOW_WEEKS).mean()


def calculate_previous_deviation(variation):
    """Standard deviation of the 12 variations before each week."""
    return variation.shift(1).rolling(ALERT_WINDOW_WEEKS).std()


def add_usual_range(prices):
    """Add each week's variation and the average and deviation of the 12 before it.

    A series needs 12 previous variations without gaps; otherwise both stay empty.
    """
    prices = add_weekly_variation(prices)
    variation_by_series = prices.groupby(SERIES_COLUMNS)["variation"]
    prices["usual_variation"] = variation_by_series.transform(calculate_previous_average)
    prices["variation_deviation"] = variation_by_series.transform(
        calculate_previous_deviation)
    return prices


def find_price_alerts(prices):
    """K6: rows whose weekly variation is outside average +/- 2 standard deviations."""
    prices = add_usual_range(prices)
    distance = (prices["variation"] - prices["usual_variation"]).abs()
    is_alert = distance > ALERT_DEVIATIONS * prices["variation_deviation"]
    return prices[is_alert]
# endregion
