"""«Mapa de la app» (D-285): the whole system in one interactive view that explains itself.

Left to right, the layers the data goes through: the sources, the ingestion, the landing, the bronze layer, the dbt
transformation, the data warehouse, the publication, the panel and its readers. Above, the orchestration; below the
flow, the browser layer; at the bottom, what watches the system (quality, parity, security, observability, documents
and measurement) and the AI support tool, which is not part of the data flow.

Every technology is a node with its logo. On hover: what it is, its role in GreenOcean, when it acts and what it
connects with; that last list is read from the connections of the drawing, so the text and the lines never disagree.
Small technologies live inside the node of their function, so nothing the project uses is left out. A click opens the
page of the panel where the node is at work.

The nodes are HTML, so the text never shrinks; one script draws the lines between them. Without a filter only the data
flow is drawn; each line carries its own themes, so a filter draws every line of its theme with its label and lights
every node those lines join (D-291): security, for instance, is the author, the panel and its secrets, GitHub Actions,
the repository, the read-only database, the visitor's SQL and the tests that attack them. The cursor on a node draws its
own lines. Pure functions: no Streamlit.
"""

import base64
import html
import json

from bi import brand_icons, database_map, doc_views

# The themes of the filters, in the order of the buttons.
THEMES = [
    ("datos", "Datos"),
    ("orquestacion", "Orquestación"),
    ("calidad", "Calidad"),
    ("seguridad", "Seguridad"),
    ("observabilidad", "Observabilidad"),
    ("navegador", "Navegador"),
    ("apoyo", "Apoyo"),
]
# The columns of the flow, left to right.
LAYERS = [
    "Fuentes",
    "Ingesta",
    "Aterrizaje",
    "Bronce",
    "Transformación",
    "Data warehouse",
    "Publicación",
    "Panel",
    "Lectores",
]
# The kinds of line: (key, label).
LINE_KINDS = [("flow", "datos"), ("order", "órdenes"), ("check", "controles"), ("support", "apoyo")]
# key: (name, logo, themes, (row, column), what it is, role in GreenOcean, when it acts, page, [(small tool, what)]).
# A logo is «brand:<slug>», «source:<key>», «person:<key>» or «icon:<name>». Rows: «top» (orchestration), «flow»,
# «flow2» (a second node in a column of the flow), «web» (the browser layer) and «watch» (what watches the system).
NODES = {
    "odepa": (
        "ODEPA",
        "source:odepa",
        ["datos"],
        ("flow", 1),
        "Oficina de Estudios y Políticas Agrarias del Ministerio de Agricultura de Chile.",
        "Publica cada semana los CSV de precios mayoristas y al consumidor: la fuente de todos los precios.",
        "Publica cada semana; la carga descarga cada martes.",
        "Dashboard",
        [],
    ),
    "ine": (
        "INE",
        "source:ine",
        ["datos"],
        ("flow2", 1),
        "Instituto Nacional de Estadísticas de Chile.",
        "Publica el IPC de alimentos, con el que los precios se expresan en pesos de hoy.",
        "Publica cada mes; la carga descarga cada martes.",
        "Contexto del precio",
        [],
    ),
    "agent": (
        "Agente de ingesta",
        "brand:python",
        ["datos"],
        ("flow", 2),
        "Programa en Python que descarga los archivos de las fuentes.",
        "agent/agent.py descarga los CSV de ODEPA, revisa su encabezado y anota su huella; etl/ine.py descarga "
        "el IPC y lo escribe directo en bronce.",
        "Cada martes, al comienzo de la carga.",
        "Pipeline y arquitectura",
        [
            ("requests", "biblioteca de Python que descarga por HTTPS, con reintentos."),
            (
                "certifi y la raíz emSign",
                "certificados que verifican la conexión con ODEPA; la raíz emSign viaja "
                "con el agente desde que certifi la retiró (D-164).",
            ),
            ("hashlib · SHA-256", "calcula la huella de cada archivo y la guarda en manifest.json."),
            ("etl/ine.py", "descarga las dos series del IPC del INE."),
        ],
    ),
    "sqlite": (
        "SQLite",
        "brand:sqlite",
        ["datos", "calidad"],
        ("flow", 3),
        "Base de datos relacional en un solo archivo, sin servidor.",
        "etl/raw.db guarda las filas de ODEPA tal como llegan; etl/datos.db es el respaldo que calcula el ETL "
        "en Python (etl/etl.py), para comprobar la paridad con DuckDB.",
        "Cada martes, justo después de la descarga.",
        "Modelo de datos",
        [("etl/etl.py", "el ETL en Python que escribe el respaldo, por un camino independiente de dbt.")],
    ),
    "parquet": (
        "Parquet",
        "brand:apacheparquet",
        ["datos"],
        ("flow", 4),
        "Formato abierto de archivos por columnas, comprimido.",
        "etl/bronze/ guarda la copia literal de cada fuente, un archivo por fuente y año, con todas las "
        "columnas como texto.",
        "Cada martes, antes de dbt.",
        "Modelo de datos",
        [("pyarrow", "biblioteca de Apache Arrow que escribe los archivos Parquet (etl/bronze.py).")],
    ),
    "dbt": (
        "dbt Core",
        "brand:dbt",
        ["datos", "calidad"],
        ("flow", 5),
        "Herramienta que construye modelos SQL en orden de dependencias y los prueba.",
        "Lee el bronce y construye staging, intermedio y marts; corre sus pruebas de datos y, si una falla, la "
        "carga se detiene y la base publicada no cambia.",
        "Cada martes con dbt build; en cada push solo se compila (dbt parse).",
        "Pipeline y arquitectura",
        [
            ("dbt-duckdb", "el adaptador que hace correr dbt sobre DuckDB."),
            (
                "staging · intermedio · marts",
                "las tres capas de modelos: tipos, reglas de negocio y el modelo estrella.",
            ),
            ("pruebas de datos", "claves únicas, valores aceptados, relaciones y conciliación de filas."),
        ],
    ),
    "duckdb": (
        "DuckDB",
        "brand:duckdb",
        ["datos"],
        ("flow", 6),
        "Base de datos analítica por columnas, en un solo archivo y sin servidor.",
        "Motor donde dbt construye el data warehouse y base servida etl/datos.duckdb, que el panel lee en solo "
        "lectura.",
        "Cada martes; la base servida se reemplaza solo al final de una carga válida.",
        "Modelo de datos",
        [
            ("SQL", "el lenguaje de los modelos, de las consultas del panel (bi/queries.sql) y del estudio SQL."),
            ("pandas", "recibe el resultado de cada consulta que el panel convierte en tabla o gráfico."),
        ],
    ),
    "release": (
        "Release «base-actual»",
        "brand:github",
        ["datos", "orquestacion"],
        ("flow", 7),
        "Archivo publicado en GitHub, fuera del historial de Git.",
        "Guarda una sola copia de la base servida, reemplazada por cada carga; en main queda su puntero "
        "etl/datos.version, con la huella, el tamaño y la fecha (D-270).",
        "Al final de cada carga que pasó todas las pruebas.",
        "Ejecuciones",
        [("bi/served_database.py", "descarga la base del release y la usa solo si su huella coincide.")],
    ),
    "streamlit": (
        "Streamlit",
        "brand:streamlit",
        ["datos"],
        ("flow", 8),
        "Framework de Python para aplicaciones web de datos.",
        "Dibuja este panel con la base servida en solo lectura y lo publica en Streamlit Community Cloud "
        "desde la rama main.",
        "Cada vez que alguien abre una página.",
        "Dashboard",
        [
            (
                "Páginas",
                "Panorama de precios, Insights, Precios e inflación, Pipeline y linaje, Modelo de datos, Calidad y "
                "auditoría, Consultas SQL, Centro de operación, Arquitectura de seguridad, Stack y evidencia, "
                "Mapa de la app y la carpeta de documentos.",
            ),
            ("Streamlit Community Cloud", "el servicio gratuito que publica el panel y guarda sus secretos."),
        ],
    ),
    "visitor": (
        "Visitante",
        "person:visitor",
        ["datos"],
        ("flow", 9),
        "Cualquier persona con el enlace público.",
        "Lee el panel y usa el estudio SQL sin cuenta: los datos son públicos.",
        "Cuando abre el panel.",
        "Dashboard",
        [],
    ),
    "author": (
        "Autor",
        "person:author",
        ["seguridad", "orquestacion"],
        ("flow2", 9),
        "Quien mantiene el proyecto.",
        "Mantiene el código y los secretos; con la clave de control puede lanzar la carga desde el panel.",
        "Cuando cambia el código o lanza una carga manual.",
        "Ejecuciones",
        [
            ("clave de control", "la escribe en «Acceso del autor» para abrir el botón «Ejecutar pipeline ahora»."),
            (
                "verificación en dos pasos",
                "en sus cuentas de GitHub y de Streamlit; declarada por el autor, no verificable desde el repositorio.",
            ),
        ],
    ),
    "secrets": (
        "Secretos del panel",
        "icon:key",
        ["seguridad"],
        ("flow2", 7),
        "Los dos secretos del panel, guardados en Streamlit Community Cloud y nunca en el repositorio.",
        "CONTROL_CODE abre el acceso del autor; GITHUB_TOKEN, con permisos mínimos, deja al panel lanzar la "
        "carga y leer el estado de las ejecuciones. Ninguno aparece en pantalla ni en los mensajes de error.",
        "Cuando el autor escribe la clave y cuando el panel consulta GitHub.",
        "Mapa de seguridad",
        [
            ("CONTROL_CODE", "la clave de control del autor."),
            ("hmac.compare_digest", "compara la clave en tiempo constante."),
            (
                "GITHUB_TOKEN",
                "token para lanzar el workflow y leer sus ejecuciones; el panel avisa 14 días antes de su vencimiento.",
            ),
        ],
    ),
    "github": (
        "Repositorio GitHub",
        "brand:git",
        ["orquestacion"],
        ("top", 2),
        "Plataforma que guarda el código en un repositorio Git público.",
        "Guarda el código en main, recibe cada cambio y publica el informe semanal como issue.",
        "En cada cambio del código y al final de cada carga.",
        "Ejecuciones",
        [
            ("Git", "versiona el código y el puntero de la base."),
            ("GitHub Issues · gh", "el informe semanal se publica como issue con la interfaz de línea de comandos."),
        ],
    ),
    "actions": (
        "GitHub Actions",
        "brand:github",
        ["orquestacion"],
        ("top", 4),
        "Servicio de GitHub que ejecuta workflows en máquinas temporales.",
        "semanal.yml corre la carga completa, la prueba y la publica; también se lanza a mano desde el panel "
        "con la clave de control, por la API de GitHub.",
        "Cada martes a las 12:00 UTC, o a mano.",
        "Ejecuciones",
        [
            ("cron del martes", "0 12 * * 2: la carga corre sola cada martes."),
            ("workflow_dispatch", "la ejecución manual, desde GitHub o desde el panel con la clave."),
            ("caché de Actions", "guarda los CSV de los años cerrados para no descargarlos cada semana."),
        ],
    ),
    "ci": (
        "pytest · CI",
        "brand:pytest",
        ["calidad", "orquestacion"],
        ("watch", 3),
        "Las pruebas automáticas y la integración continua.",
        "pruebas.yml corre pytest y dbt parse en cada push; semanal.yml corre pytest sobre la base nueva antes de "
        "publicarla, incluida la paridad.",
        "En cada push y cada martes, antes de publicar.",
        "Monitoreo",
        [
            ("pytest", "el framework de pruebas de Python: recalcula cada cifra desde la fuente."),
            ("dbt parse", "comprueba que los modelos y las pruebas de dbt compilan."),
        ],
    ),
    "web": (
        "HTML · CSS · JavaScript",
        "icon:code",
        ["navegador"],
        ("web", 8),
        "Los lenguajes del navegador.",
        "El panel genera el HTML y el CSS de cada vista (las barras, el menú, los diagramas en SVG, los temas) y "
        "pequeños scripts para las animaciones, el zoom y los textos al pasar el cursor.",
        "En el navegador del lector, en cada página.",
        "Stack y evidencia",
        [
            ("SVG", "los diagramas: el pipeline, el modelo estrella, la seguridad y este mapa."),
            ("CSS", "los cuatro temas, el componente de botones y el ajuste a una pantalla."),
            ("JavaScript", "el zoom, las animaciones, el menú y los trazos de este mapa."),
        ],
    ),
    "charts": (
        "Altair · Vega-Lite",
        "icon:chart",
        ["navegador"],
        ("web", 9),
        "Biblioteca de gráficos declarativos de Python y su motor en el navegador.",
        "Dibuja los gráficos de Precios e inflación y del Resumen, con el formato de números del idioma.",
        "En el navegador, cuando una página muestra un gráfico.",
        "Contexto del precio",
        [],
    ),
    "gates": (
        "Puertas de calidad",
        "icon:shield",
        ["calidad"],
        ("watch", 2),
        "Tres controles que detienen la carga si algo no cumple.",
        "Puerta 1, el archivo; puerta 2, cada fila; puerta 3, la base: si una falla, no se publica nada.",
        "En cada carga.",
        "Monitoreo",
        [("bi/quality_live.py", "mide los once indicadores de calidad sobre la base publicada.")],
    ),
    "parity": (
        "Paridad SQLite ↔ DuckDB",
        "icon:parity",
        ["calidad"],
        ("watch", 4),
        "Comparación de dos caminos independientes.",
        "El respaldo SQLite y la base servida deben dar los mismos precios, los mismos rechazos y la misma suma.",
        "En cada carga, antes de publicar.",
        "Monitoreo",
        [("tests/test_migration_parity.py", "la prueba que compara las dos bases.")],
    ),
    "security": (
        "Seguridad",
        "icon:shield",
        ["seguridad"],
        ("watch", 5),
        "Las amenazas, sus controles y las pruebas que los verifican.",
        "El SQL público con límites, la base en solo lectura, la clave de control y el token protegido; los "
        "casos S-01 a S-14 los atacan en cada push.",
        "En cada push.",
        "Mapa de seguridad",
        [
            ("bi/security_map.py", "la arquitectura de seguridad, con el OWASP Top 10 como guía."),
            ("tests/test_security.py", "los ataques convertidos en pruebas."),
        ],
    ),
    "monitoring": (
        "Observabilidad",
        "icon:pulse",
        ["observabilidad"],
        ("watch", 6),
        "Cómo se sabe qué pasó en cada carga.",
        "etl_run, dbt_result, el log de cada paso de GitHub Actions y el correo que GitHub envía si la carga falla.",
        "En cada carga.",
        "Ejecuciones",
        [("bi/monitoring.py", "el diagrama de las señales y de quién las lee.")],
    ),
    "docs": (
        "Documentos",
        "icon:files",
        ["apoyo"],
        ("watch", 7),
        "La documentación del proyecto, en Markdown.",
        "Siete documentos en docs/ y docs/en/, cada uno con su página en el panel y su PDF.",
        "Cuando alguien abre la carpeta Documentos.",
        "Documentos",
        [("Markdown", "el formato de los documentos, el mismo en GitHub y en el panel.")],
    ),
    "measurement": (
        "Medición de pantallas",
        "icon:ruler",
        ["calidad"],
        ("watch", 8),
        "Medición del diseño en un navegador real.",
        "tests/medicion/medir.cjs mide cada página a 1440 × 790 y 1920 × 1000; imprimir.cjs compara cada "
        "documento impreso con su página.",
        "Antes de cada cambio visual.",
        "Stack y evidencia",
        [("Playwright", "maneja Chrome para medir; se instala fuera del proyecto, sin ser una dependencia.")],
    ),
    "ai": (
        "Apoyo con IA",
        "icon:spark",
        ["apoyo"],
        ("watch", 9),
        "Herramienta de apoyo, fuera del flujo de datos.",
        "Se usó Claude como apoyo para la revisión técnica, la revisión de la documentación y la elección de "
        "etiquetas. El contexto del proyecto vive en archivos Markdown (CLAUDE.md y docs/), con un enfoque "
        "parecido a la recuperación de contexto, pero sin RAG: no hay base vectorial ni embeddings.",
        "Durante el desarrollo; nunca en la carga ni en el panel.",
        "Documentos",
        [],
    ),
}
# (from, to, kind, what travels, themes). Every line goes from the one that acts to the one that receives; a filter shows
# the lines of its theme with their label, and the nodes they join (D-291).
LINKS = [
    ("odepa", "agent", "flow", "CSV", ["datos"]),
    ("ine", "agent", "flow", "IPC", ["datos"]),
    ("agent", "sqlite", "flow", "CSV → raw.db", ["datos"]),
    ("sqlite", "parquet", "flow", "copia por año", ["datos"]),
    ("agent", "parquet", "flow", "IPC, directo", ["datos"]),
    ("parquet", "dbt", "flow", "fuentes", ["datos"]),
    ("dbt", "duckdb", "flow", "marts", ["datos", "calidad"]),
    ("duckdb", "release", "flow", "base servida", ["datos"]),
    ("release", "streamlit", "flow", "descarga y huella", ["datos", "seguridad"]),
    ("streamlit", "web", "flow", "HTML de cada vista", ["navegador"]),
    ("streamlit", "charts", "flow", "gráficos", ["navegador"]),
    ("web", "visitor", "flow", "el panel", ["datos", "navegador"]),
    ("web", "author", "flow", "el panel", ["navegador"]),
    ("visitor", "streamlit", "order", "consultas del estudio SQL", ["datos", "seguridad"]),
    ("github", "streamlit", "order", "despliegue de main", ["orquestacion"]),
    ("actions", "agent", "order", "lanza la carga", ["orquestacion"]),
    ("actions", "release", "order", "publica la base", ["orquestacion"]),
    ("actions", "ci", "order", "corre las pruebas", ["orquestacion", "calidad"]),
    ("actions", "github", "order", "puntero e informe semanal", ["orquestacion", "observabilidad"]),
    ("release", "actions", "flow", "base anterior, para el historial", ["orquestacion"]),
    ("release", "ci", "flow", "base para las pruebas", ["calidad"]),
    ("author", "github", "order", "push con su cuenta", ["orquestacion", "seguridad"]),
    ("author", "streamlit", "order", "clave de control", ["orquestacion", "seguridad"]),
    ("streamlit", "secrets", "check", "compara la clave, lee el token", ["seguridad"]),
    ("streamlit", "actions", "order", "carga manual con el token", ["orquestacion", "seguridad"]),
    ("streamlit", "github", "check", "estado de las ejecuciones (API)", ["observabilidad"]),
    ("ci", "github", "check", "resultado junto al commit", ["orquestacion", "calidad"]),
    ("ci", "security", "order", "S-01 a S-14 en cada push", ["seguridad", "calidad"]),
    ("ci", "parity", "order", "corre la paridad", ["calidad"]),
    ("gates", "agent", "check", "puerta 1", ["calidad"]),
    ("gates", "dbt", "check", "puertas 2 y 3", ["calidad"]),
    ("gates", "release", "check", "publica solo si todo pasa", ["calidad"]),
    ("parity", "sqlite", "check", "respaldo", ["calidad"]),
    ("parity", "duckdb", "check", "base nueva", ["calidad"]),
    ("security", "streamlit", "check", "SQL con límites, clave y token", ["seguridad"]),
    ("security", "duckdb", "check", "solo lectura", ["seguridad"]),
    ("security", "github", "check", "ningún secreto en Git", ["seguridad"]),
    ("security", "actions", "check", "permisos mínimos", ["seguridad"]),
    ("monitoring", "actions", "check", "log de cada paso", ["observabilidad"]),
    ("monitoring", "duckdb", "check", "etl_run y dbt_result", ["observabilidad"]),
    ("actions", "author", "check", "correo si la carga falla", ["observabilidad"]),
    ("measurement", "streamlit", "check", "una pantalla", ["calidad"]),
    ("docs", "streamlit", "support", "páginas y PDF", ["apoyo"]),
    ("ai", "docs", "support", "revisión, sin RAG", ["apoyo"]),
]
# Where each line happens: (file, text that must be in it), or the platform that does it when no file of the project
# can show it. A test reads every file, so a line of the map cannot claim what the code does not do (D-293).
PLATFORM = "platform"
LINK_EVIDENCE = {
    ("odepa", "agent"): ("agent/input.csv", "datos.odepa.gob.cl"),
    ("ine", "agent"): ("etl/ine.py", "www.ine.gob.cl"),
    ("agent", "sqlite"): ("etl/etl.py", "def load_raw_files"),
    ("sqlite", "parquet"): ("etl/bronze.py", "pq.write_table"),
    ("agent", "parquet"): ("etl/ine.py", "pq.write_table"),
    ("parquet", "dbt"): ("dbt/models/staging/sources.yml", "read_parquet"),
    ("dbt", "duckdb"): ("dbt/profiles.yml", "type: duckdb"),
    ("duckdb", "release"): (".github/workflows/semanal.yml", "gh release upload base-actual etl/datos.duckdb"),
    ("release", "streamlit"): ("bi/served_database.py", "/releases/download/"),
    ("release", "actions"): (".github/workflows/semanal.yml", "run: python bi/served_database.py"),
    ("release", "ci"): (".github/workflows/pruebas.yml", "run: python bi/served_database.py"),
    ("streamlit", "web"): ("bi/dashboard.py", "st.html("),
    ("streamlit", "charts"): ("bi/dashboard.py", "st.altair_chart("),
    ("web", "visitor"): (PLATFORM, "Streamlit Cloud"),
    ("web", "author"): (PLATFORM, "Streamlit Cloud"),
    ("visitor", "streamlit"): ("bi/sql_explorer.py", "ROW_LIMIT = 5000"),
    ("github", "streamlit"): (PLATFORM, "Streamlit Cloud"),
    ("actions", "agent"): (".github/workflows/semanal.yml", "run: python agent/agent.py"),
    ("actions", "release"): (".github/workflows/semanal.yml", "gh release upload"),
    ("actions", "ci"): (".github/workflows/semanal.yml", "run: pytest -q"),
    ("actions", "github"): (".github/workflows/semanal.yml", "gh issue create"),
    ("author", "github"): (PLATFORM, "GitHub"),
    ("author", "streamlit"): ("bi/dashboard.py", 'SECRET_CONTROL_CODE = "CONTROL_CODE"'),
    ("streamlit", "secrets"): ("bi/control.py", "hmac.compare_digest"),
    ("streamlit", "actions"): ("bi/control.py", "/dispatches"),
    ("streamlit", "github"): ("bi/control.py", "/actions/runs/"),
    ("ci", "github"): (".github/workflows/pruebas.yml", "push:"),
    ("ci", "security"): ("tests/test_security.py", "def test_no_secret_is_tracked_by_git"),
    ("ci", "parity"): (
        "tests/test_migration_parity.py",
        "def test_every_weekly_price_has_the_same_key_flag_count_and_price",
    ),
    ("gates", "agent"): ("agent/agent.py", "REASON_UNEXPECTED_HEADER"),
    ("gates", "dbt"): ("dbt/tests/rnf05_rows_reconcile.sql", "select"),
    ("gates", "release"): ("etl/pipeline.py", "etl.MINIMUM_ROWS_RATIO"),
    ("parity", "sqlite"): ("tests/test_migration_parity.py", "sqlite3"),
    ("parity", "duckdb"): ("tests/test_migration_parity.py", "duckdb"),
    ("security", "streamlit"): ("tests/test_control.py", "def test_github_error_never_shows_the_token"),
    ("security", "duckdb"): ("bi/sql_explorer.py", "SET lock_configuration = true"),
    ("security", "github"): ("tests/test_security.py", "def test_no_secret_is_tracked_by_git"),
    ("security", "actions"): ("tests/test_security.py", "def test_the_weekly_job_has_least_privilege"),
    ("monitoring", "actions"): ("bi/control.py", "/jobs"),
    ("monitoring", "duckdb"): ("etl/pipeline.py", "etl_run"),
    ("actions", "author"): (PLATFORM, "GitHub"),
    ("measurement", "streamlit"): ("tests/medicion/medir.cjs", "1440"),
    ("docs", "streamlit"): ("bi/dashboard.py", "PROJECT_DOCUMENTS = {"),
    ("ai", "docs"): ("CLAUDE.md", "docs/"),
}


def evidence_label(source, target):
    """The short name of where a line happens: the file name, or the platform."""
    place, detail = LINK_EVIDENCE[(source, target)]
    return detail if place == PLATFORM else place.rsplit("/", 1)[-1]


ROWS = {"top": 1, "flow": 3, "flow2": 4, "web": 5, "watch": 6}
# Thin line icons for the nodes that are not a brand, drawn in the accent of the theme (24-unit grid).
LINE_ICONS = {
    "shield": '<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "code": '<path d="m8 8-4 4 4 4"/><path d="m16 8 4 4-4 4"/><path d="m13.5 5-3 14"/>',
    "chart": '<path d="M4 20V4"/><path d="M4 20h16"/><path d="m7 15 4-5 3 3 5-7"/>',
    "parity": '<path d="M4 8h13"/><path d="m14 5 3 3-3 3"/><path d="M20 16H7"/><path d="m10 13-3 3 3 3"/>',
    "pulse": '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
    "files": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/>',
    "ruler": '<rect x="3" y="8" width="18" height="8" rx="1.5"/><path d="M7 8v3M11 8v4M15 8v3M19 8v4"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9"/><path d="m16 7 3 3"/><path d="m14 9 2 2"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4"/><path d="m6.5 6.5 2.5 2.5M15 15l2.5 2.5M17.5 6.5 15 9M9 15l-2.5 2.5"/>',
}
ROW_LABELS = {1: "Orquestación", 5: "Navegador", 6: "Lo que vigila"}
KIND_COLORS = {"flow": "#3987e5", "order": "#c98500", "check": "#199e70", "support": "#8b8fa3"}


def esc(value):
    return html.escape(str(value), quote=True)


def connections(key):
    """«→ dbt: fuentes», «← ODEPA: CSV»: what the node connects with, read from LINKS."""
    lines = [f"→ {NODES[target][0]}: {what}" for source, target, _, what, _ in LINKS if source == key]
    return lines + [f"← {NODES[source][0]}: {what}" for source, target, _, what, _ in LINKS if target == key]


def node_themes(key):
    """The themes of a node: its own, and those of every line that touches it, so a filter lights every node it involves."""
    themes = list(NODES[key][2])
    for source, target, _, _, line_themes in LINKS:
        if key in (source, target):
            themes += [theme for theme in line_themes if theme not in themes]
    return themes


def logo_image(spec, palette):
    """A logo as an image (st.html drops inline SVG), without a background, in its own color."""
    kind, name = spec.split(":")
    if kind == "brand":
        color = (
            palette["strong_text"]
            if name in ("github", "git")
            else doc_views.DISCS.get(name, ("", palette["accent"]))[1]
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{color}">'
            f'{brand_icons.logo_body(name)}</svg>'
        )
    elif kind == "source":
        svg = database_map.source_logo(name).replace(
            '<svg class="logo" ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1
        )
    elif kind == "person":
        color = doc_views.PERSON_DISCS[name][1]
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" fill="{color}">'
            '<circle cx="18" cy="12" r="6"/><path d="M6 31c1-8 6-12 12-12s11 4 12 12z"/></svg>'
        )
    else:
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{palette["accent"]}" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{LINE_ICONS[name]}</svg>'
        )
    return f'<img class="am-logo" alt="" src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}">'


def build_tip(key):
    name, _, _, _, what, role, when, _, group = NODES[key]
    parts = [("Qué es", what), ("Rol en GreenOcean", role), ("Cuándo actúa", when)]
    left = f'<b class="am-tip-name">{esc(name)}</b>' + "".join(
        f"<i>{esc(head)}</i><span>{esc(text)}</span>" for head, text in parts
    )
    # Each connection names where it happens, so the reader can check it in the code.
    places = [evidence_label(source, target) for source, target, *_ in LINKS if source == key]
    places += [evidence_label(source, target) for source, target, *_ in LINKS if target == key]
    right = f"<i>{esc('Se conecta con')}</i>" + "".join(
        f'<span>{esc(line)} <code class="am-src">{esc(place)}</code></span>'
        for line, place in zip(connections(key), places)
    )
    extra = ""
    if group:
        extra = (
            f'<span class="am-tip-col"><i>{esc("Incluye")}</i>'
            + "".join(f"<span><b>{esc(tool)}</b> — {esc(text)}</span>" for tool, text in group)
            + "</span>"
        )
    # Up to three short columns (what it is, what it touches, what it includes), so the box is wide and low and covers
    # as little of the drawing as possible.
    return (
        f'<span class="am-tip" role="tooltip"><span class="am-tip-col">{left}</span>'
        f'<span class="am-tip-col">{right}</span>{extra}</span>'
    )


def build_node(key, palette, addresses):
    name, logo, themes, (row, column), _, _, _, page, group = NODES[key]
    extra = f'<small class="am-more">+{len(group)}</small>' if group else ""
    return (
        f'<a class="am-node" id="am-{key}" data-key="{key}" data-themes="{" ".join(node_themes(key))}" '
        f'href="{esc(addresses.get(page, "#"))}" target="_self" '
        f'style="grid-row:{ROWS[row]};grid-column:{column}">'
        f'{logo_image(logo, palette)}<b class="am-name">{esc(name)}{extra}</b>{build_tip(key)}</a>'
    )


def build_css(palette):
    ink, text, muted, card, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    kinds = "".join(
        f".am-line.k-{kind} {{ stroke:{color}; }} .am-key.k-{kind}::before {{ background:{color}; }}"
        for kind, color in KIND_COLORS.items()
    )
    return f"""<style>
.am {{ position:relative; display:flex; flex-direction:column; gap:8px; color:{text}; container:am / inline-size; }}
.am-bar {{ display:flex; flex-wrap:wrap; align-items:center; gap:6px 14px; font-size:12px; }}
.am-filters {{ display:flex; flex-wrap:wrap; gap:4px; }}
.am-filter {{ font:inherit; font-size:12px; padding:3px 10px; border-radius:9px; cursor:pointer; color:{ink};
  border:1px solid {border}; background:transparent; }}
.am-filter:hover, .am-filter:focus-visible {{ border-color:{accent}; outline:none; }}
.am-filter.on {{ border-color:{accent}; background:color-mix(in srgb, {accent} 14%, transparent); }}
.am-legend {{ display:flex; flex-wrap:wrap; gap:12px; color:{muted}; margin-left:auto; }}
.am-key {{ display:inline-flex; align-items:center; gap:6px; }}
.am-key::before {{ content:""; width:22px; height:2px; border-radius:2px; }}
.am-key.k-order::before {{ height:0; border-top:2px dashed #c98500; background:none; }}
.am-key.k-check::before {{ height:0; border-top:2px dotted #199e70; background:none; }}
.am-stage {{ position:relative; display:grid; grid-template-columns:repeat(9, minmax(0, 1fr));
  grid-template-rows:auto auto auto auto auto auto; gap:14px 10px; padding:6px 0 4px; }}
.am-lines {{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; overflow:visible; z-index:0; }}
.am-line {{ fill:none; stroke-width:1.6; opacity:0; transition:opacity .15s ease; }}
.am-line.base {{ opacity:.6; }}
.am-tip code.am-src {{ font-size:10.5px; padding:0 4px; border-radius:4px; color:{muted};
  background:color-mix(in srgb, {border} 45%, transparent); }}
.am-label {{ font-size:10.5px; font-weight:500; fill:{text}; stroke:var(--am-surface, transparent); stroke-width:4px;
  paint-order:stroke; stroke-linejoin:round; opacity:0; transition:opacity .15s ease; }}
.am-line.k-order {{ stroke-dasharray:6 5; }} .am-line.k-check {{ stroke-dasharray:2 4; }} .am-line.k-support {{ stroke-width:1.2; }}
{kinds}
.am-layer {{ grid-row:2; font-size:10.5px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{muted};
  text-align:center; border-bottom:1px solid color-mix(in srgb, {border} 70%, transparent); padding-bottom:4px; }}
.am-band {{ grid-column:1 / -1; align-self:stretch; border:1px dashed color-mix(in srgb, {border} 80%, transparent);
  border-radius:12px; position:relative; z-index:0; }}
.am-band span {{ position:absolute; top:-8px; left:12px; padding:0 6px; font-size:10.5px; font-weight:600;
  letter-spacing:.08em; text-transform:uppercase; color:{muted}; background:var(--am-surface, transparent); }}
.am-node {{ position:relative; z-index:1; display:flex; flex-direction:column; align-items:center; gap:4px;
  padding:6px 4px; border-radius:10px; text-decoration:none !important; color:{ink} !important; min-width:0;
  transition:opacity .15s ease, background .15s ease; }}
.am-node:hover, .am-node:focus-visible {{ background:color-mix(in srgb, {accent} 10%, transparent); outline:none; z-index:5; }}
.am-logo {{ width:30px; height:30px; display:block; }}
.am-name {{ font-size:12px; font-weight:600; line-height:1.25; text-align:center; overflow-wrap:break-word; }}
.am-more {{ margin-left:4px; font-size:10.5px; font-weight:500; color:{accent}; }}
.am-tip {{ position:absolute; top:calc(100% + 4px); left:50%; transform:translateX(-50%); width:min(800px, 66vw); z-index:20;
  display:none; grid-auto-flow:column; grid-auto-columns:minmax(0, 1fr); gap:0 16px; padding:10px 14px; border-radius:12px;
  text-align:left; pointer-events:none; overflow:hidden;
  background:{card}; border:1px solid {border}; box-shadow:0 18px 40px -18px rgba(0,0,0,.45); color:{text};
  font-size:12px; font-weight:400; line-height:1.4; }}
.am-tip-col {{ display:flex; flex-direction:column; gap:2px; min-width:0; }}
.am-tip i {{ margin-top:5px; font-style:normal; font-size:10.5px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:{muted}; }}
.am-tip b {{ color:{ink}; font-weight:600; }}
.am-tip-name {{ font-size:13px; }}
.am-node:hover .am-tip, .am-node:focus-visible .am-tip {{ display:grid; }}
.am-node[style*="grid-column:1"] .am-tip, .am-node[style*="grid-column:2"] .am-tip,
.am-node[style*="grid-column:3"] .am-tip {{ left:0; transform:none; }}
.am-node[style*="grid-column:7"] .am-tip, .am-node[style*="grid-column:8"] .am-tip,
.am-node[style*="grid-column:9"] .am-tip {{ left:auto; right:0; transform:none; }}
.am-node[style*="grid-row:6"] .am-tip, .am-node[style*="grid-row:5"] .am-tip {{ top:auto; bottom:calc(100% + 4px); }}
.am.has-focus .am-node:not(.on), .am[data-filter] .am-node.dim {{ opacity:.22; }}
.am[data-filter] .am-line {{ opacity:0; }}
.am[data-filter] .am-line.show {{ opacity:.95; stroke-width:2; }}
.am[data-filter] .am-label.show {{ opacity:1; }}
.am.has-focus .am-line, .am.has-focus .am-label {{ opacity:0; }}
.am.has-focus .am-line.on {{ opacity:1; stroke-width:2.2; }}
.am.has-focus .am-label.on {{ opacity:1; }}
.am-note {{ font-size:11.5px; color:{muted}; margin:0; }}
@container am (max-width:760px) {{
  .am-stage {{ grid-template-columns:1fr 1fr; }}
  .am-stage > * {{ grid-row:auto !important; grid-column:auto !important; }}
  .am-layer, .am-band, .am-lines {{ display:none; }}
  .am-tip {{ left:0 !important; right:auto !important; transform:none !important; grid-template-columns:1fr; width:80vw; }}
}}
/* D-324: nine columns of about 90 px: the layer names and the node names shrink to fit instead of running into each other. */
@container am (max-width:1200px) {{
  .am-layer {{ font-size:10px; letter-spacing:0; text-transform:none; }} .am-name {{ font-size:11px; }} .am-more {{ font-size:10px; }}
}}
@media (min-width:1700px) and (min-height:950px) {{
  .am-stage {{ row-gap:30px; }} .am-logo {{ width:40px; height:40px; }} .am-name {{ font-size:13.5px; }}
  .am-node {{ padding:10px 6px; }} .am-layer {{ font-size:11.5px; }}
}}
@media (prefers-reduced-motion:reduce) {{ .am-node, .am-line {{ transition:none; }} }}
</style>"""


# Draws the lines once the nodes have their place, again on every resize; highlights the path of the node under the
# cursor; a filter dims what is outside its theme. No HTML in the script (st.html would drop it).
SCRIPT = r"""<script>
(() => {
  const maps = document.querySelectorAll(".am:not([data-ready])");
  maps.forEach((map) => {
    map.dataset.ready = "1";
    const stage = map.querySelector(".am-stage");
    const links = JSON.parse(map.dataset.links);
    const whats = Array.from(map.querySelectorAll(".am-whats span"), (item) => item.textContent);
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("class", "am-lines");
    stage.prepend(svg);
    const node = (key) => stage.querySelector("#am-" + key);
    const draw = () => {
      while (svg.firstChild) { svg.removeChild(svg.firstChild); }
      const box = stage.getBoundingClientRect();
      const pairs = {};
      links.forEach(([from, to, kind, themes], index) => {
        const a = node(from), b = node(to);
        if (!a || !b) { return; }
        const ra = a.querySelector(".am-logo").getBoundingClientRect();
        const rb = b.querySelector(".am-logo").getBoundingClientRect();
        const x1 = ra.left + ra.width / 2 - box.left, y1 = ra.top + ra.height / 2 - box.top;
        const x2 = rb.left + rb.width / 2 - box.left, y2 = rb.top + rb.height / 2 - box.top;
        const horizontal = Math.abs(x2 - x1) >= Math.abs(y2 - y1);
        // A second line between the same nodes bows further; a line along a row that skips a node arcs around it,
        // towards the middle of the drawing, so no line leaves it.
        const pair = [from, to].sort().join(" ");
        const twin = pairs[pair] || 0;
        pairs[pair] = twin + 1;
        const flat = Math.abs(y2 - y1) > 8 ? 0 : (Math.abs(x2 - x1) > 150 ? 56 : 0);
        const bow = (flat + twin * 22) * (y1 > box.height / 2 ? -1 : 1);
        const d = horizontal
          ? "M" + x1 + " " + y1 + " C" + (x1 + x2) / 2 + " " + (y1 + bow) + " " + (x1 + x2) / 2 + " " + (y2 + bow) + " " + x2 + " " + y2
          : "M" + x1 + " " + y1 + " C" + (x1 + bow) + " " + (y1 + y2) / 2 + " " + (x2 + bow) + " " + (y1 + y2) / 2 + " " + x2 + " " + y2;
        const path = document.createElementNS(ns, "path");
        path.setAttribute("d", d);
        // Without a filter, only the data flow and what reaches the reader are drawn.
        const base = kind === "flow" && (themes.includes("datos") || themes.includes("navegador"));
        path.setAttribute("class", "am-line k-" + kind + (base ? " base" : ""));
        path.dataset.from = from;
        path.dataset.to = to;
        path.dataset.themes = themes.join(" ");
        svg.appendChild(path);
        const label = document.createElementNS(ns, "text");
        label.setAttribute("class", "am-label");
        label.setAttribute("x", (x1 + x2) / 2);
        label.setAttribute("y", (y1 + y2) / 2 - 4);
        label.setAttribute("text-anchor", "middle");
        label.textContent = whats[index];
        label.dataset.from = from;
        label.dataset.to = to;
        label.dataset.themes = themes.join(" ");
        label.path = path;
        svg.appendChild(label);
      });
      applyFilter();
    };
    const lines = () => svg.querySelectorAll(".am-line, .am-label");
    // Each visible label takes the place along its line, above or below it, that covers the least of the other labels,
    // the nodes and the headings.
    const place = (labels) => {
      const box = stage.getBoundingClientRect();
      const rect = (item) => {
        const r = item.getBoundingClientRect();
        return {left: r.left - box.left, top: r.top - box.top, right: r.right - box.left, bottom: r.bottom - box.top};
      };
      const fixed = Array.from(stage.querySelectorAll(".am-logo, .am-name, .am-layer, .am-band span"), rect);
      const placed = [];
      const overlap = (a, list) => list.reduce((sum, b) => sum + Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left))
        * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top)), 0);
      labels.forEach((label) => {
        const length = label.path.getTotalLength();
        let best = null;
        [0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74, 0.18, 0.82].forEach((share, rank) => {
          const point = label.path.getPointAtLength(length * share);
          [-4, 13].forEach((shift) => {
            label.setAttribute("x", point.x);
            label.setAttribute("y", point.y + shift);
            const r = label.getBBox();
            const area = {left: r.x - 3, top: r.y - 1, right: r.x + r.width + 3, bottom: r.y + r.height + 1};
            const score = overlap(area, placed) * 10 + overlap(area, fixed) + rank;
            if (!best || score > -1 && best.score > score) { best = {score, x: point.x, y: point.y + shift, area}; }
          });
        });
        label.setAttribute("x", best.x);
        label.setAttribute("y", best.y);
        placed.push(best.area);
      });
    };
    // The description of a node never covers the drawing when the side menu is open: it shows over the menu, where no
    // line runs. With the menu closed, it goes where it covers the fewest of the node's own lines and neighbours. Only
    // its style changes; the element stays where Streamlit put it.
    const dodge = (item) => {
      const tip = item.querySelector(".am-tip");
      if (!tip) { return; }
      ["position", "left", "top", "right", "bottom", "transform", "width", "maxHeight", "gridAutoFlow", "zIndex", "fontSize"]
        .forEach((name) => { tip.style[name] = ""; });
      item.style.zIndex = "";
      const menu = document.querySelector('[data-testid="stSidebar"]');
      const side = menu ? menu.getBoundingClientRect() : null;
      if (side && side.width >= 240 && side.right > 0 && window.innerWidth > side.right + 600) {
        tip.style.position = "fixed";
        tip.style.left = (side.left + 10) + "px";
        tip.style.top = "12px";
        tip.style.width = (Math.max(side.right, stage.getBoundingClientRect().left - 12) - side.left - 10) + "px";
        tip.style.maxHeight = (window.innerHeight - 24) + "px";
        tip.style.gridAutoFlow = "row";
        tip.style.fontSize = "11.5px";
        tip.style.transform = "none";
        tip.style.right = "auto";
        tip.style.bottom = "auto";
        tip.style.zIndex = "1000001";
        item.style.zIndex = "1000001";  // the menu is drawn above the page: the node rises with its description
        return;
      }
      const box = stage.getBoundingClientRect();
      const own = item.getBoundingClientRect();
      const t = tip.getBoundingClientRect();
      const w = t.width, h = t.height;
      const nx = own.left - box.left, ny = own.top - box.top, nw = own.width, nh = own.height;
      const points = [];
      svg.querySelectorAll(".am-line.on").forEach((line) => {
        const length = line.getTotalLength();
        for (let step = 0; length > step; step += 10) { points.push(line.getPointAtLength(step)); }
      });
      const others = Array.from(stage.querySelectorAll(".am-node.on"), (other) => {
        const r = other.getBoundingClientRect();
        return {x: r.left - box.left + r.width / 2, y: r.top - box.top + r.height / 2};
      });
      const clampX = (x) => Math.max(0, Math.min(x, box.width - w));
      // Next to the node first, then a grid of nine places over the drawing; never outside it.
      const candidates = [[clampX(nx + nw / 2 - w / 2), ny + nh + 4], [clampX(nx + nw / 2 - w / 2), ny - h - 4]];
      [0, (box.height - h) / 2, box.height - h].forEach((y) => {
        [0, (box.width - w) / 2, box.width - w].forEach((x) => candidates.push([x, y]));
      });
      let best = null;
      candidates.forEach(([x, y], rank) => {
        if (0 > x || x + w > box.width + 1 || -8 > y || y + h > box.height + 8) { return; }
        const inside = (p) => p.x >= x && x + w >= p.x && p.y >= y && y + h >= p.y;
        const score = points.filter(inside).length + others.filter(inside).length * 25 + rank * 0.3;
        if (!best || best.score > score) { best = {score, x, y}; }
      });
      if (!best) { return; }
      tip.style.left = (best.x - nx) + "px";
      tip.style.top = (best.y - ny) + "px";
      tip.style.right = "auto";
      tip.style.bottom = "auto";
      tip.style.transform = "none";
    };
    stage.querySelectorAll(".am-node").forEach((item) => {
      const key = item.dataset.key;
      const enter = () => {
        map.classList.add("has-focus");
        item.classList.add("on");
        lines().forEach((line) => {
          if (line.dataset.from === key || line.dataset.to === key) {
            line.classList.add("on");
            const other = node(line.dataset.from === key ? line.dataset.to : line.dataset.from);
            if (other) { other.classList.add("on"); }
          }
        });
        place(svg.querySelectorAll(".am-label.on"));
        dodge(item);
      };
      const leave = () => {
        item.style.zIndex = "";
        map.classList.remove("has-focus");
        stage.querySelectorAll(".on").forEach((element) => element.classList.remove("on"));
      };
      item.addEventListener("mouseenter", enter);
      item.addEventListener("focus", enter);
      item.addEventListener("mouseleave", leave);
      item.addEventListener("blur", leave);
    });
    const applyFilter = () => {
      const theme = map.dataset.filter;
      stage.querySelectorAll(".am-node").forEach((item) => {
        item.classList.toggle("dim", !!theme && !item.dataset.themes.split(" ").includes(theme));
      });
      lines().forEach((line) => {
        line.classList.toggle("show", !!theme && line.dataset.themes.split(" ").includes(theme));
      });
      place(svg.querySelectorAll(".am-label.show"));
    };
    map.querySelectorAll(".am-filter").forEach((button) => {
      button.addEventListener("click", () => {
        const same = map.dataset.filter === button.dataset.theme;
        map.querySelectorAll(".am-filter").forEach((other) => other.classList.remove("on"));
        if (same) { delete map.dataset.filter; } else { map.dataset.filter = button.dataset.theme; button.classList.add("on"); }
        applyFilter();
      });
    });
    new ResizeObserver(draw).observe(stage);
    draw();
  });
})();
</script>"""


def build_map_html(palette, addresses):
    """The whole map: filters and legend, the layers, the bands and the nodes; the script adds the lines."""
    filters = "".join(
        f'<button type="button" class="am-filter" data-theme="{key}">{esc(label)}</button>' for key, label in THEMES
    )
    legend = "".join(f'<span class="am-key k-{kind}">{esc(label)}</span>' for kind, label in LINE_KINDS)
    layers = "".join(
        f'<span class="am-layer" style="grid-column:{index}">{esc(name)}</span>'
        for index, name in enumerate(LAYERS, start=1)
    )
    bands = "".join(
        f'<div class="am-band" style="grid-row:{row}"><span>{esc(label)}</span></div>'
        for row, label in ROW_LABELS.items()
    )
    nodes = "".join(build_node(key, palette, addresses) for key in NODES)
    data = esc(json.dumps([[source, target, kind, themes] for source, target, kind, _, themes in LINKS]))
    # The label of each line is a text node, not part of the data, so the translation layer reaches it (D-284).
    whats = "".join(f"<span>{esc(what)}</span>" for _, _, _, what, _ in LINKS)
    return (
        build_css(palette) + f'<div class="am" style="--am-surface:{palette["background"]}" data-links="{data}">'
        f'<div class="am-bar"><span class="am-filters" role="group" aria-label="{esc("Filtrar por tema")}">{filters}'
        f'</span><span class="am-legend">{legend}</span></div>'
        f'<div class="am-stage" aria-label="{esc("Mapa de la app")}">{layers}{bands}{nodes}</div>'
        f'<div class="am-whats" hidden>{whats}</div>'
        f'<p class="am-note">{esc("Sin filtro, el flujo de datos; un tema muestra todas sus piezas y conexiones. El cursor explica cada pieza y un clic abre su página.")}</p>'
        "</div>" + SCRIPT
    )
