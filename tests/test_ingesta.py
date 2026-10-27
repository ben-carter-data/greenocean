"""The ingestion modules on their own (D-323): the bronze copy of raw.db, the IPC of the INE and the steps of the weekly
load, each with small files made here, so they run without the network, without dbt and without the real databases.
They add tests only: the logic of the load does not change."""

import json
import sqlite3

import duckdb
import pyarrow.parquet as pq
import pytest

from etl import bronze, etl, ine, pipeline

INE_TEXT = (
    '"Año";"Mes";"División";"Grupo";"Índice";"Variación Mensual (%)"\n'
    '"2024";"1";"1";"";"101,5";"0,4"\n'
    '"2024";"1";"1";"1.1";"99,0";"0,1"\n'
    '"2024";"2";"1";"";"102,0";"0,5"\n'
    '"2024";"2";"2";"";"110,0";"1,0"\n'
)


def raw_database(path):
    connection = sqlite3.connect(path)
    for table in etl.RAW_TABLE_BY_SOURCE.values():
        connection.execute(f"CREATE TABLE {table} (product TEXT, price TEXT, file_year INTEGER)")
        connection.executemany(
            f"INSERT INTO {table} VALUES (?, ?, ?)",
            [("Lechuga", "500", 2025), ("Papa", "800", 2025), ("Lechuga", "650", 2026)],
        )
    connection.commit()
    return connection


# region bronze
def test_d323_bronze_writes_one_parquet_per_source_and_year_with_every_column_as_text(tmp_path):
    connection = raw_database(tmp_path / "raw.db")
    written = bronze.export_source(connection, etl.SOURCE_WHOLESALE, bronze_dir=tmp_path)
    assert written == {2025: 2, 2026: 1}
    table = pq.read_table(tmp_path / "odepa_wholesale" / "file_year=2025" / "data.parquet")
    assert table.column_names == ["product", "price"] and table.num_rows == 2
    assert all(str(field.type) == "string" for field in table.schema)
    assert table.column("price").to_pylist() == ["500", "800"]  # kept exactly as read, in order


def test_d323_bronze_main_exports_both_sources_from_raw_db(tmp_path, monkeypatch, capsys):
    raw_database(tmp_path / "raw.db").close()
    monkeypatch.setattr(etl, "RAW_DATABASE_FILE", tmp_path / "raw.db")
    monkeypatch.setattr(bronze.export_source, "__defaults__", (tmp_path / "bronze",))
    bronze.main()
    for table in bronze.BRONZE_TABLES.values():
        assert (tmp_path / "bronze" / table / "file_year=2026" / "data.parquet").exists()
    assert "BRONZE | odepa_consumer | 2025 | 2 filas" in capsys.readouterr().out


# endregion


# region INE
def test_d323_ine_keeps_only_the_food_division_itself_as_published():
    rows = ine.parse_rows(INE_TEXT, "base_2023")
    assert rows == [
        {"file": "base_2023", "year": "2024", "month": "1", "index_value": "101,5", "monthly_change": "0,4"},
        {"file": "base_2023", "year": "2024", "month": "2", "index_value": "102,0", "monthly_change": "0,5"},
    ]


class FakeResponse:
    def __init__(self, text):
        self.content = text.encode("latin-1")

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, text):
        self.text, self.urls = text, []

    def get(self, url, timeout, headers):
        self.urls.append(url)
        return FakeResponse(self.text)


def test_d323_ine_downloads_both_files_and_refuses_a_file_without_the_division():
    session = FakeSession(INE_TEXT)
    files = ine.download(session)
    assert set(files) == set(ine.INE_FILES) and session.urls == list(ine.INE_FILES.values())
    with pytest.raises(ValueError):
        ine.download(FakeSession('"Año";"Mes";"División";"Grupo";"Índice"\n"2024";"1";"2";"";"110"\n'))


def test_d323_ine_writes_its_bronze_and_main_keeps_the_previous_one_when_the_ine_fails(tmp_path, monkeypatch, capsys):
    files = {"base_2023": ine.parse_rows(INE_TEXT, "base_2023")}
    ine.write_bronze(files, bronze_dir=tmp_path)
    table = pq.read_table(tmp_path / ine.BRONZE_TABLE / "file=base_2023" / "data.parquet")
    assert table.column("index_value").to_pylist() == ["101,5", "102,0"]
    monkeypatch.setattr(ine.bronze, "BRONZE_DIR", tmp_path)
    monkeypatch.setattr(ine, "download", lambda: (_ for _ in ()).throw(ConnectionError("sin red")))
    assert ine.main() == 0 and "se usa el último bronce disponible" in capsys.readouterr().out
    monkeypatch.setattr(ine.bronze, "BRONZE_DIR", tmp_path / "vacio")
    assert ine.main() == 1
    monkeypatch.setattr(ine, "download", lambda: files)
    monkeypatch.setattr(ine.write_bronze, "__defaults__", (tmp_path / "nuevo",))
    assert ine.main() == 0 and (tmp_path / "nuevo" / ine.BRONZE_TABLE / "file=base_2023" / "data.parquet").exists()


# endregion


# region pipeline
RUN = (1, "2026-10-20T12:00:00", etl.STATUS_LOADED, 10, 9, 1, "")


def test_d323_the_run_history_comes_from_the_served_database_then_the_old_sqlite_then_nothing(tmp_path):
    served, legacy = tmp_path / "datos.duckdb", tmp_path / "datos.db"
    assert pipeline.read_run_history(served, legacy) == []
    with sqlite3.connect(legacy) as connection:
        connection.execute(pipeline.ETL_RUN_SCHEMA)
        connection.execute("INSERT INTO etl_run VALUES (?, ?, ?, ?, ?, ?, ?)", RUN)
    assert pipeline.read_run_history(served, legacy) == [RUN]
    with duckdb.connect(str(served)) as connection:
        connection.execute(pipeline.ETL_RUN_SCHEMA)
        connection.execute("INSERT INTO etl_run VALUES (?, ?, ?, ?, ?, ?, ?)", RUN[:1] + RUN[1:])
    assert pipeline.read_run_history(served, legacy)[0][0] == 1


def test_d323_run_dbt_says_whether_the_build_passed():
    assert pipeline.run_dbt(3, dbt_command="true")[0] is True
    assert pipeline.run_dbt(3, dbt_command="false")[0] is False


def work_database(path):
    with duckdb.connect(str(path)) as connection:
        for table in pipeline.SERVING_TABLES:
            connection.execute(f"CREATE TABLE {table} (value INTEGER)")
            connection.execute(f"INSERT INTO {table} VALUES (1)")
        connection.execute("CREATE TABLE int_prices__validated (reason VARCHAR)")
        connection.execute("INSERT INTO int_prices__validated VALUES (NULL), (NULL), ('precio cero')")


def test_d323_rows_are_counted_as_dbt_validated_them(tmp_path):
    work_database(tmp_path / "work.duckdb")
    assert pipeline.count_rows(tmp_path / "work.duckdb") == (3, 2, 1)


def test_d323_dbt_artifacts_become_the_nodes_and_results_the_panel_reads(tmp_path):
    assert pipeline.read_dbt_artifacts(tmp_path) == ([], [])
    manifest = {
        "nodes": {
            "model.p.stg": {
                "resource_type": "model",
                "name": "stg",
                "fqn": ["p", "staging", "stg"],
                "config": {"materialized": "view"},
                "depends_on": {"nodes": ["source.p.raw"]},
            },
            "test.p.t": {"resource_type": "test", "name": "t", "fqn": ["p", "t"], "column_name": "id"},
            "seed.p.s": {"resource_type": "seed", "name": "s", "fqn": ["p", "s"]},
        },
        "sources": {"source.p.raw": {"resource_type": "source", "name": "raw", "fqn": ["p", "raw"]}},
    }
    results = {
        "metadata": {"generated_at": "2026-10-20T15:55:00.123Z"},
        "results": [
            {"unique_id": "model.p.stg", "status": "success", "execution_time": 0.5},
            {"unique_id": "test.p.t", "status": "pass", "failures": 0},
        ],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "run_results.json").write_text(json.dumps(results))
    nodes, statuses = pipeline.read_dbt_artifacts(tmp_path)
    by_id = {node[0]: node for node in nodes}
    assert set(by_id) == {"model.p.stg", "test.p.t", "source.p.raw"}  # seeds stay out
    assert (
        by_id["model.p.stg"][3] == "staging"
        and by_id["source.p.raw"][3] == "bronze"
        and by_id["test.p.t"][6] == "singular"
    )
    assert statuses == [
        ("model.p.stg", "success", 0.5, 0, "2026-10-20T15:55:00"),
        ("test.p.t", "pass", 0.0, 0, "2026-10-20T15:55:00"),
    ]


def test_d323_the_served_database_is_written_whole_and_a_failed_run_only_adds_its_row(tmp_path):
    work, served = tmp_path / "work.duckdb", tmp_path / "datos.duckdb"
    work_database(work)
    pipeline.write_serving_database([], RUN, work_file=work, serving_file=served, artifacts=([], []))
    with duckdb.connect(str(served), read_only=True) as connection:
        tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
        assert set(pipeline.SERVING_TABLES) | {"etl_run", "dbt_node", "dbt_result"} <= tables
        assert connection.execute("SELECT count(*) FROM etl_run").fetchone()[0] == 1
    failed = (2, "2026-10-27T12:00:00", etl.STATUS_FAILED, 0, 0, 0, "dbt build: error")
    pipeline.record_failed_run([RUN], failed, serving_file=served)
    with duckdb.connect(str(served), read_only=True) as connection:
        assert connection.execute("SELECT status FROM etl_run ORDER BY run_id").fetchall() == [("LOADED",), ("FAILED",)]
        assert (
            connection.execute("SELECT count(*) FROM weekly_price").fetchone()[0] == 1
        )  # the tables stay as they were
    pipeline.record_failed_run([RUN], failed, serving_file=tmp_path / "no-existe.duckdb")  # nothing to record into


def test_d323_the_ipc_is_rebuilt_from_the_served_database_when_the_ine_does_not_answer(tmp_path, monkeypatch):
    served = tmp_path / "datos.duckdb"
    with duckdb.connect(str(served)) as connection:
        connection.execute(
            "CREATE TABLE ine_ipc_source (file VARCHAR, year VARCHAR, month VARCHAR, index_value VARCHAR, monthly_change VARCHAR)"
        )
        connection.execute("INSERT INTO ine_ipc_source VALUES ('base_2023', '2024', '1', '101,5', '0,4')")
    written = {}
    monkeypatch.setattr(pipeline.ine, "main", lambda: 1)
    monkeypatch.setattr(pipeline.ine, "write_bronze", lambda files: written.update(files))
    pipeline.prepare_ipc(served)
    assert written == {"base_2023": [{"year": "2024", "month": "1", "index_value": "101,5", "monthly_change": "0,4"}]}
    with pytest.raises(RuntimeError):
        pipeline.prepare_ipc(tmp_path / "no-existe.duckdb")
    monkeypatch.setattr(pipeline.ine, "main", lambda: 0)
    assert pipeline.prepare_ipc(tmp_path / "no-existe.duckdb") is None  # the INE answered: nothing to rebuild


# endregion


# region profile of the downloaded years (T-27)
def test_d323_the_year_report_prints_each_fact_against_the_reference_year(capsys):
    from etl import profile_years

    profile = {
        "rows_read": 10,
        "rejections": {"NON_POSITIVE_PRICE": 2},
        "week_count": 3,
        "first_week": "2025-01-06",
        "last_week": "2025-01-20",
        "missing_weeks": [],
        "unknown_regions": [],
        "unknown_channels": ["Kiosco"],
        "unit_shares": {"kilo": 0.75, "unidad": 0.25},
        "units": {"$/kilo", "$/caja 10 kilos"},
        "product_keys": {("Frutas", "Manzana", "Gala", "Primera"), ("Frutas", "Pera", "", "")},
    }
    reference = dict(profile, units={"$/kilo"}, product_keys={("Frutas", "Manzana", "Gala", "Primera")})
    assert profile_years.format_shares({"unidad": 0.25, "kilo": 0.7034}) == "kilo 70.34%, unidad 25.00%"
    profile_years.print_year("wholesale", 2025, profile, reference)
    out = capsys.readouterr().out
    assert "rejected: 2" in out and "unknown channels: ['Kiosco']" in out and "missing: none" in out
    assert "units absent from 2026: 1" in out and "of which 1 of the 1 2026 keys" in out


def test_d323_the_profile_of_the_years_reads_every_year_of_raw_db(tmp_path, monkeypatch, capsys):
    from etl import profile_years

    raw_database(tmp_path / "raw.db").close()
    monkeypatch.setattr(profile_years.etl, "open_database", lambda: sqlite3.connect(tmp_path / "raw.db"))
    monkeypatch.setattr(profile_years.etl, "load_raw_files", lambda connection: [("consumer_2026.csv", "UNCHANGED", 3)])
    seen = []
    monkeypatch.setattr(profile_years, "profile_year", lambda rows, source: seen.append((source, len(rows))) or {})
    monkeypatch.setattr(
        profile_years, "print_year", lambda source, year, profile, reference: seen.append(("print", year))
    )
    assert profile_years.main() == 0
    assert "UNCHANGED | consumer_2026.csv | 3 rows" in capsys.readouterr().out
    assert ("print", 2025) in seen and ("print", 2026) in seen
    raw = sqlite3.connect(tmp_path / "raw.db")
    assert len(profile_years.read_raw_year(raw, etl.SOURCE_WHOLESALE, 2025)) == 2


# endregion
