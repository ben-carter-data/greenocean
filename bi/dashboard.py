"""Streamlit dashboard for the price monitor.

Run it with:  streamlit run bi/dashboard.py

It reads etl/datos.db through the named queries of bi/queries.sql, and the
state of the weekly pipeline through the GitHub API (bi/control.py).
Texts shown to the user are in Spanish; code and comments are in English.
The color modes and chart palettes live in bi/charts.py.
"""
import base64
import html
import importlib
import json
import logging
import math
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# region Imports of the project
# Streamlit runs this file as a script, so the project folder is added to the
# import path to reach the other modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bi  # noqa: E402
from bi import (alerts, price_context, architecture, charts, control, data_browser, home_mockup, lag,  # noqa: E402
                audit_trace, database_crossings, database_map, doc_diagrams, er_diagram, document_pdf, github_page, inflation_view, lineage, operation_center, quality_evidence, quality_live, quality_view, security_map, sql_explorer, stack_page, project, quality, queries, star_model, zoom)
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
# D-162: read-only SQL on the gold layer, the destination of «Consultas SQL» in the pipeline.
PAGE_SQL = "Consultas SQL"
RETIRED_VIEWS = {"Histórico y estacionalidad": "Contexto del precio"}
PAGE_ALERTS = "Alertas"
PAGE_KPI = "Indicadores explicados"
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
# The documentation is the project's real documents (D-151): requirements,
# architecture and decisions, read from docs/ so the panel shows what GitHub holds.
PAGE_PRD = "PRD · Requisitos del producto"
PAGE_SAD = "SAD · Arquitectura"
PAGE_ADR = "ADR · Decisiones de arquitectura"
# Step 7 of the refonte: the SAD's scalability section, on its own page.
PAGE_SCALABILITY = "Escalabilidad"
# D-201: security has its own section, the attack view and the test plan that backs it.
PAGE_SECURITY = "Mapa de seguridad"
PAGE_SECURITY_PLAN = "Plan de pruebas de seguridad"
# D-211: the stack in 30 seconds, for a recruiter.
PAGE_STACK = "Stack y evidencia"
SECTION_RESOURCES = "Enlaces"
# A sidebar-only folder (D-118): two external links, no Streamlit page of its own,
# so it is not part of WINDOWS/ROUTE — rendered specially in show_sidebar_navigation.
SECTION_SOURCES = "Fuentes"
SOURCE_LINKS = [
    ("ODEPA: precios mayoristas", project.WHOLESALE_SOURCE_URL),
    ("ODEPA: precios al consumidor", project.CONSUMER_SOURCE_URL),
    ("INE: IPC de alimentos", project.INE_IPC_SOURCE_URL),
]
# The visit is a portfolio route, like a CV with its evidence: the project, then the
# dashboard, the code with its results and, for whoever wants more, the technical detail.
# Sources and links have one place of their own, out of the route (D-070).
SECTION_PROJECT = "El proyecto"
SECTION_KPI = "KPIs"
REPORT_WINDOW = "Dashboard"
SECTION_QUERIES = "Preguntas y resultados SQL"
SECTION_CODE = "Código del proyecto"
SECTION_PYTHON = "Análisis con Python"
SECTION_TECHNICAL = "Ingeniería de datos"
SECTION_LINKS = "Documentación"
SECTION_SECURITY = "Seguridad"
WINDOWS = {
    SECTION_PROJECT: [PAGE_COVER, PAGE_BUSINESS, PAGE_RULES, PAGE_STACK],
    SECTION_KPI: [PAGE_KPI],
    REPORT_WINDOW: [PAGE_HOME, PAGE_DATA, PAGE_ANALYSIS, PAGE_GAP, PAGE_CHANNELS, PAGE_ALERTS,
                    PAGE_SEASONALITY, PAGE_SQL],
    SECTION_TECHNICAL: [PAGE_DIAGRAMS, PAGE_ARCHITECTURE, PAGE_DEVOPS, PAGE_OPERATIONS, PAGE_RUNS],
    SECTION_SECURITY: [PAGE_SECURITY, PAGE_SECURITY_PLAN],
    SECTION_LINKS: [PAGE_PRD, PAGE_SAD, PAGE_ADR, PAGE_SCALABILITY, PAGE_DOCUMENTATION, PAGE_GLOSSARY,
                    PAGE_MANUAL],
    SECTION_RESOURCES: [PAGE_LINKS],
}
# The SQL and Python consoles left the app (D-143): the code lives in GitHub and the
# answers in the dashboard; their old addresses open the Resumen.
# «Código Python y SQL» left too (D-148): GitHub shows the code; its address opens the GitHub page.
ROUTE = [REPORT_WINDOW, SECTION_TECHNICAL, SECTION_SECURITY, SECTION_LINKS]
# The former KPI page remains as a hidden compatibility destination for old links;
# its business information now lives in the dashboard and documentation.
WINDOWS = {window: WINDOWS[window] for window in ROUTE + [SECTION_PROJECT, SECTION_RESOURCES, SECTION_KPI]}
WINDOW_PATHS = {SECTION_PROJECT: "proyecto", REPORT_WINDOW: "dashboard", SECTION_KPI: "kpis",
                SECTION_TECHNICAL: "arquitectura-y-operacion", SECTION_SECURITY: "seguridad",
                SECTION_LINKS: "documentacion-y-enlaces", SECTION_RESOURCES: "enlaces"}
WINDOW_ICONS = {SECTION_PROJECT: ":material/assignment:", REPORT_WINDOW: ":material/dashboard:",
                SECTION_KPI: ":material/insights:",
                SECTION_TECHNICAL: ":material/account_tree:", SECTION_SECURITY: ":material/lock:", SECTION_LINKS: ":material/menu_book:", SECTION_RESOURCES: ":material/link:"}
ROUTE_LEADS = {SECTION_PROJECT: "qué problema resuelve y qué se construyó",
               SECTION_LINKS: "los requisitos, la arquitectura y las decisiones del proyecto",
               SECTION_KPI: "qué mide cada KPI, cómo se calcula y qué límites tiene",
               REPORT_WINDOW: "los precios y cambios de la semana",
               SECTION_TECHNICAL: "pipeline, modelo estrella, DevOps y operación",
               SECTION_SECURITY: "qué podría intentar un atacante y las pruebas que lo detienen"}
WINDOW_OF_VIEW = {view: window for window, views in WINDOWS.items() for view in views}
VIEW_PARAMETER = "vista"
# Session flag: the window being drawn is a report (Dashboard), so every view fits one
# screen, like a page of Looker or Power BI (D-067).
COMPACT_VIEW = "compact_view"
# Tile heights of a report page, in pixels: two rows fit a 1440 x 900 screen.
TILE_HEIGHT = 255
# A gap above +300 % does not compare the same thing: in street markets, which sell in
# bulk like the wholesale market, 99 % of the gaps stay under +253 %; above +300 % the
# consumer price is a packed format (supermarket trays of 250-500 g) against bulk
# wholesale (bins of 400 kilos, trays of 7 kilos). Out of the ranking and the median,
# listed apart, never deleted (D-068).
MAXIMUM_COMPARABLE_GAP = 3.0
# «Subió fuerte»: a weekly change above this share, in the sentence on top.
STRONG_CHANGE = 0.10
# Filters of the whole report (D-069): one bar for every Dashboard view, kept while the
# reader moves with ◀ ▶. The product comes from a click (cross filter or drill-down).
ALL_VALUES = "Todas"
GLOBAL_FILTERS = {"group": "Grupo", "region": "Región", "week": "Semana"}
# Dashboard summary (D-072): a slider sets how many rows the ranking shows.
TOP_N_RANGE = (1, 100)
DEFAULT_TOP_N = 20
RANKING_TITLES = {"Mayores movimientos": "¿Qué precios cambiaron más?",
                  "Alzas": "¿Qué precios subieron más?", "Bajas": "¿Qué precios bajaron más?"}
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
    PAGE_PRD: ":material/assignment:", PAGE_SAD: ":material/account_tree:", PAGE_ADR: ":material/gavel:",
    PAGE_SCALABILITY: ":material/trending_up:", PAGE_SQL: ":material/terminal:",
    PAGE_SECURITY: ":material/lock:", PAGE_STACK: ":material/stacks:", PAGE_SECURITY_PLAN: ":material/fact_check:",
    PAGE_HOME: ":material/dashboard:", PAGE_DATA: ":material/table_view:", PAGE_COVER: ":material/home:",
    PAGE_BUSINESS: ":material/assignment:",
    PAGE_DIAGRAMS: ":material/account_tree:", PAGE_ARCHITECTURE: ":material/schema:",
    PAGE_ANALYSIS: ":material/monitoring:", PAGE_GAP: ":material/compare_arrows:",
    PAGE_CHANNELS: ":material/storefront:", PAGE_SEASONALITY: ":material/calendar_month:",
    PAGE_ALERTS: ":material/notifications_active:", PAGE_KPI: ":material/insights:",
    PAGE_RULES: ":material/rule:", PAGE_DEVOPS: ":material/shield:",
    PAGE_OPERATIONS: ":material/health_and_safety:", PAGE_RUNS: ":material/play_circle:",
    PAGE_MANUAL: ":material/menu_book:",
    PAGE_GLOSSARY: ":material/dictionary:", PAGE_LINKS: ":material/link:",
}
PAGE_PATHS = {
    PAGE_DOCUMENTATION: "documentacion-general",
    PAGE_SECURITY: "mapa-de-seguridad", PAGE_STACK: "stack-y-evidencia", PAGE_SECURITY_PLAN: "plan-de-pruebas-de-seguridad",
    PAGE_PRD: "prd", PAGE_SAD: "sad", PAGE_ADR: "adr", PAGE_SCALABILITY: "escalabilidad", PAGE_SQL: "consultas-sql",
    PAGE_HOME: "dashboard", PAGE_DATA: "datos", PAGE_COVER: "portada", PAGE_BUSINESS: "negocio",
    PAGE_DIAGRAMS: "diagramas",
    PAGE_ARCHITECTURE: "arquitectura", PAGE_ANALYSIS: "analisis", PAGE_GAP: "brecha",
    PAGE_CHANNELS: "canales", PAGE_SEASONALITY: "estacionalidad", PAGE_ALERTS: "alertas",
    PAGE_KPI: "indicadores",
    PAGE_RULES: "reglas", PAGE_DEVOPS: "devops", PAGE_OPERATIONS: "operaciones",
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
    TAB_CODE: PAGE_LINKS, TAB_RUNS: PAGE_RUNS, TAB_QUALITY: PAGE_OPERATIONS,
    TAB_WEEK: PAGE_ANALYSIS, TAB_GAP: PAGE_GAP, TAB_CHANNELS: PAGE_CHANNELS,
    TAB_SEASONALITY: PAGE_SEASONALITY, TAB_ALERTS: PAGE_ALERTS,
    TAB_EXPLORER: PAGE_HOME, TAB_QUERIES: PAGE_HOME,
}
OLD_PATHS = {
    "inicio": (PAGE_HOME, None), "el-proyecto": (PAGE_COVER, None), "panel": (PAGE_HOME, None),
    "margenes": (PAGE_GAP, None), "canales-y-regiones": (PAGE_CHANNELS, None),
    "consultas": (PAGE_HOME, None), "codigo": (PAGE_LINKS, None),
    # The three profile pages became the real documents (D-151).
    "documentacion-bi": (PAGE_PRD, None), "documentacion-ba": (PAGE_PRD, None),
    "documentacion-it": (PAGE_SAD, None), "pipeline": (PAGE_DIAGRAMS, None),
    "preguntas-y-resultados": (PAGE_HOME, None), "analisis-python": (PAGE_HOME, None),
    "queries": (PAGE_HOME, None), "python": (PAGE_HOME, None),
    # The retired «Consulta de datos» screen (C03).
    "datos-y-codigo": (PAGE_HOME, None),
    "codigo-y-resultados": (PAGE_HOME, None),
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
RUN_HISTORY_COUNT = 8
MANIFEST_FILE = Path(__file__).resolve().parent.parent / "agent" / "downloads" / "manifest.json"
CHILE_TIME_ZONE = "America/Santiago"
# GitHub allows 60 questions per hour without a key, shared by every app on the
# same server: an answer is kept 5 minutes before asking again.
GITHUB_CACHE_SECONDS = 300
# Centro de operación (D-165): while a run is in progress the stage asks GitHub again
# this often; without a token GitHub allows 60 requests an hour, so it waits longer.
LIVE_SECONDS_WITH_TOKEN = 15
LIVE_SECONDS_WITHOUT_TOKEN = 60
OPERATION_RECENT_RUNS = 5
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
ALERT_LIST_HINT = ("**Qué muestra:** los productos cuyo cambio semanal se salió de su rango "
                   "habitual (más de 2 desviaciones estándar respecto de las 12 semanas "
                   "previas). **Cómo leerlo:** el semáforo dice cuán lejos: ● moderada (2 a 3"
                   "), ▲ alta (3 a 4), ◆ muy alta (4 o más); la barra mide esa distancia y la "
                   "marca vertical es el límite de 2.")
ARCHITECTURE_HINT = ("Los datos viajan de izquierda a derecha. **Bronce**: el archivo tal "
                     "como llega. **Limpieza y reglas**: se corrigen formatos y se aplican "
                     "las reglas de negocio. **Calidad**: si algo no cuadra, no se guarda "
                     "nada. **Oro**: la base lista para analizar. Arriba, quién da las "
                     "órdenes; abajo, cómo sabemos qué pasó. El punto de color de cada paso "
                     "es su estado real. Pasa el mouse sobre cada pieza para ver qué hace. "
                     "**Siglas**: ODEPA, Oficina de Estudios y Políticas Agrarias; CSV, archivo "
                     "de valores separados por comas; ETL, extraer, transformar y cargar; RN, "
                     "regla de negocio; SQL, lenguaje de consultas; MD, Markdown.")
# The project page. Texts come from docs/DISENO.md (sections 2 to 4) and DECISIONES.md.
# Idea de negocio, in short pieces: what each card says, without repeating
# «Empieza aquí» (the problem in three sentences lives there).
AUDIENCE_CARDS = [
    ("Analista de pricing o compras", "Márgenes, canales, regiones y alertas.", PAGE_ANALYSIS),
    ("Revisor técnico", "Si el proyecto es confiable: calidad, pruebas y documentos.", TAB_QUALITY),
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
COVER_LIMITS = ("Precios nominales y reales, con el IPC de alimentos del INE. La brecha de precio no mide "
                "ganancias. Los datos describen; no prueban causas.")
SOURCE_LABELS = {"Precios mayoristas": "Diario · frutas y hortalizas",
                 "Precios al consumidor": "Semanal · todos los grupos"}
LIMIT_CARDS = [
    ("Nominales y reales", "Precios e inflación descuenta la inflación de alimentos con el IPC del INE; "
                           "el Resumen compara en pesos de cada semana."),
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
    "el resultado en `weekly_price` del respaldo `datos.db`; dbt hace lo mismo en `datos.duckdb`, la base que lee el panel.")
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
# Why a row is rejected (RN-11), in the words of validate_rows() in etl/etl.py.
REASON_TEXTS = {
    etl.REASON_UNREADABLE_VALUE: "un precio, una fecha o la región no se pudo leer",
    etl.REASON_NON_POSITIVE_PRICE: "un precio (mínimo, máximo o promedio) es cero o negativo",
    etl.REASON_MINIMUM_ABOVE_MAXIMUM: "el precio mínimo es mayor que el máximo",
    etl.REASON_DATE_OUTSIDE_FILE_YEAR: "la fecha no cae en el año del archivo",
    etl.REASON_NON_POSITIVE_VOLUME: "una fila mayorista sin volumen no puede entrar al "
                                    "promedio ponderado (RN-07)",
}
# Short Spanish name of each rejection reason, for the tables (D-141).
REASON_NAMES = {
    etl.REASON_UNREADABLE_VALUE: "Valor ilegible", etl.REASON_NON_POSITIVE_PRICE: "Precio cero o negativo",
    etl.REASON_MINIMUM_ABOVE_MAXIMUM: "Mínimo mayor que máximo",
    etl.REASON_DATE_OUTSIDE_FILE_YEAR: "Fecha fuera del año del archivo",
    etl.REASON_NON_POSITIVE_VOLUME: "Sin volumen",
}
# The fields of a rejected row worth reading, as ODEPA sent them, in Spanish.
REJECTED_ROW_LABELS = {
    "price_date": "Fecha", "week_start": "Semana", "region": "Región", "market": "Mercado",
    "channel": "Canal", "product": "Producto", "variety": "Variedad", "quality": "Calidad",
    "sale_unit": "Unidad de venta", "unit": "Unidad", "volume": "Volumen",
    "min_price": "Precio mínimo", "max_price": "Precio máximo", "avg_price": "Precio promedio",
}
# What each group of project links is for. ODEPA (D-118) moved to its own
# sidebar folder, «Fuentes»: it is not GitHub, so it is not a group here any more.
LINK_GROUP_LEADS = {
    "Código y operación": "Cada ejecución, cada informe y cada cambio.",
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
NOMINAL_PRICES_TEXT = "Precios nominales, sin ajuste por inflación."
# Contexto: nominal prices or real prices deflated with the INE IPC (D-155).
CONTEXT_BASIS_KEY = "context_price_basis"
BASIS_NOMINAL, BASIS_REAL = "Precios del día", "Sin inflación"
BASIS_HELP = ("Precios del día: lo que se pagó cada semana. Sin inflación (IPC): todos los precios en pesos del "
              "último mes publicado por el INE, descontada la inflación de alimentos, para comparar con años "
              "anteriores sin que la inflación los haga parecer caros.")
STATE_ORDER = {"bajo": 0, "dentro": 1, "sobre": 2}
# The switch of Pipeline y linaje: the whole journey first, its dbt stretch on demand.
PIPELINE_VIEW_KEY = "pipeline_view"
PIPELINE_JOURNEY, PIPELINE_LINEAGE = "Recorrido por capas", "Linaje dbt"
LINEAGE_HINT = ("Se dibuja con el manifiesto de la última construcción de dbt, que el pipeline guarda en la "
                "base: si se agrega un modelo o una prueba, aparece aquí en la carga siguiente.")
ATTRIBUTION_TEXT = (
    "Datos: Oficina de Estudios y Políticas Agrarias (ODEPA), Ministerio de "
    "Agricultura de Chile, licencia Creative Commons Atribución; IPC de alimentos: Instituto "
    "Nacional de Estadísticas (INE). Este proyecto no es un producto oficial de ODEPA ni del INE. "
    "Lectura de los datos: el precio nacional es un promedio simple de las regiones, sin ponderar "
    "por población o ventas; cada variación semanal compara las mismas regiones en ambas semanas. "
    "Los indicadores describen el histórico; no predicen precios. Los precios se reconstruyen "
    "desde la fuente en las pruebas automáticas.")
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
    [data-testid="stMain"] h1 {{font-weight:500 !important; letter-spacing:-.035em;}}
    [data-testid="stMain"] h2, [data-testid="stMain"] h3 {{font-weight:500 !important; letter-spacing:-.02em;}}
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
    .devops-layers-title {{ font-size:.7rem; font-weight:600; letter-spacing:.08em;
        text-transform:uppercase; color:{palette["reference"]}; margin:0 0 6px; }}
    .st-key-devops_layers {{ margin-top:10px; }}
    .st-key-devops_layers button {{ justify-content:flex-start !important; min-height:52px;
        padding:10px 16px !important; border-radius:14px !important; background:{palette["card"]} !important;
        border:1px solid {palette["card_border"]} !important;
        box-shadow:0 10px 22px -16px rgba(0,0,0,.3); transition:transform .14s ease; }}
    .st-key-devops_layers button:hover {{ transform:translateY(-2px); border-color:{palette["accent"]} !important; }}
    .st-key-devops_layers button p {{ font-weight:600; font-size:.92rem; }}
    .st-key-devops_layers button [data-testid="stIconMaterial"] {{ color:{palette["accent"]}; }}
    /* Idle pause (D-131): set by IDLE_ANIMATION_SCRIPT after 20 s without activity. */
    .greenocean-idle *, .greenocean-idle *::before, .greenocean-idle *::after {{
        animation-play-state:paused !important; }}
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
    .kpi-strip-value {{ font-size:1.5rem; font-weight:600; line-height:1.15;
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
    .devops-cycle-mobile li {{ display:flex; align-items:flex-start;
        gap:14px; padding:12px 0; border-bottom:1px solid {palette["card_border"]}; }}
    /* A grid of floating cards, not a long list (D-122): the same elevated-card
       language as the KPI gallery and the GitHub page. */
    .technical-rows li {{ display:flex; align-items:flex-start; gap:12px; padding:16px;
        border-radius:14px; background:{palette["card"]}; border:1px solid {palette["card_border"]};
        box-shadow:0 12px 24px -14px rgba(0,0,0,.22), 0 2px 6px -1px rgba(0,0,0,.1);
        transition:transform .15s ease; }}
    .technical-rows li:hover {{ transform:translateY(-3px); }}
    .devops-logos {{ display:flex; gap:6px; flex-shrink:0; width:66px; }}
    .devops-logos svg {{ width:28px; height:28px; }}
    .devops-cycle-mobile span {{ display:block; font-size:.85rem; color:{palette["text"]}; }}
    .technical-rows {{ list-style:none; padding:0; margin:8px 0 20px; display:grid;
        grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:14px; }}
    .technical-rows .component-symbol {{ width:28px; height:30px; margin:0; }}
    /* Layer cards (D-137): compact, floating, the real logo of each tool; auto-fit so
       two cards fill the dialog instead of leaving half of it empty. */
    .layer-cards {{ display:flex; flex-wrap:wrap; gap:16px;
        margin:6px 0 10px; --github-ink:{palette["strong_text"]}; }}
    .layer-card {{ flex:1 1 300px; display:flex; gap:14px; align-items:flex-start; padding:16px 18px;
        border-radius:18px; background:{palette["card"]}; border:1px solid {palette["card_border"]};
        box-shadow:0 14px 28px -16px color-mix(in srgb, var(--brand) 50%, #0004),
                   0 2px 7px -2px rgba(0,0,0,.14);
        transition:transform .16s ease, box-shadow .16s ease; }}
    .layer-card:hover {{ transform:translateY(-4px);
        box-shadow:0 22px 36px -16px color-mix(in srgb, var(--brand) 58%, #0004),
                   0 4px 10px -2px rgba(0,0,0,.16); }}
    .layer-logo {{ flex:none; display:flex; align-items:center; justify-content:center;
        width:44px; height:44px; border-radius:12px; color:var(--brand);
        background:color-mix(in srgb, var(--brand) 14%, transparent); }}
    .layer-logo svg {{ width:24px; height:24px; }}
    .layer-body {{ min-width:0; }}
    .layer-body strong {{ display:block; font-size:.95rem; font-weight:500; line-height:1.3;
        color:{palette["strong_text"]}; letter-spacing:-.01em; }}
    .layer-body p {{ margin:4px 0 6px; font-size:.86rem; line-height:1.45; color:{palette["text"]}; }}
    .layer-note {{ font-size:.75rem; color:{palette["reference"]}; }}
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
    .kpi-value {{ font-size: 2rem; font-weight: 600; color: {palette["strong_text"]};
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
    .section-title {{ font-size: 1.3rem; font-weight: 600; color: {palette["strong_text"]};
                      margin: 0; line-height: 1.3; }}
    .section-lead {{ font-size: 1rem; color: {palette["text"]}; margin: 4px 0 0 0;
                     max-width: 72ch; line-height: 1.5; }}
    .subsection-title {{ font-size: 1.08rem; font-weight: 500; color: {palette["strong_text"]};
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
    .question-number {{ color:{palette["text"]}; font-size:.75rem; font-weight:500;
        letter-spacing:.055em; text-transform:uppercase; margin-bottom:10px; }}
    .question-title {{ color:{palette["strong_text"]}; font-size:clamp(1.15rem,1.45vw,1.48rem);
        font-weight:720; line-height:1.28; max-width:24ch; }}
    .question-scope {{ color:{palette["text"]}; font-size:.94rem; line-height:1.5;
        margin:12px 0 15px; max-width:34ch; }}
    .question-action a {{ color:{palette["accent"]}; font-weight:500;
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
                         width: 28px; height: 28px; border-radius: 50%; font-weight: 600;
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
    .page-lineage {{ margin: -4px 0 4px; }}
    .lineage-badge {{ display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 600;
        padding: 3px 10px; border-radius: 999px; border: 1px solid {palette["card_border"]};
        color: {palette["text"]}; background: {palette["card"]}; }}
    .lineage-badge::before {{ content: ""; width: 7px; height: 7px; border-radius: 50%; background: #9aa4b2; }}
    .lineage-badge.ok::before {{ background: #16a34a; }}
    .lineage-badge.failed::before {{ background: #dc2626; }}
    .lineage-frame {{ max-width: 1100px; margin: 0 auto; }}
    .detail-facts {{ display: grid; gap: 10px 18px; margin-bottom: 8px;
                     grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }}
    .detail-value {{ font-size: 15px; font-weight: 600; color: {palette["strong_text"]}; }}
    table.card-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    table.card-table th {{ text-align: left; color: {palette["text"]}; font-weight: 500;
                          padding: 6px 4px; border-bottom: 1px solid {palette["card_border"]}; }}
    table.card-table td {{ padding: 8px 4px; border-bottom: 1px solid {palette["card_border"]};
                          color: {palette["strong_text"]}; }}
    .link-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                  gap: 14px; margin: 10px 0; }}
    /* Floating, not flush (D-118): the same elevated-card language as the KPI
       gallery (D-114b), shared by this grid wherever it is used. */
    .link-card {{ display: flex; align-items: center; gap: 8px; min-height: 52px;
                  padding: 10px 12px; border-radius: 14px; background: {palette["card"]};
                  border: 1px solid {palette["card_border"]};
                  box-shadow: 0 12px 24px -14px rgba(0,0,0,.22), 0 2px 6px -1px rgba(0,0,0,.1);
                  transition: transform .16s ease, box-shadow .16s ease; }}
    .link-card:hover {{ transform: translateY(-3px);
                        box-shadow: 0 18px 32px -14px rgba(0,0,0,.26), 0 3px 8px -1px rgba(0,0,0,.12); }}
    .link-card a {{ flex: 1; display: flex; align-items: center; gap: 10px;
                    text-decoration: none; min-width: 0; }}
    .link-card .link-icon {{ font-family: "Material Symbols Rounded"; font-size: 22px;
                             color: {palette["accent"]}; }}
    .link-card .link-text {{ display: flex; flex-direction: column; min-width: 0; }}
    .link-card strong {{ color: {palette["strong_text"]}; font-size: 0.9rem; }}
    .link-card small {{ color: {palette["text"]}; font-size: 0.78rem; line-height: 1.3; }}
    .gh-repo-header {{ display: flex; align-items: center; gap: 12px; padding: 14px 18px;
                       margin: 10px 0 22px; border-radius: 14px; background: {palette["card"]};
                       border: 1px solid {palette["card_border"]}; text-decoration: none;
                       color: {palette["strong_text"]}; transition: border-color .12s ease; }}
    .gh-repo-header:hover {{ border-color: {palette["accent"]}; }}
    .gh-repo-slug {{ font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 0.95rem;
                     font-weight: 600; flex: 1; }}
    .gh-repo-open {{ font-size: 0.78rem; color: {palette["accent"]}; }}
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
    /* Pipeline labels a step larger (D-150): the 1560-unit drawing is shown at about
       930 px, which made 13-unit labels near 8 px on screen. */
    [class*="st-key-card_pipeline_main"] svg text[font-size="8"] {{font-size:9.5px;}}
    [class*="st-key-card_pipeline_main"] svg text[font-size="9.5"] {{font-size:11px;}}
    [class*="st-key-card_pipeline_main"] svg text[font-size="12"] {{font-size:13.5px;}}
    [class*="st-key-card_pipeline_main"] svg text[font-size="13"] {{font-size:14.5px;}}
    /* Project documents (D-151): a readable column, clean tables, spaced headings. */
    .doc-source {{font-size:.85rem; margin:-4px 0 14px;}}
    /* A sheet (step 6): centred, with margins on both sides, like a printed page. */
    .st-key-project_document {{max-width:900px; margin:6px auto 30px; padding:44px 60px 48px;
        background:{palette['card']}; border:1px solid {palette['card_border']}; border-radius:16px;
        box-shadow:0 18px 40px -24px rgba(0,0,0,.45), 0 2px 6px -2px rgba(0,0,0,.12);}}
    .st-key-project_document > div > div:first-child h2:first-child {{border-top:none; margin-top:0;}}
    .st-key-project_document .doc-diagram {{background:transparent;}}
    @media (max-width:900px) {{ .st-key-project_document {{padding:22px 18px 26px;}} }}
    .st-key-project_document h2 {{font-size:1.35rem; font-weight:600; letter-spacing:-.02em;
        margin:34px 0 10px; padding-top:14px; border-top:1px solid {palette['card_border']};
        color:{palette['strong_text']};}}
    .st-key-project_document h3 {{font-size:1.05rem; font-weight:500; margin:22px 0 6px;
        color:{palette['strong_text']};}}
    .st-key-project_document p, .st-key-project_document li {{font-size:.95rem; line-height:1.68;
        color:{palette['text']};}}
    .st-key-project_document strong {{color:{palette['strong_text']};}}
    .st-key-project_document blockquote {{border-left:3px solid {palette['accent']}; margin:12px 0;
        padding:8px 16px; background:color-mix(in srgb,{palette['accent']} 6%,transparent);
        border-radius:0 10px 10px 0;}}
    .st-key-project_document table {{width:100%; border-collapse:collapse; margin:10px 0 18px;
        font-size:.86rem; border:1px solid {palette['card_border']}; border-radius:10px; overflow:hidden;}}
    .st-key-project_document th {{background:color-mix(in srgb,{palette['accent']} 7%,{palette['card']});
        color:{palette['strong_text']}; font-weight:500; text-align:left; padding:8px 12px;}}
    .st-key-project_document td {{padding:8px 12px; border-top:1px solid {palette['card_border']};
        vertical-align:top; line-height:1.5;}}
    .st-key-project_document hr {{display:none;}}
    .doc-diagram {{margin:12px 0 22px; padding:14px; border:1px solid {palette['card_border']};
        border-radius:14px; background:{palette['card']};}}
    .doc-diagram .zoom-content > svg {{display:block; width:100%; height:auto; max-height:640px; margin:0 auto;}}
    .st-key-card_pipeline_main {{margin-top:10px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="12"] {{font-size:13px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="13"] {{font-size:15px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="14"] {{font-size:15px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="15"] {{font-size:16px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-main-link svg text[font-size="16"] {{font-size:17px;}}
    .stApp:has(.overview-pipeline) .pipeline-gallery-link:hover svg {{transform:scale(1.01);}}
    .stApp:has(.overview-pipeline) .pipeline-open-label {{
        position:absolute; right:8px; bottom:6px; padding:3px 8px; border-radius:999px;
        color:{palette["strong_text"]}; background:{palette["card"]};
        border:1px solid {palette["card_border"]}; font-size:.68rem; font-weight:500;
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
        font-weight:500;}}
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
        font-weight:600; letter-spacing:-.02em; line-height:1.05; padding:0; margin:0 0 10px;
        color:{palette["strong_text"]}; }}
    .cover-tagline {{ color:{palette["strong_text"]}; font-size:clamp(1.2rem,2.1vw,1.6rem);
        font-weight:600; line-height:1.25; margin:0 0 12px; }}
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
    .cover-figures-title {{ color:{palette["strong_text"]}; font-weight:600; font-size:.95rem;
        margin-bottom:10px; }}
    .cover-figures dl {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
        gap:16px 22px; margin:0; }}
    .cover-figures dt {{ color:{palette["text"]}; font-size:.8rem; font-weight:600; }}
    .cover-figures dd {{ color:{palette["strong_text"]}; font-size:1.75rem; font-weight:600;
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
    .cover-statement h3 {{ color:{palette["strong_text"]}; font-size:1.08rem; font-weight:600;
        margin:0 0 4px; padding:0; }}
    .cover-statement p {{ color:{palette["text"]}; margin:0; line-height:1.45; }}
    .cover-heading {{ color:{palette["strong_text"]}; font-size:1.5rem !important;
        font-weight:600; margin:22px 0 4px !important; padding:0 !important; }}
    .st-key-cover_evidence {{ gap:0 !important; flex-wrap:nowrap !important;
        padding-bottom:18px; border-bottom:1px solid {palette["card_border"]}; }}
    .st-key-cover_evidence > div {{ flex:1 1 0 !important; min-width:0; }}
    [class*="st-key-cover_evidence_"]:not([class*="_link_"]) {{ padding:0 22px; height:100%; }}
    .st-key-cover_evidence > div:first-child [class*="st-key-cover_evidence_"] {{ padding-left:0; }}
    .st-key-cover_evidence > div + div {{ border-left:1px solid {palette["card_border"]}; }}
    .cover-evidence-title {{ color:{palette["strong_text"]}; font-weight:600; font-size:1.05rem;
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
    palette = charts.get_palette(mode)
    # The shared finish is optional: without the file the base style still applies.
    finish_file = Path(__file__).with_name("premium.css")
    finish = finish_file.read_text() if finish_file.exists() else ""
    for token, key in {"CARD": "card", "BORDER": "card_border", "INK": "strong_text",
                       "ACCENT": "accent", "BG": "background"}.items():
        finish = finish.replace("__" + token + "__", palette[key])
    st.markdown(f"<style>{build_style_css(mode)}{finish}</style>", unsafe_allow_html=True)


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
        border-radius:0; padding:4px 0 8px !important; margin:0 0 6px; justify-content:flex-start; column-gap:14px;
        flex-wrap:wrap !important; row-gap:6px;}}
    .st-key-app_header .app-brand {{font-size:.86rem; font-weight:600; color:{palette['strong_text']};
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}}
    /* Volver opens the row, beside the path: Streamlit Cloud draws its own toolbar
       (Share, star, edit, GitHub) over the top right corner. */
    .st-key-header_preferences {{flex-wrap:nowrap !important; align-items:center; gap:8px; width:auto !important;
        order:-1; margin-right:4px;}}
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
        .st-key-header_preferences {{order:0; margin-left:0;}}
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
    """Name, icon and one line of description; the address is never shown as text.
    Opens a new tab (D-116): the same-window convention of D-070 is what made
    GitHub refuse to load when this app runs behind an iframe wrapper (D-113)."""
    return (f'<div class="link-card"><a href="{html.escape(link["url"], quote=True)}" '
            f'target="_blank" rel="noopener noreferrer"><span class="link-icon">{link["icon"]}</span>'
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
            '<svg viewBox="-3 -3 40 44" fill="none" stroke="currentColor" stroke-width="2.2" '
            'stroke-linecap="round" stroke-linejoin="round">'
            '<g transform="translate(1.2 2)" opacity=".24" stroke-width="3.3">' + shape + '</g>'
            '<g fill="currentColor" fill-opacity=".13">' + shape + '</g>'
            '<g transform="translate(-.45 -.55)" stroke="white" opacity=".65" stroke-width=".65">'
            + shape + '</g></svg></span>')


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
                PAGE_PRD, PAGE_SAD, PAGE_ADR):
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
            show_cover_link(pages, PAGE_DIAGRAMS, "Ver la arquitectura", "cover_secondary",
                            help=f"Muestra {ROUTE_LEADS[SECTION_TECHNICAL]}.")
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


IPC_TABLE_DEFINITIONS = {
    "ipc_weekly": "el deflactor de cada semana: el IPC del mes de su lunes frente al último mes publicado, "
                  "para expresar los precios en pesos reales",
    "ipc_monthly": "el IPC de alimentos del INE como una sola serie mensual, base 2023 = 100",
    "ine_ipc_source": "las filas del IPC tal como se leyeron del INE, para rehacer la capa bronce si el INE no responde",
}
TABLE_ROLES = {"weekly_price": "hechos", "dim_product": "dimensión", "dim_region": "dimensión",
              "dim_channel": "dimensión", "dim_date": "dimensión", "etl_run": "auditoría",
              "rejection": "auditoría", "ipc_weekly": "IPC", "ipc_monthly": "IPC", "ine_ipc_source": "IPC"}


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
            '<span class="page-freshness">De dónde viene cada tabla de la base y cómo se relacionan: el modelo estrella convierte los precios en '
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
        background:{palette['card']}; padding:14px 20px 18px;}}
    .st-key-architecture_diagram svg {{display:block; width:100%; height:auto;
        max-height:calc((100vh - 360px) * 1.2);}}
    .arch-legend {{display:flex; flex-wrap:wrap; gap:8px 22px; margin:12px 4px 0; padding-top:10px;
        border-top:1px solid {palette['card_border']}; font-size:12px; line-height:1.5; color:{palette['text']};}}
    .arch-phrase {{font-size:.85rem; color:{palette['strong_text']}; margin:0 0 8px;}}
    .st-key-architecture_detail, .st-key-architecture_tables {{border:1px solid {palette['card_border']};
        border-radius:14px; background:{palette['card']}; padding:12px 16px 10px;}}
    .arch-detail-head {{display:flex; align-items:baseline; gap:10px; flex-wrap:wrap;}}
    .arch-detail-head code {{font-size:1.05rem; font-weight:600; color:{palette['accent']};}}
    .arch-detail-role {{font-size:11px; padding:2px 9px; border-radius:999px;
        background:{palette['field']}; color:{palette['text']};}}
    .arch-detail-rows {{margin-left:auto; font-size:12px; color:{palette['text']};}}
    .arch-detail-text {{font-size:.86rem; line-height:1.5; color:{palette['strong_text']}; margin:7px 0 9px;}}
    .st-key-architecture_tables_list label p {{font-size:.86rem !important;}}
    </style>"""


def show_architecture_page(mode):
    """The star model as one panoramic view (D-147): every table, column, key and row
    count is in the drawing; each table explains itself on hover. No table picker,
    no SQL."""
    row_counts = read_table_row_counts()
    definitions = project.parse_definitions(project.read_section(
        project.read_document(project.PROJECT_GUIDE_FILE), "Modelo de datos"))
    columns = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
    definitions = {**IPC_TABLE_DEFINITIONS, **definitions}
    tooltips = {table: f"{table} · {TABLE_ROLES[table]} · {charts.format_thousands(row_counts[table])} filas\n"
                       f"{definitions.get(table, '').capitalize()}"
                for table in project.TABLE_NAMES + project.IPC_TABLE_NAMES}
    st.markdown(build_architecture_css(mode), unsafe_allow_html=True)
    st.markdown(build_architecture_header(row_counts, read_latest_run()), unsafe_allow_html=True)
    # Two views of the same database (D-189): where each table comes from, and how
    # the tables relate. Each keeps the whole screen.
    view = st.segmented_control("Vista del modelo", MODEL_VIEWS, default=MODEL_VIEWS[0], key=MODEL_VIEW_KEY,
                                label_visibility="collapsed") or MODEL_VIEWS[0]
    if view == MODEL_VIEWS[0]:
        counts, layers, tests = read_database_map(get_database_version())
        st.iframe(database_map.build_map_html(charts.get_palette(mode), counts, layers, tests,
                                              read_store_sizes()), height=660)
        return
    if view == MODEL_VIEWS[3]:
        st.markdown('<p class="arch-phrase">Cada flecha es un punto donde dos bases se tocan, con su número y su comprobación de ahora. '
                    'Pasa el cursor por un número o por un logo.</p>', unsafe_allow_html=True)
        st.iframe(database_crossings.build_crossings_html(charts.get_palette(mode), read_crossing_checks(get_database_version())),
                  height=640)
        return
    if view == MODEL_VIEWS[2]:
        schema = read_er_schema(get_database_version())
        st.markdown('<p class="arch-phrase">El modelo en la notación clásica: cada tabla con sus columnas y tipos, sus claves y las '
                    'relaciones entre ellas. Los tipos se leen de la base.</p>', unsafe_allow_html=True)
        with st.container(key="architecture_diagram"):
            st.markdown(er_diagram.build_er_svg(schema, row_counts, mode, tooltips), unsafe_allow_html=True)
        return
    st.markdown('<p class="arch-phrase">1 fila de weekly_price = un producto '
                '(variedad y calidad) × región × canal × unidad × semana. '
                'Pasa el mouse por una tabla para ver para qué sirve.</p>', unsafe_allow_html=True)
    with st.container(key="architecture_diagram"):
        st.markdown(star_model.build_star_svg(columns, row_counts, mode, tooltips=tooltips),
                    unsafe_allow_html=True)
        st.markdown('<div class="arch-legend"><span><b>PK</b> clave primaria</span>'
                    '<span><b>FK</b> clave foránea</span><span><b>cian</b> medida</span>'
                    '<span>' + build_external_link_html("etl/schema.sql en GitHub",
                                                        project.build_github_url("etl/schema.sql"))
                    + '</span></div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def read_crossing_checks(database_version):
    """The live checks of the «Cruces entre bases» view (D-197)."""
    return database_crossings.read_checks()


@st.cache_data(show_spinner=False)
def read_er_schema(database_version):
    """Columns and DuckDB types of the tables of the entity-relationship diagram (D-195)."""
    return er_diagram.read_schema()


MODEL_VIEWS = ["Dónde viven los datos", "Modelo estrella", "Entidad-relación", "Cruces entre bases"]
MODEL_VIEW_KEY = "model_view"


@st.cache_data(show_spinner=False)
def read_database_map(database_version):
    """Rows of every served table, dbt models per layer and dbt tests, for the map (D-189)."""
    counts = {name: count for name, count, _ in sql_explorer.describe_tables()}
    nodes = queries.run_sql("SELECT resource_type, layer, count(*) AS n FROM dbt_node GROUP BY ALL")
    layers = {row.layer: int(row.n) for row in nodes.itertuples() if row.resource_type == "model"}
    tests = int(nodes.loc[nodes["resource_type"] == "test", "n"].sum())
    return counts, layers, tests


# raw.db is 665 MB on the author's computer and never in the repository (D-020); where
# the file is missing, the documented size is shown with an approximation sign.
RAW_DATABASE_SIZE_TEXT = "≈ 665 MB"


def format_file_size(size):
    megabytes = size / 1_000_000
    return f"{megabytes:,.0f} MB".replace(",", ".") if megabytes >= 10 else f"{megabytes:.1f} MB".replace(".", ",")


def read_store_sizes():
    """{store key: size text} of the files of the storage diagram that exist here (D-191)."""
    sizes = {}
    for key, path in (("served", queries.DATABASE_FILE), ("backup", etl.BASE_DIR / "datos.db")):
        if Path(path).exists():
            sizes[key] = format_file_size(Path(path).stat().st_size)
    raw = etl.RAW_DATABASE_FILE
    sizes["raw"] = format_file_size(raw.stat().st_size) if raw.exists() else RAW_DATABASE_SIZE_TEXT
    return sizes


@st.cache_data
def count_cached_table_rows(database_version, tables):
    """Rows of each table of the data warehouse, counted once per database. The list of
    tables is part of the cache key: a table added by a deploy never meets an old count."""
    return project.count_table_rows()


def read_table_row_counts():
    return count_cached_table_rows(get_database_version(), tuple(project.TABLE_NAMES + project.IPC_TABLE_NAMES))


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
    st.markdown(build_external_link_html("Ver la consulta en GitHub", build_query_address(name)),
                unsafe_allow_html=True)


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
                st.markdown(build_external_link_html("Ver en GitHub", build_query_address(query_name)),
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
    text = (f"En datos.duckdb: {evidence}" if evidence != "—"
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


# region Código y resultados (C03)
CATALOG_TREND_WEEKS = 26
CATALOG_BAR_COUNT = 12
CATALOG_FILES = {project.MATCH_COVERAGE_QUERY_NAME: "etl/etl.py"}
QUERIES_PATH = "bi/queries.sql"


def build_query_address(name):
    """The query in GitHub, the source of truth of the code (D-143)."""
    path, line = find_catalog_line(name)
    return f"{project.build_github_url(path)}#L{line}"


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
     "compares": "Muestra cada fila rechazada tal como llegó, con su fuente (wholesale = precios "
                 "mayoristas, consumer = precios al consumidor) y su motivo.",
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


def show_compact_page_header(title, description):
    """A one-line header, like the Dashboard's: title and freshness together; the
    description shows on hover instead of taking a line of its own."""
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    run_text = "Carga correcta" if run_kind == "ok" else "Última carga con falla"
    freshness = format_chile_time(parse_run_start(latest_run["started_at"]))
    st.markdown(f'<div class="compact-header"><h1 title="{html.escape(description, quote=True)}">'
                f'{html.escape(title)}</h1><span class="page-freshness">Datos al '
                f'{freshness} {build_chip(run_text, run_kind)}</span></div>',
                unsafe_allow_html=True)


# endregion


def show_idea_tab(mode):
    """Business definition, scope and acceptance criteria, read from the project brief."""
    brief = project.read_guide_table("Marco de negocio")
    for row in brief:
        st.markdown(build_info_card_html(row["Elemento"], row["Definición"],
            component=row["Forma"]), unsafe_allow_html=True)
    show_section_intro("Entregables", "Resultados verificables del proyecto.", True)
    st.markdown(build_place_link(PAGE_HOME, "Dashboard:") + " · "
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


@st.cache_data
def read_cached_week_snapshot(database_version, week):
    """The regional index (K3) of one week of valid observations."""
    sql = ("SELECT * FROM (" + queries.read_query_body("k3_regional_index") + ") "
           "WHERE week_start = ?")
    return add_display_columns(queries.run_sql(sql, parameters=(week,)))


def read_cached_market_snapshot(database_version):
    """The regional index (K3) of the latest week."""
    return read_cached_week_snapshot(database_version, f"{read_latest_week():%Y-%m-%d}")


def keep_covered_cells(points):
    """Channels and regions with data in at least half of the other axis: the map never
    shows rows or columns that are almost all «Sin dato»."""
    for axis, other in [("channel", "region"), ("region", "channel")]:
        coverage = points.groupby(axis)[other].nunique() / max(points[other].nunique(), 1)
        points = points[points[axis].isin(coverage[coverage >= MINIMUM_MAP_COVERAGE].index)]
    return points


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


def regional_week_changes(current, previous):
    """Compare the same product, channel and region in two exact consecutive weeks."""
    keys = list(queries.KEY_COLUMNS) + ["region", "channel"]
    merged = current.merge(previous[keys + ["price"]].rename(columns={"price": "previous_price"}),
                           on=keys, how="left", validate="one_to_one")
    valid = merged["previous_price"].gt(0) & merged["price"].notna()
    merged["weekly_change"] = ((merged["price"] / merged["previous_price"] - 1) * 100).where(valid)
    return merged


def describe_week_span(week):
    """«05–11 oct 2026»: the Monday and the Sunday of the analyzed week."""
    start = pd.Timestamp(week)
    end = start + pd.Timedelta(days=6)
    months = charts.MONTH_NAMES
    if start.month == end.month:
        return f"{start:%d}–{end:%d} {months[end.month - 1]} {end.year}"
    return f"{start:%d} {months[start.month - 1]} – {end:%d} {months[end.month - 1]} {end.year}"


def read_report_gaps(week, group, region, product):
    """The week's gaps under the report's filters: (comparable, left out above +300 %)."""
    gaps = read_cached_week_gaps(get_database_version(), week)
    if group != ALL_VALUES:
        gaps = gaps[gaps["product_group"] == group]
    if region != ALL_VALUES:
        gaps = gaps[gaps["region"] == region]
    return split_comparable_gaps(keep_product(gaps, product))


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
        if (!params.has('_home_region') || params.has('_home_key') || params.has('vista')) return;
        event.preventDefault();
        setTriggerValue('link', url.search);
    };
    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
}
"""
HOME_LINK_PARAMETERS = ("_home_region", "_home_week", "familia")


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
    for name in HOME_LINK_PARAMETERS:
        if parameters.get(name):
            st.query_params[name] = parameters[name][0]
        else:
            st.query_params.pop(name, None)


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
    matched = snapshot[regional].merge(prior[regional], on=join + ['region'], suffixes=('', '_before'))
    same = matched.groupby(join, as_index=False).agg(_same_now=('price', 'mean'),
                                                     _same_before=('price_before', 'mean'),
                                                     _same_regions=('region', 'nunique'),
                                                     _quotes_now=('observation_count', 'sum'),
                                                     _quotes_before=('observation_count_before', 'sum'))
    regions_now = snapshot.groupby(join).region.nunique().rename('_regions_now')
    regions_before = prior.groupby(join).region.nunique().rename('_regions_before')
    # The prices shown stay the national price of each week (every region with a price),
    # the same figure Contexto de precios shows; only the change is like for like (D-153).
    rows = (variations.drop(columns=['variation', 'change_amount'])
            .merge(same, on=join, how='left')
            .merge(regions_now, on=join, how='left').merge(regions_before, on=join, how='left'))
    valid = rows['_same_before'].gt(0) & rows['_same_now'].notna()
    rows['variation'] = (rows['_same_now'] / rows['_same_before'] - 1).where(valid)
    rows['change_amount'] = (rows['_same_now'] - rows['_same_before']).where(valid)
    rows['_coverage_changed'] = valid & ((rows['_regions_now'] != rows['_same_regions'])
                                         | (rows['_regions_before'] != rows['_same_regions']))
    return rows


def summarize_family_coverage(variations):
    """Per family, the same counts as the coverage note: prices this week, those with a
    valid change (the rows of the family table), single-quote changes and changes that
    left a region out, so the note can speak of the family the table shows."""
    valid = variations.variation.notna() & variations.variation.abs().lt(float('inf'))
    rows = variations.assign(_valid=valid,
                             _thin=variations.get('_single_quote', False),
                             _changed=variations.get('_coverage_changed', False))
    return {family: {'available': len(group), 'comparable': int(group._valid.sum()),
                     'single_quote': int((group._thin & group._valid).sum()),
                     'coverage_changed': int((group._changed & group._valid).sum())}
            for family, group in rows.groupby('product_group')}


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
        variations=compare_same_regions(variations,snapshot,prior,join)
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
    # D-146: a change resting on a single quote in either week is one isolated price,
    # not a market movement; it stays in the family median but not in the ranking.
    thin=pd.Series(False,index=variations.index)
    if region == ALL_VALUES and '_quotes_now' in variations:
        thin=variations.variation.notna() & ((variations._quotes_now<2) | (variations._quotes_before<2))
    variations['_single_quote']=thin
    ranked=home_mockup.order_movements(variations[~thin],count,order)
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
                single_quote=int(thin.sum()),
                family_coverage=summarize_family_coverage(variations),
                week_label=f'{week_date:%d-%m-%Y}',previous_label=f'{pd.Timestamp(previous_week):%d-%m-%Y}')


# A region's direction must be told apart from a coin toss (D-146).
REGION_DIRECTION_P_VALUE = 0.05


def sign_test_p_value(up, down):
    """Two-sided exact sign test: the chance of a split at least this uneven if a rise
    and a fall were equally likely."""
    up, down = int(up), int(down)
    total = up + down
    if not total:
        return 1.0
    tail = sum(math.comb(total, count) for count in range(max(up, down), total + 1))
    return min(1.0, 2 * tail / 2 ** total)


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
            if state in ('rise', 'fall') and sign_test_p_value(up, down) >= REGION_DIRECTION_P_VALUE:
                state = 'mixed'
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
        return f'background-color:{background};color:{foreground};font-weight:600'
    def change_css(value):
        foreground = ('#ff8a96' if dark else '#b91c1c') if value.startswith('+') else ('#83baff' if dark else '#1d4ed8')
        return f'color:{foreground};font-weight:600'
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
        icons = {'Hortalizas': '🥬', 'Frutas': '🍎', 'Pan': '🍞',
                 'Carne bovina': '🥩', 'Abarrotes y otros': '🥫'}
        # Every family gets the same tile (D-150): the number of alerts is written on it,
        # so neither the shape nor the colour has to stand for a quantity.
        tile_css = []
        for index, family in enumerate(families):
            icon = icons.get(family, '🍗' if 'Cerdo' in family else '🥚')
            tile_css.append(f'.st-key-home_alert_card_{index}'
                            '{--alert-tone:#db3349;--alert-shape:inset(0 round 24%);}'
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
    """The family table under the chosen order; ties stay in a stable, readable order.
    A change resting on a single quote sorts after the others (D-146)."""
    names = lambda row: (str(row['product']), str(row['variety']), str(row['channel']))
    thin = lambda row: bool(row.get('_single_quote'))
    if order == 'Nombre':
        return sorted(rows, key=names)
    if order == 'Subidas':
        return sorted(rows, key=lambda row: (thin(row), -row['variation'], names(row)))
    if order == 'Bajadas':
        return sorted(rows, key=lambda row: (thin(row), row['variation'], names(row)))
    if order == 'Inusuales':
        # National alerts only, the most unusual first (distance to the usual range).
        return sorted((row for row in rows if row.get('is_alert')),
                      key=lambda row: (-row.get('_severity', 0), names(row)))
    return sorted(rows, key=lambda row: (thin(row), -abs(row['variation']), names(row)))


def show_market_overview(mode, prefix):
    """Map, movement by family and products of one family on one screen (D-092)."""
    # Streamlit reruns this file without reimporting helpers; keep the live page
    # in sync when the dashboard markup changes during development.
    importlib.reload(home_mockup)
    st.markdown(home_mockup.style(mode,charts.get_palette(mode)),unsafe_allow_html=True)
    options=read_cached_filter_options(get_database_version())
    apply_home_link_click()
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
    show_alert_trigger()
    st.markdown('<div class="greenocean-mockup">' + home_mockup.dashboard_header(
        describe_week_span(week), updated, latest['status']==etl.STATUS_LOADED, model['family_rows'],
        regional_rows, None if region == ALL_VALUES else region, compared=sum(model['counts']),
        available=model['available'], alerts=model['alert_count'] if region == ALL_VALUES else None)
        + '</div>', unsafe_allow_html=True)
    map_column, detail_column = st.container(key='home_overview').columns([0.7, 1.3], gap='small')
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
            search_column, channel_column, order_column = st.columns(
                [1.35, 1.25, 1.5], vertical_alignment='center')
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
            st.markdown('<div class="greenocean-mockup">' + home_mockup.products_table(
                rows, model['week_label'], model['previous_label'], query.strip()) + '</div>', unsafe_allow_html=True)
    # Under both columns, full width (D-150): the note no longer lengthens one side.
    st.markdown('<div class="greenocean-mockup">' + home_mockup.coverage_note(
        model, build_page_address(PAGE_OPERATIONS), build_page_address(PAGE_DOCUMENTATION), family)
        + '</div>', unsafe_allow_html=True)


def show_home_page(mode):
    """Market dashboard with latest-week rankings; diagrams have their own destination."""
    with st.container(key="market_dashboard"):
        show_market_overview(mode, "home")


def show_pipeline_page_header():
    """The same one-line header as every technical page (D-150)."""
    show_compact_page_header("Pipeline y linaje", "El recorrido de los datos, de ODEPA y el INE al panel, "
                             "y el linaje de dbt con el estado de sus pruebas.")


@st.cache_data
def read_lineage(database_version):
    """(nodes, results) of the last dbt build, as the pipeline saved them."""
    return lineage.read_tables(queries.run_sql)


def show_pipeline_figures(summary):
    """One strip of four real figures: the latest load and the latest dbt build."""
    run = read_latest_run()
    tests = (f'{summary["passing"]}/{summary["tests"]}', "superadas en la última construcción") if summary \
        else ("—", "linaje dbt en migración")
    st.markdown('<div class="runs-metrics">'
                + build_runs_metric_html("Filas leídas", charts.format_thousands(run["rows_read"]),
                                         "de los archivos de ODEPA")
                + build_runs_metric_html("Filas cargadas", charts.format_thousands(run["rows_loaded"]),
                                         f'{charts.format_thousands(run["rows_rejected"])} rechazadas, con su motivo')
                + build_runs_metric_html("Modelos dbt", str(summary["models"]) if summary else "—",
                                         "staging, intermedio y marts")
                + build_runs_metric_html("Pruebas dbt", *tests)
                + '</div>', unsafe_allow_html=True)


def show_diagrams_page(mode):
    """Pipeline y linaje (step 4 of the refonte): the figures of the latest load and
    build, then one card with a switch. It opens on the whole journey by layers
    (D-136), with its dbt stretch framed; «Linaje dbt» opens that stretch model by
    model, from the build's own manifest."""
    states, figures, pipeline_run, latest_load, error_note = read_journey()
    show_pipeline_page_header()
    nodes, results = read_lineage(get_database_version())
    summary = lineage.summarize_build(nodes, results)
    st.markdown(build_runs_css(mode), unsafe_allow_html=True)
    show_pipeline_figures(summary)
    view = st.session_state.get(PIPELINE_VIEW_KEY, PIPELINE_JOURNEY) if summary else PIPELINE_JOURNEY
    lineage_view = view == PIPELINE_LINEAGE
    title = "Dentro del tramo dbt: modelo por modelo" if lineage_view else "Recorrido completo por capas"
    with open_card("pipeline_main", title, hint=LINEAGE_HINT if lineage_view else ARCHITECTURE_HINT):
        if summary:
            st.segmented_control("Vista", [PIPELINE_JOURNEY, PIPELINE_LINEAGE], default=PIPELINE_JOURNEY,
                                 key=PIPELINE_VIEW_KEY, label_visibility="collapsed")
        if lineage_view:
            st.markdown(zoom.build_zoom_frame_html(lineage.build_lineage_svg(nodes, results, mode),
                                                   "diagram-wide"), unsafe_allow_html=True)
            if getattr(lineage, "LINEAGE_SCRIPT", ""):
                # Hovering a model follows only its inputs and outputs; a click pins them.
                st.html(lineage.LINEAGE_SCRIPT, unsafe_allow_javascript=True)
        else:
            # Inline SVG (not an image), so each piece shows its explanation on hover.
            st.markdown(zoom.build_zoom_frame_html(
                            architecture.build_journey_svg(states, figures, mode, animate_flow=True),
                            "diagram-wide")
                        + zoom.build_zoom_frame_html(
                            architecture.build_vertical_journey_svg(states, figures, mode, animate_flow=True),
                            "diagram-narrow"), unsafe_allow_html=True)
            st.markdown(build_journey_legend_html(), unsafe_allow_html=True)
        st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)
        st.html(zoom.TIP_SCRIPT, unsafe_allow_javascript=True)


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
    st.caption(f"{len(shown_rows)} alertas filtradas · se muestran {min(shown_count,len(shown_rows))}. Alcance nacional: promedio simple de las mismas regiones en ambas semanas, sin ponderación por ventas.")
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
def read_context_regional_prices(database_version):
    """Every valid regional price of the Contexto channels, read once per load."""
    channels = ", ".join("?" for _ in CONTEXT_CHANNELS)
    rows = queries.run_sql(f"""SELECT wp.week_start, p.product_group, p.product, p.variety, p.quality,
                                      ch.channel, wp.normalized_unit, wp.region_id, wp.price
                               FROM weekly_price wp JOIN dim_product p USING(product_id)
                               JOIN dim_channel ch USING(channel_id)
                               WHERE wp.flag IS NULL AND ch.channel IN ({channels})""",
                           parameters=list(CONTEXT_CHANNELS))
    rows["week_start"] = pd.to_datetime(rows["week_start"])
    return rows


def keep_regions_of_week(regional, week):
    """One series over the regions with a price in `week` (D-146): every past week
    averages those same regions, so a usual range compares like with like instead of
    whichever regions reported each year. Returns week_start, national_price."""
    regions = set(regional.loc[regional["week_start"] == week, "region_id"])
    same = regional[regional["region_id"].isin(regions)]
    return (same.groupby("week_start", as_index=False)["price"].mean()
            .rename(columns={"price": "national_price"}))


@st.cache_data
def read_ipc_weekly(database_version):
    """The deflator of every week (D-155): IPC de alimentos del INE, month of the Monday."""
    rows = queries.run_sql("SELECT week_start, real_factor, provisional, reference_year, reference_month "
                           "FROM ipc_weekly")
    return rows.assign(week_start=pd.to_datetime(rows["week_start"]))


def describe_ipc_reference(ipc):
    """«septiembre 2026», the month whose pesos the real prices are in."""
    first = ipc.iloc[0]
    return f"{price_context.MONTHS[int(first['reference_month']) - 1]} {int(first['reference_year'])}"


def deflate_series(rows, ipc):
    """Real prices (D-155): each week's national price × its IPC factor, in pesos of the
    last published month. The nominal price stays beside it as nominal_price."""
    rows = rows.merge(ipc[["week_start", "real_factor"]], on="week_start", how="left")
    rows["nominal_price"] = rows["national_price"]
    rows["national_price"] = rows["national_price"] * rows["real_factor"]
    return rows.drop(columns="real_factor")


@st.cache_data
def read_context_model(database_version, key_items, week, real=False):
    """Everything the page shows for one product, computed once per weekly load.
    real=True: the series, its usual range and its states, in real pesos (D-155)."""
    key = dict(key_items)
    regional = read_context_regional_prices(database_version)
    mask = pd.Series(True, index=regional.index)
    for field, value in key.items():
        mask &= regional[field] == value
    product = regional[mask]
    week = pd.Timestamp(week)
    dates = read_dim_date(database_version)
    target_iso, month = describe_target_week(dates, week)
    # ISO week and month come from dim_date, the calendar of the data warehouse.
    series = {channel: keep_regions_of_week(product[product["channel"] == channel], week)
              .merge(dates, on="week_start", how="left")
              .sort_values("week_start").reset_index(drop=True) for channel in CONTEXT_CHANNELS}
    dates_indexed = dates.set_index("week_start")
    series = {channel: rows for channel, rows in series.items() if not rows.empty}
    if real:
        ipc = read_ipc_weekly(database_version)
        series = {channel: deflate_series(rows, ipc) for channel, rows in series.items()}
    weekly = []
    now = {}
    for channel, rows in series.items():
        context = price_context.weekly_context(rows, week, dates=dates_indexed)
        context = context.assign(channel=channel)
        if real:
            context = context.merge(rows[["week_start", "nominal_price"]], on="week_start", how="left")
        weekly.append(context)
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
            "patterns": patterns, "pattern_years": years, "seasonal": seasonal, "month": month,
            "year": year, "margins": read_context_margins(key, week, dates, target_iso, database_version)}


def read_context_margins(key, week, dates, target_iso, database_version):
    """K1 back in sight (D-146): what the consumer pays over the wholesale price, per
    consumer channel, with its usual range. Both prices share week, region, product
    key and unit (RN-06); the regions are those with a pair this week, in every week.
    {channel: {value, usual, state, regions}}; empty for a product without wholesale price.
    """
    pairs = read_cached_rows_for_key("k1_margin", tuple(sorted(key.items())), database_version)
    if pairs.empty:
        return {}
    pairs = pairs.assign(week_start=pd.to_datetime(pairs["week_start"]))
    margins = {}
    for channel in CONTEXT_CHANNELS:
        rows = pairs[pairs["channel"] == channel].rename(columns={"margin": "price"})
        if not rows["week_start"].eq(week).any():
            continue
        regions = set(rows.loc[rows["week_start"] == week, "region"])
        series = (rows[rows["region"].isin(regions)].groupby("week_start", as_index=False)["price"].mean()
                  .rename(columns={"price": "national_price"}).merge(dates, on="week_start", how="left"))
        value = float(series.loc[series["week_start"] == week, "national_price"].iloc[0])
        usual = price_context.rango_habitual(series, week, target_iso)
        margins[channel] = {"value": value, "usual": usual, "regions": len(regions),
                            "state": price_context.estado_precio(value, usual)}
    return margins


@st.cache_data
def read_family_outliers(database_version, product_group, week, exclude_product, exclude_variety):
    """Other products of the same family whose price is outside its own habitual range.

    One row per product/channel with a price this week that is «sobre» or «bajo» lo
    habitual (the same ±1 ISO-week rule as the main chart), sorted by how far past
    the limit it is, farthest first (D-098).
    """
    regional = read_context_regional_prices(database_version)
    family = regional[regional["product_group"] == product_group]
    dates = read_dim_date(database_version)
    week = pd.Timestamp(week)
    target_iso, _ = describe_target_week(dates, week)
    results = []
    group_columns = ["product", "variety", "quality", "normalized_unit", "channel"]
    for key_values, group in family.groupby(group_columns):
        product, variety, quality, unit, channel = key_values
        if product == exclude_product and variety == exclude_variety:
            continue
        if not group["week_start"].eq(week).any():
            continue
        group = keep_regions_of_week(group, week).merge(dates, on="week_start", how="left")
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


def describe_context_option(option):
    """«Tomate · Larga vida — Primera, kilo»: what the search field shows and matches."""
    name = option["product"] if option["variety"] == UNSPECIFIED else f"{option['product']} · {option['variety']}"
    return f"{name} — {option['quality']}, {option['normalized_unit']}"


def choose_context_product(options, key, column):
    """One search field over every product, quality and unit (step 5 of the refonte):
    typing filters the list, as in the Resumen; the family is in the breadcrumb."""
    choices = [tuple(row) for row in options[queries.KEY_COLUMNS].itertuples(index=False)]
    current = tuple(key[field] for field in queries.KEY_COLUMNS)
    labels = {choice: describe_context_option(dict(zip(queries.KEY_COLUMNS, choice))) for choice in choices}
    chosen = column.selectbox("Buscar producto", choices, index=choices.index(current) if current in choices else 0,
                              format_func=labels.get, key=f"context_search_{'_'.join(map(str, current))}",
                              placeholder="Escribe un producto…")
    chosen = dict(zip(queries.KEY_COLUMNS, chosen))
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


def build_context_margin_card(margins):
    """The consumer price over the wholesale price, per channel, against its usual range."""
    if not margins:
        return ('<section class="ctx-card"><h3>Sobre el precio mayorista</h3><div class="ctx-foot">'
                'Este producto no tiene precio mayorista comparable: el cruce solo existe para frutas '
                'y verduras con la misma unidad en ambas fuentes.</div></section>')
    rows = []
    for channel, item in margins.items():
        usual = item["usual"]
        habit = (f'Habitual: {charts.format_signed_percent(usual[0] * 100)} a '
                 f'{charts.format_signed_percent(usual[1] * 100)}' if usual else 'Habitual: sin historia suficiente')
        label, kind = STATE_CHIPS[item["state"]]
        rows.append(f'<div class="ctx-price-row"><i style="background:{charts.CONTEXT_CHANNELS[channel]}"></i>'
                    f'<div><strong>{channel}</strong><small>{habit}</small></div><div class="ctx-price">'
                    f'<b>{charts.format_signed_percent(item["value"] * 100)}</b>'
                    f'<span class="ctx-state {kind}">{label}</span></div></div>')
    hint = build_hint_icon("Cuánto paga el consumidor sobre el precio mayorista, en la misma semana, región, "
                           "producto y unidad (K1). No es ganancia: no descuenta transporte ni costos.")
    return (f'<section class="ctx-card"><h3>Sobre el precio mayorista{hint}</h3>' + "".join(rows) + '</section>')


def split_yearly_change(rows, ipc, week):
    """What a year of price change owes to food inflation (D-161). rows: one channel's
    nominal national prices. Between the same week a year ago and this week, the
    inflation part is what the old price would have risen with the food IPC; the rest is
    the product's own movement. An accounting split, not a cause. None without both prices."""
    week = pd.Timestamp(week)
    before = week - pd.Timedelta(weeks=52)
    prices = rows.set_index("week_start")["nominal_price" if "nominal_price" in rows else "national_price"]
    factors = ipc.set_index("week_start")["real_factor"]
    if not {week, before} <= set(prices.dropna().index) or not {week, before} <= set(factors.index):
        return None
    now, then = float(prices[week]), float(prices[before])
    inflation = then * factors[before] / factors[week] - then
    return {"before": before, "then": then, "now": now, "change": now - then,
            "inflation": inflation, "own": now - then - inflation}


def build_split_html(split):
    """One line and a two-part bar: inflation in grey, the product's own part in colour."""
    if not split:
        return ""
    money = lambda value: ("+" if value >= 0 else "−") + "$" + charts.format_thousands(abs(value))
    total = abs(split["inflation"]) + abs(split["own"]) or 1
    inflation_width = abs(split["inflation"]) / total * 100
    own_kind = "up" if split["own"] >= 0 else "down"
    return (f'<div class="ctx-split" title="Desde la semana del {split["before"]:%d-%m-%Y}: '
            f'${charts.format_thousands(split["then"])} → ${charts.format_thousands(split["now"])}">'
            f'<small>12 meses: <b>{money(split["change"])}</b> = inflación {money(split["inflation"])} · '
            f'propio {money(split["own"])}</small>'
            f'<span class="ctx-split-bar"><b class="inf" style="width:{inflation_width:.1f}%"></b>'
            f'<b class="{own_kind}" style="width:{100 - inflation_width:.1f}%"></b></span></div>')


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
                    f'<small>{habit}</small>{build_split_html(item.get("split"))}</div><div class="ctx-price"><b>{price}</b>'
                    f'<span class="ctx-state {kind}">{label}</span></div></div>')
    hint = build_hint_icon(f"Precio por {unit}. Habitual = percentil 25 a 75 de la misma semana ISO "
                           "(y la semana antes y después) en años anteriores. 12 meses: cuánto cambió el precio "
                           "desde la misma semana del año pasado, y qué parte equivale a la inflación de "
                           "alimentos (IPC del INE) y qué parte es propia del producto. Es una cuenta, no una causa.")
    return (f'<section class="ctx-card"><h3>Precio esta semana{hint}</h3>' + "".join(rows) + '</section>')


def build_context_next_card(patterns, pattern_years, month, seasonal=None, year=None):
    """3 months × 2 channels, as a compact strip: month, arrow and % change (D-098).
    A month shows its change only when at least 3 previous years agree on its
    direction (D-146); otherwise «sin patrón claro»."""
    months = [(month - 1 + step) % 12 + 1 for step in range(1, 4)]
    header = "".join(f'<th>{price_context.MONTHS[following - 1][:3].capitalize()}</th>' for following in months)
    channel_rows = []
    any_history = False
    for channel in CONTEXT_CHANNELS:
        years = pattern_years.get(channel, 0)
        pattern = patterns.get(channel, {})
        if years < price_context.MINIMUM_YEARS:
            cells = '<td colspan="3" class="ctx-next-empty">Sin historia suficiente</td>'
        else:
            any_history = True
            changes = dict(price_context.proximos_meses(pattern, month, count=3))
            cells = ""
            for following in months:
                change = changes.get(following)
                agreeing, compared = (price_context.acuerdo_entre_anios(
                    seasonal[seasonal["channel"] == channel], month, following, year)
                    if seasonal is not None else (0, 0))
                if change is None:
                    cells += '<td>—</td>'
                elif seasonal is not None and not price_context.tiene_patron_claro(agreeing, compared):
                    cells += (f'<td class="ctx-next-unclear" title="Solo {agreeing} de {compared} años '
                              'coinciden en la dirección: sin patrón claro.">sin patrón</td>')
                else:
                    arrow = "▲" if change > 0.05 else "▼" if change < -0.05 else "▬"
                    cells += f'<td class="{"rise" if change > 0.05 else "fall" if change < -0.05 else ""}">' \
                             f'{arrow} {charts.format_percent(abs(change))}</td>'
        color = charts.CONTEXT_CHANNELS[channel]
        channel_rows.append(f'<tr><th><i style="background:{color}"></i>{channel}</th>{cells}</tr>')
    hint = build_hint_icon("Cambio típico del índice estacional frente a este mes, por canal, en años "
                           "anteriores. Se muestra solo si al menos 3 años coinciden en la dirección. "
                           "Es un patrón histórico, no un pronóstico.")
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
    # Not the alerts: an alert is an unusual change from one week to the next (K6); this
    # table is a price level unusual for the time of year, as the chart above.
    title = (f'<h3>Otros productos de {html.escape(product_group)} con precio fuera de lo habitual para la época{hint}</h3>'
             '<p class="ctx-table-lead">No son las alertas: una alerta es un cambio brusco de una semana a otra; '
             'aquí, un precio alto o bajo para esta época del año, como en el gráfico de arriba.</p>')
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


@st.cache_data
def read_ipc_monthly(database_version):
    """The food IPC of the INE, month by month since prices start (2022), base 2023 = 100."""
    rows = queries.run_sql("SELECT year, month, food_index, origin FROM ipc_monthly WHERE year >= 2022 "
                           "ORDER BY year, month")
    rows["month_start"] = pd.to_datetime(dict(year=rows["year"], month=rows["month"], day=1))
    rows["yearly"] = rows["food_index"].pct_change(12) * 100
    return rows


@st.dialog("IPC de alimentos del INE", width="large")
def show_ipc_dialog(mode):
    """The deflator itself (D-155): the monthly food IPC the real prices are computed with."""
    rows = read_ipc_monthly(get_database_version())
    first, last = rows.iloc[0], rows.iloc[-1]
    year_ago = rows.iloc[-13] if len(rows) > 12 else first
    month = lambda row: f"{price_context.MONTHS[int(row['month']) - 1]} {int(row['year'])}"
    total = (last["food_index"] / first["food_index"] - 1) * 100
    yearly = (last["food_index"] / year_ago["food_index"] - 1) * 100
    st.caption(f"División 1 «Alimentos y bebidas no alcohólicas», base 2023 = 100. De {month(first)} a "
               f"{month(last)} los alimentos subieron {charts.format_signed_percent(total)}; en los últimos 12 meses, "
               f"{charts.format_signed_percent(yearly)}.")
    palette = charts.get_palette(mode)
    x = alt.X("month_start:T", title=None, axis=alt.Axis(format="%b %Y", tickCount=8))
    tooltip = [alt.Tooltip("month_start:T", title="Mes", format="%m-%Y"),
               alt.Tooltip("food_index:Q", title="Índice", format=",.2f"),
               alt.Tooltip("yearly:Q", title="Variación 12 meses (%)", format="+.1f")]
    # No area: an area anchors the axis at 0 and flattens a +45 % rise into a flat line.
    line = alt.Chart(rows).mark_line(strokeWidth=2.6, color=palette["accent"], interpolate="monotone").encode(
        x=x, y=alt.Y("food_index:Q", title="Índice (2023 = 100)", scale=alt.Scale(zero=False)), tooltip=tooltip)
    point = alt.Chart(rows.tail(1)).mark_point(filled=True, size=70, color=palette["accent"]).encode(
        x=x, y="food_index:Q", tooltip=tooltip)
    show_chart(charts.apply_chart_style(alt.layer(line, point).properties(height=300), mode))
    st.caption(f"Cada semana usa el IPC del mes de su lunes; los precios «sin inflación» quedan en pesos de "
               f"{month(last)}. Las semanas de un mes que el INE aún no publica usan ese último mes y se marcan "
               "provisionales. Antes de 2024, la serie empalmada del INE enlazada por la variación oficial de "
               "enero 2024 (D-155).")


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
    .ctx-title h1 {{font-size:23px!important;font-weight:400;margin:0!important;padding:0!important;display:inline;}}
    .ctx-answer b {{font-weight:500;color:{palette['strong_text']};}}
    [class*="st-key-inf_card_"] {{gap:2px!important;border:1px solid {palette['card_border']};border-radius:16px;padding:10px 12px 2px;
        background:linear-gradient(180deg,color-mix(in srgb,{palette['card']} 92%,{'#fff' if palette['base'] != charts.BASE_DARK else '#000'}) 0%,{palette['card']} 100%);
        box-shadow:{'0 1px 0 rgba(255,255,255,.07) inset, 0 22px 40px -28px rgba(0,0,0,.9), 0 0 0 1px rgba(255,255,255,.03)' if palette['base'] == charts.BASE_DARK else '0 1px 0 #fff inset, 0 22px 40px -30px rgba(15,27,45,.45), 0 6px 14px -10px rgba(15,27,45,.18)'};
        transition:transform .25s ease,box-shadow .25s ease;}}
    [class*="st-key-inf_card_"]:hover {{transform:translateY(-3px);
        box-shadow:{'0 1px 0 rgba(255,255,255,.09) inset, 0 30px 50px -28px rgba(0,0,0,.95), 0 0 0 1px rgba(255,255,255,.05)' if palette['base'] == charts.BASE_DARK else '0 1px 0 #fff inset, 0 30px 50px -28px rgba(15,27,45,.5), 0 10px 18px -10px rgba(15,27,45,.2)'};}}
    .inf-panel-head {{display:flex;flex-direction:column;gap:1px;line-height:1.25;}}
    .inf-panel-head b {{font-size:14px;font-weight:400;color:{palette['strong_text']};letter-spacing:-.01em;}}
    .inf-panel-head span {{font-size:12px;font-weight:400;}}
    [class*="st-key-inf_card_"] [data-testid="stMarkdownContainer"] {{margin-bottom:0!important;}}
    [class*="st-key-inf_card_"] [data-testid="stElementToolbar"] {{display:none!important;}}
    [class*="st-key-inf_card_"] [class*="st-key-inf_zoom_"] button, .st-key-inf_unfocus button {{min-height:26px!important;padding:0 12px!important;}}
    [class*="st-key-inf_card_"] [class*="st-key-inf_zoom_"] button p, .st-key-inf_unfocus button p {{font-size:12px!important;font-weight:300!important;}}
    .st-key-inf_card_focus {{border:1px solid {palette['card_border']};border-radius:18px;padding:18px 22px 10px;gap:14px!important;
        background:{palette['card']};box-shadow:0 1px 0 rgba(255,255,255,.06) inset,0 28px 50px -32px rgba(0,0,0,.6);}}
    .st-key-inf_card_focus .inf-panel-head b {{font-size:20px;}} .st-key-inf_card_focus .inf-panel-head span {{font-size:14px;}}
    .ctx-answer {{margin:10px 0 22px!important;}}
    .st-key-ctx_main .ctx-head h3 {{margin:8px 0 6px!important;}}
    .st-key-ctx_main p.ctx-reading {{margin:0 0 20px!important;}}
    .st-key-ctx_main {{gap:16px!important;}}
    [class*="st-key-inf_card_"] [data-testid="stVegaLiteChart"] {{margin-top:2px;}}
    .ctx-title .page-freshness {{display:inline-flex;gap:6px;margin-left:12px;font-size:12px;}}
    .ctx-answer {{font-size:15px;line-height:1.5;font-weight:300;color:{palette['text']};margin:4px 0 0;max-width:900px;}}
    .ctx-split {{margin-top:5px;}}
    .ctx-split small {{display:block;font-size:11px!important;}}
    .ctx-split-bar {{display:flex;height:5px;border-radius:3px;overflow:hidden;margin-top:3px;max-width:190px;
        background:{palette['grid']};}}
    .ctx-split-bar b {{display:block;height:100%;}}
    .ctx-split-bar b.inf {{background:{palette['reference']};}}
    .ctx-split-bar b.up {{background:#e66767;}} .ctx-split-bar b.down {{background:#3987e5;}}
    .ctx-table-lead {{font-size:12px!important;color:{palette['text']};margin:-4px 0 8px!important;}}
    .inf-card {{border:1px solid {palette['card_border']};border-radius:12px;background:{palette['card']};padding:14px 16px;}}
    .inf-card h3 {{font-size:15px!important;font-weight:600;margin:0!important;padding:0!important;color:{palette['strong_text']};}}
    .inf-lead {{font-size:12px!important;color:{palette['text']};margin:2px 0 10px!important;}}
    .inf-row {{display:grid;grid-template-columns:10px 1fr 78px;grid-template-areas:"dot name total" ". bar bar" ". chip year";
        column-gap:8px;row-gap:3px;padding:7px 0;border-top:1px solid {palette['card_border']};align-items:center;}}
    .inf-row > i {{grid-area:dot;width:9px;height:9px;border-radius:50%;}}
    .inf-name {{grid-area:name;font-weight:500;font-size:13px;color:{palette['strong_text']};}}
    .inf-total {{grid-area:total;text-align:right;font-weight:600;font-size:13px;color:{palette['strong_text']};}}
    .inf-bar {{grid-area:bar;position:relative;height:6px;border-radius:3px;background:{palette['grid']};}}
    .inf-bar b {{display:block;height:100%;border-radius:3px;}}
    .inf-bar em {{position:absolute;top:-3px;width:2px;height:12px;background:{palette['strong_text']};}}
    .inf-row .chip {{grid-area:chip;justify-self:start;font-size:10.5px;}}
    .inf-year {{grid-area:year;text-align:right;font-size:11.5px;color:{palette['text']};white-space:nowrap;}}
    .st-key-ctx_main .ctx-head h3 {{margin-bottom:4px!important;}}
    .st-key-ctx_main p.ctx-reading {{margin:0 0 8px!important;}}
    .st-key-ctx_product {{border:1px solid {palette['card_border']};border-radius:12px;background:{palette['card']};padding:10px 16px 6px;margin-top:6px;}}
    .ctx-ipc-note {{display:block;margin-top:4px;font-size:13px;color:{palette['text']};}}
    .ctx-ipc-note b:first-child {{display:inline-block;font-size:10.5px;letter-spacing:.06em;padding:1px 7px;
        margin-right:6px;border-radius:999px;color:{palette['accent']};
        background:color-mix(in srgb,{palette['accent']} 12%,transparent);vertical-align:1px;}}
    .st-key-ctx_main p.ctx-reading {{font-size:12.5px!important;line-height:1.45!important;font-weight:300;color:{palette['text']};margin:0 0 20px!important;}}
    .st-key-ctx_main {{gap:10px!important;padding:2px 0 0;}}
    .st-key-ctx_main [data-testid="stHorizontalBlock"] {{gap:14px;}}
    .st-key-ctx_side {{gap:10px;}}
    .st-key-ctx_bottom {{margin-top:10px;}}
    .ctx-head h3, .ctx-card h3 {{font-size:15px!important;font-weight:500;margin:0!important;padding:0!important;
        color:{palette['strong_text']};display:flex;align-items:center;gap:6px;}}
    .ctx-head {{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;}}
    .ctx-keys {{display:flex;gap:14px;font-size:11px;color:{palette['text']};white-space:nowrap;}}
    .ctx-keys i {{display:inline-block;width:14px;height:3px;border-radius:2px;margin-right:5px;vertical-align:middle;}}
    .ctx-keys i.band {{height:9px;background:{palette['grid']};}}
    .st-key-ctx_main .ctx-head h3 {{white-space:nowrap;}}
    .st-key-ctx_main .ctx-keys {{flex-wrap:wrap;justify-content:flex-end;row-gap:2px;gap:4px 12px;}}
    .ctx-keys i.nominal {{height:0;border-top:2px dashed {palette['reference']};border-radius:0;}}
    .st-key-ctx_main [data-testid="stButtonGroup"] {{justify-content:flex-end;display:flex;flex-wrap:nowrap;}}
    .st-key-ctx_main [data-testid="stButtonGroup"] button {{min-height:26px!important;padding:0 10px!important;}}
    .st-key-ctx_main [data-testid="stButtonGroup"] button p {{font-size:12px!important;}}
    .ctx-card {{border:1px solid {palette['card_border']};border-radius:12px;background:{palette['card']};padding:12px 16px;}}
    /* The chart and the two side cards end on the same line (D-150): the cards share
       the chart's height. */
    [data-testid="stHorizontalBlock"]:has(.st-key-ctx_main) {{align-items:stretch;}}
    [data-testid="stColumn"]:has(.st-key-ctx_side) > [data-testid="stVerticalBlock"],
    .st-key-ctx_side {{height:100%;}}
    [data-testid="stColumn"]:has(.st-key-ctx_side) [data-testid="stLayoutWrapper"] {{height:100%;flex:1 1 auto;}}
    .st-key-ctx_side {{display:flex;flex-direction:column;}}
    .st-key-ctx_side > [data-testid="stElementContainer"] {{flex:1 1 0;display:flex;}}
    .st-key-ctx_side [data-testid="stMarkdown"], .st-key-ctx_side [data-testid="stMarkdown"] > div,
    .st-key-ctx_side [data-testid="stMarkdownContainer"] {{height:100%;width:100%;margin:0 !important;}}
    .st-key-ctx_side [data-testid="stMarkdown"] > div {{align-items:stretch !important;}}
    .st-key-ctx_side .ctx-card {{height:100%;margin:0 !important;box-sizing:border-box;display:flex;flex-direction:column;
        justify-content:space-around;}}
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
    .ctx-next-unclear {{color:{palette['text']};font-size:.75rem;font-style:italic;}}
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


def build_inflation_note(model, other, real, wrap):
    """One sentence when food inflation changes the answer for a channel (D-155): in
    real pesos the price reads otherwise than in today's pesos. Empty when it does not."""
    nominal, deflated = (other, model) if real else (model, other)
    changed = []
    for channel in CONTEXT_CHANNELS:
        before = nominal["now"].get(channel, {}).get("state")
        after = deflated["now"].get(channel, {}).get("state")
        if before in STATE_ORDER and after in STATE_ORDER and before != after:
            changed.append((channel, after, STATE_ORDER[after] < STATE_ORDER[before]))
    if not changed:
        return ""
    if real:
        lead = "Con los precios del día, "
        parts = [f'en {channel.lower()} estaría '
                 f'{wrap(channel, price_context.STATES[nominal["now"][channel]["state"]])}'
                 for channel, _, _ in changed]
    else:
        lead = "Descontada la inflación de alimentos (IPC del INE), "
        parts = [f'en {channel.lower()} está {wrap(channel, price_context.STATES[state])}: subió '
                 + ('menos' if lower else 'más') + ' que la inflación de alimentos'
                 for channel, state, lower in changed]
    return f'<span class="ctx-ipc-note"><b>IPC</b> {lead}{"; ".join(parts)}.</span>'


@st.cache_data
def read_family_inflation(database_version):
    """(monthly index per family and IPC, last IPC month, summary, IPC total, IPC 12 m) (D-163)."""
    rows, last = inflation_view.build_family_index(
        queries.run_sql(inflation_view.SERIES_SQL),
        queries.run_sql("SELECT year, month, food_index FROM ipc_monthly"))
    summary, ipc_total, ipc_year = inflation_view.summarize_families(rows, last)
    return rows, last, summary, ipc_total, ipc_year


def build_family_panel_titles(summary, ipc_total=None):
    """{family: "Hortalizas|+60,2 % · más que la inflación"}, biggest gap first; with
    ipc_total, the food IPC closes the list as the basket every family is measured against."""
    percent = lambda value: "—" if value is None or pd.isna(value) else charts.format_signed_percent(value)
    titles = {row.family: f"{home_mockup.short_family(row.family)}|{percent(row.total)} · {row.verdict}"
              for row in summary.itertuples()}
    if ipc_total is not None:
        titles[inflation_view.IPC_NAME] = f"IPC de alimentos (INE)|{percent(ipc_total)} · la canasta de referencia"
    return titles


FAMILY_CARD_COLUMNS = 4


def build_family_card_title_html(family, title):
    """The head of a family card: the name, and under it the rise and the verdict in
    the family's color."""
    name, verdict = title.split("|", 1)
    color = inflation_view.FAMILY_COLORS.get(family, "var(--text-color)")
    return (f'<div class="inf-panel-head"><b>{html.escape(name)}</b>'
            f'<span style="color:{color}">{html.escape(verdict)}</span></div>')


FAMILY_FOCUS_KEY = "inf_focus"


def focus_family(family):
    st.session_state[FAMILY_FOCUS_KEY] = family


def show_family_cards(rows, titles, mode, real):
    """One raised card per family (D-174), four per row, the same chart size and the
    same y scale. A card's «Ampliar» shows that family alone, large (D-177)."""
    domain = inflation_view.family_domain(rows, real)
    focus = st.session_state.get(FAMILY_FOCUS_KEY)
    if focus in titles:
        with st.container(key="inf_card_focus"):
            with st.container(horizontal=True, vertical_alignment="center"):
                st.markdown(build_family_card_title_html(focus, titles[focus]), unsafe_allow_html=True)
                st.button("Ver todas", key="inf_unfocus", icon=":material/close:", on_click=focus_family, args=(None,))
            st.altair_chart(inflation_view.draw_family_card(rows, focus, mode, real=real, domain=domain, height=420),
                            width="stretch", theme=None)
        return
    families = list(titles)
    for start in range(0, len(families), FAMILY_CARD_COLUMNS):
        columns = st.columns(FAMILY_CARD_COLUMNS, gap="small")
        for offset, family in enumerate(families[start:start + FAMILY_CARD_COLUMNS]):
            with columns[offset], st.container(key=f"inf_card_{start + offset}"):
                st.markdown(build_family_card_title_html(family, titles[family]), unsafe_allow_html=True)
                st.altair_chart(inflation_view.draw_family_card(rows, family, mode, real=real, domain=domain),
                                width="stretch", theme=None)
                st.button("Ampliar", key=f"inf_zoom_{start + offset}", icon=":material/open_in_full:",
                          on_click=focus_family, args=(family,))


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
    latest = read_latest_run()
    run_kind = "ok" if latest["status"] == etl.STATUS_LOADED else "failed"
    month = lambda pair: f"{price_context.MONTHS[pair[1] - 1]} {pair[0]}"
    above = [home_mockup.short_family(f) for f in summary.loc[summary["verdict"] == "más que la inflación", "family"]]
    below = [home_mockup.short_family(f) for f in summary.loc[summary["verdict"] == "menos que la inflación", "family"]]
    join = lambda names: ", ".join(names[:-1]) + " y " + names[-1] if len(names) > 1 else "".join(names)
    answer = (f'De enero 2022 a {month(last)}, la canasta de alimentos del INE subió '
              f'<b>{charts.format_signed_percent(ipc_total)}</b> ({charts.format_signed_percent(ipc_year)} en 12 meses).'
              + (f' Subieron más: <b>{html.escape(join(above))}</b>.' if above else '')
              + (f' Subieron menos: <b>{html.escape(join(below))}</b>.' if below else ''))
    title, basis = st.columns([2.9, 1.1], vertical_alignment="bottom")
    title.markdown(f'<div class="ctx-title compact-header"><h1>¿Qué alimentos subieron más que la inflación?</h1>'
                   f'<span class="page-freshness">Datos al {format_chile_time(parse_run_start(latest["started_at"]))} '
                   f'{build_chip("Carga correcta" if run_kind == "ok" else "Última carga con falla", run_kind)}</span></div>'
                   f'<p class="ctx-answer">{answer}</p>', unsafe_allow_html=True)
    basis.segmented_control("Precios", [BASIS_NOMINAL, BASIS_REAL], default=BASIS_NOMINAL,
                            key=CONTEXT_BASIS_KEY, label_visibility="collapsed", help=BASIS_HELP)
    real = st.session_state.get(CONTEXT_BASIS_KEY) == BASIS_REAL
    with st.container(key="ctx_main"):
        lead = ("Sin inflación: la línea punteada es la canasta del INE (100). Arriba de ella, la familia subió más."
                if real else "Precios de consumidor de ODEPA, mediana por familia; la línea punteada es el IPC de alimentos. "
                "Misma escala en todos los gráficos.")
        st.markdown(f'<div class="ctx-head"><h3>Índice mensual por familia, enero 2022 = 100</h3></div>'
                    f'<p class="ctx-reading">{lead}</p>', unsafe_allow_html=True)
        show_family_cards(rows, build_family_panel_titles(summary, ipc_total), mode, real)
    st.caption(f"Cada familia compara los mismos productos de enero 2022 a {month(last)} (series de consumidor con "
               "precio en ambos meses). El IPC de alimentos se calcula con precios de alimentos: subir con él no "
               "prueba que la inflación cause la subida; dice si la familia subió más o menos que la canasta.")


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


def build_runs_metric_html(label, value, note=""):
    return (f'<div class="runs-metric"><span class="runs-metric-label">{html.escape(label)}</span>'
            f'<span class="runs-metric-value">{html.escape(value)}</span>'
            f'<span class="runs-metric-note">{note}</span></div>')


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
    """Start the pipeline, show its steps live and end with one clear sentence:
    completed, or where it stopped (D-149). Returns True when it completed."""
    requested_at = datetime.now(timezone.utc)
    try:
        control.start_workflow_run(token)
    except Exception as error:  # GitHub refused the request or did not answer
        st.error(f"No se pudo iniciar la ejecución: {control.describe_github_error(error)}.",
                 icon=":material/error:")
        return False
    with st.status("Ejecutando el pipeline en GitHub Actions…", expanded=True) as status_box:
        run = wait_for_manual_run(requested_at, token)
        if run is None:
            status_box.update(label="GitHub no confirmó el inicio.", state="error", expanded=True)
            st.error("La ejecución no se confirmó. Revisa el historial en un minuto.",
                     icon=":material/error:")
            return False
        state = follow_run_progress(run["id"], token, st.empty())
        fetch_pipeline_runs.clear()
        if state == control.RUN_OK:
            status_box.update(label="Ejecución completada.", state="complete", expanded=True)
            st.success("Se ejecutó correctamente: datos descargados, revisados y guardados. "
                       "El panel los muestra en 1 o 2 minutos, al recibir la base nueva.",
                       icon=":material/check_circle:")
            st.toast("Pipeline ejecutado correctamente.", icon=":material/check_circle:")
            return True
        if state == control.RUN_IN_PROGRESS:
            status_box.update(label="Sigue en curso.", state="running", expanded=True)
            st.info("La ejecución sigue en curso en GitHub; su resultado aparecerá en el historial.")
            return False
        status_box.update(label="La ejecución no terminó.", state="error", expanded=True)
        st.error("No se ejecutó completamente: un paso falló (marcado con ❌). Los datos "
                 "anteriores siguen intactos; los logs están en el historial.", icon=":material/error:")
        st.toast("La ejecución falló.", icon=":material/error:")
        return False


ADMIN_UNLOCKED = "admin_unlocked"


@st.cache_resource
def get_login_guard():
    """One guard for every visitor of this server (D-199)."""
    return control.LoginGuard()
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


RELOADED_NOTICE = "panel_reloaded"


def reload_panel_data():
    """Read datos.db again (the weekly load or a manual run may have replaced it)."""
    st.cache_data.clear()
    st.session_state[RELOADED_NOTICE] = True


@st.dialog("Ejecutar el pipeline ahora", width="medium")
def show_run_now_dialog(token, access_code):
    """The manual run behind the control code, in a layer above the page (D-149)."""
    st.caption("Descarga los archivos de ODEPA, los limpia, los prueba y guarda la base, igual "
               "que la ejecución automática de cada martes. Tarda unos 5 minutos.")
    if not st.session_state.get(ADMIN_UNLOCKED):
        typed_code = st.text_input("Clave de control", key="run_now_code", autocomplete="off")
        if not st.button("Ejecutar", type="primary", icon=":material/play_arrow:", key="run_now_confirm"):
            return
        ok, message = get_login_guard().check(typed_code, access_code)
        if not ok:
            st.error(message, icon=":material/lock:")
            return
        st.session_state[ADMIN_UNLOCKED] = True
    show_token_expiration(token)
    run_pipeline_now(token)


def show_admin_card():
    """One door for the author (D-202): before the control code, only «Acceso del autor»; after
    it, the manual run (D-149) and the administration links. The reload is harmless and stays
    for everyone. The pipeline also runs by itself every Tuesday."""
    access_code = get_secret(SECRET_CONTROL_CODE)
    token = get_secret(SECRET_GITHUB_TOKEN)
    unlocked = bool(access_code and st.session_state.get(ADMIN_UNLOCKED))
    if unlocked:
        with st.container(key="runs_admin", horizontal=True, vertical_alignment="center", gap="small"):
            if st.button("Ejecutar pipeline ahora", type="primary", icon=":material/power_settings_new:",
                         key="runs_run_now", disabled=not token,
                         help="Lanza el pipeline en GitHub Actions." if token else
                              "Falta el token de GitHub en los secretos del panel."):
                show_run_now_dialog(token, access_code)
            st.markdown('<div class="run-now-label">Ejecutar pipeline ahora</div><div class="run-now-note">'
                        'Acceso del autor abierto.</div>', unsafe_allow_html=True)
    with st.container(key="runs_tools", horizontal=True, gap="small"):
        st.button("Recargar datos", icon=":material/refresh:", key="runs_reload",
                  width="stretch", on_click=reload_panel_data,
                  help="Vuelve a leer la base guardada; no ejecuta el pipeline.")
        show_author_access(access_code, unlocked)
    if st.session_state.pop(RELOADED_NOTICE, False):
        latest = read_latest_run()
        st.toast(f"Datos recargados · base del {format_chile_time(parse_run_start(latest['started_at']))}.",
                 icon=":material/check_circle:")


AUTHOR_CODE_MESSAGE = "author_code_message"


def check_author_code(access_code):
    """The code typed in «Acceso del autor», checked by the shared guard (D-199); the field is
    emptied either way, so the code never stays on screen."""
    typed_code = st.session_state.get("author_access_code", "")
    st.session_state["author_access_code"] = ""
    if not typed_code:
        return
    ok, message = get_login_guard().check(typed_code, access_code)
    if ok:
        st.session_state[ADMIN_UNLOCKED] = True
    else:
        st.session_state[AUTHOR_CODE_MESSAGE] = message


def lock_author_access():
    st.session_state[ADMIN_UNLOCKED] = False


def show_author_access(access_code, unlocked):
    """«Acceso del autor» (D-165, D-202): the control code opens the manual run and the
    administration links together; each link still asks for its own login."""
    if unlocked:
        with st.popover("Enlaces del autor", icon=":material/lock_open:", width="stretch",
                        help="Administrar la app publicada, los secretos y los tokens."):
            for link in ADMIN_LINKS:
                st.markdown(f'<a href="{html.escape(link["url"], quote=True)}" target="_blank" rel="noopener noreferrer">'
                            f'<b>{html.escape(link["name"])}</b></a> · {html.escape(link["description"])}',
                            unsafe_allow_html=True)
            st.caption("Cada enlace pide tu propia sesión de GitHub o de Streamlit.")
            st.button("Cerrar acceso", icon=":material/lock:", key="author_access_close", on_click=lock_author_access)
        return
    with st.popover("Acceso del autor", icon=":material/lock:", width="stretch",
                    help="Lanzar el pipeline y los enlaces de administración, con la clave de control."):
        if not access_code:
            st.caption("Se activa cuando el autor guarda la clave de control en los secretos del panel.")
            return
        # Enter opens it (D-203): the code is checked when the field commits, no extra button.
        st.text_input("Clave de control", key="author_access_code", autocomplete="off",
                      on_change=check_author_code, args=(access_code,), placeholder="Escribe la clave y pulsa Enter")
        message = st.session_state.pop(AUTHOR_CODE_MESSAGE, None)
        if message:
            st.error(message, icon=":material/lock:")


def build_runs_css(mode):
    palette = charts.get_palette(mode)
    return f"""<style>
    /* D-207: the control code is a plain text field shown as dots, so the browser never takes
       it for an account password and never offers to generate or save one. */
    .st-key-author_access_code input, .st-key-run_now_code input {{-webkit-text-security:disc; text-security:disc;}}
    .runs-metrics {{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:6px 0 16px;}}
    /* The manual run is a round power button (D-149): deep glossy blue, a brushed
       metal ring, the white power symbol. The words sit under it. */
    .st-key-runs_run_now {{display:flex; justify-content:center; align-self:center; margin:10px auto 2px;}}
    .st-key-runs_run_now > div, .st-key-runs_run_now [data-testid="stButton"],
    .st-key-runs_run_now [data-testid="stTooltipHoverTarget"] {{display:flex; justify-content:center; width:100%;}}
    .st-key-runs_run_now button {{width:52px; height:52px; min-height:52px; flex:0 0 52px; padding:0; border-radius:50% !important;
        border:2px solid #ffffff !important; color:#fff !important;
        background:radial-gradient(circle at 50% 30%, #4f8dff 0%, #1d5fe0 38%, #0a37a6 72%, #06246f 100%) !important;
        box-shadow:0 0 0 4px #dfe3ea, 0 0 0 5px #aab3c0,
                   inset 0 7px 10px -5px rgba(255,255,255,.55), inset 0 -7px 11px -5px rgba(0,0,0,.45),
                   0 10px 18px -8px rgba(10,55,166,.6);
        transition:transform .12s ease, box-shadow .12s ease, filter .12s ease;}}
    .st-key-runs_run_now button:hover:not(:disabled) {{transform:translateY(-2px); filter:brightness(1.08);}}
    .st-key-runs_run_now button:active:not(:disabled) {{transform:translateY(1px) scale(.98);}}
    .st-key-runs_run_now button p, .st-key-runs_run_now button [data-testid="stMarkdownContainer"] {{display:none !important;}}
    .st-key-runs_run_now button > div {{display:flex; align-items:center; justify-content:center; gap:0 !important;
        width:100%; height:100%; margin:0;}}
    .st-key-runs_run_now button [data-testid="stIconMaterial"] {{font-size:24px !important; width:24px; height:24px; line-height:1; margin:0 !important; color:#fff;
        text-shadow:0 1px 2px rgba(0,0,0,.35);}}
    .st-key-runs_run_now button:disabled {{opacity:.72; cursor:not-allowed;}}
    .run-now-label {{text-align:center; font-weight:500; font-size:.92rem; color:{palette['strong_text']}; margin:10px 0 0;}}
    .run-now-note {{text-align:center; font-size:.78rem; color:{palette['text']}; margin-top:2px;}}
    .runs-metric {{display:flex; flex-direction:column; gap:3px; padding:12px 16px; border-radius:14px;
        background:{palette['card']}; border:1px solid {palette['card_border']};
        box-shadow:0 10px 22px -16px rgba(0,0,0,.25);}}
    .runs-metric-label {{font-size:.68rem; font-weight:500; letter-spacing:.06em; text-transform:uppercase;
        color:{palette['reference']};}}
    .runs-metric-value {{font-size:1.12rem; font-weight:500; letter-spacing:-.01em;
        color:{palette['strong_text']}; font-variant-numeric:tabular-nums;}}
    .runs-metric-note {{font-size:.76rem; color:{palette['text']};}}
    .runs-card-title {{display:flex; align-items:center; gap:7px; font-size:.92rem; font-weight:500;
        color:{palette['strong_text']}; margin:0 0 10px;}}
    .runs-table {{width:100%; border-collapse:collapse; font-size:.84rem;}}
    .runs-table th {{text-align:left; font-size:.68rem; font-weight:500; letter-spacing:.05em;
        text-transform:uppercase; color:{palette['reference']}; padding:6px 8px;
        border-bottom:1px solid {palette['card_border']};}}
    .runs-table td {{padding:9px 8px; border-bottom:1px solid {palette['card_border']};
        color:{palette['strong_text']}; font-variant-numeric:tabular-nums;}}
    .runs-table tr:last-child td {{border-bottom:0;}}
    .runs-table tbody tr:hover td {{background:color-mix(in srgb,{palette['accent']} 5%,transparent);}}
    .runs-link {{text-align:right;}}
    @media (max-width:900px) {{ .runs-metrics {{grid-template-columns:repeat(2,minmax(0,1fr));}} }}
    </style>"""


def show_runs_page(mode):
    """Centro de operación (D-165): the weekly run as a path of floating logos, each
    with what it does and where to act, and beside it the facts and the manual run."""
    show_compact_page_header("Centro de operación", "El recorrido de cada martes, del lanzamiento "
                             "al panel: el estado de cada paso, su log y dónde actuar.")
    runs_tab, platform_tab = st.tabs(["Operación", "Plataforma"])
    with runs_tab:
        show_runs_tab(mode)
    with platform_tab:
        show_devops_tab(mode)


def show_security_page(mode):
    """What a visitor could try, the barriers that stop it and the test behind each (D-200, D-201)."""
    show_compact_page_header(PAGE_SECURITY, "Qué podría intentar un visitante y qué lo detiene.")
    st.caption("Cada puerta que podría tentar a un atacante, las barreras que la cierran y la prueba automática que "
               "las ataca en cada push. El código es público: la seguridad no depende de esconder cómo está hecho, "
               "sino de las claves, que nunca aparecen.")
    st.iframe(security_map.build_security_html(charts.get_palette(mode)), height=590)
    st.markdown('<p class="doc-source">El método, los casos de prueba y los resultados de la última revisión: '
                + build_link_html(f"{PAGE_SECURITY_PLAN} →", build_page_address(PAGE_SECURITY_PLAN)) + '</p>',
                unsafe_allow_html=True)


def show_runs_tab(mode):
    """The stage, refreshed by itself every few seconds while a run is in progress."""
    st.markdown(build_runs_css(mode), unsafe_allow_html=True)
    runs, _ = read_pipeline_runs()
    live = bool(runs) and runs[0]["state"] == control.RUN_IN_PROGRESS
    st.fragment(lambda: show_operation_center(mode, live),
                run_every=(LIVE_SECONDS_WITH_TOKEN if get_secret(SECRET_GITHUB_TOKEN)
                           else LIVE_SECONDS_WITHOUT_TOKEN) if live else None)()


@st.cache_data(ttl=GITHUB_CACHE_SECONDS, show_spinner=False)
def fetch_run_step_details(run_id):
    """Steps of one run with their log addresses. A failure raises, and is not cached."""
    return control.list_run_step_details(run_id, get_secret(SECRET_GITHUB_TOKEN))


def read_operation_runs(live):
    """(runs, step details of the latest, why GitHub failed or ""). While a run is in
    progress GitHub is asked directly, not through the five-minute cache."""
    if live:
        fetch_pipeline_runs.clear()
        fetch_run_step_details.clear()
    runs, error_text = read_pipeline_runs()
    if not runs:
        return runs, {}, error_text
    last_answers = get_last_github_answers()
    try:
        details = fetch_run_step_details(runs[0]["id"])
    except Exception as error:  # GitHub unreachable or refused
        # The traceback goes to the server log (Streamlit Cloud: «Manage app»).
        logging.getLogger(__name__).exception("Centro de operación: los pasos de la ejecución %s no se pudieron leer",
                                              runs[0]["id"])
        details = last_answers.get(("details", runs[0]["id"]), {})
        return runs, details, error_text or control.describe_github_error(error)
    last_answers[("details", runs[0]["id"])] = details
    return runs, details, error_text


@st.cache_data(show_spinner=False)
def read_published_figures(database_version):
    """Last week, prices and weeks of the published database."""
    return queries.run_sql("SELECT max(week_start) AS last_week, count(*) AS prices, "
                           "count(DISTINCT week_start) AS weeks FROM weekly_price").iloc[0]


def build_operation_fact(label, value, note=""):
    return (f'<div class="oc-fact"><span class="oc-fact-label">{html.escape(label)}</span>'
            f'<span class="oc-fact-value">{html.escape(value)}</span>'
            f'<span class="oc-fact-note">{note}</span></div>')


def build_operation_facts(latest_load, published, now):
    """Next run, published data and latest load: what to know before acting."""
    next_run = control.calculate_next_scheduled_run(now)
    hours = int((next_run - now).total_seconds() // 3600)
    wait = f"faltan {hours} h" if hours < 48 else f"faltan {hours // 24} días"
    last_week = pd.Timestamp(published["last_week"])
    return (build_operation_fact("Próxima ejecución", f"{to_chile_time(next_run):%d-%m · %H:%M}",
                                 f"automática, cada martes · {wait}")
            + build_operation_fact("Datos publicados", f"Semana del {last_week:%d-%m-%Y}",
                                   f"{charts.format_thousands(published['prices'])} precios · "
                                   f"{charts.format_thousands(published['weeks'])} semanas")
            + build_operation_fact("Última carga", f"{charts.format_thousands(latest_load['rows_loaded'])} filas",
                                   f"de {charts.format_thousands(latest_load['rows_read'])} leídas · "
                                   f"{charts.format_thousands(latest_load['rows_rejected'])} rechazadas"))


def build_recent_runs_html(runs):
    """The latest runs, one line each with its colour and a link to its logs."""
    colors = {control.RUN_OK: charts.STATUS_COLORS["good"], control.RUN_FAILED: charts.STATUS_COLORS["critical"],
              control.RUN_IN_PROGRESS: charts.STATUS_COLORS["running"]}
    words = {control.RUN_OK: "correcta", control.RUN_FAILED: "falló", control.RUN_IN_PROGRESS: "en curso",
             control.RUN_SIMULATED_FAILURE: "falla simulada"}
    lines = "".join(
        f'<a class="oc-run" href="{html.escape(run["url"], quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'<span class="oc-dot" style="background:{colors.get(run["state"], charts.STATUS_COLORS["unknown"])}"></span>'
        f'{to_chile_time(run["started_at"]):%d-%m %H:%M} · {html.escape(run["trigger"].lower())} · '
        f'{words.get(run["state"], "")} ↗</a>'
        for run in runs[:OPERATION_RECENT_RUNS])
    return f'<div class="oc-runs"><span class="oc-fact-label">Últimas ejecuciones</span>{lines}</div>'


def show_operation_center(mode, live=False):
    palette = charts.get_palette(mode)
    runs, details, error_text = read_operation_runs(live)
    latest_load = read_latest_run()
    states = operation_center.build_step_states(runs[0] if runs else None, details,
                                                latest_load["status"] == etl.STATUS_LOADED)
    unlocked = bool(st.session_state.get(ADMIN_UNLOCKED))
    # The latest runs go under the path and the manual run beside the facts, so both
    # columns end together and the page fits one screen.
    stage_column, side_column = st.columns([2.4, 1], gap="large")
    with stage_column:
        st.iframe(operation_center.build_stage_html(palette, states, unlocked), height="content")
        if runs:
            st.markdown(build_recent_runs_html(runs), unsafe_allow_html=True)
    with side_column:
        if error_text:
            st.caption(f"GitHub no respondió ({error_text}); se muestra la última respuesta guardada.")
        st.markdown(build_operation_side_css(palette)
                    + build_operation_facts(latest_load, read_published_figures(get_database_version()),
                                            datetime.now(timezone.utc)), unsafe_allow_html=True)
        show_admin_card()


def build_operation_side_css(palette):
    return f"""<style>
    .oc-fact {{display:flex; flex-direction:column; gap:1px; padding:10px 0;
        border-bottom:1px solid {palette['card_border']};}}
    .oc-fact-label {{font-size:.68rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase;
        color:{palette['reference']};}}
    .oc-fact-value {{font-size:1.15rem; font-weight:600; color:{palette['strong_text']};
        font-variant-numeric:tabular-nums;}}
    .oc-fact-note {{font-size:.8rem; color:{palette['text']};}}
    .oc-runs {{display:flex; flex-wrap:wrap; align-items:center; gap:4px 20px; padding-top:10px;
        border-top:1px solid {palette['card_border']};}}
    .oc-runs .oc-fact-label {{flex-basis:100%;}}
    .oc-run {{display:flex; align-items:center; font-size:.82rem; color:{palette['text']} !important;
        text-decoration:none !important; padding:2px 0;}}
    .oc-run:hover {{color:{palette['strong_text']} !important;}}
    .oc-dot {{display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; flex-shrink:0;}}
    .st-key-runs_admin {{padding:14px 0 6px;}}
    .st-key-runs_admin .st-key-runs_run_now {{margin:0 6px 0 4px; flex:none;}}
    .st-key-runs_admin .run-now-label, .st-key-runs_admin .run-now-note {{text-align:left; margin:0;}}
    </style>"""


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


def read_journey():
    """(states, figures, pipeline run, latest load, GitHub error) of the live diagram."""
    with st.spinner("Consultando el estado del pipeline…"):
        step_states, pipeline_run, error_text = read_latest_pipeline_steps()
    latest_load = read_latest_run()
    manifest = read_download_manifest()
    states = build_journey_states(step_states, pipeline_run, latest_load, manifest)
    figures = build_journey_figures(manifest, pipeline_run, latest_load)
    build = lineage.summarize_build(*read_lineage(get_database_version()))
    if build:
        figures["dbt"] = f"{build['models']} modelos · {build['passing']}/{build['tests']} pruebas"
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


def show_architecture_group(heading, lead, title_column, text_column, note_column, titled=True):
    """Technical details as compact rows, rather than oversized uniform cards. In a
    dialog the dialog already carries the heading, so only the lead shows."""
    if titled:
        show_section_intro(heading, lead, True)
    else:
        st.caption(lead)
    rows = ''.join(build_layer_card_html(row[title_column], row[text_column],
                                         format_architecture_note(note_column, row[note_column]))
                   for row in project.read_guide_table(heading))
    st.markdown(f'<div class="technical-rows layer-cards">{rows}</div>', unsafe_allow_html=True)


# The real tool behind each row of a layer (D-137): its own mark, in its brand colour.
LAYER_ROW_LOGOS = {
    "Base en solo lectura": "sqlite", "Consola SQL de solo lectura": "sqlite",
    "Secretos fuera del código": "streamlit", "Permisos mínimos del workflow": "github",
    "Datos crudos fuera del repositorio": "git", "Workflow semanal": "github",
    "Tests en cada push": "pytest", "Caché de años cerrados": "github",
    "Despliegue continuo": "streamlit", "Entorno de desarrollo": "python",
    "Tabla `etl_run`": "sqlite", "Tabla `rejection`": "sqlite", "Logs del agente": "python",
    "Historial de GitHub Actions": "github", "Correo de GitHub": "github",
    "Issue «Informe semanal AAAA-MM-DD»": "github", "Este panel": "streamlit",
}
BRAND_COLOURS = {"github": "var(--github-ink)", "sqlite": "#0f80cc", "streamlit": "#ff4b4b",
                 "git": "#f05032", "pytest": "#0a9edc", "python": "#3776ab"}


def build_layer_card_html(title, text, note):
    """One floating card: the tool's real logo on a tinted tile, the title, what it
    does and where it lives, with no empty space below (D-137)."""
    slug = LAYER_ROW_LOGOS.get(title, "github")
    colour = BRAND_COLOURS[slug]
    return (f'<div class="layer-card" style="--brand:{colour}">'
            f'<span class="layer-logo"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
            f'{architecture.brand_icons.logo_body(slug)}</svg></span>'
            f'<div class="layer-body"><strong>{format_inline(title)}</strong>'
            f'<p>{format_inline(text)}</p><span class="layer-note">{note}</span></div></div>')


def build_journey_legend_html():
    """What the colored dot of each step and the moving arrows mean."""
    return (f'{build_chip("OK", "ok")} {build_chip("En curso", "running")} '
            f'{build_chip("Falla", "failed")} {build_chip("Sin datos", "neutral")}'
            '<div class="kpi-note" style="margin-top:8px">Punto de color en cada '
            'paso: estado de la última ejecución del pipeline y de la base actual. '
            'El movimiento ilustrativo, no actividad en vivo, muestra el recorrido; '
            'el estado identifica la ejecución real.</div>')


def build_devops_figures(figures):
    """The pipeline figures plus the size of datos.db, the test functions and the
    prices of the latest week (what the weekly job added), all read now."""
    latest_week = read_latest_week()
    week_prices = project.count_week_prices(f"{latest_week:%Y-%m-%d}")
    return dict(figures, database_size=project.describe_file_size(queries.DATABASE_FILE),
                test_functions=f"{project.count_test_functions()} funciones de prueba",
                week_prices=(f"semana {latest_week:%d-%m}: "
                             f"{charts.format_thousands(week_prices)} precios"))


DEVOPS_COST_TEXT = (
    "SQLite permite almacenar los datos sin un servidor de base de datos dedicado. GitHub Actions "
    "coordina las ejecuciones y Streamlit publica el panel. La capacidad depende del volumen, la "
    "duración de las cargas y las cuotas de cada servicio. La arquitectura debe revisarse antes de "
    "aumentar la frecuencia o incorporar fuentes de mayor tamaño.")
DEVOPS_LAYER_ICONS = {"Seguridad": ":material/shield:", "DevOps": ":material/autorenew:",
                      "Observabilidad": ":material/monitoring:", "Informes": ":material/description:",
                      "Coste y capacidad": ":material/savings:"}


def show_devops_layer_dialog(heading, next_run):
    """One layer's detail in a dialog, so the page itself stays the diagram (D-132)."""
    def body():
        if heading == "Coste y capacidad":
            st.markdown(DEVOPS_COST_TEXT)
            return
        show_architecture_group(*next(group for group in ARCHITECTURE_GROUPS if group[0] == heading),
                                titled=False)
        if heading == "DevOps":
            st.markdown(f'<div class="info-note">Próxima ejecución automática: {next_run}.</div>',
                        unsafe_allow_html=True)
        if heading == "Informes":
            reports = next(link["url"] for link in project.PROJECT_LINKS
                           if link["name"] == "Informes semanales")
            st.markdown(f'<div class="info-note">{build_external_link_html("Ver los informes semanales en GitHub", reports)}'
                        '</div>', unsafe_allow_html=True)
    st.dialog(heading, width="large")(body)()


def show_devops_tab(mode):
    """The whole platform architecture, full width, and its layers as a row of tiles
    that open their detail (D-132, D-136). The lifecycle drawing and the link to
    Pipeline are gone: this page has its own architecture."""
    states, figures, pipeline_run, latest_load, error_note = read_journey()
    st.markdown(zoom.build_zoom_frame_html(
        architecture.build_devops_svg(states, build_devops_figures(figures), mode, animate_flow=True),
        "diagram-devops"), unsafe_allow_html=True)
    with st.container(key="devops_layers", horizontal=True, gap="small"):
        for heading, lead in [(group[0], group[1]) for group in ARCHITECTURE_GROUPS] + [
                ("Coste y capacidad", "Qué cuesta operar y hasta dónde alcanza.")]:
            if st.button(heading, key=f"devops_layer_{heading}", icon=DEVOPS_LAYER_ICONS[heading],
                         help=lead, width="stretch"):
                show_devops_layer_dialog(heading, figures["next_run"])
    st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)
    st.html(zoom.TIP_SCRIPT, unsafe_allow_javascript=True)


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
                  "Motivo": REASON_NAMES.get(row["reason"], row["reason"])}
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


@st.cache_data
def read_parity(database_version):
    """SQLite backup against DuckDB, once per load (D-154)."""
    return quality.check_parity()


@st.cache_data(ttl=300, show_spinner=False)
def read_rejection_count(database_version):
    """Rows the validation set apart, for the anomalies box of the quality page (D-176)."""
    return int(queries.run_sql("SELECT count(*) AS n FROM rejection").iloc[0, 0])


@st.cache_data(ttl=300, show_spinner=False)
def read_quality_evidence(database_version, manifest_text, file_versions):
    """Invalidate checks when either the database, manifest or local source files change."""
    return quality.check_database(), quality.check_source_files(json.loads(manifest_text), MANIFEST_FILE.parent)


# A control's status color, by its first word (D-120): green when met, amber
# while pending, red on a real failure — the same reading as a status dot
# elsewhere in the app.
QUALITY_STATUS_COLORS = {"fail": "#e66767", "pending": "#c98500", "ok": "#22b35a"}


def classify_quality_status(status):
    if status.startswith("Falla") or status.startswith("Sin registro"):
        return "fail"
    if status.startswith("Pendiente"):
        return "pending"
    return "ok"


def build_quality_grid_css(mode):
    palette = charts.get_palette(mode)
    return f"""<style>
    .quality-grid {{display:grid; grid-template-columns:repeat(auto-fill, minmax(260px,1fr));
        gap:16px; margin:14px 0;}}
    .quality-card {{display:flex; flex-direction:column; gap:7px; padding:16px 18px;
        border-radius:16px; background:{palette['card']}; border:1px solid {palette['card_border']};
        box-shadow:0 12px 24px -14px color-mix(in srgb,var(--q-color) 55%,#0003),
                   0 2px 6px -1px rgba(0,0,0,.12);
        transition:transform .15s ease, box-shadow .15s ease;}}
    .quality-card:hover {{transform:translateY(-4px);}}
    .quality-card-title {{font-weight:500; color:{palette['strong_text']}; font-size:.92rem;}}
    .quality-badge {{display:inline-block; align-self:flex-start; padding:3px 10px;
        border-radius:999px; font-size:.72rem; font-weight:500; color:#fff;
        background:var(--q-color);}}
    .quality-card-text {{font-size:.83rem; line-height:1.5; color:{palette['text']};}}
    </style>"""


def build_quality_card_html(title, status, evidence):
    color = QUALITY_STATUS_COLORS[classify_quality_status(status)]
    return (f'<div class="quality-card" style="--q-color:{color}">'
            f'<div class="quality-card-title">{html.escape(title)}</div>'
            f'<span class="quality-badge">{html.escape(status)}</span>'
            f'<div class="quality-card-text">{html.escape(evidence)}</div></div>')


QUALITY_PICK_KEY = "qa_pick"
QUALITY_OPEN_KEY = "qa_open"


def open_quality_evidence():
    """A card chosen in the pills opens its dialog once; the pills clear themselves."""
    st.session_state[QUALITY_OPEN_KEY] = st.session_state.get(QUALITY_PICK_KEY)
    st.session_state[QUALITY_PICK_KEY] = None


def recheck_quality():
    """Run every check again, now: the caches of the board are dropped (D-171)."""
    read_quality_evidence.clear()
    read_quality_measures.clear()
    read_parity.clear()
    read_lineage.clear()
    st.session_state["qa_rechecked_at"] = datetime.now(timezone.utc)


QUALITY_VIEWS = ["Calidad", "Auditoría"]
QUALITY_VIEW_KEY = "quality_view"
AUDIT_KEYS = {"family": "audit_family", "product": "audit_product", "channel": "audit_channel", "region": "audit_region", "series": "audit_series"}
AUDIT_DEFAULTS = {"product": "Tomate", "channel": "Supermercado", "region": "Región Metropolitana de Santiago"}


@st.cache_data(ttl=300, show_spinner=False)
def read_quality_measures(database_version):
    """The raw figures of the «Calidad» view, read from the database on every load (D-196)."""
    return quality_live.read_measures()


@st.cache_data(show_spinner=False)
def check_trace_file(name, entry_text, file_version):
    """The registered SHA-256 of a source file against the file itself, where the file exists."""
    return audit_trace.check_file(name, json.loads(entry_text))


def show_operations_page(mode):
    """Calidad y auditoría in two views (D-196). Calidad: is the data good today, measured on
    the real database against thresholds shown beside each figure. Auditoría: where one price
    comes from, step by step, with what could not be checked here said as such."""
    show_compact_page_header("Calidad y auditoría", "Calidad mide si los datos están bien hoy; auditoría prueba que lo "
                             "publicado se puede rastrear y repetir.")
    view = st.segmented_control("Vista de calidad y auditoría", QUALITY_VIEWS, default=QUALITY_VIEWS[0], key=QUALITY_VIEW_KEY,
                                label_visibility="collapsed") or QUALITY_VIEWS[0]
    if view == QUALITY_VIEWS[0]:
        show_quality_view(mode)
    else:
        show_audit_view(mode)


def show_quality_view(mode):
    measures = read_quality_measures(get_database_version())
    indicators = quality_live.build_indicators(measures)
    flags = measures["flags"]
    st.iframe(quality_live.build_page_html(charts.get_palette(mode), indicators, measures["runs"], measures["rejections"], flags),
              height=500)
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.button("Volver a medir", icon=":material/refresh:", key="qa_recheck_page", on_click=recheck_quality,
                  help="Descarta lo guardado y mide de nuevo sobre la base publicada.")
        rechecked = st.session_state.get("qa_rechecked_at")
        st.caption(f"Medido de nuevo a las {to_chile_time(rechecked):%H:%M:%S}." if rechecked else
                   "Cada indicador se mide en la base de la última carga.")


def show_audit_view(mode):
    manifest = read_download_manifest()
    run = read_latest_run()
    nodes, results = read_lineage(get_database_version())
    build = lineage.summarize_build(nodes, results)
    build_part = (dict(tests=int(build["tests"]), passing=int(build["passing"]), ok=bool(build["ok"]),
                       built_at=f"{build['built_at']:%d-%m-%Y}" if build.get("built_at") is not None else "") if build else None)
    try:
        options = sql_explorer.load_parameter_options()
    except Exception:
        options = None
    if options is None:
        st.info("No se pudo leer la base de datos para elegir un precio.")
        return
    families = sorted(options["families"])
    with st.container(key="audit_pickers", horizontal=True, vertical_alignment="bottom", gap="small"):
        default_family = next((name for name, items in options["families"].items() if AUDIT_DEFAULTS["product"] in items), families[0])
        family = st.selectbox("Familia", families, key=AUDIT_KEYS["family"], index=families.index(default_family))
        products = options["families"][family]
        if st.session_state.get(AUDIT_KEYS["product"]) not in products:
            st.session_state[AUDIT_KEYS["product"]] = AUDIT_DEFAULTS["product"] if AUDIT_DEFAULTS["product"] in products else products[0]
        product = st.selectbox("Producto", products, key=AUDIT_KEYS["product"])
        channels = options["channels"].get(product, [])
        if st.session_state.get(AUDIT_KEYS["channel"]) not in channels:
            st.session_state[AUDIT_KEYS["channel"]] = AUDIT_DEFAULTS["channel"] if AUDIT_DEFAULTS["channel"] in channels else channels[0]
        channel = st.selectbox("Canal", channels, key=AUDIT_KEYS["channel"])
        regions = options["regions"]
        if st.session_state.get(AUDIT_KEYS["region"]) not in regions:
            st.session_state[AUDIT_KEYS["region"]] = AUDIT_DEFAULTS["region"] if AUDIT_DEFAULTS["region"] in regions else regions[0]
        region = st.selectbox("Región", regions, key=AUDIT_KEYS["region"])
        series = audit_trace.find_series(product, channel, region)
        labels = [f"{row.variety} · {row.quality} · {row.normalized_unit}" for row in series.itertuples()]
        if labels and st.session_state.get(AUDIT_KEYS["series"]) not in labels:
            st.session_state[AUDIT_KEYS["series"]] = labels[0]
        chosen = st.selectbox("Serie", labels or ["—"], key=AUDIT_KEYS["series"])
    # The controls that hold the chain up, as in the evidence dialogs of D-171.
    versions = tuple((path.name, path.stat().st_size, path.stat().st_mtime_ns)
                     for path in sorted(MANIFEST_FILE.parent.glob("*.csv")))
    checks, files = read_quality_evidence(get_database_version(), json.dumps(manifest, sort_keys=True), versions)
    parity = read_parity(get_database_version())
    evidence = quality_view.build_evidence(checks, files, manifest, run, build, parity,
                                           lambda value: format_chile_time(parse_run_start(value)),
                                           rejections=read_rejection_count(get_database_version()))
    controls = quality_view.build_columns(evidence)
    if series.empty:
        st.info("Ese producto no tiene precios en ese canal y región. Prueba con otra región.")
    else:
        item = series.iloc[labels.index(chosen)]
        row = audit_trace.read_trace(product, item["variety"], item["quality"], channel, region, item["normalized_unit"])
        name = audit_trace.source_file_name(row)
        entry = manifest.get(name) or {}
        path = audit_trace.DOWNLOADS / name
        file_version = (path.stat().st_size, path.stat().st_mtime_ns) if path.is_file() else None
        status = check_trace_file(name, json.dumps(entry, sort_keys=True), file_version)
        steps = audit_trace.build_trace_steps(row, manifest, run, build_part, status)
        st.iframe(audit_trace.build_trace_html(charts.get_palette(mode), row, steps, controls), height=380)
    database_ok = checks["integrity_ok"] and not any(checks[key] for key in ("foreign_keys", "duplicates", "invalid"))
    if not database_ok or any(item["status"].startswith("Falla") for item in files):
        st.error("Se detectó una discrepancia en los controles locales. Revisa la evidencia antes de utilizar los resultados.")
    with st.container(key=quality_view.EXPANDER_KEY, horizontal=True, vertical_alignment="center", gap="small"):
        st.markdown('<span class="qa-open-label">Abrir la evidencia de</span>', unsafe_allow_html=True)
        st.pills("Abrir la evidencia de", [title for _, title, _ in quality_evidence.CARDS], key=QUALITY_PICK_KEY,
                 on_change=open_quality_evidence, label_visibility="collapsed")
    st.caption("Cada control abre los datos que lo respaldan y su método; «Volver a comprobar» corre los controles de nuevo.")
    chosen_card = st.session_state.pop(QUALITY_OPEN_KEY, None)
    if chosen_card in quality_evidence.TITLES.values():
        key = next(key for key, title in quality_evidence.TITLES.items() if title == chosen_card)
        show_quality_evidence_dialog(key, mode, dict(manifest=manifest, files=files, checks=checks, parity=parity,
                                                     nodes=nodes, results=results, evidence=evidence))


@st.dialog("Evidencia", width="large")
def show_quality_evidence_dialog(key, mode, context):
    """One card's evidence: what it checks, its rows, its method, and a recheck."""
    st.markdown(f"### {quality_evidence.TITLES[key]}")
    st.markdown(quality_evidence.EXPLANATIONS[key])
    if key == "files":
        st.dataframe(quality_evidence.manifest_frame(context["manifest"]), hide_index=True, width="stretch")
        st.caption(f"Registro: agent/downloads/manifest.json · {len(context['manifest'])} archivos.")
    elif key == "shield":
        st.dataframe(quality_evidence.files_frame(context["files"]), hide_index=True, width="stretch")
        if any(item["actual"] is None for item in context["files"]):
            st.caption("Los archivos CSV no viven en el servidor del panel (no se suben al repositorio): aquí la "
                       "huella solo se comprueba cuando el panel corre junto a las descargas.")
    elif key == "calendar":
        checks = context["checks"]
        st.markdown(f"**{checks['weeks']} semanas**, del {quality_view.format_week(checks['first'])} "
                    f"al {quality_view.format_week(checks['last'])}.")
        missing = queries.run_sql(quality_evidence.MISSING_WEEKS_SQL)
        if missing.empty:
            st.success("Ninguna semana falta entre la primera y la última.", icon=":material/check_circle:")
        else:
            st.dataframe(missing, hide_index=True, width="stretch")
        show_evidence_method(quality_evidence.MISSING_WEEKS_SQL)
    elif key == "gear":
        st.dataframe(queries.run_sql(quality_evidence.RUNS_SQL), hide_index=True, width="stretch")
        show_quality_tab(mode)
    elif key == "layers":
        st.dataframe(lineage.build_rule_matrix(context["nodes"], context["results"]), hide_index=True, width="stretch",
                     column_config={"Regla": st.column_config.TextColumn(width="small"),
                                    "Pruebas dbt": st.column_config.NumberColumn(width="small")})
        st.caption("Cada regla del PRD con las pruebas de dbt que la comprueban en cada carga.")
        st.dataframe(queries.run_sql(quality_evidence.DBT_TESTS_SQL), hide_index=True, width="stretch")
        show_evidence_method(quality_evidence.DBT_TESTS_SQL)
    elif key == "database":
        frame = quality_evidence.checks_frame(context["checks"])
        st.dataframe(frame[["comprobación", "casos"]], hide_index=True, width="stretch")
        show_evidence_method("\n\n".join(frame["sql"]))
    elif key == "parity":
        st.dataframe(quality_evidence.parity_frame(context["parity"]), hide_index=True, width="stretch")
        show_evidence_method(quality.PARITY_SQL + "  -- en SQLite y en DuckDB")
    elif key in quality_evidence.TEST_LINKS:
        st.markdown("Esta auditoría corre con las pruebas automáticas en cada cambio del repositorio y en cada "
                    "carga semanal. Su código y su último resultado:")
        for label, address in quality_evidence.test_links(key):
            st.markdown(build_link_html(f"{label} ↗", address), unsafe_allow_html=True)
    else:
        st.info("Sin evidencia que mostrar: es un límite declarado, no una comprobación.")
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.button("Volver a comprobar", icon=":material/refresh:", key="qa_recheck", on_click=recheck_quality,
                  help="Corre de nuevo los controles sobre la base publicada y los archivos.")
        rechecked = st.session_state.get("qa_rechecked_at")
        if rechecked:
            st.caption(f"Comprobado de nuevo a las {to_chile_time(rechecked):%H:%M:%S}.")


def show_evidence_method(sql):
    with st.expander("Método: la consulta que lo comprueba", expanded=False, icon=":material/code:"):
        st.code(sql, language="sql")




# endregion


# region Links page
def build_github_icon_svg(size=22):
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="currentColor" '
            f'aria-hidden="true">{architecture.brand_icons.logo_body("github")}</svg>')


def prepare_resource_cards(links):
    """The same links, with a real GitHub mark for every link that actually goes to
    GitHub (D-116) — the material glyph stays only for links that do not (ODEPA)."""
    github_icon = build_github_icon_svg()
    return [dict(link, icon=github_icon if link["url"].startswith(project.GITHUB_URL) else link["icon"])
            for link in links]


def build_github_repo_header_html():
    """A small repo strip, like GitHub's own title bar, before sending the reader
    there for real (D-116)."""
    slug = "/".join(project.GITHUB_URL.rstrip("/").split("/")[-2:])
    return (f'<a class="gh-repo-header" href="{html.escape(project.GITHUB_URL, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">{build_github_icon_svg(26)}'
            f'<span class="gh-repo-slug">{html.escape(slug)}</span>'
            '<span class="gh-repo-open">Abrir repositorio ↗</span></a>')


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


def show_links_page(mode):
    """The repository is the single destination for commits, executions and full
    documents (D-106): one hero with the repository, then its three uses —
    automatización, trazabilidad, documentación — each item opening GitHub in a new
    tab (D-116) with its own copy button. ODEPA and the INE live in «Fuentes» (D-118)."""
    # Our own trusted markup, in its own frame: st.html sanitises the SVG gradients,
    # filters and buttons the page is made of.
    st.iframe('<!doctype html><html lang="es"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width,initial-scale=1"></head>'
              '<body style="margin:0;background:transparent">'
              + github_page.build_github_page_html(mode) + github_page.GITHUB_PAGE_SCRIPT + '</body></html>',
              height="content")

# endregion


# region Project documents (D-151)
PROJECT_DOCUMENTS = {
    PAGE_PRD: ("PRD.md", "Qué resuelve el producto, para quién y con qué requisitos."),
    PAGE_SAD: ("SAD.md", "Cómo está construido: pipeline, plataforma y modelo de datos."),
    PAGE_ADR: ("ADR.md", "Las diez decisiones de arquitectura que más pesan, con su motivo."),
    PAGE_SECURITY_PLAN: ("SEGURIDAD.md", "Cómo se buscan, se corrigen y se prueban en cada push los puntos débiles."),
}
DOCUMENT_DIAGRAM = re.compile(r"^\[\[diagrama:(\w+)\]\]\s*$", re.MULTILINE)


def build_document_diagram_html(name, mode):
    """A live panel diagram behind a [[diagrama:…]] marker (platform, pipeline, star model),
    as markup for st.markdown; "" when the marker is drawn in its own frame instead."""
    if name in ("plataforma", "pipeline"):
        states, figures, *_ = read_journey()
        if name == "plataforma":
            return zoom.build_zoom_frame_html(architecture.build_devops_svg(
                states, build_devops_figures(figures), mode, animate_flow=False), "diagram-devops")
        return zoom.build_zoom_frame_html(architecture.build_journey_svg(
            states, figures, mode, animate_flow=False), "diagram-wide")
    if name == "modelo":
        row_counts = read_table_row_counts()
        columns = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
        return star_model.build_star_svg(columns, row_counts, mode)
    return ""


def show_document_diagram(name, mode):
    """One marker of a document: the document views and the security map in their own frame
    (hover tips and gradients need it, D-205), the live diagrams inline."""
    palette = charts.get_palette(mode)
    if name in doc_diagrams.DOC_DIAGRAMS:
        st.iframe(doc_diagrams.DOC_DIAGRAMS[name](mode), height=doc_diagrams.HEIGHTS[name])
    elif name == "seguridad":
        st.iframe(security_map.build_security_html(palette), height=590)
    else:
        st.markdown('<div class="doc-diagram">' + build_document_diagram_html(name, mode) + '</div>',
                    unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def build_document_pdf(path, modified, title, subtitle):
    """The document as a PDF with cover, contents and page numbers, once per version."""
    return document_pdf.build_pdf(Path(path).read_text(encoding="utf-8"), title, subtitle)


def show_scalability_page(mode):
    """Escalabilidad: the SAD's own section, so the page and GitHub say the same."""
    # D-210: the section left the two-page SAD for the decision log, unchanged.
    text = (project.PROJECT_DIR / "docs" / "DECISIONES.md").read_text(encoding="utf-8")
    match = re.search(r"^### Escalabilidad\n(.*?)(?=^##|\Z)", text, re.MULTILINE | re.DOTALL)
    show_compact_page_header(PAGE_SCALABILITY, "Qué se agregaría y cuándo: clima previsto; nube solo con datos "
                             "de una empresa (ADR-31).")
    st.markdown('<div class="doc-source">' + build_external_link_html(
        "Sección completa en docs/DECISIONES.md", project.build_github_url("docs/DECISIONES.md")) + '</div>',
        unsafe_allow_html=True)
    with st.container(key="project_document"):
        st.markdown(match.group(1) if match else "La sección de escalabilidad no está en docs/DECISIONES.md.")


@st.cache_data(show_spinner=False)
def read_stack_figures(database_version):
    """The three figures of «Stack y evidencia», once per database."""
    return stack_page.read_figures()


def show_stack_page(mode):
    """«Stack y evidencia» (D-211): each logo explains itself and opens the page where it works."""
    show_compact_page_header(PAGE_STACK, "Las herramientas del proyecto y dónde se ven en uso.")
    addresses = {page: build_page_address(page) for *_, page in stack_page.STACK}
    st.html(stack_page.build_stack_html(charts.get_palette(mode), read_stack_figures(get_database_version()),
                                        addresses))


def show_project_document(mode, title):
    """A document of docs/ as a page: the same text as in GitHub, its diagrams drawn
    from the live project, no code."""
    filename, lead = PROJECT_DOCUMENTS[title]
    text = (project.PROJECT_DIR / "docs" / filename).read_text(encoding="utf-8")
    # The page header carries the title; the document's own H1 would repeat it.
    text = re.sub(r"\A# .*\n", "", text)
    show_compact_page_header(title, lead)
    source, download = st.columns([4, 1], vertical_alignment="center")
    source.markdown('<div class="doc-source">' + build_external_link_html(
        f"docs/{filename} en GitHub", project.build_github_url(f"docs/{filename}")) + '</div>',
        unsafe_allow_html=True)
    path = project.PROJECT_DIR / "docs" / filename
    download.download_button("Descargar PDF", build_document_pdf(str(path), path.stat().st_mtime, title, lead),
                             file_name=f"GreenOcean_{filename.removesuffix('.md')}.pdf", mime="application/pdf",
                             icon=":material/download:", width="stretch", key=f"pdf_{filename}")
    with st.container(key="project_document"):
        position = 0
        for marker in DOCUMENT_DIAGRAM.finditer(text):
            st.markdown(text[position:marker.start()])
            show_document_diagram(marker.group(1), mode)
            position = marker.end()
        st.markdown(text[position:])
    st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)
    st.html(zoom.TIP_SCRIPT, unsafe_allow_javascript=True)
# endregion

# region Entry point
def show_document_page(mode, title, subtitle, renderer):
    show_page_header(title, subtitle)
    renderer(mode)


SHOW_PAGE_BY_TITLE = {
    PAGE_DOCUMENTATION: lambda mode: show_project_document(mode, PAGE_PRD),
    PAGE_PRD: lambda mode: show_project_document(mode, PAGE_PRD),
    PAGE_SAD: lambda mode: show_project_document(mode, PAGE_SAD),
    PAGE_ADR: lambda mode: show_project_document(mode, PAGE_ADR),
    PAGE_SCALABILITY: show_scalability_page,
    PAGE_STACK: lambda mode: show_stack_page(mode),
    PAGE_SECURITY: lambda mode: show_security_page(mode),
    PAGE_SECURITY_PLAN: lambda mode: show_project_document(mode, PAGE_SECURITY_PLAN),
    PAGE_SQL: lambda mode: sql_explorer.show_sql_explorer_page(mode),
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
    PAGE_KPI: show_kpi_page,
    PAGE_ARCHITECTURE: show_architecture_page,
    PAGE_DEVOPS: lambda mode: (show_compact_page_header(
        PAGE_DEVOPS, "Automatización, seguridad, observabilidad e informes."), show_devops_tab(mode)),
    PAGE_OPERATIONS: show_operations_page,
    PAGE_RUNS: show_runs_page,
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
# Every diagram animates by default, with no toggle (D-131); after 20 s without a
# mouse move, key, touch or scroll the page pauses CSS and SVG animations, and the
# next movement resumes them — so a forgotten tab does not keep spending resources.
IDLE_ANIMATION_SCRIPT = """<script>(() => {
    if (window.greenoceanIdleBound) { return; }
    window.greenoceanIdleBound = true;
    const IDLE_MS = 20000;
    let timer = null;
    const setPaused = (paused) => {
        document.documentElement.classList.toggle('greenocean-idle', paused);
        document.querySelectorAll('svg').forEach((svg) => {
            try { paused ? svg.pauseAnimations() : svg.unpauseAnimations(); } catch (_) {}
        });
    };
    const wake = () => {
        if (document.documentElement.classList.contains('greenocean-idle')) { setPaused(false); }
        clearTimeout(timer);
        timer = setTimeout(() => setPaused(true), IDLE_MS);
    };
    ['mousemove', 'pointerdown', 'keydown', 'wheel', 'touchstart', 'scroll'].forEach((name) =>
        window.addEventListener(name, wake, { passive: true, capture: true }));
    wake();
})();</script>"""
FOLD_SIDEBAR_SCRIPT = f"""<script>
(() => {{
// D-166: a phone turned sideways shows the computer layout, menu included. Streamlit
// folded the menu when the page opened upright, so it opens again on turning.
const phoneLandscape = window.matchMedia("(orientation: landscape) and (max-height: 500px)");
const openMenu = () => {{
    let attempts = 0;
    const open = () => {{
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const button = document.querySelector('[data-testid="stExpandSidebarButton"]');
        if (sidebar && sidebar.getAttribute("aria-expanded") === "true") {{ return; }}
        if (button) {{ button.click(); }} else if (attempts++ < 40) {{ setTimeout(open, 100); }}
    }};
    open();
}};
if (!window.greenoceanPhoneTurnBound) {{
    window.greenoceanPhoneTurnBound = true;
    phoneLandscape.addEventListener("change", (event) => {{ if (event.matches) {{ openMenu(); }} }});
    if (phoneLandscape.matches) {{ openMenu(); }}
}}
if (phoneLandscape.matches) {{ return; }}
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
    summary = lineage.summarize_build(*read_lineage(get_database_version()))
    st.markdown(f'<div class="page-lineage">{lineage.build_badge_html(summary)}</div>', unsafe_allow_html=True)
    st.caption(ATTRIBUTION_TEXT)


def order_windows():
    """The data-first route, followed by documentation and links."""
    return ROUTE + [SECTION_PROJECT, SECTION_RESOURCES, SECTION_KPI]


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
    st.html(PHONE_LAYOUT_HTML + FOLD_SIDEBAR_SCRIPT + RELOAD_HOME_SCRIPT + IDLE_ANIMATION_SCRIPT + build_visit_history_script(),
            unsafe_allow_javascript=True)


# D-166: the panel is read in landscape. A phone held upright sees one screen asking to
# turn it (no page can rotate a phone: only the reader can); turned, the phone gets
# the computer layout in miniature, every page whole, and no empty band on top.
# Tablets and computers never match these queries. Plain fills only: st.html strips
# SVG gradients.
PHONE_LAYOUT_HTML = """<style>
.go-rotate {display:none;}
@media (max-width:600px) and (orientation:portrait) {
  .go-rotate {display:flex; position:fixed; inset:0; z-index:2147483647; flex-direction:column;
    align-items:center; justify-content:center; gap:10px; padding:48px 32px 72px; text-align:center;
    background:radial-gradient(120% 70% at 50% 30%, #17406f 0%, #0f2747 55%, #0a1b33 100%);
    color:#cfd6e2; font-family:"Source Sans Pro",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
  .go-rotate .go-brand {font-size:26px; font-weight:600; color:#6ee7b7;}
  .go-rotate .go-brand span {color:#7dd3fc;}
  .go-rotate .go-sub {font-size:13px; color:#98a2b3;}
  .go-rotate .go-phone {position:relative; width:80px; height:150px; margin:56px 0 44px; border-radius:16px;
    background:#174a7c; border:5px solid #c3ccd8; box-shadow:0 24px 30px rgba(0,0,0,.45);
    animation:go-turn 3.2s cubic-bezier(.65,0,.35,1) infinite;}
  .go-rotate .go-phone i {position:absolute; display:block; border-radius:3px;}
  .go-rotate h2 {margin:0; font-size:30px; font-weight:600; color:#ffffff; line-height:1.2;}
  .go-rotate p {margin:0; max-width:300px; font-size:16px; line-height:1.45;}
  @keyframes go-turn {0%,18% {transform:rotate(0deg);} 45%,72% {transform:rotate(-90deg);} 100% {transform:rotate(0deg);}}
}
@media (orientation:landscape) and (max-height:500px) {
  /* The computer layout drawn at 1/0.62 the width, then shrunk back to the screen. */
  .stApp {transform:scale(.62); transform-origin:0 0; width:161.3vw !important; height:161.3vh !important;}
  /* Streamlit sizes its scrolling area to the screen height: it must grow with the scale. */
  [data-testid="stAppViewContainer"] > div, [data-testid="stMain"], [data-testid="stSidebar"] {height:161.3vh !important; max-height:none !important;}
  [data-testid="stHeader"] {display:none !important;}
  [data-testid="stMainBlockContainer"] {padding-top:.4rem !important;}
}
</style>
<div class="go-rotate" role="alertdialog" aria-label="Gira tu teléfono">
  <div class="go-brand">Green<span>Ocean</span></div>
  <div class="go-sub">Monitor de precios de alimentos</div>
  <div class="go-phone" aria-hidden="true">
    <i style="left:24px;top:4px;width:22px;height:5px;background:#0a1b33"></i>
    <i style="left:7px;top:18px;width:10px;height:110px;background:#6ee7b7;opacity:.6"></i>
    <i style="left:23px;top:18px;width:40px;height:9px;background:#ffffff;opacity:.5"></i>
    <i style="left:25px;top:44px;width:12px;height:12px;border-radius:50%;background:#7dd3fc"></i>
    <i style="left:45px;top:44px;width:12px;height:12px;border-radius:50%;background:#6ee7b7"></i>
    <i style="left:25px;top:66px;width:12px;height:12px;border-radius:50%;background:#fda4af"></i>
    <i style="left:45px;top:66px;width:12px;height:12px;border-radius:50%;background:#fde68a"></i>
    <i style="left:23px;top:94px;width:40px;height:6px;background:#ffffff;opacity:.35"></i>
  </div>
  <h2>Gira tu teléfono</h2>
  <p>El panel se lee en horizontal: así ves el pipeline completo y el menú de un vistazo.</p>
</div>"""


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



# D-213: the menu is a stack of colored blocks, one per kind of reader, always visible and
# open by default; each page lives in exactly one block. «Ver como» (D-209) is gone: every
# reader sees everything, so whoever wants the breadth of the work sees it at a glance.
# (key, title, (color on a dark sidebar, color on a light one), pages or source links)
# D-215, D-216: each block is a card in one of the panel's four tones (blue, Vantablack, dark
# grey, light grey), its accent a lighter or darker step of that same tone, nothing else; the documents sit at the end of their block and the
# documents' block closes the menu, just before the sources.
# (key, title, tone, accent, pages or source links)
MENU_BLOCKS = [
    ("negocio", "Negocio · BI", "azul", "#9cc8ff", [PAGE_HOME, PAGE_SEASONALITY]),
    ("ingenieria", "Ingeniería de datos", "vantablack", "#c7cdd6",
     [PAGE_DIAGRAMS, PAGE_ARCHITECTURE, PAGE_OPERATIONS, PAGE_SQL, PAGE_SAD]),
    ("devops", "DevOps y seguridad", "grafito", "#aab3bf", [PAGE_RUNS, PAGE_SECURITY, PAGE_SECURITY_PLAN]),
    ("stack", "Stack y evidencia", "azul", "#9cc8ff", [PAGE_STACK]),
    ("analisis", "Análisis de negocio · BA", "gris", "#334155", [PAGE_PRD, PAGE_ADR, PAGE_SCALABILITY]),
    ("fuentes", "Fuentes", "gris", "#334155", SOURCE_LINKS),
]
# Card tone → (background, text). Fixed in every theme, so each card reads the same everywhere.
CARD_TONES = {"azul": ("#12325a", "#e8f1ff"), "vantablack": ("#050607", "#e6e8ec"),
              "grafito": ("#2b2f36", "#eceff3"), "gris": ("#e6e9ee", "#1f2933")}


SOURCE_ICON_SVG = ('<svg class="nav-source-icon" viewBox="0 0 24 24" width="15" height="15" aria-hidden="true">'
                   '<path fill="currentColor" d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3zM5 5h6v2H5v12h12v-6h2v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"/></svg>')
SIDEBAR_TOP_LABELS = {REPORT_WINDOW: "Dashboard", SECTION_TECHNICAL: "Ingeniería de datos",
                      SECTION_PROJECT: "Proyecto", SECTION_LINKS: "Documentación", SECTION_SECURITY: "Seguridad",
                      SECTION_RESOURCES: "GitHub"}
SIDEBAR_LABELS = {PAGE_HOME: "Resumen semanal", PAGE_SEASONALITY: "Precios e inflación",
                  PAGE_DIAGRAMS: "Pipeline y linaje", PAGE_OPERATIONS: "Calidad y auditoría",
                  PAGE_RUNS: "Centro de operación",
                  PAGE_DOCUMENTATION: "Documentación", PAGE_MANUAL: "Manual",
                  PAGE_COVER: "Descripción general", PAGE_BUSINESS: "Alcance del proyecto"}


def read_current_view(window):
    """The view drawn in a window: the address first, then the last choice."""
    views = read_window_views(window)
    view = st.query_params.get(VIEW_PARAMETER, st.session_state.get(window_view_key(window), views[0]))
    return view if view in views else views[0]


def build_section_colors_css(dark):
    """Each block as a HUD-like card (D-215): its tone, a glowing border in its accent and
    corner brackets; the title in the accent and the pages in the card's text color."""
    rules = []
    for key, _, tone, accent, _ in MENU_BLOCKS:
        background, text = CARD_TONES[tone]
        rules.append(f'.st-key-nav_block_{key} {{position:relative; margin:0 0 12px !important; padding:3px 6px 4px !important;'
                     f' background:linear-gradient(160deg,color-mix(in srgb,{background} 92%,{accent}) 0%,{background} 60%);'
                     f' border:1px solid color-mix(in srgb,{accent} 55%,transparent); border-radius:6px;'
                     f' box-shadow:0 0 14px color-mix(in srgb,{accent} 22%,transparent), inset 0 0 18px color-mix(in srgb,{accent} 8%,transparent);'
                     f' gap:0 !important;}}')
        rules.append(f'.st-key-nav_block_{key}::before, .st-key-nav_block_{key}::after {{content:""; position:absolute;'
                     f' width:12px; height:12px; pointer-events:none;}}')
        rules.append(f'.st-key-nav_block_{key}::before {{top:-1px; left:-1px; border-top:2px solid {accent};'
                     f' border-left:2px solid {accent}; border-top-left-radius:6px;}}')
        rules.append(f'.st-key-nav_block_{key}::after {{bottom:-1px; right:-1px; border-bottom:2px solid {accent};'
                     f' border-right:2px solid {accent}; border-bottom-right-radius:6px;}}')
        rules.append(f'.st-key-nav_block_{key} [data-testid="stPageLink"] p, .st-key-nav_block_{key} .nav-source-link '
                     f'{{color:{text} !important; -webkit-text-fill-color:{text} !important; text-shadow:none !important;}}')
        rules.append(f'.st-key-nav_block_{key} [data-testid="stIconMaterial"], .st-key-nav_block_{key} .nav-source-icon '
                     f'{{color:{accent} !important;}}')
        # The current page: a bar in the card's accent.
        rules.append(f'.st-key-nav_block_{key} [class*="_nav_current"] [data-testid="stPageLink"] a '
                     f'{{box-shadow:inset 2px 0 {accent} !important; border-color:transparent !important;}}')
        rules.append(f'.st-key-nav_block_{key} [data-testid="stPageLink"] a:hover {{background:color-mix(in srgb,{accent} 14%,transparent) !important;}}')
        rules.append(f'.st-key-nav_group_{key} button {{border-bottom:1px solid color-mix(in srgb,{accent} 40%,transparent) !important;'
                     f' border-radius:0 !important; margin-bottom:3px;}}')
        rules.append(f'.st-key-nav_group_{key} button p {{color:{accent} !important; -webkit-text-fill-color:{accent} !important;'
                     f' font-size:.7rem !important; font-weight:650 !important; letter-spacing:.08em !important;'
                     f' text-transform:uppercase;}}')
    rules.append('[class*="st-key-nav_block_"], [class*="st-key-nav_group_"], [class*="st-key-nav_group_"] > div, '
                 '[class*="st-key-nav_group_"] button {width:100% !important; box-sizing:border-box;}')
    rules.append('[class*="st-key-nav_group_"] button > div, [class*="st-key-nav_group_"] button p '
                 '{justify-content:flex-start !important; text-align:left !important;}')

    # Only the sources leave the app, so only they look like web links: a fine underline.
    rules.append('[data-testid="stSidebar"] a.nav-source-link {text-decoration:underline !important; text-decoration-thickness:1px; '
                 'text-underline-offset:3px; text-decoration-color:color-mix(in srgb, currentColor 55%, transparent);}')
    rules.append('[data-testid="stSidebar"] a.nav-source-link:hover {text-decoration-color:currentColor;}')
    return "\n    ".join(rules)


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
    /* D-215: a narrow inner margin, so the menu cards hold long page names on one line. */
    [data-testid="stSidebarUserContent"] {{padding:6px 4px 0 !important;}}
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
        font-weight:400; letter-spacing:-.01em; padding-left:5px;
        white-space:normal; overflow:visible; text-overflow:clip; line-height:1.3;
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}}
    /* D-209: a small icon before each page says what it is, in its section's color. */
    [data-testid="stSidebar"] [data-testid="stPageLink"] [data-testid="stIconMaterial"] {{font-size:15px !important;
        width:15px; color:currentColor; opacity:.9;}}
    [class*="st-key-nav_child_"] [data-testid="stPageLink"] a {{color:{child_green} !important;}}
    .nav-source-icon {{vertical-align:-3px; margin-right:8px;}}
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
    {build_section_colors_css(dark)}
    /* GitHub's mark on a light pill in the footer (D-124): a near-black logo on a
       near-white background reads on every sidebar, navy included, where the
       blue mark inside the list almost vanished. */
    .st-key-sidebar_tools {{gap:8px !important; justify-content:flex-start !important;}}
    .st-key-sidebar_tools > div {{flex:0 0 auto !important; width:auto !important;}}
    .sidebar-github {{display:inline-flex; align-items:center; justify-content:center;
        width:38px; height:38px; border-radius:11px; background:#f6f8fa;
        border:1px solid rgba(255,255,255,.55); color:#1f2328 !important;
        box-shadow:0 6px 14px -6px rgba(0,0,0,.45); transition:transform .12s ease, box-shadow .12s ease;}}
    .sidebar-github svg {{fill:#1f2328;}}
    .sidebar-github:hover {{transform:translateY(-1px); box-shadow:0 9px 18px -6px rgba(0,0,0,.5);}}
    .sidebar-github-current {{outline:2px solid {palette['accent']}; outline-offset:2px;}}
    /* «Fuentes»: external children in the same green as every other child (D-118). */
    .nav-source-link {{display:block; padding:3px 7px 3px 7px; margin:1px 0; border-radius:5px;
        font-size:.78rem; font-weight:400; letter-spacing:-.005em; text-decoration:none !important;
        color:{child_green} !important; -webkit-text-fill-color:{child_green} !important;
        line-height:1.5;
        transition:background .12s ease;}}
    .nav-source-link:hover {{background:color-mix(in srgb,{text} 7%,transparent);}}
    .st-key-sidebar_footer {{position:fixed; left:17px; bottom:0; width:266px; padding:13px 5px 12px;
        background:linear-gradient(180deg,transparent 0%,{sidebar_bottom} 18%); gap:7px !important; z-index:5;
        border-top:1px solid {hairline};}}
    /* The alert trigger, now on top of the Resumen (D-169), keeps its red, quiet look. */
    .st-key-home_alert_bar {{margin:-4px 0 -10px;}}
    .st-key-home_alert_trigger button {{justify-content:flex-start; border:0 !important;
        background:transparent !important; color:{alert_text} !important; border-radius:5px;
        padding:3px 7px !important; min-height:27px; box-shadow:none !important;}}
    .st-key-home_alert_trigger button:hover {{background:color-mix(in srgb,{alert_text} 10%,transparent) !important;}}
    .st-key-home_alert_trigger button p {{color:{alert_text} !important; -webkit-text-fill-color:{alert_text} !important;
        font-weight:560; font-size:.78rem; text-align:left; letter-spacing:-.005em;}}
    .st-key-sidebar_appearance [data-testid="stPopover"] button {{background:transparent !important;
        box-shadow:none !important; color:{quiet} !important; padding:6px 8px !important;}}
    .st-key-sidebar_appearance [data-testid="stPopover"] button p {{color:{quiet} !important; font-size:.76rem !important;}}
    .st-key-sidebar_footer [data-testid="stCaptionContainer"] p {{color:{text} !important; opacity:.75;
        font-size:.67rem; line-height:1.35; padding:0 3px;}}
    </style>"""


SIDEBAR_NAV_VERSION = 8


def show_sidebar_navigation(windows_by_title, current_window, order):
    """The menu (D-213): colored blocks by kind of reader, open by default, each a folder
    that a click folds; under each title, its pages with their icon (D-209)."""
    st.sidebar.markdown(build_sidebar_css(get_mode()), unsafe_allow_html=True)
    if st.session_state.get("sidebar_nav_version") != SIDEBAR_NAV_VERSION:
        for key, *_ in MENU_BLOCKS:
            st.session_state[f"nav_open_{key}"] = True
        st.session_state["sidebar_nav_version"] = SIDEBAR_NAV_VERSION
    current_view = read_current_view(current_window)
    for key, title, _, _, pages in MENU_BLOCKS:
        open_key = f"nav_open_{key}"
        is_open = st.session_state.get(open_key, True)
        with st.sidebar.container(key=f"nav_block_{key}"):
            show_menu_block(windows_by_title, current_window, current_view, key, title, pages, open_key, is_open)
    show_sidebar_footer(current_window)


def show_menu_block(windows_by_title, current_window, current_view, key, title, pages, open_key, is_open):
    """One card of the menu: its title, which folds it, and its pages (D-215)."""
    with st.container(key=f"nav_group_{key}"):
        if st.button(f"{'⌄' if is_open else '›'}  {title}", key=f"nav_toggle_{key}"):
            st.session_state[open_key] = not is_open
            st.rerun()
    if not is_open:
        return
    if pages is SOURCE_LINKS:
        # They leave the app (D-118): plain external links, not Streamlit pages.
        for index, (name, url) in enumerate(pages):
            with st.container(key=f"nav_child_{key}_{index}"):
                st.markdown(f'<a class="nav-source-link" href="{html.escape(url, quote=True)}" '
                            f'target="_blank" rel="noopener noreferrer">{SOURCE_ICON_SVG}{html.escape(name)}</a>',
                            unsafe_allow_html=True)
        return
    for index, view in enumerate(pages):
        window = WINDOW_OF_VIEW[view]
        active = window == current_window and view == current_view
        with st.container(key=f"nav_child_{key}_{index}" + ("_nav_current" if active else "")):
            st.page_link(windows_by_title[window], label=SIDEBAR_LABELS.get(view, view),
                         icon=PAGE_ICONS.get(view), query_params=keep_context() | {VIEW_PARAMETER: view})


def build_sidebar_github_html(is_current):
    """GitHub's mark on a light pill in the sidebar footer (D-124): not a row of the
    list, where it read as one more section and its blue mark sank into the navy."""
    current = " sidebar-github-current" if is_current else ""
    return (f'<a class="sidebar-github{current}" href="{html.escape(build_page_address(PAGE_LINKS), quote=True)}" '
            f'target="_self" aria-label="GitHub del proyecto" title="GitHub del proyecto">'
            f'{build_github_icon_svg(20)}</a>')


def show_alert_trigger():
    """The price alerts, at the top of the Resumen (D-169): the same button and dialog
    the sidebar held since D-096, now where the week's figures are."""
    alerts_now = read_price_alerts()
    week = read_latest_week()
    count = int((alerts_now["week_start"] == week).sum()) if not alerts_now.empty else 0
    with st.container(key="home_alert_bar", horizontal=True, horizontal_alignment="right",
                      vertical_alignment="center"):
        if st.button(f"▲  Alerta de precio · {count}", key="home_alert_trigger",
                     help=f"{count} cambios de precio fuera de lo habitual esta semana. Abre el detalle por familia."):
            st.session_state["home_alert_selected_family"] = None
            show_home_alerts_dialog(f"{week:%Y-%m-%d}", ALL_VALUES, None, get_mode())


def show_sidebar_footer(current_window=None):
    """Appearance and the GitHub mark, always at the bottom, on every page."""
    with st.sidebar.container(key="sidebar_footer"):
        with st.container(key="sidebar_tools", horizontal=True, vertical_alignment="center"):
            with st.container(key="sidebar_appearance"):
                show_theme_field()
            st.markdown(build_sidebar_github_html(current_window == SECTION_RESOURCES),
                        unsafe_allow_html=True)
        st.caption("Fuente: ODEPA · actualización automática cada martes.")


# D-172: Streamlit reloads this file on each run but keeps the imported bi/* modules
# as they were; on Streamlit Cloud a push then shows a new menu with old pages until
# someone reboots the app. Each run compares the modules' files with the time they
# were loaded and reloads the ones that changed, dependencies first.
# The times live on the bi package, which outlives the script runs: Streamlit
# re-executes this file on every run, so a global here would start empty each time.
MODULE_TIMES = vars(bi).setdefault("MODULE_TIMES", {})


def reload_changed_modules():
    """Reload every bi/* module whose file changed since it was loaded."""
    package = Path(__file__).resolve().parent
    changed = []
    for name, module in sorted(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if not name.startswith("bi.") or name == __name__ or not file or not file.startswith(str(package)):
            continue
        try:
            modified = os.stat(file).st_mtime_ns
        except OSError:
            continue
        if name not in MODULE_TIMES:
            MODULE_TIMES[name] = modified
        elif modified != MODULE_TIMES[name]:
            MODULE_TIMES[name] = modified
            changed.append(module)
    # brand_icons feeds devops: reload the ones without bi.* imports first.
    for module in sorted(changed, key=lambda module: sum(1 for value in vars(module).values()
                                                         if getattr(value, "__name__", "").startswith("bi."))):
        importlib.reload(module)
    return [module.__name__ for module in changed]


def main():
    """Theme, navigation with icons and the chosen page."""
    reload_changed_modules()
    st.set_page_config(page_title="Monitor de precios de alimentos", layout="wide",
                       # A green tile with white bars: the Material glyph was dark and
                       # nearly invisible on a dark browser tab.
                       page_icon=str(Path(__file__).resolve().parent / "assets" / "favicon.png"))
    if not queries.DATABASE_FILE.exists():
        st.error("Falta etl/datos.db. Ejecuta primero: python etl/etl.py")
        return
    settle_theme()
    st.session_state.pop(PROFILE_PARAMETER, None)
    st.query_params.pop("perfil", None)
    restore_return_context()
    # «Ver como» left the menu (D-213); an old ?ver= address still opens, without it.
    st.query_params.pop("ver", None)
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
        "Referencias": [windows_by_title[SECTION_RESOURCES]],
        "Compatibilidad": [windows_by_title[SECTION_PROJECT], windows_by_title[SECTION_KPI]] + redirects},
        position="hidden")
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
