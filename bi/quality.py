"""Read-only evidence checks. Passing checks are not a source-price certification."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from bi import queries


def check_database(database_file=queries.DATABASE_FILE):
    """Check the stored database independently of dashboard aggregations."""
    with queries.open_database(database_file) as connection:
        # DuckDB checksums every block it reads: a full scan fails on a damaged file.
        integrity = ['ok'] if connection.execute('SELECT COUNT(*) FROM weekly_price').fetchone() else ['error']
        foreign_keys = connection.execute('''SELECT
            (SELECT COUNT(*) FROM weekly_price w LEFT JOIN dim_product p USING(product_id) WHERE p.product_id IS NULL)
          + (SELECT COUNT(*) FROM weekly_price w LEFT JOIN dim_region r USING(region_id) WHERE r.region_id IS NULL)
          + (SELECT COUNT(*) FROM weekly_price w LEFT JOIN dim_channel c USING(channel_id) WHERE c.channel_id IS NULL)
          + (SELECT COUNT(*) FROM weekly_price w LEFT JOIN dim_date d USING(week_start) WHERE d.week_start IS NULL)
          + (SELECT COUNT(*) FROM rejection j LEFT JOIN etl_run e USING(run_id) WHERE e.run_id IS NULL)''').fetchone()[0]
        duplicates = connection.execute('''SELECT COUNT(*) FROM (
            SELECT 1 FROM weekly_price GROUP BY week_start, product_id, region_id,
            channel_id, normalized_unit HAVING COUNT(*) > 1)''').fetchone()[0]
        invalid = connection.execute('''SELECT COUNT(*) FROM weekly_price WHERE flag IS NULL
            AND (price IS NULL OR price <= 0 OR normalized_unit IS NULL
            OR observation_count <= 0 OR TRY_CAST(week_start AS DATE) IS NULL
            OR dayofweek(TRY_CAST(week_start AS DATE)) != 1)''').fetchone()[0]
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
