"""What the panel reads (D-541): the published Base DuckDB, its weekly prices, alerts and indicators, and the
Chile time of the loads. Every read is cached by the version of the base, so a new load is read once.
"""

import contextvars
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import duckdb
import pandas as pd
import streamlit as st

from bi import alerts, channel_latest, control, queries, served_database
from bi.constants import (
    ALL_VALUES,
    CHILE_TIME_ZONE,
    GITHUB_CACHE_SECONDS,
    RUN_HISTORY_COUNT,
    SECRET_GITHUB_TOKEN,
    UNSPECIFIED,
)
from etl import etl

# region Constants
NATIONAL_KEY = ["week_start", "product_group", "product", "variety", "quality", "channel", "normalized_unit"]
# endregion


# region Variables
# D-405: the Dashboard's data, for every channel (the Dashboard itself) or for one channel with its own two latest weeks
# (step 2 of «Semanal», D-494, read from latest_by_source). The scope is set while «Semanal» draws with a channel;
# every reader below keys its cache on it, so «Todos los canales» never shows a channel's numbers, and one code draws both.
PRICE_SCOPE: contextvars.ContextVar[str | None] = contextvars.ContextVar("price_scope", default=None)
# endregion


# region Published database and its reads
@st.cache_resource(show_spinner="Descargando la base de la última carga…")
def ensure_published_database(pointer_text):
    """Once per pointer (D-270): the weekly job commits etl/datos.version, so a new load reruns this."""
    return served_database.ensure_database()


def follow_published_database():
    """Download the database of the latest load when the local one is missing or older; None, or what failed.
    A failed download keeps the local file, if there is one: the panel shows the previous load."""
    pointer = served_database.POINTER_FILE
    try:
        ensure_published_database(pointer.read_text(encoding="utf-8") if pointer.exists() else "")
    except Exception as error:  # no network, or the release is not there yet
        return f"{type(error).__name__}"
    return None


def get_database_version():
    """Changes when the weekly job saves a new database, so cached data is read again."""
    return queries.DATABASE_FILE.stat().st_mtime


def add_display_columns(rows):
    """Add the date and the product key label used by filters and charts."""
    if "week_start" in rows.columns:
        rows["week_start"] = pd.to_datetime(rows["week_start"])
    if {"variety", "normalized_unit"} <= set(rows.columns):
        # The unit is part of the label: one product can be sold by kilo and by unit.
        rows["key_label"] = rows["variety"] + " · " + rows["quality"] + " · $/" + rows["normalized_unit"]
    return rows


@st.cache_data
def read_cached_indicator(query_name, database_version):
    """Rows of one indicator, kept in memory until the database changes."""
    return add_display_columns(queries.run_query(query_name))


def read_indicator(query_name):
    """Rows of one indicator for the current database."""
    return read_cached_indicator(query_name, get_database_version())


@st.cache_data
def read_cached_rows_for_key(query_name, key_items, database_version):
    """Rows of one indicator for one product key, filtered by SQLite (D-050)."""
    return add_display_columns(queries.run_query_for_key(query_name, dict(key_items)))


def read_indicator_for_key(query_name, key):
    """Rows of one indicator for the chosen product key."""
    return read_cached_rows_for_key(query_name, tuple(sorted(key.items())), get_database_version())


def read_week_range():
    """First and last week loaded in the data warehouse, with their years."""
    return read_indicator("quality_week_range").iloc[0]


def read_latest_week():
    """Monday of the latest week with prices: the Dashboard's common week, or a channel's own (D-405)."""
    channel = current_channel()
    if channel is not None:
        return pd.Timestamp(max(read_channel_frame(get_database_version(), channel)["week_start"]))
    return pd.Timestamp(read_week_range()["last_week"])


def current_channel():
    return PRICE_SCOPE.get()


def scoped(name):
    """A key of the Dashboard's state, its own for each channel page."""
    channel = current_channel()
    return name if channel is None else f"{name}@{channel}"


@st.cache_data(show_spinner=False)
def read_channel_frame(database_version, channel):
    """The valid prices of one channel in its own two latest weeks (latest_by_source)."""
    frame = read_latest_by_source(database_version)
    if frame is None:
        return pd.DataFrame(columns=["week_start", "channel", "region", "price"])
    keep = (
        (frame["channel"] == channel) & frame["flag"].isna() & frame["price"].notna() & frame["normalized_unit"].notna()
    )
    return frame[keep].copy()


@st.cache_data(show_spinner=False)
def read_channel_national_prices(database_version, channel):
    """The k6_national_weekly_price rows of one channel: the national price is the plain average of its regions, and
    the change against the week before uses only the regions with a price in both weeks (D-144), as the query does."""
    part = read_channel_frame(database_version, channel)
    national = part.groupby(NATIONAL_KEY, as_index=False)["price"].mean().rename(columns={"price": "national_price"})
    keys = NATIONAL_KEY[1:] + ["region_id"]
    same = []
    weeks = sorted(part["week_start"].unique())
    for before, now in zip(weeks, weeks[1:]):
        if (pd.Timestamp(now) - pd.Timestamp(before)).days != 7:
            continue
        matched = channel_latest.same_package_matches(
            part[part["week_start"] == now].merge(
                part[part["week_start"] == before][keys + ["price", "observation_count"]],
                on=keys,
                suffixes=("", "_before"),
            )
        )
        grouped = matched.groupby(NATIONAL_KEY[1:], as_index=False).agg(
            same_region_price=("price", "mean"),
            same_region_previous_price=("price_before", "mean"),
            same_region_quotes=("observation_count", "sum"),
            same_region_previous_quotes=("observation_count_before", "sum"),
        )
        same.append(grouped.assign(week_start=now))
    columns = ["same_region_price", "same_region_previous_price", "same_region_quotes", "same_region_previous_quotes"]
    if same:
        national = national.merge(pd.concat(same), on=NATIONAL_KEY, how="left")
    else:
        national = national.assign(**{column: float("nan") for column in columns})
    return add_display_columns(national)


@st.cache_data(show_spinner=False)
def read_channel_week_snapshot(database_version, channel, week):
    """The k3_regional_index rows of one channel and week."""
    part = read_channel_frame(database_version, channel)
    part = part[part["week_start"] == week]
    national = part.groupby(NATIONAL_KEY)["price"].transform("mean")
    snapshot = part.assign(national_price=national, regional_index=part["price"] / national)
    columns = NATIONAL_KEY[:6] + [
        "region",
        "normalized_unit",
        "price",
        "national_price",
        "regional_index",
        "observation_count",
    ]
    return add_display_columns(snapshot[columns].copy())


def describe_loaded_years():
    """'año 2026' or 'años 2022 a 2026', from the weeks really loaded in datos.db."""
    week_range = read_week_range()
    if week_range["first_year"] == week_range["last_year"]:
        return f"año {week_range['last_year']}"
    return f"años {week_range['first_year']} a {week_range['last_year']}"


def read_cached_price_alerts(database_version):
    """K6 alerts of every week; on a channel page, only that channel's (D-405)."""
    found = read_cached_price_alerts_all(database_version)
    channel = current_channel()
    return found if channel is None else found[found["channel"] == channel]


@st.cache_data
def read_cached_price_alerts_all(database_version):
    """K6 alerts of every week, computed once per database."""
    prices = queries.run_query("k6_national_weekly_price")
    return add_display_columns(alerts.find_price_alerts(prices))


def read_price_alerts():
    """K6 alerts for the current database."""
    return read_cached_price_alerts(get_database_version())


@st.cache_data(show_spinner=False)
def read_cached_region_series(database_version, region):
    """D-499: what «Semanal» needs of one region under the rule of K6: its alerts, and the weekly changes behind the
    little lines of its families. Read once per region, and only the result stays in memory."""
    prices = queries.run_query_for_region("k6_regional_weekly_price", region)
    changes = alerts.add_weekly_variation(prices)
    changes = changes.loc[changes["variation"].notna(), ["week_start", "product_group", "channel", "variation"]]
    return add_display_columns(alerts.find_price_alerts(prices)), changes


def read_place_alerts(region=None):
    """D-499: the alerts of the place chosen in step 1: K6 with all of Chile, the same rule on its own prices in a
    region; on a channel page, that channel's (D-405)."""
    if region in (None, ALL_VALUES):
        return read_price_alerts()
    found = read_cached_region_series(get_database_version(), region)[0]
    channel = current_channel()
    return found if channel is None else found[found["channel"] == channel]


@st.cache_data
def read_cached_match_coverage(database_version):
    """K7, computed once per database: its query crosses the whole price table."""
    connection = queries.open_database()
    coverage = etl.measure_match_coverage(connection)
    connection.close()
    return coverage


def read_match_coverage():
    """K7 as (keys with margin, consumer keys)."""
    return read_cached_match_coverage(get_database_version())


def read_latest_run():
    """Latest ETL run recorded in the database (one row)."""
    return read_indicator("quality_runs").iloc[0]


def describe_product(row):
    """'Tomate Larga vida · Primera', leaving out parts ODEPA does not specify."""
    description = row["product"]
    if row["variety"] != UNSPECIFIED:
        description += f" {row['variety']}"
    if row["quality"] != UNSPECIFIED:
        description += f" · {row['quality']}"
    return description


@st.cache_data(show_spinner=False)
def read_latest_by_source(database_version):
    """D-365: the last two weeks of each source; None while the served base is older than the table."""
    try:
        return queries.run_sql("SELECT * FROM latest_by_source")
    except duckdb.Error:
        return None


# endregion


# region Time
def to_chile_time(moment):
    """A UTC datetime in Chilean time; a fixed UTC-3 if the time zone is missing."""
    try:
        return moment.astimezone(ZoneInfo(CHILE_TIME_ZONE))
    except Exception:  # time zone database not installed
        return moment.astimezone(timezone(timedelta(hours=-3)))


def format_chile_time(moment):
    """'12-10-2026 05:52' in Chilean time."""
    return f"{to_chile_time(moment):%d-%m-%Y %H:%M}"


def parse_run_start(started_at):
    """The ETL stores its start in UTC as '2026-10-12T08:52:08'."""
    return datetime.fromisoformat(started_at).replace(tzinfo=timezone.utc)


# endregion


# region Overview reads
def read_cached_national_prices(database_version):
    """Every national price series, every week (K6); on a channel page, that channel's own weeks (D-405)."""
    channel = current_channel()
    if channel is not None:
        return read_channel_national_prices(database_version, channel)
    return read_cached_national_prices_all(database_version)


@st.cache_data
def read_cached_national_prices_all(database_version):
    """Every national price series, every week (K6): read once, filtered in memory, so a
    click on a new product answers without a query (D-069)."""
    return add_display_columns(queries.run_query("k6_national_weekly_price"))


def read_cached_all_variations(database_version):
    """Weekly change of every national price series (K6 base); on a channel page, that channel's (D-405)."""
    return read_cached_all_variations_in(database_version, current_channel())


@st.cache_data
def read_cached_all_variations_in(database_version, channel):
    """Weekly change of every national price series, every week (K6 base)."""
    if channel is None:
        prices = alerts.add_weekly_variation(queries.run_query("k6_national_weekly_price"))
    else:
        prices = alerts.add_weekly_variation(read_channel_national_prices(database_version, channel))
    return add_display_columns(prices[prices["variation"].notna()].copy())


# endregion


# region GitHub reads
def get_secret(name):
    """A dashboard secret, or None when it is not configured."""
    try:
        return st.secrets.get(name)
    except Exception:  # no secrets file at all
        return None


@st.cache_resource
def get_last_github_answers():
    """Last good answers of GitHub, shared by every visitor, used when GitHub fails."""
    return {}


@st.cache_data(ttl=GITHUB_CACHE_SECONDS, show_spinner=False)
def fetch_pipeline_runs():
    """Latest runs from GitHub. A failure raises, and is not kept in the cache."""
    token = get_secret(SECRET_GITHUB_TOKEN)
    runs = control.list_workflow_runs(token, RUN_HISTORY_COUNT)
    return control.mark_simulated_failures(runs, token)


def read_pipeline_runs():
    """(latest runs, why GitHub failed or ""). On a failure, the last good answer."""
    last_answers = get_last_github_answers()
    try:
        runs = fetch_pipeline_runs()
    except Exception as error:  # GitHub unreachable or refused
        return last_answers.get("runs", []), control.describe_github_error(error)
    last_answers["runs"] = runs
    return runs, ""


@st.cache_data(ttl=3600, show_spinner=False)
def read_cached_token_expiration(token):
    """Expiration of the token, asked to GitHub at most once an hour."""
    return control.read_token_expiration(token)


# endregion
