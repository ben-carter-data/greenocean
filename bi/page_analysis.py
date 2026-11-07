"""«Análisis» and its tabs (D-541): «Mensual», «Histórico», «Precios e inflación», «Insights», «Interesados» and
«Método», with the family cards, the price context and the texts of the analysis.
"""

import functools
import html
import re

import pandas as pd
import streamlit as st

from bi import (
    ba_trends,
    business_analysis,
    charts,
    doc_diagrams,
    home_mockup,
    i18n,
    inflation_view,
    interest_map,
    overview,
    quality_live,
    quality_metrics,
    queries,
    weeks,
)
from bi.app_frame import (
    DRAWN_TAB,
    build_kpi_code_html,
    build_page_address,
    can_open,
    find_menu_page,
    is_dark_theme,
    keep_context,
    show_page_bar,
    show_view_tabs,
)
from bi.constants import (
    BA_HISTORY_TAB,
    BA_MONTHLY_TAB,
    BA_RETIRED_TABS,
    BA_TAB_OF_VIEW,
    BA_TAB_PARAMETER,
    BA_TABS,
    BASIS_HELP,
    BASIS_NOMINAL,
    BASIS_REAL,
    CONTEXT_BASIS_KEY,
    GIT_TAB_LOG,
    GIT_TAB_PARAMETER,
    NO_DATA_TEXT,
    PAGE_ANALYSIS,
    PAGE_BA,
    PAGE_GIT,
    PAGE_HOME,
    PAGE_ICONS,
    PAGE_INSIGHTS,
    PAGE_QUALITY_PLAN,
    PAGE_SEASONALITY,
    PAGE_STAKEHOLDERS,
    SIDEBAR_ICONS,
    VIEW_PARAMETER,
    WINDOW_OF_VIEW,
    WINDOW_PAGES,
)
from bi.data_access import (
    get_database_version,
    read_cached_all_variations,
    read_cached_national_prices,
    read_cached_price_alerts_all,
    read_indicator,
    read_price_alerts,
)
from bi.i18n import tr
from bi import static_files

# region Constants
CONTEXT_CHANNELS = list(charts.CONTEXT_CHANNELS)


FAMILY_CARD_COLUMNS = 4


# What «Precios e inflación» measures (D-267), in the right corner of its bar, with its definition on hover.
INFLATION_TERMS = [
    (
        "KPI",
        "Variación vs IPC",
        "Diferencia, en puntos, entre lo que subió la familia desde enero 2022 y lo que subió el IPC de alimentos del INE. "
        f"Más de {inflation_view.SAME_PACE_POINTS:.0f} puntos arriba: subió más que la inflación; más de "
        f"{inflation_view.SAME_PACE_POINTS:.0f} abajo: menos.",
    ),
    (
        "Métrica",
        "Índice ene 2022 = 100",
        "Cada mes, el precio promedio de las semanas de cada serie de consumidor de ODEPA sobre su precio de enero "
        "2022, por 100; la familia toma la mediana de sus series, sin ponderar. Solo entran las series con precio en "
        "enero 2022 y en el último mes del INE; un mes intermedio usa las que tienen precio ese mes.",
    ),
]


FAMILY_FOCUS_KEY = "inf_focus"


OVERVIEW_WEEK_KEY, OVERVIEW_FAMILY_KEY = "ov_week", "ov_family"


BA_TAB_KEY = "ba_tab"


INTEREST_RESERVED = 215


SYSTEM_DECISION_PAGES = {"sqap": PAGE_QUALITY_PLAN, "git": PAGE_GIT}
# endregion


# region «Análisis» and its tabs
def build_interest_map_html(rows, palette, address_of_view):
    """D-444: the interest map of «Interesados»; D-455: drawn by bi/interest_map.py, which the PRD draws too. A
    stakeholder whose page this view's menu does not lead to says where it opens instead."""
    link_of = functools.partial(interest_link, address_of_view)
    return interest_map.build_map_html(rows, palette, link_of, tr, criterion=not DRAWN_TAB.get())


def interest_link(address_of_view, row):
    """The address of a stakeholder's page when this view's menu leads to it; otherwise where it opens instead."""
    view = next((page for page in (find_menu_page(name) for name in row["pages"]) if page), None)
    if view and can_open(view):
        return address_of_view(view), ""
    return None, tr("Se abre en la vista Profesional.")


def show_ba_page(mode):
    """«Análisis» (D-456): the Analysis in one page, in tabs. «Mensual» and «Histórico» (D-457) are the
    history of the prices as a report, one period month by month and the whole history year by year; the other tabs
    are the pages it gathered, drawn by their own code, each under its tab."""
    show_page_bar(
        PAGE_BA,
        PAGE_BA,
        "La historia de los precios por mes, año y temporada, con sus valores atípicos; los precios frente a la "
        "inflación, las respuestas de hoy, quién usa los datos y cómo se calcula cada cifra.",
        live="weekly_price, ipc_weekly y las alertas K6 se leen en la Base DuckDB al abrir la página.",
    )
    palette = charts.get_palette(mode)
    wanted = st.query_params.get(BA_TAB_PARAMETER)
    wanted = BA_RETIRED_TABS.get(wanted, wanted)
    if wanted in BA_TABS:
        st.session_state[BA_TAB_KEY] = wanted  # read once: from here on, the tabs rule
        st.query_params.pop(BA_TAB_PARAMETER)
    # D-458: the tab and the period of this run are already in the session, before their widgets are drawn
    show_ba_context(
        st.session_state.get(BA_TAB_KEY) if st.session_state.get(BA_TAB_KEY) in BA_TABS else BA_TABS[0], mode
    )
    with st.container(key="ba_head", horizontal=True, vertical_alignment="bottom"):
        tab = show_view_tabs(BA_TAB_KEY, BA_TABS, palette)
        if tab in (BA_MONTHLY_TAB, BA_HISTORY_TAB):
            show_ba_filters(tab)  # D-456: the report's filters share the row of the tabs, like a report of Power BI
    token = DRAWN_TAB.set(tab)
    try:
        if tab == BA_MONTHLY_TAB:
            show_ba_monthly(mode)
        elif tab == BA_HISTORY_TAB:
            show_ba_history(mode)
        elif tab == BA_TAB_OF_VIEW[PAGE_SEASONALITY]:
            show_price_context_page(mode)
        elif tab == BA_TAB_OF_VIEW[PAGE_INSIGHTS]:
            show_insights_page(mode)
        elif tab == BA_TAB_OF_VIEW[PAGE_STAKEHOLDERS]:
            show_stakeholders_page(mode)
        else:
            show_ba_method(mode)
    finally:
        DRAWN_TAB.reset(token)


@st.cache_data(show_spinner=False)
def read_ba_history(database_version):
    """The history behind «Mensual» and «Histórico» (D-456, D-457), read once per database: the monthly index of the
    families and of the whole basket against the IPC (D-163), K1, K4 and the K6 alerts, each with the month of its
    week."""
    rows, last = inflation_view.build_family_index(
        queries.run_sql(inflation_view.SERIES_SQL),
        queries.run_sql("SELECT year, month, food_index FROM ipc_monthly"),
        basket=True,
    )
    margins = ba_trends.add_month_key(
        queries.run_query("k1_margin")[["week_start", "product_group", "product", "margin"]]
    )
    seasonal = ba_trends.add_month_key(
        queries.run_query("k4_seasonal_index")[["week_start", "product_group", "product", "seasonal_index"]]
    )
    found = read_cached_price_alerts_all(database_version)
    alerts_found = ba_trends.add_month_key(found[["week_start", "product_group", "product", "variation"]])
    return rows, last, margins, seasonal, alerts_found


@st.cache_data(show_spinner=False)
def read_ba_products(database_version):
    """D-478: the same history one level down, each product of the consumer series as a family is computed."""
    _, _, margins, seasonal, alerts_found = read_ba_history(database_version)
    return ba_trends.product_frames(
        queries.run_sql(inflation_view.SERIES_SQL),
        queries.run_sql("SELECT year, month, food_index FROM ipc_monthly"),
        margins,
        seasonal,
        alerts_found,
    )


@st.cache_data(show_spinner=False)
def read_ba_food_cpi(database_version):
    """D-518: the INE food CPI of every month published, for the insight of «Histórico»."""
    return queries.run_sql("SELECT year, month, food_index FROM ipc_monthly")


def show_ba_context(tab, mode):
    """D-458: the green panel above the tabs says what the reader is looking at, from which month to which, and why
    each chart starts and ends where it does; it follows the tab and the period chosen."""
    rows, last, *_ = read_ba_history(get_database_version())
    if rows.empty:
        return
    if tab == BA_MONTHLY_TAB:
        period = st.session_state.get("ba_period")
        lead, detail = ba_trends.monthly_context(
            period if period in ba_trends.periods(last) else ba_trends.periods(last)[0], last
        )
    elif tab == BA_HISTORY_TAB:
        lead, detail = ba_trends.history_context(last)
    elif tab == BA_TAB_OF_VIEW[PAGE_SEASONALITY]:
        lead, detail = ba_trends.inflation_context(last)
    elif tab == BA_TAB_OF_VIEW[PAGE_INSIGHTS]:
        version = get_database_version()
        week = overview_week(sorted(read_cached_all_variations(version)["week_start"].unique()))
        lead, detail = ba_trends.insights_context(week, last)
    elif tab == BA_TAB_OF_VIEW[PAGE_STAKEHOLDERS]:
        lead, detail = ba_trends.stakeholders_context()
    else:
        lead, detail = ba_trends.method_context()
    st.markdown(
        ba_trends.build_context_css(charts.get_palette(mode), ba_green(mode)) + ba_trends.context_html(lead, detail),
        unsafe_allow_html=True,
    )


def ba_green(mode):
    """The fluorescent green of GreenOcean (D-450), deeper on a light theme so it still reads on white."""
    return home_mockup.SEARCH_DARK if is_dark_theme(mode) else home_mockup.SEARCH_LIGHT


def show_ba_filters(tab):
    """The family of «Mensual» and «Histórico», and the period of «Mensual», on the row of the tabs; what each means is
    on hover. «Histórico» has no period: it is always from January 2022 to the last month."""
    rows, last, *_ = read_ba_history(get_database_version())
    if rows.empty:
        return
    with st.container(key="ba_filters", horizontal=True, vertical_alignment="bottom", width="content"):
        if tab == BA_MONTHLY_TAB:
            st.selectbox(
                tr("Período"),
                ba_trends.periods(last),
                key="ba_period",
                format_func=tr,
                width=190,
                help=tr(
                    "Los últimos 12 meses o un año, mes a mes, hasta {}, el último mes que publicó el INE. Un año se "
                    "mide de diciembre a diciembre, como el IPC."
                ).format(ba_trends.month_label(last)),
            )
        family = st.selectbox(
            tr("Familia"),
            [ba_trends.BASKET] + ba_trends.families(rows),
            key="ba_family",
            format_func=lambda name: tr(home_mockup.short_family(name)),
            width=210,
            help=tr(
                "Toda la canasta: la mediana de todas las series de consumidor, sin ponderar (el IPC del INE pondera "
                "por gasto); una familia, solo las suyas."
            ),
        )
        # D-478: under the family, any of its products (of the whole basket, each with its family); typing searches
        family_of = read_ba_products(get_database_version())[-1]
        products = [ba_trends.ALL_PRODUCTS] + ba_trends.products_of(family_of, family)
        if st.session_state.get("ba_product") not in products:
            st.session_state["ba_product"] = ba_trends.ALL_PRODUCTS
        st.selectbox(
            tr("Producto"),
            products,
            key="ba_product",
            format_func=lambda key: (
                tr(key)
                if key == ba_trends.ALL_PRODUCTS
                else ba_trends.product_name(key)
                if family != ba_trends.BASKET
                else f"{ba_trends.product_name(key)} · {home_mockup.short_family(family_of[key])}"
            ),
            width=230,
            help=tr("Escribe para buscar un producto; sus cifras se calculan como las de una familia."),
        )


def chosen_ba_family(rows):
    """The family chosen in «Mensual» or «Histórico»: the two tabs share it."""
    choices = [ba_trends.BASKET] + ba_trends.families(rows)
    return choices, st.session_state.get("ba_family") if st.session_state.get("ba_family") in choices else choices[0]


def chosen_ba_level(rows, margins, seasonal, found):
    """D-478: what «Mensual» and «Histórico» show: the frames and name of the subject (the basket, a family or a
    product) and the table's rows, one level under the family (the families under the basket, a family's products
    under it, with the family first), each as (frames, name)."""
    choices, family = chosen_ba_family(rows)
    family_frames = (rows, margins, seasonal, found)
    product = st.session_state.get("ba_product")
    product_rows, product_margins, product_seasonal, product_found, family_of = read_ba_products(get_database_version())
    product_frames = (product_rows, product_margins, product_seasonal, product_found)
    if product not in family_of:
        product = None
    if product:
        family = family_of[product]
    if family == ba_trends.BASKET:
        return (family_frames, family), [(family_frames, name) for name in choices]
    siblings = ba_trends.products_of(family_of, family)
    if product:  # the chosen product right under its family, so the two are read together
        siblings = [product] + [key for key in siblings if key != product]
    table = [(family_frames, family)] + [(product_frames, key) for key in siblings]
    return (product_frames, product) if product else (family_frames, family), table


def show_ba_monthly(mode):
    """«Mensual» (D-457): one period, the last 12 months or one year, month by month: five KPI cards, three charts and
    the table by family. Every card and column says on hover how it is computed; every chart, which months it shows."""
    palette = charts.get_palette(mode)
    rows, last, margins, seasonal, found = read_ba_history(get_database_version())
    if rows.empty:
        st.info(NO_DATA_TEXT)
        return
    st.markdown(ba_trends.build_css(palette, ba_green(mode)), unsafe_allow_html=True)
    (frames, subject), table = chosen_ba_level(rows, margins, seasonal, found)
    period = st.session_state.get("ba_period")
    if period not in ba_trends.periods(last):
        period = ba_trends.periods(last)[0]
    start, end = ba_trends.bounds(period, last)
    figures = ba_trends.monthly(*frames, subject, start, end)
    st.markdown(
        ba_trends.monthly_cards(figures, start, end, ba_trends.wholesale_families(margins)), unsafe_allow_html=True
    )
    show_ba_tiles(ba_trends.monthly_tiles(frames[0], figures, start, end, mode))
    summaries = [ba_trends.monthly(*item_frames, name, start, end) for item_frames, name in table]
    st.markdown(ba_trends.monthly_table(summaries, subject), unsafe_allow_html=True)


def show_ba_history(mode):
    """«Histórico» (D-457): the whole history, from January 2022 to the last month, year by year and by season: five
    KPI cards, three charts and the table by family."""
    palette = charts.get_palette(mode)
    rows, last, margins, seasonal, found = read_ba_history(get_database_version())
    if rows.empty:
        st.info(NO_DATA_TEXT)
        return
    st.markdown(ba_trends.build_css(palette, ba_green(mode)), unsafe_allow_html=True)
    (frames, subject), table = chosen_ba_level(rows, margins, seasonal, found)
    figures = ba_trends.history(*frames, subject, last)
    st.markdown(ba_trends.history_cards(figures, last), unsafe_allow_html=True)
    show_ba_tiles(ba_trends.history_tiles(frames[0], figures, last, mode))
    insight = ba_trends.food_cpi_insight(read_ba_food_cpi(get_database_version()))
    if insight:  # D-518
        st.markdown(ba_trends.insight_html(*insight), unsafe_allow_html=True)
    summaries = [ba_trends.history(*item_frames, name, last) for item_frames, name in table]
    st.markdown(ba_trends.history_table(summaries, subject), unsafe_allow_html=True)


def show_ba_tiles(tiles):
    """D-457, D-460: three charts side by side, each with its title and the months it shows. Its green magnifier opens it
    large in a window, with what it measures and what follows from it."""
    for index, (column, (title, note, measures, deduce, draw)) in enumerate(zip(st.columns(3, gap="medium"), tiles)):
        heading = f'<p class="ba-chart-title">{html.escape(title)}<span>{html.escape(note)}</span></p>'
        with column, st.container(key=f"ba_tile_{index}"):
            # its own key: a key that started with «ba_tile_» would take the tile's height rules and leave the chart none
            with st.container(key=f"ba_chart_head_{index}", horizontal=True, vertical_alignment="top"):
                st.markdown(heading, unsafe_allow_html=True, width="stretch")
                if st.button(
                    tr("Ampliar"), icon=":material/zoom_in:", key=f"ba_enlarge_{index}", help=tr("Ampliar el gráfico")
                ):
                    st.dialog(title, width="large")(show_ba_chart_dialog)(title, note, measures, deduce, draw)
            st.altair_chart(draw(height="container"), width="stretch", height="stretch", theme=None)


def show_ba_chart_dialog(title, note, measures, deduce, draw):
    """D-460: a chart of «Mensual» or «Histórico» at the size of the window, with its months, what it measures and what
    follows from it. The window's own title is hidden in every dialog (D-316), so the chart's title opens its content."""
    st.markdown(
        f'<p class="ba-zoom-title">{html.escape(title)}<span>{html.escape(note)}</span></p>'
        + ba_trends.zoom_text(measures, deduce),
        unsafe_allow_html=True,
    )
    st.altair_chart(draw(width="container", height=ba_trends.ZOOM_HEIGHT), width="stretch", theme=None)


def show_ba_method(mode):
    """«Método» (D-456): only what the PRD does not hold, read from the documents: how each KPI is computed and the
    system decisions. The rest of the old «Análisis de negocio y sistemas» lives in the PRD."""
    palette = charts.get_palette(mode)
    st.markdown(
        build_analysis_css(palette) + f"<style>{build_insight_table_css(palette)}</style>", unsafe_allow_html=True
    )
    kpis, decisions = st.columns([1.35, 1], gap="large")
    with kpis, st.container(key="analysis_body"):
        show_analysis_block("KPIs", mode)
    with decisions, st.container(key="analysis_decisions"):
        show_analysis_block("Decisiones de sistema", mode)


def show_stakeholders_page(mode):
    """«Interesados» (D-376, D-444): the interest map, read from the PRD (3.4) in the reader's language: three rings
    around GreenOcean and each stakeholder on its ring, with why it is there and the page it opens."""
    show_page_bar(
        PAGE_STAKEHOLDERS,
        PAGE_STAKEHOLDERS,
        "Quién usa estos datos y cuánto depende de ellos.",
    )
    palette = charts.get_palette(mode)
    st.markdown(build_interest_css(palette), unsafe_allow_html=True)
    st.markdown(
        build_interest_map_html(business_analysis.read_interest(), palette, build_page_address), unsafe_allow_html=True
    )


def build_interest_css(palette):
    # D-458: as a tab, the green panel above the tabs takes height; the rule of the rings moved into it.
    return interest_map.build_css(palette, reserved=INTEREST_RESERVED if DRAWN_TAB.get() else 190)


# endregion


# region Price context and family cards
def build_context_css(mode):
    palette = charts.get_palette(mode)
    return static_files.style(
        "analysis_context.css",
        {
            'var(--go-text)': palette['text'],
            'var(--go-accent)': palette['accent'],
            'var(--go-strong-text)': palette['strong_text'],
            'var(--go-card-border)': palette['card_border'],
            'var(--go-card)': palette['card'],
            'var(--go-fff-if-palette-base-charts-base-dark-else-000)': '#fff'
            if palette['base'] != charts.BASE_DARK
            else '#000',
            'var(--go-0-1px-0-rgba-255-255-255-07-inset-0-22px-40px-28)': '0 1px 0 rgba(255,255,255,.07) inset, 0 22px 40px -28px rgba(0,0,0,.9), 0 0 0 1px rgba(255,255,255,.03)'
            if palette['base'] == charts.BASE_DARK
            else '0 1px 0 #fff inset, 0 22px 40px -30px rgba(15,27,45,.45), 0 6px 14px -10px rgba(15,27,45,.18)',
            'var(--go-0-1px-0-rgba-255-255-255-09-inset-0-30px-50px-28)': '0 1px 0 rgba(255,255,255,.09) inset, 0 30px 50px -28px rgba(0,0,0,.95), 0 0 0 1px rgba(255,255,255,.05)'
            if palette['base'] == charts.BASE_DARK
            else '0 1px 0 #fff inset, 0 30px 50px -28px rgba(15,27,45,.5), 0 10px 18px -10px rgba(15,27,45,.2)',
            'var(--go-reference)': palette['reference'],
            'var(--go-grid)': palette['grid'],
        },
    )


@st.cache_data
def read_family_inflation(database_version):
    """(monthly index per family and IPC, last IPC month, summary, IPC total, IPC 12 m) (D-163)."""
    rows, last = inflation_view.build_family_index(
        queries.run_sql(inflation_view.SERIES_SQL), queries.run_sql("SELECT year, month, food_index FROM ipc_monthly")
    )
    summary, ipc_total, ipc_year = inflation_view.summarize_families(rows, last)
    return rows, last, summary, ipc_total, ipc_year


@st.cache_data(show_spinner=False)
def read_product_inflation(database_version):
    """D-478: the same monthly index one level down: one line per product of the consumer series (its own series
    against January 2022, the families' rule), its summary against the IPC, and each product's family."""
    series = queries.run_sql(inflation_view.SERIES_SQL)
    rows, last = inflation_view.build_family_index(
        series.assign(product_group=series["product"]),
        queries.run_sql("SELECT year, month, food_index FROM ipc_monthly"),
    )
    summary, _, _ = inflation_view.summarize_families(rows, last)
    indexed = set(rows["product_group"])
    family_of = {
        product: group for product, group in zip(series["product"], series["product_group"]) if product in indexed
    }
    return rows, summary, family_of


def format_family_percent(value):
    """A family's change for its panel title, or a dash when it has none."""
    return "—" if value is None or pd.isna(value) else charts.format_signed_percent(value)


def format_cpi_month(pair):
    """(2026, 9) as «septiembre 2026», in the words of the charts."""
    return f"{charts.CHILE_LOCALE['time']['months'][pair[1] - 1]} {pair[0]}"


def build_family_panel_titles(summary, ipc_total=None):
    """{family: "Hortalizas|+60,2 % · más que la inflación"}, biggest gap first; with
    ipc_total, the food IPC closes the list as the basket every family is measured against."""
    percent = format_family_percent
    titles = {
        row.family: f"{home_mockup.short_family(row.family)}|{percent(row.total)} · {row.verdict}"
        for row in summary.itertuples()
    }
    if ipc_total is not None:
        titles[inflation_view.IPC_NAME] = f"IPC de alimentos (INE)|{percent(ipc_total)} · la canasta de referencia"
    return titles


def build_family_card_title_html(family, title, color=None):
    """The head of a family card: the name, and under it the rise and the verdict in
    the family's color (a product's, D-478, in its family's)."""
    name, verdict = title.split("|", 1)
    color = color or inflation_view.FAMILY_COLORS.get(family, "var(--text-color)")
    return (
        f'<div class="inf-panel-head"><b>{html.escape(name)}</b>'
        f'<span style="color:{color}">{html.escape(verdict)}</span></div>'
    )


def focus_family(family):
    st.session_state[FAMILY_FOCUS_KEY] = family


def build_family_insights_html(insights, family, color=None):
    """The reading of an enlarged family (D-267): what its own numbers say, one short line per fact."""
    color = color or inflation_view.FAMILY_COLORS.get(family, "#94a3b8")
    return (
        f'<div class="inf-insights" style="--c:{color}"><h4>Lectura de los datos</h4>'
        + "".join(f'<p><em>{html.escape(label)}</em>{html.escape(text)}</p>' for label, text in insights)
        + "</div>"
    )


def show_family_cards(rows, titles, mode, real, summary=None, last=None):
    """One raised card per family (D-174), four per row, the same chart size and the
    same y scale. A card's «Ampliar» shows that family alone, large (D-177), beside
    the reading of its own numbers (D-267)."""
    domain = inflation_view.family_domain(rows, real)
    focus = st.session_state.get(FAMILY_FOCUS_KEY)
    if focus in titles:
        # D-478: the enlarged family goes down to any of its products, each read against the IPC as a family is
        product_rows, product_summary, family_of = read_product_inflation(get_database_version())
        products = [ba_trends.ALL_PRODUCTS] + sorted(name for name, group in family_of.items() if group == focus)
        if st.session_state.get("inf_product") not in products:
            st.session_state["inf_product"] = ba_trends.ALL_PRODUCTS
        product = st.session_state["inf_product"]
        color = inflation_view.FAMILY_COLORS.get(focus)
        subject, subject_rows, subject_summary, subject_domain, title = (
            (focus, rows, summary, domain, titles[focus])
            if product == ba_trends.ALL_PRODUCTS
            else (
                product,
                product_rows,
                product_summary,
                None,  # a product keeps its own scale: the families' would cut it
                build_family_panel_titles(product_summary[product_summary["family"] == product])[product],
            )
        )
        with st.container(key="inf_card_focus"):
            with st.container(horizontal=True, vertical_alignment="center"):
                st.markdown(build_family_card_title_html(subject, title, color), unsafe_allow_html=True)
                if len(products) > 1:
                    st.selectbox(
                        tr("Producto"),
                        products,
                        key="inf_product",
                        format_func=tr,
                        label_visibility="collapsed",
                        width=240,
                        help=tr("Escribe para buscar un producto; sus cifras se calculan como las de una familia."),
                    )
                st.button("Ver todas", key="inf_unfocus", icon=":material/close:", on_click=focus_family, args=(None,))
            chart_column, reading_column = st.columns([2.5, 1], gap="medium")
            chart_column.altair_chart(
                inflation_view.draw_family_focus(
                    subject_rows, subject, mode, real=real, domain=subject_domain, height=420, tint=color
                ),
                width="stretch",
                theme=None,
            )
            if subject_summary is not None and last is not None:
                reading_column.markdown(
                    build_family_insights_html(
                        inflation_view.family_insights(subject_rows, subject_summary, subject, last, real),
                        subject,
                        color,
                    ),
                    unsafe_allow_html=True,
                )
        return
    families = list(titles)
    for start in range(0, len(families), FAMILY_CARD_COLUMNS):
        columns = st.columns(FAMILY_CARD_COLUMNS, gap="small")
        for offset, family in enumerate(families[start : start + FAMILY_CARD_COLUMNS]):
            with columns[offset], st.container(key=f"inf_card_{start + offset}"):
                st.markdown(build_family_card_title_html(family, titles[family]), unsafe_allow_html=True)
                st.altair_chart(
                    inflation_view.draw_family_card(rows, family, mode, real=real, domain=domain, height="container"),
                    width="stretch",
                    height="stretch",
                    theme=None,
                )
                st.button(
                    "Ampliar",
                    key=f"inf_zoom_{start + offset}",
                    icon=":material/open_in_full:",
                    on_click=focus_family,
                    args=(family,),
                )


def show_price_context_page(mode):
    """Precios e inflación (D-163, D-167): one question — which food families rose more
    than the food IPC of the INE — answered by one small chart per family, the same
    size and scale, each against the IPC. Nothing else on the page."""
    st.markdown(build_context_css(mode), unsafe_allow_html=True)
    version = get_database_version()
    rows, last, summary, ipc_total, ipc_year = read_family_inflation(version)
    if rows.empty:
        st.info(NO_DATA_TEXT)
        return

    month = format_cpi_month
    above = [home_mockup.short_family(f) for f in summary.loc[summary["verdict"] == "más que la inflación", "family"]]
    below = [home_mockup.short_family(f) for f in summary.loc[summary["verdict"] == "menos que la inflación", "family"]]
    join = i18n.join_names
    answer = (
        f'De enero 2022 a {month(last)}, la canasta de alimentos del INE subió '
        f'<b>{charts.format_signed_percent(ipc_total)}</b> ({charts.format_signed_percent(ipc_year)} en 12 meses).'
        + (f' Subieron más: <b>{html.escape(join(above))}</b>.' if above else '')
        + (f' Subieron menos: <b>{html.escape(join(below))}</b>.' if below else '')
    )
    # D-267: the answer leaves the page for the bar: the title says it on hover and three chips count it.
    show_page_bar(
        PAGE_SEASONALITY,
        "¿Qué alimentos subieron más que la inflación?",
        re.sub(r"<[^>]+>", "", answer),
        [
            (
                f'<em>IPC</em><b>{charts.format_signed_percent(ipc_total)}</b>',
                f"De enero 2022 a {month(last)}, el último mes que publicó el INE, la canasta de alimentos del INE subió {charts.format_signed_percent(ipc_total)} desde enero 2022 y "
                f"{charts.format_signed_percent(ipc_year)} en los últimos 12 meses.",
            ),
            (
                f'<b class="rise">{len(above)} más</b><b class="fall">{len(below)} menos</b>',
                (f"Subieron más que la inflación: {join(above)}. " if above else "")
                + (f"Subieron menos: {join(below)}." if below else ""),
            ),
        ],
        terms=INFLATION_TERMS,
    )
    real = st.session_state.get(CONTEXT_BASIS_KEY) == BASIS_REAL
    with st.container(key="ctx_main"):
        lead = (
            "Sin inflación: la línea punteada es la canasta del INE (100). Arriba de ella, la familia subió más."
            if real
            else "Precios de consumidor de ODEPA, mediana por familia de las series con precio en enero 2022 y en el "
            "último mes; la línea punteada es el IPC de alimentos. Misma escala en todos los gráficos."
        )
        # The switch takes the width it needs, so it is never cut on a narrow window.
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(
                f'<div class="ctx-head"><h3>Índice mensual por familia, enero 2022 = 100</h3></div>'
                f'<p class="ctx-reading">{lead}</p>',
                unsafe_allow_html=True,
                width="stretch",
            )
            st.segmented_control(
                "Precios",
                [BASIS_NOMINAL, BASIS_REAL],
                default=BASIS_NOMINAL,
                width="content",
                key=CONTEXT_BASIS_KEY,
                label_visibility="collapsed",
                help=BASIS_HELP,
            )
        # D-458: what used to be the note under the cards, the months and what rising with the CPI means, is now
        # in the green panel above the tabs of «Análisis».
        show_family_cards(rows, build_family_panel_titles(summary, ipc_total), mode, real, summary, last)


# endregion


# region Insights
def overview_week(weeks):
    """The chosen week, kept as an ISO date (D-303): a value the widget left in another language is dropped."""
    chosen = st.session_state.get(OVERVIEW_WEEK_KEY)
    known = {f"{pd.Timestamp(w):%Y-%m-%d}" for w in weeks}
    return pd.Timestamp(chosen) if chosen in known else pd.Timestamp(weeks[-1])


@st.cache_data(show_spinner=False)
def read_cached_database_counts(database_version):
    return queries.run_sql(
        "SELECT (SELECT count(*) FROM weekly_price) AS prices, (SELECT count(*) FROM dim_date) AS weeks, "
        "(SELECT count(*) FROM dim_region) AS regions, (SELECT count(*) FROM dim_channel) AS channels"
    ).iloc[0]


def build_insight_table_html(head, rows, extra_class="", markup_columns=()):
    """A table of the Insights tab: its header and its rows of text, the first column in bold. The columns in
    markup_columns already hold their HTML (a link, D-385)."""
    header = "".join(f"<th>{html.escape(tr(cell))}</th>" for cell in head)
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{cell if index in markup_columns else html.escape(tr(cell))}</td>" for index, cell in enumerate(row)
        )
        + "</tr>"
        for row in rows
    )
    classes = f"ov-it {extra_class}".strip()
    return f'<div class="{classes}" tabindex="0"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>'


def build_insight_table_css(palette):
    """The look of the text tables of Insights, shared with «Análisis de negocio y sistemas» (D-377)."""
    return static_files.fill(
        "analysis_insights.css",
        {
            'var(--go-accent)': palette['accent'],
            'var(--go-charts-readable-on-palette-accent)': charts.readable_on(palette['accent']),
            'var(--go-text)': palette['text'],
            'var(--go-card-border)': palette['card_border'],
            'var(--go-strong-text)': palette['strong_text'],
        },
    )


def build_insight_card_html(kind, title, who, icon, lines):
    paragraphs = "".join(f"<p>{html.escape(line)}</p>" for line in lines)
    return (
        f'<div class="ov-insight ov-insight-{kind}"><span class="ov-insight-who">{overview.point_icon(icon)}'
        f'<span>{html.escape(tr("Para"))}: {html.escape(tr(who))}</span></span>'
        f'<h4>{html.escape(tr(title))}</h4>{paragraphs}</div>'
    )


def show_overview_insights(mode, version):
    """D-302: the questions the dashboard answers with today's answer and two insights computed from the current
    load: one for whoever buys, one for whoever designs the data. D-377: the definition of each KPI moved to
    «Análisis de negocio y sistemas»; a link leads there."""
    palette = charts.get_palette(mode)
    variations, alerts_rows = read_cached_all_variations(version), read_price_alerts()
    prices = read_cached_national_prices(version)
    week = overview_week(sorted(variations["week_start"].unique()))
    upto, upto_prices = variations[variations["week_start"] <= week], prices[prices["week_start"] <= week]
    moves = overview.family_moves(upto_prices, upto, week)
    market = overview.market_weeks(upto_prices, upto, alerts_rows[alerts_rows["week_start"] <= week])
    rows, last, summary, ipc_total, ipc_year = read_family_inflation(version)
    above = summary[summary["verdict"] == "más que la inflación"]["family"].map(home_mockup.short_family)
    runs = read_indicator("quality_runs").sort_values("run_id")
    flags = read_indicator("quality_flag_counts")
    results = queries.run_sql("SELECT status, count(*) AS n FROM dbt_result GROUP BY status").set_index("status")["n"]
    tests = int(results.get("pass", 0)), int(results.sum() - results.get("success", 0))
    indicators = quality_live.build_indicators(quality_live.read_measures())
    green = sum(1 for row in indicators if row[4] == "ok")
    now = market.iloc[-1]
    margin_now = read_indicator("k1_margin")
    margin_now = margin_now[margin_now["week_start"] == f"{week:%Y-%m-%d}"]
    gaps = margin_now.groupby("product_group")["margin"].median().mul(100) if not margin_now.empty else None
    market_count = sum(len(data["wholesale"]) for data in overview.read_points().values())
    first_year = overview.ipc_twelve_months(rows).iloc[0]
    first_month = ba_trends.month_label((first_year["month_start"].year, first_year["month_start"].month))
    last_month = ba_trends.month_label(last)
    santiago = len(overview.read_points().get("Región Metropolitana de Santiago", {}).get("wholesale", []))
    points = f"{inflation_view.SAME_PACE_POINTS:.0f}"
    short = home_mockup.short_family
    fell = moves[moves["state"] == "Bajó"]["product_group"].map(short)
    rose = moves[moves["state"] == "Subió"]["product_group"].map(short)
    questions = [
        (
            "¿Qué está subiendo y qué está bajando esta semana?",
            "Persona común",
            PAGE_HOME,
            f"Subieron: {overview.join(rose) or 'ninguna familia'}. Bajaron: {overview.join(fell) or 'ninguna familia'}. "
            "Mediana de cada familia frente a la semana anterior.",
        ),
        (
            "¿Qué alimentos se encarecieron más desde 2022?",
            "Persona común",
            "Precios e inflación",
            (
                f"{overview.join(above)} subieron más de {points} puntos sobre el IPC de alimentos desde enero 2022 "
                f"({overview.signed(ipc_total)})."
                if len(above)
                else "Ninguna familia subió más que los alimentos en general."
            ),
        ),
        (
            "¿La inflación de los alimentos está bajando?",
            "Persona común",
            "Precios e inflación",
            # D-480: the answer is computed, never a fixed «Sí», and both months are named
            (
                f"Sí: en 12 meses a {last_month} bajó {overview.signed(ipc_year)}."
                if ipc_year < 0
                else f"Sí, sube más lento: de {overview.signed(first_year['change'])} en 12 meses a {first_month} a "
                f"{overview.signed(ipc_year)} a {last_month}."
                if ipc_year < first_year["change"]
                else f"No, sube más rápido: de {overview.signed(first_year['change'])} en 12 meses a {first_month} a "
                f"{overview.signed(ipc_year)} a {last_month}."
            ),
        ),
        (
            "¿Dónde se compra por mayor?",
            "Comerciante mayorista",
            PAGE_INSIGHTS,
            f"{market_count} mercados mayoristas en {len(overview.read_points())} regiones, {santiago} de ellos en Santiago.",
        ),
        (
            "¿Cuánto se agrega entre el mercado mayorista y el consumidor?",
            "Comerciante mayorista",
            "Consultas SQL · Brecha mayorista",
            (
                f"Mediana de la brecha (K1), semana {weeks.week_range(week)}: "
                f"{overview.join(f'{short(f)} {overview.signed(v)}' for f, v in gaps.items())}."
                if gaps is not None
                else "Sin datos esta semana."
            ),
        ),
        (
            "¿Puedo confiar en estas cifras?",
            "Quien diseña los datos",
            "Controles de datos",
            f"{green} de {len(indicators)} indicadores de calidad de los datos en su umbral y {tests[0]} de {tests[1]} pruebas de datos.",
        ),
    ]
    st.markdown(
        static_files.style(
            "overview_insights.css",
            {
                'var(--go-build-insight-table-css-palette)': build_insight_table_css(palette),
                'var(--go-card_border)': palette['card_border'],
                'var(--go-card)': palette['card'],
                'var(--go-rise)': palette['rise'],
                'var(--go-accent)': palette['accent'],
                'var(--go-strong_text)': palette['strong_text'],
                'var(--go-text)': palette['text'],
            },
        ),
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.35, 1], gap="medium")
    with left:
        st.markdown(
            build_insight_table_html(["Pregunta", "Para quién", "Dónde verlo", "La respuesta de hoy"], questions),
            unsafe_allow_html=True,
        )
        analysis = WINDOW_PAGES.get(WINDOW_OF_VIEW[PAGE_BA])  # absent when a test draws the page alone
        if analysis:  # D-377, D-456: the definition of each KPI lives in the tab «Método»; its values stay here
            st.page_link(
                analysis,
                label=tr("Ver las definiciones de los KPI"),
                icon=":material/functions:",
                query_params=keep_context()
                | {VIEW_PARAMETER: PAGE_BA, BA_TAB_PARAMETER: BA_TAB_OF_VIEW[PAGE_ANALYSIS]},
            )
    with right:
        drops = overview.best_drops(upto, week)
        database = read_cached_database_counts(version)
        readers = {
            ":material/person: Persona común": "buyer",
            ":material/storefront: Mayorista": "wholesale",
            ":material/database: Datos": "architect",
        }
        reader = (
            st.segmented_control(
                tr("Para quién"),
                list(readers),
                default=list(readers)[0],
                key="ov_insight_reader",
                label_visibility="collapsed",
                format_func=tr,
            )
            or list(readers)[0]
        )
        kind = readers[reader]
        if kind == "buyer":
            card = build_insight_card_html(
                "buyer",
                "Qué conviene mirar esta semana",
                "Una persona común",
                "person",
                overview.consumer_insights(moves, drops, summary, ipc_total, ipc_year),
            )
        elif kind == "wholesale":
            card = build_insight_card_html(
                "wholesale",
                "Qué pasa en el mercado mayorista",
                "Un comerciante que compra por mayor",
                "mercado",
                overview.wholesale_insights(upto, week, read_indicator("k1_margin")),
            )
        else:
            card = build_insight_card_html(
                "architect",
                "Qué dicen los datos de esta carga",
                "Quien diseña o revisa los datos",
                "datos",
                overview.architect_insights(
                    runs.iloc[-1], tests, green, len(indicators), database, flags, now["comparable"], now["prices"]
                ),
            )
        st.markdown(f'<div class="ov-insights">{card}</div>', unsafe_allow_html=True)


def show_insights_page(mode):
    """Insights: the questions people ask, each with today's answer, and one reading per kind of reader (D-308)."""
    show_page_bar(
        PAGE_INSIGHTS,
        "Insights",
        "Preguntas reales de quien compra, de quien vende por mayor y de quien diseña "
        "los datos, con la respuesta de hoy.",
    )
    show_overview_insights(mode, get_database_version())


# endregion


# region Analysis texts
def show_analysis_text(paragraphs):
    st.markdown(
        '<div class="an-text">' + "".join(f"<p>{html.escape(text)}</p>" for text in paragraphs) + "</div>",
        unsafe_allow_html=True,
    )


def show_analysis_lead(text):
    st.markdown(f'<p class="an-lead">{html.escape(text)}</p>', unsafe_allow_html=True)


def show_analysis_link(view, label, parameters=None):
    """A link to the page that holds the rest; absent when a test draws the page alone, and in the Usuario view,
    whose menu does not lead there (D-502)."""
    window = WINDOW_PAGES.get(WINDOW_OF_VIEW.get(view))
    if window and can_open(view):
        st.page_link(
            window,
            label=label,
            icon=SIDEBAR_ICONS.get(view, PAGE_ICONS.get(view)),
            query_params=keep_context() | {VIEW_PARAMETER: view} | (parameters or {}),
        )


def show_analysis_block(block, mode):
    """One block of the case (D-377), read from the documents the moment it is drawn."""
    read = business_analysis
    if block == "El problema":
        show_analysis_text(read.read_problem())
    elif block == "Interesados":
        stakeholders = read.read_stakeholders()
        show_analysis_lead(tr("Interesados: {}.").format(i18n.join_names([row["name"] for row in stakeholders])))
        st.markdown(
            build_insight_table_html(
                ["Interesado", "Pregunta", "Decisión"],
                [(row["name"], row["question"], row["decision"]) for row in stakeholders],
            ),
            unsafe_allow_html=True,
        )
        show_analysis_link(PAGE_STAKEHOLDERS, tr("Ver Interesados"))
    elif block == "Qué escuchamos":
        show_analysis_text([read.read_heard()])
    elif block == "Requisitos":
        st.markdown(
            build_insight_table_html(["ID", "Requisito", "Criterio medible"], read.read_requirements(), "an-ids"),
            unsafe_allow_html=True,
        )
    elif block == "Alcance":
        scope = read.read_scope()
        included, excluded = st.columns(2, gap="small")
        included.markdown(
            build_insight_table_html(["Incluye", "Por qué"], [row[:2] for row in scope]), unsafe_allow_html=True
        )
        excluded.markdown(
            build_insight_table_html(["Excluye", "Por qué"], [row[2:] for row in scope]), unsafe_allow_html=True
        )
    elif block == "Proceso":
        show_analysis_lead(tr("El ciclo de cada semana: la carga, sus pruebas, la publicación y los dos informes."))
        st.iframe(doc_diagrams.DOC_DIAGRAMS["ciclo_semanal"](mode), height="content")
    elif block == "KPIs":
        show_analysis_lead(
            tr(
                "Los valores de cada KPI se ven en el dashboard Semanal, en Insights y en Precios e inflación. "
                "Un KPI con indicador técnico (K1 a K8) abre su cálculo paso a paso; los demás se calculan solo para "
                "el panel."
            )
        )
        # D-385: the technical indicator (K code and its name) next to each KPI, so the two vocabularies meet.
        rows = [(name, build_kpi_code_html(name), how, why) for name, how, why in overview.KPIS]
        st.markdown(
            build_insight_table_html(
                ["KPI", "Indicador técnico", "Cómo se calcula", "Por qué"], rows, markup_columns=(1,)
            ),
            unsafe_allow_html=True,
        )
    elif block == "Decisiones de sistema":
        for item in read.system_decisions():
            text, link = st.columns([4.5, 1], vertical_alignment="center")
            line = " ".join(
                (f"<b>{html.escape(tr(label))}</b> · " if label else "") + html.escape(part)
                for label, part in zip(item["labels"], item["parts"])
            )
            text.markdown(
                f'<p class="an-decision"><b>{html.escape(tr(item["title"]))}</b> · {line}</p>', unsafe_allow_html=True
            )
            with link:
                view = SYSTEM_DECISION_PAGES[item["page"]]
                # the failure register opens on its log tab (D-346), the rest of the decisions on their page
                show_analysis_link(view, tr("Ver"), {GIT_TAB_PARAMETER: GIT_TAB_LOG} if view == PAGE_GIT else None)
    elif block == "Evaluación":
        show_analysis_text(
            [tr("Cómo sabemos que funciona: los KPI, la calidad de los datos y el feedback."), read.read_evaluation()]
        )
        st.markdown(
            build_insight_table_html(["Criterio", "Cómo se verifica"], read.read_acceptance()), unsafe_allow_html=True
        )
        reports = quality_metrics.read_reports()
        if reports:
            within, _, measured = quality_metrics.report_counts(reports[-1])
            st.caption(
                tr("Último informe: {}, {} de {} indicadores dentro de lo aceptable.").format(
                    quality_metrics.report_name(reports[-1], i18n.is_english()), within, measured
                )
            )
    else:  # «Del feedback al cambio»
        st.markdown(
            build_insight_table_html(["Revisión", "Qué escuchamos", "Qué cambió", "Decisión"], read.read_feedback()),
            unsafe_allow_html=True,
        )


def build_analysis_css(palette):
    """D-377: the list of blocks on the left, the block on the right; texts and tables sized to fit one screen."""
    ink, text, accent, line = palette["strong_text"], palette["text"], palette["accent"], palette["card_border"]
    return static_files.style(
        "analysis.css",
        {
            'var(--go-text)': text,
            'var(--go-accent)': accent,
            'var(--go-ink)': ink,
            'var(--go-line)': line,
        },
    )


# endregion
