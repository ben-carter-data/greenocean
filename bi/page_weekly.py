"""«Semanal» (D-541): the weekly dashboard in four steps (region, optional channel, family and products), with its
price alerts, the line of alerts and search over step 4, the enlarged window and «Descargar» to Excel or CSV.
"""

import base64
import importlib
import json
import math
from urllib.parse import parse_qs, urlencode

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitAPIException

from bi import (
    alerts,
    channel_icons,
    channel_latest,
    charts,
    data_terms,
    home_mockup,
    i18n,
    overview,
    price_export,
    queries,
    weeks,
)
from bi.app_frame import (
    build_page_address,
    build_view_path,
    channel_address,
    describe_late_sources,
    is_public_profile,
    show_return_button,
)
from bi.constants import (
    ALERT_KINDS,
    ALERT_LEVELS,
    ALL_VALUES,
    CHANNEL_PARAMETER,
    DASHBOARD_WEEKS,
    DEFAULT_TOP_N,
    DROP,
    DROP_LEVELS,
    HOME_FAMILY_DONE,
    HOME_FLASH,
    HOME_LINK_PARAMETERS,
    HOME_REGION_DONE,
    HOME_SEARCHED,
    HOME_STEP_PARAMETER,
    PAGE_DOCUMENTATION,
    PAGE_HOME,
    PAGE_OPERATIONS,
    PRODUCT_DIRECTIONS,
    RISE,
    TOP_N_RANGE,
    WINDOW_OF_VIEW,
)
from bi.data_access import (
    PRICE_SCOPE,
    current_channel,
    get_database_version,
    parse_run_start,
    read_all_families,
    read_cached_all_variations,
    read_cached_market_snapshot,
    read_cached_national_prices,
    read_cached_region_series,
    read_cached_week_snapshot,
    read_compared_weeks,
    read_latest_by_source,
    read_latest_run,
    read_place_alerts,
    read_price_alerts,
    scoped,
    to_chile_time,
)
from bi.i18n import tr
from etl import etl

# region Constants
# The map and the family list are hand-drawn SVG/HTML with plain links, so a click
# used to navigate the browser: a full page reload and a brand-new session. This
# component catches those same-page clicks and hands the link's parameters to
# Python instead, so the page reruns in place (D-123).
HOME_LINKS_JS = """
export default function(component) {
    const { setTriggerValue } = component;
    const handler = (event) => {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey
            || event.shiftKey || event.altKey) return;
        const link = event.target.closest && event.target.closest('.greenocean-mockup a[href]');
        if (!link) return;
        const url = new URL(link.getAttribute('href'), window.location.href);
        if (url.origin !== window.location.origin || url.pathname !== window.location.pathname) return;
        // Only the map and family links: a product's «Contexto del precio» link
        // carries a view and a product key, and must navigate (D-123b).
        const params = url.searchParams;
        // D-406, D-494: «Semanal» links to itself, whatever its channel (step 2); another view navigates.
        const here = new URLSearchParams(window.location.search);
        const samePage = params.get('vista') === here.get('vista');
        if (!params.has('_home_region') || params.has('_home_key') || (params.has('vista') && !samePage)) return;
        event.preventDefault();
        setTriggerValue('link', url.search);
    };
    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
}
"""


# A region's direction must be told apart from a coin toss (D-146).
REGION_DIRECTION_P_VALUE = 0.05


NOTHING_MOVED = {
    'Subidas': 'Ninguno de estos productos subió esta semana.',
    'Bajadas': 'Ninguno de estos productos bajó esta semana.',
}


SEARCH_STILL_CSS = '.st-key-home_products_search [data-testid="stTextInputRootElement"] {animation:none!important;}'
# endregion


# region Filters and the steps
def read_filter(name):
    """The value of a report filter, kept across views and windows."""
    return st.session_state.get(scoped(f"dashboard_{name}"), ALL_VALUES)


def read_cached_filter_options(database_version):
    """D-405: keyed on the scope, so a channel page never reads the Dashboard's cache."""
    return read_cached_filter_options_in(database_version, current_channel())


@st.cache_data
def read_cached_filter_options_in(database_version, channel):
    """Categories, regions and the last weeks with prices, for the report's bar."""
    variations = read_cached_all_variations(database_version)
    weeks = sorted(variations["week_start"].unique(), reverse=True)[:DASHBOARD_WEEKS]
    snapshot = read_cached_market_snapshot(database_version)
    return {
        "group": [ALL_VALUES] + sorted(variations["product_group"].unique()),
        "region": [ALL_VALUES] + sorted(snapshot["region"].unique()),
        "week": [f"{pd.Timestamp(week):%Y-%m-%d}" for week in weeks],
    }


def keep_product(rows, product):
    """The rows of the chosen product key (all rows when none is chosen)."""
    if not product:
        return rows
    for column, value in product["key"].items():
        rows = rows[rows[column] == value]
    return rows


def describe_week_span(week):
    """«5–11 oct 2026»: the Monday and the Sunday of the analyzed week (D-374)."""
    return weeks.week_range(week, year=True)


def build_movement_proportions(rows):
    """Mutually exclusive parts of all comparable national series, not just Top N."""
    values = rows["variation"].dropna()
    counts = [int(values.gt(0).sum()), int(values.lt(0).sum()), int(values.eq(0).sum())]
    total = sum(counts)
    return pd.DataFrame(
        {
            "label": ["Subieron", "Bajaron", "Sin cambio"],
            "value": counts,
            "share": [count / total * 100 if total else 0 for count in counts],
        }
    )


def apply_home_link_click():
    """Turn a captured map or family click into the same query parameters its link
    carried, without navigating; the rest of the page reads them as before."""
    # Registered on every run, not at import: each Streamlit runtime keeps its own
    # registry, and the same definition registers again silently.
    home_links = st.components.v2.component("home_overview_links", js=HOME_LINKS_JS)
    clicked = home_links(key="home_overview_links", on_link_change=lambda: None).link
    if not clicked:
        return
    parameters = parse_qs(clicked.lstrip("?"))
    step = (parameters.get(HOME_STEP_PARAMETER) or [None])[0]
    if step == "region" and not st.session_state.get(scoped(HOME_REGION_DONE)):
        st.session_state[scoped(HOME_REGION_DONE)] = True
        st.session_state[scoped(HOME_FLASH)] = "families"  # the panel that just opened lights up for a moment
    elif step == "family" and not st.session_state.get(scoped(HOME_FAMILY_DONE)):
        st.session_state[scoped(HOME_REGION_DONE)] = True
        st.session_state[scoped(HOME_FAMILY_DONE)] = True
        st.session_state[scoped(HOME_FLASH)] = "products"
    for name in HOME_LINK_PARAMETERS:
        if parameters.get(name):
            st.query_params[name] = parameters[name][0]
        else:
            st.query_params.pop(name, None)
    # D-531: a channel link (step 2) carries the steps already done into the scope of the channel it opens
    if not step and parameters.get('_home_region'):
        channel = (parameters.get(CHANNEL_PARAMETER) or [None])[0]
        for name in (HOME_REGION_DONE, HOME_FAMILY_DONE):
            if st.session_state.get(scoped(name)):
                st.session_state[name if channel is None else f'{name}@{channel}'] = True


def apply_home_focus(options):
    """Apply only validated deep-link selections, once; never override live widgets."""
    token = st.query_params.get("_home_key")
    marker = repr({k: v for k, v in st.query_params.to_dict().items() if k.startswith('_home_')})
    requested = any(st.query_params.get('_home_' + name) for name in ('group', 'region', 'week'))
    if (not token and not requested) or marker == st.session_state.get(scoped('mock_focus_seen')):
        return
    st.session_state[scoped('mock_focus_seen')] = marker
    for name in ('group', 'region', 'week'):
        value = st.query_params.get('_home_' + name)
        if value in options[name] or value == ALL_VALUES:
            st.session_state[scoped('dashboard_' + name)] = value
    count = st.query_params.get('_home_count', '')
    if count.isdigit() and TOP_N_RANGE[0] <= int(count) <= 10_000:
        st.session_state['dashboard_top_n'] = int(count)
    order = st.query_params.get('_home_order')
    if order in home_mockup.ORDERS:
        st.session_state['home_order'] = order
    if token:
        try:
            payload = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
            if set(payload) == set(queries.KEY_COLUMNS + ['channel']) and all(
                isinstance(v, str) for v in payload.values()
            ):
                st.session_state['mock_focus_key'] = payload
        except (ValueError, TypeError, UnicodeError):
            return


def scope_address():
    """The address of «Semanal», with its channel when step 2 has one (D-405, D-494)."""
    channel = current_channel()
    return build_page_address(PAGE_HOME) if channel is None else channel_address(channel)


def scope_path():
    """The path of the bar: «… › Semanal», and «… › Semanal › Feria libre» with a channel (D-405, D-494)."""
    channel = current_channel()
    path = build_view_path(WINDOW_OF_VIEW[PAGE_HOME], PAGE_HOME)
    return path if channel is None else f"{path} › {data_terms.term(channel)}"


def build_steps_css(palette, region_open, family_open, flash, searched=False):
    """D-352: a panel that waits for the step before it is dimmed and cannot be used; the one that has just opened lights
    up for a moment. Panels 2 and 3 are the containers «home_families» and «home_products». D-372: the search stops
    glowing once someone typed in it."""
    rules = []
    if searched:
        rules.append(SEARCH_STILL_CSS)
    for container, opened in (
        ("home_channels", region_open),
        ("home_families", region_open),
        ("home_products", family_open),
    ):
        if not opened:
            rules.append(
                f".st-key-{container} > *:not(:has(.mock-lock)) "
                "{opacity:.38;pointer-events:none;filter:saturate(.4);user-select:none;}"
            )
    if flash in ("families", "products"):
        target = "home_families" if flash == "families" else "home_products"
        rules.append(f".st-key-{target} {{animation:mock-unlock 1.6s ease-out 1; border-radius:12px;}}")
    return "<style>" + "".join(rules) + "</style>" if rules else ""


# endregion


# region The week's model and the regions
def compare_same_regions(variations, snapshot, prior, join):
    """National weekly change over the same regions in both weeks (D-144).

    A national price averages the regions with data that week; when the set of
    regions changes, the plain change mixes a price movement with a change of
    composition (a product sold in Arica and Santiago, then only in Santiago, «moves»
    without any regional price moving). Both prices shown and the change are the
    averages of the regions present in both weeks; a key with no region in common
    has no valid comparison. _coverage_changed marks the keys that left regions out.
    """
    regional = join + ['region', 'price', 'observation_count']
    named = regional + (['_packages'] if '_packages' in snapshot else [])  # D-522: the packages each region compares
    matched = snapshot[named].merge(prior[regional], on=join + ['region'], suffixes=('', '_before'))
    same = matched.groupby(join, as_index=False).agg(
        _same_now=('price', 'mean'),
        _same_before=('price_before', 'mean'),
        _same_regions=('region', 'nunique'),
        _quotes_now=('observation_count', 'sum'),
        _quotes_before=('observation_count_before', 'sum'),
        **({'_packages': ('_packages', home_mockup.join_packages)} if '_packages' in matched else {}),
    )
    regions_now = snapshot.groupby(join).region.nunique().rename('_regions_now')
    regions_before = prior.groupby(join).region.nunique().rename('_regions_before')
    # D-327: the table shows the price of the regions with a price in both weeks (_same_now, _same_before), the same
    # prices the change is computed from; the national price of each week stays as the fallback (D-153).
    rows = (
        variations.drop(columns=['variation', 'change_amount'])
        .merge(same, on=join, how='left')
        .merge(regions_now, on=join, how='left')
        .merge(regions_before, on=join, how='left')
    )
    valid = rows['_same_before'].gt(0) & rows['_same_now'].notna()
    rows['variation'] = (rows['_same_now'] / rows['_same_before'] - 1).where(valid)
    rows['change_amount'] = (rows['_same_now'] - rows['_same_before']).where(valid)
    rows['_coverage_changed'] = valid & (
        (rows['_regions_now'] != rows['_same_regions']) | (rows['_regions_before'] != rows['_same_regions'])
    )
    return rows


def summarize_family_coverage(variations):
    """Per family, the same counts as the coverage note: prices this week, those with a
    valid change (the rows of the family table), single-quote changes and changes that
    left a region out, so the note can speak of the family the table shows."""
    valid = variations.variation.notna() & variations.variation.abs().lt(float('inf'))
    rows = variations.assign(
        _valid=valid, _thin=variations.get('_single_quote', False), _changed=variations.get('_coverage_changed', False)
    )
    return {
        family: {
            'available': len(group),
            'comparable': int(group._valid.sum()),
            'single_quote': int((group._thin & group._valid).sum()),
            'coverage_changed': int((group._changed & group._valid).sum()),
        }
        for family, group in rows.groupby('product_group')
    }


def read_home_model(week, group, region, count, order='Mayores cambios', product_filter=None):
    """Real regional or national series; K6 stays explicitly national."""
    version = get_database_version()
    week_date = pd.Timestamp(week)
    previous_week = f'{week_date - pd.Timedelta(days=7):%Y-%m-%d}'
    prices = read_cached_national_prices(version)
    current = prices[prices['week_start'] == week_date].copy()
    previous = prices[prices['week_start'] == pd.Timestamp(previous_week)].copy()
    if group != ALL_VALUES:
        current = current[current['product_group'] == group]
        previous = previous[previous['product_group'] == group]
    if product_filter:
        family, product, variety = product_filter
        current = current[
            (current['product_group'] == family) & (current['product'] == product) & (current['variety'] == variety)
        ]
        previous = previous[
            (previous['product_group'] == family) & (previous['product'] == product) & (previous['variety'] == variety)
        ]
    snapshot, prior = read_compared_weeks(version, week)
    if group != ALL_VALUES:
        snapshot = snapshot[snapshot['product_group'] == group]
        prior = prior[prior['product_group'] == group]
    if product_filter:
        family, product, variety = product_filter
        snapshot = snapshot[
            (snapshot['product_group'] == family) & (snapshot['product'] == product) & (snapshot['variety'] == variety)
        ]
        prior = prior[
            (prior['product_group'] == family) & (prior['product'] == product) & (prior['variety'] == variety)
        ]
    coverage = snapshot.region.nunique()
    join = queries.KEY_COLUMNS + ['channel']
    if region != ALL_VALUES:
        snapshot = snapshot[snapshot.region == region]
        prior = prior[prior.region == region]
        current = snapshot.assign(national_price=snapshot.price)
        previous = prior.assign(national_price=prior.price)
        coverage = snapshot.region.nunique()
    variations = home_mockup.compare_week(current, previous, join)
    variations['_coverage_changed'] = False
    if region == ALL_VALUES:
        variations = compare_same_regions(variations, snapshot, prior, join)
    valid = variations[variations.variation.notna() & variations.variation.abs().lt(float('inf'))].copy()
    parts = build_movement_proportions(valid)
    counts = [int(v) for v in parts.value]
    alert_rows = read_price_alerts()
    if group != ALL_VALUES:
        alert_rows = alert_rows[alert_rows.product_group == group]
    if product_filter:
        family, product, variety = product_filter
        alert_rows = alert_rows[
            (alert_rows['product_group'] == family)
            & (alert_rows['product'] == product)
            & (alert_rows['variety'] == variety)
        ]
    alert_count = len(alert_rows[alert_rows.week_start == week_date])
    alert_previous = len(alert_rows[alert_rows.week_start == pd.Timestamp(previous_week)])
    variations['is_alert'] = False
    variations['_severity'] = 0.0
    if region == ALL_VALUES:
        week_alerts = alert_rows[alert_rows.week_start == week_date].copy()
        week_alerts['_severity'] = (
            week_alerts.variation - week_alerts.usual_variation
        ).abs() / week_alerts.variation_deviation
        variations = variations.drop(columns=['is_alert', '_severity']).merge(
            week_alerts[join + ['_severity']].assign(is_alert=True), on=join, how='left', validate='one_to_one'
        )
        variations['is_alert'] = variations.is_alert.eq(True)
        variations['_severity'] = variations['_severity'].fillna(0)
    example_sets = {}
    for kind, subset in {
        'up': variations[variations.variation > 0],
        'down': variations[variations.variation < 0],
        'equal': variations[variations.variation == 0],
        'alert': variations[variations.is_alert.eq(True)],
    }.items():
        subset = subset.copy()
        if not subset.empty:
            subset['_sort'] = subset.variation.abs()
            subset = subset.sort_values(['_sort'] + join, ascending=[False] + [True] * len(join))
            example_sets[kind] = [
                f"{home_mockup.product_label(row, True)} · {row['channel']}" for _, row in subset.head(2).iterrows()
            ]
    # D-146: a change resting on a single quote in either week is one isolated price,
    # not a market movement; it stays in the family median but not in the ranking.
    thin = pd.Series(False, index=variations.index)
    if region == ALL_VALUES and '_quotes_now' in variations:
        thin = variations.variation.notna() & ((variations._quotes_now < 2) | (variations._quotes_before < 2))
    variations['_single_quote'] = thin
    ranked = home_mockup.order_movements(variations[~thin], count, order)
    if ranked.empty and valid.empty and order != 'Inusuales':
        ranked = variations.sort_values(join).head(count)
    # Default selection is the first displayed movement; clicks retain the exact key.
    chosen = None
    focus = st.session_state.get('mock_focus_key')
    if focus:
        matched = variations
        for field, value in focus.items():
            matched = matched[matched[field] == value]
        if not matched.empty:
            chosen = matched.iloc[0]
    if chosen is None:
        reference = ranked if not ranked.empty else variations.sort_values(join)
        if not reference.empty:
            chosen = reference.iloc[0]
    history = pd.DataFrame(columns=['week_start', 'national_price'])
    subtitle = 'Sin producto con precios disponibles'
    if chosen is not None:
        key = {field: chosen[field] for field in queries.KEY_COLUMNS}
        channel = chosen['channel']
        if region == ALL_VALUES:
            history = keep_product(prices, {'key': key})
            history = history[history.channel == channel]
        else:
            sql = '''SELECT w.week_start,w.price AS national_price FROM weekly_price w
                JOIN dim_product p USING(product_id) JOIN dim_region r USING(region_id)
                JOIN dim_channel c USING(channel_id) WHERE w.flag IS NULL
                AND p.product_group=? AND p.product=? AND p.variety=? AND p.quality=?
                AND w.normalized_unit=? AND r.region=? AND c.channel=? AND w.week_start BETWEEN ? AND ?'''
            history = queries.run_sql(
                sql,
                parameters=list(key.values())
                + [region, channel, f'{week_date - pd.Timedelta(weeks=11):%Y-%m-%d}', week],
            )
            history['week_start'] = pd.to_datetime(history.week_start)
        history = history[history.week_start.between(week_date - pd.Timedelta(weeks=11), week_date)]
        subtitle = home_mockup.product_label(chosen, True) + ' · ' + channel + ' · $/' + key['normalized_unit']
    return dict(
        counts=counts,
        alert_count=alert_count,
        alert_delta=alert_count - alert_previous,
        examples=example_sets,
        product_filter=product_filter,
        family_rows=variations[variations.variation.notna() & variations.variation.abs().lt(float('inf'))].to_dict(
            'records'
        ),
        rows=ranked.to_dict('records'),
        selected=chosen.to_dict() if chosen is not None else None,
        history=history,
        subtitle=subtitle,
        coverage=coverage,
        missing=max(0, len(current) - sum(counts)),
        available=len(current),
        national=region == ALL_VALUES,
        coverage_changed=int(variations['_coverage_changed'].sum()),
        single_quote=int(thin.sum()),
        family_coverage=summarize_family_coverage(variations),
        week_label=weeks.week_range(week_date),  # D-374: «12–18 oct», never the Monday alone
        previous_label=weeks.week_range(previous_week),
    )


def sign_test_p_value(up, down):
    """Two-sided exact sign test: the chance of a split at least this uneven if a rise
    and a fall were equally likely."""
    up, down = int(up), int(down)
    total = up + down
    if not total:
        return 1.0
    tail = sum(math.comb(total, count) for count in range(max(up, down), total + 1))
    return min(1.0, 2 * tail / 2**total)


def build_regional_movement_model(current, previous):
    """Summarize equivalent weekly prices by region without inventing a basket.

    A movement smaller than 0.05 % is displayed as unchanged, consistently with
    the product tables. The percentage is the share in the dominant direction.
    A region is painted «rise» or «fall» only when its rises and falls differ more
    than chance allows (sign test, p < 0.05, D-146); 52 % against 48 % is a coin toss.
    """
    join = queries.KEY_COLUMNS + ['channel', 'region']
    current = current[join + ['price']].rename(columns={'price': 'national_price'})
    previous = previous[join + ['price']].rename(columns={'price': 'national_price'})
    compared = home_mockup.compare_week(current, previous, join)
    compared = compared[compared['variation'].notna() & compared['variation'].abs().lt(float('inf'))].copy()
    rows = []
    current_counts = current.groupby('region').size().to_dict()
    previous_counts = previous.groupby('region').size().to_dict()
    for region in sorted(set(current['region'])):
        values = compared.loc[compared['region'] == region, 'variation']
        up = int(values.ge(0.0005).sum())
        down = int(values.le(-0.0005).sum())
        stable = int(values.abs().lt(0.0005).sum())
        total = up + down + stable
        missing = max(0, int(current_counts.get(region, 0)) - total)
        # D-329: the products this region priced the week before and not this week, also out of the comparison.
        dropped = max(0, int(previous_counts.get(region, 0)) - total)
        counts = {'rise': up, 'fall': down, 'neutral': stable}
        if not total:
            state, share = 'missing', None
        else:
            largest = max(counts.values())
            leaders = [name for name, value in counts.items() if value == largest]
            state = leaders[0] if len(leaders) == 1 else 'mixed'
            if state in ('rise', 'fall') and sign_test_p_value(up, down) >= REGION_DIRECTION_P_VALUE:
                state = 'mixed'
            share = largest / total * 100
        rows.append(
            {
                'region': region,
                'state': state,
                'share': share,
                'up': up,
                'down': down,
                'stable': stable,
                'total': total,
                'missing': missing,
                'dropped': dropped,
            }
        )
    return rows


def read_regional_movement_model(week, group=ALL_VALUES, product_filter=None):
    """All available regions under the family/product filters of the dashboard."""
    version = get_database_version()
    current, previous = read_compared_weeks(version, week)
    if group != ALL_VALUES:
        current = current[current['product_group'] == group]
        previous = previous[previous['product_group'] == group]
    if product_filter:
        family, product, variety = product_filter
        for frame_name, frame in (('current', current), ('previous', previous)):
            filtered = frame[
                (frame['product_group'] == family) & (frame['product'] == product) & (frame['variety'] == variety)
            ]
            if frame_name == 'current':
                current = filtered
            else:
                previous = filtered
    return build_regional_movement_model(current, previous)


def read_cached_region_directions(database_version, week):
    """D-405: keyed on the scope, so a channel page never reads the Dashboard's cache."""
    return read_cached_region_directions_in(database_version, week, current_channel())


@st.cache_data
def read_cached_region_directions_in(database_version, week, channel):
    """{(product key, channel): (regions up, regions down, regions with their change)} between two consecutive weeks."""
    join = queries.KEY_COLUMNS + ['channel']
    current, previous = read_compared_weeks(database_version, week)
    columns = join + ['region', 'price']
    compared = home_mockup.compare_week(
        current[columns].rename(columns={'price': 'national_price'}),
        previous[columns].rename(columns={'price': 'national_price'}),
        join + ['region'],
    )
    compared = compared[compared['variation'].notna() & compared['variation'].abs().lt(float('inf'))]
    up = compared[compared['variation'] >= 0.0005].groupby(join).size()
    down = compared[compared['variation'] <= -0.0005].groupby(join).size()
    names = {}
    for key, group in compared.groupby(join):
        ordered = group.sort_values('variation', ascending=False)
        names[key] = [
            (home_mockup.short_region(region), float(change) * 100)
            for region, change in zip(ordered['region'], ordered['variation'])
        ]
    keys = set(up.index) | set(down.index)
    # D-304: (regions up, regions down, [(region, change in %)]), so the table can say which regions, not only how many.
    return {key: (int(up.get(key, 0)), int(down.get(key, 0)), names.get(key, [])) for key in keys}


def read_cached_region_calculation(database_version, week):
    """D-405: keyed on the scope, so a channel page never reads the Dashboard's cache."""
    return read_cached_region_calculation_in(database_version, week, current_channel())


@st.cache_data
def read_cached_region_calculation_in(database_version, week, channel):
    """What each row of the products table was calculated from (D-327): {(product key, channel): {used, out}} and the
    number of regions the source publishes. `used` lists, per region with a price in both weeks, (region, price of the
    week before, price of the week); `out` lists the regions left out, each with the reason: no price this week
    («now»), none the week before («before») or in neither («both»). Nothing is filled in."""
    week_date = pd.Timestamp(week)
    join = queries.KEY_COLUMNS + ['channel']
    current, previous = read_compared_weeks(database_version, week)
    published_before = read_cached_week_snapshot(database_version, f'{week_date - pd.Timedelta(days=7):%Y-%m-%d}')
    published = sorted(queries.run_sql('SELECT region FROM dim_region')['region'])
    columns = join + ['region', 'price']
    both = current[columns].merge(previous[columns], on=join + ['region'], suffixes=('_now', '_before'))
    now_regions = current.groupby(join).region.agg(set)
    before_regions = published_before.groupby(join).region.agg(set)
    calculation = {}
    for key, group in both.groupby(join):
        used = sorted(
            (home_mockup.short_region(region), float(before), float(now))
            for region, before, now in zip(group['region'], group['price_before'], group['price_now'])
        )
        in_now, in_before = now_regions.get(key, set()), before_regions.get(key, set())
        compared = set(group['region'])
        out = [
            (
                home_mockup.short_region(region),
                'package'  # D-522: a price both weeks, but no package in common
                if region in in_now and region in in_before
                else 'before'
                if region in in_now
                else 'now'
                if region in in_before
                else 'both',
            )
            for region in published
            if region not in compared
        ]
        calculation[key] = {'used': used, 'out': sorted(out)}
    return calculation, len(published)


def read_home_trends(database_version, week, region=None):
    """D-405: keyed on the scope, so a channel page never reads the Dashboard's cache."""
    return read_home_trends_in(database_version, week, current_channel(), region)


@st.cache_data(show_spinner=False)
def read_home_trends_in(database_version, week, channel, region=None):
    """The last 8 weeks of the median weekly change (in %) by family and for the whole basket, for the little lines of
    the Dashboard (D-352), of all of Chile or of the region chosen (D-499). Comparable series only, like the median
    beside them; calculated from the same weekly variations as the weeks table."""
    if region is None:
        variations = read_cached_all_variations(database_version)
    else:
        variations = read_cached_region_series(database_version, region)[1]
        variations = variations if channel is None else variations[variations["channel"] == channel]
    upto = variations[variations["week_start"] <= pd.Timestamp(week)]
    heat = overview.family_heat(upto, weeks=8).sort_values("week_start")
    by_family = {group: list(frame["change"]) for group, frame in heat.groupby("product_group")}
    last = sorted(upto["week_start"].unique())[-8:]
    valid = overview.comparable(upto[upto["week_start"].isin(last)])
    basket = list(valid.groupby("week_start")["variation"].median().sort_index().mul(100))
    return by_family, basket


@st.cache_data(show_spinner=False)
def read_channel_cards(database_version, region=None):
    """The channels of the data with their own latest week and median change (D-404), for step 2 (D-494); with a region
    chosen, only those that publish there, with that region's figures (D-499)."""
    frame = read_latest_by_source(database_version)
    if frame is None:
        return []
    return channel_latest.channel_cards(frame if region is None else frame[frame["region"] == region])


# endregion


# region Price alerts
def home_alert_rows(week, group, product_filter=None, direction=None, region=None):
    """The alerts of the place chosen (D-499) in the same week and product scope as the dashboard; D-477: only the
    sharp rises or only the sharp drops when a direction is given."""
    rows = read_place_alerts(region)
    rows = rows[rows['week_start'] == pd.Timestamp(week)]
    if direction == RISE:
        rows = rows[rows['variation'] > 0]
    elif direction == DROP:
        rows = rows[rows['variation'] < 0]
    if group != ALL_VALUES:
        rows = rows[rows['product_group'] == group]
    if product_filter:
        family, product, variety = product_filter
        rows = rows[(rows['product_group'] == family) & (rows['product'] == product) & (rows['variety'] == variety)]
    rows = rows.copy()
    rows['_distance'] = (rows['variation'] - rows['usual_variation']).abs() / rows['variation_deviation']
    return rows.sort_values(['_distance', 'product_group', 'product'], ascending=[False, True, True])


def alert_prices(row):
    """(before, now): the same-region prices behind the change; a row without them shows «—», never a price worked
    back from the change."""
    before, now = row.get('same_region_previous_price'), row.get('same_region_price')
    if before is not None and now is not None and pd.notna(before) and pd.notna(now) and before > 0:
        return float(before), float(now)
    return None, row['national_price']


def alert_count_text(count, direction):
    """«8 alzas fuertes», «1 baja fuerte» (D-477)."""
    one, many = ALERT_KINDS[direction]
    return f'{count} {one if count == 1 else many}'


def family_alerts_table(week, family, direction, query, region=None):
    """D-489, D-492: the products table with only the sharp rises or the sharp drops of the chosen family (or of the
    whole basket), at the national price of K6; the search looks only among them. The levels and the rule are said on
    hover (D-479): the «Nivel» header and the buttons. D-498: the panel and the enlarged table draw the same one."""
    rows = home_alert_rows(week, family or ALL_VALUES, direction=direction, region=region)
    if query:
        rows = rows[[matches_product_search(row, query) for row in rows.to_dict('records')]]
    return (
        '<div class="greenocean-mockup">'
        + home_mockup.alert_table(
            alert_items(rows), query, level_guide_text(direction == RISE, not is_public_profile())
        )
        + '</div>'
    )


def alert_items(rows):
    """The alert rows with their level and the two published prices of their change (D-482), in severity order."""
    items = []
    for row in rows.to_dict('records'):
        before, now = alert_prices(row)
        items.append(
            {**row, 'level': find_alert_level(row['_distance'], row['variation'] > 0)[0], 'before': before, 'now': now}
        )
    return items


def level_guide_text(rise, professional):
    """D-479, D-492: what each level means, said on hover of the «Nivel» header: its threshold in standard deviations,
    from the same table that colours the rows; in the reader's language, since a hover text has no layer of its own."""
    parts = []
    for floor, label, _, _ in ALERT_LEVELS if rise else DROP_LEVELS:
        if professional:
            template, value = ('{}: {} σ o más', floor) if floor else ('{}: más de {} σ', alerts.ALERT_DEVIATIONS)
        else:
            template, value = ('{}: {}× o más', floor) if floor else ('{}: más de {}×', alerts.ALERT_DEVIATIONS)
        parts.append(tr(template).format(i18n.translate_text(label), value))
    return ' · '.join(parts) + '. ' + i18n.translate_text(alerts.describe_scale(professional))


def find_alert_level(distance, rise=True):
    """(label, icon, status) of an alert by its distance in standard deviations; D-477: a drop takes the drop words."""
    levels = ALERT_LEVELS if rise else DROP_LEVELS
    return next((label, icon, status) for floor, label, icon, status in levels if distance >= floor)


def show_alert_buttons(week, family, family_open, alert, prefix, region=None):
    """D-491: the sharp rises (red) and the sharp drops (green) of the chosen family, or of the whole basket; they wake
    up once a family is chosen (D-352). One shows only those products, and pressing it again brings back every product.
    The count is of the place chosen: national, like K6 (D-477, D-489), or of the region (D-499). D-498: drawn by the
    panel and by the enlarged table, each with its keys; it returns the one pressed, and the caller remembers it."""
    now = read_place_alerts(region)
    now = now[now["week_start"] == pd.Timestamp(week)] if not now.empty else now
    if family_open and family not in (None, ALL_VALUES) and not now.empty:
        now = now[now["product_group"] == family]
    counts = {
        RISE: int((now["variation"] > 0).sum()) if not now.empty else 0,
        DROP: int((now["variation"] < 0).sum()) if not now.empty else 0,
    }
    chips = [
        (
            RISE,
            f"{prefix}_alert_trigger",
            tr("▲ {} alzas fuertes").format(counts[RISE]) if counts[RISE] != 1 else tr("▲ 1 alza fuerte"),
        ),
        (
            DROP,
            f"{prefix}_drop_trigger",
            tr("▼ {} bajas fuertes").format(counts[DROP]) if counts[DROP] != 1 else tr("▼ 1 baja fuerte"),
        ),
    ]
    pressed = None
    for direction, key, label in chips:
        on = alert == direction
        help_text = (
            tr("Pulsa de nuevo para ver todos los productos.")
            if on
            else alerts.describe_kind(direction == RISE, not is_public_profile(), bool(region))
            if family_open
            else tr("Elige primero una familia.")
        )
        if st.button(
            label,
            key=key,
            type="primary" if on else "secondary",
            disabled=not family_open or not counts[direction],
            help=help_text,
        ):
            pressed = direction
    return pressed


def show_alert_line(week, family, family_open, alert, region=None, rerun_scope="app"):
    """D-491: between steps 2 and 3, a thin line with the alert buttons, which show only those products in step 3.
    D-492: the search sits on the same line and never leaves: with a kind of alert chosen it looks only among those
    alerts. D-497: beside it, the filter by direction; an alert already shows one direction, so the filter rests at
    «Todo» while it is chosen and the two never contradict each other. D-532: drawn inside the fragment of step 4,
    a press reruns only that fragment."""
    with st.container(key="home_alert_line", horizontal=True, gap="small", vertical_alignment="center"):
        pressed = show_alert_buttons(week, family, family_open, alert, "home", region)
        if pressed:
            if pressed == alert:
                st.query_params.pop("alerta", None)
            else:
                st.query_params["alerta"] = pressed
            try:
                st.rerun(scope=rerun_scope)
            except StreamlitAPIException:  # a full run (the first draw, AppTest): the whole page reruns instead
                st.rerun()
        st.text_input(
            "Buscar",
            key="home_products_search",
            icon=":material/search:",
            placeholder="Producto, ej.: lechuga",
            label_visibility="collapsed",
            type="search",
            live=True,
            disabled=not family_open,
        )
        if alert:
            st.session_state["home_products_direction"] = PRODUCT_DIRECTIONS[0]
        st.selectbox(
            "Mostrar",
            PRODUCT_DIRECTIONS,
            key="home_products_direction",
            label_visibility="collapsed",
            disabled=not family_open or bool(alert),
        )


# endregion


# region Products of step 4
normalize_search = overview.normalize_search


matches_product_search = overview.matches_search  # D-478: one search rule for every table


def keep_direction(rows, direction):
    """D-497: «Subidas» or «Bajadas» keep every product that moved that way, sharp or not; a change that rounds to
    0.0 % is neither, as the table paints it (change_state)."""
    state = {'Subidas': 'rise', 'Bajadas': 'fall'}.get(direction)
    return rows if state is None else [row for row in rows if home_mockup.change_state(row['variation']) == state]


def sort_family_products(rows):
    """The family table, the largest change first; ties stay in a stable, readable order.
    A change resting on a single quote or a single region sorts after the others (D-146, D-327)."""

    def names(row):
        return (str(row['product']), str(row['variety']), str(row['channel']))

    def thin(row):
        # D-327: a change that rests on one quote, or on one region, is the least solid and goes last.
        return bool(row.get('_single_quote')) or row.get('_same_regions') == 1

    return sorted(rows, key=lambda row: (thin(row), -abs(row['variation']), names(row)))


@st.dialog("Productos", width="large")
def show_products_dialog(channel, *window):  # noqa: D417
    """D-498: a press in the window reruns only the window, outside the scope of show_home_page, so it brings the
    channel of step 2 back: the alerts are read under it (D-405)."""
    token = PRICE_SCOPE.set(channel)
    try:
        draw_products_window(*window)
    finally:
        PRICE_SCOPE.reset(token)


def draw_products_window(family, average, scope, family_rows, week, model, region, published=None, note="", updated=""):
    """The products table at the size of the window (D-317) with the same filters as the panel (D-322): it opens with the
    panel's search and direction (D-497), and filters on its own without closing. D-498: the same line as the panel,
    with the alert buttons; the window remembers its alert, since a press in it reruns only the window. D-509: and the
    same «Descargar», beside the count of prices. D-525: its notes say the window's own choices, not the panel's when
    it opened, and with an alert it carries the alerts table, as the panel does."""
    week_label, previous_label = model["week_label"], model["previous_label"]
    alert = st.session_state.get("dialog_products_alert")
    if alert:
        st.session_state["dialog_products_direction"] = PRODUCT_DIRECTIONS[0]
    with st.container(horizontal=True, vertical_alignment="center", key="dialog_products_filters"):
        pressed = show_alert_buttons(week, family, True, alert, "dialog", region)
        if pressed:
            st.session_state["dialog_products_alert"] = None if pressed == alert else pressed
            st.rerun(scope="fragment")
        query = st.text_input(
            'Buscar',
            key='dialog_products_search',
            icon=':material/search:',
            placeholder='Producto, ej.: lechuga',
            label_visibility='collapsed',
            type='search',
            live=True,
        )
        direction = st.selectbox(
            'Mostrar',
            PRODUCT_DIRECTIONS,
            key='dialog_products_direction',
            label_visibility='collapsed',
            disabled=bool(alert),
        )
    filters = describe_price_filters(region, current_channel(), family, direction, query.strip(), alert)
    if alert:
        with st.container(key='dialog_products_head', horizontal=True, vertical_alignment='center'):
            st.markdown(
                '<div class="greenocean-mockup products-large">' + home_mockup.alert_heading(region=region) + '</div>',
                unsafe_allow_html=True,
                width='stretch',
            )
            show_price_download(
                alert_download_rows(week, family, alert, query.strip(), region, family_rows),
                model,
                scope,
                week,
                updated,
                published,
                filters,
                'dialog',
            )
        st.markdown(family_alerts_table(week, family, alert, query.strip(), region), unsafe_allow_html=True)
        return
    rows = keep_direction(list(family_rows), direction)
    if query.strip():
        rows = [row for row in rows if matches_product_search(row, query)]
    rows = sort_family_products(rows)
    with st.container(key='dialog_products_head', horizontal=True, vertical_alignment='center'):
        st.markdown(
            '<div class="greenocean-mockup products-large">'
            + home_mockup.products_heading(family, average, scope, len(rows), len(family_rows), note)
            + '</div>',
            unsafe_allow_html=True,
            width='stretch',
        )
        show_price_download(rows, model, scope, week, updated, published, filters, 'dialog')
    st.markdown(
        '<div class="greenocean-mockup">'
        + home_mockup.products_table(
            rows,
            week_label,
            previous_label,
            query.strip(),
            region,
            published,
            show_family=family == ALL_VALUES,
            empty_note=NOTHING_MOVED.get(direction, ''),
        )
        + '</div>',
        unsafe_allow_html=True,
    )


# endregion


# region «Descargar»
@st.cache_data(show_spinner=False)
def build_price_files(built, notes, language):
    """D-509: the two files of «Descargar», built once per set of prices (the language is part of the key, because
    the headings and the notes are read in it)."""
    del language  # part of the cache key, not of the call
    return price_export.build_workbook(built, notes), price_export.build_csv(built)


def show_price_download(rows, model, scope, week, updated, published, filters, prefix):
    """D-509: the prices of step 4 as a file: every filtered price, not only the rows in sight, in the language of the
    visit. A dataset to work with, so Excel carries its table, its filter and its formats, and a sheet of notes."""
    built = tuple(
        tuple(values) for values in price_export.build_rows(rows, model['week_label'], model['previous_label'], scope)
    )
    notes = tuple(price_export.build_notes(model['week_label'], filters, updated, model, published))
    with st.popover(tr('Descargar'), icon=':material/download:', disabled=not built):
        if not built:
            st.caption(tr('No hay precios que descargar con estos filtros.'))
            return
        st.caption(tr('{} precios, con los filtros de esta pantalla.').format(home_mockup.number(len(built))))
        book, table = build_price_files(built, notes, i18n.get_language())
        st.download_button(
            tr('Excel (.xlsx)'),
            book,
            price_export.build_name(week, scope, 'xlsx'),
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            icon=':material/table_view:',
            key=f'{prefix}_download_xlsx',
            width='stretch',
        )
        st.download_button(
            tr('CSV (.csv)'),
            table,
            price_export.build_name(week, scope, 'csv'),
            'text/csv',
            icon=':material/description:',
            key=f'{prefix}_download_csv',
            width='stretch',
        )


def describe_price_filters(region, channel, family, direction, query, alert):
    """D-509: what the file holds, as the screen has it: the four steps, the order and the search."""
    chosen = [
        (
            'Región',
            tr('Todo Chile') if region in (None, ALL_VALUES) else home_mockup.short_region(region),
        ),
        ('Canal', data_terms.term(channel) if channel else tr('Todos los canales')),
        ('Familia', tr('Toda la canasta') if family in (None, ALL_VALUES) else home_mockup.short_family(family)),
    ]
    if alert:
        chosen.append(('Alertas', tr('Solo alzas fuertes') if alert == RISE else tr('Solo bajas fuertes')))
    if direction and direction != PRODUCT_DIRECTIONS[0]:
        chosen.append(('Mostrar', tr(direction)))
    if query:
        chosen.append(('Búsqueda', query))
    return chosen


def alert_download_rows(week, family, alert, query, region, family_rows):
    """D-525: with an alert chosen, «Descargar» carries the rows of the alerts table, not the family's: the same rows,
    in the same order and with the two prices the table shows (D-482); the search looks only among them, as the
    table does. The regions up and down come from the same count as the products table, and the package compared
    from the family row of the same product, when it has one (D-522)."""
    key = queries.KEY_COLUMNS + ['channel']
    directions = read_cached_region_directions(get_database_version(), week)
    packages = {tuple(row[field] for field in key): row.get('_packages') for row in family_rows}
    rows = []
    for row in home_alert_rows(week, family or ALL_VALUES, direction=alert, region=region).to_dict('records'):
        if query and not matches_product_search(row, query):
            continue
        before, now = alert_prices(row)
        product = tuple(row[field] for field in key)
        rows.append(
            {
                **{field: row[field] for field in key},
                'national_price': row['national_price'],
                '_same_before': before,
                '_same_now': now,
                'variation': row['variation'],
                '_regions': directions.get(product),
                '_packages': packages.get(product),
                '_single_quote': False,  # an alert rests on at least two quotes in each week (K6)
            }
        )
    return rows


# endregion


# region The page
def show_market_overview(mode, prefix):
    """Map, movement by family and products of one family on one screen (D-092)."""
    # Streamlit reruns this file without reimporting helpers; keep the live page
    # in sync when the dashboard markup changes during development.
    importlib.reload(home_mockup)
    options = read_cached_filter_options(get_database_version())
    apply_home_focus(options)
    if read_filter('week') not in options['week']:
        st.session_state[scoped('dashboard_week')] = options['week'][0]
    if read_filter('region') not in options['region']:
        st.session_state[scoped('dashboard_region')] = ALL_VALUES
    week, region = read_filter('week'), read_filter('region')
    st.session_state.pop('home_product_selection', None)
    latest = read_latest_run()
    stamp = to_chile_time(parse_run_start(latest['started_at']))
    month = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'][stamp.month - 1]
    updated = f'{stamp.day} {month} · {stamp:%H:%M}'
    # Every family stays in the movement chart; the selected one fills the product table.
    model = read_home_model(week, ALL_VALUES, region, DEFAULT_TOP_N)
    regional_rows = read_regional_movement_model(week)
    averages = home_mockup.family_averages(model['family_rows'])
    families = [family for family, _, _ in averages]
    family = st.query_params.get('familia')
    choices = families + [ALL_VALUES]  # D-450: «Toda la canasta» is chosen like a family and shows every product
    if family not in choices:
        family = families[0] if families else None
    scope = 'todo Chile' if region == ALL_VALUES else home_mockup.short_region(region)
    # D-352, D-372: in every view (user, professional and author) the panels 2 and 3 wait for the step before them.
    # D-531: only a click of this session opens a step; the address alone (a reload, a restored tab) opens nothing,
    # and choosing a profile again brings every step back to waiting (reset_home_steps).
    region_open = bool(st.session_state.get(scoped(HOME_REGION_DONE)))
    family_open = bool(st.session_state.get(scoped(HOME_FAMILY_DONE)))
    if not family_open:
        family = None  # no family is chosen for the reader
    products_family = family or (families[0] if families else None)  # what the locked table shows, dimmed

    def overview_link(chosen_region, chosen_family, step=None, alert=None):
        address = scope_address()  # D-405: a channel page links to itself
        parameters = {'_home_region': chosen_region or ALL_VALUES, '_home_week': week}
        if chosen_family:
            parameters['familia'] = chosen_family
        if alert:
            parameters['alerta'] = alert
        if step:
            parameters[HOME_STEP_PARAMETER] = step
        return address + ('&' if '?' in address else '?') + urlencode(parameters)

    def channel_link(chosen_channel):
        # D-494: step 2 keeps the region and the family; without «_home_week» a channel opens on its own latest week
        address = channel_address(chosen_channel) if chosen_channel else build_page_address(PAGE_HOME)
        parameters = {'_home_region': region}
        if family:
            parameters['familia'] = family
        return address + ('&' if '?' in address else '?') + urlencode(parameters)

    flash = st.session_state.pop(scoped(HOME_FLASH), None)
    palette = charts.get_palette(mode)
    if st.session_state.get('home_products_search'):
        st.session_state[scoped(HOME_SEARCHED)] = (
            True  # D-372: once someone typed, the search stops glowing for the visit
        )
    st.markdown(
        build_steps_css(palette, region_open, family_open, flash, st.session_state.get(scoped(HOME_SEARCHED))),
        unsafe_allow_html=True,
    )

    # D-264: the only header of the Resumen, one thin bar.
    with st.container(key="home_bar", horizontal=True, vertical_alignment="center"):
        show_return_button()
        st.markdown(
            home_mockup.dashboard_bar(
                scope_path(),
                describe_week_span(week),
                model['family_rows'],
                regional_rows,
                None if region == ALL_VALUES else region,
                compared=sum(model['counts']),
                available=model['available'],
                next_label=weeks.week_range(weeks.next_week(week)),  # D-374
            ),
            unsafe_allow_html=True,
            width="stretch",
        )
        st.markdown(
            home_mockup.dashboard_updated(updated, latest['status'] == etl.STATUS_LOADED),
            unsafe_allow_html=True,
            width="content",
        )
    place = None if region == ALL_VALUES else region  # D-499: what step 1 chose; everything after it works on it
    # D-398: the header only places the reader. The note of a late source is content, in one row under the bar.
    notice = describe_late_sources(latest['message'] if latest['status'] == etl.STATUS_LOADED else '')
    channel = current_channel()
    if channel is not None:  # D-405: a channel says only its own delay
        card = next(
            (item for item in read_channel_cards(get_database_version(), place) if item['channel'] == channel),
            None,
        )
        notice = (
            tr('ODEPA aún no publica la semana {}').format(i18n.tr_week(card['late'])) if card and card['late'] else ''
        )
        everyone = read_all_families()
        if card and len(card['families']) < len(everyone):  # D-406: read from the data, never written by hand
            names = i18n.join_names(home_mockup.short_family(family) for family in card['families'])
            covered = tr('Este canal publica {} de las {} familias: {}.').format(
                len(card['families']), len(everyone), names
            )
            notice = f'{covered} {notice}'.strip()
    # D-490: the row under the bar holds only the note of a late source; D-491: the alerts sit between steps 2 and 3.
    if notice:
        with st.container(key='home_info', horizontal=True, vertical_alignment='center'):
            st.caption(notice)  # D-356: a quiet line; the week is not filled in, it waits for the source
    # D-452: a channel page behaves exactly as the Dashboard: its three panels stay together (D-446), nothing folds.

    def show_products(alert):
        with st.container(key='home_products'):
            query = st.session_state.get('home_products_search', '').strip()  # D-492: typed in the alert line
            if not family_open:
                st.markdown(
                    f'<div class="greenocean-mockup">{home_mockup.lock_overlay(4)}</div>', unsafe_allow_html=True
                )
            rows = [
                row
                for row in model['family_rows']
                if products_family == ALL_VALUES or row['product_group'] == products_family
            ]
            family_rows = list(rows)
            average = (
                home_mockup.basket_median(model['family_rows'])
                if products_family == ALL_VALUES
                else next((value for name, value, _ in averages if name == products_family), None)
            )
            direction = st.session_state.get('home_products_direction', PRODUCT_DIRECTIONS[0])  # D-497: alert line
            total = len(rows)
            rows = keep_direction(rows, direction)
            if query:
                rows = [row for row in rows if matches_product_search(row, query)]
            rows = sort_family_products(rows)
            published = None
            note = ''
            if region == ALL_VALUES:
                # D-327: what every row was calculated from, and the one line that says how to read the prices.
                calculation, published = read_cached_region_calculation(get_database_version(), week)
                coverage = model.get('family_coverage', {})
                stats = (
                    {key: sum(item.get(key, 0) for item in coverage.values()) for key in ('available', 'comparable')}
                    if products_family == ALL_VALUES
                    else coverage.get(products_family) or {}
                )
                note = home_mockup.products_note(published, stats.get('available', 0) - stats.get('comparable', 0))
                for row in family_rows:
                    row['_calc'] = calculation.get(tuple(row[field] for field in queries.KEY_COLUMNS + ['channel']))
            # D-497: with the filter in the alert line, «Ampliar» shares the heading's line and the table keeps the height
            with st.container(key='home_products_head', horizontal=True, vertical_alignment='center'):
                st.markdown(
                    '<div class="greenocean-mockup">'
                    + (
                        home_mockup.alert_heading(step=4, region=place)
                        if alert
                        else home_mockup.products_heading(
                            products_family or 'Sin familia', average, scope, len(rows), total, note, step=4
                        )
                    )
                    + '</div>',
                    unsafe_allow_html=True,
                    width='stretch',
                )
                with st.container(key='home_products_tools'):
                    show_price_download(
                        # D-525: with an alert chosen, the file carries the alerts table, the one in sight
                        alert_download_rows(week, family, alert, query, place, family_rows) if alert else rows,
                        model,
                        scope,
                        week,
                        updated,
                        published,
                        describe_price_filters(region, current_channel(), products_family, direction, query, alert),
                        'home',
                    )
                enlarge = st.button(
                    tr('Ampliar'),
                    icon=':material/open_in_full:',
                    key='home_products_enlarge',
                    help=tr('Ampliar la tabla de productos'),
                )
            directions = read_cached_region_directions(get_database_version(), week)
            for row in rows:
                row['_regions'] = directions.get(tuple(row[field] for field in queries.KEY_COLUMNS + ['channel']))
            table_html = (
                family_alerts_table(week, family, alert, query, place)
                if alert
                else '<div class="greenocean-mockup">'
                + home_mockup.products_table(
                    rows,
                    model['week_label'],
                    model['previous_label'],
                    query.strip(),
                    None if region == ALL_VALUES else region,
                    published,
                    show_family=products_family == ALL_VALUES,
                    empty_note=NOTHING_MOVED.get(direction, ''),
                )
                + '</div>'
            )
            st.markdown(table_html, unsafe_allow_html=True)
            if enlarge:
                for row in family_rows:
                    row['_regions'] = directions.get(tuple(row[field] for field in queries.KEY_COLUMNS + ['channel']))
                st.session_state.update(
                    {
                        'dialog_products_search': query,
                        'dialog_products_direction': direction,
                        'dialog_products_alert': alert,
                    }
                )
                show_products_dialog(
                    current_channel(),
                    family or 'Sin familia',
                    average,
                    scope,
                    family_rows,
                    week,
                    model,
                    None if region == ALL_VALUES else region,
                    published,
                    note,
                    updated,
                )

    # D-494: the map gives a little room to the right side: steps 2 (the channels) and 3 (the families) side by side, of
    # one height, and under both the alert line and the products, across the whole width.
    map_column, detail_column = st.container(key='home_overview').columns([0.6, 1.6], gap='small')
    # Markdown's explicit HTML mode preserves the inline geographic SVG; st.html's
    # sanitizer intentionally removes interactive SVG links.
    map_column.markdown(
        '<div class="greenocean-mockup">'
        + home_mockup.regional_map(
            regional_rows,
            lambda chosen: overview_link(chosen, family, 'region'),
            model['week_label'],
            model['previous_label'],
            None if region == ALL_VALUES else region,
            step=1,
            all_link=overview_link(None, family, 'region'),
            prompt=not region_open,
        )
        + '</div>',
        unsafe_allow_html=True,
    )
    trends, basket_trend = read_home_trends(get_database_version(), week, place)
    basket_value = home_mockup.basket_median(model['family_rows'])
    with detail_column:
        channel_column, family_column = st.container(key='home_top').columns([0.35, 0.65], gap='small')
        with channel_column, st.container(key='home_channels'):
            # D-494: step 2 waits for the region dimmed, without a padlock of its own: step 3 already says what to do
            st.markdown(
                '<div class="greenocean-mockup">'
                + home_mockup.channel_list(
                    read_channel_cards(get_database_version(), place),
                    channel_link,
                    current_channel(),
                    channel_link(None),
                    lambda name: channel_icons.image(name, 20),
                    step=2,
                )
                + '</div>',
                unsafe_allow_html=True,
            )
        with family_column, st.container(key='home_families'):
            if not region_open:
                st.markdown(
                    f'<div class="greenocean-mockup">{home_mockup.lock_overlay(3)}</div>', unsafe_allow_html=True
                )
            st.markdown(
                '<div class="greenocean-mockup">'
                + home_mockup.family_movement(
                    model['family_rows'],
                    lambda chosen: overview_link(None if region == ALL_VALUES else region, chosen, 'family'),
                    family,
                    scope,
                    home_mockup.movement_note(model),
                    step=3,
                    trends=trends,
                    basket=None
                    if basket_value is None
                    # D-506: the counts behind the median, from the same comparable prices
                    else (basket_value, basket_trend, home_mockup.basket_counts(model['family_rows'])),
                    basket_link=overview_link(None if region == ALL_VALUES else region, ALL_VALUES, 'family'),
                )
                + '</div>',
                unsafe_allow_html=True,
            )

        @st.fragment
        def show_products_section():
            """D-532: the alert line and step 4 rerun on their own: a search, a filter, an alert button or «Ampliar»
            no longer redraw the map and steps 1 to 3. D-489, D-491: ▲ or ▼ shows only the chosen family's sharp rises
            or drops in step 4; choosing a family again brings back every product. The alert is read here, because this
            part reruns without the page."""
            chosen = st.query_params.get('alerta') if family_open else None
            chosen = chosen if chosen in ALERT_KINDS else None
            show_alert_line(week, products_family, family_open, chosen, place, rerun_scope='fragment')
            if st.session_state.get('home_products_search'):  # D-372: the glow stops here too, between page runs
                st.session_state[scoped(HOME_SEARCHED)] = True
                st.markdown(f'<style>{SEARCH_STILL_CSS}</style>', unsafe_allow_html=True)
            show_products(chosen)

        show_products_section()
    # Under both columns, full width (D-150): the note no longer lengthens one side.
    st.markdown(
        '<div class="greenocean-mockup">'
        + home_mockup.coverage_note(
            model,
            # D-502: the Usuario view has no «Controles de datos» nor «Plan de calidad»: no link to them
            None if is_public_profile() else build_page_address(PAGE_OPERATIONS),
            None if is_public_profile() else build_page_address(PAGE_DOCUMENTATION),
            family,
        )
        + '</div>',
        unsafe_allow_html=True,
    )


def show_home_page(mode):
    """«Semanal» (D-494): its optional step 2 draws the whole page with one channel's prices and that channel's own latest
    week (D-405); without a channel, every channel in the week both sources published (D-356)."""
    apply_home_link_click()  # before the channel is read: a click on step 2 changes it
    channel = st.query_params.get(CHANNEL_PARAMETER)
    known = {card["channel"] for card in read_channel_cards(get_database_version())}
    token = PRICE_SCOPE.set(channel) if channel in known else None
    try:
        with st.container(key="market_dashboard"):
            show_market_overview(mode, "home")
    finally:
        if token is not None:
            PRICE_SCOPE.reset(token)


# endregion
