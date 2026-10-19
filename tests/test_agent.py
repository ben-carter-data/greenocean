"""Tests for the download agent. They never use the network: downloads are faked."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import agent  # noqa: E402

VALID_WHOLESALE_CSV = (
    '"Fecha","ID region","Region","Mercado","Subsector","Producto","Variedad / Tipo",'
    '"Calidad","Unidad de comercializacion","Origen","Volumen","Precio minimo",'
    '"Precio maximo","Precio promedio"\r\n'
    '"2026-01-02","13","RM","Lo Valledor","Hortalizas","Tomate","Larga vida",'
    '"Primera","$/caja 18 kilos","RM","100","9000,0000","10000,0000","9500,0000"\r\n')
OPEN_YEAR_RESOURCE = {"source": "wholesale", "year": 2099, "url": "http://test/file.csv"}


@pytest.fixture(autouse=True)
def temporary_download_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "DOWNLOAD_DIR", tmp_path)
    monkeypatch.setattr(agent, "MANIFEST_FILE", tmp_path / "manifest.json")
    return tmp_path


def fake_downloader(content):
    def downloader(url, destination_path):
        destination_path.write_text(content, encoding="utf-8-sig")
    return downloader


def run_agent(content, resource=OPEN_YEAR_RESOURCE):
    return agent.download_all_resources(
        [dict(resource)], downloader=fake_downloader(content), seconds_between_retries=0)


def test_input_file_lists_both_sources():
    resources = agent.load_input_resources()
    assert {resource["source"] for resource in resources} == {"wholesale", "consumer"}
    assert all(isinstance(resource["year"], int) for resource in resources)


def test_valid_download_is_saved_and_recorded(tmp_path):
    assert run_agent(VALID_WHOLESALE_CSV) == 0
    assert (tmp_path / "wholesale_2099.csv").exists()
    assert "wholesale_2099.csv" in agent.load_manifest()


def test_unexpected_header_is_rejected(tmp_path):
    changed_header = VALID_WHOLESALE_CSV.replace('"Mercado"', '"Mercado nuevo"')
    assert run_agent(changed_header) == 1
    assert not (tmp_path / "wholesale_2099.csv").exists()


def test_empty_file_and_header_only_file_are_invalid(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")
    assert agent.validate_downloaded_file(empty_file, "wholesale") == (
        False, agent.REASON_EMPTY_FILE)
    header_only_file = tmp_path / "header_only.csv"
    header_only_file.write_text(VALID_WHOLESALE_CSV.split("\r\n")[0] + "\r\n",
                                encoding="utf-8-sig")
    assert agent.validate_downloaded_file(header_only_file, "wholesale") == (
        False, agent.REASON_NO_ROWS)


def test_download_error_is_retried_then_counted_as_failure():
    attempts = []

    def failing_downloader(url, destination_path):
        attempts.append(url)
        raise ConnectionError("no network")

    failures = agent.download_all_resources(
        [dict(OPEN_YEAR_RESOURCE)], downloader=failing_downloader,
        seconds_between_retries=0)
    assert failures == 1
    assert len(attempts) == agent.FETCH_WARNINGS_THRESHOLD


def test_failed_download_keeps_the_previous_file(tmp_path):
    run_agent(VALID_WHOLESALE_CSV)
    run_agent("garbage")
    saved_content = (tmp_path / "wholesale_2099.csv").read_bytes().decode("utf-8-sig")
    assert saved_content == VALID_WHOLESALE_CSV


def test_closed_year_is_not_downloaded_again(tmp_path):
    closed_year_resource = dict(OPEN_YEAR_RESOURCE, year=2020)
    (tmp_path / "wholesale_2020.csv").write_text(VALID_WHOLESALE_CSV, encoding="utf-8-sig")

    def downloader_that_must_not_run(url, destination_path):
        raise AssertionError("a closed year must not be downloaded again")

    failures = agent.download_all_resources(
        [closed_year_resource], downloader=downloader_that_must_not_run,
        seconds_between_retries=0)
    assert failures == 0


def test_d164_odepa_root_is_trusted_on_top_of_certifi():
    # datos.odepa.gob.cl chains to emSign Root CA - G1, which certifi dropped.
    bundle = agent.build_certificate_bundle().read_text(encoding="utf-8")
    assert bundle.startswith(Path(agent.certifi.where()).read_text(encoding="utf-8"))
    assert "emSign Root CA - G1" in bundle
    assert bundle.count("-----BEGIN CERTIFICATE-----") > 100


def test_d164_download_verifies_the_certificate_with_that_bundle(tmp_path, monkeypatch):
    calls = {}

    class Response:
        content = b"data"

        def raise_for_status(self):
            pass

    def fake_get(url, **options):
        calls.update(options)
        return Response()

    monkeypatch.setattr(agent.requests, "get", fake_get)
    agent.download_file("https://datos.odepa.gob.cl/file.csv", tmp_path / "file.csv")
    assert "emSign Root CA - G1" in Path(calls["verify"]).read_text(encoding="utf-8")
