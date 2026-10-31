"""«Despliegue» (D-255): the deployment diagram of GreenOcean, in the form of the UML deployment diagram.

Nodes are the 3D boxes where something runs (devices and platforms); inside them, the execution environments
(a runner, a Python process, a repository) hold the artifacts that are deployed there (files, databases,
workflows). The lines are the communication paths, each with its protocol. Every piece is a real one: the workflows
in .github/workflows/, the files of the repository and the services the panel talks to. The live part reads the
state of the weekly workflow and of the panel, the size of the served database and the dates of the last load.

build_deployment_html() returns one HTML document for st.iframe (CSS only, no script).
"""

import html
from pathlib import Path
from urllib.parse import urlparse

from bi import architecture, charts, control, project, queries, quality_view

WIDTH, HEIGHT = 1000, 566
DEPTH = 12
REPOSITORY = Path(__file__).resolve().parent.parent
# Nodes: key -> (x, y, width, height, stereotype, name). (x, y) is the front face; the top and the side stick out DEPTH.
NODES = {
    "odepa": (20, 40, 230, 92, "dispositivo", "ODEPA"),
    "ine": (20, 160, 230, 90, "dispositivo", "INE"),
    "author": (20, 300, 230, 190, "dispositivo", "Computador del autor"),
    "github": (320, 40, 470, 480, "plataforma", "GitHub"),
    "streamlit": (810, 40, 175, 300, "plataforma", "Streamlit Cloud"),
    "browser": (810, 392, 175, 80, "dispositivo", "Navegador"),
}
# Execution environments, nested in a node: key -> (x, y, width, height, node, name).
ENVIRONMENTS = {
    "runner": (336, 84, 206, 236, "github", "Runner ubuntu-latest"),
    "python": (346, 216, 186, 96, "github", "Python 3.11"),
    "repo": (336, 358, 206, 150, "github", "Repositorio · rama main"),
    "cache": (590, 84, 180, 56, "github", "Caché de Actions"),
    "issues": (590, 178, 180, 56, "github", "Pull requests"),
    "app": (822, 84, 151, 236, "streamlit", "Streamlit"),
    "venv": (32, 344, 206, 134, "author", "Python 3.11 o 3.12"),
}
# Communication paths: (path, protocol, chip position). Straight segments only. A protocol of two lines is a tuple.
PATHS = [
    ("M250 86 H298 V124 H336", "HTTPS", (254, 80)),
    ("M250 199 H310 V158 H336", "HTTPS", (254, 193)),
    ("M250 420 H336", "git push", (262, 414)),
    ("M440 320 V358", "git push", (452, 344)),
    ("M542 112 H590", "", None),
    ("M542 206 H590", "", None),
    ("M810 158 H542", ("API REST de GitHub", "lanzar, leer estado y logs, cancelar"), (548, 152)),  # D-370
    ("M542 440 H640 V300 H810", "despliegue de main", (650, 294)),
    ("M897 392 V340", "HTTPS", (908, 372)),
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
    "runner": "Una máquina Ubuntu de GitHub Actions que nace y se borra en cada ejecución: el job semanal de cada martes "
    "(semanal.yml) y las pruebas de cada push (pruebas.yml).",
    "python": "El entorno Python 3.11 del runner: descarga, aterrizaje en SQLite, bronce en Parquet y dbt build sobre DuckDB.",
    "repo": "El repositorio público: el código en la rama main y la base servida en el release «base-actual». Solo si pasan "
    "todas las pruebas, la carga reemplaza la base del release y sube su puntero con un commit «Weekly data update» (D-270).",
    "cache": "Guarda los CSV de los años cerrados, que ya no cambian, para no descargarlos cada semana. Se borra si no se usa en 7 días.",
    "issues": "Después de cada carga semanal, el workflow de calidad propone el informe semanal numerado como un pull "
    "request, que el autor revisa y aprueba antes de que el panel lo muestre (D-331, D-363).",
    "app": "Streamlit ejecuta bi/dashboard.py desde la rama main. Descarga del release la base de la última carga, comprueba su "
    "huella y la lee en solo lectura; guarda los secretos del panel y, con la clave de control, lanza la carga por la API de GitHub.",
    "browser": "Cualquier visitante, o el autor. El panel público no pide cuenta; la clave solo abre el botón «Ejecutar pipeline ahora».",
}


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
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
svg.dep {{ display:block; width:100%; height:auto; overflow:visible; }}
.front {{ fill:{'rgba(255,255,255,.04)' if dark else '#ffffff'}; stroke:{ink}; stroke-width:1.5; }}
.top {{ fill:{'rgba(255,255,255,.10)' if dark else '#e3e9f2'}; stroke:{ink}; stroke-width:1.5; stroke-linejoin:round; }}
.side {{ fill:{'rgba(255,255,255,.02)' if dark else '#cfd8e6'}; stroke:{ink}; stroke-width:1.5; stroke-linejoin:round; }}
.env {{ fill:{card}; stroke:{muted}; stroke-width:1.2; }}
.env.inner {{ fill:{'rgba(255,255,255,.05)' if dark else '#f4f7fb'}; stroke-dasharray:5 4; }}
.node, .envg {{ outline:none; cursor:default; }}
.node:hover .front, .node:focus .front, .envg:hover .env, .envg:focus .env {{ stroke:{accent}; }}
.stereo {{ font-size:11.5px; font-style:italic; fill:{muted}; }}
.name {{ font-size:13.5px; font-weight:700; fill:{ink}; }}
.note {{ font-size:11.5px; fill:{muted}; }}
.art {{ font:500 11.5px ui-monospace, SFMono-Regular, Menlo, monospace; fill:{ink}; }}
.live {{ font-size:12px; font-weight:600; fill:{accent}; }}
.page {{ fill:{card}; stroke:{ink}; stroke-width:1.1; }}
.fold {{ fill:none; stroke:{ink}; stroke-width:1.1; }}
.path {{ fill:none; stroke:{accent}; stroke-width:1.8; }}
.chip {{ font:600 11.5px ui-monospace, SFMono-Regular, Menlo, monospace; fill:{ink}; paint-order:stroke; stroke:{palette['background']}; stroke-width:4px; }}
.legend {{ font-size:11.5px; fill:{muted}; }}
.tip {{ opacity:0; pointer-events:none; transition:opacity .15s ease; }}
.tip div {{ position:absolute; width:300px; padding:12px 14px; border-radius:14px; background:{card}; border:1px solid {border};
  box-shadow:0 18px 40px rgba(0,0,0,{'.55' if dark else '.2'}); color:{text}; font-size:12.5px; line-height:1.45; }}
.tip b {{ display:block; margin-bottom:3px; font-size:13px; color:{ink}; }}
@media print {{ .tip {{ display:none !important; }} }}
{hovers}
</style>"""


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


def read_hosts():
    ine_host = urlparse(project.INE_IPC_SOURCE_URL).netloc
    odepa_host = urlparse(project.WHOLESALE_SOURCE_URL).netloc
    return odepa_host, ine_host


def build_contents(states, figures):
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
        "streamlit": heading(824, 64, "plataforma", "Streamlit Cloud"),
        "browser": (
            heading(824, 416, "dispositivo", "Navegador")
            + '<text class="note" x="824" y="452">visitante o autor, sin cuenta</text>'
        ),
    }
    envs = {
        "runner": (
            heading(348, 104, "entorno de ejecución", "Runner ubuntu-latest")
            + '<text class="note" x="348" y="138">efímero: nace en cada ejecución</text>'
            + artifact(348, 158, "semanal.yml")
            + f'<text class="live" x="366" y="173">próxima {esc(figures.get("next_run", ""))}</text>'
            + artifact(348, 192, "pruebas.yml")
            + '<text class="note" x="366" y="207">en cada push</text>'
            + state_dot(526, 102, states.get("workflow"))
        ),
        "python": (
            heading(356, 234, "entorno de ejecución", "Python 3.11")
            + artifact(356, 270, "agent.py · etl.py")
            + artifact(356, 286, "bronze.py")
            + artifact(356, 302, "dbt build · DuckDB")
        ),
        "repo": (
            heading(348, 378, "entorno de ejecución", "Repositorio · main y release")
            + artifact(348, 414, "código del proyecto")
            + artifact(348, 430, f"datos.duckdb · {project.describe_file_size(queries.DATABASE_FILE)}")
            + artifact(348, 446, "datos.version · puntero")
            + artifact(348, 462, "manifest.json")
            + f'<text class="live" x="348" y="486">{esc(figures.get("week_prices", ""))}</text>'
        ),
        "cache": heading(602, 100, "entorno de ejecución", "Caché de Actions")
        + artifact(602, 134, "CSV de años cerrados"),
        "issues": heading(602, 194, "entorno de ejecución", "Pull requests") + artifact(602, 228, "informe semanal"),
        "app": (
            heading(834, 104, "entorno de ejecución", "Streamlit")
            + artifact(834, 150, "dashboard.py")
            + artifact(834, 172, "datos.duckdb")
            + '<text class="note" x="852" y="187">solo lectura</text>'
            + artifact(834, 210, "st.secrets")
            + '<text class="note" x="852" y="225">token y clave</text>'
            + f'<text class="live" x="834" y="256">{esc(figures.get("panel_time", ""))}</text>'
            + state_dot(958, 118, states.get("panel"))
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


def build_deployment_html(palette, states, figures):
    """The nodes, the environments inside them and the communication paths, with the live state of each piece."""
    parts, envs = build_contents(states, figures)
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
        f'<circle cx="26" cy="550" r="5" fill="{architecture.STATE_COLORS[control.RUN_OK]}"/>'
        '<text class="legend" x="38" y="554">estado de la última ejecución y del panel · la línea muestra quién inicia la comunicación</text>'
    )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        + build_css(palette)
        + f'</head><body>{quality_view.DEFS}<svg class="dep" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'preserveAspectRatio="xMidYMid meet" role="img" aria-label="Diagrama de despliegue">{head}{"".join(drawn)}'
        f'{paths}{chips}{legend}{"".join(tips)}</svg></body></html>'
    )
