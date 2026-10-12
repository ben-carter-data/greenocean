"""Streamlit dashboard for the price monitor.

Run it with:  streamlit run bi/dashboard.py

It reads etl/datos.db through the named queries of bi/queries.sql, and the
state of the weekly robot through the GitHub API (bi/control.py).
Texts shown to the user are in Spanish; code and comments are in English.
The two color modes live in .streamlit/config.toml, the charts in bi/charts.py.
"""
import hmac
import html
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

# region Imports of the project
# Streamlit runs this file as a script, so the project folder is added to the
# import path to reach the other modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import alerts, architecture, charts, control, queries  # noqa: E402
from etl import etl  # noqa: E402
# endregion

# region Constants
PROFILE_ANALYST = "Analista de pricing / compras"
PROFILE_DATA_TEAM = "Equipo de datos"

PAGE_OVERVIEW = "Panel"
PAGE_PROJECT = "El proyecto"
PAGE_MARGINS = "Márgenes"
PAGE_CHANNELS_AND_REGIONS = "Canales y regiones"
PAGE_SEASONALITY = "Estacionalidad"
PAGE_ALERTS = "Alertas"
PAGE_ARCHITECTURE = "Cómo funciona"
PAGE_CONTROL = "Centro de control"
PAGE_DATA_QUALITY = "Calidad de datos"
PAGES_BY_PROFILE = {
    PROFILE_ANALYST: [PAGE_OVERVIEW, PAGE_PROJECT, PAGE_MARGINS, PAGE_CHANNELS_AND_REGIONS,
                      PAGE_SEASONALITY, PAGE_ALERTS, PAGE_ARCHITECTURE, PAGE_CONTROL],
    PROFILE_DATA_TEAM: [PAGE_OVERVIEW, PAGE_PROJECT, PAGE_ARCHITECTURE, PAGE_CONTROL,
                        PAGE_DATA_QUALITY],
}
PAGE_ICONS = {
    PAGE_OVERVIEW: ":material/space_dashboard:", PAGE_PROJECT: ":material/lightbulb:",
    PAGE_MARGINS: ":material/percent:",
    PAGE_CHANNELS_AND_REGIONS: ":material/storefront:",
    PAGE_SEASONALITY: ":material/calendar_month:",
    PAGE_ALERTS: ":material/notifications_active:",
    PAGE_ARCHITECTURE: ":material/account_tree:", PAGE_CONTROL: ":material/smart_toy:", PAGE_DATA_QUALITY: ":material/verified:",
}
PAGE_PATHS = {
    PAGE_OVERVIEW: "panel", PAGE_PROJECT: "el-proyecto", PAGE_MARGINS: "margenes",
    PAGE_CHANNELS_AND_REGIONS: "canales-y-regiones", PAGE_SEASONALITY: "estacionalidad",
    PAGE_ALERTS: "alertas", PAGE_ARCHITECTURE: "como-funciona",
    PAGE_CONTROL: "centro-de-control",
    PAGE_DATA_QUALITY: "calidad-de-datos",
}

# Choices shown first when they exist, so every page opens with a known case.
DEFAULT_GROUP = "Hortalizas"
DEFAULT_PRODUCT = "Tomate"
DEFAULT_REGION = "Región Metropolitana de Santiago"
DEFAULT_CHANNEL = "Feria libre"
SUPERMARKET = "Supermercado"
DEFAULT_MARGIN_CHANNELS = [DEFAULT_CHANNEL, SUPERMARKET]
WHOLESALE_LABEL = "Mayorista"
UNSPECIFIED = "Sin especificar"
SOURCE_NAMES = {etl.SOURCE_WHOLESALE: "Mayorista", etl.SOURCE_CONSUMER: "Consumidor"}
FLAG_NAMES = {"SIN_MARCA": "Usados en los indicadores",
              etl.FLAG_UNIT_NOT_CONVERTIBLE: "Unidad no convertible",
              etl.FLAG_OUTLIER: "Atípicos"}
OVERVIEW_ALERT_COUNT = 6
ALERTS_PAGE_BAR_COUNT = 15
RUN_HISTORY_COUNT = 8

MANIFEST_FILE = Path(__file__).resolve().parent.parent / "agent" / "downloads" / "manifest.json"
ISSUES_PAGE_URL = f"https://github.com/{control.REPOSITORY}/issues"
CHILE_TIME_ZONE = "America/Santiago"
# Seconds between two questions to GitHub while the robot works, and the
# longest wait: a normal run takes about one minute.
PROGRESS_POLL_SECONDS = 4
PROGRESS_MAXIMUM_SECONDS = 600
# Names of the dashboard secrets that enable the "run now" button.
SECRET_GITHUB_TOKEN = "GITHUB_TOKEN"
SECRET_CONTROL_CODE = "CONTROL_CODE"

# Plain explanations shown when the mouse passes over the ⓘ of each card.
KEY_FIGURES_HINT = ("▲ en rojo: el precio **subió** frente a la semana anterior. "
                    "▼ en azul: **bajó**. En el margen, «pts» son puntos porcentuales: "
                    "de 58 % a 44 % son −14 pts.")
PRICE_TREND_HINT = ("Cada línea es el precio promedio de un canal, semana a semana, en "
                    "pesos por kilo (o por unidad). La línea gris es el mercado mayorista: "
                    "la distancia entre la gris y las demás es lo que agrega el comercio.")
MEDIAN_MARGIN_HINT = ("Cuánto más paga el consumidor que el mayorista, en %. **145 %** "
                      "significa que el consumidor paga 2,45 veces el precio mayorista. "
                      "Es la mediana de las semanas mostradas.")
MARGIN_TREND_HINT = ("El margen de cada canal, semana a semana. Si la línea sube, la "
                     "distancia entre el precio al consumidor y el mayorista creció.")
REGIONAL_INDEX_HINT = ("**1,00** es el promedio nacional de la semana. **1,46** = 46 % más "
                       "caro que el promedio; **0,66** = 34 % más barato. Promedio de todas "
                       "las semanas. La línea punteada marca el 1,00.")
CHANNEL_GAP_HINT = ("Compara cada canal con el canal de referencia. **+62,7 %** = ese canal "
                    "es 62,7 % más caro; un valor **negativo** = más barato. Solo cuenta "
                    "semanas y regiones donde ambos tienen precio.")
ALERTS_HINT = ("Productos cuyo precio cambió esta semana mucho más de lo que suele cambiar. "
               "▲ en rojo: subió; ▼ en azul: bajó. «Variación habitual» es su cambio "
               "semanal promedio de las 12 semanas anteriores. Son señales para revisar, "
               "no conclusiones.")
SEASONAL_INDEX_HINT = ("**1,00** es el precio promedio del año. **1,20** = esa semana el "
                       "precio estuvo 20 % sobre su promedio; **0,80** = 20 % bajo. Con un "
                       "solo año cargado es variación dentro del año, aún no estacionalidad.")
NATIONAL_PRICE_HINT = ("Promedio simple de las regiones con dato, en pesos por kilo (o por "
                       "unidad), semana a semana.")
ARCHITECTURE_HINT = ("Los datos viajan de izquierda a derecha. **Bronce**: el archivo tal "
                     "como llega. **Limpieza y reglas**: se corrigen formatos y se aplican "
                     "las reglas de negocio. **Calidad**: si algo no cuadra, no se guarda "
                     "nada. **Oro**: la base lista para analizar. Arriba, quién da las "
                     "órdenes; abajo, cómo sabemos qué pasó. El punto de color de cada paso "
                     "es su estado real.")
# The project page. Texts come from docs/DISENO.md (sections 2 to 4) and DECISIONES.md.
PROBLEM_TEXT = (
    "Un analista de pricing, compras o abastecimiento que quiere seguir los precios de los "
    "alimentos en Chile tiene que bajar archivos de dos fuentes de ODEPA cada semana, "
    "convertir unidades distintas (cajas, bins, mallas, kilos) y cruzarlos a mano. Las "
    "fuentes existen, pero están separadas y no se pueden comparar sin trabajo previo. "
    "Este proyecto hace ese trabajo solo, cada semana, y deja el resultado en un panel.")
AUDIENCE_TEXT = (
    "**Analista de pricing o compras**: márgenes, canales, regiones y alertas.  \n"
    "**Equipo de datos**: si la carga funcionó y qué quedó fuera.  \n"
    "Más adelante: un resumen para gerencia y una vista simple para consumidores.")
WHY_TEXT = (
    "Los datos son abiertos y oficiales, el cruce entre precio mayorista y precio al "
    "consumidor se pudo verificar con datos reales, y las preguntas son las que se hace "
    "a diario un área de pricing o abastecimiento. Se descartaron el scraping de "
    "supermercados (condiciones de uso inciertas) y otros temas con menos valor al cruzar.")
DATA_TEXT = (
    "Dos conjuntos de datos abiertos de ODEPA (Ministerio de Agricultura): **precios "
    "mayoristas** de frutas y hortalizas, diarios, y **precios al consumidor**, semanales, "
    "por región y tipo de comercio. Licencia Creative Commons Atribución.")
LIMITS_TEXT = (
    "Precios nominales, sin ajuste por inflación. Por ahora, un solo año cargado (2026). "
    "La papa no tiene margen porque sus calidades no coinciden entre las dos fuentes. "
    "Las cifras del panel son cálculos sobre datos oficiales; los hallazgos se publican "
    "solo después de verificarlos.")
# (question, page where it is answered, state: available, partial or pending, note)
BUSINESS_QUESTIONS = [
    ("¿Cuál es el margen entre el precio mayorista y el precio al consumidor, y cómo "
     "evoluciona?", PAGE_MARGINS, "available", "Frutas y verduras"),
    ("¿Cuánto difiere el precio entre canales: supermercado, feria, carnicería…?",
     PAGE_CHANNELS_AND_REGIONS, "available", "Todos los grupos"),
    ("¿En qué regiones son más altos los precios?", PAGE_CHANNELS_AND_REGIONS,
     "available", "Todos los grupos"),
    ("¿En qué semanas sube y baja cada producto, y cuánto?", PAGE_SEASONALITY,
     "partial", "Un solo año cargado"),
    ("¿Con cuántas semanas de diferencia sigue el precio al consumidor al mayorista?",
     "—", "pending", "Necesita el histórico"),
    ("¿Qué productos se movieron esta semana fuera de su rango normal?", PAGE_ALERTS,
     "available", "Todos los grupos"),
]
QUESTION_STATES = {"available": ("Disponible", "ok"), "partial": ("Parcial", "running"),
                   "pending": ("Pendiente", "neutral")}

NO_DATA_TEXT = "No hay datos para esta selección."
NOMINAL_PRICES_TEXT = "Precios nominales, sin ajuste por inflación."
ATTRIBUTION_TEXT = (
    "Datos: Oficina de Estudios y Políticas Agrarias (ODEPA), Ministerio de "
    "Agricultura de Chile, licencia Creative Commons Atribución. "
    "Este proyecto no es un producto oficial de ODEPA.")
# endregion


# region Style
def get_mode():
    """Active color mode chosen by the reader; dark until the browser reports it."""
    theme_type = st.context.theme.type
    return theme_type if theme_type in charts.PALETTES else charts.MODE_DARK


def build_style_css(mode):
    """Cards, key figures, chips and tables, in the colors of the active mode."""
    palette = charts.get_palette(mode)
    return f"""
    [class*="st-key-card_"] {{
        background: {palette["card"]}; border: 1px solid {palette["card_border"]};
        border-radius: 18px; padding: 18px 20px 14px 20px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
    }}
    .card-title {{ font-size: 1.05rem; font-weight: 600; color: {palette["strong_text"]}; }}
    .page-subtitle {{ color: {palette["text"]}; margin-top: -0.6rem; }}
    .kpi-label {{ color: {palette["text"]}; font-size: 0.9rem; }}
    .kpi-value {{ font-size: 2rem; font-weight: 700; color: {palette["strong_text"]};
                 line-height: 1.2; }}
    .kpi-note {{ color: {palette["text"]}; font-size: 0.8rem; }}
    .chip {{ display: inline-block; padding: 2px 10px; border-radius: 999px;
            font-size: 0.8rem; font-weight: 600; margin-left: 6px; }}
    .chip-ok {{ background: rgba(12, 163, 12, 0.16); color: #22b35a; }}
    .chip-failed {{ background: rgba(208, 59, 59, 0.16); color: #e66767; }}
    .chip-running {{ background: rgba(57, 135, 229, 0.16); color: #5b9cf0; }}
    .chip-neutral {{ background: rgba(128, 128, 128, 0.16); color: {palette["text"]}; }}
    .chip-rise {{ background: rgba(227, 73, 72, 0.16); color: {palette["rise"]}; }}
    .chip-fall {{ background: rgba(57, 135, 229, 0.16); color: {palette["fall"]}; }}
    .hint {{ position: relative; display: inline-block; margin-left: 8px; cursor: help;
            color: {palette["text"]}; font-weight: 400; outline: none;
            padding: 0 4px; font-size: 1.1em; }}
    /* :focus makes the explanation open with a tap on phones, where there is no mouse. */
    .hint:hover::after, .hint:focus::after {{
        content: attr(data-hint); position: absolute; left: 0; top: 1.7em; z-index: 1000;
        width: min(340px, 75vw); padding: 10px 12px; border-radius: 10px; white-space: normal;
        background: {palette["card"]}; border: 1px solid {palette["card_border"]};
        color: {palette["strong_text"]}; font-size: 0.85rem; font-weight: 400;
        line-height: 1.45; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }}
    .hint-chip {{ position: relative; cursor: help; outline: none; }}
    .hint-chip:focus::after {{
        content: attr(data-hint); position: absolute; right: 0; top: 1.9em; z-index: 1000;
        width: min(260px, 70vw); padding: 8px 10px; border-radius: 10px; white-space: normal;
        background: {palette["card"]}; border: 1px solid {palette["card_border"]};
        color: {palette["strong_text"]}; font-size: 0.8rem; font-weight: 400;
    }}
    /* On narrow screens the explanation opens as a panel at the bottom of the
       screen, so it never runs off the edge. */
    @media (max-width: 640px) {{
        .hint:hover::after, .hint:focus::after, .hint-chip:focus::after {{
            position: fixed; left: 16px; right: 16px; bottom: 16px; top: auto;
            width: auto; font-size: 0.95rem;
        }}
    }}
    table.card-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    table.card-table th {{ text-align: left; color: {palette["text"]}; font-weight: 500;
                          padding: 6px 4px; border-bottom: 1px solid {palette["card_border"]}; }}
    table.card-table td {{ padding: 8px 4px; border-bottom: 1px solid {palette["card_border"]};
                          color: {palette["strong_text"]}; }}
    """


def apply_style(mode):
    """Add the dashboard CSS to the page."""
    st.markdown(f"<style>{build_style_css(mode)}</style>", unsafe_allow_html=True)


def open_card(key, title=None, caption=None, hint=None):
    """A rounded card; use it with 'with'. The key must be unique on the page.

    hint, when given, is a short explanation in plain words that appears when
    the mouse passes over the ⓘ next to the title.
    """
    card = st.container(key=f"card_{key}")
    hint_icon = build_hint_icon(hint) if hint else ""
    if title or hint:
        card.markdown(f'<div class="card-title">{html.escape(title or "")}{hint_icon}</div>',
                      unsafe_allow_html=True)
    if caption:
        card.caption(caption)
    return card


def build_hint_icon(hint):
    """An ⓘ that shows a short explanation when the mouse passes over it, or when
    it is tapped on a phone (tabindex makes it focusable)."""
    plain_hint = html.escape(hint.replace("**", ""), quote=True)
    return (f'<span class="hint" tabindex="0" role="button" aria-label="{plain_hint}" '
            f'data-hint="{plain_hint}">ⓘ</span>')


def build_chip(text, kind, hover_text=None):
    """A small colored label: kind is ok, failed, running, neutral, rise or fall.

    hover_text, when given, appears when the mouse passes over the label.
    """
    if not hover_text:
        return f'<span class="chip chip-{kind}">{html.escape(text)}</span>'
    escaped_hover_text = html.escape(hover_text, quote=True)
    return (f'<span class="chip chip-{kind} hint-chip" tabindex="0" '
            f'title="{escaped_hover_text}" data-hint="{escaped_hover_text}">'
            f'{html.escape(text)}</span>')


def build_html_table(headers, rows):
    """A simple table; cells are already-escaped HTML (they may contain chips)."""
    header_cells = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    body_rows = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
                        for row in rows)
    return f'<table class="card-table"><tr>{header_cells}</tr>{body_rows}</table>'


def show_chart(chart):
    """Draw an Altair chart with its own colors (not Streamlit's chart theme)."""
    st.altair_chart(chart, use_container_width=True, theme=None)
# endregion


# region Data access
def get_database_version():
    """Changes when the robot saves a new database, so cached data is read again."""
    return queries.DATABASE_FILE.stat().st_mtime


def add_display_columns(rows):
    """Add the date and the product key label used by filters and charts."""
    if "week_start" in rows.columns:
        rows["week_start"] = pd.to_datetime(rows["week_start"])
    if "variety" in rows.columns:
        # The unit is part of the label: one product can be sold by kilo and by unit.
        rows["key_label"] = (rows["variety"] + " · " + rows["quality"]
                             + " · $/" + rows["normalized_unit"])
    return rows


@st.cache_data
def read_cached_indicator(query_name, database_version):
    """Rows of one indicator, kept in memory until the database changes."""
    return add_display_columns(queries.run_query(query_name))


def read_indicator(query_name):
    """Rows of one indicator for the current database."""
    return read_cached_indicator(query_name, get_database_version())


@st.cache_data
def read_cached_price_alerts(database_version):
    """K6 alerts of every week, computed once per database."""
    prices = queries.run_query("k6_national_weekly_price")
    return add_display_columns(alerts.find_price_alerts(prices))


def read_price_alerts():
    """K6 alerts for the current database."""
    return read_cached_price_alerts(get_database_version())


def read_match_coverage():
    """K7 as (keys with margin, consumer keys)."""
    connection = queries.open_database()
    coverage = etl.measure_match_coverage(connection)
    connection.close()
    return coverage


def read_latest_run():
    """Latest ETL run recorded in the database (one row)."""
    return read_indicator("quality_runs").iloc[0]


def describe_product(row):
    """'Tomate Larga vida · Primera', leaving out parts ODEPA does not specify."""
    description = row["product"]
    if row["variety"] != UNSPECIFIED:
        description += f" {row['variety']}"
    if row["quality"] != UNSPECIFIED:
        description += f" · {row['quality']}"
    return description
# endregion


# region Time
def to_chile_time(moment):
    """A UTC datetime in Chilean time; a fixed UTC-3 if the time zone is missing."""
    try:
        return moment.astimezone(ZoneInfo(CHILE_TIME_ZONE))
    except Exception:  # time zone database not installed
        return moment.astimezone(timezone(timedelta(hours=-3)))


def format_chile_time(moment):
    """'12-10-2026 05:52' in Chilean time."""
    return f"{to_chile_time(moment):%d-%m-%Y %H:%M}"


def parse_run_start(started_at):
    """The ETL stores its start in UTC as '2026-10-12T08:52:08'."""
    return datetime.fromisoformat(started_at).replace(tzinfo=timezone.utc)


def format_duration(duration):
    """timedelta -> '57 s' or '2 min 5 s'."""
    seconds = int(duration.total_seconds())
    return f"{seconds} s" if seconds < 60 else f"{seconds // 60} min {seconds % 60} s"
# endregion


# region Filters
def choose_value(label, values, preferred_value=None, key=None):
    """Show a select box and return the chosen value."""
    options = sorted(values)
    index = options.index(preferred_value) if preferred_value in options else 0
    return st.selectbox(label, options, index=index, key=key)


def choose_product_rows(rows):
    """Narrow the rows to the group, product and variety/quality the user chooses.

    The three choices sit in one row, above the charts they filter.
    """
    group_column, product_column, key_column = st.columns(3)
    with group_column:
        group = choose_value("Grupo", rows["product_group"].unique(), DEFAULT_GROUP)
    rows = rows[rows["product_group"] == group]
    with product_column:
        product = choose_value("Producto", rows["product"].unique(), DEFAULT_PRODUCT)
    rows = rows[rows["product"] == product]
    with key_column:
        # The key with most data goes first, so the page opens with a full chart.
        key_labels = rows["key_label"].value_counts().index.to_list()
        key_label = st.selectbox("Variedad · calidad · unidad", key_labels)
    return rows[rows["key_label"] == key_label]
# endregion


# region Page header
def show_page_header(title, subtitle):
    """Page title, a one-line explanation and the freshness of the data."""
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    run_text = "Carga correcta" if run_kind == "ok" else "Última carga con falla"
    freshness = format_chile_time(parse_run_start(latest_run["started_at"]))
    title_column, status_column = st.columns([3, 2], vertical_alignment="bottom")
    with title_column:
        st.title(title)
    with status_column:
        st.markdown(f'<div style="text-align:right">Datos actualizados el {freshness} '
                    f'{build_chip(run_text, run_kind)}</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="page-subtitle">{html.escape(subtitle)}</p>',
                unsafe_allow_html=True)
# endregion


# region Key figure cards
def calculate_weekly_change(series):
    """(latest value, change against the week before in percent) of a weekly series."""
    series = series.sort_index()
    if len(series) < 2:
        return series.iloc[-1], None
    return series.iloc[-1], (series.iloc[-1] / series.iloc[-2] - 1) * 100


def build_change_chip(change, unit="%"):
    """▲ +5,8 % in red when the price rises, ▼ in blue when it falls."""
    if change is None or pd.isna(change):
        return build_chip("sin semana previa", "neutral")
    arrow, kind = ("▲", "rise") if change > 0 else ("▼", "fall")
    text = f"{arrow} {change:+.1f} {unit}".replace(".", ",")
    verb = "Subió" if change > 0 else "Bajó"
    unit_words = "puntos porcentuales" if unit == "pts" else "%"
    hover_text = (f"{verb} {abs(change):.1f} {unit_words} frente a la semana anterior. "
                  "Rojo = sube, azul = baja.").replace(".", ",", 1)
    return build_chip(text, kind, hover_text)


def show_key_figure(key, label, series, value_text, change_chip, note, mode, color):
    """One card: label, big value, weekly change and a small trend line."""
    with open_card(key):
        st.markdown(f'<div class="kpi-label">{html.escape(label)}</div>'
                    f'<div class="kpi-value">{value_text}{change_chip}</div>'
                    f'<div class="kpi-note">{html.escape(note)}</div>',
                    unsafe_allow_html=True)
        trend_rows = pd.DataFrame({"week_start": series.index, "value": series.to_numpy()})
        show_chart(charts.draw_sparkline(trend_rows, color, mode))


def show_price_figure(key, label, series, unit, mode, color):
    """Key figure card for a weekly price series."""
    if series.empty:
        with open_card(key):
            st.markdown(f'<div class="kpi-label">{html.escape(label)}</div>'
                        '<div class="kpi-value">sin dato</div>', unsafe_allow_html=True)
        return
    latest_price, change = calculate_weekly_change(series)
    show_key_figure(key, label, series, f"$ {charts.format_thousands(latest_price)}",
                    build_change_chip(change), f"$/{unit} · semana del "
                    f"{series.index.max():%d-%m}", mode, color)
# endregion


# region Overview page
def build_channel_series(rows, channel):
    """Weekly consumer price of one channel, indexed by week."""
    channel_rows = rows[rows["channel"] == channel]
    return channel_rows.set_index("week_start")["consumer_price"].sort_index()


def show_overview_figures(rows, mode):
    """Four key figure cards: wholesale, street market, supermarket and margin."""
    unit = rows["normalized_unit"].iloc[0]
    wholesale = rows.groupby("week_start")["wholesale_price"].first().sort_index()
    cards = st.columns(4)
    with cards[0]:
        show_price_figure("wholesale", "Precio mayorista", wholesale, unit, mode,
                          charts.get_channel_color(WHOLESALE_LABEL, mode))
    with cards[1]:
        show_price_figure("street_market", "Precio en feria",
                          build_channel_series(rows, DEFAULT_CHANNEL), unit, mode,
                          charts.get_channel_color(DEFAULT_CHANNEL, mode))
    with cards[2]:
        show_price_figure("supermarket", "Precio en supermercado",
                          build_channel_series(rows, SUPERMARKET), unit, mode,
                          charts.get_channel_color(SUPERMARKET, mode))
    with cards[3]:
        show_margin_figure(rows, mode)
    st.caption(f"Cómo leer las cifras: {KEY_FIGURES_HINT}".replace("**", ""))


def show_margin_figure(rows, mode):
    """Key figure card: supermarket margin over the wholesale price."""
    margins = rows[rows["channel"] == SUPERMARKET].set_index("week_start")["margin"] * 100
    if margins.empty:
        with open_card("margin"):
            st.markdown('<div class="kpi-label">Margen supermercado</div>'
                        '<div class="kpi-value">sin dato</div>', unsafe_allow_html=True)
        return
    latest_margin = margins.sort_index().iloc[-1]
    previous_change = margins.sort_index().diff().iloc[-1] if len(margins) > 1 else None
    show_key_figure("margin", "Margen supermercado sobre mayorista", margins,
                    charts.format_percent(latest_margin, decimals=0),
                    build_change_chip(previous_change, unit="pts"),
                    "(consumidor − mayorista) / mayorista", mode,
                    charts.get_channel_color(SUPERMARKET, mode))


def show_overview_trend(rows, mode):
    """Card: weekly price of the wholesale market and of each consumer channel."""
    with open_card("trend", "Precio por semana", "La línea gris es el precio mayorista.",
                   hint=PRICE_TREND_HINT):
        consumer_rows = rows[["week_start", "channel", "consumer_price"]].rename(
            columns={"consumer_price": "value"})
        wholesale_rows = rows.groupby("week_start", as_index=False)["wholesale_price"].first()
        wholesale_rows = wholesale_rows.rename(columns={"wholesale_price": "value"})
        wholesale_rows["channel"] = WHOLESALE_LABEL
        price_rows = pd.concat([wholesale_rows, consumer_rows], ignore_index=True)
        show_chart(charts.draw_weekly_lines(
            price_rows, f"$/{rows['normalized_unit'].iloc[0]}",
            "$ " + price_rows["value"].map(charts.format_thousands), mode, is_money=True))


def show_overview_margins(rows, mode):
    """Card: median margin of each consumer channel over the weeks shown."""
    with open_card("margins", "Margen mediano por canal",
                   "Cuánto más paga el consumidor que el mayorista.", hint=MEDIAN_MARGIN_HINT):
        median_margins = rows.groupby("channel")["margin"].median() * 100
        bar_rows = pd.DataFrame({"label": median_margins.index,
                                 "value": median_margins.to_numpy()})
        bar_rows["value_label"] = bar_rows["value"].map(
            lambda margin: charts.format_percent(margin, decimals=0))
        bar_rows["meaning"] = bar_rows["value"].map(charts.describe_margin)
        colors = [charts.get_channel_color(channel, mode) for channel in bar_rows["label"]]
        show_chart(charts.draw_horizontal_bars(bar_rows, "Margen mediano (%)", mode, colors))


def show_overview_regions(product, key_label, mode):
    """Card: regional index of the street market price for the chosen product."""
    with open_card("regions", "¿Dónde es más caro?",
                   "Precio en feria por región; 1 = promedio nacional.",
                   hint=REGIONAL_INDEX_HINT):
        rows = read_indicator("k3_regional_index")
        rows = rows[(rows["product"] == product) & (rows["key_label"] == key_label)
                    & (rows["channel"] == DEFAULT_CHANNEL)]
        if rows.empty:
            st.info(NO_DATA_TEXT)
            return
        average_index = rows.groupby("region")["regional_index"].mean()
        bar_rows = pd.DataFrame({
            "label": [charts.shorten_region_name(region) for region in average_index.index],
            "value": average_index.to_numpy()})
        bar_rows["value_label"] = bar_rows["value"].map(charts.format_index)
        bar_rows["meaning"] = bar_rows["value"].map(charts.describe_regional_index)
        show_chart(charts.draw_horizontal_bars(bar_rows, "Índice regional", mode,
                                               reference_value=1))


def build_alert_rows_html(alert_rows):
    """Table cells for alerts: product, channel and a red or blue change chip."""
    table_rows = []
    for alert in alert_rows.to_dict("records"):
        change = alert["variation"] * 100
        kind = "rise" if change > 0 else "fall"
        arrow = "▲" if change > 0 else "▼"
        table_rows.append([html.escape(describe_product(alert)),
                           html.escape(alert["channel"]),
                           build_chip(f"{arrow} {charts.format_signed_percent(change)}", kind,
                                      charts.describe_weekly_change(change))])
    return table_rows


def show_overview_alerts():
    """Card: the largest price movements of the latest week."""
    alert_rows = read_price_alerts()
    latest_week = read_indicator("k6_national_weekly_price")["week_start"].max()
    week_alerts = alert_rows[alert_rows["week_start"] == latest_week]
    with open_card("alerts", f"Alertas de la semana ({len(week_alerts)})",
                   f"Semana del {latest_week:%d-%m-%Y}. Señales para revisar, no conclusiones.",
                   hint=ALERTS_HINT):
        if week_alerts.empty:
            st.info("Ningún producto se movió fuera de su rango habitual.")
            return
        largest_first = week_alerts["variation"].abs().sort_values(ascending=False).index
        shown_alerts = week_alerts.loc[largest_first].head(OVERVIEW_ALERT_COUNT)
        st.markdown(build_html_table(["Producto", "Canal", "Variación"],
                                     build_alert_rows_html(shown_alerts)),
                    unsafe_allow_html=True)


def show_overview_page(mode):
    """Home page: key figures, trend, margins, regions and alerts on one screen."""
    show_page_header("Panel de precios", "Del mercado mayorista al consumidor, con datos "
                     "oficiales de ODEPA que se actualizan solos cada martes.")
    rows = read_indicator("k1_margin")
    filter_columns = st.columns([1, 1, 1.4, 1.4])
    with filter_columns[0]:
        group = choose_value("Grupo", rows["product_group"].unique(), DEFAULT_GROUP)
    rows = rows[rows["product_group"] == group]
    with filter_columns[1]:
        product = choose_value("Producto", rows["product"].unique(), DEFAULT_PRODUCT)
    rows = rows[rows["product"] == product]
    with filter_columns[2]:
        key_label = st.selectbox("Variedad · calidad · unidad",
                                 rows["key_label"].value_counts().index.to_list())
    rows = rows[rows["key_label"] == key_label]
    with filter_columns[3]:
        region = choose_value("Región", rows["region"].unique(), DEFAULT_REGION)
    rows = rows[rows["region"] == region]

    show_overview_figures(rows, mode)
    trend_column, margin_column = st.columns([3, 2])
    with trend_column:
        show_overview_trend(rows, mode)
    with margin_column:
        show_overview_margins(rows, mode)
    region_column, alert_column = st.columns([2, 3])
    with region_column:
        show_overview_regions(product, key_label, mode)
    with alert_column:
        show_overview_alerts()
    st.caption(NOMINAL_PRICES_TEXT)
# endregion


# region Project page
def build_question_rows():
    """Table cells: question number, question, page that answers it and its state."""
    rows = []
    for number, (question, page, state, scope) in enumerate(BUSINESS_QUESTIONS, start=1):
        state_text, kind = QUESTION_STATES[state]
        rows.append([f"P{number}", html.escape(question), html.escape(page),
                     build_chip(state_text, kind, scope)])
    return rows


def show_project_page(mode):
    """The business idea: the problem, who it is for and the questions it answers."""
    show_page_header("El proyecto", "Qué problema resuelve este panel, para quién y qué "
                     "preguntas de negocio responde.")
    problem_column, audience_column = st.columns([3, 2])
    with problem_column, open_card("project_problem", "El problema"):
        st.markdown(PROBLEM_TEXT)
    with audience_column, open_card("project_audience", "Para quién"):
        st.markdown(AUDIENCE_TEXT)
    with open_card("project_questions", "Preguntas de negocio que responde",
                   hint="Pasa el mouse sobre el estado para ver a qué productos aplica."):
        st.markdown(build_html_table(["", "Pregunta", "Dónde verla", "Estado"],
                                     build_question_rows()), unsafe_allow_html=True)
    why_column, data_column, limits_column = st.columns(3)
    with why_column, open_card("project_why", "Por qué este tema"):
        st.markdown(WHY_TEXT)
    with data_column, open_card("project_data", "Los datos"):
        st.markdown(DATA_TEXT)
    with limits_column, open_card("project_limits", "Límites"):
        st.markdown(LIMITS_TEXT)
# endregion


# region Margins page
def show_margins_page(mode):
    """K1: margin between the wholesale price and each consumer channel."""
    show_page_header("Márgenes", "Margen = (precio al consumidor − precio mayorista) / "
                     "precio mayorista, con la misma variedad, calidad, región, semana y unidad.")
    rows = choose_product_rows(read_indicator("k1_margin"))
    region_column, channel_column = st.columns([1, 2])
    with region_column:
        region = choose_value("Región", rows["region"].unique(), DEFAULT_REGION)
    rows = rows[rows["region"] == region]
    available_channels = sorted(rows["channel"].unique())
    with channel_column:
        channels = st.multiselect("Canal", available_channels, default=[
            channel for channel in DEFAULT_MARGIN_CHANNELS if channel in available_channels])
    rows = rows[rows["channel"].isin(channels)].copy()
    if rows.empty:
        st.info(NO_DATA_TEXT)
        return
    rows["margin_percent"] = rows["margin"] * 100
    with open_card("margin_trend", "Margen por semana", hint=MARGIN_TREND_HINT):
        margin_rows = rows[["week_start", "channel", "margin_percent"]].rename(
            columns={"margin_percent": "value"})
        show_chart(charts.draw_weekly_lines(
            margin_rows, "Margen (%)", margin_rows["value"].map(charts.format_percent),
            mode, is_money=False))
    trend_column, bars_column = st.columns([3, 2])
    with trend_column:
        show_overview_trend(rows, mode)
    with bars_column:
        show_overview_margins(rows, mode)
    st.caption(NOMINAL_PRICES_TEXT)
# endregion


# region Channels and regions page
def show_channel_gaps(rows, mode):
    """Card: K2, average price gap of each channel against a reference channel."""
    with open_card("channel_gaps", "Diferencia entre canales", hint=CHANNEL_GAP_HINT):
        if rows.empty:
            st.info("Este producto se registra en un solo canal.")
            return
        reference_channel = choose_value("Comparar contra",
                                         rows["reference_channel"].unique(), DEFAULT_CHANNEL)
        rows = rows[rows["reference_channel"] == reference_channel]
        average_gap = rows.groupby("channel")["gap"].mean() * 100
        bar_rows = pd.DataFrame({"label": average_gap.index, "value": average_gap.to_numpy()})
        bar_rows["value_label"] = bar_rows["value"].map(charts.format_signed_percent)
        bar_rows["meaning"] = [charts.describe_channel_gap(gap, reference_channel)
                               for gap in bar_rows["value"]]
        colors = [charts.get_channel_color(channel, mode) for channel in bar_rows["label"]]
        show_chart(charts.draw_horizontal_bars(bar_rows, "Diferencia promedio (%)", mode,
                                               colors, reference_value=0))
        st.caption(f"Cuánto más caro (+) o más barato (−) es cada canal que "
                   f"«{reference_channel}», en las semanas y regiones donde ambos tienen precio.")


def show_regional_index(rows, mode):
    """Card: K3, average regional index of each region for one channel."""
    with open_card("regional_index", "Precio por región", hint=REGIONAL_INDEX_HINT):
        channel = choose_value("Canal", rows["channel"].unique(), DEFAULT_CHANNEL)
        rows = rows[rows["channel"] == channel]
        average_index = rows.groupby("region")["regional_index"].mean()
        bar_rows = pd.DataFrame({
            "label": [charts.shorten_region_name(region) for region in average_index.index],
            "value": average_index.to_numpy()})
        bar_rows["value_label"] = bar_rows["value"].map(charts.format_index)
        bar_rows["meaning"] = bar_rows["value"].map(charts.describe_regional_index)
        show_chart(charts.draw_horizontal_bars(bar_rows, "Índice regional", mode,
                                               reference_value=1))
        st.caption("Sobre 1, la región es más cara que el promedio nacional de la semana; "
                   "bajo 1, más barata.")


def show_channels_and_regions_page(mode):
    """K2 and K3 for any product group, with or without a wholesale price."""
    show_page_header("Canales y regiones", "Qué canal y qué región son más caros para un "
                     "producto, incluidas carnes, lácteos y abarrotes.")
    regional_rows = choose_product_rows(read_indicator("k3_regional_index"))
    key_label = regional_rows["key_label"].iloc[0]
    product = regional_rows["product"].iloc[0]
    gap_rows = read_indicator("k2_channel_gap")
    gap_rows = gap_rows[(gap_rows["product"] == product)
                        & (gap_rows["key_label"] == key_label)]
    gaps_column, regions_column = st.columns(2)
    with gaps_column:
        show_channel_gaps(gap_rows, mode)
    with regions_column:
        show_regional_index(regional_rows, mode)
    st.caption(NOMINAL_PRICES_TEXT)
# endregion


# region Seasonality page
def show_seasonality_page(mode):
    """K4: national price of each week over the average of its year."""
    show_page_header("Estacionalidad", "Índice = precio nacional de la semana / promedio "
                     "del año. Con un solo año cargado muestra la variación dentro del año.")
    rows = choose_product_rows(read_indicator("k4_seasonal_index"))
    channel = choose_value("Canal", rows["channel"].unique(), DEFAULT_CHANNEL)
    rows = rows[rows["channel"] == channel]
    index_column, price_column = st.columns(2)
    with index_column, open_card("seasonal_index", "Índice estacional",
                                 "1 = precio promedio del año.", hint=SEASONAL_INDEX_HINT):
        index_rows = rows[["week_start", "seasonal_index"]].rename(
            columns={"seasonal_index": "value"})
        show_chart(charts.draw_single_weekly_area(
            index_rows, "Índice", index_rows["value"].map(charts.format_index), mode,
            reference_value=1))
    with price_column, open_card("national_price", "Precio nacional por semana",
                                 hint=NATIONAL_PRICE_HINT):
        price_rows = rows[["week_start", "national_price"]].rename(
            columns={"national_price": "value"})
        show_chart(charts.draw_single_weekly_area(
            price_rows, f"$/{rows['normalized_unit'].iloc[0]}",
            "$ " + price_rows["value"].map(charts.format_thousands), mode, is_money=True))
    st.caption(NOMINAL_PRICES_TEXT)
# endregion


# region Alerts page
def format_alerts(alert_rows):
    """Alerts as a table for the reader, largest movements first."""
    order = alert_rows["variation"].abs().sort_values(ascending=False).index
    alert_rows = alert_rows.loc[order]
    return pd.DataFrame({
        "Producto": [describe_product(row) for row in alert_rows.to_dict("records")],
        "Canal": alert_rows["channel"],
        "Unidad": alert_rows["normalized_unit"],
        "Precio nacional": "$ " + alert_rows["national_price"].map(charts.format_thousands),
        "Variación": (alert_rows["variation"] * 100).map(charts.format_signed_percent),
        "Variación habitual": (alert_rows["usual_variation"] * 100).map(
            charts.format_signed_percent),
    })


def show_alerts_page(mode):
    """K6: products whose price moved outside their usual range in one week."""
    show_page_header("Alertas", "Hay alerta cuando el cambio semanal del precio se aleja "
                     "más de 2 desviaciones estándar de lo habitual en las 12 semanas previas.")
    alert_rows = read_price_alerts()
    if alert_rows.empty:
        st.info("Todavía no hay semanas suficientes para calcular alertas.")
        return
    weeks = sorted(alert_rows["week_start"].dt.date.unique(), reverse=True)
    week = st.selectbox("Semana (lunes de inicio)", weeks,
                        format_func=lambda day: day.strftime("%d-%m-%Y"))
    week_rows = alert_rows[alert_rows["week_start"].dt.date == week]
    with open_card("alert_bars", f"Mayores movimientos ({len(week_rows)} alertas)",
                   "Rojo: subió. Azul: bajó.", hint=ALERTS_HINT):
        largest_first = week_rows["variation"].abs().sort_values(ascending=False).index
        shown_rows = week_rows.loc[largest_first].head(ALERTS_PAGE_BAR_COUNT)
        bar_rows = pd.DataFrame({
            "label": [f"{describe_product(row)} ({row['channel']})"
                      for row in shown_rows.to_dict("records")],
            "value": shown_rows["variation"].to_numpy() * 100})
        show_chart(charts.draw_variation_bars(bar_rows, mode))
    with open_card("alert_table", "Todas las alertas de la semana"):
        st.dataframe(format_alerts(week_rows), hide_index=True, use_container_width=True)
    st.caption(NOMINAL_PRICES_TEXT)
# endregion


# region Control center page
def get_secret(name):
    """A dashboard secret, or None when it is not configured."""
    try:
        return st.secrets.get(name)
    except Exception:  # no secrets file at all
        return None


@st.cache_data(ttl=30)
def read_robot_runs():
    """(latest runs, error text). Kept 30 seconds so GitHub is not asked on every click."""
    try:
        return control.list_workflow_runs(get_secret(SECRET_GITHUB_TOKEN),
                                          RUN_HISTORY_COUNT), ""
    except Exception as error:  # GitHub unreachable or refused
        return [], str(error)


def build_run_chip(state):
    """Chip for a robot run: Éxito, Falla or En curso."""
    texts = {control.RUN_OK: ("Éxito", "ok"), control.RUN_FAILED: ("Falla", "failed"),
             control.RUN_IN_PROGRESS: ("En curso", "running")}
    text, kind = texts.get(state, ("Omitido", "neutral"))
    return build_chip(text, kind)


def show_robot_status(runs):
    """Three cards: latest run, next automatic run and latest data load."""
    status_column, next_column, data_column = st.columns(3)
    with status_column, open_card("robot_latest"):
        st.markdown('<div class="kpi-label">Última ejecución del robot</div>',
                    unsafe_allow_html=True)
        if runs:
            latest = runs[0]
            st.markdown(f'<div class="kpi-value">{format_chile_time(latest["started_at"])}</div>'
                        f'{build_run_chip(latest["state"])}'
                        f'<span class="kpi-note"> {latest["trigger"]}</span>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="kpi-value">sin datos</div>', unsafe_allow_html=True)
    with next_column, open_card("robot_next"):
        next_run = control.calculate_next_scheduled_run(datetime.now(timezone.utc))
        st.markdown('<div class="kpi-label">Próxima ejecución automática</div>'
                    f'<div class="kpi-value">{format_chile_time(next_run)}</div>'
                    '<div class="kpi-note">Cada martes, sin intervención</div>',
                    unsafe_allow_html=True)
    with data_column, open_card("robot_data"):
        latest_run = read_latest_run()
        st.markdown('<div class="kpi-label">Filas cargadas en la última carga</div>'
                    f'<div class="kpi-value">{charts.format_thousands(latest_run["rows_loaded"])}'
                    f'</div><div class="kpi-note">{latest_run["rows_rejected"]} rechazadas</div>',
                    unsafe_allow_html=True)


def build_step_lines(steps):
    """Progress of a run as text lines with an icon per step."""
    icons = {control.RUN_OK: "✅", control.RUN_FAILED: "❌",
             control.RUN_IN_PROGRESS: "⏳", "skipped": "⏭️"}
    if not steps:
        return "⏳ Preparando el robot…"
    return "  \n".join(f"{icons.get(state, '•')} {name}" for name, state in steps)


def wait_for_manual_run(requested_at, token):
    """The run GitHub created for the click, or None if it does not appear in time."""
    for _ in range(10):
        time.sleep(PROGRESS_POLL_SECONDS)
        run = control.find_run_started_after(
            control.list_workflow_runs(token, RUN_HISTORY_COUNT), requested_at)
        if run is not None:
            return run
    return None


def follow_run_progress(run_id, token, progress_area):
    """Show the steps until the run ends; return its final state."""
    waited_seconds = 0
    while waited_seconds < PROGRESS_MAXIMUM_SECONDS:
        progress_area.markdown(build_step_lines(control.list_run_steps(run_id, token)))
        runs = control.list_workflow_runs(token, RUN_HISTORY_COUNT)
        state = next((run["state"] for run in runs if run["id"] == run_id),
                     control.RUN_IN_PROGRESS)
        if state != control.RUN_IN_PROGRESS:
            progress_area.markdown(build_step_lines(control.list_run_steps(run_id, token)))
            return state
        time.sleep(PROGRESS_POLL_SECONDS)
        waited_seconds += PROGRESS_POLL_SECONDS
    return control.RUN_IN_PROGRESS


def run_robot_now(token):
    """Start the robot and show its steps live until it finishes."""
    requested_at = datetime.now(timezone.utc)
    control.start_workflow_run(token)
    with st.status("El robot está trabajando…", expanded=True) as status_box:
        run = wait_for_manual_run(requested_at, token)
        if run is None:
            status_box.update(label="GitHub no confirmó el inicio; revisa el historial "
                              "en un minuto.", state="error")
            return
        state = follow_run_progress(run["id"], token, st.empty())
        if state == control.RUN_OK:
            status_box.update(label="Listo: datos descargados, revisados y guardados.",
                              state="complete")
            st.success("El panel muestra los datos nuevos en cuanto recibe la base "
                       "guardada, normalmente en 1 o 2 minutos. Usa «Recargar datos».")
        else:
            status_box.update(label="El robot terminó con una falla. Los datos anteriores "
                              "siguen intactos.", state="error")
    read_robot_runs.clear()


def show_run_now_card():
    """Card with the button that starts the robot, protected by an access code."""
    with open_card("run_now", "Ejecutar ahora",
                   "Descarga los datos de ODEPA, los limpia, los prueba y actualiza el "
                   "panel. Tarda alrededor de un minuto."):
        token = get_secret(SECRET_GITHUB_TOKEN)
        access_code = get_secret(SECRET_CONTROL_CODE)
        if not token or not access_code:
            st.info("El botón se activa cuando la autora configura su clave de GitHub y "
                    "su código de acceso en los secretos del panel. Mientras tanto, el "
                    "robot se puede lanzar desde GitHub.")
            st.link_button("Abrir el robot en GitHub", control.WORKFLOW_PAGE_URL,
                           icon=":material/open_in_new:")
            return
        typed_code = st.text_input("Código de acceso", type="password")
        if st.button("Ejecutar ahora", type="primary", icon=":material/play_arrow:"):
            if not hmac.compare_digest(typed_code, access_code):
                st.error("Código de acceso incorrecto.")
                return
            run_robot_now(token)


def show_run_history(runs, error_text):
    """Card: latest robot runs with their state."""
    with open_card("run_history", "Historial de ejecuciones"):
        if error_text:
            st.warning("No se pudo consultar GitHub en este momento.")
            return
        table_rows = [[format_chile_time(run["started_at"]), html.escape(run["trigger"]),
                       format_duration(run["duration"]) if run["duration"] else "—",
                       build_run_chip(run["state"]),
                       f'<a href="{html.escape(run["url"])}" target="_blank">detalle</a>']
                      for run in runs]
        st.markdown(build_html_table(["Inicio", "Tipo", "Duración", "Estado", ""],
                                     table_rows), unsafe_allow_html=True)


def show_control_page(mode):
    """The weekly robot: its state, its history and a button to run it now."""
    show_page_header("Centro de control", "El robot descarga, revisa y guarda los datos "
                     "cada martes. Aquí ves su estado y puedes lanzarlo cuando quieras.")
    runs, error_text = read_robot_runs()
    show_robot_status(runs)
    run_column, history_column = st.columns([2, 3])
    with run_column:
        show_run_now_card()
        if st.button("Recargar datos del panel", icon=":material/refresh:"):
            st.cache_data.clear()
            st.rerun()
    with history_column:
        show_run_history(runs, error_text)
# endregion


# region Architecture page
def read_download_manifest():
    """Record of the downloaded files (agent/downloads/manifest.json), or {}."""
    try:
        return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@st.cache_data(ttl=30)
def read_latest_robot_steps():
    """(state of each step by Spanish name, latest robot run) from GitHub, or ({}, None)."""
    runs, _ = read_robot_runs()
    if not runs:
        return {}, None
    try:
        steps = control.list_run_steps(runs[0]["id"], get_secret(SECRET_GITHUB_TOKEN))
    except Exception:  # GitHub unreachable: the stage shows "Sin datos"
        return {}, runs[0]
    return dict(steps), runs[0]


def get_step_state(step_states, workflow_step):
    """State of one workflow step, by its name in semanal.yml."""
    return step_states.get(control.STEP_NAMES[workflow_step], architecture.STATE_UNKNOWN)


def describe_years(manifest):
    """'año 2026' or 'años 2022 a 2026' from the downloaded files."""
    years = sorted({file_info["year"] for file_info in manifest.values()})
    if not years:
        return "sin descargas"
    if years[0] == years[-1]:
        return f"año {years[0]}"
    return f"años {years[0]} a {years[-1]}"


def build_journey_states(step_states, robot_run, latest_load, manifest):
    """Real state of each step: from the latest robot run and the current database."""
    load_state = (control.RUN_OK if latest_load["status"] == etl.STATUS_LOADED
                  else control.RUN_FAILED)
    return {
        "sources": control.RUN_OK if manifest else architecture.STATE_UNKNOWN,
        "download": get_step_state(step_states, "Download the ODEPA files"),
        "etl": get_step_state(step_states, "Run the ETL"),
        "tests": get_step_state(step_states, "Run the tests against the new database"),
        "report": get_step_state(step_states, "Publish the weekly report"),
        "robot": robot_run["state"] if robot_run else architecture.STATE_UNKNOWN,
        "load": load_state,
        "panel": control.RUN_OK,
    }


def build_journey_figures(manifest, robot_run, latest_load):
    """Short texts shown under the steps, all from real data."""
    weekly_prices = read_indicator("quality_flag_counts")["weekly_prices"].sum()
    latest_week = read_indicator("k6_national_weekly_price")["week_start"].max()
    loaded_at = to_chile_time(parse_run_start(latest_load["started_at"]))
    next_run = control.calculate_next_scheduled_run(datetime.now(timezone.utc))
    last_run = (f"última {to_chile_time(robot_run['started_at']):%d-%m %H:%M}"
                if robot_run else "sin datos del robot")
    return {
        "source_years": describe_years(manifest),
        "last_run": last_run,
        "rows_read": f"{charts.format_thousands(latest_load['rows_read'])} filas leídas",
        "rows_rejected": f"{charts.format_thousands(latest_load['rows_rejected'])} filas",
        "weekly_prices": f"{charts.format_thousands(weekly_prices)} precios",
        "latest_week": f"hasta {latest_week:%d-%m-%Y}",
        "panel_time": f"datos al {loaded_at:%d-%m %H:%M}",
        "next_run": f"{to_chile_time(next_run):%d-%m %H:%M}",
    }


def show_architecture_page(mode):
    """Live diagram of the data journey, from ODEPA to this dashboard."""
    show_page_header("Cómo funciona", "El recorrido de los datos, de ODEPA a este panel. "
                     "Los puntos de color muestran el estado real de cada paso.")
    step_states, robot_run = read_latest_robot_steps()
    latest_load = read_latest_run()
    manifest = read_download_manifest()
    with open_card("journey", hint=ARCHITECTURE_HINT):
        st.image(architecture.build_journey_svg(
            build_journey_states(step_states, robot_run, latest_load, manifest),
            build_journey_figures(manifest, robot_run, latest_load), mode),
            use_container_width=True)
    report_column, legend_column = st.columns(2)
    with report_column, open_card("journey_report"):
        st.markdown('<div class="kpi-label">Informe que deja cada ejecución</div>',
                    unsafe_allow_html=True)
        st.link_button("Ver informes semanales", ISSUES_PAGE_URL,
                       icon=":material/description:")
    with legend_column, open_card("journey_legend"):
        st.markdown(f'{build_chip("OK", "ok")} {build_chip("En curso", "running")} '
                    f'{build_chip("Falla", "failed")} {build_chip("Sin datos", "neutral")}'
                    '<div class="kpi-note" style="margin-top:8px">Punto de color en cada '
                    'paso: estado de la última ejecución del robot y de la base actual.'
                    '</div>', unsafe_allow_html=True)
# endregion


# region Data quality page
def show_load_figures(latest_run):
    """Three cards with the row counts of the latest load."""
    figures = [("Filas leídas", latest_run["rows_read"]),
               ("Filas cargadas", latest_run["rows_loaded"]),
               ("Filas rechazadas", latest_run["rows_rejected"])]
    for column, (label, count) in zip(st.columns(3), figures):
        with column, open_card(f"load_{label}"):
            st.markdown(f'<div class="kpi-label">{label}</div>'
                        f'<div class="kpi-value">{charts.format_thousands(count)}</div>',
                        unsafe_allow_html=True)


def show_flag_donut(mode):
    """Card: weekly prices used in the indicators against those left out."""
    flag_counts = read_indicator("quality_flag_counts")
    totals = flag_counts.groupby("flag")["weekly_prices"].sum()
    with open_card("flag_donut", "Estado de los precios semanales"):
        palette = charts.get_palette(mode)
        rows = pd.DataFrame({"label": [FLAG_NAMES.get(flag, flag) for flag in totals.index],
                             "value": totals.to_numpy()})
        rows["value_label"] = rows["value"].map(charts.format_thousands)
        colors = [palette["accent"] if flag == "SIN_MARCA" else
                  palette["rise"] if flag == etl.FLAG_OUTLIER else palette["reference"]
                  for flag in totals.index]
        donut_column, legend_column = st.columns([1, 1], vertical_alignment="center")
        with donut_column:
            show_chart(charts.draw_donut(rows, colors, mode))
        with legend_column:
            for label, value_label, color in zip(rows["label"], rows["value_label"], colors):
                st.markdown(f'<span style="color:{color}">●</span> {html.escape(label)}: '
                            f'**{value_label}**', unsafe_allow_html=True)


def show_quality_details():
    """Card: match coverage (K7), rejections (K8) and the list of outliers."""
    keys_with_margin, consumer_keys = read_match_coverage()
    with open_card("quality_details", "Cobertura y rechazos"):
        st.markdown(f"**K7 · Cobertura del cruce:** {keys_with_margin} de {consumer_keys} "
                    f"claves de frutas y verduras tienen margen "
                    f"({charts.format_percent(keys_with_margin / consumer_keys * 100)}).")
        rejections = read_indicator("k8_rejected_rows")
        if rejections.empty:
            st.markdown(f"**K8 · Rechazos:** {build_chip('0 filas rechazadas', 'ok')}",
                        unsafe_allow_html=True)
        else:
            st.dataframe(rejections, hide_index=True)
        outliers = read_indicator("quality_outliers").drop(columns="key_label").copy()
        outliers["week_start"] = outliers["week_start"].dt.strftime("%d-%m-%Y")
        outliers["source"] = outliers["source"].map(SOURCE_NAMES)
        outliers.columns = ["Semana", "Fuente", "Canal", "Región", "Producto", "Variedad",
                            "Calidad", "Unidad", "Precio", "Observaciones"]
        with st.expander(f"Ver los {len(outliers)} precios marcados como atípicos"):
            st.dataframe(outliers, hide_index=True)


def show_data_quality_page(mode):
    """Whether the latest load worked and what was left out."""
    show_page_header("Calidad de datos", "Qué se cargó, qué quedó fuera y por qué.")
    show_load_figures(read_latest_run())
    donut_column, details_column = st.columns([2, 3])
    with donut_column:
        show_flag_donut(mode)
    with details_column:
        show_quality_details()
# endregion


# region Entry point
SHOW_PAGE_BY_TITLE = {
    PAGE_OVERVIEW: show_overview_page,
    PAGE_PROJECT: show_project_page,
    PAGE_MARGINS: show_margins_page,
    PAGE_CHANNELS_AND_REGIONS: show_channels_and_regions_page,
    PAGE_SEASONALITY: show_seasonality_page,
    PAGE_ALERTS: show_alerts_page,
    PAGE_ARCHITECTURE: show_architecture_page,
    PAGE_CONTROL: show_control_page,
    PAGE_DATA_QUALITY: show_data_quality_page,
}


def show_attribution():
    """Footer with the data source, shown under every page."""
    st.divider()
    st.caption(ATTRIBUTION_TEXT)


def render_page(title):
    """Draw one page with the style of the active mode and the footer."""
    mode = get_mode()
    apply_style(mode)
    SHOW_PAGE_BY_TITLE[title](mode)
    show_attribution()


def build_page(title, is_default):
    """A navigation entry that draws one page."""
    return st.Page(lambda: render_page(title), title=title, icon=PAGE_ICONS[title],
                   url_path=PAGE_PATHS[title], default=is_default)


def main():
    """Profile selector, navigation with icons and the chosen page."""
    st.set_page_config(page_title="Monitor de precios de alimentos", layout="wide",
                       page_icon=":material/monitoring:")
    if not queries.DATABASE_FILE.exists():
        st.error("Falta etl/datos.db. Ejecuta primero: python etl/etl.py")
        return
    profile = st.sidebar.selectbox("¿Quién consulta?", list(PAGES_BY_PROFILE))
    pages = [build_page(title, position == 0)
             for position, title in enumerate(PAGES_BY_PROFILE[profile])]
    st.navigation(pages, position="sidebar").run()
    st.sidebar.caption("Fuente: ODEPA · actualización automática cada martes.")


if __name__ == "__main__":
    main()
# endregion
