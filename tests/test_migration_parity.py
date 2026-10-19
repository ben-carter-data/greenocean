"""Parity between the Python ETL (SQLite, backup) and dbt (DuckDB, panel) (D-154).

The panel moved to DuckDB only after this comparison came out identical; it runs
again every week while both databases are written.
"""
import json
import sqlite3
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl  # noqa: E402

SQLITE_FILE = etl.DATABASE_FILE
DUCKDB_FILE = etl.BASE_DIR / "datos.duckdb"
pytestmark = pytest.mark.skipif(not (SQLITE_FILE.exists() and DUCKDB_FILE.exists()),
                                reason="faltan etl/datos.db o etl/datos.duckdb")
PRICES = """SELECT w.week_start, p.product_group, p.product, p.variety, p.quality, w.region_id,
                   c.channel, c.source, w.normalized_unit, w.price, w.volume, w.observation_count, w.flag
            FROM weekly_price w JOIN dim_product p USING(product_id) JOIN dim_channel c USING(channel_id)"""
KEY = ["week_start", "product_group", "product", "variety", "quality", "region_id", "channel", "source",
       "normalized_unit"]


def read_both(sql):
    with sqlite3.connect(f"file:{SQLITE_FILE}?mode=ro", uri=True) as connection:
        old = pd.read_sql(sql, connection)
    with duckdb.connect(str(DUCKDB_FILE), read_only=True) as connection:
        new = connection.execute(sql).df()
    return old, new


def prepare(rows):
    rows = rows.copy()
    rows["normalized_unit"] = rows["normalized_unit"].fillna("∅")
    rows["flag"] = rows["flag"].fillna("∅")
    rows["region_id"] = rows["region_id"].astype(int)
    rows["observation_count"] = rows["observation_count"].astype(int)
    return rows


def test_every_weekly_price_has_the_same_key_flag_count_and_price():
    old, new = (prepare(rows) for rows in read_both(PRICES))
    merged = old.merge(new, on=KEY, how="outer", suffixes=("_etl", "_dbt"), indicator=True)
    assert (merged["_merge"] == "both").all(), merged[merged["_merge"] != "both"].head()
    assert (merged["flag_etl"] == merged["flag_dbt"]).all()
    assert (merged["observation_count_etl"] == merged["observation_count_dbt"]).all()
    assert (merged["price_etl"].isna() == merged["price_dbt"].isna()).all()
    priced = merged.dropna(subset=["price_etl"])
    assert ((priced["price_etl"] - priced["price_dbt"]).abs() <= priced["price_etl"].abs() * 1e-9).all()
    volume = merged.dropna(subset=["volume_etl"])
    assert ((volume["volume_etl"] - volume["volume_dbt"]).abs() <= 1e-6).all()


@pytest.mark.parametrize("table", ["dim_region", "dim_date"])
def test_dimensions_are_identical(table):
    old, new = read_both(f"SELECT * FROM {table} ORDER BY 1")
    assert old.astype(str).equals(new.astype(str))


def test_rejected_rows_are_the_same_rows_with_the_same_reason():
    old, new = read_both("SELECT source, reason, original_row FROM rejection")
    canonical = lambda rows: sorted((row.source, row.reason, json.dumps(json.loads(row.original_row),
                                     sort_keys=True, ensure_ascii=False)) for row in rows.itertuples())
    assert canonical(old) == canonical(new)
