"""Where the products are sold (D-306): the data file, regenerated from ODEPA's own files. The page that drew it is gone
(D-325); the Insights still read the file for the wholesale markets."""

import json

import pytest

from bi import overview, queries
from etl import points_of_sale


def test_d306_every_region_of_the_file_exists_in_the_database_and_none_carries_a_price():
    points = overview.read_points()
    assert points and all(set(data) == {"wholesale", "consumer", "sectors"} for data in points.values())
    if queries.DATABASE_FILE.exists():
        regions = set(queries.run_sql("SELECT region FROM dim_region")["region"])
        assert set(points) <= regions
    assert "Lo Valledor" in " ".join(points["Región Metropolitana de Santiago"]["wholesale"])


def test_d306_the_file_is_what_the_downloaded_files_say():
    if not list(points_of_sale.DOWNLOADS.glob("wholesale_*.csv")):
        pytest.skip("the ODEPA files are not here")
    assert json.loads(json.dumps(points_of_sale.build(), ensure_ascii=False)) == overview.read_points()


def test_d306_every_kind_of_consumer_point_has_its_icon():
    points = overview.read_points()
    for kind in {kind for data in points.values() for kind in data["consumer"]}:
        assert (overview.POINTS_FILE.parent / "points" / f"{overview.POINT_ICONS[kind]}.svg").exists(), kind
    assert 'class="ov-icon"' in overview.point_icon("mercado")
