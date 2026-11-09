"""Where the served database lives (D-270, ADR-35): one file in a GitHub release, replaced every week.

Git keeps every version of a committed file, so a weekly commit of etl/datos.duckdb made the history grow
by about 1 GB a year with old copies nobody reads. The weekly job now uploads the file to the release
«base-actual», replacing the one before, and commits only a small pointer, etl/datos.version: the SHA-256,
the size and the time of the file it published. The panel, the tests in CI and a fresh clone compare their
local file with the pointer and download the file of the release when it is missing or older, checking its
SHA-256 before using it. A local build newer than the pointer (python etl/pipeline.py --local) is kept.
D-567: a GitHub outage limits anonymous traffic first, so in CI the file comes through the API with the workflow's
token (GH_TOKEN), and every download is tried again on a timeout or a server error before it fails.

    python bi/served_database.py              download the published file when needed
    python bi/served_database.py --pointer    write the pointer of the local file (the weekly job, after it)
"""

from __future__ import annotations

from typing import Any, Callable

import hashlib
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import project, queries  # noqa: E402

# region Constants
RELEASE_TAG = "base-actual"
DATABASE_FILE = queries.DATABASE_FILE
POINTER_FILE = DATABASE_FILE.with_name("datos.version")
DOWNLOAD_URL = f"{project.GITHUB_URL}/releases/download/{RELEASE_TAG}/{DATABASE_FILE.name}"
RELEASE_API_URL = (
    f"https://api.github.com/repos/{project.GITHUB_URL.removeprefix('https://github.com/')}/releases/tags/{RELEASE_TAG}"
)
TIMEOUT_SECONDS = 60
# D-567: five tries, 5 s apart and then twice as long each time (75 s in all): enough for a short outage of GitHub.
ATTEMPTS, FIRST_PAUSE_SECONDS = 5, 5

# How the local file compares with the published one, and what ensure_database did.
MISSING, PRESENT, LOCAL_BUILD, OLDER = "missing", "present", "local build", "older"
DOWNLOADED, NO_POINTER = "downloaded", "no pointer"
# endregion


# region Where the served database lives
def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_pointer(
    database_file: Path = DATABASE_FILE, pointer_file: Path = POINTER_FILE, now: datetime | None = None
) -> dict[str, Any]:
    """The pointer of the file about to be published: its SHA-256, its size and when."""
    pointer = {
        "sha256": file_sha256(database_file),
        "bytes": database_file.stat().st_size,
        "published_at": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
    }
    pointer_file.write_text(json.dumps(pointer, indent=2) + "\n", encoding="utf-8")
    return pointer


def read_pointer(pointer_file: Path = POINTER_FILE) -> dict[str, Any] | None:
    return json.loads(pointer_file.read_text(encoding="utf-8")) if pointer_file.exists() else None


def compare(pointer: dict[str, Any], database_file: Path = DATABASE_FILE) -> str:
    """MISSING, PRESENT (the published file), LOCAL_BUILD (different and newer: kept) or OLDER (to replace)."""
    if not database_file.exists():
        return MISSING
    if file_sha256(database_file) == pointer["sha256"]:
        return PRESENT
    published = datetime.fromisoformat(pointer["published_at"]).timestamp()
    return LOCAL_BUILD if database_file.stat().st_mtime > published else OLDER


def source(get: Callable[..., Any] = requests.get) -> tuple[str, dict[str, str]]:
    """D-567: where to read the published file. With the workflow's token (GH_TOKEN, only in CI), through the API, as
    an authenticated request; without it, or if the token cannot read the release, at its public address."""
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        return DOWNLOAD_URL, {}
    asked = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    with get(RELEASE_API_URL, headers=asked, timeout=TIMEOUT_SECONDS) as answer:
        if 400 <= answer.status_code < 500:
            return DOWNLOAD_URL, {}
        answer.raise_for_status()
        assets = answer.json()["assets"]
    asset = next(item for item in assets if item["name"] == DATABASE_FILE.name)
    return asset["url"], {"Authorization": f"Bearer {token}", "Accept": "application/octet-stream"}


def passing(error: Exception) -> bool:
    """D-567: a failure worth trying again: no answer in time, no connection, or an error on GitHub's side."""
    if isinstance(error, requests.HTTPError):
        status = error.response.status_code if error.response is not None else 0
        return status >= 500 or status == 429
    return isinstance(error, (requests.ConnectionError, requests.Timeout))


def fetch(pointer: dict[str, Any], database_file: Path, get: Callable[..., Any]) -> None:
    """One try: download the published file next to its place and swap it in only if its SHA-256 is the pointer's."""
    url, headers = source(get)
    handle, temporary = tempfile.mkstemp(dir=database_file.parent, suffix=".duckdb.tmp")
    try:
        with (
            os.fdopen(handle, "wb") as target,
            get(url, headers=headers, stream=True, timeout=TIMEOUT_SECONDS) as answer,
        ):
            answer.raise_for_status()
            for block in answer.iter_content(1 << 20):
                target.write(block)
        received = file_sha256(temporary)
        if received != pointer["sha256"]:
            raise ValueError(f"the downloaded file does not match etl/datos.version ({received[:12]}…)")
        os.replace(temporary, database_file)  # atomic: an open read-only connection keeps the file it had
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def download(
    pointer: dict[str, Any],
    database_file: Path = DATABASE_FILE,
    get: Callable[..., Any] = requests.get,
    pause: Callable[[float], Any] = time.sleep,
) -> None:
    """The published file, tried again on a passing failure (D-567); a file that does not match is never retried."""
    for attempt in range(ATTEMPTS):
        try:
            fetch(pointer, database_file, get)
            return
        except (requests.RequestException, OSError) as error:
            if attempt == ATTEMPTS - 1 or not passing(error):
                raise
            pause(FIRST_PAUSE_SECONDS * 2**attempt)


def ensure_database(
    database_file: Path = DATABASE_FILE,
    pointer_file: Path = POINTER_FILE,
    get: Callable[..., Any] = requests.get,
    pause: Callable[[float], Any] = time.sleep,
) -> str:
    """Make the local served file the published one when needed; returns what it did."""
    pointer = read_pointer(pointer_file)
    if pointer is None:
        return NO_POINTER
    state = compare(pointer, database_file)
    if state in (PRESENT, LOCAL_BUILD):
        return state
    download(pointer, database_file, get=get, pause=pause)
    return DOWNLOADED


# endregion


# region Run
if __name__ == "__main__":
    if "--pointer" in sys.argv:
        print(json.dumps(write_pointer()))
    else:
        print(ensure_database())
# endregion
