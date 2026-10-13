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
from bi import (alerts, architecture, charts, control, explorer, lag, project,  # noqa: E402
                queries, star_model, zoom)
from etl import etl  # noqa: E402
# endregion

# region Constants
# One menu for everyone, by type of content: each entry has its tabs (D-056).
PAGE_HOME = "Inicio"
PAGE_ANALYSIS = "Análisis"
PAGE_ARCHITECTURE = "Arquitectura"
PAGE_DATA_AND_CODE = "Datos y código"
PAGE_OPERATIONS = "Operaciones"
# The project links have an entry of their own, the only place that shows them (D-058).
PAGE_LINKS = "Enlaces"
PAGES = [PAGE_HOME, PAGE_ANALYSIS, PAGE_ARCHITECTURE, PAGE_DATA_AND_CODE, PAGE_OPERATIONS,
         PAGE_LINKS]
HOME_PAGE = PAGE_HOME
PAGE_ICONS = {
    PAGE_HOME: ":material/home:", PAGE_ANALYSIS: ":material/monitoring:",
    PAGE_ARCHITECTURE: ":material/account_tree:", PAGE_DATA_AND_CODE: ":material/database:",
    PAGE_OPERATIONS: ":material/settings:", PAGE_LINKS: ":material/link:",
}
PAGE_PATHS = {
    PAGE_HOME: "inicio", PAGE_ANALYSIS: "analisis", PAGE_ARCHITECTURE: "arquitectura",
    PAGE_DATA_AND_CODE: "datos-y-codigo", PAGE_OPERATIONS: "operaciones",
    PAGE_LINKS: "enlaces",
}

# The tabs of each page travel in the address (?seccion=...), so a link can open one.
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
TABS_BY_PAGE = {
    PAGE_HOME: [TAB_IDEA, TAB_KPI, TAB_RULES, TAB_MANUAL, TAB_DECISIONS, TAB_GLOSSARY],
    PAGE_ANALYSIS: [TAB_WEEK, TAB_GAP, TAB_CHANNELS, TAB_SEASONALITY, TAB_ALERTS],
    PAGE_ARCHITECTURE: [TAB_PIPELINE, TAB_MODEL, TAB_DEVOPS],
    PAGE_DATA_AND_CODE: [TAB_EXPLORER, TAB_QUERIES, TAB_CODE],
    PAGE_OPERATIONS: [TAB_RUNS, TAB_QUALITY],
    PAGE_LINKS: [],
}
PAGE_OF_TAB = {tab: page for page, tabs in TABS_BY_PAGE.items() for tab in tabs}

# Old addresses, kept so that saved links still work: each opens its new tab (D-056).
OLD_PATHS = {
    "el-proyecto": (PAGE_HOME, None), "panel": (PAGE_ANALYSIS, TAB_WEEK),
    "margenes": (PAGE_ANALYSIS, TAB_GAP), "canales-y-regiones": (PAGE_ANALYSIS, TAB_CHANNELS),
    "estacionalidad": (PAGE_ANALYSIS, TAB_SEASONALITY), "alertas": (PAGE_ANALYSIS, TAB_ALERTS),
    "consultas": (PAGE_DATA_AND_CODE, TAB_EXPLORER), "pipeline": (PAGE_ARCHITECTURE, TAB_PIPELINE),
    "diagramas": (PAGE_ARCHITECTURE, None), "centro-de-control": (PAGE_OPERATIONS, TAB_RUNS),
    "calidad-de-datos": (PAGE_OPERATIONS, TAB_QUALITY),
}
# Tabs of the old project page that live elsewhere now.
OLD_HOME_TABS = {"Fuentes y cruces": TAB_IDEA, "Arquitectura": TAB_PIPELINE,
                 "Modelo de datos": TAB_MODEL, "Código": TAB_CODE}
# Tabs that became a page of their own: (page they lived in, tab) -> new page.
OLD_TAB_PAGES = {(PAGE_OPERATIONS, "Enlaces"): PAGE_LINKS}
TAB_PARAMETER = "seccion"
THEME_PARAMETER = "tema"
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
# A channel gap that rests on this many regions or fewer names them next to its bar.
MAXIMUM_REGIONS_NAMED = 2
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
    theme = st.session_state.get(THEME_PARAMETER)
    return theme if theme in charts.PALETTES else charts.MODE_DARK


def build_base_mode_script(base):
    """JavaScript that puts Streamlit in its light or dark base mode and reloads.

    Streamlit has no Python function for this; it keeps the reader's choice in
    the browser (localStorage, key «stActiveTheme-<path>-v2»), the same place its
    own ⋮ > Settings writes. It tries once per page and base: if Streamlit ever
    changes that key, the page does not reload again and again (D-052).
    """
    value = json.dumps("Dark" if base == charts.BASE_DARK else "Light")
    return f"""<script>
    const page = window.parent;
    const attempt = "base-mode-" + page.location.pathname + "-" + {value};
    if (!page.sessionStorage.getItem(attempt)) {{
        page.sessionStorage.setItem(attempt, "1");
        page.localStorage.setItem("stActiveTheme-" + page.location.pathname + "-v2",
                                  JSON.stringify({value}));
        page.location.reload();
    }}
    </script>"""


def match_base_mode(theme):
    """Streamlit's lists, tables and code follow its base mode: switch it when the
    chosen theme needs the other one. Nothing happens until the browser reports
    its mode."""
    base = charts.get_palette(theme)["base"]
    if st.context.theme.type in (charts.BASE_DARK, charts.BASE_LIGHT) and (
            st.context.theme.type != base):
        components.html(build_base_mode_script(base), height=0)


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
    [data-baseweb="tag"] span, [data-baseweb="tag"] svg {{
        color: {palette["on_accent"]}; fill: {palette["on_accent"]};
    }}
    .hint {{ color: {palette["accent"]} !important; }}
    """


def build_style_css(mode):
    """Cards, key figures, chips and tables, in the colors of the active theme."""
    palette = charts.get_palette(mode)
    return build_theme_css(palette) + f"""
    [class*="st-key-card_"] {{
        background: {palette["card"]}; border: 1px solid {palette["card_border"]};
        border-radius: 18px; padding: 18px 20px 14px 20px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06), inset 0 1px 0 {palette["glow"]};
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
    """Relative address of a page, one of its tabs or a KPI card."""
    parameters = {}
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
    if place in PAGE_OF_TAB:
        return build_page_address(PAGE_OF_TAB[place], place)
    return build_page_address(place)


def build_link_html(text, address):
    """A link that opens in the same tab, with already-escaped text."""
    return f'<a href="{html.escape(address)}" target="_self">{html.escape(text)}</a>'


def build_kpi_link(kpi):
    """«¿Cómo se calcula K7?»: opens the details of that indicator in Inicio."""
    address = build_page_address(PAGE_HOME, TAB_KPI, kpi)
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


def build_info_card_html(title, text, label=None, note=None, link=None, is_warning=False,
                         body_html=""):
    """One card: an optional label, a title, a short text, more content right under it
    (body_html), a note and a named link at the bottom."""
    text = capitalize_first(text)
    parts = [f'<div class="info-label">{html.escape(label)}</div>' if label else "",
             f'<div class="info-title">{format_inline(title)}</div>',
             f'<div class="info-text">{format_inline(text)}</div>', body_html,
             f'<div class="info-note">{format_inline(note)}</div>' if note else "",
             f'<div class="info-link">{link}</div>' if link else ""]
    kind = " is-warning" if is_warning else ""
    return f'<div class="info-card{kind}">{"".join(parts)}</div>'


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
    destination = f"{page} › {place}" if page else place
    return build_link_html(f"{verb} {destination}".strip(), build_place_address(place))
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
def show_page_tabs(page, tab_contents, *arguments):
    """The tabs of one page, bound to the address so a link can open one of them."""
    tabs = st.tabs(TABS_BY_PAGE[page], key=TAB_PARAMETER, bind="query-params")
    for tab, show_tab_content in zip(tabs, tab_contents):
        with tab:
            show_tab_content(*arguments)


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


def show_overview_trend(rows, mode, key="trend"):
    """Card: weekly price of the wholesale market and of each consumer channel."""
    with open_card(key, "Precio por semana", "La línea gris es el precio mayorista.",
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


def show_overview_margins(rows, mode, key="margins"):
    """Card: median margin of each consumer channel over the weeks shown."""
    with open_card(key, "Margen mediano por canal",
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


def show_overview_regions(key, mode):
    """Card: regional index of the street market price for the chosen product."""
    with open_card("regions", "¿Dónde es más caro?",
                   "Precio en feria por región; 1 = promedio nacional.",
                   hint=REGIONAL_INDEX_HINT, kpi="K3"):
        rows = read_indicator_for_key("k3_regional_index", key)
        rows = rows[rows["channel"] == DEFAULT_CHANNEL]
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
    latest_week = read_latest_week()
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
    st.caption(FILTERS_NOTE)
    return {"key": key, "region": region, "channels": channels}


def read_margin_rows(filters):
    """K1 rows of the chosen product and region."""
    rows = read_indicator_for_key("k1_margin", filters["key"])
    return rows[rows["region"] == filters["region"]]


def show_week_tab(mode, filters):
    """This week: key figures, trend, margins, regions and alerts on one screen."""
    rows = read_margin_rows(filters)
    chosen_rows = rows[rows["channel"].isin(filters["channels"])]
    if rows.empty or chosen_rows.empty:
        st.info(NO_MARGIN_TEXT)
    else:
        show_overview_figures(rows, mode)
        trend_column, margin_column = st.columns([3, 2])
        with trend_column:
            show_overview_trend(chosen_rows, mode)
        with margin_column:
            show_overview_margins(chosen_rows, mode)
    region_column, alert_column = st.columns([2, 3])
    with region_column:
        show_overview_regions(filters["key"], mode)
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


def show_pipeline_hook(mode):
    """The state line of the live pipeline; on phones also its five steps. The whole
    diagram lives only in Arquitectura (D-056)."""
    states, figures, pipeline_run, latest_load, error_note = read_journey()
    with open_card("live_pipeline", "Pipeline en vivo"):
        st.markdown(build_run_status_html(states, pipeline_run, latest_load),
                    unsafe_allow_html=True)
        if error_note:
            st.caption(error_note)
        st.markdown(build_svg_image_html(architecture.build_mini_journey_svg(
            states, figures, mode), "diagram-fit phone-only"), unsafe_allow_html=True)


def show_project_value():
    """Three sentences and the main figures, all read now."""
    st.markdown(project.read_section(project.read_document(project.PROJECT_GUIDE_FILE),
                                     "Resumen"))
    keys_with_margin, consumer_keys = read_match_coverage()
    figures = [("Precios semanales",
                charts.format_thousands(read_indicator("quality_flag_counts")
                                        ["weekly_prices"].sum())),
               ("Datos cargados", describe_loaded_years()),
               ("Cobertura (K7)", f"{keys_with_margin} de {consumer_keys} claves"),
               ("Alertas de la semana (K6)", str(read_week_alert_count()))]
    cells = "".join(f'<div><div class="kpi-label">{html.escape(label)}</div>'
                    f'<div class="card-title">{html.escape(value_text)}</div></div>'
                    for label, value_text in figures)
    st.markdown(f'<div class="figure-grid">{cells}</div>', unsafe_allow_html=True)


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
    """Inverted pyramid: the live pipeline first, then the value and the guided tours."""
    show_pipeline_hook(mode)
    with open_card("start_here", "Empieza aquí"):
        show_project_value()
        show_journeys()


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
    show_section_intro("Preguntas que responde", "Seis preguntas de un área de pricing o "
                       "abastecimiento; cada una lleva a la pestaña donde se ve.", True)
    show_info_cards(build_question_cards())


def show_audience(mode):
    """Who the panel is for, and where each reader starts."""
    show_section_intro("Para quién", "Quién lo usa hoy y qué viene después.", True)
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
    with st.expander("Ver detalles"):
        st.markdown(MATCH_DETAILS)


def show_limits(mode):
    """What the figures do not say, always in sight."""
    show_section_intro("Límites", "Lo que hay que tener presente al leer cualquier cifra.",
                       True)
    show_info_cards([build_info_card_html(title, text, is_warning=True)
                     for title, text in LIMIT_CARDS])


def show_why(mode):
    """Why this subject, with the discarded alternatives folded."""
    show_section_intro("Por qué este tema", WHY_TEXT, True)
    with st.expander("Ver detalles"):
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
        with st.expander("Ver etl/schema.sql"):
            st.code(project.read_document(project.SCHEMA_FILE), language="sql")


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
    """The question, the real example step by step and the SQL of one indicator, folded."""
    kpi = indicator["ID"]
    with st.expander(f"Ver detalles de {kpi}: ejemplo real y consulta SQL",
                     expanded=is_requested):
        if is_requested:
            st.markdown(build_chip("Llegaste desde un gráfico del panel", "running"),
                        unsafe_allow_html=True)
        st.markdown(f"**Pregunta que responde:** {question}")
        if example_steps:
            st.markdown("**Ejemplo real, calculado con la base actual:**  \n"
                        + build_steps_html(example_steps), unsafe_allow_html=True)
        sql, file_name = read_kpi_query(guide_row["Consulta"])
        st.markdown(f"**Consulta SQL** `{guide_row['Consulta']}`, en `{file_name}`:")
        st.code(sql, language="sql")
        st.markdown(build_link_html(f"Abrir {file_name} en GitHub",
                                    project.build_github_url(file_name)),
                    unsafe_allow_html=True)


def show_kpi_tab(mode):
    """K1 to K8: the eight cards first, then the details of each one folded (D-057).

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
    show_section_intro("Cómo se calcula cada una", "Abre un indicador para ver su ejemplo "
                       "paso a paso y la consulta que lo produce.", True)
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
    with st.expander("Ver detalles: regla completa, por qué y dónde ocurre"):
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


def show_sections_folded(text, first_open=True):
    """Each '## ' section of a document in its own box; only the first one open."""
    for position, (heading, body) in enumerate(project.split_sections(text)):
        with st.expander(heading, expanded=first_open and position == 0):
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
        with st.expander(f"Ver detalles: {heading[0].lower() + heading[1:]}"):
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
        with st.expander(f"Ver detalles: {heading.lower()}"):
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
        with st.expander(f"Ver detalles: {theme.lower()}"):
            for number in numbers:
                st.markdown(f"**{by_number[number]}**")
                st.markdown(decisions[by_number[number]])
    key_numbers = {number for _, _, numbers in KEY_DECISIONS for number in numbers}
    others = sorted((number for number in by_number if number not in key_numbers),
                    key=lambda number: int(number[2:]), reverse=True)
    show_section_intro("Las demás decisiones", f"{len(others)} decisiones, de la más reciente "
                       "a la más antigua.", True)
    for number in others:
        with st.expander(by_number[number]):
            st.markdown(decisions[by_number[number]])


def show_query_result_button(key, sql, parameters=()):
    """Button that runs a query on the read-only database and shows 20 rows."""
    if st.button("Ver resultado", key=f"preview_{key}", icon=":material/play_arrow:"):
        st.dataframe(project.run_preview(sql, parameters), hide_index=True,
                     use_container_width=True)
        st.caption(f"Primeras {project.PREVIEW_ROW_COUNT} filas como máximo, en solo lectura.")


def build_clause_chips(query):
    """Labels of a query; those that set its level are colored and say so on hover."""
    return " ".join(
        build_chip(clause, "running", f"Por esta etiqueta la query es {query['level']}")
        if clause in query["level_reasons"] else build_chip(clause, "neutral")
        for clause in query["clauses"])


def show_query_block(query, origin=None, parameters=()):
    """One query: question, level and labels, page, SQL folded and its first 20 rows."""
    with st.container(border=True, key=f"query_{query['name']}"):
        origin_text = f" · vive en {origin}" if origin else ""
        st.markdown(f"**{query['name']}**{origin_text}  \n{html.escape(query['question'])}",
                    unsafe_allow_html=True)
        page = query["page"]
        st.markdown(f"{build_chip(query['level'], 'ok')} {build_clause_chips(query)}  \n"
                    f"Se usa en: {build_link_html(page, build_place_address(page))}",
                    unsafe_allow_html=True)
        with st.expander("Ver SQL"):
            if query["python"]:
                sql_tab, python_tab = st.tabs(["SQL", "Python"])
                sql_tab.code(query["sql"], language="sql")
                python_tab.code("\n\n".join(query["python"]), language="python")
                st.caption("Ambas versiones dan el mismo resultado (verificado por test).")
            else:
                st.code(query["sql"], language="sql")
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
                                    "tomate en feria y supermercado.",
                        "page": TAB_EXPLORER, "python": [],
                        **project.describe_query(explorer_sql)}
    return [(match_coverage, "etl/etl.py", ()),
            (explorer_example, "bi/explorer.py", explorer_parameters)]


def show_level_criteria(groups):
    """How a query gets its level, and how many queries each level has."""
    st.markdown(build_html_table(
        ["Nivel", "Criterio (cláusulas detectadas en el texto SQL)", "Queries"],
        [[build_chip(level, "ok"), html.escape(project.LEVEL_CRITERIA[level]),
          str(len(groups[level]))] for level in project.QUERY_LEVELS]),
        unsafe_allow_html=True)
    st.caption("Cada query toma el nivel más alto que alcanza. Las etiquetas en azul son las "
               "que deciden su nivel.")


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


def show_queries_tab(mode):
    """Every SQL query of the project, by level, with Python where it exists (T-57)."""
    named_queries = project.list_named_queries()
    groups = project.group_queries_by_level(named_queries)
    with open_card("code_queries", "Queries"):
        st.markdown(f"### {len(named_queries)} queries del proyecto")
        st.caption("Las queries con nombre de bi/queries.sql, contadas al abrir la página. "
                   "Al final, la de K7 (etl/etl.py), un ejemplo de Consulta por clics y "
                   "etl/schema.sql.")
        show_level_criteria(groups)
        for level in project.QUERY_LEVELS:
            st.markdown(f"#### {level} · {len(groups[level])}")
            for query in groups[level]:
                show_query_block(query)
        st.markdown("#### Fuera de bi/queries.sql")
        for query, origin, parameters in build_extra_queries():
            show_query_block(query, origin, parameters)
        with st.expander("etl/schema.sql · creación de las tablas (no es una consulta)"):
            st.code(project.read_document(project.SCHEMA_FILE), language="sql")


def show_files_tab(mode):
    """The files of the repository, by folder, each with what it does (D-057)."""
    show_section_intro("Código", "Los archivos del repositorio por carpeta, en el orden en que "
                       "pasan los datos. Cada nombre abre el archivo en GitHub.")
    show_repository_files()


def show_idea_tab(mode):
    """The business idea: the most useful first (questions), then who it is for, the
    sources and how they are matched, the limits and why this subject (D-057)."""
    show_section_intro("Idea de negocio", "Qué preguntas responde el panel, para quién está "
                       "hecho, de dónde salen los datos y qué límites tiene.")
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


def show_home_page(mode):
    """Short home: the state of the pipeline, the value and the tours; the
    documentation in tabs (D-056)."""
    show_page_header("Monitor de precios de alimentos", "Qué problema resuelve, cómo "
                     "funciona y cómo se calcula cada cifra.")
    show_start_here(mode)
    show_page_tabs(PAGE_HOME, [show_idea_tab, show_kpi_tab, show_rules_tab, show_manual_tab,
                               show_decisions_tab, show_glossary_tab], mode)


# endregion


# region Margins page
def show_gap_tab(mode, filters):
    """K1, gap between the wholesale and each consumer channel, and K5, its lag."""
    st.caption("Brecha = (precio al consumidor − precio mayorista) / precio mayorista, con la "
               "misma variedad, calidad, región, semana y unidad.")
    rows = read_margin_rows(filters)
    rows = rows[rows["channel"].isin(filters["channels"])].copy()
    if rows.empty:
        st.info(NO_MARGIN_TEXT)
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
        show_overview_trend(rows, mode, key="gap_trend")
    with bars_column:
        show_overview_margins(rows, mode, key="gap_margins")
    show_lag_card(rows, mode)
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
                                               colors, reference_value=0))
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
                                               reference_value=1))
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
def show_seasonality_tab(mode, filters):
    """K4: national price of each week over the average of its year, by channel."""
    st.caption("Índice = precio nacional de la semana / promedio del año. Con varios años se "
               "ve qué semanas son caras o baratas cada año.")
    rows = read_indicator_for_key("k4_seasonal_index", filters["key"])
    rows = rows[rows["channel"].isin(filters["channels"])]
    if rows.empty:
        st.info(NO_DATA_TEXT)
        return
    index_column, price_column = st.columns(2)
    with index_column, open_card("seasonal_index", "Índice estacional",
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


def show_alerts_tab(mode, filters):
    """K6: products whose price moved outside their usual range in one week."""
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


def show_analysis_page(mode):
    """Every chart of the project; the filters on top hold for every tab (D-056)."""
    show_page_header(PAGE_ANALYSIS, "Del mercado mayorista al consumidor, con datos oficiales "
                     "de ODEPA que se actualizan solos cada martes.")
    filters = choose_analysis_filters()
    show_page_tabs(PAGE_ANALYSIS, [show_week_tab, show_gap_tab, show_channels_tab,
                                   show_seasonality_tab, show_alerts_tab], mode, filters)


# endregion


# region Consultas page
@st.cache_data
def read_cached_explorer_result(view, group_labels, measure_label, filters, database_version):
    """Result of one combination of choices, computed once per database (T-52)."""
    return explorer.build_result(view, read_explorer_rows(view, filters), list(group_labels),
                                 measure_label, filters)


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
            table = explorer.name_columns_for_reader(shown_rows, view, measure_label)
            st.dataframe(explorer.write_numbers_for_reader(table, view, measure_label),
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


def show_explorer_tab(mode):
    """Query builder: the reader picks a view, groups, filters and a measure with clicks."""
    st.caption("Arma tu propia consulta con clics: qué ver, cómo agruparlo, qué filtrar y "
               "cómo resumirlo.")
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
    result = read_cached_explorer_result(view, tuple(group_labels), measure_label, filters,
                                         get_database_version())
    show_explorer_result(view, result, measure_label, mode)
    show_explorer_sql(view, filters, group_labels, measure_label)


def show_data_and_code_page(mode):
    """The data by clicks, every SQL query and the files of the project (D-056)."""
    show_page_header(PAGE_DATA_AND_CODE, "Consulta los datos con clics, revisa todas las "
                     "queries SQL y los archivos del proyecto.")
    show_page_tabs(PAGE_DATA_AND_CODE, [show_explorer_tab, show_queries_tab, show_files_tab],
                   mode)


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


@st.cache_data(ttl=GITHUB_CACHE_SECONDS)
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


@st.cache_data(ttl=GITHUB_CACHE_SECONDS)
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
    """One table of docs/PROYECTO.md (Seguridad, DevOps, ...) as cards."""
    show_section_intro(heading, lead, True)
    show_info_cards([build_info_card_html(
        row[title_column], row[text_column],
        link=format_architecture_note(note_column, row[note_column]))
        for row in project.read_guide_table(heading)])


def build_journey_legend_html():
    """What the colored dot of each step and the moving arrows mean."""
    return (f'{build_chip("OK", "ok")} {build_chip("En curso", "running")} '
            f'{build_chip("Falla", "failed")} {build_chip("Sin datos", "neutral")}'
            '<div class="kpi-note" style="margin-top:8px">Punto de color en cada '
            'paso: estado de la última ejecución del pipeline y de la base actual. '
            'Las flechas solo se mueven mientras hay una ejecución en curso.</div>')


def show_pipeline_tab(mode):
    """The detailed live diagram of the data, from ODEPA to the dashboard."""
    states, figures, pipeline_run, latest_load, error_note = read_journey()
    with open_card("journey", "Recorrido completo por capas", hint=ARCHITECTURE_HINT):
        st.markdown(build_run_status_html(states, pipeline_run, latest_load),
                    unsafe_allow_html=True)
        if error_note:
            st.caption(error_note)
        # Inline SVG (not an image), so each piece shows its explanation on hover.
        st.markdown(zoom.build_zoom_frame_html(
                        architecture.build_journey_svg(states, figures, mode), "diagram-wide")
                    + zoom.build_zoom_frame_html(
                        architecture.build_vertical_journey_svg(states, figures, mode),
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


def show_devops_tab(mode):
    """The whole project in one live diagram, then security, DevOps, observability and
    reports as cards, by priority (D-057)."""
    states, figures, pipeline_run, latest_load, error_note = read_journey()
    with open_card("devops_diagram", "Arquitectura por plataforma", hint=DEVOPS_HINT):
        st.markdown(build_run_status_html(states, pipeline_run, latest_load),
                    unsafe_allow_html=True)
        if error_note:
            st.caption(error_note)
        st.markdown(zoom.build_zoom_frame_html(
            architecture.build_devops_svg(states, build_devops_figures(figures), mode))
            + build_journey_legend_html(), unsafe_allow_html=True)
    for group in ARCHITECTURE_GROUPS:
        show_architecture_group(*group)
        if group[0] == "DevOps":
            st.markdown(f'<div class="info-note">Próxima ejecución automática: '
                        f'{figures["next_run"]}.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-note">El enlace a los informes semanales está en '
                f'{build_place_link(PAGE_LINKS, "la página")}.</div>', unsafe_allow_html=True)


def show_architecture_page(mode):
    """Every diagram of the project, each in its own tab, none repeated (D-054, D-056)."""
    show_page_header(PAGE_ARCHITECTURE, "El pipeline de los datos, el modelo de datos y la "
                     "infraestructura del proyecto, con datos reales.")
    show_page_tabs(PAGE_ARCHITECTURE, [show_pipeline_tab, show_star_schema_tab,
                                       show_devops_tab], mode)
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
                     "tal como venían"):
        if rejected_rows.empty:
            st.info("La última ejecución no rechazó filas.")
        else:
            reasons = sorted(rejected_rows["Motivo"].unique())
            if len(reasons) > 1:
                reason = st.selectbox("Motivo", reasons, key="rejected_reason")
                rejected_rows = rejected_rows[rejected_rows["Motivo"] == reason]
            st.dataframe(rejected_rows, hide_index=True)
    outliers = format_outliers(read_indicator("quality_outliers"))
    with st.expander(f"Ver los {charts.format_thousands(len(outliers))} precios atípicos"):
        st.dataframe(outliers, hide_index=True)
    units = read_indicator("quality_unconvertible_units")
    units["source"] = units["source"].map(SOURCE_NAMES)
    units.columns = ["Fuente", "Canal", "Producto", "Variedad", "Calidad", "Precios semanales"]
    with st.expander("Ver los precios con unidad no convertible, por producto"):
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
    """The state of each run and the quality of each load (D-056)."""
    show_page_header(PAGE_OPERATIONS, "El pipeline descarga, revisa y guarda los datos cada "
                     "martes. Aquí ves su estado y la calidad de cada carga.")
    show_page_tabs(PAGE_OPERATIONS, [show_runs_tab, show_quality_tab], mode)


# endregion


# region Links page
def show_links_page(mode):
    """The only place with the links of the project, by group (D-058)."""
    show_page_header(PAGE_LINKS, "Todos los enlaces del proyecto en un solo lugar: el código, "
                     "las ejecuciones, las fuentes de datos y los documentos.")
    links = project.PROJECT_LINKS
    for group in dict.fromkeys(link["group"] for link in links):
        published = [link for link in links if link["group"] == group and link["url"]]
        if published:
            show_section_intro(group, LINK_GROUP_LEADS.get(group, ""), True)
            show_link_cards(published)
    upcoming = [link["name"] for link in links if not link["url"]]
    if upcoming:
        st.markdown(f'<div class="info-note">Próximamente: {html.escape(", ".join(upcoming))}.'
                    '</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-note">Los enlaces de administración (Streamlit, workflow y '
                f'tokens) están en {build_place_link(TAB_RUNS, "")} → 🔒 Administración, con '
                'la clave de control.</div>', unsafe_allow_html=True)
# endregion


# region Entry point
SHOW_PAGE_BY_TITLE = {
    PAGE_HOME: show_home_page,
    PAGE_ANALYSIS: show_analysis_page,
    PAGE_ARCHITECTURE: show_architecture_page,
    PAGE_DATA_AND_CODE: show_data_and_code_page,
    PAGE_OPERATIONS: show_operations_page,
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


def render_page(title):
    """Draw one page with the style of the active mode and the footer."""
    mode = get_mode()
    apply_style(mode)
    SHOW_PAGE_BY_TITLE[title](mode)
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
        parameters = st.query_params.to_dict()
        if tab:
            parameters[TAB_PARAMETER] = tab
        st.switch_page(target_page, query_params=parameters)
    return st.Page(redirect, title=target_page.title, url_path=url_path,
                   visibility="hidden")


def redirect_moved_tab(current_page, pages_by_title):
    """An old link to a tab that moved opens it where it lives now: the tabs of the
    former project page (D-056) and the links, now a page of their own (D-058)."""
    tab = st.query_params.get(TAB_PARAMETER)
    parameters = st.query_params.to_dict()
    moved_page = OLD_TAB_PAGES.get((current_page.title, tab))
    if moved_page:
        parameters.pop(TAB_PARAMETER)
        st.switch_page(pages_by_title[moved_page], query_params=parameters)
    moved_tab = OLD_HOME_TABS.get(tab)
    if current_page.title == HOME_PAGE and moved_tab:
        st.switch_page(pages_by_title[PAGE_OF_TAB[moved_tab]],
                       query_params=dict(parameters, **{TAB_PARAMETER: moved_tab}))


def main():
    """Theme, navigation with icons and the chosen page."""
    st.set_page_config(page_title="Monitor de precios de alimentos", layout="wide",
                       page_icon=":material/monitoring:")
    if not queries.DATABASE_FILE.exists():
        st.error("Falta etl/datos.db. Ejecuta primero: python etl/etl.py")
        return
    theme = st.sidebar.selectbox("Tema", charts.THEMES, key=THEME_PARAMETER,
                                 bind="query-params")
    match_base_mode(theme)
    pages_by_title = {title: build_page(title, position == 0)
                      for position, title in enumerate(PAGES)}
    redirects = [build_redirect_page(path, pages_by_title[page], tab)
                 for path, (page, tab) in OLD_PATHS.items()]
    current_page = st.navigation(list(pages_by_title.values()) + redirects,
                                 position="sidebar")
    redirect_moved_tab(current_page, pages_by_title)
    current_page.run()
    st.sidebar.caption("Fuente: ODEPA · actualización automática cada martes.")


if __name__ == "__main__":
    main()
# endregion
