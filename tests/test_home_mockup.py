import re
"""Data fidelity and SVG geometry of the approved initial-screen mockup."""
import json
from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from bi import dashboard, home_mockup, queries

ROOT=Path(__file__).resolve().parents[1]


def test_history_keeps_real_points_and_breaks_missing_weeks():
    rows=pd.DataFrame({'week_start':pd.to_datetime(['2026-01-05','2026-01-19']), 'national_price':[1000.,1400.]})
    markup=home_mockup.history_chart(rows,'Tomate · kilo','promedio regional simple','./')
    assert markup.count('<polyline')==2
    assert markup.count('<circle')==3 # two real points and the latest-point highlight
    assert '05-01-2026: $1.000' in markup and '19-01-2026: $1.400' in markup
    assert '12-01-2026' not in markup
    assert 'No hay historia comparable' in home_mockup.history_chart(rows.iloc[:0],'','','./')


def test_counts_are_explicit_comparisons_and_not_money_or_unique_products():
    markup=home_mockup.metrics([360,317,57],43,-27)
    assert markup.count('aria-label="cantidad"')==4
    assert 'comparaciones de precios' in markup and '27 menos' in markup
    assert 'no productos únicos ni dinero' in markup
    assert 'aunque hayas elegido una región' in home_mockup.metrics([1,2,3],8,None,True)


def test_table_uses_real_predecessor_and_escapes_labels():
    row=dict(product='<script>',variety='Gala',quality='Primera',channel='Feria',normalized_unit='kilo',
             national_price=1500.,variation=.5,_previous_price=1000.,change_amount=500.)
    markup=home_mockup.table([row],lambda r:'./',lambda r:'./?a=1&b=2')
    assert '&lt;script&gt;' in markup and '<script>' not in markup
    assert '$1.000' in markup and '$1.500' in markup and '▲ +50,0 %' in markup
    assert '+$500' in markup and 'por kilo' in markup and 'Calidad: Primera' in markup
    row['variation']=0
    assert 'class="neutral"' in home_mockup.table([row],lambda r:'./',lambda r:'./')


def test_comparison_keeps_missing_and_zero_predecessors_out_of_ranking():
    keys=['product','variety','quality','normalized_unit','channel']
    common=dict(variety='Gala',quality='Primera',normalized_unit='kilo',channel='Feria libre')
    current=pd.DataFrame([dict(common,product=p,national_price=120.) for p in ['A','B','C']])
    previous=pd.DataFrame([dict(common,product='A',national_price=100.),dict(common,product='B',national_price=0.)])
    rows=home_mockup.compare_week(current,previous,keys).assign(is_alert=False,_severity=0.)
    assert rows.iloc[0].change_amount == 20
    assert rows.iloc[0].variation == pytest.approx(.2)
    assert rows.iloc[1:].variation.isna().all()
    assert rows.iloc[1:].change_amount.isna().all()
    assert home_mockup.order_movements(rows,8,'Mayores cambios')['product'].tolist()==['A']
    markup=home_mockup.table(rows.to_dict('records'),lambda r:'./',lambda r:'./')
    assert markup.count('Sin comparación')==4
    assert 'nan' not in markup and 'inf' not in markup
    assert home_mockup.previous_price({'national_price':120.,'variation':.2}) is None


def test_ranking_orders_severity_and_breaks_ties_without_duplicates():
    common=dict(variety='Gala',quality='Primera',normalized_unit='kilo',channel='Feria libre')
    rows=pd.DataFrame([dict(common,product=p,variation=v,is_alert=a,_severity=s)
        for p,v,a,s in [('B',.2,True,3.),('A',.2,True,5.),('C',-.3,False,0.),('D',0.,False,0.)]])
    assert home_mockup.order_movements(rows,8,'Mayores cambios')['product'].tolist()==['C','A','B','D']
    assert home_mockup.order_movements(rows,8,'Subidas')['product'].tolist()==['A','B']
    assert home_mockup.order_movements(rows,8,'Bajadas')['product'].tolist()==['C']
    assert home_mockup.order_movements(rows,8,'Inusuales')['product'].tolist()==['A','B']


def test_family_chart_shows_direction_without_negative_zero_or_ambiguous_counts():
    rows = [
        {'product_group': 'Hortalizas', 'variation': .024},
        {'product_group': 'Cerdo, ave y cordero', 'variation': -.03},
        {'product_group': 'Pan', 'variation': -.0001},
    ]
    markup = home_mockup.family_summary(rows, lambda group: f'/?familia={group}')
    assert 'mock-family-bar rise' in markup and 'mock-family-bar fall' in markup
    assert 'mock-family-zero' in markup
    assert 'Las 3 familias de alimentos' in markup
    assert 'Hortalizas' in markup and '+2,4 %' in markup
    assert 'Cerdo, ave y cordero' in markup and '−3,0 %' in markup
    assert 'Sin variación' in markup and '0,0 %' in markup and '−0,0 %' not in markup
    assert markup.count('class="mock-family-tile ') == 3
    assert markup.count('class="mock-family-product"') == 3
    assert 'data:image/webp;base64,' in markup
    assert 'class="mock-family-row-image"' in markup
    assert markup.index('mock-family-tile rise') < markup.index('mock-family-tile neutral') < markup.index('mock-family-tile fall')
    assert markup.count('>Ver detalle →') == 6
    assert markup.count('class="mock-movement-icon ') == 3
    assert 'mock-movement-icon rise' in markup
    assert 'mock-movement-icon fall' in markup
    assert 'mock-movement-icon neutral' in markup
    assert '<span>Subió</span>' in markup and '<span>Bajó</span>' in markup
    assert 'comparaciones válidas' not in markup


def test_family_table_limit_matches_the_selected_order():
    rows = ([{'product_group': 'Frutas', 'variation': .03, 'is_alert': True}] * 3
            + [{'product_group': 'Frutas', 'variation': -.02, 'is_alert': False}] * 2
            + [{'product_group': 'Pan', 'variation': .01, 'is_alert': False}] * 8)
    assert home_mockup.family_table_limit(rows, 'Mayores cambios') == 8
    assert home_mockup.family_table_limit(rows, 'Subidas') == 8
    assert home_mockup.family_table_limit(rows, 'Bajadas') == 2
    assert home_mockup.family_table_limit(rows, 'Inusuales') == 3


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_dashboard_alerts_follow_week_and_family_and_keep_severity_order():
    week = dashboard.read_cached_filter_options(dashboard.get_database_version())['week'][0]
    rows = dashboard.home_alert_rows(week, 'Frutas')
    assert not rows.empty
    assert set(rows['product_group']) == {'Frutas'}
    assert rows['_distance'].is_monotonic_decreasing
    table = dashboard.home_alert_table(rows)
    assert len(table) == len(rows)
    assert table['N.º'].tolist() == list(range(1, len(rows) + 1))
    assert {'Nivel', 'Familia', 'Producto', 'Canal', 'Unidad', 'Anterior', 'Actual', 'Cambio'} <= set(table)
    assert set(table['Nivel']) <= {'Muy alta', 'Alta', 'Moderada'}
    styled = dashboard.style_home_alert_table(pd.DataFrame({
        'Nivel': ['Muy alta', 'Alta', 'Moderada'],
        'Cambio': ['+1,0 %', '−1,0 %', '0,0 %'],
    }), dashboard.charts.MODE_DARK).to_html()
    assert '#7f1d1d' in styled and '#9a3412' in styled and '#78450a' in styled


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_alert_button_opens_family_overview_without_leaving_dashboard():
    app = AppTest.from_file(ROOT/'bi/dashboard.py', default_timeout=60).run()
    assert not app.exception
    assert not app.dataframe
    assert app.button(key='home_alert_trigger') not in app.sidebar.button  # on top of the Resumen (D-169)
    app.button(key='home_alert_trigger').click().run()
    assert not app.exception
    week = dashboard.read_cached_filter_options(dashboard.get_database_version())['week'][0]
    alert_rows = dashboard.home_alert_rows(week, dashboard.ALL_VALUES)
    assert len([button for button in app.button if str(button.key).startswith('home_alert_family_')]) == alert_rows['product_group'].nunique()
    assert not app.dataframe
    assert not app.expander
    assert 'ALERTA DE PRECIO' in (ROOT/'bi/assets/alert-price.svg').read_text()


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_alert_family_detail_renders_its_toolbar_and_table():
    script = '''
import streamlit as st
from bi import dashboard
week = dashboard.read_cached_filter_options(dashboard.get_database_version())["week"][0]
st.session_state["home_alert_selected_family"] = "Frutas"
dashboard.show_home_alerts_dialog(
    week, dashboard.ALL_VALUES, None, dashboard.charts.MODE_DARK)
'''
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    assert app.button(key='home_alert_back')
    assert len([box for box in app.selectbox
                if str(box.key).startswith('home_alert_unit_')]) == 1
    assert app.dataframe


def test_d096_sidebar_footer_shows_the_real_alert_count():
    app = AppTest.from_file(ROOT/'bi/dashboard.py', default_timeout=60)
    app.run()
    assert not app.exception
    button = app.button(key='home_alert_trigger')
    week = dashboard.read_latest_week()
    count = int((dashboard.read_price_alerts()['week_start'] == week).sum())
    assert button.label == f'▲  Alerta de precio · {count}'
    dark_css = dashboard.build_sidebar_css(dashboard.charts.MODE_DARK)
    light_css = dashboard.build_sidebar_css(dashboard.charts.MODE_BLUE_LIGHT)
    assert '.st-key-home_alert_trigger button' in dark_css
    assert 'background:transparent !important; color:#ff9ca4 !important;' in dark_css
    assert 'background:transparent !important; color:#9d1f2c !important;' in light_css
    assert 'box-shadow:none !important;' in dark_css


def test_product_view_names_the_selected_product_instead_of_claiming_a_family_result():
    rows = [{'product_group': 'Pan', 'variation': .012}]
    markup = home_mockup.family_summary(rows, product_filter=('Pan', 'Marraqueta', 'Sin especificar'))
    assert 'Resultado de Marraqueta' in markup
    assert 'Cambio del producto seleccionado' in markup
    assert 'Las 1 familias' not in markup
    scope = home_mockup.product_scope('Marraqueta', 'Pan')
    assert 'no representa el cambio de toda la familia' in scope


def test_single_family_is_centered_and_comparison_context_is_plain_language():
    markup = home_mockup.family_summary([{'product_group': 'Pan', 'variation': -.031}])
    assert 'Familia seleccionada' in markup
    assert 'mock-family-gallery is-single' in markup
    assert 'Las 1 familias' not in markup
    context = home_mockup.comparison_context('05-10-2026', '28-09-2026', 'Arica y Parinacota', '13 oct')
    assert 'El precio de cada alimento.' in context
    assert 'Semana 28-09-2026 → semana 05-10-2026' in context
    assert 'por tipo de comercio, no por tienda' in context
    assert context.count('class="mock-fact-icon ') == 4


def test_regional_summary_counts_equivalent_prices_and_uses_a_display_threshold():
    keys = dict(product_group='Frutas', variety='Gala', quality='Primera',
                normalized_unit='kilo', channel='Feria libre')
    current = pd.DataFrame([
        dict(keys, product='A', region='Región de Coquimbo', price=110.0),
        dict(keys, product='B', region='Región de Coquimbo', price=99.98),
        dict(keys, product='C', region='Región de Coquimbo', price=80.0),
        dict(keys, product='D', region='Región de Coquimbo', price=130.0),
    ])
    previous = pd.DataFrame([
        dict(keys, product='A', region='Región de Coquimbo', price=100.0),
        dict(keys, product='B', region='Región de Coquimbo', price=100.0),
        dict(keys, product='C', region='Región de Coquimbo', price=100.0),
    ])
    rows = dashboard.build_regional_movement_model(current, previous)
    assert rows == [{'region': 'Región de Coquimbo', 'state': 'mixed', 'share': pytest.approx(100 / 3),
                     'up': 1, 'down': 1, 'stable': 1, 'total': 3, 'missing': 1}]


def test_regional_map_keeps_the_surface_minimal_and_exact_counts_in_the_hint():
    rows = [{'region': 'Región de Coquimbo', 'state': 'fall', 'share': 62.0,
             'up': 42, 'down': 91, 'stable': 13, 'total': 146, 'missing': 4}]
    markup = home_mockup.regional_map(
        rows, lambda region: '/dashboard?_home_region=' + str(region),
        '05-10-2026', '28-09-2026', 'Región de Coquimbo')
    assert markup.count('mock-region-shape ') == 32  # desktop and phone projections
    assert markup.count('class="mock-region-readable ') == 16
    assert markup.count('<a class="mock-region-row ') == 16
    assert '62 % ↓' in markup
    assert '91 bajaron · 42 subieron · 13 sin cambio · 146 comparados' in markup
    assert 'Semana 28-09-2026 → 05-10-2026' in markup
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
    markup = home_mockup.regional_map([], lambda region: '#' + str(region), '05-10-2026', '28-09-2026')
    shapes = dict(re.findall(r'<a href="#([^"]+)" target="_self" aria-label="[^"]*"><path class="mock-region-shape '
                             r'[^"]*" d="([^"]+)"', markup))
    rows = re.findall(r'<a class="mock-region-row [^"]*" href="#([^"]+)".*?class="mock-region-leader" '
                      r'd="M([\d.]+),([\d.]+)L([\d.]+),([\d.]+)".*?class="mock-region-name"[^>]*>([^<]+)<', markup, re.S)
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
    rows = [{'product_group': 'Frutas', 'variation': .02}, {'product_group': 'Frutas', 'variation': .04},
            {'product_group': 'Pan', 'variation': -.01}]
    markup = home_mockup.family_movement(rows, lambda family: '#' + family, 'Frutas', 'todo Chile')
    assert markup.index('Frutas') < markup.index('Pan')
    assert '<a class="mock-movement-row rise selected" href="#Frutas"' in markup
    assert '+3,0 %' in markup and '−1,0 %' in markup
    assert 'left:50%;width:50.00%' in markup and 'left:33.33%;width:16.67%' in markup


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
def test_d092_region_and_family_clicks_fill_the_products_table():
    app = AppTest.from_file(ROOT/'bi/dashboard.py', default_timeout=60)
    app.query_params['_home_region'] = 'Región de Coquimbo'
    app.query_params['_home_week'] = '2026-10-05'
    app.query_params['familia'] = 'Frutas'
    app.run()
    assert not app.exception
    assert app.session_state['dashboard_region'] == 'Región de Coquimbo'
    markup = ' '.join(block.value for block in app.markdown)
    assert 'Productos · Frutas' in markup and 'en Coquimbo' in markup
    assert '<a class="mock-region-row ' in markup and 'selected" href="' in markup
    table = re.search(r'<div class="mock-products-table".*?</table>', markup).group(0)
    assert table.count('<tr>') > 1 and 'Regiones ↑ / ↓' in table
    # Channel and order filter the same rows; prices stay real.
    app.selectbox(key='home_products_order').set_value('Bajadas').run()
    markup = ' '.join(block.value for block in app.markdown)
    table = re.search(r'<div class="mock-products-table".*?</table>', markup).group(0)
    values = [float(v.replace('−', '-').replace(',', '.')) for v in re.findall(r'<b>([+−]?[\d,]+) %</b>', table)]
    assert values == sorted(values)


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(),reason='Requires real database')
def test_home_model_matches_independent_weekly_prices_and_region_selection():
    script=f'''import sys
sys.path.insert(0,{str(ROOT)!r})
import streamlit as st
from bi import dashboard
week=f"{{dashboard.read_latest_week():%Y-%m-%d}}"
st.session_state['model']=dashboard.read_home_model(week,dashboard.ALL_VALUES,dashboard.ALL_VALUES,8)
st.session_state['regional']=dashboard.read_home_model(week,dashboard.ALL_VALUES,'Región de Coquimbo',8)
st.session_state['week']=week
'''
    app=AppTest.from_string(script,default_timeout=60).run()
    assert not app.exception
    model=app.session_state['model']; week=app.session_state['week']
    # D-144: the national change averages only the regions with a price in both weeks.
    sql='''SELECT AVG(a.price) AS current_price, AVG(b.price) AS previous_price
    FROM weekly_price a JOIN weekly_price b
    ON b.product_id=a.product_id AND b.channel_id=a.channel_id AND b.normalized_unit=a.normalized_unit
    AND b.region_id=a.region_id AND b.week_start=strftime(CAST(a.week_start AS DATE) - 7, '%Y-%m-%d')
    WHERE a.week_start=? AND a.flag IS NULL AND b.flag IS NULL
    GROUP BY a.product_id, a.channel_id, a.normalized_unit'''
    oracle=queries.run_sql(sql,parameters=[week])
    variation=oracle.current_price/oracle.previous_price-1
    assert model['counts']==[int((variation>0).sum()),int((variation<0).sum()),int((variation==0).sum())]
    # D-153: prices shown are each week's national price; when the regions are the same in
    # both weeks they reproduce the change exactly, otherwise the row says so.
    for row in model['rows']:
        if not row['_coverage_changed']:
            assert row['national_price']/row['_previous_price']-1==pytest.approx(row['variation'])
            assert row['change_amount']==pytest.approx(row['national_price']-row['_previous_price'])
    region=app.session_state['regional']
    assert all(row['region']=='Región de Coquimbo' for row in region['rows'])
    for row in region['rows']:
        assert row['national_price']/row['_previous_price']-1==pytest.approx(row['variation'])
        independent=queries.run_sql('''SELECT w.price FROM weekly_price w JOIN dim_product p USING(product_id)
            JOIN dim_region r USING(region_id) JOIN dim_channel c USING(channel_id)
            WHERE w.flag IS NULL AND week_start=? AND p.product_group=? AND p.product=?
            AND p.variety=? AND p.quality=? AND w.normalized_unit=? AND c.channel=? AND r.region=?''',
            parameters=[week]+[row[k] for k in queries.KEY_COLUMNS+['channel','region']])
        assert independent.price.iloc[0]==pytest.approx(row['national_price'])
        assert not row['is_alert']  # national alerts are never relabelled regional
    assert model['selected']==model['rows'][0]
    assert model['missing']==model['available']-sum(model['counts'])
    assert model['history'].week_start.max()<=pd.Timestamp(week)
    assert model['history'].week_start.min()>=pd.Timestamp(week)-pd.Timedelta(weeks=11)
