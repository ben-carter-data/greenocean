"""Streamlit dashboard for the price monitor.

Run it with:  streamlit run bi/dashboard.py

It reads etl/datos.db through the named queries of bi/queries.sql, and the
state of the weekly pipeline through the GitHub API (bi/control.py).
Texts shown to the user are in Spanish; code and comments are in English.
The two color modes live in .streamlit/config.toml, the charts in bi/charts.py.
"""
import base64
import hmac
import html
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# region Imports of the project
# Streamlit runs this file as a script, so the project folder is added to the
# import path to reach the other modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import (alerts, architecture, charts, control, devops, explorer, lag, market_charts, market_style, project,  # noqa: E402
                queries, star_model, zoom)
from etl import etl  # noqa: E402
# endregion

# region Constants
# The menu is the project journey; every destination is directly accessible.
PAGE_HOME = "Dashboard"
PAGE_BUSINESS = "Definición del proyecto"
PAGE_DIAGRAMS = "Pipeline y arquitectura"
PAGE_ARCHITECTURE = "Modelo de datos"
PAGE_ANALYSIS = "Esta semana"
PAGE_GAP = "Brecha de precio"
PAGE_CHANNELS = "Canales y regiones"
PAGE_SEASONALITY = "Histórico y estacionalidad"
PAGE_ALERTS = "Alertas"
PAGE_KPI = "Indicadores · BI"
PAGE_DATA_AND_CODE = "Consulta de datos"
PAGE_QUERIES = "Consultas SQL"
PAGE_CODE = "Código Python y SQL"
PAGE_DEVOPS = "DevOps y seguridad"
PAGE_OPERATIONS = "Monitoreo"
PAGE_RUNS = "Ejecuciones"
PAGE_RULES = "Reglas de calidad"
PAGE_MANUAL = "Manual"
PAGE_DECISIONS = "Decisiones"
PAGE_GLOSSARY = "Glosario"
PAGE_LINKS = "Enlaces"
NAVIGATION_GROUPS = {
    "01 · Visualizaciones": [PAGE_HOME, PAGE_ANALYSIS, PAGE_GAP, PAGE_CHANNELS,
                             PAGE_ALERTS, PAGE_SEASONALITY, PAGE_DIAGRAMS,
                             PAGE_ARCHITECTURE, PAGE_DEVOPS],
    "02 · Negocio y criterios": [PAGE_BUSINESS, PAGE_KPI, PAGE_RULES],
    "03 · Datos e implementación": [PAGE_DATA_AND_CODE, PAGE_QUERIES, PAGE_CODE],
    "04 · Operación": [PAGE_OPERATIONS, PAGE_RUNS, PAGE_MANUAL],
    "05 · Documentación": [PAGE_DECISIONS, PAGE_GLOSSARY, PAGE_LINKS],
}
PAGES = [page for pages in NAVIGATION_GROUPS.values() for page in pages]
HOME_PAGE = PAGE_HOME
PAGE_ICONS = {
    PAGE_HOME: ":material/dashboard:", PAGE_BUSINESS: ":material/assignment:",
    PAGE_DIAGRAMS: ":material/account_tree:", PAGE_ARCHITECTURE: ":material/schema:",
    PAGE_ANALYSIS: ":material/monitoring:", PAGE_GAP: ":material/compare_arrows:",
    PAGE_CHANNELS: ":material/storefront:", PAGE_SEASONALITY: ":material/calendar_month:",
    PAGE_ALERTS: ":material/notifications_active:", PAGE_KPI: ":material/insights:",
    PAGE_DATA_AND_CODE: ":material/database:", PAGE_QUERIES: ":material/data_object:",
    PAGE_CODE: ":material/code:", PAGE_RULES: ":material/rule:", PAGE_DEVOPS: ":material/shield:",
    PAGE_OPERATIONS: ":material/health_and_safety:", PAGE_RUNS: ":material/play_circle:",
    PAGE_MANUAL: ":material/menu_book:", PAGE_DECISIONS: ":material/history:",
    PAGE_GLOSSARY: ":material/dictionary:", PAGE_LINKS: ":material/link:",
}
PAGE_PATHS = {
    PAGE_HOME: "dashboard", PAGE_BUSINESS: "negocio", PAGE_DIAGRAMS: "diagramas",
    PAGE_ARCHITECTURE: "arquitectura", PAGE_ANALYSIS: "analisis", PAGE_GAP: "brecha",
    PAGE_CHANNELS: "canales", PAGE_SEASONALITY: "estacionalidad", PAGE_ALERTS: "alertas",
    PAGE_KPI: "indicadores", PAGE_DATA_AND_CODE: "datos-y-codigo", PAGE_QUERIES: "queries",
    PAGE_CODE: "codigo", PAGE_RULES: "reglas", PAGE_DEVOPS: "devops", PAGE_OPERATIONS: "operaciones",
    PAGE_RUNS: "ejecuciones", PAGE_MANUAL: "manual", PAGE_DECISIONS: "decisiones",
    PAGE_GLOSSARY: "glosario", PAGE_LINKS: "enlaces",
}
TAB_IDEA = "Idea de negocio"
TAB_KPI = "KPI y cálculos"
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
    TAB_MANUAL: PAGE_MANUAL, TAB_DECISIONS: PAGE_DECISIONS, TAB_GLOSSARY: PAGE_GLOSSARY,
    TAB_PIPELINE: PAGE_DIAGRAMS, TAB_MODEL: PAGE_ARCHITECTURE, TAB_DEVOPS: PAGE_DEVOPS,
    TAB_CODE: PAGE_CODE, TAB_RUNS: PAGE_RUNS, TAB_QUALITY: PAGE_OPERATIONS,
    TAB_WEEK: PAGE_ANALYSIS, TAB_GAP: PAGE_GAP, TAB_CHANNELS: PAGE_CHANNELS,
    TAB_SEASONALITY: PAGE_SEASONALITY, TAB_ALERTS: PAGE_ALERTS,
    TAB_EXPLORER: PAGE_DATA_AND_CODE, TAB_QUERIES: PAGE_QUERIES,
}
OLD_PATHS = {
    "inicio": (PAGE_HOME, None), "el-proyecto": (PAGE_HOME, None), "panel": (PAGE_HOME, None),
    "margenes": (PAGE_GAP, None), "canales-y-regiones": (PAGE_CHANNELS, None),
    "consultas": (PAGE_DATA_AND_CODE, None), "pipeline": (PAGE_DIAGRAMS, None),
    "centro-de-control": (PAGE_RUNS, None), "calidad-de-datos": (PAGE_OPERATIONS, None),
}
OLD_HOME_TABS = {"Fuentes y cruces": TAB_IDEA, "Arquitectura": TAB_PIPELINE,
                 "Modelo de datos": TAB_MODEL, "Código": TAB_CODE}
OLD_TAB_PAGES = {(PAGE_OPERATIONS, "Enlaces"): PAGE_LINKS}
TAB_PARAMETER = "seccion"
THEME_PARAMETER = "tema"
KPI_PARAMETER = "kpi"
PROFILE_PARAMETER = "visitor_profile"
VISITOR_PROFILES = {
    "Reclutamiento": "Recorre el resultado, las decisiones y el código del proyecto.",
    "Negocio / gerencia": "Empieza por las variaciones, las alertas y las preguntas de negocio.",
    "Analista BI": "Explora los indicadores, filtra los datos y revisa las queries SQL.",
    "Ingeniería de datos": "Sigue el pipeline, las reglas de calidad, el código y las ejecuciones.",
}
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
# Consulta por clics (D-060): a form, a summary, a table and a detail.
PAGE_SIZES = [20, 50, 100]
TABLE_ROW_HEIGHT = 35
SEARCH_APPLIED = "search_applied"
SEARCH_PAGE = "search_page"
# Icon and status color of each alert state; the label always goes with them.
ALERT_STATE_STYLES = {explorer.ALERT_NORMAL: ("●", "good"),
                      explorer.ALERT_ATTENTION: ("▲", "warning"),
                      explorer.ALERT_OUT: ("◆", "critical"),
                      explorer.ALERT_UNKNOWN: ("○", "unknown")}
SEARCH_COLUMNS = {"product": "Producto", "variety": "Variedad", "quality": "Calidad",
                  "region": "Región", "channel": "Canal", "week_start": "Semana",
                  "price": "Precio", "normalized_unit": "Unidad", "variation": "Variación %",
                  "gap": "Brecha %", "alert_state": "Alerta"}

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
                       "están en cada estado, según K6 sobre su serie nacional. **Normal:** su "
                       "cambio está dentro de 1,5 desviaciones estándar de lo habitual; "
                       "**Atención:** entre 1,5 y 2; **Fuera de rango:** más de 2 (es una "
                       "alerta K6); **Sin dato:** la serie aún no tiene 12 semanas. Toca una "
                       "tarjeta o un número para filtrar.")
SEARCH_TABLE_HINT = ("**Qué muestra:** cada precio semanal que cumple la búsqueda, con su "
                     "cambio frente a la semana anterior (▲ subió, ▼ bajó), la brecha sobre el "
                     "precio mayorista y su estado de alerta. Ordena con un clic en el título "
                     "de una columna; selecciona una fila para ver su ficha.")
# The project page. Texts come from docs/DISENO.md (sections 2 to 4) and DECISIONES.md.
# Idea de negocio, in short pieces: what each card says, without repeating
# «Empieza aquí» (the problem in three sentences lives there).
AUDIENCE_CARDS = [
    ("Analista de pricing o compras", "Márgenes, canales, regiones y alertas.", PAGE_ANALYSIS),
    ("Equipo de datos", "Si la carga funcionó y qué quedó fuera.", TAB_QUALITY),
    ("Más adelante", "Un resumen para gerencia y una vista simple para consumidores.", None),
]
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
    "Este proyecto no es un producto oficial de ODEPA.")
# endregion


# region Style
def get_mode():
    """Theme chosen by the reader in the sidebar; Vantablack until they choose."""
    theme = st.session_state.get(THEME_PARAMETER, st.query_params.get(THEME_PARAMETER))
    return theme if theme in charts.THEMES else charts.MODE_DARK


def build_base_mode_script(base):
    """Keep native widgets on the same base as the project palette.

    Streamlit infers st.context.theme from the CSS background, so it cannot
    detect a native widget theme that disagrees with the overridden page color.
    The cached frontend choice is checked instead, with one reload per change.
    """
    value = json.dumps("Dark" if base == charts.BASE_DARK else "Light")
    return f"""<script>
    const page = window.parent;
    const attempt = "project-base-request-" + page.location.pathname;
    const key = "stActiveTheme-" + page.location.pathname + "-v2";
    const wanted = {value};
    try {{
        const current = JSON.parse(page.localStorage.getItem(key) || "null");
        const requested = page.sessionStorage.getItem(attempt);
        page.sessionStorage.setItem(attempt, wanted);
        if (current !== wanted && requested !== wanted) {{
            page.localStorage.setItem(key, JSON.stringify(wanted));
            // The bound widget's URL update can arrive after this iframe.
            // Preserve the chosen palette before reloading native widgets.
            const address = new URL(page.location.href);
            address.searchParams.set("tema", wanted === "Light" ? "Corporativo" : "Vantablack");
            page.history.replaceState(null, "", address.toString());
            page.location.reload();
        }}
    }} catch (error) {{ /* CSS remains usable when browser storage is unavailable. */ }}
    </script>"""


def match_base_mode(theme):
    """Check the frontend cache, including after either direction of a theme switch."""
    components.html(build_base_mode_script(charts.get_palette(theme)["base"]), height=0)


def build_theme_css(palette):
    """Page, sidebar and links in the colors of the active theme (T-44, D-052).

    Streamlit's own widgets keep the colors of its base mode; the theme only
    restyles what it can do without fighting them.
    """
    return f"""
    .stApp, [data-testid="stHeader"] {{ background: {palette["background"]}; }}
    [data-testid="stSidebar"] {{ background: {palette["sidebar"]}; }}
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] span,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: {palette["sidebar_text"]};
    }}
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
    [data-testid="stMainBlockContainer"] {{ padding-top:2rem; }}
    .page-freshness {{ color:{palette["text"]}; font-size:0.82rem; margin-bottom:8px; }}
    [data-testid="stMain"] h1 {{ font-size:clamp(1.7rem,3vw,2.35rem); line-height:1.15; }}
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
        .mobile-rankings {{ display:block; }}
    }}
    .resource-tree {{ list-style:none; padding:0 0 0 18px; border-left:1px solid {palette["card_border"]}; }}
    .devops-cycle {{ max-width:1000px; margin:8px auto 20px; }}
    .devops-cycle > svg {{ width:100%; height:auto; display:block; }}
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
    .page-subtitle {{ color: {palette["text"]}; margin-top: -0.6rem; }}
    .kpi-label {{ color: {palette["text"]}; font-size: 0.9rem; }}
    .kpi-value {{ font-size: 2rem; font-weight: 700; color: {palette["strong_text"]};
                 line-height: 1.2; }}
    .kpi-note {{ color: {palette["text"]}; font-size: 0.8rem; }}
    .kpi-link {{ margin-left: 10px; font-size: 0.8rem; font-weight: 400; }}
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
    """


def apply_style(mode):
    """Add the dashboard CSS to the page."""
    st.markdown(f"<style>{build_style_css(mode)}</style>", unsafe_allow_html=True)


def open_card(key, title=None, caption=None, hint=None, kpi=None):
    """A rounded card; use it with 'with'. The key must be unique on the page.

    hint, when given, is a short explanation in plain words that appears when
    the mouse passes over the ⓘ next to the title. kpi, when given, adds a link
    «¿Cómo se calcula K1?» to the details of that indicator in Inicio.
    """
    card = st.container(key=f"card_{key}")
    hint_icon = build_hint_icon(hint) if hint else ""
    if kpi:
        definition = {"K1": "brecha entre consumidor y mayorista", "K2": "brecha entre canales",
                      "K3": "índice de precio regional", "K4": "estacionalidad de precios",
                      "K5": "rezago descriptivo", "K6": "variaciones y alertas",
                      "K7": "cobertura de productos comparables", "K8": "filas rechazadas"}
        hint = (hint + " " if hint else "") + f"{kpi}: {definition.get(kpi, 'indicador del proyecto')}."
        hint_icon = build_hint_icon(hint)
    kpi_link = build_kpi_link(kpi) if kpi else ""
    if title or hint:
        card.markdown(f'<div class="card-title">{build_component_symbol(component_kind(key, title))}{html.escape(title or "")}{hint_icon}'
                      f'{kpi_link}</div>', unsafe_allow_html=True)
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
    parameters = {}
    profile = st.session_state.get(PROFILE_PARAMETER)
    if profile in VISITOR_PROFILES:
        parameters["perfil"] = profile
    theme = st.session_state.get(THEME_PARAMETER)
    if theme in charts.THEMES:
        parameters[THEME_PARAMETER] = theme
    if tab:
        parameters[TAB_PARAMETER] = tab
    if kpi:
        parameters[KPI_PARAMETER] = kpi
    query = f"?{urlencode(parameters)}" if parameters else ""
    # The first page of the navigation is the home page: Streamlit serves it at
    # the root of the app, and its own path does not exist.
    path = "./" if page_title == HOME_PAGE else PAGE_PATHS[page_title]
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
    """«¿Cómo se calcula K7?»: opens the details of that indicator in Inicio."""
    address = build_page_address(PAGE_KPI, kpi=kpi)
    return (f'<span class="kpi-link">{build_link_html(f"¿Cómo se calcula {kpi}?", address)}'
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
document.querySelectorAll(".link-card a").forEach((link) => {
    link.target = "_blank"; link.rel = "noopener";
});
</script>"""


def build_link_card_html(link):
    """Name, icon and one line of description; the address is never shown as text."""
    return (f'<div class="link-card"><a href="{html.escape(link["url"], quote=True)}" '
            f'target="_blank" rel="noopener"><span class="link-icon">{link["icon"]}</span>'
            f'<span class="link-text"><strong>{html.escape(link["name"])}</strong>'
            f'<small>{html.escape(link["description"])}</small></span></a>'
            f'<button type="button" class="copy-link">Copiar enlace</button></div>')


def build_link_cards_html(links):
    """A grid of link cards; links without an address (not published yet) stay out."""
    cards = "".join(build_link_card_html(link) for link in links if link["url"])
    return f'<div class="link-grid">{cards}</div>'


def show_link_cards(links):
    """Draw link cards that open in a new tab, each with its «Copiar enlace» button."""
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
    columns, when given, are the three places for the three choices.
    """
    options = read_key_options(query_name)
    group_column, product_column, key_column = columns or st.columns(3)
    with group_column:
        group = remember_filter("group", choose_value(
            "Grupo", options["product_group"].unique(), recall_filter("group", DEFAULT_GROUP)))
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
        ("chart", r"precio|variaci|brecha|calendario|[ií]ndice|k[1-8]|indicador|tendencia"),
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
    latest_run = read_latest_run()
    run_kind = "ok" if latest_run["status"] == etl.STATUS_LOADED else "failed"
    run_text = "Carga correcta" if run_kind == "ok" else "Última carga con falla"
    freshness = format_chile_time(parse_run_start(latest_run["started_at"]))
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


def choose_analysis_filters():
    """Group, product, variety, region and channels, once for every tab of Análisis."""
    columns = st.columns([1, 1, 1.4, 1.3, 1.8])
    key = choose_product_key("k3_regional_index", columns[:3])
    rows = read_indicator_for_key("k3_regional_index", key)
    with columns[3]:
        region = remember_filter("region", choose_value(
            "Región", rows["region"].unique(), recall_filter("region", DEFAULT_REGION)))
    consumer_channels = sorted(channel for channel in rows["channel"].unique()
                               if channel != WHOLESALE_LABEL)
    remembered = [channel for channel in recall_filter("channels", DEFAULT_MARGIN_CHANNELS)
                  if channel in consumer_channels]
    with columns[4]:
        channels = remember_filter("channels", st.multiselect(
            "Canal", consumer_channels, default=remembered))
    st.caption("La selección se recuerda al recorrer las secciones de análisis.")
    return {"key": key, "region": region, "channels": channels}


def read_margin_rows(filters):
    """K1 rows of the chosen product and region."""
    rows = read_indicator_for_key("k1_margin", filters["key"])
    return rows[rows["region"] == filters["region"]]


@st.cache_data
def read_cached_latest_variations(database_version):
    """Weekly variation of every national price series in the latest week."""
    prices = alerts.add_weekly_variation(queries.run_query("k6_national_weekly_price"))
    latest = prices[prices["week_start"] == prices["week_start"].max()]
    return add_display_columns(latest[latest["variation"].notna()])


def show_week_ranking(filters, mode):
    """Card: the largest price changes of the week in the chosen group and channels."""
    group = filters["key"]["product_group"]
    rows = read_cached_latest_variations(get_database_version())
    rows = rows[(rows["product_group"] == group) & rows["channel"].isin(filters["channels"])]
    with open_card("week_ranking", f"Mayores variaciones de la semana · {group}",
                   hint=WEEK_RANKING_HINT, kpi="K6"):
        if rows.empty:
            st.info(NO_DATA_TEXT)
            return
        st.caption(f"Semana del {rows['week_start'].max():%d-%m-%Y}, frente a la anterior.")
        largest = rows.loc[rows["variation"].abs().sort_values(ascending=False).index]
        largest = largest.head(RANKING_SIZE)
        bar_rows = pd.DataFrame({
            "label": [f"{describe_product(row)} · {row['channel']}"
                      for row in largest.to_dict("records")],
            "value": largest["variation"].to_numpy() * 100})
        show_chart(charts.draw_variation_bars(bar_rows, mode))


def show_week_history(rows, filters, mode):
    """The long history, folded: wholesale and one channel per chart (two lines)."""
    with st.expander("Ver evolución histórica", expanded=True):
        for channel in filters["channels"]:
            channel_rows = rows[rows["channel"] == channel]
            if not channel_rows.empty:
                show_overview_trend(channel_rows, mode, key=f"week_history_{channel}",
                                    title=f"Precio por semana · mayorista y {channel}")


def show_week_tab(mode, filters):
    """This week: the price cards (12 weeks of trend) and the week's largest changes;
    the long history folded (D-059)."""
    rows = read_margin_rows(filters)
    if rows.empty:
        st.info(NO_MARGIN_TEXT)
    else:
        show_overview_figures(rows, mode)
    show_week_ranking(filters, mode)
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


def build_question_cards():
    """One card per business question: its state, where it applies and where to see it."""
    cards = []
    for number, (question, place, state, scope) in enumerate(BUSINESS_QUESTIONS, start=1):
        state_text, _ = QUESTION_STATES[state]
        cards.append(build_info_card_html(question, scope, label=f"P{number} · {state_text}",
                                          link=build_place_link(place)))
    return cards


def show_questions(mode):
    """What the panel answers, first: it is what a visitor came for."""
    show_section_intro("Requisitos de negocio", "Seis preguntas de un área de pricing o "
                       "abastecimiento; cada una lleva a su sección de análisis.", True)
    show_info_cards(build_question_cards())


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
    with st.expander("Ver detalles", expanded=True):
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
    with st.expander("Ver detalles", expanded=True):
        st.markdown(WHY_DETAILS)


@st.cache_data
def read_cached_week_span(database_version):
    """(weeks, first Monday, last Monday) with prices, read once per database."""
    return project.read_week_span()


def format_iso_date(text):
    """«2026-10-05» as «05-10-2026»."""
    return f"{pd.Timestamp(text):%d-%m-%Y}"


def list_star_panels(row_counts, definitions):
    """(table, title, text, JOIN, real figures) of each table of the star (T-59)."""
    week_count, first_week, last_week = read_cached_week_span(get_database_version())
    loaded_at = format_chile_time(parse_run_start(read_latest_run()["started_at"]))
    panels = [
        ("weekly_price", "weekly_price · tabla de hechos",
         "El centro de la estrella: cada fila es un precio semanal. Las claves (FK) la unen "
         "a cada punta; las medidas en cian son lo que se analiza.",
         "weekly_price\nJOIN dim_product USING (product_id)\n"
         "JOIN dim_region USING (region_id)\nJOIN dim_channel USING (channel_id)",
         f"{charts.format_thousands(row_counts['weekly_price'])} filas · datos al {loaded_at}"),
        (star_model.WEEK_CARD, "Semana · week_start",
         "Todavía no es una tabla: la semana es la columna week_start de weekly_price, el "
         "lunes de inicio (RN-08). Mejora: una dim_date con mes, año y temporada.",
         "SELECT week_start, AVG(price) FROM weekly_price GROUP BY week_start",
         f"{week_count} semanas · {format_iso_date(first_week)} a "
         f"{format_iso_date(last_week)}"),
    ]
    for table in project.DIMENSION_TABLES:
        key = table.replace("dim_", "") + "_id"
        panels.append((table, f"{table} · dimensión", definitions[table].capitalize() + ".",
                       f"weekly_price JOIN {table} USING ({key})",
                       f"{charts.format_thousands(row_counts[table])} filas"))
    return panels


def show_star_schema_tab(mode):
    """The star model drawn as a star, its explanation panel and the table list."""
    row_counts = count_cached_table_rows(get_database_version())
    definitions = project.parse_definitions(project.read_section(
        project.read_document(project.PROJECT_GUIDE_FILE), "Modelo de datos"))
    columns = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
    note = (f"Aparte, fuera de la estrella: <strong>etl_run</strong> → "
            f"<strong>rejection</strong> (auditoría de cada carga · "
            f"{charts.format_thousands(row_counts['etl_run'])} y "
            f"{charts.format_thousands(row_counts['rejection'])} filas).")
    with open_card("model_diagram", "Modelo estrella",
                   hint="**Siglas**: PK, clave primaria (identifica cada fila); FK, clave "
                        "foránea (apunta a la clave de otra tabla); JOIN, unión de dos tablas "
                        "por su clave. Pasa el mouse sobre una tabla, o tócala en el celular, "
                        "para ver qué "
                        "guarda y cómo se une a weekly_price."):
        st.markdown(star_model.build_star_model_html(
            columns, row_counts, list_star_panels(row_counts, definitions), note, mode),
            unsafe_allow_html=True)
    with open_card("model_tables", "Tablas de datos.db"):
        st.markdown(build_html_table(
            ["Tabla", "Filas", "Qué guarda"],
            [[f"<code>{table}</code>", charts.format_thousands(row_counts[table]),
              html.escape(definitions[table])] for table in project.TABLE_NAMES]),
            unsafe_allow_html=True)
        st.markdown(build_link_html("Ver etl/schema.sql en Código Python y SQL →",
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


def build_kpi_card_html(indicator, guide_row):
    """One indicator in a card: what it says in words, its formula and where to see it."""
    return build_info_card_html(indicator["Indicador"], guide_row["En palabras"],
                                label=indicator["ID"],
                                note=f"Fórmula: {indicator['Fórmula']}",
                                link=build_place_link(guide_row["Página"]))


def show_kpi_details(indicator, guide_row, question, example_steps, is_requested):
    """A real example and a link to the canonical SQL, without copying the query."""
    kpi = indicator["ID"]
    with st.expander(f"Ver detalles de {kpi}: ejemplo real y consulta SQL",
                     expanded=True):
        if is_requested:
            st.markdown(build_chip("Llegaste desde un gráfico del panel", "running"),
                        unsafe_allow_html=True)
        st.markdown(f"**Pregunta que responde:** {question}")
        if example_steps:
            st.markdown("**Ejemplo real, calculado con la base actual:**  \n"
                        + build_steps_html(example_steps), unsafe_allow_html=True)
        query_name = guide_row["Consulta"]
        st.markdown(build_link_html(f"Ver la consulta {query_name} explicada →",
                                    build_query_address(query_name)), unsafe_allow_html=True)


def show_kpi_tab(mode):
    """K1 to K8: the eight cards first, then details open by default.

    The indicator asked for from a chart goes first, with its details open.
    """
    show_section_intro("KPI y cálculos", "Las ocho cifras del panel: qué dice cada una, su "
                       "fórmula y dónde se ve. En los detalles, un ejemplo real calculado con "
                       "la base actual y su consulta SQL.")
    questions = {row["#"]: row["Pregunta"]
                 for row in project.read_design_table(project.QUESTIONS_HEADING)}
    guide_rows = {row["KPI"]: row for row in project.read_guide_table("KPI")}
    indicators = project.read_design_table(project.INDICATORS_HEADING)
    requested_kpi = st.query_params.get(KPI_PARAMETER)
    indicators.sort(key=lambda indicator: indicator["ID"] != requested_kpi)
    show_info_cards([build_kpi_card_html(indicator, guide_rows[indicator["ID"]])
                     for indicator in indicators])
    show_section_intro("Cómo se calcula cada una", "Cada indicador muestra su ejemplo "
                       "paso a paso y el enlace a la consulta que lo produce.", True)
    examples = build_cached_kpi_examples(get_database_version())
    for indicator in indicators:
        question = questions.get(indicator["Pregunta"], "¿La carga de datos es confiable?")
        show_kpi_details(indicator, guide_rows[indicator["ID"]], question,
                         examples[indicator["ID"]], indicator["ID"] == requested_kpi)


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
    with st.expander("Ver detalles: regla completa, por qué y dónde ocurre", expanded=True):
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
        with st.expander(heading, expanded=True):
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
    section = project.read_section(manual, "Tareas de la autora y tareas automáticas")
    automatic_label, automatic_text = split_bold_label(project.read_paragraphs(section)[0])
    show_section_intro("Qué hace la autora", "Lo automático no necesita a nadie; estas "
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
        with st.expander(f"Ver detalles: {heading[0].lower() + heading[1:]}", expanded=True):
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
        with st.expander(f"Ver detalles: {heading.lower()}", expanded=True):
            st.markdown(project.read_section(manual, heading).replace("### ", "#### "))
    # The terms of the manual live once, in the glossary of Inicio.
    st.markdown(f'<div class="info-note">Las siglas y los términos están en '
                f'{build_place_link(TAB_GLOSSARY, "")}.</div>', unsafe_allow_html=True)


def show_manual_tab(mode):
    """docs/MANUAL.md for whoever operates the project: the weekly run first, then the
    tasks, failures and limits; the rest folded (D-057)."""
    manual = project.read_document(project.MANUAL_FILE)
    show_section_intro("Cómo funciona", "Qué pasa solo cada martes, qué revisar y qué hacer si "
                       "algo falla. Para quien opera el proyecto sin ser técnico.")
    for show_part in [show_weekly_run, show_owner_tasks, show_failures, show_known_limits,
                      show_manual_details]:
        show_part(manual)
    show_section_intro("Recorrido del proyecto", "Cómo entrar y recorrer las páginas.", True)
    st.markdown(project.read_section(manual, "Recorrido del proyecto"))


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
    """The key decisions first, by theme; every other one folded, newest first (D-057)."""
    decisions = dict(project.list_decisions())
    by_number = {split_decision_title(title)[0]: title for title in decisions}
    show_section_intro("Decisiones y método", f"{len(decisions)} decisiones registradas, cada "
                       "una con qué se decidió, por qué, qué se descartó y qué se pierde. "
                       "Primero, las que muestran los compromisos de ingeniería de datos.")
    for theme, lead, numbers in KEY_DECISIONS:
        show_section_intro(theme, lead, True)
        show_info_cards([build_decision_card_html(by_number[number],
                                                  decisions[by_number[number]])
                         for number in numbers])
        with st.expander(f"Ver detalles: {theme.lower()}", expanded=True):
            for number in numbers:
                st.markdown(f"**{by_number[number]}**")
                st.markdown(decisions[by_number[number]])
    key_numbers = {number for _, _, numbers in KEY_DECISIONS for number in numbers}
    others = sorted((number for number in by_number if number not in key_numbers),
                    key=lambda number: int(number[2:]), reverse=True)
    show_section_intro("Las demás decisiones", f"{len(others)} decisiones, de la más reciente "
                       "a la más antigua.", True)
    for number in others:
        with st.expander(by_number[number], expanded=True):
            st.markdown(decisions[by_number[number]])


def show_query_result_button(key, sql, parameters=()):
    """Button that runs a query on the read-only database and shows 20 rows."""
    if st.button("Ver resultado", key=f"preview_{key}", icon=":material/play_arrow:"):
        st.dataframe(project.run_preview(sql, parameters), hide_index=True,
                     use_container_width=True)
        st.caption(f"Primeras {project.PREVIEW_ROW_COUNT} filas como máximo, en solo lectura.")


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


def show_query_block(query, origin=None, parameters=()):
    """One query, open by default: its clauses, where it is used, the SQL in sight
    (Python beside it when it exists) and its first 20 rows."""
    with st.expander(f"{query['name']} · {query['question']}", expanded=True):
        origin_text = f" · vive en <code>{html.escape(origin)}</code>" if origin else ""
        st.markdown(f'<div class="query-meta">{build_clause_chips(query)}</div>'
                    f'<div class="query-meta">Se usa en: {build_place_link(query["page"], "")}'
                    f'{origin_text}</div>', unsafe_allow_html=True)
        st.code(query["sql"], language="sql")
        if query["python"]:
            functions = project.PYTHON_VERSIONS[query["name"]]
            files = sorted({function.__module__.replace(".", "/") + ".py" for function in functions})
            st.caption("Reconciliación verificada por test con " + ", ".join(files) + ".")
            st.markdown(build_link_html("Ver la implementación Python en su archivo →",
                                        build_page_address(PAGE_CODE)), unsafe_allow_html=True)
        if parameters:
            st.caption(f"Valores de cada «?», enviados aparte del texto: {list(parameters)}")
        show_query_result_button(query["name"], query["sql"], parameters)


def build_extra_queries():
    """Queries that live outside bi/queries.sql: K7 (etl/etl.py) and a Consultas example."""
    explorer_sql, explorer_parameters = project.build_explorer_example()
    match_coverage = {"name": project.MATCH_COVERAGE_QUERY_NAME,
                      "sql": etl.MATCH_COVERAGE_QUERY.strip(),
                      "question": "¿Cuántas claves de producto tienen margen?",
                      "page": TAB_QUALITY, "python": [],
                      **project.describe_query(etl.MATCH_COVERAGE_QUERY)}
    explorer_example = {"name": "explorer_example", "sql": explorer_sql,
                        "question": "Ejemplo generado por Consulta por clics: precios del "
                                    "tomate en la Región Metropolitana, cinco semanas.",
                        "page": TAB_EXPLORER, "python": [],
                        **project.describe_query(explorer_sql)}
    return [(match_coverage, "etl/etl.py", ()),
            (explorer_example, "bi/explorer.py", explorer_parameters)]


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
    """The files of the README tree, one card per folder, in the order of the data."""
    files = [(path, description, address) for path, description, address
             in project.list_repository_files()
             if not any(path == folder for folder, _, _ in FOLDER_PURPOSES if folder)]
    cards = []
    for folder, title, purpose in FOLDER_PURPOSES:
        entries = [entry for entry in files if find_folder(entry[0]) == folder]
        # A folder the README lists by the names of its files («semanal.yml, pruebas.yml»).
        folder_line = next((description for path, description, _ in
                            project.list_repository_files() if path == folder), "")
        if folder and re.fullmatch(r"[\w.-]+\.\w+(, [\w.-]+\.\w+)*", folder_line):
            entries += [(folder + name, "", project.build_github_url(folder + name))
                        for name in folder_line.split(", ")]
        lines = "".join(build_file_line_html(*entry) for entry in entries)
        link = (build_link_html(f"Abrir {folder} en GitHub", project.build_github_url(folder))
                if folder and not lines else None)
        cards.append(build_info_card_html(
            title, purpose, link=link,
            body_html=f'<ul class="file-list">{lines}</ul>' if lines else ""))
    show_info_cards(cards, is_compact=True)
    st.markdown(f'<div class="info-note">Los enlaces al historial de commits y a las '
                f'ejecuciones están en {build_place_link(PAGE_LINKS, "la página")}.</div>',
                unsafe_allow_html=True)


def describe_query_part(place):
    """The part of the project a query belongs to: «Análisis › Brecha de precio»."""
    page = PAGE_OF_TAB.get(place)
    return f"{page} › {place}" if page and page != place else place


def group_queries_by_part(catalog):
    """{part of the project: its queries}, in the order of the menu and its tabs."""
    order = [tab for page in PAGES for tab in [page] + TABS_BY_PAGE[page]]
    parts = {}
    for query in sorted(catalog, key=lambda query: order.index(query["page"])
                        if query["page"] in order else len(order)):
        parts.setdefault(describe_query_part(query["page"]), []).append(query)
    return parts


def build_query_address(name):
    address = build_page_address(PAGE_QUERIES)
    return address + ("&" if "?" in address else "?") + urlencode({"consulta": name})


def show_queries_tab(mode):
    """The bank of SQL queries of the project, by the part that uses them, top to
    bottom; each one open, with its SQL in sight (T-57, D-060)."""
    named_queries = project.list_named_queries()
    show_section_intro("Queries", f"Las {len(named_queries)} queries con nombre de "
                       "`bi/queries.sql`, contadas al abrir la página, ordenadas por la parte "
                       "del panel que las usa, y dos que viven fuera. Cada una con su pregunta, "
                       "su SQL y su resultado.")
    st.markdown(f"### {len(named_queries)} queries del proyecto")
    requested = st.query_params.get("consulta")
    extras = build_extra_queries()
    requested_extra = next((entry for entry in extras if entry[0]["name"] == requested), None)
    if requested_extra:
        show_query_block(*requested_extra)
    parts = list(group_queries_by_part(named_queries).items())
    parts.sort(key=lambda item: not any(query["name"] == requested for query in item[1]))
    for part, part_queries in parts:
        st.markdown(f"#### {part} · {len(part_queries)}")
        for query in sorted(part_queries, key=lambda query: query["name"] != requested):
            show_query_block(query)
    st.markdown("#### Fuera de bi/queries.sql")
    for query, origin, parameters in extras:
        if query["name"] != requested or not requested_extra:
            show_query_block(query, origin, parameters)
    st.markdown(build_link_html("Ver los esquemas de creación de tablas en Código Python y SQL →",
                                build_page_address(PAGE_CODE)), unsafe_allow_html=True)


def show_files_tab(mode):
    """An open file tree: source and explanation together, in pipeline order."""
    show_section_intro("Python · del origen al dashboard", "Los archivos se leen en el orden "
                       "del flujo de datos. Cada acordeón está abierto: puedes plegar un "
                       "archivo o una carpeta para concentrarte en lo que te interesa.")
    catalog = project.list_code_walkthrough()
    for folder in dict.fromkeys(entry["folder"] for entry in catalog):
        with st.expander(f"📂 {folder}/", expanded=True):
            for entry in [entry for entry in catalog if entry["folder"] == folder]:
                with st.expander(f"{entry['number']:02} · {entry['path']} — {entry['title']}",
                                 expanded=True):
                    st.write(entry["purpose"])
                    st.caption(f"Entrada: {entry['input']} → Salida: {entry['output']}")
                    st.info(f"Problema que resuelve: {entry['challenge']}", icon=":material/lightbulb:")
                    st.code(entry["source"], language="python", line_numbers=True, height=420)
    show_section_intro("SQL · estructura y preguntas", "Primero las tablas que reciben los "
                       "datos; luego cada consulta con su propósito, cláusulas y resultado.")
    for path, title in [("etl/raw_schema.sql", "Capa bronce: conservar el archivo original"),
                        ("etl/schema.sql", "Modelo estrella: precios, dimensiones y auditoría")]:
        with st.expander(f"{path} — {title}", expanded=True):
            st.code(project.read_document(project.PROJECT_DIR / path), language="sql",
                    line_numbers=True, height=420)
    st.markdown(build_link_html("Continuar con las queries SQL explicadas →",
                                build_page_address(PAGE_QUERIES)),
                unsafe_allow_html=True)
    with st.expander("📂 Otros archivos del repositorio", expanded=True):
        show_repository_files()


def show_idea_tab(mode):
    """Business definition, scope and acceptance criteria, read from the project brief."""
    brief = project.read_guide_table("Marco de negocio")
    for row in brief:
        st.markdown(build_info_card_html(row["Elemento"], row["Definición"],
            component=row["Forma"]), unsafe_allow_html=True)
    show_section_intro("Entregables", "Resultados verificables del proyecto.", True)
    st.markdown(build_place_link(PAGE_HOME, "Dashboard:") + " · "
                + build_place_link(PAGE_DATA_AND_CODE, "Datos:") + " · "
                + build_place_link(PAGE_CODE, "Implementación:") + " · "
                + build_place_link(PAGE_RUNS, "Operación:"), unsafe_allow_html=True)
    for show_part in [show_questions, show_audience, show_sources, show_limits, show_why]:
        show_part(mode)


def show_glossary_tab(mode):
    """Acronyms and terms of the project in plain words, grouped by theme (T-46b, D-057)."""
    rows = project.read_guide_table("Glosario")
    show_section_intro("Glosario", f"{len(rows)} siglas y términos que aparecen en el panel, "
                       "en palabras simples y agrupados por tema.")
    themes = list(dict.fromkeys(row["Tema"] for row in rows))
    for theme in themes:
        show_section_intro(theme, GLOSSARY_THEME_LEADS.get(theme, ""), True)
        show_info_cards([build_info_card_html(row["Sigla o término"], row["Significado"],
                                              note=f"Aparece en: {row['Dónde aparece']}")
                         for row in rows if row["Tema"] == theme])


@st.cache_data
def read_cached_latest_gaps(database_version):
    """Latest-week matched prices, ranked in SQLite before reaching the UI."""
    sql = ("SELECT * FROM (" + queries.read_query_body("k1_margin") + ") "
           "WHERE week_start = (SELECT MAX(week_start) FROM weekly_price) "
           "ORDER BY margin DESC LIMIT 50")
    return add_display_columns(queries.run_sql(sql))


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
        show_chart(chart)
    st.markdown(build_mobile_ranking_html(rows, mode, is_variation), unsafe_allow_html=True)


@st.cache_data
def read_cached_market_snapshot(database_version):
    """The canonical K3 query, restricted to the latest week of valid observations."""
    sql = ("SELECT * FROM (" + queries.read_query_body("k3_regional_index") + ") "
           "WHERE week_start = (SELECT MAX(week_start) FROM weekly_price)")
    return add_display_columns(queries.run_sql(sql))


def show_market_visuals(mode, prefix, latest_week):
    """Complementary questions use a donut, an area timeline and a true 3D view."""
    snapshot = read_cached_market_snapshot(get_database_version())
    if snapshot.empty:
        st.info("No hay observaciones válidas en la última semana para el panorama.")
        return
    coverage = snapshot.groupby(queries.KEY_COLUMNS).size().reset_index(name="row_count")
    coverage = coverage.sort_values(["row_count"] + queries.KEY_COLUMNS,
                                    ascending=[False] + [True] * len(queries.KEY_COLUMNS))
    keys = [tuple(row[column] for column in queries.KEY_COLUMNS)
            for row in coverage.to_dict("records")]
    selected = st.selectbox("Producto comparable · tendencia y vista territorial", keys,
        format_func=lambda values: f"{values[0]} · " + describe_product(dict(zip(queries.KEY_COLUMNS, values)))
                                  + f" · $/{values[-1]}",
        key=f"{prefix}_visual_product",
        help="Se muestra automáticamente la combinación con más observaciones de esta semana. "
             "La comparación conserva producto, variedad, calidad y unidad.")
    key = dict(zip(queries.KEY_COLUMNS, selected))
    points = snapshot.loc[(snapshot[queries.KEY_COLUMNS] == pd.Series(key)).all(axis=1)]
    history = read_indicator_for_key("k6_national_weekly_price", key)
    history = history[history["week_start"].between(latest_week - pd.Timedelta(weeks=11), latest_week)]
    revision = "|".join(selected)
    config = {"displaylogo": False, "scrollZoom": False, "responsive": True}
    left, right = st.columns([1, 1.5])
    with left, open_card(f"{prefix}_group_share", "Composición de los datos de esta semana",
        hint="El anillo reparte el número de observaciones válidas por grupo de alimentos. "
             "El centro es el total de la semana. No representa gasto, ventas ni cuota de mercado."):
        st.plotly_chart(market_charts.draw_group_share(snapshot, mode), theme=None,
                        use_container_width=True, config=config, key=f"{prefix}_groups_plot")
        st.caption("Observaciones válidas por grupo · última semana · sin sumar precios.")
    with right, open_card(f"{prefix}_price_trend", "Pulso de precios · últimas 12 semanas",
        hint="Cada curva es un canal para el producto, variedad, calidad y unidad seleccionados. "
             "El precio nacional es el promedio simple de las regiones con dato. "
             "Las semanas sin dato quedan interrumpidas; las áreas no se suman."):
        st.plotly_chart(market_charts.draw_price_trend(history, mode, revision), theme=None,
                        use_container_width=True, config=config, key=f"{prefix}_trend_plot")
        st.caption("Pasa el mouse para ver precios; pulsa una leyenda para ocultar o mostrar un canal.")
    with open_card(f"{prefix}_regional_3d", "Territorio de precios · región × canal",
        hint="Tres ejes reales: región, canal e índice de precio regional. "
             "100 es el promedio nacional del mismo canal, producto y unidad; 120 significa "
             "20 % más caro. La altura indica el índice, no el volumen de ventas. "
             "Gira la vista arrastrando; pasa el mouse sobre un punto para ver los precios.", kpi="K3"):
        view = st.segmented_control("Representación territorial", ["3D interactivo", "Mapa 2D"],
            default="3D interactivo", key=f"{prefix}_territorial_view") or "3D interactivo"
        figure = (market_charts.draw_regional_3d(points, mode, revision) if view == "3D interactivo"
                  else market_charts.draw_regional_heatmap(points, mode, revision))
        st.plotly_chart(figure, theme=None, use_container_width=True,
                        config=config, key=f"{prefix}_territory_plot")
        st.caption("Índice 100 = promedio nacional de cada canal · misma semana, variedad, calidad y unidad. "
                   "Arrastra para girar en 3D; usa Mapa 2D si prefieres una lectura plana o tu equipo no admite 3D.")


def show_market_overview(mode, prefix):
    """Useful charts on arrival, with ranking controls above the charts."""
    latest_week = read_latest_week()
    variations = read_cached_latest_variations(get_database_version())
    all_alerts = read_price_alerts()
    week_alerts = all_alerts[all_alerts["week_start"] == latest_week]
    total = read_indicator("quality_flag_counts")["weekly_prices"].sum()
    values = [("Precios semanales", charts.format_thousands(total), "database", "Historial disponible"),
              ("Semana observada", f"{latest_week:%d-%m-%Y}", "document", "Última semana con datos"),
              ("Series con variación", charts.format_thousands(len(variations)), "chart", "Comparación semanal nacional"),
              ("Alertas de esta semana", str(len(week_alerts)), "alert", "Cambios fuera del rango habitual")]
    cells = "".join(f'<div><div class="market-metric-heading">{build_component_symbol(kind)}'
                    f'<span class="kpi-label">{label}</span></div>'
                    f'<div class="kpi-value">{value}</div>'
                    f'<div class="market-metric-note">{note}</div></div>'
                    for label, value, kind, note in values)
    st.markdown(f'<div class="overview-metrics">{cells}</div>', unsafe_allow_html=True)
    if prefix == "home":
        profile = st.session_state.get(PROFILE_PARAMETER)
        if profile in VISITOR_PROFILES:
            st.caption(VISITOR_PROFILES[profile])
    show_section_intro("01 · Lo que dicen los datos", "Última semana disponible · todos los grupos de productos · "
                       "pasa el mouse sobre una barra para ver su detalle.")
    with st.expander("Ajustar el ranking · Top N, alzas y bajas", expanded=True):
        count_column, direction_column = st.columns([1, 2])
        with count_column:
            count = st.select_slider("Top N · cantidad de resultados", [5, 10, 15, 20], value=10,
                                     key=f"{prefix}_top_n")
        with direction_column:
            direction = st.segmented_control("Orden del ranking",
                ["Mayores movimientos", "Alzas", "Bajas"], default="Mayores movimientos",
                key=f"{prefix}_ranking_direction") or "Mayores movimientos"
    show_section_intro("Movimientos y brechas · ranking detallado",
                       "Top N de la última semana, con el orden elegido arriba.", True)
    ranked = rank_weekly_movements(variations, count, direction)
    left, right = st.columns(2)
    with left, open_card(f"{prefix}_movements", f"Top {count} · cambios de precio",
        hint="Compara el precio nacional con la semana anterior, para cada producto y canal. "
             "Rojo y ▲: alza; azul y ▼: baja. La longitud de la barra mide el cambio en %. "
             "Top N significa los primeros N resultados del ranking.", kpi="K6"):
        if ranked.empty:
            st.info("No hay cambios disponibles para este orden en la última semana.")
        else:
            labels = [f"{describe_product(row)} · {row['channel']} · $/{row['normalized_unit']}"
                      for row in ranked.to_dict("records")]
            bars = pd.DataFrame({"label": labels, "value": ranked["variation"].to_numpy() * 100})
            show_ranking_chart(bars, mode, f"{prefix}_movements", is_variation=True)
            st.caption("Precio nacional: promedio simple de las regiones con dato. "
                       "Cada fila identifica producto, canal y unidad.")
    gaps = read_cached_latest_gaps(get_database_version()).head(count)
    with right, open_card(f"{prefix}_gaps", f"Top {count} · brechas consumidor / mayorista",
        hint="Ordena las mayores brechas de precio de la misma semana, producto, unidad y "
             "región. Brecha = (consumidor / mayorista − 1) × 100. Un 50 % significa que "
             "el consumidor paga 1,5 veces el mayorista. No mide utilidad ni costo del comercio.",
        kpi="K1"):
        if gaps.empty:
            st.info("No hay pares comparables en la última semana.")
        else:
            bars = pd.DataFrame({
                "label": [f"{describe_product(row)} · {row['channel']} · "
                          f"{charts.shorten_region_name(row['region'])} · $/{row['normalized_unit']}"
                          for row in gaps.to_dict("records")],
                "value": gaps["margin"].to_numpy() * 100})
            bars["value_label"] = bars["value"].map(charts.format_percent)
            show_ranking_chart(bars, mode, f"{prefix}_gaps")
            st.caption("Frutas y hortalizas con precio mayorista comparable. "
                       "Cada fila conserva la región; no se mezclan precios de distintas unidades.")
    show_section_intro("Explorar el mercado", "Después del Top N: composición de los datos, "
                       "tendencia del producto elegido y comparación territorial.", True)
    show_market_visuals(mode, prefix, latest_week)
    with st.expander("Ver y descargar los datos del ranking", expanded=True):
        detail = ranked[["product_group", "product", "variety", "quality", "channel",
                         "normalized_unit", "week_start", "national_price", "variation"]].copy()
        detail["variation"] *= 100
        detail = detail.rename(columns={"product_group": "Grupo", "product": "Producto",
            "variety": "Variedad", "quality": "Calidad", "channel": "Canal",
            "normalized_unit": "Unidad", "week_start": "Semana", "national_price": "Precio nacional",
            "variation": "Variación %"})
        st.dataframe(detail, hide_index=True, use_container_width=True)
        st.download_button("Descargar ranking CSV", detail.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"ranking-{latest_week:%Y-%m-%d}.csv", mime="text/csv",
                           key=f"{prefix}_download")
    st.caption(NOMINAL_PRICES_TEXT)


def show_home_page(mode):
    """Market dashboard with latest-week rankings; diagrams have their own destination."""
    st.markdown(f"<style>{market_style.build_css(mode)}</style>", unsafe_allow_html=True)
    with st.container(key="market_dashboard"):
        with st.container(key="market_intro"):
            st.markdown('<p class="market-eyebrow">Inteligencia de mercado · ODEPA</p>',
                        unsafe_allow_html=True)
            show_page_header("Precios de alimentos · Chile", "Observa cómo cambian los precios "
                             "y dónde se amplía la brecha entre mayorista y consumidor.")
        show_market_overview(mode, "home")


def show_diagrams_page(mode):
    show_page_header(PAGE_DIAGRAMS, "Cómo viajan los datos desde ODEPA hasta los indicadores "
                     "y en qué plataformas corre cada componente.")
    animate_flow = st.toggle("Animar el recorrido de los datos", value=True, key="animate_data_flow")
    st.caption("El movimiento ilustra el recorrido de los datos. Los puntos y el estado "
               "de ejecución muestran la última respuesta disponible del pipeline.")
    show_pipeline_tab(mode, animate_flow)
    show_section_intro("Arquitectura por plataforma", "Cada plataforma contiene los "
                       "componentes que ejecuta y sus conexiones.")
    show_infrastructure_diagram(mode, animate_flow)
    st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)


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
        show_chart(charts.draw_single_weekly_area(
            line_rows, "Brecha (%)", line_rows["value"].map(charts.format_percent), mode,
            reference_value=0))


def show_gap_tab(mode, filters):
    """K1 as a dumbbell for this week and one line per channel for its evolution, then
    K5; the whole history folded (D-059)."""
    st.caption("Brecha = (precio al consumidor − precio mayorista) / precio mayorista, con la "
               "misma variedad, calidad, región, semana y unidad.")
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
    show_lag_card(rows, mode)
    with st.expander("Ver evolución histórica", expanded=True):
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
        show_chart(charts.draw_horizontal_bars(bar_rows, "Diferencia promedio (%)", mode,
                                               colors, reference_value=0,
                                               reference_label=reference_channel))
        st.caption(f"Cuánto más caro (+) o más barato (−) es cada canal que "
                   f"«{reference_channel}», en las semanas y regiones donde ambos tienen precio.  \n"
                   f"Base de cada barra: {' · '.join(describe_gap_basis(rows))}.")
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
def build_month_rows(rows):
    """Average seasonal index of each month of each year (rows of one channel)."""
    months = rows.assign(year=rows["week_start"].dt.year, month=rows["week_start"].dt.month)
    months = months.groupby(["year", "month"], as_index=False)["seasonal_index"].mean()
    months = months.rename(columns={"seasonal_index": "value"})
    months["value_label"] = months["value"].map(charts.format_index)
    return months


def show_seasonality_history(rows, mode):
    """The weekly index and national price, folded: one line per channel."""
    with st.expander("Ver evolución histórica", expanded=True):
        index_column, price_column = st.columns(2)
        with index_column, open_card("seasonal_index", "Índice estacional por semana",
                                     "1 = precio promedio del año.", hint=SEASONAL_INDEX_HINT,
                                     kpi="K4"):
            index_rows = rows[["week_start", "channel", "seasonal_index"]].rename(
                columns={"seasonal_index": "value"})
            show_chart(charts.draw_weekly_lines(
                index_rows, "Índice", index_rows["value"].map(charts.format_index), mode,
                is_money=False))
        with price_column, open_card("national_price", "Precio nacional por semana",
                                     hint=NATIONAL_PRICE_HINT, kpi="K4"):
            price_rows = rows[["week_start", "channel", "national_price"]].rename(
                columns={"national_price": "value"})
            show_chart(charts.draw_weekly_lines(
                price_rows, f"$/{rows['normalized_unit'].iloc[0]}",
                "$ " + price_rows["value"].map(charts.format_thousands), mode, is_money=True))


def show_seasonality_tab(mode, filters):
    """K4 as a calendar of months and years, one per channel; the weekly lines folded
    (D-059)."""
    st.caption("Índice = precio nacional de la semana / promedio del año. Con varios años se "
               "ve qué meses son caros o baratos cada año.")
    rows = read_indicator_for_key("k4_seasonal_index", filters["key"])
    rows = rows[rows["channel"].isin(filters["channels"])]
    if rows.empty:
        st.info(NO_DATA_TEXT)
        return
    for channel in [channel for channel in filters["channels"] if channel in set(rows["channel"])]:
        with open_card(f"seasonal_calendar_{channel}", f"Calendario de precios · {channel}",
                       "Más oscuro = más caro ese mes.", hint=HEATMAP_HINT, kpi="K4"):
            show_chart(charts.draw_heatmap(build_month_rows(rows[rows["channel"] == channel]),
                                           mode))
    show_seasonality_history(rows, mode)
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
    st.caption("Hay alerta cuando el cambio semanal del precio se aleja más de 2 desviaciones "
               "estándar de lo habitual en las 12 semanas previas. Muestra todos los productos.")
    alert_rows = read_price_alerts()
    if alert_rows.empty:
        st.info("Todavía no hay semanas suficientes para calcular alertas.")
        return
    weeks = sorted(alert_rows["week_start"].dt.date.unique(), reverse=True)
    week = st.selectbox("Semana (lunes de inicio)", weeks,
                        format_func=lambda day: day.strftime("%d-%m-%Y"))
    week_rows = alert_rows[alert_rows["week_start"].dt.date == week]
    distance = ((week_rows["variation"] - week_rows["usual_variation"]).abs()
                / week_rows["variation_deviation"])
    shown_rows = week_rows.loc[distance.sort_values(ascending=False).index]
    with open_card("alert_list", f"Alertas de la semana ({len(week_rows)})",
                   "De la más lejana a su rango habitual a la más cercana.",
                   hint=ALERT_LIST_HINT, kpi="K6"):
        st.markdown(build_alert_list_html(shown_rows.head(ALERTS_PAGE_BAR_COUNT), mode),
                    unsafe_allow_html=True)
        if len(shown_rows) > ALERTS_PAGE_BAR_COUNT:
            st.caption(f"Se muestran las {ALERTS_PAGE_BAR_COUNT} más lejanas; todas están en "
                       "la tabla de abajo.")
    with st.expander("Ver todas las alertas de la semana en tabla", expanded=True):
        st.dataframe(format_alerts(week_rows), hide_index=True, use_container_width=True)
    st.caption(NOMINAL_PRICES_TEXT)


def show_analysis_view(mode, title, renderer):
    show_page_header(title, "Análisis de precios oficiales de ODEPA, con unidades y "
                     "series comparables.")
    st.markdown(build_link_html("Ver el panorama general en Dashboard →",
                                build_page_address(PAGE_HOME)), unsafe_allow_html=True)
    if renderer is show_alerts_tab:
        renderer(mode, None)
    else:
        filters = choose_analysis_filters()
        renderer(mode, filters)


def show_analysis_page(mode):
    show_analysis_view(mode, PAGE_ANALYSIS, show_week_tab)


# endregion


# region Consulta por clics
@st.cache_data
def read_cached_search_options(database_version):
    """The values of each field of the form, read once per database."""
    return explorer.read_search_options()


@st.cache_data
def read_cached_alert_states(database_version):
    """The K6 state of every national series and week, computed once per database."""
    return explorer.build_alert_states(queries.run_query("k6_national_weekly_price"))


@st.cache_data
def read_cached_search(filter_items, database_version):
    """The rows of one search with their alert state, kept until the database changes."""
    filters = dict(filter_items)
    rows = explorer.read_search_rows(filters)
    rows = explorer.add_alert_states(rows, read_cached_alert_states(database_version))
    return rows


def build_default_search(options):
    """The search the tab opens with: everything, in the latest week."""
    filters = {field: explorer.ALL for field in explorer.LIST_FIELD_COLUMNS}
    filters.update({explorer.FIELD_FIRST_WEEK: options["weeks"][0],
                    explorer.FIELD_LAST_WEEK: options["weeks"][0],
                    explorer.FIELD_ALERT: explorer.ALL})
    return filters


def read_applied_search(options):
    """The search applied last (the default one the first time)."""
    if SEARCH_APPLIED not in st.session_state:
        st.session_state[SEARCH_APPLIED] = build_default_search(options)
    return st.session_state[SEARCH_APPLIED]


def set_search_value(field, value):
    """Apply one value now and show it in its field of the form (used by callbacks,
    which run before the widgets are drawn)."""
    st.session_state[SEARCH_APPLIED][field] = value
    st.session_state[f"search_{field}"] = value
    st.session_state[SEARCH_PAGE] = 1


def apply_search():
    """«Buscar»: the form becomes the applied search."""
    st.session_state[SEARCH_APPLIED] = {field: st.session_state[f"search_{field}"]
                                        for field in explorer.SEARCH_FIELDS}
    st.session_state[SEARCH_PAGE] = 1


def clear_search(options):
    """«Limpiar»: back to the default search, in the form too."""
    st.session_state[SEARCH_APPLIED] = build_default_search(options)
    for field, value in st.session_state[SEARCH_APPLIED].items():
        st.session_state[f"search_{field}"] = value
    st.session_state[SEARCH_PAGE] = 1


def list_field_options(field, options, applied):
    """Options of one list field; product, variety and quality follow the group, product
    and variety applied, so they only offer what exists."""
    if field not in (explorer.FIELD_PRODUCT, explorer.FIELD_VARIETY, explorer.FIELD_QUALITY):
        return [explorer.ALL] + options[field]
    products = options["products"]
    for parent in [explorer.FIELD_GROUP, explorer.FIELD_PRODUCT, explorer.FIELD_VARIETY]:
        if parent == field:
            break
        column = explorer.LIST_FIELD_COLUMNS[parent][1]
        if applied[parent] != explorer.ALL:
            products = products[products[column] == applied[parent]]
    column = explorer.LIST_FIELD_COLUMNS[field][1]
    return [explorer.ALL] + sorted(products[column].unique())


def format_search_value(field, value):
    """How a value reads in the form and in the chips."""
    if field in (explorer.FIELD_FIRST_WEEK, explorer.FIELD_LAST_WEEK):
        return f"{pd.Timestamp(value):%d-%m-%Y}"
    if field == explorer.FIELD_SOURCE:
        return explorer.SOURCE_NAMES.get(value, value)
    return str(value)


def show_search_field(field, column, options, applied):
    """One field of the form, with the applied value chosen."""
    if field in (explorer.FIELD_FIRST_WEEK, explorer.FIELD_LAST_WEEK):
        choices = options["weeks"]
    elif field == explorer.FIELD_ALERT:
        choices = [explorer.ALL] + explorer.ALERT_STATES
    else:
        choices = list_field_options(field, options, applied)
    key = f"search_{field}"
    if st.session_state.get(key, applied[field]) not in choices:
        st.session_state[key] = explorer.ALL if explorer.ALL in choices else choices[0]
    elif key not in st.session_state:
        st.session_state[key] = applied[field]
    column.selectbox(explorer.FIELD_LABELS[field], choices, key=key,
                     format_func=lambda value: format_search_value(field, value))


def show_search_form(options, applied):
    """The form, in a card: fields in rows of four, «Limpiar» and «Buscar»."""
    with open_card("search_form", "Buscar precios semanales"):
        with st.form("search_form", border=False):
            fields = explorer.SEARCH_FIELDS
            for start in range(0, len(fields), 4):
                columns = st.columns(4)
                for column, field in zip(columns, fields[start:start + 4]):
                    show_search_field(field, column, options, applied)
            clear_column, search_column, _ = st.columns([1, 1, 4])
            clear_column.form_submit_button("Limpiar", on_click=clear_search, args=(options,),
                                            use_container_width=True)
            search_column.form_submit_button("Buscar", type="primary", on_click=apply_search,
                                             icon=":material/search:", use_container_width=True)


def show_active_filters(options, applied):
    """The filters in use as chips; ✕ removes one."""
    default = build_default_search(options)
    active = [field for field in explorer.SEARCH_FIELDS if applied[field] != default[field]]
    if not active:
        return
    with st.container(key="search_chips", horizontal=True):
        for field in active:
            st.button(f"{explorer.FIELD_LABELS[field]}: "
                      f"{format_search_value(field, applied[field])} ✕",
                      key=f"chip_{field}", on_click=set_search_value,
                      args=(field, default[field]))


def show_search_summary(rows, applied, mode):
    """Cards by alert state of the latest week, and the breakdown by group; a click
    on a card or a count applies that filter."""
    counts = explorer.summarize_latest_week(rows)
    week = rows["week_start"].max()
    with open_card("search_summary", "Resumen de la última semana", f"Semana del {week:%d-%m-%Y}.",
                   hint=SEARCH_SUMMARY_HINT, kpi="K6"):
        with st.container(key="search_kpis"):
            for column, state in zip(st.columns(4), explorer.ALERT_STATES):
                icon, status = ALERT_STATE_STYLES[state]
                color = charts.get_status_text_color(status, mode)
                with column, st.container(key=f"alert_card_{explorer.ALERT_STATES.index(state)}"):
                    st.markdown(f'<div class="alert-card-label" style="color:{color}">{icon} '
                                f'{html.escape(state)}</div><div class="kpi-value">'
                                f'{charts.format_thousands(counts[state])}</div>',
                                unsafe_allow_html=True)
                    st.button("Ver solo estos", key=f"filter_state_{state}",
                              on_click=set_search_value, args=(explorer.FIELD_ALERT, state),
                              type="tertiary", disabled=applied[explorer.FIELD_ALERT] == state)
        with st.expander("Ver el desglose por grupo", expanded=True):
            groups = explorer.summarize_groups(rows)
            for group, group_counts in groups.iterrows():
                columns = st.columns([2, 1, 1, 1, 1], vertical_alignment="center")
                columns[0].button(group, key=f"filter_group_{group}", type="tertiary",
                                  on_click=set_search_value, args=(explorer.FIELD_GROUP, group))
                for column, state in zip(columns[1:], explorer.ALERT_STATES):
                    icon, _ = ALERT_STATE_STYLES[state]
                    column.button(f"{icon} {charts.format_thousands(group_counts[state])}",
                                  key=f"filter_{group}_{state}", type="tertiary",
                                  help=f"{group} · {state}", on_click=apply_group_and_state,
                                  args=(group, state))


def apply_group_and_state(group, state):
    """A count of the breakdown: its group and its state at once."""
    set_search_value(explorer.FIELD_GROUP, group)
    set_search_value(explorer.FIELD_ALERT, state)


def build_search_table(rows):
    """The rows of one page with readable columns: arrows and colors on the change, and
    the alert as a badge (icon + text, never color alone)."""
    table = rows[list(SEARCH_COLUMNS)].rename(columns=SEARCH_COLUMNS)
    # A missing wholesale price arrives as None: numbers, so «—» can stand for it.
    table["Variación %"] = pd.to_numeric(table["Variación %"], errors="coerce") * 100
    table["Brecha %"] = pd.to_numeric(table["Brecha %"], errors="coerce") * 100
    table["Alerta"] = [f"{ALERT_STATE_STYLES[state][0]} {state}" for state in table["Alerta"]]
    return table


def style_search_table(table, mode):
    """Colors of the change (red up, blue down) and of the alert badge."""
    palette = charts.get_palette(mode)

    def color_change(value):
        if pd.isna(value) or value == 0:
            return ""
        return f"color: {palette['rise'] if value > 0 else palette['fall']}; font-weight: 600"

    def color_alert(text):
        status = next(status for state, (icon, status) in ALERT_STATE_STYLES.items()
                      if text.endswith(state))
        color = charts.get_status_text_color(status, mode)
        return (f"color: {color}; background-color: {color}22; border-radius: 999px; "
                "font-weight: 600")

    def write_change(value):
        if pd.isna(value):
            return "—"
        arrow = "▲" if value > 0 else "▼" if value < 0 else "="
        return f"{arrow} {charts.format_signed_percent(value)}"

    return (table.style
            .format({"Precio": lambda value: f"$ {charts.format_thousands(value)}",
                     "Variación %": write_change,
                     "Brecha %": lambda value: "—" if pd.isna(value)
                     else charts.format_signed_percent(value),
                     "Semana": lambda value: f"{value:%d-%m-%Y}"}, na_rep="—")
            .map(color_change, subset=["Variación %"])
            .map(color_alert, subset=["Alerta"]))


def show_search_table(rows, applied, mode):
    """The results in a card: a page of 20, 50 or 100 rows, CSV and SQL; selecting a row
    returns it."""
    with open_card("search_table", "Resultados", hint=SEARCH_TABLE_HINT):
        size_column, page_column, info_column = st.columns([1, 1, 3],
                                                           vertical_alignment="bottom")
        page_size = size_column.selectbox("Filas por página", PAGE_SIZES, key="search_page_size")
        last_page = max(1, -(-len(rows) // page_size))
        page = page_column.number_input("Página", min_value=1, max_value=last_page, step=1,
                                        key=SEARCH_PAGE)
        shown, first, last, total = explorer.take_page(rows, page_size, page)
        info_column.markdown(f'<div class="search-count">Mostrando {first} a {last} de '
                             f'{charts.format_thousands(total)} resultados</div>',
                             unsafe_allow_html=True)
        event = st.dataframe(style_search_table(build_search_table(shown), mode),
                             hide_index=True, use_container_width=True, key="search_results",
                             # The whole page in sight: a header and one line per row.
                             height=TABLE_ROW_HEIGHT * (len(shown) + 1) + 3,
                             on_select="rerun", selection_mode="single-row",
                             column_config={"Producto": st.column_config.TextColumn(
                                 width="medium", pinned=True)})
        csv_column, sql_column, _ = st.columns([1, 1, 4])
        csv_column.download_button(
            "⤓ CSV", build_search_table(rows).to_csv(index=False).encode("utf-8"),
            file_name="consulta_precios.csv", mime="text/csv", type="tertiary")
        with sql_column.popover("</> Ver SQL"):
            sql, parameters = explorer.build_search_query(applied)
            st.code(sql, language="sql")
            st.caption(f"Valores de cada «?», enviados aparte del texto: {list(parameters)}")
            st.caption("El estado de alerta se agrega después con K6 (`bi/alerts.py`).")
    selected = event.selection.rows
    return shown.iloc[selected[0]] if selected else None


def show_selected_detail(row, mode):
    """The card of the chosen price: its data, then its history, its gap by channel and
    the alerts of its series."""
    icon, status = ALERT_STATE_STYLES[row["alert_state"]]
    color = charts.get_status_text_color(status, mode)
    with open_card("search_detail", f"{describe_product(row)} · {row['channel']}"):
        facts = [("Región", row["region"]), ("Semana", f"{row['week_start']:%d-%m-%Y}"),
                 ("Precio", f"$ {charts.format_thousands(row['price'])} por "
                            f"{row['normalized_unit']}"),
                 ("Alerta", f'<span style="color:{color}">{icon} {row["alert_state"]}</span>')]
        st.markdown('<div class="detail-facts">' + "".join(
            f'<div><div class="kpi-label">{label}</div><div class="detail-value">'
            f'{value if label == "Alerta" else html.escape(value)}</div></div>'
            for label, value in facts) + "</div>", unsafe_allow_html=True)
        history = explorer.read_series_history(row)
        line_rows = history.rename(columns={"price": "value"})
        show_chart(charts.draw_single_weekly_area(
            line_rows, f"$/{row['normalized_unit']}",
            "$ " + line_rows["value"].map(charts.format_thousands), mode, is_money=True,
            week_format=charts.SHORT_WEEK_AXIS_FORMAT))
        st.caption(f"Últimas {explorer.HISTORY_WEEKS} semanas de la serie seleccionada.")
        st.markdown(build_place_link(TAB_GAP) + " · " + build_place_link(TAB_ALERTS),
                    unsafe_allow_html=True)


def show_explorer_tab(mode):
    """Search of weekly prices: form, summary, table and detail (D-060)."""
    show_section_intro("Consulta por clics", "Busca precios semanales con el formulario: el "
                       "resumen dice cuántos están fuera de lo habitual, la tabla los lista y "
                       "la ficha muestra el detalle del que elijas.")
    options = read_cached_search_options(get_database_version())
    applied = read_applied_search(options)
    show_search_form(options, applied)
    show_active_filters(options, applied)
    if applied[explorer.FIELD_FIRST_WEEK] > applied[explorer.FIELD_LAST_WEEK]:
        st.warning("«Semana desde» es posterior a «Semana hasta».")
        return
    search_filters = {field: value for field, value in applied.items()
                      if field != explorer.FIELD_ALERT}
    rows = read_cached_search(tuple(sorted(search_filters.items())), get_database_version())
    if len(rows) > explorer.MAXIMUM_RESULT_ROWS:
        st.warning(f"La búsqueda trae {charts.format_thousands(len(rows))} precios; acótala "
                   f"(menos semanas, un grupo o una región) para ver hasta "
                   f"{charts.format_thousands(explorer.MAXIMUM_RESULT_ROWS)}.")
        return
    if rows.empty:
        st.info(NO_DATA_TEXT)
        return
    show_search_summary(rows, applied, mode)
    rows = explorer.keep_alert_state(rows, applied[explorer.FIELD_ALERT])
    selected = show_search_table(rows, applied, mode)
    if selected is not None:
        show_selected_detail(selected, mode)
# endregion


def show_data_and_code_page(mode):
    """The data explorer has a direct destination; queries and source files live separately."""
    show_page_header(PAGE_DATA_AND_CODE, "Busca y revisa precios semanales por producto, región, canal y fechas.")
    show_explorer_tab(mode)


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
ADMIN_LINKS = [
    {"name": "Administrar la app en Streamlit",
     "description": "Reboot, secretos y registros del panel publicado.",
     "url": control.STREAMLIT_ADMIN_URL, "icon": "settings"},
    {"name": "Lanzar el workflow en GitHub", "description": "Run workflow, desde GitHub.",
     "url": control.WORKFLOW_PAGE_URL, "icon": "play_circle"},
    {"name": "Crear token", "description": "Clave nueva para «Ejecutar ahora».",
     "url": control.TOKEN_CREATE_URL, "icon": "key"},
    {"name": "Ver mis tokens", "description": "Vencimiento y permisos de cada clave.",
     "url": control.TOKENS_URL, "icon": "vpn_key"},
]


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
        st.info("«Ejecutar ahora» se activa cuando la autora guarda su token de GitHub en "
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
            st.caption("Se activa cuando la autora guarda la clave de control en los "
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
                       f'<a href="{html.escape(run["url"])}" target="_blank">detalle</a>']
                      for run in runs]
        st.markdown(build_html_table(["Inicio", "Tipo", "Duración", "Estado", ""],
                                     table_rows), unsafe_allow_html=True)


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
            'El movimiento ilustra el recorrido; el estado identifica la ejecución real.</div>')


def show_pipeline_tab(mode, animate_flow=False):
    """The detailed live diagram of the data, from ODEPA to the dashboard."""
    states, figures, pipeline_run, latest_load, error_note = read_journey()
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


def show_infrastructure_diagram(mode, animate_flow=False):
    states, figures, pipeline_run, latest_load, error_note = read_journey()
    with open_card("devops_diagram", "Arquitectura por plataforma", hint=DEVOPS_HINT):
        st.markdown(zoom.build_zoom_frame_html(
            architecture.build_devops_svg(states, build_devops_figures(figures), mode, animate_flow=animate_flow)),
            unsafe_allow_html=True)


def show_devops_tab(mode):
    """Compact lifecycle with real tool logos; deployment topology remains unique."""
    states, figures, pipeline_run, latest_load, error_note = read_journey()
    animate = st.toggle("Animar el ciclo DevOps", value=True, key="animate_devops_cycle")
    st.markdown(devops.build_html(states, mode, animate), unsafe_allow_html=True)
    st.caption("El movimiento ilustra el ciclo de trabajo. Los puntos de estado muestran "
               "la última evidencia disponible; no afirman que haya una ejecución en curso.")
    st.markdown(build_link_html("Ver el pipeline y la arquitectura →",
                                build_page_address(PAGE_DIAGRAMS)), unsafe_allow_html=True)
    for group in ARCHITECTURE_GROUPS:
        show_architecture_group(*group)
        if group[0] == "DevOps":
            st.markdown(f'<div class="info-note">Próxima ejecución automática: '
                        f'{figures["next_run"]}.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-note">El enlace a los informes semanales está en '
                f'{build_place_link(PAGE_LINKS, "la página")}.</div>', unsafe_allow_html=True)


def show_architecture_page(mode):
    """The data model has a direct sidebar entry, without another tab layer."""
    show_page_header(PAGE_ARCHITECTURE, "La estructura que convierte los precios en "
                     "indicadores comparables: tablas, claves y relaciones.")
    show_star_schema_tab(mode)
    st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)


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
                     "tal como venían", expanded=True):
        if rejected_rows.empty:
            st.info("La última ejecución no rechazó filas.")
        else:
            reasons = sorted(rejected_rows["Motivo"].unique())
            if len(reasons) > 1:
                reason = st.selectbox("Motivo", reasons, key="rejected_reason")
                rejected_rows = rejected_rows[rejected_rows["Motivo"] == reason]
            st.dataframe(rejected_rows, hide_index=True)
    outliers = format_outliers(read_indicator("quality_outliers"))
    with st.expander(f"Ver los {charts.format_thousands(len(outliers))} precios atípicos", expanded=True):
        st.dataframe(outliers, hide_index=True)
    units = read_indicator("quality_unconvertible_units")
    units["source"] = units["source"].map(SOURCE_NAMES)
    units.columns = ["Fuente", "Canal", "Producto", "Variedad", "Calidad", "Precios semanales"]
    with st.expander("Ver los precios con unidad no convertible, por producto", expanded=True):
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


def show_operations_page(mode):
    """Monitoring shows load quality; launching and history have their own entry."""
    show_page_header(PAGE_OPERATIONS, "Calidad de la última carga, datos excluidos y motivos.")
    show_quality_tab(mode)


# endregion


# region Links page
def show_links_page(mode):
    """The only place with the links of the project, by group (D-058)."""
    show_page_header(PAGE_LINKS, "Todos los enlaces del proyecto en un solo lugar: el código, "
                     "las ejecuciones, las fuentes de datos y los documentos.")
    for group in dict.fromkeys(link["group"] for link in project.PROJECT_LINKS):
        show_section_intro(group, LINK_GROUP_LEADS.get(group, ""), True)
        entries = [link for link in project.PROJECT_LINKS if link["group"] == group]
        rows = "".join(
            f'<li><a href="{html.escape(link["url"], quote=True)}" target="_blank" '
            f'rel="noopener noreferrer">{html.escape(link["name"])}</a>'
            f'<span>{html.escape(link["description"])}</span></li>'
            for link in entries if link["url"])
        st.markdown(f'<ul class="resource-tree">{rows}</ul>', unsafe_allow_html=True)
        upcoming = [link["name"] for link in entries if not link["url"]]
        if upcoming:
            st.caption("Por publicar: " + ", ".join(upcoming))

# endregion


# region Entry point
def show_document_page(mode, title, subtitle, renderer):
    show_page_header(title, subtitle)
    renderer(mode)


SHOW_PAGE_BY_TITLE = {
    PAGE_HOME: show_home_page,
    PAGE_BUSINESS: lambda mode: show_document_page(mode, PAGE_BUSINESS,
        "Las preguntas, las fuentes y las decisiones de negocio detrás de los datos.", show_idea_tab),
    PAGE_DIAGRAMS: show_diagrams_page,
    PAGE_ANALYSIS: show_analysis_page,
    PAGE_GAP: lambda mode: show_analysis_view(mode, PAGE_GAP, show_gap_tab),
    PAGE_CHANNELS: lambda mode: show_analysis_view(mode, PAGE_CHANNELS, show_channels_tab),
    PAGE_SEASONALITY: lambda mode: show_analysis_view(mode, PAGE_SEASONALITY, show_seasonality_tab),
    PAGE_ALERTS: lambda mode: show_analysis_view(mode, PAGE_ALERTS, show_alerts_tab),
    PAGE_QUERIES: lambda mode: show_document_page(mode, PAGE_QUERIES,
        "Cada consulta con su pregunta, cláusulas y resultado en solo lectura.", show_queries_tab),
    PAGE_KPI: lambda mode: show_document_page(mode, PAGE_KPI,
        "BI: inteligencia de negocios. Cada indicador, su fórmula y un ejemplo real.", show_kpi_tab),
    PAGE_ARCHITECTURE: show_architecture_page,
    PAGE_DATA_AND_CODE: show_data_and_code_page,
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
    PAGE_DECISIONS: lambda mode: show_document_page(mode, PAGE_DECISIONS,
        "Decisiones de diseño con su motivo y sus límites.", show_decisions_tab),
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


def build_journey_navigation(title, position):
    index = PAGES.index(title)
    group = next(group for group, pages in NAVIGATION_GROUPS.items() if title in pages)
    previous = (build_link_html("← Anterior · " + PAGES[index - 1], build_page_address(PAGES[index - 1]))
                if index else '<span>Inicio del recorrido</span>')
    following = (build_link_html("Siguiente · " + PAGES[index + 1] + " →", build_page_address(PAGES[index + 1]))
                 if index + 1 < len(PAGES) else build_link_html("Volver al dashboard →", build_page_address(PAGE_HOME)))
    return (f'<nav class="project-navigation" aria-label="Recorrido del proyecto · {position}">'
            f'<div>{previous}</div><div class="journey-position">{html.escape(group)} · '
            f'{index + 1}/{len(PAGES)}</div><div>{following}</div></nav>')


def render_page(title):
    """Draw one page with the style of the active mode and the footer."""
    mode = get_mode()
    apply_style(mode)
    st.markdown(build_journey_navigation(title, "inicio"), unsafe_allow_html=True)
    SHOW_PAGE_BY_TITLE[title](mode)
    st.markdown(build_journey_navigation(title, "final"), unsafe_allow_html=True)
    show_attribution()
    st.html(FOLD_SIDEBAR_SCRIPT, unsafe_allow_javascript=True)


def build_page(title, is_default):
    """A navigation entry that draws one page."""
    return st.Page(lambda: render_page(title), title=title, icon=PAGE_ICONS[title],
                   url_path=PAGE_PATHS[title], default=is_default)


def build_redirect_page(url_path, target_page, tab=None):
    """A hidden page at an old address that opens its new place, keeping the
    parameters of the link (D-051, D-056)."""
    def redirect():
        parameters = {key: value for key, value in st.query_params.to_dict().items()
                      if key != THEME_PARAMETER}
        if tab:
            parameters[TAB_PARAMETER] = tab
        st.switch_page(target_page, query_params=parameters)
    return st.Page(redirect, title=target_page.title, url_path=url_path,
                   visibility="hidden")


def redirect_moved_tab(current_page, pages_by_title):
    """Keep deep links working after moving a tab to the sidebar."""
    tab = st.query_params.get(TAB_PARAMETER)
    if (current_page.title, tab) in OLD_TAB_PAGES:
        st.query_params.pop(TAB_PARAMETER, None)
        st.switch_page(pages_by_title[OLD_TAB_PAGES[(current_page.title, tab)]],
                       query_params={key: value for key, value in st.query_params.to_dict().items()
                                     if key != THEME_PARAMETER})
    tab = OLD_HOME_TABS.get(tab, tab)
    destination = PAGE_OF_TAB.get(tab)
    if destination and destination != current_page.title:
        parameters = {key: value for key, value in st.query_params.to_dict().items()
                      if key != THEME_PARAMETER}
        if tab in TABS_BY_PAGE[destination]:
            parameters[TAB_PARAMETER] = tab
        else:
            parameters.pop(TAB_PARAMETER, None)
        st.switch_page(pages_by_title[destination], query_params=parameters)


@st.dialog("Monitor de precios de alimentos", dismissible=False, width="small")
def choose_visitor_profile():
    """One choice per session, before any data or diagram is displayed."""
    st.markdown("### ¿Desde qué mirada quieres recorrerlo?")
    st.write("Accede al seguimiento de precios, variaciones y alertas de alimentos en Chile. "
             "Tu perfil orienta el recorrido; todas las secciones están disponibles.")
    with st.form("visitor_welcome"):
        selected = st.radio("¿Quién consulta?", list(VISITOR_PROFILES), index=None,
                            format_func=lambda value: value)
        submitted = st.form_submit_button("Abrir dashboard", type="primary",
                                          use_container_width=True)
    if submitted:
        if selected is None:
            st.info("Elige un perfil para continuar.")
        else:
            st.session_state[PROFILE_PARAMETER] = selected
            st.query_params["perfil"] = selected
            st.session_state["open_dashboard_after_profile"] = True
            st.rerun()


def change_visitor_profile():
    st.session_state.pop(PROFILE_PARAMETER, None)
    st.query_params.pop("perfil", None)


def main():
    """Theme, navigation with icons and the chosen page."""
    st.set_page_config(page_title="Monitor de precios de alimentos", layout="wide",
                       page_icon=":material/monitoring:")
    if not queries.DATABASE_FILE.exists():
        st.error("Falta etl/datos.db. Ejecuta primero: python etl/etl.py")
        return
    # Migrate old links to Claro to the remaining light theme.
    if st.query_params.get(THEME_PARAMETER) == charts.MODE_LIGHT:
        st.query_params[THEME_PARAMETER] = charts.MODE_CORPORATE
    if st.session_state.get(THEME_PARAMETER) == charts.MODE_LIGHT:
        st.session_state[THEME_PARAMETER] = charts.MODE_CORPORATE
    saved_profile = st.query_params.get("perfil")
    if saved_profile in VISITOR_PROFILES and PROFILE_PARAMETER not in st.session_state:
        st.session_state[PROFILE_PARAMETER] = saved_profile
    if st.session_state.get(PROFILE_PARAMETER) not in VISITOR_PROFILES:
        apply_style(get_mode())
        choose_visitor_profile()
        st.stop()
    st.query_params["perfil"] = st.session_state[PROFILE_PARAMETER]
    st.sidebar.markdown("**MONITOR DE PRECIOS**")
    st.sidebar.caption("Seguimiento de precios · ODEPA")
    st.sidebar.caption(st.session_state[PROFILE_PARAMETER])
    st.sidebar.button("Cambiar perfil", on_click=change_visitor_profile,
                      icon=":material/person:", use_container_width=True)
    theme = st.sidebar.selectbox("Tema", charts.THEMES, key=THEME_PARAMETER,
                                 bind="query-params")
    match_base_mode(theme)
    pages_by_title = {title: build_page(title, position == 0)
                      for position, title in enumerate(PAGES)}
    redirects = [build_redirect_page(path, pages_by_title[page], tab)
                 for path, (page, tab) in OLD_PATHS.items()]
    sections = {group: [pages_by_title[title] for title in titles]
                for group, titles in NAVIGATION_GROUPS.items()}
    sections["Compatibilidad"] = redirects
    current_page = st.navigation(sections, position="sidebar", expanded=True)
    if st.session_state.pop("open_dashboard_after_profile", False):
        st.switch_page(pages_by_title[PAGE_HOME], query_params={"perfil": st.session_state[PROFILE_PARAMETER]})
    redirect_moved_tab(current_page, pages_by_title)
    current_page.run()
    st.sidebar.caption("Fuente: ODEPA · actualización automática cada martes.")


if __name__ == "__main__":
    main()
# endregion
