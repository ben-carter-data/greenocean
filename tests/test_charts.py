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


def test_unknown_mode_falls_back_to_the_default_corporativo():
    assert charts.get_palette(None) == charts.PALETTES[charts.MODE_CORPORATE]


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


def test_d059_dumbbell_joins_wholesale_and_each_channel_with_its_gap():
    rows = pd.DataFrame({"channel": ["Feria libre", "Supermercado"],
                         "wholesale_price": [1387.0, 1387.0], "consumer_price": [1569.0, 1990.0],
                         "gap_label": ["+13,2 %", "+43,5 %"]})
    spec = charts.draw_dumbbell(rows, "kilo", charts.MODE_DARK).to_dict()
    marks = [layer["mark"]["type"] for layer in spec["layer"]]
    assert marks == ["rule", "point", "point", "text"]
    assert "$ 1.990" in str(spec)


def test_d059_heatmap_is_one_hue_light_to_dark_in_every_theme():
    rows = pd.DataFrame({"year": [2025, 2025], "month": [1, 2], "value": [0.9, 1.2],
                         "value_label": ["0,90", "1,20"]})
    for mode in charts.THEMES:
        spec = charts.draw_heatmap(rows, mode).to_dict()
        assert spec["encoding"]["color"]["scale"]["range"] == charts.HEAT_RAMPS[mode]
    assert charts.HEAT_RAMPS[charts.MODE_DARK][1] == "#22d3ee"


def test_d059_variation_bars_say_the_direction_with_an_arrow_too():
    rows = pd.DataFrame({"label": ["Tomate", "Papa"], "value": [12.3, -4.5]})
    text = str(charts.draw_variation_bars(rows, charts.MODE_LIGHT).to_dict())
    assert "▲ +12,3 %" in text and "▼ -4,5 %" in text


def test_d059_a_reference_line_can_say_its_name():
    rows = pd.DataFrame({"label": ["A", "B"], "value": [1.2, 0.9], "value_label": ["1,2", "0,9"]})
    spec = charts.draw_horizontal_bars(rows, "Índice", charts.MODE_DARK, reference_value=1,
                                       reference_label="Promedio nacional").to_dict()
    assert "Promedio nacional" in str(spec)


def test_a_change_that_rounds_to_zero_says_it_did_not_move():
    assert charts.describe_weekly_change(0.04) == "Sin cambio frente a la semana anterior"
    assert charts.describe_weekly_change(-0.04) == "Sin cambio frente a la semana anterior"
    assert charts.describe_weekly_change(-1.8).startswith("Bajó 1,8")


def test_chile_map_keeps_all_regions_and_missing_indices_without_mutation():
    import copy
    import json
    geometry = json.loads((Path(__file__).resolve().parent.parent /
                           'bi/assets/chile-regions.geojson').read_text())
    original = copy.deepcopy(geometry)
    rows = pd.DataFrame({'region': ['Región de Coquimbo'], 'regional_index': [1.2], 'price': [1500.]})
    for theme in charts.THEMES:
        spec = charts.draw_chile_map(rows, geometry, theme).to_dict()
        features = spec['data']['values']
        assert len(features) == 16
        known = next(f for f in features if f['properties']['region'] == 'Región de Coquimbo')
        assert known['properties']['index'] == 120 and known['properties']['price'] == 1500
        missing = [f for f in features if f['properties']['status'] == 'Sin dato comparable']
        assert len(missing) == 15 and all(f['properties']['index'] is None for f in missing)
        assert all(f['properties']['fill'] == charts.get_palette(theme)['grid'] for f in missing)
        assert spec['mark']['invalid'] is None  # Vega must not discard grey regions.
    assert geometry == original
    # D3 spherical projections need clockwise exterior rings, or they draw a globe.
    for feature in geometry['features']:
        for polygon in feature['geometry']['coordinates']:
            outer = polygon[0]
            assert sum(a[0]*b[1] - b[0]*a[1] for a,b in zip(outer,outer[1:])) < 0


def test_regional_zones_show_direction_and_distinguish_missing_from_stable():
    rows = pd.DataFrame({"region": ["Región de Coquimbo", "Región de Valparaíso", "Región del Maule"],
                         "weekly_change": [10., -5., 0.]})
    for theme in charts.THEMES:
        spec = charts.draw_regional_zones(rows, theme).to_dict()
        values = next(iter(spec["datasets"].values()))
        assert len(values) == 16
        cells = {value["label"]: value for value in values}
        assert cells["Coquimbo"]["fill"] == charts.get_palette(theme)["rise"]
        assert cells["Valparaíso"]["fill"] == charts.get_palette(theme)["fall"]
        assert cells["Maule"]["status"] == "Sin cambio"
        assert cells["Arica"]["status"] == "Sin comparación"
        assert cells["Maule"]["fill"] != cells["Arica"]["fill"]


def test_d094_price_context_breaks_lines_at_missing_weeks_and_does_not_start_at_zero():
    rows = pd.DataFrame({"week_start": pd.to_datetime(["2026-09-21", "2026-09-28", "2026-10-05"]),
                         "channel": ["Feria libre"] * 3, "price": [1200., None, 1500.],
                         "p25": [1000., 1000., 1100.], "p75": [1300., 1300., 1400.],
                         "state": ["dentro", None, "sobre"]})
    for theme in charts.THEMES:
        spec = charts.draw_price_context(rows, theme).to_dict()
        text = str(spec)
        assert "'zero': False" in text and "'type': 'area'" in text
        lines = next(values for values in spec["datasets"].values()
                     if values and "segment" in values[0] and len(values) == 2)
        # The missing week starts a new segment: the line is not drawn across it.
        assert lines[0]["segment"] != lines[1]["segment"]
        assert "Feria: sobre lo habitual" in text


def test_d094_full_history_has_lines_only_and_gaps_for_missing_weeks():
    rows = pd.DataFrame({"week_start": pd.to_datetime(["2026-01-05", "2026-01-19"]),
                         "channel": ["Feria libre", "Feria libre"], "national_price": [100., 120.]})
    spec = charts.draw_full_history(rows, charts.MODE_LIGHT).to_dict()
    assert spec["mark"]["type"] == "line" and "area" not in str(spec)
    values = next(iter(spec["datasets"].values()))
    assert len({row["segment"] for row in values}) == 2


def test_d094_seasonal_pattern_marks_this_month_solid_and_the_next_two_outlined():
    pattern = {month: 100. + month for month in range(1, 13)}
    spec = charts.draw_seasonal_pattern(pattern, "Feria libre", 11, charts.MODE_LIGHT).to_dict()
    values = next(iter(spec["datasets"].values()))
    kinds = {row["month"]: row["kind"] for row in values}
    assert kinds[11] == "actual" and kinds[12] == "proximo" and kinds[1] == "proximo" and kinds[2] == "otro"
    assert {row["fill"] for row in values if row["kind"] == "actual"} == {"#2563C9"}


def test_geographic_changes_keep_boundaries_and_missing_distinct_from_zero():
    import json
    geometry = json.loads((Path(__file__).resolve().parent.parent / 'bi/assets/chile-regions.geojson').read_text())
    rows = pd.DataFrame({'region': ['Región de Coquimbo', 'Región de Valparaíso', 'Región del Maule'],
                         'weekly_change': [10., -5., 0.], 'price': [100., 200., 300.]})
    for theme in charts.THEMES:
        for full in (False, True):
            spec = charts.draw_regional_change_map(rows, geometry, theme, full).to_dict()
            map_spec = spec['layer'][0] if full else spec
            features = map_spec.get('data', {}).get('values')
            if features is None:
                features = spec['datasets'][map_spec['data']['name']]
            assert len(features) == 16
            props = {f['properties']['region']: f['properties'] for f in features}
            assert props['Región de Coquimbo']['fill'] == charts.get_palette(theme)['rise']
            assert props['Región de Valparaíso']['fill'] == charts.get_palette(theme)['fall']
            assert props['Región del Maule']['status'] == 'Sin cambio'
            assert sum(p['weekly_change'] is None for p in props.values()) == 13
            assert len(spec['projection']['fit']['features']) == (32 if full else 3)
    assert 'weekly_change' not in geometry['features'][0]['properties']
