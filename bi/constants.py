"""The fixed names of the panel: its pages, menu sections, address parameters, themes and the texts that never change.

Every part of the panel reads them from here (D-541), so a page module never has to import bi/dashboard.py, which
Streamlit runs as its main script.
"""

from pathlib import Path

from bi import charts, project
from etl import etl

# region Constants
# The menu is the project journey; every destination is directly accessible.
# D-459: the three pages of «Negocio · BA y BI» are dashboards, under the title «Dashboards»; the weekly one is
# «Semanal», and the old address «Dashboard» opens it.
PAGE_HOME = "Semanal"
# D-296: the macro dashboard of the whole project, in tabs, like a BI tool; the first page of the menu.
PAGE_INSIGHTS = "Insights"
PAGE_CHANNELS = "Último dato por canal"  # D-365: each source with its own latest week
PAGE_STAKEHOLDERS = "Interesados"  # D-376: who uses the data, what they ask and where the answer is
PAGE_ANALYSIS = "Análisis de negocio y sistemas"  # D-377: the BA and BSA work, told as a case
BRAND_GREEN_DARK = "#72e7ad"
BRAND_GREEN_LIGHT = "#167046"
PAGE_DIAGRAMS = "Pipeline y arquitectura"
PAGE_ARCHITECTURE = "Modelo de datos"
PAGE_SEASONALITY = "Contexto del precio"
# D-162: read-only SQL on the gold layer, the destination of «Consultas SQL» in the pipeline.
PAGE_SQL = "Consultas SQL"
PAGE_RULES = "Reglas de transformación"  # D-523: what the pipeline does to the data and why
# D-456: the Analysis in one page, in tabs, like a report of Power BI: the history of the prices first, then
# the four pages it gathers. Their old addresses open their tab. D-457: the history is read two ways that never mix,
# one period month by month and the whole history year by year; the old «Tendencias» opens «Mensual».
PAGE_BA = "Análisis"
BA_MONTHLY_TAB = "Mensual"
BA_HISTORY_TAB = "Histórico"
BA_RETIRED_TABS = {"Tendencias": BA_MONTHLY_TAB}
BA_TAB_OF_VIEW = {
    PAGE_SEASONALITY: "Precios e inflación",
    PAGE_INSIGHTS: "Insights",
    PAGE_STAKEHOLDERS: "Interesados",
    PAGE_ANALYSIS: "Método",
}
BA_TABS = [BA_MONTHLY_TAB, BA_HISTORY_TAB] + list(BA_TAB_OF_VIEW.values())
RETIRED_VIEWS = {
    "Histórico y estacionalidad": "Contexto del precio",
    "Dashboard general": PAGE_HOME,
    "Dónde comprar": PAGE_HOME,  # D-325: the page is gone; its old address opens «Semanal»
    PAGE_CHANNELS: PAGE_HOME,  # D-494: the channels are step 2 of «Semanal»; an old address keeps its «canal»
    "Dashboard": PAGE_HOME,  # D-459: its name until «Semanal»
}
PAGE_KPI = "Indicadores explicados"
PAGE_OPERATIONS = "Monitoreo"
PAGE_ACTIONS = "GitHub Actions"  # D-339: the author's read-only view of the workflow runs
PAGE_CONFIG = "Configuración"  # D-409: the author's console, in place of «Enlaces del autor»
PAGE_RUNS = "Ejecuciones"
# D-420 (the author's decision): the whole «DevOps y seguridad» section is the Autor's: operation and internal security
# are shown only to the administrator profile, and the server checks it before drawing any of them.
AUTHOR_ONLY_PAGES = {PAGE_RUNS, PAGE_ACTIONS, PAGE_CONFIG}
NO_ACCESS = "No tienes acceso a esta página: es solo para el perfil Autor."
PAGE_MANUAL = "Manual"
PAGE_GLOSSARY = "Glosario"
PAGE_LINKS = "Enlaces"
PAGE_DOCUMENTATION = "Documentación"
# The three profile views of «Documentación» (D-110): one per reader, each its own
# sidebar child, folded by default like every other section.
# The documentation is the project's real documents (D-151): requirements,
# architecture and decisions, read from docs/ so the panel shows what GitHub holds.
PAGE_PRD = "PRD · Requisitos del producto"
PAGE_CLOSURE = "Acta de cierre"  # D-529
PAGE_SAD = "SAD · Arquitectura"
PAGE_ADR = "ADR · Decisiones de arquitectura"
# D-201: security has its own section, the attack view and the test plan that backs it.
PAGE_SECURITY = "Mapa de seguridad"
# D-211: the stack in 30 seconds, for a recruiter.
PAGE_STACK = "Stack y evidencia"
# D-282: one folder holds every document; the documents added with it have their own page. D-533: «del proyecto»,
# beside the folder of the study of the source.
PAGE_FOLDER = "Documentos del proyecto"
PAGE_SOURCE_STUDY = "Análisis de la fuente de datos"  # D-533: the two notebooks that study ODEPA's raw file
# D-285: the whole system in one view, next to the stack.
PAGE_APP_MAP = "Mapa de la app"
# D-320: how the project was assessed against software and data quality standards.
PAGE_METHOD = "Plan de calidad"
GIT_TAB_PARAMETER, GIT_TAB_LOG = "pestana", "registro"  # D-346: «Ver registro completo» opens the Incident log
BA_TAB_PARAMETER = GIT_TAB_PARAMETER  # D-456: the tab of «Análisis» an address opens
PAGE_GIT = "Cambios e incidentes"  # D-344: how a change travels from an idea to a live deployment
PAGE_DECISION_INDEX = "Índice de decisiones"
# D-290: the test plan and the security plan are one document; the scalability plan and the data dictionary live in the SAD.
PAGE_TEST_PLAN = "Plan de pruebas y seguridad"
PAGE_QUALITY_PLAN = "SQAP · Plan de calidad del software"  # D-355
# D-318: the views that only old addresses reached left; each address opens the page that now holds its content.
RETIRED_VIEWS.update(
    {
        "Datos": PAGE_HOME,
        "Portada": PAGE_HOME,
        "Definición del proyecto": PAGE_PRD,
        "Esta semana": PAGE_HOME,
        "Brecha de precio": PAGE_SQL,
        "Canales y regiones": PAGE_HOME,
        "Alertas": PAGE_HOME,
        "Reglas de calidad": PAGE_TEST_PLAN,
        "DevOps y seguridad": PAGE_RUNS,
        # D-507: the three pages of «Calidad» say what each one does; an old address opens the same page
        "Método y calidad": PAGE_METHOD,
        "Git workflow": PAGE_GIT,
        "Calidad y auditoría": PAGE_OPERATIONS,
        "Análisis BA y BI": PAGE_BA,  # D-508: the dashboard is «Análisis»
    }
)
RETIRED_VIEWS.update(
    {
        "Plan de pruebas de seguridad": PAGE_TEST_PLAN,
        "Plan de pruebas": PAGE_TEST_PLAN,
        "Escalabilidad": PAGE_SAD,
        "Diccionario de datos": PAGE_SAD,
        "Documentos": PAGE_FOLDER,  # D-533: its name until «Documentos del proyecto»
    }
)
SECTION_RESOURCES = "Enlaces"
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
SECTION_TECHNICAL = "Ingeniería de datos"
SECTION_LINKS = "Documentación"
SECTION_SECURITY = "Seguridad"
WINDOWS = {
    SECTION_PROJECT: [PAGE_STACK, PAGE_APP_MAP, PAGE_METHOD, PAGE_GIT],
    SECTION_KPI: [PAGE_KPI],
    REPORT_WINDOW: [
        PAGE_HOME,
        PAGE_INSIGHTS,
        PAGE_SEASONALITY,
        PAGE_SQL,
        PAGE_STAKEHOLDERS,
        PAGE_ANALYSIS,
        PAGE_BA,
    ],
    SECTION_TECHNICAL: [
        PAGE_DIAGRAMS,
        PAGE_RULES,
        PAGE_ARCHITECTURE,
        PAGE_OPERATIONS,
        PAGE_RUNS,
        PAGE_ACTIONS,
        PAGE_CONFIG,
    ],
    SECTION_SECURITY: [PAGE_SECURITY, PAGE_TEST_PLAN],
    SECTION_LINKS: [
        PAGE_FOLDER,
        PAGE_SOURCE_STUDY,
        PAGE_PRD,
        PAGE_SAD,
        PAGE_ADR,
        PAGE_CLOSURE,
        PAGE_DOCUMENTATION,
        PAGE_GLOSSARY,
        PAGE_MANUAL,
        PAGE_DECISION_INDEX,
        PAGE_QUALITY_PLAN,
    ],
    SECTION_RESOURCES: [PAGE_LINKS],
}
# The SQL and Python consoles left the app (D-143): the code lives in GitHub and the
# answers in the dashboard; their old addresses open the Resumen.
# «Código Python y SQL» left too (D-148): GitHub shows the code; its address opens the GitHub page.
ROUTE = [REPORT_WINDOW, SECTION_TECHNICAL, SECTION_SECURITY, SECTION_LINKS]
# The former KPI page remains as a hidden compatibility destination for old links;
# its business information now lives in the dashboard and documentation.
WINDOWS = {window: WINDOWS[window] for window in ROUTE + [SECTION_PROJECT, SECTION_RESOURCES, SECTION_KPI]}
WINDOW_PATHS = {
    SECTION_PROJECT: "proyecto",
    REPORT_WINDOW: "dashboard",
    SECTION_KPI: "kpis",
    SECTION_TECHNICAL: "arquitectura-y-operacion",
    SECTION_SECURITY: "seguridad",
    SECTION_LINKS: "documentacion-y-enlaces",
    SECTION_RESOURCES: "enlaces",
}
WINDOW_ICONS = {
    SECTION_PROJECT: ":material/assignment:",
    REPORT_WINDOW: ":material/dashboard:",
    SECTION_KPI: ":material/insights:",
    SECTION_TECHNICAL: ":material/account_tree:",
    SECTION_SECURITY: ":material/lock:",
    SECTION_LINKS: ":material/menu_book:",
    SECTION_RESOURCES: ":material/link:",
}
ROUTE_LEADS = {
    SECTION_PROJECT: "qué problema resuelve y qué se construyó",
    SECTION_LINKS: "los requisitos, la arquitectura y las decisiones del proyecto",
    SECTION_KPI: "qué mide cada KPI, cómo se calcula y qué límites tiene",
    REPORT_WINDOW: "los precios y cambios de la semana",
    SECTION_TECHNICAL: "pipeline, modelo estrella, DevOps y operación",
    SECTION_SECURITY: "qué podría intentar un atacante y las pruebas que lo detienen",
}
WINDOW_OF_VIEW = {view: window for window, views in WINDOWS.items() for view in views}
VIEW_PARAMETER = "vista"
# Session flag: the window being drawn is a report (Dashboard), so every view fits one
# screen, like a page of Looker or Power BI (D-067).
COMPACT_VIEW = "compact_view"
# Filters of the whole report (D-069): one bar for every Dashboard view, kept while the
# reader moves with ◀ ▶. The product comes from a click (cross filter or drill-down).
ALL_VALUES = "Todas"
# Dashboard summary (D-072): a slider sets how many rows the ranking shows.
TOP_N_RANGE = (1, 100)
DEFAULT_TOP_N = 20
DASHBOARD_WEEKS = 26
# The groups of views before D-065, kept for the documents that name them.
NAVIGATION_GROUPS = WINDOWS
PAGES = [page for pages in NAVIGATION_GROUPS.values() for page in pages]
HOME_PAGE = PAGE_HOME
PAGE_ICONS = {
    PAGE_DOCUMENTATION: ":material/menu_book:",
    PAGE_PRD: ":material/assignment:",
    PAGE_CLOSURE: ":material/flag:",
    PAGE_SAD: ":material/account_tree:",
    PAGE_ADR: ":material/gavel:",
    PAGE_SQL: ":material/terminal:",
    PAGE_RULES: ":material/rule:",
    PAGE_SECURITY: ":material/lock:",
    PAGE_STACK: ":material/stacks:",
    PAGE_INSIGHTS: ":material/lightbulb:",
    PAGE_STAKEHOLDERS: ":material/groups:",
    PAGE_ANALYSIS: ":material/analytics:",
    PAGE_BA: ":material/query_stats:",
    PAGE_HOME: ":material/dashboard:",
    PAGE_DIAGRAMS: ":material/account_tree:",
    PAGE_ARCHITECTURE: ":material/schema:",
    PAGE_SEASONALITY: ":material/calendar_month:",
    PAGE_KPI: ":material/insights:",
    PAGE_OPERATIONS: ":material/health_and_safety:",
    PAGE_RUNS: ":material/play_circle:",
    PAGE_ACTIONS: ":material/fact_check:",
    PAGE_CONFIG: ":material/settings:",
    PAGE_MANUAL: ":material/menu_book:",
    PAGE_GLOSSARY: ":material/dictionary:",
    PAGE_LINKS: ":material/link:",
    PAGE_FOLDER: ":material/folder_open:",
    PAGE_SOURCE_STUDY: ":material/manage_search:",
    PAGE_DECISION_INDEX: ":material/list_alt:",
    PAGE_APP_MAP: ":material/hub:",
    PAGE_METHOD: ":material/verified:",
    PAGE_GIT: ":material/alt_route:",
    PAGE_TEST_PLAN: ":material/fact_check:",
    PAGE_QUALITY_PLAN: ":material/workspace_premium:",
}
PAGE_PATHS = {
    PAGE_DOCUMENTATION: "documentacion-general",
    PAGE_SECURITY: "mapa-de-seguridad",
    PAGE_STACK: "stack-y-evidencia",
    PAGE_PRD: "prd",
    PAGE_CLOSURE: "acta-de-cierre",
    PAGE_SAD: "sad",
    PAGE_ADR: "adr",
    PAGE_SQL: "consultas-sql",
    PAGE_RULES: "reglas-de-transformacion",
    PAGE_HOME: "dashboard",
    PAGE_INSIGHTS: "insights",
    PAGE_STAKEHOLDERS: "interesados",
    PAGE_ANALYSIS: "analisis-de-negocio-y-sistemas",
    PAGE_BA: "analisis-ba-y-bi",
    PAGE_DIAGRAMS: "diagramas",
    PAGE_ARCHITECTURE: "arquitectura",
    PAGE_SEASONALITY: "estacionalidad",
    PAGE_KPI: "indicadores",
    PAGE_OPERATIONS: "operaciones",
    PAGE_RUNS: "ejecuciones",
    PAGE_ACTIONS: "github-actions",
    PAGE_CONFIG: "configuracion",
    PAGE_MANUAL: "manual",
    PAGE_GLOSSARY: "glosario",
    PAGE_LINKS: "enlaces",
    PAGE_FOLDER: "documentos",
    PAGE_SOURCE_STUDY: "analisis-de-la-fuente",
    PAGE_APP_MAP: "mapa-de-la-app",
    PAGE_DECISION_INDEX: "indice-de-decisiones",
    PAGE_TEST_PLAN: "plan-de-pruebas",
    PAGE_QUALITY_PLAN: "plan-de-calidad",
    PAGE_METHOD: "metodo-y-calidad",
    PAGE_GIT: "git-workflow",
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
    TAB_IDEA: PAGE_PRD,
    TAB_KPI: PAGE_KPI,
    TAB_RULES: PAGE_TEST_PLAN,
    TAB_MANUAL: PAGE_MANUAL,
    TAB_DECISIONS: PAGE_DOCUMENTATION,
    TAB_GLOSSARY: PAGE_GLOSSARY,
    TAB_PIPELINE: PAGE_DIAGRAMS,
    TAB_MODEL: PAGE_ARCHITECTURE,
    TAB_DEVOPS: PAGE_RUNS,
    TAB_CODE: PAGE_LINKS,
    TAB_RUNS: PAGE_RUNS,
    TAB_QUALITY: PAGE_OPERATIONS,
    TAB_WEEK: PAGE_HOME,
    TAB_GAP: PAGE_SQL,
    TAB_CHANNELS: PAGE_HOME,
    TAB_SEASONALITY: PAGE_SEASONALITY,
    TAB_ALERTS: PAGE_HOME,
    TAB_EXPLORER: PAGE_HOME,
    TAB_QUERIES: PAGE_HOME,
}
OLD_PATHS = {
    "inicio": (PAGE_HOME, None),
    "el-proyecto": (PAGE_HOME, None),
    "panel": (PAGE_HOME, None),
    "margenes": (PAGE_SQL, None),
    "canales-y-regiones": (PAGE_HOME, None),
    "consultas": (PAGE_HOME, None),
    "codigo": (PAGE_LINKS, None),
    # The three profile pages became the real documents (D-151).
    "documentacion-bi": (PAGE_PRD, None),
    "documentacion-ba": (PAGE_PRD, None),
    "documentacion-it": (PAGE_SAD, None),
    "pipeline": (PAGE_DIAGRAMS, None),
    # D-290: the documents merged into others.
    "escalabilidad": (PAGE_SAD, None),
    "diccionario-de-datos": (PAGE_SAD, None),
    "plan-de-pruebas-de-seguridad": (PAGE_TEST_PLAN, None),
    "preguntas-y-resultados": (PAGE_HOME, None),
    "analisis-python": (PAGE_HOME, None),
    "queries": (PAGE_HOME, None),
    "python": (PAGE_HOME, None),
    # The retired «Consulta de datos» screen (C03).
    "datos-y-codigo": (PAGE_HOME, None),
    "codigo-y-resultados": (PAGE_HOME, None),
    "detalle-tecnico": (PAGE_DIAGRAMS, None),
    "fuentes-y-enlaces": (PAGE_LINKS, None),
    "centro-de-control": (PAGE_RUNS, None),
    "calidad-de-datos": (PAGE_OPERATIONS, None),
    # Windows and views before the portfolio route (D-070).
    "operacion": (PAGE_OPERATIONS, None),
    "documentacion": (PAGE_DOCUMENTATION, None),
    "decisiones": (PAGE_DOCUMENTATION, None),
    "vista-3d": (PAGE_SEASONALITY, None),
}
OLD_HOME_TABS = {
    "Fuentes y cruces": TAB_IDEA,
    "Arquitectura": TAB_PIPELINE,
    "Modelo de datos": TAB_MODEL,
    "Código": TAB_CODE,
}
OLD_TAB_PAGES = {(PAGE_OPERATIONS, "Enlaces"): PAGE_LINKS}
TAB_PARAMETER = "seccion"
THEME_PARAMETER = "tema"
# The theme of the whole visit: kept in the session and written to the address on every
# run, so every section, link and reload keeps it (D-070).
THEME_STATE = "chosen_theme"
# Retired theme names still open their closest theme (D-071).
RETIRED_THEMES = {
    charts.MODE_LIGHT: charts.MODE_CORPORATE,
    "ChatGPT": charts.MODE_GRAPHITE,
    "Grafito": charts.MODE_GRAPHITE,
}
DEFAULT_THEME = charts.MODE_DARK  # D-349: a visit with no ?tema= opens dark, also the entry window
KPI_PARAMETER = "kpi"
# D-295: two profiles, asked once on entry. «Consulta» (anyone who comes to read prices) sees the business pages;
# «Profesional» (data engineering, business analysis, recruiting) sees the whole project, in the order of a CV.
PROFILE_PARAMETER = "perfil"
PROFILE_STATE = "visitor_profile"
PROFILE_PUBLIC, PROFILE_PROFESSIONAL = "consulta", "profesional"
PROFILES = {
    PROFILE_PUBLIC: ("Vista de usuario", ":material/person:"),
    PROFILE_PROFESSIONAL: ("Vista profesional", ":material/work:"),
}
# D-295: the professional view puts one profile forward; the menu then reads like that portfolio, its sections in
# this order (the sources and the documents stay at the foot of the menu).
ROLE_PARAMETER = "rol"
ROLE_STATE = "visitor_role"
ROLES = {"data": "Data Eng", "ba": "BA", "bi": "BI", "devops": "DevOps", "seguridad": "Seguridad"}
ROLE_ORDER = {
    "data": ["ingenieria", "negocio", "devops", "stack", "calidad"],
    "ba": ["negocio", "stack", "ingenieria", "devops", "calidad"],
    "bi": ["negocio", "ingenieria", "stack", "devops", "calidad"],
    "devops": ["devops", "ingenieria", "negocio", "stack", "calidad"],
    "seguridad": ["stack", "devops", "ingenieria", "negocio", "calidad"],  # D-420: security sits in «Stack y evidencia»
}
DEFAULT_ROLE = "bi"  # a user view unlocked with the key reads the business first
LANDING_STATE = "profile_landing"
# D-502: all the Usuario view has: its two dashboards and the sources. Nothing else, and no door to the rest.
PUBLIC_BLOCKS = {"negocio", "fuentes"}

UNSPECIFIED = "Sin especificar"
SOURCE_NAMES = {etl.SOURCE_WHOLESALE: "Mayorista", etl.SOURCE_CONSUMER: "Consumidor"}
FLAG_NAMES = {
    "SIN_MARCA": "Usados en los indicadores",
    etl.FLAG_UNIT_NOT_CONVERTIBLE: "Unidad no convertible",
    etl.FLAG_OUTLIER: "Atípicos",
}
RUN_HISTORY_COUNT = 8
CHILE_TIME_ZONE = "America/Santiago"
# GitHub allows 60 questions per hour without a key, shared by every app on the
# same server: an answer is kept 5 minutes before asking again.
GITHUB_CACHE_SECONDS = 300
# «Centro de operación» (D-165): while a run is in progress the stage asks GitHub again
# this often; without a token GitHub allows 60 requests an hour, so it waits longer.
LIVE_SECONDS_WITH_TOKEN = 15
LIVE_SECONDS_WITHOUT_TOKEN = 60
OPERATION_RECENT_RUNS = 5
# The database is published only after these steps passed (D-034), so a published load
# proves their state when GitHub does not answer.
STEPS_PROVED_BY_A_SAVED_LOAD = {"Download the ODEPA files", "Run the ETL", "Run the tests against the new database"}
# Seconds between two questions to GitHub while the pipeline runs, and the
# longest wait: a normal run takes about one minute.
PROGRESS_POLL_SECONDS = 4
# Names of the dashboard secrets that enable the "run now" button.
SECRET_GITHUB_TOKEN = "GITHUB_TOKEN"
SECRET_READ_TOKEN = "GITHUB_READ_TOKEN"  # D-339: read-only; D-397: the only one «GitHub Actions» sends
SECRET_CONTROL_CODE = "CONTROL_CODE"
REPORT_PARAMETER = "informe"  # D-333: the quality report a link opens

ARCHITECTURE_HINT = (
    "Los datos viajan de izquierda a derecha. **Bronce**: el archivo tal "
    "como llega. **Limpieza y reglas**: se corrigen formatos y se aplican "
    "las reglas de negocio. **Calidad**: si algo no cuadra, no se guarda "
    "nada. **Oro**: la base lista para analizar. Arriba, quién da las "
    "órdenes; abajo, cómo sabemos qué pasó. El punto de color de cada paso "
    "es su estado real. Pasa el mouse sobre cada pieza para ver qué hace. "
    "**Siglas**: ODEPA, Oficina de Estudios y Políticas Agrarias; CSV, archivo "
    "de valores separados por comas; ETL, extraer, transformar y cargar; RN, "
    "regla de negocio; SQL, lenguaje de consultas; MD, Markdown."
)
# The tables of «DevOps y seguridad» by priority: what protects the data first,
# then what runs the project, how a run is observed and what gets published.
# (heading in docs/PROYECTO.md, sentence, title column, text column, note column)
# Why a row is rejected (RN-11), in the words of validate_rows() in etl/etl.py.
REASON_TEXTS = {
    etl.REASON_UNREADABLE_VALUE: "un precio, una fecha o la región no se pudo leer",
    etl.REASON_NON_POSITIVE_PRICE: "un precio (mínimo, máximo o promedio) es cero o negativo",
    etl.REASON_MINIMUM_ABOVE_MAXIMUM: "el precio mínimo es mayor que el máximo",
    etl.REASON_DATE_OUTSIDE_FILE_YEAR: "la fecha no cae en el año del archivo",
    etl.REASON_NON_POSITIVE_VOLUME: "una fila mayorista sin volumen no puede entrar al promedio ponderado (RN-07)",
}
# Short Spanish name of each rejection reason, for the tables (D-141).
REASON_NAMES = {
    etl.REASON_UNREADABLE_VALUE: "Valor ilegible",
    etl.REASON_NON_POSITIVE_PRICE: "Precio cero o negativo",
    etl.REASON_MINIMUM_ABOVE_MAXIMUM: "Mínimo mayor que máximo",
    etl.REASON_DATE_OUTSIDE_FILE_YEAR: "Fecha fuera del año del archivo",
    etl.REASON_NON_POSITIVE_VOLUME: "Sin volumen",
}
# The fields of a rejected row worth reading, as ODEPA sent them, in Spanish.
REJECTED_ROW_LABELS = {
    "price_date": "Fecha",
    "week_start": "Semana",
    "region": "Región",
    "market": "Mercado",
    "channel": "Canal",
    "product": "Producto",
    "variety": "Variedad",
    "quality": "Calidad",
    "sale_unit": "Unidad de venta",
    "unit": "Unidad",
    "volume": "Volumen",
    "min_price": "Precio mínimo",
    "max_price": "Precio máximo",
    "avg_price": "Precio promedio",
}
NO_DATA_TEXT = "No hay datos para esta selección."
# Alertas: (lowest distance in standard deviations, label, icon, status color).
ALERT_LEVELS = [
    (4, "Alza extrema", "◆", "critical"),
    (3, "Alza muy fuerte", "▲", "serious"),
    (0, "Alza fuerte", "●", "warning"),
]
# D-477: a sharp drop is good news for the buyer, not a danger: its own words and its own colour, green.
DROP_LEVELS = [(4, "Baja extrema", "◆", "good"), (3, "Baja muy fuerte", "▼", "good"), (0, "Baja fuerte", "●", "good")]
RISE, DROP = "alza", "baja"
# (one, many) of each kind, the official names approved by the author (D-477).
ALERT_KINDS = {RISE: ("alza fuerte", "alzas fuertes"), DROP: ("baja fuerte", "bajas fuertes")}
# Contexto: nominal prices or real prices deflated with the INE IPC (D-155).
CONTEXT_BASIS_KEY = "context_price_basis"
BASIS_NOMINAL, BASIS_REAL = "Precios del día", "Sin inflación"
BASIS_HELP = (
    "Precios del día: el índice con los precios pagados. Sin inflación (IPC): el índice de la familia dividido por "
    "el IPC de alimentos del INE, por 100; sobre 100, la familia subió más que los alimentos en general."
)
# The switch of Pipeline y linaje: the whole journey first, its dbt stretch on demand.
PIPELINE_VIEW_KEY = "pipeline_view"
PIPELINE_JOURNEY, PIPELINE_LINEAGE = "Recorrido por capas", "Linaje dbt"
LINEAGE_HINT = (
    "Se dibuja con el manifiesto de la última construcción de dbt, que el pipeline guarda en la "
    "base: si se agrega un modelo o una prueba, aparece aquí en la carga siguiente."
)
ATTRIBUTION_TEXT = (
    "Datos: Oficina de Estudios y Políticas Agrarias (ODEPA), Ministerio de "
    "Agricultura de Chile, licencia Creative Commons Atribución; IPC de alimentos: Instituto "
    "Nacional de Estadísticas (INE). Este proyecto no es un producto oficial de ODEPA ni del INE. "
    "Lectura de los datos: el precio nacional es un promedio simple de las regiones, sin ponderar "
    "por población o ventas; cada variación semanal compara las mismas regiones y el mismo envase en ambas semanas. "
    "Los indicadores describen el histórico; no predicen precios. Los precios se reconstruyen "
    "desde la fuente en las pruebas automáticas."
)


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


HOME_LINK_PARAMETERS = ("_home_region", "_home_week", "familia", "alerta", "canal")  # D-489 alerts; D-494 channel


# D-352: the reading order of the Dashboard. A map or «Todo Chile» click completes step 1, a family click step 2; for the
# user view the panels 2 and 3 stay locked until the step before them is done, and a step done is never locked again.
HOME_STEP_PARAMETER = "_home_step"


HOME_REGION_DONE, HOME_FAMILY_DONE, HOME_FLASH = "home_region_done", "home_family_done", "home_flash"


HOME_SEARCHED = "home_searched"  # D-372


RUN_WINDOW_OPEN = "run_window_open"


ADMIN_UNLOCKED = "admin_unlocked"


# D-282: the folder, in reading order, with the family that colors each file.
# D-381: grouped by the four folders of docs/, each document in the folder of its subject.
FOLDER_DOCUMENTS = [
    (PAGE_PRD, "negocio"),
    (PAGE_CLOSURE, "negocio"),
    (PAGE_GLOSSARY, "negocio"),
    (PAGE_SAD, "arquitectura"),
    (PAGE_ADR, "arquitectura"),
    (PAGE_DECISION_INDEX, "arquitectura"),
    (PAGE_QUALITY_PLAN, "calidad"),
    (PAGE_TEST_PLAN, "calidad"),
    (PAGE_MANUAL, "operacion"),
]


FOLDER_ORDER = [page for page, _ in FOLDER_DOCUMENTS]


# D-536: four documents are annexes. They stay in docs/, the panel and the tests still read them, and their pages open
# from the links of the other documents; the folder lists only the five main ones.
FOLDER_ANNEXES = (PAGE_GLOSSARY, PAGE_ADR, PAGE_DECISION_INDEX, PAGE_TEST_PLAN)


FOLDER_SHOWN = [page for page in FOLDER_ORDER if page not in FOLDER_ANNEXES]


RETURN_CONTEXT_KEYS = [
    "dashboard_group",
    "dashboard_region",
    "dashboard_week",
    "dashboard_product",
    "dashboard_top_n",
    "analysis_group",
    "analysis_product",
    "analysis_key_label",
    "analysis_region",
    "analysis_channels",
]


PAGE_HISTORY = "page_history"


RETURN_TARGET = "return_target"


HISTORY_LIMIT = 30


# Besides its address, a page is its report filters and the Dashboard's steps (each channel keeps its own, «key@canal»).
HISTORY_STATE_KEYS = {*RETURN_CONTEXT_KEYS, HOME_REGION_DONE, HOME_FAMILY_DONE, HOME_SEARCHED}


# D-213: one section per kind of reader, open by default; each page lives in exactly one section.
# D-231: a flat menu, like the sidebar of a chat app: no cards, borders, shadows or gradients;
# small grey headings, a hairline between sections, a thin icon per page, and the current page
# with a faint fill and a blue bar on its left. The documents close the list, before the sources.
# (key, title, pages or source links)
MENU_BLOCKS = [
    (
        "negocio",
        "Negocio · BA y BI",
        # D-453: the section opens with its dashboards as tiles; D-456: «Análisis» gathers in its tabs the history
        # of the prices and the former pages «Precios e inflación», «Insights» and «Interesados», with the method.
        # D-494: «Último dato por canal» became step 2 of «Semanal»: the section is two dashboards.
        [PAGE_HOME, PAGE_BA],
    ),
    ("ingenieria", "Ingeniería de datos", [PAGE_DIAGRAMS, PAGE_RULES, PAGE_ARCHITECTURE, PAGE_SQL]),
    ("devops", "DevOps y seguridad", [PAGE_RUNS, PAGE_ACTIONS, PAGE_CONFIG]),  # D-420: the Autor's only
    ("stack", "Stack y evidencia", [PAGE_STACK, PAGE_APP_MAP, PAGE_SECURITY]),  # D-420: security, for the Profesional
    (
        "calidad",
        "Calidad",
        [PAGE_METHOD, PAGE_OPERATIONS, PAGE_GIT],  # D-507: the plan, the controls, the log
    ),  # D-343: quality and audit, and the method behind it
    ("fuentes", "Fuentes de datos", SOURCE_LINKS),
    ("documentos", "Documentos", [PAGE_FOLDER, PAGE_SOURCE_STUDY]),  # D-533: two folders
]


# D-308: a page that opens from a button of another page and has no line of its own in the menu.
DOOR_PAGES: dict[str, str] = {}  # D-398: «Precios e inflación», the only one, joined the menu


MENU_BLOCK_OF_VIEW = {view: title for _, title, pages in MENU_BLOCKS if pages is not SOURCE_LINKS for view in pages}


SIDEBAR_TOP_LABELS = {
    REPORT_WINDOW: "Dashboards",
    SECTION_TECHNICAL: "Ingeniería de datos",
    SECTION_PROJECT: "Proyecto",
    SECTION_LINKS: "Documentación",
    SECTION_SECURITY: "Seguridad",
    SECTION_RESOURCES: "GitHub",
}


SIDEBAR_LABELS = {
    PAGE_INSIGHTS: "Insights",
    PAGE_HOME: "Semanal",
    PAGE_SEASONALITY: "Precios e inflación",
    PAGE_DIAGRAMS: "Pipeline y linaje",
    PAGE_OPERATIONS: "Controles de datos",
    PAGE_RUNS: "Centro de operación",
    PAGE_ACTIONS: "GitHub Actions",
    PAGE_CONFIG: "Configuración",
    PAGE_SECURITY: "Arquitectura de seguridad",
    PAGE_DOCUMENTATION: "Documentación",
    PAGE_MANUAL: "Manual de operación",
}


FOLDER_TILES = [PAGE_FOLDER, PAGE_SOURCE_STUDY]  # D-533: the project's documents, then the study of the source
# endregion

# region Variables
MANIFEST_FILE = Path(__file__).resolve().parent.parent / "agent" / "downloads" / "manifest.json"
# endregion
