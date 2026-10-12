"""T-27: profile every downloaded year before loading the history.

Run it with:  python etl/profile_years.py

It copies the downloaded files into raw.db (as the ETL does) and prints one
block per source and year: rows, rejections, units, channels, regions, weeks
and how many 2026 product keys also exist that year. It never writes to datos.db.
"""
import sys
from pathlib import Path

import pandas as pd

# region Imports of the project
# This file runs as a script, so the project folder is added to the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import etl  # noqa: E402
# endregion

# region Constants
# The year every other year is compared with: the one the dashboard already shows.
REFERENCE_YEAR = 2026
NOT_CONVERTIBLE = "not convertible"
# endregion


# region Profile
def read_raw_year(raw_connection, source, year):
    """Every raw row of one source and file year, all columns as text."""
    return pd.read_sql(f"SELECT * FROM {etl.RAW_TABLE_BY_SOURCE[source]} WHERE file_year = ?",
                       raw_connection, params=(year,))


def count_rejections(reasons):
    """RN-11 reasons and how many rows each one rejects, e.g. {'NON_POSITIVE_PRICE': 3}."""
    return reasons[reasons != ""].value_counts().to_dict()


def measure_unit_shares(units):
    """Share of rows that each normalized unit receives (RN-03 to RN-05)."""
    normalized_units = units.map(lambda unit: etl.convert_unit(unit)[0] or NOT_CONVERTIBLE)
    return normalized_units.value_counts(normalize=True).to_dict()


def find_new_units(units, reference_units):
    """Units absent from the reference year, with the conversion the ETL would apply."""
    return {unit: etl.convert_unit(unit) for unit in sorted(set(units) - set(reference_units))}


def list_product_keys(valid_rows):
    """Distinct product keys (group, product, variety, quality) of the valid rows."""
    return set(valid_rows[etl.PRODUCT_COLUMNS].itertuples(index=False, name=None))


def profile_year(raw_rows, source):
    """Facts about one source and year, measured with the ETL's own rules.

    Returns a dictionary; the 'units' and 'product_keys' entries are kept so
    each year can be compared with the reference year.
    """
    clean_rows = etl.clean(raw_rows, source)
    reasons = etl.validate_rows(clean_rows)
    valid_rows = etl.assign_week_start(clean_rows[reasons == ""].copy())
    return {
        "rows_read": len(raw_rows),
        "rejections": count_rejections(reasons),
        "first_week": valid_rows["week_start"].min().date(),
        "last_week": valid_rows["week_start"].max().date(),
        "week_count": valid_rows["week_start"].nunique(),
        "missing_weeks": etl.find_missing_weeks(valid_rows["week_start"]),
        "unknown_regions": sorted(set(valid_rows["region_id"].astype(int))
                                  - etl.KNOWN_REGION_IDS),
        "unknown_channels": sorted(set(valid_rows["channel"]) - etl.KNOWN_CHANNELS),
        "unit_shares": measure_unit_shares(valid_rows["unit"]),
        "units": set(valid_rows["unit"]),
        "product_keys": list_product_keys(valid_rows),
    }
# endregion


# region Report
def format_shares(shares):
    """{'kilo': 0.7034} -> 'kilo 70.34 %'."""
    return ", ".join(f"{unit} {share:.2%}" for unit, share in sorted(shares.items()))


def print_year(source, year, profile, reference_profile):
    """Print the facts of one source and year, compared with the reference year."""
    shared_keys = profile["product_keys"] & reference_profile["product_keys"]
    print(f"\n{source} {year}")
    print(f"  rows read: {profile['rows_read']}")
    print(f"  rejected: {sum(profile['rejections'].values())} {profile['rejections']}")
    print(f"  weeks: {profile['week_count']} ({profile['first_week']} to "
          f"{profile['last_week']}), missing: {profile['missing_weeks'] or 'none'}")
    print(f"  unknown regions: {profile['unknown_regions'] or 'none'}, "
          f"unknown channels: {profile['unknown_channels'] or 'none'}")
    print(f"  units: {format_shares(profile['unit_shares'])}")
    new_units = find_new_units(profile["units"], reference_profile["units"])
    print(f"  units absent from {REFERENCE_YEAR}: {len(new_units)}")
    for unit, conversion in new_units.items():
        print(f"    {unit} -> {conversion}")
    print(f"  product keys: {len(profile['product_keys'])}, of which "
          f"{len(shared_keys)} of the {len(reference_profile['product_keys'])} "
          f"{REFERENCE_YEAR} keys")


def main():
    """Load the downloaded files into raw.db and print the profile of every year."""
    raw_connection = etl.open_database()
    for file_name, status, row_count in etl.load_raw_files(raw_connection):
        print(f"{status} | {file_name} | {row_count} rows")
    for source in etl.SOURCES:
        years = [row[0] for row in raw_connection.execute(
            f"SELECT DISTINCT file_year FROM {etl.RAW_TABLE_BY_SOURCE[source]} ORDER BY 1")]
        reference_profile = profile_year(read_raw_year(raw_connection, source, REFERENCE_YEAR),
                                         source)
        for year in years:
            profile = profile_year(read_raw_year(raw_connection, source, year), source)
            print_year(source, year, profile, reference_profile)
    raw_connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
# endregion
