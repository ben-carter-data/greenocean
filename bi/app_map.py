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
import colorsys
import html
import json
import re

from bi import app_map_detail as detail, static_files
from bi import brand_icons, charts, database_map, doc_views, i18n

# region Constants
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
# key: (name, logo, themes, (row, column), what it is, role in GreenOcean, when it acts, page, [(small tool, what)]).
# A logo is «brand:<slug>», «source:<key>», «person:<key>» or «icon:<name>». Rows: «top» (orchestration), «flow»,
# «flow2» (a second node in a column of the flow), «web» (the browser layer) and «watch» (what watches the system).
NODES = {
    "odepa": (
        "ODEPA mayorista",
        "source:odepa",
        ["datos"],
        ("flow", 1),
        "Oficina de Estudios y Políticas Agrarias del Ministerio de Agricultura de Chile.",
        "Publica los precios mayoristas de frutas y hortalizas, diarios, en un CSV por año.",
        "Publica cada semana; la carga descarga cada martes.",
        "Semanal",
        [],
    ),
    "odepa_consumer": (
        "ODEPA consumidor",
        "source:odepa",
        ["datos"],
        ("flow2", 1),
        "Oficina de Estudios y Políticas Agrarias del Ministerio de Agricultura de Chile.",
        "Publica los precios al consumidor por canal (feria libre, supermercado, carnicería y los demás), semanales, "
        "en un CSV por año.",
        "Publica cada semana; la carga descarga cada martes.",
        "Semanal",  # D-494: its channels are step 2 of «Semanal»
        [],
    ),
    "ine": (
        "INE",
        "source:ine",
        ["datos"],
        ("web", 1),
        "Instituto Nacional de Estadísticas de Chile.",
        "Publica el IPC de alimentos, con el que los precios se expresan en pesos de hoy.",
        "Publica cada mes; la carga descarga cada martes.",
        "Análisis",
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
        ("flow2", 3),
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
        ("flow2", 5),
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
        "Motor donde dbt construye el data warehouse y Base DuckDB etl/datos.duckdb, que el panel lee en solo lectura.",
        "Cada martes; la Base DuckDB se reemplaza solo al final de una carga válida.",
        "Modelo de datos",
        [
            ("SQL", "el lenguaje de los modelos, de las consultas del panel (bi/queries.sql) y del estudio SQL."),
            ("pandas", "recibe el resultado de cada consulta que el panel convierte en tabla o gráfico."),
            ("openpyxl", "escribe el Excel de «Descargar» del paso 4: la tabla con su filtro y su hoja de notas."),
        ],
    ),
    "release": (
        "Release «base-actual»",
        "icon:tag",
        ["datos", "orquestacion"],
        ("flow2", 7),
        "Archivo publicado en GitHub, fuera del historial de Git.",
        "Guarda una sola copia de la Base DuckDB, reemplazada por cada carga; en main queda su puntero "
        "etl/datos.version, con la huella, el tamaño y la fecha (D-270).",
        "Al final de cada carga que pasó todas las pruebas.",
        "Ejecuciones",
        [("bi/served_database.py", "descarga la base del release y la usa solo si su huella coincide.")],
    ),
    "streamlit": (
        "Panel web",
        "brand:streamlit",
        ["datos"],
        ("flow", 8),
        "Framework de Python para aplicaciones web de datos.",
        "Dibuja este panel con la Base DuckDB en solo lectura y lo publica en Streamlit Community Cloud "
        "desde la rama main.",
        "Cada vez que alguien abre una página.",
        "Semanal",
        [
            (
                "Páginas",
                "Semanal, Análisis (Mensual, Histórico, Precios e inflación, "
                "Insights, Interesados y Método), Pipeline y linaje, Reglas de transformación, Modelo de datos, Consultas SQL, Stack y evidencia, Mapa de la app, "
                "Arquitectura de seguridad, Plan de calidad, Controles de datos, Cambios e incidentes y la carpeta de "
                "documentos; el Autor ve además Centro de operación, GitHub Actions y Configuración.",
            ),
        ],
    ),
    # D-382: the three views of the panel are three people.
    "visitor": (
        "Usuario",
        "person:visitor",
        ["datos"],
        ("flow", 9),
        "Quien quiere saber cómo se mueven los precios: analista, compras, gerencia o público.",
        "Ve el negocio: sus dos dashboards, Semanal y Análisis, sin cuenta: los datos son públicos.",
        "Cuando elige la vista Usuario.",
        "Semanal",
        [],
    ),
    "professional": (
        "Profesional",
        "person:professional",
        ["datos"],
        ("flow2", 9),
        "Quien revisa cómo está hecho el proyecto: datos, arquitectura, calidad, DevOps o seguridad.",
        "Ve todo el panel, ordenado según su perfil, y usa el estudio SQL de solo lectura, sin cuenta.",
        "Cuando elige la vista Profesional.",
        "Consultas SQL",
        [],
    ),
    "author": (
        "Autor",
        "person:author",
        ["seguridad", "orquestacion"],
        ("web", 9),
        "Quien mantiene el proyecto.",
        "Ve lo mismo que el Profesional; mantiene el código y los secretos, y con la clave de control lanza, sigue y cancela la carga desde el panel.",
        "Cuando cambia el código o lanza una carga manual.",
        "Ejecuciones",
        [
            ("clave de control", "la única clave del panel: la escribe en «Elige tu vista» para entrar como Autor."),
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
        ("flow2", 8),
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
                "token para lanzar el workflow y leer sus ejecuciones; el panel avisa 15 días antes de su vencimiento.",
            ),
        ],
    ),
    "semanal": (
        "semanal.yml",
        "icon:workflow",
        ["orquestacion", "datos"],
        ("top", 2),
        "El workflow de la carga semanal, escrito por el proyecto.",
        "Descarga, construye, prueba y publica la Base DuckDB en una máquina de GitHub, y abre el «Informe semanal».",
        "Cada martes a las 12:07 UTC, o a mano.",
        "Pipeline y arquitectura",
        [
            ("cron del martes", "7,22,37,52 12-14 * * 2: la carga corre sola cada martes."),
            ("workflow_dispatch", "la ejecución manual, desde GitHub o desde el panel con la clave."),
        ],
    ),
    "pruebas": (
        "pruebas.yml",
        "icon:workflow",
        ["calidad", "orquestacion"],
        ("top", 3),
        "El workflow de las pruebas de cada push, escrito por el proyecto.",
        "Corre ruff, mypy, dbt parse y pytest sobre la base publicada, en Python 3.11 y 3.12; nunca publica nada.",
        "En cada push y en cada pull request.",
        "Monitoreo",
        [],
    ),
    "calidad": (
        "calidad.yml",
        "icon:workflow",
        ["calidad", "orquestacion"],
        ("top", 4),
        "El workflow de la medición y el informe de calidad, escrito por el proyecto.",
        "Mide los 14 indicadores del plan de calidad y, tras una carga en verde, propone el informe semanal como pull "
        "request, que se fusiona solo si el código está en su aceptable.",
        "En cada push y después de cada carga.",
        "Plan de calidad",
        [("bandit · pip-audit · detect-secrets", "las herramientas que alimentan tres indicadores de seguridad.")],
    ),
    "github": (
        "GitHub",
        "brand:github",
        ["orquestacion"],
        ("top", 6),
        "Plataforma que guarda el código en un repositorio Git público y corre los workflows.",
        "Guarda el código en main, corre los tres workflows en sus máquinas, guarda la caché de los años cerrados, "
        "publica la base en un release y recibe el «Informe semanal» como issue y el informe de calidad como pull "
        "request.",
        "En cada push, cada martes y cada vez que el panel consulta su API.",
        "Stack y evidencia",
        [
            ("Git", "versiona el código y el puntero de la base."),
            ("GitHub Issues · gh", "el informe semanal se publica como issue con la interfaz de línea de comandos."),
            ("caché de Actions", "guarda los CSV de los años cerrados para no descargarlos cada semana."),
        ],
    ),
    "pypi": (
        "PyPI",
        "icon:box",
        ["seguridad", "orquestacion"],
        ("top", 7),
        "El índice público de paquetes de Python.",
        "Entrega las dependencias de requirements.txt y requirements-pipeline.txt en cada instalación, cada una con "
        "su versión máxima.",
        "En cada carga, en cada push y cuando el panel se reinicia.",
        "Stack y evidencia",
        [],
    ),
    "stcloud": (
        "Streamlit Community Cloud",
        "icon:cloud",
        ["navegador", "seguridad"],
        ("top", 8),
        "El servicio gratuito que publica el panel.",
        "Corre el Panel web desde la rama main y guarda sus secretos: CONTROL_CODE, GITHUB_TOKEN y GITHUB_READ_TOKEN.",
        "Al abrir el panel; despierta la app cuando alguien la visita.",
        "Stack y evidencia",
        [],
    ),
    "devops": (
        "DevOps y seguridad",
        "icon:console",
        ["seguridad", "orquestacion", "observabilidad"],
        ("web", 8),
        "Las tres páginas del Autor: Centro de operación, GitHub Actions y Configuración.",
        "Lanza, sigue y cancela la carga por la API de GitHub, muestra el estado de los workflows y sus logs, y los "
        "tokens con su vencimiento.",
        "Cuando el Autor entra con su clave.",
        "Ejecuciones",
        [
            ("Centro de operación", "«Ejecutar pipeline ahora», «Cancelar», «Recargar datos» y «Cerrar acceso»."),
            ("Configuración", "los tokens, la última carga y los cinco casos del MANUAL."),
        ],
    ),
    "ci": (
        "pytest",
        "brand:pytest",
        ["calidad", "orquestacion"],
        ("watch", 3),
        "Las pruebas automáticas del proyecto.",
        "pruebas.yml las corre todas en cada push; semanal.yml corre las de datos sobre la base nueva antes de "
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
        ("web", 6),
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
        ("web", 7),
        "Biblioteca de gráficos declarativos de Python y su motor en el navegador.",
        "Dibuja los gráficos de «Análisis» y del dashboard Semanal, con el formato de números del idioma.",
        "En el navegador, cuando una página muestra un gráfico.",
        "Análisis",
        [],
    ),
    "gates": (
        "Puerta de publicación",
        "icon:gate",
        ["calidad"],
        ("watch", 2),
        "Los criterios que detienen la carga si algo no cumple.",
        "El encabezado de cada archivo, los modelos y las pruebas de dbt, las filas frente a la última carga, las "
        "semanas sin huecos, el atraso de las fuentes y las pruebas de datos: si uno falla, no se publica nada.",
        "En cada carga.",
        "Monitoreo",
        [
            (
                "bi/quality_live.py",
                "mide los once indicadores de calidad de los datos sobre la base publicada, en cada carga.",
            )
        ],
    ),
    "parity": (
        "Respaldo y paridad",
        "icon:parity",
        ["calidad"],
        ("watch", 4),
        "Comparación de dos caminos independientes.",
        "El respaldo SQLite y la Base DuckDB deben dar los mismos precios, los mismos rechazos y la misma suma.",
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
        "Nueve documentos en cuatro carpetas de docs/ y de docs/en/, cada uno con su página en el panel y su PDF: la carpeta muestra los cinco principales, y los cuatro anexos se abren desde sus enlaces; aparte, el estudio de la fuente en dos cuadernos de Jupyter.",
        "Cuando alguien abre la carpeta Documentos del proyecto o Análisis de la fuente de datos.",
        "Documentos del proyecto",
        [
            ("Markdown", "el formato de los documentos, el mismo en GitHub y en el panel."),
            ("Jupyter", "los dos cuadernos que estudian el archivo mayorista de ODEPA, en notebooks/."),
        ],
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
        "Documentos del proyecto",
        [],
    ),
}
# (from, to, kind, what travels, themes, rhythm, what goes exactly, what comes back). Every line goes from the one that
# acts to the one that receives; a filter shows the lines of its theme with their label (D-291), a rhythm moves only the
# lines that run with it, and a click on a line opens what travels on it (D-441).
LINKS = [
    (
        "odepa",
        "agent",
        "flow",
        "CSV mayorista",
        ["datos"],
        "week",
        "agent/agent.py pide por HTTPS el CSV del año en curso; los años cerrados vienen de la caché.",
        "El archivo, con su encabezado validado y su huella SHA-256 en manifest.json.",
    ),
    (
        "odepa_consumer",
        "agent",
        "flow",
        "CSV consumidor",
        ["datos"],
        "week",
        "Lo mismo: solo se descarga el archivo del año en curso.",
        "Los precios por canal, con su huella.",
    ),
    (
        "ine",
        "agent",
        "flow",
        "IPC",
        ["datos"],
        "month",
        "etl/ine.py pide los dos CSV del IPC en cada carga; el INE agrega un mes nuevo cada mes.",
        "La división 1, alimentos; si el INE no responde, se usan las filas de la base publicada.",
    ),
    (
        "agent",
        "sqlite",
        "flow",
        "CSV → raw.db",
        ["datos"],
        "week",
        "Las filas de ODEPA tal como llegaron.",
        "Nada: es la zona de aterrizaje.",
    ),
    (
        "sqlite",
        "parquet",
        "flow",
        "copia por año",
        ["datos"],
        "week",
        "etl/bronze.py copia raw.db a Parquet, un archivo por fuente y año.",
        "Nada: el bronce queda listo para dbt.",
    ),
    (
        "agent",
        "parquet",
        "flow",
        "IPC, directo",
        ["datos"],
        "week",
        "etl/ine.py escribe el IPC directo en etl/bronze/ine_ipc.",
        "Nada.",
    ),
    (
        "parquet",
        "dbt",
        "flow",
        "fuentes",
        ["datos"],
        "week",
        "dbt lee el bronce con read_parquet; nunca lee raw.db.",
        "Los modelos construidos y el resultado de cada prueba.",
    ),
    (
        "dbt",
        "duckdb",
        "flow",
        "marts",
        ["datos", "calidad"],
        "week",
        "Las tablas del panel se copian a una base compacta, etl/datos.duckdb.",
        "La base nueva, con la carga registrada en etl_run.",
    ),
    (
        "duckdb",
        "release",
        "flow",
        "Base DuckDB",
        ["datos"],
        "week",
        "gh release upload base-actual etl/datos.duckdb --clobber.",
        "El release reemplazado; el commit actualiza etl/datos.version.",
    ),
    (
        "release",
        "streamlit",
        "flow",
        "descarga y huella",
        ["datos", "seguridad"],
        "week",
        "El panel ve el puntero nuevo en main y descarga el archivo del release.",
        "La base, aceptada solo si su SHA-256 coincide con el puntero.",
    ),
    (
        "streamlit",
        "web",
        "flow",
        "HTML de cada vista",
        ["navegador"],
        "always",
        "Cada página genera su HTML, su CSS y sus diagramas.",
        "Lo que el lector hace: un clic, un filtro, una consulta.",
    ),
    (
        "streamlit",
        "charts",
        "flow",
        "gráficos",
        ["navegador"],
        "always",
        "Las especificaciones de los gráficos, con los números del idioma.",
        "Nada.",
    ),
    (
        "visitor",
        "streamlit",
        "access",
        "vista Usuario",
        ["datos", "navegador"],
        "always",
        "Elige «Usuario» en «Elige tu vista»; no hay cuenta ni clave.",
        "«Negocio · BA y BI»: las páginas del negocio.",
    ),
    (
        "professional",
        "streamlit",
        "access",
        "vista Profesional y SQL",
        ["datos", "navegador", "seguridad"],
        "always",
        "Elige «Profesional» y, en «Consultas SQL», escribe consultas de solo lectura.",
        "Todo el panel salvo «DevOps y seguridad»; cada consulta, hasta 5.000 filas en 10 segundos.",
    ),
    (
        "author",
        "devops",
        "access",
        "CONTROL_CODE",
        ["seguridad", "orquestacion"],
        "manual",
        "La clave del Autor, comparada en tiempo constante; el servidor comprueba la sesión antes de cada página y de "
        "cada acción.",
        "«DevOps y seguridad»; la sesión vence a los 30 minutos sin actividad.",
    ),
    (
        "author",
        "github",
        "order",
        "git push",
        ["orquestacion", "seguridad"],
        "push",
        "Un cambio de código con su decisión D-xxx, con la cuenta del autor.",
        "pruebas.yml y calidad.yml corren sobre ese commit.",
    ),
    # D-469: the start of the weekly load: GitHub Actions runs semanal.yml by its cron (or the Autor, by hand).
    (
        "github",
        "semanal",
        "order",
        "martes 12:07 UTC",
        ["orquestacion"],
        "week",
        "GitHub Actions corre semanal.yml cada martes a las 12:07 UTC (cron 7,22,37,52 12-14 * * 2); el Autor también puede lanzarla "
        "a mano.",
        "Una máquina temporal con el repositorio, que corre los pasos de la carga.",
    ),
    (
        "semanal",
        "agent",
        "order",
        "lanza la carga",
        ["orquestacion"],
        "week",
        "Martes 12:07 UTC (cron 7,22,37,52 12-14 * * 2): una máquina de GitHub corre los pasos de la carga.",
        "Si un paso falla, los siguientes no corren.",
    ),
    (
        "semanal",
        "release",
        "order",
        "publica la base",
        ["orquestacion"],
        "week",
        "Solo si todo pasó: sube la base y hace el commit del puntero.",
        "El release y el puntero nuevos.",
    ),
    (
        "semanal",
        "ci",
        "order",
        "«pytest -m datos»",
        ["orquestacion", "calidad"],
        "week",
        "Las pruebas de datos sobre la base nueva, con la paridad.",
        "Verde para publicar, o la carga se detiene.",
    ),
    (
        "semanal",
        "github",
        "order",
        "puntero e «Informe semanal»",
        ["orquestacion", "observabilidad"],
        "week",
        "El commit «Weekly data update» y el issue «Informe semanal AAAA-MM-DD».",
        "El informe anterior queda cerrado (D-438).",
    ),
    (
        "release",
        "semanal",
        "flow",
        "base anterior",
        ["orquestacion"],
        "week",
        "Al empezar, la carga baja la Base DuckDB publicada.",
        "Sus filas del IPC, por si el INE no responde.",
    ),
    (
        "release",
        "ci",
        "flow",
        "base para las pruebas",
        ["calidad"],
        "push",
        "pruebas.yml baja la base publicada para probar el código contra datos reales.",
        "Nada: las pruebas solo la leen.",
    ),
    (
        "pypi",
        "semanal",
        "flow",
        "dependencias",
        ["orquestacion", "seguridad"],
        "week",
        "pip install -r requirements-pipeline.txt, cada dependencia con su tope.",
        "El entorno de la carga.",
    ),
    (
        "pypi",
        "pruebas",
        "flow",
        "dependencias",
        ["calidad"],
        "push",
        "Lo mismo en cada push, en Python 3.11 y 3.12.",
        "El entorno de las pruebas.",
    ),
    (
        "github",
        "pruebas",
        "order",
        "cada push",
        ["orquestacion", "calidad"],
        "push",
        "Cada push o pull request dispara pruebas.yml.",
        "Verde o rojo junto al commit.",
    ),
    (
        "github",
        "calidad",
        "order",
        "cada push",
        ["calidad"],
        "push",
        "Cada push dispara la medición de los 14 indicadores.",
        "La medición, como artefacto de la ejecución.",
    ),
    (
        "semanal",
        "calidad",
        "order",
        "carga en verde",
        ["calidad", "orquestacion"],
        "week",
        "Al terminar una carga en verde, calidad.yml escribe el informe semanal.",
        "El pull request «Actualizar medición de calidad».",
    ),
    (
        "calidad",
        "github",
        "order",
        "informe como pull request",
        ["calidad"],
        "week",
        "El informe semanal en una rama propia, con su pull request.",
        "La fusión, si los indicadores de código están en su aceptable (D-436).",
    ),
    (
        "pruebas",
        "ci",
        "order",
        "corre pytest",
        ["calidad"],
        "push",
        "ruff, mypy, dbt parse y la suite completa con su cobertura.",
        "Verde o rojo; nunca publica nada.",
    ),
    (
        "github",
        "stcloud",
        "order",
        "commit en main",
        ["orquestacion"],
        "push",
        "Cada commit en main queda disponible para el panel publicado.",
        "No verificado: si lo toma sin «Reboot».",
    ),
    (
        "stcloud",
        "streamlit",
        "order",
        "aloja el panel",
        ["navegador", "seguridad"],
        "always",
        "Corre bi/dashboard.py con sus secretos.",
        "Las páginas de cada visita.",
    ),
    (
        "devops",
        "semanal",
        "order",
        "lanza y cancela (GITHUB_TOKEN)",
        ["orquestacion", "seguridad"],
        "manual",
        "«Ejecutar pipeline ahora» pide a la API de GitHub un workflow_dispatch; «Cancelar» detiene la ejecución.",
        "El id de la ejecución, que la ventana sigue cada 4 segundos.",
    ),
    (
        "devops",
        "github",
        "check",
        "estado y logs (GITHUB_READ_TOKEN)",
        ["observabilidad"],
        "manual",
        "Consultas de solo lectura a la API: ejecuciones, pasos y logs.",
        "El estado de cada workflow, guardado 120 segundos.",
    ),
    (
        "streamlit",
        "github",
        "check",
        "estado en vivo (GITHUB_READ_TOKEN)",
        ["observabilidad"],
        "always",
        "El «Flujo del sistema en vivo» consulta la carga en curso.",
        "Los pasos de la carga; los logs solo para el Autor.",
    ),
    (
        "streamlit",
        "secrets",
        "check",
        "lee los secretos",
        ["seguridad"],
        "always",
        "El panel lee sus secretos de Streamlit Community Cloud.",
        "Nunca se muestran en pantalla ni en un error.",
    ),
    (
        "devops",
        "secrets",
        "check",
        "compara la clave, usa el token",
        ["seguridad"],
        "manual",
        "hmac.compare_digest compara CONTROL_CODE; GITHUB_TOKEN autoriza la orden.",
        "Entrar o no; tras 3 fallos, una espera creciente.",
    ),
    (
        "semanal",
        "author",
        "check",
        "correo si la carga falla",
        ["observabilidad"],
        "week",
        "GitHub envía el correo «Run failed».",
        "El Autor también ve «La carga del … falló» en el panel.",
    ),
    (
        "ci",
        "security",
        "order",
        "S-01 a S-14",
        ["seguridad", "calidad"],
        "push",
        "Los ataques convertidos en pruebas.",
        "Verde, o el push queda en rojo.",
    ),
    (
        "ci",
        "parity",
        "order",
        "corre la paridad",
        ["calidad"],
        "week",
        "La prueba que compara la Base DuckDB con el respaldo.",
        "Verde para publicar.",
    ),
    (
        "gates",
        "agent",
        "check",
        "encabezado",
        ["calidad"],
        "week",
        "Cada archivo debe traer las columnas esperadas.",
        "UNEXPECTED_HEADER detiene la carga.",
    ),
    (
        "gates",
        "dbt",
        "check",
        "pruebas y filas",
        ["calidad"],
        "week",
        "Las pruebas de dbt y las filas leídas frente a la última carga.",
        "Una falla detiene la carga.",
    ),
    (
        "gates",
        "release",
        "check",
        "publica solo si todo pasa",
        ["calidad"],
        "week",
        "La decisión final de la puerta.",
        "Publicar, o dejar la base como estaba.",
    ),
    (
        "parity",
        "sqlite",
        "check",
        "respaldo",
        ["calidad"],
        "week",
        "Las cifras del respaldo etl/datos.db.",
        "Lo que se compara.",
    ),
    (
        "parity",
        "duckdb",
        "check",
        "base nueva",
        ["calidad"],
        "week",
        "Las cifras de la Base DuckDB construida con dbt.",
        "Lo que se compara.",
    ),
    (
        "security",
        "streamlit",
        "check",
        "SQL con límites, clave y token",
        ["seguridad"],
        "push",
        "Las pruebas atacan la consulta SQL, la clave y el token.",
        "Cada ataque, rechazado.",
    ),
    (
        "security",
        "duckdb",
        "check",
        "solo lectura",
        ["seguridad"],
        "always",
        "El panel abre la base en solo lectura, sin archivos ni red.",
        "Una orden que escribe se rechaza.",
    ),
    (
        "security",
        "github",
        "check",
        "ningún secreto en Git",
        ["seguridad"],
        "push",
        "detect-secrets y una prueba revisan el repositorio.",
        "Ningún secreto versionado.",
    ),
    (
        "security",
        "semanal",
        "check",
        "permisos mínimos",
        ["seguridad"],
        "push",
        "semanal.yml solo escribe contenido e issues.",
        "Una prueba lo comprueba en cada push.",
    ),
    (
        "monitoring",
        "semanal",
        "check",
        "log de cada paso",
        ["observabilidad"],
        "week",
        "GitHub guarda el log de cada paso de cada carga.",
        "Lo que la página «GitHub Actions» muestra al Autor.",
    ),
    (
        "monitoring",
        "duckdb",
        "check",
        "etl_run y dbt_result",
        ["observabilidad"],
        "week",
        "Cada carga queda registrada con sus filas y el resultado de cada modelo.",
        "Las cifras de «Controles de datos».",
    ),
    (
        "measurement",
        "streamlit",
        "check",
        "una pantalla",
        ["calidad"],
        "manual",
        "medir.cjs abre cada página en Chrome a 1440 × 790 y 1920 × 1000.",
        "Si algo no cabe o se desborda.",
    ),
    (
        "docs",
        "streamlit",
        "support",
        "páginas y PDF",
        ["apoyo"],
        "push",
        "Los documentos de docs/ y docs/en/.",
        "Una página por documento y su PDF impreso.",
    ),
    (
        "ai",
        "docs",
        "support",
        "revisión, sin RAG",
        ["apoyo"],
        "manual",
        "Revisión técnica y de la documentación durante el desarrollo.",
        "Nada en la carga ni en el panel.",
    ),
]
# Where each line happens: (file, text that must be in it), or the platform that does it when no file of the project
# can show it. A test reads every file, so a line of the map cannot claim what the code does not do (D-293).
PLATFORM = "platform"
LINK_EVIDENCE = {
    ("odepa", "agent"): ("agent/input.csv", "precio_mayorista"),
    ("odepa_consumer", "agent"): ("agent/input.csv", "precio_consumidor"),
    ("ine", "agent"): ("etl/ine.py", "www.ine.gob.cl"),
    ("agent", "sqlite"): ("etl/etl.py", "def load_raw_files"),
    ("sqlite", "parquet"): ("etl/bronze.py", "pq.write_table"),
    ("agent", "parquet"): ("etl/ine.py", "pq.write_table"),
    ("parquet", "dbt"): ("dbt/models/staging/sources.yml", "read_parquet"),
    ("dbt", "duckdb"): ("dbt/profiles.yml", "type: duckdb"),
    ("duckdb", "release"): (".github/workflows/semanal.yml", "gh release upload base-actual etl/datos.duckdb"),
    ("release", "streamlit"): ("bi/served_database.py", "/releases/download/"),
    ("streamlit", "web"): ("bi/dashboard.py", "st.html("),
    ("streamlit", "charts"): ("bi/app_frame.py", "st.altair_chart("),
    ("visitor", "streamlit"): ("bi/app_frame.py", 'st.button(tr("Usuario")'),
    ("professional", "streamlit"): ("bi/sql_explorer.py", "ROW_LIMIT = 5000"),
    ("author", "devops"): ("bi/constants.py", 'SECRET_CONTROL_CODE = "CONTROL_CODE"'),
    ("author", "github"): (PLATFORM, "GitHub"),
    ("github", "semanal"): (".github/workflows/semanal.yml", 'cron: "7,22,37,52 12-14 * * 2"'),
    ("semanal", "agent"): (".github/workflows/semanal.yml", "run: python agent/agent.py"),
    ("semanal", "release"): (".github/workflows/semanal.yml", "gh release upload"),
    ("semanal", "ci"): (".github/workflows/semanal.yml", "run: pytest -q"),
    ("semanal", "github"): (".github/workflows/semanal.yml", "gh issue create"),
    ("release", "semanal"): (".github/workflows/semanal.yml", "run: python bi/served_database.py"),
    ("release", "ci"): (".github/workflows/pruebas.yml", "run: python bi/served_database.py"),
    ("pypi", "semanal"): (".github/workflows/semanal.yml", "pip install -r requirements-pipeline.txt"),
    ("pypi", "pruebas"): (".github/workflows/pruebas.yml", "pip install -r requirements-pipeline.txt"),
    ("github", "pruebas"): (".github/workflows/pruebas.yml", "push:"),
    ("github", "calidad"): (".github/workflows/calidad.yml", "push:"),
    ("semanal", "calidad"): (".github/workflows/calidad.yml", "workflows: [semanal]"),
    ("calidad", "github"): (".github/workflows/calidad.yml", "gh pr create"),
    ("pruebas", "ci"): (".github/workflows/pruebas.yml", "pytest -q"),
    ("github", "stcloud"): (PLATFORM, "Streamlit Cloud"),
    ("stcloud", "streamlit"): (PLATFORM, "Streamlit Cloud"),
    ("devops", "semanal"): ("bi/control.py", "/dispatches"),
    ("devops", "github"): ("bi/github_actions.py", "/logs"),
    ("streamlit", "github"): ("bi/control.py", "/actions/runs/"),
    ("streamlit", "secrets"): ("bi/data_access.py", "def get_secret"),
    ("devops", "secrets"): ("bi/control.py", "hmac.compare_digest"),
    ("semanal", "author"): (PLATFORM, "GitHub"),
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
    ("security", "semanal"): ("tests/test_security.py", "def test_the_weekly_job_has_least_privilege"),
    ("monitoring", "semanal"): ("bi/control.py", "/jobs"),
    ("monitoring", "duckdb"): ("etl/pipeline.py", "etl_run"),
    ("measurement", "streamlit"): ("tests/medicion/medir.cjs", "1440"),
    ("docs", "streamlit"): ("bi/page_documents.py", "PROJECT_DOCUMENTS = {"),
    ("ai", "docs"): ("CLAUDE.md", "docs/"),
}
# D-441: who owns what, as boxes behind the nodes: (owner, grid rows, grid columns, label). Solid for what the project
# wrote, dotted for what it does not control; the people have their own box, each one with its access line.
OWNER_BOXES = [
    ("proyecto", "1 / 2", "2 / 6", "Proyecto · workflows"),
    ("plataforma", "1 / 2", "6 / 10", "Plataformas externas"),
    ("fuente", "3 / 6", "1 / 2", "Externas"),  # under the header «Fuentes»: the column is too narrow for both words
    ("proyecto", "3 / 7", "2 / 9", "Proyecto GreenOcean"),
    ("persona", "3 / 6", "9 / 10", "Personas"),
]
# The walk through a Tuesday load (D-441): (one line, the nodes it lights, the lines it moves).
TOUR = [
    (
        "Martes 12:07 UTC: GitHub corre semanal.yml en una máquina temporal.",
        ["semanal", "github"],
        [("github", "semanal"), ("semanal", "agent")],
    ),
    ("Instala las dependencias de PyPI, cada una con su tope.", ["pypi", "semanal"], [("pypi", "semanal")]),
    (
        "Baja la base publicada y los CSV nuevos de ODEPA, y valida su encabezado; los años cerrados vienen de la caché.",
        ["release", "odepa", "odepa_consumer", "agent", "gates"],
        [("release", "semanal"), ("odepa", "agent"), ("odepa_consumer", "agent"), ("gates", "agent")],
    ),
    ("Las filas aterrizan en raw.db y etl/etl.py construye el respaldo.", ["agent", "sqlite"], [("agent", "sqlite")]),
    (
        "El bronce en Parquet, y el IPC del INE directo en bronce.",
        ["sqlite", "parquet", "ine"],
        [("sqlite", "parquet"), ("ine", "agent"), ("agent", "parquet")],
    ),
    (
        "dbt build: {models} modelos y {tests} pruebas.",
        ["parquet", "dbt", "duckdb"],
        [("parquet", "dbt"), ("dbt", "duckdb")],
    ),
    (
        "La puerta de publicación y pytest: filas, semanas, atraso de las fuentes y paridad.",
        ["gates", "ci", "parity"],
        [
            ("gates", "dbt"),
            ("semanal", "ci"),
            ("ci", "parity"),
            ("parity", "sqlite"),
            ("parity", "duckdb"),
            ("gates", "release"),
        ],
    ),
    (
        "Cada paso deja su log, y la carga, su registro en etl_run. Si algo falla, la carga se detiene y GitHub avisa al "
        "Autor por correo.",
        ["monitoring", "semanal", "author"],
        [("monitoring", "semanal"), ("monitoring", "duckdb"), ("semanal", "author")],
    ),
    (
        "Si todo pasó, la base sube al release y se abre el «Informe semanal».",
        ["duckdb", "release", "github"],
        [("duckdb", "release"), ("semanal", "release"), ("semanal", "github")],
    ),
    (
        "calidad.yml escribe el informe semanal y lo propone como pull request.",
        ["calidad", "github"],
        [("semanal", "calidad"), ("calidad", "github")],
    ),
    (
        "El panel ve el puntero nuevo, comprueba la huella y baja la base.",
        ["release", "streamlit"],
        [("release", "streamlit")],
    ),
    (
        "El Usuario y el Profesional ya ven la semana nueva.",
        ["visitor", "professional", "streamlit"],
        [("visitor", "streamlit"), ("professional", "streamlit")],
    ),
]


# D-467, D-468: what lights at rest, one line at a time, in the order the weekly load really runs: GitHub Actions starts
# semanal.yml on Tuesday (or the Autor, by hand); the job installs, takes the published database, downloads ODEPA, lands
# it, copies it to bronze, adds the IPC, builds with dbt, tests, publishes, reports; calidad.yml follows; Streamlit
# Community Cloud takes the new pointer and the panel serves the week to the people.
STORY = [
    ("github", "semanal", ""),
    ("pypi", "semanal", "pip install"),
    ("release", "semanal", "bi/served_database.py"),
    ("semanal", "agent", ""),
    ("odepa", "agent", "agent/agent.py"),
    ("odepa_consumer", "agent", ""),
    ("gates", "agent", "lo revisa agent.py al bajar"),
    ("agent", "sqlite", "etl/etl.py"),
    ("sqlite", "parquet", "etl/pipeline.py"),
    ("ine", "agent", "etl/ine.py"),
    ("agent", "parquet", ""),
    ("parquet", "dbt", "dbt build"),
    ("gates", "dbt", "las pruebas de dbt"),
    ("gates", "release", "fuente atrasada, pocas filas"),  # etl/pipeline.py, right after dbt, before the database
    ("dbt", "duckdb", "se escribe datos.duckdb"),
    ("semanal", "ci", ""),
    ("ci", "parity", ""),
    ("parity", "sqlite", ""),
    ("parity", "duckdb", ""),
    ("duckdb", "release", "gh release upload"),
    ("semanal", "github", ""),
    ("semanal", "calidad", "workflow_run"),
    ("calidad", "github", ""),
    ("github", "stcloud", ""),
    ("stcloud", "streamlit", ""),
    ("release", "streamlit", ""),
    ("streamlit", "web", ""),
    ("streamlit", "charts", ""),
    ("visitor", "streamlit", ""),
    ("professional", "streamlit", ""),
]
# D-471: the list beside the map groups the steps by who runs them, as the author read it.
STORY_GROUPS = [
    ("GitHub Actions (cron del martes)", 1),
    ("semanal.yml, un paso tras otro", 20),
    ("Después de la carga", 4),
    ("Cuando alguien abre el panel", 5),
]
STORY_TITLE = "La carga semanal, paso a paso"
STORY_PARALLEL = "Desde el paso 21, Streamlit Cloud toma el commit mientras GitHub abre el informe y corre calidad.yml."
PEOPLE_KEYS = {"visitor", "professional", "author"}
# endregion


# region «Mapa de la app»
def story_steps():
    """The story as [line index, towards a person]: each line in its turn, from GitHub's start to the people."""
    index = {link[:2]: number for number, link in enumerate(LINKS)}
    return [[index[(source, target)], source in PEOPLE_KEYS] for source, target, _ in STORY]


def build_story_list():
    """D-471: the steps of the weekly load beside the map, grouped by who runs them, each with the file that does it;
    the step in view lights up, and a click on a step shows its line."""
    names = {key: SHORT_NAMES.get(key, node[0]) for key, node in NODES.items()}
    rows, number = [], 0
    for title, count in STORY_GROUPS:
        rows.append(f'<p class="am-steps-group">{esc(title)}</p>')
        for source, target, note in STORY[number : number + count]:
            what = next(link[3] for link in LINKS if link[:2] == (source, target))
            rows.append(
                f'<button type="button" class="am-step" data-step="{number}"><b>{number + 1}</b>'
                f'<span>{esc(names[source])} → {esc(names[target])}: <i>{esc(what)}</i></span>'
                + (f"<code>{esc(note)}</code>" if note else "")
                + "</button>"
            )
            number += 1
    return (
        f'<aside class="am-steps" aria-label="{esc(STORY_TITLE)}"><div class="am-steps-in">'
        f'<p class="am-steps-title">{esc(STORY_TITLE)}</p>{"".join(rows)}'
        f'<p class="am-steps-note">{esc(STORY_PARALLEL)}</p></div></aside>'
    )


def evidence_label(source, target):
    """The short name of where a line happens: the file name, or the platform."""
    place, detail = LINK_EVIDENCE[(source, target)]
    return detail if place == PLATFORM else place.rsplit("/", 1)[-1]


ROWS = {"top": 1, "flow": 3, "flow2": 4, "web": 5, "watch": 6}
# Thin line icons for the nodes that are not a brand, drawn in the accent of the theme (24-unit grid).
LINE_ICONS = {
    # D-441: a workflow (a job that branches into steps), a release (a tagged package) and a gate (a barrier).
    "workflow": '<circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><rect x="14.5" y="9.5" width="6" '
    'height="5" rx="1.2"/><path d="M6 8.5v7"/><path d="M8.5 6h2.5a2.5 2.5 0 0 1 2.5 2.5V12h1"/>',
    "tag": '<path d="M3.5 12.5V4.5a1 1 0 0 1 1-1h8l8.5 8.5-9 9z"/><circle cx="8" cy="8" r="1.6"/>',
    "gate": '<path d="M4 21V5"/><path d="M20 21V5"/><path d="M4 9h16"/><path d="M4 14h16"/><path d="m8 9 4 5m0-5 4 5"/>',
    "shield": '<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "code": '<path d="m8 8-4 4 4 4"/><path d="m16 8 4 4-4 4"/><path d="m13.5 5-3 14"/>',
    "chart": '<path d="M4 20V4"/><path d="M4 20h16"/><path d="m7 15 4-5 3 3 5-7"/>',
    "parity": '<path d="M4 8h13"/><path d="m14 5 3 3-3 3"/><path d="M20 16H7"/><path d="m10 13-3 3 3 3"/>',
    "pulse": '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
    "files": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/>',
    "ruler": '<rect x="3" y="8" width="18" height="8" rx="1.5"/><path d="M7 8v3M11 8v4M15 8v3M19 8v4"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9"/><path d="m16 7 3 3"/><path d="m14 9 2 2"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4"/><path d="m6.5 6.5 2.5 2.5M15 15l2.5 2.5M17.5 6.5 15 9M9 15l-2.5 2.5"/>',
    "box": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4 7.5 8 4.5 8-4.5"/><path d="M12 12v9"/>',
    "cloud": '<path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.2 9.5 4.3 4.3 0 0 0 7 18z"/>',
    "console": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3"/><path d="M12 15h5"/>',
    "stop": '<circle cx="12" cy="12" r="9"/><path d="M9 9h6v6H9z"/>',
    "play": '<circle cx="12" cy="12" r="9"/><path d="m10 8 6 4-6 4z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
}
ROW_LABELS = {5: "Navegador y operación", 6: "Lo que vigila"}
KIND_COLORS = {"flow": "#3987e5", "order": "#c98500", "check": "#199e70", "support": "#8b8fa3", "access": "#e883a7"}
LINE_KINDS = [
    ("flow", "datos"),
    ("order", "órdenes"),
    ("check", "controles"),
    ("support", "apoyo"),
    ("access", "accesos"),
]
OWNER_STYLES = {"proyecto": "solid", "plataforma": "dashed", "fuente": "dashed", "persona": "dotted"}
OWNER_COLORS = {"proyecto": "#56b4e0", "plataforma": "#8b96a8", "fuente": "#3fb6a8", "persona": "#e883a7"}


def esc(value):
    return html.escape(str(value), quote=True)


def connections(key):
    """«→ dbt: fuentes», «← ODEPA: CSV»: what the node connects with, read from LINKS."""
    lines = [f"→ {NODES[link[1]][0]}: {link[3]}" for link in LINKS if link[0] == key]
    return lines + [f"← {NODES[link[0]][0]}: {link[3]}" for link in LINKS if link[1] == key]


def node_themes(key):
    """The themes of a node: its own, and those of every line that touches it, so a filter lights every node it involves."""
    themes = list(NODES[key][2])
    for link in LINKS:
        if key in link[:2]:
            themes += [theme for theme in link[4] if theme not in themes]
    return themes


def node_rhythms(key):
    """The rhythms of a node: its own and those of its lines, so a rhythm lights every node of its chain."""
    rhythms = [detail.CARDS[key][1]] if key in detail.CARDS else []
    for link in LINKS:
        if key in link[:2] and link[5] not in rhythms:
            rhythms.append(link[5])
    return rhythms


def logo_id(spec):
    """The name of a logo's CSS variable: «brand:python» → «lg-brand-python»."""
    return "lg-" + re.sub(r"[^a-z0-9]+", "-", spec.lower())


def logo_image(spec, palette):
    """A logo as an image (st.html drops inline SVG), without a background, in its own color. D-441: each logo is
    defined once on the map as a CSS variable (logo_sheet) and every piece that shows it points at it."""
    return f'<span class="am-logo" style="background-image:var(--{logo_id(spec)})"></span>'


def logo_sheet(specs, palette):
    """The CSS variables of every logo of the map and its insides, each one written once."""
    return "".join(f"--{logo_id(spec)}:url('{logo_data(spec, palette)}');" for spec in sorted(set(specs)))


def logo_data(spec, palette):
    """The logo as a data address, in its own color."""
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
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"


def build_tip(key):
    name, _, _, _, what, role, when, _, group = NODES[key]
    parts = [("Qué es", what), ("Rol en GreenOcean", role), ("Cuándo actúa", when)]
    left = f'<b class="am-tip-name">{esc(name)}</b>' + "".join(
        f"<i>{esc(head)}</i><span>{esc(text)}</span>" for head, text in parts
    )
    # Each connection names where it happens, so the reader can check it in the code.
    places = [evidence_label(*link[:2]) for link in LINKS if link[0] == key]
    places += [evidence_label(*link[:2]) for link in LINKS if link[1] == key]
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
    # D-473: the full card (its numbers, with the command that gives each one) opens from here
    more = f'<button type="button" class="am-tipcard" data-card="{key}">{esc("Ver la ficha completa")}</button>'
    return (
        f'<span class="am-tip" role="tooltip"><span class="am-tip-col">{left}{more}</span>'
        f'<span class="am-tip-col">{right}</span>{extra}</span>'
    )


# D-441: the name the map writes under a logo, when the full one would crowd the drawing. The full name stays in the
# piece's description (aria-label), its card and the caption under the map.
SHORT_NAMES = {
    "agent": "Agente",
    "release": "Release",
    "secrets": "Secretos",
    "stcloud": "Streamlit Cloud",
    "devops": "DevOps",
    "web": "HTML · CSS · JS",
    "charts": "Altair",
    "gates": "Puerta",
    "parity": "Paridad",
    "measurement": "Medición",
    "ai": "IA",
}


def build_node(key, palette):
    """A piece of the map. D-441: a click opens its card; the piece that sets a rhythm carries that rhythm's button."""
    name, logo, _, (row, column), *_, group = NODES[key]
    extra = f'<small class="am-more">+{len(group)}</small>' if group else ""
    chip = "".join(
        f'<button type="button" class="am-rchip" data-rhythm="{rhythm}">▶ {esc(label)}</button>'
        for rhythm, label in detail.RHYTHMS
        if detail.RHYTHM_OWNER[rhythm] == key
    )
    # Two small buttons beside the logo, as in the author's sketch: «i» opens the card (the text) and the magnifier goes
    # inside (how the tool works in GreenOcean). A click on the piece itself still opens the card.
    info = f'<button type="button" class="am-info" data-card="{key}" aria-label="{esc("Ver la ficha")}">i</button>'
    lupa = (
        f'<button type="button" class="am-lupa" data-inside="{key}" aria-label="{esc("Ver por dentro")}"></button>'
        if key in detail.INSIDES or key in detail.ENGINES
        else ""
    )
    return (
        f'<div class="am-node" role="button" tabindex="0" id="am-{key}" data-key="{key}" '
        f'data-themes="{" ".join(node_themes(key))}" data-rhythms="{" ".join(node_rhythms(key))}" '
        f'style="grid-row:{ROWS[row]};grid-column:{column}" aria-label="{esc(name)}">'
        f'{logo_image(logo, palette)}{info}{lupa}<b class="am-name">{esc(SHORT_NAMES.get(key, name))}{extra}</b>'
        f"{chip}{build_tip(key)}</div>"
    )


def build_card(key, facts, addresses):
    """The card of a piece (D-441): what it does, what it has inside, its numbers with the command that gives each one,
    what happens when it fails and why it is so, with its decision; a button opens its inside and a link its page."""
    name, _, _, _, what, role, when, page, group = NODES[key]
    owner, rhythm, fail, why, decisions = detail.CARDS[key]
    rhythm_label = dict(detail.RHYTHMS)[rhythm]
    inside = detail.inside_of(key, facts) or [tool for tool, _ in group]
    numbers = detail.numbers_of(key, facts)
    english = i18n.is_english()
    sections = [("Qué hace", f"<p>{esc(role)} {esc(when)}</p>")]
    if inside:
        sections.append(
            (
                "Qué tiene adentro",
                '<p class="am-chips">' + "".join(f"<span>{esc(item)}</span>" for item in inside) + "</p>",
            )
        )
    if numbers:
        sections.append(
            (
                "Los números",
                "<ul>"
                + "".join(
                    f'<li><b>{esc(value)}</b> {esc(label)} <code>{esc(command)}</code></li>'
                    for label, value, command in numbers
                )
                + "</ul>",
            )
        )
    if fail:
        sections.append(("Si algo falla", f"<p>{esc(fail)}</p>"))
    titles = [(reference, detail.read_decision(reference, english=english)) for reference in decisions]
    references = (
        "".join(
            f"<li><code>{esc(reference)}</code>{f' · {esc(title)}' if title else ''}</li>"
            for reference, title in titles
        )
        or f"<li>{esc('Sin decisión registrada para esta pieza.')}</li>"
    )
    sections.append(("Por qué lo hice así", f"<p>{esc(why)}</p><ul>{references}</ul>"))
    body = "".join(f'<div class="am-sec"><i>{esc(head)}</i>{content}</div>' for head, content in sections)
    zoom = (
        f'<button type="button" class="am-zoom" data-inside="{key}">⌕ {esc("Ver por dentro")}</button>'
        if key in detail.INSIDES or key in detail.ENGINES
        else ""
    )
    return (
        f'<section class="am-card" data-card="{key}" hidden role="dialog" aria-label="{esc(name)}">'
        f'<button type="button" class="am-close" aria-label="{esc("Cerrar")}">✕</button>'
        f'<p class="am-tags"><span class="am-tag o-{owner}">{esc(detail.OWNERS[owner])}</span>'
        f'<span class="am-tag r-{rhythm}">{esc(rhythm_label)}</span></p>'
        f'<h3>{esc(name)}</h3><p class="am-what">{esc(what)}</p>{body}'
        f'<p class="am-actions">{zoom}<a class="am-open" href="{esc(addresses.get(page, "#"))}" target="_self">'
        f'{esc("Abrir su página")} →</a></p></section>'
    )


def build_link_card(index, color):
    """The card of a line (D-441): what travels on it exactly, what comes back, how often and where it happens, under
    a bar of the line's own colour."""
    source, target, kind, what, _, rhythm, travels, returns = LINKS[index]
    place, text = LINK_EVIDENCE[(source, target)]
    where = text if place == PLATFORM else place
    return (
        f'<section class="am-card am-linkcard" data-link="{index}" hidden role="dialog">'
        f'<button type="button" class="am-close" aria-label="{esc("Cerrar")}">✕</button>'
        f'<p class="am-tags"><span class="am-tag k-{kind}">{esc(dict(LINE_KINDS)[kind])}</span>'
        f'<span class="am-tag r-{rhythm}">{esc(dict(detail.RHYTHMS)[rhythm])}</span></p>'
        f'<h3><span class="am-swatch" style="background:{color}"></span>{esc(NODES[source][0])} → '
        f"{esc(NODES[target][0])}</h3><p class=\"am-what\">{esc(what)}</p>"
        f'<div class="am-sec"><i>{esc("Qué viaja")}</i><p>{esc(travels)}</p></div>'
        f'<div class="am-sec"><i>{esc("Qué vuelve")}</i><p>{esc(returns)}</p></div>'
        f'<div class="am-sec"><i>{esc("Dónde ocurre")}</i><p><code>{esc(where)}</code></p></div></section>'
    )


def inside_views(key, facts):
    """The views of a piece's magnifier (D-441): how the tool itself works, then what it does in GreenOcean."""
    views = []
    if key in detail.ENGINES:
        views.append(("engine", "Cómo funciona", detail.ENGINES[key](facts)))
    if key in detail.INSIDES:
        views.append(("app", "En GreenOcean", detail.INSIDES[key](facts)))
    return views


def build_istage(prefix, inside, palette):
    """One drawing of a magnifier: its columns, logos and lines, drawn like the map."""
    columns = inside["columns"]
    cells = []
    for column, (header, items) in enumerate(columns, start=1):
        cells.append(f'<span class="am-layer" style="grid-column:{column}">{esc(header)}</span>')
        for place, item in enumerate(items, start=1):
            row = (item.get("row") or place) + 1
            tip = (
                f'<span class="am-tip am-itip" role="tooltip"><span class="am-tip-col"><b class="am-tip-name">'
                f'{esc(item["name"])}</b><span>{esc(item["what"])}</span></span></span>'
                if item["what"]
                else ""
            )
            sub = f'<small class="am-sub">{esc(item["sub"])}</small>' if item["sub"] else ""
            cells.append(
                f'<div class="am-node am-inode" tabindex="0" id="am-{esc(prefix)}-{esc(item["id"])}" '
                f'data-key="{esc(prefix)}-{esc(item["id"])}" style="grid-row:{row};grid-column:{column}">'
                f'{logo_image(item["logo"], palette)}<b class="am-name">{esc(item["name"])}</b>{sub}{tip}</div>'
            )
    colors = line_colors(palette, len(inside["links"]))
    links = esc(
        json.dumps(
            [
                [f"{prefix}-{a}", f"{prefix}-{b}", label, dash, color]
                for (a, b, label, dash), color in zip(inside["links"], colors)
            ]
        )
    )
    labels = "".join(f"<span>{esc(label)}</span>" for _, _, label, _ in inside["links"])
    return (
        f'<div class="am-stage am-istage" data-links="{links}" '
        f'style="grid-template-columns:repeat({len(columns)}, minmax(0, 1fr))">{"".join(cells)}</div>'
        f'<div class="am-ilabels" hidden>{labels}</div>'
    )


def build_inside(key, facts, palette):
    """The magnifier of a piece (D-441). A tool has two views, how it works and what it does here, behind two
    buttons; a piece of the project has only the second."""
    views = inside_views(key, facts)
    buttons = (
        '<div class="am-views" role="group">'
        + "".join(
            f'<button type="button" class="am-vbtn{" on" if number == 0 else ""}" data-view="{view}">{esc(label)}</button>'
            for number, (view, label, _) in enumerate(views)
        )
        + "</div>"
        if len(views) > 1
        else ""
    )
    drawings = "".join(
        f'<div class="am-view" data-view="{view}"{" hidden" if number else ""}>'
        f"{build_istage(f'{key}-{view}', inside, palette)}</div>"
        for number, (view, _, inside) in enumerate(views)
    )
    return f'<section class="am-inside" data-inside="{key}" hidden>{buttons}{drawings}</section>'


def tour_steps(facts):
    """The steps of the Tuesday walk, with the figures of dbt read from dbt_node."""
    index = {link[:2]: number for number, link in enumerate(LINKS)}
    models, tests = detail.count_kind(facts, "model"), detail.count_kind(facts, "test")
    return [
        (text.format(models=models, tests=tests), nodes, [index[pair] for pair in pairs]) for text, nodes, pairs in TOUR
    ]


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
        f".am-line.k-{kind} {{ stroke:{color}; }}"
        f" .am-tag.k-{kind} {{ color:{color}; }} .am-msg.k-{kind} {{ fill:{color}; }}"
        for kind, color in KIND_COLORS.items()
    )
    owners = "".join(
        f".am-own.o-{owner} {{ border:1.5px {OWNER_STYLES[owner]} color-mix(in srgb, {color} 70%, transparent); }}"
        f" .am-own.o-{owner} span {{ color:{color}; }} .am-tag.o-{owner} {{ color:{color}; }}"
        for owner, color in OWNER_COLORS.items()
    )
    rhythm_colors = {"week": "#f0b347", "month": "#3fb6a8", "push": "#a78bfa", "manual": "#56b4e0", "always": "#4ade80"}
    rhythms = "".join(
        f".am-tag.r-{rhythm}, .am-rchip[data-rhythm={rhythm}], .am-rbtn[data-rhythm={rhythm}] {{ color:{color}; }}"
        for rhythm, color in rhythm_colors.items()
    )
    return f"""<style>
.am {{ position:relative; display:flex; flex-direction:column; gap:6px; color:{text}; container:am / inline-size; }}
.am-bar {{ display:flex; flex-wrap:wrap; align-items:center; gap:6px 14px; font-size:12px; }}
.am-filters, .am-rhythms {{ display:flex; flex-wrap:wrap; align-items:center; gap:4px; }}
.am-filter, .am-rbtn, .am-tourbtn, .am-vbtn {{ font:inherit; font-size:12px; padding:3px 10px; border-radius:9px; cursor:pointer;
  color:{ink}; border:1px solid {border}; background:transparent; }}
.am-rbtn {{ color:inherit; }}
.am-filter:hover, .am-filter:focus-visible, .am-vbtn:hover, .am-vbtn:focus-visible, .am-rbtn:hover, .am-rbtn:focus-visible, .am-tourbtn:hover,
.am-tourbtn:focus-visible {{ border-color:{accent}; outline:none; }}
.am-filter.on, .am-rbtn.on {{ border-color:currentColor; background:color-mix(in srgb, currentColor 14%, transparent); }}
.am-filter.on, .am-vbtn.on {{ border-color:{accent}; background:color-mix(in srgb, {accent} 14%, transparent); }}
.am-tourbtn {{ border-color:#f0b347; color:#f0b347; font-weight:600; }}
/* D-441: the map can take the whole window; its rows then spread out so the lines and their labels have room. */
.am-fullbtn {{ margin-left:auto; font:inherit; font-size:12px; padding:3px 10px; border-radius:9px; cursor:pointer;
  color:{ink}; border:1px solid {border}; background:transparent; }}
.am-fullbtn:hover, .am-fullbtn:focus-visible {{ border-color:{accent}; outline:none; }}
.am-close-full, .am.am-full .am-open-full {{ display:none; }} .am.am-full .am-close-full {{ display:inline; }}
.am.am-full {{ position:fixed; inset:0; z-index:1000000; height:100vh; padding:14px 26px 10px; overflow:auto;
  background:var(--am-surface); }}
/* D-472: on the whole screen the right column is the list of the load's steps, not an empty frame waiting for a
   description: a description, opened with its «i», shows over it while it is read. */
.am.am-full .am-row {{ flex:1 1 auto; min-height:0; }}
.am.am-full .am-main {{ flex:1 1 auto; min-height:0; grid-template-rows:auto auto 1fr 1fr 1fr 1fr; }}
.am.am-full .am-main .am-node {{ align-self:center; }}
.am-tourbtn.on {{ background:color-mix(in srgb, #f0b347 16%, transparent); }}
.am-rhythms > em {{ font-style:normal; color:{muted}; margin-right:2px; }}
.am-legend {{ display:flex; flex-wrap:wrap; gap:12px; color:{muted}; margin-left:auto; }}
.am-key {{ display:inline-flex; align-items:center; gap:6px; }}
/* D-441: each line has a colour of its own; the legend tells the kind by the stroke. */
.am-key::before {{ content:""; width:22px; height:2px; border-radius:2px; background:{muted}; }}
.am-key.k-order::before {{ height:0; border-top:2px dashed {muted}; background:none; }}
.am-key.k-check::before {{ height:0; border-top:2px dotted {muted}; background:none; }}
.am-key.k-support::before {{ height:1px; }} .am-key.k-access::before {{ height:3px; }}
.am-key.o-solid::before {{ height:10px; width:16px; background:none; border:1.5px solid {muted}; border-radius:3px; }}
.am-key.o-dashed::before {{ height:10px; width:16px; background:none; border:1.5px dashed {muted}; border-radius:3px; }}
.am-stage {{ position:relative; display:grid; grid-template-columns:repeat(9, minmax(0, 1fr));
  grid-template-rows:auto auto auto auto auto auto; gap:14px 10px; padding:6px 0 4px; }}
/* D-441: room for the lines to breathe: the outside columns a little narrower and further from the project; the
   sources and the people keep a wide aisle to the project box, where their lines and labels run. */
@container am (min-width:900px) {{
  .am-main > [style$="grid-column:1"], .am-main > .am-own[style$="grid-column:1 / 2"] {{ margin-right:26px; }}
  .am-main > [style$="grid-column:9"], .am-main > .am-own[style$="grid-column:9 / 10"] {{ margin-left:26px; }}
}}
.am-main {{ grid-template-columns:minmax(0, .88fr) repeat(7, minmax(0, 1fr)) minmax(0, .88fr); column-gap:16px; }}
.am-istage {{ grid-template-rows:none; grid-auto-rows:auto; padding-top:10px; }}
.am-views {{ display:flex; gap:4px; margin-bottom:4px; }}
/* D-441: the second bar (rhythms and the Tuesday walk) costs a row: the map rows sit closer to keep one screen. */
.am-main {{ row-gap:6px; }} .am-main .am-node {{ padding:2px 4px; }} .am-main .am-layer {{ margin-bottom:8px; }}
/* D-469: room over the top row, where the line from GitHub to semanal.yml runs with its label. */
.am-main {{ margin-top:16px; }}
/* D-471: the steps of the load beside the map, as tall as the map, scrolling on their own. */
.am-row {{ display:flex; gap:16px; align-items:stretch; }}
.am-row > .am-main {{ flex:1 1 auto; min-width:0; }}
.am-steps {{ position:relative; flex:0 0 280px; margin-top:16px; border-left:1px solid {border}; }}
.am-steps-in {{ position:absolute; inset:0; overflow-y:auto; padding:0 4px 0 12px; scrollbar-width:thin; }}
.am-steps-title {{ margin:0 0 6px; font-size:12.5px; font-weight:700; color:{ink}; }}
.am-steps-group {{ margin:8px 0 3px; font-size:10.5px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  color:{muted}; }}
.am-step {{ display:grid; grid-template-columns:22px 1fr; column-gap:6px; width:100%; padding:3px 6px; margin:0;
  border:0; border-radius:7px; background:transparent; color:{text}; font:inherit; font-size:11.5px; line-height:1.35;
  text-align:left; cursor:pointer; }}
.am-step b {{ color:{muted}; font-weight:600; text-align:right; font-variant-numeric:tabular-nums; }}
.am-step i {{ font-style:normal; color:{muted}; }}
.am-step code {{ grid-column:2; font-size:10.5px; color:{muted}; }}
.am-step:hover, .am-step:focus-visible {{ background:color-mix(in srgb, {accent} 10%, transparent); outline:none; }}
.am-step.now {{ background:color-mix(in srgb, #f0b347 16%, transparent); box-shadow:inset 2px 0 0 #f0b347; color:{ink}; }}
.am-step.now b {{ color:#f0b347; }}
.am-steps-note {{ margin:8px 0 4px; font-size:10.5px; line-height:1.4; color:{muted}; }}
@container am (max-width:900px) {{ .am-steps {{ display:none; }} }}
/* D-441: the pieces of the map fill their space: bigger logos, with «i» and the magnifier beside them. */
.am-main .am-logo {{ width:36px; height:36px; }}
.am-lines {{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; overflow:visible; z-index:1; }}
.am-line {{ fill:none; stroke-width:1.6; opacity:0; transition:opacity .15s ease; }}
.am-line.base {{ opacity:.6; }}
.am-hit {{ fill:none; stroke:transparent; stroke-width:12; pointer-events:none; cursor:pointer; }}
.am-hit.live {{ pointer-events:stroke; }}
/* D-468: no moving dot: the line of each step blinks on its turn, and its two ends stand out. */
.am-msg {{ display:none !important; }}
@keyframes am-blink {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
.am .am-main .am-line.blink {{ opacity:1 !important; stroke-width:2.6px; animation:am-blink .35s ease-out; }}
/* D-469: at rest one line shows at a time, in the order the load runs; every other line and label waits hidden. */
.am.telling .am-main .am-line:not(.blink), .am.telling .am-main .am-label:not(.story) {{ opacity:0 !important; }}
.am .am-main .am-label.story {{ opacity:1 !important; }}
.am .am-main .am-node.lit {{ background:color-mix(in srgb, #f0b347 14%, transparent); box-shadow:0 0 0 1.5px #f0b347 inset; }}
.am-tip code.am-src {{ font-size:10.5px; padding:0 4px; border-radius:4px; color:{muted};
  background:color-mix(in srgb, {border} 45%, transparent); }}
.am-label {{ font-size:10.5px; font-weight:500; fill:{text}; stroke:var(--am-surface, transparent); stroke-width:4px;
  paint-order:stroke; stroke-linejoin:round; opacity:0; transition:opacity .15s ease; }}
.am-line.k-order {{ stroke-dasharray:6 5; }} .am-line.k-check {{ stroke-dasharray:2 4; }} .am-line.k-support {{ stroke-width:1.2; }}
.am-line.k-access {{ stroke-width:2.6; }} .am-line.dash {{ stroke-dasharray:5 5; }}
.am-swatch {{ display:inline-block; width:22px; height:4px; border-radius:2px; margin-right:10px; vertical-align:middle; }}
.am-line.am-arrow {{ stroke-dasharray:none; stroke-linecap:round; stroke-linejoin:round; }}
{kinds}
{owners}
{rhythms}
.am-layer {{ grid-row:2; font-size:10.5px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{muted};
  text-align:center; border-bottom:1px solid color-mix(in srgb, {border} 70%, transparent); padding-bottom:4px; }}
.am-istage .am-layer {{ grid-row:1; }}
/* D-441: the compartments stand apart (about 4 mm between boxes), and inside the project each band is a step darker:
   the application, then «Navegador y operación», then «Lo que vigila». What is outside the project keeps the page. */
.am-own {{ align-self:stretch; justify-self:stretch; border-radius:14px; position:relative; z-index:0; margin:-6px 4px; }}
.am-shade {{ grid-column:2 / 9; align-self:stretch; justify-self:stretch; position:relative; z-index:0; margin:-3px 6px -2px; }}
.am-shade.s-1 {{ background:color-mix(in srgb, {text} 5%, transparent); }}
.am-shade.s-2 {{ background:color-mix(in srgb, {text} 10%, transparent); border-radius:0 0 11px 11px; }}
.am-own span {{ position:absolute; top:-8px; left:12px; padding:0 6px; font-size:10.5px; font-weight:700;
  letter-spacing:.08em; text-transform:uppercase; background:var(--am-surface, transparent); white-space:nowrap; }}
.am-band {{ grid-column:2 / 9; align-self:start; border-top:0;
  position:relative; z-index:0; height:0; margin-top:-7px; }}
.am-band span {{ position:absolute; top:-8px; left:12px; padding:0 6px; font-size:10px; font-weight:600;
  letter-spacing:.08em; text-transform:uppercase; color:{muted}; background:var(--am-surface, transparent); }}
.am-node {{ position:relative; z-index:2; display:flex; flex-direction:column; align-items:center; gap:4px;
  padding:6px 4px; border-radius:10px; text-decoration:none !important; color:{ink} !important; min-width:0;
  cursor:pointer; transition:opacity .15s ease, background .15s ease; }}
.am-node:hover, .am-node:focus-visible {{ background:color-mix(in srgb, {accent} 10%, transparent); outline:none; z-index:5; }}
.am-node.tour {{ background:color-mix(in srgb, #f0b347 16%, transparent); box-shadow:0 0 0 1.5px #f0b347 inset; }}
.am-logo {{ width:30px; height:30px; display:block; background-position:center; background-size:contain;
  background-repeat:no-repeat; }}
.am [hidden] {{ display:none !important; }}
.am.has-card .am-tip {{ display:none !important; }}
.am-name {{ font-size:12px; font-weight:600; line-height:1.25; text-align:center; overflow-wrap:break-word; }}
.am-sub {{ font-size:10.5px; color:{muted}; text-align:center; line-height:1.25; overflow-wrap:anywhere; }}
.am-inode {{ cursor:default; }}
/* A line that runs down a column passes behind the names, never through them. */
.am-istage .am-name, .am-istage .am-sub {{ background:{palette["background"]}; padding:0 3px; }}
.am-more {{ margin-left:4px; font-size:10.5px; font-weight:500; color:{accent}; }}
/* D-467: the «i» and the magnifier sit on the logo's upper corners, part of the piece, not beside it. */
.am-lupa {{ position:absolute; top:3px; left:calc(50% + 7px); width:15px; height:15px; padding:0; border-radius:50%;
  cursor:zoom-in; color:{accent};
  border:1px solid color-mix(in srgb, {accent} 60%, transparent); background:var(--am-surface, transparent); z-index:3; }}
.am-lupa:hover, .am-lupa:focus-visible {{ background:color-mix(in srgb, {accent} 22%, transparent); outline:none; }}
.am-info {{ position:absolute; top:3px; right:calc(50% + 7px); width:15px; height:15px; padding:0; border-radius:50%;
  cursor:pointer; color:{accent}; border:1px solid color-mix(in srgb, {accent} 60%, transparent);
  background:var(--am-surface, transparent); z-index:3; font:italic 700 10px/13px Georgia, serif; text-align:center; }}
.am-info:hover, .am-info:focus-visible {{ background:color-mix(in srgb, {accent} 22%, transparent); outline:none; }}
/* A magnifier drawn with CSS (st.html drops inline SVG): a ring and its handle. */
.am-lupa::before {{ content:""; position:absolute; left:2.5px; top:2.5px; width:5.5px; height:5.5px; border-radius:50%;
  border:1.5px solid currentColor; }}
.am-lupa::after {{ content:""; position:absolute; left:9px; top:9.5px; width:3.5px; height:1.5px; background:currentColor;
  transform:rotate(45deg); transform-origin:left center; border-radius:1px; }}
.am-rchip {{ font:inherit; font-size:10px; font-weight:600; padding:1px 7px; border-radius:8px; cursor:pointer;
  border:1px solid currentColor; background:color-mix(in srgb, currentColor 8%, transparent); white-space:nowrap; }}
.am-rchip:hover, .am-rchip:focus-visible {{ background:color-mix(in srgb, currentColor 22%, transparent); outline:none; }}
.am-tip {{ position:absolute; top:calc(100% + 4px); left:50%; transform:translateX(-50%); width:min(800px, 66vw); z-index:20;
  display:none; grid-auto-flow:column; grid-auto-columns:minmax(0, 1fr); gap:0 16px; padding:10px 14px; border-radius:12px;
  text-align:left; pointer-events:none; overflow:hidden;
  background:{card}; border:1px solid {border}; box-shadow:0 18px 40px -18px rgba(0,0,0,.45); color:{text};
  font-size:12px; font-weight:400; line-height:1.4; }}
.am-itip {{ width:min(320px, 70vw); }}
.am-tip-col {{ display:flex; flex-direction:column; gap:2px; min-width:0; }}
.am-tip i {{ margin-top:5px; font-style:normal; font-size:10.5px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:{muted}; }}
.am-tip b {{ color:{ink}; font-weight:600; }}
.am-tip-name {{ font-size:13px; }}
.am-tipcard {{ pointer-events:auto; align-self:flex-start; margin-top:8px; padding:3px 9px; border-radius:8px; cursor:pointer; font:inherit;
  font-size:11.5px; font-weight:600; color:{accent}; border:1px solid color-mix(in srgb, {accent} 55%, transparent);
  background:transparent; }}
.am-tipcard::after {{ content:" →"; }}
.am-tipcard:hover, .am-tipcard:focus-visible {{ background:color-mix(in srgb, {accent} 16%, transparent); outline:none; }}
.am-node.tipped .am-tip {{ display:grid; }}
.am-node[style*="grid-column:1"] .am-tip, .am-node[style*="grid-column:2"] .am-tip,
.am-node[style*="grid-column:3"] .am-tip {{ left:0; transform:none; }}
.am-node[style*="grid-column:7"] .am-tip, .am-node[style*="grid-column:8"] .am-tip,
.am-node[style*="grid-column:9"] .am-tip {{ left:auto; right:0; transform:none; }}
.am-node[style*="grid-row:6"] .am-tip, .am-node[style*="grid-row:5"] .am-tip {{ top:auto; bottom:calc(100% + 4px); }}
.am.has-focus .am-main .am-node:not(.on), .am[data-filter] .am-main .am-node.dim, .am[data-rhythm] .am-main .am-node.dim,
.am.touring .am-main .am-node:not(.tour) {{ opacity:.22; }}
.am[data-filter] .am-main .am-node:not(.end), .am[data-rhythm] .am-main .am-node:not(.end) {{ opacity:.22; }}
.am[data-filter] .am-main .am-node.end, .am[data-rhythm] .am-main .am-node.end {{ opacity:1; }}
.am[data-filter] .am-main .am-line, .am[data-rhythm] .am-main .am-line, .am.touring .am-main .am-line {{ opacity:0; }}
.am[data-filter] .am-line.show, .am[data-rhythm] .am-line.show, .am.touring .am-line.show {{ opacity:.95; stroke-width:2; }}
.am[data-filter] .am-label.show, .am[data-rhythm] .am-label.show, .am.touring .am-label.show {{ opacity:1; }}
.am.has-focus .am-main .am-line, .am.has-focus .am-main .am-label {{ opacity:0; }}
.am.has-focus .am-line.on {{ opacity:1; stroke-width:2.2; }}
.am.has-focus .am-label.on {{ opacity:1; }}
/* D-441: every visible line says what it carries: at rest the lines always drawn, with a theme or a rhythm its lines,
   under the cursor the lines of that piece; the cursor on a line brings its label forward. */
.am:not([data-filter]):not([data-rhythm]):not(.touring):not(.has-focus) .am-main .am-label.base {{ opacity:1; }}
.am .am-main .am-label.tight {{ opacity:0 !important; }} .am .am-main .am-label.peek {{ opacity:1 !important; }}
.am-istage .am-line {{ opacity:.6; }} .am-istage .am-label {{ opacity:1; }}
.am-crumb {{ display:flex; align-items:center; gap:10px; font-size:12.5px; }}
.am-crumb button {{ font:inherit; font-weight:600; padding:4px 12px; border-radius:9px; cursor:pointer; color:{ink};
  border:1px solid {border}; background:transparent; }}
.am-crumb button:hover, .am-crumb button:focus-visible {{ border-color:{accent}; outline:none; }}
.am-crumb b {{ color:{ink}; }}
.am-card {{ position:absolute; z-index:60; top:44px; left:50%; transform:translateX(-50%); width:min(620px, 96%);
  max-height:calc(100% - 52px); overflow:auto; padding:16px 18px 12px; border-radius:16px; background:{card};
  border:1px solid {border}; box-shadow:0 24px 70px -20px rgba(0,0,0,.7); color:{text}; font-size:13px; line-height:1.45; }}
.am-card h3 {{ margin:2px 0 2px; font-size:18px; color:{ink}; }}
.am-card .am-what {{ margin:0 0 8px; color:{muted}; font-size:12px; }}
.am-close {{ position:absolute; top:10px; right:10px; width:28px; height:28px; border-radius:50%; cursor:pointer;
  color:{muted}; border:1px solid {border}; background:transparent; font:inherit; }}
.am-close:hover, .am-close:focus-visible {{ color:{ink}; border-color:{accent}; outline:none; }}
.am-tags {{ display:flex; flex-wrap:wrap; gap:6px; margin:0 36px 6px 0; }}
.am-tag {{ font-size:11px; font-weight:600; padding:1px 9px; border-radius:999px; border:1px solid currentColor; }}
.am-sec {{ border-top:1px solid color-mix(in srgb, {border} 70%, transparent); padding:8px 0; }}
.am-sec > i {{ display:block; font-style:normal; font-size:10.5px; font-weight:600; letter-spacing:.08em;
  text-transform:uppercase; color:{muted}; margin-bottom:3px; }}
.am-sec p, .am-sec ul {{ margin:0; }} .am-sec ul {{ padding-left:18px; }}
.am-sec li b {{ color:#f0b347; font-variant-numeric:tabular-nums; }}
.am-sec code {{ font-size:11px; padding:0 4px; border-radius:4px; color:{muted};
  background:color-mix(in srgb, {border} 45%, transparent); }}
.am-chips {{ display:flex; flex-wrap:wrap; gap:5px; }}
.am-chips span {{ font-size:11.5px; padding:2px 8px; border-radius:7px; border:1px solid color-mix(in srgb, {border} 80%, transparent); }}
.am-actions {{ display:flex; flex-wrap:wrap; gap:10px; margin:10px 0 2px; }}
.am-zoom, .am-open {{ font:inherit; font-weight:600; font-size:12.5px; padding:6px 12px; border-radius:10px; cursor:pointer;
  border:1px solid {border}; background:transparent; color:{ink} !important; text-decoration:none !important; }}
.am-zoom {{ border-color:{accent}; color:{accent} !important; }}
.am-zoom:hover, .am-open:hover, .am-zoom:focus-visible, .am-open:focus-visible {{ background:color-mix(in srgb, {accent} 12%, transparent); outline:none; }}
.am-caption {{ margin:0; font-size:12.5px; color:{ink}; }}
.am-caption b {{ color:#f0b347; margin-right:8px; font-variant-numeric:tabular-nums; }}
/* D-441: the legend sits under the map; inside a piece or during the walk its place goes to what is on screen. */
.am-foot {{ font-size:11.5px; }}
.am-crumb:not([hidden]) ~ .am-foot {{ display:none; }}
.am-caption:not([hidden]) ~ .am-foot {{ display:none; }}
/* D-441: a narrow window (a tablet, a phone) keeps the same drawing, scaled down like a picture; a tap opens the card
   and «Pantalla completa» shows it large. Hover descriptions have no place on a miniature. */
.am.am-mini .am-main .am-tip {{ display:none !important; }}
/* D-324: nine columns of about 90 px: the layer names and the node names shrink to fit instead of running into each other. */
@container am (max-width:1200px) {{
  .am-layer {{ font-size:10px; letter-spacing:0; text-transform:none; }} .am-name {{ font-size:11px; }} .am-more {{ font-size:10px; }}
  .am-own span {{ font-size:9.5px; letter-spacing:.04em; }}
}}
@media (min-width:1700px) and (min-height:950px) {{
  .am-stage {{ row-gap:30px; }} .am-logo {{ width:40px; height:40px; }} .am-name {{ font-size:13.5px; }}
  .am-node {{ padding:10px 6px; }} .am-layer {{ font-size:11.5px; }}
}}
@media (prefers-reduced-motion:reduce) {{ .am-node, .am-line {{ transition:none; }} .am-msg {{ display:none; }} }}
</style>"""


# Draws the lines once the nodes have their place, again on every resize; highlights the path of the node under the
# cursor; a theme or a rhythm dims what is outside it. D-441: a dot travels along the lines that are moving; a click on
# a piece opens its card, on a line what travels on it; the magnifier opens the inside of a piece; the Tuesday walk
# lights one step at a time. No HTML and no «less than» sign in the script (st.html would drop it).
SCRIPT = "<script>" + static_files.read("app_map.js") + "</script>"  # D-543: the script lives in bi/static/app_map.js


def rhythm_phases():
    """The steps in which each rhythm moves: a rhythm the Tuesday walk covers moves step by step, in the order of the
    walk; any other moves all at once (an empty list)."""
    index = {link[:2]: number for number, link in enumerate(LINKS)}
    phases = {}
    for rhythm, _ in detail.RHYTHMS:
        steps = [[index[pair] for pair in pairs if LINKS[index[pair]][5] == rhythm] for _, _, pairs in TOUR]
        steps = [step for step in steps if step]
        phases[rhythm] = steps if len(steps) > 1 else []
    return phases


def line_colors(palette, count=None):
    """D-441: one colour per line, told apart by hue (the golden angle between neighbours) and by three steps of
    lightness, and kept at 3:1 on the theme's background (WCAG 2.1 for graphics): each line reads on its own in a dark
    theme and in a light one."""
    background = palette["background"]
    levels = (0.64, 0.54, 0.74) if charts.relative_luminance(background) < 0.18 else (0.40, 0.31, 0.49)
    colors = []
    for index in range(len(LINKS) if count is None else count):
        red, green, blue = colorsys.hls_to_rgb((index * 137.508 + 210) % 360 / 360, levels[index % 3], 0.78)
        color = "#{:02x}{:02x}{:02x}".format(*(round(channel * 255) for channel in (red, green, blue)))
        colors.append(charts.legible(color, background, 3))
    return colors


def is_base(kind, themes):
    """A line drawn at rest: the data and the browser flow, and the access of each person. Decided here and not in the
    script, where the English layer would turn the theme «datos» into «data» (D-441)."""
    return (kind == "flow" and bool({"datos", "navegador"} & set(themes))) or kind == "access"


def build_map_html(palette, addresses, facts=None):
    """The whole map: filters, rhythms and legend, the owner boxes, the layers and the nodes; behind them, the card of
    every piece and every line and the inside of every piece. The script adds the lines and their moving dots."""
    filters = "".join(
        f'<button type="button" class="am-filter" data-theme="{key}">{esc(label)}</button>' for key, label in THEMES
    )
    rhythms = "".join(
        f'<button type="button" class="am-rbtn" data-rhythm="{key}">{esc(label)}</button>'
        for key, label in detail.RHYTHMS
    )
    legend = "".join(f'<span class="am-key k-{kind}">{esc(label)}</span>' for kind, label in LINE_KINDS)
    legend += (
        f'<span class="am-key o-solid">{esc("propio")}</span><span class="am-key o-dashed">{esc("externo")}</span>'
    )
    layers = "".join(
        f'<span class="am-layer" style="grid-column:{index}">{esc(name)}</span>'
        for index, name in enumerate(LAYERS, start=1)
    )
    # D-467: no owner boxes and no shaded bands: their edges crossed the lines. A row keeps only its name.
    bands = "".join(
        f'<div class="am-band" style="grid-row:{row}"><span>{esc(label)}</span></div>'
        for row, label in ROW_LABELS.items()
    )
    nodes = "".join(build_node(key, palette) for key in NODES)
    data = esc(
        json.dumps(
            [
                [source, target, kind, themes, rhythm, is_base(kind, themes), color]
                for (source, target, kind, _, themes, rhythm, *_), color in zip(LINKS, line_colors(palette))
            ]
        )
    )
    # The label of each line is a text node, not part of the data, so the translation layer reaches it (D-284).
    whats = "".join(f"<span>{esc(link[3])}</span>" for link in LINKS)
    cards = "".join(build_card(key, facts, addresses) for key in NODES)
    colors = line_colors(palette)
    cards += "".join(build_link_card(index, colors[index]) for index in range(len(LINKS)))
    insides = "".join(build_inside(key, facts, palette) for key in NODES if inside_views(key, facts))
    specs = [node[1] for node in NODES.values()] + [
        item["logo"]
        for key in NODES
        for _, _, inside in inside_views(key, facts)
        for _, items in inside["columns"]
        for item in items
    ]
    tour = "".join(
        f'<span data-nodes="{" ".join(nodes_)}" data-links="{" ".join(map(str, indexes))}">{esc(text)}</span>'
        for text, nodes_, indexes in tour_steps(facts)
    )
    return (
        build_css(palette)
        + f'<div class="am" style="--am-surface:{palette["background"]};{logo_sheet(specs, palette)}">'
        '<div class="am-bars">'
        f'<div class="am-bar"><span class="am-filters" role="group" aria-label="{esc("Filtrar por tema")}">{filters}'
        "</span></div>"
        f'<div class="am-bar"><span class="am-rhythms" role="group" aria-label="{esc("Filtrar por ritmo")}">'
        f'<em>{esc("Ritmo")}</em>{rhythms}</span>'
        f'<button type="button" class="am-tourbtn">▶ {esc("Recorrido del martes")}</button>'
        f'<button type="button" class="am-fullbtn"><span class="am-open-full">⤢ {esc("Pantalla completa")}</span>'
        f'<span class="am-close-full">⤡ {esc("Salir de pantalla completa")}</span></button></div></div>'
        f'<div class="am-crumb" hidden><button type="button">← {esc("Volver")}</button>'
        f'<span>{esc("Mapa de la app")} › <b></b></span></div>'
        '<div class="am-row">'
        f'<div class="am-stage am-main" data-links="{data}" data-phases="{esc(json.dumps(rhythm_phases()))}" '
        f'data-story="{esc(json.dumps(story_steps()))}" '
        f'aria-label="{esc("Mapa de la app")}">'
        f"{layers}{bands}{nodes}</div>{build_story_list()}</div>"
        f"{insides}{cards}"
        f'<p class="am-caption" hidden><b></b><span></span></p>'
        ''
        f'<div class="am-whats" hidden>{whats}</div><div class="am-tour" hidden>{tour}</div>'
        f'<div class="am-bar am-foot"><span class="am-legend">{legend}</span></div>'
        "</div>" + SCRIPT
    )


# endregion
