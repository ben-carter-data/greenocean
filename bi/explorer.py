"""Search of «Consulta por clics»: a form, a summary, a table and a detail (D-060).

The reader fills a form; the panel finds the weekly prices that match, says how
many of them are normal, worth a look or out of their usual range, lists them
page by page and opens the detail of the one chosen.

Every field is checked against a fixed list (an allowlist), so only known
columns reach a query. The values the reader chooses always travel as SQL
parameters (?), never inside the SQL text. The weekly change comes from SQL
(LAG); the alert state reuses K6 (bi/alerts.py), so its logic lives in one place.
"""
from datetime import date, timedelta

import pandas as pd

from bi import alerts, queries

# region Constants
FIELD_GROUP = "group"
FIELD_PRODUCT = "product"
FIELD_VARIETY = "variety"
FIELD_QUALITY = "quality"
FIELD_REGION = "region"
FIELD_CHANNEL = "channel"
FIELD_SOURCE = "source"
FIELD_FIRST_WEEK = "first_week"
FIELD_LAST_WEEK = "last_week"
FIELD_ALERT = "alert_state"
# Allowlist: list field -> column of the search query (its options come from there too).
LIST_FIELD_COLUMNS = {
    FIELD_GROUP: ("dim_product", "product_group"), FIELD_PRODUCT: ("dim_product", "product"),
    FIELD_VARIETY: ("dim_product", "variety"), FIELD_QUALITY: ("dim_product", "quality"),
    FIELD_REGION: ("dim_region", "region"), FIELD_CHANNEL: ("dim_channel", "channel"),
    FIELD_SOURCE: ("dim_channel", "source"),
}
SEARCH_FIELDS = list(LIST_FIELD_COLUMNS) + [FIELD_FIRST_WEEK, FIELD_LAST_WEEK, FIELD_ALERT]
FIELD_LABELS = {FIELD_GROUP: "Grupo", FIELD_PRODUCT: "Producto", FIELD_VARIETY: "Variedad",
                FIELD_QUALITY: "Calidad", FIELD_REGION: "Región", FIELD_CHANNEL: "Canal",
                FIELD_SOURCE: "Fuente", FIELD_FIRST_WEEK: "Semana desde",
                FIELD_LAST_WEEK: "Semana hasta", FIELD_ALERT: "Estado de alerta"}
ALL = "Todos"
SOURCE_NAMES = {"wholesale": "Mayorista", "consumer": "Consumidor"}

# Alert state of a weekly price, from the K6 distance of its national series: how many
# standard deviations its change went from the usual change of the 12 weeks before.
ALERT_NORMAL = "Normal"
ALERT_ATTENTION = "Atención"
ALERT_OUT = "Fuera de rango"
ALERT_UNKNOWN = "Sin dato"
ALERT_STATES = [ALERT_NORMAL, ALERT_ATTENTION, ALERT_OUT, ALERT_UNKNOWN]
# Between 1.5 and the K6 limit of 2 the change is not an alert yet, but worth a look.
ATTENTION_DEVIATIONS = 1.5

# A search wider than this asks the reader to narrow it, so the page stays fast.
MAXIMUM_RESULT_ROWS = 50_000
DAYS_IN_A_WEEK = 7
HISTORY_WEEKS = 12

SEARCH_QUERY = """WITH filtered AS (
    SELECT weekly_price.week_start, weekly_price.product_id, weekly_price.region_id,
           weekly_price.channel_id, weekly_price.normalized_unit, weekly_price.price,
           dim_product.product_group, dim_product.product, dim_product.variety,
           dim_product.quality, dim_region.region, dim_channel.channel, dim_channel.source
    FROM weekly_price
    JOIN dim_product ON dim_product.product_id = weekly_price.product_id
    JOIN dim_region ON dim_region.region_id = weekly_price.region_id
    JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
    WHERE weekly_price.flag IS NULL
      AND weekly_price.week_start BETWEEN ? AND ?{conditions}
),
with_previous AS (
    SELECT filtered.*,
           LAG(price) OVER series AS previous_price,
           LAG(week_start) OVER series AS previous_week
    FROM filtered
    WINDOW series AS (PARTITION BY product_id, region_id, channel_id, normalized_unit
                      ORDER BY week_start)
)
SELECT with_previous.*, wholesale.price AS wholesale_price
FROM with_previous
LEFT JOIN dim_channel AS wholesale_channel ON wholesale_channel.source = 'wholesale'
LEFT JOIN weekly_price AS wholesale
  ON wholesale.channel_id = wholesale_channel.channel_id
 AND wholesale.week_start = with_previous.week_start
 AND wholesale.product_id = with_previous.product_id
 AND wholesale.region_id = with_previous.region_id
 AND wholesale.normalized_unit = with_previous.normalized_unit
 AND wholesale.flag IS NULL
WHERE with_previous.week_start >= ?
ORDER BY with_previous.week_start DESC, with_previous.product, with_previous.variety,
         with_previous.quality, with_previous.region, with_previous.channel"""

HISTORY_QUERY = """SELECT week_start, price
FROM weekly_price
WHERE product_id = ? AND region_id = ? AND channel_id = ? AND normalized_unit = ?
  AND flag IS NULL AND week_start <= ?
ORDER BY week_start DESC
LIMIT ?"""
# endregion


# region Query
def validate_filters(filters):
    """Raise ValueError for a field outside the allowlist."""
    unknown = set(filters) - set(SEARCH_FIELDS)
    if unknown:
        raise ValueError(f"Campos desconocidos: {sorted(unknown)}")


def build_search_query(filters):
    """(SQL, parameters) of a search. Only known columns reach the SQL text; every
    value chosen by the reader travels as a parameter."""
    validate_filters(filters)
    first_week = date.fromisoformat(str(filters[FIELD_FIRST_WEEK]))
    # One week before the first one, so its change against the week before exists.
    parameters = [str(first_week - timedelta(days=DAYS_IN_A_WEEK)),
                  str(filters[FIELD_LAST_WEEK])]
    conditions = ""
    for field, (table, column) in LIST_FIELD_COLUMNS.items():
        value = filters.get(field, ALL)
        if value != ALL:
            conditions += f"\n      AND {table}.{column} = ?"
            parameters.append(value)
    parameters.append(str(first_week))
    return SEARCH_QUERY.format(conditions=conditions), tuple(parameters)


def read_search_rows(filters, database_file=queries.DATABASE_FILE):
    """The weekly prices that match the form, with their change and their gap."""
    sql, parameters = build_search_query(filters)
    connection = queries.open_database(database_file)
    rows = pd.read_sql_query(sql, connection, params=parameters)
    connection.close()
    return add_changes(rows)


def read_search_options(database_file=queries.DATABASE_FILE):
    """The values each list field offers, and the weeks loaded: all from the base."""
    connection = queries.open_database(database_file)
    options = {field: [row[0] for row in connection.execute(
                   f"SELECT DISTINCT {column} FROM {table} ORDER BY {column}")]
               for field, (table, column) in LIST_FIELD_COLUMNS.items()}
    options["weeks"] = [row[0] for row in connection.execute(
        "SELECT DISTINCT week_start FROM weekly_price ORDER BY week_start DESC")]
    options["products"] = pd.read_sql_query(
        "SELECT product_group, product, variety, quality FROM dim_product", connection)
    connection.close()
    return options


def read_series_history(row, weeks=HISTORY_WEEKS, database_file=queries.DATABASE_FILE):
    """The last weeks of the price series of one result row, oldest first."""
    connection = queries.open_database(database_file)
    history = pd.read_sql_query(HISTORY_QUERY, connection, params=(
        int(row["product_id"]), int(row["region_id"]), int(row["channel_id"]),
        row["normalized_unit"], str(row["week_start"])[:10], weeks))
    connection.close()
    history["week_start"] = pd.to_datetime(history["week_start"])
    return history.sort_values("week_start")
# endregion


# region Changes and alert states
def add_changes(rows):
    """Weekly change against the week right before (none across a gap) and, for consumer
    prices, the gap over the wholesale price of the same key, region, week and unit."""
    rows = rows.copy()
    rows["week_start"] = pd.to_datetime(rows["week_start"])
    previous_week = pd.to_datetime(rows["previous_week"])
    is_consecutive = (rows["week_start"] - previous_week).dt.days == DAYS_IN_A_WEEK
    rows["variation"] = (rows["price"] / rows["previous_price"] - 1).where(is_consecutive)
    is_consumer = rows["source"] == "consumer"
    rows["gap"] = (rows["price"] / rows["wholesale_price"] - 1).where(is_consumer)
    return rows


def classify_alert_state(distance):
    """Normal, Atención or Fuera de rango, by the K6 distance in standard deviations."""
    if pd.isna(distance):
        return ALERT_UNKNOWN
    if distance > alerts.ALERT_DEVIATIONS:
        return ALERT_OUT
    if distance > ATTENTION_DEVIATIONS:
        return ALERT_ATTENTION
    return ALERT_NORMAL


def build_alert_states(national_prices):
    """The alert state of each national series and week (K6, bi/alerts.py)."""
    prices = alerts.add_usual_range(national_prices)
    distance = ((prices["variation"] - prices["usual_variation"]).abs()
                / prices["variation_deviation"])
    states = prices[alerts.SERIES_COLUMNS + ["week_start"]].copy()
    states["alert_state"] = distance.map(classify_alert_state)
    states["alert_distance"] = distance
    return states


def add_alert_states(rows, states):
    """Each weekly price takes the state of its national series that week (K6 is national,
    D-033); a price without a usual range yet is «Sin dato»."""
    keys = alerts.SERIES_COLUMNS + ["week_start"]
    rows = rows.merge(states, on=keys, how="left")
    rows["alert_state"] = rows["alert_state"].fillna(ALERT_UNKNOWN)
    return rows


def keep_alert_state(rows, state):
    """Only the rows of one alert state (all of them for «Todos»)."""
    return rows if state == ALL else rows[rows["alert_state"] == state]
# endregion


# region Summary and pages
def summarize_latest_week(rows):
    """{state: count} of the latest week of the result, in the order of ALERT_STATES."""
    latest = rows[rows["week_start"] == rows["week_start"].max()]
    counts = latest["alert_state"].value_counts()
    return {state: int(counts.get(state, 0)) for state in ALERT_STATES}


def summarize_groups(rows):
    """Counts of the latest week by product group and alert state, largest group first."""
    latest = rows[rows["week_start"] == rows["week_start"].max()]
    table = pd.crosstab(latest["product_group"], latest["alert_state"])
    table = table.reindex(columns=ALERT_STATES, fill_value=0)
    return table.loc[table.sum(axis=1).sort_values(ascending=False).index]


def take_page(rows, page_size, page):
    """(rows of one page, first shown, last shown, total), counting from 1."""
    total = len(rows)
    last_page = max(1, -(-total // page_size))
    page = min(max(1, page), last_page)
    start = (page - 1) * page_size
    shown = rows.iloc[start:start + page_size]
    return shown, (start + 1 if total else 0), start + len(shown), total
# endregion
