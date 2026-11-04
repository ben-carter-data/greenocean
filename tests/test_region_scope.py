"""D-499: with a region chosen in step 1, everything after it in «Semanal» works on that region."""

import re
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from bi import alerts, channel_latest, dashboard, home_mockup, queries

ROOT = Path(__file__).resolve().parents[1]
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason='Requires real database')
SERIES = ['product_group', 'product', 'variety', 'quality', 'channel', 'normalized_unit']


def latest_week():
    return dashboard.read_cached_filter_options(dashboard.get_database_version())['week'][0]


def regions():
    return sorted(queries.run_sql('SELECT region FROM dim_region')['region'])


def open_semanal(region, family='Frutas', **parameters):
    app = AppTest.from_file(ROOT / 'bi/dashboard.py', default_timeout=60)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PUBLIC
    app.query_params.update({'_home_region': region, 'familia': family, **parameters})
    app.session_state[dashboard.scoped(dashboard.HOME_REGION_DONE)] = True
    app.session_state[dashboard.scoped(dashboard.HOME_FAMILY_DONE)] = True  # D-530: the address alone unlocks nothing
    app.run()
    assert not app.exception
    return app


def markup_of(app):
    return ' '.join(block.value for block in app.markdown)


def recompute_alerts(region, week):
    """The rule of K6 written again, series by series, from the changes of one region in the same package (D-522)."""
    frame = queries.run_sql(
        """SELECT week_start, product_group, product, variety, quality, channel, normalized_unit, price_now, price_before,
                  quotes_now, quotes_before
           FROM weekly_same_package JOIN dim_product USING (product_id) JOIN dim_channel USING (channel_id)
           JOIN dim_region USING (region_id) WHERE region = ?""",
        parameters=[region],
    )
    frame['week_start'] = pd.to_datetime(frame['week_start'])
    day = pd.Timestamp(week)
    found = {}
    for key, series in frame.groupby(SERIES):
        series = series.set_index('week_start').sort_index()
        weeks = [day - pd.Timedelta(weeks=back) for back in range(12, -1, -1)]  # 12 usual changes and the one judged
        if not all(moment in series.index for moment in weeks):
            continue
        changes = series.loc[weeks, 'price_now'] / series.loc[weeks, 'price_before'] - 1
        usual, change = changes.iloc[:-1], changes.iloc[-1]
        unusual = abs(change - usual.mean()) > 2 * usual.std()
        judged = series.loc[weeks[-1]]
        if unusual and abs(change) >= 0.10 and judged['quotes_now'] >= 2 and judged['quotes_before'] >= 2:
            found[key] = change
    return found


@needs_database
def test_d499_every_alert_of_a_region_is_recalculated_from_its_raw_prices():
    week, checked = latest_week(), 0
    for region in regions():
        shown = dashboard.read_place_alerts(region)
        shown = shown[shown['week_start'] == pd.Timestamp(week)]
        expected = recompute_alerts(region, week)
        assert {tuple(row[column] for column in SERIES) for row in shown.to_dict('records')} == set(expected), region
        for row in shown.to_dict('records'):
            assert row['variation'] == pytest.approx(expected[tuple(row[column] for column in SERIES)])
            checked += 1
    assert checked > 0


@needs_database
def test_d499_the_buttons_and_their_table_follow_the_region_and_say_it():
    week = latest_week()
    region = next(
        name
        for name in regions()
        if len(dashboard.home_alert_rows(week, 'Frutas', direction=dashboard.RISE, region=name))
    )
    rises = dashboard.home_alert_rows(week, 'Frutas', direction=dashboard.RISE, region=region)
    app = open_semanal(region)
    button = app.button(key='home_alert_trigger')
    assert not button.disabled and button.label.startswith(f'▲ {len(rises)} alza')
    button.click().run()
    assert not app.exception
    markup = markup_of(app)
    assert f'precio de ODEPA en {home_mockup.short_region(region)}' in markup
    assert 'precio nacional de ODEPA' not in markup and markup.count('class="mock-level ') == len(rises)
    # in the enlarged table too
    app.button(key='home_products_enlarge').click().run()
    assert not app.exception
    assert app.button(key='dialog_alert_trigger').label == app.button(key='home_alert_trigger').label
    assert markup_of(app).count('class="mock-level ') == 2 * len(rises)


@needs_database
def test_d499_with_all_of_chile_nothing_changes():
    week = latest_week()
    national = dashboard.read_price_alerts()
    assert dashboard.read_place_alerts(dashboard.ALL_VALUES) is national or dashboard.read_place_alerts(None).equals(
        national
    )
    rises = dashboard.home_alert_rows(week, 'Frutas', direction=dashboard.RISE)
    app = open_semanal(dashboard.ALL_VALUES)
    assert app.button(key='home_alert_trigger').label.startswith(f'▲ {len(rises)} alza')
    version = dashboard.get_database_version()
    assert dashboard.read_channel_cards(version) == channel_latest.channel_cards(
        dashboard.read_latest_by_source(version)
    )
    app.button(key='home_alert_trigger').click().run()
    assert 'precio nacional de ODEPA' in markup_of(app)


@needs_database
def test_d499_step_two_shows_only_the_channels_of_the_region_with_their_figures():
    version = dashboard.get_database_version()
    frame = dashboard.read_latest_by_source(version)
    everyone = {card['channel'] for card in dashboard.read_channel_cards(version)}
    region = min(regions(), key=lambda name: frame[frame['region'] == name]['channel'].nunique())
    cards = dashboard.read_channel_cards(version, region)
    assert cards == channel_latest.channel_cards(frame[frame['region'] == region])
    assert {card['channel'] for card in cards} < everyone
    markup = markup_of(open_semanal(region))
    assert markup.count('mock-channel-row mock-channel-tile') == len(cards)
    # a saved address with a channel that does not publish there goes back to all of Chile
    absent = sorted(everyone - {card['channel'] for card in cards})[0]
    markup = markup_of(open_semanal(region, **{dashboard.CHANNEL_PARAMETER: absent}))
    assert markup.count('mock-channel-row mock-channel-tile') == len(everyone)


@needs_database
def test_d499_the_little_lines_end_on_the_figure_beside_them():
    version, week = dashboard.get_database_version(), latest_week()
    for region in regions():
        by_family, basket = dashboard.read_home_trends(version, week, region)
        rows = dashboard.read_home_model(week, dashboard.ALL_VALUES, region, 8)['family_rows']
        for family, median, _ in home_mockup.family_averages(rows):
            assert by_family[family][-1] == pytest.approx(median * 100), (region, family)
        assert basket[-1] == pytest.approx(home_mockup.basket_median(rows) * 100), region


@needs_database
def test_d499_it_is_said_in_english_too():
    week = latest_week()
    region = next(
        name
        for name in regions()
        if len(dashboard.home_alert_rows(week, 'Frutas', direction=dashboard.RISE, region=name))
    )
    markup = markup_of(open_semanal(region, lang='en', alerta=dashboard.RISE))
    assert f'ODEPA price in {home_mockup.short_region(region)}' in markup and 'precio de ODEPA' not in markup
    assert re.search(r'Weekly median over the last 8 weeks, ', markup) and 'Mediana semanal' not in markup


def test_d499_the_formula_names_the_price_it_uses():
    assert 'precio nacional' in alerts.describe_kind(True, True)
    assert 'precio de la región elegida' in alerts.describe_kind(True, True, True)
