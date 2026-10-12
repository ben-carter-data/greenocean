"""Query builder of the Consultas page: the reader builds a query with clicks.

Every choice is checked against fixed lists (an allowlist), so only known
columns and measures reach a query. Values chosen by the reader always travel
as SQL parameters (?), never inside the SQL text.

Weekly prices are filtered in SQL. Margins and alerts start from what the
dashboard already computes (the k1_margin query and bi/alerts.py) and are
filtered with pandas, so their logic lives in one place only. Grouping and the
measure are always computed with pandas, because SQLite has no median.
"""
import pandas as pd

from bi import queries

# region Constants
VIEW_PRICES = "Precios semanales"
VIEW_MARGINS = "Márgenes"
VIEW_ALERTS = "Alertas"
VIEWS = [VIEW_PRICES, VIEW_MARGINS, VIEW_ALERTS]

GROUP_PRODUCT = "Producto"
GROUP_REGION = "Región"
GROUP_CHANNEL = "Canal"
GROUP_WEEK = "Semana"
GROUP_MONTH = "Mes"
# Allowlist: grouping choice -> column of the rows.
GROUP_COLUMNS = {GROUP_PRODUCT: "product", GROUP_REGION: "region",
                 GROUP_CHANNEL: "channel", GROUP_WEEK: "week_start", GROUP_MONTH: "month"}
TIME_GROUPS = {GROUP_WEEK, GROUP_MONTH}
# K6 alerts are computed on the national price (D-033), so they have no region.
GROUPS_BY_VIEW = {
    VIEW_PRICES: [GROUP_PRODUCT, GROUP_REGION, GROUP_CHANNEL, GROUP_WEEK, GROUP_MONTH],
    VIEW_MARGINS: [GROUP_PRODUCT, GROUP_REGION, GROUP_CHANNEL, GROUP_WEEK, GROUP_MONTH],
    VIEW_ALERTS: [GROUP_PRODUCT, GROUP_CHANNEL, GROUP_WEEK, GROUP_MONTH],
}

FILTER_PRODUCTS = "products"
FILTER_REGIONS = "regions"
FILTER_CHANNELS = "channels"
FILTER_FIRST_WEEK = "first_week"
FILTER_LAST_WEEK = "last_week"
LIST_FILTER_COLUMNS = {FILTER_PRODUCTS: "product", FILTER_REGIONS: "region",
                       FILTER_CHANNELS: "channel"}
KNOWN_FILTERS = set(LIST_FILTER_COLUMNS) | {FILTER_FIRST_WEEK, FILTER_LAST_WEEK}

# Allowlist: measure choice -> pandas aggregation.
MEASURES = {"Promedio": "mean", "Mediana": "median", "Mínimo": "min", "Máximo": "max"}

# The number each view measures, its name for the reader and its scale.
VALUE_COLUMN = "value"
VALUE_TITLES = {VIEW_PRICES: "precio ($)", VIEW_MARGINS: "margen (%)",
                VIEW_ALERTS: "variación (%)"}
COUNT_TITLES = {VIEW_PRICES: "Precios semanales", VIEW_MARGINS: "Márgenes semanales",
                VIEW_ALERTS: "Alertas"}
# Whole pesos for prices, one decimal for percentages, as in the other pages.
DECIMALS_BY_VIEW = {VIEW_PRICES: 0, VIEW_MARGINS: 1, VIEW_ALERTS: 1}
UNIT_COLUMN = "normalized_unit"
COUNT_COLUMN = "row_count"
COLUMN_TITLES = {"product": "Producto", "region": "Región", "channel": "Canal",
                 "week_start": "Semana", "month": "Mes", UNIT_COLUMN: "Unidad"}

MAXIMUM_SHOWN_ROWS = 1000
CHART_MAXIMUM_SERIES = 8
CHART_MAXIMUM_BARS = 30
SERIES_SEPARATOR = " · "
TOTAL_LABEL = "Total"

# Weekly prices used by the indicators: flagged prices stay out (RN-05, RN-12).
PRICE_QUERY = """SELECT weekly_price.week_start, dim_product.product, dim_region.region,
       dim_channel.channel, weekly_price.normalized_unit, weekly_price.price
FROM weekly_price
JOIN dim_product ON dim_product.product_id = weekly_price.product_id
JOIN dim_region ON dim_region.region_id = weekly_price.region_id
JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
WHERE weekly_price.flag IS NULL"""
# Allowlist: list filter -> column of the price query.
PRICE_FILTER_COLUMNS = {FILTER_PRODUCTS: "dim_product.product",
                        FILTER_REGIONS: "dim_region.region",
                        FILTER_CHANNELS: "dim_channel.channel"}
PRICE_OPTION_QUERIES = {
    FILTER_PRODUCTS: "SELECT DISTINCT product FROM dim_product ORDER BY product",
    FILTER_REGIONS: "SELECT region FROM dim_region ORDER BY region_id",
    FILTER_CHANNELS: "SELECT DISTINCT channel FROM dim_channel ORDER BY channel",
}
PRICE_WEEK_RANGE_QUERY = "SELECT MIN(week_start), MAX(week_start) FROM weekly_price"
# endregion


# region Choices
def validate_choices(view, group_labels, measure_label, filters):
    """Raise ValueError when a choice is not in the allowlists."""
    if view not in VIEWS:
        raise ValueError(f"Unknown view: {view}")
    unknown_groups = set(group_labels) - set(GROUPS_BY_VIEW[view])
    if unknown_groups:
        raise ValueError(f"Unknown grouping for {view}: {sorted(unknown_groups)}")
    if TIME_GROUPS <= set(group_labels):
        raise ValueError("Week and month cannot be grouped together")
    if measure_label not in MEASURES:
        raise ValueError(f"Unknown measure: {measure_label}")
    unknown_filters = set(filters) - KNOWN_FILTERS
    if unknown_filters:
        raise ValueError(f"Unknown filter: {sorted(unknown_filters)}")


def list_group_columns(view, group_labels):
    """Columns to group by. Prices always add the unit: $/kilo and $/unidad never mix."""
    columns = [GROUP_COLUMNS[label] for label in GROUPS_BY_VIEW[view] if label in group_labels]
    if view == VIEW_PRICES:
        columns.append(UNIT_COLUMN)
    return columns
# endregion


# region Weekly prices in SQL
def build_price_query(filters):
    """(SQL text, parameters) for the weekly prices that pass the filters.

    Only fixed column names enter the text; every chosen value is a parameter.
    """
    conditions = []
    parameters = []
    for filter_name, column in PRICE_FILTER_COLUMNS.items():
        values = list(filters.get(filter_name) or [])
        if values:
            placeholders = ", ".join("?" for _ in values)
            conditions.append(f"{column} IN ({placeholders})")
            parameters += values
    if filters.get(FILTER_FIRST_WEEK):
        conditions.append("weekly_price.week_start >= ?")
        parameters.append(str(filters[FILTER_FIRST_WEEK]))
    if filters.get(FILTER_LAST_WEEK):
        conditions.append("weekly_price.week_start <= ?")
        parameters.append(str(filters[FILTER_LAST_WEEK]))
    sql = PRICE_QUERY + "".join(f"\n  AND {condition}" for condition in conditions)
    return sql, parameters


def read_price_rows(filters, database_file=queries.DATABASE_FILE):
    """Weekly prices that pass the filters, read through the read-only connection."""
    sql, parameters = build_price_query(filters)
    connection = queries.open_database(database_file)
    rows = pd.read_sql(sql, connection, params=parameters)
    connection.close()
    rows["week_start"] = pd.to_datetime(rows["week_start"])
    return rows.rename(columns={"price": VALUE_COLUMN})


def read_price_options(database_file=queries.DATABASE_FILE):
    """Real values for the price filters, and the first and last week with data."""
    connection = queries.open_database(database_file)
    options = {name: [row[0] for row in connection.execute(sql)]
               for name, sql in PRICE_OPTION_QUERIES.items()}
    first_week, last_week = connection.execute(PRICE_WEEK_RANGE_QUERY).fetchone()
    connection.close()
    options[FILTER_FIRST_WEEK] = pd.Timestamp(first_week).date()
    options[FILTER_LAST_WEEK] = pd.Timestamp(last_week).date()
    return options
# endregion


# region Margins and alerts in pandas
def prepare_margin_rows(margin_rows):
    """Rows of k1_margin with the margin in percent as the measured value."""
    return margin_rows.assign(**{VALUE_COLUMN: margin_rows["margin"] * 100})


def prepare_alert_rows(alert_rows):
    """Rows of find_price_alerts with the weekly variation in percent as the value."""
    return alert_rows.assign(**{VALUE_COLUMN: alert_rows["variation"] * 100})


def filter_rows(rows, filters):
    """Keep the rows that pass the filters; an empty list means 'all'."""
    is_kept = pd.Series(True, index=rows.index)
    for filter_name, column in LIST_FILTER_COLUMNS.items():
        values = filters.get(filter_name)
        if values and column in rows.columns:
            is_kept &= rows[column].isin(values)
    if filters.get(FILTER_FIRST_WEEK):
        is_kept &= rows["week_start"] >= pd.Timestamp(filters[FILTER_FIRST_WEEK])
    if filters.get(FILTER_LAST_WEEK):
        is_kept &= rows["week_start"] <= pd.Timestamp(filters[FILTER_LAST_WEEK])
    return rows[is_kept]
# endregion


# region Grouping and measure
def add_month_column(rows):
    """Month of each week as '2026-03', taken from its Monday."""
    return rows.assign(month=rows["week_start"].dt.strftime("%Y-%m"))


def aggregate_rows(rows, group_columns, measure_label):
    """One row per group with the chosen measure and how many rows it summarizes."""
    aggregation = MEASURES[measure_label]
    if rows.empty:
        return pd.DataFrame(columns=group_columns + [VALUE_COLUMN, COUNT_COLUMN])
    if not group_columns:
        return pd.DataFrame({VALUE_COLUMN: [rows[VALUE_COLUMN].agg(aggregation)],
                             COUNT_COLUMN: [len(rows)]})
    result = rows.groupby(group_columns, as_index=False).agg(
        **{VALUE_COLUMN: (VALUE_COLUMN, aggregation), COUNT_COLUMN: (VALUE_COLUMN, "size")})
    return result.sort_values(group_columns, ignore_index=True)


def build_result(view, rows, group_labels, measure_label, filters):
    """Filter, group and measure the rows of one view. Raises ValueError on unknown choices."""
    validate_choices(view, group_labels, measure_label, filters)
    rows = add_month_column(filter_rows(rows, filters))
    return aggregate_rows(rows, list_group_columns(view, group_labels), measure_label)


def limit_rows(result):
    """(at most 1.000 rows to show, True when the result had more)."""
    return result.head(MAXIMUM_SHOWN_ROWS), len(result) > MAXIMUM_SHOWN_ROWS


def name_columns_for_reader(result, view, measure_label):
    """Spanish column titles ('Producto', 'Promedio · precio ($)') and rounded values."""
    titles = dict(COLUMN_TITLES)
    titles[VALUE_COLUMN] = f"{measure_label} · {VALUE_TITLES[view]}"
    titles[COUNT_COLUMN] = COUNT_TITLES[view]
    result = result.copy()
    result[VALUE_COLUMN] = result[VALUE_COLUMN].round(DECIMALS_BY_VIEW[view])
    if "week_start" in result.columns:
        result["week_start"] = pd.to_datetime(result["week_start"]).dt.date
    return result.rename(columns=titles)
# endregion


# region Chart data
def find_time_column(result):
    """'week_start' or 'month' when the result is grouped by time, else None."""
    for column in ["week_start", "month"]:
        if column in result.columns:
            return column
    return None


def build_series_labels(result, columns):
    """One label per row joining the given columns: 'Tomate · Feria libre'."""
    if not columns:
        return pd.Series(TOTAL_LABEL, index=result.index)
    return result[columns].astype(str).agg(SERIES_SEPARATOR.join, axis=1)


def prepare_line_rows(result):
    """Rows for a line chart (week_start, channel, value): one line per series.

    The column is called 'channel' because the chart draws one line per channel;
    here a 'channel' can also be a product or a region.
    """
    time_column = find_time_column(result)
    other_columns = [column for column in result.columns
                     if column not in {time_column, VALUE_COLUMN, COUNT_COLUMN}]
    return pd.DataFrame({"week_start": pd.to_datetime(result[time_column]),
                         "channel": build_series_labels(result, other_columns),
                         "value": result[VALUE_COLUMN]})


def prepare_bar_rows(result):
    """Rows for horizontal bars (label, value): the largest values first."""
    label_columns = [column for column in result.columns
                     if column not in {VALUE_COLUMN, COUNT_COLUMN}]
    rows = pd.DataFrame({"label": build_series_labels(result, label_columns),
                         "value": result[VALUE_COLUMN]})
    return rows.sort_values("value", ascending=False).head(CHART_MAXIMUM_BARS)
# endregion
