"""Where the served database lives (D-270, ADR-35): one file in a GitHub release, replaced every week.

Git keeps every version of a committed file, so a weekly commit of etl/datos.duckdb made the history grow
by about 1 GB a year with old copies nobody reads. The weekly job now uploads the file to the release
«base-actual», replacing the one before, and commits only a small pointer, etl/datos.version: the SHA-256,
the size and the time of the file it published. The panel, the tests in CI and a fresh clone compare their
local file with the pointer and download the file of the release when it is missing or older, checking its
SHA-256 before using it. A local build newer than the pointer (python etl/pipeline.py --local) is kept.

    python bi/served_database.py              download the published file when needed
    python bi/served_database.py --pointer    write the pointer of the local file (the weekly job, after it)
"""
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import project, queries  # noqa: E402

RELEASE_TAG = "base-actual"
DATABASE_FILE = queries.DATABASE_FILE
POINTER_FILE = DATABASE_FILE.with_name("datos.version")
DOWNLOAD_URL = f"{project.GITHUB_URL}/releases/download/{RELEASE_TAG}/{DATABASE_FILE.name}"
TIMEOUT_SECONDS = 60

# How the local file compares with the published one, and what ensure_database did.
MISSING, PRESENT, LOCAL_BUILD, OLDER = "missing", "present", "local build", "older"
DOWNLOADED, NO_POINTER = "downloaded", "no pointer"


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_pointer(database_file=DATABASE_FILE, pointer_file=POINTER_FILE, now=None):
    """The pointer of the file about to be published: its SHA-256, its size and when."""
    pointer = {"sha256": file_sha256(database_file), "bytes": database_file.stat().st_size,
               "published_at": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")}
    pointer_file.write_text(json.dumps(pointer, indent=2) + "\n", encoding="utf-8")
    return pointer


def read_pointer(pointer_file=POINTER_FILE):
    return json.loads(pointer_file.read_text(encoding="utf-8")) if pointer_file.exists() else None


def compare(pointer, database_file=DATABASE_FILE):
    """MISSING, PRESENT (the published file), LOCAL_BUILD (different and newer: kept) or OLDER (to replace)."""
    if not database_file.exists():
        return MISSING
    if file_sha256(database_file) == pointer["sha256"]:
        return PRESENT
    published = datetime.fromisoformat(pointer["published_at"]).timestamp()
    return LOCAL_BUILD if database_file.stat().st_mtime > published else OLDER


def download(pointer, database_file=DATABASE_FILE, url=DOWNLOAD_URL, get=requests.get):
    """Download the published file next to its place and swap it in only if its SHA-256 is the pointer's."""
    handle, temporary = tempfile.mkstemp(dir=database_file.parent, suffix=".duckdb.tmp")
    try:
        with os.fdopen(handle, "wb") as target, get(url, stream=True, timeout=TIMEOUT_SECONDS) as answer:
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


def ensure_database(database_file=DATABASE_FILE, pointer_file=POINTER_FILE, get=requests.get):
    """Make the local served file the published one when needed; returns what it did."""
    pointer = read_pointer(pointer_file)
    if pointer is None:
        return NO_POINTER
    state = compare(pointer, database_file)
    if state in (PRESENT, LOCAL_BUILD):
        return state
    download(pointer, database_file, get=get)
    return DOWNLOADED


if __name__ == "__main__":
    if "--pointer" in sys.argv:
        print(json.dumps(write_pointer()))
    else:
        print(ensure_database())
