"""What each technology named in the diagrams is, and what it does in this project.

One entry per tool, format, layer or acronym that a diagram shows as a logo, a pill,
a chip or a label. bi/architecture.py, bi/devops.py and bi/lineage.py put
describe(key) in an SVG <title>, so the browser shows it on hover. Every role below
was checked against the code (agent/, etl/, dbt/, bi/, .github/workflows/).
"""

# region Glossary
TECH_GLOSSARY = {
    # Languages and libraries
    "python": {
        "nombre": "Python", "sigla": "",
        "que_es": "lenguaje de programación de uso general.",
        "rol": "escribe todo el proyecto: la ingesta (agent/agent.py, etl/ine.py), el ETL "
               "(etl/etl.py, etl/pipeline.py) y el panel. Corre en Python 3.11 en GitHub Actions."},
    "requests": {
        "nombre": "requests", "sigla": "",
        "que_es": "biblioteca de Python para hacer solicitudes web.",
        "rol": "descarga por HTTPS los CSV de ODEPA (agent/agent.py, con reintentos) y del IPC "
               "del INE (etl/ine.py)."},
    "pandas": {
        "nombre": "pandas", "sigla": "",
        "que_es": "biblioteca de Python para tablas en memoria (DataFrames).",
        "rol": "recibe el resultado de las consultas a DuckDB que el panel convierte en "
               "tablas y gráficos."},
    "pyarrow": {
        "nombre": "pyarrow", "sigla": "",
        "que_es": "biblioteca de Python de Apache Arrow, que lee y escribe Parquet.",
        "rol": "escribe la capa bronce en Parquet: etl/bronze.py copia raw.db y etl/ine.py "
               "guarda el IPC, todo como texto."},
    "sql": {
        "nombre": "SQL", "sigla": "Structured Query Language",
        "que_es": "lenguaje de consultas estructurado, para leer y transformar tablas.",
        "rol": "los modelos dbt (dbt/models/*.sql) y las consultas del panel (bi/queries.sql) "
               "están escritos en SQL y los ejecuta DuckDB."},
    # Storage and formats
    "sqlite": {
        "nombre": "SQLite", "sigla": "",
        "que_es": "base de datos relacional embebida en un solo archivo.",
        "rol": "zona de aterrizaje raw.db (los CSV de ODEPA tal como llegan) y el respaldo "
               "datos.db que aún escribe etl/etl.py."},
    "duckdb": {
        "nombre": "DuckDB", "sigla": "",
        "que_es": "base de datos analítica en columnas, embebida en un archivo.",
        "rol": "el data warehouse que sirve al panel (datos.duckdb), leído en solo lectura; "
               "dbt construye antes en una base de trabajo aparte."},
    "parquet": {
        "nombre": "Parquet", "sigla": "",
        "que_es": "formato de archivo en columnas de Apache, estándar en data lakes.",
        "rol": "formato de la capa bronce: un archivo por fuente y año de ODEPA y por archivo "
               "del INE, que dbt lee como fuentes."},
    "csv": {
        "nombre": "CSV", "sigla": "Comma-Separated Values",
        "que_es": "archivo de texto con valores separados por comas (o punto y coma).",
        "rol": "el formato en que ODEPA y el INE publican sus datos; la ingesta los descarga "
               "tal cual."},
    "markdown": {
        "nombre": "Markdown", "sigla": "MD",
        "que_es": "formato de texto plano con marcas simples para títulos, listas y tablas.",
        "rol": "bi/report.py escribe el informe semanal en Markdown (report.md), que se "
               "publica como issue de GitHub."},
    "yaml": {
        "nombre": "YAML", "sigla": "YAML Ain't Markup Language",
        "que_es": "formato de texto para archivos de configuración.",
        "rol": "define los workflows (semanal.yml, pruebas.yml) y la configuración dbt "
               "(dbt_project.yml, sources.yml, schema.yml)."},
    # Transformation
    "dbt": {
        "nombre": "dbt", "sigla": "data build tool",
        "que_es": "herramienta que construye modelos SQL en orden de dependencias y los prueba.",
        "rol": "dbt Core con dbt-duckdb transforma bronce en staging, intermedio y marts; "
               "etl/pipeline.py corre dbt build y solo publica si todo pasa."},
    "dbt_build": {
        "nombre": "dbt build", "sigla": "",
        "que_es": "comando de dbt que construye cada modelo y corre sus pruebas.",
        "rol": "«OK» significa que todos los modelos y pruebas pasaron en la base de trabajo; "
               "solo entonces etl/pipeline.py reemplaza datos.duckdb."},
    "etl": {
        "nombre": "ETL", "sigla": "Extract, Transform, Load",
        "que_es": "extraer, transformar y cargar: el proceso que lleva datos de la fuente a "
                  "una base lista para analizar.",
        "rol": "bronce en Parquet más los modelos dbt con sus pruebas "
               "(etl/pipeline.py), y el respaldo SQLite de etl/etl.py."},
    # Layers and models
    "bronze": {
        "nombre": "Bronze (bronce)", "sigla": "",
        "que_es": "primera capa de la arquitectura medallón (bronze → silver → gold): los "
                  "datos crudos, sin limpiar.",
        "rol": "copia exacta en Parquet, todas las columnas como texto (etl/bronze.py y "
               "etl/ine.py); dbt la lee como fuentes."},
    "silver": {
        "nombre": "Silver (plata)", "sigla": "",
        "que_es": "capa media de la arquitectura medallón: datos limpios, tipados y validados.",
        "rol": "los modelos dbt de staging (tipos y textos) e intermedios: validan y apartan "
               "las filas inválidas, llevan a kilo, unidad o litro, agrupan por semana y "
               "marcan los precios atípicos."},
    "gold": {
        "nombre": "Gold (oro)", "sigla": "",
        "que_es": "capa final de la arquitectura medallón: datos listos para el consumo.",
        "rol": "los marts de dbt (el modelo estrella, rejection y las tablas del IPC), copiados "
               "a datos.duckdb, que leen el panel, el informe y las consultas SQL."},
    "manifest": {
        "nombre": "manifest.json", "sigla": "",
        "que_es": "registro en JSON de los archivos descargados.",
        "rol": "agent/downloads/manifest.json guarda el hash SHA-256 de cada CSV de ODEPA para "
               "saber si cambió; el workflow semanal lo guarda en el repositorio."},
    "raw": {
        "nombre": "raw_*", "sigla": "",
        "que_es": "tablas crudas de la zona de aterrizaje.",
        "rol": "raw_wholesale y raw_consumer de raw.db (SQLite): las filas de ODEPA tal como "
               "llegan, que etl/bronze.py copia a Parquet."},
    "ine_ipc": {
        "nombre": "ine_ipc", "sigla": "",
        "que_es": "tabla bronce del IPC del INE en Parquet.",
        "rol": "etl/ine.py la escribe directo en bronze/ine_ipc, sin pasar por raw.db; la lee "
               "el modelo stg_ine__ipc_monthly."},
    "sources": {
        "nombre": "sources.yml", "sigla": "",
        "que_es": "declaración de las fuentes de un proyecto dbt.",
        "rol": "apunta dbt a los Parquet de bronce (odepa_wholesale, odepa_consumer, "
               "ine_ipc) con read_parquet."},
    "stg": {
        "nombre": "Staging (stg_*)", "sigla": "",
        "que_es": "capa dbt que limpia cada fuente por separado.",
        "rol": "stg_odepa__wholesale, stg_odepa__consumer y stg_ine__ipc_monthly convierten "
               "tipos y normalizan textos; se materializan como vistas."},
    "int": {
        "nombre": "Intermedio (int_*)", "sigla": "",
        "que_es": "capa dbt donde se aplican las reglas de negocio.",
        "rol": "int_prices__validated, __units_normalized, __weekly y __outlier_flagged validan, "
               "llevan a kilo o unidad, agrupan por semana y marcan atípicos; son tablas."},
    "marts": {
        "nombre": "Marts", "sigla": "",
        "que_es": "capa final de un data warehouse, lista para el consumo.",
        "rol": "el modelo estrella (dim_* y weekly_price), rejection y el IPC mensual y "
               "semanal: tablas que se copian a datos.duckdb."},
    "view": {
        "nombre": "Vista", "sigla": "",
        "que_es": "consulta guardada con nombre: no almacena filas, se calcula al leerla.",
        "rol": "materialización de los modelos de staging (dbt_project.yml)."},
    "table": {
        "nombre": "Tabla", "sigla": "",
        "que_es": "modelo materializado: dbt guarda sus filas en la base.",
        "rol": "materialización de los modelos intermedios y de los marts (dbt_project.yml)."},
    "etl_run": {
        "nombre": "etl_run", "sigla": "",
        "que_es": "tabla de control con una fila por carga.",
        "rol": "etl/pipeline.py registra en datos.duckdb cada ejecución, también las fallidas; "
               "el centro de control la muestra."},
    "dbt_result": {
        "nombre": "dbt_node y dbt_result", "sigla": "",
        "que_es": "tablas con el manifest y los resultados del último dbt build.",
        "rol": "etl/pipeline.py las copia a datos.duckdb; de ellas sale el linaje dbt y el "
               "estado de cada prueba."},
    # Platforms and operations
    "streamlit": {
        "nombre": "Streamlit", "sigla": "",
        "que_es": "framework de Python para aplicaciones web de datos.",
        "rol": "este panel (bi/dashboard.py), publicado en Streamlit Community Cloud; abre "
               "datos.duckdb en solo lectura."},
    "streamlit_cloud": {
        "nombre": "Streamlit Community Cloud", "sigla": "",
        "que_es": "servicio que publica aplicaciones Streamlit desde un repositorio de GitHub.",
        "rol": "publica el panel y lo vuelve a desplegar cada vez que cambia la rama main."},
    "git": {
        "nombre": "Git", "sigla": "",
        "que_es": "sistema de control de versiones.",
        "rol": "versiona el código; el workflow semanal hace checkout, commit y push de "
               "datos.duckdb, datos.db y manifest.json."},
    "github": {
        "nombre": "GitHub", "sigla": "",
        "que_es": "plataforma que aloja repositorios Git.",
        "rol": "aloja el repositorio (rama main), ejecuta los workflows y publica el informe "
               "semanal como issue."},
    "github_cli": {
        "nombre": "GitHub CLI", "sigla": "CLI: Command-Line Interface",
        "que_es": "comando gh, interfaz de línea de comandos de GitHub.",
        "rol": "gh issue create publica el informe semanal como issue al final del workflow "
               "semanal."},
    "github_actions": {
        "nombre": "GitHub Actions", "sigla": "",
        "que_es": "servicio de GitHub que ejecuta workflows en máquinas Ubuntu temporales.",
        "rol": "semanal.yml corre cada martes a las 12:00 UTC (o a mano) y pruebas.yml en cada "
               "push y pull request."},
    "github_issues": {
        "nombre": "GitHub Issues", "sigla": "",
        "que_es": "registro de temas de un repositorio de GitHub.",
        "rol": "cada ejecución semanal publica ahí su informe: estado de la carga y alertas."},
    "actions_cache": {
        "nombre": "Caché de Actions", "sigla": "",
        "que_es": "almacenamiento de GitHub Actions para reutilizar archivos entre ejecuciones.",
        "rol": "actions/cache guarda los CSV de los años cerrados para no descargarlos cada "
               "semana (D-047)."},
    "secrets": {
        "nombre": "Secretos", "sigla": "",
        "que_es": "valores confidenciales guardados fuera del código.",
        "rol": "el panel lee con st.secrets el token de GitHub y la clave del botón «Ejecutar "
               "ahora»; el workflow usa el token propio de GitHub Actions."},
    "ci": {
        "nombre": "CI", "sigla": "Continuous Integration",
        "que_es": "integración continua: probar automáticamente cada cambio del código.",
        "rol": "pruebas.yml corre dbt parse y pytest en cada push y pull request."},
    "cd": {
        "nombre": "CD", "sigla": "Continuous Delivery",
        "que_es": "entrega continua: llevar a producción, sin pasos manuales, lo que ya pasó todas las pruebas.",
        "rol": "semanal.yml construye la carga cada martes y, solo si pytest pasa sobre la base nueva, la guarda "
               "en main con un commit; el panel se publica desde main."},
    "pytest": {
        "nombre": "pytest", "sigla": "",
        "que_es": "framework de pruebas automáticas para Python.",
        "rol": "corre las pruebas de tests/ en cada push y, en el workflow semanal, contra la "
               "base nueva: si falla, no se guarda nada."},
    "https": {
        "nombre": "HTTPS", "sigla": "Hypertext Transfer Protocol Secure",
        "que_es": "protocolo web cifrado.",
        "rol": "la ingesta descarga por HTTPS los CSV de ODEPA y del INE, y los visitantes "
               "abren el panel por HTTPS."},
    "api": {
        "nombre": "API", "sigla": "Application Programming Interface",
        "que_es": "interfaz para que un programa pida datos a otro.",
        "rol": "ODEPA y el INE no ofrecen una API en el flujo usado: se descargan CSV. El panel "
               "sí usa la API REST de GitHub para el botón «Ejecutar ahora» (bi/control.py)."},
    # Sources
    "odepa": {
        "nombre": "ODEPA", "sigla": "Oficina de Estudios y Políticas Agrarias",
        "que_es": "servicio del Ministerio de Agricultura de Chile.",
        "rol": "publica en datos abiertos los precios mayoristas diarios y al consumidor "
               "semanales, un CSV por año y fuente."},
    "ine": {
        "nombre": "INE", "sigla": "Instituto Nacional de Estadísticas",
        "que_es": "organismo oficial de estadísticas de Chile.",
        "rol": "publica el IPC; etl/ine.py descarga dos de sus CSV para expresar los precios "
               "en pesos reales (D-155)."},
    "ipc": {
        "nombre": "IPC", "sigla": "Índice de Precios al Consumidor",
        "que_es": "indicador oficial de la inflación.",
        "rol": "se usa la división «Alimentos y bebidas no alcohólicas», mensual; los marts "
               "ipc_monthly e ipc_weekly dan el deflactor de cada semana."},
}

# The pills of bi/architecture.TECH whose glossary key differs from their own id.
TECH_KEYS = {"github": "github_cli"}
# The chips on the links of bi/architecture: chip text -> glossary key. A chip not
# listed here keeps its own explanation (architecture.CHIP_TOOLTIPS).
CHIP_KEYS = {
    "CSV": "csv", "manifest": "manifest", "raw_*": "raw", "ine_ipc": "ine_ipc",
    "sources": "sources", "stg_*": "stg", "int_*": "int", "OK": "dbt_build", "SQL": "sql", "consultas": "sql",
    "MD": "markdown", "HTTPS": "https", "git push": "git", "checkout · commit": "git",
    "cache": "actions_cache", "gh issue create": "github_cli", "on: push": "ci",
    "st.secrets": "secrets", "despliegue de main": "streamlit_cloud",
}
# Items of the bands and other labelled pieces: label -> glossary key.
LABEL_KEYS = {
    "GitHub Actions": "github_actions", "Secretos": "secrets", "etl_run": "etl_run",
    "dbt_result": "dbt_result", "Pruebas automáticas": "pytest", "etl/pipeline.py": "etl",
    "GITHUB": "github", "STREAMLIT COMMUNITY CLOUD": "streamlit_cloud",
    "BRONZE": "bronze", "SILVER": "silver", "GOLD": "gold",
}
# Brand logos (bi/assets/logos) -> glossary key.
LOGO_KEYS = {
    "python": "python", "sqlite": "sqlite", "duckdb": "duckdb", "dbt": "dbt",
    "apacheparquet": "parquet", "streamlit": "streamlit", "github": "github", "git": "git",
    "pytest": "pytest",
}
# Words of the column subtitles («HTTPS · CSV · sin API») -> glossary key.
WORD_KEYS = {
    "HTTPS": "https", "CSV": "csv", "API": "api", "Python": "python", "requests": "requests",
    "SQLite": "sqlite", "Parquet": "parquet", "dbt": "dbt", "DuckDB": "duckdb",
    "Streamlit": "streamlit", "GitHub": "github", "SQL": "sql",
}
# endregion


# region Text
def describe(key):
    """One plain-text line for an SVG <title>: what it is, its acronym, its role here."""
    entry = TECH_GLOSSARY[key]
    name = entry["nombre"] + (f" ({entry['sigla']})" if entry["sigla"] else "")
    return f"{name} — {entry['que_es']} Aquí: {entry['rol']}"


def describe_words(text):
    """The entries of every known technology named in a «A · B · C» label, one per line."""
    keys = []
    for word in text.replace("·", " ").split():
        key = WORD_KEYS.get(word)
        if key and key not in keys:
            keys.append(key)
    return "\n".join(describe(key) for key in keys)
# endregion
