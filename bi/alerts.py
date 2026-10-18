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
    """Add the price change of each week against the week before, as a fraction.

    D-144: when the rows carry the price of the regions present in both weeks
    (same_region_price, same_region_previous_price), the change is theirs, so a
    region that starts or stops reporting is not read as a price movement.
    """
    prices = prices.sort_values(SERIES_COLUMNS + ["week_start"]).copy()
    prices["week_start"] = pd.to_datetime(prices["week_start"])
    if "same_region_previous_price" in prices.columns:
        previous = prices["same_region_previous_price"]
        prices["variation"] = (prices["same_region_price"] / previous - 1).where(previous > 0)
        return prices
    series = prices.groupby(SERIES_COLUMNS)
    previous_price = series["national_price"].shift(1)
    previous_week = series["week_start"].shift(1)
    days_since_previous_week = (prices["week_start"] - previous_week).dt.days
    # A change measured across a gap of several weeks is not a weekly change.
    is_consecutive_week = days_since_previous_week == DAYS_IN_A_WEEK
    variation = prices["national_price"] / previous_price - 1
    prices["variation"] = variation.where(is_consecutive_week)
    return prices


def add_usual_range(prices):
    """Add each week's variation and the average and deviation of the 12 before it.

    A series needs 12 previous variations without gaps; otherwise both stay empty.
    The window runs over the whole column at once, which is much faster than one
    series at a time; a window that would reach into the previous series is
    discarded, because a row needs 12 earlier rows of its own series.
    """
    prices = add_weekly_variation(prices)
    series = prices.groupby(SERIES_COLUMNS)
    # The week judged is left out of its own usual range.
    window = series["variation"].shift(1).rolling(ALERT_WINDOW_WEEKS)
    has_full_window = series.cumcount() >= ALERT_WINDOW_WEEKS
    prices["usual_variation"] = window.mean().where(has_full_window)
    prices["variation_deviation"] = window.std().where(has_full_window)
    return prices


def find_price_alerts(prices):
    """K6: rows whose weekly variation is outside average +/- 2 standard deviations."""
    prices = add_usual_range(prices)
    distance = (prices["variation"] - prices["usual_variation"]).abs()
    is_alert = distance > ALERT_DEVIATIONS * prices["variation_deviation"]
    return prices[is_alert]
# endregion
