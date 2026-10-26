"""Tests for the chart helpers: number formats, region names and channel colors."""
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts  # noqa: E402
from etl import etl  # noqa: E402


def test_numbers_are_written_as_in_chile():
    assert charts.format_thousands(1234567.4) == "1.234.567"
    assert charts.format_percent(60.06) == "60,1 %"
    assert charts.format_signed_percent(-14.46) == "-14,5 %"
    assert charts.format_index(1.234) == "1,23"


def test_every_known_channel_has_its_own_fixed_color_in_every_theme():
    for mode in charts.THEMES:
        channel_colors = charts.PALETTES[mode]["channels"]
        assert set(channel_colors) == etl.KNOWN_CHANNELS
        assert len(set(channel_colors.values())) == len(channel_colors)


def test_unknown_mode_falls_back_to_the_default_corporativo():
    assert charts.get_palette(None) == charts.PALETTES[charts.MODE_CORPORATE]


def test_numbers_that_round_to_zero_have_no_minus_sign():
    assert charts.format_index(-0.001) == "0,00"
    assert charts.format_percent(-0.04) == "0,0 %"


def test_lags_are_written_in_plain_words():
    assert charts.describe_weeks(0) == "la misma semana"
    assert charts.describe_weeks(1) == "1 semana"
    assert charts.describe_weeks(3) == "3 semanas"


def test_visible_themes_keep_legacy_light_palette_compatible():
    """Vantablack and Dark Grey are dark; Corporativo, Blue Light and Claro are light."""
    assert charts.THEMES == ["Corporativo", "Vantablack", "Blue Light", "Dark Grey"]
    keys = set(charts.PALETTES[charts.MODE_DARK])
    for theme in charts.THEMES:
        palette = charts.PALETTES[theme]
        assert set(palette) == keys
        expected = (charts.DARK_CHANNELS if palette["base"] == charts.BASE_DARK
                    else charts.LIGHT_CHANNELS)
        assert palette["channels"] == expected
    assert {charts.PALETTES[theme]["base"] for theme in
            [charts.MODE_DARK, charts.MODE_GRAPHITE]} == {charts.BASE_DARK}
    assert {charts.PALETTES[theme]["base"] for theme in
            [charts.MODE_CORPORATE, charts.MODE_BLUE_LIGHT, charts.MODE_LIGHT]} == {
                charts.BASE_LIGHT}

