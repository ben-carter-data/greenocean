"""Evidence must distinguish passed checks, missing files and actual failures."""

import hashlib
import sqlite3
from pathlib import Path

from bi import quality


def test_source_manifest_is_not_a_verified_file(tmp_path):
    expected = hashlib.sha256(b'original').hexdigest()
    manifest = {'source.csv': {'hash': expected, 'downloaded_at': '2026-10-13'}}
    missing = quality.check_source_files(manifest, tmp_path)[0]
    assert missing['status'].startswith('Pendiente') and missing['actual'] is None
    (tmp_path / 'source.csv').write_bytes(b'original')
    assert quality.check_source_files(manifest, tmp_path)[0]['status'].startswith('Verificado')
    (tmp_path / 'source.csv').write_bytes(b'changed')
    assert quality.check_source_files(manifest, tmp_path)[0]['status'].startswith('Falla')


def test_manifest_cannot_read_outside_source_directory(tmp_path):
    (tmp_path / 'outside.csv').write_bytes(b'original')
    result = quality.check_source_files({'../outside.csv': {'hash': 'anything'}}, tmp_path)[0]
    assert result['actual'] is None and result['status'].startswith('Pendiente')


def test_database_checks_detect_bad_values_duplicate_keys_and_broken_references(tmp_path):
    path = tmp_path / 'test.db'
    with sqlite3.connect(path) as connection:
        connection.executescript((Path(__file__).resolve().parents[1] / 'etl/schema.sql').read_text())
        # FK enforcement deliberately off: the independent checker must still catch it.
        for _ in range(2):
            connection.execute("INSERT INTO weekly_price VALUES ('2026-10-06', 1, 1, 1, 'kilo', -2, NULL, 0, NULL)")
    result = quality.check_database(path)
    assert result['integrity_ok']  # Structurally valid SQLite is not sufficient.
    assert result['duplicates'] == 1 and result['invalid'] == 2
    # Two rows × four missing parents: product, region, channel and, since D-095, the week.
    assert result['foreign_keys'] == 8
