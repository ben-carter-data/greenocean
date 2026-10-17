"""Read-only evidence checks. Passing checks are not a source-price certification."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from bi import queries


def check_database(database_file=queries.DATABASE_FILE):
    """Check the stored database independently of dashboard aggregations."""
    with queries.open_database(database_file) as connection:
        integrity = [row[0] for row in connection.execute('PRAGMA quick_check')]
        foreign_keys = len(connection.execute('PRAGMA foreign_key_check').fetchall())
        duplicates = connection.execute('''SELECT COUNT(*) FROM (
            SELECT 1 FROM weekly_price GROUP BY week_start, product_id, region_id,
            channel_id, normalized_unit HAVING COUNT(*) > 1)''').fetchone()[0]
        invalid = connection.execute('''SELECT COUNT(*) FROM weekly_price WHERE flag IS NULL
            AND (price IS NULL OR price <= 0 OR normalized_unit IS NULL
            OR observation_count <= 0 OR date(week_start) IS NULL
            OR strftime('%w',week_start) != '1')''').fetchone()[0]
        weeks, first, last = connection.execute('''SELECT COUNT(DISTINCT week_start),
            MIN(week_start), MAX(week_start) FROM weekly_price''').fetchone()
    return dict(checked_at=datetime.now(timezone.utc).isoformat(),
                integrity_ok=integrity == ['ok'], integrity=integrity,
                foreign_keys=foreign_keys, duplicates=duplicates, invalid=invalid,
                weeks=weeks, first=first, last=last)


def check_source_files(manifest, directory):
    """A manifest alone is recorded provenance, not a verified file checksum."""
    evidence = []
    for name, metadata in sorted(manifest.items()):
        # Never let a malformed manifest read outside the source directory.
        path = Path(directory) / Path(name).name
        expected = metadata.get('hash', '') if isinstance(metadata, dict) else ''
        status = 'Pendiente · archivo no disponible'
        actual = None
        if path.is_file() and name == Path(name).name:
            digest = hashlib.sha256()
            with path.open('rb') as source:
                for block in iter(lambda: source.read(1024 * 1024), b''):
                    digest.update(block)
            actual = digest.hexdigest()
            status = ('Verificado · SHA-256 coincide' if expected and actual == expected else
                      'Falla · SHA-256 distinto' if expected else 'Pendiente · sin huella registrada')
        evidence.append(dict(file=name, status=status, expected=expected, actual=actual,
                             downloaded_at=metadata.get('downloaded_at', '') if isinstance(metadata, dict) else ''))
    return evidence
