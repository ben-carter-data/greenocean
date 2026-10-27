"""«Dashboard» (D-296): the macro view repeats no figure of its own; each one is the Resumen's, the Precios e inflación
page's or Calidad y auditoría's, recomputed here from the same tables."""

import re

import pytest

from bi import alerts, charts, dashboard, home_mockup, overview, queries

needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")


@pytest.fixture(scope="module")
def market():
    prices = queries.run_query("k6_national_weekly_price")
    variations = alerts.add_weekly_variation(prices.copy())
    prices["week_start"] = prices["week_start"].astype("datetime64[ns]")
    week = variations["week_start"].max()
    return prices, variations, week


@needs_database
def test_d296_the_market_tab_counts_the_same_prices_and_moves_as_the_resumen(market):
    prices, variations, week = market
    weeks = overview.market_weeks(prices, variations, variations.iloc[0:0].assign(product_group=[]))
    last = weeks.iloc[-1]
    valid = variations[(variations["week_start"] == week) & variations["variation"].notna()]
    assert last["prices"] == len(prices[prices["week_start"] == week])  # every national series with a price
    assert last["comparable"] == len(valid)
    moves = overview.family_moves(prices, variations, week).set_index("product_group")
    for family, rows in valid.groupby("product_group"):
        assert moves.loc[family, "change"] == pytest.approx(rows["variation"].median() * 100)
        assert moves.loc[family, "state"] == overview.state(rows["variation"].median() * 100)
    moved = overview.directions(variations, week).set_index("direction")["prices"]
    assert moved.sum() == len(valid)
    assert moved["Subieron"] == (valid["variation"] >= overview.STILL).sum()


@needs_database
def test_d303_changing_the_language_keeps_the_dashboard_working():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(dashboard.Path(dashboard.__file__)), default_timeout=60)
    app.query_params.update({"vista": dashboard.PAGE_INSIGHTS, "perfil": "profesional", "lang": "en"})
    app.session_state[dashboard.OVERVIEW_WEEK_KEY] = "Oct 12–18"  # what a widget may leave after a language change
    app.run()
    assert not app.exception


@needs_database
def test_d311_the_reading_of_the_period_chains_the_cells_of_the_weeks_table(market):
    _, variations, _ = market
    heat = overview.family_heat(variations, weeks=8)
    lines = overview.weeks_insight(heat)
    chained = {
        family: ((1 + rows.sort_values("week_start")["change"] / 100).prod() - 1) * 100
        for family, rows in heat.groupby("family")
    }
    top = max(chained, key=chained.get)
    rises = int((heat[heat["family"] == top]["change"] >= overview.QUIET).sum())
    assert lines[0].startswith(f"En estas 8 semanas, {top} es la que más se encareció: {overview.signed(chained[top])}")
    assert f"con alzas en {rises} de ellas" in lines[0] and len(lines) == 3
    # D-314: the table's Total column is the same chain, its rows go from the most to the least, and no cell reads «-0,0».
    totals = overview.period_totals(heat)
    assert totals.to_dict() == pytest.approx(chained)
    order = list(totals.sort_values(ascending=False).index)
    table = overview.build_heat_table_html(
        heat,
        "family",
        "week",
        "change",
        list(dict.fromkeys(heat.sort_values("week_start")["week"])),
        order,
        charts.get_palette(charts.THEMES[0]),
        totals=totals.to_dict(),
        total_title="Total 8 sem",
    )
    assert "Total 8 sem" in table and "-0,0" not in table and "−0,0" not in table
    assert (
        overview.signed(chained[top]).replace(" %", "") in table.replace(".", ",")
        or f"{chained[top]:+.1f}".replace(".", ",") in table
    )
    assert table.index(f">{order[0]}<") < table.index(f">{order[-1]}<")


def test_d308_the_dashboard_is_gone_and_its_pieces_have_a_place():
    source = (dashboard.Path(dashboard.__file__)).read_text(encoding="utf-8")
    assert "def show_overview_page" not in source and "def show_overview_inflation" not in source
    assert dashboard.MENU_BLOCKS[0][2] == [dashboard.HOME_PAGE, dashboard.PAGE_WHERE, dashboard.PAGE_INSIGHTS]
    assert dashboard.DOOR_PAGES == {
        dashboard.PAGE_SEASONALITY: dashboard.HOME_PAGE
    }  # opens from a button of the Panorama
    assert dashboard.RETIRED_VIEWS["Dashboard general"] == dashboard.PAGE_WHERE
    assert re.search(
        r'key=OVERVIEW_WEEKS_KEY,\s*width=190', source
    )  # the table of weeks opens as a dialog from the Panorama
    assert charts.get_palette(charts.THEMES[0]) and home_mockup
