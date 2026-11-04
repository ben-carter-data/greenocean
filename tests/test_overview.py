"""«Dashboard» (D-296): the macro view repeats no figure of its own; each one is the Resumen's, the Precios e inflación
page's or Controles de datos's, recomputed here from the same tables."""

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


def test_d308_the_dashboard_is_gone_and_its_pieces_have_a_place():
    source = (dashboard.Path(dashboard.__file__)).read_text(encoding="utf-8")
    assert "def show_overview_page" not in source and "def show_overview_inflation" not in source
    # D-453: the section opens with its dashboards as tiles; D-494: «Último dato por canal» became step 2 of Semanal
    # D-456: and «Análisis BA y BI», whose tabs hold «Interesados» (D-376), the method (D-377), «Precios e inflación»
    # (D-398) and «Insights»
    assert dashboard.MENU_BLOCKS[0][2] == [
        dashboard.HOME_PAGE,
        dashboard.PAGE_BA,
    ]  # D-325: «Dónde comprar» is gone
    assert dashboard.DOOR_PAGES == {}  # D-398: «Precios e inflación» left the Dashboard's header for the menu
    assert dashboard.RETIRED_VIEWS["Dashboard general"] == dashboard.HOME_PAGE
    # D-490: the table of the last weeks left «Semanal», with its selector
    assert "def show_weeks_table" not in source and "HOME_VIEWS" not in source
    assert charts.get_palette(charts.THEMES[0]) and home_mockup


@needs_database
def test_d325_where_to_buy_is_gone_and_its_old_address_opens_the_panorama():
    source = dashboard.Path(dashboard.__file__).read_text(encoding="utf-8")
    assert "show_where_page" not in source and "PAGE_WHERE" not in source
    assert [name for _, _, pages in dashboard.MENU_BLOCKS[:1] for name in pages] == [
        dashboard.HOME_PAGE,  # D-442
        dashboard.PAGE_BA,  # D-456
    ]
    assert "Dónde comprar" not in dashboard.SIDEBAR_LABELS.values()
    assert dashboard.RETIRED_VIEWS["Dónde comprar"] == dashboard.HOME_PAGE
    # The names of the page's helpers are gone from the module; what the Insights read of the points file stays.
    for name in ("build_regions_html", "build_region_column", "regional_price_levels", "house_image", "mini_map"):
        assert not hasattr(overview, name), name
    assert overview.read_points() and overview.point_icon("mercado")
    from streamlit.testing.v1 import AppTest

    for language in ("es", "en"):
        app = AppTest.from_file(str(dashboard.Path(dashboard.__file__)), default_timeout=60)
        app.query_params.update({"vista": "Dónde comprar", "perfil": "profesional", "lang": language})
        app.run()
        assert not app.exception
        markup = " ".join(block.value for block in app.sidebar.markdown)
        assert "Where to buy" not in markup and "Dónde comprar" not in markup
        assert [link.proto.label for link in app.sidebar.get("page_link")][:2] in (
            ["Semanal", "Análisis BA y BI"],  # D-456, D-459, D-494: the section's two dashboards
            ["Weekly", "BA and BI analysis"],
        )


@needs_database
def test_d478_the_insights_name_the_family_of_each_product(market):
    _, variations, week = market
    drops = overview.best_drops(variations, week)
    assert drops and all(len(drop) == 4 for drop in drops)
    for product, _, _, family in drops:
        # D-482: the label carries the variety after the product's name
        named = variations["product"].map(lambda name: product == name or product.startswith(f"{name} "))
        assert family in set(variations.loc[named, "product_group"])
    line = next(
        text
        for text in overview.consumer_insights(
            overview.family_moves(*market), drops, overview.pd.DataFrame(columns=["verdict", "family"]), 0.0, 0.0
        )
        if text.startswith("Las mayores bajas")
    )
    assert all(f"{product} · {home_mockup.short_family(family)}" in line for product, _, _, family in drops)
