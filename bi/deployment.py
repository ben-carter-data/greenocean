"""«Despliegue» (D-255): the deployment diagram of GreenOcean, in the form of the UML deployment diagram.

Nodes are the 3D boxes where something runs (devices and platforms); inside them, the execution environments
(a runner, a Python process, a repository) hold the artifacts that are deployed there (files, databases,
workflows). The lines are the communication paths, each with its protocol. Every piece is a real one: the workflows
in .github/workflows/, the files of the repository and the services the panel talks to. The live part reads the
state of the weekly workflow and of the panel, the size of the served database and the dates of the last load.
D-422: the release is its own environment (the repository keeps only the pointer, D-270), the three workflows are drawn
(the weekly load and its quality report on one runner, the tests of each push on another) and the panel reads the
database from the release.

build_deployment_html() returns one HTML document for st.iframe (CSS only, no script).
"""

import html
from pathlib import Path
from urllib.parse import urlparse

from bi import architecture, charts, control, project, quality_view, queries, static_files

# region Constants
WIDTH, HEIGHT = 1210, 566  # D-422: wider, not taller, so it keeps its height on screen
DEPTH = 12
# Nodes: key -> (x, y, width, height, stereotype, name). (x, y) is the front face; the top and the side stick out DEPTH.
NODES = {
    "odepa": (20, 40, 230, 92, "dispositivo", "ODEPA"),
    "ine": (20, 160, 230, 90, "dispositivo", "INE"),
    "author": (20, 300, 230, 190, "dispositivo", "Computador del autor"),
    "github": (320, 40, 680, 480, "plataforma", "GitHub"),
    "streamlit": (1020, 40, 175, 300, "plataforma", "Streamlit Cloud"),
    "browser": (1020, 392, 175, 80, "dispositivo", "Navegador"),
}
# Execution environments, nested in a node: key -> (x, y, width, height, node, name).
ENVIRONMENTS = {
    "runner": (336, 84, 206, 236, "github", "Runner ubuntu-latest"),
    "python": (346, 216, 186, 96, "github", "Python 3.11"),
    "repo": (336, 358, 206, 150, "github", "Repositorio · rama main"),
    "cache": (590, 84, 180, 56, "github", "Caché de Actions"),
    # D-383: the two reports, each where GitHub keeps it: the weekly report as an issue, the quality report as a pull request.
    "issues": (590, 180, 180, 56, "github", "Issues"),
    "pulls": (590, 252, 180, 56, "github", "Pull requests"),
    # D-422: the tests of each push run on a runner of their own, apart from the weekly load.
    "tests": (590, 392, 180, 120, "github", "Runner ubuntu-latest"),
    "release": (800, 196, 184, 94, "github", "Release «base-actual»"),
    "app": (1032, 84, 151, 236, "streamlit", "Streamlit"),
    "venv": (32, 344, 206, 134, "author", "Python 3.11 o 3.12"),
}
# Communication paths: (path, protocol, chip position). Straight segments only. A protocol of two lines is a tuple.
PATHS = [
    ("M250 86 H298 V124 H336", "HTTPS", (254, 80)),
    ("M250 199 H310 V158 H336", "HTTPS", (254, 193)),
    ("M250 420 H336", "git push", (262, 414)),
    ("M440 320 V358", "git push", (452, 344)),
    ("M542 112 H590", "", None),
    ("M542 208 H590", "", None),
    ("M542 280 H590", "", None),
    ("M542 316 H892 V290", "gh release upload", (790, 336)),  # D-422: the load replaces the served database
    ("M542 450 H590", "", None),  # D-422: every push starts the tests
    ("M1020 158 H542", ("API REST de GitHub", "lanzar, leer estado y logs, cancelar"), (548, 152)),  # D-370
    ("M1020 278 H984", "", None),  # D-422: the panel downloads the database from the release
    ("M542 372 H1060 V340", "despliegue de main", (800, 366)),
    ("M1107 392 V340", "HTTPS", (1118, 372)),
]
# What each node says on hover: what runs there and how it was deployed.
TIPS = {
    "odepa": "Publica los CSV de precios mayoristas y al consumidor. El agente de ingesta los descarga por HTTPS cada martes.",
    "ine": "Publica el IPC de alimentos. La carga lo descarga y lo cruza con los precios para calcular el precio real.",
    "github": "La plataforma que guarda el código y la base publicada, ejecuta la carga semanal y las pruebas, y recibe los informes. "
    "El repositorio es público.",
    "streamlit": "El servicio gratuito que publica el panel con un enlace público, sin servidor que mantener, y guarda sus secretos.",
    "author": "Donde se desarrolla. Aquí vive el aterrizaje raw.db, que no se sube a GitHub (D-020), y desde aquí se hace git push; "
    "las pruebas se corren antes de cada commit.",
    "venv": "El entorno de Python del autor: el panel, la ingesta, el ETL y dbt, más pytest. dbt corre en un entorno aparte. "
    "Aquí vive el aterrizaje raw.db, que no se sube a git.",
    "runner": "Una máquina Ubuntu de GitHub Actions que nace y se borra en cada ejecución: la carga de cada martes "
    "(semanal.yml) y, al terminar, la medición de calidad que propone el informe (calidad.yml).",
    "tests": "Otra máquina Ubuntu, aparte de la carga: en cada push corre las pruebas (pruebas.yml: lint, mypy y pytest en "
    "Python 3.11 y 3.12) y mide la calidad sin proponer informe (calidad.yml). No toca la base publicada.",
    "release": "Guarda la Base DuckDB, datos.duckdb, fuera de git. Solo si pasan todas las pruebas, la carga la reemplaza "
    "(D-270); el panel la descarga de aquí.",
    "python": "El entorno Python 3.11 del runner: descarga, aterrizaje en SQLite, bronce en Parquet y dbt build sobre DuckDB.",
    "repo": "El repositorio público, rama main: el código y el puntero datos.version, que dice qué base del release está "
    "publicada. Solo si pasan todas las pruebas, la carga sube el puntero con un commit «Weekly data update» (D-270).",
    "cache": "Guarda los CSV de los años cerrados, que ya no cambian, para no descargarlos cada semana. Se borra si no se usa en 7 días.",
    "issues": "Al final de cada carga, el workflow semanal (semanal.yml) abre un issue «Informe semanal» con lo que se cargó "
    "y lo que se revisó.",
    "pulls": "Después de cada carga en verde, calidad.yml mide los indicadores y propone el informe de "
    "calidad numerado como un pull request; se fusiona solo si los indicadores de código están en su aceptable (D-431, D-436).",
    "app": "Streamlit ejecuta bi/dashboard.py desde la rama main. Descarga del release la base de la última carga, comprueba su "
    "huella y la lee en solo lectura; guarda los secretos del panel y, en la sesión del Autor, lanza la carga por la API de GitHub.",
    "browser": "El Usuario, el Profesional o el Autor. El panel público no pide cuenta; la clave de control solo abre lo del Autor, "
    "como el botón «Ejecutar pipeline ahora».",
}
# endregion


# region Variables
REPOSITORY = Path(__file__).resolve().parent.parent
# endregion


# region Pieces and style
def esc(value):
    return html.escape(str(value))


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    hovers = "".join(
        f"svg:has(#n-{key}:hover, #n-{key}:focus) #tip-{key} {{ opacity:1; }}"
        for key in list(NODES) + list(ENVIRONMENTS)
    )
    return static_files.style(
        "deployment.css",
        {
            'var(--go-text)': text,
            'var(--go-rgba-255-255-255-04-if-dark-else-ffffff)': 'rgba(255,255,255,.04)' if dark else '#ffffff',
            'var(--go-ink)': ink,
            'var(--go-rgba-255-255-255-06-if-dark-else-e3e9f2)': 'rgba(255,255,255,.06)' if dark else '#e3e9f2',
            'var(--go-muted)': muted,
            'var(--go-rgba-255-255-255-03-if-dark-else-dfe6f0)': 'rgba(255,255,255,.03)' if dark else '#dfe6f0',
            'var(--go-card)': card,
            'var(--go-rgba-255-255-255-05-if-dark-else-f4f7fb)': 'rgba(255,255,255,.05)' if dark else '#f4f7fb',
            'var(--go-accent)': accent,
            'var(--go-background)': palette['background'],
            'var(--go-border)': border,
            'var(--go-55-if-dark-else-2)': '.55' if dark else '.2',
            'var(--go-hovers)': hovers,
        },
    )


def box(x, y, width, height):
    """The 3D box of a node: front, top and side faces."""
    d = DEPTH
    return (
        f'<polygon class="top" points="{x},{y} {x + d},{y - d} {x + width + d},{y - d} {x + width},{y}"/>'
        f'<polygon class="side" points="{x + width},{y} {x + width + d},{y - d} {x + width + d},{y + height - d} {x + width},{y + height}"/>'
        f'<rect class="front" x="{x}" y="{y}" width="{width}" height="{height}"/>'
    )


def artifact(x, y, label):
    """A deployed file: the UML artifact mark and its name."""
    return (
        f'<path class="page" d="M{x} {y - 10} h8 l4 4 v10 h-12 z"/><path class="fold" d="M{x + 8} {y - 10} v4 h4"/>'
        f'<text class="art" x="{x + 18}" y="{y}">{esc(label)}</text>'
    )


def heading(x, y, stereotype, name):
    return (
        f'<text class="stereo" x="{x}" y="{y}">«{esc(stereotype)}»</text>'
        f'<text class="name" x="{x}" y="{y + 16}">{esc(name)}</text>'
    )


def state_dot(x, y, state):
    color = architecture.STATE_COLORS.get(state) if state != architecture.STATE_UNKNOWN else None
    return f'<circle cx="{x}" cy="{y}" r="5.5" fill="{color}"/>' if color else ""


# endregion


# region The hosts and their contents
def read_hosts():
    ine_host = urlparse(project.INE_IPC_SOURCE_URL).netloc
    odepa_host = urlparse(project.WHOLESALE_SOURCE_URL).netloc
    return odepa_host, ine_host


def build_contents(states, figures, live=True):
    """Everything drawn inside the nodes and the environments, with its live figures."""
    odepa_host, ine_host = read_hosts()
    raw = REPOSITORY / "etl" / "raw.db"
    raw_text = f"etl/raw.db · {project.describe_file_size(raw)}" if raw.exists() else "etl/raw.db · solo aquí"
    parts = {
        "odepa": (
            heading(34, 64, "dispositivo", "ODEPA")
            + f'<text class="note" x="34" y="98">{esc(odepa_host)}</text>'
            + artifact(34, 116, "CSV mayorista y consumidor")
            + state_dot(236, 62, states.get("sources"))
        ),
        "ine": (
            heading(34, 184, "dispositivo", "INE")
            + f'<text class="note" x="34" y="218">{esc(ine_host)}</text>'
            + artifact(34, 236, "IPC de alimentos")
            + state_dot(236, 182, states.get("sources"))
        ),
        "author": heading(34, 324, "dispositivo", "Computador del autor"),
        "github": heading(334, 64, "plataforma", "GitHub")
        + '<text class="note" x="400" y="80">código, automatización e informes</text>',
        "streamlit": heading(1034, 64, "plataforma", "Streamlit Cloud"),
        "browser": (
            heading(1034, 416, "dispositivo", "Navegador")
            + '<text class="note" x="1034" y="452">Usuario, Profesional o Autor</text>'
        ),
    }
    envs = {
        "runner": (
            heading(348, 104, "entorno de ejecución", "Runner ubuntu-latest")
            + '<text class="note" x="348" y="138">efímero: nace en cada ejecución</text>'
            + artifact(348, 158, "semanal.yml")
            + (f'<text class="live" x="366" y="173">próxima {esc(figures.get("next_run", ""))}</text>' if live else "")
            + artifact(348, 192, "calidad.yml")
            + '<text class="note" x="366" y="207">tras una carga en verde</text>'
            + state_dot(526, 102, states.get("workflow"))
        ),
        "python": (
            heading(356, 234, "entorno de ejecución", "Python 3.11")
            + artifact(356, 270, "agent.py · etl.py")
            + artifact(356, 286, "bronze.py")
            + artifact(356, 302, "dbt build · DuckDB")
        ),
        "repo": (
            heading(348, 378, "entorno de ejecución", "Repositorio · rama main")
            + artifact(348, 414, "código del proyecto")
            + artifact(348, 430, "datos.version · puntero")
            + artifact(348, 446, "manifest.json")
            + f'<text class="live" x="348" y="486">{esc(figures.get("week_prices", ""))}</text>'
        ),
        "release": (
            heading(812, 216, "entorno de ejecución", "Release «base-actual»")
            + artifact(812, 254, f"datos.duckdb · {project.describe_file_size(queries.DATABASE_FILE)}")
            + '<text class="note" x="830" y="270">fuera de git</text>'
        ),
        "tests": (
            heading(602, 412, "entorno de ejecución", "Runner ubuntu-latest")
            + '<text class="note" x="602" y="446">aparte, en cada push</text>'
            + artifact(602, 466, "pruebas.yml")
            + '<text class="note" x="620" y="481">lint · pytest 3.11 y 3.12</text>'
            + artifact(602, 500, "calidad.yml · solo mide")
        ),
        "cache": heading(602, 100, "entorno de ejecución", "Caché de Actions")
        + artifact(602, 134, "CSV de años cerrados"),
        "issues": heading(602, 200, "entorno de ejecución", "Issues") + artifact(602, 234, "informe semanal"),
        "pulls": heading(602, 268, "entorno de ejecución", "Pull requests") + artifact(602, 302, "informe de calidad"),
        "app": (
            heading(1044, 104, "entorno de ejecución", "Streamlit")
            + artifact(1044, 150, "dashboard.py")
            + artifact(1044, 172, "datos.duckdb")
            + '<text class="note" x="1062" y="187">solo lectura</text>'
            + artifact(1044, 210, "st.secrets")
            + '<text class="note" x="1062" y="225">tokens y clave</text>'
            + f'<text class="live" x="1044" y="256">{esc(figures.get("panel_time", ""))}</text>'
            + state_dot(1168, 118, states.get("panel"))
        ),
        "venv": (
            heading(44, 364, "entorno de ejecución", "Python 3.11 o 3.12")
            + artifact(44, 402, "código del proyecto")
            + artifact(44, 420, raw_text)
            + artifact(44, 438, "pytest · dbt aparte")
            + '<text class="note" x="44" y="460">el aterrizaje no se sube a git</text>'
        ),
    }
    return parts, envs


# endregion


# region Drawing the deployment
def build_deployment_html(palette, states, figures, live=True):
    """The nodes, the environments inside them and the communication paths, with the live state of each piece.
    D-448: the SAD draws it with live=False, a fixed picture without the state dots and the next run."""
    parts, envs = build_contents(states, figures, live)
    head = (
        f'<defs><marker id="dep-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto"><path d="M0 0 10 5 0 10z" fill="{palette["accent"]}"/></marker></defs>'
    )
    drawn, tips = [], []
    for key, (x, y, width, height, stereotype, name) in NODES.items():
        drawn.append(f'<g class="node" id="n-{key}" tabindex="0">{box(x, y, width, height)}{parts[key]}</g>')
    for key, (x, y, width, height, node, name) in ENVIRONMENTS.items():
        inner = " inner" if key == "python" else ""
        drawn.append(
            f'<g class="envg" id="n-{key}" tabindex="0"><rect class="env{inner}" x="{x}" y="{y}" width="{width}" '
            f'height="{height}" rx="6"/>{envs[key]}</g>'
        )
    for key in list(NODES) + list(ENVIRONMENTS):
        x, y, width, height = NODES[key][:4] if key in NODES else ENVIRONMENTS[key][:4]
        tx = min(max(x, 8), WIDTH - 308)
        up = y + height > 440
        tips.append(
            f'<g class="tip" id="tip-{key}"><foreignObject x="{tx}" y="{y - 6 if up else y + height + 8}" width="300" height="1" '
            f'overflow="visible"><div xmlns="http://www.w3.org/1999/xhtml" style="{"bottom:0" if up else "top:0"}">'
            f'<b>{esc((NODES.get(key) or ENVIRONMENTS[key])[5])}</b>{esc(TIPS[key])}</div></foreignObject></g>'
        )
    paths = "".join(f'<path class="path" d="{d}" marker-end="url(#dep-head)"/>' for d, *_ in PATHS)
    chips = "".join(
        f'<text class="chip" x="{pos[0]}" y="{pos[1] + 18 * row}">{esc(line)}</text>'
        for _, label, pos in PATHS
        if label
        for row, line in enumerate(label if isinstance(label, tuple) else (label,))
    )
    legend = (
        (
            f'<circle cx="26" cy="550" r="5" fill="{architecture.STATE_COLORS[control.RUN_OK]}"/>'
            '<text class="legend" x="38" y="554">estado de la última ejecución y del panel · la línea muestra quién inicia la comunicación</text>'
        )
        if live
        else '<text class="legend" x="26" y="554">la línea muestra quién inicia la comunicación</text>'
    )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        + build_css(palette)
        + f'</head><body>{quality_view.DEFS}<svg class="dep" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'preserveAspectRatio="xMidYMid meet" role="img" aria-label="Diagrama de despliegue">{head}{"".join(drawn)}'
        f'{paths}{chips}{legend}{"".join(tips)}</svg></body></html>'
    )


# endregion
