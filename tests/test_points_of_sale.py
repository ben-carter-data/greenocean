"""Where the products are sold (D-306): information only, regenerated from ODEPA's own files."""

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


def test_d310_each_region_is_a_column_of_houses_with_its_points_and_no_price():
    points = overview.read_points()
    column = overview.build_region_column(
        "Región Metropolitana de Santiago", points["Región Metropolitana de Santiago"], 200
    )
    assert "Vega Central Mapocho de Santiago" in column and column.count('class="ov-house') == 3 + 1
    assert (
        "Supermercado, Feria libre" in column and "$" not in column and " %" not in column
    )  # the retail kinds, on hover
    assert (
        overview.place_kind("Vega Central Mapocho de Santiago") == "fair"
        and overview.place_kind("Femacal de La Calera") == "market"
    )
    assert 'class="ov-mini"' in column
    for kind in {kind for data in points.values() for kind in data["consumer"]}:
        assert (overview.POINTS_FILE.parent / "points" / f"{overview.POINT_ICONS[kind]}.svg").exists(), kind
    regions = overview.ordered_regions(points, {name: 13 for name in points})
    assert overview.build_regions_html(regions, points).count('class="ov-region"') == len(points)


def test_d322_the_price_level_of_each_region_is_the_median_index_of_products_two_regions_price():
    from bi import queries

    week = queries.run_sql("SELECT max(week_start) AS w FROM weekly_price")["w"][0]
    frame = queries.run_sql(
        "SELECT * FROM (" + queries.read_query_body("k3_regional_index") + ") WHERE week_start = ?", parameters=(week,)
    )
    levels = overview.regional_price_levels(frame)
    shared = frame[frame.groupby(overview.PRICE_KEY)["region"].transform("count") >= 2]
    for region, (level, prices, rank) in levels.items():
        rows = shared[shared["region"] == region]
        assert prices == len(rows) and level == pytest.approx((rows["regional_index"].median() - 1) * 100)
    ranks = sorted(levels.values(), key=lambda item: item[2])
    assert [item[2] for item in ranks] == list(range(1, len(levels) + 1))
    assert all(a[0] >= b[0] for a, b in zip(ranks, ranks[1:]))  # rank 1 is the dearest
