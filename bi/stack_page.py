"""«Stack y evidencia» (D-211, D-266): the project's stack as a high-level architecture diagram.

The data flows left to right through the tools in the order it meets them (ODEPA and the INE,
Python, SQLite, Parquet, dbt, DuckDB, Streamlit). Above, GitHub Actions launches the load and
SQL is the language dbt, DuckDB and the panel share; below, pytest checks the landing and the
served database. Every tool says what it is under its name; on hover, its role here, when it
acts and the tools it is connected with, read from the arrows themselves so the text and the
drawing never disagree. A click opens the page of the app where it is at work. Under the
diagram, three real figures read from the served database and the repository, never typed.

Pure functions: no Streamlit. bi/dashboard.py draws the HTML and hands over the addresses.
"""

import base64
import html
import re
from pathlib import Path

from bi import brand_icons, charts, database_map, doc_views, live_mark, project, queries, static_files

# region Constants and variables
REPOSITORY = Path(__file__).resolve().parent.parent
# Disc colors (light top, dark bottom, glyph) beyond database_map.BRANDS.
EXTRA_DISCS = {
    "pytest": ("#7fc4ff", "#1f6fb5", "#ffffff"),
    "streamlit": ("#ff8f98", "#e0303f", "#ffffff"),
    "sql": ("#b7a6ff", "#5b3fd0", "#ffffff"),
}
# (key, name, what it is, destination page title). The page titles are the dashboard's view
# names; the dashboard turns them into addresses. The order is the one the data meets them.
STACK = [
    ("python", "Python", "Lenguaje de programación", "Pipeline y arquitectura"),
    ("sqlite", "SQLite", "Base de datos ligera", "Modelo de datos"),
    ("apacheparquet", "Parquet", "Formato columnar", "Modelo de datos"),
    ("dbt", "dbt", "Transformación SQL", "Pipeline y arquitectura"),
    ("sql", "SQL", "Lenguaje de consultas", "Consultas SQL"),
    ("duckdb", "DuckDB", "Base analítica", "Modelo de datos"),
    ("pytest", "pytest", "Pruebas en Python", "Monitoreo"),
    ("github", "GitHub Actions", "CI/CD de GitHub", "Cambios e incidentes"),  # D-445: a page the Profesional opens
    ("streamlit", "Streamlit", "Framework web", "Semanal"),
]
SOURCES = [("odepa", "ODEPA", "Precios de alimentos"), ("ine", "INE", "IPC de alimentos")]

# The stage: positions are in a fixed 1150 × 590 drawing that scales with the width.
WIDTH, HEIGHT, LOGO, SOURCE_LOGO = 1150, 590, 68, 50
FLOW_Y = 268
COLORS = {"flow": "#3987e5", "ops": "#c98500", "sql": "#9085e9", "test": "#199e70"}
# key: (x, y, stage, role in GreenOcean, when it acts). The centre of the logo is at (x, y).
NODES = {
    "github": (
        120,
        62,
        "Orquestación",
        "semanal.yml corre la carga completa, prueba la base nueva y la publica en "
        "un release; pruebas.yml corre pytest y dbt parse.",
        "Cada martes (semanal.yml) y en cada push (pruebas.yml).",
    ),
    "sql": (
        910,
        72,
        "Lenguaje común",
        "Los modelos de dbt, las reglas de calidad y los indicadores del panel "
        "(bi/queries.sql) son consultas SQL; la página Consultas SQL deja escribir las propias.",
        "En cada transformación y en cada página que muestra una cifra.",
    ),
    "odepa": (
        120,
        180,
        "Fuente",
        "Fuente de todos los precios: publica cada semana los CSV de precios mayoristas y al consumidor.",
        "Cada semana publica; GreenOcean descarga cada martes.",
    ),
    "ine": (
        120,
        286,
        "Fuente",
        "Publica el IPC de alimentos, con el que los precios se expresan en pesos de hoy.",
        "Cada mes publica; GreenOcean descarga cada martes.",
    ),
    "python": (
        270,
        FLOW_Y,
        "Ingesta",
        "agent/agent.py descarga los CSV de ODEPA y etl/ine.py el IPC; "
        "etl/pipeline.py guarda las filas, copia el bronce, lanza dbt build y publica la base solo si todo pasa.",
        "Cada martes, cuando GitHub Actions lanza la carga.",
    ),
    "sqlite": (
        430,
        FLOW_Y,
        "Aterrizaje",
        "etl/raw.db guarda las filas de ODEPA tal como llegan; etl/datos.db es "
        "el respaldo que calcula el ETL en Python, para comprobar la paridad con DuckDB.",
        "Cada martes, justo después de la descarga.",
    ),
    "apacheparquet": (
        590,
        FLOW_Y,
        "Capa bronce",
        "etl/bronze/ guarda la copia literal de cada fuente, un archivo por año: ODEPA desde raw.db y el IPC del INE.",
        "Cada martes, antes de dbt.",
    ),
    "dbt": (
        750,
        FLOW_Y,
        "Transformación",
        "Lee el bronce y construye staging, intermedio y marts; corre sus pruebas "
        "de datos y, si una falla, la carga se detiene y la base publicada no cambia.",
        "Cada martes con dbt build; en cada push solo se compila (dbt parse).",
    ),
    "duckdb": (
        910,
        FLOW_Y,
        "Data warehouse",
        "Motor donde dbt construye el data warehouse "
        "(etl/warehouse_build.duckdb) y Base DuckDB etl/datos.duckdb, que el panel lee en solo lectura.",
        "Cada martes; la Base DuckDB se reemplaza solo al final de una carga válida.",
    ),
    "streamlit": (
        1070,
        FLOW_Y,
        "Panel",
        "Dibuja este panel con etl/datos.duckdb en solo lectura y lo publica en "
        "Streamlit Community Cloud desde la rama main.",
        "Cada vez que alguien abre una página; muestra la base nueva cuando la carga la sube.",
    ),
    "pytest": (
        670,
        478,
        "Calidad",
        "Recalcula los precios desde las filas crudas, compara SQLite con DuckDB, audita "
        "cada cifra del panel y ataca la seguridad (casos S-01 a S-14).",
        "En cada push y cada martes, antes de subir la base nueva.",
    ),
}
WHAT_IT_IS = {
    "python": "Lenguaje de programación de propósito general, con bibliotecas para datos y para la web.",
    "sqlite": "Motor de base de datos relacional que vive en un solo archivo, sin servidor.",
    "apacheparquet": "Formato abierto de archivos por columnas, comprimido, que leen todos los data warehouse.",
    "dbt": "dbt Core: herramienta que transforma datos con modelos SQL versionados, con pruebas y linaje.",
    "sql": "Lenguaje estándar para consultar y transformar tablas.",
    "duckdb": "Base de datos analítica por columnas, en un solo archivo y sin servidor.",
    "pytest": "Framework de pruebas automáticas para Python.",
    "github": "Servicio de GitHub que ejecuta workflows (CI/CD) en máquinas temporales, por calendario o por evento.",
    "streamlit": "Framework de Python para construir aplicaciones web de datos.",
    "odepa": "Oficina de Estudios y Políticas Agrarias del Ministerio de Agricultura de Chile.",
    "ine": "Instituto Nacional de Estadísticas de Chile.",
}
# (from, to, kind, orthogonal path, label, label x, label y, what it says). The arrow goes the
# way the data or the order travels; the hover text of every tool is built from this list.
EDGES = [
    (
        "odepa",
        "python",
        "flow",
        "M146 180 H200 V254 H236",
        "CSV",
        172,
        180,
        "Python descarga por HTTPS los archivos anuales de precios de ODEPA.",
    ),
    (
        "ine",
        "python",
        "flow",
        "M146 286 H240",
        "IPC",
        190,
        286,
        "Python descarga por HTTPS las series del IPC de alimentos del INE.",
    ),
    (
        "python",
        "sqlite",
        "flow",
        "M304 268 H394",
        "filas crudas",
        349,
        268,
        "Las filas de los CSV entran sin cambios a etl/raw.db.",
    ),
    (
        "sqlite",
        "apacheparquet",
        "flow",
        "M464 268 H554",
        "por año",
        509,
        268,
        "etl/bronze.py copia las tablas de raw.db a Parquet, un archivo por fuente y año.",
    ),
    (
        "apacheparquet",
        "dbt",
        "flow",
        "M624 268 H714",
        "bronce",
        669,
        268,
        "dbt lee el bronce como sus fuentes (sources).",
    ),
    (
        "dbt",
        "duckdb",
        "flow",
        "M784 268 H874",
        "marts",
        829,
        268,
        "dbt materializa staging, intermedio y marts en DuckDB; las tablas del panel pasan a etl/datos.duckdb.",
    ),
    (
        "duckdb",
        "streamlit",
        "flow",
        "M944 268 H1034",
        "solo lectura",
        989,
        268,
        "El panel abre etl/datos.duckdb en solo lectura: ninguna página puede cambiar los datos.",
    ),
    (
        "github",
        "python",
        "ops",
        "M154 62 H256 V236",
        "cada martes",
        216,
        62,
        "El workflow semanal.yml lanza la descarga, el ETL y etl/pipeline.py en una máquina de GitHub.",
    ),
    (
        "python",
        "dbt",
        "ops",
        "M286 237 V196 H738 V237",
        "dbt build",
        512,
        196,
        "etl/pipeline.py lanza dbt build: modelos y pruebas de datos en la base de trabajo.",
    ),
    (
        "github",
        "pytest",
        "ops",
        "M86 62 H40 V478 H636",
        "cada push y cada martes",
        330,
        478,
        "pruebas.yml corre pytest en cada push; semanal.yml lo corre contra la base nueva antes de subirla.",
    ),
    ("sql", "dbt", "sql", "M910 162 V190 H762 V236", "modelos", 762, 214, "Cada modelo de dbt es un archivo .sql."),
    (
        "sql",
        "duckdb",
        "sql",
        "M910 162 V236",
        "lo ejecuta",
        910,
        214,
        "DuckDB es el motor que ejecuta el SQL de dbt y el del panel.",
    ),
    (
        "sql",
        "streamlit",
        "sql",
        "M910 190 H1058 V236",
        "consultas",
        1058,
        214,
        "Cada cifra del panel sale de una consulta de bi/queries.sql; la página Consultas SQL corre las propias.",
    ),
    (
        "pytest",
        "sqlite",
        "test",
        "M670 444 V404 H430 V364",
        "recalcula cada precio",
        550,
        404,
        "Las pruebas recalculan los precios desde las filas crudas de raw.db y comparan el respaldo SQLite con DuckDB.",
    ),
    (
        "pytest",
        "duckdb",
        "test",
        "M670 404 H910 V364",
        "audita cada cifra",
        790,
        404,
        "Las pruebas recalculan cada cifra del panel desde etl/datos.duckdb.",
    ),
]
# Points where a line splits in two.
JUNCTIONS = [("sql", 910, 190), ("test", 670, 404)]
DASH, DASHED = ' stroke-dasharray="6 5"', ' class="dashed"'
LEGEND = [
    ("flow", "el dato que fluye"),
    ("ops", "quién lanza a quién"),
    ("sql", "dónde se usa SQL"),
    ("test", "qué verifican las pruebas"),
]
# endregion


# region «Stack y evidencia»
def read_figures(database_file=queries.DATABASE_FILE, tests_dir=REPOSITORY / "tests"):
    """{prices, tests, loads}: weekly prices served, automatic tests (pytest + dbt) and recorded loads."""
    connection = queries.open_database(database_file)
    try:
        prices = connection.execute("SELECT count(*) FROM weekly_price").fetchone()[0]
        dbt_tests = connection.execute("SELECT count(*) FROM dbt_node WHERE resource_type = 'test'").fetchone()[0]
        loads = connection.execute("SELECT count(*) FROM etl_run").fetchone()[0]
    finally:
        connection.close()
    return {"prices": prices, "tests": project.count_test_functions(Path(tests_dir)) + dbt_tests, "loads": loads}


def format_number(value):
    return f"{value:,}".replace(",", ".")


def as_image(svg):
    """An SVG as an image: st.html strips inline SVG gradients and markers, a data: image keeps them."""
    svg = re.sub(r'<svg class="logo"', '<svg xmlns="http://www.w3.org/2000/svg"', svg, count=1)
    return f'<img class="logo" alt="" src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}">'


def disc_logo(key):
    if key in {source for source, *_ in SOURCES}:
        return as_image(doc_views.disc_logo("source", key))
    return as_image(disc_svg(key))


def disc_svg(key):
    if key in database_map.BRANDS:
        return database_map.brand_logo(key, "-stack")
    top, bottom, glyph = EXTRA_DISCS[key]
    body = (
        f'<text x="36" y="43" text-anchor="middle" font-family="ui-monospace, Menlo, monospace" font-weight="800" '
        f'font-size="19" fill="{glyph}">SQL</text>'
        if key == "sql"
        else f'<g fill="{glyph}" transform="translate(17 17) scale(1.58)">{brand_icons.logo_body(key)}</g>'
    )
    return (
        f'<svg class="logo" viewBox="0 0 72 72" aria-hidden="true"><defs>'
        f'<radialGradient id="disc-{key}-stack" cx="35%" cy="28%" r="85%"><stop offset="0" stop-color="{top}"/>'
        f'<stop offset="1" stop-color="{bottom}"/></radialGradient></defs>'
        f'<circle cx="36" cy="36" r="31" fill="url(#disc-{key}-stack)"/>'
        f'<ellipse cx="29" cy="19" rx="16" ry="8" fill="#fff" opacity=".3"/>{body}</svg>'
    )


def names():
    return dict([(key, name) for key, name, *_ in STACK] + [(key, name) for key, name, _ in SOURCES])


def connections(key):
    """What a tool is connected with, read from the arrows, one per line: «→ SQLite: filas crudas»."""
    name = names()
    out = [f"→ {name[target]}: {label}" for source, target, _, _, label, *_ in EDGES if source == key]
    into = [f"← {name[source]}: {label}" for source, target, _, _, label, *_ in EDGES if target == key]
    return "\n".join(into + out)


def build_wires_svg(palette):
    """Every line of the diagram as one image: right angles only, an arrowhead where it arrives."""
    markers = "".join(
        f'<marker id="h-{kind}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
        f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{color}"/></marker>'
        for kind, color in COLORS.items()
    )
    lines = "".join(
        f'<path d="{path}" fill="none" stroke="{COLORS[kind]}" stroke-width="2"'
        f'{DASH if kind == "sql" else ""} marker-end="url(#h-{kind})"/>'
        for _, _, kind, path, *_ in EDGES
    )
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{COLORS[kind]}"/>' for kind, x, y in JUNCTIONS)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}"><defs>{markers}</defs>'
        f'{lines}{dots}</svg>'
    )
    return f'<img class="sk-wires" alt="" src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}">'


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
    )
    shadow = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    sans = '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    return static_files.style(
        "stack_page.css",
        {
            'var(--go-width)': WIDTH,
            'var(--go-height)': HEIGHT,
            'var(--go-logo-2)': LOGO / 2,
            'var(--go-source-logo-2)': SOURCE_LOGO / 2,
            'var(--go-logo)': LOGO,
            'var(--go-shadow)': shadow,
            'var(--go-source-logo)': SOURCE_LOGO,
            'var(--go-ink)': ink,
            'var(--go-sans)': sans,
            'var(--go-text)': text,
            'var(--go-muted)': muted,
            'var(--go-background)': palette['background'],
            'var(--go-card)': card,
            'var(--go-border)': border,
            'var(--go-5-if-dark-else-18)': '.5' if dark else '.18',
            'var(--go-accent)': palette['accent'],
            'var(--go-live-mark-css-dark)': live_mark.build_css(dark),
        },
    )


def tip_html(x, y, parts, footer=""):
    side = " start" if x < WIDTH * 0.2 else " end" if x > WIDTH * 0.8 else ""
    up = " up" if y > HEIGHT * 0.6 else ""
    return (
        f'<span class="sk-tip{side}{up}" role="tooltip">'
        + "".join(f"<i>{html.escape(head)}</i>{html.escape(text)}" for head, text in parts)
        + (f"<u>{html.escape(footer)}</u>" if footer else "")
        + "</span>"
    )


def position(x, y):
    return f"left:{x / WIDTH * 100:.3f}%;top:{y / HEIGHT * 100:.3f}%"


def build_node(key, name, definition, address=None):
    x, y, stage, role, when = NODES[key]
    parts = [
        ("Qué es", WHAT_IT_IS[key]),
        ("Rol en GreenOcean", role),
        ("Cuándo actúa", when),
        ("Se conecta con", connections(key)),
    ]
    body = f'{disc_logo(key)}<b>{html.escape(name)}</b><small>{html.escape(definition)}</small>' + (
        "" if address is None else f'<em>{html.escape(stage)}</em>'
    )
    label = html.escape(f"{name}: {definition}. {role}", quote=True)
    if address is None:
        return (
            f'<div class="sk-node source" tabindex="0" style="{position(x, y)}" aria-label="{label}">'
            f'{body}{tip_html(x, y, parts)}</div>'
        )
    return (
        f'<a class="sk-node" href="{html.escape(address, quote=True)}" target="_self" style="{position(x, y)}" '
        f'aria-label="{label}">{body}{tip_html(x, y, parts, "Clic: verlo en uso.")}</a>'
    )


def build_stack_html(palette, figures, addresses):
    """The architecture diagram, every tool a link to its page with its explanation, and the three figures."""
    nodes = [build_node(key, name, definition, addresses[page]) for key, name, definition, page in STACK]
    nodes += [build_node(key, name, definition) for key, name, definition in SOURCES]
    chips = [
        f'<span class="sk-chip" tabindex="0" style="{position(x, y)};color:{charts.legible(COLORS[kind], palette["background"])}">'
        f'{html.escape(label)}'
        f'{tip_html(x, y, [("Qué viaja" if kind == "flow" else "Qué significa", what)])}</span>'
        for _, _, kind, _, label, x, y, what in EDGES
    ]
    legend = "".join(
        f'<span{DASHED if kind == "sql" else ""} style="--c:{COLORS[kind]}">{html.escape(text)}</span>'
        for kind, text in LEGEND
    )
    evidence = [
        (figures["prices"], "precios semanales procesados"),
        (figures["tests"], "pruebas automáticas (pytest y dbt)"),
        (figures["loads"], "cargas semanales registradas"),
    ]
    numbers = "".join(
        f'<div><strong>{format_number(value)}</strong><span>{html.escape(label)}</span></div>'
        for value, label in evidence
    ) + live_mark.build_html(  # D-510: the three figures are read when the page opens
        "weekly_price, dbt_node y etl_run se cuentan en la Base DuckDB al abrir la página; las pruebas de pytest, en "
        "la carpeta tests/."
    )
    return (
        build_css(palette) + '<div class="sk-map"><div class="sk-stage" role="group" '
        'aria-label="Arquitectura del stack de GreenOcean">'
        + build_wires_svg(palette)
        + "".join(chips)
        + "".join(nodes)
        + f'</div><p class="sk-legend">{legend}</p></div><div class="evidence">{numbers}</div>'
    )


# endregion
