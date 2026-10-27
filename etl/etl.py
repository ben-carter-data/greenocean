"""ETL for the price monitor.

Flow: load_raw_files -> clean -> validate_rows -> apply_business_rules
      -> check_quality -> load.

load_raw_files() copies the downloaded files into raw.db exactly as published.
The other steps turn them into weekly prices in datos.db, applying the
business rules (RN) of docs/DISENO.md. Each rule is named where it is applied.
"""

from __future__ import annotations

from typing import Any

import csv
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# region Variables
BASE_DIR = Path(__file__).resolve().parent
# Raw database: large, rebuilt on every run and never committed to the repository.
RAW_DATABASE_FILE = BASE_DIR / "raw.db"
RAW_SCHEMA_FILE = BASE_DIR / "raw_schema.sql"
# Indicator database: weekly prices, committed so the dashboard can read it.
DATABASE_FILE = BASE_DIR / "datos.db"
SCHEMA_FILE = BASE_DIR / "schema.sql"
DOWNLOAD_DIR = BASE_DIR.parent / "agent" / "downloads"

STATUS_LOADED = "LOADED"
STATUS_UNCHANGED = "UNCHANGED"
STATUS_FAILED = "FAILED"
# endregion

# region Constants
SOURCE_WHOLESALE = "wholesale"
SOURCE_CONSUMER = "consumer"
SOURCES = [SOURCE_WHOLESALE, SOURCE_CONSUMER]

NON_BREAKING_SPACE = "\u00a0"
PRODUCT_SEPARATOR = "|"
# Value ODEPA itself uses when a variety or quality is not informed.
UNSPECIFIED = "Sin especificar"
# Channel name given to the wholesale source in dim_channel.
WHOLESALE_CHANNEL = "Mayorista"
RAW_TABLE_BY_SOURCE = {SOURCE_WHOLESALE: "raw_wholesale", SOURCE_CONSUMER: "raw_consumer"}
CONSUMER_GROUP_BY_WHOLESALE_SUBSECTOR = {"Hortalizas y tubérculos": "Hortalizas"}

PRICE_COLUMNS = ["min_price", "max_price", "avg_price"]
TEXT_COLUMNS_BY_SOURCE = {
    SOURCE_WHOLESALE: ["region", "subsector", "product", "variety", "quality", "sale_unit"],
    SOURCE_CONSUMER: ["region", "sales_channel", "product_group", "product", "unit"],
}
# Columns shared by both sources after clean().
CLEAN_COLUMNS = [
    "source",
    "file_year",
    "first_date",
    "last_date",
    "region_id",
    "region",
    "channel",
    "product_group",
    "product",
    "variety",
    "quality",
    "unit",
    "volume",
    "min_price",
    "max_price",
    "avg_price",
]

REASON_UNREADABLE_VALUE = "UNREADABLE_VALUE"
REASON_NON_POSITIVE_PRICE = "NON_POSITIVE_PRICE"
REASON_MINIMUM_ABOVE_MAXIMUM = "MINIMUM_ABOVE_MAXIMUM"
REASON_DATE_OUTSIDE_FILE_YEAR = "DATE_OUTSIDE_FILE_YEAR"
REASON_NON_POSITIVE_VOLUME = "NON_POSITIVE_VOLUME"

UNIT_KILO = "kilo"
UNIT_EACH = "unidad"
UNIT_LITER = "litro"
# Units whose price is already expressed per kilo, per unit or per liter.
NORMALIZED_UNIT_BY_PREFIX = {"$/kilo": UNIT_KILO, "$/unidad": UNIT_EACH, "$/litro": UNIT_LITER}
UNIT_NUMBER_PATTERN = re.compile(r"\d+(?:,\d+)?")
# A quantity followed by its measure: "18 kilos", "15 unidades", "900 ml".
UNIT_QUANTITY_PATTERN = re.compile(r"(\d+(?:,\d+)?) ?(kilos?|unidades|gramos|grs|litros?|ml)\b")
# Measure word -> (normalized unit, how many normalized units one of them is).
NORMALIZED_UNIT_BY_MEASURE = {
    "kilo": (UNIT_KILO, 1),
    "kilos": (UNIT_KILO, 1),
    "gramos": (UNIT_KILO, 0.001),
    "grs": (UNIT_KILO, 0.001),
    "unidades": (UNIT_EACH, 1),
    "litro": (UNIT_LITER, 1),
    "litros": (UNIT_LITER, 1),
    "ml": (UNIT_LITER, 0.001),
}

# One weekly price per combination of these columns.
WEEKLY_KEY_COLUMNS = [
    "week_start",
    "source",
    "channel",
    "region_id",
    "product_group",
    "product",
    "variety",
    "quality",
    "normalized_unit",
]
# Values written in weekly_price.flag, named as in the design document.
FLAG_UNIT_NOT_CONVERTIBLE = "UNIDAD_NO_CONVERTIBLE"
FLAG_OUTLIER = "ATIPICO"
# RN-12: a price is an outlier beyond 5 times, or below 1/5 of, the median.
OUTLIER_FACTOR = 5
# The median is taken inside one source: retail prices are compared with retail
# prices and wholesale prices with wholesale prices.
OUTLIER_GROUP_COLUMNS = ["week_start", "source", "product_group", "product", "normalized_unit"]

PRODUCT_COLUMNS = ["product_group", "product", "variety", "quality"]
CHANNEL_COLUMNS = ["channel", "source"]
# Columns of the weekly_price table, in order.
WEEKLY_PRICE_COLUMNS = [
    "week_start",
    "product_id",
    "region_id",
    "channel_id",
    "normalized_unit",
    "price",
    "volume",
    "observation_count",
    "flag",
]

# A load is refused when it reads less than this share of the previous one.
MINIMUM_ROWS_RATIO = 0.9
# Chile has 16 regions, numbered 1 to 16.
KNOWN_REGION_IDS = set(range(1, 17))
KNOWN_CHANNELS = {
    WHOLESALE_CHANNEL,
    "Supermercado",
    "Feria libre",
    "Carnicería",
    "Panadería",
    "Mercado Minorista",
    "Mercado Mayorista",
    "Supermercado en Línea",
}
# D-042: weeks the source itself never published (checked in the original file).
# They are accepted; any other missing week still stops the load.
KNOWN_SOURCE_GAPS = {SOURCE_CONSUMER: {"2022-05-02"}}
PROBLEM_TOO_FEW_ROWS = "TOO_FEW_ROWS"
PROBLEM_MISSING_WEEKS = "MISSING_WEEKS"
PROBLEM_UNKNOWN_REGION = "UNKNOWN_REGION"
PROBLEM_UNKNOWN_CHANNEL = "UNKNOWN_CHANNEL"
PROBLEM_DUPLICATE_KEYS = "DUPLICATE_KEYS"

# K7. A key is product + variety + quality. It has a margin when a wholesale
# and a consumer price exist for the same week, region and unit (RN-06),
# neither of them flagged (RN-05, RN-12).
MATCH_COVERAGE_QUERY = """
WITH priced AS (
    SELECT weekly_price.week_start, weekly_price.product_id, weekly_price.region_id,
           weekly_price.normalized_unit, dim_channel.source
    FROM weekly_price
    JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
    WHERE weekly_price.flag IS NULL
),
consumer_keys AS (
    SELECT DISTINCT weekly_price.product_id
    FROM weekly_price
    JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
    JOIN dim_product ON dim_product.product_id = weekly_price.product_id
    WHERE dim_channel.source = 'consumer'
      AND dim_product.product_group IN ('Frutas', 'Hortalizas')
),
keys_with_margin AS (
    SELECT DISTINCT consumer.product_id
    FROM priced AS consumer
    JOIN priced AS wholesale
      ON wholesale.week_start = consumer.week_start
     AND wholesale.product_id = consumer.product_id
     AND wholesale.region_id = consumer.region_id
     AND wholesale.normalized_unit = consumer.normalized_unit
    WHERE consumer.source = 'consumer' AND wholesale.source = 'wholesale'
)
SELECT (SELECT COUNT(*) FROM keys_with_margin), (SELECT COUNT(*) FROM consumer_keys)
"""
# endregion


# region Database
def open_database(database_file: Path = RAW_DATABASE_FILE, schema_file: Path = RAW_SCHEMA_FILE) -> sqlite3.Connection:
    """Open a database and create the tables of its schema if they do not exist."""
    connection = sqlite3.connect(database_file)
    connection.executescript(schema_file.read_text(encoding="utf-8"))
    return connection


# endregion


# region Raw load
def load_raw_files(connection: sqlite3.Connection, download_dir: Path = DOWNLOAD_DIR) -> list[tuple[str, str, int]]:
    """Load every downloaded file into its raw table.

    A year whose file did not change (same hash) is skipped. If the file
    changed, the rows of that year are replaced. Returns a list of
    (file_name, status, row_count).
    """
    manifest = json.loads((download_dir / "manifest.json").read_text(encoding="utf-8"))
    load_summary = []
    for file_name, file_info in sorted(manifest.items()):
        table = RAW_TABLE_BY_SOURCE[file_info["source"]]
        rows_already_loaded = connection.execute(
            f"SELECT COUNT(*) FROM {table} WHERE file_year = ? AND file_hash = ?",
            (file_info["year"], file_info["hash"]),
        ).fetchone()[0]
        if rows_already_loaded:
            load_summary.append((file_name, STATUS_UNCHANGED, rows_already_loaded))
            continue

        with open(download_dir / file_name, encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            next(reader)  # header, already validated by the agent
            rows = [[file_info["year"], file_info["hash"], *row] for row in reader]

        placeholders = ",".join("?" * len(rows[0]))
        with connection:  # all or nothing
            connection.execute(f"DELETE FROM {table} WHERE file_year = ?", (file_info["year"],))
            connection.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        load_summary.append((file_name, STATUS_LOADED, len(rows)))
    return load_summary


# endregion


# region Clean
def normalize_text(value: str) -> str:
    """RN-13: remove non-breaking and repeated spaces; letter case is not changed."""
    return " ".join(value.replace(NON_BREAKING_SPACE, " ").split())


def convert_decimal_text(text_column: pd.Series) -> pd.Series:
    """RN-01: turn text with a decimal comma into numbers. Unreadable text becomes NaN."""
    return pd.to_numeric(text_column.str.replace(",", ".", regex=False), errors="coerce")


def split_consumer_product(product: str) -> tuple[str, str, str]:
    """RN-02: split 'Producto|Variedad|Calidad' into its three parts."""
    parts = product.split(PRODUCT_SEPARATOR)
    if len(parts) != 3:
        return product, UNSPECIFIED, UNSPECIFIED
    return parts[0].strip(), parts[1].strip(), parts[2].strip()


def add_wholesale_columns(rows: pd.DataFrame) -> pd.DataFrame:
    """Fill the common columns from the wholesale columns."""
    rows["first_date"] = pd.to_datetime(rows["price_date"], errors="coerce")
    rows["last_date"] = rows["first_date"]
    rows["channel"] = WHOLESALE_CHANNEL
    # Both sources must name the group the same way to share one product key.
    rows["product_group"] = rows["subsector"].replace(CONSUMER_GROUP_BY_WHOLESALE_SUBSECTOR)
    rows["unit"] = rows["sale_unit"]
    rows["volume"] = convert_decimal_text(rows["volume"])
    return rows


def add_consumer_columns(rows: pd.DataFrame) -> pd.DataFrame:
    """Fill the common columns from the consumer columns."""
    rows["first_date"] = pd.to_datetime(rows["week_start"], errors="coerce")
    rows["last_date"] = pd.to_datetime(rows["week_end"], errors="coerce")
    rows["channel"] = rows["sales_channel"]
    product_parts = [split_consumer_product(product) for product in rows["product"]]
    rows[["product", "variety", "quality"]] = pd.DataFrame(product_parts, index=rows.index)
    # The consumer source publishes no volume.
    rows["volume"] = float("nan")
    return rows


def clean(raw_rows: pd.DataFrame, source: str) -> pd.DataFrame:
    """Turn the raw text rows of one source into typed rows with common columns.

    The result keeps the index of raw_rows, so a rejected row can be traced
    back to its original text.
    """
    rows = raw_rows.copy()
    for column in TEXT_COLUMNS_BY_SOURCE[source]:
        rows[column] = rows[column].map(normalize_text)
    for column in PRICE_COLUMNS:
        rows[column] = convert_decimal_text(rows[column])
    rows["region_id"] = pd.to_numeric(rows["region_id"], errors="coerce")
    rows["source"] = source
    if source == SOURCE_WHOLESALE:
        rows = add_wholesale_columns(rows)
    else:
        rows = add_consumer_columns(rows)
    return rows[CLEAN_COLUMNS]


# endregion


# region Validation
def validate_rows(clean_rows: pd.DataFrame) -> pd.Series:
    """RN-11: return the rejection reason of each row, or "" when the row is valid.

    A row with several problems gets the first reason found, so every row
    read ends either loaded or rejected exactly once.
    """
    checked_columns = PRICE_COLUMNS + ["first_date", "last_date", "region_id"]
    is_unreadable = clean_rows[checked_columns].isna().any(axis=1)
    is_non_positive = (clean_rows[PRICE_COLUMNS] <= 0).any(axis=1)
    is_minimum_above_maximum = clean_rows["min_price"] > clean_rows["max_price"]
    # The first consumer week of a year starts in December of the previous one,
    # so a week belongs to the file when either of its ends falls in that year.
    is_outside_file_year = (clean_rows["first_date"].dt.year != clean_rows["file_year"]) & (
        clean_rows["last_date"].dt.year != clean_rows["file_year"]
    )
    # A wholesale row without volume cannot take part in a weighted average (RN-07).
    is_missing_volume = (clean_rows["source"] == SOURCE_WHOLESALE) & ~(clean_rows["volume"] > 0)

    reasons = pd.Series("", index=clean_rows.index)
    checks = [
        (is_unreadable, REASON_UNREADABLE_VALUE),
        (is_non_positive, REASON_NON_POSITIVE_PRICE),
        (is_minimum_above_maximum, REASON_MINIMUM_ABOVE_MAXIMUM),
        (is_outside_file_year, REASON_DATE_OUTSIDE_FILE_YEAR),
        (is_missing_volume, REASON_NON_POSITIVE_VOLUME),
    ]
    for is_invalid, reason in checks:
        reasons[is_invalid & (reasons == "")] = reason
    return reasons


def build_rejections(raw_rows: pd.DataFrame, reasons: pd.Series, source: str) -> pd.DataFrame:
    """RN-11: keep each rejected row exactly as it was read, with its reason."""
    rejected_rows = raw_rows[reasons != ""]
    original_rows = [json.dumps(row, ensure_ascii=False) for row in rejected_rows.to_dict("records")]
    return pd.DataFrame({"source": source, "reason": reasons[reasons != ""].to_list(), "original_row": original_rows})


# endregion


# region Units
def convert_unit(unit_text: str) -> tuple[str | None, float | None]:
    """RN-03, RN-04, RN-05: read a sale unit such as '$/caja 18 kilos'.

    Returns (normalized unit, quantity the price must be divided by), or
    (None, None) when the unit does not declare exactly one quantity.
    """
    text = unit_text.lower()
    for prefix, normalized_unit in NORMALIZED_UNIT_BY_PREFIX.items():
        if text.startswith(prefix):
            return normalized_unit, 1.0
    # Two numbers mean a range ("1,5 a 2 kilos") or a pack of packs
    # ("12 canastillos 125 gramos"): there is no single quantity to divide by.
    if len(UNIT_NUMBER_PATTERN.findall(text)) != 1:
        return None, None
    quantity_match = UNIT_QUANTITY_PATTERN.search(text)
    if quantity_match is None:
        return None, None
    normalized_unit, measure_size = NORMALIZED_UNIT_BY_MEASURE[quantity_match.group(2)]
    quantity = float(quantity_match.group(1).replace(",", ".")) * measure_size
    if quantity <= 0:
        return None, None
    return normalized_unit, quantity


def normalize_units(rows: pd.DataFrame) -> pd.DataFrame:
    """RN-03, RN-04, RN-05: add normalized_unit and normalized_price to each row.

    Rows whose unit is not convertible are kept, with both columns empty.
    """
    conversions = [(unit, *convert_unit(unit)) for unit in rows["unit"].unique()]
    conversion_table = pd.DataFrame(conversions, columns=["unit", "normalized_unit", "unit_quantity"])
    rows = rows.merge(conversion_table, on="unit", how="left")
    rows["normalized_price"] = rows["avg_price"] / rows["unit_quantity"]
    return rows


# endregion


# region Weekly aggregation
def assign_week_start(rows: pd.DataFrame) -> pd.DataFrame:
    """RN-08: a week is identified by its Monday, the consumer's 'Fecha inicio'."""
    days_since_monday = pd.to_timedelta(rows["first_date"].dt.dayofweek, unit="D")
    rows["week_start"] = rows["first_date"] - days_since_monday
    return rows


def aggregate_wholesale_weekly(wholesale_rows: pd.DataFrame) -> pd.DataFrame:
    """RN-07: weekly wholesale price = daily prices weighted by their volume."""
    rows = wholesale_rows.copy()
    rows["price_times_volume"] = rows["normalized_price"] * rows["volume"]
    weekly_prices = rows.groupby(WEEKLY_KEY_COLUMNS, dropna=False, as_index=False).agg(
        price_times_volume=("price_times_volume", "sum"), volume=("volume", "sum"), observation_count=("volume", "size")
    )
    weekly_prices["price"] = weekly_prices["price_times_volume"] / weekly_prices["volume"]
    # Without a normalized unit there is no price: the sum above would give 0.
    weekly_prices.loc[weekly_prices["normalized_unit"].isna(), "price"] = float("nan")
    return weekly_prices.drop(columns="price_times_volume")


def aggregate_consumer_weekly(consumer_rows: pd.DataFrame) -> pd.DataFrame:
    """RN-09: weekly consumer price = plain average by region, channel and product.

    RN-10: the 'Mercado Mayorista' point of sale is one more channel here.
    """
    weekly_prices = consumer_rows.groupby(WEEKLY_KEY_COLUMNS, dropna=False, as_index=False).agg(
        price=("normalized_price", "mean"), observation_count=("avg_price", "size")
    )
    weekly_prices["volume"] = float("nan")
    return weekly_prices


def aggregate_weekly(rows: pd.DataFrame) -> pd.DataFrame:
    """Build one row per week, product key, region, channel and normalized unit."""
    rows = assign_week_start(rows)
    is_wholesale = rows["source"] == SOURCE_WHOLESALE
    weekly_prices = pd.concat(
        [aggregate_wholesale_weekly(rows[is_wholesale]), aggregate_consumer_weekly(rows[~is_wholesale])],
        ignore_index=True,
    )
    weekly_prices["flag"] = None
    # RN-05: the row is kept, without price and with its reason.
    is_not_convertible = weekly_prices["normalized_unit"].isna()
    weekly_prices.loc[is_not_convertible, "flag"] = FLAG_UNIT_NOT_CONVERTIBLE
    return weekly_prices


# endregion


# region Outliers
def flag_outliers(weekly_prices: pd.DataFrame) -> pd.DataFrame:
    """RN-12: flag prices far from the median of their product in that week.

    The median covers every variety, quality, region and channel of the
    product inside one source. A flagged row is kept; the indicators leave it out.
    """
    median_price = weekly_prices.groupby(OUTLIER_GROUP_COLUMNS)["price"].transform("median")
    is_too_high = weekly_prices["price"] > median_price * OUTLIER_FACTOR
    is_too_low = weekly_prices["price"] < median_price / OUTLIER_FACTOR
    weekly_prices.loc[is_too_high | is_too_low, "flag"] = FLAG_OUTLIER
    return weekly_prices


# endregion


# region Business rules
def apply_business_rules(valid_rows: pd.DataFrame) -> pd.DataFrame:
    """Apply the unit, weekly and outlier rules to the valid rows of both sources."""
    rows = normalize_units(valid_rows)
    weekly_prices = aggregate_weekly(rows)
    return flag_outliers(weekly_prices)


# endregion


# region Quality checks
def read_previous_rows_read(connection: sqlite3.Connection) -> int | None:
    """Rows read by the latest successful run, or None on the first run."""
    row = connection.execute(
        "SELECT rows_read FROM etl_run WHERE status = ? ORDER BY run_id DESC LIMIT 1", (STATUS_LOADED,)
    ).fetchone()
    return row[0] if row else None


def find_missing_weeks(week_starts: pd.Series) -> list[str]:
    """List the Mondays between the first and the last week that have no data."""
    expected_weeks = pd.date_range(week_starts.min(), week_starts.max(), freq="7D")
    weeks_with_data = set(week_starts)
    return [str(week.date()) for week in expected_weeks if week not in weeks_with_data]


def find_unexpected_missing_weeks(week_starts: pd.Series, source: str) -> list[str]:
    """Missing Mondays of one source, leaving out the known gaps of the source (D-042)."""
    if not len(week_starts):
        return []
    known_gaps = KNOWN_SOURCE_GAPS.get(source, set())
    return [week for week in find_missing_weeks(week_starts) if week not in known_gaps]


def check_quality(weekly_prices: pd.DataFrame, rows_read: int, previous_rows_read: int | None) -> list[str]:
    """Return the problems that must stop the load; an empty list means go ahead."""
    problems = []
    # The files only grow during a year, so far fewer rows means a truncated file.
    if previous_rows_read and rows_read < previous_rows_read * MINIMUM_ROWS_RATIO:
        problems.append(
            f"{PROBLEM_TOO_FEW_ROWS}: read {rows_read} rows, the previous successful run read {previous_rows_read}"
        )
    for source in SOURCES:
        source_weeks = weekly_prices.loc[weekly_prices["source"] == source, "week_start"]
        missing_weeks = find_unexpected_missing_weeks(source_weeks, source)
        if missing_weeks:
            problems.append(f"{PROBLEM_MISSING_WEEKS}: {source} has no data for {', '.join(missing_weeks)}")
    unknown_regions = sorted(set(weekly_prices["region_id"]) - KNOWN_REGION_IDS)
    if unknown_regions:
        problems.append(f"{PROBLEM_UNKNOWN_REGION}: {unknown_regions}")
    unknown_channels = sorted(set(weekly_prices["channel"]) - KNOWN_CHANNELS)
    if unknown_channels:
        problems.append(f"{PROBLEM_UNKNOWN_CHANNEL}: {unknown_channels}")
    # RN-14 and D-046: the database has no unique index, so the check lives here.
    duplicate_count = weekly_prices.duplicated(WEEKLY_KEY_COLUMNS).sum()
    if duplicate_count:
        problems.append(f"{PROBLEM_DUPLICATE_KEYS}: {duplicate_count} weekly prices share their key with another one")
    return problems


# endregion


# region Load
def read_raw_rows(raw_connection: sqlite3.Connection, source: str) -> pd.DataFrame:
    """Read every raw row of one source, all columns as text."""
    return pd.read_sql(f"SELECT * FROM {RAW_TABLE_BY_SOURCE[source]}", raw_connection)


def insert_rows(connection: sqlite3.Connection, table: str, rows: pd.DataFrame) -> None:
    """Insert a DataFrame into the table that has the same column names."""
    # sqlite3 only accepts plain Python values, and NaN must become NULL.
    values = rows.astype(object).where(rows.notna(), None).values.tolist()
    column_names = ", ".join(rows.columns)
    placeholders = ", ".join("?" * len(rows.columns))
    connection.executemany(f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})", values)


def add_new_dimension_rows(
    connection: sqlite3.Connection, table: str, rows: pd.DataFrame, key_columns: list[str]
) -> None:
    """Insert only the rows whose key is not in the dimension yet.

    Existing rows keep their identifier, so identifiers are stable between runs.
    """
    existing_keys = pd.read_sql(f"SELECT * FROM {table}", connection)[key_columns]
    compared_rows = rows.merge(existing_keys, on=key_columns, how="left", indicator=True)
    new_rows = compared_rows[compared_rows["_merge"] == "left_only"]
    insert_rows(connection, table, new_rows.drop(columns="_merge"))


def attach_dimension_identifiers(connection: sqlite3.Connection, weekly_prices: pd.DataFrame) -> pd.DataFrame:
    """Replace product and channel names by their identifiers in the dimensions."""
    products = pd.read_sql("SELECT * FROM dim_product", connection)
    channels = pd.read_sql("SELECT * FROM dim_channel", connection)
    rows = weekly_prices.merge(products, on=PRODUCT_COLUMNS).merge(channels, on=CHANNEL_COLUMNS)
    rows["week_start"] = rows["week_start"].dt.strftime("%Y-%m-%d")
    return rows[WEEKLY_PRICE_COLUMNS]


MONTH_NAMES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]
# Southern hemisphere: summer is December to February.
SEASON_BY_MONTH = {
    12: "verano",
    1: "verano",
    2: "verano",
    3: "otoño",
    4: "otoño",
    5: "otoño",
    6: "invierno",
    7: "invierno",
    8: "invierno",
    9: "primavera",
    10: "primavera",
    11: "primavera",
}
DIM_DATE_COLUMNS = ["week_start", "iso_year", "iso_week", "month", "month_name", "year", "season"]


def build_dim_date(first_week: Any, last_week: Any) -> pd.DataFrame:
    """Every Monday from the first to the last week, without gaps (D-095)."""
    weeks = pd.date_range(pd.Timestamp(first_week), pd.Timestamp(last_week), freq="7D")
    calendar = weeks.isocalendar()
    return pd.DataFrame(
        {
            "week_start": weeks.strftime("%Y-%m-%d"),
            "iso_year": calendar["year"].to_numpy().astype(int),
            "iso_week": calendar["week"].to_numpy().astype(int),
            "month": weeks.month,
            "month_name": [MONTH_NAMES[month - 1] for month in weeks.month],
            "year": weeks.year,
            "season": [SEASON_BY_MONTH[month] for month in weeks.month],
        }
    )[DIM_DATE_COLUMNS]


def ensure_weekly_price_references_dim_date(connection: sqlite3.Connection) -> bool:
    """Databases created before D-095: rebuild weekly_price with its date key.

    SQLite cannot add a foreign key to an existing table. The rows are copied
    unchanged, in the same transaction as the caller.
    """
    references = {row[2] for row in connection.execute("PRAGMA foreign_key_list(weekly_price)")}
    if "dim_date" in references:
        return False
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    start = schema.index("CREATE TABLE IF NOT EXISTS weekly_price")
    definition = schema[start : schema.index(");", start) + 2]
    connection.execute("ALTER TABLE weekly_price RENAME TO weekly_price_before_d095")
    connection.execute(definition)
    columns = ", ".join(WEEKLY_PRICE_COLUMNS)
    connection.execute(f"INSERT INTO weekly_price ({columns}) SELECT {columns} FROM weekly_price_before_d095")
    connection.execute("DROP TABLE weekly_price_before_d095")
    return True


def refresh_dim_date(connection: sqlite3.Connection, week_starts: Any = None) -> None:
    """Rebuild dim_date from the weeks of weekly_price (or the given ones)."""
    if week_starts is None:
        first, last = connection.execute("SELECT MIN(week_start), MAX(week_start) FROM weekly_price").fetchone()
    else:
        first, last = min(week_starts), max(week_starts)
    connection.execute("DELETE FROM dim_date")
    if first is not None:
        insert_rows(connection, "dim_date", build_dim_date(first, last))


def record_run(
    connection: sqlite3.Connection, started_at: str, status: str, row_counts: dict[str, Any], message: str = ""
) -> int | None:
    """Write one line in etl_run and return its identifier."""
    cursor = connection.execute(
        "INSERT INTO etl_run (started_at, status, rows_read, rows_loaded,"
        " rows_rejected, message) VALUES (?, ?, ?, ?, ?, ?)",
        (started_at, status, row_counts["rows_read"], row_counts["rows_loaded"], row_counts["rows_rejected"], message),
    )
    return cursor.lastrowid


def load(
    connection: sqlite3.Connection,
    weekly_prices: pd.DataFrame,
    regions: pd.DataFrame,
    rejections: pd.DataFrame,
    started_at: str,
    row_counts: dict[str, Any],
) -> None:
    """RN-14: write the result of one run; running it again leaves the same rows.

    Everything happens in one transaction: if any step fails, the database
    stays as it was before the run.
    """
    with connection:
        add_new_dimension_rows(connection, "dim_region", regions, ["region_id"])
        add_new_dimension_rows(
            connection, "dim_product", weekly_prices[PRODUCT_COLUMNS].drop_duplicates(), PRODUCT_COLUMNS
        )
        add_new_dimension_rows(
            connection, "dim_channel", weekly_prices[CHANNEL_COLUMNS].drop_duplicates(), CHANNEL_COLUMNS
        )
        # The weekly prices are rebuilt from the raw data, so they are replaced.
        ensure_weekly_price_references_dim_date(connection)
        connection.execute("DELETE FROM weekly_price")
        # Every week referenced by a price exists in dim_date before the price (D-095).
        refresh_dim_date(connection, list(weekly_prices["week_start"]))
        insert_rows(connection, "weekly_price", attach_dimension_identifiers(connection, weekly_prices))
        run_id = record_run(connection, started_at, STATUS_LOADED, row_counts)
        # Only the rejections of the latest run are kept; etl_run keeps the counts.
        connection.execute("DELETE FROM rejection")
        insert_rows(connection, "rejection", rejections.assign(run_id=run_id))


# endregion


# region Indicators
def measure_match_coverage(connection: sqlite3.Connection) -> Any:
    """K7: consumer fruit and vegetable keys with a margin, over all such keys.

    Returns (keys with margin, consumer keys).
    """
    return connection.execute(MATCH_COVERAGE_QUERY).fetchone()


# endregion


# region Run
def clean_and_validate_all_sources(
    raw_connection: sqlite3.Connection,
) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """Return (valid rows, rejections, rows read) for both sources together."""
    valid_parts = []
    rejection_parts = []
    rows_read = 0
    for source in SOURCES:
        raw_rows = read_raw_rows(raw_connection, source)
        if raw_rows.empty:
            continue
        clean_rows = clean(raw_rows, source)
        reasons = validate_rows(clean_rows)
        valid_parts.append(clean_rows[reasons == ""])
        rejection_parts.append(build_rejections(raw_rows, reasons, source))
        rows_read += len(raw_rows)
    valid_rows = pd.concat(valid_parts, ignore_index=True)
    # Valid rows always have a region, so the identifier can be a whole number.
    valid_rows["region_id"] = valid_rows["region_id"].astype(int)
    return valid_rows, pd.concat(rejection_parts, ignore_index=True), rows_read


def run_etl(raw_connection: sqlite3.Connection, connection: sqlite3.Connection) -> dict[str, Any]:
    """Run the whole ETL from the raw tables. Returns the counts of the run."""
    started_at = datetime.now().isoformat(timespec="seconds")
    valid_rows, rejections, rows_read = clean_and_validate_all_sources(raw_connection)
    row_counts: dict[str, Any] = {
        "rows_read": rows_read,
        "rows_loaded": len(valid_rows),
        "rows_rejected": len(rejections),
    }
    weekly_prices = apply_business_rules(valid_rows)
    row_counts["weekly_prices"] = len(weekly_prices)

    problems = check_quality(weekly_prices, rows_read, read_previous_rows_read(connection))
    if problems:
        # Nothing is loaded: the previous weekly prices stay untouched.
        row_counts["status"] = STATUS_FAILED
        row_counts["message"] = " | ".join(problems)
        with connection:
            record_run(connection, started_at, STATUS_FAILED, row_counts, row_counts["message"])
        return row_counts

    regions = valid_rows[["region_id", "region"]].drop_duplicates("region_id")
    load(connection, weekly_prices, regions, rejections, started_at, row_counts)
    # The table is rebuilt on every run; compacting keeps the committed file at
    # its smallest size (D-046).
    connection.execute("VACUUM")
    row_counts["status"] = STATUS_LOADED
    row_counts["message"] = ""
    return row_counts


# endregion


# region Entry point
def main() -> int:
    """Load the downloaded files, run the ETL and print a summary.

    Exit code 1 means the quality checks stopped the load.
    """
    raw_connection = open_database()
    for file_name, status, row_count in load_raw_files(raw_connection):
        print(f"{status} | {file_name} | {row_count} rows")
    connection = open_database(DATABASE_FILE, SCHEMA_FILE)
    row_counts = run_etl(raw_connection, connection)
    print(
        f"{row_counts['status']} | read {row_counts['rows_read']}"
        f" | loaded {row_counts['rows_loaded']}"
        f" | rejected {row_counts['rows_rejected']}"
        f" | weekly prices {row_counts['weekly_prices']}"
    )
    if row_counts["status"] == STATUS_FAILED:
        print(f"Quality checks failed, nothing was loaded: {row_counts['message']}")
    else:
        keys_with_margin, consumer_keys = measure_match_coverage(connection)
        print(f"K7 | {keys_with_margin} of {consumer_keys} consumer keys have a margin")
    raw_connection.close()
    connection.close()
    return 1 if row_counts["status"] == STATUS_FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
# endregion
