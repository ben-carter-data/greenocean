"""Market views preserve comparable prices, gaps, counts and the existing palette."""
import pandas as pd
import pytest

from bi import charts, market_charts


def product_rows():
    return pd.DataFrame({
        "product_group": ["Hortalizas"] * 3, "product": ["Tomate"] * 3,
        "variety": ["Larga vida"] * 3, "quality": ["Primera"] * 3,
        "normalized_unit": ["kilo"] * 3,
        "region": ["Región del Maule", "Región de Valparaíso", "Región del Maule"],
        "channel": ["Feria libre", "Feria libre", "Supermercado"],
        "regional_index": [.8, 1.2, 1.1], "price": [800., 1200., 2200.],
        "national_price": [1000., 1000., 2000.],
        "week_start": pd.to_datetime(["2026-10-05"] * 3)})


@pytest.mark.parametrize("mode", charts.THEMES)
def test_3d_height_is_relative_to_each_channel_and_preserves_real_prices(mode):
    figure = market_charts.draw_regional_3d(product_rows(), mode, "tomate-kilo")
    points = [trace for trace in figure.data if trace.mode == "markers"]
    assert sorted(value for trace in points for value in trace.z) == pytest.approx([80, 110, 120])
    for trace in points:
        assert trace.marker.color == charts.get_channel_color(trace.name, mode)
    assert {tuple(point[3:6]) for trace in points for point in trace.customdata} == {
        ("800", "1.000", "kilo"), ("1.200", "1.000", "kilo"), ("2.200", "2.000", "kilo")}
    assert figure.layout.uirevision == "tomate-kilo"


def test_donut_counts_observations_instead_of_summing_incomparable_prices():
    rows = product_rows()
    rows.loc[2, "product_group"] = "Frutas"
    figure = market_charts.draw_group_share(rows, charts.MODE_DARK)
    counts = dict(zip(figure.data[0].labels, figure.data[0].values))
    assert counts == {"Hortalizas": 2, "Frutas": 1}


def test_timeline_does_not_invent_a_price_for_a_missing_week():
    rows = product_rows().iloc[:2].copy()
    rows["week_start"] = pd.to_datetime(["2026-09-21", "2026-10-05"])
    rows["national_price"] = [1000., 1200.]
    figure = market_charts.draw_price_trend(rows, charts.MODE_DARK, "tomate-kilo")
    trace = figure.data[0]
    assert tuple(trace.y) == (1000., None, 1200.)
    assert not trace.connectgaps
    assert trace.fill != "tonexty"  # Channel prices must never stack.


@pytest.mark.parametrize("draw", [market_charts.draw_regional_3d,
                                  market_charts.draw_regional_heatmap,
                                  market_charts.draw_price_trend])
def test_product_views_reject_mixed_units(draw):
    rows = product_rows()
    rows.loc[1, "normalized_unit"] = "unidad"
    with pytest.raises(ValueError, match="unidad"):
        draw(rows, charts.MODE_DARK, "mixed")


def test_heatmap_keeps_an_unobserved_region_channel_pair_missing():
    figure = market_charts.draw_regional_heatmap(product_rows(), charts.MODE_DARK, "tomate-kilo")
    assert pd.isna(figure.data[0].z).sum() == 1
    assert not figure.data[0].hoverongaps
