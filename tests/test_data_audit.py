"""Data audit (D-144): what the panel publishes can be checked against the source.

Invariants of the data warehouse (weekly calendar, unique keys, load counts) and an
independent recomputation of weekly prices from the raw rows of ODEPA. The raw
check needs etl/raw.db, which stays out of the repository (D-020): it runs where
the pipeline runs and is skipped elsewhere.
"""
import random
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import dashboard, queries  # noqa: E402
from etl import etl  # noqa: E402

needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(),
                                    reason="etl/datos.db has not been built")
needs_raw = pytest.mark.skipif(not etl.RAW_DATABASE_FILE.exists(),
                               reason="etl/raw.db is not in the repository (D-020)")
SAMPLE_SIZE = 60


def read(sql, parameters=()):
    return queries.run_sql(sql, parameters=parameters)


# region Weekly calendar and keys
@needs_database
def test_every_week_is_a_monday_and_the_calendar_has_no_gap():
    assert read("SELECT COUNT(*) AS n FROM weekly_price WHERE dayofweek(CAST(week_start AS DATE)) <> 1")["n"][0] == 0
    weeks = pd.to_datetime(read("SELECT week_start FROM dim_date ORDER BY week_start")["week_start"])
    assert (weeks.diff().dropna().dt.days == 7).all()
    missing = read("SELECT COUNT(DISTINCT week_start) AS n FROM weekly_price "
                   "WHERE week_start NOT IN (SELECT week_start FROM dim_date)")["n"][0]
    assert missing == 0


@needs_database
def test_only_the_known_source_gap_leaves_a_week_without_prices():
    """D-042: ODEPA's consumer file has no week 18 of 2022; every other week has both sources."""
    empty = read("""SELECT d.week_start, ch.source FROM dim_date d
                    CROSS JOIN (SELECT DISTINCT source FROM dim_channel) ch
                    WHERE NOT EXISTS (SELECT 1 FROM weekly_price w JOIN dim_channel c USING(channel_id)
                                      WHERE w.week_start = d.week_start AND c.source = ch.source)""")
    assert empty.to_dict("records") == [{"week_start": "2022-05-02", "source": "consumer"}]


@needs_database
def test_one_price_per_week_product_region_channel_and_unit():
    duplicated = read("""SELECT COUNT(*) AS n FROM (SELECT 1 FROM weekly_price
                         GROUP BY week_start, product_id, region_id, channel_id, normalized_unit
                         HAVING COUNT(*) > 1)""")["n"][0]
    assert duplicated == 0
    assert read("SELECT COUNT(*) AS n FROM weekly_price WHERE price <= 0")["n"][0] == 0
    assert read("SELECT COUNT(*) AS n FROM dim_product "
                "WHERE product_group IS NULL OR product_group = ''")["n"][0] == 0


@needs_database
def test_every_row_read_is_loaded_or_rejected_exactly_once():
    runs = read("SELECT rows_read, rows_loaded, rows_rejected FROM etl_run")
    assert (runs["rows_read"] == runs["rows_loaded"] + runs["rows_rejected"]).all()
    latest = runs.iloc[-1]
    assert read("SELECT COUNT(*) AS n FROM rejection")["n"][0] == latest["rows_rejected"]
# endregion


# region Independent recomputation from the raw rows
def normalize(text):
    return " ".join(str(text).replace("\xa0", " ").split())


def to_number(text):
    try:
        return float(str(text).replace(",", "."))
    except ValueError:
        return None


def recompute_weekly_price(raw, row):
    """The weekly price of one panel row, rebuilt from raw.db without the ETL's
    aggregation: volume-weighted for wholesale (RN-07), plain average for consumer
    (RN-09). Only the unit reading (RN-03 to RN-05) is shared with the ETL."""
    monday = pd.Timestamp(row["week_start"])
    if row["source"] == etl.SOURCE_WHOLESALE:
        days = [f"{monday + pd.Timedelta(days=day):%Y-%m-%d}" for day in range(7)]
        rows = pd.read_sql(f"SELECT * FROM raw_wholesale WHERE region_id = ? "
                           f"AND price_date IN ({','.join('?' * 7)})", raw,
                           params=[str(row["region_id"])] + days)
        same = ((rows["product"].map(normalize) == row["product"])
                & (rows["variety"].map(normalize) == row["variety"])
                & (rows["quality"].map(normalize) == row["quality"]))
        unit_column = "sale_unit"
    else:
        rows = pd.read_sql("SELECT * FROM raw_consumer WHERE region_id = ? AND week_start = ?",
                           raw, params=[str(row["region_id"]), row["week_start"][:10]])
        parts = rows["product"].map(normalize).str.split("|")
        keys = parts.map(lambda part: tuple(piece.strip() for piece in part) if len(part) == 3
                         else ("|".join(part), etl.UNSPECIFIED, etl.UNSPECIFIED))
        same = ((keys == (row["product"], row["variety"], row["quality"]))
                & (rows["sales_channel"].map(normalize) == row["channel"]))
        unit_column = "unit"
    prices, weights = [], []
    for raw_row in rows[same].to_dict("records"):
        unit, quantity = etl.convert_unit(normalize(raw_row[unit_column]))
        values = [to_number(raw_row[column]) for column in ("min_price", "max_price", "avg_price")]
        if unit != row["normalized_unit"] or any(value is None or value <= 0 for value in values):
            continue
        weight = to_number(raw_row["volume"]) if row["source"] == etl.SOURCE_WHOLESALE else 1.0
        if not weight or weight <= 0:
            continue
        prices.append(values[2] / quantity)
        weights.append(weight)
    return sum(price * weight for price, weight in zip(prices, weights)) / sum(weights)


@needs_database
@needs_raw
@pytest.mark.parametrize("source", [etl.SOURCE_WHOLESALE, etl.SOURCE_CONSUMER])
def test_weekly_prices_rebuild_exactly_from_the_raw_rows(source):
    panel = read("""SELECT wp.week_start, p.product, p.variety, p.quality, wp.region_id, ch.channel,
                           ch.source, wp.normalized_unit, wp.price
                    FROM weekly_price wp JOIN dim_product p USING(product_id)
                    JOIN dim_channel ch USING(channel_id)
                    WHERE wp.price IS NOT NULL AND ch.source = ?""", (source,))
    sample = panel.iloc[random.Random(144).sample(range(len(panel)), SAMPLE_SIZE)]
    raw = sqlite3.connect(f"file:{etl.RAW_DATABASE_FILE}?mode=ro", uri=True)
    try:
        for row in sample.to_dict("records"):
            assert recompute_weekly_price(raw, row) == pytest.approx(row["price"], rel=1e-9), row
    finally:
        raw.close()
# endregion


# region The Resumen compares the same regions (D-144)
def test_a_national_change_compares_only_the_regions_present_in_both_weeks():
    join = ["product_group", "product", "variety", "quality", "normalized_unit", "channel"]
    key = dict(product_group="Hortalizas", product="Caigua", variety="Sin especificar",
               quality="Primera", normalized_unit="kilo", channel="Mayorista")
    # Santiago does not move; Arica sells only the week before, at a lower price.
    before = pd.DataFrame([dict(key, region="Santiago", price=1000.0, observation_count=5),
                           dict(key, region="Arica", price=400.0, observation_count=3)])
    now = pd.DataFrame([dict(key, region="Santiago", price=1000.0, observation_count=4)])
    plain = pd.DataFrame([dict(key, national_price=1000.0, _previous_price=700.0,
                               variation=1000 / 700 - 1, change_amount=300.0)])
    compared = dashboard.compare_same_regions(plain, now, before, join).iloc[0]
    # The change is like for like; the prices shown stay each week's national price (D-153).
    assert compared["variation"] == 0 and compared["_previous_price"] == 700.0
    assert compared["_same_regions"] == 1
    assert bool(compared["_coverage_changed"])
    # With no region in common there is no valid comparison, never a guessed one.
    alone = dashboard.compare_same_regions(plain, now.assign(region="Arica"),
                                           before[before.region == "Santiago"], join).iloc[0]
    assert pd.isna(alone["variation"])
# endregion


# region What the panel concludes is meaningful (D-146)
def test_a_family_moves_like_its_typical_product_not_like_its_extremes():
    from bi import home_mockup
    rows = [{"product_group": "Frutas", "variation": value} for value in (0.0, 0.0, 0.001, 0.5)]
    [(family, typical, members)] = home_mockup.family_averages(rows)
    assert typical == pytest.approx(0.0005) and len(members) == 4


def test_a_region_is_painted_only_when_its_direction_beats_chance():
    assert dashboard.sign_test_p_value(285, 217) < 0.01
    assert dashboard.sign_test_p_value(107, 104) > 0.5
    key = dict(product_group="Frutas", product="Pera", variety="X", quality="Primera",
               normalized_unit="kilo", channel="Feria libre")
    def week(prices):
        return pd.DataFrame([dict(key, product=f"P{index}", region=region, price=price)
                             for index, (region, price) in enumerate(prices)])
    before = week([("Maule", 100.0)] * 40 + [("Biobío", 100.0)] * 40)
    after = week([("Maule", 110.0)] * 38 + [("Maule", 90.0)] * 2
                 + [("Biobío", 110.0)] * 21 + [("Biobío", 90.0)] * 19)
    states = {row["region"]: row["state"] for row in dashboard.build_regional_movement_model(after, before)}
    assert states == {"Maule": "rise", "Biobío": "mixed"}


def test_an_alert_must_be_unusual_and_material():
    from bi import alerts
    rows = pd.DataFrame({"variation": [0.06, 0.12, 0.12], "usual_variation": [0.0, 0.0, 0.0],
                         "variation_deviation": [0.01, 0.01, 0.1]})
    assert list(alerts.is_price_alert(rows)) == [False, True, False]


# endregion


@needs_database
def test_the_panel_reproduces_the_reference_figures_of_its_week():
    """The target of the migration: same week, same figures (D-153)."""
    sys.path.insert(0, str(Path(__file__).parent))
    import snapshot_figures
    reference = snapshot_figures.read_reference()
    current = snapshot_figures.compute_snapshot()
    if current["week"] != reference["week"]:
        pytest.skip("la base ya tiene otra semana; la referencia es de " + reference["week"])
    # Sums of 800.000 decimals depend on the order of addition: same value to 1e-12.
    current_sums, reference_sums = current.pop("price_sum_by_source"), reference.pop("price_sum_by_source")
    assert current == reference
    assert current_sums.keys() == reference_sums.keys()
    for source, total in reference_sums.items():
        assert current_sums[source] == pytest.approx(total, rel=1e-12)
# endregion
