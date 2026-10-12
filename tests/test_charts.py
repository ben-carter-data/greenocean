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


def test_every_known_channel_has_its_own_fixed_color_in_both_modes():
    for mode in [charts.MODE_DARK, charts.MODE_LIGHT]:
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
