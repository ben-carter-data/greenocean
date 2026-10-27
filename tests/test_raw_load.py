"""Tests for the raw table load."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import agent  # noqa: E402
from etl import etl  # noqa: E402
from tests.test_agent import (
    OPEN_YEAR_RESOURCE,
    VALID_WHOLESALE_CSV,  # noqa: E402
    fake_downloader,
)


def download_into(tmp_path, monkeypatch, content):
    monkeypatch.setattr(agent, "DOWNLOAD_DIR", tmp_path)
    monkeypatch.setattr(agent, "MANIFEST_FILE", tmp_path / "manifest.json")
    agent.download_all_resources(
        [dict(OPEN_YEAR_RESOURCE)], downloader=fake_downloader(content), seconds_between_retries=0
    )


def count_wholesale_rows(connection):
    return connection.execute("SELECT COUNT(*) FROM raw_wholesale").fetchone()[0]


def test_table_row_count_equals_csv_row_count(tmp_path, monkeypatch):
    download_into(tmp_path, monkeypatch, VALID_WHOLESALE_CSV)
    connection = etl.open_database(tmp_path / "test.db")
    assert etl.load_raw_files(connection, tmp_path) == [("wholesale_2099.csv", etl.STATUS_LOADED, 1)]
    assert count_wholesale_rows(connection) == 1


def test_loading_twice_does_not_duplicate_rows(tmp_path, monkeypatch):
    download_into(tmp_path, monkeypatch, VALID_WHOLESALE_CSV)
    connection = etl.open_database(tmp_path / "test.db")
    etl.load_raw_files(connection, tmp_path)
    assert etl.load_raw_files(connection, tmp_path)[0][1] == etl.STATUS_UNCHANGED
    assert count_wholesale_rows(connection) == 1


def test_updated_file_replaces_the_rows_of_its_year(tmp_path, monkeypatch):
    download_into(tmp_path, monkeypatch, VALID_WHOLESALE_CSV)
    connection = etl.open_database(tmp_path / "test.db")
    etl.load_raw_files(connection, tmp_path)
    two_row_csv = VALID_WHOLESALE_CSV + VALID_WHOLESALE_CSV.split("\r\n")[1] + "\r\n"
    download_into(tmp_path, monkeypatch, two_row_csv)
    etl.load_raw_files(connection, tmp_path)
    assert count_wholesale_rows(connection) == 2
