"""The served database lives in a release that every load replaces; git keeps only its pointer (D-270, ADR-35)."""

import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from bi import served_database

# region Variables
ROOT = Path(__file__).resolve().parent.parent
# endregion


# region Test served database
class Answer:
    """What requests.get returns, enough for download()."""

    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, size):
        yield self.body


def published(tmp_path, body=b"base de la semana", when=None):
    """A pointer for body, as the weekly job writes it, and the getter that serves body."""
    source = tmp_path / "published.duckdb"
    source.write_bytes(body)
    pointer = tmp_path / "datos.version"
    served_database.write_pointer(source, pointer, now=when)
    return pointer, (lambda url, **_: Answer(body))


def test_a_missing_database_is_downloaded_and_checked(tmp_path, monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    pointer, get = published(tmp_path)
    local = tmp_path / "datos.duckdb"
    assert served_database.ensure_database(local, pointer, get=get) == served_database.DOWNLOADED
    assert local.read_bytes() == b"base de la semana"
    assert served_database.ensure_database(local, pointer, get=get) == served_database.PRESENT  # nothing to do twice


def test_an_older_database_is_replaced_by_the_published_one(tmp_path):
    local = tmp_path / "datos.duckdb"
    local.write_bytes(b"base de la semana pasada")
    old = datetime.now(timezone.utc).timestamp() - 3600
    os.utime(local, (old, old))
    pointer, get = published(tmp_path)
    assert served_database.ensure_database(local, pointer, get=get) == served_database.DOWNLOADED
    assert local.read_bytes() == b"base de la semana"


def test_a_local_build_newer_than_the_published_one_is_kept(tmp_path):
    pointer, get = published(tmp_path, when=datetime.now(timezone.utc) - timedelta(days=1))
    local = tmp_path / "datos.duckdb"
    local.write_bytes(b"reconstruida en local con --local")
    assert served_database.ensure_database(local, pointer, get=get) == served_database.LOCAL_BUILD
    assert local.read_bytes() == b"reconstruida en local con --local"


def test_a_download_that_does_not_match_the_pointer_never_replaces_the_database(tmp_path):
    pointer, _ = published(tmp_path)
    local = tmp_path / "datos.duckdb"
    local.write_bytes(b"base anterior")
    old = datetime.now(timezone.utc).timestamp() - 3600
    os.utime(local, (old, old))
    with pytest.raises(ValueError):
        served_database.ensure_database(local, pointer, get=lambda url, **_: Answer(b"archivo alterado"))
    assert local.read_bytes() == b"base anterior"
    assert not list(tmp_path.glob("*.tmp"))  # the partial download is gone


def test_without_a_pointer_nothing_is_downloaded(tmp_path):
    assert (
        served_database.ensure_database(
            tmp_path / "datos.duckdb", tmp_path / "datos.version", get=lambda *a, **k: pytest.fail("no download")
        )
        == served_database.NO_POINTER
    )


def test_the_weekly_job_reads_last_week_database_and_publishes_the_file_before_its_pointer():
    workflow = (ROOT / ".github" / "workflows" / "semanal.yml").read_text(encoding="utf-8")
    assert workflow.index("python bi/served_database.py\n") < workflow.index("python etl/pipeline.py")
    upload = workflow.index("gh release upload base-actual etl/datos.duckdb --clobber")
    assert (
        upload < workflow.index("python bi/served_database.py --pointer") < workflow.index("git add etl/datos.version")
    )
    assert "git add etl/datos.db" not in workflow and "etl/datos.duckdb agent" not in workflow
    assert "python bi/served_database.py" in (ROOT / ".github" / "workflows" / "pruebas.yml").read_text(
        encoding="utf-8"
    )


def test_git_keeps_the_pointer_and_neither_database():
    tracked = subprocess.run(["git", "ls-files", "etl"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert "etl/datos.version" in tracked
    assert "etl/datos.duckdb" not in tracked and "etl/datos.db" not in tracked


class Reply(Answer):
    """An answer with a status: a server error raises the HTTPError requests raises."""

    def __init__(self, body=b"", status=200, data=None):
        super().__init__(body)
        self.status_code, self.data = status, data

    def raise_for_status(self):
        if self.status_code >= 400:
            failure = served_database.requests.Response()
            failure.status_code = self.status_code
            raise served_database.requests.HTTPError(response=failure)

    def json(self):
        return self.data


def test_d567_an_outage_is_waited_out_and_a_missing_file_is_not(tmp_path, monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    pointer, _ = published(tmp_path)
    answers = iter([Reply(status=504), Reply(status=502), Reply(b"base de la semana")])
    pauses = []
    local = tmp_path / "datos.duckdb"
    served = served_database.ensure_database(local, pointer, get=lambda url, **_: next(answers), pause=pauses.append)
    assert served == served_database.DOWNLOADED and local.read_bytes() == b"base de la semana"
    assert pauses == [5, 10]  # twice as long each time
    pauses.clear()
    with pytest.raises(served_database.requests.HTTPError):  # a 404 is not an outage: no second try
        served_database.ensure_database(
            tmp_path / "otra.duckdb", pointer, get=lambda url, **_: Reply(status=404), pause=pauses.append
        )
    assert pauses == []
    always = [Reply(status=504)] * served_database.ATTEMPTS
    with pytest.raises(served_database.requests.HTTPError):  # a long outage still fails, after its tries
        served_database.ensure_database(
            tmp_path / "tercera.duckdb", pointer, get=lambda url, **_: always.pop(), pause=pauses.append
        )
    assert len(pauses) == served_database.ATTEMPTS - 1


class Release:
    """GitHub as the download sees it: the release's API names its file, and each address answers the week's base."""

    def __init__(self):
        self.asked = []

    def __call__(self, url, headers=None, **_):
        self.asked.append((url, dict(headers or {})))
        if url == served_database.RELEASE_API_URL:
            return Reply(data={"assets": [{"name": "datos.duckdb", "url": "https://api.github.com/asset/1"}]})
        return Reply(b"base de la semana")


def test_d567_in_ci_the_release_is_read_with_the_workflow_token(tmp_path, monkeypatch):
    pointer, _ = published(tmp_path)
    get = Release()
    asked = get.asked
    monkeypatch.setenv("GH_TOKEN", "token-de-prueba")
    served_database.ensure_database(tmp_path / "datos.duckdb", pointer, get=get)
    assert [url for url, _ in asked] == [served_database.RELEASE_API_URL, "https://api.github.com/asset/1"]
    assert all(headers["Authorization"] == "Bearer token-de-prueba" for _, headers in asked)
    assert asked[1][1]["Accept"] == "application/octet-stream"
    monkeypatch.delenv("GH_TOKEN")  # without it (the panel, a clone), the public address, anonymously
    asked.clear()
    served_database.ensure_database(tmp_path / "otra.duckdb", pointer, get=get)
    assert asked == [(served_database.DOWNLOAD_URL, {})]
    for name in ("pruebas", "calidad", "semanal"):  # every workflow passes its token to the download
        workflow = (ROOT / ".github" / "workflows" / f"{name}.yml").read_text(encoding="utf-8")
        start = workflow.index("served_database.py") - 600
        assert "GH_TOKEN: ${{ github.token }}" in workflow[start : workflow.index("served_database.py") + 200], name
        assert 'PIP_RETRIES: "10"' in workflow and "cache: pip" in workflow, name


def test_the_pointer_names_the_release_file_the_panel_downloads():
    pointer = served_database.read_pointer()
    assert len(pointer["sha256"]) == 64 and pointer["bytes"] > 0
    assert served_database.DOWNLOAD_URL.endswith("/releases/download/base-actual/datos.duckdb")


# endregion
