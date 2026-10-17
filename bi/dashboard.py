"""Streamlit dashboard for the price monitor.

Run it with:  streamlit run bi/dashboard.py

It reads etl/datos.db through the named queries of bi/queries.sql, and the
state of the weekly pipeline through the GitHub API (bi/control.py).
Texts shown to the user are in Spanish; code and comments are in English.
The color modes and chart palettes live in bi/charts.py.
"""
import base64
import hmac
import html
import importlib
import inspect
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# region Imports of the project
# Streamlit runs this file as a script, so the project folder is added to the
# import path to reach the other modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import (alerts, price_context, architecture, charts, control, devops, data_browser, home_mockup, lag, market_charts, market_style, project, quality,  # noqa: E402
                queries, star_model, zoom)
from etl import etl  # noqa: E402
# endregion

# region Constants
# The menu is the project journey; every destination is directly accessible.
PAGE_HOME = "Dashboard"
PAGE_DATA = "Datos"
# The cover of the portfolio (C01): what the project is, in one screen, with real figures
# and a way into the dashboard and the code. The full definition is the view after it.
PAGE_COVER = "Portada"
COVER_NAME = "GreenOcean"
BRAND_GREEN_DARK = "#72e7ad"
BRAND_GREEN_LIGHT = "#167046"
PAGE_BUSINESS = "Definición del proyecto"
PAGE_DIAGRAMS = "Pipeline y arquitectura"
PAGE_ARCHITECTURE = "Modelo de datos"
PAGE_ANALYSIS = "Esta semana"
PAGE_GAP = "Brecha de precio"
PAGE_CHANNELS = "Canales y regiones"
PAGE_SEASONALITY = "Contexto del precio"
RETIRED_VIEWS = {"Histórico y estacionalidad": "Contexto del precio"}
PAGE_ALERTS = "Alertas"
PAGE_KPI = "Indicadores explicados"
PAGE_QUERIES = "Preguntas y resultados"
PAGE_CODE = "Código Python y SQL"
# «Consulta de datos» (Consulta por clics) is retired (C03): the catalog of questions
# answers with real results; its links and old addresses open the catalog.
PAGE_DATA_AND_CODE = PAGE_QUERIES
PAGE_DEVOPS = "DevOps y seguridad"
PAGE_OPERATIONS = "Monitoreo"
PAGE_RUNS = "Ejecuciones"
PAGE_RULES = "Reglas de calidad"
PAGE_MANUAL = "Manual"
PAGE_DECISIONS = "Decisiones"
PAGE_GLOSSARY = "Glosario"
PAGE_LINKS = "Enlaces"
PAGE_DOCUMENTATION = "Documentación"
# The three profile views of Documentación (D-110): one per reader, each its own
# sidebar child, folded by default like every other section.
PAGE_DOC_BI = "Business Intelligence"
PAGE_DOC_BA = "Business Analyst"
PAGE_DOC_IT = "IT y operación"
SECTION_RESOURCES = "Enlaces"
# The visit is a portfolio route, like a CV with its evidence: the project, then the
# dashboard, the code with its results and, for whoever wants more, the technical detail.
# Sources and links have one place of their own, out of the route (D-070).
SECTION_PROJECT = "El proyecto"
SECTION_KPI = "KPIs"
REPORT_WINDOW = "Dashboard"
SECTION_QUERIES = "Preguntas y resultados SQL"
SECTION_CODE = "Código del proyecto"
SECTION_TECHNICAL = "Arquitectura y operación"
SECTION_LINKS = "Documentación"
WINDOWS = {
    SECTION_PROJECT: [PAGE_COVER, PAGE_BUSINESS, PAGE_RULES],
    SECTION_KPI: [PAGE_KPI],
    REPORT_WINDOW: [PAGE_HOME, PAGE_DATA, PAGE_ANALYSIS, PAGE_GAP, PAGE_CHANNELS, PAGE_ALERTS,
                    PAGE_SEASONALITY],
    SECTION_QUERIES: [PAGE_QUERIES],
    SECTION_CODE: [PAGE_CODE],
    SECTION_TECHNICAL: [PAGE_DIAGRAMS, PAGE_ARCHITECTURE, PAGE_DEVOPS, PAGE_OPERATIONS, PAGE_RUNS],
    SECTION_LINKS: [PAGE_DOC_BI, PAGE_DOC_BA, PAGE_DOC_IT, PAGE_DOCUMENTATION, PAGE_GLOSSARY,
                    PAGE_MANUAL],
    SECTION_RESOURCES: [PAGE_LINKS],
}
ROUTE = [REPORT_WINDOW, SECTION_TECHNICAL, SECTION_CODE, SECTION_QUERIES, SECTION_PROJECT]
# The former KPI page remains as a hidden compatibility destination for old links;
# its business information now lives in the dashboard and documentation.
WINDOWS = {window: WINDOWS[window] for window in ROUTE + [SECTION_LINKS, SECTION_RESOURCES, SECTION_KPI]}
WINDOW_PATHS = {SECTION_PROJECT: "proyecto", REPORT_WINDOW: "dashboard", SECTION_KPI: "kpis",
                SECTION_QUERIES: "preguntas-y-resultados", SECTION_CODE: "codigo",
                SECTION_TECHNICAL: "arquitectura-y-operacion",
                SECTION_LINKS: "documentacion-y-enlaces", SECTION_RESOURCES: "enlaces"}
WINDOW_ICONS = {SECTION_PROJECT: ":material/assignment:", REPORT_WINDOW: ":material/dashboard:",
                SECTION_KPI: ":material/insights:",
                SECTION_QUERIES: ":material/query_stats:", SECTION_CODE: ":material/code:",
                SECTION_TECHNICAL: ":material/account_tree:", SECTION_LINKS: ":material/menu_book:", SECTION_RESOURCES: ":material/link:"}
ROUTE_LEADS = {SECTION_PROJECT: "qué problema resuelve y qué se construyó",
               SECTION_KPI: "qué mide cada KPI, cómo se calcula y qué límites tiene",
               REPORT_WINDOW: "los precios y cambios de la semana",
               SECTION_QUERIES: "cada pregunta, su resultado y el SQL que lo produce",
               SECTION_CODE: "los archivos reales, agrupados por su función",
               SECTION_TECHNICAL: "pipeline, modelo estrella, DevOps y operación"}
WINDOW_OF_VIEW = {view: window for window, views in WINDOWS.items() for view in views}
VIEW_PARAMETER = "vista"
# Session flag: the window being drawn is a report (Dashboard), so every view fits one
# screen, like a page of Looker or Power BI (D-067).
COMPACT_VIEW = "compact_view"
# Tile heights of a report page, in pixels: two rows fit a 1440 x 900 screen.
TILE_HEIGHT = 255
ALERTS_SCREEN_COUNT = 8
# A gap above +300 % does not compare the same thing: in street markets, which sell in
# bulk like the wholesale market, 99 % of the gaps stay under +253 %; above +300 % the
# consumer price is a packed format (supermarket trays of 250-500 g) against bulk
# wholesale (bins of 400 kilos, trays of 7 kilos). Out of the ranking and the median,
# listed apart, never deleted (D-068).
MAXIMUM_COMPARABLE_GAP = 3.0
# «Subió fuerte»: a weekly change above this share, in the sentence on top.
STRONG_CHANGE = 0.10
# The pulse shows three series by default; the reader adds the others.
PULSE_CHANNELS = ["Mayorista", "Feria libre", "Supermercado"]
# Filters of the whole report (D-069): one bar for every Dashboard view, kept while the
# reader moves with ◀ ▶. The product comes from a click (cross filter or drill-down).
ALL_VALUES = "Todas"
GLOBAL_FILTERS = {"group": "Grupo", "region": "Región", "week": "Semana"}
# Dashboard summary (D-072): a slider sets how many rows the ranking shows.
TOP_N_RANGE = (1, 100)
DEFAULT_TOP_N = 20
RANKING_TITLES = {"Mayores movimientos": "¿Qué precios cambiaron más?",
                  "Alzas": "¿Qué precios subieron más?", "Bajas": "¿Qué precios bajaron más?"}
# The trend keeps one or two curves: more lines on top of each other no longer read.
PULSE_MAXIMUM_CHANNELS = 2
GAP_MEANING = ("La brecha de precio compara el precio al consumidor con el mayorista: no "
               "mide ganancia ni descuenta costos.")
ALERT_MEANING = ("Una alerta señala un cambio poco habitual: invita a revisar, no prueba un "
                 "error ni explica su causa.")
NO_COMPARABLE_TEXT = "Sin datos comparables"
DASHBOARD_WEEKS = 26
# A channel or region of the territory map needs data in this share of the other axis.
MINIMUM_MAP_COVERAGE = 0.5
BAR_STEP = 22
# The groups of views before D-065, kept for the documents that name them.
NAVIGATION_GROUPS = WINDOWS
PAGES = [page for pages in NAVIGATION_GROUPS.values() for page in pages]
HOME_PAGE = PAGE_HOME
PAGE_ICONS = {
    PAGE_DOCUMENTATION: ":material/menu_book:",
    PAGE_DOC_BI: ":material/insights:", PAGE_DOC_BA: ":material/assignment:",
    PAGE_DOC_IT: ":material/build:",
    PAGE_HOME: ":material/dashboard:", PAGE_DATA: ":material/table_view:", PAGE_COVER: ":material/home:",
    PAGE_BUSINESS: ":material/assignment:",
    PAGE_DIAGRAMS: ":material/account_tree:", PAGE_ARCHITECTURE: ":material/schema:",
    PAGE_ANALYSIS: ":material/monitoring:", PAGE_GAP: ":material/compare_arrows:",
    PAGE_CHANNELS: ":material/storefront:", PAGE_SEASONALITY: ":material/calendar_month:",
    PAGE_ALERTS: ":material/notifications_active:", PAGE_KPI: ":material/insights:",
    PAGE_QUERIES: ":material/data_object:",
    PAGE_CODE: ":material/code:", PAGE_RULES: ":material/rule:", PAGE_DEVOPS: ":material/shield:",
    PAGE_OPERATIONS: ":material/health_and_safety:", PAGE_RUNS: ":material/play_circle:",
    PAGE_MANUAL: ":material/menu_book:",
    PAGE_GLOSSARY: ":material/dictionary:", PAGE_LINKS: ":material/link:",
}
PAGE_PATHS = {
    PAGE_DOCUMENTATION: "documentacion-general",
    PAGE_DOC_BI: "documentacion-bi", PAGE_DOC_BA: "documentacion-ba",
    PAGE_DOC_IT: "documentacion-it",
    PAGE_HOME: "dashboard", PAGE_DATA: "datos", PAGE_COVER: "portada", PAGE_BUSINESS: "negocio",
    PAGE_DIAGRAMS: "diagramas",
    PAGE_ARCHITECTURE: "arquitectura", PAGE_ANALYSIS: "analisis", PAGE_GAP: "brecha",
    PAGE_CHANNELS: "canales", PAGE_SEASONALITY: "estacionalidad", PAGE_ALERTS: "alertas",
    PAGE_KPI: "indicadores", PAGE_QUERIES: "queries",
    PAGE_CODE: "codigo", PAGE_RULES: "reglas", PAGE_DEVOPS: "devops", PAGE_OPERATIONS: "operaciones",
    PAGE_RUNS: "ejecuciones", PAGE_MANUAL: "manual",
    PAGE_GLOSSARY: "glosario", PAGE_LINKS: "enlaces",
}
TAB_IDEA = "Idea de negocio"
TAB_KPI = "Cifras y cálculos"
TAB_RULES = "Reglas de calidad"
TAB_MANUAL = "Cómo funciona"
TAB_DECISIONS = "Decisiones y método"
TAB_GLOSSARY = "Glosario"
TAB_WEEK = "Esta semana"
TAB_GAP = "Brecha de precio"
TAB_CHANNELS = "Canales y regiones"
TAB_SEASONALITY = "Estacionalidad"
TAB_ALERTS = "Alertas"
TAB_PIPELINE = "Pipeline"
TAB_MODEL = "Modelo de datos"
TAB_DEVOPS = "DevOps y seguridad"
TAB_EXPLORER = "Consulta por clics"
TAB_QUERIES = "Queries"
TAB_CODE = "Código"
TAB_RUNS = "Ejecuciones"
TAB_QUALITY = "Calidad de datos"
TABS_BY_PAGE = {page: [] for page in PAGES}
PAGE_OF_TAB = {
    TAB_IDEA: PAGE_BUSINESS, TAB_KPI: PAGE_KPI, TAB_RULES: PAGE_RULES,
    TAB_MANUAL: PAGE_MANUAL, TAB_DECISIONS: PAGE_DOCUMENTATION, TAB_GLOSSARY: PAGE_GLOSSARY,
    TAB_PIPELINE: PAGE_DIAGRAMS, TAB_MODEL: PAGE_ARCHITECTURE, TAB_DEVOPS: PAGE_DEVOPS,
    TAB_CODE: PAGE_CODE, TAB_RUNS: PAGE_RUNS, TAB_QUALITY: PAGE_OPERATIONS,
    TAB_WEEK: PAGE_ANALYSIS, TAB_GAP: PAGE_GAP, TAB_CHANNELS: PAGE_CHANNELS,
    TAB_SEASONALITY: PAGE_SEASONALITY, TAB_ALERTS: PAGE_ALERTS,
    TAB_EXPLORER: PAGE_QUERIES, TAB_QUERIES: PAGE_QUERIES,
}
OLD_PATHS = {
    "inicio": (PAGE_HOME, None), "el-proyecto": (PAGE_COVER, None), "panel": (PAGE_HOME, None),
    "margenes": (PAGE_GAP, None), "canales-y-regiones": (PAGE_CHANNELS, None),
    "consultas": (PAGE_QUERIES, None), "pipeline": (PAGE_DIAGRAMS, None),
    # The retired «Consulta de datos» screen (C03).
    "datos-y-codigo": (PAGE_QUERIES, None),
    "codigo-y-resultados": (PAGE_QUERIES, None),
    "detalle-tecnico": (PAGE_DIAGRAMS, None),
    "fuentes-y-enlaces": (PAGE_LINKS, None),
    "centro-de-control": (PAGE_RUNS, None), "calidad-de-datos": (PAGE_OPERATIONS, None),
    # Windows and views before the portfolio route (D-070).
    "operacion": (PAGE_OPERATIONS, None), "documentacion": (PAGE_DOCUMENTATION, None), "decisiones": (PAGE_DOCUMENTATION, None),
    "vista-3d": (PAGE_SEASONALITY, None),
}
OLD_HOME_TABS = {"Fuentes y cruces": TAB_IDEA, "Arquitectura": TAB_PIPELINE,
                 "Modelo de datos": TAB_MODEL, "Código": TAB_CODE}
OLD_TAB_PAGES = {(PAGE_OPERATIONS, "Enlaces"): PAGE_LINKS}
TAB_PARAMETER = "seccion"
THEME_PARAMETER = "tema"
# The theme of the whole visit: kept in the session and written to the address on every
# run, so every section, link and reload keeps it (D-070).
THEME_STATE = "chosen_theme"
# Retired theme names still open their closest theme (D-071).
RETIRED_THEMES = {charts.MODE_LIGHT: charts.MODE_CORPORATE, "ChatGPT": charts.MODE_GRAPHITE,
                  "Grafito": charts.MODE_GRAPHITE}
DEFAULT_THEME = charts.MODE_CORPORATE
KPI_PARAMETER = "kpi"
PROFILE_PARAMETER = "visitor_profile"
PIPELINE_DIAGRAM_PARAMETER = "diagrama"
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
# A channel gap that rests on this many regions or fewer names them next to its bar.
MAXIMUM_REGIONS_NAMED = 2
ALERTS_PAGE_BAR_COUNT = 15
RUN_HISTORY_COUNT = 8
MANIFEST_FILE = Path(__file__).resolve().parent.parent / "agent" / "downloads" / "manifest.json"
CHILE_TIME_ZONE = "America/Santiago"
# GitHub allows 60 questions per hour without a key, shared by every app on the
# same server: an answer is kept 5 minutes before asking again.
GITHUB_CACHE_SECONDS = 300
# The database is saved only after these steps passed (D-034), so a saved load
# proves their state when GitHub does not answer.
STEPS_PROVED_BY_A_SAVED_LOAD = {"Download the ODEPA files", "Run the ETL",
                                "Run the tests against the new database"}
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
LAG_HINT = ("Cuántas semanas tarda el precio al consumidor en moverse después del "
            "mayorista. Para cada desfase de 0 a 8 semanas se mide la **correlación** entre "
            "los cambios semanales de ambos precios: 1 = se mueven igual, 0 = sin relación. "
            "El rezago es el desfase con la correlación más alta, si se distingue de cero "
            "(más de 2/√pares). Necesita 26 semanas.")
LAG_NOTE = ("Indicador descriptivo: muestra qué desfase coincide mejor con los datos, no "
            "prueba que el precio mayorista cause el cambio al consumidor.")
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
WEEK_RANKING_HINT = ("**Qué muestra:** los productos del grupo elegido cuyo precio más cambió "
                     "esta semana frente a la anterior, en los canales elegidos. **Cómo leerlo:"
                     "** ▲ en rojo subió, ▼ en azul bajó; la barra más larga es el mayor "
                     "cambio. Es el precio nacional (promedio de las regiones).")
DUMBBELL_HINT = ("**Qué muestra:** el precio mayorista (punto gris) y el precio al consumidor "
                 "de cada canal (punto de color) en la última semana con ambos precios, en "
                 "la región elegida. **Cómo leerlo:** cuanto más larga la línea, mayor la "
                 "brecha; el número a la derecha es la brecha en %.")
GAP_LINE_HINT = ("**Qué muestra:** la brecha de un canal (consumidor − mayorista, sobre el "
                 "mayorista) semana a semana, en las últimas 52 semanas. **Cómo leerlo:** si "
                 "la línea sube, el consumidor paga proporcionalmente más; la línea punteada "
                 "es 0 %, sin brecha.")
HEATMAP_HINT = ("**Qué muestra:** el índice estacional promedio de cada mes (1 = precio "
                "promedio de su año), un año por fila. **Cómo leerlo:** más oscuro = más caro "
                "ese mes; compara una columna de arriba abajo para ver si el mismo mes se "
                "repite caro o barato cada año.")
ALERT_LIST_HINT = ("**Qué muestra:** los productos cuyo cambio semanal se salió de su rango "
                   "habitual (más de 2 desviaciones estándar respecto de las 12 semanas "
                   "previas). **Cómo leerlo:** el semáforo dice cuán lejos: ● moderada (2 a 3"
                   "), ▲ alta (3 a 4), ◆ muy alta (4 o más); la barra mide esa distancia y la "
                   "marca vertical es el límite de 2.")
NATIONAL_PRICE_HINT = ("Promedio simple de las regiones con dato, en pesos por kilo (o por "
                       "unidad), semana a semana.")
ARCHITECTURE_HINT = ("Los datos viajan de izquierda a derecha. **Bronce**: el archivo tal "
                     "como llega. **Limpieza y reglas**: se corrigen formatos y se aplican "
                     "las reglas de negocio. **Calidad**: si algo no cuadra, no se guarda "
                     "nada. **Oro**: la base lista para analizar. Arriba, quién da las "
                     "órdenes; abajo, cómo sabemos qué pasó. El punto de color de cada paso "
                     "es su estado real. Pasa el mouse sobre cada pieza para ver qué hace. "
                     "**Siglas**: ODEPA, Oficina de Estudios y Políticas Agrarias; CSV, archivo "
                     "de valores separados por comas; ETL, extraer, transformar y cargar; RN, "
                     "regla de negocio; SQL, lenguaje de consultas; MD, Markdown.")
DEVOPS_HINT = ("Cada recuadro es una plataforma y, dentro, lo que corre en ella: ODEPA, tu "
               "computador, GitHub (repositorio, Actions, caché e Issues), Streamlit Cloud y "
               "quienes usan el panel. Cada línea dice cómo se comunican dos piezas. Las cifras "
               "y los puntos de color son reales; sin punto, no hay un estado que leer. Pasa "
               "el mouse sobre cada pieza para ver qué hace. **Siglas**: CI, integración "
               "continua (pruebas automáticas en cada cambio); HTTPS, conexión web cifrada; "
               "API, la puerta por la que un programa habla con GitHub; CSV, archivo de "
               "valores separados por comas.")
SEARCH_SUMMARY_HINT = ("**Qué muestra:** cuántos precios de la última semana de la búsqueda "
                       "están en cada estado. **Dentro de lo habitual:** el cambio se parece a "
                       "los cambios recientes; **Conviene revisar:** fue mayor de lo normal; "
                       "**Cambio poco común:** se alejó claramente de su comportamiento "
                       "reciente; **Aún sin historial:** faltan semanas para comparar. Toca una "
                       "tarjeta o un número para ver solo ese grupo.")
SEARCH_TABLE_HINT = ("**Qué muestra:** cada precio semanal que cumple la búsqueda, con su "
                     "cambio frente a la semana anterior, la diferencia con el precio mayorista "
                     "y si ese cambio se parece a lo ocurrido recientemente. Ordena con un clic "
                     "en el título de una columna; selecciona una fila para ver su ficha.")
# The project page. Texts come from docs/DISENO.md (sections 2 to 4) and DECISIONES.md.
# Idea de negocio, in short pieces: what each card says, without repeating
# «Empieza aquí» (the problem in three sentences lives there).
AUDIENCE_CARDS = [
    ("Analista de pricing o compras", "Márgenes, canales, regiones y alertas.", PAGE_ANALYSIS),
    ("Equipo de datos", "Si la carga funcionó y qué quedó fuera.", TAB_QUALITY),
    ("Más adelante", "Un resumen para gerencia y una vista simple para consumidores.", None),
]
# The cover (C01): three short statements, three things a visitor can check, and the
# limits. The numbers next to them are read from the base, never written here.
COVER_TAGLINE = ("Precios de alimentos en Chile: ", "de archivos públicos a información semanal")
COVER_LEAD = ("Integra los precios mayoristas y al consumidor de ODEPA para comparar precios, "
              "seguir sus cambios y revisar alertas cada semana.")
COVER_STATEMENTS = [
    ("database", "El problema", "Dos archivos públicos separados, con unidades distintas, "
                                "que había que cruzar a mano cada semana."),
    ("workflow", "Trabajo desarrollado", "Ingesta, limpieza, modelo de datos, consultas SQL, dashboard "
                              "y automatización semanal."),
    ("person", "Para quién", "Equipos de pricing, compras y abastecimiento que necesitan "
                             "comparar precios y anticipar revisiones de compra."),
]
COVER_OFFER = ("Comparaciones por canal y región, evolución de precios y cambios de la semana "
               "que conviene revisar.")
COVER_LIMITS = ("Precios nominales, sin ajuste por inflación. La brecha de precio no mide "
                "ganancias. Los datos describen; no prueban causas.")
SOURCE_LABELS = {"Precios mayoristas": "Diario · frutas y hortalizas",
                 "Precios al consumidor": "Semanal · todos los grupos"}
LIMIT_CARDS = [
    ("Precios nominales", "Sin ajuste por inflación: al comparar años, parte de la subida es "
                          "inflación."),
    ("Desde enero de 2022", "Los datos cargados empiezan en enero de 2022."),
    ("La papa no tiene margen", "Sus calidades no coinciden entre las dos fuentes."),
    ("Cálculos, no hallazgos", "Las cifras del panel son cálculos sobre datos oficiales; los "
                               "hallazgos se publican solo después de verificarlos."),
]
WHY_TEXT = ("Los datos son abiertos y oficiales, el cruce entre precio mayorista y precio al "
            "consumidor se pudo verificar con datos reales, y las preguntas son las que se "
            "hace a diario un área de pricing o abastecimiento.")
WHY_DETAILS = ("Se descartaron el scraping de supermercados (condiciones de uso inciertas) y "
               "otros temas con menos valor al cruzar.")
MATCH_DETAILS = (
    "**Clave de cruce:** producto + variedad + calidad + región + semana (lunes de inicio).  \n"
    "**Reglas que lo hacen:** RN-02 (nombres), RN-03 a RN-05 (unidades), RN-07 y RN-08 "
    "(semanas) y RN-06 (margen solo con la misma unidad).  \n"
    "**Dónde ocurre:** `etl/etl.py` lee `raw_wholesale` y `raw_consumer` de `raw.db` y deja "
    "el resultado en `weekly_price` de `datos.db`.")
# The quality rules in the order the ETL applies them (etl/etl.py), then the one
# that lives in the margin query: (stage, what it does, rules, where it happens).
RULE_STAGES = [
    ("Limpieza", "Cada fila leída se pone en un formato común antes de revisarla.",
     ["RN-13", "RN-01", "RN-02"], "`clean()` en `etl/etl.py`"),
    ("Validación", "Las filas que no se pueden usar se apartan con su motivo; nunca se borran "
                   "en silencio.", ["RN-11"],
     "`validate_rows()` y `build_rejections()` en `etl/etl.py`; tabla `rejection`"),
    ("Unidades", "Los precios se llevan a kilo, unidad o litro para poder compararlos.",
     ["RN-03", "RN-04", "RN-05"], "`normalize_units()` en `etl/etl.py`"),
    ("Semanas", "Los precios diarios y de cada punto de venta se juntan en un precio por "
                "semana.", ["RN-08", "RN-07", "RN-09", "RN-10"],
     "`assign_week_start()` y `aggregate_weekly()` en `etl/etl.py`"),
    ("Atípicos", "Los precios muy lejos del resto se marcan y quedan fuera de los "
                 "indicadores.", ["RN-12"], "`flag_outliers()` en `etl/etl.py`"),
    ("Carga", "La base se reconstruye completa y se revisa antes de guardarla.", ["RN-14"],
     "`check_quality()` y `load()` en `etl/etl.py`; tabla `weekly_price`"),
    ("Al calcular el margen", "El margen solo compara precios en la misma unidad.",
     ["RN-06"], "consulta `k1_margin` en `bi/queries.sql`"),
]
# The decisions a reviewer should see first: real data-engineering trade-offs
# (source, architecture and cost, reliability, rigor), agreed with the author.
KEY_DECISIONS = [
    ("Datos", "De dónde salen los datos y cómo se cruzan sin inventar nada.",
     ["D-001", "D-007", "D-042"]),
    ("Arquitectura y costo", "Qué se eligió para operar sin costo y dentro de los límites de "
                             "GitHub.", ["D-012", "D-020", "D-046"]),
    ("Confiabilidad del pipeline", "Cómo cada martes se carga todo o nada, sin duplicar ni "
                                   "descargar de más.", ["D-024", "D-034", "D-047"]),
    ("Rigor", "Qué se publica y cómo se comprueba.", ["D-018", "D-049", "D-019"]),
]
# What each theme of the glossary groups, in one sentence.
GLOSSARY_THEME_LEADS = {
    "Fuentes": "De dónde vienen los precios.",
    "Pipeline": "Lo que corre cada martes y cómo se controla.",
    "Base de datos": "Cómo se guardan y se leen los datos.",
    "Indicadores": "Las cifras y las reglas que las producen.",
    "Conexiones": "Cómo se comunican las piezas.",
}
# The tables of «DevOps y seguridad» by priority: what protects the data first,
# then what runs the project, how a run is observed and what gets published.
# (heading in docs/PROYECTO.md, sentence, title column, text column, note column)
ARCHITECTURE_GROUPS = [
    ("Seguridad", "Qué protege los datos y las claves del proyecto.", "Medida",
     "Qué protege", "Archivo"),
    ("DevOps", "Qué hace correr el proyecto solo: cada semana y en cada cambio del código.",
     "Pieza", "Qué hace", "Archivo"),
    ("Observabilidad", "Cómo se sabe qué pasó en cada carga.", "Fuente", "Qué registra",
     "Dónde se ve"),
    ("Informes", "Qué se publica después de cada carga.", "Informe", "Qué contiene", "Cuándo"),
]
# The folders of the repository in the order the data goes through them, each
# with what it is for. «» is the root.
FOLDER_PURPOSES = [
    ("", "Raíz del repositorio", "Por dónde empezar: qué es el proyecto y cómo correrlo."),
    ("agent/", "agent/", "Ingesta: descarga y valida los archivos de ODEPA."),
    ("etl/", "etl/", "Limpieza, reglas de negocio y carga en las dos bases."),
    ("bi/", "bi/", "Indicadores, panel, diagramas e informe semanal."),
    ("tests/", "tests/", "Pruebas automáticas que corren en cada cambio y cada martes."),
    (".github/workflows/", ".github/workflows/", "Automatización en GitHub Actions."),
    ("docs/", "docs/", "Diseño, decisiones, manual y textos del panel."),
]
# Why a row is rejected (RN-11), in the words of validate_rows() in etl/etl.py.
REASON_TEXTS = {
    etl.REASON_UNREADABLE_VALUE: "un precio, una fecha o la región no se pudo leer",
    etl.REASON_NON_POSITIVE_PRICE: "un precio (mínimo, máximo o promedio) es cero o negativo",
    etl.REASON_MINIMUM_ABOVE_MAXIMUM: "el precio mínimo es mayor que el máximo",
    etl.REASON_DATE_OUTSIDE_FILE_YEAR: "la fecha no cae en el año del archivo",
    etl.REASON_NON_POSITIVE_VOLUME: "una fila mayorista sin volumen no puede entrar al "
                                    "promedio ponderado (RN-07)",
}
# The fields of a rejected row worth reading, as ODEPA sent them, in Spanish.
REJECTED_ROW_LABELS = {
    "price_date": "Fecha", "week_start": "Semana", "region": "Región", "market": "Mercado",
    "channel": "Canal", "product": "Producto", "variety": "Variedad", "quality": "Calidad",
    "sale_unit": "Unidad de venta", "unit": "Unidad", "volume": "Volumen",
    "min_price": "Precio mínimo", "max_price": "Precio máximo", "avg_price": "Precio promedio",
}
# What each group of project links is for.
LINK_GROUP_LEADS = {
    "Código y operación": "El código, cada ejecución, cada informe y cada cambio.",
    "Fuentes de datos": "Los archivos originales de ODEPA.",
    "Documentos": "El manual de operación y el registro de decisiones.",
}
# (question, page where it is answered, state: available, partial or pending, note)
BUSINESS_QUESTIONS = [
    ("¿Cuál es el margen entre el precio mayorista y el precio al consumidor, y cómo "
     "evoluciona?", TAB_GAP, "available", "Frutas y verduras"),
    ("¿Cuánto difiere el precio entre canales: supermercado, feria, carnicería…?",
     TAB_CHANNELS, "available", "Todos los grupos"),
    ("¿En qué regiones son más altos los precios?", TAB_CHANNELS,
     "available", "Todos los grupos"),
    ("¿En qué semanas sube y baja cada producto, y cuánto?", TAB_SEASONALITY,
     "available", "Todos los grupos, desde 2022"),
    ("¿Con cuántas semanas de diferencia sigue el precio al consumidor al mayorista?",
     TAB_GAP, "available", "Frutas y verduras; descriptivo, no prueba causa"),
    ("¿Qué productos se movieron esta semana fuera de su rango normal?", TAB_ALERTS,
     "available", "Todos los grupos"),
]
QUESTION_STATES = {"available": ("Disponible", "ok"), "partial": ("Parcial", "running"),
                   "pending": ("Pendiente", "neutral")}

NO_DATA_TEXT = "No hay datos para esta selección."
NO_MARGIN_TEXT = ("Este producto no tiene precio mayorista en esta región y canal: la brecha "
                  "solo existe para frutas y verduras con la misma unidad (RN-06). Mira "
                  "Canales y regiones o Estacionalidad.")
# Esta semana: how many products the ranking shows, and the weeks of each small line.
RANKING_SIZE = 12
SPARKLINE_WEEKS = 12
# Brecha de precio: the weeks of the gap line (the whole history is folded).
GAP_LINE_WEEKS = 52
# Alertas: (lowest distance in standard deviations, label, icon, status color).
ALERT_LEVELS = [(4, "Muy alta", "◆", "critical"), (3, "Alta", "▲", "serious"),
                (0, "Moderada", "●", "warning")]
FILTERS_NOTE = ("Los filtros valen para todas las pestañas. Canales y regiones compara todos "
                "los canales y regiones del producto; Alertas muestra todos los productos.")
NOMINAL_PRICES_TEXT = "Precios nominales, sin ajuste por inflación."
ATTRIBUTION_TEXT = (
    "Datos: Oficina de Estudios y Políticas Agrarias (ODEPA), Ministerio de "
    "Agricultura de Chile, licencia Creative Commons Atribución. "
    "Este proyecto no es un producto oficial de ODEPA. "
    "Lectura de los datos: el precio nacional es un promedio simple de las regiones disponibles, "
    "sin ponderar por población o ventas. Los indicadores describen el histórico; no predicen precios. "
    "Las pruebas verifican reglas concretas, no certifican cada dato de la fuente.")
# endregion


# region Style
def get_mode():
    """Theme of the visit; Corporativo until the reader chooses another one."""
    theme = st.session_state.get(THEME_STATE)
    return theme if theme in charts.THEMES else DEFAULT_THEME


def settle_theme():
    """The address wins when it names a theme (a shared link); otherwise the session
    keeps the theme. Either way the address shows it."""
    requested = st.query_params.get(THEME_PARAMETER)
    requested = RETIRED_THEMES.get(requested, requested)
    if requested in charts.THEMES:
        st.session_state[THEME_STATE] = requested
    st.session_state[THEME_STATE] = get_mode()
    st.query_params[THEME_PARAMETER] = st.session_state[THEME_STATE]


def keep_theme_from_field():
    """The theme field changed: keep it for the whole visit."""
    st.session_state[THEME_STATE] = st.session_state["theme_field"]
    st.query_params[THEME_PARAMETER] = st.session_state[THEME_STATE]


def build_base_mode_script(theme_or_base):
    """Keep native widgets on the same base as the project palette.

    Streamlit infers st.context.theme from the CSS background, so it cannot
    detect a native widget theme that disagrees with the overridden page color.
    The cached frontend choice is checked instead, with one reload per change.
    Streamlit keeps that choice per address, so it is written for every section at
    once: moving between sections never reloads the page, which would end the session
    and its filters (D-070).
    """
    theme = theme_or_base if theme_or_base in charts.THEMES else (
        charts.MODE_DARK if theme_or_base == charts.BASE_DARK else charts.MODE_CORPORATE)
    base = charts.get_palette(theme)["base"]
    value = json.dumps("Dark" if base == charts.BASE_DARK else "Light")
    selected_theme = json.dumps(theme)
    section_paths = json.dumps([""] + list(WINDOW_PATHS.values()))
    return f"""<script>
    const page = window.parent;
    const attempt = "project-base-request-" + page.location.pathname;
    const key = "stActiveTheme-" + page.location.pathname + "-v2";
    const wanted = {value};
    // The app may live under a folder: the sections share the current page's folder.
    const folder = page.location.pathname.replace(/[^/]*$/, "");
    try {{
        const current = JSON.parse(page.localStorage.getItem(key) || "null");
        const requested = page.sessionStorage.getItem(attempt);
        // Stored preference can already match while React still uses the old base.
        const ink = page.getComputedStyle(page.document.body).color.match(/[0-9.]+/g);
        const brightInk = ink && (Number(ink[0]) * .2126 + Number(ink[1]) * .7152 + Number(ink[2]) * .0722) > 128;
        const baseMatches = ink && (wanted === "Dark" ? brightInk : !brightInk);
        if (baseMatches) {{ page.sessionStorage.removeItem(attempt); }}
        for (const path of {section_paths}) {{
            page.localStorage.setItem("stActiveTheme-" + folder + path + "-v2",
                                      JSON.stringify(wanted));
        }}
        if (!baseMatches && requested !== wanted) {{
            page.sessionStorage.setItem(attempt, wanted);
            // The address keeps the chosen palette across the reload.
            const address = new URL(page.location.href);
            address.searchParams.set("tema", {selected_theme});
            page.history.replaceState(null, "", address.toString());
            // This reload only syncs Streamlit's native-widget base mode; it is not
            // a real page refresh, so it must not send the reader back home (D-099).
            page.sessionStorage.setItem("greenoceanThemeReload", "1");
            page.location.reload();
        }}
    }} catch (error) {{ /* CSS remains usable when browser storage is unavailable. */ }}
    </script>"""


def match_base_mode(theme):
    """Check the frontend cache, including after either direction of a theme switch."""
    components.html(build_base_mode_script(theme), height=0)


def build_theme_css(palette):
    """Page, sidebar and links in the colors of the active theme (T-44, D-052).

    Streamlit's own widgets keep the colors of its base mode; the theme only
    restyles what it can do without fighting them.
    """
    return f"""
    .stApp {{ background: {palette["background"]}; color:{palette["text"]};
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    [data-testid="stMain"] p, [data-testid="stMain"] h1, [data-testid="stMain"] h2,
    [data-testid="stMain"] h3, [data-testid="stMain"] label, [data-testid="stMain"] input {{
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    [data-testid="stMain"] h1 {{font-weight:610 !important; letter-spacing:-.035em;}}
    [data-testid="stMain"] h2, [data-testid="stMain"] h3 {{font-weight:560 !important; letter-spacing:-.02em;}}
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{ color:{palette["text"]}; }}
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {{ color:{palette["text"]}; }}
    [data-testid="stHeading"] h1, [data-testid="stHeading"] h2,
    [data-testid="stHeading"] h3, [data-testid="stHeading"] h4 {{color:{palette["strong_text"]};}}
    [data-testid="stExpander"] details {{background:{palette["card"]}; border-color:{palette["card_border"]};}}
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p,
    [data-baseweb="tab"] p {{color:{palette["text"]};}}
    [data-testid="stPopoverBody"], [data-testid="stDialog"] [role="dialog"] {{
        background:{palette["card"]}; color:{palette["text"]};}}
    [data-testid="stRadio"] p {{color:{palette["text"]};}}
    [data-baseweb="select"] > div, [data-baseweb="input"],
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {{
        background:{palette["field"]}; color:{palette["strong_text"]}; border-color:{palette["card_border"]};}}
    [data-baseweb="select"] input {{color:{palette["strong_text"]};}}
    [data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] [role="option"] {{
        background:{palette["field"]}; color:{palette["strong_text"]};}}
    [data-baseweb="popover"] [role="option"]:hover {{background:{palette["card"]};}}
    button[kind="secondary"], button[kind="secondaryFormSubmit"] {{
        background:{palette["card"]}; color:{palette["strong_text"]}; border-color:{palette["card_border"]};}}

    /* Desktop navigation stays in normal flow. On mobile the fixed logo bar
       needs an opaque surface so scrolling text never crosses the logo. */
    [data-testid="stHeader"] {{ background: transparent; }}
    @media(max-width:800px) {{
        [data-testid="stHeader"] {{background:{palette['background']};}}
    }}
    /* The app owns its four themes; hide Streamlit's duplicate theme/utility menu.
       Keep the header itself so the sidebar toggle and GreenOcean logo still work. */
    [data-testid="stMainMenu"] {{ display:none !important; }}
    [data-testid="stHeader"], [data-testid="stHeader"] * {{pointer-events:none !important;}}
    [data-testid="stHeader"] button, [data-testid="stHeader"] button *,
    [data-testid="stHeader"] a, [data-testid="stHeader"] a * {{pointer-events:auto !important;}}
    [data-testid="stSidebar"] {{ background: {palette["sidebar"]}; }}
    /* Streamlit's local file watcher is a floating developer control. It can
       cover report content when the viewport is narrow, so it is never part
       of the presentation UI. */
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] span,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: {palette["sidebar_text"]};
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stPageLink"] p,
    [data-testid="stSidebar"] [data-testid="stPageLink"] span {{ color:{palette["sidebar_text"]}; }}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a {{ background:transparent !important; }}
    [data-testid="stSidebarNavLink"][aria-current="page"] {{
        box-shadow: inset 2px 0 0 {palette["accent"]}, 0 0 14px {palette["glow"]};
    }}
    [data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {{
        color: {palette["accent"]};
    }}
    [data-testid="stMain"] a {{ color: {palette["accent"]}; }}
    /* Text on the accent color (the chips of a multiple choice), always readable. */
    [data-testid="stToolbar"] button, [data-testid="stToolbar"] button p,
    [data-testid="stToolbar"] svg {{ color:{palette["strong_text"]}; fill:{palette["strong_text"]}; }}
    [data-testid="stCode"] pre, [data-testid="stCode"] code {{
        background:{palette["field"]} !important; color:{palette["strong_text"]};
    }}
    [data-baseweb="tag"] span, [data-baseweb="tag"] svg {{
        color: {palette["on_accent"]}; fill: {palette["on_accent"]};
    }}
    button[kind="primary"], button[kind="primaryFormSubmit"] {{
        background:{palette["accent"]}; color:{palette["on_accent"]};
    }}
    button[kind="primary"] p, button[kind="primaryFormSubmit"] p {{
        color:{palette["on_accent"]} !important;
    }}
    .hint {{ color: {palette["accent"]} !important; }}
    """


# Code colors for the light themes: Streamlit's own steps fall under 3:1 on white,
# so each kind of token takes a darker step of its hue (4.5:1 or more).
LIGHT_CODE_COLORS = {"string": "#15803d", "boolean": "#15803d", "number": "#0f766e",
                     "operator": "#c2410c", "keyword": "#1d4ed8", "function": "#1d4ed8",
                     "comment": "#57606a", "punctuation": "#57606a"}


def build_code_colors_css(palette):
    """Darker code tokens on the light themes; Vantablack keeps Streamlit's colors."""
    if palette["base"] != charts.BASE_LIGHT:
        return ""
    return "".join(f'[data-testid="stCode"] .token.{token} {{ color: {color} !important; }}'
                   for token, color in LIGHT_CODE_COLORS.items())


def build_style_css(mode):
    """Cards, key figures, chips and tables, in the colors of the active theme."""
    palette = charts.get_palette(mode)
    return build_theme_css(palette) + f"""
    [class*="st-key-card_"] {{
        background: {palette["card"]}; border: 1px solid {palette["card_border"]};
        border-radius: 18px; padding: 18px 20px 14px 20px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06), inset 0 1px 0 {palette["glow"]};
    }}
    [data-testid="stMainBlockContainer"] {{ padding-top:1.1rem; }}
    .page-freshness {{ color:{palette["text"]}; font-size:0.82rem; margin-bottom:8px; }}
    [data-testid="stMain"] h1 {{ font-size:clamp(1.7rem,3vw,2.35rem); line-height:1.15; }}
    @media(max-width:700px) {{
        [data-testid="stHorizontalBlock"]:has(.st-key-catalog_list) {{ flex-wrap:wrap; }}
        [data-testid="stColumn"]:has(.st-key-catalog_list) {{ min-width:100%; }}
    }}
    /* The report: title and analyzed week, actions at the right. */
    .report-title h1 {{ font-size:clamp(1.6rem,2.6vw,2.2rem) !important; margin:0 !important;
        padding:0 !important; line-height:1.15; }}
    .report-title p {{ margin:4px 0 0; color:{palette["text"]}; font-size:.92rem; }}
    .report-title strong {{ color:{palette["strong_text"]}; }}
    .report-divider {{ margin:0 10px; color:{palette["card_border"]}; }}
    .st-key-report_actions {{ gap:14px; align-items:center; flex-wrap:wrap; }}
    .st-key-report_actions [data-testid="stMarkdownContainer"] p {{ margin:0; }}
    /* The filter bar: one panel, each name written at the left of its field. */
    .st-key-report_filters {{ background:{palette["card"]}; border:1px solid {palette["card_border"]};
        border-radius:14px; padding:8px 14px; gap:6px 18px; flex-wrap:wrap !important; }}
    [class*="st-key-bar_"] {{ flex-wrap:nowrap !important; min-width:0; }}
    [class*="st-key-bar_"] [data-testid="stSelectbox"],
    [class*="st-key-bar_"] [data-testid="stSlider"] {{ flex:1 1 0; min-width:0; }}
    /* The width of each field lives on its wrapper, the item of the bar's row. */
    .st-key-report_filters > div:has(> [class*="st-key-bar_"]) {{ flex:1 1 170px; min-width:0; }}
    .st-key-report_filters > div:has(> .st-key-bar_product) {{ flex:2 1 240px; }}
    .st-key-report_filters > div:has(> .st-key-bar_top_n) {{ flex:1.4 1 190px; }}
    .st-key-report_filters > div:has(> .st-key-bar_order) {{ flex:1 1 150px; }}
    .bar-label {{ color:{palette["text"]}; font-size:.85rem; white-space:nowrap; }}
    /* The figures of the week: one line, no cards, thin dividers. */
    .kpi-strip {{ display:flex; flex-wrap:wrap; margin:6px 0 0;
        border-top:1px solid {palette["card_border"]}; border-bottom:1px solid {palette["card_border"]}; }}
    .kpi-strip-item {{ flex:1 1 170px; display:flex; flex-direction:column; gap:0;
        padding:6px 16px; min-width:0; text-decoration:none !important; color:inherit !important;
        border-left:1px solid {palette["card_border"]}; }}
    .kpi-strip-item:first-child {{ border-left:none; padding-left:4px; }}
    .kpi-strip-item:hover .kpi-strip-label {{ color:{palette["accent"]}; }}
    .kpi-strip-value {{ font-size:1.5rem; font-weight:750; line-height:1.15;
        color:{palette["strong_text"]}; white-space:nowrap; }}
    .kpi-strip-rise {{ color:{charts.get_status_text_color("critical", mode)}; }}
    .kpi-strip-accent {{ color:{palette["accent"]}; }}
    .kpi-strip-good {{ color:{charts.get_status_text_color("good", mode)}; font-size:1.2rem; }}
    .kpi-strip-label {{ color:{palette["strong_text"]}; font-size:.88rem; font-weight:600; }}
    .kpi-strip-note {{ color:{palette["text"]}; font-size:.75rem; white-space:normal; }}
    .kpi-strip-label {{ white-space:normal; }}
    .kpi-strip-meaning {{ justify-content:center; color:{palette["text"]}; font-size:.85rem; }}
    .filter-scope {{ color:{palette["text"]}; font-size:.78rem; margin:2px 0 0; }}
    .strip-note {{ color:{palette["text"]}; font-size:.8rem; margin:4px 0 0; }}
    .ring-legend {{ list-style:none; padding:0; margin:0; font-size:.84rem; }}
    .ring-legend span:nth-child(2) {{ min-width:0; white-space:normal; overflow-wrap:anywhere; }}
    .st-key-ranking_caption {{ flex-wrap:nowrap !important; justify-content:space-between; }}
    .st-key-ranking_caption [data-testid="stCaptionContainer"] {{ flex:1 1 auto; min-width:0; }}
    .st-key-ranking_order {{ flex:none; }}
    .ring-legend li {{ display:grid; grid-template-columns:8px minmax(0,1fr) auto; gap:8px; padding:3px 0; }}
    .ring-legend strong {{ color:{palette["strong_text"]}; }}
    .ring-note {{ color:{palette["text"]}; font-size:.78rem; margin:8px 0 0; }}
    /* Streamlit sizes markdown p and li itself: these win over it (D-072). */
    [data-testid="stMarkdownContainer"] ul.ring-legend li {{ font-size:.84rem; margin:0;
        white-space:nowrap; }}
    [data-testid="stMarkdownContainer"] p.ring-note,
    [data-testid="stMarkdownContainer"] p.filter-scope {{ font-size:.78rem; line-height:1.4; }}
    .report-footer {{ display:flex; flex-wrap:wrap; gap:6px 18px; align-items:center;
        color:{palette["text"]}; font-size:.85rem; padding:6px 0;
        border-top:1px solid {palette["card_border"]}; }}
    .report-footer a {{ font-weight:600; }}
    .project-navigation {{ display:grid; grid-template-columns:1fr auto 1fr; gap:12px;
        align-items:center; padding:12px 0; border-bottom:1px solid {palette["card_border"]};
        margin:4px 0 20px; font-size:0.85rem; }}
    .project-navigation > div:last-child {{ text-align:right; }}
    .journey-position {{ color:{palette["text"]}; font-size:0.75rem; }}
    .component-symbol {{ display:inline-flex; width:38px; height:42px; flex-shrink:0;
        vertical-align:middle; margin:0 10px 8px 0; color:{palette["accent"]}; }}
    .component-symbol svg {{ width:100%; height:100%; }}
    .info-card[data-component-kind="security"] {{ border-radius:18px 18px 42% 42% / 18px 18px 32px 32px;
        border-top:3px solid {palette["accent"]}; padding-bottom:36px; }}
    .info-card[data-component-kind="database"] {{ border-radius:50% / 18px;
        border-top:3px double {palette["accent"]}; border-bottom:3px double {palette["accent"]}; }}
    .info-card[data-component-kind="workflow"] {{ border-left:4px solid {palette["accent"]};
        border-radius:4px 24px 24px 4px; }}
    .info-card[data-component-kind="document"], .info-card[data-component-kind="code"] {{
        border-radius:3px 20px 3px 3px; border-top:3px solid {palette["accent"]}; }}
    .info-card[data-component-kind="chart"] {{ border-radius:8px; border-bottom:3px solid {palette["accent"]}; }}
    .info-card[data-component-kind="rule"] {{ border-radius:20px 4px 20px 4px;
        border-left:3px solid {palette["accent"]}; }}
    .info-card[data-component-kind="person"] {{ border-radius:28px 28px 8px 8px; }}
    .info-card[data-component-kind="mission"], .info-card[data-component-kind="vision"],
    .info-card[data-component-kind="scope"] {{ margin:14px 0; border-radius:0 16px 16px 0;
        border-left:4px solid {palette["accent"]}; display:flow-root; }}
    .info-card[data-component-kind="mission"] .component-symbol,
    .info-card[data-component-kind="vision"] .component-symbol,
    .info-card[data-component-kind="scope"] .component-symbol {{ width:64px; height:68px;
        float:left; margin:0 22px 6px 0; }}
    .info-card[data-component-kind="vision"] {{ border-radius:28px; border-left:1px solid {palette["card_border"]}; }}
    .info-card[data-component-kind="alert"] {{ border-left:4px solid {palette["rise"]}; border-radius:4px; }}
    [class*="st-key-card_"]:has(.component-symbol[data-kind="security"]) {{
        border-radius:18px 18px 40px 40px; border-top:3px solid {palette["accent"]}; }}
    [class*="st-key-card_"]:has(.component-symbol[data-kind="database"]) {{
        border-radius:30px / 16px; border-block:3px double {palette["card_border"]}; }}
    [class*="st-key-card_"]:has(.component-symbol[data-kind="workflow"]) {{
        border-left:4px solid {palette["accent"]}; border-radius:4px 20px 20px 4px; }}
    [class*="st-key-card_"]:has(.component-symbol[data-kind="chart"]) {{
        border-radius:8px; border-bottom:3px solid {palette["accent"]}; }}
    @media (max-width:640px) {{
        .project-navigation {{ grid-template-columns:1fr 1fr; gap:8px; }}
        .journey-position {{ grid-column:1/-1; grid-row:1; text-align:center; }}
        .component-symbol {{ width:30px; height:34px; }}
    }}
    .overview-metrics {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
        gap:16px; padding:20px; margin:12px 0 24px; border-radius:16px;
        background:{palette["card"]}; border:1px solid {palette["card_border"]}; }}
    .overview-metrics .kpi-value {{ font-size:1.75rem; margin-top:6px; overflow-wrap:anywhere; }}
    .mobile-rankings {{ display:none; list-style:none; padding:0; margin:12px 0; }}
    .mobile-rankings li {{ margin:0 0 16px; }}
    .mobile-ranking-label {{ display:flex; align-items:flex-start; gap:12px; margin-bottom:6px;
        font-size:0.85rem; line-height:1.4; color:{palette["strong_text"]}; }}
    .mobile-ranking-label span {{ min-width:0; overflow-wrap:anywhere; flex:1; }}
    .mobile-ranking-label strong {{ white-space:nowrap; }}
    .mobile-ranking-track {{ position:relative; height:8px; border-radius:4px;
        background:{palette["grid"]}; overflow:hidden; }}
    .mobile-ranking-track span {{ position:absolute; top:0; height:100%; border-radius:4px; }}
    .mobile-ranking-track i {{ position:absolute; left:50%; height:100%;
        border-left:1px solid {palette["text"]}; }}
    @media (max-width:640px) {{
        [class*="_ranking_desktop"] {{ display:none; }}
        /* The summary's clickable rankings too: on a phone the list replaces them and the
           Producto field does the filtering (D-072). */
        [class*="st-key-"][class*="_movements_chart_"],
        [class*="st-key-"][class*="_gaps_chart_"] {{ display:none; }}
        .mobile-rankings {{ display:block; }}
    }}
    .resource-tree {{ list-style:none; padding:0 0 0 18px; border-left:1px solid {palette["card_border"]}; }}
    .devops-cycle {{
        width:min(100%,780px,calc((100vh - 220px) * 2.04));
        margin:6px auto 14px;
    }}
    .devops-cycle > svg {{
        width:100%; height:auto; max-height:calc(100vh - 220px);
        display:block; margin:0 auto;
    }}
    .devops-cycle-mobile {{ display:none; list-style:none; padding:0; }}
    .devops-cycle-mobile li, .technical-rows li {{ display:flex; align-items:flex-start;
        gap:14px; padding:12px 0; border-bottom:1px solid {palette["card_border"]}; }}
    .devops-logos {{ display:flex; gap:6px; flex-shrink:0; width:66px; }}
    .devops-logos svg {{ width:28px; height:28px; }}
    .devops-cycle-mobile span {{ display:block; font-size:.85rem; color:{palette["text"]}; }}
    .technical-rows {{ list-style:none; padding:0; margin:0 0 20px; }}
    .technical-rows .component-symbol {{ width:28px; height:30px; margin:0; }}
    .technical-rows li > div {{ min-width:0; }}
    .technical-rows p {{ margin:4px 0; font-size:.9rem; line-height:1.5; }}
    @media(max-width:640px) {{
        .devops-cycle {{ display:none; }}
        .devops-cycle-mobile {{ display:block; }}
    }}
    .resource-tree li {{ display:grid; grid-template-columns:minmax(160px,1fr) 2fr;
        gap:12px; margin:0; padding:14px 8px; border-bottom:1px solid {palette["card_border"]}; }}
    .resource-tree li span {{ color:{palette["text"]}; }}
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stWidgetLabel"],
    [data-testid="stMain"] [data-testid="stCaptionContainer"] {{ color:{palette["strong_text"]}; }}
    [data-testid="stExpander"] details {{ background:{palette["card"]};
        border:1px solid {palette["card_border"]}; border-radius:12px; }}
    [data-testid="stExpander"] summary {{ color:{palette["strong_text"]}; }}
    [data-testid="stDialog"] [data-testid="stWidgetLabel"],
    [data-testid="stDialog"] [data-testid="stMarkdownContainer"] {{ color:{palette["strong_text"]}; }}
    [data-testid="stDialog"] [role="dialog"] {{ background:{palette["card"]};
        color:{palette["strong_text"]}; border:1px solid {palette["card_border"]}; }}
    [data-testid="stSidebarNav"] [data-testid="stHeading"],
    [data-testid="stSidebarNav"] header, [data-testid="stSidebarNav"] p {{
        color:{palette["sidebar_text"]}; }}
    @media (max-width:640px) {{
        .overview-metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); padding:14px; }}
        .overview-metrics .kpi-value {{ font-size:1.3rem; }}
        .resource-tree li {{ grid-template-columns:1fr; gap:4px; }}
    }}
    .card-title {{ font-size: 1.05rem; font-weight: 600; color: {palette["strong_text"]}; }}
    .page-subtitle {{ color: {palette["text"]}; margin-top: 0; line-height:1.5; }}
    .kpi-label {{ color: {palette["text"]}; font-size: 0.9rem; }}
    .kpi-value {{ font-size: 2rem; font-weight: 700; color: {palette["strong_text"]};
                 line-height: 1.2; }}
    .kpi-note {{ color: {palette["text"]}; font-size: 0.8rem; }}
    .kpi-link {{ margin-left: 10px; font-size: 0.8rem; font-weight: 400; }}
    .card-title {{ display:flex; align-items:flex-start; gap:10px; flex-wrap:wrap; min-width:0; line-height:1.45; padding-bottom:6px; }}
    .card-title > *:not(.card-title-text) {{ flex: none; }}
    .card-title-text {{ min-width: 0; overflow: hidden; text-overflow: ellipsis;
                        white-space:normal; overflow-wrap:break-word; }}
    .card-title .kpi-link {{ margin-left: auto; white-space: nowrap; }}
    [class*="st-key-card_"] {{gap:12px;}}
    [class*="st-key-card_"] [data-testid="stCaptionContainer"] p {{line-height:1.55; margin:0; padding:2px 0 6px;}}
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p {{line-height:1.45; padding-bottom:4px;}}
    .regional-detail td, .regional-detail th, .chart-sample td, .chart-sample th {{line-height:1.5; vertical-align:top;}}
    .compact-header {{row-gap:10px;}}

    .chip {{ display: inline-block; padding: 2px 10px; border-radius: 999px;
            font-size: 0.8rem; font-weight: 600; margin-left: 6px; }}
    .chip-ok {{ background: rgba(12, 163, 12, 0.16);
               color: {charts.get_status_text_color("good", mode)}; }}
    .chip-failed {{ background: rgba(208, 59, 59, 0.16);
                   color: {charts.get_status_text_color("critical", mode)}; }}
    .chip-running {{ background: rgba(57, 135, 229, 0.16);
                    color: {charts.get_status_text_color("running", mode)}; }}
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
    .figure-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
                    margin: 8px 0; }}
    .phone-only {{ display: none; }}
    .diagram-fit {{ width: 100%; min-width: 0; }}
    .diagram-fit img {{ display: block; width: 100%; max-width: 100%; height: auto; }}
    .pipeline-mini {{ width: 100%; overflow-x: auto; padding: 8px 0 2px; }}
    .pipeline-mini svg {{ display: block; width: 100%; min-width: 700px; height: auto; }}
    /* The whole diagram: wide from left to right; on narrow screens (phones,
       tablets, small windows) the wide one would shrink to unreadable text, so
       the vertical version takes its place. */
    .diagram-narrow {{ display: none; max-width: 440px; margin: 0 auto; }}
    @media (max-width: 1000px) {{
        .diagram-wide {{ display: none; }}
        .diagram-narrow {{ display: block; }}
    }}
    {zoom.build_zoom_css(palette)}
    .run-status {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
                   margin: 0 0 10px 0; font-size: 0.9rem; }}
    /* Phones: two figures per row and less empty room above the title, so
       «Empieza aquí» fits on one screen. */
    @media (max-width: 640px) {{
        .figure-grid {{ grid-template-columns: repeat(2, 1fr); }}
        .phone-only {{ display: block; }}
        [data-testid="stMainBlockContainer"] {{ padding-top: 2.5rem; }}
        [class*="st-key-card_start_here"] li {{ font-size: 0.9rem; line-height: 1.4; }}
    }}
    /* Text sections (D-057): a title with one sentence, cards in a grid that stack
       by themselves on narrow screens, numbered steps and folded details. */
    .section-head {{ margin: 22px 0 10px 0; text-align: left; }}
    .section-title {{ font-size: 1.3rem; font-weight: 700; color: {palette["strong_text"]};
                      margin: 0; line-height: 1.3; }}
    .section-lead {{ font-size: 1rem; color: {palette["text"]}; margin: 4px 0 0 0;
                     max-width: 72ch; line-height: 1.5; }}
    .subsection-title {{ font-size: 1.08rem; font-weight: 650; color: {palette["strong_text"]};
                         margin: 0; }}
    .info-grid {{ display: grid; gap: 12px; margin: 6px 0 8px 0;
                  grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); }}
    .info-grid.is-compact {{ align-items: start; }}
    /* Business questions use an editorial layout: the symbol and the words float
       directly on the page, without six repetitive card backgrounds. */
    .question-showcase {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
        column-gap:clamp(28px,4vw,72px); row-gap:clamp(38px,6vw,82px);
        margin:20px 0 36px; align-items:start; }}
    .question-item {{ min-width:0; padding:8px 4px; }}
    .question-item .component-symbol {{ display:block; float:none; width:76px; height:86px;
        margin:0 0 20px; color:{palette["accent"]};
        filter:drop-shadow(0 12px 18px {palette["glow"]});
        transition:transform .28s ease, filter .28s ease; }}
    .question-item:hover .component-symbol {{ transform:translateY(-6px) scale(1.025);
        filter:drop-shadow(0 18px 24px {palette["glow"]}); }}
    .question-number {{ color:{palette["text"]}; font-size:.75rem; font-weight:650;
        letter-spacing:.055em; text-transform:uppercase; margin-bottom:10px; }}
    .question-title {{ color:{palette["strong_text"]}; font-size:clamp(1.15rem,1.45vw,1.48rem);
        font-weight:720; line-height:1.28; max-width:24ch; }}
    .question-scope {{ color:{palette["text"]}; font-size:.94rem; line-height:1.5;
        margin:12px 0 15px; max-width:34ch; }}
    .question-action a {{ color:{palette["accent"]}; font-weight:650;
        text-decoration:none; }}
    .question-action a:hover {{ text-decoration:underline; text-underline-offset:4px; }}
    @media(max-width:900px) {{ .question-showcase {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
    @media(max-width:560px) {{
        .question-showcase {{ grid-template-columns:1fr; row-gap:42px; }}
        .question-item {{ padding:4px 2px; }}
        .question-item .component-symbol {{ width:66px; height:74px; margin-bottom:14px; }}
        .question-title {{ max-width:none; }}
    }}
    .info-card {{ display: flex; flex-direction: column; gap: 6px; min-width: 0;
                  padding: 16px 18px; border-radius: 16px; text-align: left;
                  background: {palette["card"]}; border: 1px solid {palette["card_border"]}; }}
    .info-card.is-warning {{ border-left: 3px solid {palette["rise"]}; }}
    .info-card.is-highlight {{ border: 1px solid {palette["accent"]};
                               box-shadow: 0 0 0 1px {palette["accent"]}33,
                                           0 0 18px {palette["accent"]}33; }}
    .info-label {{ font-size: 0.76rem; letter-spacing: 0.05em; text-transform: uppercase;
                   color: {palette["text"]}; }}
    .info-title {{ font-size: 1.02rem; font-weight: 600; color: {palette["strong_text"]};
                   line-height: 1.35; }}
    .info-text {{ font-size: 0.94rem; color: {palette["strong_text"]}; line-height: 1.5;
                  overflow-wrap: break-word; }}
    .info-note {{ font-size: 0.83rem; color: {palette["text"]}; line-height: 1.45; }}
    .info-link {{ margin-top: auto; padding-top: 4px; font-size: 0.9rem; }}
    .info-card code, .steps code {{ overflow-wrap: anywhere; }}
    .file-list {{ list-style: none; padding: 0 !important; margin: 4px 0 0 0 !important;
                  display: grid; gap: 6px; font-size: 0.9rem; }}
    .file-list li {{ margin: 0; line-height: 1.45; color: {palette["strong_text"]}; }}
    .file-list a {{ font-family: monospace; font-size: 0.86rem; }}
    /* !important: Streamlit indents every list of a Markdown block. */
    .steps {{ list-style: none; counter-reset: step; padding: 0 !important;
              margin: 6px 0 8px 0 !important; display: grid; gap: 10px; }}
    .steps li {{ counter-increment: step; position: relative; min-width: 0; margin: 0;
                 padding: 14px 16px 14px 58px; border-radius: 14px; line-height: 1.5;
                 background: {palette["card"]}; border: 1px solid {palette["card_border"]};
                 color: {palette["strong_text"]}; font-size: 0.94rem; }}
    .steps li::before {{ content: counter(step); position: absolute; left: 16px; top: 13px;
                         width: 28px; height: 28px; border-radius: 50%; font-weight: 700;
                         display: flex; align-items: center; justify-content: center;
                         background: {palette["accent"]}; color: {palette["background"]}; }}
    .stat-line {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 12px;
                  margin: 4px 0 6px 0; }}
    .stat-line strong {{ font-size: 1.35rem; color: {palette["strong_text"]}; }}
    /* Alertas: one row per alert; on phones the row wraps and the bar takes a line. */
    .alert-list {{ list-style: none; padding: 0 !important; margin: 4px 0 !important;
                   display: grid; gap: 8px; }}
    .alert-row {{ display: grid; align-items: center; gap: 4px 12px; margin: 0;
                  grid-template-columns: 7.5rem minmax(0, 1fr) 5.5rem minmax(90px, 160px) 4.5rem;
                  padding: 8px 10px; border-radius: 10px; border: 1px solid {palette["card_border"]};
                  font-size: 0.9rem; color: {palette["strong_text"]}; }}
    .alert-status {{ font-weight: 600; white-space: nowrap; }}
    .alert-product {{ min-width: 0; overflow-wrap: break-word; }}
    .alert-change {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
    .alert-meter {{ position: relative; height: 8px; border-radius: 4px;
                    background: {palette["grid"]}; }}
    .alert-bar {{ position: absolute; left: 0; top: 0; bottom: 0; border-radius: 4px; }}
    .alert-limit {{ position: absolute; top: -4px; bottom: -4px; width: 2px;
                    background: {palette["strong_text"]}; }}
    .alert-distance {{ color: {palette["text"]}; font-size: 0.82rem; white-space: nowrap; }}
    @media (max-width: 640px) {{
        .alert-row {{ grid-template-columns: auto minmax(0, 1fr) auto; }}
        .alert-product {{ grid-column: 1 / -1; order: -1; }}
        .alert-meter {{ grid-column: 1 / -1; }}
    }}
    /* Datos y código (D-060): cards with a soft accent border, titles 14-16 px, text 13 px. */
    .query-meta {{ font-size: 13px; color: {palette["text"]}; margin: 2px 0 6px 0; }}
    .query-meta .chip {{ margin: 2px 4px 2px 0; }}
    /* Código y resultados (C03): the list of questions and the chosen one, sober. */
    .catalog-list-title {{ font-size: 17px; font-weight: 600; color: {palette["strong_text"]};
                           margin: 0 0 6px 0; }}
    .st-key-catalog_list [data-testid="stRadio"] [role="radiogroup"] {{ gap: 2px; }}
    .st-key-catalog_list [data-testid="stRadio"] label {{ width: 100%; padding: 7px 8px;
        border-radius: 6px; border-left: 3px solid transparent; }}
    .st-key-catalog_list [data-testid="stRadio"] label:has(input:checked) {{
        background: {palette["accent"]}14; border-left-color: {palette["accent"]}; }}
    .st-key-catalog_list [data-testid="stRadio"] label p {{ font-size: 14px;
        color: {palette["strong_text"]}; }}
    .catalog-head {{ display: flex; justify-content: space-between; gap: 16px;
                     align-items: flex-start; flex-wrap: wrap; margin-bottom: 8px; }}
    .catalog-question {{ font-size: 26px !important; margin: 0 !important; padding: 0 !important;
                         color: {palette["strong_text"]}; }}
    .catalog-compares {{ margin: 4px 0 2px 0; color: {palette["text"]}; font-size: 15px; }}
    .catalog-facts {{ margin: 0; color: {palette["strong_text"]}; font-size: 14px; }}
    .catalog-steps {{ display: flex; gap: 8px; align-items: center; font-size: 13px;
                      color: {palette["text"]}; flex-wrap: wrap; }}
    .catalog-step b {{ display: inline-flex; width: 22px; height: 22px; border-radius: 50%;
        align-items: center; justify-content: center; margin-right: 5px; font-size: 12px;
        border: 1px solid {palette["card_border"]}; color: {palette["strong_text"]}; }}
    .catalog-block-title {{ display: flex; justify-content: space-between; gap: 12px;
        flex-wrap: wrap; font-size: 16px; font-weight: 600; color: {palette["strong_text"]}; }}
    .catalog-block-title span {{ font-size: 13px; font-weight: 400; color: {palette["text"]}; }}
    .catalog-reading {{ font-size: 14px; color: {palette["text"]}; margin: 4px 0 6px 0; }}
    /* On a phone the list scrolls in its own box, so the result is a short scroll away. */
    @media (max-width: 640px) {{
        .st-key-catalog_list [data-testid="stRadio"] [role="radiogroup"] {{
            max-height: 230px; overflow-y: auto; flex-wrap: nowrap; }}
        .catalog-question {{ font-size: 22px !important; }}
    }}
    /* Consulta por clics (D-060). */
    [class*="st-key-card_search_"] {{ border-color: {palette["accent"]}40; }}
    [class*="st-key-card_search_"] .card-title {{ font-size: 16px; }}
    [class*="st-key-card_search_"] label p {{ font-size: 13px; }}
    [class*="st-key-search_chips"] {{ gap: 6px; margin: 4px 0 10px 0; flex-wrap: wrap; }}
    [class*="st-key-chip_"] button {{ border-radius: 999px; min-height: 30px; padding: 2px 12px;
                                      font-size: 13px; color: {palette["accent"]};
                                      border: 1px solid {palette["accent"]}66;
                                      background: {palette["accent"]}14; }}
    [class*="st-key-chip_"] button:hover {{ background: {palette["accent"]}2a;
                                            color: {palette["accent"]}; }}
    [class*="st-key-alert_card_"] {{ padding: 12px 14px; border-radius: 14px;
                                     background: {palette["background"]};
                                     border: 1px solid {palette["card_border"]}; }}
    .alert-card-label {{ font-size: 14px; font-weight: 600; }}
    [class*="st-key-alert_card_"] button p {{ font-size: 13px; }}
    [class*="st-key-group_breakdown"] button {{ min-height: 3.35rem; height: auto; }}
    [class*="st-key-group_breakdown"] button p {{
        white-space: normal !important; overflow: visible !important;
        text-overflow: clip !important; line-height: 1.25;
    }}
    [class*="st-key-card_search_form"] button[kind="primaryFormSubmit"] {{
        background: {palette["accent"]}; border-color: {palette["accent"]};
        color: {palette["on_accent"]}; }}
    /* Phones: the four state cards in a 2 x 2 grid instead of one column. */
    @media (max-width: 640px) {{
        [class*="st-key-search_kpis"] [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important; gap: 8px !important; }}
        [class*="st-key-search_kpis"] [data-testid="stColumn"] {{
            flex: 1 1 calc(50% - 8px) !important; min-width: calc(50% - 8px) !important; }}
        [class*="st-key-search_kpis"] .kpi-value {{ font-size: 1.5rem; }}
    }}
    .search-count {{ font-size: 13px; color: {palette["text"]}; padding-bottom: 10px; }}
    .detail-facts {{ display: grid; gap: 10px 18px; margin-bottom: 8px;
                     grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }}
    .detail-value {{ font-size: 15px; font-weight: 600; color: {palette["strong_text"]}; }}
    table.card-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    table.card-table th {{ text-align: left; color: {palette["text"]}; font-weight: 500;
                          padding: 6px 4px; border-bottom: 1px solid {palette["card_border"]}; }}
    table.card-table td {{ padding: 8px 4px; border-bottom: 1px solid {palette["card_border"]};
                          color: {palette["strong_text"]}; }}
    .link-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                  gap: 10px; margin: 6px 0; }}
    .link-card {{ display: flex; align-items: center; gap: 8px; min-height: 52px;
                  padding: 8px 10px; border-radius: 12px; background: {palette["card"]};
                  border: 1px solid {palette["card_border"]}; }}
    .link-card a {{ flex: 1; display: flex; align-items: center; gap: 10px;
                    text-decoration: none; min-width: 0; }}
    .link-card .link-icon {{ font-family: "Material Symbols Rounded"; font-size: 22px;
                             color: {palette["accent"]}; }}
    .link-card .link-text {{ display: flex; flex-direction: column; min-width: 0; }}
    .link-card strong {{ color: {palette["strong_text"]}; font-size: 0.9rem; }}
    .link-card small {{ color: {palette["text"]}; font-size: 0.78rem; line-height: 1.3; }}
    .copy-link {{ flex: none; min-height: 36px; padding: 4px 10px; border-radius: 8px;
                  cursor: pointer; font-size: 0.75rem; background: transparent;
                  color: {palette["text"]}; border: 1px solid {palette["card_border"]}; }}
    .copy-link:hover {{ color: {palette["accent"]}; border-color: {palette["accent"]}; }}
    .admin-locked {{ color: {palette["text"]}; font-size: 0.9rem; }}
    {build_code_colors_css(palette)}
    /* Report pages (Dashboard, D-067): one screen like Looker or Power BI. Title and
       freshness on one line, compact figures, tighter cards and gaps. */
    .compact-header {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 14px;
                       margin: 0 0 2px 0; }}
    .compact-header h1 {{ font-size: 1.3rem !important; margin: 0 !important; white-space: nowrap;
                          padding: 0 !important; line-height: 1.25; cursor: help; }}
    .compact-header .page-freshness {{ margin: 0; font-size: 0.8rem; }}
    /* Main navigation views open as a complete panorama. Long tables and
       methodology remain available in folded sections below that overview. */
    [data-testid="stElementContainer"]:has(.overview-viewport-marker) {{display:none;}}
    .stApp:has(.overview-viewport-marker) [data-testid="stMainBlockContainer"] {{
        padding-bottom:8px !important;}}
    .stApp:has(.overview-viewport-marker) .st-key-window_page,
    .stApp:has(.overview-viewport-marker) .st-key-window_page > [data-testid="stVerticalBlock"] {{
        gap:.45rem !important;}}
    .stApp:has(.overview-viewport-marker) [data-testid="stExpander"] summary {{
        min-height:34px; padding:5px 10px;}}
    .stApp:has(.overview-viewport-marker) [data-testid="stExpander"] summary p {{
        font-size:.82rem; line-height:1.2;}}
    .stApp:has(.overview-viewport-marker) hr {{margin:.25rem 0;}}
    /* Pipeline is a one-screen gallery: two detailed diagrams receive the
       available space, while the execution state stays in a compact strip. */
    .stApp:has(.overview-pipeline) [data-testid="stMainBlockContainer"] {{
        padding-bottom:4px!important;}}
    .stApp:has(.overview-pipeline) .pipeline-page-header {{
        display:block; margin:0 0 10px; padding:0;}}
    .stApp:has(.overview-pipeline) .pipeline-page-header h1 {{
        font-size:1.28rem!important; line-height:1.2;}}
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_"] {{
        padding:5px 8px; gap:4px; overflow:hidden;}}
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_"] .card-title {{
        font-size:.92rem; line-height:1.2; padding-bottom:0;}}
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_main"] {{
        min-height:0;}}
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_status"],
    .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_platform"] {{
        height:160px; min-height:160px; overflow:visible;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-link {{
        position:relative; display:flex; align-items:center; justify-content:center;
        width:100%; overflow:hidden; border-radius:10px; text-decoration:none!important;
        cursor:zoom-in; outline:1px solid transparent; transition:background .18s ease,
        outline-color .18s ease;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link {{
        height:clamp(285px,calc(100vh - 420px),760px);}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-secondary-link {{
        height:105px;}}
    .stApp:has(.overview-pipeline) .pipeline-status-content {{
        display:flex; flex-direction:column; min-width:0;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-status-preview {{
        display:flex; align-items:center; justify-content:center; height:83px;
        width:100%; overflow:hidden;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-status-preview svg {{
        display:block; width:100%; height:100%;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-link:hover,
    .stApp:has(.overview-pipeline) .pipeline-gallery-link:focus-visible {{
        background:{palette["accent"]}14; outline-color:{palette["accent"]};}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-link svg {{
        display:block; width:100%; height:100%; max-width:100%; max-height:100%;
        transition:transform .18s ease;}}
    .stApp:has(.overview-pipeline) .pipeline-platform-detailed {{display:none;}}
    .stApp:has(.overview-pipeline) .pipeline-platform-compact {{display:block; width:100%; height:100%;}}
    .stApp:has(.overview-pipeline) .pipeline-platform-compact svg,
    .stApp:has(.overview-pipeline) .pipeline-platform-detailed svg {{
        display:block; width:100%; height:100%;}}
    /* The complete SVG has room between its nodes: use it for larger labels
       in the preview without changing the focused diagram or its geometry. */
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="12"] {{font-size:13px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="13"] {{font-size:15px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="14"] {{font-size:15px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="15"] {{font-size:16px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="16"] {{font-size:17px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-link:hover svg {{transform:scale(1.01);}}
    .stApp:has(.overview-pipeline) .pipeline-open-label {{
        position:absolute; right:8px; bottom:6px; padding:3px 8px; border-radius:999px;
        color:{palette["strong_text"]}; background:{palette["card"]};
        border:1px solid {palette["card_border"]}; font-size:.68rem; font-weight:650;
        box-shadow:0 2px 10px rgba(0,0,0,.18);}}
    .stApp:has(.overview-pipeline) .run-status {{margin-bottom:2px; font-size:.7rem;}}
    .stApp:has(.overview-pipeline) .pipeline-focus-toolbar {{
        display:flex; align-items:center; justify-content:center;
        margin:0 0 5px; min-height:34px;}}
    .stApp:has(.overview-pipeline) .pipeline-focus-toolbar strong {{
        color:{palette["strong_text"]}; font-size:1rem;}}
    .stApp:has(.overview-pipeline) [class*="st-key-pipeline_focus_"] {{
        position:relative; height:calc(100vh - 155px); min-height:0; padding:8px 10px;
        overflow:hidden;
        border:1px solid {palette["card_border"]}; border-radius:14px;
        background:{palette["card"]};}}
    .stApp:has(.overview-pipeline) .pipeline-focus-return {{
        display:flex; justify-content:flex-end; margin:4px 2px 0;}}
    .stApp:has(.overview-pipeline) .pipeline-focus-return a {{
        display:inline-flex; align-items:center; min-height:32px; padding:5px 11px;
        border-radius:999px; border:1px solid {palette["card_border"]};
        background:{palette["card"]}; color:{palette["accent"]};
        box-shadow:0 3px 12px rgba(0,0,0,.15); text-decoration:none; font-size:.76rem;
        font-weight:650;}}
    .stApp:has(.overview-pipeline) .pipeline-focus-return a:hover {{
        border-color:{palette["accent"]};}}
    .stApp:has(.overview-pipeline) [class*="st-key-pipeline_focus_"] .zoom-buttons {{
        position:absolute; left:14px; bottom:12px; z-index:3; margin:0;
        justify-content:flex-start;}}
    .stApp:has(.overview-pipeline) [class*="st-key-pipeline_focus_"] .zoom-viewport {{
        max-height:calc(100vh - 215px);}}
    .stApp:has(.overview-pipeline) [class*="st-key-pipeline_focus_"] .zoom-content svg {{
        max-height:calc(100vh - 215px);}}
    @media (max-height:800px) and (min-width:1001px) {{
        .stApp:has(.overview-pipeline) .pipeline-gallery-main-link {{
            height:clamp(240px,calc(100vh - 440px),320px);}}
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_status"],
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_platform"] {{
            height:175px; min-height:175px;}}
        .stApp:has(.overview-pipeline) .pipeline-gallery-secondary-link {{height:90px;}}
        .stApp:has(.overview-pipeline) .pipeline-gallery-status-preview {{height:68px;}}
    }}
    @media (min-height:1000px) and (min-width:1200px) {{
        .stApp:has(.overview-pipeline) .pipeline-gallery-main-link {{
            height:clamp(420px,42vh,600px);}}
        .stApp:has(.overview-pipeline) [data-testid="stHorizontalBlock"]:has(
            [class*="st-key-card_pipeline_gallery_status"]) {{
            display:flex; flex-direction:column; gap:6px;}}
        .stApp:has(.overview-pipeline) [data-testid="stColumn"]:has(
            [class*="st-key-card_pipeline_gallery_status"]),
        .stApp:has(.overview-pipeline) [data-testid="stColumn"]:has(
            [class*="st-key-card_pipeline_gallery_platform"]) {{
            width:100%!important; flex:0 0 auto!important;}}
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_status"] {{
            height:100px; min-height:100px;}}
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_platform"] {{
            height:clamp(290px,29vh,390px); min-height:0;}}
        .stApp:has(.overview-pipeline) .pipeline-status-content {{
            flex-direction:row; align-items:center; gap:12px; height:65px;}}
        .stApp:has(.overview-pipeline) .pipeline-status-content .run-status {{
            flex:1; min-width:0; margin:0; white-space:nowrap;}}
        .stApp:has(.overview-pipeline) .pipeline-gallery-status-preview {{
            flex:1; min-width:0; height:65px;}}
        .stApp:has(.overview-pipeline) .pipeline-gallery-secondary-link {{
            height:calc(clamp(290px,29vh,390px) - 50px);}}
        .stApp:has(.overview-pipeline) .pipeline-platform-compact {{display:none;}}
        .stApp:has(.overview-pipeline) .pipeline-platform-detailed {{
            display:block; width:100%; height:100%;}}
    }}
    @media (max-width:1000px) {{
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_status"],
        .stApp:has(.overview-pipeline) [class*="st-key-card_pipeline_gallery_platform"] {{
            height:auto; min-height:150px;}}
    }}
    .stApp:has(.overview-history) [data-testid="stVegaLiteChart"] {{max-height:52vh; overflow:hidden;}}
    .stApp:has(.overview-devops) .devops-cycle {{
        width:min(100%,720px,calc((100vh - 260px) * 2.04)); margin:0 auto 3px;}}
    .stApp:has(.overview-devops) .devops-cycle > svg {{max-height:calc(100vh - 260px);}}
    .stApp:has(.overview-kpis) .kpi-register td,
    .stApp:has(.overview-kpis) .kpi-register th {{padding:5px 7px!important; line-height:1.2;}}
    /* The report starts right under the header: the invisible script frame between them
       keeps no band of its own. */
    [class*="st-key-report_page"] {{ gap:1rem; margin-top:0; }}
    [class*="st-key-report_page"] [data-testid="stVerticalBlock"] {{ gap:1rem; }}
    [class*="st-key-report_page"] [class*="st-key-card_"] {{ padding:16px 18px 18px 18px;
                                                              border-radius: 14px; }}
    [class*="st-key-report_page"] .card-title {{ font-size: 0.95rem; margin-bottom: 2px; }}
    [class*="st-key-report_page"] .card-title .component-symbol {{ width: 24px; height: 26px;
                                                                    margin: 0; }}
    [class*="st-key-report_page"] .kpi-link {{ font-size: 0.75rem; }}
    /* Three channels fit on one line in the pulse's field. */
    [class*="st-key-report_page"] [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        font-size: 0.72rem; height: 22px; margin: 1px 3px 1px 0; padding: 0 4px 0 6px; }}
    [class*="st-key-report_page"] .overview-metric .component-symbol {{ width: 22px; height: 22px;
                                                                        margin: 0 6px 0 0; }}
    [class*="st-key-report_page"] .overview-metric .kpi-label {{ font-size: 0.82rem; }}
    [class*="st-key-report_page"] .overview-metric .market-metric-note {{ font-size: 0.72rem;
                                                                          margin: 0; }}
    [class*="st-key-report_page"] .overview-metrics {{ gap: 8px !important;
                                                       margin: 0 0 4px 0 !important; }}
    /* Each figure on one line: its name left, its value right. */
    [class*="st-key-report_page"] .overview-metrics > .overview-metric {{ padding:6px 12px !important; }}
    [class*="st-key-report_page"] .overview-metrics .market-metric-heading {{ margin: 0 !important; }}
    [class*="st-key-report_page"] .overview-metrics .kpi-value {{ font-size: 1.25rem !important;
                                                                  line-height: 1.2 !important;
                                                                  white-space: nowrap; }}
    [class*="st-key-report_page"] .market-eyebrow {{ display: none; }}
    .summary-sentence {{ font-size: 0.95rem; font-weight: 600; color: {palette["strong_text"]};
                         margin: 0 0 6px 0; line-height: 1.35; }}
    .context-line {{ font-size: 0.75rem; color: {palette["text"]}; margin: 0; }}
    [class*="st-key-report_page"] [data-testid="stHorizontalBlock"] {{ gap:14px; }}
    .st-key-dashboard_filter_bar {{ padding:10px 14px 8px; margin:4px 0 2px;
        background:{palette["card"]}; border:1px solid {palette["card_border"]}; border-radius:14px; }}
    [class*="st-key-report_page"] [data-testid="stCaptionContainer"] {{ margin: 0; }}
    /* Bold text of the side menu takes the menu's own ink (navy menu in Corporativo). */
    [data-testid="stSidebar"] strong {{ color: {palette["sidebar_text"]}; }}
    /* Every list of the page stands out from what is behind it: its own fill and a
       visible border, the accent on hover and focus (D-060). */
    [data-testid="stMain"] :is([data-testid="stSelectbox"], [data-testid="stMultiSelect"])
        .react-aria-ComboBox > div {{
        background: {palette["field"]} !important;
        border: 1px solid {palette["reference"]}99 !important; border-radius: 10px !important;
    }}
    [data-testid="stMain"] :is([data-testid="stSelectbox"], [data-testid="stMultiSelect"])
        .react-aria-ComboBox > div:hover,
    [data-testid="stMain"] :is([data-testid="stSelectbox"], [data-testid="stMultiSelect"])
        .react-aria-ComboBox > div:focus-within {{
        border-color: {palette["accent"]} !important;
    }}
    /* A text field inside a card stands out from the card around it. */
    [class*="st-key-card_"] [data-testid="stTextInputRootElement"] {{
        background: {palette["background"]} !important;
        border-color: {palette["reference"]} !important;
    }}
    /* Long file paths wrap inside their cell on phones; words do not break. */
    table.card-table td a {{ overflow-wrap: anywhere; }}
    /* The cover (C01): flat and quiet; thin rules separate its rows, no cards per line. */
    .st-key-cover_top {{ justify-content:space-between; flex-wrap:wrap !important; gap:8px 16px;
        margin-bottom:6px; }}
    .st-key-cover_top > div {{ width:auto !important; flex:0 1 auto; }}
    .st-key-cover_top [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
    .st-key-cover_top [data-testid="stMarkdownContainer"] p {{ margin:0; }}
    .cover-eyebrow {{ color:{palette["text"]}; font-size:.76rem; font-weight:600;
        letter-spacing:.14em; text-transform:uppercase; }}
    a.cover-github {{ display:inline-block; padding:7px 14px; border:1px solid {palette["card_border"]};
        border-radius:10px; color:{palette["strong_text"]} !important; font-size:.88rem;
        font-weight:600; text-decoration:none; white-space:nowrap; }}
    a.cover-github:hover, a.cover-github:focus-visible {{ border-color:{palette["accent"]}; }}
    [data-testid="stMain"] .st-key-cover_hero h1 {{ font-size:clamp(2.5rem,5vw,3.7rem);
        font-weight:800; letter-spacing:-.02em; line-height:1.05; padding:0; margin:0 0 10px;
        color:{palette["strong_text"]}; }}
    .cover-tagline {{ color:{palette["strong_text"]}; font-size:clamp(1.2rem,2.1vw,1.6rem);
        font-weight:700; line-height:1.25; margin:0 0 12px; }}
    .cover-tagline span {{ display:block; color:{palette["accent"]}; }}
    /* Links of the cover say where they go: the icon of the target window is noise. */
    [class*="st-key-cover_"] [data-testid="stPageLink"] a > span:has([data-testid="stIconMaterial"]) {{
        display:none; }}
    .cover-lead {{ color:{palette["text"]}; font-size:1.06rem; line-height:1.5; margin:0 0 6px;
        max-width:34em; }}
    .st-key-cover_actions {{ flex-wrap:wrap !important; gap:12px; margin-top:4px; }}
    .st-key-cover_actions > div {{ width:auto !important; flex:0 0 auto; }}
    :is(.st-key-cover_primary, .st-key-cover_secondary) [data-testid="stPageLink"] a,
    :is(.st-key-cover_primary, .st-key-cover_secondary) a {{ display:inline-flex;
        align-items:center; padding:9px 18px; border-radius:10px; text-decoration:none;
        border:1px solid {palette["card_border"]}; background:transparent; }}
    .st-key-cover_primary [data-testid="stPageLink"] a, .st-key-cover_primary a {{
        background:{palette["accent"]}; border-color:{palette["accent"]}; }}
    .st-key-cover_primary a, .st-key-cover_primary a * {{ color:{palette["on_accent"]} !important;
        font-weight:600; }}
    .st-key-cover_secondary a, .st-key-cover_secondary a * {{ color:{palette["strong_text"]} !important;
        font-weight:600; }}
    .st-key-cover_primary a:hover {{ filter:brightness(1.08); }}
    .st-key-cover_secondary a:hover {{ border-color:{palette["accent"]}; }}
    .cover-figures {{ border:1px solid {palette["card_border"]}; border-radius:14px;
        background:{palette["card"]}; padding:18px 22px 14px; }}
    .cover-figures-title {{ color:{palette["strong_text"]}; font-weight:700; font-size:.95rem;
        margin-bottom:10px; }}
    .cover-figures dl {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
        gap:16px 22px; margin:0; }}
    .cover-figures dt {{ color:{palette["text"]}; font-size:.8rem; font-weight:600; }}
    .cover-figures dd {{ color:{palette["strong_text"]}; font-size:1.75rem; font-weight:700;
        margin:2px 0 0; line-height:1.15; font-variant-numeric:tabular-nums; }}
    .cover-figures dl span {{ color:{palette["text"]}; font-size:.78rem; }}
    .cover-figures p {{ color:{palette["text"]}; font-size:.74rem; margin:14px 0 0;
        padding-top:10px; border-top:1px solid {palette["grid"]}; }}
    .cover-statements {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
        margin:26px 0 0; padding:20px 0; border-top:1px solid {palette["card_border"]};
        border-bottom:1px solid {palette["card_border"]}; }}
    .cover-statements .cover-statement {{ padding:0 22px; }}
    .cover-statements .cover-statement:first-child {{ padding-left:0; }}
    .cover-statements .cover-statement + .cover-statement {{
        border-left:1px solid {palette["card_border"]}; }}
    .cover-statement {{ display:flex; gap:14px; align-items:flex-start; }}
    .cover-statement .component-symbol {{ width:28px; height:32px; margin:2px 0 0; }}
    .cover-statement h3 {{ color:{palette["strong_text"]}; font-size:1.08rem; font-weight:700;
        margin:0 0 4px; padding:0; }}
    .cover-statement p {{ color:{palette["text"]}; margin:0; line-height:1.45; }}
    .cover-heading {{ color:{palette["strong_text"]}; font-size:1.5rem !important;
        font-weight:700; margin:22px 0 4px !important; padding:0 !important; }}
    .st-key-cover_evidence {{ gap:0 !important; flex-wrap:nowrap !important;
        padding-bottom:18px; border-bottom:1px solid {palette["card_border"]}; }}
    .st-key-cover_evidence > div {{ flex:1 1 0 !important; min-width:0; }}
    [class*="st-key-cover_evidence_"]:not([class*="_link_"]) {{ padding:0 22px; height:100%; }}
    .st-key-cover_evidence > div:first-child [class*="st-key-cover_evidence_"] {{ padding-left:0; }}
    .st-key-cover_evidence > div + div {{ border-left:1px solid {palette["card_border"]}; }}
    .cover-evidence-title {{ color:{palette["strong_text"]}; font-weight:700; font-size:1.05rem;
        margin-bottom:4px; }}
    .cover-evidence-title span {{ color:{palette["accent"]}; margin-right:10px;
        font-variant-numeric:tabular-nums; }}
    .cover-evidence p {{ color:{palette["text"]}; margin:0 0 6px; line-height:1.45; }}
    .cover-evidence p.cover-evidence-figure {{ color:{palette["strong_text"]}; font-size:.9rem;
        font-weight:600; }}
    :is([class*="st-key-cover_evidence_link_"], .st-key-cover_offer_link,
        .st-key-cover_limits_link) [data-testid="stPageLink"] a {{ padding:0; min-height:0;
        background:transparent !important; }}
    :is([class*="st-key-cover_evidence_link_"], .st-key-cover_offer_link,
        .st-key-cover_limits_link) a, :is([class*="st-key-cover_evidence_link_"],
        .st-key-cover_offer_link, .st-key-cover_limits_link) a * {{
        color:{palette["accent"]} !important; font-weight:600; }}
    .st-key-cover_closing {{ gap:0 !important; flex-wrap:nowrap !important; padding-top:18px; }}
    .st-key-cover_closing > div {{ flex:1 1 0 !important; min-width:0; }}
    .st-key-cover_closing > div + div {{ border-left:1px solid {palette["card_border"]}; }}
    .st-key-cover_offer {{ padding-right:22px; }}
    .st-key-cover_limits {{ padding-left:22px; }}
    :is(.st-key-cover_offer_link, .st-key-cover_limits_link) {{ padding-left:42px; }}
    .st-key-profile_choice {{ margin-top:18px; }}
    @media(max-width:900px) {{
        .cover-statements {{ grid-template-columns:1fr; padding:6px 0; }}
        .cover-statements .cover-statement {{ padding:14px 0; }}
        .cover-statements .cover-statement + .cover-statement {{ border-left:none;
            border-top:1px solid {palette["grid"]}; }}
        .st-key-cover_evidence, .st-key-cover_closing {{ flex-wrap:wrap !important; }}
        .st-key-cover_evidence > div, .st-key-cover_closing > div {{ flex:1 1 100% !important; }}
        .st-key-cover_evidence > div + div, .st-key-cover_closing > div + div {{ border-left:none;
            border-top:1px solid {palette["grid"]}; }}
        [class*="st-key-cover_evidence_"]:not([class*="_link_"]) {{ padding:12px 0; }}
        .st-key-cover_offer, .st-key-cover_limits {{ padding:12px 0; }}
    }}
    @media(max-width:640px) {{
        .app-brand span {{ display:inline; }}
        .kpi-strip-item {{ flex:1 1 45%; border-left:none; padding-left:4px; }}
        .kpi-strip-value {{ font-size:1.35rem; }}
        .st-key-report_filters > div:has(> [class*="st-key-bar_"]) {{ flex:1 1 100%; }}
    }}
    """


def apply_style(mode):
    """Add the dashboard CSS to the page."""
    st.markdown(f"<style>{build_style_css(mode)}</style>", unsafe_allow_html=True)



OVERVIEW_CLASS_BY_VIEW = {
    PAGE_HOME: "overview-dashboard",
    PAGE_SEASONALITY: "overview-history",
    PAGE_KPI: "overview-kpis",
    PAGE_DIAGRAMS: "overview-pipeline",
    PAGE_ARCHITECTURE: "overview-model",
    PAGE_DEVOPS: "overview-devops",
}


GRAPH_HELP = {
    PAGE_DATA: "Consulta precios semanales, variaciones y brechas; filtra y recorre los registros de la base.",
    PAGE_HOME: "Resumen de precios: cambios de esta semana, evolución y comparación regional.",
    PAGE_ANALYSIS: "Esta semana: los precios que más subieron y bajaron frente a la semana anterior.",
    PAGE_GAP: "Brecha: cuánto más cuesta al consumidor que al mayorista, para el mismo producto, unidad, región y semana. No es ganancia.",
    PAGE_CHANNELS: "Regiones: compara dónde y en qué canal cuesta más el mismo producto.",
    PAGE_ALERTS: "Alertas: cambios semanales poco habituales que conviene revisar; no prueban un error.",
    PAGE_SEASONALITY: "Contexto del precio: si el precio de esta semana es normal, dónde conviene comprar y qué suele pasar. No es una predicción.",
    PAGE_KPI: "KPI significa indicador clave: consulta su valor, periodo, comparación, fórmula y límites.",
    PAGE_DIAGRAMS: "Pipeline: pasos que descargan, transforman y validan los datos antes de mostrarlos.",
    PAGE_ARCHITECTURE: "Modelo: tablas, relaciones y claves que organizan los datos del proyecto.",
    PAGE_DEVOPS: "DevOps: cómo se automatizan las pruebas, las cargas y la operación del proyecto.",
}


def show_reading_guide():
    terms = {"Brecha": "Diferencia entre precio al consumidor y mayorista. Mayorista $1.000 y consumidor $1.300: brecha de 30 %. No mide ganancia.",
             "Variación": "Cambio frente a la semana anterior: positivo subió, negativo bajó.",
             "Índice": "Compara con una referencia: 100 significa igual al promedio si el gráfico usa base 100; en base 1, la referencia es 1.",
             "Mediana": "Valor del centro al ordenar los resultados; resume el cambio típico sin dejar que un valor extremo domine.",
             "Filas visibles": "Límite de productos por familia. El extremo derecho muestra todos los resultados disponibles."}
    words = [f'<span class="hint reading-term" tabindex="0" role="button" aria-label="{html.escape(text, quote=True)}" data-hint="{html.escape(text, quote=True)}">{name}</span>' for name, text in terms.items()]
    st.markdown('<div class="reading-guide">Ayuda al pasar el cursor: ' + ' · '.join(words) + '</div>', unsafe_allow_html=True)


def show_data_sample(frame, title="Muestra del gráfico · primeros 3 resultados"):
    """Small visible sample from exactly the displayed data, not a second ranking."""
    if frame.empty:
        return
    sample = frame.head(3).fillna("—")
    meanings = {"Variación": "Cambio frente a la semana anterior. Un valor negativo significa que bajó.",
                "Precio nacional": "Promedio simple de las regiones con datos, sin ponderar por población ni ventas.",
                "Mayorista": "Precio observado en el canal mayorista, para la unidad indicada.",
                "Consumidor": "Precio observado en el canal de venta al consumidor, para la misma unidad.",
                "Diferencia": "Porcentaje sobre el precio mayorista; no mide ganancia.",
                "Índice": "Precio frente a su referencia; consulta si el gráfico usa base 1 o base 100.",
                "Índice (100 = promedio anual)": "100 = promedio de las semanas disponibles del año; 120 = 20 % por encima.",
                "Canal": "Tipo de punto de venta, como feria libre o supermercado.",
                "Unidad": "Cantidad de referencia del precio: kilo, unidad u otra unidad normalizada."}
    headers = [f'<span class="hint reading-term" tabindex="0" role="button" aria-label="{html.escape(meanings[str(c)], quote=True)}" data-hint="{html.escape(meanings[str(c)], quote=True)}">{html.escape(str(c))}</span>'
               if str(c) in meanings else html.escape(str(c)) for c in sample.columns]
    heading = "".join(f'<th scope="col">{value}</th>' for value in headers)
    body = "".join('<tr>' + ''.join(f'<td>{html.escape(str(value))}</td>' for value in row) + '</tr>'
                   for row in sample.itertuples(index=False, name=None))
    st.markdown('<div class="chart-sample"><div class="sample-title">' + html.escape(title) + '</div>' +
                '<table class="card-table"><thead><tr>' + heading + '</tr></thead><tbody>' + body + '</tbody></table>' +
                ('<div class="sample-title">Precios redondeados para leerlos; los porcentajes usan los valores completos.</div>' if any(column in sample.columns for column in ('Precio nacional', 'Mayorista', 'Consumidor')) else '') + '</div>', unsafe_allow_html=True)


def is_dark_surface(color):
    """Whether a hex surface needs the luminous brand colors."""
    rgb = tuple(int(color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return sum(rgb) / 3 < .5


def build_greenocean_logo(mode, sidebar=False):
    """Transparent wordmark, displayed by Streamlit outside the navigation links."""
    background = charts.get_palette(mode)["sidebar" if sidebar else "background"]
    dark = is_dark_surface(background)
    green, ocean = (BRAND_GREEN_DARK, "#80baff") if dark else (BRAND_GREEN_LIGHT, "#185ca8")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="190" height="36" viewBox="0 0 190 36">'
            '<title>GreenOcean</title>'
            '<text x="0" y="27" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" '
            'font-size="28" font-weight="500" letter-spacing="-.8">'
            f'<tspan fill="{green}">Green</tspan><tspan fill="{ocean}">Ocean</tspan></text></svg>')



def show_app_header(window):
    """Shared, sober graphic navigation, followed by preferences and location."""
    palette = charts.get_palette(get_mode())
    st.logo(build_greenocean_logo(get_mode(), sidebar=True),
            icon_image=build_greenocean_logo(get_mode()), size="large")
    st.markdown(f"""<style>
    [data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"] > style:only-child) {{display:none;}}
    .stApp:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMainBlockContainer"] {{padding-top:54px !important;}}
    .reading-guide {{font-size:.8rem; margin:5px 0 14px; color:{palette['text']};}}
    .reading-term {{font-size:inherit; margin-left:0; border-bottom:1px dotted currentColor; font-weight:400;}}
    .regional-detail {{width:100%; font-size:.75rem; border-collapse:collapse;}}
    .regional-detail td, .regional-detail th {{padding:5px 6px!important; text-align:left;}}
    .chart-sample {{margin-top:8px; padding-bottom:12px; overflow-x:auto;}}
    .sample-title {{font-size:.75rem; color:{palette['text']}; margin-bottom:4px;}}
    .chart-sample table {{width:100%; font-size:.75rem; border-collapse:collapse;}}
    .chart-sample td, .chart-sample th {{padding:5px 7px; text-align:left; white-space:normal; border-bottom:1px solid {palette['card_border']};}}

    [data-testid="stMarkdownContainer"]:has(> .report-title) {{margin-bottom:0;}}
    .report-title p {{display:flex; flex-wrap:wrap; align-items:center; gap:6px 12px; margin:8px 0 12px;}}
    .st-key-report_page .card-title {{flex-wrap:wrap; align-items:flex-start;}}
    .st-key-report_page .card-title-text {{flex:1 1 140px; white-space:normal; overflow:visible;}}
    .st-key-report_page [data-testid="stCaptionContainer"] {{overflow-wrap:anywhere;}}
    /* The page's path, Volver and the theme choice: the only header on every page (D-096). */
    .st-key-app_header {{background:transparent; border:0; border-bottom:1px solid {palette['card_border']};
        border-radius:0; padding:4px 0 8px !important; margin:0 0 6px; justify-content:space-between;
        flex-wrap:wrap !important; row-gap:6px;}}
    .st-key-app_header .app-brand {{font-size:.86rem; font-weight:600; color:{palette['strong_text']};
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}}
    .st-key-header_preferences {{flex-wrap:nowrap !important; align-items:center; gap:8px; width:auto !important;
        margin-left:auto;}}
    .st-key-header_preferences > div {{flex:none; min-width:0;}}
    .st-key-header_preferences [data-testid="stPopover"] button {{width:40px; min-width:40px; padding:8px;}}
    .st-key-header_preferences [data-testid="stPopover"] button p {{position:absolute; width:1px;
        height:1px; overflow:hidden; clip-path:inset(50%);}}
    .st-key-window_page [data-testid="stMarkdownContainer"] h3 {{font-size:1.2rem; font-weight:500;}}
    .st-key-window_page [data-testid="stMarkdownContainer"] p,
    .st-key-window_page [data-testid="stMarkdownContainer"] li {{
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.65;}}
    .block-container, [data-testid="stMainBlockContainer"] {{padding-top:1rem !important; padding-bottom:.5rem !important;}}
    [data-testid="stSidebarNav"] p, [data-testid="stSidebar"] [data-testid="stPageLink"] p {{
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; font-weight:400; letter-spacing:-.015em;}}
    @media(max-width:700px) {{
        .st-key-app_header .app-brand {{white-space:normal; flex:1 1 100%; order:1;}}
        .st-key-header_preferences {{order:2; margin-left:0;}}
    }}
    </style>""", unsafe_allow_html=True)
    view = read_current_view(window)
    # Contexto del precio draws its own route and «Volver al resumen»: showing the
    # generic path and Volver here too would duplicate them (D-098). Appearance now
    # lives in the shared sidebar footer, where it stays available without competing
    # with the page title.
    minimal = view == PAGE_SEASONALITY
    window_label = SIDEBAR_TOP_LABELS.get(window, window)
    path = window_label if len(read_window_views(window)) == 1 else f"{window_label} › {SIDEBAR_LABELS.get(view, view)}"
    with st.container(key="app_header", horizontal=True, vertical_alignment="center"):
        if not minimal:
            st.markdown(f'<div class="app-brand" aria-label="Página actual">{html.escape(path)}</div>',
                        unsafe_allow_html=True)
        if not minimal:
            with st.container(key="header_preferences", horizontal=True):
                if st.button("Volver", icon=":material/arrow_back:", key="return_to_previous",
                             help="Volver al punto anterior del proyecto, con su selección."):
                    st.html(RETURN_ACTION_SCRIPT, unsafe_allow_javascript=True)
    theme = get_mode()
    match_base_mode(theme)
    return theme


def show_theme_field():
    """A compact appearance icon; four named choices remain accessible."""
    st.session_state["theme_field"] = get_mode()
    icon = ":material/dark_mode:" if charts.get_palette(get_mode())["base"] == "dark" else ":material/light_mode:"
    with st.popover("Apariencia", icon=icon, help="Cambiar los colores: Corporativo, Vantablack, Blue Light o Dark Grey."):
        st.radio("Apariencia del panel", charts.THEMES, key="theme_field", on_change=keep_theme_from_field)



def open_card(key, title=None, caption=None, hint=None, kpi=None):
    """A rounded card; use it with 'with'. The key must be unique on the page.

    hint, when given, is a short explanation in plain words that appears when
    the mouse passes over the ⓘ next to the title. kpi is only the internal
    destination identifier; visitors see a plain «Cómo se calcula» link.
    """
    card = st.container(key=f"card_{key}")
    hint_icon = build_hint_icon(hint) if hint else ""
    if kpi:
        definition = {"K1": "brecha entre consumidor y mayorista", "K2": "brecha entre canales",
                      "K3": "índice de precio regional", "K4": "estacionalidad de precios",
                      "K5": "rezago descriptivo", "K6": "variaciones y alertas",
                      "K7": "cobertura de productos comparables", "K8": "filas rechazadas"}
        hint = (hint + " " if hint else "") + (
            "Este cálculo corresponde a " + definition.get(kpi, "un indicador del proyecto") + ".")
        hint_icon = build_hint_icon(hint)
    kpi_link = build_kpi_link(kpi) if kpi else ""
    if title or hint:
        # One line: the title shortens with «…» (whole on hover); ⓘ and the link stay whole.
        card.markdown(f'<div class="card-title">{build_component_symbol(component_kind(key, title))}'
                      f'<span class="card-title-text" title="{html.escape(title or "")}">'
                      f'{html.escape(title or "")}</span>{hint_icon}{kpi_link}</div>',
                      unsafe_allow_html=True)
    if caption:
        card.caption(caption)
    return card


def build_hint_icon(hint):
    """An ⓘ that shows a short explanation when the mouse passes over it, or when
    it is tapped on a phone (tabindex makes it focusable)."""
    # Explain identifiers inline, so a visitor never needs to guess an acronym.
    terms = {"KPI": "indicador clave de desempeño", "SQL": "lenguaje de consultas",
             "BI": "inteligencia de negocios", "BA": "análisis de negocio"}
    plain = hint.replace("**", "")
    used = [f"{term}: {meaning}" for term, meaning in terms.items()
            if re.search(rf"\b{term}\b", plain)]
    if used:
        plain += " · " + "; ".join(used) + "."
    plain_hint = html.escape(plain, quote=True)
    return (f'<span class="hint" tabindex="0" role="button" aria-label="{plain_hint}" '
            f'data-hint="{plain_hint}">ⓘ</span>')


def build_page_address(page_title, tab=None, kpi=None):
    """Relative address of a page, one of its tabs or a KPI card."""
    legacy_gap = page_title == PAGE_GAP
    page_title = {PAGE_ANALYSIS: PAGE_HOME, PAGE_GAP: PAGE_DATA, PAGE_CHANNELS: PAGE_DATA}.get(page_title, page_title)
    parameters = {"datos_modo":"brecha"} if legacy_gap else {}
    theme = st.session_state.get(THEME_STATE)
    if theme in charts.THEMES:
        parameters[THEME_PARAMETER] = theme
    if tab:
        parameters[TAB_PARAMETER] = tab
    if kpi:
        parameters[KPI_PARAMETER] = kpi
    window = WINDOW_OF_VIEW.get(page_title, page_title)
    if page_title in WINDOW_OF_VIEW and page_title != read_window_views(window)[0]:
        parameters[VIEW_PARAMETER] = page_title
    query = f"?{urlencode(parameters)}" if parameters else ""
    # The first window is the home page: Streamlit serves it at the root of the app.
    path = "./" if window == start_window() else WINDOW_PATHS[window]
    return path + query


def build_place_address(place):
    """Address of a place named in a document: a page or a tab of a page."""
    if place == "Inicio":  # historical document labels
        return build_page_address(PAGE_HOME)
    if place in PAGE_OF_TAB:
        page = PAGE_OF_TAB[place]
        return build_page_address(page, place if place in TABS_BY_PAGE[page] else None)
    return build_page_address(place)


def build_link_html(text, address):
    """A link that opens in the same tab, with already-escaped text."""
    return f'<a href="{html.escape(address)}" target="_self">{html.escape(text)}</a>'


def build_kpi_link(kpi):
    """Open an indicator's explanation without exposing its internal K-code."""
    address = build_page_address(PAGE_KPI, kpi=kpi)
    if st.session_state.get(COMPACT_VIEW):
        return (f'<span class="kpi-link" title="Abrir la explicación del cálculo">'
                f'{build_link_html("Cómo se calcula →", address)}</span>')
    return (f'<span class="kpi-link">{build_link_html("¿Cómo se calcula?", address)}'
            '</span>')


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


def build_svg_image_html(svg, css_class="", is_actual_size=False):
    """An SVG drawing as an image tag, so CSS can show it only on some screens.

    At actual size it keeps its own width (inside a box that scrolls sideways)
    instead of shrinking to the screen, so its text stays readable.
    """
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    size = "" if is_actual_size else ' style="width:100%"'
    return (f'<div class="{css_class}"><img src="data:image/svg+xml;base64,{data}"{size} '
            f'alt="Recorrido de los datos"></div>')


# Copies the address of a link card without showing it. One listener for the
# whole page, so a block drawn twice does not copy twice.
COPY_LINK_SCRIPT = """<script>
if (!window.linkCardsReady) {
    window.linkCardsReady = true;
    document.addEventListener("click", (event) => {
        const button = event.target.closest(".copy-link");
        if (!button) { return; }
        const link = button.closest(".link-card").querySelector("a");
        const show = (text) => {
            button.textContent = text;
            setTimeout(() => { button.textContent = "Copiar enlace"; }, 1500);
        };
        // Older browsers, or a page without focus: a hidden field and the copy command.
        const copyWithField = () => {
            const field = document.createElement("textarea");
            field.value = link.href;
            field.style.position = "fixed";
            field.style.opacity = "0";
            document.body.appendChild(field);
            field.select();
            const copied = document.execCommand("copy");
            field.remove();
            show(copied ? "Copiado ✓" : "No se pudo copiar");
        };
        if (navigator.clipboard) {
            navigator.clipboard.writeText(link.href).then(() => show("Copiado ✓"), copyWithField);
        } else {
            copyWithField();
        }
    });
}
</script>"""


def build_link_card_html(link):
    """Name, icon and one line of description; the address is never shown as text."""
    # Same window: the browser's back button returns here; the visitor may still open a
    # new tab on purpose (D-070).
    return (f'<div class="link-card"><a href="{html.escape(link["url"], quote=True)}" '
            f'rel="noopener"><span class="link-icon">{link["icon"]}</span>'
            f'<span class="link-text"><strong>{html.escape(link["name"])} ↗</strong>'
            f'<small>{html.escape(link["description"])}</small></span></a>'
            f'<button type="button" class="copy-link">Copiar enlace</button></div>')


def build_link_cards_html(links):
    """A grid of link cards; links without an address (not published yet) stay out."""
    cards = "".join(build_link_card_html(link) for link in links if link["url"])
    return f'<div class="link-grid">{cards}</div>'


def show_link_cards(links):
    """Draw link cards to outside services, each with its «Copiar enlace» button."""
    st.html(build_link_cards_html(links) + COPY_LINK_SCRIPT, unsafe_allow_javascript=True)


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
    if {"variety", "normalized_unit"} <= set(rows.columns):
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
def read_cached_key_options(query_name, database_version):
    """Product keys of one indicator with their number of rows (D-050)."""
    return add_display_columns(queries.list_query_keys(query_name))


def read_key_options(query_name):
    """Product keys offered by the filters of one indicator."""
    return read_cached_key_options(query_name, get_database_version())


@st.cache_data
def read_cached_rows_for_key(query_name, key_items, database_version):
    """Rows of one indicator for one product key, filtered by SQLite (D-050)."""
    return add_display_columns(queries.run_query_for_key(query_name, dict(key_items)))


def read_indicator_for_key(query_name, key):
    """Rows of one indicator for the chosen product key."""
    return read_cached_rows_for_key(query_name, tuple(sorted(key.items())),
                                    get_database_version())


def read_week_range():
    """First and last week loaded in the data warehouse, with their years."""
    return read_indicator("quality_week_range").iloc[0]


def read_latest_week():
    """Monday of the latest week with prices."""
    return pd.Timestamp(read_week_range()["last_week"])


def describe_loaded_years():
    """'año 2026' or 'años 2022 a 2026', from the weeks really loaded in datos.db."""
    week_range = read_week_range()
    if week_range["first_year"] == week_range["last_year"]:
        return f"año {week_range['last_year']}"
    return f"años {week_range['first_year']} a {week_range['last_year']}"


@st.cache_data
def read_cached_price_alerts(database_version):
    """K6 alerts of every week, computed once per database."""
    prices = queries.run_query("k6_national_weekly_price")
    return add_display_columns(alerts.find_price_alerts(prices))


def read_price_alerts():
    """K6 alerts for the current database."""
    return read_cached_price_alerts(get_database_version())


@st.cache_data
def read_cached_match_coverage(database_version):
    """K7, computed once per database: its query crosses the whole price table."""
    connection = queries.open_database()
    coverage = etl.measure_match_coverage(connection)
    connection.close()
    return coverage


def read_match_coverage():
    """K7 as (keys with margin, consumer keys)."""
    return read_cached_match_coverage(get_database_version())


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


def recall_filter(name, default=None):
    """The value the reader chose last for one filter of Análisis, or default."""
    return st.session_state.get(f"analysis_{name}", default)


def remember_filter(name, value):
    """Keep a filter of Análisis, so it holds in every tab and after leaving the page."""
    st.session_state[f"analysis_{name}"] = value
    return value


def choose_product_key(query_name, columns=None):
    """Group, product and variety/quality/unit chosen by the reader, as a key.

    The options come from the indicator; only the chosen key is read later.
    columns, when given, are the three places for the three choices. Inside the report,
    the category of the report's bar fixes the group (D-069).
    """
    options = read_key_options(query_name)
    group_column, product_column, key_column = columns or st.columns(3)
    report_group = read_filter("group") if st.session_state.get(COMPACT_VIEW) else ALL_VALUES
    with group_column:
        if report_group != ALL_VALUES and report_group in set(options["product_group"]):
            group = report_group
            st.markdown(f'<div class="fixed-filter"><span class="kpi-label">Grupo</span>'
                        f'<strong>{html.escape(group)}</strong><small>desde la barra del '
                        f'informe</small></div>', unsafe_allow_html=True)
        else:
            group = remember_filter("group", choose_value(
                "Grupo", options["product_group"].unique(),
                recall_filter("group", DEFAULT_GROUP)))
    options = options[options["product_group"] == group]
    with product_column:
        product = remember_filter("product", choose_value(
            "Producto", options["product"].unique(), recall_filter("product", DEFAULT_PRODUCT)))
    options = options[options["product"] == product]
    with key_column:
        # The key with most data goes first, so the page opens with a full chart.
        labels = options.sort_values("row_count", ascending=False)["key_label"].to_list()
        remembered = recall_filter("key_label")
        key_label = remember_filter("key_label", st.selectbox(
            "Variedad · calidad · unidad", labels,
            index=labels.index(remembered) if remembered in labels else 0))
    chosen = options[options["key_label"] == key_label].iloc[0]
    return {column: chosen[column] for column in queries.KEY_COLUMNS}


# endregion


# region Text sections
def format_inline(text):
    """Escaped text with the two marks the documents use: **bold** and `code`."""
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)


def show_section_intro(title, lead, is_subsection=False):
    """A section title and one sentence that says what the section is for."""
    title_class = "subsection-title" if is_subsection else "section-title"
    st.markdown(f'<div class="section-head"><div class="{title_class}">{html.escape(title)}'
                f'</div><div class="section-lead">{format_inline(lead)}</div></div>',
                unsafe_allow_html=True)


def capitalize_first(text):
    """A text that may come from the middle of a sentence, starting in upper case."""
    return text[:1].upper() + text[1:]


COMPONENT_SYMBOLS = {
    "security": '<path d="M16 2 29 7v11c0 8-6 13-13 16C9 31 3 26 3 18V7Z"/><path d="m10 18 4 4 8-9"/>',
    "database": '<ellipse cx="16" cy="7" rx="12" ry="4"/><path d="M4 7v20c0 6 24 6 24 0V7M4 17c0 6 24 6 24 0"/>',
    "workflow": '<rect x="2" y="12" width="8" height="10" rx="2"/><rect x="22" y="12" width="8" height="10" rx="2"/><path d="M11 17h10m-4-4 4 4-4 4"/>',
    "document": '<path d="M7 2h13l7 7v23H7Z M20 2v8h7M11 16h12M11 21h12M11 26h8"/>',
    "code": '<rect x="2" y="4" width="28" height="26" rx="3"/><path d="M2 10h28m-19 6-5 4 5 4m10-8 5 4-5 4m-3-9-4 10"/>',
    "chart": '<path d="M4 4v26h26M9 24V14m8 10V8m8 16V3"/>',
    "person": '<circle cx="16" cy="10" r="6"/><path d="M4 32v-4c0-13 24-13 24 0v4"/>',
    "mission": '<circle cx="16" cy="17" r="13"/><circle cx="16" cy="17" r="7"/><path d="m16 17 14-14m-7 0h7v7"/>',
    "vision": '<path d="M1 17Q16-4 31 17 16 38 1 17Z"/><circle cx="16" cy="17" r="6"/>',
    "scope": '<path d="M11 3H3v9m18-9h8v9M3 22v9h8m18-9v9h-8M8 17h16"/>',
    "rule": '<path d="m9 3 14 0 8 14-8 14H9L1 17Z"/><path d="m9 17 5 5 10-11"/>',
    "alert": '<path d="M16 3 31 30H1Z M16 12v9m0 4v1"/>',
    "gap": '<path d="M3 10h26M3 26h26"/><circle cx="10" cy="10" r="4"/>'
           '<circle cx="23" cy="26" r="4"/><path d="M10 14v8m13-8v8"/>',
    "channels": '<circle cx="16" cy="6" r="4"/><circle cx="5" cy="29" r="4"/>'
                '<circle cx="16" cy="29" r="4"/><circle cx="27" cy="29" r="4"/>'
                '<path d="M16 10v8M5 18h22M5 18v7m11-7v7m11-7v7"/>',
    "region": '<path d="M16 34S5 23 5 14a11 11 0 0 1 22 0c0 9-11 20-11 20Z"/>'
              '<circle cx="16" cy="14" r="4"/>',
    "calendar": '<rect x="3" y="6" width="26" height="26" rx="4"/>'
                '<path d="M3 14h26M9 2v8m14-8v8M9 20h4m6 0h4M9 26h4m6 0h4"/>',
    "lag": '<circle cx="16" cy="19" r="13"/><path d="M16 11v9l6 4M8 3 4 8h8"/>',
    "decision": '<path d="M16 2v10M5 31V19h22v12M16 12v7"/><circle cx="16" cy="4" r="3"/><circle cx="5" cy="30" r="3"/><circle cx="27" cy="30" r="3"/>',
}


def component_kind(*texts):
    """A visual vocabulary based on the object's function, rather than uniform boxes."""
    text = " ".join(str(value or "") for value in texts).lower()
    for kind, pattern in [
        ("security", r"seguridad|secret|clave|token|permiso|administraci|acceso"),
        ("mission", r"misi[oó]n|objetivo"), ("vision", r"visi[oó]n"),
        ("scope", r"alcance|cobertura"), ("decision", r"decisi|d-\d"),
        ("alert", r"alerta|rechaz|falla|riesgo|l[ií]mite"),
        ("rule", r"regla|rn-\d|validaci|control de|calidad"),
        ("workflow", r"descarga|agente|pipeline|workflow|journey|recorrido|devops|ejecuci|prueba|cron|cach[eé]"),
        ("code", r"c[oó]digo|python|sql|quer[yi]|consulta"),
        ("database", r"tabla|base|datos\.db|raw\.db|modelo|dimensi[oó]n|fuente|registro|etl_run"),
        ("person", r"stakeholder|geren|analista|equipo|usuario|qui[eé]n"),
        ("region", r"regional_map|d[oó]nde es m[aá]s caro"),
        ("chart", r"precio|variaci|brecha|calendario|[ií]ndice|k[1-8]|indicador|tendencia|evolucion|usable_data"),
    ]:
        if re.search(pattern, text):
            return kind
    return "document"


def build_component_symbol(kind):
    shape = COMPONENT_SYMBOLS.get(kind, COMPONENT_SYMBOLS["document"])
    return (f'<span class="component-symbol" data-kind="{kind}" aria-hidden="true">'
            '<svg viewBox="0 0 32 36" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round">' + shape + '</svg></span>')


def build_info_card_html(title, text, label=None, note=None, link=None, is_warning=False,
                         body_html="", is_highlight=False, component=None):
    """One card: an optional label, a title, a short text, more content right under it
    (body_html), a note and a named link at the bottom."""
    text = capitalize_first(text)
    semantic = component or component_kind(title, label)
    parts = [build_component_symbol(semantic),
             f'<div class="info-label">{html.escape(label)}</div>' if label else "",
             f'<div class="info-title">{format_inline(title)}</div>',
             f'<div class="info-text">{format_inline(text)}</div>', body_html,
             f'<div class="info-note">{format_inline(note)}</div>' if note else "",
             f'<div class="info-link">{link}</div>' if link else ""]
    kind = " is-warning" if is_warning else " is-highlight" if is_highlight else ""
    return f'<div class="info-card{kind}" data-component-kind="{semantic}">{"".join(parts)}</div>'


def show_info_cards(cards_html, is_compact=False):
    """Cards in a grid: side by side when they fit, stacked on narrow screens. Compact
    cards keep their own height instead of the tallest one of their row."""
    kind = " is-compact" if is_compact else ""
    st.markdown(f'<div class="info-grid{kind}">{"".join(cards_html)}</div>',
                unsafe_allow_html=True)


def build_steps_html(steps):
    """Numbered steps of a process, in order: [(label, text)] or plain texts."""
    items = "".join(f"<li><strong>{format_inline(step[0])}:</strong> {format_inline(step[1])}"
                    "</li>" if isinstance(step, tuple) else f"<li>{format_inline(step)}</li>"
                    for step in steps)
    return f'<ol class="steps">{items}</ol>'


def build_place_link(place, verb="Ver en"):
    """A link whose words say where it goes: «Ver en Análisis › Brecha de precio»."""
    page = PAGE_OF_TAB.get(place)
    destination = (f"{page} › {place}" if page and place in TABS_BY_PAGE[page]
                   else page or place)
    return build_link_html(f"{verb} {destination}".strip(), build_place_address(place))
# endregion


# region Page header
def show_page_header(title, subtitle):
    """Page title, a one-line explanation and the freshness of the data."""
    if title in (PAGE_DOCUMENTATION, PAGE_MANUAL, PAGE_DECISIONS, PAGE_GLOSSARY, PAGE_LINKS, "GitHub",
                PAGE_DOC_BI, PAGE_DOC_BA, PAGE_DOC_IT):
        st.title(title)
        st.markdown(f'<p class="page-subtitle">{html.escape(subtitle)}</p>', unsafe_allow_html=True)
        return
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    run_text = "Carga correcta" if run_kind == "ok" else "Última carga con falla"
    freshness = format_chile_time(parse_run_start(latest_run["started_at"]))
    if st.session_state.get(COMPACT_VIEW):
        # A report page: title and freshness on one line; the sentence on hover.
        st.markdown(f'<div class="compact-header"><h1 title="{html.escape(subtitle)}">'
                    f'{html.escape(title)}</h1><span class="page-freshness">Datos al '
                    f'{freshness} {build_chip(run_text, run_kind)}</span></div></div>',
                    unsafe_allow_html=True)
        return
    st.title(title)
    st.markdown(f'<p class="page-subtitle">{html.escape(subtitle)}</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-freshness">Datos actualizados el {freshness} '
                f'{build_chip(run_text, run_kind)}</div>', unsafe_allow_html=True)


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
        # The small line shows the last weeks: five years would flatten this week away.
        recent = series.sort_index().tail(SPARKLINE_WEEKS)
        trend_rows = pd.DataFrame({"week_start": recent.index, "value": recent.to_numpy()})
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
                    f"{series.index.max():%d-%m-%Y}", mode, color)
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
    first_row = st.columns(2 if st.session_state.get(COMPACT_VIEW) else 4)
    cards = first_row + (st.columns(2) if len(first_row) == 2 else [])
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
    if not st.session_state.get(COMPACT_VIEW):
        st.caption(f"Cómo leer las cifras: {KEY_FIGURES_HINT}".replace("**", "")
                   + f" La línea de cada tarjeta muestra las últimas {SPARKLINE_WEEKS} semanas.")


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


def show_overview_trend(rows, mode, key="trend", title="Precio por semana"):
    """Card: weekly price of the wholesale market and of each consumer channel."""
    with open_card(key, title, "La línea gris es el precio mayorista.",
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


def choose_analysis_filters(include_region=True, include_channels=True):
    """Group, product, variety, region and channels, once for every tab of Análisis."""
    columns = st.columns([1, 1, 1.4] + ([1.3] if include_region else []) + ([1.8] if include_channels else []))
    key = choose_product_key("k3_regional_index", columns[:3])
    rows = read_indicator_for_key("k3_regional_index", key)
    report_region = read_filter("region") if st.session_state.get(COMPACT_VIEW) else ALL_VALUES
    region = recall_filter("region", DEFAULT_REGION)
    if include_region:
        with columns[3]:
            if report_region != ALL_VALUES and report_region in set(rows["region"]):
                region = report_region
                st.markdown(f'<div class="fixed-filter"><span class="kpi-label">Región</span>'
                            f'<strong>{html.escape(charts.shorten_region_name(region))}</strong>'
                            f'<small>desde la barra del informe</small></div>',
                            unsafe_allow_html=True)
            else:
                region = remember_filter("region", choose_value(
                    "Región", rows["region"].unique(), recall_filter("region", DEFAULT_REGION)))
    consumer_channels = sorted(channel for channel in rows["channel"].unique()
                               if channel != WHOLESALE_LABEL)
    remembered = [channel for channel in recall_filter("channels", DEFAULT_MARGIN_CHANNELS)
                  if channel in consumer_channels]
    channels = consumer_channels
    if include_channels:
        with columns[-1]:
            channels = remember_filter("channels", st.multiselect(
                "Canal", consumer_channels, default=remembered))
    if not st.session_state.get(COMPACT_VIEW):
        st.caption("La selección se recuerda al recorrer las secciones de análisis.")
    return {"key": key, "region": region, "channels": channels}


def read_margin_rows(filters):
    """K1 rows of the chosen product and region."""
    rows = read_indicator_for_key("k1_margin", filters["key"])
    return rows[rows["region"] == filters["region"]]


@st.cache_data
def read_cached_national_prices(database_version):
    """Every national price series, every week (K6): read once, filtered in memory, so a
    click on a new product answers without a query (D-069)."""
    return add_display_columns(queries.run_query("k6_national_weekly_price"))


@st.cache_data
def read_cached_all_variations(database_version):
    """Weekly change of every national price series, every week (K6 base)."""
    prices = alerts.add_weekly_variation(queries.run_query("k6_national_weekly_price"))
    return add_display_columns(prices[prices["variation"].notna()].copy())


def read_week_variations(week=None, group=None):
    """The weekly changes of one week (the latest by default), of one group if given."""
    rows = read_cached_all_variations(get_database_version())
    week = pd.Timestamp(week) if week else rows["week_start"].max()
    rows = rows[rows["week_start"] == week]
    return rows[rows["product_group"] == group] if group and group != ALL_VALUES else rows


def read_cached_latest_variations(database_version):
    """Weekly variation of every national price series in the latest week."""
    return read_week_variations()


@st.cache_data
def read_cached_week_summary(database_version, week, group=ALL_VALUES, region=ALL_VALUES):
    """The chosen week and the week before, in business terms: how many prices rose and
    fell, the typical change, the comparable median gap and the active alerts (D-068).
    The category applies to everything; the region only to the gap, the one figure
    measured by region (changes and alerts are national)."""
    variations = read_cached_all_variations(database_version)
    if group != ALL_VALUES:
        variations = variations[variations["product_group"] == group]
    weeks = sorted(variations.loc[variations["week_start"] <= pd.Timestamp(week),
                                  "week_start"].unique())[-2:]
    alert_rows = read_price_alerts()
    if group != ALL_VALUES:
        alert_rows = alert_rows[alert_rows["product_group"] == group]
    summary = {}
    for name, current in zip(["previous", "latest"], weeks):
        changes = variations.loc[variations["week_start"] == current, "variation"]
        gaps = read_cached_week_gaps(database_version, f"{pd.Timestamp(current):%Y-%m-%d}")
        if group != ALL_VALUES:
            gaps = gaps[gaps["product_group"] == group]
        if region != ALL_VALUES:
            gaps = gaps[gaps["region"] == region]
        comparable = gaps.loc[gaps["margin"] <= MAXIMUM_COMPARABLE_GAP, "margin"]
        summary[name] = {
            "rises": int((changes > 0).sum()), "falls": int((changes < 0).sum()),
            # Without data the figure is missing, never 0 % (D-072).
            "typical_change": float(changes.median() * 100) if len(changes) else None,
            "median_gap": float(comparable.median() * 100) if len(comparable) else None,
            "alerts": int((alert_rows["week_start"] == current).sum())}
    summary.setdefault("previous", summary["latest"])
    latest = variations[variations["week_start"] == weeks[-1]]
    summary["week"] = pd.Timestamp(weeks[-1])
    summary["strong_rises"] = int(latest.loc[latest["variation"] > STRONG_CHANGE,
                                             "product"].nunique())
    summary["top_rise"] = latest.loc[latest["variation"].idxmax()].to_dict()
    return summary


def build_summary_sentence(summary):
    """«Esta semana subieron 214 precios y bajaron 180. 46 productos subieron más de
    10 %; la mayor alza fue Manzana en Mayorista (+55,6 %).»"""
    latest = summary["latest"]
    top = summary["top_rise"]
    return (f"Esta semana subieron {charts.format_thousands(latest['rises'])} series de precios "
            f"y bajaron {charts.format_thousands(latest['falls'])}. {summary['strong_rises']} "
            f"productos subieron más de {STRONG_CHANGE * 100:.0f} %; la mayor alza fue "
            f"{top['product']} en {top['channel']} "
            f"({charts.format_signed_percent(top['variation'] * 100)}).")


def describe_week_change(change, unit):
    """«▲ 12 frente a la semana anterior», in words and arrow, never color alone."""
    if change is None or pd.isna(change):
        return "sin comparación con la semana anterior"
    # The arrow says the direction; the number goes without sign.
    if unit == "pts":
        amount = charts.format_percent(abs(change)).replace(" %", " pts")
    else:
        amount = charts.format_thousands(abs(change))
    arrow = "▲" if change > 0 else "▼" if change < 0 else "="
    return f"{arrow} {amount} frente a la semana anterior"


def describe_short_change(change, unit):
    """«▼ 27 vs. semana anterior»: the strip's note, short enough for one line."""
    return describe_week_change(change, unit).replace("frente a la", "vs.")


def subtract(latest, previous):
    """latest − previous, or None when either figure is missing."""
    return None if latest is None or previous is None else latest - previous


def build_kpi_strip_html(summary, coverage, latest_run, include_note=True):
    """The figures of the week on one line, without cards (D-072): each one with its change
    in words and arrow, and each one opens the view that explains it."""
    latest, previous = summary["latest"], summary["previous"]
    matched, total = coverage
    # Like the approved mockup: three figures and what an alert means. The weekly
    # rises and the median gap stay in «Esta semana» and «Brecha» (D-072).
    values = [
        ("rise", str(latest["alerts"]), "Alertas semanales",
         describe_short_change(subtract(latest["alerts"], previous["alerts"]), ""),
         build_page_address(PAGE_ALERTS)),
        ("accent", charts.format_percent(matched / total * 100) if total else NO_COMPARABLE_TEXT,
         "Productos con precios comparables",
         f"{charts.format_thousands(matched)} de {charts.format_thousands(total)} con precio "
         "mayorista y al consumidor",
         build_page_address(PAGE_OPERATIONS))]
    symbols = ["notifications_active", "compare_arrows"]
    explanations = ["Cambios de precio que requieren revisión; no son errores confirmados.",
                    "Productos presentes tanto en mayorista como en venta al consumidor."]
    actions = ["Revisar alertas →", "Ver cobertura →"]
    cells = "".join(
        f'<a class="kpi-strip-item" href="{html.escape(address)}" target="_self">'
        f'<span class="kpi-strip-label"><span class="material-symbols-rounded metric-symbol" aria-hidden="true">{symbol}</span>{html.escape(label)}</span>'
        f'<span class="kpi-strip-value kpi-strip-{kind}">{html.escape(value)}</span>'
        f'<span class="kpi-strip-note">{html.escape(note)}</span>'
        f'<span class="metric-explanation">{html.escape(explanation)}</span>'
        f'<span class="metric-action">{action}</span></a>'
        for (kind, value, label, note, address), symbol, explanation, action in zip(values, symbols, explanations, actions))
    is_loaded = latest_run["status"] == etl.STATUS_LOADED
    load = (f'<a class="kpi-strip-item" href="{html.escape(build_page_address(PAGE_OPERATIONS))}"'
            f' target="_self"><span class="kpi-strip-label"><span class="material-symbols-rounded metric-symbol" aria-hidden="true">task_alt</span>Última carga</span>'
            f'<span class="kpi-strip-value kpi-strip-{"good" if is_loaded else "rise"}">'
            f'{"✓" if is_loaded else "!"} {"Carga correcta" if is_loaded else "Carga con falla"}'
            f'</span><span class="kpi-strip-note">{html.escape(format_chile_time(parse_run_start(latest_run["started_at"])))}'
            '</span><span class="metric-explanation">Estado registrado por el proceso de carga. Consulta los controles y sus límites.</span>'
            '<span class="metric-action">Ver calidad →</span></a>')
    note = ('<span class="kpi-strip-item kpi-strip-meaning">ⓘ Una alerta invita a revisar; '
            'no explica la causa.</span>')
    return f'<div class="kpi-strip">{cells}{load}{note if include_note else ""}</div>'


def build_context_line(summary, variations):
    """The technical figures, small: the week, the series and the history."""
    total = read_indicator("quality_flag_counts")["weekly_prices"].sum()
    return (f'<div class="context-line">Semana del {summary["week"]:%d-%m-%Y} · '
            f'{charts.format_thousands(len(variations))} series comparadas con la semana '
            f'anterior · {charts.format_thousands(total)} precios semanales desde 2022</div>')


def split_comparable_gaps(gaps):
    """(gaps that compare the same thing, gaps left out as a packed format)."""
    is_comparable = gaps["margin"] <= MAXIMUM_COMPARABLE_GAP
    return gaps[is_comparable], gaps[~is_comparable]


@st.cache_data
def read_cached_group_changes(database_version, week):
    """Typical weekly change of each product group in one week, in percent."""
    variations = read_cached_all_variations(database_version)
    variations = variations[variations["week_start"] == pd.Timestamp(week)]
    return (variations.groupby("product_group")["variation"].median() * 100).sort_values(
        ascending=False)


def show_week_ranking(filters, mode):
    """Card: the largest price changes of the week in the chosen group and channels."""
    group = filters["key"]["product_group"]
    week = read_filter("week") if st.session_state.get(COMPACT_VIEW) else ALL_VALUES
    rows = read_week_variations(None if week == ALL_VALUES else week, group)
    rows = rows[rows["channel"].isin(filters["channels"])]
    with open_card("week_ranking", f"Mayores variaciones de la semana · {group}",
                   hint=WEEK_RANKING_HINT, kpi="K6"):
        if rows.empty:
            st.info(NO_DATA_TEXT)
            return
        st.caption(f"Semana del {rows['week_start'].max():%d-%m-%Y}, frente a la anterior. "
                   f"{KEY_FIGURES_HINT}".replace("**", ""))
        largest = rows.loc[rows["variation"].abs().sort_values(ascending=False).index]
        largest = largest.head(RANKING_SIZE)
        bar_rows = pd.DataFrame({
            "label": [f"{describe_product(row)} · {row['channel']}"
                      for row in largest.to_dict("records")],
            "value": largest["variation"].to_numpy() * 100})
        chart = charts.draw_variation_bars(bar_rows, mode)
        if st.session_state.get(COMPACT_VIEW):
            chart = chart.properties(height=alt.Step(BAR_STEP))
        show_chart(chart)


def show_week_history(rows, filters, mode):
    """The long history, folded: wholesale and one channel per chart (two lines)."""
    with st.expander("Ver evolución histórica", expanded=False):
        for channel in filters["channels"]:
            channel_rows = rows[rows["channel"] == channel]
            if not channel_rows.empty:
                show_overview_trend(channel_rows, mode, key=f"week_history_{channel}",
                                    title=f"Precio por semana · mayorista y {channel}")


def show_week_tab(mode, filters):
    """This week on one screen: the price cards (12 weeks of trend) 2 x 2 at the left and
    the week's largest changes at the right; the long history below, folded (D-067)."""
    rows = read_margin_rows(filters)
    cards_column, ranking_column = st.columns([1.1, 1.5])
    with cards_column:
        if rows.empty:
            st.info(NO_MARGIN_TEXT)
        else:
            show_overview_figures(rows, mode)
    with ranking_column:
        show_week_ranking(filters, mode)
    if st.session_state.get(COMPACT_VIEW):
        # Moved from the summary (D-072): which group rose most, a click goes into it.
        show_group_card("week", read_report_week(), mode)
    if not rows.empty:
        show_week_history(rows, filters, mode)
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
    return int((alert_rows["week_start"] == read_latest_week()).sum())


def summarize_journey_state(states):
    """(word, chip kind) of the whole pipeline: its worst real step state."""
    step_states = [states.get(name) for name in ["sources", "download", "etl", "load", "panel"]]
    if control.RUN_FAILED in step_states:
        return "con falla", "failed"
    if control.RUN_IN_PROGRESS in step_states:
        return "en curso", "running"
    if all(state == control.RUN_OK for state in step_states):
        return "OK", "ok"
    return "sin datos", "neutral"


def describe_state_source(error_text, step_states, latest_load):
    """Where the states come from when GitHub did not answer, and why it did not."""
    if step_states:
        source = "se muestra la última respuesta guardada"
    else:
        loaded_at = format_chile_time(parse_run_start(latest_load["started_at"]))
        source = f"los estados salen de la última carga guardada en la base ({loaded_at})"
    return f"GitHub no respondió ({error_text}); {source}."


def list_journey_steps(journey):
    """(text, address) of each stop of a guided tour of the project."""
    tabs = {tab: build_place_address(tab) for tab in PAGE_OF_TAB}
    journeys = {
        JOURNEY_MANAGER: [(TAB_WEEK, tabs[TAB_WEEK]), (TAB_ALERTS, tabs[TAB_ALERTS]),
                          (TAB_KPI, tabs[TAB_KPI])],
        JOURNEY_ANALYST: [(TAB_IDEA, tabs[TAB_IDEA]), (TAB_GAP, tabs[TAB_GAP]),
                          (TAB_KPI, tabs[TAB_KPI]), (TAB_RULES, tabs[TAB_RULES]),
                          (TAB_DECISIONS, tabs[TAB_DECISIONS])],
        JOURNEY_TECHNICAL: [(PAGE_ARCHITECTURE, build_page_address(PAGE_ARCHITECTURE)),
                            (TAB_QUERIES, tabs[TAB_QUERIES]),
                            (PAGE_OPERATIONS, build_page_address(PAGE_OPERATIONS))],
    }
    return journeys[journey]


def build_question_showcase_html():
    """Six borderless editorial items, each with its own meaningful symbol."""
    symbols = ["gap", "channels", "region", "calendar", "lag", "alert"]
    items = []
    for number, (question, place, state, scope) in enumerate(BUSINESS_QUESTIONS, start=1):
        state_text, _ = QUESTION_STATES[state]
        items.append(
            f'<article class="question-item">{build_component_symbol(symbols[number - 1])}'
            f'<div class="question-number">Pregunta {number} · {html.escape(state_text)}</div>'
            f'<div class="question-title">{format_inline(question)}</div>'
            f'<div class="question-scope">{format_inline(scope)}</div>'
            f'<div class="question-action">{build_place_link(place)}</div></article>')
    return f'<div class="question-showcase">{"".join(items)}</div>'


def show_questions(mode):
    """What the panel answers, first: it is what a visitor came for."""
    show_section_intro("Requisitos de negocio", "Seis preguntas de un área de pricing o "
                       "abastecimiento; cada una lleva a su sección de análisis.", True)
    st.markdown(build_question_showcase_html(), unsafe_allow_html=True)


def show_audience(mode):
    """Who the panel is for, and where each reader starts."""
    show_section_intro("Stakeholders y usuarios", "Roles previstos, necesidades y acceso a los resultados.", True)
    show_info_cards([build_info_card_html(
        title, text, link=build_place_link(place, "Ir a") if place else None,
        note=None if place else "Pendiente.") for title, text, place in AUDIENCE_CARDS])


def show_sources(mode):
    """Both ODEPA sources, the three steps that make them comparable, and the coverage."""
    section = project.read_section(project.read_document(project.PROJECT_GUIDE_FILE),
                                   "Fuentes y cruces")
    show_section_intro("Las fuentes y cómo se cruzan", "Dos archivos abiertos de ODEPA "
                       "(Ministerio de Agricultura), uno por año. Existen, pero están "
                       "separados: antes de compararlos hay que resolver tres diferencias.", True)
    show_info_cards([build_info_card_html(name, text, label=SOURCE_LABELS.get(name))
                     for name, text in project.parse_labeled_items(section)])
    st.markdown('<div class="info-note">Licencia Creative Commons Atribución. Los enlaces a '
                f'las fuentes están en {build_place_link(PAGE_LINKS, "la página")}'
                '.</div>', unsafe_allow_html=True)
    st.markdown(build_steps_html(project.parse_labeled_items(section, numbered=True)),
                unsafe_allow_html=True)
    keys_with_margin, consumer_keys = read_match_coverage()
    st.markdown(f'<p class="info-text">{format_inline(project.read_closing_paragraph(section))}'
                f'</p><div class="stat-line"><span class="kpi-label">Cobertura del cruce (K7)'
                f'</span><strong>{keys_with_margin} de {consumer_keys} claves</strong>'
                f'<span class="info-note">'
                f'{charts.format_percent(keys_with_margin / consumer_keys * 100)} de las claves '
                f'de frutas y verduras del consumidor</span>{build_kpi_link("K7")}</div>',
                unsafe_allow_html=True)
    with st.expander("Ver detalles", expanded=False):
        st.markdown(MATCH_DETAILS)


def show_limits(mode):
    """What the figures do not say, always in sight."""
    show_section_intro("Límites", "Lo que hay que tener presente al leer cualquier cifra.",
                       True)
    show_info_cards([build_info_card_html(title, text, is_warning=True)
                     for title, text in LIMIT_CARDS])


def show_why(mode):
    """Why this subject, with the discarded alternatives folded."""
    show_section_intro("Justificación del proyecto", WHY_TEXT, True)
    with st.expander("Ver detalles", expanded=False):
        st.markdown(WHY_DETAILS)


@st.cache_data
def read_cached_week_span(database_version):
    """(weeks, first Monday, last Monday) with prices, read once per database."""
    return project.read_week_span()


@st.cache_data
def read_cached_cover_figures(database_version):
    """What the base holds today, for the cover: regions, channels, products, groups."""
    row = queries.run_sql(
        "SELECT (SELECT COUNT(*) FROM dim_region) AS regions, "
        "(SELECT COUNT(*) FROM dim_channel) AS channels, "
        "(SELECT COUNT(DISTINCT product) FROM dim_product) AS products, "
        "(SELECT COUNT(DISTINCT product_group) FROM dim_product) AS groups").iloc[0]
    return {name: int(value) for name, value in row.items()}


def format_month_year(text):
    """«2022-01-03» as «ene 2022»."""
    moment = pd.Timestamp(text)
    return f"{charts.MONTH_NAMES[moment.month - 1]} {moment.year}"


def show_cover_link(pages, view, label, key, help=None):
    """A link to a view of the route, in the same window: with the navigation pages it
    keeps the session (filters) and the theme; without them, a plain address."""
    window = WINDOW_OF_VIEW[view]
    with st.container(key=key):
        if not pages:
            st.markdown(build_link_html(label, build_page_address(view)), unsafe_allow_html=True)
            return
        parameters = keep_context()
        if view != read_window_views(window)[0]:
            parameters[VIEW_PARAMETER] = view
        st.page_link(pages[window], label=label, query_params=parameters, help=help)


def build_cover_figures_html():
    """The panel beside the title: real figures of the base, instead of an illustration."""
    figures = read_cached_cover_figures(get_database_version())
    week_count, first_week, last_week = read_cached_week_span(get_database_version())
    weekly_prices = read_indicator("quality_flag_counts")["weekly_prices"].sum()
    items = [("Precios semanales", charts.format_thousands(weekly_prices),
              "mayoristas y al consumidor"),
             ("Semanas", charts.format_thousands(week_count),
              f"{format_month_year(first_week)} – {format_month_year(last_week)}"),
             ("Productos", charts.format_thousands(figures["products"]),
              f"en {figures['groups']} grupos de alimentos"),
             ("Regiones · canales", f"{figures['regions']} · {figures['channels']}",
              "con precios en la base")]
    rows = "".join(f'<div><dt>{html.escape(label)}</dt><dd>{value}</dd>'
                   f'<span>{html.escape(note)}</span></div>' for label, value, note in items)
    return ('<section class="cover-figures" aria-label="La base hoy">'
            '<div class="cover-figures-title">La base hoy</div>'
            f'<dl>{rows}</dl><p>Cifras leídas de la base de datos del proyecto.</p></section>')


def list_cover_evidence():
    """(title, what it proves, real figure, view, link label) of «Trazabilidad y operación»."""
    totals = read_indicator("quality_flag_counts").groupby("flag")["weekly_prices"].sum()
    used = totals.get("SIN_MARCA", 0) / totals.sum() * 100
    latest_run = read_latest_run()
    run_text = ("correcta" if latest_run["status"] == etl.STATUS_LOADED else "con falla")
    loaded_at = format_chile_time(parse_run_start(latest_run["started_at"])).split(" ")[0]
    return [
        ("Trazabilidad de los datos", "Cada precio conserva su origen; los registros excluidos mantienen el motivo de validación.",
         f"{charts.format_percent(used)} de los precios semanales pasa los controles.",
         PAGE_RULES, "Ver reglas de calidad →"),
        ("Análisis reproducible", "Las definiciones de los indicadores, sus fórmulas y las consultas SQL están disponibles para revisión.",
         f"{len(queries.load_queries())} consultas con nombre en `bi/queries.sql`.",
         PAGE_KPI, "Ver indicadores explicados →"),
        ("Operación semanal", "GitHub Actions ejecuta la descarga, validación y carga de datos cada martes, con registro del resultado.",
         f"Última carga: {loaded_at} · {run_text}.", PAGE_RUNS, "Ver ejecuciones →"),
    ]


def show_cover_page(mode, pages=None):
    """The portfolio cover (C01): name, what it does, the way in, what can be checked and
    the limits, in one screen. Everything else stays in its own view."""
    with st.container(key="cover_top", horizontal=True, vertical_alignment="center"):
        st.markdown('<div class="cover-eyebrow">Analítica de precios · Datos abiertos de ODEPA</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<a class="cover-github" href="{html.escape(project.GITHUB_URL, quote=True)}" '
                    'target="_blank" rel="noopener noreferrer">Repositorio en GitHub ↗</a>',
                    unsafe_allow_html=True)
    text_column, figures_column = st.columns([1.5, 1], gap="large", vertical_alignment="center")
    with text_column, st.container(key="cover_hero"):
        st.title(COVER_NAME, anchor=False)
        plain, highlighted = COVER_TAGLINE
        st.markdown(f'<p class="cover-tagline">{html.escape(plain)}<span>'
                    f'{html.escape(highlighted)}</span></p><p class="cover-lead">'
                    f'{html.escape(COVER_LEAD)}</p>', unsafe_allow_html=True)
        with st.container(key="cover_actions", horizontal=True, vertical_alignment="center"):
            show_cover_link(pages, PAGE_HOME, "Explorar el dashboard →", "cover_primary",
                            help=f"Muestra {ROUTE_LEADS[REPORT_WINDOW]}.")
            show_cover_link(pages, PAGE_QUERIES, "Ver código y resultados", "cover_secondary",
                            help=f"Muestra {ROUTE_LEADS[SECTION_QUERIES]}.")
    with figures_column:
        st.markdown(build_cover_figures_html(), unsafe_allow_html=True)
    statements = "".join(
        f'<div class="cover-statement">{build_component_symbol(symbol)}<div>'
        f'<h3>{html.escape(title)}</h3><p>{html.escape(text)}</p></div></div>'
        for symbol, title, text in COVER_STATEMENTS)
    st.markdown(f'<div class="cover-statements">{statements}</div>'
                '<h2 class="cover-heading">Trazabilidad y operación</h2>', unsafe_allow_html=True)
    with st.container(key="cover_evidence", horizontal=True):
        for number, (title, text, figure, view, label) in enumerate(list_cover_evidence(), 1):
            with st.container(key=f"cover_evidence_{number}"):
                st.markdown(f'<div class="cover-evidence"><div class="cover-evidence-title">'
                            f'<span>{number:02d}</span>{html.escape(title)}</div>'
                            f'<p>{html.escape(text)}</p><p class="cover-evidence-figure">'
                            f'{format_inline(figure)}'
                            '</p></div>', unsafe_allow_html=True)
                show_cover_link(pages, view, label, f"cover_evidence_link_{number}")
    with st.container(key="cover_closing", horizontal=True):
        for key, symbol, title, text, link in [
                ("cover_offer", "chart", "Lo que aporta", COVER_OFFER,
                 (PAGE_ANALYSIS, "Ver el detalle de la semana →")),
                ("cover_limits", "document", "Límites claros", COVER_LIMITS,
                 (PAGE_BUSINESS, "Leer alcance y método →"))]:
            with st.container(key=key):
                st.markdown(f'<div class="cover-statement">{build_component_symbol(symbol)}<div>'
                            f'<h3>{html.escape(title)}</h3><p>{html.escape(text)}</p></div></div>',
                            unsafe_allow_html=True)
                show_cover_link(pages, *link, f"{key}_link")
    st.markdown("### Reutilización y nuevas fuentes")
    st.markdown("La separación entre ingesta, transformación, modelo de datos, consultas y presentación permite reutilizar la estructura del proyecto. "
                "Una nueva fuente requiere adaptar su descarga, esquema y reglas de validación; las pruebas deben verificar las nuevas claves y unidades.")
    st.markdown("En un proyecto de rendimiento deportivo se pueden conservar la navegación, los temas, la automatización y la organización del código. "
                "El modelo, los indicadores, las fuentes y las reglas de calidad deben diseñarse para deportistas, sesiones y resultados. "
                "La implementación actual está especializada en precios ODEPA; todavía no es una plantilla intercambiable solo cambiando una URL.")


def format_iso_date(text):
    """«2026-10-05» as «05-10-2026»."""
    return f"{pd.Timestamp(text):%d-%m-%Y}"


TABLE_ROLES = {"weekly_price": "hechos", "dim_product": "dimensión", "dim_region": "dimensión",
              "dim_channel": "dimensión", "dim_date": "dimensión", "etl_run": "auditoría",
              "rejection": "auditoría"}
# One real, runnable query per table: what a reader would actually ask it (D-097).
TABLE_EXAMPLE_SQL = {
    "weekly_price": "SELECT COUNT(*) FROM weekly_price WHERE flag IS NULL;",
    "dim_product": "SELECT * FROM dim_product WHERE product = 'Tomate';",
    "dim_region": "SELECT * FROM dim_region ORDER BY region;",
    "dim_channel": "SELECT * FROM dim_channel;",
    "dim_date": "SELECT * FROM dim_date WHERE iso_year = 2026 AND iso_week = 41;",
    "etl_run": "SELECT * FROM etl_run ORDER BY started_at DESC LIMIT 1;",
    "rejection": "SELECT reason, COUNT(*) FROM rejection GROUP BY reason;",
}
ARCHITECTURE_TABLE_KEY = "architecture_selected_table"


def build_architecture_header(row_counts, latest_run):
    """Title, a one-line description and three real figures, on the right (D-097)."""
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    run_text = "Carga correcta" if run_kind == "ok" else "Última carga con falla"
    freshness = format_chile_time(parse_run_start(latest_run["started_at"]))
    chips = [("weekly_price", f"{charts.format_thousands(row_counts['weekly_price'])} filas"),
             ("Auditoría", f"{charts.format_thousands(row_counts['etl_run'])} cargas · "
                           f"{charts.format_thousands(row_counts['rejection'])} rechazos"),
             ("Última carga", f"{freshness} · {run_text}")]
    return (f'<div class="arch-head compact-header"><h1>{html.escape(PAGE_ARCHITECTURE)}</h1>'
            '<span class="page-freshness">Modelo estrella que convierte los precios en '
            'indicadores comparables. Las líneas relacionan tablas; no son pasos de '
            'ejecución.</span></div><div class="arch-chips">'
            + "".join(f'<div class="arch-chip"><span>{html.escape(label)}</span>'
                      f'<div>{html.escape(value)}</div></div>' for label, value in chips)
            + "</div>")


def build_architecture_css(mode):
    palette = charts.get_palette(mode)
    return f"""<style>
    .arch-head {{display:flex; align-items:baseline; flex-wrap:wrap; gap:6px 18px; margin:0;}}
    .arch-head h1 {{font-size:1.5rem !important; margin:0 !important; padding:0 !important;}}
    .arch-head .page-freshness {{margin:2px 0 0; font-size:.86rem; max-width:900px;}}
    .arch-chips {{display:flex; gap:10px; flex-wrap:wrap; margin:10px 0 4px;}}
    .arch-chip {{border:1px solid {palette['card_border']}; border-radius:9px; background:{palette['card']};
        padding:6px 13px; min-width:150px;}}
    .arch-chip span {{display:block; font-size:10.5px; color:{palette['text']}; line-height:1.3;}}
    .arch-chip div {{font-size:13px; color:{palette['strong_text']}; font-weight:600; white-space:nowrap;}}
    .st-key-architecture_body [data-testid="stHorizontalBlock"] {{align-items:stretch; gap:14px;}}
    .st-key-architecture_diagram {{border:1px solid {palette['card_border']}; border-radius:14px;
        background:{palette['card']}; padding:12px 16px 10px;}}
    .st-key-architecture_diagram svg {{display:block; width:100%; height:auto;
        max-height:calc(100vh - 300px);}}
    .arch-legend {{display:flex; gap:16px; margin-top:6px; font-size:11.5px; color:{palette['text']};}}
    .arch-phrase {{font-size:.85rem; color:{palette['strong_text']}; margin:0 0 8px;}}
    .st-key-architecture_detail, .st-key-architecture_tables {{border:1px solid {palette['card_border']};
        border-radius:14px; background:{palette['card']}; padding:12px 16px 10px;}}
    .arch-detail-head {{display:flex; align-items:baseline; gap:10px; flex-wrap:wrap;}}
    .arch-detail-head code {{font-size:1.05rem; font-weight:700; color:{palette['accent']};}}
    .arch-detail-role {{font-size:11px; padding:2px 9px; border-radius:999px;
        background:{palette['field']}; color:{palette['text']};}}
    .arch-detail-rows {{margin-left:auto; font-size:12px; color:{palette['text']};}}
    .arch-detail-text {{font-size:.86rem; line-height:1.5; color:{palette['strong_text']}; margin:7px 0 9px;}}
    .st-key-architecture_tables_list label p {{font-size:.86rem !important;}}
    </style>"""


def show_architecture_table_detail(table, row_counts, definitions):
    """Name, role, rows, a short description and a real example query (D-097)."""
    st.markdown(f'<div class="arch-detail-head"><code>{html.escape(table)}</code>'
                f'<span class="arch-detail-role">{TABLE_ROLES[table]}</span>'
                f'<span class="arch-detail-rows">{charts.format_thousands(row_counts[table])} filas</span></div>'
                f'<p class="arch-detail-text">{html.escape((definitions[table][0].upper() + definitions[table][1:]))}</p>',
                unsafe_allow_html=True)
    st.code(TABLE_EXAMPLE_SQL[table], language="sql", wrap_lines=True)


def show_architecture_page(mode):
    """One screen at 1920×1080: the star model, its detail and every table (D-097)."""
    row_counts = count_cached_table_rows(get_database_version())
    definitions = project.parse_definitions(project.read_section(
        project.read_document(project.PROJECT_GUIDE_FILE), "Modelo de datos"))
    columns = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
    st.markdown(build_architecture_css(mode), unsafe_allow_html=True)
    st.markdown(build_architecture_header(row_counts, read_latest_run()), unsafe_allow_html=True)
    selected = st.session_state.get(ARCHITECTURE_TABLE_KEY, "weekly_price")
    if selected not in project.TABLE_NAMES:
        selected = "weekly_price"
    with st.container(key="architecture_body"):
        diagram_column, side_column = st.columns([2.1, 1], gap="medium")
        with diagram_column:
            st.markdown('<p class="arch-phrase">1 fila de weekly_price = un producto '
                        '(variedad y calidad) × región × canal × unidad × semana.</p>',
                        unsafe_allow_html=True)
            with st.container(key="architecture_diagram"):
                st.markdown(star_model.build_star_svg(columns, row_counts, mode, selected=selected),
                            unsafe_allow_html=True)
                st.markdown('<div class="arch-legend"><span><b>PK</b> clave primaria</span>'
                            '<span><b>FK</b> clave foránea</span>'
                            '<span><b>cian</b> medida</span></div>', unsafe_allow_html=True)
        with side_column:
            with st.container(key="architecture_detail"):
                st.markdown("##### Detalle de la tabla seleccionada")
                show_architecture_table_detail(selected, row_counts, definitions)
            with st.container(key="architecture_tables"):
                st.markdown("##### Tablas de datos.db")
                with st.container(key="architecture_tables_list"):
                    st.radio("Elegir tabla", project.TABLE_NAMES, key=ARCHITECTURE_TABLE_KEY,
                             label_visibility="collapsed",
                             format_func=lambda table: f"{table} · {TABLE_ROLES[table]} · "
                                                        f"{charts.format_thousands(row_counts[table])} filas")
                st.markdown(build_link_html("Ver etl/schema.sql en Código del proyecto →",
                                            build_page_address(PAGE_CODE)), unsafe_allow_html=True)


@st.cache_data
def build_cached_kpi_examples(database_version):
    """Real examples of K1 to K8, computed once per database."""
    return build_kpi_examples()


@st.cache_data
def count_cached_table_rows(database_version):
    """Rows of each table of the data warehouse, counted once per database."""
    return project.count_table_rows()


def build_kpi_examples():
    """{KPI: steps of its real example}, computed from the current database."""
    key = project.EXAMPLE_KEY
    margin_rows = read_indicator_for_key("k1_margin", key)
    keys_with_margin, consumer_keys = read_match_coverage()
    return {"K1": project.build_k1_example(margin_rows),
            "K2": project.build_k2_example(read_indicator_for_key("k2_channel_gap", key)),
            "K3": project.build_k3_example(read_indicator_for_key("k3_regional_index", key)),
            "K4": project.build_k4_example(read_indicator_for_key("k4_seasonal_index", key)),
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


KPI_LIMITS = {
    "K1": "Compara precios; no mide ganancia ni descuenta costos. Requiere pares comparables.",
    "K2": "Solo compara canales que tienen precios del mismo producto en semanas y regiones coincidentes.",
    "K3": "La referencia usa las regiones con datos. Una región sin precio no equivale a un precio cero.",
    "K4": "Describe patrones del histórico disponible; no es una predicción de precios.",
    "K5": "El rezago es descriptivo, no prueba causalidad. Necesita historia suficiente (26 semanas).",
    "K6": "Una alerta invita a revisar un cambio poco habitual; no demuestra un error ni explica su causa.",
    "K7": "Mide cobertura del cruce entre fuentes, no garantiza la exactitud de cada precio.",
    "K8": "Cero rechazos no implica que todos los precios sean utilizables: atípicos y unidades no convertibles se registran aparte.",
}


KPI_PRESENTATION = {
    "K1": ("Brecha de precio", "gap", "Diferencia entre el precio al consumidor y el mayorista."),
    "K2": ("Comparación de canales", "channels", "Diferencia de precio entre dos canales de venta."),
    "K3": ("Precio por región", "region", "Precio regional frente al promedio de las regiones con datos."),
    "K4": ("Estacionalidad", "calendar", "Semanas más caras o más baratas dentro de un año."),
    "K5": ("Rezago de precios", "lag", "Desfase entre los cambios mayoristas y los del consumidor."),
    "K6": ("Alertas de precio", "alert", "Cambios semanales que se salen del comportamiento habitual."),
    "K7": ("Cobertura del cruce", "scope", "Productos con precios comparables en ambas fuentes."),
    "K8": ("Filas rechazadas", "security", "Registros que no superan la validación de la carga."),
}


KPI_SMART_SCOPE = {
    "K1": ("Porcentaje de diferencia sobre el precio mayorista.", "Comparar precios de compra y venta sin confundir la brecha con ganancia.", "Misma semana, región, producto y unidad."),
    "K2": ("Porcentaje de diferencia entre dos canales.", "Identificar qué canal ofrece un precio más alto o más bajo.", "Misma semana y región para ambos canales."),
    "K3": ("Índice base 1: 1 representa el promedio de las regiones con datos.", "Identificar diferencias territoriales de precio.", "Semana seleccionada, dentro del mismo canal."),
    "K4": ("Razón entre el precio semanal y el promedio anual del producto.", "Reconocer patrones estacionales antes de comparar precios.", "Semana frente al año correspondiente del histórico disponible."),
    "K5": ("Semanas de desfase entre 0 y 8; correlación descriptiva de las variaciones.", "Explorar el desfase entre precios mayoristas y del consumidor, sin afirmar causalidad.", "Historia mínima de 26 semanas; desfases de 0 a 8 semanas."),
    "K6": ("Cambios fuera del rango de ±2 desviaciones estándar de las 12 semanas anteriores.", "Priorizar cambios de precio que merecen revisión.", "Revisión semanal con una referencia móvil de 12 semanas."),
    "K7": ("Porcentaje de claves del consumidor que tienen comparación mayorista.", "Conocer el alcance de las comparaciones entre las dos fuentes.", "Cobertura del histórico disponible, recalculada con cada carga."),
    "K8": ("Porcentaje de filas rechazadas sobre las filas leídas, por motivo.", "Localizar problemas de validación de la carga.", "Cada ejecución de carga; el ejemplo identifica la ejecución utilizada."),
}


def build_kpi_table_html(rows):
    """A readable two-column fact sheet, wrapping within the available width."""
    body = "".join(f'<tr><th scope="row">{html.escape(str(label))}</th>'
                   f'<td>{html.escape(str(value))}</td></tr>' for label, value in rows)
    return ('<table class="kpi-fact-table"><thead><tr><th scope="col">Aspecto</th>'
            '<th scope="col">Explicación</th></tr></thead><tbody>' + body + '</tbody></table>')


def build_kpi_smart_html(identifier):
    """Separate measurable indicators from business goals not yet agreed with an owner."""
    measure, relevance, period = KPI_SMART_SCOPE[identifier]
    criteria = [
        ("S · Específico", KPI_PRESENTATION[identifier][2]),
        ("M · Medible", measure),
        ("A · Alcanzable", "No hay meta acordada. Primero se debe revisar el resultado de partida y los recursos disponibles para saber qué objetivo es viable."),
        ("R · Relevante", relevance),
        ("T · Temporal", period + " El plazo de una meta se define cuando exista un objetivo acordado."),
    ]
    return ('<div class="kpi-smart"><h4>Criterios SMART</h4>'
            '<p>SMART ayuda a definir objetivos concretos, medibles, viables, útiles y con plazo. Aquí se distingue lo que ya se mide de las metas que todavía no se han acordado.</p>'
            + build_kpi_table_html(criteria) + '</div>')



def build_kpi_card_html(indicator, guide_row):
    """A short, scannable summary; formulas and evidence belong to its disclosure."""
    title, symbol, summary = KPI_PRESENTATION[indicator["ID"]]
    return (f'<div class="kpi-tile-summary">{build_component_symbol(symbol)}'
            f'<h3>{html.escape(title)}</h3><p>{html.escape(summary)}</p></div>')


KPI_ICONS = {"K1": ":material/compare_arrows:", "K2": ":material/hub:",
             "K3": ":material/location_on:", "K4": ":material/calendar_month:",
             "K5": ":material/schedule:", "K6": ":material/notification_important:",
             "K7": ":material/join_inner:", "K8": ":material/verified_user:"}


def build_kpi_relief_css(mode):
    """Local vector relief, transparent background; no images or external assets."""
    palette = charts.get_palette(mode)
    rules = []
    for identifier, (_, symbol, _) in KPI_PRESENTATION.items():
        shape = COMPONENT_SYMBOLS[symbol]
        for active in (False, True):
            ink = palette["accent"] if active else palette["strong_text"]
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="72" height="80" viewBox="0 0 72 80">'
                   f'<ellipse cx="36" cy="70" rx="15" ry="1.5" fill="{ink}" opacity=".035"/>'
                   f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
                   f'<g transform="translate(14.7 10) scale(1.3)" stroke="{ink}" opacity=".12" stroke-width="2.2">{shape}</g>'
                   f'<g transform="translate(14 9) scale(1.3)" stroke="{ink}" stroke-width="2">{shape}</g>'
                   '</g></svg>')
            encoded = base64.b64encode(svg.encode()).decode()
            qualifier = '[kind="primary"]' if active else ''
            rules.append(f'.st-key-choose_{identifier} button{qualifier} [data-testid="stIconMaterial"] '
                         + '{background-image:url("data:image/svg+xml;base64,' + encoded + '");}')
    return "\n".join(rules)


def select_kpi(identifier):
    st.session_state["selected_kpi"] = identifier
    st.query_params[KPI_PARAMETER] = identifier


@st.cache_data
def read_kpi_observation(database_version, identifier):
    """One explicitly scoped observation, never a fabricated global average or target."""
    if identifier in ("K1", "K2", "K3", "K4", "K5"):
        query = {"K1": "k1_margin", "K2": "k2_channel_gap", "K3": "k3_regional_index",
                 "K4": "k4_seasonal_index", "K5": "k1_margin"}[identifier]
        rows = project.select_example_rows(read_indicator_for_key(query, project.EXAMPLE_KEY),
                   region=None if identifier == "K4" else project.EXAMPLE_REGION,
                   channel=project.EXAMPLE_OTHER_CHANNEL if identifier == "K2" else project.EXAMPLE_CHANNEL)
        if identifier == "K2":
            rows = rows[rows["reference_channel"] == project.EXAMPLE_CHANNEL]
        if rows.empty:
            return [("Resultado observado", "Sin datos comparables para la serie de referencia.")]
        row = rows.loc[rows["week_start"].idxmax()]
        scope = " · ".join(str(project.EXAMPLE_KEY[c]) for c in queries.KEY_COLUMNS)
        scope += " · " + str(row["channel"])
        if "region" in row:
            scope += " · " + str(row["region"])
        result = [("Serie de referencia", scope), ("Periodo del resultado", "Semana del " + project.format_week(row["week_start"]))]
        if identifier == "K5":
            best = lag.find_lag(lag.correlate_by_lag(rows)) if lag.has_enough_weeks(rows) else None
            result[1] = ("Periodo del resultado", f"{project.format_week(rows['week_start'].min())} a {project.format_week(rows['week_start'].max())}")
            value = "Sin historia suficiente" if best is None else (charts.describe_weeks(best[0]) if lag.is_clear_relation(best[1], best[2]) else "Sin relación clara")
            return result + [("Resultado observado", value), ("Comparación", "Cambios mayoristas frente a cambios del consumidor; desfases de 0 a 8 semanas.")]
        field = {"K1": "margin", "K2": "gap", "K3": "regional_index", "K4": "seasonal_index"}[identifier]
        value = charts.format_signed_percent(float(row[field]) * 100) if identifier in ("K1", "K2") else charts.format_index(row[field])
        reference = {"K1": "Precio mayorista de la misma semana, región y unidad.",
                     "K2": "Precio en " + str(row.get("reference_channel", "")) + ", misma semana, región y unidad.",
                     "K3": "1 = promedio simple de las regiones con precio en ese canal y semana.",
                     "K4": "1 = promedio de las semanas disponibles del mismo año; el año en curso es provisional."}[identifier]
        prior = rows[rows["week_start"] == row["week_start"] - pd.Timedelta(days=7)]
        previous = "No hay dato comparable en la semana anterior." if prior.empty else (
            charts.format_signed_percent(float(prior.iloc[0][field]) * 100) if identifier in ("K1", "K2") else charts.format_index(prior.iloc[0][field]))
        return result + [("Resultado observado", value), ("Referencia de cálculo", reference), ("Semana anterior · mismo indicador", previous)]
    if identifier == "K6":
        rows = read_price_alerts()
        week = pd.Timestamp(read_latest_week())
        counts = [len(rows[rows["week_start"] == date]) for date in (week, week - pd.Timedelta(days=7))]
        return [("Resultado observado", f"{counts[0]} alertas"), ("Periodo del resultado", "Semana del " + project.format_week(week)),
                ("Comparación", f"{counts[1]} alertas en la semana anterior; diferencia: {counts[0] - counts[1]:+d}."),
                ("Alcance", "Todos los productos y canales; cambios fuera del rango habitual de las 12 semanas anteriores.")]
    if identifier == "K7":
        matched, total = read_match_coverage()
        _, first, last = project.read_week_span()
        return [("Resultado observado", charts.format_percent(matched / total * 100) if total else "Sin datos"),
                ("Comparación", f"{matched:,} claves con cruce de {total:,} claves del consumidor."),
                ("Periodo del resultado", f"Histórico: {first} a {last}"),
                ("Alcance", "Cobertura del cruce definida en el ETL; no representa ventas ni población.")]
    run = read_latest_run()
    share = run["rows_rejected"] / run["rows_read"] * 100 if run["rows_read"] else None
    return [("Resultado observado", charts.format_percent(share) if share is not None else "Sin filas leídas"),
            ("Periodo del resultado", str(run["started_at"])),
            ("Comparación", f"{run['rows_rejected']:,} filas rechazadas de {run['rows_read']:,} filas leídas en esta carga."),
            ("Alcance", "Última carga registrada; comparación de proporción, no contra una meta.")]


def show_kpi_details(indicator, guide_row, question, example_steps, is_requested=False):
    """One full-width reading area, updated by the icon selector above it."""
    identifier = indicator["ID"]
    with st.container(key="kpi_reading"):
        st.subheader(KPI_PRESENTATION[identifier][0])
        st.caption("K1–K5 muestran una serie de referencia identificada en la ficha, no un promedio de todos los productos. K6–K8 muestran el alcance indicado en su resultado.")
        summary_tab, smart_tab, example_tab = st.tabs(["Qué mide", "Objetivo y criterios SMART", "Ejemplo y consulta"])
        with summary_tab:
            measure, relevance, period = KPI_SMART_SCOPE[identifier]
            if identifier in ("K1", "K2", "K7", "K8"):
                measure += " La razón de la fórmula se multiplica por 100 para expresarla en %."
            rows = [("Indicador", KPI_PRESENTATION[identifier][0]),
                    ("Pregunta que responde", question),
                    *read_kpi_observation(get_database_version(), identifier),
                    ("Qué significa", guide_row["En palabras"]),
                    ("Para qué sirve", relevance),
                    ("Cómo se mide", measure),
                    ("Fórmula", indicator["Fórmula"]),
                    ("Periodo de análisis", period),
                    ("Meta", "Sin meta de negocio acordada. Este indicador describe o controla los datos; no se asigna un objetivo artificial."),
                    ("Límites", KPI_LIMITS[identifier])]
            st.markdown(build_kpi_table_html(rows), unsafe_allow_html=True)
            st.markdown(build_place_link(guide_row["Página"]), unsafe_allow_html=True)
        with smart_tab:
            st.markdown(build_kpi_smart_html(identifier), unsafe_allow_html=True)
        with example_tab:
            if example_steps:
                st.caption("Ejemplo real, calculado con la base actual.")
                st.markdown(build_kpi_table_html([(f"Paso {number}", step)
                            for number, step in enumerate(example_steps, 1)]), unsafe_allow_html=True)
            query_name = guide_row["Consulta"]
            st.markdown(build_link_html(f"Ver la consulta {query_name} explicada →",
                                        build_query_address(query_name)), unsafe_allow_html=True)


def show_kpi_legacy(mode):
    """Eight transparent icon buttons and a single shared detail area."""
    palette = charts.get_palette(mode)
    st.markdown(f"""<style>
    .st-key-kpi_catalog [data-testid="stHorizontalBlock"] {{display:grid; grid-template-columns:repeat(8,minmax(0,1fr)); gap:12px;}}
    .st-key-kpi_catalog [data-testid="stColumn"] {{width:100% !important; min-width:0;}}
    .st-key-kpi_catalog button {{
        width:100%; min-height:124px; padding:6px 4px; background:transparent !important;
        border:0 !important; border-radius:0; box-shadow:none !important;
        color:{palette['text']}; display:flex; flex-direction:column; gap:12px;
    }}
    .st-key-kpi_catalog button [data-testid="stIconMaterial"] {{
        font-size:0 !important; width:72px !important; height:80px !important; flex-shrink:0;
        background-repeat:no-repeat; background-position:center; background-size:contain;
        transition:transform .18s ease;
    }}
    .st-key-kpi_catalog button span:has(> [data-testid="stIconMaterial"]) {{
        width:72px; height:80px; flex-shrink:0;}}
    .st-key-kpi_catalog button [data-has-shortcut] {{display:flex; flex-direction:column;
        align-items:center; gap:3px;}}
    .st-key-kpi_catalog button p {{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
        font-size:.85rem; font-weight:400; letter-spacing:-.015em; white-space:normal !important;
        overflow:visible !important; overflow-wrap:normal !important; word-break:normal !important; line-height:1.5; text-overflow:clip !important; color:{palette['text']} !important;}}
    .st-key-kpi_catalog button[kind="primary"] p {{color:{palette['accent']} !important;}}
    .st-key-kpi_catalog button:hover {{color:{palette['accent']}; transform:translateY(-2px);}}
    .st-key-kpi_catalog button:hover [data-testid="stIconMaterial"] {{transform:translateY(-2px);}}
    .st-key-kpi_catalog button:focus-visible {{outline:2px solid {palette['accent']}; outline-offset:2px;}}
    .st-key-kpi_catalog button[kind="primary"] {{border-bottom:2px solid {palette['accent']} !important;
        color:{palette['accent']};}}
    .st-key-kpi_reading {{border-top:1px solid {palette['card_border']}; padding-top:16px;}}
    .st-key-kpi_reading h3 {{font-size:1.25rem;}}
    .kpi-fact-table {{width:100%; table-layout:fixed; border-collapse:collapse;
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; font-size:.86rem;}}
    .kpi-fact-table th, .kpi-fact-table td {{padding:10px 14px; text-align:left;
        vertical-align:top; border-bottom:1px solid {palette['card_border']};
        overflow-wrap:anywhere; white-space:normal; line-height:1.5;}}
    .kpi-fact-table th:first-child {{width:22%; font-weight:500;}}
    .kpi-fact-table thead th {{color:{palette['strong_text']}; background:{palette['card']};}}
    .kpi-fact-table tbody th {{color:{palette['strong_text']};}}
    .kpi-fact-table td {{color:{palette['text']};}}
    @media(max-width:600px) {{
        .kpi-fact-table th, .kpi-fact-table td {{padding:9px 7px; font-size:.8rem;}}
        .kpi-fact-table th:first-child {{width:32%;}}
    }}
    @media(max-width:1100px) {{
        .st-key-kpi_catalog [data-testid="stHorizontalBlock"] {{grid-template-columns:repeat(4,minmax(0,1fr));}}
    }}
    @media(max-width:600px) {{
        .st-key-kpi_catalog [data-testid="stHorizontalBlock"] {{grid-template-columns:repeat(2,minmax(0,1fr));}}
    }}
    @media(prefers-reduced-motion:reduce) {{
        .st-key-kpi_catalog button:hover,
        .st-key-kpi_catalog button:hover [data-testid="stIconMaterial"] {{transform:none; transition:none;}}
    }}
    {build_kpi_relief_css(mode)}
    </style>""", unsafe_allow_html=True)
    questions = {row["#"]: row["Pregunta"]
                 for row in project.read_design_table(project.QUESTIONS_HEADING)}
    guide_rows = {row["KPI"]: row for row in project.read_guide_table("KPI")}
    indicators = project.read_design_table(project.INDICATORS_HEADING)
    by_id = {indicator["ID"]: indicator for indicator in indicators}
    requested = st.query_params.get(KPI_PARAMETER)
    selected = requested if requested in by_id else st.session_state.get("selected_kpi", "K1")
    if selected not in by_id:
        selected = "K1"
    st.session_state["selected_kpi"] = selected
    with st.container(key="kpi_catalog"):
        for offset in range(0, len(indicators), 8):
            columns = st.columns(8, gap="small")
            for column, indicator in zip(columns, indicators[offset:offset + 8]):
                identifier = indicator["ID"]
                title, _, description = KPI_PRESENTATION[identifier]
                with column:
                    st.button(title, icon=KPI_ICONS[identifier], key=f"choose_{identifier}",
                              type="primary" if identifier == selected else "secondary",
                              help=description, use_container_width=True,
                              on_click=select_kpi, args=(identifier,))
    indicator = by_id[selected]
    examples = build_cached_kpi_examples(get_database_version())
    question = questions.get(indicator["Pregunta"], "¿La carga de datos es confiable?")
    show_kpi_details(indicator, guide_rows[selected], question, examples[selected])


@st.cache_data
def read_explorer_facets(version):
    return data_browser.facets()


def show_data_page(mode):
    show_page_header("Explorar datos de precios", "Cada fila muestra el precio de un producto, variedad y calidad, en una región, canal, unidad y semana.")
    options, first, last = read_explorer_facets(get_database_version())
    apply_home_data_context(options, first, last)
    st.caption("Cada fila es un precio semanal agregado. Los precios excluidos de indicadores se conservan en la vista Precios semanales.")
    if st.query_params.get('_home_key'):
        address=build_page_address(PAGE_HOME)
        context={k:v for k,v in st.query_params.to_dict().items() if k.startswith('_home_')}
        st.markdown(build_link_html('← Volver al producto en el dashboard',address+('&' if '?' in address else '?')+urlencode(context)),unsafe_allow_html=True)
        if st.query_params.get('_home_region') == ALL_VALUES:
            st.caption("Origen: promedio nacional del dashboard. Aquí puedes revisar los precios regionales que componen ese promedio, en las dos semanas seleccionadas.")
    if st.button("Restablecer filtros", key="data_reset"):
        for name in list(st.session_state):
            if name.startswith("data_") and name != "data_reset":
                del st.session_state[name]
        st.query_params.pop("datos_modo", None)
        for name in list(st.query_params):
            if name.startswith('_home_'):
                st.query_params.pop(name,None)
        st.rerun()
    requested = st.query_params.get("datos_modo")
    if requested == "brecha" and requested != st.session_state.get("data_requested_mode"):
        st.session_state["data_requested_mode"] = requested
        st.session_state["data_mode"] = data_browser.MODES[2]
    if requested != "brecha":
        st.session_state["data_requested_mode"] = None
    data_mode = st.radio("Vista de datos", data_browser.MODES, horizontal=True, key="data_mode")
    scope_col, size_col, sort_col, direction_col = st.columns([2,1,2,1])
    period = scope_col.selectbox("Periodo", ["Todo el histórico", "Última semana", "Rango de fechas"], key="data_period")
    size = size_col.number_input("Filas por página", min_value=8, max_value=100, value=100, key="data_size")
    sorts = ['week_start','product','region','channel'] + (['margin','wholesale_price','consumer_price'] if data_mode == data_browser.MODES[2] else ['price','observation_count'] + (['variation'] if data_mode == data_browser.MODES[1] else []))
    sort = sort_col.selectbox("Ordenar resultados", sorts, format_func=lambda f: data_browser.LABELS.get(f,f), key="data_sort_"+str(data_browser.MODES.index(data_mode)))
    descending = direction_col.selectbox("Orden", ["Descendente","Ascendente"], key="data_direction") == "Descendente"
    start = end = None
    if period == "Última semana":
        start = end = last
    elif period == "Rango de fechas":
        dates = st.date_input("Desde / hasta", value=(pd.Timestamp(first).date(),pd.Timestamp(last).date()), min_value=pd.Timestamp(first).date(), max_value=pd.Timestamp(last).date(), key="data_dates")
        if len(dates) != 2:
            st.info("Selecciona ambas fechas para consultar."); return
        start, end = dates
    fields = list(data_browser.FIELDS)
    if data_mode == data_browser.MODES[2]:
        fields.remove('flag')
    filters = {}
    with st.expander("Filtrar productos, regiones, canales y calidad", expanded=True):
        for offset in range(0,len(fields),4):
            for column, field in zip(st.columns(4),fields[offset:offset+4]):
                value = column.selectbox(data_browser.FIELDS[field], [None]+options[field], key="data_filter_"+field,
                    format_func=lambda v: "Todos" if v is None else FLAG_NAMES.get(v,v), placeholder="Todos")
                if value is not None:
                    filters[field] = value
    signature = repr((data_mode,filters,str(start),str(end),sort,descending,size))
    if signature != st.session_state.get("data_signature"):
        st.session_state["data_page"] = 0
        st.session_state["data_signature"] = signature
    rows,total,page = data_browser.read_page(data_mode,filters,start,end,sort,descending,
                         st.session_state.get("data_page",0),int(size))
    st.session_state["data_page"] = page
    pages = max(1,(total+size-1)//size)
    left,center,right = st.columns([1,3,1])
    if left.button("← Anterior", disabled=page == 0, key="data_previous"):
        st.session_state["data_page"] -= 1; st.rerun()
    center.caption(f"{total:,} resultados · página {page+1} de {pages} · filas {page*size+1 if total else 0}–{min((page+1)*size,total)}".replace(",","."))
    if right.button("Siguiente →", disabled=page+1 >= pages, key="data_next"):
        st.session_state["data_page"] += 1; st.rerun()
    display = rows.drop(columns=['record_id','percentage'],errors='ignore').copy()
    if 'margin' in display:
        display['Comparabilidad'] = display['margin'].map(lambda v: 'Revisar formato (>300 %)' if v > MAXIMUM_COMPARABLE_GAP else 'Dentro del rango de comparación')
        display['margin'] *= 100
    if 'flag' in display:
        display['flag'] = display['flag'].map(lambda v: FLAG_NAMES.get(v,v))
    if 'variation' in display:
        display.insert(0,'Comparación semanal',display['variation'].map(
            lambda value: 'Sin comparación' if pd.isna(value) else 'Con semana anterior'))
    display = display.rename(columns=data_browser.LABELS)
    formats = {data_browser.LABELS[field]:home_mockup.money
               for field in ('price','previous_price','consumer_price','wholesale_price')
               if data_browser.LABELS[field] in display}
    formats.update({data_browser.LABELS[field]:lambda value:home_mockup.percent(value,True)
                    for field in ('variation','margin') if data_browser.LABELS[field] in display})
    formats['Semana'] = lambda value: pd.Timestamp(value).strftime('%d-%m-%Y')
    # Styler controls display only: native sorting and CSV keep numeric precision.
    st.dataframe(display.style.format(formats,na_rep="Sin comparación"), hide_index=True,
                 use_container_width=True, height=min(500,max(150,36*(len(display)+1)+4)))
    st.download_button("Descargar esta página (CSV)", display.to_csv(index=False).encode('utf-8-sig'), 'precios-pagina.csv', 'text/csv', key="data_csv")
    st.caption("La ordenación superior se aplica a todos los resultados antes de paginar. La ordenación al pulsar una columna solo reorganiza la página visible.")
    st.caption("Precios en pesos chilenos, redondeados para leer. La descarga conserva la precisión original. Sin comparación significa que falta un precio anterior válido.")
    if data_mode == data_browser.MODES[2]:
        st.caption("Brecha = (consumidor − mayorista) / mayorista. Misma semana, producto, variedad, calidad, región y unidad. No mide ganancia; los valores altos requieren revisar formato y comparabilidad.")
    elif data_mode == data_browser.MODES[1]:
        st.caption("Variación = (precio actual / precio anterior − 1) × 100. Se compara la misma serie regional con exactamente siete días antes. Sin precio anterior válido, no se calcula.")


def apply_home_data_context(options, first, last):
    """Apply a validated dashboard drill-through once, before creating data widgets."""
    marker=repr({k:v for k,v in st.query_params.to_dict().items() if k.startswith('_home_')})
    token=st.query_params.get('_home_key')
    if not token or len(token)>6000 or st.session_state.get('data_home_context')==marker:
        return
    try:
        payload=json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        if set(payload)!=set(queries.KEY_COLUMNS+['channel']):
            return
        if any(not isinstance(value,str) or value not in options[field] for field,value in payload.items()):
            return
        week=pd.Timestamp(st.query_params.get('_home_week'))
        if pd.isna(week) or not pd.Timestamp(first)<=week<=pd.Timestamp(last):
            return
    except (ValueError,TypeError,UnicodeError):
        return
    for field in data_browser.FIELDS:
        st.session_state['data_filter_'+field]=payload.get(field)
    region=st.query_params.get('_home_region')
    st.session_state['data_filter_region']=region if region in options['region'] else None
    st.session_state['data_filter_flag']='SIN_MARCA'
    st.session_state['data_mode']=data_browser.MODES[1]
    st.session_state['data_period']='Rango de fechas'
    st.session_state['data_dates']=(max(week-pd.Timedelta(days=7),pd.Timestamp(first)).date(),week.date())
    st.session_state['data_page']=0
    st.session_state['data_home_context']=marker


KPI_QUESTIONS = {"K1":"¿Cuánto más cuesta al consumidor que al mayorista?",
    "K2":"¿Cuánto difiere el precio entre canales de venta?", "K3":"¿Cómo se compara el precio regional con el promedio del canal?",
    "K4":"¿En qué periodos el precio supera su promedio anual?", "K5":"¿Con qué desfase se relacionan cambios mayoristas y del consumidor?",
    "K6":"¿Qué productos cambiaron fuera de su rango habitual?", "K7":"¿Qué proporción de productos permite cruzar mayorista y consumidor?",
    "K8":"¿Qué proporción de filas rechazó la última carga?"}
# The path of a KPI, seen at once from left to right: its result, its context, its query.
# Each node sits on the top edge of its card; the line joins them at three heights (D-090).
KPI_FIGURE = re.compile(r"^([+\-−]?[\d.,]+(?:\s?%)?)\s*(.*)$")
# Card columns in % of the path width, and the height of each node on the line, in px.
KPI_COLUMNS = (30, 36, 28)
KPI_GAP = 3
KPI_NODE_HEIGHTS = (44, 128, 44)
KPI_BAND_HEIGHT = 160
KPI_ICONS_SVG = {
    "trend": '<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "bars": '<path d="M5 19V11M10 19V6M15 19v-5M20 19V9"/>',
    "code": '<path d="M8 7l-5 5 5 5M16 7l5 5-5 5"/>',
}


def split_kpi_figure(result):
    """(figure, unit): «43 alertas» → («43», «alertas»); a sentence stays whole as unit."""
    match = KPI_FIGURE.match(result.strip())
    return (match.group(1), match.group(2).lstrip("· ")) if match else ("", result)


def build_kpi_icon(name):
    return (f'<svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{KPI_ICONS_SVG[name]}</svg>')


def kpi_node_positions():
    """Horizontal centre of each card, in % of the path width."""
    left, centres = 0, []
    for width in KPI_COLUMNS:
        centres.append(left + width / 2)
        left += width + KPI_GAP
    return centres


def build_kpi_path_html():
    """The line from «Inicio» to «Detalle técnico» through the three nodes, drawn once."""
    (x1, x2, x3), (y1, y2, y3) = [x * 10 for x in kpi_node_positions()], KPI_NODE_HEIGHTS
    lead = f"M4 {y1} L{x1} {y1}"
    first = f"M{x1} {y1} C{x1 + 150} {y1},{x2 - 160} {y2},{x2} {y2}"
    second = f"M{x2} {y2} C{x2 + 170} {y2},{x3 - 150} {y3},{x3} {y3} L992 12"
    paths = "".join(f'<path class="{kind}" d="{d}" vector-effect="non-scaling-stroke"/>'
                    for kind, d in (("kpi-line", lead), ("kpi-line", first), ("kpi-line kpi-line-next", second)))
    nodes = "".join(f'<span class="kpi-node" style="left:{x}%;top:{y}px">{number}</span>' for number, (x, y)
                    in enumerate(zip(kpi_node_positions(), KPI_NODE_HEIGHTS), 1))
    return (f'<div class="kpi-band" aria-hidden="true"><svg viewBox="0 0 1000 {KPI_BAND_HEIGHT}" '
            f'preserveAspectRatio="none">{paths}</svg>{nodes}<span class="kpi-start"><i></i>Inicio</span>'
            '<span class="kpi-end">Detalle técnico<i></i></span></div>')


def build_kpi_card_head(number, title):
    return f'<div class="kpi-card-title"><span class="sr-only">{number}. </span>{html.escape(title)}</div>'


def build_kpi_impact_html(identifier, evidence, run_kind, freshness):
    """Card 1: the figure alone, large, with its meaning, the state of the data and the week."""
    result = evidence.get("Resultado observado", "Sin dato comparable")
    figure, unit = split_kpi_figure(result)
    if figure and not unit:
        unit = KPI_PRESENTATION[identifier][2]
    if identifier in ("K3", "K4") and figure:
        unit = "1 = " + ("promedio regional del canal" if identifier == "K3" else "promedio anual")
    comparison = evidence.get("Comparación", "")
    if "Semana anterior · mismo indicador" in evidence:
        comparison = "Semana anterior: " + evidence["Semana anterior · mismo indicador"]
    period = freshness if identifier == "K8" else evidence.get("Periodo del resultado", "")
    has_data = bool(figure) or result not in ("Sin datos", "Sin dato comparable")
    state, text = ((run_kind, "Carga correcta" if run_kind == "ok" else "Última carga con falla")
                   if has_data else ("neutral", "Sin dato comparable"))
    number = (f'<div class="kpi-figure">{html.escape(figure)}</div>' if figure
              else f'<div class="kpi-figure kpi-figure-text">{html.escape(result)}</div>')
    return (build_kpi_card_head(1, "Resultado") + number
            + (f'<div class="kpi-lead">{html.escape(unit)}</div>' if figure and unit else "")
            + f'<div class="kpi-rule"></div><div class="kpi-line-text kpi-status"><span class="kpi-state kpi-state-{state}">'
            f'<i></i>{html.escape(text)}</span><span>{html.escape(period)}</span></div>'
            + (f'<div class="kpi-line-text">{build_kpi_icon("trend")}{html.escape(comparison)}</div>' if comparison else ""))


def build_kpi_scope_html(evidence, period):
    """Context · Alcance: the reference series as chips, then what it is and its period."""
    series = evidence.get("Serie de referencia")
    if series:
        chips = "".join(f'<span>{html.escape(part)}</span>' for part in series.split(" · "))
        note = "Una serie de referencia identificada, no un promedio de todos los productos."
        body = f'<div class="kpi-chips">{chips}</div>'
    else:
        body, note = "", evidence.get("Alcance", "Sin alcance registrado.")
    return (body + '<div class="kpi-rule"></div>'
            f'<div class="kpi-line-text">{build_kpi_icon("info")}{html.escape(note)}</div>'
            f'<div class="kpi-line-text">{build_kpi_icon("bars")}{html.escape(period)}</div>')


@st.dialog("Consulta SQL", width="large")
def show_kpi_query_dialog(name):
    """The stored query, on demand, in a layer above the module: nothing moves under it."""
    st.caption(f"{name} · solo lectura, tal como está en el repositorio.")
    st.code(read_catalog_sql(name), language="sql", wrap_lines=True)
    st.markdown(build_link_html("Ver su resultado completo en Preguntas y resultados SQL →",
                                build_query_address(name)), unsafe_allow_html=True)


def build_kpi_module_css(mode):
    palette = charts.get_palette(mode)
    dark = palette['base'] == charts.BASE_DARK
    accent = palette['accent']
    glow = f"drop-shadow(0 0 6px {accent}) drop-shadow(0 0 14px {accent}66)" if dark else "none"
    sans = '-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",sans-serif'
    columns = " ".join(f"{width}%" for width in KPI_COLUMNS)
    # Columns start one flex gap (16 px) below the band: each top border crosses its node.
    offsets = [height - 16 for height in KPI_NODE_HEIGHTS]
    return f"""<style>
    .kpi-head .compact-header {{display:flex; align-items:baseline; flex-wrap:wrap; gap:6px 18px; margin:0 0 12px;}}
    .kpi-head h1 {{font-size:1.6rem !important; margin:0 !important; padding:0 !important;}}
    .kpi-head .kpi-sub {{color:{palette['text']}; font-size:.9rem;}}
    .kpi-head .page-freshness {{margin:0 0 0 auto; font-size:.82rem;}}
    .st-key-kpi_module {{border:1px solid {palette['card_border']}; border-radius:18px; padding:16px 22px 26px;
        background:{palette['card'] if not dark else f"radial-gradient(120% 90% at 50% 0%, {accent}14, transparent 60%), {palette['background']}"};}}
    .st-key-kpi_question [data-testid="stHorizontalBlock"] {{align-items:center; gap:12px;}}
    .kpi-question-label {{border:1px solid {palette['card_border']}; border-radius:10px; padding:9px 14px;
        font:500 .9rem {sans}; color:{palette['strong_text']}; text-align:center; white-space:nowrap;}}
    .st-key-kpi_path {{position:relative; margin-top:8px;}}
    .kpi-band {{position:absolute; left:0; right:0; top:0; height:{KPI_BAND_HEIGHT}px; pointer-events:none;}}
    .kpi-band svg {{position:absolute; inset:0; width:100%; height:100%; overflow:visible; filter:{glow};}}
    .kpi-line {{fill:none; stroke:{accent}; stroke-width:3; stroke-linecap:round;}}
    .kpi-line-next {{stroke-dasharray:7 9; stroke-width:2.4;}}
    .kpi-start, .kpi-end {{position:absolute; top:{KPI_NODE_HEIGHTS[0] - 40}px; display:flex; align-items:center; gap:8px;
        font:500 .78rem {sans}; color:{palette['strong_text']}; padding:4px 10px; border-radius:8px;
        border:1px solid {palette['card_border']}; background:{palette['card']};}}
    .kpi-start {{left:0;}} .kpi-end {{right:0; top:-8px;}}
    .kpi-start i, .kpi-end i {{width:9px; height:9px; border-radius:50%; border:2px solid {accent};}}
    .st-key-kpi_path > div > [data-testid="stHorizontalBlock"] {{display:grid !important;
        grid-template-columns:{columns}; column-gap:{KPI_GAP}%; align-items:start;}}
    .st-key-kpi_path [data-testid="stColumn"] {{width:auto !important; min-width:0;}}
    .st-key-kpi_card_1 {{margin-top:{offsets[0]}px;}} .st-key-kpi_card_2 {{margin-top:{offsets[1]}px;}}
    .st-key-kpi_card_3 {{margin-top:{offsets[2]}px;}}
    .st-key-kpi_card_1, .st-key-kpi_card_2, .st-key-kpi_card_3 {{position:relative; overflow:visible;
        border:1px solid {accent if dark else palette['card_border']}; border-color:{accent}55; border-radius:14px;
        padding:40px 22px 20px; background:{palette['card']};
        box-shadow:{f"0 0 0 1px {accent}12, 0 0 24px {accent}14" if dark else "0 10px 28px rgba(15,23,42,.07)"};}}
    .sr-only {{position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0);}}
    .kpi-node {{position:absolute; transform:translate(-50%,-50%); width:52px; height:52px;
        border-radius:50%; display:grid; place-items:center; z-index:2; font:600 1.35rem {sans};
        color:{palette['strong_text']}; background:{palette['card'] if not dark else palette['background']};
        border:3px solid {accent}; box-shadow:{f"0 0 14px {accent}, 0 0 30px {accent}55" if dark else f"0 0 0 5px {accent}22"};}}
    .kpi-card-title {{font:700 .95rem {sans}; letter-spacing:.06em; text-transform:uppercase;
        color:{palette['strong_text']}; margin-bottom:6px;}}
    .kpi-figure {{font:700 clamp(2.8rem,4.6vw,4.4rem)/1.05 {sans}; letter-spacing:-.035em; white-space:nowrap;
        color:{accent}; font-variant-numeric:tabular-nums; margin:4px 0 8px;
        text-shadow:{f"0 0 22px {accent}55" if dark else "none"};}}
    .kpi-figure-text {{white-space:normal; font-size:clamp(1.6rem,2.6vw,2.2rem);}}
    .kpi-lead {{font:400 1rem/1.4 {sans}; color:{palette['strong_text']};}}
    .kpi-rule {{height:1px; background:{palette['card_border']}; margin:14px 0 12px;}}
    .kpi-line-text {{display:flex; align-items:flex-start; gap:10px; font:400 .86rem/1.45 {sans};
        color:{palette['strong_text']}; margin:0 0 8px;}}
    .kpi-status {{flex-wrap:wrap; gap:4px 8px;}}
    .kpi-icon {{width:20px; height:20px; flex-shrink:0; stroke:{palette['text']};}}
    .kpi-state {{display:inline-flex; align-items:center; gap:8px; white-space:nowrap;}}
    .kpi-state i {{width:9px; height:9px; border-radius:50%; background:{palette['reference']};}}
    .kpi-state-ok {{color:#34c759;}} .kpi-state-ok i {{background:#34c759; box-shadow:0 0 8px #34c75999;}}
    .kpi-state-failed {{color:#ff9f0a;}} .kpi-state-failed i {{background:#ff9f0a;}}
    .st-key-kpi_card_2 [data-baseweb="tab-list"] {{gap:18px;}}
    .st-key-kpi_card_2 [data-baseweb="tab-panel"] {{padding-top:12px;}}
    .kpi-chips {{display:flex; flex-wrap:wrap; gap:8px;}}
    .kpi-chips span {{padding:5px 13px; border-radius:999px; font:400 .84rem {sans}; color:{palette['strong_text']};
        border:1px solid {palette['card_border']}; background:{palette['field']};}}
    .kpi-formula {{font:500 .84rem/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; padding:10px 12px;
        border-radius:10px; background:{palette['field']}; color:{palette['strong_text']};
        border:1px solid {palette['card_border']}; overflow-wrap:anywhere; margin-bottom:10px;}}
    .kpi-query-name {{font:500 .95rem ui-monospace,SFMono-Regular,Menlo,monospace; color:{palette['strong_text']};
        padding:11px 14px; border-radius:10px; background:{palette['field']}; border:1px solid {palette['card_border']};
        margin:6px 0 12px; overflow-wrap:anywhere;}}
    .st-key-kpi_query_open button {{width:100%; justify-content:flex-start; border:1.5px solid {accent} !important;
        color:{accent} !important; background:transparent !important; border-radius:10px; min-height:46px;
        font-weight:600;}}
    .st-key-kpi_query_open button p {{color:{accent} !important; font-weight:600;}}
    @media(max-width:900px) {{
        .kpi-band {{display:none;}}
        .st-key-kpi_path > div > [data-testid="stHorizontalBlock"] {{grid-template-columns:1fr; row-gap:14px;}}
        .st-key-kpi_card_1, .st-key-kpi_card_2, .st-key-kpi_card_3 {{margin-top:0; padding-top:20px;}}
        .kpi-card-title .sr-only {{position:static; width:auto; height:auto; clip:auto; color:{accent};}}
        .kpi-head .page-freshness {{margin-left:0;}}
        .kpi-card-title {{padding-left:0;}}
    }}
    </style>"""


def show_kpi_tab(mode):
    """The whole path of one KPI, in sight at once: result → context → query (D-090)."""
    st.markdown(build_kpi_module_css(mode), unsafe_allow_html=True)
    indicators = project.read_design_table(project.INDICATORS_HEADING)
    guide = {r['KPI']:r for r in project.read_guide_table('KPI')}
    by_id = {r['ID']:r for r in indicators}
    requested = st.query_params.get(KPI_PARAMETER,'K1')
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    freshness = format_chile_time(parse_run_start(latest_run['started_at']))
    with st.container(key="kpi_module"):
        with st.container(key="kpi_question"):
            label, choice = st.columns([2, 8])
            label.markdown('<div class="kpi-question-label">Pregunta de negocio</div>', unsafe_allow_html=True)
            selected = choice.selectbox("Pregunta de negocio", list(by_id),
                                        index=list(by_id).index(requested) if requested in by_id else 0,
                                        format_func=lambda k: f"{KPI_PRESENTATION[k][0]} — {KPI_QUESTIONS[k]}",
                                        key="kpi_register_selection", label_visibility="collapsed",
                                        on_change=lambda: select_kpi(st.session_state["kpi_register_selection"]))
        evidence = dict(read_kpi_observation(get_database_version(), selected))
        query_name = guide[selected]['Consulta']
        measure, _, period = KPI_SMART_SCOPE[selected]
        reference = evidence.get("Referencia de cálculo")
        with st.container(key="kpi_path"):
            st.markdown(build_kpi_path_html(), unsafe_allow_html=True)
            result, context, query = st.columns(3)
            with result, st.container(key="kpi_card_1"):
                st.markdown(build_kpi_impact_html(selected, evidence, run_kind, freshness), unsafe_allow_html=True)
            with context, st.container(key="kpi_card_2"):
                st.markdown(build_kpi_card_head(2, "Contexto"), unsafe_allow_html=True)
                scope_tab, logic_tab, limits_tab = st.tabs(["Alcance", "Lógica", "Límites"])
                scope_tab.markdown(build_kpi_scope_html(evidence, period), unsafe_allow_html=True)
                logic_tab.markdown(f'<div class="kpi-formula">{html.escape(by_id[selected]["Fórmula"])}</div>'
                                   f'<div class="kpi-line-text">{build_kpi_icon("info")}{html.escape(measure)}</div>'
                                   + (f'<div class="kpi-line-text">{build_kpi_icon("bars")}{html.escape(reference)}</div>'
                                      if reference else ""), unsafe_allow_html=True)
                limits_tab.markdown(f'<div class="kpi-line-text">{build_kpi_icon("info")}{html.escape(KPI_LIMITS[selected])}</div>'
                                    f'<div class="kpi-line-text">{build_kpi_icon("bars")}Sin meta de negocio acordada: '
                                    'el indicador describe o controla los datos.</div>', unsafe_allow_html=True)
            with query, st.container(key="kpi_card_3"):
                st.markdown(build_kpi_card_head(3, "Consulta")
                            + f'<div class="kpi-query-name">{html.escape(query_name)}</div>'
                            '<div class="kpi-line-text">Consulta guardada que produce este resultado, en solo lectura.</div>',
                            unsafe_allow_html=True)
                if st.button("Desplegar SQL", key="kpi_query_open", icon=":material/code:", use_container_width=True):
                    show_kpi_query_dialog(query_name)
                st.markdown(build_link_html("Abrir en el catálogo →", build_query_address(query_name)),
                            unsafe_allow_html=True)


def show_kpi_page(mode):
    """KPIs with a one-line header, so the whole path fits one screen."""
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    run_text = "Carga correcta" if run_kind == "ok" else "Última carga con falla"
    freshness = format_chile_time(parse_run_start(latest_run["started_at"]))
    st.markdown(f'<div class="kpi-head"><div class="compact-header"><h1>{html.escape(SECTION_KPI)}</h1>'
                '<span class="kpi-sub">Elige una pregunta y recorre su camino: resultado, contexto y consulta.</span>'
                f'<span class="page-freshness">Datos actualizados el {freshness} {build_chip(run_text, run_kind)}</span></div></div>',
                unsafe_allow_html=True)
    show_kpi_tab(mode)


def describe_rule_evidence(rule):
    """Real figure of one rule from datos.db, or a dash when the base cannot show it."""
    if rule == "RN-06":
        return project.describe_margin_evidence(
            int(read_key_options("k1_margin")["row_count"].sum()))
    if rule == "RN-11":
        # The saved example row is long: it goes in the details, not in the card.
        return project.describe_rejection_evidence(read_indicator("k8_rejected_rows"))
    return read_cached_rule_evidence(get_database_version()).get(rule, "—")


def build_rule_card_html(rule, guide_row):
    """One rule: what it does with a row and its real figure in datos.db."""
    evidence = describe_rule_evidence(rule)
    if evidence[:2].istitle():
        # After the colon a sentence goes on in lower case; codes and numbers stay.
        evidence = evidence[0].lower() + evidence[1:]
    text = (f"En datos.db: {evidence}" if evidence != "—"
            else "La base no guarda una cifra para esta regla.")
    return build_info_card_html(guide_row["Qué hace con la fila"], text, label=rule)


def show_rule_details(rules, design_rules, guide_rows, where):
    """The whole rule, why it exists, its documented example and where it happens."""
    with st.expander("Ver detalles: regla completa, por qué y dónde ocurre", expanded=False):
        for rule in rules:
            guide_row = guide_rows[rule]
            example = guide_row["Ejemplo documentado"]
            st.markdown(f"**{rule}.** {design_rules[rule]}  \n**Por qué:** {guide_row['Por qué']}"
                        + (f"  \n**Ejemplo documentado:** {example}" if example != "—" else ""))
            if rule == "RN-11" and project.read_rejection_example():
                st.markdown("**Ejemplo de fila rechazada, tal como se guardó:**")
                st.code(project.read_rejection_example(), language="json", wrap_lines=True)
        st.markdown(f"**Dónde ocurre:** {where}.")


def show_rules_tab(mode):
    """RN-01 to RN-14 in the order the data goes through them, with real evidence (D-057)."""
    show_section_intro("Reglas de calidad", "Las 14 reglas que sigue cada fila, en el orden en "
                       "que el ETL las aplica, con lo que hace cada una y su cifra real en la "
                       "base.")
    design_rules = {rule["ID"]: rule["Regla"]
                    for rule in project.read_design_table(project.RULES_HEADING)}
    guide_rows = {row["Regla"]: row for row in project.read_guide_table("Reglas de calidad")}
    for number, (stage, lead, rules, where) in enumerate(RULE_STAGES, start=1):
        show_section_intro(f"{number}. {stage}", lead, True)
        show_info_cards([build_rule_card_html(rule, guide_rows[rule]) for rule in rules])
        show_rule_details(rules, design_rules, guide_rows, where)


def show_sections_folded(text):
    """Each '## ' section of a document in its own box, open by default."""
    for heading, body in project.split_sections(text):
        with st.expander(heading, expanded=False):
            st.markdown(body)


def split_bold_label(text):
    """(label, rest) of a paragraph that starts with «**Label:**»."""
    match = re.match(r"\*\*(.+?):\*\* ?(.*)", text, flags=re.DOTALL)
    return (match.group(1), match.group(2)) if match else ("", text)


def build_table_cards_html(rows, title_column, text_column, action_column=None):
    """A lookup table as cards: one row per card, its action as the note."""
    return [build_info_card_html(row[title_column], row[text_column],
                                 note=f"Qué hacer: {row[action_column]}" if action_column
                                 else None) for row in rows]


def show_weekly_run(manual):
    """What the weekly job does, in order, and what happens when a step fails."""
    section = project.read_section(manual, "Qué pasa cada martes")
    paragraphs = project.read_paragraphs(section)
    show_section_intro("Qué pasa cada martes", paragraphs[0], True)
    st.markdown(build_steps_html(project.read_numbered_items(section)),
                unsafe_allow_html=True)
    show_info_cards([build_info_card_html("Nada se guarda a medias", paragraphs[-1],
                                          is_warning=True)])


def show_owner_tasks(manual):
    """What runs alone and the four tasks of the author."""
    section = project.read_section(manual, "Tareas del autor y tareas automáticas")
    automatic_label, automatic_text = split_bold_label(project.read_paragraphs(section)[0])
    show_section_intro("Qué hace el autor", "Lo automático no necesita a nadie; estas "
                       "tareas, sí.", True)
    show_info_cards([build_info_card_html(automatic_label, automatic_text)]
                    + [build_info_card_html(label, text)
                       for label, text in project.parse_labeled_items(section)])


def show_failures(manual):
    """Where a failure shows, and what to do, folded by kind of failure."""
    section = project.read_section(manual, "Cómo leer un aviso rojo")
    paragraphs = project.read_paragraphs(section)
    show_section_intro("Si algo falla", paragraphs[0].rstrip(":") + ".", True)
    show_info_cards(build_table_cards_html(
        project.parse_markdown_table(project.read_section_lead(section)), "Dónde", "Qué se ve"))
    st.markdown(f'<div class="info-note">{format_inline(paragraphs[1])}</div>',
                unsafe_allow_html=True)
    for heading, title, text, action in [
            ("Qué significa que falle cada paso y qué hacer", "Paso", "Qué suele significar",
             "Qué hacer"),
            ("Fallas del panel publicado", "Qué se ve", "Qué significa", "Qué hacer")]:
        with st.expander(f"Ver detalles: {heading[0].lower() + heading[1:]}", expanded=False):
            show_info_cards(build_table_cards_html(project.parse_markdown_table(
                project.read_subsection(manual, heading)), title, text, action))


def show_known_limits(manual):
    """The limits of the current set-up, always in sight."""
    show_section_intro("Límites conocidos", "Cuándo el diseño actual deja de alcanzar, y qué "
                       "hacer entonces.", True)
    show_info_cards([build_info_card_html(label, text, is_warning=True) for label, text in
                     project.parse_labeled_items(project.read_section(manual,
                                                                      "Límites conocidos"))])


def show_manual_details(manual):
    """The rest of the manual, folded: the live diagram and administration."""
    show_section_intro("Más detalles", "Para quien quiere comprobar cómo funciona cada parte.",
                       True)
    for heading in ["Qué es real en el diagrama del pipeline", "Administración y enlaces"]:
        with st.expander(f"Ver detalles: {heading.lower()}", expanded=False):
            st.markdown(project.read_section(manual, heading).replace("### ", "#### "))
    # The terms of the manual live once, in the glossary of Inicio.
    st.markdown(f'<div class="info-note">Las siglas y los términos están en '
                f'{build_place_link(TAB_GLOSSARY, "")}.</div>', unsafe_allow_html=True)


def show_manual_tab(mode):
    """Read the operating manual as a document, without decorative cards."""
    manual = project.read_document(project.MANUAL_FILE)
    for heading in ["Qué pasa cada martes", "Tareas del autor y tareas automáticas",
                    "Cómo leer un aviso rojo", "Límites conocidos", "Recorrido del proyecto"]:
        st.subheader(heading)
        st.markdown(project.read_section(manual, heading))



def split_decision_title(title):
    """(«D-046», «Sin índice único…») of a decision heading."""
    number, _, name = title.partition(" · ")
    return number, name


def read_first_sentence(text):
    """The first sentence of a text, to show it in a card."""
    return re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]


def build_decision_card_html(title, body):
    """A key decision: its name and why it was taken, in one sentence."""
    number, name = split_decision_title(title)
    fields = dict(project.parse_labeled_items(body))
    return build_info_card_html(name, f"Por qué: {read_first_sentence(fields['Por qué'])}",
                                label=number)


def show_decisions_tab(mode):
    """A chronological engineering decision register, read as documentation."""
    decisions = project.list_decisions()
    st.caption("Registro de decisiones: alcance, justificación y consecuencias. Orden cronológico inverso.")
    for title, body in sorted(decisions, key=lambda item: int(split_decision_title(item[0])[0][2:]), reverse=True):
        with st.expander(title, expanded=False):
            st.markdown(body)



def build_clause_chips(query):
    """The SQL clauses a query uses, as labels."""
    explanations = {
        "WITH": "Nombra resultados intermedios para leer el cálculo por etapas.",
        "SELECT": "Elige las columnas y los cálculos que devuelve la consulta.",
        "JOIN": "Une tablas por sus claves para comparar los datos que corresponden.",
        "Auto-join": "Compara dos filas de la misma tabla, por ejemplo dos canales.",
        "WHERE": "Filtra las filas antes de agrupar o calcular.",
        "GROUP BY": "Agrupa filas de la misma serie para calcular su resumen.",
        "Agregados": "Resume filas con sumas, promedios, conteos, mínimos o máximos.",
        "HAVING": "Filtra grupos después del cálculo, por ejemplo por historia suficiente.",
        "ORDER BY": "Ordena el resultado para comparar o seguir el tiempo.",
        "Funciones de ventana": "Calcula sobre filas relacionadas sin perder cada observación.",
        "LAG": "Obtiene el valor anterior de una serie para medir el cambio.",
        "CASE": "Aplica una condición y devuelve el resultado que corresponde.",
        "Subconsultas": "Usa el resultado de una consulta dentro de otra.",
        "Funciones de fecha": "Interpreta fechas para agrupar o comparar semanas.",
        project.PYTHON_RECONCILIATION: "Un test comprueba que SQL y Python dan el mismo resultado.",
    }
    return " ".join(build_chip(clause, "neutral", explanations.get(clause))
                    for clause in query["clauses"])


def find_folder(path):
    """The folder of FOLDER_PURPOSES a file belongs to («» for the root)."""
    folders = [folder for folder, _, _ in FOLDER_PURPOSES if folder and path.startswith(folder)]
    return max(folders, key=len) if folders else ""


def build_file_line_html(path, description, address):
    """One file: its name (a link to it on GitHub when it is there) and what it does."""
    name = path.rstrip("/").split("/")[-1] + ("/" if path.endswith("/") else "")
    label = build_link_html(name, address) if address else f"<code>{html.escape(name)}</code>"
    return f"<li>{label}{' — ' + format_inline(description) if description else ''}</li>"


def show_repository_files():
    """Read the actual public configuration, tests and workflows inside the app."""
    groups = [
        ("Configuración · entorno y dependencias", ":material/settings:",
         ["requirements.txt", ".gitignore", ".devcontainer/devcontainer.json", ".streamlit/config.toml"]),
        ("Pruebas · tests/", ":material/fact_check:",
         [path.relative_to(project.PROJECT_DIR).as_posix() for path in
          sorted((project.PROJECT_DIR / "tests").glob("test_*.py"))]),
        ("Automatización · GitHub Actions", ":material/automation:",
         [path.relative_to(project.PROJECT_DIR).as_posix() for path in
          sorted((project.PROJECT_DIR / ".github/workflows").glob("*.yml"))]),
    ]
    languages = {".py": "python", ".sql": "sql", ".json": "json", ".toml": "toml", ".yml": "yaml"}
    for title, icon, paths in groups:
        with st.expander(title, expanded=False, icon=icon):
            for path in paths:
                file = project.PROJECT_DIR / path
                if file.is_file():
                    with st.expander(path, expanded=False):
                        st.code(project.read_document(file), language=languages.get(file.suffix, "text"),
                                line_numbers=True, height=420)
    st.caption("La documentación técnica y los enlaces externos tienen secciones independientes en el menú.")


# region Código y resultados (C03)
# One catalog for the whole window: each question with the stored query that answers
# it, its real result read from etl/datos.db on the read-only connection, how to read
# it, its SQL and its Python. Only stored queries run: the reader never writes SQL.
CATALOG_PARAMETER = "consulta"
CATALOG_SELECTED = "catalog_selected"
CATALOG_PREVIEW_ROWS = 12
CATALOG_TREND_WEEKS = 26
CATALOG_BAR_COUNT = 12
CATALOG_FILES = {project.MATCH_COVERAGE_QUERY_NAME: "etl/etl.py"}
QUERIES_PATH = "bi/queries.sql"


def build_query_address(name):
    """Address of the catalog opened on one query."""
    address = build_page_address(PAGE_QUERIES)
    return address + ("&" if "?" in address else "?") + urlencode({CATALOG_PARAMETER: name})


def read_catalog_sql(name):
    """The SQL of a catalog question, as it is written in its file."""
    if name == project.MATCH_COVERAGE_QUERY_NAME:
        return etl.MATCH_COVERAGE_QUERY.strip()
    return queries.load_queries()[name].strip()


def find_catalog_line(name):
    """(file, first line) of a query, so «Abrir archivo» lands on it on GitHub."""
    path = CATALOG_FILES.get(name, QUERIES_PATH)
    marker = ("MATCH_COVERAGE_QUERY = " if name in CATALOG_FILES else f"-- name: {name}\n")
    text = (project.PROJECT_DIR / path).read_text(encoding="utf-8")
    return path, text[:text.index(marker)].count("\n") + 1


def build_catalog_sql(name, filters=()):
    """(SQL, parameters) of a catalog result: the stored query, filtered from outside.

    The filter columns are fixed by the catalog; their values travel as parameters.
    """
    body = project.strip_sql_comments(read_catalog_sql(name)).strip().rstrip(";")
    if not filters:
        return body, ()
    conditions = " AND ".join(f"{column} = ?" for column, _ in filters)
    return (f"SELECT * FROM (\n{body}\n)\nWHERE {conditions}",
            tuple(value for _, value in filters))


@st.cache_data
def read_cached_catalog_rows(name, filters, database_version):
    """Rows of one catalog result, on the read-only connection."""
    sql, parameters = build_catalog_sql(name, filters)
    return queries.run_sql(sql, parameters=parameters)


def read_catalog_rows(name, filters=()):
    """Rows of one catalog result for the current database."""
    return read_cached_catalog_rows(name, filters, get_database_version()).copy()


@st.cache_data
def read_cached_catalog_row_counts(database_version):
    """Rows affected by every stored query, unfiltered: like a database engine's own
    row count next to each query, so the list reads without opening any of them (D-108)."""
    return {entry["name"]: len(read_cached_catalog_rows(entry["name"], (), database_version))
            for entry in CATALOG}


def read_catalog_row_counts():
    return read_cached_catalog_row_counts(get_database_version())


def build_example_filters(**columns):
    """The case the dashboard opens with (tomato, kilo), plus a few more columns."""
    return (tuple((column, project.EXAMPLE_KEY[column]) for column in queries.KEY_COLUMNS)
            + tuple(columns.items()))


def describe_example_product():
    key = project.EXAMPLE_KEY
    return f"{key['product']} {key['variety']} · {key['quality']}"


def describe_catalog_week(rows, prefix="Semana del"):
    if rows.empty:
        return "Sin semanas con dato"
    return f"{prefix} {project.format_week(rows['week_start'].max())}"


def keep_latest_week(rows):
    return rows[rows["week_start"] == rows["week_start"].max()]


def keep_last_weeks(rows, count=CATALOG_TREND_WEEKS):
    weeks = sorted(rows["week_start"].unique())[-count:]
    return rows[rows["week_start"].isin(weeks)]


def build_catalog_bars(labels, values, value_labels):
    """Rows for charts.draw_horizontal_bars."""
    return pd.DataFrame({"label": list(labels), "value": list(values),
                         "value_label": list(value_labels)})


def build_example_result(rows, filters, facts, chart):
    return {"rows": rows.reset_index(drop=True), "filters": filters, "facts": facts,
            "chart": chart if not rows.empty else None}


def build_regional_result(mode):
    """K3: the regions of the example, the latest week, as an index (100 = average)."""
    filters = build_example_filters(channel=project.EXAMPLE_CHANNEL)
    rows = keep_latest_week(read_catalog_rows("k3_regional_index", filters))
    rows = rows.sort_values("regional_index", ascending=False)
    bars = build_catalog_bars(rows["region"].map(charts.shorten_region_name),
                              rows["regional_index"] * 100,
                              [f"{value * 100:.0f}" for value in rows["regional_index"]])
    chart = (charts.draw_horizontal_bars(bars, "Índice regional (100 = promedio)", mode,
                                         reference_value=100, reference_label="100")
             if not bars.empty else None)
    facts = [describe_example_product(), project.EXAMPLE_CHANNEL,
             f"$/{project.EXAMPLE_KEY['normalized_unit']}", describe_catalog_week(rows)]
    return build_example_result(rows, filters, facts, chart)


def build_channel_gap_result(mode):
    """K2: each consumer channel against the street market, same region and week."""
    filters = build_example_filters(region=project.EXAMPLE_REGION,
                                    reference_channel=project.EXAMPLE_CHANNEL)
    rows = keep_latest_week(read_catalog_rows("k2_channel_gap", filters))
    bars = build_catalog_bars(rows["channel"], rows["gap"] * 100,
                              [charts.format_signed_percent(gap * 100) for gap in rows["gap"]])
    chart = (charts.draw_horizontal_bars(bars, f"Diferencia con {project.EXAMPLE_CHANNEL} (%)",
                                         mode, reference_value=0) if not bars.empty else None)
    facts = [describe_example_product(), f"Canales frente a {project.EXAMPLE_CHANNEL}",
             charts.shorten_region_name(project.EXAMPLE_REGION),
             f"$/{project.EXAMPLE_KEY['normalized_unit']}", describe_catalog_week(rows)]
    return build_example_result(rows, filters, facts, chart)


def build_margin_result(mode):
    """K1: consumer price against wholesale price, by region, the latest week."""
    filters = build_example_filters(channel=project.EXAMPLE_CHANNEL)
    rows = keep_latest_week(read_catalog_rows("k1_margin", filters))
    rows = rows.sort_values("margin", ascending=False)
    bars = build_catalog_bars(rows["region"].map(charts.shorten_region_name),
                              rows["margin"] * 100,
                              [charts.format_signed_percent(margin * 100)
                               for margin in rows["margin"]])
    chart = (charts.draw_horizontal_bars(bars, "Brecha de precio (%)", mode, reference_value=0)
             if not bars.empty else None)
    facts = [describe_example_product(), f"{project.EXAMPLE_CHANNEL} frente a Mayorista",
             f"$/{project.EXAMPLE_KEY['normalized_unit']}", describe_catalog_week(rows)]
    return build_example_result(rows, filters, facts, chart)


def build_national_price_result(mode):
    """K6: national weekly price of the example, by channel, the last 26 weeks."""
    filters = build_example_filters()
    rows = keep_last_weeks(read_catalog_rows("k6_national_weekly_price", filters))
    lines = rows.assign(week_start=pd.to_datetime(rows["week_start"]),
                        value=rows["national_price"])
    chart = (charts.draw_weekly_lines(lines, "Precio nacional ($)",
                                      lines["value"].map(project.format_money), mode, True)
             if not lines.empty else None)
    facts = [describe_example_product(), "Todos los canales",
             f"$/{project.EXAMPLE_KEY['normalized_unit']}",
             describe_catalog_week(rows, f"{CATALOG_TREND_WEEKS} semanas hasta el")]
    return build_example_result(rows, filters, facts, chart)


def build_seasonal_result(mode):
    """K4: each week of the latest year against the average of that year."""
    filters = build_example_filters(channel=project.EXAMPLE_CHANNEL)
    rows = read_catalog_rows("k4_seasonal_index", filters)
    rows = rows[rows["price_year"] == rows["price_year"].max()]
    area = rows.assign(week_start=pd.to_datetime(rows["week_start"]),
                       value=rows["seasonal_index"] * 100)
    chart = (charts.draw_single_weekly_area(area, "Índice estacional (100 = promedio del año)",
                                            area["value"].map(lambda value: f"{value:.0f}"),
                                            mode, reference_value=100)
             if not area.empty else None)
    year = rows["price_year"].max() if not rows.empty else "sin año"
    facts = [describe_example_product(), project.EXAMPLE_CHANNEL,
             f"$/{project.EXAMPLE_KEY['normalized_unit']}", f"Año {year}"]
    return build_example_result(rows, filters, facts, chart)


def build_weekly_variations_result(mode):
    """K5 in SQL: wholesale and consumer weekly changes of one series, side by side."""
    filters = build_example_filters(region=project.EXAMPLE_REGION,
                                    channel=project.EXAMPLE_CHANNEL)
    rows = keep_last_weeks(read_catalog_rows("k5_weekly_variations_sql", filters))
    lines = pd.concat([
        rows.assign(channel=WHOLESALE_LABEL, value=rows["wholesale_variation"] * 100),
        rows.assign(channel=project.EXAMPLE_CHANNEL, value=rows["consumer_variation"] * 100),
    ]).dropna(subset=["value"])
    lines["week_start"] = pd.to_datetime(lines["week_start"])
    chart = (charts.draw_weekly_lines(lines, "Cambio semanal (%)",
                                      lines["value"].map(charts.format_signed_percent),
                                      mode, False) if not lines.empty else None)
    facts = [describe_example_product(), f"Mayorista y {project.EXAMPLE_CHANNEL}",
             charts.shorten_region_name(project.EXAMPLE_REGION),
             f"$/{project.EXAMPLE_KEY['normalized_unit']}",
             describe_catalog_week(rows, f"{CATALOG_TREND_WEEKS} semanas hasta el")]
    return build_example_result(rows, filters, facts, chart)


def build_usual_range_result(mode):
    """K6 in SQL: the alerts of the latest week, largest change first."""
    filters = (("is_alert", 1),)
    rows = keep_latest_week(read_catalog_rows("k6_usual_range_sql", filters))
    rows = rows.reindex(rows["variation"].abs().sort_values(ascending=False).index)
    top = rows.head(CATALOG_BAR_COUNT)
    # Quality and unit too: two series of one product would share a bar name.
    bars = build_catalog_bars(top["product"] + " " + top["variety"] + " " + top["quality"]
                              + " · " + top["channel"] + " · $/" + top["normalized_unit"],
                              top["variation"] * 100,
                              [charts.format_signed_percent(value * 100)
                               for value in top["variation"]])
    chart = (charts.draw_horizontal_bars(bars, "Cambio frente a la semana anterior (%)", mode,
                                         reference_value=0, label_limit=320)
             if not bars.empty else None)
    facts = ["Todos los productos", "Todos los canales", "Unidad de cada serie",
             describe_catalog_week(rows)]
    return build_example_result(rows, filters, facts, chart)


def build_table_result(name, facts, chart_builder=None):
    """A result without a filter: the whole stored query, as a table (or a chart)."""
    def build(mode):
        rows = read_catalog_rows(name)
        chart = chart_builder(rows, mode) if chart_builder and not rows.empty else None
        return build_example_result(rows, (), facts, chart)
    build.__name__ = f"build_{name}_result"
    return build


def draw_flag_count_bars(rows, mode):
    """quality_flag_counts: weekly prices by source and flag."""
    bars = build_catalog_bars(
        rows["source"].map(lambda source: SOURCE_NAMES.get(source, source)) + " · "
        + rows["flag"].map(lambda flag: FLAG_NAMES.get(flag, flag)),
        rows["weekly_prices"], rows["weekly_prices"].map(charts.format_thousands))
    return charts.draw_horizontal_bars(bars, "Precios semanales", mode, label_limit=260)


def draw_unconvertible_bars(rows, mode):
    """quality_unconvertible_units: the products with most prices without a unit."""
    top = rows.head(CATALOG_BAR_COUNT)
    bars = build_catalog_bars(top["product"] + " " + top["variety"] + " " + top["quality"]
                              + " · " + top["channel"], top["weekly_prices"],
                              top["weekly_prices"].map(charts.format_thousands))
    return charts.draw_horizontal_bars(bars, "Precios semanales sin unidad comparable", mode,
                                       label_limit=260)


def build_match_coverage_result(mode):
    """K7: product keys with a margin over product keys with a consumer price."""
    rows = read_catalog_rows(project.MATCH_COVERAGE_QUERY_NAME)
    # The query returns two unnamed counts; they get a name to be read.
    rows.columns = ["keys_with_margin", "consumer_keys"]
    rows["coverage"] = rows["keys_with_margin"] / rows["consumer_keys"]
    return build_example_result(rows, (), ["Todos los productos", "Mayorista y consumidor",
                                           "Todas las semanas"], None)


PRICE_THEME = "Precios"
QUALITY_THEME = "Calidad de datos"
LIMIT_NO_DATA = "Sin dato no significa precio cero: esa región, canal o semana no se informó."
# Question, what it compares, how to read it, and the function that builds its result.
# "chart" says whether the question's own result draws a chart (D-108): true for
# every price question and the two quality ones with a chart_builder; the rest show
# only a table, so the list marks them 📋 instead of 📊.
CATALOG = [
    {"name": "k3_regional_index", "theme": PRICE_THEME, "question": "¿Dónde es más caro?",
     "compares": "Compara regiones para el mismo producto, canal, unidad y semana.",
     "reading": "100 es el promedio simple de las regiones con dato esa semana; 112 significa "
                "12 % sobre ese promedio. " + LIMIT_NO_DATA,
     "build": build_regional_result, "chart": True},
    {"name": "k2_channel_gap", "theme": PRICE_THEME, "question": "¿Cuánto difieren los canales?",
     "compares": "Compara cada canal de venta con la feria libre: misma región, producto, "
                 "unidad y semana.",
     "reading": "+20 % significa que ese canal cobró un 20 % más que la feria libre esa semana. "
                "Solo se comparan canales con precio en la misma semana.",
     "build": build_channel_gap_result, "chart": True},
    {"name": "k1_margin", "theme": PRICE_THEME,
     "question": "¿Cuánto separa al consumidor del mayorista?",
     "compares": "Compara el precio al consumidor con el mayorista: misma región, producto, "
                 "unidad y semana.",
     "reading": GAP_MEANING + " Solo hay brecha donde existen los dos precios.",
     "build": build_margin_result, "chart": True},
    {"name": "k6_national_weekly_price", "theme": PRICE_THEME,
     "question": "¿Cómo evolucionó el precio?",
     "compares": "Sigue el precio nacional semana a semana, por canal, para el mismo producto "
                 "y unidad.",
     "reading": "El precio nacional es el promedio simple de las regiones con dato: no pondera "
                "por población ni por volumen vendido. " + LIMIT_NO_DATA,
     "build": build_national_price_result, "chart": True},
    {"name": "k6_usual_range_sql", "theme": PRICE_THEME,
     "question": "¿Qué precios cambiaron fuera de lo habitual?",
     "compares": "Compara el cambio de cada semana con las 12 semanas anteriores de la misma "
                 "serie: producto, canal y unidad.",
     "reading": ALERT_MEANING + " Una serie sin 12 semanas previas no se juzga.",
     "build": build_usual_range_result, "chart": True},
    {"name": "k4_seasonal_index", "theme": PRICE_THEME,
     "question": "¿En qué semanas del año es más caro?",
     "compares": "Compara el precio nacional de cada semana con el promedio de su año: mismo "
                 "producto, canal y unidad.",
     "reading": "100 es el promedio del año; un año en curso se compara solo con las semanas "
                "ya cargadas.",
     "build": build_seasonal_result, "chart": True},
    {"name": "k5_weekly_variations_sql", "theme": PRICE_THEME,
     "question": "¿El precio mayorista anticipa al del consumidor?",
     "compares": "Pone lado a lado el cambio semanal del precio mayorista y del consumidor de "
                 "la misma serie: producto, región, canal y unidad.",
     "reading": "Muestra cambios, no causas. La relación entre ambos se mide en Python "
                "(bi/lag.py) y es descriptiva. Una semana sin la anterior no tiene cambio.",
     "build": build_weekly_variations_result, "chart": True},
    {"name": "quality_runs", "theme": QUALITY_THEME, "question": "¿La última carga funcionó?",
     "compares": "Lista las últimas ejecuciones del ETL, de la más reciente a la más antigua.",
     "reading": "Cada fila es una ejecución: cuándo empezó, su estado y cuántas filas leyó, "
                "cargó y rechazó.",
     "build": build_table_result("quality_runs", ["Todas las fuentes", "Últimas 10 cargas"]),
     "chart": False},
    {"name": "k8_rejected_rows", "theme": QUALITY_THEME,
     "question": "¿Qué datos quedaron fuera en la última carga?",
     "compares": "Cuenta las filas rechazadas por fuente y motivo, sobre las filas leídas.",
     "reading": "Una fila rechazada se guarda con su motivo; no se corrige ni se reemplaza "
                "por otro valor.",
     "build": build_table_result("k8_rejected_rows", ["Por fuente y motivo", "Última carga"]),
     "chart": False},
    {"name": "quality_rejected_rows", "theme": QUALITY_THEME,
     "question": "¿Cómo venían las filas rechazadas?",
     "compares": "Muestra cada fila rechazada tal como llegó, con su fuente y su motivo.",
     "reading": "Es la fila original del archivo de origen (RN-11): sirve para revisar la "
                "fuente, no para recalcular indicadores.",
     "build": build_table_result("quality_rejected_rows", ["Por fuente y motivo",
                                                           "Última carga"]),
     "chart": False},
    {"name": "quality_flag_counts", "theme": QUALITY_THEME,
     "question": "¿Cuántos precios entran en los indicadores?",
     "compares": "Cuenta los precios semanales por fuente y por marca de calidad.",
     "reading": "Los precios marcados se conservan en la base, pero no entran en los "
                "indicadores.",
     "build": build_table_result("quality_flag_counts", ["Mayorista y consumidor",
                                                         "Todas las semanas"],
                                 draw_flag_count_bars), "chart": True},
    {"name": "quality_outliers", "theme": QUALITY_THEME,
     "question": "¿Qué precios se marcaron como atípicos?",
     "compares": "Lista los precios semanales marcados como atípicos, del más reciente al más "
                 "antiguo.",
     "reading": "Atípico no significa error: el precio se conserva, pero queda fuera de los "
                "indicadores (RN-12).",
     "build": build_table_result("quality_outliers", ["Todos los productos",
                                                      "Todas las semanas"]), "chart": False},
    {"name": "quality_unconvertible_units", "theme": QUALITY_THEME,
     "question": "¿Qué precios no tienen unidad comparable?",
     "compares": "Cuenta, por producto y canal, los precios cuya unidad no se convierte a kilo "
                 "o unidad.",
     "reading": "Sin unidad comparable no hay precio comparable: se guarda, pero no se compara "
                "(RN-05).",
     "build": build_table_result("quality_unconvertible_units", ["Por producto y canal",
                                                                 "Todas las semanas"],
                                 draw_unconvertible_bars), "chart": True},
    {"name": "quality_week_range", "theme": QUALITY_THEME,
     "question": "¿Qué semanas cubre la base?",
     "compares": "Muestra la primera y la última semana cargadas, con su año.",
     "reading": "El año de una semana es el de su jueves (regla ISO), igual que en el índice "
                "estacional.",
     "build": build_table_result("quality_week_range", ["Toda la base"]), "chart": False},
    {"name": project.MATCH_COVERAGE_QUERY_NAME, "theme": QUALITY_THEME,
     "question": "¿Cuántos productos tienen brecha calculable?",
     "compares": "Compara las claves de producto con precio al consumidor y las que además "
                 "tienen precio mayorista comparable.",
     "reading": "Una clave sin brecha no es un error: el mayorista no informa ese producto, "
                "región o unidad. Vive en etl/etl.py porque cada carga la imprime.",
     "build": build_match_coverage_result, "chart": False},
]
CATALOG_BY_NAME = {entry["name"]: entry for entry in CATALOG}


def list_catalog_functions(name, build):
    """The Python that serves a question: its result, the read-only reader and, when
    there is one, the version a test reconciles with the SQL (D-049)."""
    functions = list(project.PYTHON_VERSIONS.get(name, []))
    if name == project.MATCH_COVERAGE_QUERY_NAME:
        functions.append(etl.measure_match_coverage)
    return functions + [build, build_catalog_sql, queries.run_sql, queries.open_database]


def match_catalog_search(entry, text):
    """True when every word of the search is in the question, its theme or its name."""
    haystack = " ".join([entry["question"], entry["compares"], entry["theme"],
                         entry["name"]]).lower()
    return all(word in haystack for word in text.lower().split())


def choose_catalog_entry():
    """The question shown: from the address when a link asks for one, then the list."""
    requested = st.query_params.get(CATALOG_PARAMETER)
    if requested in CATALOG_BY_NAME and requested != st.session_state.get(
            f"{CATALOG_SELECTED}_synced"):
        st.session_state[CATALOG_SELECTED] = requested
        st.session_state[f"{CATALOG_SELECTED}_synced"] = requested
    if st.session_state.get(CATALOG_SELECTED) not in CATALOG_BY_NAME:
        st.session_state[CATALOG_SELECTED] = CATALOG[0]["name"]
    return CATALOG_BY_NAME[st.session_state[CATALOG_SELECTED]]


CATALOG_THEMES = [PRICE_THEME, QUALITY_THEME]


def keep_catalog_choice(theme):
    """One theme's list changed: show that question, keep it in the address and clear
    the other theme's list so only one question ever reads as chosen (D-107)."""
    chosen = st.session_state.get(f"catalog_choice_{theme}")
    if chosen in CATALOG_BY_NAME:
        st.session_state[CATALOG_SELECTED] = chosen
        st.session_state[f"{CATALOG_SELECTED}_synced"] = chosen
        st.query_params[CATALOG_PARAMETER] = chosen
        for other in CATALOG_THEMES:
            if other != theme:
                st.session_state[f"catalog_choice_{other}"] = None


def describe_catalog_option(name, counts):
    """A question as a database engine would list its query: the question, its real
    row count (unfiltered, whole table) and whether it ends in a chart or a table
    (D-108)."""
    icon = "📊" if CATALOG_BY_NAME[name]["chart"] else "📋"
    count = counts.get(name, 0)
    word = "fila" if count == 1 else "filas"
    return f'{CATALOG_BY_NAME[name]["question"]} · {charts.format_thousands(count)} {word} {icon}'


def show_catalog_list(selected):
    """Left: the questions of the project, grouped by theme, each with its real row
    count and a 📊/📋 mark — a database engine's own summary next to each query —
    with a search; stacks on top on a phone (D-107, D-108)."""
    st.markdown('<div class="catalog-list-title">Consultas del proyecto</div>',
                unsafe_allow_html=True)
    text = st.text_input("Buscar consulta", key="catalog_search", icon=":material/search:",
                         placeholder="Buscar: región, canal, carga…",
                         label_visibility="collapsed")
    entries = [entry for entry in CATALOG if match_catalog_search(entry, text or "")]
    if not entries:
        st.caption("Ninguna consulta coincide con la búsqueda.")
        return
    counts = read_catalog_row_counts()
    for theme in CATALOG_THEMES:
        theme_entries = [entry for entry in entries if entry["theme"] == theme]
        if not theme_entries:
            continue
        st.caption(f"{theme.upper()} · {len(theme_entries)}")
        names = [entry["name"] for entry in theme_entries]
        key = f"catalog_choice_{theme}"
        st.session_state[key] = selected["name"] if selected["name"] in names else None
        st.radio(theme, names, key=key,
                 format_func=lambda name: describe_catalog_option(name, counts),
                 on_change=keep_catalog_choice, args=(theme,), label_visibility="collapsed")
    st.caption(f"{len(entries)} de {len(CATALOG)} consultas · precios y calidad de datos.")
    st.markdown(build_link_html("Funciones Python y archivos SQL →",
                                build_page_address(PAGE_CODE)), unsafe_allow_html=True)


def build_catalog_steps_html():
    """1 Pregunta → 2 Resultado → 3 Código: the order the detail reads in."""
    steps = " <span aria-hidden=\"true\">→</span> ".join(
        f'<span class="catalog-step"><b>{number}</b>{label}</span>'
        for number, label in [(1, "Pregunta"), (2, "Resultado"), (3, "Código")])
    return f'<div class="catalog-steps">{steps}</div>'


def build_external_link_html(text, address):
    """A link that leaves the app: it says where it goes and opens a new tab (↗)."""
    return (f'<a href="{html.escape(address)}" target="_blank" rel="noopener noreferrer">'
            f'{html.escape(text)} ↗</a>')


def build_github_link_html(text, address):
    """An external GitHub link with its brand mark, opening a new tab on a plain
    click (D-113): the global click handler no longer forces external links into
    the same frame, which GitHub refuses when this app runs behind an iframe."""
    icon = (f'<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" '
            f'aria-hidden="true" class="doc-github-icon">{architecture.brand_icons.logo_body("github")}</svg>')
    return (f'<a href="{html.escape(address)}" target="_blank" rel="noopener noreferrer" '
            f'class="doc-github-link">{icon}{html.escape(text)} ↗</a>')


def show_catalog_result(entry, result):
    """2 · The real result: chart or table, how to read it, the whole table and the CSV."""
    rows = result["rows"]
    with st.container(border=True, key="catalog_result"):
        st.markdown(f'<div class="catalog-block-title">Resultado de la consulta'
                    f'<span>{charts.format_thousands(len(rows))} filas · solo lectura</span>'
                    '</div>', unsafe_allow_html=True)
        if rows.empty:
            st.info("La consulta no devolvió filas con la base actual.")
        elif result["chart"] is not None:
            show_chart(result["chart"])
        else:
            st.caption("El resultado es una tabla. Abre el detalle para consultar sus filas.")
        st.markdown(f'<div class="catalog-reading"><b>Cómo leerlo.</b> '
                    f'{format_inline(entry["reading"])}</div>', unsafe_allow_html=True)
        with st.expander(f"Ver tabla completa · {charts.format_thousands(len(rows))} filas", expanded=False):
            st.dataframe(rows, hide_index=True, width="stretch")
        st.download_button("Descargar resultado (CSV)", rows.to_csv(index=False).encode("utf-8"),
                           file_name=f"{entry['name']}.csv", mime="text/csv",
                           icon=":material/download:", on_click="ignore",
                           key=f"catalog_download_{entry['name']}")


def show_catalog_code(entry, result):
    """3 · The code: the stored SQL (copy button on hover), its file on GitHub, how this
    result filtered it and the Python that serves it."""
    name = entry["name"]
    path, line = find_catalog_line(name)
    address = f"{project.build_github_url(path)}#L{line}"
    sql = read_catalog_sql(name)
    with st.expander("Ver el SQL que produce este resultado", expanded=False):
        st.markdown(f'<div class="catalog-block-title">Consulta SQL'
                    f'<span>{build_external_link_html(f"Abrir archivo · {path} en GitHub", address)}'
                    f'</span></div><div class="query-meta">Nombre en el código: '
                    f'<code>{html.escape(name)}</code> · {html.escape(path)}, línea {line} · '
                    f'{build_clause_chips(project.describe_query(sql))}</div>',
                    unsafe_allow_html=True)
        st.code(sql, language="sql", line_numbers=True, wrap_lines=True,
                height="content" if sql.count("\n") < 18 else 380)
        with st.expander(f"Ver consulta completa · {path}", expanded=False):
            executed, parameters = build_catalog_sql(name, result["filters"])
            st.caption("La consulta guardada, sin comentarios, tal como corrió para este "
                       "resultado en la conexión de solo lectura.")
            st.code(executed, language="sql", wrap_lines=True)
            if parameters:
                st.caption(f"Valores de cada «?», enviados aparte del texto: {list(parameters)}")
    with st.expander("Implementación Python · Ver funciones", expanded=False):
        for function in list_catalog_functions(name, entry["build"]):
            module = sys.modules[function.__module__]
            file = Path(module.__file__).resolve().relative_to(project.PROJECT_DIR).as_posix()
            st.markdown(f'<div class="query-meta"><code>{html.escape(function.__name__)}</code> · '
                        f'{build_external_link_html(file, project.build_github_url(file))}</div>',
                        unsafe_allow_html=True)
            st.code(inspect.getsource(function), language="python")


def show_catalog_detail(entry, mode):
    """Right: 1 the question and what it compares, 2 its result, 3 its code."""
    result = entry["build"](mode)
    facts = '<span aria-hidden="true"> · </span>'.join(
        f"<span>{html.escape(str(fact))}</span>" for fact in result["facts"])
    st.markdown(f'<div class="catalog-head"><div><h2 class="catalog-question">'
                f'{html.escape(entry["question"])}</h2><p class="catalog-compares">'
                f'{html.escape(entry["compares"])}</p><p class="catalog-facts">{facts}</p>'
                f'</div>{build_catalog_steps_html()}</div>', unsafe_allow_html=True)
    show_catalog_result(entry, result)
    show_catalog_code(entry, result)


def show_queries_page_header():
    """A one-line header, like the Dashboard's: title and freshness together, so the
    question list and its result are visible without scrolling past a tall title
    block (D-107)."""
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    run_text = "Carga correcta" if run_kind == "ok" else "Última carga con falla"
    freshness = format_chile_time(parse_run_start(latest_run["started_at"]))
    st.markdown(f'<div class="compact-header"><h1 title="Cada consulta, la pregunta que '
                f'responde y su resultado real, en solo lectura.">'
                f'{html.escape(SECTION_QUERIES)}</h1><span class="page-freshness">Datos al '
                f'{freshness} {build_chip(run_text, run_kind)}</span></div>',
                unsafe_allow_html=True)


def show_queries_tab(mode):
    """Código y resultados (C03): the list of questions on the left; the chosen one
    with its real result, how to read it and its code on the right."""
    entry = choose_catalog_entry()
    with st.container(key="catalog"):
        list_column, detail_column = st.columns([1, 2.7], gap="medium")
        with list_column, st.container(border=True, key="catalog_list"):
            show_catalog_list(entry)
        with detail_column:
            show_catalog_detail(entry, mode)


def show_queries_page(mode):
    show_queries_page_header()
    show_queries_tab(mode)
# endregion


FOLDER_CODE_LABELS = {
    "agent": "Ingesta · agent/ — descargar y validar las fuentes",
    "etl": "Transformación · etl/ — limpiar, normalizar y cargar",
    "bi": "Análisis y visualización · bi/ — consultas, indicadores y dashboard",
}


def show_files_tab(mode):
    """Code folders open initially, with purpose and actual source inside."""
    show_section_intro("Python · del origen al dashboard", "Cada carpeta reúne archivos con su propósito y su código real. Puedes plegarlos cuando quieras. "
                       "El orden sigue el recorrido de los datos.")
    catalog = project.list_code_walkthrough()
    for folder in dict.fromkeys(entry["folder"] for entry in catalog):
        with st.expander(FOLDER_CODE_LABELS.get(folder, f"{folder}/"), expanded=False,
                         icon={"agent": ":material/download:", "etl": ":material/filter_alt:",
                               "bi": ":material/analytics:"}.get(folder, ":material/folder:")):
            for entry in [entry for entry in catalog if entry["folder"] == folder]:
                with st.expander(f"{entry['number']:02} · {entry['path']} — {entry['title']}",
                                 expanded=False):
                    st.write(entry["purpose"])
                    st.caption(f"Entrada: {entry['input']} → Salida: {entry['output']}")
                    st.info(f"Problema que resuelve: {entry['challenge']}", icon=":material/lightbulb:")
                    st.code(entry["source"], language="python", line_numbers=True, height=420)
    show_section_intro("SQL · consultas y modelo", "Abre queries.sql para explorar las consultas "
                       "del proyecto, o un esquema para revisar las tablas. Los resultados "
                       "tienen su propia sección: Preguntas y resultados SQL.")
    for path, title in [("bi/queries.sql", "Consultas SQL: preguntas e indicadores del proyecto"),
                        ("etl/raw_schema.sql", "Capa bronce: conservar el archivo original"),
                        ("etl/schema.sql", "Modelo estrella: precios, dimensiones y auditoría")]:
        with st.expander(f"{path} — {title}", expanded=False):
            st.code(project.read_document(project.PROJECT_DIR / path), language="sql",
                    line_numbers=True, height=420)
    with st.expander("Configuración, pruebas y automatización", expanded=False):
        show_repository_files()


def show_idea_tab(mode):
    """Business definition, scope and acceptance criteria, read from the project brief."""
    brief = project.read_guide_table("Marco de negocio")
    for row in brief:
        st.markdown(build_info_card_html(row["Elemento"], row["Definición"],
            component=row["Forma"]), unsafe_allow_html=True)
    show_section_intro("Entregables", "Resultados verificables del proyecto.", True)
    st.markdown(build_place_link(PAGE_HOME, "Dashboard:") + " · "
                + build_place_link(PAGE_QUERIES, "Resultados:") + " · "
                + build_place_link(PAGE_CODE, "Implementación:") + " · "
                + build_place_link(PAGE_RUNS, "Operación:"), unsafe_allow_html=True)
    for show_part in [show_questions, show_audience, show_sources, show_limits, show_why]:
        show_part(mode)


def show_glossary_tab(mode):
    """Terminology as a document, grouped by functional area."""
    rows = project.read_guide_table("Glosario")
    for theme in dict.fromkeys(row["Tema"] for row in rows):
        st.subheader(theme)
        for row in [row for row in rows if row["Tema"] == theme]:
            st.markdown(f"**{row['Sigla o término']}.** {row['Significado']} "
                        f"— Uso: {row['Dónde aparece']}.")


@st.cache_data
def read_cached_week_gaps(database_version, week):
    """Matched wholesale and consumer prices of one week, largest gap first."""
    sql = ("SELECT * FROM (" + queries.read_query_body("k1_margin") + ") "
           "WHERE week_start = ? ORDER BY margin DESC")
    return add_display_columns(queries.run_sql(sql, parameters=(week,)))


def read_cached_latest_gaps(database_version):
    """Latest-week matched prices, largest gap first."""
    return read_cached_week_gaps(database_version, f"{read_latest_week():%Y-%m-%d}")


def rank_weekly_movements(rows, count, direction="Mayores movimientos"):
    """Rank only finite changes; each label retains channel and measurement unit."""
    rows = rows.dropna(subset=["variation"]).copy()
    rows = rows[rows["variation"].abs() != float("inf")]
    if direction == "Alzas":
        rows = rows[rows["variation"] > 0].sort_values("variation", ascending=False)
    elif direction == "Bajas":
        rows = rows[rows["variation"] < 0].sort_values("variation")
    else:
        rows = rows.loc[rows["variation"].abs().sort_values(ascending=False).index]
    return rows.head(count)


def build_short_labels(rows, describe):
    """A short name per row (product and channel); rows with the same short name get an
    invisible mark, so each one keeps its own bar."""
    labels, seen = [], {}
    for row in rows.to_dict("records"):
        label = describe(row)
        seen[label] = seen.get(label, 0) + 1
        labels.append(label + "\u200b" * (seen[label] - 1))
    return labels


def describe_price_row(row):
    """Detail of one weekly price for a tooltip: variety, quality, unit and price."""
    parts = [part for part in (row.get("variety"), row.get("quality"))
             if part and part != UNSPECIFIED]
    region = f" · {charts.shorten_region_name(row['region'])}" if row.get("region") else ""
    price = (f" · $ {charts.format_thousands(row['national_price'])}/{row['normalized_unit']}"
             if "national_price" in row else "")
    return f"{row['product']} {' · '.join(parts)} · {row['channel']}{region}{price}".strip()


def build_mobile_ranking_html(rows, mode, is_variation=False):
    """Readable bars on phones: full label above, value beside it, no clipped axis."""
    palette = charts.get_palette(mode)
    maximum = max(rows["value"].abs().max(), 1e-9)
    has_negative = (rows["value"] < 0).any()
    items = []
    for row in rows.to_dict("records"):
        value = row["value"]
        label = row.get("value_label", charts.format_signed_percent(value))
        color = (palette["rise"] if value > 0 else palette["fall"]) if is_variation else palette["accent"]
        width = abs(value) / maximum * (50 if has_negative else 100)
        left = (50 - width if value < 0 else 50) if has_negative else 0
        items.append(f'<li><div class="mobile-ranking-label"><span>{html.escape(row["label"])}</span>'
                     f'<strong>{html.escape(label)}</strong></div>'
                     f'<div class="mobile-ranking-track"><span style="left:{left:.3f}%;'
                     f'width:{width:.3f}%;background:{color}"></span>'
                     + ('<i aria-hidden="true"></i>' if has_negative else '') + '</div></li>')
    return '<ol class="mobile-rankings" aria-label="Ranking de precios">' + ''.join(items) + '</ol>'


def show_ranking_chart(rows, mode, key, is_variation=False):
    """The same ranked values in an interactive desktop chart and readable phone bars."""
    with st.container(key=f"{key}_ranking_desktop"):
        chart = (charts.draw_variation_bars(rows, mode, keep_rank_order=True) if is_variation
                 else charts.draw_horizontal_bars(rows, "Brecha de precio (%)", mode))
        if st.session_state.get(COMPACT_VIEW):
            # Each bar already writes its value: the axis numbers only crowd a narrow tile.
            chart = chart.properties(height=alt.Step(BAR_STEP)).configure_axisX(
                labels=False, ticks=False, title=None)
        show_chart(chart)
    st.markdown(build_mobile_ranking_html(rows, mode, is_variation), unsafe_allow_html=True)


@st.cache_data
def read_cached_week_snapshot(database_version, week):
    """The regional index (K3) of one week of valid observations."""
    sql = ("SELECT * FROM (" + queries.read_query_body("k3_regional_index") + ") "
           "WHERE week_start = ?")
    return add_display_columns(queries.run_sql(sql, parameters=(week,)))


def read_cached_market_snapshot(database_version):
    """The regional index (K3) of the latest week."""
    return read_cached_week_snapshot(database_version, f"{read_latest_week():%Y-%m-%d}")


def choose_market_product(snapshot, prefix):
    """The product of the trend and the territory: the one with most observations first."""
    if snapshot.empty:
        return None
    coverage = snapshot.groupby(queries.KEY_COLUMNS).size().reset_index(name="row_count")
    coverage = coverage.sort_values(["row_count"] + queries.KEY_COLUMNS,
                                    ascending=[False] + [True] * len(queries.KEY_COLUMNS))
    keys = [tuple(row[column] for column in queries.KEY_COLUMNS)
            for row in coverage.to_dict("records")]
    selected = st.selectbox(
        "Producto del pulso y del territorio", keys, key=f"{prefix}_visual_product",
        label_visibility="collapsed",
        format_func=lambda values: describe_product(dict(zip(queries.KEY_COLUMNS, values)))
                                  + f" · $/{values[-1]}",
        help="Se muestra primero la combinación con más observaciones de esta semana. La "
             "comparación conserva producto, variedad, calidad y unidad.")
    return dict(zip(queries.KEY_COLUMNS, selected))


def show_market_visuals(mode, prefix, latest_week, snapshot, key, trend_column, share_column):
    """Price pulse and weekly composition in the first report row."""
    if key is None:
        st.info("No hay observaciones válidas en la última semana para el panorama.")
        return
    history = read_indicator_for_key("k6_national_weekly_price", key)
    history = history[history["week_start"].between(latest_week - pd.Timedelta(weeks=11),
                                                    latest_week)]
    revision = "|".join(str(value) for value in key.values())
    config = {"displaylogo": False, "scrollZoom": False, "responsive": True}
    with trend_column, open_card(f"{prefix}_price_trend", "Pulso de precios · 12 semanas",
        hint="Cada curva es un canal para el producto elegido arriba. El precio nacional es "
             "el promedio simple de las regiones con dato. Las semanas sin dato quedan "
             "interrumpidas; pulsa una leyenda para ocultar o mostrar un canal."):
        channels = sorted(history["channel"].unique())
        chosen = st.multiselect("Canales", channels, key=f"{prefix}_pulse_channels",
                                default=[channel for channel in PULSE_CHANNELS
                                         if channel in channels] or channels[:3],
                                max_selections=3, label_visibility="collapsed",
                                help="Hasta tres canales a la vez, para que las líneas se lean.")
        history = history[history["channel"].isin(chosen)]
        figure = market_charts.draw_price_trend(history, mode, revision)
        # The legend in rows above the plot, so the lines keep the height of the tile.
        figure.update_layout(height=TILE_HEIGHT, margin=dict(l=8, r=8, t=8, b=8),
                             legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0,
                                         entrywidth=.33, entrywidthmode="fraction",
                                         font=dict(size=10)))
        st.plotly_chart(figure, theme=None,
                        use_container_width=True, config=config, key=f"{prefix}_trend_plot")
    with share_column, open_card(f"{prefix}_group_changes", "¿Qué grupo subió más?",
        hint="El cambio típico (la mediana) de los precios de cada grupo de alimentos frente "
             "a la semana anterior. ▲ en rojo: subió; ▼ en azul: bajó."):
        changes = read_cached_group_changes(get_database_version())
        bars = pd.DataFrame({"label": changes.index, "value": changes.to_numpy()})
        chart = charts.draw_variation_bars(bars, mode)
        if st.session_state.get(COMPACT_VIEW):
            chart = chart.properties(height=alt.Step(BAR_STEP + 4)).configure_axisX(
                labels=False, ticks=False, title=None)
        show_chart(chart)


def keep_covered_cells(points):
    """Channels and regions with data in at least half of the other axis: the map never
    shows rows or columns that are almost all «Sin dato»."""
    for axis, other in [("channel", "region"), ("region", "channel")]:
        coverage = points.groupby(axis)[other].nunique() / max(points[other].nunique(), 1)
        points = points[points[axis].isin(coverage[coverage >= MINIMUM_MAP_COVERAGE].index)]
    return points


def show_market_territory(mode, prefix, snapshot, key):
    """Readable regional matrix for the report; 3D remains an advanced view only."""
    if key is None:
        return
    points = keep_covered_cells(
        snapshot.loc[(snapshot[queries.KEY_COLUMNS] == pd.Series(key)).all(axis=1)])
    revision = "|".join(str(value) for value in key.values())
    with open_card(f"{prefix}_regional_map", "Territorio · precio relativo por región y canal",
        hint="Cada celda compara una región con el promedio nacional del mismo canal, producto "
             "y unidad. 100 es el promedio; 120 significa 20 % más caro. El color y el número "
             "permiten leerlo sin girar una figura.", kpi="K3"):
        figure = market_charts.draw_regional_heatmap(points, mode, revision)
        figure.update_layout(height=TILE_HEIGHT, margin=dict(l=8, r=8, t=8, b=8))
        st.plotly_chart(figure, theme=None, use_container_width=True,
                        config={"displaylogo": False, "responsive": True},
                        key=f"{prefix}_territory_plot")


def build_mini_bars(values, color):
    """Small accessible bars for a KPI; their heights come from the supplied data."""
    values = [float(value) for value in values if pd.notna(value)]
    if not values:
        values = [0]
    maximum = max(values) or 1
    width = 100 / len(values)
    bars = "".join(
        f'<rect x="{index * width + width * .18:.2f}" y="{27 - value / maximum * 22:.2f}" '
        f'width="{width * .64:.2f}" height="{max(value / maximum * 22, 1):.2f}" rx="1.5"/>'
        for index, value in enumerate(values))
    return (f'<svg class="metric-mini-chart" viewBox="0 0 100 30" role="img" '
            f'aria-label="Distribución relativa"><g fill="{color}">{bars}</g></svg>')


def build_overview_figures_html(latest_week, variations, week_alerts, snapshot, mode):
    """Four useful and clickable figures, each with context from the real data."""
    total = read_indicator("quality_flag_counts")["weekly_prices"].sum()
    palette = charts.get_palette(mode)
    group_counts = snapshot.groupby("product_group").size().sort_values(ascending=False)
    variation_counts = variations.groupby("channel").size().sort_values(ascending=False)
    alert_rate = len(week_alerts) / max(len(variations), 1) * 100
    values = [
        ("Observaciones históricas", charts.format_thousands(total), "database",
         "Base disponible para explorar", group_counts.tolist(), PAGE_DATA_AND_CODE),
        ("Semana observada", f"{latest_week:%d-%m-%Y}", "document",
         "Última semana consolidada", [1, 1, 1, 1], PAGE_SEASONALITY),
        ("Series con variación", charts.format_thousands(len(variations)), "chart",
         "Comparadas con la semana anterior", variation_counts.tolist(), PAGE_ANALYSIS),
        ("Alertas semanales", str(len(week_alerts)), "alert",
         f"{charts.format_percent(alert_rate)} de las series", [100 - alert_rate, alert_rate], PAGE_ALERTS),
    ]
    cells = "".join(
        f'<a class="overview-metric" href="{html.escape(build_page_address(page))}" target="_self" '
        f'aria-label="Abrir {html.escape(label)}"><div class="market-metric-heading">'
        f'{build_component_symbol(kind)}<span class="kpi-label">{html.escape(label)}</span>'
        f'<span class="metric-arrow" aria-hidden="true">→</span></div>'
        f'<div class="metric-value-row"><div><div class="kpi-value">{html.escape(value)}</div>'
        f'<div class="market-metric-note">{html.escape(note)}</div></div>'
        f'{build_mini_bars(points, palette["accent"])}</div></a>'
        for label, value, kind, note, points, page in values)
    return f'<div class="overview-metrics">{cells}</div>'


def choose_ranking(prefix, count_column, direction_column):
    """Top N and order of the ranking, in one compact row."""
    count = count_column.selectbox("Top N", [5, 8, 10, 15], index=1, key=f"{prefix}_top_n",
                                   label_visibility="collapsed",
                                   format_func=lambda value: f"Top {value}",
                                   help="Cuántos productos muestra cada ranking.")
    direction = direction_column.segmented_control(
        "Orden del ranking", ["Mayores movimientos", "Alzas", "Bajas"],
        default="Mayores movimientos", key=f"{prefix}_ranking_direction",
        label_visibility="collapsed") or "Mayores movimientos"
    return count, direction


def format_ranking_table(ranked):
    """The ranking as a readable table: Spanish columns, pesos, percent and the date."""
    detail = pd.DataFrame({
        "Grupo": ranked["product_group"], "Producto": ranked["product"],
        "Variedad": ranked["variety"], "Calidad": ranked["quality"], "Canal": ranked["channel"],
        "Unidad": ranked["normalized_unit"],
        "Semana": pd.to_datetime(ranked["week_start"]).dt.strftime("%d-%m-%Y"),
        "Precio nacional": ["$ " + charts.format_thousands(value)
                            for value in ranked["national_price"]],
        "Variación": [charts.format_signed_percent(value * 100)
                      for value in ranked["variation"]]})
    return detail


# region Report filters and cross filtering (D-069)
def read_filter(name):
    """The value of a report filter, kept across views and windows."""
    return st.session_state.get(f"dashboard_{name}", ALL_VALUES)


def set_filter(name, value):
    """Set a report filter (used by callbacks and clicks). The bar copies it into its
    field before drawing it: a field already drawn cannot be written."""
    st.session_state[f"dashboard_{name}"] = value
    if name in ("group", "week"):
        # A new category or week starts a new search: the product goes away.
        st.session_state.pop("dashboard_product", None)
    reset_chart_selections()


def keep_filter_from_field(name):
    """The bar's field changed: keep its value as the report filter."""
    set_filter(name, st.session_state[f"dashboard_{name}_field"])


def reset_chart_selections():
    """New chart keys, so a cleared selection can be chosen again."""
    st.session_state["dashboard_round"] = st.session_state.get("dashboard_round", 0) + 1


def read_product_filter():
    """The product chosen by a click: its key, its channel and its name, or None."""
    return st.session_state.get("dashboard_product")


def clear_product_filter():
    st.session_state.pop("dashboard_product", None)
    reset_chart_selections()


@st.cache_data
def read_cached_filter_options(database_version):
    """Categories, regions and the last weeks with prices, for the report's bar."""
    variations = read_cached_all_variations(database_version)
    weeks = sorted(variations["week_start"].unique(), reverse=True)[:DASHBOARD_WEEKS]
    snapshot = read_cached_market_snapshot(database_version)
    return {"group": [ALL_VALUES] + sorted(variations["product_group"].unique()),
            "region": [ALL_VALUES] + sorted(snapshot["region"].unique()),
            "week": [f"{pd.Timestamp(week):%Y-%m-%d}" for week in weeks]}


def format_filter_value(name, value):
    """What a field of the bar shows: the week as a Chilean date, «Todos» for no group."""
    if name == "week":
        return f"{pd.Timestamp(value):%d-%m-%Y}"
    if name == "group" and value == ALL_VALUES:
        return "Todos"
    return str(value)


def open_bar_field(name, label):
    """One field of the bar: its name written at its left, both on one line."""
    field = st.container(key=f"bar_{name}", horizontal=True, vertical_alignment="center",
                         gap="small")
    field.markdown(f'<span class="bar-label">{html.escape(label)}</span>',
                   unsafe_allow_html=True)
    return field


def show_global_field(name, label, options):
    """A filter that holds for every Dashboard view: group, region or week."""
    st.session_state[f"dashboard_{name}_field"] = read_filter(name)
    with open_bar_field(name, label):
        st.selectbox(label, options, key=f"dashboard_{name}_field",
                     on_change=keep_filter_from_field, args=(name,),
                     label_visibility="collapsed",
                     format_func=lambda value, name=name: format_filter_value(name, value))


def keep_product_from_field(choices):
    """The product field changed: it filters the summary like a click on a bar."""
    chosen = st.session_state.get("dashboard_product_field")
    if chosen in choices:
        row = choices[chosen]
        st.session_state["dashboard_product"] = {
            "key": {column: row[column] for column in queries.KEY_COLUMNS}, "channel": None,
            "name": " ".join(part for part in (row["product"], row["variety"])
                             if part != UNSPECIFIED)}
    else:
        st.session_state.pop("dashboard_product", None)
    reset_chart_selections()


def show_product_field(week, group):
    """Producto: every key with a price in the chosen week and group (D-072)."""
    rows = read_week_variations(week, None if group == ALL_VALUES else group)
    rows = rows.drop_duplicates(queries.KEY_COLUMNS).sort_values(["product", "variety"])
    choices = {f"{describe_product(row)} · {row['normalized_unit']}": row
               for row in rows.to_dict("records")}
    product = read_product_filter()
    current = next((label for label, row in choices.items() if product and all(
        row[column] == product["key"][column] for column in queries.KEY_COLUMNS)), "Todos")
    if product and current == "Todos":
        # Chained filters: a product outside the chosen group or week is let go, so the
        # field and the charts never disagree (D-072).
        clear_product_filter()
    st.session_state["dashboard_product_field"] = current
    with open_bar_field("product", "Producto"):
        st.selectbox("Producto", ["Todos"] + list(choices), key="dashboard_product_field",
                     on_change=keep_product_from_field, args=(choices,),
                     label_visibility="collapsed")


def show_top_n_field():
    """Top N: a slider, its value always written next to it (D-072)."""
    st.session_state.setdefault("dashboard_top_n", DEFAULT_TOP_N)
    st.session_state["dashboard_top_n"] = max(TOP_N_RANGE[0], min(TOP_N_RANGE[1], st.session_state["dashboard_top_n"]))
    with open_bar_field("top_n", "Top N"):
        st.slider("Top N", *TOP_N_RANGE, key="dashboard_top_n", step=1,
                  label_visibility="collapsed",
                  help="Cuántos productos muestra el ranking.")
    return st.session_state["dashboard_top_n"]


def show_order_field():
    """Which changes the ranking shows: both directions, only rises or only falls."""
    with st.container(key="ranking_order", width=130):
        st.selectbox(
            "Orden del ranking", list(RANKING_TITLES), key="dashboard_ranking_direction",
            label_visibility="collapsed",
            format_func=lambda value: {"Mayores movimientos": "▲▼ Ambos", "Alzas": "▲ Alzas",
                                       "Bajas": "▼ Bajas"}[value])


def show_report_filters(with_summary_fields=False, include_product=True, include_region=True):
    """One bar for the whole report: group, region and week, kept across its views
    (D-069). The summary adds the product and Top N (D-072). Returns Top N."""
    options = read_cached_filter_options(get_database_version())
    if read_filter("week") not in options["week"]:
        st.session_state["dashboard_week"] = options["week"][0]
    week = read_filter("week")
    count = None
    with st.container(key="report_filters", horizontal=True, vertical_alignment="center"):
        show_global_field("group", GLOBAL_FILTERS["group"], options["group"])
        if with_summary_fields and include_product:
            show_product_field(week, read_filter("group"))
        if include_region:
            show_global_field("region", GLOBAL_FILTERS["region"], options["region"])
        show_global_field("week", GLOBAL_FILTERS["week"], options["week"])
        if with_summary_fields:
            count = show_top_n_field()
    return count


def show_breadcrumb_and_chips():
    """«Todas › Frutas › Manzana» to go back up, and a chip per active filter to remove it."""
    group, product = read_filter("group"), read_product_filter()
    with st.container(key="report_breadcrumb", horizontal=True, vertical_alignment="center"):
        st.button("Todas las categorías" if group == ALL_VALUES else "Todas", key="crumb_all", type="tertiary", on_click=set_filter,
                  args=("group", ALL_VALUES), disabled=group == ALL_VALUES and not product)
        if group != ALL_VALUES:
            st.markdown('<span class="crumb-separator">›</span>', unsafe_allow_html=True)
            st.button(group, key="crumb_group", type="tertiary", on_click=clear_product_filter,
                      disabled=not product)
        if product:
            st.markdown('<span class="crumb-separator">›</span>', unsafe_allow_html=True)
            st.button(f"Filtro: {product['name']} ✕", key="chip_product",
                      on_click=clear_product_filter, help="Quitar el filtro de producto")
        if read_filter("region") != ALL_VALUES:
            st.button(f"Región: {charts.shorten_region_name(read_filter('region'))} ✕",
                      key="chip_region", on_click=set_filter, args=("region", ALL_VALUES),
                      help="Quitar el filtro de región")


def read_picked(event):
    """The value clicked in an Altair chart, or None."""
    picked = (event or {}).get("selection", {}).get("pick") or []
    return picked[0] if picked else None


def apply_click(chart_key, picked, apply):
    """Apply a click once: the chart keeps its selection after the rerun."""
    signature = f"{chart_key}:{picked}"
    if picked and st.session_state.get("dashboard_last_click") != signature:
        st.session_state["dashboard_last_click"] = signature
        apply(picked)
        st.rerun()


def show_clickable_chart(chart, key):
    """An Altair chart whose clicks come back to the page."""
    round_number = st.session_state.get("dashboard_round", 0)
    return st.altair_chart(chart, use_container_width=True, theme=None, on_select="rerun",
                           key=f"{key}_{round_number}")
# endregion


def show_excluded_gaps(excluded):
    """The gaps left out of the ranking, with what each one compares (D-068)."""
    if excluded.empty:
        return
    # Fact and hypothesis kept apart (C05): the format mismatch is not checked row by row.
    with st.expander(f"Brechas sobre +300 % fuera del ranking: {len(excluded)}",
                     expanded=False):
        st.caption("Criterio: una brecha sobre +300 % sale del ranking y de la mediana; la "
                   "fila se conserva en la base y en «Brecha de precio». Hecho medido: en la "
                   "feria libre, que vende a granel como el mayorista, el 99 % de las brechas "
                   "queda bajo +253 %. Hipótesis, revisada en algunos casos (frutilla, "
                   "naranja): el precio al consumidor corresponde a un formato envasado y el "
                   "mayorista a uno a granel; no está verificado fila por fila.")
        st.dataframe(pd.DataFrame({
            "Producto": [describe_product(row) for row in excluded.to_dict("records")],
            "Canal": excluded["channel"], "Región": excluded["region"],
            "Unidad": excluded["normalized_unit"],
            "Mayorista": ["$ " + charts.format_thousands(value)
                          for value in excluded["wholesale_price"]],
            "Consumidor": ["$ " + charts.format_thousands(value)
                           for value in excluded["consumer_price"]],
            "Brecha": [charts.format_percent(value * 100, 0) for value in excluded["margin"]]}),
            hide_index=True, use_container_width=True)


def describe_variation_detail(row):
    """Tooltip of a weekly change: product, channel, unit, price, change and week."""
    return (f"{describe_price_row(row)} · {charts.format_signed_percent(row['variation'] * 100)}"
            f" frente a la semana anterior · semana del {row['week_start']:%d-%m-%Y}")


def describe_gap_detail(row):
    """Tooltip of a gap: product, channel, region, both prices, unit and week."""
    return (f"{describe_product(row)} · {row['channel']} · "
            f"{charts.shorten_region_name(row['region'])} · mayorista $ "
            f"{charts.format_thousands(row['wholesale_price'])} y consumidor $ "
            f"{charts.format_thousands(row['consumer_price'])} por {row['normalized_unit']}"
            f" · semana del {pd.Timestamp(row['week_start']):%d-%m-%Y}")


def build_product_filter(row):
    """The product filter of one clicked row: its key, its channel and a short name."""
    parts = [part for part in (row["variety"],) if part and part != UNSPECIFIED]
    return {"key": {column: row[column] for column in queries.KEY_COLUMNS},
            "channel": row["channel"], "name": " ".join([row["product"]] + parts)}


def select_ranked_product(row, detail=False):
    """A ranking click updates only its lower detail, never the overview's population."""
    st.session_state["dashboard_product"] = build_product_filter(row)
    if detail:
        key = {column: row[column] for column in queries.KEY_COLUMNS}
        options = read_key_options("k3_regional_index")
        for column, value in key.items():
            options = options[options[column] == value]
        st.session_state["analysis_group"] = key["product_group"]
        st.session_state["analysis_product"] = key["product"]
        if not options.empty:
            st.session_state["analysis_key_label"] = options.iloc[0]["key_label"]
        st.session_state["analysis_channels"] = [row["channel"]]
        if "region" in row:
            st.session_state["analysis_region"] = row["region"]


def keep_product(rows, product):
    """The rows of the chosen product key (all rows when none is chosen)."""
    if not product:
        return rows
    for column, value in product["key"].items():
        rows = rows[rows[column] == value]
    return rows


def choose_default_key(ranked, week):
    """The product of the pulse and the map before any click: the first of the ranking
    with a price in two regions or more, so the map has something to compare."""
    if ranked.empty:
        return None
    snapshot = read_cached_week_snapshot(get_database_version(), week)
    regions = snapshot.groupby(queries.KEY_COLUMNS)["region"].nunique()
    for row in ranked.to_dict("records"):
        key = tuple(row[column] for column in queries.KEY_COLUMNS)
        if regions.get(key, 0) >= 2:
            return {column: row[column] for column in queries.KEY_COLUMNS}
    return {column: ranked.iloc[0][column] for column in queries.KEY_COLUMNS}


def describe_ranking_change(row):
    movement = "subió" if row["variation"] > 0 else "bajó" if row["variation"] < 0 else "no cambió"
    amount = " " + charts.format_percent(abs(row["variation"]) * 100) if row["variation"] else ""
    return (f"En este ranking, {row['product']} en {row['channel']} {movement}{amount} "
            "frente a la semana anterior. Las barras más largas muestran cambios mayores.")


def describe_regional_comparison(row):
    difference = (row["regional_index"] - 1) * 100
    region = charts.shorten_region_name(row["region"])
    if abs(difference) < .05:
        return f"{region} tiene un precio igual al promedio nacional de {row['channel']}."
    position = "por encima" if difference > 0 else "por debajo"
    return (f"{region} está {charts.format_percent(abs(difference))} {position} del promedio "
            f"nacional de {row['channel']}. Se compara el mismo producto y la misma unidad.")


def show_foldable_table(table_html, label="Ver tabla de detalle"):
    with st.expander(label, expanded=False):
        st.markdown(table_html, unsafe_allow_html=True)


def show_movements_card(prefix, ranked, count, mode, direction=None):
    """Card: the largest weekly changes; a click on a bar filters by its product."""
    direction = direction or st.session_state.get("dashboard_ranking_direction") or "Mayores movimientos"
    with open_card(f"{prefix}_movements", RANKING_TITLES[direction],
        hint="Cada barra compara el precio de un producto con la semana anterior. "
             "▲ en rojo subió; ▼ en azul bajó. Las barras más largas muestran cambios mayores. "
             + (describe_ranking_change(ranked.iloc[0]) if not ranked.empty else "No hay datos para esta selección.")
             + " Haz clic en una barra para ver ese producto en los demás gráficos; doble clic para soltarla.",
        kpi="K6"):
        # The order sits on the subtitle's line: it belongs to this ranking only.
        with st.container(horizontal=True, vertical_alignment="center",
                          key=f"{prefix}_ranking_caption"):
            st.caption(f"Top {count} · frente a la semana anterior · precio nacional")
        if ranked.empty:
            st.info("No hay cambios disponibles para esta selección.")
            return
        bars = pd.DataFrame({
            "label": build_short_labels(ranked, lambda row: f"{row['product']} {row['variety'] if row['variety'] != UNSPECIFIED else ''} · {row['quality']} · {row['channel']}"),
            "value": ranked["variation"].to_numpy() * 100,
            "detail": [describe_variation_detail(row) for row in ranked.to_dict("records")],
            "pick": [str(position) for position in range(len(ranked))]})
        chart = charts.draw_variation_bars(bars, mode, keep_rank_order=True, select_field="pick").configure_axisY(
            labelExpr="split(datum.label, ' · ')", labelLineHeight=12, labelLimit=185)
        event = show_clickable_chart(compact_bar_chart(chart, step=44), f"{prefix}_movements_chart")
        apply_click(f"{prefix}_movements", read_picked(event), lambda picked: select_ranked_product(ranked.iloc[int(picked["pick"])], detail=prefix.startswith("week_top")))
        st.markdown(build_mobile_ranking_html(bars, mode, True), unsafe_allow_html=True)
        sample = format_ranking_table(ranked).copy()
        sample["Producto"] = [describe_product(row) for row in ranked.to_dict("records")]
        sample["Precio anterior"] = ["$ " + charts.format_thousands(row['national_price']/(1+row['variation'])) for row in ranked.to_dict('records')]
        show_data_sample(sample[["Producto", "Canal", "Precio anterior", "Precio nacional", "Unidad", "Variación"]])


def show_gaps_card(prefix, gaps, count, mode):
    """Card: the largest comparable gaps; a click on a bar filters by its product."""
    with open_card(f"{prefix}_gaps", "¿Dónde es mayor la brecha esta semana?",
        caption=f"Top {count} · precio al consumidor sobre el mayorista · mismo producto, "
                "unidad, región y semana",
        hint="Cuánto más paga el consumidor que el mayorista por el mismo producto, unidad, "
             "región y semana. Solo pares comparables: las brechas sobre +300 % se listan "
             "aparte, porque probablemente comparan formatos distintos (granel y envasado). "
             "La brecha no mide ganancias ni descuenta costos. Clic en una barra para filtrar.",
        kpi="K1"):
        if gaps.empty:
            st.info("No hay pares comparables para esta selección.")
            return
        describe = lambda row: f"{describe_product(row).replace(chr(183), chr(47))} · {row['channel']} · {charts.shorten_region_name(row['region'])}"
        bars = pd.DataFrame({
            "label": build_short_labels(gaps, describe),
            "value": gaps["margin"].to_numpy() * 100,
            "detail": [describe_gap_detail(row) for row in gaps.to_dict("records")],
            "pick": [str(position) for position in range(len(gaps))]})
        bars["value_label"] = bars["value"].map(charts.format_percent)
        chart = charts.draw_horizontal_bars(bars, "Diferencia sobre el mayorista (%)", mode, select_field="pick",
                                            is_sorted_by_value=False).configure_axisY(
                                                labelExpr="split(datum.label, ' · ')", labelLimit=245, labelLineHeight=12).properties(height=alt.Step(44))
        event = show_clickable_chart(compact_bar_chart(chart, step=44), f"{prefix}_gaps_chart")
        apply_click(f"{prefix}_gaps", read_picked(event), lambda picked: select_ranked_product(gaps.iloc[int(picked["pick"])], detail=prefix == "gap"))
        st.markdown(build_mobile_ranking_html(bars, mode), unsafe_allow_html=True)
        show_data_sample(pd.DataFrame({
            "Producto": [describe_product(row) for row in gaps.to_dict("records")],
            "Región / canal": [charts.shorten_region_name(row['region']) + " · " + row['channel'] for row in gaps.to_dict("records")],
            "Unidad": gaps["normalized_unit"],
            "Mayorista": gaps["wholesale_price"].map(lambda value: "$ " + charts.format_thousands(value)),
            "Consumidor": gaps["consumer_price"].map(lambda value: "$ " + charts.format_thousands(value)),
            "Diferencia": (gaps["margin"] * 100).map(charts.format_signed_percent)}))


def show_group_card(prefix, week, mode):
    """Card: the typical change of each group; a click goes down into that group."""
    with open_card(f"{prefix}_group_changes", "¿Qué grupo subió más?",
        caption="Cambio típico (mediana) de cada grupo frente a la semana anterior",
        hint="El cambio típico (la mediana) de los precios de cada grupo frente a la semana "
             "anterior. Haz clic en un grupo para ver solo sus productos."):
        changes = read_cached_group_changes(get_database_version(), week)
        bars = pd.DataFrame({"label": changes.index, "value": changes.to_numpy(),
                             "pick": changes.index})
        # Long group names shorten with «…» (whole in the tooltip): the bars keep room.
        chart = charts.draw_variation_bars(bars, mode, select_field="pick", label_limit=105)
        event = show_clickable_chart(compact_bar_chart(chart, BAR_STEP + 4),
                                     f"{prefix}_groups_chart")
        apply_click(f"{prefix}_groups", read_picked(event),
                    lambda picked: set_filter("group", picked["pick"]))


def compact_bar_chart(chart, step=None):
    """A ranking for a report tile: fixed band and no axis numbers (each bar has its value)."""
    if not st.session_state.get(COMPACT_VIEW):
        return chart
    # The axis title comes from the encoding, so it is hidden by size, not by name.
    # Room on the right, so the value after the longest bar is never cut.
    return chart.properties(height=alt.Step(step or BAR_STEP),
                            padding={"left": 0, "top": 0, "bottom": 0, "right": 30}).configure_axisX(
        labels=False, ticks=False, domain=False, titleFontSize=0, titlePadding=0)


def show_pulse_card(prefix, key, week, mode):
    """Card: the national price of the product, three channels at most, 12 weeks."""
    history = keep_product(read_cached_national_prices(get_database_version()), {"key": key})
    week = pd.Timestamp(week)
    history = history[history["week_start"].between(week - pd.Timedelta(weeks=11), week)]
    name = " ".join(part for part in (key["product"], key["variety"]) if part != UNSPECIFIED)
    unit = key["normalized_unit"]
    channels = sorted(history["channel"].unique())
    initial_channels = ([channel for channel in PULSE_CHANNELS if channel in channels] or channels)[:PULSE_MAXIMUM_CHANNELS]
    hint_channels = st.session_state.get(f"{prefix}_pulse_channels_{name}", initial_channels)
    current = history[(history["week_start"] == week) & history["channel"].isin(hint_channels)]
    prices = " · ".join(f"{row['channel']}: $ {charts.format_thousands(row['national_price'])}/{unit}"
                        for row in current.to_dict("records"))
    reading = ("Semana elegida: " + prices + ". " if prices else
               "No hay precio en la semana elegida para los canales seleccionados. ")
    with open_card(f"{prefix}_price_trend", "¿Cómo evolucionó el producto?",
        caption=f"{name} · $/{unit} · promedio nacional · últimas 12 semanas",
        hint=reading + "Cada línea muestra cómo cambió el precio de un canal durante las últimas 12 semanas. "
             "El precio nacional es el promedio simple de las regiones con dato. "
             "Un corte significa que falta un dato, no que el precio sea cero."):
        channels = sorted(history["channel"].unique())
        chosen = st.multiselect("Canales", channels, key=f"{prefix}_pulse_channels_{name}",
                                default=([channel for channel in PULSE_CHANNELS
                                          if channel in channels] or channels)[
                                    :PULSE_MAXIMUM_CHANNELS],
                                max_selections=PULSE_MAXIMUM_CHANNELS,
                                label_visibility="collapsed")
        figure = market_charts.draw_price_trend(history[history["channel"].isin(chosen)],
                                                mode, name)
        # The unit sits level over the axis, not as a vertical title to cut on a narrow
        # card; no fill under the lines, so a week without data reads as a cut (D-072).
        figure.update_yaxes(title=None)
        figure.update_traces(fill=None)
        figure.add_annotation(text=f"$/{unit}", xref="paper", yref="paper", x=0, y=1.0,
                              xanchor="left", yanchor="bottom", showarrow=False,
                              font=dict(size=11))
        figure.update_layout(height=TILE_HEIGHT - 80, margin=dict(l=8, r=8, t=24, b=8),
                             legend=dict(orientation="h", y=1.0, yanchor="bottom", x=1,
                                         xanchor="right", font=dict(size=10)))
        st.plotly_chart(figure, theme=None, use_container_width=True,
                        config={"displaylogo": False, "responsive": True},
                        key=f"{prefix}_trend_plot")


def regional_week_changes(current, previous):
    """Compare the same product, channel and region in two exact consecutive weeks."""
    keys = list(queries.KEY_COLUMNS) + ["region", "channel"]
    merged = current.merge(previous[keys + ["price"]].rename(columns={"price": "previous_price"}),
                           on=keys, how="left", validate="one_to_one")
    valid = merged["previous_price"].gt(0) & merged["price"].notna()
    merged["weekly_change"] = ((merged["price"] / merged["previous_price"] - 1) * 100).where(valid)
    return merged


def show_map_card(prefix, key, week, mode, compact=False):
    """Readable regional zones, colored by actual week-on-week price movement."""
    version = get_database_version()
    current = keep_covered_cells(keep_product(read_cached_week_snapshot(version, week), {"key": key}))
    previous_week = f"{pd.Timestamp(week) - pd.Timedelta(days=7):%Y-%m-%d}"
    previous = keep_covered_cells(keep_product(read_cached_week_snapshot(version, previous_week), {"key": key}))
    points = regional_week_changes(current, previous)
    short_name = " ".join(part for part in (key["product"], key["variety"]) if part != UNSPECIFIED)
    with open_card(f"{prefix}_regional_map", "¿Dónde subieron o bajaron?",
        caption=f"{short_name} · por {key['normalized_unit']} · semana del {pd.Timestamp(week):%d-%m-%Y}",
        hint="Cada zona representa una región. Compara el mismo producto y canal con la semana anterior. "
             "Rojo: subió; azul: bajó; gris: sin cambio. Las zonas vacías no tienen comparación disponible.", kpi="K6"):
        channels = sorted(points["channel"].unique())
        if not channels:
            st.info("No hay precios disponibles para esta selección.")
            return
        field_key = f"{prefix}_map_channel"
        if st.session_state.get(field_key) not in channels:
            st.session_state[field_key] = channels[0]
        channel = st.selectbox("Canal de comparación", channels, key=field_key)
        selected = points[points["channel"] == channel].copy()
        geometry = json.loads((Path(__file__).parent / "assets" / "chile-regions.geojson").read_text())
        comparable = int(selected["weekly_change"].notna().sum())
        with_price = int(selected["price"].notna().sum())
        st.caption(f"{with_price} de 16 regiones con precio actual · {comparable} con comparación semanal · {channel}")
        all_regions = pd.DataFrame({"region": [f["properties"]["region"] for f in sorted(geometry["features"], key=lambda f: -max(p[1] for poly in f["geometry"]["coordinates"] for ring in poly for p in ring))]})
        detail = all_regions.merge(selected[["region", "price", "previous_price", "weekly_change"]], on="region", how="left", validate="one_to_one")
        detail["Estado"] = detail.apply(lambda r: "Sin precio actual" if pd.isna(r["price"]) else "Sin precio anterior" if pd.isna(r["weekly_change"]) else "▲ Subió" if r["weekly_change"] > 0 else "▼ Bajó" if r["weekly_change"] < 0 else "= Sin cambio", axis=1)
        detail["Región"] = detail["region"].map(charts.shorten_region_name)
        for source, label in (("price", "Precio actual"), ("previous_price", "Precio anterior")):
            detail[label] = detail[source].map(lambda v: "—" if pd.isna(v) else "$ " + f"{v:,.0f}".replace(",", "."))
        detail["Variación"] = detail["weekly_change"].map(lambda v: "—" if pd.isna(v) else f"{v:+.1f} %".replace(".", ","))
        visible = detail[detail["price"].notna()]
        st.markdown(visible[["Región", "Precio actual", "Precio anterior", "Variación", "Estado"]].to_html(index=False, border=0, classes="regional-detail"), unsafe_allow_html=True)
        st.caption(f"Precios en pesos por {key['normalized_unit']}. Las otras {16-with_price} regiones no tienen precio actual para esta selección.")
        with st.expander("Ubicar estas regiones en el mapa de Chile", expanded=False):
            chart = charts.draw_regional_change_map(selected, geometry, mode, full_country=True)
            event = show_clickable_chart(chart, f"{prefix}_map_chart")
            apply_click(f"{prefix}_map", read_picked(event),
                        lambda picked: set_filter("region", picked.get("properties.region", picked.get("region")))
                        if picked.get("properties.region", picked.get("region")) in set(selected["region"]) else None)
            st.caption("Rojo ▲ Subió · Azul ▼ Bajó · Gris = Sin cambio · Sin relleno = Sin comparación")
            st.caption("Las 16 regiones de Chile. Un precio actual sin precio de la semana anterior no permite calcular una variación.")




def show_regional_overview(week, group, mode, prefix):
    """Compare within each series first, then summarize changes by region."""
    version = get_database_version()
    current = keep_covered_cells(read_cached_week_snapshot(version, week))
    previous = keep_covered_cells(read_cached_week_snapshot(version, f"{pd.Timestamp(week)-pd.Timedelta(days=7):%Y-%m-%d}"))
    if group != ALL_VALUES:
        current = current[current["product_group"] == group]
        previous = previous[previous["product_group"] == group]
    changes = regional_week_changes(current, previous)
    valid = changes.dropna(subset=["weekly_change"])
    with open_card(f"{prefix}_regional_overview", "¿Qué pasó en cada región?",
                   caption="Todos los productos del grupo · comparación con la semana anterior",
                   hint="Primero se compara cada producto, variedad, calidad, unidad y canal consigo mismo. Después se resume por región. La mediana es el cambio del centro: no es inflación ni una variación ponderada por ventas."):
        if valid.empty:
            st.info("No hay series regionales comparables esta semana.")
            return
        summary = valid.groupby("region").agg(series=("weekly_change", "size"), median=("weekly_change", "median"),
                    rises=("weekly_change", lambda v: (v > 0).sum()), falls=("weekly_change", lambda v: (v < 0).sum()),
                    stable=("weekly_change", lambda v: (v == 0).sum())).reset_index()
        summary = summary.sort_values("median", ascending=False)
        table = pd.DataFrame({"Región": summary["region"].map(charts.shorten_region_name),
             "Series": summary["series"], "▲ Suben": summary["rises"], "▼ Bajan": summary["falls"],
             "= Iguales": summary["stable"], "Cambio mediano": summary["median"].map(lambda v: f"{v:+.1f} %".replace(".", ","))})
        st.caption(f"{len(summary)} regiones con comparación · {len(valid):,} series comparables".replace(",", "."))
        st.markdown(table.to_html(index=False, border=0, classes="regional-detail"), unsafe_allow_html=True)
        st.caption("La base cargada contiene precios válidos de 9 de las 16 regiones de Chile; no representa cobertura nacional completa.")
        st.caption("Cada serie cuenta una vez. Se reúnen canales y productos distintos; no se suman ni promedian sus precios. Las regiones sin comparación quedan fuera del resumen.")


def show_regional_ranking(points):
    """Under the heat map (D-072): the dearest and the cheapest cell in words, and every
    cell as a ranking table with its price, so nothing needs a hover."""
    ranked = points.sort_values("regional_index", ascending=False)
    describe = (lambda row: f"{charts.shorten_region_name(row['region'])} · {row['channel']} "
                            f"({row['regional_index'] * 100:.0f})")
    top, bottom = ranked.iloc[0], ranked.iloc[-1]
    # The answer sits on the expander's own line: readable closed, the table when opened.
    with st.expander(f"Ver tabla · mayor índice: {describe(top)} · menor índice: {describe(bottom)}", expanded=False):
        st.dataframe(pd.DataFrame({
            "Región": ranked["region"].map(charts.shorten_region_name),
            "Canal": ranked["channel"],
            "Precio": ["$ " + charts.format_thousands(value) for value in ranked["price"]],
            "Unidad": ranked["normalized_unit"],
            "Índice": (ranked["regional_index"] * 100).round().astype(int)}),
            hide_index=True, use_container_width=True)


def describe_week_span(week):
    """«05–11 oct 2026»: the Monday and the Sunday of the analyzed week."""
    start = pd.Timestamp(week)
    end = start + pd.Timedelta(days=6)
    months = charts.MONTH_NAMES
    if start.month == end.month:
        return f"{start:%d}–{end:%d} {months[end.month - 1]} {end.year}"
    return f"{start:%d} {months[start.month - 1]} – {end:%d} {months[end.month - 1]} {end.year}"


def show_dashboard_title(week, ranked, prefix):
    """Title, the analyzed week apart from the date of the last load, and two actions:
    how to read the data (in the panel) and the ranking as CSV (D-072)."""
    latest_run = read_latest_run()
    is_loaded = latest_run["status"] == etl.STATUS_LOADED
    title_column, actions_column = st.columns([3, 1.25], vertical_alignment="bottom")
    with title_column:
        st.markdown(
            f'<div class="report-title"><h1>Los precios esta semana</h1><p>Semana analizada: '
            f'<strong>{describe_week_span(week)}</strong><span class="report-divider">│</span>'
            f'Última carga: {format_chile_time(parse_run_start(latest_run["started_at"]))} '
            f'{build_chip("Completada" if is_loaded else "Con falla", "ok" if is_loaded else "failed")}'
            '</p></div>', unsafe_allow_html=True)
    with actions_column, st.container(key="report_actions", horizontal=True,
                                      horizontal_alignment="right"):
        st.markdown(build_link_html("Definiciones y método →", build_page_address(PAGE_KPI)),
                    unsafe_allow_html=True)
        detail = format_ranking_table(ranked)
        st.download_button("Descargar CSV", detail.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"ranking-{week}.csv", mime="text/csv",
                           icon=":material/download:", key=f"{prefix}_download",
                           help="El ranking de la semana con su grupo, variedad, calidad, "
                                "canal, unidad, precio y variación.")


def read_report_gaps(week, group, region, product):
    """The week's gaps under the report's filters: (comparable, left out above +300 %)."""
    gaps = read_cached_week_gaps(get_database_version(), week)
    if group != ALL_VALUES:
        gaps = gaps[gaps["product_group"] == group]
    if region != ALL_VALUES:
        gaps = gaps[gaps["region"] == region]
    return split_comparable_gaps(keep_product(gaps, product))


def show_usable_data_card(mode):
    """Card: which weekly prices can be used. A whole with three parts, so a ring; its
    scope is the whole history and it does not change with the filters (D-072)."""
    totals = read_indicator("quality_flag_counts").groupby("flag")["weekly_prices"].sum()
    totals = totals.sort_values(ascending=False)
    with open_card("usable_data", "¿Qué datos podemos usar?",
                   caption="Histórico 2022–2026 · todos los datos",
                   hint="El resumen cuenta registros de precios, no ventas. Distingue partes "
                        "del total histórico: usados, atípicos o con unidad no convertible. "
                        "Cada registro corresponde a un producto, región, canal y semana. "
                        "Los excluidos se conservan con su motivo; no se borran."):
        used_count = int(totals.get("SIN_MARCA", 0))
        total = int(totals.sum())
        used = used_count / total * 100 if total else 0
        rejected = total - used_count
        palette = charts.get_palette(mode)
        st.markdown(f'<div class="quality-summary"><strong class="quality-value">{charts.format_percent(used)}</strong>'
                    f'<span>de los registros históricos se usan en los indicadores</span>'
                    f'<div class="quality-meter" role="meter" aria-label="Registros utilizables" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{used}">'
                    f'<span style="width:{used}%;background:{palette["accent"]}"></span></div>'
                    f'<div class="quality-counts"><strong>{charts.format_thousands(used_count)}</strong> usados de {charts.format_thousands(total)} registros</div>'
                    f'<div class="quality-counts">{charts.format_thousands(rejected)} excluidos: '
                    f'{charts.format_thousands(int(totals.get(etl.FLAG_OUTLIER, 0)))} atípicos y '
                    f'{charts.format_thousands(int(totals.get(etl.FLAG_UNIT_NOT_CONVERTIBLE, 0)))} con unidad no convertible.</div>'
                    f'{build_link_html("Revisar calidad de datos →", build_page_address(PAGE_OPERATIONS))}</div>', unsafe_allow_html=True)


def show_week_gap_ranking(mode):
    """Moved from the summary (D-072): the week's largest comparable gaps under the
    report's filters, and the ones left out, listed with their prices."""
    count = st.session_state.get("dashboard_top_n", DEFAULT_TOP_N)
    comparable, excluded = read_report_gaps(read_report_week(), read_filter("group"),
                                            read_filter("region"), None)
    show_gaps_card("gap", comparable.head(count), count, mode)
    show_excluded_gaps(excluded)


def build_movement_proportions(rows):
    """Mutually exclusive parts of all comparable national series, not just Top N."""
    values = rows["variation"].dropna()
    counts = [int(values.gt(0).sum()), int(values.lt(0).sum()), int(values.eq(0).sum())]
    total = sum(counts)
    return pd.DataFrame({"label": ["Subieron", "Bajaron", "Sin cambio"], "value": counts,
                         "share": [count / total * 100 if total else 0 for count in counts]})


def show_movement_proportions(rows, week, group, mode):
    palette = charts.get_palette(mode)
    parts = build_movement_proportions(rows)
    total = int(parts["value"].sum())
    current = read_cached_national_prices(get_database_version())
    current = current[current["week_start"] == pd.Timestamp(week)]
    if group != ALL_VALUES:
        current = current[current["product_group"] == group]
    missing = max(0, len(current) - total)
    with open_card("movement_proportions", "¿Qué proporción subió o bajó?",
                   caption="Todas las series nacionales comparables del grupo · no solo el Top N",
                   hint="Cada porción cuenta series de un producto, variedad, calidad, unidad y canal. "
                        "Rojo: subieron; azul: bajaron; gris: precio igual a la semana anterior. "
                        "Cada serie cuenta una vez, sin ponderar por ventas. No son cuotas de mercado ni gasto."):
        if not total:
            st.info("No hay series con comparación frente a la semana anterior.")
            return
        colors = [palette["rise"], palette["fall"], palette["reference"]]
        parts["value_label"] = [f"{count} series · {charts.format_percent(share)}" for count, share in zip(parts["value"], parts["share"])]
        ring, explanation = st.columns([1, 1.3], vertical_alignment="center")
        with ring:
            show_chart(charts.draw_donut(parts, colors, mode, center=str(total), center_note="series", size=175))
        with explanation:
            for item, color in zip(parts.to_dict("records"), colors):
                st.markdown(f'<div style="margin:8px 0"><span style="color:{color}">●</span> '
                            f'{item["label"]} <strong>{charts.format_percent(item["share"])}</strong>'
                            f' · {item["value"]} series</div>', unsafe_allow_html=True)
        st.caption(f"Cada serie es un producto y canal. {missing} series con precio esta semana no tienen comparación y quedan fuera del anillo. No representa ventas.")


def apply_home_focus(options):
    """Apply only validated deep-link selections, once; never override live widgets."""
    token = st.query_params.get("_home_key")
    marker = repr({k:v for k,v in st.query_params.to_dict().items() if k.startswith('_home_')})
    requested = any(st.query_params.get('_home_' + name) for name in ('group', 'region', 'week'))
    if (not token and not requested) or marker == st.session_state.get('mock_focus_seen'):
        return
    st.session_state['mock_focus_seen'] = marker
    for name in ('group','region','week'):
        value=st.query_params.get('_home_'+name)
        if value in options[name] or value == ALL_VALUES:
            st.session_state['dashboard_'+name]=value
    count = st.query_params.get('_home_count', '')
    if count.isdigit() and TOP_N_RANGE[0] <= int(count) <= 10_000:
        st.session_state['dashboard_top_n'] = int(count)
    order = st.query_params.get('_home_order')
    if order in home_mockup.ORDERS:
        st.session_state['home_order'] = order
    if token:
        try:
            payload=json.loads(base64.urlsafe_b64decode(token.encode()).decode())
            if set(payload) == set(queries.KEY_COLUMNS+['channel']) and all(isinstance(v,str) for v in payload.values()):
                st.session_state['mock_focus_key']=payload
        except (ValueError,TypeError,UnicodeError):
            return


def clear_home_product():
    st.session_state['home_product_field'] = 'Todos los productos'


def read_home_model(week, group, region, count, order='Mayores cambios', product_filter=None):
    """Real regional or national series; K6 stays explicitly national."""
    version=get_database_version()
    week_date=pd.Timestamp(week)
    previous_week=f'{week_date-pd.Timedelta(days=7):%Y-%m-%d}'
    prices=read_cached_national_prices(version)
    current=prices[prices['week_start']==week_date].copy()
    previous=prices[prices['week_start']==pd.Timestamp(previous_week)].copy()
    if group != ALL_VALUES:
        current=current[current['product_group']==group]
        previous=previous[previous['product_group']==group]
    if product_filter:
        family, product, variety = product_filter
        current=current[(current['product_group']==family) & (current['product']==product) & (current['variety']==variety)]
        previous=previous[(previous['product_group']==family) & (previous['product']==product) & (previous['variety']==variety)]
    snapshot=read_cached_week_snapshot(version,week)
    prior=read_cached_week_snapshot(version,previous_week)
    if group != ALL_VALUES:
        snapshot=snapshot[snapshot['product_group']==group]
        prior=prior[prior['product_group']==group]
    if product_filter:
        family, product, variety = product_filter
        snapshot=snapshot[(snapshot['product_group']==family) & (snapshot['product']==product) & (snapshot['variety']==variety)]
        prior=prior[(prior['product_group']==family) & (prior['product']==product) & (prior['variety']==variety)]
    coverage=snapshot.region.nunique()
    join=queries.KEY_COLUMNS+['channel']
    if region != ALL_VALUES:
        snapshot=snapshot[snapshot.region==region]
        prior=prior[prior.region==region]
        current=snapshot.assign(national_price=snapshot.price)
        previous=prior.assign(national_price=prior.price)
        coverage=snapshot.region.nunique()
    variations=home_mockup.compare_week(current,previous,join)
    variations['_coverage_changed']=False
    if region == ALL_VALUES:
        regions_now=snapshot.groupby(join).region.agg(frozenset).rename('_regions_now')
        regions_before=prior.groupby(join).region.agg(frozenset).rename('_regions_before')
        variations=variations.merge(regions_now,on=join,how='left').merge(regions_before,on=join,how='left')
        variations['_coverage_changed']=(variations['_regions_now'] != variations['_regions_before']) & variations.variation.notna()
    valid=variations[variations.variation.notna() & variations.variation.abs().lt(float('inf'))].copy()
    parts=build_movement_proportions(valid)
    counts=[int(v) for v in parts.value]
    alert_rows=read_price_alerts()
    if group != ALL_VALUES:
        alert_rows=alert_rows[alert_rows.product_group==group]
    if product_filter:
        family, product, variety = product_filter
        alert_rows=alert_rows[(alert_rows['product_group']==family) & (alert_rows['product']==product) & (alert_rows['variety']==variety)]
    alert_count=len(alert_rows[alert_rows.week_start==week_date])
    alert_previous=len(alert_rows[alert_rows.week_start==pd.Timestamp(previous_week)])
    variations['is_alert']=False
    variations['_severity']=0.0
    if region == ALL_VALUES:
        week_alerts=alert_rows[alert_rows.week_start==week_date].copy()
        week_alerts['_severity']=(week_alerts.variation-week_alerts.usual_variation).abs()/week_alerts.variation_deviation
        variations=variations.drop(columns=['is_alert','_severity']).merge(
            week_alerts[join+['_severity']].assign(is_alert=True),on=join,how='left',validate='one_to_one')
        variations['is_alert']=variations.is_alert.eq(True)
        variations['_severity']=variations['_severity'].fillna(0)
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
                f"{home_mockup.product_label(row, True)} · {row['channel']}"
                for _, row in subset.head(2).iterrows()
            ]
    ranked=home_mockup.order_movements(variations,count,order)
    if ranked.empty and valid.empty and order != 'Inusuales':
        ranked=variations.sort_values(join).head(count)
    # Default selection is the first displayed movement; clicks retain the exact key.
    chosen=None
    focus=st.session_state.get('mock_focus_key')
    if focus:
        matched=variations
        for field,value in focus.items():
            matched=matched[matched[field]==value]
        if not matched.empty:
            chosen=matched.iloc[0]
    if chosen is None:
        reference=ranked if not ranked.empty else variations.sort_values(join)
        if not reference.empty:
            chosen=reference.iloc[0]
    history=pd.DataFrame(columns=['week_start','national_price'])
    subtitle='Sin producto con precios disponibles'
    if chosen is not None:
        key={field:chosen[field] for field in queries.KEY_COLUMNS}
        channel=chosen['channel']
        if region == ALL_VALUES:
            history=keep_product(prices,{'key':key})
            history=history[history.channel==channel]
        else:
            sql='''SELECT w.week_start,w.price AS national_price FROM weekly_price w
                JOIN dim_product p USING(product_id) JOIN dim_region r USING(region_id)
                JOIN dim_channel c USING(channel_id) WHERE w.flag IS NULL
                AND p.product_group=? AND p.product=? AND p.variety=? AND p.quality=?
                AND w.normalized_unit=? AND r.region=? AND c.channel=? AND w.week_start BETWEEN ? AND ?'''
            history=queries.run_sql(sql,parameters=list(key.values())+[region,channel,f'{week_date-pd.Timedelta(weeks=11):%Y-%m-%d}',week])
            history['week_start']=pd.to_datetime(history.week_start)
        history=history[history.week_start.between(week_date-pd.Timedelta(weeks=11),week_date)]
        subtitle=home_mockup.product_label(chosen,True)+' · '+channel+' · $/'+key['normalized_unit']
    return dict(counts=counts,alert_count=alert_count,alert_delta=alert_count-alert_previous,
                examples=example_sets,
                product_filter=product_filter,
                family_rows=variations[variations.variation.notna() & variations.variation.abs().lt(float('inf'))].to_dict('records'),
                rows=ranked.to_dict('records'),selected=chosen.to_dict() if chosen is not None else None,
                history=history,subtitle=subtitle,coverage=coverage,missing=max(0,len(current)-sum(counts)),
                available=len(current),national=region==ALL_VALUES,
                coverage_changed=int(variations['_coverage_changed'].sum()),
                week_label=f'{week_date:%d-%m-%Y}',previous_label=f'{pd.Timestamp(previous_week):%d-%m-%Y}')


def build_regional_movement_model(current, previous):
    """Summarize equivalent weekly prices by region without inventing a basket.

    A movement smaller than 0.05 % is displayed as unchanged, consistently with
    the product tables. The percentage is the share in the dominant direction.
    """
    join = queries.KEY_COLUMNS + ['channel', 'region']
    current = current[join + ['price']].rename(columns={'price': 'national_price'})
    previous = previous[join + ['price']].rename(columns={'price': 'national_price'})
    compared = home_mockup.compare_week(current, previous, join)
    compared = compared[compared['variation'].notna()
                        & compared['variation'].abs().lt(float('inf'))].copy()
    rows = []
    current_counts = current.groupby('region').size().to_dict()
    for region in sorted(set(current['region'])):
        values = compared.loc[compared['region'] == region, 'variation']
        up = int(values.ge(.0005).sum())
        down = int(values.le(-.0005).sum())
        stable = int(values.abs().lt(.0005).sum())
        total = up + down + stable
        missing = max(0, int(current_counts.get(region, 0)) - total)
        counts = {'rise': up, 'fall': down, 'neutral': stable}
        if not total:
            state, share = 'missing', None
        else:
            largest = max(counts.values())
            leaders = [name for name, value in counts.items() if value == largest]
            state = leaders[0] if len(leaders) == 1 else 'mixed'
            share = largest / total * 100
        rows.append({'region': region, 'state': state, 'share': share, 'up': up,
                     'down': down, 'stable': stable, 'total': total, 'missing': missing})
    return rows


def read_regional_movement_model(week, group=ALL_VALUES, product_filter=None):
    """All available regions under the family/product filters of the dashboard."""
    version = get_database_version()
    week_date = pd.Timestamp(week)
    previous_week = f'{week_date - pd.Timedelta(days=7):%Y-%m-%d}'
    current = read_cached_week_snapshot(version, week).copy()
    previous = read_cached_week_snapshot(version, previous_week).copy()
    if group != ALL_VALUES:
        current = current[current['product_group'] == group]
        previous = previous[previous['product_group'] == group]
    if product_filter:
        family, product, variety = product_filter
        for frame_name, frame in (('current', current), ('previous', previous)):
            filtered = frame[(frame['product_group'] == family) & (frame['product'] == product)
                             & (frame['variety'] == variety)]
            if frame_name == 'current':
                current = filtered
            else:
                previous = filtered
    return build_regional_movement_model(current, previous)


def home_alert_rows(week, group, product_filter=None):
    """National alerts in the same week and product scope as the dashboard."""
    rows = read_price_alerts()
    rows = rows[rows['week_start'] == pd.Timestamp(week)]
    if group != ALL_VALUES:
        rows = rows[rows['product_group'] == group]
    if product_filter:
        family, product, variety = product_filter
        rows = rows[(rows['product_group'] == family) & (rows['product'] == product)
                    & (rows['variety'] == variety)]
    rows = rows.copy()
    rows['_distance'] = ((rows['variation'] - rows['usual_variation']).abs()
                         / rows['variation_deviation'])
    return rows.sort_values(['_distance', 'product_group', 'product'],
                            ascending=[False, True, True])


def home_alert_table(rows):
    """Readable, severity-ordered rows for the dashboard alert dialog."""
    records = rows.to_dict('records')
    return pd.DataFrame({
        'N.º': range(1, len(records) + 1),
        'Nivel': [find_alert_level(row['_distance'])[0] for row in records],
        'Familia': [row['product_group'] for row in records],
        'Producto': [describe_product(row) for row in records],
        'Canal': [row['channel'] for row in records],
        'Unidad': [f"$/{row['normalized_unit']}" for row in records],
        'Anterior': [home_mockup.money(row['national_price'] / (1 + row['variation']))
                     for row in records],
        'Actual': [home_mockup.money(row['national_price']) for row in records],
        'Cambio': [home_mockup.percent(row['variation'] * 100, True) for row in records],
    })


def style_home_alert_table(table, mode):
    """Color the alert level and price direction without changing their text labels."""
    dark = charts.get_palette(mode)['base'] == 'dark'
    colors = ({'Muy alta': ('#7f1d1d', '#fff4f4'), 'Alta': ('#9a3412', '#fff4e8'),
               'Moderada': ('#78450a', '#fff4d2')} if dark else
              {'Muy alta': ('#fee2e2', '#991b1b'), 'Alta': ('#ffedd5', '#9a3412'),
               'Moderada': ('#fef3c7', '#854d0e')})
    def level_css(value):
        background, foreground = colors[value]
        return f'background-color:{background};color:{foreground};font-weight:700'
    def change_css(value):
        foreground = ('#ff8a96' if dark else '#b91c1c') if value.startswith('+') else ('#83baff' if dark else '#1d4ed8')
        return f'color:{foreground};font-weight:700'
    return table.style.map(level_css, subset=['Nivel']).map(change_css, subset=['Cambio'])


@st.dialog('Alertas de precio', width='large')
def show_home_alerts_dialog(week, group, product_filter, mode):
    rows = home_alert_rows(week, group, product_filter)
    if rows.empty:
        st.info('No hay alertas para esta selección.')
        return
    counts = rows.groupby('product_group').size().sort_values(ascending=False)
    families = counts.index.tolist()
    selected = st.session_state.get('home_alert_selected_family')
    if selected not in families:
        selected = None
        st.session_state['home_alert_selected_family'] = None
    if selected is None:
        st.html('<div class="home-alert-overview-marker"></div>')
        st.caption(f'{len(rows)} cambios poco habituales · {len(families)} familias · datos nacionales de ODEPA')
        st.html('<div class="home-alert-gallery-legend">'
                '<span><i class="hot"></i>Más alertas</span>'
                '<span><i class="warm"></i>Intermedio</span>'
                '<span><i class="mild"></i>Menos alertas</span>'
                '<small>El color indica cantidad, no gravedad.</small></div>')
        icons = {'Hortalizas': '🥬', 'Frutas': '🍎', 'Pan': '🍞',
                 'Carne bovina': '🥩', 'Abarrotes y otros': '🥫'}
        max_count = int(counts.max())
        tile_css = []
        shapes = ('circle(50%)',
                  'polygon(18% 0%,82% 0%,100% 50%,82% 100%,18% 100%,0% 50%)',
                  'polygon(50% 0%,100% 50%,50% 100%,0% 50%)',
                  'polygon(50% 0%,100% 100%,0% 100%)',
                  'polygon(25% 0%,75% 0%,100% 25%,100% 75%,75% 100%,25% 100%,0% 75%,0% 25%)',
                  'inset(0 round 28%)',
                  'polygon(50% 0%,95% 35%,80% 95%,20% 95%,5% 35%)')
        for index, family in enumerate(families):
            icon = icons.get(family, '🍗' if 'Cerdo' in family else '🥚')
            ratio = int(counts[family]) / max_count
            tone = ('#db3349' if ratio >= .75 else '#ed6b29' if ratio >= .45
                    else '#f3a536' if ratio >= .25 else '#c6a062')
            tile_css.append(f'.st-key-home_alert_card_{index}'
                            f'{{--alert-tone:{tone};--alert-shape:{shapes[index % len(shapes)]};}}'
                            f'.st-key-home_alert_card_{index} button::after{{content:"{icon}";}}')
        st.html('<style>' + ''.join(tile_css) + '</style>')
        for start in range(0, len(families), 4):
            columns = st.columns(4, gap='small')
            for offset, family in enumerate(families[start:start + 4]):
                index = start + offset
                total = int(counts[family])
                label = f'{family}\n{total} {"alerta" if total == 1 else "alertas"}  →'
                with columns[offset].container(key=f'home_alert_card_{index}'):
                    if st.button(label, key=f'home_alert_family_{index}', use_container_width=True):
                        st.session_state['home_alert_selected_family'] = family
                        st.rerun(scope='fragment')
        st.caption('La alerta señala un cambio inusual respecto de la semana anterior; no significa que el alimento sea el más caro.')
        return

    st.html('<div class="home-alert-detail-marker"></div>')
    family_rows = rows[rows['product_group'] == selected]
    family_total = len(family_rows)
    with st.container(key='home_alert_detail_heading', horizontal=True,
                      vertical_alignment='center', gap='small'):
        if st.button('← Familias', key='home_alert_back'):
            st.session_state['home_alert_selected_family'] = None
            st.rerun(scope='fragment')
        st.subheader(f'{selected} · {family_total} {"alerta" if family_total == 1 else "alertas"}')
    units = ['Todas las unidades'] + sorted(family_rows['normalized_unit'].unique())
    unit_key = f'home_alert_unit_{selected}'
    if st.session_state.get(unit_key) not in units:
        st.session_state[unit_key] = units[0]
    with st.container(key='home_alert_detail_tools', horizontal=True,
                      vertical_alignment='bottom', gap='small'):
        st.html('<div class="home-alert-level-guide">'
                '<span><i class="critical"></i>Muy alta</span>'
                '<span><i class="high"></i>Alta</span>'
                '<span><i class="moderate"></i>Moderada</span>'
                '<small>El color indica cuán inusual fue el cambio.</small></div>')
        selected_unit = st.selectbox('Unidad', units, key=unit_key,
                                     format_func=lambda value: value if value == 'Todas las unidades' else f'$/{value}')
    if selected_unit != 'Todas las unidades':
        family_rows = family_rows[family_rows['normalized_unit'] == selected_unit]
        st.caption(f'Mostrando {len(family_rows)} de {family_total} alertas de esta familia.')
    table = home_alert_table(family_rows).drop(columns='Familia')
    st.dataframe(style_home_alert_table(table, mode),
                 hide_index=True, use_container_width=True,
                 height=min(520, max(150, 35 * (len(family_rows) + 1))))


PRODUCT_ORDERS = ('Mayor cambio', 'Subidas', 'Bajadas', 'Nombre', 'Inusuales')


def normalize_search(text):
    """Lower case without accents: «Ají», «aji» and «AJI» read the same."""
    decomposed = unicodedata.normalize('NFD', str(text).lower())
    return ''.join(char for char in decomposed if unicodedata.category(char) != 'Mn').strip()


def matches_product_search(row, query):
    """True when every searched word starts a word of the product or its variety."""
    words = re.split(r'[^0-9a-zñ]+', normalize_search(f"{row['product']} {row['variety']}"))
    return all(any(word.startswith(term) for word in words) for term in normalize_search(query).split())


@st.cache_data
def read_cached_region_directions(database_version, week):
    """{(product key, channel): (regions up, regions down)} between two consecutive weeks."""
    week_date = pd.Timestamp(week)
    join = queries.KEY_COLUMNS + ['channel']
    current = read_cached_week_snapshot(database_version, week)
    previous = read_cached_week_snapshot(database_version, f'{week_date - pd.Timedelta(days=7):%Y-%m-%d}')
    columns = join + ['region', 'price']
    compared = home_mockup.compare_week(current[columns].rename(columns={'price': 'national_price'}),
                                        previous[columns].rename(columns={'price': 'national_price'}),
                                        join + ['region'])
    compared = compared[compared['variation'].notna() & compared['variation'].abs().lt(float('inf'))]
    up = compared[compared['variation'] >= .0005].groupby(join).size()
    down = compared[compared['variation'] <= -.0005].groupby(join).size()
    keys = set(up.index) | set(down.index)
    return {key: (int(up.get(key, 0)), int(down.get(key, 0))) for key in keys}


def sort_family_products(rows, order):
    """The family table under the chosen order; ties stay in a stable, readable order."""
    names = lambda row: (str(row['product']), str(row['variety']), str(row['channel']))
    if order == 'Nombre':
        return sorted(rows, key=names)
    if order == 'Subidas':
        return sorted(rows, key=lambda row: (-row['variation'], names(row)))
    if order == 'Bajadas':
        return sorted(rows, key=lambda row: (row['variation'], names(row)))
    if order == 'Inusuales':
        # National alerts only, the most unusual first (distance to the usual range).
        return sorted((row for row in rows if row.get('is_alert')),
                      key=lambda row: (-row.get('_severity', 0), names(row)))
    return sorted(rows, key=lambda row: (-abs(row['variation']), names(row)))


def show_market_overview(mode, prefix):
    """Map, movement by family and products of one family on one screen (D-092)."""
    # Streamlit reruns this file without reimporting helpers; keep the live page
    # in sync when the dashboard markup changes during development.
    importlib.reload(home_mockup)
    st.markdown(home_mockup.style(mode,charts.get_palette(mode)),unsafe_allow_html=True)
    options=read_cached_filter_options(get_database_version())
    apply_home_focus(options)
    if read_filter('week') not in options['week']:
        st.session_state['dashboard_week']=options['week'][0]
    if read_filter('region') not in options['region']:
        st.session_state['dashboard_region']=ALL_VALUES
    week,region=read_filter('week'),read_filter('region')
    st.session_state.pop('home_product_selection', None)
    latest=read_latest_run()
    stamp=to_chile_time(parse_run_start(latest['started_at']))
    month=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'][stamp.month-1]
    updated=f'{stamp.day} {month} · {stamp:%H:%M}'
    # Every family stays in the movement chart; the selected one fills the product table.
    model=read_home_model(week,ALL_VALUES,region,DEFAULT_TOP_N)
    regional_rows=read_regional_movement_model(week)
    averages=home_mockup.family_averages(model['family_rows'])
    families=[family for family, _, _ in averages]
    family=st.query_params.get('familia')
    if family not in families:
        family=families[0] if families else None
    scope='todo Chile' if region == ALL_VALUES else home_mockup.short_region(region)
    def overview_link(chosen_region, chosen_family):
        address = build_page_address(PAGE_HOME)
        parameters = {'_home_region': chosen_region or ALL_VALUES, '_home_week': week}
        if chosen_family:
            parameters['familia'] = chosen_family
        return address + ('&' if '?' in address else '?') + urlencode(parameters)
    def context_link(page,row):
        payload={field:row[field] for field in queries.KEY_COLUMNS+['channel']}
        token=base64.urlsafe_b64encode(json.dumps(payload,ensure_ascii=False).encode()).decode()
        address=build_page_address(page)
        return address+('&' if '?' in address else '?')+urlencode({
            '_home_key':token,'_home_group':row['product_group'],'_home_region':region,'_home_week':week})
    st.markdown('<div class="greenocean-mockup">' + home_mockup.dashboard_header(
        describe_week_span(week), updated, latest['status']==etl.STATUS_LOADED, model['family_rows'],
        regional_rows, None if region == ALL_VALUES else region) + '</div>', unsafe_allow_html=True)
    map_column, detail_column = st.container(key='home_overview').columns([0.56, 1.44], gap='small')
    # Markdown's explicit HTML mode preserves the inline geographic SVG; st.html's
    # sanitizer intentionally removes interactive SVG links.
    map_column.markdown('<div class="greenocean-mockup">' + home_mockup.regional_map(
        regional_rows, lambda chosen: overview_link(chosen, family), model['week_label'],
        model['previous_label'], None if region == ALL_VALUES else region) + '</div>', unsafe_allow_html=True)
    with detail_column:
        st.markdown('<div class="greenocean-mockup">' + home_mockup.family_movement(
            model['family_rows'], lambda chosen: overview_link(None if region == ALL_VALUES else region, chosen),
            family, scope) + '</div>', unsafe_allow_html=True)
        with st.container(key='home_products'):
            rows=[row for row in model['family_rows'] if row['product_group'] == family]
            average=next((value for name, value, _ in averages if name == family), None)
            heading = st.empty()
            search_column, channel_column, order_column, history_column = st.columns(
                [1.7, 1.25, 1.35, 0.95], vertical_alignment='center')
            query = search_column.text_input('Buscar', key='home_products_search', icon=':material/search:',
                                             placeholder='Producto, ej.: lechuga', label_visibility='collapsed',
                                             type='search', live=True)
            channels=['Todos'] + sorted({str(row['channel']) for row in rows})
            if st.session_state.get('home_products_channel') not in channels:
                st.session_state['home_products_channel']='Todos'
            channel=channel_column.selectbox('Canal', channels, key='home_products_channel')
            # Alerts are national: «Inusuales» only applies to the whole country.
            orders=PRODUCT_ORDERS if region == ALL_VALUES else PRODUCT_ORDERS[:-1]
            if st.session_state.get('home_products_order') not in orders:
                st.session_state['home_products_order']=orders[0]
            order=order_column.selectbox('Orden', orders, key='home_products_order')
            total=len(rows)
            if channel != 'Todos':
                rows=[row for row in rows if row['channel'] == channel]
            if query.strip():
                rows=[row for row in rows if matches_product_search(row, query)]
            rows=sort_family_products(rows, order)
            heading.markdown('<div class="greenocean-mockup">' + home_mockup.products_heading(
                family or 'Sin familia', average, scope, len(rows), total) + '</div>', unsafe_allow_html=True)
            directions=read_cached_region_directions(get_database_version(), week)
            for row in rows:
                row['_regions']=directions.get(tuple(row[field] for field in queries.KEY_COLUMNS+['channel']))
            history_address=(context_link(PAGE_SEASONALITY, rows[0]) if rows else build_page_address(PAGE_SEASONALITY))
            history_column.markdown(f'<div class="greenocean-mockup"><a class="mock-history-button" '
                                    f'href="{html.escape(history_address)}" target="_self">Contexto del precio</a></div>',
                                    unsafe_allow_html=True)
            st.markdown('<div class="greenocean-mockup">' + home_mockup.products_table(
                rows, lambda row: context_link(PAGE_SEASONALITY, row), model['week_label'],
                model['previous_label'], query.strip()) + home_mockup.coverage_note(
                model, build_page_address(PAGE_OPERATIONS), build_page_address(PAGE_DOCUMENTATION))
                + '</div>', unsafe_allow_html=True)


def show_home_page(mode):
    """Market dashboard with latest-week rankings; diagrams have their own destination."""
    with st.container(key="market_dashboard"):
        show_market_overview(mode, "home")


PIPELINE_DIAGRAMS = {"recorrido", "estado", "arquitectura"}


def build_pipeline_diagram_address(diagram):
    """Direct address of one diagram inside the Pipeline page."""
    address = build_page_address(PAGE_DIAGRAMS)
    separator = "&" if "?" in address else "?"
    return address + separator + urlencode({PIPELINE_DIAGRAM_PARAMETER: diagram})


def build_pipeline_mini_svg(states, figures, mode, animate_flow):
    """Build the compact execution journey, including hot-reload compatibility."""
    mini_builder_parameters = inspect.signature(
        architecture.build_mini_journey_svg).parameters
    if "animate_flow" in mini_builder_parameters:
        return architecture.build_mini_journey_svg(
            states, figures, mode, animate_flow=animate_flow)
    return architecture.build_mini_journey_svg(states, figures, mode)


def build_pipeline_gallery_link(svg, diagram, label, css_class=""):
    """A whole diagram acts as the entry point to its focused view."""
    address = build_pipeline_diagram_address(diagram)
    return (f'<a class="pipeline-gallery-link {html.escape(css_class)}" '
            f'href="{html.escape(address)}" target="_self" '
            f'aria-label="Ampliar {html.escape(label)}">{svg}'
            f'<span class="pipeline-open-label">Ampliar ↗</span></a>')


def show_pipeline_page_header():
    """A clean title above the gallery; execution evidence lives in its own card."""
    st.markdown('<div class="compact-header pipeline-page-header">'
                '<h1>Pipeline y arquitectura</h1></div>', unsafe_allow_html=True)


def show_focused_pipeline_diagram(diagram, mode, animate_flow, journey):
    """Show one Pipeline diagram alone, with a compact return control."""
    states, figures, pipeline_run, latest_load, error_note = journey
    titles = {"recorrido": "Recorrido completo por capas",
              "estado": "Estado de la última ejecución",
              "arquitectura": "Arquitectura por plataforma"}
    st.markdown(
        '<div class="pipeline-focus-toolbar">'
        f'<strong>{html.escape(titles[diagram])}</strong></div>',
        unsafe_allow_html=True)
    with st.container(key=f"pipeline_focus_{diagram}"):
        if diagram == "recorrido":
            st.markdown(
                zoom.build_zoom_frame_html(
                    architecture.build_journey_svg(
                        states, figures, mode, animate_flow=animate_flow), "diagram-wide")
                + zoom.build_zoom_frame_html(
                    architecture.build_vertical_journey_svg(
                        states, figures, mode, animate_flow=animate_flow), "diagram-narrow"),
                unsafe_allow_html=True)
        elif diagram == "estado":
            st.markdown(build_run_status_html(states, pipeline_run, latest_load),
                        unsafe_allow_html=True)
            if error_note:
                st.caption(error_note)
            st.markdown(zoom.build_zoom_frame_html(build_pipeline_mini_svg(
                states, figures, mode, animate_flow)), unsafe_allow_html=True)
            st.markdown(build_journey_legend_html(), unsafe_allow_html=True)
        else:
            st.markdown(zoom.build_zoom_frame_html(architecture.build_devops_svg(
                states, build_devops_figures(figures), mode,
                animate_flow=animate_flow), "diagram-devops"), unsafe_allow_html=True)
    st.markdown('<div class="pipeline-focus-return">'
                + build_link_html("← Volver a los tres diagramas",
                                  build_page_address(PAGE_DIAGRAMS))
                + '</div>', unsafe_allow_html=True)
    st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)


def show_diagrams_page(mode):
    # Streamlit may rerun this module while retaining an older architecture
    # import from the same live session.
    if not hasattr(architecture, "build_platform_gallery_svg"):
        importlib.reload(architecture)
    focused = st.query_params.get(PIPELINE_DIAGRAM_PARAMETER)
    focused = focused if focused in PIPELINE_DIAGRAMS else None
    journey = read_journey()
    # The motion explains the data route and is part of the diagram itself. Keep it
    # on consistently; the SVG still honours the operating system's reduced-motion
    # preference for accessibility.
    animate_flow = True
    if focused:
        show_focused_pipeline_diagram(focused, mode, animate_flow, journey)
        return

    show_pipeline_page_header()
    states, figures, pipeline_run, latest_load, error_note = journey

    # The complete journey is the main diagram, so it leads the gallery and gets
    # substantially more room than either supporting view.
    with open_card("pipeline_gallery_main", "Recorrido completo por capas",
                   hint=ARCHITECTURE_HINT):
        st.markdown(build_pipeline_gallery_link(
            architecture.build_journey_svg(
                states, figures, mode, animate_flow=animate_flow),
            "recorrido", "Recorrido completo por capas", "pipeline-gallery-main-link"),
            unsafe_allow_html=True)

    status_column, platform_column = st.columns(2, gap="small")
    with status_column, open_card("pipeline_gallery_status", "Estado de la última ejecución",
                                  hint=ARCHITECTURE_HINT):
        st.markdown('<div class="pipeline-status-content">'
                    + build_run_status_html(states, pipeline_run, latest_load)
                    + '<div class="pipeline-gallery-status-preview">'
                    + build_pipeline_mini_svg(states, figures, mode, animate_flow)
                    + '</div></div>', unsafe_allow_html=True)
    with platform_column, open_card("pipeline_gallery_platform", "Arquitectura por plataforma",
                                    hint=DEVOPS_HINT):
        st.markdown(build_pipeline_gallery_link(
            '<span class="pipeline-platform-compact">'
            + architecture.build_platform_gallery_svg(states, figures, mode,
                                                      animate_flow=animate_flow)
            + '</span><span class="pipeline-platform-detailed">'
            + architecture.build_devops_svg(states, build_devops_figures(figures), mode,
                                             animate_flow=animate_flow)
            + '</span>',
            "arquitectura", "Arquitectura por plataforma",
            "pipeline-gallery-secondary-link"), unsafe_allow_html=True)


# endregion


# region Margins page
def show_gap_dumbbell(rows, mode):
    """Card: wholesale and consumer price of each channel in the latest common week."""
    latest_week = rows["week_start"].max()
    week_rows = rows[rows["week_start"] == latest_week]
    with open_card("gap_dumbbell", "Mayorista y consumidor, la última semana",
                   hint=DUMBBELL_HINT, kpi="K1"):
        st.caption(f"Semana del {latest_week:%d-%m-%Y}, {week_rows['region'].iloc[0]}. "
                   "Punto gris: mayorista; punto de color: cada canal.")
        dumbbell_rows = week_rows[["channel", "wholesale_price", "consumer_price"]].copy()
        dumbbell_rows["gap_label"] = [charts.format_signed_percent(margin * 100)
                                      for margin in week_rows["margin"]]
        show_chart(charts.draw_dumbbell(dumbbell_rows, rows["normalized_unit"].iloc[0], mode))
        missing = sorted(set(rows["channel"]) - set(week_rows["channel"]))
        if missing:
            st.caption(f"Sin precio esa semana: {', '.join(missing)}.")


def show_gap_line(rows, channel, mode, weeks=None, key_prefix="gap_line"):
    """Card: the gap of one channel, week by week, as one line."""
    channel_rows = rows[rows["channel"] == channel].sort_values("week_start")
    if weeks:
        channel_rows = channel_rows.tail(weeks)
    period = f"últimas {weeks} semanas" if weeks else "todo el período"
    with open_card(f"{key_prefix}_{channel}", f"Brecha · {channel}", period,
                   hint=GAP_LINE_HINT, kpi="K1"):
        line_rows = pd.DataFrame({"week_start": channel_rows["week_start"],
                                  "value": channel_rows["margin"] * 100})
        chart = charts.draw_single_weekly_area(
            line_rows, "Brecha (%)", line_rows["value"].map(charts.format_percent), mode,
            reference_value=0)
        if st.session_state.get(COMPACT_VIEW) and key_prefix == "gap_line":
            chart = chart.properties(height=TILE_HEIGHT - 60)
        show_chart(chart)


def show_gap_tab(mode, filters):
    """K1 on one screen: the dumbbell of this week, then one gap line per channel side by
    side; K5 and the whole history below (D-067)."""
    rows = read_margin_rows(filters)
    rows = rows[rows["channel"].isin(filters["channels"])].copy()
    if rows.empty:
        st.info(NO_MARGIN_TEXT)
        return
    show_gap_dumbbell(rows, mode)
    channels = [channel for channel in filters["channels"] if channel in set(rows["channel"])]
    for column, channel in zip(st.columns(len(channels)), channels):
        with column:
            show_gap_line(rows, channel, mode, weeks=GAP_LINE_WEEKS)
    st.caption("Brecha = (precio al consumidor − precio mayorista) / precio mayorista, con la "
               "misma variedad, calidad, región, semana y unidad.")
    with st.expander("Análisis avanzado · tiempo entre cambios de precios", expanded=False):
        show_lag_card(rows, mode)
    with st.expander("Ver evolución histórica", expanded=False):
        for channel in channels:
            show_gap_line(rows, channel, mode, key_prefix="gap_history")
    st.caption(NOMINAL_PRICES_TEXT)


def build_lag_bar_rows(correlations, best_lag, mode):
    """Bars of K5: one per lag, the chosen lag in the accent color."""
    correlations = correlations.dropna(subset=["correlation"])
    palette = charts.get_palette(mode)
    bar_rows = pd.DataFrame({
        "label": [charts.describe_weeks(weeks).capitalize()
                  for weeks in correlations["lag_weeks"]],
        "value": correlations["correlation"].to_numpy(),
        "value_label": correlations["correlation"].map(charts.format_index).to_numpy(),
        "meaning": [f"Correlación con {pairs} pares de cambios semanales"
                    for pairs in correlations["pair_count"]]})
    colors = [palette["accent"] if weeks == best_lag else palette["reference"]
              for weeks in correlations["lag_weeks"]]
    return bar_rows, colors


def show_lag_card(rows, mode):
    """Card: K5, weeks the consumer price takes to follow the wholesale price."""
    with open_card("lag", "Tiempo entre el cambio mayorista y el consumidor",
                   hint=LAG_HINT, kpi="K5"):
        channel = choose_value("Canal", rows["channel"].unique(), DEFAULT_CHANNEL,
                               key="lag_channel")
        series_rows = rows[rows["channel"] == channel]
        if not lag.has_enough_weeks(series_rows):
            st.info(f"Este cálculo necesita {lag.MINIMUM_WEEKS} semanas con ambos precios; esta "
                    f"selección tiene {series_rows['week_start'].nunique()}.")
            return
        correlations = lag.correlate_by_lag(series_rows)
        best = lag.find_lag(correlations)
        if best is None:
            st.info("No hay cambios semanales suficientes para calcular el rezago.")
            return
        best_lag, correlation, pair_count = best
        if lag.is_clear_relation(correlation, pair_count):
            lag_text = charts.describe_weeks(best_lag).capitalize()
        else:
            # The highest of several weak correlations is noise, not a lag.
            lag_text = "Sin relación clara"
        st.markdown(f'<div class="kpi-value">{lag_text}</div>'
                    f'<div class="kpi-note">correlación más alta '
                    f'{charts.format_index(correlation)} en {channel}, con {pair_count} '
                    f'pares de cambios semanales</div>', unsafe_allow_html=True)
        bar_rows, colors = build_lag_bar_rows(correlations, best_lag, mode)
        show_chart(charts.draw_horizontal_bars(bar_rows, "Correlación", mode, colors,
                                               reference_value=0, is_sorted_by_value=False))
        st.caption(LAG_NOTE)
# endregion


# region Channels and regions page
def describe_gap_basis(rows):
    """What each bar stands on: 'Supermercado: 9 regiones, 363 semanas'.

    When a single region is behind a bar it is named, so a regional figure is
    never read as a national one (the +131 % of Arica, T-52).
    """
    lines = []
    for channel, channel_rows in rows.groupby("channel"):
        regions = sorted(channel_rows["region"].unique())
        region_text = (f"1 región ({charts.shorten_region_name(regions[0])})"
                       if len(regions) == 1 else f"{len(regions)} regiones")
        # Each row is one week in one region where both channels have a price.
        count_text = (f"{charts.format_thousands(len(channel_rows))} semanas"
                      if len(regions) == 1
                      else f"{charts.format_thousands(len(channel_rows))} comparaciones")
        lines.append(f"{channel}: {region_text}, {count_text}")
    return lines


def label_channel_with_its_regions(channel, regions):
    """'Supermercado · solo Arica y Parinacota' when 1 or 2 regions stand behind a bar.

    Next to the bar, so a regional figure is never read as a national one.
    """
    if len(regions) > MAXIMUM_REGIONS_NAMED:
        return channel
    names = ", ".join(charts.shorten_region_name(region) for region in sorted(regions))
    return f"{channel} · solo {names}"


def list_channels_without_pairs(rows, consumer_channels, reference_channel):
    """Channels of the product that never share a week and region with the reference."""
    channels_with_pairs = set(rows["channel"])
    return sorted(set(consumer_channels) - channels_with_pairs - {reference_channel})


def show_channel_gaps(rows, consumer_channels, mode):
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
        regions_by_channel = rows.groupby("channel")["region"].unique()
        bar_rows = pd.DataFrame({
            "label": [label_channel_with_its_regions(channel, regions_by_channel[channel])
                      for channel in average_gap.index],
            "value": average_gap.to_numpy()})
        bar_rows["value_label"] = bar_rows["value"].map(charts.format_signed_percent)
        bar_rows["meaning"] = [charts.describe_channel_gap(gap, reference_channel)
                               for gap in bar_rows["value"]]
        colors = [charts.get_channel_color(channel, mode) for channel in average_gap.index]
        chart = charts.draw_horizontal_bars(bar_rows, "Diferencia promedio (%)", mode,
                                            colors, reference_value=0,
                                            reference_label=reference_channel, label_limit=175)
        chart = chart.configure_axisY(labelExpr="split(datum.label, ' · ')", labelLineHeight=12)
        show_chart(chart.properties(height=max(160, len(bar_rows) * 50)))
        st.caption(f"Cuánto más caro (+) o más barato (−) es cada canal que "
                   f"«{reference_channel}», en las semanas y regiones donde ambos tienen precio.  \n"
                   f"Base de cada barra: {' · '.join(describe_gap_basis(rows))}.")
        show_data_sample(pd.DataFrame({"Canal / alcance": bar_rows["label"], "Diferencia": bar_rows["value_label"], "_order": bar_rows["value"]}).sort_values("_order", ascending=False).drop(columns="_order"))
        missing_channels = list_channels_without_pairs(rows, consumer_channels,
                                                       reference_channel)
        if missing_channels:
            st.caption(f"Sin datos comparables con «{reference_channel}»: "
                       f"{', '.join(missing_channels)}.")


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
                                               reference_value=1,
                                               reference_label="Promedio nacional"))
        show_data_sample(pd.DataFrame({"Región": bar_rows["label"], "Índice": bar_rows["value_label"], "_order": bar_rows["value"]}).sort_values("_order", ascending=False).drop(columns="_order"))
        st.caption("Sobre 1, la región es más cara que el promedio nacional de la semana; "
                   "bajo 1, más barata.")


def show_channels_tab(mode, filters):
    """K2 and K3 for any product group, with or without a wholesale price."""
    st.caption("Qué canal y qué región son más caros para el producto elegido, incluidas "
               "carnes, lácteos y abarrotes.")
    regional_rows = read_indicator_for_key("k3_regional_index", filters["key"])
    gap_rows = read_indicator_for_key("k2_channel_gap", filters["key"])
    consumer_channels = [channel for channel in regional_rows["channel"].unique()
                         if channel != WHOLESALE_LABEL]
    gaps_column, regions_column = st.columns(2)
    with gaps_column:
        show_channel_gaps(gap_rows, consumer_channels, mode)
    with regions_column:
        show_regional_index(regional_rows, mode)
    st.caption(NOMINAL_PRICES_TEXT)


# endregion


# region Seasonality page
# endregion


# region Alerts page
def format_alerts(alert_rows, keep_order=False):
    """Alerts as a table for the reader, largest movements first."""
    if not keep_order:
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


def find_alert_level(distance):
    """(label, icon, status) of an alert by its distance in standard deviations."""
    return next((label, icon, status) for floor, label, icon, status in ALERT_LEVELS
                if distance >= floor)


def build_alert_list_html(alert_rows, mode):
    """One row per alert: traffic light (icon + label), product, change and how far it
    went beyond its usual range, as a bar with the limit of 2 marked."""
    distances = ((alert_rows["variation"] - alert_rows["usual_variation"]).abs()
                 / alert_rows["variation_deviation"])
    longest = max(distances.max(), alerts.ALERT_DEVIATIONS * 2)
    limit_left = alerts.ALERT_DEVIATIONS / longest * 100
    items = []
    for row, distance in zip(alert_rows.to_dict("records"), distances):
        label, icon, status = find_alert_level(distance)
        change = row["variation"] * 100
        arrow = "▲" if change > 0 else "▼"
        items.append(
            f'<li class="alert-row"><span class="alert-status" style="color:'
            f'{charts.get_status_text_color(status, mode)}">{icon} {label}</span>'
            f'<span class="alert-product">{html.escape(describe_product(row))} · '
            f'{html.escape(row["channel"])}</span>'
            f'<span class="alert-change">{arrow} {charts.format_signed_percent(change)}</span>'
            f'<span class="alert-meter" title="{charts.format_index(distance)} desviaciones '
            f'estándar; el límite es {alerts.ALERT_DEVIATIONS}"><span class="alert-bar" style='
            f'"width:{distance / longest * 100:.1f}%;background:{charts.STATUS_COLORS[status]}">'
            f'</span><span class="alert-limit" style="left:{limit_left:.1f}%"></span></span>'
            f'<span class="alert-distance">{charts.format_index(distance)} desv.</span></li>')
    return f'<ul class="alert-list">{"".join(items)}</ul>'


def show_alerts_tab(mode, filters):
    """K6 as a traffic-light list with how far each change went; the table folded
    (D-059)."""
    alert_rows = read_price_alerts()
    if alert_rows.empty:
        st.info("Todavía no hay semanas suficientes para calcular alertas.")
        return
    weeks = sorted(alert_rows["week_start"].dt.date.unique(), reverse=True)
    report_week = read_filter("week") if st.session_state.get(COMPACT_VIEW) else ALL_VALUES
    if report_week != ALL_VALUES:
        # Inside the report the week comes from its bar (D-069).
        week = pd.Timestamp(report_week).date()
    else:
        week_column, _ = st.columns([1, 4])
        week = week_column.selectbox("Semana (lunes de inicio)", weeks,
                                     format_func=lambda day: day.strftime("%d-%m-%Y"))
    group = read_filter("group") if st.session_state.get(COMPACT_VIEW) else ALL_VALUES
    if group != ALL_VALUES:
        alert_rows = alert_rows[alert_rows["product_group"] == group]
    week_rows = alert_rows[alert_rows["week_start"].dt.date == week]
    distance = ((week_rows["variation"] - week_rows["usual_variation"]).abs()
                / week_rows["variation_deviation"])
    shown_rows = week_rows.loc[distance.sort_values(ascending=False).index]
    control, product_col, channel_col = st.columns([1,2,2])
    shown_count = control.slider("Top N de alertas",8,100,20,key="alerts_top_n")
    selected_product = product_col.selectbox("Producto de la alerta", ["Todos"]+sorted(shown_rows["product"].unique()),key="alerts_product")
    selected_channel = channel_col.selectbox("Canal de la alerta", ["Todos"]+sorted(shown_rows["channel"].unique()),key="alerts_channel")
    if selected_product != "Todos":
        shown_rows = shown_rows[shown_rows["product"] == selected_product]
    if selected_channel != "Todos":
        shown_rows = shown_rows[shown_rows["channel"] == selected_channel]
    st.caption(f"{len(shown_rows)} alertas filtradas · se muestran {min(shown_count,len(shown_rows))}. Alcance nacional: promedio simple de las regiones disponibles, sin ponderación por ventas.")
    with open_card("alert_list", f"Alertas de la semana ({len(week_rows)})",
                   "Primero, los cambios más inusuales. La barra muestra qué tanto se alejan de lo habitual; la marca negra es el umbral de alerta.",
                   hint=ALERT_LIST_HINT, kpi="K6"):
        st.markdown(build_alert_list_html(shown_rows.head(shown_count), mode),
                    unsafe_allow_html=True)
        alert_sample = format_alerts(shown_rows.head(shown_count),keep_order=True)
        alert_sample["Precio anterior"] = (shown_rows.head(shown_count)["national_price"]/(1+shown_rows.head(shown_count)["variation"])).map(lambda v:"$ "+charts.format_thousands(v)).to_numpy()
        show_data_sample(alert_sample[["Producto","Canal","Precio anterior","Precio nacional","Unidad","Variación"]])
        if len(shown_rows) > shown_count:
            st.caption(f"Se muestran las {shown_count} más lejanas; todas están en la tabla "
                       "de abajo. Hay alerta cuando el cambio semanal se aleja más de 2 "
                       "desviaciones estándar de lo habitual en las 12 semanas previas.")
    with st.expander("Ver todas las alertas de la semana en tabla", expanded=False):
        table = format_alerts(shown_rows, keep_order=True)
        table["Precio anterior"] = (shown_rows["national_price"] / (1+shown_rows["variation"])).map(lambda v: "$ " + charts.format_thousands(v)).to_numpy()
        table["Región / alcance"] = "Nacional · regiones disponibles"
        table["Regla"] = "Cambio fuera de media ± 2 desviaciones de las 12 semanas previas"
        st.dataframe(table, hide_index=True, use_container_width=True)
    st.caption(NOMINAL_PRICES_TEXT)


def read_report_week():
    """The week of the report's bar (the latest when none is chosen)."""
    week = read_filter("week")
    return week if week != ALL_VALUES else f"{read_latest_week():%Y-%m-%d}"


def show_analysis_view(mode, title, renderer):
    titles = {PAGE_GAP: "¿Cuánto más cuesta al consumidor?", PAGE_ANALYSIS: "¿Qué precios cambiaron esta semana?",
              PAGE_CHANNELS: "¿Dónde cuesta más el mismo producto?", PAGE_SEASONALITY: "¿Cómo evolucionan los precios?",
              PAGE_ALERTS: "¿Qué cambios conviene revisar?"}
    show_page_header(titles.get(title, title), GRAPH_HELP.get(title, "Precios oficiales de ODEPA."))
    show_reading_guide()
    if renderer in (show_gap_tab, show_week_tab, show_alerts_tab):
        show_report_filters(with_summary_fields=renderer is not show_alerts_tab, include_product=False, include_region=renderer is show_gap_tab)
        if renderer is show_alerts_tab:
            renderer(mode, None)
            return
        if renderer is show_gap_tab:
            st.caption("Ejemplo de lectura: mayorista 1.000 pesos/kg y consumidor 1.300 pesos/kg = 30 % de diferencia. No es ganancia. Las diferencias sobre +300 % se revisan aparte.")
            show_week_gap_ranking(mode)
        else:
            rows = read_week_variations(read_report_week(), read_filter("group"))
            count = st.session_state.get("dashboard_top_n", DEFAULT_TOP_N)
            left, right = st.columns(2)
            with left:
                show_movements_card("week_top_rises", rank_weekly_movements(rows, count, "Alzas"), count, mode, direction="Alzas")
            with right:
                show_movements_card("week_top_falls", rank_weekly_movements(rows, count, "Bajas"), count, mode, direction="Bajas")
            show_group_card("week", read_report_week(), mode)
        st.divider()
        st.subheader("Detalle de un producto")
        filters = choose_analysis_filters()
        if renderer is show_week_tab:
            detail = read_margin_rows(filters)
            if detail.empty:
                st.info(NO_MARGIN_TEXT)
            else:
                show_overview_figures(detail, mode)
                show_week_history(detail, filters, mode)
        else:
            renderer(mode, filters)
        return
    # Placeholder keeps the answer above the optional exploration controls.
    chart_area = st.container()
    st.divider()
    st.subheader("Cambiar el producto del análisis")
    filters = choose_analysis_filters(include_region=False, include_channels=False)
    with chart_area:
        key = filters["key"]
        st.caption("Producto analizado: " + " · ".join(str(key[column]) for column in queries.KEY_COLUMNS) + " · histórico disponible completo")
        renderer(mode, filters)


# region Contexto del precio (D-094)
CONTEXT_CHANNELS = list(charts.CONTEXT_CHANNELS)
CONTEXT_KEY = "context_key"
CONTEXT_DEFAULT = {"product_group": "Hortalizas", "product": "Tomate", "variety": "Larga vida",
                   "quality": "Primera", "normalized_unit": "kilo"}
STATE_CHIPS = {"sobre": ("Sobre lo habitual", "rise"), "dentro": ("Dentro de lo habitual", "neutral"),
               "bajo": ("Bajo lo habitual", "fall"), "sin_historia": ("Sin historia suficiente", "neutral")}


@st.cache_data
def read_context_options(database_version):
    """Products with a street-market or supermarket price: the only ones this page reads."""
    prices = read_cached_national_prices(database_version)
    rows = prices[prices["channel"].isin(CONTEXT_CHANNELS)]
    return rows[queries.KEY_COLUMNS].drop_duplicates().sort_values(queries.KEY_COLUMNS).reset_index(drop=True)


@st.cache_data
def read_dim_date(database_version):
    """The calendar dimension (D-095): ISO week, month and season of every week."""
    rows = queries.run_sql("SELECT week_start, iso_year, iso_week, month, season FROM dim_date")
    return rows.assign(week_start=pd.to_datetime(rows["week_start"]))


def describe_target_week(dates, week):
    """((ISO year, ISO week), month) of week, from dim_date; falls back to week's own."""
    indexed = dates.set_index("week_start")
    if week in indexed.index:
        target = indexed.loc[week]
        return (int(target["iso_year"]), int(target["iso_week"])), int(target["month"])
    return None, week.month


@st.cache_data
def read_context_model(database_version, key_items, week):
    """Everything the page shows for one product, computed once per weekly load."""
    key = dict(key_items)
    prices = read_cached_national_prices(database_version)
    mask = pd.Series(True, index=prices.index)
    for field, value in key.items():
        mask &= prices[field] == value
    product = prices[mask & prices["channel"].isin(CONTEXT_CHANNELS)]
    week = pd.Timestamp(week)
    dates = read_dim_date(database_version)
    target_iso, month = describe_target_week(dates, week)
    # ISO week and month come from dim_date, the calendar of the data warehouse.
    series = {channel: product[product["channel"] == channel][["week_start", "national_price"]]
              .merge(dates, on="week_start", how="left")
              .sort_values("week_start").reset_index(drop=True) for channel in CONTEXT_CHANNELS}
    dates_indexed = dates.set_index("week_start")
    series = {channel: rows for channel, rows in series.items() if not rows.empty}
    weekly = []
    now = {}
    for channel, rows in series.items():
        context = price_context.weekly_context(rows, week, dates=dates_indexed)
        weekly.append(context.assign(channel=channel))
        usual = price_context.rango_habitual(rows, week, target_iso)
        price = rows.loc[rows["week_start"] == week, "national_price"]
        price = float(price.iloc[0]) if not price.empty else None
        now[channel] = {"price": price, "usual": usual,
                        "state": price_context.estado_precio(price, usual) if price is not None else "sin_historia"}
    weekly = pd.concat(weekly, ignore_index=True) if weekly else pd.DataFrame(
        columns=["week_start", "price", "p25", "p75", "state", "channel"])
    # The gap's own habitual range, same ±1-week window; only shown when this
    # week's gap falls outside it (D-098).
    gap_now, gap_state = None, "sin_historia"
    if len(series) == 2:
        gaps = price_context.brecha(series["Feria libre"], series["Supermercado"])
        current = gaps.loc[gaps["week_start"] == week, "gap"]
        gap_now = float(current.iloc[0]) if not current.empty else None
        gap_range = price_context.brecha_rango_habitual(gaps, week, target_iso)
        gap_state = price_context.estado_precio(gap_now, gap_range) if gap_now is not None else "sin_historia"
    seasonal = read_cached_rows_for_key("k4_seasonal_index", tuple(sorted(key.items())), database_version)
    seasonal = seasonal.merge(dates[["week_start", "month"]], on="week_start", how="left")
    year = target_iso[0] if target_iso else week.isocalendar().year
    patterns, years = {}, {}
    for channel in CONTEXT_CHANNELS:
        rows = seasonal[seasonal["channel"] == channel]
        patterns[channel] = price_context.patron_estacional(rows, current_year=year)
        years[channel] = int((rows["price_year"].astype(int) < year).groupby(rows["price_year"]).any().sum())
    return {"series": series, "weekly": weekly, "now": now, "gap_now": gap_now, "gap_state": gap_state,
            "patterns": patterns, "pattern_years": years, "seasonal": seasonal, "month": month}


@st.cache_data
def read_family_outliers(database_version, product_group, week, exclude_product, exclude_variety):
    """Other products of the same family whose price is outside its own habitual range.

    One row per product/channel with a price this week that is «sobre» or «bajo» lo
    habitual (the same ±1 ISO-week rule as the main chart), sorted by how far past
    the limit it is, farthest first (D-098).
    """
    prices = read_cached_national_prices(database_version)
    family = prices[(prices["product_group"] == product_group) & prices["channel"].isin(CONTEXT_CHANNELS)]
    dates = read_dim_date(database_version)
    family = family.merge(dates, on="week_start", how="left")
    week = pd.Timestamp(week)
    target_iso, _ = describe_target_week(dates, week)
    results = []
    group_columns = ["product", "variety", "quality", "normalized_unit", "channel"]
    for key_values, group in family.groupby(group_columns):
        product, variety, quality, unit, channel = key_values
        if product == exclude_product and variety == exclude_variety:
            continue
        current = group.loc[group["week_start"] == week, "national_price"]
        if current.empty or pd.isna(current.iloc[0]):
            continue
        price = float(current.iloc[0])
        usual = price_context.rango_habitual(group, week, target_iso)
        state = price_context.estado_precio(price, usual)
        if state not in ("sobre", "bajo"):
            continue
        low, high, _ = usual
        distance = (price / high - 1) * 100 if state == "sobre" else (1 - price / low) * 100
        results.append({"product": product, "variety": variety, "quality": quality,
                        "normalized_unit": unit, "channel": channel, "price": price,
                        "state": state, "distance": distance})
    rows = pd.DataFrame(results, columns=["product", "variety", "quality", "normalized_unit",
                                          "channel", "price", "state", "distance"])
    return rows.sort_values("distance", ascending=False).head(6).reset_index(drop=True)


def read_context_key(options):
    """The product of the page: a link from the Resumen first, then the last choice."""
    token = st.query_params.get("_home_key")
    if token and st.session_state.get("context_token") != token:
        st.session_state["context_token"] = token
        try:
            payload = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
            key = {field: payload.get(field) for field in queries.KEY_COLUMNS}
            matched = options
            for field, value in key.items():
                matched = matched[matched[field] == value]
            if not matched.empty:
                st.session_state[CONTEXT_KEY] = key
            else:
                st.session_state["context_notice"] = (
                    f"{payload.get('product')} no tiene precios de feria ni de supermercado; "
                    "se muestra otro producto de la misma familia.")
                same = options[options["product_group"] == payload.get("product_group")]
                if not same.empty:
                    st.session_state[CONTEXT_KEY] = same.iloc[0].to_dict()
        except (ValueError, TypeError, UnicodeError):
            pass
    key = st.session_state.get(CONTEXT_KEY)
    if not key or options[(options[list(key)] == pd.Series(key)).all(axis=1)].empty:
        default = options[(options[list(CONTEXT_DEFAULT)] == pd.Series(CONTEXT_DEFAULT)).all(axis=1)]
        key = (default if not default.empty else options).iloc[0].to_dict()
    st.session_state[CONTEXT_KEY] = key
    return key


def choose_context_product(options, key, columns):
    """Familia, producto and calidad · unidad, each limited by the previous choice."""
    def pick(column, label, values, current, render):
        values = list(dict.fromkeys(values))
        index = values.index(current) if current in values else 0
        return column.selectbox(label, values, index=index, format_func=render,
                                key=f"context_{label}_{key['product_group']}_{key['product']}_{key['variety']}")
    group = pick(columns[0], "Familia", options["product_group"], key["product_group"], str)
    rows = options[options["product_group"] == group]
    names = list(zip(rows["product"], rows["variety"]))
    current = (key["product"], key["variety"]) if group == key["product_group"] else names[0]
    product, variety = pick(columns[1], "Producto", names, current,
                            lambda pair: pair[0] if pair[1] == UNSPECIFIED else f"{pair[0]} · {pair[1]}")
    rows = rows[(rows["product"] == product) & (rows["variety"] == variety)]
    pairs = list(zip(rows["quality"], rows["normalized_unit"]))
    current = (key["quality"], key["normalized_unit"]) if (product, variety) == (key["product"], key["variety"]) else pairs[0]
    quality, unit = pick(columns[2], "Calidad · unidad", pairs, current, lambda pair: f"{pair[0]} · {pair[1]}")
    chosen = {"product_group": group, "product": product, "variety": variety,
              "quality": quality, "normalized_unit": unit}
    if chosen != key:
        st.session_state[CONTEXT_KEY] = chosen
        st.rerun()
    return chosen


def describe_context_product(key):
    return key["product"] if key["variety"] == UNSPECIFIED else f"{key['product']} {key['variety'].lower()}"


def build_context_self_link(product_group, row):
    """Address of this same page, with one product of the «Otros productos» table preselected."""
    payload = {"product_group": product_group, "product": row.product, "variety": row.variety,
              "quality": row.quality, "normalized_unit": row.normalized_unit}
    token = base64.urlsafe_b64encode(json.dumps(payload, ensure_ascii=False).encode()).decode()
    address = build_page_address(PAGE_SEASONALITY)
    return address + ("&" if "?" in address else "?") + urlencode({"_home_key": token})


def build_context_price_card(now, unit):
    rows = []
    for channel in CONTEXT_CHANNELS:
        item = now.get(channel)
        color = charts.CONTEXT_CHANNELS[channel]
        if not item:
            rows.append(f'<div class="ctx-price-row"><i style="background:{color}"></i><div><strong>{channel}</strong>'
                        '<small>Sin precios para este producto</small></div><div class="ctx-price"><b>—</b></div></div>')
            continue
        usual = item["usual"]
        habit = (f'Habitual: ${charts.format_thousands(usual[0])} a ${charts.format_thousands(usual[1])}'
                 if usual else 'Habitual: sin historia suficiente')
        label, kind = STATE_CHIPS[item["state"]] if item["price"] is not None else ("Sin precio esta semana", "neutral")
        price = '—' if item["price"] is None else '$' + charts.format_thousands(item["price"])
        rows.append(f'<div class="ctx-price-row"><i style="background:{color}"></i><div><strong>{channel}</strong>'
                    f'<small>{habit}</small></div><div class="ctx-price"><b>{price}</b>'
                    f'<span class="ctx-state {kind}">{label}</span></div></div>')
    hint = build_hint_icon(f"Precio por {unit}. Habitual = percentil 25 a 75 de la misma semana ISO "
                           "(y la semana antes y después) en años anteriores.")
    return (f'<section class="ctx-card"><h3>Precio esta semana{hint}</h3>' + "".join(rows) + '</section>')


def build_context_next_card(patterns, pattern_years, month):
    """3 months × 2 channels, as a compact strip: month, arrow and % change (D-098)."""
    months = [(month - 1 + step) % 12 + 1 for step in range(1, 4)]
    header = "".join(f'<th>{price_context.MONTHS[following - 1][:3].capitalize()}</th>' for following in months)
    channel_rows = []
    any_history = False
    for channel in CONTEXT_CHANNELS:
        years = pattern_years.get(channel, 0)
        pattern = patterns.get(channel, {})
        if years < price_context.MINIMUM_YEARS:
            cells = f'<td colspan="3" class="ctx-next-empty">Sin historia suficiente</td>'
        else:
            any_history = True
            changes = dict(price_context.proximos_meses(pattern, month, count=3))
            cells = ""
            for following in months:
                change = changes.get(following)
                if change is None:
                    cells += '<td>—</td>'
                else:
                    arrow = "▲" if change > 0.05 else "▼" if change < -0.05 else "▬"
                    cells += f'<td class="{"rise" if change > 0.05 else "fall" if change < -0.05 else ""}">' \
                             f'{arrow} {charts.format_percent(abs(change))}</td>'
        color = charts.CONTEXT_CHANNELS[channel]
        channel_rows.append(f'<tr><th><i style="background:{color}"></i>{channel}</th>{cells}</tr>')
    hint = build_hint_icon("Cambio típico del índice estacional frente a este mes, por canal, en años "
                           "anteriores. Es un patrón histórico, no un pronóstico.")
    foot = ("Patrón de años anteriores. No es un pronóstico." if any_history else
            "Sin historia suficiente en ningún canal: hacen falta al menos dos años anteriores.")
    return ('<section class="ctx-card"><h3>Qué suele pasar en las próximas semanas' + hint + '</h3>'
            f'<table class="ctx-next-table"><thead><tr><th></th>{header}</tr></thead>'
            f'<tbody>{"".join(channel_rows)}</tbody></table>'
            f'<div class="ctx-foot">{foot}</div></section>')


def build_context_outliers_table(rows, product_group):
    """«Otros productos de {familia} fuera de lo habitual»: a short, sorted table (D-098)."""
    hint = build_hint_icon("Productos de la misma familia cuyo precio de esta semana, en cualquier "
                           "canal, está fuera de su propio percentil 25 a 75 habitual (misma ventana "
                           "de ±1 semana ISO). Ordenados por qué tan lejos están del límite.")
    title = f'<h3>Otros productos de {html.escape(product_group)} fuera de lo habitual{hint}</h3>'
    if rows.empty:
        return (f'<section class="ctx-card ctx-card-wide">{title}'
                f'<div class="ctx-note">Ningún otro producto de {html.escape(product_group)} está '
                'fuera de lo habitual esta semana.</div></section>')
    body = []
    for row in rows.itertuples():
        label = row.product if row.variety == UNSPECIFIED else f"{row.product} · {row.variety}"
        state_label, kind = STATE_CHIPS[row.state]
        link = html.escape(build_context_self_link(product_group, row))
        body.append('<tr>'
                    f'<td><a href="{link}" target="_self">{html.escape(label)}</a>'
                    f'<small>{html.escape(row.quality)} · $/{html.escape(row.normalized_unit)}</small></td>'
                    f'<td>{html.escape(row.channel)}</td>'
                    f'<td class="num">${charts.format_thousands(row.price)}</td>'
                    f'<td><span class="ctx-state {kind}">{html.escape(state_label)}</span></td>'
                    f'<td class="num">{charts.format_percent(row.distance)}</td></tr>')
    return (f'<section class="ctx-card ctx-card-wide">{title}'
            '<div class="ctx-outlier-scroll"><table class="ctx-outlier-table"><thead><tr>'
            '<th>Producto</th><th>Canal</th><th>Precio actual</th><th>Estado</th>'
            '<th>Distancia al límite</th></tr></thead><tbody>' + "".join(body) + '</tbody></table></div></section>')


@st.dialog("Serie completa", width="large")
def show_full_history_dialog(series, mode, label):
    rows = pd.concat([rows.assign(channel=channel) for channel, rows in series.items()])
    st.caption(f"{label} · {rows['week_start'].min():%d-%m-%Y} a {rows['week_start'].max():%d-%m-%Y} · "
               "precio nacional semanal, sin áreas; las semanas sin dato quedan en blanco.")
    show_chart(charts.draw_full_history(rows, mode))
    st.caption(NOMINAL_PRICES_TEXT)


@st.dialog("Datos del gráfico", width="large")
def show_context_data_dialog(model):
    weekly = model["weekly"].copy()
    table = pd.DataFrame({
        "Semana": weekly["week_start"].dt.strftime("%d-%m-%Y"), "Canal": weekly["channel"],
        "Precio": weekly["price"], "Habitual desde (P25)": weekly["p25"], "Habitual hasta (P75)": weekly["p75"],
        "Estado": weekly["state"].map(lambda value: price_context.STATES.get(value, "sin precio"))})
    st.caption("Últimas 52 semanas. Habitual = P25–P75 de la semana ISO (y la semana antes y después) "
               "en años anteriores (sin el año en curso).")
    st.dataframe(table.sort_values(["Semana", "Canal"], ascending=[False, True]), hide_index=True,
                 use_container_width=True, height=280,
                 column_config={name: st.column_config.NumberColumn(format="$%.0f")
                                for name in ("Precio", "Habitual desde (P25)", "Habitual hasta (P75)")})
    seasonal = model["seasonal"]
    seasonal = seasonal[seasonal["channel"].isin(CONTEXT_CHANNELS)]
    st.caption("Índice estacional semanal (K4): precio de la semana ÷ promedio de su año; 1 = promedio.")
    st.dataframe(pd.DataFrame({"Semana": seasonal["week_start"].dt.strftime("%d-%m-%Y"), "Año": seasonal["price_year"],
                               "Canal": seasonal["channel"], "Índice": seasonal["seasonal_index"].round(3)})
                 .sort_values("Semana", ascending=False), hide_index=True, use_container_width=True, height=220)


def build_context_css(mode):
    palette = charts.get_palette(mode)
    return f"""<style>
    .ctx-crumb {{font-size:12.5px;color:{palette['text']};}} .ctx-crumb a {{color:{palette['accent']}!important;text-decoration:none;}}
    .ctx-crumb b {{color:{palette['strong_text']};}}
    .ctx-back {{display:inline-flex;float:right;padding:5px 12px;border:1px solid {palette['card_border']};border-radius:8px;
        font-size:12.5px;color:{palette['strong_text']}!important;text-decoration:none!important;background:{palette['card']};}}
    .ctx-title h1 {{font-size:21px!important;font-weight:700;margin:0!important;padding:0!important;display:inline;}}
    .ctx-title .page-freshness {{display:inline-flex;gap:6px;margin-left:12px;font-size:12px;}}
    .ctx-answer {{font-size:14px;line-height:1.45;color:{palette['strong_text']};margin:4px 0 0;max-width:900px;}}
    .st-key-ctx_main {{border:1px solid {palette['card_border']};border-radius:12px;background:{palette['card']};padding:10px 16px 4px;}}
    .st-key-ctx_side {{gap:10px;}}
    .st-key-ctx_bottom {{margin-top:10px;}}
    .ctx-head h3, .ctx-card h3 {{font-size:15px!important;font-weight:700;margin:0!important;padding:0!important;
        color:{palette['strong_text']};display:flex;align-items:center;gap:6px;}}
    .ctx-head {{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;}}
    .ctx-keys {{display:flex;gap:14px;font-size:11px;color:{palette['text']};white-space:nowrap;}}
    .ctx-keys i {{display:inline-block;width:14px;height:3px;border-radius:2px;margin-right:5px;vertical-align:middle;}}
    .ctx-keys i.band {{height:9px;background:{palette['grid']};}}
    .ctx-card {{border:1px solid {palette['card_border']};border-radius:12px;background:{palette['card']};padding:12px 16px;}}
    .ctx-card-wide {{padding-bottom:6px;}}
    .ctx-price-row {{display:grid;grid-template-columns:10px 1fr auto;gap:10px;align-items:center;padding:8px 0;border-top:1px solid {palette['card_border']};}}
    .ctx-price-row i {{width:9px;height:9px;border-radius:50%;}}
    .ctx-price-row strong {{display:block;font-size:13px;color:{palette['strong_text']};}}
    .ctx-price-row small {{font-size:11px;color:{palette['text']};}}
    .ctx-price {{text-align:right;}} .ctx-price b {{display:block;font-size:20px;color:{palette['strong_text']};font-variant-numeric:tabular-nums;}}
    .ctx-state {{font-size:11px;font-weight:600;}} .ctx-state.rise {{color:#c0392b;}} .ctx-state.fall {{color:#1f7a4d;}} .ctx-state.neutral {{color:{palette['text']};}}
    .ctx-note {{font-size:12px!important;line-height:1.45;color:{palette['strong_text']};margin:6px 0 0!important;}}
    .ctx-next-table {{width:100%;border-collapse:collapse;margin-top:4px;font-size:12.5px;}}
    .ctx-next-table th, .ctx-next-table td {{padding:6px 4px;text-align:center;border-top:1px solid {palette['card_border']};}}
    .ctx-next-table thead th {{border-top:0;color:{palette['text']};font-weight:500;font-size:11px;}}
    .ctx-next-table tbody th {{text-align:left;font-weight:600;color:{palette['strong_text']};white-space:nowrap;}}
    .ctx-next-table tbody th i {{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;}}
    .ctx-next-table td.rise {{color:#c0392b;}} .ctx-next-table td.fall {{color:#1f7a4d;}}
    .ctx-next-empty {{color:{palette['text']};font-style:italic;}}
    .ctx-foot {{font-size:10.5px;color:{palette['text']};margin:8px 0 0!important;}}
    .ctx-outlier-scroll {{overflow:auto;max-height:230px;}}
    .ctx-outlier-table {{width:100%;min-width:640px;border-collapse:collapse;font-size:12.5px;}}
    .ctx-outlier-table th {{text-align:left;padding:6px 10px;color:{palette['text']};font-weight:500;font-size:11px;
        border-bottom:1px solid {palette['card_border']};}}
    .ctx-outlier-table td {{padding:7px 10px;border-bottom:1px solid {palette['card_border']};color:{palette['strong_text']};}}
    .ctx-outlier-table td a {{color:{palette['accent']}!important;text-decoration:none;font-weight:600;}}
    .ctx-outlier-table td small {{display:block;font-size:10.5px;color:{palette['text']};font-weight:400;}}
    .ctx-outlier-table td.num {{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}}
    .st-key-ctx_links button {{padding:0 4px!important;min-height:0!important;}}
    .st-key-ctx_links button p {{font-size:12px!important;color:{palette['accent']}!important;font-weight:600;}}
    .st-key-ctx_links [data-testid="stCaptionContainer"] p {{font-size:11px!important;}}
    </style>"""


def show_price_context_page(mode):
    """¿El precio de esta semana es normal? One screen, no scroll at 1920×1080 (D-098)."""
    st.markdown(build_context_css(mode), unsafe_allow_html=True)
    version = get_database_version()
    options = read_context_options(version)
    if options.empty:
        st.info(NO_DATA_TEXT)
        return
    key = read_context_key(options)
    week = f"{read_latest_week():%Y-%m-%d}"
    crumb, back = st.columns([5, 1], vertical_alignment="center")
    home = build_page_address(PAGE_HOME)
    home_family = home + ("&" if "?" in home else "?") + urlencode({"familia": key["product_group"]})
    label = describe_context_product(key)
    crumb.markdown(f'<div class="ctx-crumb"><a href="{html.escape(home)}" target="_self">Resumen</a> › '
                   f'<a href="{html.escape(home_family)}" target="_self">{html.escape(key["product_group"])}</a> › '
                   f'<b>{html.escape(label)}</b></div>', unsafe_allow_html=True)
    back.markdown(f'<a class="ctx-back" href="{html.escape(home_family)}" target="_self">← Volver al resumen</a>',
                  unsafe_allow_html=True)
    title, *fields = st.columns([2.6, 0.9, 1.1, 0.9], vertical_alignment="bottom")
    key = choose_context_product(options, key, fields)
    label = describe_context_product(key)
    model = read_context_model(version, tuple(sorted(key.items())), week)
    latest = read_latest_run()
    run_kind = "ok" if latest["status"] == etl.STATUS_LOADED else "failed"
    states = {channel: model["now"][channel]["state"] for channel in CONTEXT_CHANNELS
              if channel in model["now"] and model["now"][channel]["price"] is not None}
    # The gap only earns a mention when it is outside its own habitual range (D-098).
    gap_word = {"sobre": "mayor", "bajo": "menor"}.get(model["gap_state"])
    def wrap(channel, phrase):
        return f'<b style="color:{charts.CONTEXT_CHANNELS.get(channel, "inherit")}">{html.escape(phrase)}</b>'
    sentence = price_context.answer_sentence(html.escape(label.lower()), model["month"], states, gap_word, wrap=wrap)
    title.markdown(f'<div class="ctx-title compact-header"><h1>¿El precio de esta semana es normal?</h1>'
                   f'<span class="page-freshness">Datos al {format_chile_time(parse_run_start(latest["started_at"]))} '
                   f'{build_chip("Carga correcta" if run_kind == "ok" else "Última carga con falla", run_kind)}</span></div>'
                   f'<p class="ctx-answer">{sentence}</p>', unsafe_allow_html=True)
    notice = st.session_state.pop("context_notice", None)
    if notice:
        st.caption(notice)
    left, right = st.columns([3.05, 1], gap="small")
    with left:
        with st.container(key="ctx_main"):
            hint = build_hint_icon("Línea: precio de cada semana. Banda: rango habitual de esa misma semana "
                                   "(y la semana antes y después) en años anteriores, percentil 25 a 75. Si la "
                                   "línea sale de la banda, el precio es inusual.")
            st.markdown(f'<div class="ctx-head"><h3>Últimas 52 semanas frente a lo habitual{hint}</h3>'
                        '<div class="ctx-keys">'
                        + ''.join(f'<span><i style="background:{color}"></i>{channel}</span>'
                                  for channel, color in charts.CONTEXT_CHANNELS.items() if channel in model["series"])
                        + '<span><i class="band"></i>Rango habitual</span></div></div>', unsafe_allow_html=True)
            if model["weekly"].empty:
                st.info("Este producto no tiene precios de feria ni de supermercado.")
            else:
                show_chart(charts.draw_price_context(model["weekly"], mode, height=350))
            with st.container(key="ctx_links", horizontal=True, vertical_alignment="center"):
                missing = int(model["weekly"]["price"].isna().sum()) if not model["weekly"].empty else 0
                st.caption("Precios nominales, sin ajuste por inflación."
                           + (f" {missing} semanas sin dato quedan en blanco; no se interpolan." if missing else ""))
                years = sorted({day.year for rows in model["series"].values() for day in rows["week_start"]})
                span = f"{years[0]}–{years[-1]}" if years else ""
                if st.button(f"Ver serie completa {span} →", key="ctx_full", type="tertiary"):
                    show_full_history_dialog(model["series"], mode, label)
                if st.button("Ver datos del gráfico →", key="ctx_data", type="tertiary"):
                    show_context_data_dialog(model)
    with right, st.container(key="ctx_side"):
        st.markdown(build_context_price_card(model["now"], key["normalized_unit"]), unsafe_allow_html=True)
        st.markdown(build_context_next_card(model["patterns"], model["pattern_years"], model["month"]),
                    unsafe_allow_html=True)
    with st.container(key="ctx_bottom"):
        outliers = read_family_outliers(version, key["product_group"], week, key["product"], key["variety"])
        st.markdown(build_context_outliers_table(outliers, key["product_group"]), unsafe_allow_html=True)
# endregion


def show_analysis_page(mode):
    show_analysis_view(mode, PAGE_ANALYSIS, show_week_tab)


# endregion


# region Control center page
def get_secret(name):
    """A dashboard secret, or None when it is not configured."""
    try:
        return st.secrets.get(name)
    except Exception:  # no secrets file at all
        return None


@st.cache_resource
def get_last_github_answers():
    """Last good answers of GitHub, shared by every visitor, used when GitHub fails."""
    return {}


@st.cache_data(ttl=GITHUB_CACHE_SECONDS, show_spinner=False)
def fetch_pipeline_runs():
    """Latest runs from GitHub. A failure raises, and is not kept in the cache."""
    token = get_secret(SECRET_GITHUB_TOKEN)
    runs = control.list_workflow_runs(token, RUN_HISTORY_COUNT)
    return control.mark_simulated_failures(runs, token)


def read_pipeline_runs():
    """(latest runs, why GitHub failed or ""). On a failure, the last good answer."""
    last_answers = get_last_github_answers()
    try:
        runs = fetch_pipeline_runs()
    except Exception as error:  # GitHub unreachable or refused
        return last_answers.get("runs", []), control.describe_github_error(error)
    last_answers["runs"] = runs
    return runs, ""


def build_run_chip(state):
    """Chip for a pipeline run: Éxito, Falla or En curso."""
    texts = {control.RUN_OK: ("Éxito", "ok"), control.RUN_FAILED: ("Falla", "failed"),
             control.RUN_IN_PROGRESS: ("En curso", "running"),
             control.RUN_SIMULATED_FAILURE: ("Falla simulada (prueba)", "neutral")}
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
            # Without GitHub, the latest load saved in the database is still a fact.
            latest_load = read_latest_run()
            st.markdown(f'<div class="kpi-value">'
                        f'{format_chile_time(parse_run_start(latest_load["started_at"]))}</div>'
                        f'<span class="kpi-note">última carga guardada en la base</span>',
                        unsafe_allow_html=True)
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
                              "en un minuto.", state="error", expanded=True)
            return
        state = follow_run_progress(run["id"], token, st.empty())
        if state == control.RUN_OK:
            status_box.update(label="Listo: datos descargados, revisados y guardados.",
                              state="complete", expanded=True)
            st.success("El panel muestra los datos nuevos en cuanto recibe la base "
                       "guardada, normalmente en 1 o 2 minutos. Usa «Recargar datos».")
        else:
            status_box.update(label="La ejecución terminó con una falla. Los datos anteriores "
                              "siguen intactos.", state="error", expanded=True)
    read_pipeline_runs.clear()


ADMIN_UNLOCKED = "admin_unlocked"
ADMIN_LINKS = project.ADMIN_LINKS


@st.cache_data(ttl=3600, show_spinner=False)
def read_cached_token_expiration(token):
    """Expiration of the token, asked to GitHub at most once an hour."""
    return control.read_token_expiration(token)


def show_token_expiration(token):
    """«Tu token vence en X días», highlighted under 14 days. Never the token itself."""
    try:
        expiration = read_cached_token_expiration(token)
    except Exception as error:  # GitHub unreachable or the token was refused
        st.warning(f"No se pudo leer el vencimiento del token: "
                   f"{control.describe_github_error(error)}.")
        return
    sentence, is_urgent = control.describe_token_expiration(expiration,
                                                            datetime.now(timezone.utc))
    if is_urgent:
        st.warning(sentence, icon=":material/schedule:")
    else:
        st.caption(sentence)


def show_admin_unlocked(token):
    """What the control code opens: admin links, token expiration and «Ejecutar ahora»."""
    show_link_cards(ADMIN_LINKS)
    if not token:
        st.info("«Ejecutar ahora» se activa cuando el autor guarda su token de GitHub en "
                "los secretos del panel («Crear token», arriba).")
        return
    show_token_expiration(token)
    if st.button("Ejecutar ahora", type="primary", icon=":material/play_arrow:",
                 help="Descarga los datos de ODEPA, los limpia, los prueba y actualiza el "
                      "panel. Tarda alrededor de un minuto."):
        run_pipeline_now(token)


def show_admin_card():
    """Administration, behind the control code: nothing of it shows without the code."""
    with open_card("admin", "🔒 Administración"):
        access_code = get_secret(SECRET_CONTROL_CODE)
        if st.session_state.get(ADMIN_UNLOCKED) and access_code:
            show_admin_unlocked(get_secret(SECRET_GITHUB_TOKEN))
            return
        st.markdown('<div class="admin-locked">Requiere clave de control.</div>',
                    unsafe_allow_html=True)
        if not access_code:
            st.caption("Se activa cuando el autor guarda la clave de control en los "
                       "secretos del panel.")
            return
        typed_code = st.text_input("Clave de control", type="password")
        if st.button("Desbloquear", icon=":material/lock_open:"):
            if hmac.compare_digest(typed_code, access_code):
                st.session_state[ADMIN_UNLOCKED] = True
                st.rerun()
            st.error("Clave incorrecta.")


def show_run_history(runs, error_text):
    """Card: latest pipeline runs with their state."""
    with open_card("run_history", "Historial de ejecuciones"):
        if error_text:
            # The real cause, so a failure can be diagnosed from the public panel.
            st.warning(f"No se pudo consultar GitHub: {error_text}.")
            if not runs:
                return
            st.caption("Se muestra la última respuesta guardada.")
        table_rows = [[format_chile_time(run["started_at"]), html.escape(run["trigger"]),
                       format_duration(run["duration"]) if run["duration"] else "—",
                       build_run_chip(run["state"]),
                       f'<a href="{html.escape(run["url"])}">Ver en GitHub ↗</a>']
                      for run in runs]
        show_foldable_table(build_html_table(["Inicio", "Tipo", "Duración", "Estado", ""],
                                     table_rows), 'Ver historial de ejecuciones')


def show_runs_tab(mode):
    """The weekly pipeline: its state, its history and, behind the control code, the
    button to run it now and the administration links."""
    show_section_intro("Ejecuciones", "El estado del job semanal: la última ejecución, la "
                       "próxima, la última carga y el historial. Con la clave de control se "
                       "puede lanzar ahora.")
    runs, error_text = read_pipeline_runs()
    show_pipeline_status(runs)
    run_column, history_column = st.columns([2, 3])
    with run_column:
        show_admin_card()
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


@st.cache_data(ttl=GITHUB_CACHE_SECONDS, show_spinner=False)
def fetch_run_steps(run_id):
    """Steps of one run from GitHub. A failure raises, and is not kept in the cache."""
    return dict(control.list_run_steps(run_id, get_secret(SECRET_GITHUB_TOKEN)))


def read_latest_pipeline_steps():
    """(state of each step by Spanish name, latest run, why GitHub failed or "").

    Without an answer from GitHub the steps are {} and the diagram takes its
    states from the database (build_journey_states).
    """
    runs, error_text = read_pipeline_runs()
    if not runs:
        return {}, None, error_text
    last_answers = get_last_github_answers()
    try:
        steps = fetch_run_steps(runs[0]["id"])
    except Exception as error:  # GitHub unreachable or refused
        steps = last_answers.get(("steps", runs[0]["id"]), {})
        return steps, runs[0], error_text or control.describe_github_error(error)
    last_answers[("steps", runs[0]["id"])] = steps
    return steps, runs[0], error_text


def get_step_state(step_states, workflow_step):
    """State of one workflow step, by its name in semanal.yml."""
    return step_states.get(control.STEP_NAMES[workflow_step], architecture.STATE_UNKNOWN)


def read_step_state(step_states, workflow_step, load_state):
    """State of one step: from GitHub, or from the latest saved load when GitHub did
    not answer (only for the steps a saved load proves passed)."""
    if step_states:
        return get_step_state(step_states, workflow_step)
    if workflow_step in STEPS_PROVED_BY_A_SAVED_LOAD:
        return load_state
    return architecture.STATE_UNKNOWN


def build_journey_states(step_states, pipeline_run, latest_load, manifest):
    """Real state of each step: from the latest pipeline run and the current database.

    Without an answer from GitHub, the latest load saved in etl_run stands in: the
    database is only saved after download, ETL and tests passed (D-034). What the
    database cannot tell (the report, the workflow itself) stays unknown, and an
    unknown state is drawn without a dot.
    """
    load_state = (control.RUN_OK if latest_load["status"] == etl.STATUS_LOADED
                  else control.RUN_FAILED)
    return {
        "sources": control.RUN_OK if manifest else architecture.STATE_UNKNOWN,
        "download": read_step_state(step_states, "Download the ODEPA files", load_state),
        "etl": read_step_state(step_states, "Run the ETL", load_state),
        "tests": read_step_state(step_states, "Run the tests against the new database",
                                 load_state),
        "report": read_step_state(step_states, "Publish the weekly report", load_state),
        "workflow": pipeline_run["state"] if pipeline_run else architecture.STATE_UNKNOWN,
        "load": load_state,
        "etl_run": load_state,
        "panel": control.RUN_OK,
    }


def build_journey_figures(manifest, pipeline_run, latest_load):
    """Short texts shown under the steps, all from real data."""
    weekly_prices = read_indicator("quality_flag_counts")["weekly_prices"].sum()
    latest_week = read_latest_week()
    loaded_at = to_chile_time(parse_run_start(latest_load["started_at"]))
    next_run = control.calculate_next_scheduled_run(datetime.now(timezone.utc))
    last_run = (f"última {to_chile_time(pipeline_run['started_at']):%d-%m %H:%M}"
                if pipeline_run else "sin datos del workflow")
    return {
        "source_years": describe_loaded_years(),
        "last_run": last_run,
        "rows_read": f"{charts.format_thousands(latest_load['rows_read'])} filas leídas",
        "rows_rejected": f"{charts.format_thousands(latest_load['rows_rejected'])} filas",
        "weekly_prices": f"{charts.format_thousands(weekly_prices)} precios",
        "latest_week": f"hasta {latest_week:%d-%m-%Y}",
        "panel_time": f"datos al {loaded_at:%d-%m %H:%M}",
        "next_run": f"{to_chile_time(next_run):%d-%m %H:%M}",
    }


def describe_last_run_time(pipeline_run, latest_load):
    """Date and time of the latest pipeline run; without GitHub, of the latest saved load."""
    if pipeline_run:
        return format_chile_time(pipeline_run["started_at"])
    return format_chile_time(parse_run_start(latest_load["started_at"]))


def build_run_status_html(states, pipeline_run, latest_load):
    """«Estado de la última ejecución (date) · se actualiza al recargar la página»."""
    word, kind = summarize_journey_state(states)
    return (f'<div class="run-status">{build_chip(word, kind)} Estado de la última '
            f'ejecución ({describe_last_run_time(pipeline_run, latest_load)}) · se actualiza '
            'al recargar la página</div>')


def read_journey():
    """(states, figures, pipeline run, latest load, GitHub error) of the live diagram."""
    with st.spinner("Consultando el estado del pipeline…"):
        step_states, pipeline_run, error_text = read_latest_pipeline_steps()
    latest_load = read_latest_run()
    manifest = read_download_manifest()
    states = build_journey_states(step_states, pipeline_run, latest_load, manifest)
    figures = build_journey_figures(manifest, pipeline_run, latest_load)
    error_note = (describe_state_source(error_text, step_states, latest_load)
                  if error_text else None)
    return states, figures, pipeline_run, latest_load, error_note


def format_architecture_note(column, text):
    """The note of an architecture card: a file by its name (whole path on hover), a
    place of the panel as a named link, or plain text."""
    if text in PAGE_PATHS or text in PAGE_OF_TAB:
        return build_place_link(text)
    if project.is_in_repository(text):
        return (f'{html.escape(column)}: <code title="{html.escape(text)}">'
                f'{html.escape(text.rstrip("/").split("/")[-1])}</code>')
    return f"{html.escape(column)}: {format_inline(text)}"


def show_architecture_group(heading, lead, title_column, text_column, note_column):
    """Technical details as compact rows, rather than oversized uniform cards."""
    show_section_intro(heading, lead, True)
    kind = {"Seguridad": "security", "DevOps": "workflow",
            "Observabilidad": "chart", "Informes": "document"}[heading]
    rows = ''.join(f'<li>{build_component_symbol(kind)}<div>'
        f'<strong>{html.escape(row[title_column])}</strong>'
        f'<p>{format_inline(row[text_column])}</p>'
        f'<span class="kpi-note">{format_architecture_note(note_column, row[note_column])}</span>'
        '</div></li>' for row in project.read_guide_table(heading))
    st.markdown(f'<ul class="technical-rows">{rows}</ul>', unsafe_allow_html=True)


def build_journey_legend_html():
    """What the colored dot of each step and the moving arrows mean."""
    return (f'{build_chip("OK", "ok")} {build_chip("En curso", "running")} '
            f'{build_chip("Falla", "failed")} {build_chip("Sin datos", "neutral")}'
            '<div class="kpi-note" style="margin-top:8px">Punto de color en cada '
            'paso: estado de la última ejecución del pipeline y de la base actual. '
            'El movimiento ilustrativo, no actividad en vivo, muestra el recorrido; '
            'el estado identifica la ejecución real.</div>')


def show_pipeline_tab(mode, animate_flow=False, journey=None):
    """The detailed live diagram of the data, from ODEPA to the dashboard."""
    states, figures, pipeline_run, latest_load, error_note = journey or read_journey()
    with open_card("journey", "Recorrido completo por capas", hint=ARCHITECTURE_HINT):
        st.markdown(build_run_status_html(states, pipeline_run, latest_load),
                    unsafe_allow_html=True)
        if error_note:
            st.caption(error_note)
        # Inline SVG (not an image), so each piece shows its explanation on hover.
        st.markdown(zoom.build_zoom_frame_html(
                        architecture.build_journey_svg(states, figures, mode, animate_flow=animate_flow), "diagram-wide")
                    + zoom.build_zoom_frame_html(
                        architecture.build_vertical_journey_svg(states, figures, mode, animate_flow=animate_flow),
                        "diagram-narrow"), unsafe_allow_html=True)
        st.markdown(build_journey_legend_html(), unsafe_allow_html=True)


def build_devops_figures(figures):
    """The pipeline figures plus the size of datos.db, the test functions and the
    prices of the latest week (what the weekly job added), all read now."""
    latest_week = read_latest_week()
    week_prices = project.count_week_prices(f"{latest_week:%Y-%m-%d}")
    return dict(figures, database_size=project.describe_file_size(queries.DATABASE_FILE),
                test_functions=f"{project.count_test_functions()} funciones de prueba",
                week_prices=(f"semana {latest_week:%d-%m}: "
                             f"{charts.format_thousands(week_prices)} precios"))


def show_infrastructure_diagram(mode, animate_flow=False, journey=None):
    states, figures, pipeline_run, latest_load, error_note = journey or read_journey()
    with open_card("devops_diagram", "Arquitectura por plataforma", hint=DEVOPS_HINT):
        st.markdown(zoom.build_zoom_frame_html(
            architecture.build_devops_svg(states, build_devops_figures(figures), mode, animate_flow=animate_flow),
            "diagram-devops"),
            unsafe_allow_html=True)


def show_devops_tab(mode):
    """Compact lifecycle with real tool logos; deployment topology remains unique."""
    states, figures, pipeline_run, latest_load, error_note = read_journey()
    st.caption("Responsabilidades de mantenimiento: código, pruebas, cargas, publicación y seguimiento. Este ciclo no representa el orden de ejecución de una carga; ese recorrido está en Pipeline.")
    animate = st.toggle("Animar el ciclo DevOps", value=True, key="animate_devops_cycle")
    st.markdown(devops.build_html(states, mode, animate), unsafe_allow_html=True)
    st.caption("El movimiento ilustra el ciclo de trabajo. Los puntos de estado muestran "
               "la última evidencia disponible; no afirman que haya una ejecución en curso.")
    st.markdown(build_link_html("Ver el pipeline y la arquitectura →",
                                build_page_address(PAGE_DIAGRAMS)), unsafe_allow_html=True)
    with st.expander("Ver coste, capacidad, seguridad y observabilidad", expanded=False):
        st.subheader("Coste y capacidad")
        st.markdown("SQLite permite almacenar los datos sin un servidor de base de datos dedicado. GitHub Actions coordina las ejecuciones y Streamlit publica el panel. "
                    "La capacidad depende del volumen, la duración de las cargas y las cuotas de cada servicio. La arquitectura debe revisarse antes de aumentar la frecuencia o incorporar fuentes de mayor tamaño.")
        for group in ARCHITECTURE_GROUPS:
            show_architecture_group(*group)
            if group[0] == "DevOps":
                st.markdown(f'<div class="info-note">Próxima ejecución automática: '
                            f'{figures["next_run"]}.</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-note">El enlace a los informes semanales está en '
                    f'{build_place_link(PAGE_LINKS, "la página")}.</div>', unsafe_allow_html=True)


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
    """Card: match coverage (K7)."""
    keys_with_margin, consumer_keys = read_match_coverage()
    with open_card("quality_details", "Cobertura del cruce", kpi="K7"):
        st.markdown(f'<div class="kpi-value">{keys_with_margin} de {consumer_keys}</div>'
                    f'<div class="kpi-note">claves de frutas y verduras del consumidor tienen '
                    f'margen ({charts.format_percent(keys_with_margin / consumer_keys * 100)})'
                    f'</div>', unsafe_allow_html=True)


def describe_reasons(rejections):
    """«NON_POSITIVE_PRICE (201): un precio … es cero o negativo», one per reason."""
    return "; ".join(f"{row['reason']} ({charts.format_thousands(row['rejected_rows'])}): "
                     f"{REASON_TEXTS.get(row['reason'], 'motivo sin descripción')}"
                     for row in rejections.to_dict("records"))


def build_excluded_cards(latest_run, rejections, flag_totals):
    """What was left out of the indicators, and why: rejected, outliers, no unit."""
    rejected = int(rejections["rejected_rows"].sum()) if not rejections.empty else 0
    share = charts.format_percent(rejected / latest_run["rows_read"] * 100, decimals=3)
    rejected_text = (f"{charts.format_thousands(rejected)} de "
                     f"{charts.format_thousands(latest_run['rows_read'])} filas leídas ({share}). "
                     + (f"Motivo: {describe_reasons(rejections)}." if rejected
                        else "La última ejecución no rechazó filas."))
    outliers = int(flag_totals.get(etl.FLAG_OUTLIER, 0))
    unconvertible = int(flag_totals.get(etl.FLAG_UNIT_NOT_CONVERTIBLE, 0))
    return [
        build_info_card_html("Filas rechazadas", rejected_text, label="RN-11 · no se cargan",
                             note="Se guardan tal como venían en la tabla `rejection`; nunca "
                                  "se borran en silencio.", is_warning=True),
        build_info_card_html("Precios atípicos", f"{charts.format_thousands(outliers)} precios "
                             "semanales a más de 5 veces, o menos de 1/5, de la mediana de su "
                             "producto esa semana.", label="RN-12 · fuera de los indicadores",
                             note="Siguen en `weekly_price` con la marca `ATIPICO`."),
        build_info_card_html("Unidad no convertible", f"{charts.format_thousands(unconvertible)}"
                             " precios semanales en unidades con un rango o sin cantidad "
                             "declarada (un atado de 1,5 a 2 kilos, una docena de atados): no "
                             "se pueden llevar a kilo ni a unidad.",
                             label="RN-05 · sin precio comparable",
                             note="Siguen en `weekly_price` con la marca "
                                  "`UNIDAD_NO_CONVERTIBLE`, sin margen."),
    ]


def build_rejected_rows_table(rejected_rows):
    """The rejected rows as ODEPA sent them, with readable columns in Spanish."""
    records = []
    for row in rejected_rows.to_dict("records"):
        original = json.loads(row["original_row"])
        record = {"Fuente": SOURCE_NAMES.get(row["source"], row["source"]),
                  "Motivo": row["reason"]}
        record.update({label: original[key] for key, label in REJECTED_ROW_LABELS.items()
                       if key in original})
        records.append(record)
    return pd.DataFrame(records)


def format_outliers(outliers):
    """The outliers with readable columns in Spanish."""
    outliers = outliers.drop(columns="key_label").copy()
    outliers["week_start"] = outliers["week_start"].dt.strftime("%d-%m-%Y")
    outliers["source"] = outliers["source"].map(SOURCE_NAMES)
    outliers.columns = ["Semana", "Fuente", "Canal", "Región", "Producto", "Variedad",
                        "Calidad", "Unidad", "Precio", "Observaciones"]
    return outliers


def show_excluded_rows(latest_run):
    """Which rows were left out, why, and the rows themselves folded."""
    rejections = read_indicator("k8_rejected_rows")
    flag_totals = read_indicator("quality_flag_counts").groupby("flag")["weekly_prices"].sum()
    show_section_intro("Qué quedó fuera y por qué", "Tres grupos de datos que no entran a los "
                       "indicadores; ninguno se borra.", True)
    show_info_cards(build_excluded_cards(latest_run, rejections, flag_totals))
    rejected_rows = build_rejected_rows_table(read_indicator("quality_rejected_rows"))
    with st.expander(f"Ver las {charts.format_thousands(len(rejected_rows))} filas rechazadas, "
                     "tal como venían", expanded=False):
        if rejected_rows.empty:
            st.info("La última ejecución no rechazó filas.")
        else:
            reasons = sorted(rejected_rows["Motivo"].unique())
            if len(reasons) > 1:
                reason = st.selectbox("Motivo", reasons, key="rejected_reason")
                rejected_rows = rejected_rows[rejected_rows["Motivo"] == reason]
            st.dataframe(rejected_rows, hide_index=True)
    outliers = format_outliers(read_indicator("quality_outliers"))
    with st.expander(f"Ver los {charts.format_thousands(len(outliers))} precios atípicos", expanded=False):
        st.dataframe(outliers, hide_index=True)
    units = read_indicator("quality_unconvertible_units")
    units["source"] = units["source"].map(SOURCE_NAMES)
    units.columns = ["Fuente", "Canal", "Producto", "Variedad", "Calidad", "Precios semanales"]
    with st.expander("Ver los precios con unidad no convertible, por producto", expanded=False):
        st.dataframe(units, hide_index=True)
    st.caption("Consultas: `quality_rejected_rows`, `quality_outliers` y "
               "`quality_unconvertible_units` en `bi/queries.sql`.")


def show_quality_tab(mode):
    """What the latest load read and kept, then what was left out and why (D-057)."""
    show_section_intro("Calidad de datos", "Qué se cargó en la última ejecución, qué quedó "
                       "fuera y por qué.")
    latest_run = read_latest_run()
    show_load_figures(latest_run)
    donut_column, details_column = st.columns([3, 2])
    with donut_column:
        show_flag_donut(mode)
    with details_column:
        show_quality_details()
    show_excluded_rows(latest_run)


@st.cache_data(ttl=300, show_spinner=False)
def read_quality_evidence(database_version, manifest_text, file_versions):
    """Invalidate checks when either the database, manifest or local source files change."""
    return quality.check_database(), quality.check_source_files(json.loads(manifest_text), MANIFEST_FILE.parent)


def show_operations_page(mode):
    """Evidence first: implemented checks, independently checked storage, pending audits."""
    show_page_header("Calidad y trazabilidad", "Origen, controles y evidencia disponible de los datos que alimentan el panel.")
    manifest = read_download_manifest()
    versions = tuple((path.name, path.stat().st_size, path.stat().st_mtime_ns)
                     for path in sorted(MANIFEST_FILE.parent.glob("*.csv")))
    checks, files = read_quality_evidence(get_database_version(), json.dumps(manifest, sort_keys=True), versions)
    run = read_latest_run()
    database_ok = checks["integrity_ok"] and not any(checks[key] for key in ("foreign_keys", "duplicates", "invalid"))
    matching = sum(item["status"].startswith("Verificado") for item in files)
    failed = sum(item["status"].startswith("Falla") for item in files)
    source_state = "Falla detectada" if failed else "Verificado" if files and matching == len(files) else "Pendiente de comprobación"
    rows = [
        ["Origen y archivos", "Registro disponible" if manifest else "Sin registro disponible", f"{len(files)} archivos registrados en manifest.json, con fecha y huella SHA-256. Esto identifica las descargas; no certifica cada precio."],
        ["Integridad de archivos originales", source_state, f"{matching} de {len(files)} archivos locales coinciden con su huella; {failed} discrepancias. Los archivos ausentes no se consideran verificados."],
        ["Última carga registrada", "Superada" if run["status"] == etl.STATUS_LOADED else "Falla registrada", f"Ejecución {run['run_id']} · {format_chile_time(parse_run_start(run['started_at']))} (Chile) · estado {run['status']}. Es evidencia de la carga guardada, no del último intento remoto."],
        ["Comprobación de la base actual", "Verificado · alcance limitado" if database_ok else "Falla detectada", f"SQLite: {'correcto' if checks['integrity_ok'] else 'error'}; referencias inválidas: {checks['foreign_keys']}; claves duplicadas: {checks['duplicates']}; precios utilizables con formato inválido: {checks['invalid']}."],
        ["Cobertura temporal", "Disponible", f"{checks['weeks']} semanas, desde {checks['first']} hasta {checks['last']}. Es cobertura registrada, no confirmación de que la fuente esté al día."],
        ["Reconciliación fuente → base", "Pendiente", "Falta contrastar los precios originales y sus unidades con la transformación y los agregados almacenados."],
        ["Recálculo independiente de indicadores", "Pendiente", "Las pruebas de software no sustituyen una reconciliación independiente de todos los indicadores contra la fuente."],
        ["Concordancia cálculo → pantalla", "Pendiente", "Falta documentar una muestra auditada con producto, región, canal, periodo y valor mostrado."],
        ["Contraste con otra fuente", "Pendiente", "No hay una comparación independiente de precios con otra fuente equivalente."],
    ]
    st.markdown(build_html_table(["Control", "Estado", "Evidencia y alcance"], rows), unsafe_allow_html=True)
    st.caption("Comprobación local de la base: " + format_chile_time(datetime.fromisoformat(checks["checked_at"])) + " (Chile). Se actualiza al cambiar los archivos o, como máximo, cada cinco minutos al consultar esta vista.")
    if not database_ok or failed:
        st.error("Se detectó una discrepancia en los controles locales. Revisa la evidencia antes de utilizar los resultados.")
    st.info("La carga aplica controles de calidad. La auditoría completa de origen a pantalla sigue pendiente; no se declara una garantía absoluta de exactitud.")
    with st.expander("Ver evidencia de los archivos originales", expanded=False):
        if files:
            st.dataframe(pd.DataFrame(files).rename(columns={"file": "Archivo", "status": "Comprobación", "expected": "SHA-256 registrado", "actual": "SHA-256 comprobado", "downloaded_at": "Fecha registrada"}), hide_index=True, width="stretch")
        else:
            st.info("No hay manifiesto de descargas disponible.")
    st.markdown(build_link_html("Ver ejecuciones del pipeline →", build_page_address(PAGE_RUNS)), unsafe_allow_html=True)
    show_quality_tab(mode)


# endregion


# region Links page
def build_resource_row(link):
    """One link: a page of the panel opens here; an outside service says where it goes
    (↗) and opens in the same window (D-070)."""
    if link.get("page"):
        inside = build_link_html(f"Leer {link['name']} en el panel", build_page_address(
            link["page"]))
        return (f'<li>{inside}<span>{html.escape(link["description"])} · '
                f'<a href="{html.escape(link["url"], quote=True)}" target="_self" rel="noopener">'
                f'ver el original en GitHub ↗</a></span></li>')
    return (f'<li><a href="{html.escape(link["url"], quote=True)}" target="_self" rel="noopener noreferrer">'
            f'{html.escape(link["name"])} ↗</a><span>{html.escape(link["description"])}'
            '</span></li>')


DOC_PROFILES = {
    "BI": (PAGE_DOC_BI, "Qué mide el negocio: los indicadores y su alcance."),
    "BA": (PAGE_DOC_BA, "Qué problema resuelve el proyecto, su misión y su alcance."),
    "IT": (PAGE_DOC_IT, "Las decisiones técnicas clave y cómo opera cada semana."),
}


def build_business_frame_lookup():
    """{Elemento → Definición} of the business frame («Marco de negocio»), read once."""
    return {row["Elemento"]: row["Definición"] for row in project.read_guide_table("Marco de negocio")}


def build_doc_profile_css(mode):
    """Typography for a profile page: a label line per field, a muted paragraph under
    it, generous spacing and a hairline between fields — the reading rhythm of a
    product spec sheet instead of inline bold labels in a run of text (D-111)."""
    palette = charts.get_palette(mode)
    return f"""<style>
    .doc-profile {{max-width:720px;}}
    .doc-profile:has(.doc-kpi-grid) {{max-width:960px;}}
    .doc-field {{padding:22px 0; border-top:1px solid {palette['card_border']};}}
    .doc-field:first-child {{border-top:0; padding-top:4px;}}
    .doc-field-label {{font-size:1.05rem; font-weight:650; letter-spacing:-.015em;
        color:{palette['strong_text']}; margin-bottom:7px;}}
    .doc-field-text {{font-size:.98rem; line-height:1.65; color:{palette['text']};}}
    .doc-field-text code {{word-break:break-word;}}
    /* A floating gallery, not a flat list: each KPI its own elevated card, lifting
       further on hover — the opposite of the tinted, flush rows this replaces. */
    .doc-kpi-grid {{display:grid; grid-template-columns:repeat(auto-fill, minmax(230px, 1fr));
        gap:18px; margin-top:10px;}}
    .doc-kpi-row {{display:flex; flex-direction:column; align-items:flex-start; gap:4px;
        padding:20px; border-radius:18px; background:{palette['card']};
        border:1px solid {palette['card_border']};
        box-shadow:0 14px 28px -14px color-mix(in srgb, var(--kpi-color) 55%, #0003),
                   0 2px 7px -2px rgba(0,0,0,.14);
        transition:transform .16s ease, box-shadow .16s ease;}}
    .doc-kpi-row:hover {{transform:translateY(-5px);
        box-shadow:0 22px 36px -14px color-mix(in srgb, var(--kpi-color) 60%, #0003),
                   0 4px 10px -2px rgba(0,0,0,.16);}}
    .doc-kpi-icon {{display:flex; align-items:center; justify-content:center;
        width:48px; height:48px; border-radius:13px; margin-bottom:4px;
        background:color-mix(in srgb, var(--kpi-color) 16%, transparent); color:var(--kpi-color);}}
    .doc-kpi-icon .component-symbol {{width:26px; height:28px; margin:0; color:inherit;}}
    .doc-kpi-name {{font-weight:650; color:{palette['strong_text']};}}
    .doc-kpi-code {{font-weight:600; color:var(--kpi-color); font-size:.78rem;
        margin-left:8px; letter-spacing:.02em;}}
    .doc-kpi-text {{font-size:.9rem; line-height:1.55; color:{palette['text']}; margin-top:2px;}}
    .doc-profile-link {{display:inline-block; margin-top:26px; font-size:.95rem;}}
    .doc-github-link {{display:inline-flex; align-items:center;}}
    .doc-github-icon {{margin-right:6px;}}
    .doc-decisions {{display:flex; flex-direction:column; gap:8px; margin-top:10px;}}
    .doc-decision {{font-size:.95rem; line-height:1.55; color:{palette['text']};}}
    .doc-decision-id {{font-weight:650; color:{palette['accent']}; margin-right:4px;}}
    </style>"""


def build_doc_field_html(label, text):
    return (f'<div class="doc-field"><div class="doc-field-label">{html.escape(label)}</div>'
            f'<div class="doc-field-text">{format_inline(text)}</div></div>')


# A distinct color per KPI (D-114), reusing the same eight hues the pipeline
# diagrams already use for their layers — one visual language across the panel.
KPI_COLORS = [color for layer, color in architecture.LAYER_COLORS.items() if layer != "orchestration"]


def build_doc_kpi_row_html(kpi, name, icon, text, color):
    return (f'<div class="doc-kpi-row" style="--kpi-color:{color}">'
            f'<span class="doc-kpi-icon">{build_component_symbol(icon)}</span>'
            f'<div class="doc-kpi-name">{html.escape(name)}'
            f'<span class="doc-kpi-code">{kpi}</span></div>'
            f'<div class="doc-kpi-text">{html.escape(text)}</div></div>')


def show_doc_bi_body(frame, mode):
    """What a BI reader needs: the eight indicators and the data they cover, never SQL.
    Each one real — the same name, icon and description used across the panel — in
    its own colored row instead of a link out to another page (D-114)."""
    st.markdown(build_doc_profile_css(mode), unsafe_allow_html=True)
    rows = "".join(build_doc_kpi_row_html(kpi, name, icon, text, color) for (kpi, (name, icon, text)),
                   color in zip(KPI_PRESENTATION.items(), KPI_COLORS))
    st.markdown('<div class="doc-profile">'
                + build_doc_field_html("Alcance de los datos", frame["Alcance"])
                + '<div class="doc-field"><div class="doc-field-label">Los ocho indicadores'
                f'</div><div class="doc-kpi-grid">{rows}</div></div></div>',
                unsafe_allow_html=True)


def show_doc_ba_body(frame, mode):
    """What a BA reader needs: mission, vision and scope, in the business's own words
    — the whole «Marco de negocio» table, not a subset with a link to the rest
    (D-115): the link opened a page repeating the same fields."""
    st.markdown(build_doc_profile_css(mode), unsafe_allow_html=True)
    fields = "".join(build_doc_field_html(element, frame[element]) for element in
                     ["Misión", "Visión", "Objetivo de negocio", "Alcance", "Fuera de alcance",
                      "Criterios de aceptación"])
    st.markdown(f'<div class="doc-profile">{fields}</div>', unsafe_allow_html=True)


def describe_weekly_run():
    """What the weekly job does, in one sentence: the lead of «Qué pasa cada martes»,
    trimmed before its «Hace, en orden:» list so it never ends mid-thought (D-111)."""
    manual = project.read_document(project.MANUAL_FILE)
    lead = project.read_paragraphs(project.read_section(manual, "Qué pasa cada martes"))[0]
    return lead.split(". Hace, en orden:")[0].rstrip(".") + "."


def read_key_decision_sentences():
    """{D-ID → the real sentence of its «Decisión:» field}, for every decision cited
    by KEY_DECISIONS — what was actually decided, not just its category (D-112)."""
    decisions = dict(project.list_decisions())
    sentences = {}
    for _, _, ids in KEY_DECISIONS:
        for identifier in ids:
            title = next(heading for heading in decisions if heading.startswith(f"{identifier} ·"))
            fields = dict(project.parse_labeled_items(decisions[title]))
            sentences[identifier] = capitalize_first(read_first_sentence(fields["Decisión"]))
    return sentences


def build_doc_decision_field_html(group, lead, ids, sentences):
    """One KEY_DECISIONS group as a field: its category, then each real decision
    sentence with its D-ID, so the page says what was decided, not only its theme."""
    items = "".join(
        f'<div class="doc-decision"><span class="doc-decision-id">{identifier}</span> '
        f'{format_inline(sentences[identifier])}</div>' for identifier in ids)
    return (f'<div class="doc-field"><div class="doc-field-label">{html.escape(group)}</div>'
            f'<div class="doc-field-text">{format_inline(lead)}</div>'
            f'<div class="doc-decisions">{items}</div></div>')


def show_doc_it_body(mode):
    """What an IT reader needs: why the system is built this way, with the real
    decisions behind it — no code or SQL; the repository already shows both,
    commit by commit."""
    st.markdown(build_doc_profile_css(mode), unsafe_allow_html=True)
    sentences = read_key_decision_sentences()
    decisions = "".join(build_doc_decision_field_html(group, lead, ids, sentences)
                        for group, lead, ids in KEY_DECISIONS)
    st.markdown(f'<div class="doc-profile">{decisions}'
                + build_doc_field_html("Operación semanal", describe_weekly_run())
                + '</div>', unsafe_allow_html=True)
    st.markdown('<div class="doc-profile-link">' + build_github_link_html(
        "Ver el registro completo de decisiones",
        f"{project.GITHUB_URL}/blob/main/docs/DECISIONES.md") + '</div>', unsafe_allow_html=True)


def show_documentation_bi_page(mode):
    show_page_header(*DOC_PROFILES["BI"])
    show_doc_bi_body(build_business_frame_lookup(), mode)


def show_documentation_ba_page(mode):
    show_page_header(*DOC_PROFILES["BA"])
    show_doc_ba_body(build_business_frame_lookup(), mode)


def show_documentation_it_page(mode):
    show_page_header(*DOC_PROFILES["IT"])
    show_doc_it_body(mode)


def show_documentation_bi_card(frame, mode):
    with open_card("doc_bi", *DOC_PROFILES["BI"]):
        show_doc_bi_body(frame, mode)


def show_documentation_ba_card(frame, mode):
    with open_card("doc_ba", *DOC_PROFILES["BA"]):
        show_doc_ba_body(frame, mode)


def show_documentation_it_card(mode):
    with open_card("doc_it", *DOC_PROFILES["IT"]):
        show_doc_it_body(mode)


def show_documentation_page(mode):
    """Kept for old addresses (D-105): the three profiles together, one screen. The
    sidebar itself now opens each profile as its own page (D-110)."""
    show_page_header("Documentación", "Qué resuelve el proyecto, para quién y cómo opera.")
    frame = build_business_frame_lookup()
    bi_column, ba_column, it_column = st.columns(3, gap="medium")
    with bi_column:
        show_documentation_bi_card(frame, mode)
    with ba_column:
        show_documentation_ba_card(frame, mode)
    with it_column:
        show_documentation_it_card(mode)


def show_links_page(mode):
    """The repository is the single destination for code, commits, executions and full
    documents: no separate «Código» section repeats what GitHub already shows (D-106)."""
    show_page_header("GitHub", "El código, las ejecuciones y los documentos completos del "
                     "proyecto viven en el repositorio. Los destinos externos se identifican con ↗.")
    st.markdown(build_link_html("Consultar ejecuciones dentro del proyecto →", build_page_address(PAGE_RUNS)), unsafe_allow_html=True)
    for group in ("Código y operación", "Fuentes de datos", "Documentos"):
        st.subheader(group)
        entries = [link for link in project.PROJECT_LINKS if link["group"] == group and link["url"]]
        rows = "".join(build_resource_row(link) for link in entries)
        st.markdown(f'<ul class="resource-tree">{rows}</ul>', unsafe_allow_html=True)

# endregion


# region Entry point
def show_document_page(mode, title, subtitle, renderer):
    show_page_header(title, subtitle)
    renderer(mode)


SHOW_PAGE_BY_TITLE = {
    PAGE_DOCUMENTATION: show_documentation_page,
    PAGE_DOC_BI: show_documentation_bi_page, PAGE_DOC_BA: show_documentation_ba_page,
    PAGE_DOC_IT: show_documentation_it_page,
    PAGE_HOME: show_home_page,
    PAGE_DATA: show_data_page,
    PAGE_COVER: show_cover_page,
    PAGE_BUSINESS: lambda mode: show_document_page(mode, PAGE_BUSINESS,
        "Las preguntas, las fuentes y las decisiones de negocio detrás de los datos.", show_idea_tab),
    PAGE_DIAGRAMS: show_diagrams_page,
    PAGE_ANALYSIS: show_analysis_page,
    PAGE_GAP: lambda mode: show_analysis_view(mode, PAGE_GAP, show_gap_tab),
    PAGE_CHANNELS: lambda mode: show_analysis_view(mode, PAGE_CHANNELS, show_channels_tab),
    PAGE_SEASONALITY: show_price_context_page,
    PAGE_ALERTS: lambda mode: show_analysis_view(mode, PAGE_ALERTS, show_alerts_tab),
    PAGE_QUERIES: show_queries_page,
    PAGE_KPI: show_kpi_page,
    PAGE_ARCHITECTURE: show_architecture_page,
    PAGE_CODE: lambda mode: show_document_page(mode, PAGE_CODE,
        "Del primer archivo que descarga datos al código que los presenta.", show_files_tab),
    PAGE_DEVOPS: lambda mode: show_document_page(mode, PAGE_DEVOPS,
        "Automatización, seguridad, observabilidad e informes.", show_devops_tab),
    PAGE_OPERATIONS: show_operations_page,
    PAGE_RUNS: lambda mode: show_document_page(mode, PAGE_RUNS,
        "Historial real del pipeline y ejecución manual con acceso de administración.", show_runs_tab),
    PAGE_RULES: lambda mode: show_document_page(mode, PAGE_RULES,
        "Qué se valida y qué ocurre cuando una fila no cumple las reglas.", show_rules_tab),
    PAGE_MANUAL: lambda mode: show_document_page(mode, PAGE_MANUAL,
        "Cómo operar el proyecto y resolver sus fallas.", show_manual_tab),
    PAGE_GLOSSARY: lambda mode: show_document_page(mode, PAGE_GLOSSARY,
        "Siglas y conceptos explicados en contexto.", show_glossary_tab),
    PAGE_LINKS: show_links_page,
}


# Tablets and narrow windows: the menu folds once per visit, so the page gets the
# whole width; once the reader opens it again it stays open (D-057). Streamlit
# already folds it on phones; computers keep it open.
NARROW_SCREEN_WIDTH = 1024
FOLD_SIDEBAR_SCRIPT = f"""<script>
(() => {{
if (window.innerWidth >= {NARROW_SCREEN_WIDTH}) {{ return; }}
try {{ if (sessionStorage.getItem("sidebarFolded")) {{ return; }} }} catch (error) {{ return; }}
let tries = 0;
const fold = () => {{
    const sidebar = document.querySelector('[data-testid="stSidebar"]');
    const button = document.querySelector('[data-testid="stSidebarCollapseButton"] button');
    if (sidebar && button && sidebar.getAttribute("aria-expanded") === "true") {{
        button.click();
        try {{ sessionStorage.setItem("sidebarFolded", "yes"); }} catch (error) {{}}
    }} else if (sidebar && sidebar.getAttribute("aria-expanded") === "false") {{
        try {{ sessionStorage.setItem("sidebarFolded", "yes"); }} catch (error) {{}}
    }} else if (tries++ < 40) {{
        setTimeout(fold, 100);
    }}
}};
fold();
}})();
</script>"""


def show_attribution():
    """Footer of every page: the data source. The project links live only in
    Operaciones (D-056)."""
    st.divider()
    st.caption(ATTRIBUTION_TEXT)


def order_windows():
    """The data-first route, followed by documentation and links."""
    return ROUTE + [SECTION_LINKS, SECTION_RESOURCES, SECTION_KPI]


def start_window(profile=None):
    """A single public entry point; legacy profile arguments are ignored."""
    return REPORT_WINDOW


def read_window_views(window, profile=None):
    """One stable order for every visitor."""
    return [p for p in WINDOWS[window] if p not in (PAGE_ANALYSIS, PAGE_GAP, PAGE_CHANNELS)]


def number_window(window, order):
    """«02 · Dashboard»: its step in the route; the links page has no number."""
    if window not in ROUTE:
        return window
    return f"{order.index(window) + 1:02d} · {window}"


def window_of_page(page):
    """The window a navigation entry draws (its title carries a number)."""
    return page.title.split(" · ", 1)[-1]


def window_view_key(window):
    """Session key of the view chosen in one window."""
    return f"view_{WINDOW_PATHS[window]}"


def step_view(window, step):
    """◀ or ▶: the view before or after the current one, going round."""
    views = read_window_views(window)
    key = window_view_key(window)
    st.session_state[key] = views[(views.index(st.session_state[key]) + step) % len(views)]


def synchronize_window_view(window):
    """Apply a deep-linked view before its header widget is instantiated."""
    views = read_window_views(window)
    key = window_view_key(window)
    requested = st.query_params.get(VIEW_PARAMETER)
    if requested in (PAGE_ANALYSIS, PAGE_GAP, PAGE_CHANNELS):
        if requested == PAGE_GAP:
            st.query_params["datos_modo"] = "brecha"
        requested = PAGE_HOME if requested == PAGE_ANALYSIS else PAGE_DATA
        st.query_params[VIEW_PARAMETER] = requested
    if requested in views and requested != st.session_state.get(f"{key}_synced"):
        st.session_state[key] = requested
        st.session_state[f"{key}_synced"] = requested
    if st.session_state.get(key) not in views:
        st.session_state[key] = views[0]


def choose_window_view(window):
    """The view of a window: from the address when a link asks for one, then from the
    selector; ◀ ▶ step through them without leaving the window (D-065)."""
    views = read_window_views(window)
    key = window_view_key(window)
    requested = st.query_params.get(VIEW_PARAMETER)
    if requested in (PAGE_ANALYSIS, PAGE_GAP, PAGE_CHANNELS):
        if requested == PAGE_GAP:
            st.query_params["datos_modo"] = "brecha"
        requested = PAGE_HOME if requested == PAGE_ANALYSIS else PAGE_DATA
        st.query_params[VIEW_PARAMETER] = requested
    if requested in views and requested != st.session_state.get(f"{key}_synced"):
        st.session_state[key] = requested
    if st.session_state.get(key) not in views:
        st.session_state[key] = views[0]
    view = st.session_state[key]
    st.session_state[f"{key}_synced"] = view
    if view == views[0]:
        st.query_params.pop(VIEW_PARAMETER, None)
    else:
        st.query_params[VIEW_PARAMETER] = view
    return view


def render_window(window, pages=None):
    """Draw one section: its view selector, the chosen view, the route and the footer."""
    mode = get_mode()
    apply_style(mode)
    st.session_state[COMPACT_VIEW] = window == REPORT_WINDOW
    synchronize_window_view(window)
    show_app_header(window)
    view = choose_window_view(window)
    with st.container(key="report_page" if window == REPORT_WINDOW else "window_page"):
        overview_class = OVERVIEW_CLASS_BY_VIEW.get(view)
        if overview_class:
            st.markdown(f'<span class="overview-viewport-marker {overview_class}" '
                        'aria-hidden="true"></span>', unsafe_allow_html=True)
        if view == PAGE_COVER:
            # The cover links with the navigation pages, so a visit keeps its session.
            show_cover_page(mode, pages)
        else:
            SHOW_PAGE_BY_TITLE[view](mode)
    if view not in OVERVIEW_CLASS_BY_VIEW:
        if pages:
            show_route_footer(window, pages)
        show_attribution()
    st.html(FOLD_SIDEBAR_SCRIPT + RELOAD_HOME_SCRIPT + build_visit_history_script(), unsafe_allow_javascript=True)


def keep_context():
    """The address of the next page keeps the theme and the profile (filters and choices
    stay in the session)."""
    context = {}
    if st.session_state.get(THEME_STATE) in charts.THEMES:
        context[THEME_PARAMETER] = st.session_state[THEME_STATE]
    return context


def show_route_footer(window, pages):
    """«← Volver» and «Siguiente →» with what the next step proves; same window."""
    if window not in ROUTE:
        return
    position = ROUTE.index(window)
    st.divider()
    with st.container(key="route_footer", horizontal=True, horizontal_alignment="distribute",
                      vertical_alignment="center"):
        if position > 0:
            back = ROUTE[position - 1]
            st.page_link(pages[back], label=f"← Volver: {back}", query_params=keep_context())
        if position < len(ROUTE) - 1:
            following = ROUTE[position + 1]
            st.page_link(pages[following], label=f"Siguiente: {following} →",
                         help=f"Muestra {ROUTE_LEADS[following]}.", query_params=keep_context())
    if position < len(ROUTE) - 1:
        st.caption(f"Siguiente paso: {ROUTE_LEADS[ROUTE[position + 1]]}.")



def render_page(title):
    """Draw one view alone, as tests and old callers do."""
    mode = get_mode()
    apply_style(mode)
    SHOW_PAGE_BY_TITLE[title](mode)
    show_attribution()


def build_window_page(window, order, start, pages):
    """A navigation entry that draws one section, numbered by its step in the route."""
    return st.Page(lambda: render_window(window, pages), title=number_window(window, order),
                   icon=WINDOW_ICONS[window], url_path=WINDOW_PATHS[window],
                   visibility="hidden" if window == SECTION_KPI else "visible",
                   default=window == start)


def build_redirect_page(url_path, view, windows_by_title):
    """A hidden page at an old address that opens its window on the same view (D-065)."""
    def redirect():
        parameters = {key: value for key, value in st.query_params.to_dict().items()
                      }
        window = WINDOW_OF_VIEW[view]
        if view != read_window_views(window)[0]:
            parameters[VIEW_PARAMETER] = view
        st.switch_page(windows_by_title[window], query_params=parameters)
    return st.Page(redirect, title=view, url_path=url_path, visibility="hidden")


def redirect_moved_tab(current_page, windows_by_title):
    """Keep deep links with ?seccion=… working: they open the view that holds that tab."""
    tab = st.query_params.get(TAB_PARAMETER)
    current_window = window_of_page(current_page)
    special_view = next((target for (old_page, old_tab), target in OLD_TAB_PAGES.items()
                         if old_tab == tab and WINDOW_OF_VIEW.get(old_page) == current_window), None)
    view = special_view or PAGE_OF_TAB.get(OLD_HOME_TABS.get(tab, tab))
    if not view:
        return
    st.query_params.pop(TAB_PARAMETER, None)
    window = WINDOW_OF_VIEW[view]
    parameters = {key: value for key, value in st.query_params.to_dict().items()
                  }
    if view != read_window_views(window)[0]:
        parameters[VIEW_PARAMETER] = view
    if window != window_of_page(current_page) or st.query_params.get(VIEW_PARAMETER) != parameters.get(
            VIEW_PARAMETER):
        st.switch_page(windows_by_title[window], query_params=parameters)


RETURN_CONTEXT_KEYS = ["dashboard_group", "dashboard_region", "dashboard_week", "dashboard_product", "dashboard_top_n",
                       "analysis_group", "analysis_product", "analysis_key_label", "analysis_region", "analysis_channels"]


def restore_return_context():
    encoded = st.query_params.pop("_ctx", None)
    if not encoded or len(encoded) > 16000:
        return
    try:
        snapshot = json.loads(base64.b64decode(encoded, validate=True))
        if isinstance(snapshot, dict):
            for key in RETURN_CONTEXT_KEYS:
                value = snapshot.get(key)
                if key == "dashboard_top_n":
                    if isinstance(value, int) and not isinstance(value, bool) and 8 <= value <= 20:
                        st.session_state[key] = value
                elif key == "dashboard_product":
                    if (isinstance(value, dict) and isinstance(value.get("key"), dict)
                            and all(isinstance(value["key"].get(field), str) for field in queries.KEY_COLUMNS)
                            and isinstance(value.get("name"), str)):
                        st.session_state[key] = value
                elif key == "analysis_channels":
                    if isinstance(value, list) and all(isinstance(item, str) for item in value):
                        st.session_state[key] = value
                elif isinstance(value, str):
                    st.session_state[key] = value
    except (ValueError, TypeError, UnicodeDecodeError):
        pass


def build_visit_history_script():
    snapshot = {key: st.session_state[key] for key in RETURN_CONTEXT_KEYS if key in st.session_state}
    encoded = json.dumps(snapshot, ensure_ascii=True, default=str).replace("<", "\\u003c")
    return """<script>(() => {
    try {
        if (!document.documentElement.dataset.greenoceanLinksBound) {
            document.documentElement.dataset.greenoceanLinksBound = 'true';
            document.addEventListener('click', event => {
                if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
                const anchor = event.target.closest && event.target.closest('a[href]');
                if (!anchor || anchor.hasAttribute('download')) return;
                // Only internal navigation forces the same tab (D-113): this app may run
                // behind an iframe wrapper, where forcing target=_self on an external
                // link (GitHub, ODEPA…) makes the destination refuse to be framed.
                if (anchor.hostname === location.hostname) anchor.target = '_self';
            }, true);
        }
        const url = new URL(location.href); url.searchParams.delete('_ctx');
        const identity = url.pathname + '|' + ['vista','kpi','consulta'].map(k => url.searchParams.get(k) || '').join('|');
        const pending = sessionStorage.getItem('greenoceanReturning');
        if (pending && pending !== identity) return;
        if (pending) sessionStorage.removeItem('greenoceanReturning');
        const rows = JSON.parse(sessionStorage.getItem('greenoceanTrail') || '[]');
        const record = {url:url.pathname + url.search, identity, filters:__FILTERS__};
        if (rows.length && rows[rows.length-1].identity === identity) rows[rows.length-1] = record;
        else rows.push(record);
        sessionStorage.setItem('greenoceanTrail', JSON.stringify(rows.slice(-30)));
    } catch (_) {}
    })();</script>""".replace("__FILTERS__", encoded)


RETURN_ACTION_SCRIPT = """<script>(() => {
    try {
        const rows = JSON.parse(sessionStorage.getItem('greenoceanTrail') || '[]');
        if (rows.length > 1) rows.pop();
        const previous = rows.length > 0 ? rows[rows.length-1] : null;
        const url = new URL(previous ? previous.url : '/', location.origin);
        if (url.origin !== location.origin) return;
        if (previous) {
            sessionStorage.setItem('greenoceanReturning', previous.identity);
            url.searchParams.set('_ctx', btoa(unescape(encodeURIComponent(JSON.stringify(previous.filters || {})))));
        }
        sessionStorage.setItem('greenoceanTrail', JSON.stringify(rows));
        location.assign(url.href);
    } catch (_) { location.assign('/'); }
})();</script>"""

RELOAD_HOME_SCRIPT = """<script>
(() => {
    if (document.documentElement.dataset.greenoceanReloadHandled === "true") return;
    document.documentElement.dataset.greenoceanReloadHandled = "true";
    // A reload just to sync the theme's base mode (D-099): stay on this page.
    try {
        if (sessionStorage.getItem("greenoceanThemeReload")) {
            sessionStorage.removeItem("greenoceanThemeReload");
            return;
        }
    } catch (_) {}
    const navigation = performance.getEntriesByType("navigation")[0];
    if (!navigation || navigation.type !== "reload") return;
    const current = new URL(window.location.href);
    const home = new URL("/", current);
    for (const name of ["tema"]) {
        if (current.searchParams.has(name)) home.searchParams.set(name, current.searchParams.get(name));
    }
    home.searchParams.set("vista", "Dashboard");
    try {
        const trail = JSON.parse(sessionStorage.getItem('greenoceanTrail') || '[]');
        const last = trail[trail.length - 1];
        if (last && last.filters && Object.keys(last.filters).length) {
            home.searchParams.set('_ctx', btoa(unescape(encodeURIComponent(JSON.stringify(last.filters)))));
        }
    } catch (_) {}
    if (current.pathname !== home.pathname || current.search !== home.search || current.hash) {
        window.location.replace(home.href);
    }
})();
</script>"""


# The side menu follows the VS Code explorer model: one flat stack of short,
# conventional section names. Only a section's chevron carries visual meaning;
# pages appear underneath after expansion.
SIDEBAR_TREE = [
    ("", [(REPORT_WINDOW, [PAGE_HOME, PAGE_SEASONALITY, PAGE_DATA]),
          (SECTION_TECHNICAL, [PAGE_DIAGRAMS, PAGE_ARCHITECTURE, PAGE_DEVOPS, PAGE_OPERATIONS, PAGE_RUNS]),
          (SECTION_QUERIES, [PAGE_QUERIES]),
          # «El proyecto» and the old «Documentación» folder of six pages are now
          # three, one per reader (D-105, D-110): the same folder pattern as every
          # other section, not a special-cased flat link. «Código» merges into
          # «GitHub»: nobody reads source files in the sidebar when the real
          # repository, with every file and commit, is one link away (D-106).
          (SECTION_LINKS, [PAGE_DOC_BI, PAGE_DOC_BA, PAGE_DOC_IT]),
          (SECTION_RESOURCES, None)]),
]
SIDEBAR_TOP_LABELS = {REPORT_WINDOW: "Dashboard", SECTION_TECHNICAL: "Arquitectura",
                      SECTION_QUERIES: "Análisis SQL",
                      SECTION_PROJECT: "Proyecto", SECTION_LINKS: "Documentación",
                      SECTION_RESOURCES: "GitHub"}
SIDEBAR_LABELS = {PAGE_HOME: "Resumen semanal", PAGE_SEASONALITY: "Contexto de precios",
                  PAGE_DIAGRAMS: "Pipeline", PAGE_OPERATIONS: "Calidad de datos",
                  PAGE_QUERIES: "Preguntas y resultados",
                  PAGE_DOCUMENTATION: "Documentación", PAGE_MANUAL: "Manual",
                  PAGE_COVER: "Descripción general", PAGE_BUSINESS: "Alcance del proyecto"}


def read_current_view(window):
    """The view drawn in a window: the address first, then the last choice."""
    views = read_window_views(window)
    view = st.query_params.get(VIEW_PARAMETER, st.session_state.get(window_view_key(window), views[0]))
    return view if view in views else views[0]


def build_sidebar_css(mode):
    palette = charts.get_palette(mode)
    text = palette["sidebar_text"]
    # The wordmark and its child links sit on the sidebar, so their contrast must
    # follow that surface. Corporativo has a light page but a dark navy sidebar.
    dark = is_dark_surface(palette["sidebar"])
    child_green = BRAND_GREEN_DARK if dark else BRAND_GREEN_LIGHT
    sidebar_top = "#101824" if dark else "#ffffff"
    sidebar_bottom = "#080d15" if dark else "#f5f7fb"
    hairline = "rgba(148, 163, 184, .18)" if dark else "rgba(15, 23, 42, .12)"
    quiet = "rgba(214, 218, 227, .68)" if dark else "rgba(31, 41, 55, .68)"
    alert_text = "#ff9ca4" if dark else "#9d1f2c"
    return f"""<style>
    [data-testid="stSidebar"] {{
        background:linear-gradient(180deg,{sidebar_top} 0%,{palette['sidebar']} 38%,{sidebar_bottom} 100%);
        border-right:1px solid {hairline}; box-shadow:10px 0 32px rgba(0,0,0,.12);}}
    [data-testid="stSidebar"][aria-expanded="true"] {{min-width:300px !important; max-width:300px !important;}}
    [data-testid="stSidebarContent"] {{background:transparent;}}
    [data-testid="stSidebarHeader"] {{height:66px; padding:10px 17px 7px !important;
        border-bottom:1px solid {hairline};}}
    [data-testid="stSidebarHeader"] img {{max-width:144px !important;}}
    [data-testid="stSidebarCollapseButton"] button {{width:32px; height:32px; min-height:32px;
        border:1px solid {hairline} !important; border-radius:10px !important;
        background:color-mix(in srgb,{palette['field']} 72%,transparent) !important;
        box-shadow:inset 0 1px rgba(255,255,255,.04);}}
    [data-testid="stSidebarUserContent"] {{padding:6px 17px 0 !important;}}
    [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {{gap:0 !important;
        min-height:calc(100vh - 86px); padding-bottom:116px;}}
    [data-testid="stSidebarNav"] {{display:none;}}
    /* A folder row (D-102): a real button, styled as plain text, with a chevron that
       folds it — the same affordance as VS Code's Explorer. */
    [class*="st-key-nav_group_"] button {{width:100%; justify-content:flex-start; gap:0 !important;
        border:0 !important; background:transparent !important; box-shadow:none !important;
        padding:3px 7px !important; border-radius:5px; min-height:27px; transition:background .12s ease;}}
    [class*="st-key-nav_group_"] button:hover:not(:disabled) {{background:color-mix(in srgb,{text} 7%,transparent) !important;}}
    [class*="st-key-nav_group_"] button:disabled {{cursor:default; opacity:1;}}
    [class*="st-key-nav_group_"] button p {{font-size:.78rem !important; font-weight:430 !important;
        letter-spacing:-.005em; color:{text} !important;
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}}
    .st-key-nav_group_current button p {{color:{text} !important;}}
    .st-key-nav_group_current button [data-testid="stIconMaterial"] {{color:{palette['accent']}; opacity:1;}}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a {{padding:3px 7px !important; border-radius:5px;
        background:transparent !important; box-shadow:none !important; min-height:27px; gap:0 !important;
        border:1px solid transparent; transition:background .12s ease,border-color .12s ease;}}
    [data-testid="stSidebar"] [data-testid="stPageLink"] p {{font-size:.78rem; color:{text} !important;
        font-weight:400; letter-spacing:-.005em; padding-left:10px;
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}}
    [data-testid="stSidebar"] [data-testid="stPageLink"] [data-testid="stIconMaterial"] {{display:none !important;}}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a > span:has([data-testid="stIconMaterial"]) {{
        display:none !important;}}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
        background:color-mix(in srgb,{text} 7%,transparent) !important;
        border-color:{hairline};}}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:focus,
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:active,
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:visited {{
        background:transparent !important; color:{text} !important; box-shadow:none !important;}}
    /* Expanded rows remain on the same axis as their parent: this is a flat,
       aligned explorer rather than an indented tree. */
    [class*="st-key-nav_child_"] {{margin-left:0; padding-left:0; border-left:0;}}
    [class*="st-key-nav_"]:not([class*="st-key-nav_child_"]) {{margin:1px 0;}}
    [class*="st-key-nav_current"] [data-testid="stPageLink"] a,
    [class*="_nav_current"] [data-testid="stPageLink"] a {{
        background:transparent !important; border-color:transparent; box-shadow:none !important;}}
    [class*="st-key-nav_current"] [data-testid="stPageLink"] a:hover,
    [class*="_nav_current"] [data-testid="stPageLink"] a:hover {{
        background:transparent !important; border-color:transparent !important;}}
    [class*="st-key-nav_current"] [data-testid="stPageLink"] p,
    [class*="_nav_current"] [data-testid="stPageLink"] p {{font-weight:500; color:{palette['strong_text']} !important;}}
    [class*="st-key-nav_current"] [data-testid="stPageLink"] [data-testid="stIconMaterial"],
    [class*="_nav_current"] [data-testid="stPageLink"] [data-testid="stIconMaterial"] {{
        opacity:1; color:{palette['accent']};}}
    [class*="st-key-nav_child_"] [data-testid="stPageLink"] p {{color:{child_green} !important;
        -webkit-text-fill-color:{child_green} !important; font-weight:460;
        text-shadow:0 0 10px color-mix(in srgb,{child_green} 18%,transparent);}}
    .st-key-sidebar_footer {{position:fixed; left:17px; bottom:0; width:266px; padding:13px 5px 12px;
        background:linear-gradient(180deg,transparent 0%,{sidebar_bottom} 18%); gap:7px !important; z-index:5;
        border-top:1px solid {hairline};}}
    .st-key-home_alert_trigger button {{width:100%; justify-content:flex-start; border:0 !important;
        background:transparent !important; color:{alert_text} !important; border-radius:5px;
        padding:7px 5px; min-height:30px; box-shadow:none !important;}}
    .st-key-home_alert_trigger button:hover {{background:transparent !important; filter:brightness(1.12);}}
    .st-key-home_alert_trigger button p {{color:{alert_text} !important; -webkit-text-fill-color:{alert_text} !important;
        font-weight:560; font-size:.79rem; text-align:left;}}
    .st-key-sidebar_appearance [data-testid="stPopover"] button {{background:transparent !important;
        box-shadow:none !important; color:{quiet} !important; padding:6px 8px !important;}}
    .st-key-sidebar_appearance [data-testid="stPopover"] button p {{color:{quiet} !important; font-size:.76rem !important;}}
    .st-key-sidebar_footer [data-testid="stCaptionContainer"] p {{color:{text} !important; opacity:.75;
        font-size:.67rem; line-height:1.35; padding:0 3px;}}
    </style>"""


def nav_open_key(window):
    return f"nav_open_{WINDOW_PATHS[window]}"


SIDEBAR_NAV_VERSION = 4


def show_sidebar_navigation(windows_by_title, current_window, order):
    """A VS Code-like explorer: aligned top-level titles, no numbering or item
    icons, and a chevron only for sections that contain pages."""
    st.sidebar.markdown(build_sidebar_css(get_mode()), unsafe_allow_html=True)
    if st.session_state.get("sidebar_nav_version") != SIDEBAR_NAV_VERSION:
        for _, sections in SIDEBAR_TREE:
            for window, views in sections:
                if views is not None:
                    st.session_state[nav_open_key(window)] = False
        st.session_state["sidebar_nav_version"] = SIDEBAR_NAV_VERSION
    current_view = read_current_view(current_window)
    for heading, sections in SIDEBAR_TREE:
        if heading:
            st.sidebar.markdown(f'<div class="nav-heading">{heading}</div>', unsafe_allow_html=True)
        for window, views in sections:
            label = SIDEBAR_TOP_LABELS.get(window, window)
            if views is None:
                key = "nav_current" if window == current_window else f"nav_{WINDOW_PATHS[window]}"
                with st.sidebar.container(key=key):
                    st.page_link(windows_by_title[window], label=label, query_params=keep_context())
                continue
            # Every folder starts closed, including the section that owns the current
            # page. Opening it never changes the alignment of the rows it reveals.
            open_key = nav_open_key(window)
            is_open = st.session_state.get(open_key, False)
            group_key = "nav_group_current" if window == current_window else f"nav_group_{WINDOW_PATHS[window]}"
            chevron = "⌄" if is_open else "›"
            with st.sidebar.container(key=group_key):
                if st.button(f"{chevron}  {label}", key=f"nav_toggle_{WINDOW_PATHS[window]}"):
                    st.session_state[open_key] = not is_open
                    st.rerun()
            if not is_open:
                continue
            for index, view in enumerate(views):
                active = window == current_window and view == current_view
                key = f"nav_child_{WINDOW_PATHS[window]}_{index}" + ("_nav_current" if active else "")
                with st.sidebar.container(key=key):
                    st.page_link(windows_by_title[window], label=SIDEBAR_LABELS.get(view, view),
                                 query_params=keep_context() | {VIEW_PARAMETER: view})
    show_sidebar_footer()


def show_sidebar_footer():
    """The price alerts, apart from the navigation and always at the bottom, on every page."""
    alerts_now = read_price_alerts()
    week = read_latest_week()
    count = int((alerts_now["week_start"] == week).sum()) if not alerts_now.empty else 0
    # The alert dialog's styling (shapes, legend, colors) lives in home_mockup's
    # stylesheet, built only for the Resumen page before D-096. The trigger now
    # sits in this sidebar on every page, so its CSS must load everywhere too,
    # or the dialog renders as plain unstyled buttons (D-100).
    st.markdown(home_mockup.style(get_mode(), charts.get_palette(get_mode())), unsafe_allow_html=True)
    with st.sidebar.container(key="sidebar_footer"):
        if st.button(f"▲  Alerta de precio · {count}", key="home_alert_trigger",
                     help=f"{count} cambios de precio fuera de lo habitual esta semana. Abre el detalle por familia."):
            st.session_state["home_alert_selected_family"] = None
            show_home_alerts_dialog(f"{week:%Y-%m-%d}", ALL_VALUES, None, get_mode())
        with st.container(key="sidebar_appearance"):
            show_theme_field()
        st.caption("Fuente: ODEPA · actualización automática cada martes.")


def main():
    """Theme, navigation with icons and the chosen page."""
    st.set_page_config(page_title="Monitor de precios de alimentos", layout="wide",
                       page_icon=":material/monitoring:")
    if not queries.DATABASE_FILE.exists():
        st.error("Falta etl/datos.db. Ejecuta primero: python etl/etl.py")
        return
    settle_theme()
    st.session_state.pop(PROFILE_PARAMETER, None)
    st.query_params.pop("perfil", None)
    restore_return_context()
    profile = None
    order = order_windows()
    start = start_window(profile)
    windows_by_title = {}
    windows_by_title.update({window: build_window_page(window, order, start, windows_by_title)
                             for window in order})
    redirects = [build_redirect_page(path, view, windows_by_title)
                 for view, path in PAGE_PATHS.items() if path not in WINDOW_PATHS.values()]
    redirects += [build_redirect_page(path, page, windows_by_title)
                  for path, (page, _) in OLD_PATHS.items()
                  if path not in WINDOW_PATHS.values() and path not in PAGE_PATHS.values()]
    current_page = st.navigation({
        "Recorrido": [windows_by_title[window] for window in ROUTE],
        "Referencias": [windows_by_title[SECTION_LINKS], windows_by_title[SECTION_RESOURCES]],
        "Compatibilidad": [windows_by_title[SECTION_KPI]] + redirects}, position="hidden")
    # Historical root links may request a project view. Keep that exact destination
    # when Dashboard becomes the root, rather than silently showing another view.
    # Views renamed since: old links open the new title (D-094).
    if st.query_params.get(VIEW_PARAMETER) in RETIRED_VIEWS:
        st.query_params[VIEW_PARAMETER] = RETIRED_VIEWS[st.query_params[VIEW_PARAMETER]]
    requested_view = st.query_params.get(VIEW_PARAMETER)
    requested_window = WINDOW_OF_VIEW.get(requested_view)
    if requested_window and requested_window != window_of_page(current_page):
        st.switch_page(windows_by_title[requested_window], query_params=st.query_params.to_dict())
    redirect_moved_tab(current_page, windows_by_title)
    current_window = window_of_page(current_page)
    if current_window not in WINDOWS:
        # An old address: it only switches to its window, before any menu is drawn.
        current_page.run()
        return
    show_sidebar_navigation(windows_by_title, current_window, order)
    # The dashboard is the public home page; choosing a profile is optional.
    current_page.run()


if __name__ == "__main__":
    main()
# endregion
