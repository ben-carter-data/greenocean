"""The activity bar of the menu (D-539, D-540): line icons in one tone, like VS Code's, and the stack of each area.

Each area of the project has an icon in the bar that opens the names of the tools and engineering concepts it uses,
in order of relevance, with no explanation: a list to show the stack and to study it. Every name is used in this
repository (D-540 lists where).
"""

import html
import re

from bi.i18n import tr

# region Constants
# Line icons on a 24 px grid. The bar paints them through a CSS mask, so one shape takes the tone of each theme and
# brightens on hover or when its page is open.
ICONS = {
    "documents": (
        '<path d="M14 3H8.5A1.5 1.5 0 0 0 7 4.5v12A1.5 1.5 0 0 0 8.5 18h9a1.5 1.5 0 0 0 1.5-1.5V8z"/>'
        '<path d="M14 3v5h5"/><path d="M4 7.5v12A1.5 1.5 0 0 0 5.5 21H15"/>'
    ),
    "study": (
        '<path d="M9 3h6"/><path d="M10 3v6.2L4.6 18.4A1.7 1.7 0 0 0 6 21h12a1.7 1.7 0 0 0 1.4-2.6L14 9.2V3"/>'
        '<path d="M7.2 15h9.6"/>'
    ),
    "sources": (
        '<ellipse cx="12" cy="5.5" rx="7" ry="2.5"/><path d="M5 5.5v13c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-13"/>'
        '<path d="M5 12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5"/>'
    ),
    "code": '<path d="M8 7l-5 5 5 5"/><path d="M16 7l5 5-5 5"/><path d="M13.5 4.5l-3 15"/>',
    "data": (
        '<circle cx="5" cy="6" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="12" r="2"/>'
        '<path d="M7 6h3.5a3 3 0 0 1 3 3 3 3 0 0 0 3 3H17"/><path d="M7 18h3.5a3 3 0 0 0 3-3 3 3 0 0 1 3-3"/>'
    ),
    "quality": '<path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
    "devops": (
        '<path d="M7.5 8.5C5 8.5 3 10 3 12s2 3.5 4.5 3.5c3.5 0 5.5-7 9-7 2.5 0 4.5 1.5 4.5 3.5s-2 3.5-4.5 3.5'
        'c-3.5 0-5.5-7-9-7z"/>'
    ),
    "business": '<path d="M4 20h16"/><path d="M7 20v-6"/><path d="M12 20V8"/><path d="M17 20v-10"/>',
}

# (key, title, icon, names): the five areas, in the order of the bar; each list from the most to the least relevant.
STACK_AREAS = [
    (
        "code",
        "Stack · Código",
        "code",
        ["Python", "SQL", "pandas", "Git", "Jupyter", "requests", "Markdown"],
    ),
    (
        "data",
        "Stack · Ingeniería de datos",
        "data",
        [
            "ETL",
            "DuckDB",
            "dbt Core",
            "Staging · intermedio · marts",
            "Data warehouse",
            "Modelo estrella: hechos y dimensiones",
            "Parquet",
            "PyArrow",
            "SQLite",
            "Ingesta de datos",
            "Capa de aterrizaje y capa bronce",
            "Linaje de datos",
            "Normalización de unidades",
            "Carga semanal por lotes",
        ],
    ),
    (
        "quality",
        "Stack · Calidad",
        "quality",
        [
            "Pruebas de datos de dbt",
            "pytest",
            "Pruebas que recalculan las cifras",
            "Cobertura de código",
            "Ruff",
            "mypy",
            "Detección de atípicos",
            "AppTest de Streamlit",
            "Playwright",
            "Plan de calidad (SQAP)",
            "Plan de pruebas",
            "Registro de fallas y no conformidades",
        ],
    ),
    (
        "devops",
        "Stack · DevOps y seguridad",
        "devops",
        [
            "GitHub Actions",
            "CI/CD",
            "Cron",
            "GitHub",
            "Conventional Commits",
            "GitHub Releases",
            "Gestión de secretos",
            "Mínimo privilegio",
            "Bandit",
            "pip-audit",
            "detect-secrets",
            "OWASP",
            "Huella SHA-256",
            "Streamlit Community Cloud",
        ],
    ),
    (
        "business",
        "Stack · Negocio · BA y BI",
        "business",
        [
            "Streamlit",
            "Dashboards",
            "KPI",
            "Altair",
            "Precios reales con el IPC",
            "Alertas de precio",
            "Requisitos del producto (PRD)",
            "Interesados",
            "Reglas de negocio",
            "Decisiones de arquitectura (ADR)",
            "Arquitectura de software (SAD)",
            "Excel y CSV",
        ],
    ),
]
# D-550: what each name is, in one sentence, and where the project uses it; shown on hover or focus.
STACK_HINTS = {
    "Python": "Lenguaje de programación. Aquí: la descarga, el ETL, el pipeline, el panel y las pruebas.",
    "SQL": "Lenguaje para consultar bases de datos. Aquí: los modelos de dbt, las consultas del panel y la página «Consultas SQL».",
    "pandas": "Librería de Python para tablas de datos. Aquí: limpia y valida las filas en el ETL y prepara los datos del panel.",
    "Git": "Guarda cada cambio del código con su historia. Aquí: cada cambio es un commit con su decisión escrita.",
    "Jupyter": "Cuadernos que juntan código, resultados y texto. Aquí: el estudio del archivo mayorista de ODEPA, en español y en inglés.",
    "requests": "Librería de Python para pedir archivos por internet. Aquí: descarga los archivos de ODEPA y el IPC del INE, y lee GitHub.",
    "Markdown": "Formato de texto simple, con títulos y listas. Aquí: los documentos del proyecto, que el panel muestra e imprime.",
    "ETL": "Extraer, transformar y cargar datos. Aquí: etl/etl.py guarda las filas de ODEPA tal como llegan y arma el respaldo datos.db.",
    "DuckDB": "Base de datos para análisis que cabe en un archivo. Aquí: datos.duckdb, la base que construye dbt y que lee el panel.",
    "dbt Core": "Transforma datos con SQL en pasos ordenados y los prueba. Aquí: los modelos de dbt/ y sus 31 pruebas.",
    "Staging · intermedio · marts": "Las tres capas de dbt: limpiar, combinar y entregar. Aquí: van de las filas de bronce a las tablas que usa el panel.",
    "Data warehouse": "Base pensada para analizar, no para operar. Aquí: un archivo DuckDB pequeño que se publica cada semana.",
    "Modelo estrella: hechos y dimensiones": "Una tabla de hechos rodeada de tablas que la describen. Aquí: weekly_price, con producto, región, canal y fecha.",
    "Parquet": "Formato de archivo por columnas, compacto y rápido. Aquí: la capa bronce, una copia literal de cada fuente por año.",
    "PyArrow": "Librería de Python para datos por columnas. Aquí: escribe los archivos Parquet de la capa bronce.",
    "SQLite": "Base de datos en un solo archivo, sin servidor. Aquí: raw.db, el aterrizaje de ODEPA, y datos.db, el respaldo.",
    "Ingesta de datos": "Traer los datos desde su fuente. Aquí: agent/agent.py descarga y valida los archivos de ODEPA cada martes.",
    "Capa de aterrizaje y capa bronce": "Las primeras paradas de los datos, sin cambiarlos. Aquí: raw.db guarda las filas tal como llegan y bronce las copia en Parquet.",
    "Linaje de datos": "El camino de cada tabla desde su origen. Aquí: la página «Pipeline y linaje» lo dibuja a partir del proyecto dbt.",
    "Normalización de unidades": "Llevar cada precio a una misma unidad. Aquí: unas 200 formas de escribir la unidad pasan a precio por kilo o por unidad.",
    "Carga semanal por lotes": "Procesar todos los datos juntos, a una hora fija. Aquí: cada martes GitHub Actions corre la carga completa.",
    "Pruebas de datos de dbt": "Reglas que revisan los datos al construirlos. Aquí: 31 pruebas; si una falla, la base no se publica.",
    "pytest": "Herramienta para escribir y correr pruebas en Python. Aquí: las pruebas del proyecto, que corren en cada push.",
    "Pruebas que recalculan las cifras": "Rehacen una cifra por otro camino. Aquí: comparan lo que muestra el panel con un cálculo propio desde las filas crudas.",
    "Cobertura de código": "Qué parte del código ejecutan las pruebas. Aquí: el CI exige al menos el 90 %.",
    "Ruff": "Revisa el estilo y los errores del código Python. Aquí: corre en cada push.",
    "mypy": "Revisa los tipos de datos del código Python. Aquí: los diez módulos principales, en cada push.",
    "Detección de atípicos": "Marcar valores fuera de lo normal. Aquí: un precio cinco veces sobre o bajo la mediana de su semana se marca y queda fuera.",
    "AppTest de Streamlit": "Prueba una app de Streamlit sin navegador. Aquí: las pruebas abren cada página en los dos idiomas.",
    "Playwright": "Maneja un navegador real para medir páginas. Aquí: se usó a mano para medir el diseño; no corre en el CI.",
    "Plan de calidad (SQAP)": "Documento que dice qué calidad se cuida y cómo se mide. Aquí: cada indicador tiene su límite aceptable y se mide en cada push.",
    "Plan de pruebas": "Documento que dice qué se prueba y cómo. Aquí: el Plan de pruebas y seguridad, con los ataques que se repiten en cada cambio.",
    "Registro de fallas y no conformidades": "Cada falla con su causa y su arreglo. Aquí: lo muestra la página «Cambios e incidentes».",
    "GitHub Actions": "Servicio de GitHub que corre tareas solo. Aquí: la carga de cada martes, las pruebas de cada push y la medición de calidad.",
    "CI/CD": "Integración y entrega continuas: probar y publicar en automático. Aquí: pruebas en cada push y una base que se publica solo si pasan.",
    "Cron": "Forma de programar una tarea a una hora fija. Aquí: semanal.yml lanza la carga cada martes.",
    "GitHub": "Plataforma que guarda el código y su historia. Aquí: el repositorio, los workflows y la base publicada.",
    "Conventional Commits": "Una forma fija de escribir los mensajes de commit. Aquí: cada commit dice su tipo, qué cambia y su decisión.",
    "GitHub Releases": "Versiones publicadas con sus archivos. Aquí: el release «base-actual» guarda la base que lee el panel.",
    "Gestión de secretos": "Guardar las claves fuera del código. Aquí: los tokens y la clave del Autor viven en los secretos de GitHub y de Streamlit.",
    "Mínimo privilegio": "Dar a cada pieza solo los permisos que necesita. Aquí: cada workflow declara los suyos y el panel lee GitHub con un token de solo lectura.",
    "Bandit": "Busca problemas de seguridad en el código Python. Aquí: corre en el workflow de calidad.",
    "pip-audit": "Busca fallas de seguridad conocidas en las dependencias. Aquí: corre en el workflow de calidad.",
    "detect-secrets": "Busca claves escritas por error. Aquí: corre en el workflow de calidad, con una lista de lo que ya se revisó.",
    "OWASP": "Lista de los riesgos de seguridad más comunes en aplicaciones web. Aquí: el Plan de pruebas clasifica con ella los ataques de cada cambio.",
    "Huella SHA-256": "Código único que identifica el contenido de un archivo. Aquí: comprueba que los archivos y la base publicada no cambiaron en el camino.",
    "Streamlit Community Cloud": "Servicio gratuito que publica apps de Streamlit. Aquí: aloja el panel público.",
    "Streamlit": "Librería de Python para construir apps de datos. Aquí: todo el panel.",
    "Dashboards": "Pantallas que resumen datos para decidir. Aquí: «Semanal» y «Análisis».",
    "KPI": "Indicador clave. Aquí: el cambio típico de la semana, cuántos precios subieron y bajaron, y la brecha entre consumidor y mayorista.",
    "Altair": "Librería de gráficos para Python. Aquí: dibuja los gráficos del panel.",
    "Precios reales con el IPC": "Precios sin el efecto de la inflación. Aquí: el IPC de alimentos del INE los lleva a pesos del último mes publicado.",
    "Alertas de precio": "Avisos de cambios fuera de lo normal. Aquí: un precio que se aleja de sus semanas anteriores más de lo esperable.",
    "Requisitos del producto (PRD)": "Documento que dice qué problema se resuelve y qué debe hacer el producto. Aquí: requisitos numerados, cada uno con su prueba.",
    "Interesados": "Las personas a quienes afecta el proyecto. Aquí: la pestaña «Interesados» de «Análisis» los ordena por cuánto dependen de él.",
    "Reglas de negocio": "Lo que los datos deben cumplir. Aquí: cada regla tiene su número, se aplica en el código y tiene su prueba.",
    "Decisiones de arquitectura (ADR)": "Registro de las decisiones técnicas importantes. Aquí: cada ADR nombra la prueba que lo confirma.",
    "Arquitectura de software (SAD)": "Documento que describe cómo está construido el sistema. Aquí: la carga, los datos, el despliegue y la capacidad.",
    "Excel y CSV": "Formatos para llevarse los datos. Aquí: «Descargar» entrega los precios en Excel y «Consultas SQL» exporta tablas en CSV.",
}
STACK_HELP = "Pasa el mouse sobre un nombre para ver qué es y dónde se usa."
# A hint reads «what it is. Aquí: where the project uses it», in Spanish or English.
HINT_PARTS = re.compile(r"^(.*?\.) (Aquí|Here): (.*)$")
# endregion


# region The activity bar of the menu
def build_icon_svg(name):
    """One icon as an SVG file, for the CSS mask of its button."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )


def build_hint_html(name):
    """What a name is, then «Aquí:» in bold and where the project uses it, in the language of the visit."""
    what, label, where = HINT_PARTS.match(tr(STACK_HINTS[name])).groups()
    return f"{html.escape(what)} <b>{html.escape(label)}:</b> {html.escape(where)}"


def build_stack_html(title, names):
    """The window of one area: its title and its names, numbered in order of relevance. D-550: each name says what it is
    and where the project uses it, at the foot of the window, when the mouse or the keyboard reaches it."""
    items = "".join(
        f'<li tabindex="0">{html.escape(tr(name))}<span class="stack-hint" role="tooltip">{build_hint_html(name)}</span></li>'
        for name in names
    )
    return (
        f'<div class="stack-list"><p class="stack-title">{html.escape(tr(title))}</p><ol>{items}</ol>'
        f'<p class="stack-help">{html.escape(tr(STACK_HELP))}</p></div>'
    )


# endregion
