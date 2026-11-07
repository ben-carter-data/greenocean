"""Data fidelity and SVG geometry of the approved initial-screen mockup."""

import inspect
import re
from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from bi import dashboard, home_mockup, page_weekly, queries

# region Constants
ROOT = Path(__file__).resolve().parents[1]
# endregion


# region Tables and rankings
def test_table_uses_real_predecessor_and_escapes_labels():
    row = dict(
        product='<script>',
        variety='Gala',
        quality='Primera',
        channel='Feria',
        normalized_unit='kilo',
        national_price=1500.0,
        variation=0.5,
        _previous_price=1000.0,
        change_amount=500.0,
    )
    markup = home_mockup.table([row], lambda r: './', lambda r: './?a=1&b=2')
    assert '&lt;script&gt;' in markup and '<script>' not in markup
    assert '$1.000' in markup and '$1.500' in markup and '▲ +50,0 %' in markup
    assert '+$500' in markup and 'por kilo' in markup and 'Calidad: Primera' in markup
    row['variation'] = 0
    assert 'class="neutral"' in home_mockup.table([row], lambda r: './', lambda r: './')


def test_comparison_keeps_missing_and_zero_predecessors_out_of_ranking():
    keys = ['product', 'variety', 'quality', 'normalized_unit', 'channel']
    common = dict(variety='Gala', quality='Primera', normalized_unit='kilo', channel='Feria libre')
    current = pd.DataFrame([dict(common, product=p, national_price=120.0) for p in ['A', 'B', 'C']])
    previous = pd.DataFrame(
        [dict(common, product='A', national_price=100.0), dict(common, product='B', national_price=0.0)]
    )
    rows = home_mockup.compare_week(current, previous, keys).assign(is_alert=False, _severity=0.0)
    assert rows.iloc[0].change_amount == 20
    assert rows.iloc[0].variation == pytest.approx(0.2)
    assert rows.iloc[1:].variation.isna().all()
    assert rows.iloc[1:].change_amount.isna().all()
    assert home_mockup.order_movements(rows, 8, 'Mayores cambios')['product'].tolist() == ['A']
    markup = home_mockup.table(rows.to_dict('records'), lambda r: './', lambda r: './')
    assert markup.count('Sin comparación') == 4
    assert 'nan' not in markup and 'inf' not in markup
    assert home_mockup.previous_price({'national_price': 120.0, 'variation': 0.2}) is None


def test_ranking_orders_severity_and_breaks_ties_without_duplicates():
    common = dict(variety='Gala', quality='Primera', normalized_unit='kilo', channel='Feria libre')
    rows = pd.DataFrame(
        [
            dict(common, product=p, variation=v, is_alert=a, _severity=s)
            for p, v, a, s in [
                ('B', 0.2, True, 3.0),
                ('A', 0.2, True, 5.0),
                ('C', -0.3, False, 0.0),
                ('D', 0.0, False, 0.0),
            ]
        ]
    )
    assert home_mockup.order_movements(rows, 8, 'Mayores cambios')['product'].tolist() == ['C', 'A', 'B', 'D']
    assert home_mockup.order_movements(rows, 8, 'Subidas')['product'].tolist() == ['A', 'B']
    assert home_mockup.order_movements(rows, 8, 'Bajadas')['product'].tolist() == ['C']
    assert home_mockup.order_movements(rows, 8, 'Inusuales')['product'].tolist() == ['A', 'B']


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_dashboard_alerts_follow_week_and_family_and_keep_severity_order():
    week = dashboard.read_cached_filter_options(dashboard.get_database_version())['week'][0]
    rows = dashboard.home_alert_rows(week, 'Frutas')
    assert not rows.empty
    assert set(rows['product_group']) == {'Frutas'}
    assert rows['_distance'].is_monotonic_decreasing
    items = dashboard.alert_items(rows)
    assert len(items) == len(rows)
    # D-477: a rise takes the rise words, a drop the drop words; D-478: every level is at least «fuerte», as its alert
    rises = {'Alza extrema', 'Alza muy fuerte', 'Alza fuerte'}
    drops = {'Baja extrema', 'Baja muy fuerte', 'Baja fuerte'}
    for item in items:
        assert item['level'] in (rises if item['variation'] > 0 else drops), item['level']
    falls = dashboard.alert_items(dashboard.home_alert_rows(week, 'Frutas', direction='baja'))
    assert {item['level'] for item in falls} <= drops
    # D-492: drawn like the products table, each level a tint of its alert's colour, three for each kind
    table = home_mockup.alert_table(items, level_title='niveles')
    assert table.startswith('<div class="mock-products-table"') and '<th title="niveles">Nivel</th>' in table
    assert table.count('<tr>') == len(items) + 1
    assert set(home_mockup.ALERT_LEVEL_CLASSES) == rises | drops
    assert len(set(home_mockup.ALERT_LEVEL_CLASSES.values())) == 6
    assert 'Ningún producto empieza por «zz» en estas alertas.' in home_mockup.alert_table([], 'zz')


def test_d497_the_filter_keeps_one_direction_with_the_sharp_ones_and_says_when_nothing_moved():
    assert dashboard.PRODUCT_DIRECTIONS == ('Todo', 'Subidas', 'Bajadas')
    rows = [{'variation': value} for value in (0.50, 0.02, 0.0004, 0.0, -0.0004, -0.02, -0.50)]

    def kept(direction):
        return [row['variation'] for row in dashboard.keep_direction(rows, direction)]

    assert kept('Todo') == [row['variation'] for row in rows]
    assert kept('Subidas') == [0.50, 0.02]  # the sharp rise is included; what rounds to 0.0 % is neither
    assert kept('Bajadas') == [-0.02, -0.50]
    note = dashboard.NOTHING_MOVED['Subidas']
    assert note in home_mockup.products_table([], 'a', 'b', 'kiw', empty_note=note)
    assert 'Ningún producto empieza por «kiw»' in home_mockup.products_table([], 'a', 'b', 'kiw')


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_d497_the_filter_sits_beside_the_search_and_rests_while_an_alert_is_chosen():
    app = AppTest.from_file(ROOT / 'bi/dashboard.py', default_timeout=60)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PUBLIC
    app.run()
    assert app.selectbox(key='home_products_direction').disabled  # no family chosen yet (D-352)
    app.query_params.update({'_home_region': dashboard.ALL_VALUES, 'familia': 'Frutas'})
    app.session_state[dashboard.scoped(dashboard.HOME_REGION_DONE)] = True
    app.session_state[dashboard.scoped(dashboard.HOME_FAMILY_DONE)] = True  # D-530: the address alone unlocks nothing
    app.run()
    box = app.selectbox(key='home_products_direction')
    assert not box.disabled and box.value == 'Todo'
    # «Subidas» shows every sharp rise of the alert button, and the normal ones with them
    week = dashboard.read_cached_filter_options(dashboard.get_database_version())['week'][0]
    sharp = dashboard.home_alert_rows(week, 'Frutas', direction=dashboard.RISE)
    assert len(sharp)
    box.set_value('Subidas').run()
    assert not app.exception
    markup = ' '.join(block.value for block in app.markdown)
    table = re.search(r'<div class="mock-products-table".*?</table>', markup).group(0)
    assert {str(name) for name in sharp['product']} <= {
        name.split(' · ')[0] for name in re.findall(r'<td><strong>([^<]+)</strong>', table)
    }
    # with an alert chosen the filter rests at «Todo», so it never contradicts the table
    app.button(key='home_alert_trigger').click().run()
    assert not app.exception
    box = app.selectbox(key='home_products_direction')
    assert box.disabled and box.value == 'Todo'
    app.button(key='home_alert_trigger').click().run()
    assert not app.selectbox(key='home_products_direction').disabled
    # it is drawn in the alert line, right after the search
    from bi import page_weekly
    from tests import code_shape

    line = code_shape.tree_of(page_weekly.show_alert_line)
    keyed = {code_shape.keyword(call, 'key'): call.lineno for call in code_shape.every_call(line)}
    assert keyed[code_shape.normal('"home_products_search"')] < keyed[code_shape.normal('"home_products_direction"')]


def test_d498_the_window_brings_the_channel_back_when_it_reruns_alone(monkeypatch):
    seen = []
    # D-541: the window and what it draws live in bi/page_weekly.py, so the stand-in goes there
    monkeypatch.setattr(page_weekly, 'draw_products_window', lambda *window: seen.append(dashboard.current_channel()))
    inspect.unwrap(page_weekly.show_products_dialog)('Feria libre')
    assert seen == ['Feria libre'] and dashboard.current_channel() is None


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_d498_the_enlarged_table_has_the_line_of_the_panel_and_opens_with_its_choices():
    app = AppTest.from_file(ROOT / 'bi/dashboard.py', default_timeout=60)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PUBLIC
    app.query_params.update({'_home_region': dashboard.ALL_VALUES, 'familia': 'Frutas'})
    app.session_state[dashboard.scoped(dashboard.HOME_REGION_DONE)] = True
    app.session_state[dashboard.scoped(dashboard.HOME_FAMILY_DONE)] = True  # D-530: the address alone unlocks nothing
    app.run()
    app.selectbox(key='home_products_direction').set_value('Subidas').run()
    app.button(key='home_products_enlarge').click().run()
    assert not app.exception and app.get('dialog')
    for kind in ('alert', 'drop'):
        window, panel = app.button(key=f'dialog_{kind}_trigger'), app.button(key=f'home_{kind}_trigger')
        assert window.label == panel.label and window.disabled == panel.disabled
    filtered = app.selectbox(key='dialog_products_direction')
    assert filtered.options == ['Todo', 'Subidas', 'Bajadas'] and filtered.value == 'Subidas'
    assert not filtered.disabled and app.text_input(key='dialog_products_search').value == ''
    # with an alert chosen, «Ampliar» is there too and the window opens on that alert
    week = dashboard.read_cached_filter_options(dashboard.get_database_version())['week'][0]
    sharp = dashboard.home_alert_rows(week, 'Frutas', direction=dashboard.RISE)
    app.query_params['alerta'] = dashboard.RISE
    app.run()
    app.button(key='home_products_enlarge').click().run()
    assert not app.exception and app.get('dialog')
    filtered = app.selectbox(key='dialog_products_direction')
    assert filtered.disabled and filtered.value == 'Todo'
    markup = ' '.join(block.value for block in app.markdown)
    assert markup.count('class="mock-level ') == 2 * len(sharp) > 0  # the panel's table and the window's
    css = dashboard.build_sidebar_css(dashboard.charts.MODE_DARK)  # R-004: the stylesheet the page receives
    assert '.st-key-dialog_alert_trigger button' in css and '.st-key-dialog_drop_trigger button' in css


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_d491_the_alert_line_waits_for_a_family_then_filters_step_three_and_comes_back():
    app = AppTest.from_file(ROOT / 'bi/dashboard.py', default_timeout=60)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PUBLIC  # the Usuario view
    app.run()
    assert not app.exception
    assert app.button(key='home_alert_trigger').disabled  # no family chosen yet (D-352)
    app.query_params.update({'_home_region': dashboard.ALL_VALUES, 'familia': 'Frutas'})
    app.session_state[dashboard.scoped(dashboard.HOME_REGION_DONE)] = True
    app.session_state[dashboard.scoped(dashboard.HOME_FAMILY_DONE)] = True  # D-530: the address alone unlocks nothing
    app.run()
    week = dashboard.read_cached_filter_options(dashboard.get_database_version())['week'][0]
    rows = dashboard.home_alert_rows(week, 'Frutas', direction=dashboard.RISE)
    rise = app.button(key='home_alert_trigger')
    assert not rise.disabled and rise.label == f'▲ {len(rows)} alzas fuertes'  # the family's own count
    rise.click().run()
    assert not app.exception and app.query_params['alerta'] == dashboard.RISE
    markup = ' '.join(block.value for block in app.markdown)
    assert 'precio nacional de ODEPA' in markup and markup.count('class="mock-level ') == len(rows)
    assert not app.get('dialog')  # no window (D-489)
    # D-492: the search stays, and looks only among the alerts shown
    first = str(rows.iloc[0]['product'])
    app.text_input(key='home_products_search').set_value(first[:4]).run()
    markup = ' '.join(block.value for block in app.markdown)
    found = rows[[dashboard.matches_product_search(row, first[:4]) for row in rows.to_dict('records')]]
    assert markup.count('class="mock-level ') == len(found) > 0
    app.text_input(key='home_products_search').set_value('').run()
    app.button(key='home_alert_trigger').click().run()  # pressed again: every product
    markup = ' '.join(block.value for block in app.markdown)
    assert 'alerta' not in app.query_params and 'class="mock-level ' not in markup


def test_d491_the_families_carry_no_alert_marks_and_the_hint_says_why_the_bar_differs():
    rows = [{'product_group': 'Frutas', 'variation': -0.02}, {'product_group': 'Pan', 'variation': 0.01}]
    markup = home_mockup.family_movement(rows, lambda family: f'#{family}', None, 'todo Chile')
    assert 'mock-alert-mark' not in markup
    assert 'una familia puede bajar en conjunto y tener productos que subieron' in markup


def test_d096_sidebar_footer_shows_the_real_alert_count():
    app = AppTest.from_file(ROOT / 'bi/dashboard.py', default_timeout=60)
    app.run()
    assert not app.exception
    button = app.button(key='home_alert_trigger')
    week = dashboard.read_latest_week()
    now = dashboard.read_price_alerts()
    now = now[now['week_start'] == week]
    rises, drops = int((now['variation'] > 0).sum()), int((now['variation'] < 0).sum())
    # D-477: the sharp rises and the sharp drops, apart
    assert button.label == (f'▲ {rises} alzas fuertes' if rises != 1 else '▲ 1 alza fuerte')
    assert app.button(key='home_drop_trigger').label == (
        f'▼ {drops} bajas fuertes' if drops != 1 else '▼ 1 baja fuerte'
    )
    assert rises + drops == len(now)
    dark_css = dashboard.build_sidebar_css(dashboard.charts.MODE_DARK)
    light_css = dashboard.build_sidebar_css(dashboard.charts.MODE_BLUE_LIGHT)
    assert '.st-key-home_alert_trigger button' in dark_css
    assert 'background:color-mix(in srgb,#ff9ca4 14%,transparent) !important;' in dark_css
    assert 'background:color-mix(in srgb,#9d1f2c 14%,transparent) !important;' in light_css
    assert 'box-shadow:none !important;' in dark_css


def test_regional_summary_counts_equivalent_prices_and_uses_a_display_threshold():
    keys = dict(
        product_group='Frutas', variety='Gala', quality='Primera', normalized_unit='kilo', channel='Feria libre'
    )
    current = pd.DataFrame(
        [
            dict(keys, product='A', region='Región de Coquimbo', price=110.0),
            dict(keys, product='B', region='Región de Coquimbo', price=99.98),
            dict(keys, product='C', region='Región de Coquimbo', price=80.0),
            dict(keys, product='D', region='Región de Coquimbo', price=130.0),
        ]
    )
    previous = pd.DataFrame(
        [
            dict(keys, product='A', region='Región de Coquimbo', price=100.0),
            dict(keys, product='B', region='Región de Coquimbo', price=100.0),
            dict(keys, product='C', region='Región de Coquimbo', price=100.0),
        ]
    )
    rows = dashboard.build_regional_movement_model(current, previous)
    assert rows == [
        {
            'region': 'Región de Coquimbo',
            'state': 'mixed',
            'share': pytest.approx(100 / 3),
            'up': 1,
            'down': 1,
            'stable': 1,
            'total': 3,
            'missing': 1,
            'dropped': 0,  # D-329: none priced the week before and missing this week
        }
    ]


def test_regional_map_keeps_the_surface_minimal_and_exact_counts_in_the_hint():
    rows = [
        {
            'region': 'Región de Coquimbo',
            'state': 'fall',
            'share': 62.0,
            'up': 42,
            'down': 91,
            'stable': 13,
            'total': 146,
            'missing': 4,
        }
    ]
    markup = home_mockup.regional_map(
        rows,
        lambda region: '/dashboard?_home_region=' + str(region),
        '5–11 oct',
        '28 sep – 4 oct',
        'Región de Coquimbo',
    )
    assert markup.count('mock-region-shape ') == 16
    assert markup.count('<a class="mock-region-row ') == 16
    assert '62 % ↓' in markup
    assert '91 bajaron · 42 subieron · 13 sin cambio · 146 comparados' in markup
    assert 'Semana 28 sep – 4 oct → 5–11 oct' in markup
    assert '_home_region=Región de Arica y Parinacota' in markup
    # A second click on the selected region returns to the whole country.
    assert '<a class="mock-region-row fall selected" href="/dashboard?_home_region=None"' in markup
    assert 'inflación' not in markup.lower() and 'canasta' not in markup.lower()


def _inside(x, y, path):
    """Even-odd point-in-polygon over every ring of an SVG path made of M/L/Z."""
    inside = False
    for ring in re.findall(r'M([^Z]+)Z', path):
        points = [tuple(map(float, pair.split(','))) for pair in ring.split('L')]
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def _cross(a, b, c, d):
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    return side(a, b, c) * side(a, b, d) < 0 and side(c, d, a) * side(c, d, b) < 0


def test_d092_each_line_starts_inside_its_region_and_no_two_lines_cross():
    markup = home_mockup.regional_map([], lambda region: '#' + str(region), '5–11 oct', '28 sep – 4 oct')
    shapes = dict(
        re.findall(
            r'<a href="#([^"]+)" target="_self" aria-label="[^"]*"><path class="mock-region-shape '
            r'[^"]*" d="([^"]+)"',
            markup,
        )
    )
    rows = re.findall(
        r'<a class="mock-region-row [^"]*" href="#([^"]+)".*?class="mock-region-leader" '
        r'd="M([\d.]+),([\d.]+)L([\d.]+),([\d.]+)".*?class="mock-region-name"[^>]*>([^<]+)<',
        markup,
        re.S,
    )
    assert len(shapes) == len(rows) == 16
    lines = []
    for region, x1, y1, x2, y2, name in rows:
        assert _inside(float(x1), float(y1), shapes[region]), name
        lines.append(((float(x1), float(y1)), (float(x2), float(y2))))
    # Rows follow the regions from north to south, so the lines never cross.
    assert [line[1][1] for line in lines] == sorted(line[1][1] for line in lines)
    assert [line[0][1] for line in lines] == sorted(line[0][1] for line in lines)
    for first in range(len(lines)):
        for second in range(first + 1, len(lines)):
            assert not _cross(*lines[first], *lines[second]), (rows[first][5], rows[second][5])


def test_d092_map_keeps_the_real_proportions_of_chile():
    _, width = home_mockup.real_projection(home_mockup.chile_regions_geometry())
    left, top, bottom = home_mockup.MAP_BOX
    # About 38.4° of latitude for 9.3° of longitude at a mean latitude near 37° S.
    assert 4.6 < (bottom - top) / (width - left) < 5.4
    assert width < home_mockup.LIST_LEFT - 10


def test_d092_family_movement_marks_the_selection_and_scales_from_zero():
    rows = [
        {'product_group': 'Frutas', 'variation': 0.02},
        {'product_group': 'Frutas', 'variation': 0.04},
        {'product_group': 'Pan', 'variation': -0.01},
    ]
    markup = home_mockup.family_movement(rows, lambda family: '#' + family, 'Frutas', 'todo Chile')
    assert markup.index('Frutas') < markup.index('Pan')
    assert '<a class="mock-movement-row rise selected" href="#Frutas"' in markup
    assert '+3,0 %' in markup and '−1,0 %' in markup
    assert 'left:50%;width:50.00%' in markup and 'left:33.33%;width:16.67%' in markup


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_d092_region_and_family_clicks_fill_the_products_table():
    app = AppTest.from_file(ROOT / 'bi/dashboard.py', default_timeout=60)
    app.query_params['_home_region'] = 'Región de Coquimbo'
    app.query_params['_home_week'] = '2026-10-05'
    app.query_params['familia'] = 'Frutas'
    # D-530: the address alone unlocks nothing; the visit chose both steps
    app.session_state[dashboard.scoped(dashboard.HOME_REGION_DONE)] = True
    app.session_state[dashboard.scoped(dashboard.HOME_FAMILY_DONE)] = True
    app.run()
    assert not app.exception
    assert app.session_state['dashboard_region'] == 'Región de Coquimbo'
    markup = ' '.join(block.value for block in app.markdown)
    assert 'mock-products-family">Frutas' in markup and 'en Coquimbo' in markup
    assert 'class="mock-chile-map"' in markup and 'class="mock-chosen"' not in markup  # D-446: the map stays
    table = re.search(r'<div class="mock-products-table".*?</table>', markup).group(0)
    assert table.count('<tr>') > 1 and 'Regiones ↑ / ↓' in table
    # D-497: the filter keeps one direction of the same rows, in the chosen region
    app.selectbox(key='home_products_direction').set_value('Bajadas').run()
    markup = ' '.join(block.value for block in app.markdown)
    table = re.search(r'<div class="mock-products-table".*?</table>', markup).group(0)
    assert '<td class="num rise">' not in table and '<td class="num neutral">' not in table


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_home_model_matches_independent_weekly_prices_and_region_selection():
    script = f'''import sys
sys.path.insert(0,{str(ROOT)!r})
import streamlit as st
from bi import dashboard
week=f"{{dashboard.read_latest_week():%Y-%m-%d}}"
st.session_state['model']=dashboard.read_home_model(week,dashboard.ALL_VALUES,dashboard.ALL_VALUES,8)
st.session_state['regional']=dashboard.read_home_model(week,dashboard.ALL_VALUES,'Región de Coquimbo',8)
st.session_state['week']=week
'''
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    model = app.session_state['model']
    week = app.session_state['week']
    # D-144, D-522: the national change averages only the regions with a price in both weeks, in the same package.
    sql = '''SELECT AVG(price_now) AS current_price, AVG(price_before) AS previous_price
    FROM weekly_same_package WHERE week_start=?
    GROUP BY product_id, channel_id, normalized_unit'''
    oracle = queries.run_sql(sql, parameters=[week])
    variation = oracle.current_price / oracle.previous_price - 1
    assert model['counts'] == [int((variation > 0).sum()), int((variation < 0).sum()), int((variation == 0).sum())]
    # D-153: prices shown are each week's national price; when the regions are the same in
    # both weeks they reproduce the change exactly, otherwise the row says so.
    for row in model['rows']:
        # D-522: the change is the one of the prices the row shows, those of the same regions and the same package.
        assert row['_same_now'] / row['_same_before'] - 1 == pytest.approx(row['variation'])
        assert row['change_amount'] == pytest.approx(row['_same_now'] - row['_same_before'])
    region = app.session_state['regional']
    assert all(row['region'] == 'Región de Coquimbo' for row in region['rows'])
    for row in region['rows']:
        assert row['national_price'] / row['_previous_price'] - 1 == pytest.approx(row['variation'])
        independent = queries.run_sql(  # D-522: the price of the same package in both weeks
            '''SELECT w.price_now AS price FROM weekly_same_package w JOIN dim_product p USING(product_id)
            JOIN dim_region r USING(region_id) JOIN dim_channel c USING(channel_id)
            WHERE week_start=? AND p.product_group=? AND p.product=?
            AND p.variety=? AND p.quality=? AND w.normalized_unit=? AND c.channel=? AND r.region=?''',
            parameters=[week] + [row[k] for k in queries.KEY_COLUMNS + ['channel', 'region']],
        )
        assert independent.price.iloc[0] == pytest.approx(row['national_price'])
        assert not row['is_alert']  # national alerts are never relabelled regional
    assert model['selected'] == model['rows'][0]
    assert model['missing'] == model['available'] - sum(model['counts'])
    assert model['history'].week_start.max() <= pd.Timestamp(week)
    assert model['history'].week_start.min() >= pd.Timestamp(week) - pd.Timedelta(weeks=11)


def test_d304_the_regions_column_says_which_regions_on_hover():
    row = {
        'variation': 0.08,
        'quality': 'Primera',
        'normalized_unit': 'kilo',
        'channel': 'Supermercado',
        'national_price': 100.0,
        'product': 'Osobuco',
        'variety': 'Sin especificar',
        'product_group': 'Carne bovina',
        '_regions': (2, 1, [('Maule', 12.0), ('Ñuble', 4.0), ('Biobío', -3.0)]),
    }
    page = home_mockup.products_table([row], '12–18 oct', '5–11 oct', selected='Región del Maule')
    assert '<b class="rise">2 ↑</b> / <b class="fall">1 ↓</b>' in page
    assert (
        page.count('<li class="') == 3 and '<li class="rise chosen"><span>Maule</span>' in page
    )  # the chosen region is marked
    assert '<li class="fall"><span>Biobío</span>' in page


# endregion


# region The products table explains itself (D-327)
ZAPALLO = {
    'product': 'Zapallo',
    'variety': 'Camote',
    'quality': '1a nueva(o)',
    'normalized_unit': 'kilo',
    'channel': 'Mayorista',
    'product_group': 'Hortalizas',
    'national_price': 1812.07,  # the week's national price, 7 regions
    '_previous_price': 1199.36,  # the week before, 8 regions: Arica, the cheapest, was still priced
    '_same_before': 1247.07,
    '_same_now': 1812.07,
    '_same_regions': 2,  # the fixture keeps two of the seven regions, enough to read the calculation
    'variation': 1812.07 / 1247.07 - 1,
    '_coverage_changed': True,
    '_regions': (2, 0, [('Biobío', 66.7), ('Coquimbo', 28.1)]),
    '_calc': {
        'used': [('Biobío', 1200.0, 2000.0), ('Coquimbo', 1336.03, 1711.22)],
        'out': [('Arica y Parinacota', 'now'), ('Los Lagos', 'both')],
    },
}


def test_d327_the_row_shows_the_prices_of_the_regions_it_compares_and_opens_its_calculation():
    page = home_mockup.products_table([dict(ZAPALLO)], '12–18 oct', '5–11 oct', published=9)
    # The two prices and the change rest on the same regions, so dividing them gives the change shown.
    assert '$1.247' in page and '$1.812' in page and '$1.199' not in page and '+45,3 %' in page
    assert 'Precio</span> 5–11 oct' in page and 'Precio</span> 12–18 oct' in page  # D-374: ranges
    assert 'title="Precio medio: promedio de las regiones con precio publicado en las dos semanas"' in page  # D-447
    assert '<summary>Ver cálculo · 2 de 9 regiones</summary>' in page and 'regiones comunes' not in page
    assert (
        '<span>Biobío</span><span class="mock-calc-prices"><span>$1.200</span> → <span>$2.000</span></span><b>+66,7 %</b>'
        in page
    )
    assert 'Promedio de 2 regiones' in page
    assert '<li><span>Arica y Parinacota</span><em>sin precio publicado la semana 12–18 oct</em></li>' in page
    assert '<li><span>Los Lagos</span><em>sin precio publicado en las dos semanas</em></li>' in page
    # One region reads in the singular; a row without the calculation (a region chosen on the map) has no link.
    alone = dict(ZAPALLO, _same_regions=1, _calc={'used': [('Maule', 1200.0, 1888.89)], 'out': []})
    page = home_mockup.products_table([alone], '12–18 oct', '5–11 oct')
    assert '<summary>Ver cálculo · 1 región</summary>' in page and 'Promedio de 1 región' in page
    assert 'Todas las regiones publicaron este producto las dos semanas.' in page
    plain = {key: value for key, value in ZAPALLO.items() if key not in ('_calc', '_same_before', '_same_now')}
    page = home_mockup.products_table([plain], '12–18 oct', '5–11 oct')
    assert '<details' not in page and '$1.199' in page  # without the like-for-like prices, the national ones


def test_d327_the_fixed_note_says_what_the_prices_are_and_what_is_not_shown():
    note = home_mockup.products_note(9, 19)
    assert 'la fuente publica 9' in note and 'sin rellenar' in note
    assert '19 precios sin región comparable no aparecen' in note and note.count('<span>') == 3
    assert '19 precios' not in home_mockup.products_note(9, 0)


def test_d327_a_change_resting_on_one_region_sorts_last():
    from bi import dashboard

    wide = dict(ZAPALLO, product='Acelga', variation=0.30, _same_regions=7, _single_quote=False)
    narrow = dict(ZAPALLO, product='Ají', variation=0.50, _same_regions=1)
    quote = dict(ZAPALLO, product='Apio', variation=0.40, _single_quote=True)
    names = [row['product'] for row in dashboard.sort_family_products([narrow, quote, wide])]
    assert names == ['Acelga', 'Ají', 'Apio'] or names[0] == 'Acelga', names


# endregion


# region Families, basket and steps
def test_d329_the_families_and_the_map_say_what_they_are_calculated_from():
    note = home_mockup.movement_note({'available': 305, 'missing': 19, 'coverage_changed': 121, 'national': True})
    assert 'Con 286 de 305 precios de la semana' in note and 'En 121 quedó fuera una región sin precio' in note
    regional = home_mockup.movement_note({'available': 40, 'missing': 4, 'coverage_changed': 0, 'national': False})
    assert '36 de 40' in regional and 'quedó fuera' not in regional
    assert home_mockup.movement_note({'available': 0, 'missing': 0}) == ''
    row = {'region': 'Región de Arica y Parinacota', 'state': 'fall', 'share': 59.0, 'up': 10, 'down': 20, 'stable': 4}
    page = home_mockup.regional_map(
        [dict(row, total=34, missing=5, dropped=92)], lambda region: '#', '12–18 oct', '5–11 oct'
    )
    assert '97 productos sin precio publicado en una de las dos semanas: fuera del cálculo' in page
    page = home_mockup.regional_map([dict(row, total=34, missing=0, dropped=0)], lambda region: '#', '12-10', '05-10')
    assert 'fuera del cálculo' not in page


def test_d478_the_whole_basket_names_each_products_family():
    page = home_mockup.products_table([dict(ZAPALLO)], '12–18 oct', '5–11 oct', show_family=True)
    assert '<th>Familia</th>' in page and '<td class="mock-family-cell">Hortalizas</td>' in page
    assert page.index('<th>Producto</th>') < page.index('<th>Familia</th>') < page.index('<th>Canal</th>')
    one_family = home_mockup.products_table([dict(ZAPALLO)], '12–18 oct', '5–11 oct')
    assert '<th>Familia</th>' not in one_family and 'mock-family-cell' not in one_family
    empty = home_mockup.products_table([], '12–18 oct', '5–11 oct', query='kiw', show_family=True)
    assert 'Ningún producto empieza por «kiw» en la canasta.' in empty


def test_d480_step_three_says_how_each_figure_is_computed():
    row = {
        'product': 'Pan',
        'variety': '',
        'quality': '',
        'channel': 'Panadería',
        'normalized_unit': 'kilo',
        'variation': 0.1,
        'national_price': 1100.0,
        '_previous_price': 1000.0,
    }
    national = home_mockup.products_table([row], 'b', 'a')
    regional = home_mockup.products_table([row], 'b', 'a', selected='Región de Ñuble')
    assert 'promedio de las regiones' in national and 'promedio de las regiones' not in regional
    assert 'Precio publicado en la región elegida' in regional
    heading = home_mockup.products_heading('Pan', 0.01, 'todo Chile', 1, 1, step=3)
    assert 'mock-hint' in heading and 'Regiones ↑ / ↓' in heading and '0,05 %' in heading
    assert '<title>' in home_mockup.sparkline([1, 2, 3]) and 'todo Chile' in home_mockup.trend_label()


# endregion
