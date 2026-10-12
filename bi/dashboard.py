"""Streamlit dashboard for the price monitor.

Run it with:  streamlit run bi/dashboard.py

It reads etl/datos.db through the named queries of bi/queries.sql, and the
state of the weekly pipeline through the GitHub API (bi/control.py).
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
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

# region Imports of the project
# Streamlit runs this file as a script, so the project folder is added to the
# import path to reach the other modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import (alerts, architecture, charts, control, explorer, lag, project,  # noqa: E402
                queries)
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
PAGE_EXPLORER = "Consultas"
PAGE_ARCHITECTURE = "Pipeline"
PAGE_CONTROL = "Centro de control"
PAGE_DATA_QUALITY = "Calidad de datos"
PAGES_BY_PROFILE = {
    PROFILE_ANALYST: [PAGE_OVERVIEW, PAGE_PROJECT, PAGE_MARGINS, PAGE_CHANNELS_AND_REGIONS,
                      PAGE_SEASONALITY, PAGE_ALERTS, PAGE_EXPLORER, PAGE_ARCHITECTURE,
                      PAGE_CONTROL],
    PROFILE_DATA_TEAM: [PAGE_OVERVIEW, PAGE_PROJECT, PAGE_ARCHITECTURE, PAGE_CONTROL,
                        PAGE_DATA_QUALITY, PAGE_EXPLORER],
}
PAGE_ICONS = {
    PAGE_OVERVIEW: ":material/space_dashboard:", PAGE_PROJECT: ":material/lightbulb:",
    PAGE_MARGINS: ":material/percent:",
    PAGE_CHANNELS_AND_REGIONS: ":material/storefront:",
    PAGE_SEASONALITY: ":material/calendar_month:",
    PAGE_ALERTS: ":material/notifications_active:",
    PAGE_EXPLORER: ":material/manage_search:",
    PAGE_ARCHITECTURE: ":material/account_tree:", PAGE_CONTROL: ":material/smart_toy:", PAGE_DATA_QUALITY: ":material/verified:",
}
PAGE_PATHS = {
    PAGE_OVERVIEW: "panel", PAGE_PROJECT: "el-proyecto", PAGE_MARGINS: "margenes",
    PAGE_CHANNELS_AND_REGIONS: "canales-y-regiones", PAGE_SEASONALITY: "estacionalidad",
    PAGE_ALERTS: "alertas", PAGE_EXPLORER: "consultas", PAGE_ARCHITECTURE: "pipeline",
    PAGE_CONTROL: "centro-de-control",
    PAGE_DATA_QUALITY: "calidad-de-datos",
}

# The project page: its tabs travel in the address (?seccion=...), so a link can
# open one of them; ?perfil=... chooses the profile the same way.
PROJECT_TAB_IDEA = "Idea de negocio"
PROJECT_TAB_SOURCES = "Fuentes y cruces"
PROJECT_TAB_MODEL = "Modelo de datos"
PROJECT_TAB_KPI = "KPI y cálculos"
PROJECT_TAB_RULES = "Reglas de calidad"
PROJECT_TAB_MANUAL = "Cómo funciona"
PROJECT_TAB_DECISIONS = "Decisiones y método"
PROJECT_TAB_CODE = "Código"
PROJECT_TABS = [PROJECT_TAB_IDEA, PROJECT_TAB_SOURCES, PROJECT_TAB_MODEL, PROJECT_TAB_KPI,
                PROJECT_TAB_RULES, PROJECT_TAB_MANUAL, PROJECT_TAB_DECISIONS, PROJECT_TAB_CODE]
TAB_PARAMETER = "seccion"
PROFILE_PARAMETER = "perfil"
KPI_PARAMETER = "kpi"
JOURNEY_MANAGER = "Soy gerente"
JOURNEY_ANALYST = "Soy analista"
JOURNEY_TECHNICAL = "Soy técnico"

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
# Consultas page: it opens with one row per product and channel.
EXPLORER_DEFAULT_GROUPS = [explorer.GROUP_PRODUCT, explorer.GROUP_CHANNEL]
EXPLORER_FILTER_LABELS = {explorer.FILTER_PRODUCTS: "Producto",
                          explorer.FILTER_REGIONS: "Región", explorer.FILTER_CHANNELS: "Canal"}
# The named query each pandas-built view starts from, shown in «Ver SQL».
EXPLORER_BASE_QUERIES = {explorer.VIEW_MARGINS: "k1_margin",
                         explorer.VIEW_ALERTS: "k6_national_weekly_price"}

MANIFEST_FILE = Path(__file__).resolve().parent.parent / "agent" / "downloads" / "manifest.json"
ISSUES_PAGE_URL = f"https://github.com/{control.REPOSITORY}/issues"
CHILE_TIME_ZONE = "America/Santiago"
# Seconds between two questions to GitHub while the pipeline runs, and the
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
LAG_HINT = ("Cuántas semanas tarda el precio al consumidor en moverse después del "
            "mayorista. Para cada desfase de 0 a 8 semanas se mide la **correlación** entre "
            "los cambios semanales de ambos precios: 1 = se mueven igual, 0 = sin relación. "
            "El rezago es el desfase con la correlación más alta, si se distingue de cero "
            "(más de 2/√pares). Necesita 26 semanas.")
LAG_NOTE = ("Indicador descriptivo: muestra qué desfase coincide mejor con los datos, no "
            "prueba que el precio mayorista cause el cambio al consumidor.")
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
                       "precio estuvo 20 % sobre su promedio; **0,80** = 20 % bajo. Con "
                       "datos desde 2022 se ve si el producto sube o baja siempre en las "
                       "mismas semanas del año.")
NATIONAL_PRICE_HINT = ("Promedio simple de las regiones con dato, en pesos por kilo (o por "
                       "unidad), semana a semana.")
ARCHITECTURE_HINT = ("Los datos viajan de izquierda a derecha. **Bronce**: el archivo tal "
                     "como llega. **Limpieza y reglas**: se corrigen formatos y se aplican "
                     "las reglas de negocio. **Calidad**: si algo no cuadra, no se guarda "
                     "nada. **Oro**: la base lista para analizar. Arriba, quién da las "
                     "órdenes; abajo, cómo sabemos qué pasó. El punto de color de cada paso "
                     "es su estado real.")
EXPLORER_VIEW_HINT = ("**Precios semanales**: el precio de cada producto por región y canal, "
                      "semana a semana. **Márgenes**: cuánto más paga el consumidor que el "
                      "mayorista, en %. **Alertas**: cambios semanales fuera de lo habitual, "
                      "calculados con el precio nacional (por eso no tienen región).")
EXPLORER_GROUP_HINT = ("Cada casilla parte el resultado en grupos: Producto + Canal da una fila "
                       "por producto en cada canal. Producto junta todas sus variedades y "
                       "calidades. En precios se agrega siempre la unidad ($/kilo, $/unidad) "
                       "para no mezclar pesos por kilo con pesos por unidad.")
EXPLORER_FILTER_HINT = ("Una lista vacía incluye todo. Las fechas son el lunes de cada semana.")
EXPLORER_MEASURE_HINT = ("Cómo resumir cada grupo. **Mediana**: el valor del medio; los precios "
                         "muy altos o muy bajos la mueven menos que al promedio.")
EXPLORER_RESULT_HINT = ("Una fila por grupo, con la medida elegida y cuántos valores semanales "
                        "resume. Los precios marcados como atípicos o sin unidad convertible "
                        "quedan fuera, igual que en el resto del panel.")
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
    "Precios nominales, sin ajuste por inflación: al comparar años, parte de la subida "
    "es inflación. Datos desde enero de 2022. "
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
     "available", "Todos los grupos, desde 2022"),
    ("¿Con cuántas semanas de diferencia sigue el precio al consumidor al mayorista?",
     PAGE_MARGINS, "available", "Frutas y verduras; descriptivo, no prueba causa"),
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
    .kpi-link {{ margin-left: 10px; font-size: 0.8rem; font-weight: 400; }}
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
    /* On narrow screens the explanation opens as a panel at the bottom of the
       screen, so it never runs off the edge. On computers the chips use the
       browser's own tooltip (title), so only one explanation shows at a time. */
    @media (max-width: 640px) {{
        .hint:hover::after, .hint:focus::after {{
            position: fixed; left: 16px; right: 16px; bottom: 16px; top: auto;
            width: auto; font-size: 0.95rem;
        }}
        .hint-chip:focus::after {{
            content: attr(data-hint); position: fixed; left: 16px; right: 16px;
            bottom: 16px; z-index: 1000; padding: 10px 12px; border-radius: 10px;
            white-space: normal; background: {palette["card"]};
            border: 1px solid {palette["card_border"]}; color: {palette["strong_text"]};
            font-size: 0.95rem; font-weight: 400; line-height: 1.45;
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


def open_card(key, title=None, caption=None, hint=None, kpi=None):
    """A rounded card; use it with 'with'. The key must be unique on the page.

    hint, when given, is a short explanation in plain words that appears when
    the mouse passes over the ⓘ next to the title. kpi, when given, adds a link
    «¿Cómo se calcula?» to that indicator in the project page.
    """
    card = st.container(key=f"card_{key}")
    hint_icon = build_hint_icon(hint) if hint else ""
    kpi_link = build_kpi_link(kpi) if kpi else ""
    if title or hint:
        card.markdown(f'<div class="card-title">{html.escape(title or "")}{hint_icon}'
                      f'{kpi_link}</div>', unsafe_allow_html=True)
    if caption:
        card.caption(caption)
    return card


def build_hint_icon(hint):
    """An ⓘ that shows a short explanation when the mouse passes over it, or when
    it is tapped on a phone (tabindex makes it focusable)."""
    plain_hint = html.escape(hint.replace("**", ""), quote=True)
    return (f'<span class="hint" tabindex="0" role="button" aria-label="{plain_hint}" '
            f'data-hint="{plain_hint}">ⓘ</span>')


def build_page_address(page_title, tab=None, kpi=None):
    """Relative address of a page, a project tab or a KPI card.

    A page that only the data team profile shows takes that profile with it.
    """
    parameters = {}
    if page_title not in PAGES_BY_PROFILE[PROFILE_ANALYST]:
        parameters[PROFILE_PARAMETER] = PROFILE_DATA_TEAM
    if tab:
        parameters[TAB_PARAMETER] = tab
    if kpi:
        parameters[KPI_PARAMETER] = kpi
    query = f"?{urlencode(parameters)}" if parameters else ""
    return PAGE_PATHS[page_title] + query


def build_link_html(text, address):
    """A link that opens in the same tab, with already-escaped text."""
    return f'<a href="{html.escape(address)}" target="_self">{html.escape(text)}</a>'


def build_kpi_link(kpi):
    """«¿Cómo se calcula?»: opens the card of the indicator in the project page."""
    address = build_page_address(PAGE_PROJECT, PROJECT_TAB_KPI, kpi)
    return f'<span class="kpi-link">{build_link_html("¿Cómo se calcula?", address)}</span>'


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
    """Changes when the weekly job saves a new database, so cached data is read again."""
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
                   "Cuánto más paga el consumidor que el mayorista.", hint=MEDIAN_MARGIN_HINT,
                   kpi="K1"):
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
                   hint=REGIONAL_INDEX_HINT, kpi="K3"):
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
                   hint=ALERTS_HINT, kpi="K6"):
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
@st.cache_data
def read_cached_rule_evidence(database_version):
    """Real figure of each quality rule, read once per database."""
    return project.read_rule_evidence()


def read_week_alert_count():
    """Number of K6 alerts in the latest week with prices."""
    alert_rows = read_price_alerts()
    latest_week = read_indicator("k6_national_weekly_price")["week_start"].max()
    return int((alert_rows["week_start"] == latest_week).sum())


def show_small_figure(label, value_text):
    """A label and a value, smaller than a key figure card."""
    st.markdown(f'<div class="kpi-label">{html.escape(label)}</div>'
                f'<div class="card-title">{html.escape(value_text)}</div>',
                unsafe_allow_html=True)


def show_pipeline_hook(mode):
    """Mini diagram of the pipeline with the real state of the latest run."""
    step_states, pipeline_run = read_latest_pipeline_steps()
    latest_load = read_latest_run()
    manifest = read_download_manifest()
    st.image(architecture.build_mini_journey_svg(
        build_journey_states(step_states, pipeline_run, latest_load, manifest),
        build_journey_figures(manifest, pipeline_run, latest_load), mode),
        use_container_width=True)


def show_project_value():
    """Three sentences and the main figures, all read now."""
    st.markdown(project.read_section(project.read_document(project.PROJECT_GUIDE_FILE),
                                     "Resumen"))
    keys_with_margin, consumer_keys = read_match_coverage()
    figures = [("Precios semanales cargados",
                charts.format_thousands(read_indicator("quality_flag_counts")
                                        ["weekly_prices"].sum())),
               ("Datos de ODEPA", describe_years(read_download_manifest())),
               ("Cobertura del cruce (K7)", f"{keys_with_margin} de {consumer_keys} claves"),
               ("Alertas de la última semana (K6)", str(read_week_alert_count()))]
    for column, (label, value_text) in zip(st.columns(len(figures)), figures):
        with column:
            show_small_figure(label, value_text)


def list_journey_steps(journey):
    """(text, address) of each stop of a guided tour of the project."""
    tabs = {tab: build_page_address(PAGE_PROJECT, tab) for tab in PROJECT_TABS}
    journeys = {
        JOURNEY_MANAGER: [("Panel", build_page_address(PAGE_OVERVIEW)),
                          ("Alertas", build_page_address(PAGE_ALERTS)),
                          ("KPI y cálculos", tabs[PROJECT_TAB_KPI])],
        JOURNEY_ANALYST: [("Idea de negocio", tabs[PROJECT_TAB_IDEA]),
                          ("KPI y cálculos", tabs[PROJECT_TAB_KPI]),
                          ("Reglas de calidad", tabs[PROJECT_TAB_RULES]),
                          ("Decisiones y método", tabs[PROJECT_TAB_DECISIONS])],
        JOURNEY_TECHNICAL: [("Pipeline", build_page_address(PAGE_ARCHITECTURE)),
                            ("Código y consultas SQL", tabs[PROJECT_TAB_CODE]),
                            ("Centro de control", build_page_address(PAGE_CONTROL))],
    }
    return journeys[journey]


def show_journeys():
    """Three guided tours; the chosen one shows its stops as links, in order."""
    journey = st.segmented_control("Elige tu recorrido",
                                   [JOURNEY_MANAGER, JOURNEY_ANALYST, JOURNEY_TECHNICAL],
                                   key="journey")
    if not journey:
        return
    stops = [f"{number}. {build_link_html(text, address)}"
             for number, (text, address) in enumerate(list_journey_steps(journey), start=1)]
    if journey == JOURNEY_MANAGER:
        stops.append(f"{len(stops) + 1}. Hallazgos: se publican cuando estén verificados.")
    st.markdown(" &nbsp;→&nbsp; ".join(stops), unsafe_allow_html=True)


def show_start_here(mode):
    """Inverted pyramid: the real pipeline, the value, then the guided tours."""
    with open_card("start_here", "Empieza aquí"):
        show_pipeline_hook(mode)
        show_project_value()
        show_journeys()


def build_question_rows():
    """Table cells: question number, question, page that answers it and its state."""
    rows = []
    for number, (question, page, state, scope) in enumerate(BUSINESS_QUESTIONS, start=1):
        state_text, kind = QUESTION_STATES[state]
        rows.append([f"P{number}", html.escape(question), html.escape(page),
                     build_chip(state_text, kind, scope)])
    return rows


def show_business_idea_tab(mode):
    """The business idea: the problem, who it is for and the questions it answers."""
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


def show_sources_tab(mode):
    """Both ODEPA sources, how they are matched and the real match coverage."""
    text_column, figure_column = st.columns([3, 1])
    with text_column, open_card("sources_text", "Dos fuentes, una clave"):
        st.markdown(project.read_section(project.read_document(project.PROJECT_GUIDE_FILE),
                                         "Fuentes y cruces"))
    keys_with_margin, consumer_keys = read_match_coverage()
    with figure_column, open_card("sources_coverage", "Cobertura del cruce", kpi="K7"):
        st.markdown(f'<div class="kpi-value">{keys_with_margin} de {consumer_keys}</div>'
                    f'<div class="kpi-note">claves de frutas y verduras del consumidor con '
                    f'margen ({charts.format_percent(keys_with_margin / consumer_keys * 100)})'
                    f'</div>', unsafe_allow_html=True)


def show_model_tab(mode):
    """Star model of the data warehouse with the real rows of each table."""
    row_counts = project.count_table_rows()
    definitions = project.parse_definitions(project.read_section(
        project.read_document(project.PROJECT_GUIDE_FILE), "Modelo de datos"))
    diagram_column, table_column = st.columns([2, 3])
    with diagram_column, open_card("model_diagram", "Modelo estrella"):
        st.graphviz_chart(project.build_star_diagram(row_counts, mode),
                          use_container_width=True)
    with table_column, open_card("model_tables", "Tablas de datos.db"):
        st.markdown(build_html_table(
            ["Tabla", "Filas", "Qué guarda"],
            [[f"<code>{table}</code>", charts.format_thousands(row_counts[table]),
              html.escape(definitions[table])] for table in project.TABLE_NAMES]),
            unsafe_allow_html=True)
        with st.expander("Ver etl/schema.sql"):
            st.code(project.read_document(project.SCHEMA_FILE), language="sql")


def build_kpi_examples():
    """{KPI: steps of its real example}, computed from the current database."""
    margin_rows = read_indicator("k1_margin")
    keys_with_margin, consumer_keys = read_match_coverage()
    return {"K1": project.build_k1_example(margin_rows),
            "K2": project.build_k2_example(read_indicator("k2_channel_gap")),
            "K3": project.build_k3_example(read_indicator("k3_regional_index")),
            "K4": project.build_k4_example(read_indicator("k4_seasonal_index")),
            "K5": project.build_k5_example(margin_rows),
            "K6": project.build_k6_example(read_price_alerts()),
            "K7": project.build_k7_example(keys_with_margin, consumer_keys),
            "K8": project.build_k8_example(read_latest_run(),
                                           read_indicator("k8_rejected_rows"))}


def read_kpi_query(query_name):
    """(SQL text, file it lives in) of the query behind a KPI."""
    if query_name == project.MATCH_COVERAGE_QUERY_NAME:
        return etl.MATCH_COVERAGE_QUERY.strip(), "etl/etl.py"
    return queries.load_queries()[query_name].strip(), "bi/queries.sql"


def show_kpi_card(indicator, guide_row, question, example_steps, is_requested):
    """One KPI: question, formula in words, real example, its SQL and where to see it."""
    kpi = indicator["ID"]
    with open_card(f"kpi_{kpi}", f"{kpi} · {indicator['Indicador']}"):
        if is_requested:
            st.markdown(build_chip("Llegaste desde un gráfico del panel", "running"),
                        unsafe_allow_html=True)
        st.markdown(f"**Pregunta:** {question}  \n**En palabras:** {guide_row['En palabras']}"
                    f"  \n**Fórmula:** {indicator['Fórmula']}")
        if example_steps:
            st.markdown("**Ejemplo real, paso a paso:**  \n"
                        + "  \n".join(f"{number}. {step}"
                                      for number, step in enumerate(example_steps, start=1)))
        sql, file_name = read_kpi_query(guide_row["Consulta"])
        with st.expander(f"Ver la consulta SQL ({guide_row['Consulta']})"):
            st.code(sql, language="sql")
            st.markdown(build_link_html(f"Abrir {file_name} en GitHub",
                                        project.build_github_url(file_name)),
                        unsafe_allow_html=True)
        st.markdown("Se ve en: " + build_link_html(
            guide_row["Página"], build_page_address(guide_row["Página"])),
            unsafe_allow_html=True)


def show_kpi_tab(mode):
    """One card per indicator K1 to K8, with the one asked for from a chart first."""
    questions = {row["#"]: row["Pregunta"]
                 for row in project.read_design_table(project.QUESTIONS_HEADING)}
    guide_rows = {row["KPI"]: row for row in project.read_guide_table("KPI")}
    indicators = project.read_design_table(project.INDICATORS_HEADING)
    requested_kpi = st.query_params.get(KPI_PARAMETER)
    indicators.sort(key=lambda indicator: indicator["ID"] != requested_kpi)
    examples = build_kpi_examples()
    for indicator in indicators:
        question = questions.get(indicator["Pregunta"], "¿La carga de datos es confiable?")
        show_kpi_card(indicator, guide_rows[indicator["ID"]], question,
                      examples[indicator["ID"]], indicator["ID"] == requested_kpi)


def describe_rule_evidence(rule):
    """Real figure of one rule from datos.db, or a dash when the base cannot show it."""
    if rule == "RN-06":
        return project.describe_margin_evidence(read_indicator("k1_margin"))
    if rule == "RN-11":
        return project.describe_rejection_evidence(read_indicator("k8_rejected_rows"),
                                                   project.read_rejection_example())
    return read_cached_rule_evidence(get_database_version()).get(rule, "—")


def show_rules_tab(mode):
    """RN-01 to RN-14: what each does with a row, with real evidence; details folded."""
    rules = project.read_design_table(project.RULES_HEADING)
    guide_rows = {row["Regla"]: row for row in project.read_guide_table("Reglas de calidad")}
    with open_card("rules_table", "Reglas de calidad y su evidencia en la base"):
        st.markdown(build_html_table(
            ["Regla", "Qué hace con la fila", "Evidencia real en datos.db"],
            [[rule["ID"], html.escape(guide_rows[rule["ID"]]["Qué hace con la fila"]),
              html.escape(describe_rule_evidence(rule["ID"]))] for rule in rules]),
            unsafe_allow_html=True)
    for rule in rules:
        guide_row = guide_rows[rule["ID"]]
        with st.expander(f"{rule['ID']} · por qué y regla completa"):
            st.markdown(f"**Regla:** {rule['Regla']}  \n**Por qué:** {guide_row['Por qué']}")
            if guide_row["Ejemplo documentado"] != "—":
                st.markdown(f"**Ejemplo documentado:** {guide_row['Ejemplo documentado']}")


def show_sections_folded(text, first_open=True):
    """Each '## ' section of a document in its own box; only the first one open."""
    for position, (heading, body) in enumerate(project.split_sections(text)):
        with st.expander(heading, expanded=first_open and position == 0):
            st.markdown(body)


def show_manual_tab(mode):
    """docs/MANUAL.md, one section per box."""
    show_sections_folded(project.read_document(project.MANUAL_FILE))


def show_decisions_tab(mode):
    """docs/DECISIONES.md, one decision per box."""
    decisions = project.list_decisions()
    st.subheader("Registro de decisiones")
    st.caption(f"{len(decisions)} decisiones, cada una con qué se decidió, por qué, qué se "
               "descartó y qué se pierde.")
    for title, body in decisions:
        with st.expander(title):
            st.markdown(body)


def show_query_result_button(key, sql, parameters=()):
    """Button that runs a query on the read-only database and shows 20 rows."""
    if st.button("Ver resultado", key=f"preview_{key}", icon=":material/play_arrow:"):
        st.dataframe(project.run_preview(sql, parameters), hide_index=True,
                     use_container_width=True)
        st.caption(f"Primeras {project.PREVIEW_ROW_COUNT} filas como máximo, en solo lectura.")


def show_named_query(query):
    """One query of bi/queries.sql: question, clauses, page, SQL (and Python) and result."""
    with st.expander(f"{query['name']} · {query['question']}"):
        chips = " ".join(build_chip(clause, "neutral") for clause in query["clauses"])
        page = query["page"]
        st.markdown(f"{chips}  \nSe usa en: "
                    f"{build_link_html(page, build_page_address(page))}",
                    unsafe_allow_html=True)
        if query["python"]:
            sql_tab, python_tab = st.tabs(["SQL", "Python"])
            sql_tab.code(query["sql"], language="sql")
            python_tab.code("\n\n".join(query["python"]), language="python")
            st.caption("Ambas versiones dan el mismo resultado (verificado por test).")
        else:
            st.code(query["sql"], language="sql")
        show_query_result_button(query["name"], query["sql"])


def show_extra_queries():
    """SQL that lives outside bi/queries.sql: K7, the schema and a Consultas example."""
    with st.expander(f"{project.MATCH_COVERAGE_QUERY_NAME} · ¿Cuántas claves tienen margen? "
                     "(vive en etl/etl.py)"):
        st.code(etl.MATCH_COVERAGE_QUERY.strip(), language="sql")
        show_query_result_button(project.MATCH_COVERAGE_QUERY_NAME, etl.MATCH_COVERAGE_QUERY)
    with st.expander("etl/schema.sql · creación de las tablas"):
        st.code(project.read_document(project.SCHEMA_FILE), language="sql")
    explorer_sql, explorer_parameters = project.build_explorer_example()
    with st.expander("Ejemplo de la página Consultas · tomate en feria y supermercado"):
        st.code(explorer_sql, language="sql")
        st.caption(f"Valores de cada «?», enviados aparte del texto: {explorer_parameters}")
        show_query_result_button("explorer_example", explorer_sql, explorer_parameters)


def show_repository_files():
    """Every file of the README tree with its sentence and its link on GitHub."""
    rows = [[build_link_html(path, address) if address else html.escape(path),
             html.escape(description)]
            for path, description, address in project.list_repository_files()]
    st.markdown(build_html_table(["Archivo", "Qué hace"], rows), unsafe_allow_html=True)
    st.markdown(f"{build_link_html('Historial de commits', project.COMMITS_URL)} · "
                f"{build_link_html('Ejecuciones en GitHub Actions', project.ACTIONS_URL)}",
                unsafe_allow_html=True)


def show_code_tab(mode):
    """SQL catalog (with Python where it exists) and the files of the repository."""
    named_queries = project.list_named_queries()
    with open_card("code_queries", "Consultas SQL"):
        st.caption(f"Las {len(named_queries)} consultas con nombre de bi/queries.sql, leídas "
                   "del archivo. Las etiquetas son las cláusulas que cada una usa.")
        for query in named_queries:
            show_named_query(query)
        show_extra_queries()
    with open_card("code_files", "Archivos"):
        show_repository_files()


def show_project_page(mode):
    """The project explained by itself: the real pipeline first, the detail in tabs."""
    show_page_header("El proyecto", "Qué problema resuelve, cómo funciona y cómo se "
                     "calcula cada cifra.")
    show_start_here(mode)
    tabs = st.tabs(PROJECT_TABS, key=TAB_PARAMETER, bind="query-params")
    tab_contents = [show_business_idea_tab, show_sources_tab, show_model_tab, show_kpi_tab,
                    show_rules_tab, show_manual_tab, show_decisions_tab, show_code_tab]
    for tab, show_tab_content in zip(tabs, tab_contents):
        with tab:
            show_tab_content(mode)
# endregion


# region Margins page
def show_margins_page(mode):
    """K1, margin between the wholesale and each consumer channel, and K5, its lag."""
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
    with open_card("margin_trend", "Margen por semana", hint=MARGIN_TREND_HINT, kpi="K1"):
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
    show_lag_card(rows, mode)
    st.caption(NOMINAL_PRICES_TEXT)


def build_lag_bar_rows(correlations, best_lag, mode):
    """Bars of K5: one per lag, the chosen lag in the accent color."""
    correlations = correlations.dropna(subset=["correlation"])
    palette = charts.get_palette(mode)
    bar_rows = pd.DataFrame({
        "label": [f"{weeks} semanas" for weeks in correlations["lag_weeks"]],
        "value": correlations["correlation"].to_numpy(),
        "value_label": correlations["correlation"].map(charts.format_index).to_numpy(),
        "meaning": [f"Correlación con {pairs} pares de cambios semanales"
                    for pairs in correlations["pair_count"]]})
    colors = [palette["accent"] if weeks == best_lag else palette["reference"]
              for weeks in correlations["lag_weeks"]]
    return bar_rows, colors


def show_lag_card(rows, mode):
    """Card: K5, weeks the consumer price takes to follow the wholesale price."""
    with open_card("lag", "Rezago mayorista → consumidor (K5)", hint=LAG_HINT, kpi="K5"):
        channel = choose_value("Canal", rows["channel"].unique(), DEFAULT_CHANNEL,
                               key="lag_channel")
        series_rows = rows[rows["channel"] == channel]
        if not lag.has_enough_weeks(series_rows):
            st.info(f"K5 necesita {lag.MINIMUM_WEEKS} semanas con ambos precios; esta "
                    f"selección tiene {series_rows['week_start'].nunique()}.")
            return
        correlations = lag.correlate_by_lag(series_rows)
        best = lag.find_lag(correlations)
        if best is None:
            st.info("No hay cambios semanales suficientes para calcular el rezago.")
            return
        best_lag, correlation, pair_count = best
        if lag.is_clear_relation(correlation, pair_count):
            lag_text = f"{best_lag} semanas"
        else:
            # The highest of several weak correlations is noise, not a lag.
            lag_text = "Sin relación clara"
        st.markdown(f'<div class="kpi-value">{lag_text}</div>'
                    f'<div class="kpi-note">correlación más alta '
                    f'{charts.format_index(correlation)} en {channel}, con {pair_count} '
                    f'pares de cambios semanales</div>', unsafe_allow_html=True)
        bar_rows, colors = build_lag_bar_rows(correlations, best_lag, mode)
        show_chart(charts.draw_horizontal_bars(bar_rows, "Correlación", mode, colors,
                                               reference_value=0))
        st.caption(LAG_NOTE)
# endregion


# region Channels and regions page
def show_channel_gaps(rows, mode):
    """Card: K2, average price gap of each channel against a reference channel."""
    with open_card("channel_gaps", "Diferencia entre canales", hint=CHANNEL_GAP_HINT,
                   kpi="K2"):
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
    with open_card("regional_index", "Precio por región", hint=REGIONAL_INDEX_HINT,
                   kpi="K3"):
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
                     "del año. Con varios años se ve qué semanas son caras o baratas cada año.")
    rows = choose_product_rows(read_indicator("k4_seasonal_index"))
    channel = choose_value("Canal", rows["channel"].unique(), DEFAULT_CHANNEL)
    rows = rows[rows["channel"] == channel]
    index_column, price_column = st.columns(2)
    with index_column, open_card("seasonal_index", "Índice estacional",
                                 "1 = precio promedio del año.", hint=SEASONAL_INDEX_HINT,
                                 kpi="K4"):
        index_rows = rows[["week_start", "seasonal_index"]].rename(
            columns={"seasonal_index": "value"})
        show_chart(charts.draw_single_weekly_area(
            index_rows, "Índice", index_rows["value"].map(charts.format_index), mode,
            reference_value=1))
    with price_column, open_card("national_price", "Precio nacional por semana",
                                 hint=NATIONAL_PRICE_HINT, kpi="K4"):
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
                   "Rojo: subió. Azul: bajó.", hint=ALERTS_HINT, kpi="K6"):
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


# region Consultas page
@st.cache_data
def read_cached_price_options(database_version):
    """Real values for the price filters, read once per database."""
    return explorer.read_price_options()


@st.cache_data
def read_cached_price_rows(filters, database_version):
    """Weekly prices that pass the filters, kept until the database changes."""
    return explorer.read_price_rows(filters)


def read_explorer_rows(view, filters):
    """Rows of the chosen view before grouping, with the measured value in 'value'."""
    if view == explorer.VIEW_PRICES:
        return read_cached_price_rows(filters, get_database_version())
    if view == explorer.VIEW_MARGINS:
        return explorer.prepare_margin_rows(read_indicator("k1_margin"))
    return explorer.prepare_alert_rows(read_price_alerts())


def list_filter_options(view):
    """Values offered in each filter of the view, and its first and last week."""
    if view == explorer.VIEW_PRICES:
        return read_cached_price_options(get_database_version())
    rows = read_explorer_rows(view, {})
    options = {name: sorted(rows[column].unique())
               for name, column in explorer.LIST_FILTER_COLUMNS.items() if column in rows.columns}
    options[explorer.FILTER_FIRST_WEEK] = rows["week_start"].min().date()
    options[explorer.FILTER_LAST_WEEK] = rows["week_start"].max().date()
    return options


def choose_explorer_view():
    """Step 1: what to look at."""
    with open_card("explorer_view", "1 · Vista", hint=EXPLORER_VIEW_HINT):
        return st.radio("Vista", explorer.VIEWS, horizontal=True,
                        label_visibility="collapsed", key="explorer_view")


def choose_explorer_groups(view):
    """Step 2: one check box per grouping the view allows."""
    with open_card("explorer_groups", "2 · Agrupar por", hint=EXPLORER_GROUP_HINT):
        labels = explorer.GROUPS_BY_VIEW[view]
        return [label for column, label in zip(st.columns(len(labels)), labels)
                if column.checkbox(label, value=label in EXPLORER_DEFAULT_GROUPS,
                                   key=f"explorer_group_{view}_{label}")]


def choose_week_range(options, view):
    """Date range of the weeks; while the reader picks it, it may have one end only."""
    chosen_weeks = st.date_input(
        "Semanas entre", (options[explorer.FILTER_FIRST_WEEK],
                          options[explorer.FILTER_LAST_WEEK]),
        min_value=options[explorer.FILTER_FIRST_WEEK],
        max_value=options[explorer.FILTER_LAST_WEEK], format="DD-MM-YYYY",
        key=f"explorer_weeks_{view}")
    week_range = {explorer.FILTER_FIRST_WEEK: chosen_weeks[0]} if chosen_weeks else {}
    if len(chosen_weeks) == 2:
        week_range[explorer.FILTER_LAST_WEEK] = chosen_weeks[1]
    return week_range


def choose_explorer_filters(view):
    """Step 3: lists with the real values of the database, and the date range."""
    options = list_filter_options(view)
    filter_names = [name for name in explorer.LIST_FILTER_COLUMNS if name in options]
    with open_card("explorer_filters", "3 · Filtros", hint=EXPLORER_FILTER_HINT):
        columns = st.columns(len(filter_names) + 1)
        # The view is part of each key: every view offers its own values.
        filters = {name: column.multiselect(EXPLORER_FILTER_LABELS[name], options[name],
                                            placeholder="Todos",
                                            key=f"explorer_{name}_{view}")
                   for column, name in zip(columns, filter_names)}
        with columns[-1]:
            filters.update(choose_week_range(options, view))
    return filters


def choose_explorer_measure():
    """Step 4: how to summarize each group."""
    with open_card("explorer_measure", "4 · Medida", hint=EXPLORER_MEASURE_HINT):
        return st.radio("Medida", list(explorer.MEASURES), horizontal=True,
                        label_visibility="collapsed", key="explorer_measure")


def show_explorer_chart(view, result, mode):
    """Lines when the result is grouped by week or month, bars otherwise."""
    is_money = view == explorer.VIEW_PRICES
    value_title = explorer.VALUE_TITLES[view].capitalize()
    if explorer.find_time_column(result):
        line_rows = explorer.prepare_line_rows(result)
        series_count = line_rows["channel"].nunique()
        if series_count > explorer.CHART_MAXIMUM_SERIES:
            st.info(f"El gráfico admite hasta {explorer.CHART_MAXIMUM_SERIES} líneas y este "
                    f"resultado tiene {series_count}. Filtra o marca menos casillas.")
            return
        show_chart(charts.draw_weekly_lines(line_rows, value_title,
                                            format_explorer_values(line_rows["value"], is_money),
                                            mode, is_money))
        return
    bar_rows = explorer.prepare_bar_rows(result)
    bar_rows["value_label"] = format_explorer_values(bar_rows["value"], is_money)
    if len(result) > len(bar_rows):
        st.caption(f"El gráfico muestra los {len(bar_rows)} valores más altos.")
    show_chart(charts.draw_horizontal_bars(bar_rows, value_title, mode))


def format_explorer_values(values, is_money):
    """'$ 1.234' for prices, '12,5 %' for margins and variations."""
    if is_money:
        return "$ " + values.map(charts.format_thousands)
    return values.map(charts.format_percent)


def show_explorer_result(view, result, measure_label, mode):
    """Result card: table or chart, at most 1.000 rows on screen, and the full CSV."""
    with open_card("explorer_result", "Resultado", hint=EXPLORER_RESULT_HINT):
        if result.empty:
            st.info("Esta combinación no devuelve filas. Prueba con menos filtros o con un "
                    "rango de semanas más amplio.")
            return
        shown_rows, is_truncated = explorer.limit_rows(result)
        if is_truncated:
            st.warning(f"El resultado tiene {charts.format_thousands(len(result))} filas; se "
                       f"muestran las primeras {charts.format_thousands(len(shown_rows))}. "
                       "Descarga el CSV para verlas todas.")
        else:
            st.caption(f"{charts.format_thousands(len(result))} filas.")
        if st.toggle("Ver como gráfico", key="explorer_chart"):
            show_explorer_chart(view, result, mode)
        else:
            st.dataframe(explorer.name_columns_for_reader(shown_rows, view, measure_label),
                         hide_index=True, use_container_width=True)
        # utf-8-sig lets Excel read the accents of the Spanish titles.
        csv_text = explorer.name_columns_for_reader(result, view, measure_label).to_csv(
            index=False).encode("utf-8-sig")
        st.download_button("Descargar CSV", csv_text, file_name="consulta.csv",
                           mime="text/csv", icon=":material/download:")


def show_explorer_sql(view, filters, group_labels, measure_label):
    """Closed box with the SQL behind the result, so anyone can repeat it."""
    with st.expander("Ver SQL"):
        if view == explorer.VIEW_PRICES:
            sql, parameters = explorer.build_price_query(filters)
            st.code(sql, language="sql")
            st.caption(f"Valores de cada «?», enviados aparte del texto: {parameters}")
        else:
            st.code(queries.load_queries()[EXPLORER_BASE_QUERIES[view]], language="sql")
            st.caption("Los filtros se aplican después, con pandas."
                       + (" Las alertas se calculan sobre esta serie en bi/alerts.py."
                          if view == explorer.VIEW_ALERTS else ""))
        groups_text = ", ".join(group_labels).lower() or "nada (un solo total)"
        st.caption(f"Luego se agrupa por {groups_text} y se calcula {measure_label.lower()} "
                   "con pandas, porque SQLite no tiene mediana.")


def show_explorer_page(mode):
    """Query builder: the reader picks a view, groups, filters and a measure with clicks."""
    show_page_header("Consultas", "Arma tu propia consulta con clics: qué ver, cómo "
                     "agruparlo, qué filtrar y cómo resumirlo.")
    view_column, group_column = st.columns([2, 3])
    with view_column:
        view = choose_explorer_view()
    with group_column:
        group_labels = choose_explorer_groups(view)
    filter_column, measure_column = st.columns([3, 1])
    with filter_column:
        filters = choose_explorer_filters(view)
    with measure_column:
        measure_label = choose_explorer_measure()
    if explorer.TIME_GROUPS <= set(group_labels):
        st.warning("Elige semana o mes, no los dos a la vez.")
        return
    result = explorer.build_result(view, read_explorer_rows(view, filters), group_labels,
                                   measure_label, filters)
    show_explorer_result(view, result, measure_label, mode)
    show_explorer_sql(view, filters, group_labels, measure_label)
# endregion


# region Control center page
def get_secret(name):
    """A dashboard secret, or None when it is not configured."""
    try:
        return st.secrets.get(name)
    except Exception:  # no secrets file at all
        return None


@st.cache_data(ttl=30)
def read_pipeline_runs():
    """(latest runs, error text). Kept 30 seconds so GitHub is not asked on every click."""
    try:
        return control.list_workflow_runs(get_secret(SECRET_GITHUB_TOKEN),
                                          RUN_HISTORY_COUNT), ""
    except Exception as error:  # GitHub unreachable or refused
        return [], str(error)


def build_run_chip(state):
    """Chip for a pipeline run: Éxito, Falla or En curso."""
    texts = {control.RUN_OK: ("Éxito", "ok"), control.RUN_FAILED: ("Falla", "failed"),
             control.RUN_IN_PROGRESS: ("En curso", "running")}
    text, kind = texts.get(state, ("Omitido", "neutral"))
    return build_chip(text, kind)


def show_pipeline_status(runs):
    """Three cards: latest run, next automatic run and latest data load."""
    status_column, next_column, data_column = st.columns(3)
    with status_column, open_card("pipeline_latest"):
        st.markdown('<div class="kpi-label">Última ejecución del pipeline</div>',
                    unsafe_allow_html=True)
        if runs:
            latest = runs[0]
            st.markdown(f'<div class="kpi-value">{format_chile_time(latest["started_at"])}</div>'
                        f'{build_run_chip(latest["state"])}'
                        f'<span class="kpi-note"> {latest["trigger"]}</span>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="kpi-value">sin datos</div>', unsafe_allow_html=True)
    with next_column, open_card("pipeline_next"):
        next_run = control.calculate_next_scheduled_run(datetime.now(timezone.utc))
        st.markdown('<div class="kpi-label">Próxima ejecución automática</div>'
                    f'<div class="kpi-value">{format_chile_time(next_run)}</div>'
                    '<div class="kpi-note">Cada martes, sin intervención</div>',
                    unsafe_allow_html=True)
    with data_column, open_card("pipeline_data"):
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
        return "⏳ Preparando la ejecución…"
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


def run_pipeline_now(token):
    """Start the pipeline and show its steps live until it finishes."""
    requested_at = datetime.now(timezone.utc)
    control.start_workflow_run(token)
    with st.status("El pipeline se está ejecutando…", expanded=True) as status_box:
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
            status_box.update(label="La ejecución terminó con una falla. Los datos anteriores "
                              "siguen intactos.", state="error")
    read_pipeline_runs.clear()


def show_run_now_card():
    """Card with the button that starts the pipeline, protected by an access code."""
    with open_card("run_now", "Ejecutar ahora",
                   "Descarga los datos de ODEPA, los limpia, los prueba y actualiza el "
                   "panel. Tarda alrededor de un minuto."):
        token = get_secret(SECRET_GITHUB_TOKEN)
        access_code = get_secret(SECRET_CONTROL_CODE)
        if not token or not access_code:
            st.info("El botón se activa cuando la autora configura su clave de GitHub y "
                    "su código de acceso en los secretos del panel. Mientras tanto, el "
                    "workflow se puede lanzar desde GitHub.")
            st.link_button("Abrir el workflow en GitHub", control.WORKFLOW_PAGE_URL,
                           icon=":material/open_in_new:")
            return
        typed_code = st.text_input("Código de acceso", type="password")
        if st.button("Ejecutar ahora", type="primary", icon=":material/play_arrow:"):
            if not hmac.compare_digest(typed_code, access_code):
                st.error("Código de acceso incorrecto.")
                return
            run_pipeline_now(token)


def show_run_history(runs, error_text):
    """Card: latest pipeline runs with their state."""
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
    """The weekly pipeline: its state, its history and a button to run it now."""
    show_page_header("Centro de control", "El pipeline descarga, revisa y guarda los datos "
                     "cada martes. Aquí ves su estado y puedes lanzarlo cuando quieras.")
    runs, error_text = read_pipeline_runs()
    show_pipeline_status(runs)
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
def read_latest_pipeline_steps():
    """(state of each step by Spanish name, latest pipeline run) from GitHub, or ({}, None)."""
    runs, _ = read_pipeline_runs()
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


def build_journey_states(step_states, pipeline_run, latest_load, manifest):
    """Real state of each step: from the latest pipeline run and the current database."""
    load_state = (control.RUN_OK if latest_load["status"] == etl.STATUS_LOADED
                  else control.RUN_FAILED)
    return {
        "sources": control.RUN_OK if manifest else architecture.STATE_UNKNOWN,
        "download": get_step_state(step_states, "Download the ODEPA files"),
        "etl": get_step_state(step_states, "Run the ETL"),
        "tests": get_step_state(step_states, "Run the tests against the new database"),
        "report": get_step_state(step_states, "Publish the weekly report"),
        "workflow": pipeline_run["state"] if pipeline_run else architecture.STATE_UNKNOWN,
        "load": load_state,
        "panel": control.RUN_OK,
    }


def build_journey_figures(manifest, pipeline_run, latest_load):
    """Short texts shown under the steps, all from real data."""
    weekly_prices = read_indicator("quality_flag_counts")["weekly_prices"].sum()
    latest_week = read_indicator("k6_national_weekly_price")["week_start"].max()
    loaded_at = to_chile_time(parse_run_start(latest_load["started_at"]))
    next_run = control.calculate_next_scheduled_run(datetime.now(timezone.utc))
    last_run = (f"última {to_chile_time(pipeline_run['started_at']):%d-%m %H:%M}"
                if pipeline_run else "sin datos del workflow")
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
    show_page_header("Pipeline", "El recorrido de los datos, de ODEPA a este panel. "
                     "Los puntos de color muestran el estado real de cada paso.")
    step_states, pipeline_run = read_latest_pipeline_steps()
    latest_load = read_latest_run()
    manifest = read_download_manifest()
    with open_card("journey", hint=ARCHITECTURE_HINT):
        st.image(architecture.build_journey_svg(
            build_journey_states(step_states, pipeline_run, latest_load, manifest),
            build_journey_figures(manifest, pipeline_run, latest_load), mode),
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
                    'paso: estado de la última ejecución del pipeline y de la base actual.'
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
    PAGE_EXPLORER: show_explorer_page,
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
    profile = st.sidebar.selectbox("¿Quién consulta?", list(PAGES_BY_PROFILE),
                                   key=PROFILE_PARAMETER, bind="query-params")
    pages = [build_page(title, position == 0)
             for position, title in enumerate(PAGES_BY_PROFILE[profile])]
    st.navigation(pages, position="sidebar").run()
    st.sidebar.caption("Fuente: ODEPA · actualización automática cada martes.")


if __name__ == "__main__":
    main()
# endregion
