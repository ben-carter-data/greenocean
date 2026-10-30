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


def test_d306_the_builder_reads_odepa_files_also_where_the_real_ones_are_not():
    """The real CSV files are not in git, so on GitHub the test above skips; a small sample keeps the builder measured
    and checked everywhere (the coverage of etl/points_of_sale.py does not depend on the machine)."""
    from pathlib import Path

    sample = Path(__file__).resolve().parent / "fixtures" / "odepa_points"
    points = points_of_sale.build(sample)
    assert set(points) == {"Región Metropolitana de Santiago", "Región de Valparaíso", "Región de Ñuble"}
    santiago = points["Región Metropolitana de Santiago"]
    assert santiago["wholesale"] == ["Mercado Lo Valledor de Santiago", "Vega Central Mapocho de Santiago"]
    assert santiago["consumer"] == ["Feria libre", "Supermercado"]  # most quoted first
    assert santiago["sectors"] == ["Norte", "Oriente"]
    assert points["Región de Ñuble"] == {
        "wholesale": [],
        "consumer": ["Feria libre"],
        "sectors": [],
    }  # «Chillán» is no sector
    assert points["Región de Valparaíso"]["consumer"] == []
