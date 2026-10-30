"""Weekly load with dbt and DuckDB (D-154).

1. The agent's CSV files go into the landing database raw.db (etl.load_raw_files).
2. raw.db is copied to the bronze layer in Parquet (etl/bronze.py).
3. dbt builds and tests every model in a work database that is never committed
   (etl/warehouse_build.duckdb). If a model or a test fails, nothing else happens.
4. RN-14 / D-029: a load that reads far fewer rows than the previous one is refused.
5. The tables the panel reads are copied to a fresh, compact file, the run is
   recorded in etl_run and only then the file replaces etl/datos.duckdb.

On any failure the published database stays as it was; the failed run is recorded.
"""

from __future__ import annotations

from typing import Any, cast

import json
import os
import sqlite3
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import bronze, etl, ine  # noqa: E402

PROJECT_DIR = etl.BASE_DIR.parent
DBT_DIR = PROJECT_DIR / "dbt"
WORK_DATABASE_FILE = etl.BASE_DIR / "warehouse_build.duckdb"
SERVING_DATABASE_FILE = etl.BASE_DIR / "datos.duckdb"
# The tables of the panel, in the order they are copied.
SERVING_TABLES = [
    "dim_product",
    "dim_region",
    "dim_channel",
    "dim_date",
    "weekly_price",
    "rejection",
    "ipc_monthly",
    "ipc_weekly",
    "ine_ipc_source",
]
DBT_TARGET_DIR = DBT_DIR / "target"
# The lineage and the test results of the last dbt build travel with the serving file:
# dbt/target is not committed, and the panel draws its DAG and quality matrix from them.
DBT_NODE_COLUMNS = [
    "unique_id",
    "name",
    "resource_type",
    "layer",
    "materialized",
    "depends_on",
    "test_type",
    "column_name",
    "description",
]
ETL_RUN_SCHEMA = """CREATE TABLE IF NOT EXISTS etl_run (
    run_id INTEGER PRIMARY KEY, started_at VARCHAR NOT NULL, status VARCHAR NOT NULL,
    rows_read INTEGER NOT NULL, rows_loaded INTEGER NOT NULL, rows_rejected INTEGER NOT NULL,
    message VARCHAR)"""


def prepare_ipc(serving_file: Path = SERVING_DATABASE_FILE) -> None:
    """IPC of the INE into the bronze layer (D-155). If the INE does not answer, the
    rows kept in the published database rebuild it: the load never stops for the IPC."""
    if ine.main() == 0:
        return
    if not serving_file.exists():
        raise RuntimeError("Sin IPC: el INE no respondió y no hay una base publicada con sus filas")
    with duckdb.connect(str(serving_file), read_only=True) as connection:
        rows = connection.execute(
            "SELECT file, year, month, index_value, monthly_change FROM ine_ipc_source"
        ).fetchall()
    files: dict[str, list[dict[str, str]]] = {}
    for file, year, month, index_value, monthly_change in rows:
        files.setdefault(file, []).append(
            {"year": year, "month": month, "index_value": index_value, "monthly_change": monthly_change}
        )
    ine.write_bronze(files)
    print("IPC | bronce reconstruido desde la base publicada")


def read_run_history(
    serving_file: Path = SERVING_DATABASE_FILE, legacy_file: Path = etl.DATABASE_FILE
) -> list[tuple[Any, ...]]:
    """Every recorded run: from the serving DuckDB, or the SQLite history on the first run."""
    columns = "run_id, started_at, status, rows_read, rows_loaded, rows_rejected, message"
    if serving_file.exists():
        with duckdb.connect(str(serving_file), read_only=True) as connection:
            return connection.execute(f"SELECT {columns} FROM etl_run ORDER BY run_id").fetchall()
    if legacy_file.exists():
        with sqlite3.connect(legacy_file) as connection:
            return connection.execute(f"SELECT {columns} FROM etl_run ORDER BY run_id").fetchall()
    return []


def run_dbt(run_id: int, dbt_command: str | None = None) -> tuple[bool, str]:
    """dbt build (models and tests) in the work database. Returns (ok, last output lines)."""
    command = (dbt_command or os.environ.get("DBT_BIN", "dbt")).split() + [
        "build",
        "--profiles-dir",
        ".",
        "--vars",
        f"{{run_id: {run_id}}}",
    ]
    environment = dict(os.environ, GREENOCEAN_DUCKDB=str(WORK_DATABASE_FILE))
    result = subprocess.run(command, cwd=DBT_DIR, env=environment, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip().splitlines()
    return result.returncode == 0, "\n".join(output[-15:])


def read_last_weeks(work_file: Path = WORK_DATABASE_FILE) -> dict[str, str]:
    """D-356: the last week each source published, before the cut to the week complete in both."""
    with duckdb.connect(str(work_file), read_only=True) as connection:
        rows = connection.execute(
            "SELECT source, strftime(max(week_start), '%Y-%m-%d') FROM int_prices__weekly GROUP BY source"
        ).fetchall()
    return {str(source): str(week) for source, week in rows}


def count_rows(work_file: Path = WORK_DATABASE_FILE) -> tuple[int, int, int]:
    """(read, loaded, rejected) of the build, as dbt validated them (RNF-05)."""
    with duckdb.connect(str(work_file), read_only=True) as connection:
        # An aggregate query always returns one row; the stubs of the CI's DuckDB type it as «tuple | None».
        return cast(
            tuple[int, int, int],
            connection.execute(
                "SELECT count(*), count(*) FILTER (WHERE reason IS NULL), "
                "count(*) FILTER (WHERE reason IS NOT NULL) FROM int_prices__validated"
            ).fetchone(),
        )


def read_dbt_artifacts(target_dir: Path = DBT_TARGET_DIR) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    """(nodes, results) of the last dbt build: models, sources and tests with their
    dependencies, and the status of each one. Empty lists if dbt left no artifacts."""
    try:
        manifest = json.loads((target_dir / "manifest.json").read_text(encoding="utf-8"))
        run_results = json.loads((target_dir / "run_results.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], []
    nodes = []
    for unique_id, node in list(manifest["nodes"].items()) + list(manifest["sources"].items()):
        kind = node["resource_type"]
        if kind not in ("model", "test", "source"):
            continue
        layer = "bronze" if kind == "source" else node["fqn"][1] if kind == "model" and len(node["fqn"]) > 2 else ""
        nodes.append(
            (
                unique_id,
                node["name"],
                kind,
                layer,
                node.get("config", {}).get("materialized", ""),
                json.dumps(node.get("depends_on", {}).get("nodes", [])),
                (node.get("test_metadata") or {}).get("name", "singular" if kind == "test" else ""),
                node.get("column_name") or "",
                node.get("description") or "",
            )
        )
    generated_at = run_results["metadata"]["generated_at"][:19]
    results = [
        (
            result["unique_id"],
            result["status"],
            float(result.get("execution_time") or 0),
            int(result.get("failures") or 0),
            generated_at,
        )
        for result in run_results["results"]
    ]
    return nodes, results


def write_dbt_artifacts(
    connection: duckdb.DuckDBPyConnection, nodes: list[tuple[Any, ...]], results: list[tuple[Any, ...]]
) -> None:
    connection.execute("CREATE TABLE dbt_node (" + ", ".join(f"{column} VARCHAR" for column in DBT_NODE_COLUMNS) + ")")
    connection.execute(
        "CREATE TABLE dbt_result (unique_id VARCHAR, status VARCHAR, execution_time DOUBLE, "
        "failures INTEGER, generated_at VARCHAR)"
    )
    if nodes:
        connection.executemany(f"INSERT INTO dbt_node VALUES ({', '.join('?' for _ in DBT_NODE_COLUMNS)})", nodes)
    if results:
        connection.executemany("INSERT INTO dbt_result VALUES (?, ?, ?, ?, ?)", results)


def write_serving_database(
    history: list[tuple[Any, ...]],
    run: tuple[Any, ...],
    work_file: Path = WORK_DATABASE_FILE,
    serving_file: Path = SERVING_DATABASE_FILE,
    artifacts: tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]] | None = None,
) -> None:
    """A fresh, compact copy of the panel's tables plus etl_run, swapped in at the end."""
    temporary = serving_file.with_suffix(".duckdb.tmp")
    temporary.unlink(missing_ok=True)
    with duckdb.connect(str(temporary)) as connection:
        connection.execute(f"ATTACH '{work_file}' AS work (READ_ONLY)")
        for table in SERVING_TABLES:
            connection.execute(f"CREATE TABLE {table} AS SELECT * FROM work.main.{table}")
        connection.execute("DETACH work")
        write_dbt_artifacts(connection, *(artifacts if artifacts is not None else read_dbt_artifacts()))
        connection.execute(ETL_RUN_SCHEMA)
        connection.executemany("INSERT INTO etl_run VALUES (?, ?, ?, ?, ?, ?, ?)", history + [run])
        connection.execute("CHECKPOINT")
    os.replace(temporary, serving_file)


def record_failed_run(
    history: list[tuple[Any, ...]], run: tuple[Any, ...], serving_file: Path = SERVING_DATABASE_FILE
) -> None:
    """Keep the published tables; only add the failed run to etl_run."""
    if not serving_file.exists():
        return
    with duckdb.connect(str(serving_file)) as connection:
        connection.execute(ETL_RUN_SCHEMA)
        connection.execute("INSERT INTO etl_run VALUES (?, ?, ?, ?, ?, ?, ?)", run)


def main(dbt_command: str | None = None, load_raw: bool = True, record: bool = True) -> int:
    """record=False (--local): a development build keeps the published run history as it is."""
    started_at = datetime.now().isoformat(timespec="seconds")
    if load_raw:
        with etl.open_database() as raw_connection:
            for file_name, status, row_count in etl.load_raw_files(raw_connection):
                print(f"{status} | {file_name} | {row_count} filas")
    raw_connection = sqlite3.connect(f"file:{etl.RAW_DATABASE_FILE}?mode=ro", uri=True)
    try:
        for source in etl.SOURCES:
            bronze.export_source(raw_connection, source)
    finally:
        raw_connection.close()
    prepare_ipc()
    history = read_run_history()
    run_id = max((row[0] for row in history), default=0) + 1
    ok, output = run_dbt(run_id, dbt_command)
    if not ok:
        record_failed_run(history, (run_id, started_at, etl.STATUS_FAILED, 0, 0, 0, "dbt build: " + output[-500:]))
        print(output)
        return 1
    rows_read, rows_loaded, rows_rejected = count_rows()
    # D-356: a source more than two weeks behind stops the load (an urgent alert in the panel); a recent week only
    # one source has published is held back by dbt and named in the run's message.
    last_weeks = read_last_weeks()
    late = etl.late_source_problems(last_weeks, date.today())
    if late:
        message = " | ".join(late)
        record_failed_run(
            history, (run_id, started_at, etl.STATUS_FAILED, rows_read, rows_loaded, rows_rejected, message)
        )
        print(message)
        return 1
    previous = next((row[3] for row in reversed(history) if row[2] == etl.STATUS_LOADED), None)
    if previous and rows_read < previous * etl.MINIMUM_ROWS_RATIO:
        message = f"{etl.PROBLEM_TOO_FEW_ROWS}: read {rows_read} rows, the previous successful run read {previous}"
        record_failed_run(
            history, (run_id, started_at, etl.STATUS_FAILED, rows_read, rows_loaded, rows_rejected, message)
        )
        print(message)
        return 1
    if record:
        write_serving_database(
            history,
            (
                run_id,
                started_at,
                etl.STATUS_LOADED,
                rows_read,
                rows_loaded,
                rows_rejected,
                etl.held_back_notice(last_weeks),
            ),
        )
    else:
        write_serving_database(history[:-1], history[-1])
        with duckdb.connect(str(SERVING_DATABASE_FILE)) as connection:
            connection.execute("UPDATE rejection SET run_id = ?", [history[-1][0]])
    print(
        f"LOADED | leídas {rows_read} | cargadas {rows_loaded} | rechazadas {rows_rejected}"
        f" | {SERVING_DATABASE_FILE.name} {SERVING_DATABASE_FILE.stat().st_size / 1e6:.1f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(record="--local" not in sys.argv))
