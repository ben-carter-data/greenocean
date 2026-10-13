"""Tests for the chart helpers: number formats, region names and channel colors."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts  # noqa: E402
from etl import etl  # noqa: E402


def test_numbers_are_written_as_in_chile():
    assert charts.format_thousands(1234567.4) == "1.234.567"
    assert charts.format_percent(60.06) == "60,1 %"
    assert charts.format_signed_percent(-14.46) == "-14,5 %"
    assert charts.format_index(1.234) == "1,23"


def test_region_names_lose_their_prefix():
    assert charts.shorten_region_name("Región de La Araucanía") == "La Araucanía"
    assert charts.shorten_region_name("Región del Maule") == "Maule"
    assert charts.shorten_region_name(
        "Región Metropolitana de Santiago") == "Metropolitana de Santiago"


def test_every_known_channel_has_its_own_fixed_color_in_every_theme():
    for mode in charts.THEMES:
        channel_colors = charts.PALETTES[mode]["channels"]
        assert set(channel_colors) == etl.KNOWN_CHANNELS
        assert len(set(channel_colors.values())) == len(channel_colors)


def test_color_follows_the_channel_whatever_channels_are_shown():
    scale = charts.build_channel_color_scale(["Supermercado", "Feria libre"],
                                             charts.MODE_DARK).to_dict()
    channel_colors = charts.PALETTES[charts.MODE_DARK]["channels"]
    assert dict(zip(scale["domain"], scale["range"])) == {
        "Feria libre": channel_colors["Feria libre"],
        "Supermercado": channel_colors["Supermercado"]}


def test_unknown_mode_falls_back_to_dark():
    assert charts.get_palette(None) == charts.PALETTES[charts.MODE_DARK]


def test_variation_bars_use_red_for_rises_and_blue_for_falls():
    rows = pd.DataFrame({"label": ["Lechuga", "Ajo"], "value": [49.9, -14.5]})
    chart = charts.draw_variation_bars(rows, charts.MODE_LIGHT).to_dict()
    # The chart keeps its rows in "datasets"; the reference line has its own.
    colors = {row["label"]: row["color"]
              for dataset in chart["datasets"].values() for row in dataset
              if "label" in row}
    palette = charts.PALETTES[charts.MODE_LIGHT]
    assert colors == {"Lechuga": palette["rise"], "Ajo": palette["fall"]}


def test_numbers_are_explained_in_plain_words():
    assert charts.describe_weekly_change(49.9) == "Subió 49,9 % frente a la semana anterior"
    assert charts.describe_weekly_change(-0.4) == "Bajó 0,4 % frente a la semana anterior"
    assert charts.describe_regional_index(1.46) == "46 % más caro que el promedio nacional"
    assert charts.describe_regional_index(0.66) == "34 % más barato que el promedio nacional"
    assert charts.describe_margin(145) == "El consumidor paga 2,45 veces el precio mayorista"
    assert charts.describe_channel_gap(62.7, "Feria libre") == (
        "62,7 % más caro que Feria libre")


def test_negative_bar_labels_are_written_right_of_zero_not_over_the_names():
    rows = pd.DataFrame({"label": ["Supermercado", "Feria libre"], "value": [131.0, -3.5],
                         "value_label": ["+131,0 %", "-3,5 %"]})
    chart = charts.draw_horizontal_bars(rows, "Diferencia (%)", charts.MODE_DARK).to_dict()
    negative_layer = [layer for layer in chart["layer"]
                      if layer.get("transform") == [{"filter": "datum.value < 0"}]][0]
    assert negative_layer["encoding"]["x"] == {"datum": 0}
    assert negative_layer["mark"]["align"] == "left"


def test_bar_axis_leaves_room_for_the_labels_on_both_sides():
    domain = charts.calculate_bar_domain(pd.Series([131.0, -3.5]))
    assert domain[0] < -3.5
    assert domain[1] > 131.0
    assert charts.calculate_bar_domain(pd.Series([2.0, 5.0]))[0] == 0


def test_numbers_that_round_to_zero_have_no_minus_sign():
    assert charts.format_index(-0.001) == "0,00"
    assert charts.format_percent(-0.04) == "0,0 %"


def test_lags_are_written_in_plain_words():
    assert charts.describe_weeks(0) == "la misma semana"
    assert charts.describe_weeks(1) == "1 semana"
    assert charts.describe_weeks(3) == "3 semanas"


def test_every_chart_writes_numbers_and_months_as_in_chile():
    rows = pd.DataFrame({"week_start": pd.to_datetime(["2024-03-04", "2024-03-11"]),
                         "channel": ["Feria libre", "Feria libre"], "value": [1000.0, 1100.0]})
    chart = charts.draw_weekly_lines(rows, "$/kilo", rows["value"].astype(str),
                                     charts.MODE_DARK, is_money=True).to_dict()
    assert chart["config"]["locale"]["number"]["decimal"] == ","
    assert chart["config"]["locale"]["time"]["shortMonths"][2] == "mar"
    assert charts.WEEK_AXIS_FORMAT == "%b %Y"


def test_bars_can_keep_the_order_they_arrive_in():
    rows = pd.DataFrame({"label": ["0", "1", "2"], "value": [0.1, 0.5, 0.3],
                         "value_label": ["0,10", "0,50", "0,30"]})
    chart = charts.draw_horizontal_bars(rows, "Correlación", charts.MODE_DARK,
                                        is_sorted_by_value=False).to_dict()
    assert chart["layer"][0]["encoding"]["y"]["sort"] == ["0", "1", "2"]


def test_t44_three_themes_share_the_validated_channel_colors_of_their_base():
    """Vantablack is dark; Corporativo and Claro are light. Only surfaces, ink and
    accent change: the channel colors stay the ones validated for color blindness."""
    assert charts.THEMES == ["Vantablack", "Corporativo", "Claro"]
    keys = set(charts.PALETTES[charts.MODE_DARK])
    for theme in charts.THEMES:
        palette = charts.PALETTES[theme]
        assert set(palette) == keys
        expected = (charts.DARK_CHANNELS if palette["base"] == charts.BASE_DARK
                    else charts.LIGHT_CHANNELS)
        assert palette["channels"] == expected
    assert charts.PALETTES[charts.MODE_DARK]["base"] == charts.BASE_DARK
    assert {charts.PALETTES[theme]["base"] for theme in
            [charts.MODE_CORPORATE, charts.MODE_LIGHT]} == {charts.BASE_LIGHT}
