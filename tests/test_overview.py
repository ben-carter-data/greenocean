"""«Dashboard» (D-296): the macro view repeats no figure of its own; each one is the Resumen's, the Precios e inflación
page's or Calidad y auditoría's, recomputed here from the same tables."""
import pytest

from bi import alerts, charts, dashboard, home_mockup, inflation_view, overview, queries

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
def test_d296_the_regions_read_north_to_south_with_the_resumen_shares():
    week = queries.run_sql("SELECT max(week_start) AS w FROM weekly_price")["w"][0]
    previous = (dashboard.pd.Timestamp(week) - dashboard.pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    snapshot = lambda w: dashboard.add_display_columns(queries.run_sql(
        "SELECT * FROM (" + queries.read_query_body("k3_regional_index") + ") WHERE week_start = ?", parameters=(w,)))
    regions = dashboard.build_regional_movement_model(snapshot(week), snapshot(previous))
    ids = dict(queries.run_sql("SELECT region, region_id FROM dim_region").itertuples(index=False))
    frame = overview.region_moves(regions, ids)
    assert [ids[r] for r in frame["region"]] == sorted((ids[r] for r in frame["region"]), key=overview.REGION_ORDER.index)
    for row in regions:
        if row["total"]:
            line = frame[frame["region"] == row["region"]].iloc[0]
            assert line["up_share"] == pytest.approx(row["up"] / row["total"] * 100)
            assert line["down_share"] == pytest.approx(-row["down"] / row["total"] * 100)


@needs_database
def test_d296_the_inflation_years_chain_to_the_whole_change():
    rows, last = inflation_view.build_family_index(queries.run_sql(inflation_view.SERIES_SQL),
                                                   queries.run_sql("SELECT year, month, food_index FROM ipc_monthly"))
    years = overview.family_years(rows, last)
    summary, ipc_total, _ = inflation_view.summarize_families(rows, last)
    for family, frame in years.groupby("product_group"):
        chained = 1.0
        for change in frame.sort_values("year")["change"]:
            chained *= 1 + change / 100
        total = ipc_total if family == inflation_view.IPC_NAME else summary.set_index("family").loc[family, "total"]
        assert (chained - 1) * 100 == pytest.approx(total, abs=1e-6), family


def test_d296_each_chart_answers_one_question_and_the_cards_grow_with_the_window():
    source = (dashboard.Path(dashboard.__file__)).read_text(encoding="utf-8")
    page = source[source.index("def show_overview_market"):source.index("def build_overview_quality_html")]
    titles = [part.split('", "')[1].split('"')[0] for part in page.split('overview_head("')[1:] + page.split('overview_card("')[1:]
              if '", "' in part.split("\n")[0]]
    assert len(titles) == 12 and all(title.startswith("¿") and title.endswith("?") for title in titles), titles
    css = overview.build_css(charts.get_palette(charts.THEMES[0]))
    assert "min-height:max(calc((100vh - 318px) / 2), 196px) !important" in css
    assert 'st.slider(tr("Semanas"), 4, 12, 6' in page  # the reader chooses how many weeks the heat table shows
    assert dashboard.MENU_BLOCKS[0][2][0] == dashboard.PAGE_OVERVIEW and home_mockup  # first page of the business
