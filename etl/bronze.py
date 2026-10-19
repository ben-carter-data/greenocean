"""Bronze layer in Parquet (D-154): the raw rows of ODEPA, exactly as read.

`etl/raw.db` keeps being the landing zone of the agent's CSV files (load_raw_files);
this module copies its two tables to Parquet, one file per source and year, so the
dbt project reads a standard data-lake format that any warehouse can read too.
Columns and types are those of raw.db: nothing is cleaned here.
"""
import sqlite3
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl  # noqa: E402

BRONZE_DIR = etl.BASE_DIR / "bronze"
BRONZE_TABLES = {etl.SOURCE_WHOLESALE: "odepa_wholesale", etl.SOURCE_CONSUMER: "odepa_consumer"}


def export_source(connection, source, bronze_dir=BRONZE_DIR):
    """Write bronze/<table>/file_year=<year>/data.parquet for every year of one source.
    Returns {year: rows}."""
    table = etl.RAW_TABLE_BY_SOURCE[source]
    columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
    written = {}
    years = [row[0] for row in connection.execute(f"SELECT DISTINCT file_year FROM {table} ORDER BY 1")]
    for year in years:
        cursor = connection.execute(f"SELECT * FROM {table} WHERE file_year = ? ORDER BY rowid", (year,))
        rows = cursor.fetchall()
        # file_year is the partition key; every other column stays text, as in raw.db.
        data = {column: [row[index] for row in rows] for index, column in enumerate(columns)
                if column != "file_year"}
        schema = pa.schema([(column, pa.string()) for column in data])
        folder = bronze_dir / BRONZE_TABLES[source] / f"file_year={year}"
        folder.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.table(data, schema=schema), folder / "data.parquet", compression="zstd")
        written[int(year)] = len(rows)
    return written


def main():
    connection = sqlite3.connect(f"file:{etl.RAW_DATABASE_FILE}?mode=ro", uri=True)
    try:
        for source in etl.SOURCES:
            for year, count in export_source(connection, source).items():
                print(f"BRONZE | {BRONZE_TABLES[source]} | {year} | {count} filas")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
