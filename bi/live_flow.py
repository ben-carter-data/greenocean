"""«Flujo del sistema en vivo» (D-412): the real architecture of the project in one view, with real data.

High level, not by layers: the pieces (the sources, GitHub, the weekly load's runner, Streamlit Community Cloud, the app
and the browser, and a DevSecOps band) and the communications between them. Each arrow says who asks, what it asks,
what comes back and when; one that cannot be read anywhere is marked «deducido». The animation follows the user's rule:
a piece that works alone (dbt transforming, pytest testing) lights up and pulses; a communication is a message that
travels along its arrow from whoever asks to whoever answers, and the answer comes back along the same path.

One model serves three places: the page (in «Stack y evidencia»), the window of a manual run (focused on the run) and
the fixed picture of the SAD (no script). Pure: no Streamlit and no network; the page passes what GitHub, the database
and the files said. No token, header or log ever reaches this module.
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from bi import architecture, brand_icons, charts, control, i18n

WIDTH, HEIGHT = 1320, 650
TOP = -8  # the deduced redeploy runs above GitHub
FOCUS_BOX = (-10, TOP, 1190, 525)  # the run window: sources, GitHub and the runner
TILE = 56
CHILE = ZoneInfo("America/Santiago")
GROUP_COLORS = {
    "sources": architecture.LAYER_COLORS["sources"],
    "github": "#8a8fa3",
    "runner": architecture.LAYER_COLORS["processing"],
    "cloud": architecture.LAYER_COLORS["consumption"],
    "people": architecture.LAYER_COLORS["ingestion"],
    "devsecops": architecture.LAYER_COLORS["quality"],
}
REQUEST_COLOR = "#5b9cf0"
ANSWER_COLOR = "#22b35a"
WORKING_COLOR = "#eda100"


def t(pair: tuple[str, str]) -> str:
    return pair[1] if i18n.is_english() else pair[0]


def esc(value: Any) -> str:
    return html.escape(str(value))


# region Icons: the logos of the stack, and plain line drawings for the rest


def draw_package_icon(x: float, y: float, color: str) -> str:
    """A box with its lid: a release of GitHub."""
    return (
        f'<path d="M{x - 15} {y - 8} l15 -8 l15 8 v17 l-15 8 l-15 -8 z M{x - 15} {y - 8} l15 8 l15 -8 M{x} {y} v17" '
        f'fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round"/>'
    )


def draw_key_icon(x: float, y: float, color: str) -> str:
    return (
        f'<circle cx="{x - 7}" cy="{y}" r="7" fill="none" stroke="{color}" stroke-width="2.2"/>'
        f'<path d="M{x} {y} h15 m-5 0 v6 m-5 -6 v4" fill="none" stroke="{color}" stroke-width="2.2" '
        f'stroke-linecap="round"/>'
    )


def draw_lock_icon(x: float, y: float, color: str) -> str:
    return (
        f'<rect x="{x - 11}" y="{y - 3}" width="22" height="17" rx="3" fill="none" stroke="{color}" stroke-width="2.2"/>'
        f'<path d="M{x - 6} {y - 3} v-5 a6 6 0 0 1 12 0 v5" fill="none" stroke="{color}" stroke-width="2.2"/>'
    )


def draw_browser_icon(x: float, y: float, color: str) -> str:
    return (
        f'<rect x="{x - 16}" y="{y - 12}" width="32" height="24" rx="3" fill="none" stroke="{color}" '
        f'stroke-width="2.2"/><path d="M{x - 16} {y - 5} h32" stroke="{color}" stroke-width="2"/>'
        f'<circle cx="{x - 11}" cy="{y - 8.5}" r="1.3" fill="{color}"/>'
        f'<circle cx="{x - 7}" cy="{y - 8.5}" r="1.3" fill="{color}"/>'
    )


def draw_archive_icon(x: float, y: float, color: str) -> str:
    """A drawer of files: the Actions cache."""
    return (
        f'<rect x="{x - 15}" y="{y - 13}" width="30" height="9" rx="2" fill="none" stroke="{color}" stroke-width="2.2"/>'
        f'<path d="M{x - 13} {y - 4} v15 h26 v-15 M{x - 5} {y + 2} h10" fill="none" stroke="{color}" '
        f'stroke-width="2.2" stroke-linecap="round"/>'
    )


def logo(slug: str) -> Any:
    return lambda x, y, color: brand_icons.logo(slug, x - 17, y - 17, color, 34)


ICONS = {
    "file": architecture.draw_file_icon,
    "chart": architecture.draw_chart_icon,
    "package": draw_package_icon,
    "clock": architecture.draw_clock_icon,
    "archive": draw_archive_icon,
    "git": logo("git"),
    "report": architecture.draw_report_icon,
    "code": architecture.draw_code_icon,
    "python": logo("python"),
    "sqlite": logo("sqlite"),
    "parquet": logo("apacheparquet"),
    "dbt": logo("dbt"),
    "duckdb": logo("duckdb"),
    "pytest": logo("pytest"),
    "streamlit": logo("streamlit"),
    "browser": draw_browser_icon,
    "shield": architecture.draw_shield_icon,
    "key": draw_key_icon,
    "lock": draw_lock_icon,
}

# endregion


# region The pieces and the messages

# id: (group, x, y, icon, title, detail, evidence file, text in that file that proves the piece is real)
PIECES: dict[str, tuple[str, int, int, str, tuple[str, str], tuple[str, str], str, str]] = {
    "pypi": (
        "sources",
        50,
        200,
        "package",
        ("PyPI", "PyPI"),
        ("paquetes", "packages"),
        "requirements-pipeline.txt",
        "dbt-duckdb",
    ),
    "odepa": (
        "sources",
        50,
        330,
        "file",
        ("ODEPA", "ODEPA"),
        ("precios en CSV", "prices in CSV"),
        "agent/input.csv",
        "datos.odepa.gob.cl",
    ),
    "ine": ("sources", 50, 440, "chart", ("INE", "INE"), ("IPC de alimentos", "food CPI"), "etl/ine.py", "ine.gob.cl"),
    "actions": (
        "github",
        250,
        82,
        "clock",
        ("Actions", "Actions"),
        ("cron martes 12:00 UTC", "cron Tue 12:00 UTC"),
        ".github/workflows/semanal.yml",
        'cron: "0 12 * * 2"',
    ),
    "cache": (
        "github",
        390,
        82,
        "archive",
        ("Caché", "Cache"),
        ("años cerrados", "closed years"),
        ".github/workflows/semanal.yml",
        "actions/cache@v4",
    ),
    "repo": ("github", 530, 82, "git", ("Repositorio", "Repository"), ("main", "main"), "etl/datos.version", "sha256"),
    "issues": (
        "github",
        670,
        82,
        "report",
        ("Issues y PR", "Issues and PRs"),
        ("informes", "reports"),
        ".github/workflows/semanal.yml",
        "gh issue create",
    ),
    "release": (
        "github",
        900,
        82,
        "package",
        ("Release", "Release"),
        ("«base-actual»", "«base-actual»"),
        "bi/served_database.py",
        "base-actual",
    ),
    "api": (
        "github",
        1090,
        82,
        "code",
        ("API REST", "REST API"),
        ("api.github.com", "api.github.com"),
        "bi/control.py",
        "api.github.com",
    ),
    "python": (
        "runner",
        230,
        345,
        "python",
        ("Python", "Python"),
        ("agente y ETL", "agent and ETL"),
        "agent/agent.py",
        "requests",
    ),
    "sqlite": ("runner", 342, 345, "sqlite", ("SQLite", "SQLite"), ("respaldo", "backup"), "etl/etl.py", "sqlite3"),
    "parquet": (
        "runner",
        454,
        345,
        "parquet",
        ("Parquet", "Parquet"),
        ("bronce", "bronze"),
        "etl/bronze.py",
        "parquet",
    ),
    "dbt": (
        "runner",
        566,
        345,
        "dbt",
        ("dbt", "dbt"),
        ("staging → marts", "staging → marts"),
        "dbt/dbt_project.yml",
        "profile:",
    ),
    "duckdb": (
        "runner",
        678,
        345,
        "duckdb",
        ("DuckDB", "DuckDB"),
        ("datos.duckdb", "datos.duckdb"),
        "etl/pipeline.py",
        "duckdb",
    ),
    "pytest": (
        "runner",
        790,
        345,
        "pytest",
        ("pytest", "pytest"),
        ("pruebas de datos", "data tests"),
        ".github/workflows/semanal.yml",
        'pytest -q -m "datos',
    ),
    "app": (
        "cloud",
        1000,
        345,
        "streamlit",
        ("App", "App"),
        ("bi/dashboard.py", "bi/dashboard.py"),
        "bi/dashboard.py",
        "import streamlit",
    ),
    "browser": (
        "people",
        1240,
        345,
        "browser",
        ("Navegador", "Browser"),
        ("las tres vistas", "the three views"),
        "bi/dashboard.py",
        "PROFILE_PUBLIC",
    ),
    "ci": (
        "devsecops",
        280,
        552,
        "shield",
        ("CI en cada push", "CI on every push"),
        ("Ruff · mypy · pytest", "Ruff · mypy · pytest"),
        ".github/workflows/pruebas.yml",
        "mypy",
    ),
    "quality": (
        "devsecops",
        500,
        552,
        "report",
        ("Calidad", "Quality"),
        ("12 indicadores · informe", "12 indicators · report"),
        ".github/workflows/calidad.yml",
        "workflow_run",
    ),
    "tokens": (
        "devsecops",
        720,
        552,
        "key",
        ("Secretos y tokens", "Secrets and tokens"),
        ("lanzar · solo lectura", "launch · read only"),
        "bi/dashboard.py",
        "GITHUB_READ_TOKEN",
    ),
    "jobtoken": (
        "devsecops",
        940,
        552,
        "key",
        ("github.token", "github.token"),
        ("permisos del job", "job permissions"),
        ".github/workflows/semanal.yml",
        "github.token",
    ),
    "gate": (
        "devsecops",
        1160,
        552,
        "lock",
        ("Puerta de Autor", "Author gate"),
        ("3 fallos → espera", "3 failures → wait"),
        "bi/control.py",
        "class AttemptGate",
    ),
}
# What each DevSecOps piece does, said on hover (it has no arrow of its own).
BAND_NOTES = {
    "ci": (
        "En cada push corren Ruff, mypy y pytest (pruebas.yml); un fallo se ve antes de llegar a la app.",
        "On every push Ruff, mypy and pytest run (pruebas.yml); a failure shows before it reaches the app.",
    ),
    "quality": (
        "Mide los 12 indicadores en cada push y, después de cada carga, propone el informe en un pull request.",
        "Measures the 12 indicators on every push and, after each load, proposes the report in a pull request.",
    ),
    "tokens": (
        "CONTROL_CODE, GITHUB_TOKEN y GITHUB_READ_TOKEN viven en los secretos de Streamlit; nunca se muestran.",
        "CONTROL_CODE, GITHUB_TOKEN and GITHUB_READ_TOKEN live in Streamlit's secrets; they are never shown.",
    ),
    "jobtoken": (
        "La carga publica con el token propio del job: escribe contenido e issues, nada más.",
        "The load publishes with the job's own token: it writes contents and issues, nothing else.",
    ),
    "gate": (
        "La clave abre las páginas del Autor; tras 3 fallos cada intento espera 2 s, el doble cada vez, hasta 15 min (D-393).",
        "The key opens the Author's pages; after 3 failures each try waits 2 s, twice as long each time, up to 15 min (D-393).",
    ),
}
GROUPS = [
    # (group, x, y, width, height, title)
    ("github", 170, 16, 1000, 170, ("GITHUB", "GITHUB")),
    ("runner", 170, 262, 660, 200, ("CARGA SEMANAL · RUNNER UBUNTU", "WEEKLY LOAD · UBUNTU RUNNER")),
    ("cloud", 900, 262, 270, 200, ("STREAMLIT COMMUNITY CLOUD", "STREAMLIT COMMUNITY CLOUD")),
    ("devsecops", 170, 500, 1130, 140, ("DEVSECOPS", "DEVSECOPS")),
]

# id: who asks, who answers, path drawn from the one who asks, where its label goes, label, what is asked, what comes
# back, when, what for, deduced (nothing in GitHub or the database says it: it is how the service works).
ARROWS: dict[str, dict[str, Any]] = {
    "start": {
        "ask_by": "actions",
        "answer_by": "runner",
        "d": "M250 150 V262",
        "label_at": (250, 212),
        "label": ("inicia el job", "starts the job"),
        "ask": ("Arranca el job weekly-load en un runner ubuntu", "Starts the weekly-load job on an ubuntu runner"),
        "answer": ("El resultado de cada paso y el de la ejecución", "The result of every step and of the run"),
        "when": (
            "Cada martes a las 12:00 UTC (cron), o a mano con «Ejecutar pipeline ahora»",
            "Every Tuesday at 12:00 UTC (cron), or by hand with «Run pipeline now»",
        ),
        "why": (
            "Nadie tiene que acordarse de cargar los datos: GitHub los carga cada semana.",
            "Nobody has to remember to load the data: GitHub loads it every week.",
        ),
    },
    "pypi": {
        "ask_by": "runner",
        "answer_by": "pypi",
        "d": "M188 262 V200 H78",
        "label_at": (133, 200),
        "label": ("pip install", "pip install"),
        "ask": ("pip install -r requirements-pipeline.txt", "pip install -r requirements-pipeline.txt"),
        "answer": (
            "Los paquetes de Python en las versiones del proyecto",
            "The Python packages in the project's versions",
        ),
        "when": ("Al empezar cada carga", "At the start of every load"),
        "why": (
            "El runner empieza vacío: cada carga instala lo mismo.",
            "The runner starts empty: every load installs the same.",
        ),
    },
    "cache": {
        "ask_by": "runner",
        "answer_by": "cache",
        "d": "M390 262 V150",
        "label_at": (390, 212),
        "label": ("restaura CSV", "restores CSV"),
        "ask": (
            "Pide los CSV de los años cerrados guardados en la caché",
            "Asks for the closed years' CSV kept in the cache",
        ),
        "answer": (
            "Los archivos, o nada si la caché venció (7 días sin uso)",
            "The files, or nothing if the cache expired (7 days unused)",
        ),
        "when": ("En cada carga, antes de descargar", "On every load, before downloading"),
        "why": (
            "Los años cerrados no cambian: no se descargan otra vez (D-047).",
            "Closed years do not change: they are not downloaded again (D-047).",
        ),
    },
    "repo": {
        "ask_by": "runner",
        "answer_by": "repo",
        "d": "M530 262 V150",
        "label_at": (530, 212),
        "label": ("checkout · push", "checkout · push"),
        "ask": (
            "Clona main (actions/checkout) y, al publicar, sube el puntero etl/datos.version con git push",
            "Clones main (actions/checkout) and, when publishing, pushes the pointer etl/datos.version",
        ),
        "answer": (
            "El código del proyecto; después, el commit «Weekly data update» en main",
            "The project's code; then, the commit «Weekly data update» on main",
        ),
        "when": ("Al empezar y al publicar", "At the start and when publishing"),
        "why": (
            "La carga usa el código de main; git guarda solo el puntero de la base, no el archivo (D-270).",
            "The load uses main's code; git keeps only the database's pointer, not the file (D-270).",
        ),
    },
    "issues": {
        "ask_by": "runner",
        "answer_by": "issues",
        "d": "M670 262 V150",
        "label_at": (670, 212),
        "label": ("crea el informe", "creates the report"),
        "ask": ("gh issue create «Informe semanal AAAA-MM-DD»", "gh issue create «Informe semanal YYYY-MM-DD»"),
        "answer": ("El issue con el informe de la carga", "The issue with the load's report"),
        "when": ("Al final de cada carga publicada", "At the end of every published load"),
        "why": (
            "Cada semana queda escrita en un lugar que cualquiera puede leer.",
            "Every week stays written where anyone can read it.",
        ),
    },
    "release": {
        "ask_by": "runner",
        "answer_by": "release",
        "d": "M830 300 H872 V150",
        "label_at": (872, 212),
        "label": ("datos.duckdb", "datos.duckdb"),
        "ask": (
            "Descarga la base publicada y, al publicar, la reemplaza con gh release upload",
            "Downloads the published database and, when publishing, replaces it with gh release upload",
        ),
        "answer": (
            "La base anterior con su huella SHA-256; después, el archivo nuevo en el release",
            "The previous database with its SHA-256 fingerprint; then, the new file in the release",
        ),
        "when": ("Al empezar la carga y al publicarla", "At the start of the load and when publishing it"),
        "why": (
            "La base nueva solo se sube si pasó todas las pruebas: el panel nunca lee una a medias (ADR-11).",
            "The new database is uploaded only if it passed every test: the panel never reads a half one (ADR-11).",
        ),
    },
    "odepa": {
        "ask_by": "runner",
        "answer_by": "odepa",
        "d": "M170 330 H78",
        "label_at": (124, 330),
        "label": ("GET CSV", "GET CSV"),
        "ask": (
            "GET por HTTPS de cada CSV del año en curso (agent/agent.py)",
            "HTTPS GET of each CSV of the current year (agent/agent.py)",
        ),
        "answer": ("Los CSV de precios mayoristas y al consumidor", "The CSV of wholesale and consumer prices"),
        "when": (
            "En cada carga; los años cerrados vienen de la caché",
            "On every load; closed years come from the cache",
        ),
        "why": (
            "ODEPA publica los precios como datos abiertos; el agente anota la huella de cada archivo.",
            "ODEPA publishes the prices as open data; the agent writes down each file's fingerprint.",
        ),
    },
    "ine": {
        "ask_by": "runner",
        "answer_by": "ine",
        "d": "M170 440 H78",
        "label_at": (124, 440),
        "label": ("GET IPC", "GET CPI"),
        "ask": (
            "GET por HTTPS de las series del IPC de alimentos (etl/ine.py)",
            "HTTPS GET of the food CPI series (etl/ine.py)",
        ),
        "answer": ("Las series mensuales del IPC", "The monthly CPI series"),
        "when": ("Dentro de la construcción con dbt", "Inside the build with dbt"),
        "why": (
            "Con el IPC se calculan los precios reales, sin inflación.",
            "With the CPI the real prices are calculated, without inflation.",
        ),
    },
    "app_release": {
        "ask_by": "app",
        "answer_by": "release",
        "d": "M985 317 V236 H922 V150",
        "label_at": (985, 252),
        "label": ("lee la base", "reads the database"),
        "ask": (
            "Descarga datos.duckdb (bi/served_database.py) y comprueba su huella",
            "Downloads datos.duckdb (bi/served_database.py) and checks its fingerprint",
        ),
        "answer": (
            "La base servida, que la app abre en solo lectura",
            "The served database, which the app opens read-only",
        ),
        "when": ("Al arrancar la app y cuando cambia el puntero", "When the app starts and when the pointer changes"),
        "why": (
            "El panel lee siempre la última base publicada.",
            "The panel always reads the latest published database.",
        ),
    },
    "app_api": {
        "ask_by": "app",
        "answer_by": "api",
        "d": "M1028 330 H1090 V150",
        "label_at": (1090, 212),
        "label": ("lanzar · leer", "launch · read"),
        "ask": (
            "Lanzar: POST workflow_dispatch. Leer: GET de las ejecuciones y sus pasos",
            "Launch: POST workflow_dispatch. Read: GET of the runs and their steps",
        ),
        "answer": (
            "204, aceptada; JSON con el estado de cada paso",
            "204, accepted; JSON with the state of every step",
        ),
        "when": (
            "Al lanzar, con la clave; mientras corre, cada 30 s aquí y cada 4 s en la ventana de la ejecución",
            "When launching, with the key; while it runs, every 30 s here and every 4 s in the run's window",
        ),
        "why": ("El panel sigue la carga sin abrir GitHub.", "The panel follows the load without opening GitHub."),
    },
    "browser": {
        "ask_by": "browser",
        "answer_by": "app",
        "d": "M1212 360 H1028",
        "label_at": (1170, 360),
        "label": ("HTTPS", "HTTPS"),
        "ask": (
            "Abre una página por HTTPS (WebSocket de Streamlit)",
            "Opens a page over HTTPS (Streamlit's WebSocket)",
        ),
        "answer": ("La página dibujada con los datos de la base", "The page drawn with the database's data"),
        "when": ("En cada visita", "On every visit"),
        "why": (
            "Usuario, Profesional y Autor ven el mismo panel; la clave solo abre las páginas del Autor.",
            "User, Professional and Author see the same panel; the key only opens the Author's pages.",
        ),
    },
    "deploy": {
        "ask_by": "repo",
        "answer_by": "app",
        "d": "M530 54 V6 H1150 V262",
        "label_at": (840, 6),
        "deduced": True,
        "label": ("push a main", "push to main"),
        "ask": ("Un push a main", "A push to main"),
        "answer": (
            "Streamlit Community Cloud vuelve a desplegar la app",
            "Streamlit Community Cloud deploys the app again",
        ),
        "when": ("Después de cada push a main", "After every push to main"),
        "why": (
            "La app publicada siempre es la de main. GitHub no lo informa: se deduce de cómo trabaja Streamlit.",
            "The published app is always main's. GitHub does not report it: it is deduced from how Streamlit works.",
        ),
    },
}
RUNNER = "runner"
# Each step of semanal.yml (as GitHub names it in the run) and what it moves: arrows travel, pieces work.
STEP_ELEMENTS: dict[str, list[str]] = {
    "Set up job": ["start"],
    "Run actions/checkout@v4": ["repo"],
    "Run actions/setup-python@v5": ["python"],
    "Run pip install -r requirements-pipeline.txt": ["pypi"],
    "Find the current year": ["python"],
    "Restore the closed-year files": ["cache"],
    "Get the published database": ["release"],
    "Download the ODEPA files": ["odepa"],
    "Run the ETL (SQLite backup)": ["python", "sqlite"],
    "Build the data warehouse with dbt": ["ine", "parquet", "dbt", "duckdb"],
    "Simulate a failure": [RUNNER],
    "Run the tests against the new database": ["pytest"],
    "Publish the database": ["release", "repo"],
    "Publish the weekly report": ["issues"],
    "Post Restore the closed-year files": ["cache"],
    "Post Run actions/setup-python@v5": ["python"],
    "Post Run actions/checkout@v4": ["repo"],
    "Complete job": ["start"],
}


def step_elements(name: str) -> list[str]:
    """What a step moves; a step GitHub adds that is not in the table works inside the runner."""
    return STEP_ELEMENTS.get(name, [RUNNER])


# endregion


# region The model: what is shown, from what GitHub, the database and the files said


def format_moment(moment: datetime | None) -> str:
    if moment is None:
        return "—"
    local = moment.astimezone(CHILE)
    return f"{local:%Y-%m-%d %H:%M}" if i18n.is_english() else f"{local:%d-%m-%Y %H:%M}"


def megabytes(size: float) -> str:
    text = f"{size / 1_000_000:.1f}"
    return f"{text} MB" if i18n.is_english() else f"{text.replace('.', ',')} MB"


def read_facts(manifest: dict[str, Any], pointer: dict[str, Any], ipc_months: int, packages: int) -> dict[str, str]:
    """What travelled in the last real load, read from the files the load leaves: manifest.json (each CSV with its size
    and time), etl/datos.version (the published database) and the database (the CPI months). Only facts, no guesses."""
    published = control.parse_github_time(str(pointer.get("published_at", "")).replace("+00:00", "Z"))
    newest = max((entry.get("downloaded_at", "") for entry in manifest.values()), default="")
    latest = [entry for entry in manifest.values() if entry.get("downloaded_at", "")[:10] == newest[:10]]
    closed = [entry for entry in manifest.values() if entry not in latest]
    sha = str(pointer.get("sha256", ""))[:12]
    database = t(("datos.duckdb · {} · huella {}…", "datos.duckdb · {} · fingerprint {}…")).format(
        megabytes(pointer.get("bytes", 0)), sha
    )
    return {
        "odepa": t(("{} archivos · {} · {}", "{} files · {} · {}")).format(
            len(latest),
            megabytes(sum(entry.get("bytes", 0) for entry in latest)),
            format_moment(control.parse_github_time(f"{newest}Z") if newest else None),  # the runner's clock is UTC
        ),
        "cache": t(("{} archivos de años cerrados", "{} files of closed years")).format(len(closed)),
        "release": f"{database} · {format_moment(published)}",
        "app_release": database,
        "repo": t(("puntero {}… · {}", "pointer {}… · {}")).format(sha, format_moment(published)),
        "ine": t(("{} meses del IPC", "{} CPI months")).format(ipc_months),
        "pypi": t(("{} paquetes del proyecto", "{} packages of the project")).format(packages),
        "issues": t(("«Informe semanal {}»", "«Informe semanal {}»")).format(
            f"{published:%Y-%m-%d}" if published else "—"
        ),
    }


def build_model(runs: list[dict[str, Any]], steps: list[dict[str, Any]], facts: dict[str, str]) -> dict[str, Any]:
    """The state to draw. `runs` are the weekly workflow's latest runs, newest first; `steps` are the steps of the run
    shown: the one in progress (live) or, without one, the latest that ended (still, and replayable)."""
    current = runs[0] if runs else None
    live = bool(current and current["state"] == control.RUN_IN_PROGRESS)
    shown = current if live else next((run for run in runs if run["state"] != control.RUN_IN_PROGRESS), None)
    timeline = [
        {"name": step["name"], "elements": step_elements(step["name"]), "state": step["state"]}
        for step in steps
        if step["state"] != "skipped"
    ]
    words = {control.RUN_OK: ("correcta", "successful"), control.RUN_FAILED: ("falló", "failed")}
    if live:
        running = next((step for step in timeline if step["state"] == control.RUN_IN_PROGRESS), None)
        status = t(("En curso · {}", "Running · {}")).format(
            running["name"] if running else t(("iniciando", "starting"))
        )
    elif shown:
        status = t(
            ("Sin ejecución en curso · última ejecución real: {} ({})", "No run in progress · latest real run: {} ({})")
        ).format(format_moment(shown["started_at"]), t(words.get(shown["state"], ("—", "—"))))
    else:
        status = t(
            (
                "Sin datos de GitHub: se muestra la arquitectura, sin estado",
                "No data from GitHub: the architecture, without state",
            )
        )
    return {
        "mode": "live" if live else "still",
        "status": status,
        "timeline": timeline,
        "facts": facts,
        "run_url": shown["url"] if shown else None,
    }


# endregion


# region Drawing


def build_piece(piece_id: str, palette: dict[str, str], clickable: bool = True) -> str:
    group, x, y, icon, title, detail, *_ = PIECES[piece_id]
    color = GROUP_COLORS[group]
    half = TILE / 2
    note = BAND_NOTES.get(piece_id)
    tip = f"<title>{esc(t(title))} · {esc(t(note))}</title>" if note else f"<title>{esc(t(title))}</title>"
    return (
        f'<g class="lf-piece" id="piece-{piece_id}" data-id="{piece_id}">{tip}'
        f'<rect class="lf-tile" x="{x - half}" y="{y - half}" width="{TILE}" height="{TILE}" rx="14" '
        f'fill="{palette["card"]}" stroke="{color}" stroke-width="1.6"/>'
        f"{ICONS[icon](x, y, color)}"
        f'<text x="{x}" y="{y + half + 18}" text-anchor="middle" font-size="15" font-weight="700" '
        f'fill="{palette["strong_text"]}">{esc(t(title))}</text>'
        f'<text x="{x}" y="{y + half + 35}" text-anchor="middle" font-size="12.5" fill="{palette["text"]}">'
        f"{esc(t(detail))}</text></g>"
    )


def build_group(
    group: str, x: int, y: int, width: int, height: int, title: tuple[str, str], palette: dict[str, str]
) -> str:
    color = GROUP_COLORS[group]
    runner = ' id="piece-runner" class="lf-group"' if group == "runner" else ' class="lf-group"'
    return (
        f'<g{runner}><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" fill="none" stroke="{color}" '
        f'stroke-width="1.2" stroke-dasharray="5 5" opacity="0.9"/>'
        f'<text x="{x + 14}" y="{y + 20}" font-size="12" font-weight="700" letter-spacing="1.2" fill="{color}">'
        f"{esc(t(title))}</text></g>"
    )


def build_arrow(arrow_id: str, palette: dict[str, str]) -> str:
    arrow = ARROWS[arrow_id]
    deduced = arrow.get("deduced", False)
    label = t(arrow["label"]) + (t((" · deducido", " · deduced")) if deduced else "")
    x, y = arrow["label_at"]
    width = len(label) * 7 + 16
    dash = ' stroke-dasharray="6 5"' if deduced else ""
    return (
        f'<g class="lf-arrow" id="arrow-{arrow_id}" data-id="{arrow_id}" tabindex="0" role="button" '
        f'aria-label="{esc(label)}">'
        f'<path class="lf-hit" d="{arrow["d"]}" fill="none" stroke="transparent" stroke-width="16"/>'
        f'<path class="lf-line" d="{arrow["d"]}" fill="none" stroke="{palette["text"]}" stroke-width="1.6"{dash} '
        f'marker-end="url(#lf-head)"/>'
        f'<rect class="lf-chip" x="{x - width / 2:.1f}" y="{y - 11}" width="{width:.1f}" height="22" rx="6" '
        f'fill="{palette["card"]}" stroke="{palette["card_border"]}"/>'
        f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-size="12" font-weight="700" font-family="monospace" '
        f'fill="{palette["strong_text"]}">{esc(label)}</text></g>'
    )


def build_svg(palette: dict[str, str], focus: bool = False) -> str:
    """The architecture as one SVG: groups, pieces, arrows. The arrows go first so a piece always sits above a line."""
    box = FOCUS_BOX if focus else (0, TOP, WIDTH, HEIGHT - TOP)
    parts = [
        f'<svg class="lf-svg" viewBox="{" ".join(map(str, box))}" preserveAspectRatio="xMidYMid meet" role="img" '
        f'aria-label="{esc(t(("Flujo del sistema", "System flow")))}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">',
        f'<defs><marker id="lf-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{palette["text"]}"/></marker></defs>',
    ]
    parts += [build_group(*group, palette) for group in GROUPS]
    parts += [build_arrow(arrow_id, palette) for arrow_id in ARROWS]
    parts += [build_piece(piece_id, palette) for piece_id in PIECES]
    parts.append("</svg>")
    return "".join(parts)


def arrow_texts() -> dict[str, dict[str, Any]]:
    """What a click on an arrow says, in the reader's language."""
    names = {piece_id: t(piece[4]) for piece_id, piece in PIECES.items()}
    names[RUNNER] = t(("Runner de la carga", "Load runner"))
    return {
        arrow_id: {
            "title": f"{names[arrow['ask_by']]} → {names[arrow['answer_by']]}",
            "ask": t(arrow["ask"]),
            "answer": t(arrow["answer"]),
            "when": t(arrow["when"]),
            "why": t(arrow["why"]),
            "deduced": arrow.get("deduced", False),
        }
        for arrow_id, arrow in ARROWS.items()
    }


LABELS = {
    "ask": ("Pide", "Asks"),
    "answer": ("Responde", "Answers"),
    "when": ("Cuándo", "When"),
    "why": ("Para qué", "What for"),
    "last": ("En la última ejecución real", "In the latest real run"),
    "deduced": (
        "Deducido: no se puede leer en GitHub ni en la base.",
        "Deduced: it cannot be read on GitHub or in the database.",
    ),
    "replay": ("Repetir la última ejecución", "Replay the latest run"),
    "pause": ("Pausar", "Pause"),
    "resume": ("Seguir", "Resume"),
    "close": ("Cerrar", "Close"),
    "hint": ("Clic en una flecha: qué viaja, de ida y de vuelta.", "Click an arrow: what travels, there and back."),
    "open": ("Abrir la ejecución en GitHub", "Open the run on GitHub"),
}


def build_css(palette: dict[str, str]) -> str:
    return f"""
html, body {{ margin:0; height:100%; background:transparent; color:{palette["strong_text"]};
  font:14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; overflow:hidden; }}
.lf {{ position:relative; height:100vh; display:flex; flex-direction:column; }}
.lf-bar {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; padding:2px 4px 6px; font-size:13px; color:{palette["text"]}; }}
.lf-bar b {{ color:{palette["strong_text"]}; font-weight:600; }}
.lf-bar .lf-dot {{ width:9px; height:9px; border-radius:50%; background:{architecture.STATE_COLORS["unknown"]}; }}
.lf-live .lf-bar .lf-dot {{ background:{REQUEST_COLOR}; animation:lf-blink 1.2s ease-in-out infinite; }}
.lf-bar button {{ font:inherit; font-size:12.5px; color:{palette["strong_text"]}; background:{palette["card"]};
  border:1px solid {palette["card_border"]}; border-radius:999px; padding:3px 12px; cursor:pointer; }}
.lf-bar button:hover {{ border-color:{palette["accent"]}; }}
.lf-bar a {{ color:{palette["accent"]}; font-size:12.5px; }}
.lf-bar .lf-hint {{ margin-left:auto; font-size:12px; }}
.lf-stage {{ position:relative; flex:1; min-height:0; }}
.lf-svg {{ width:100%; height:100%; display:block; }}
.lf-arrow {{ cursor:pointer; outline:none; }}
.lf-arrow:hover .lf-line, .lf-arrow:focus .lf-line, .lf-arrow.lf-open .lf-line {{ stroke:{palette["accent"]}; stroke-width:2.4; }}
.lf-arrow:hover .lf-chip, .lf-arrow:focus .lf-chip, .lf-arrow.lf-open .lf-chip {{ stroke:{palette["accent"]}; }}
.lf-arrow.lf-done .lf-line, .lf-piece.lf-done .lf-tile {{ stroke:{ANSWER_COLOR}; }}
.lf-arrow.lf-failed .lf-line, .lf-piece.lf-failed .lf-tile {{ stroke:{architecture.STATE_COLORS["failed"]}; stroke-width:2.4; }}
.lf-arrow.lf-active .lf-line {{ stroke:{REQUEST_COLOR}; stroke-width:2.4; }}
.lf-piece.lf-working .lf-tile, .lf-group.lf-working rect {{ stroke:{WORKING_COLOR}; stroke-width:2.6;
  filter:drop-shadow(0 0 10px {WORKING_COLOR}); animation:lf-pulse 1.1s ease-in-out infinite; transform-box:fill-box;
  transform-origin:center; }}
.lf-message {{ pointer-events:none; }}
@keyframes lf-pulse {{ 50% {{ transform:scale(1.08); opacity:.75; }} }}
@keyframes lf-blink {{ 50% {{ opacity:.25; }} }}
.lf-card {{ position:absolute; left:12px; bottom:12px; width:min(420px, 92%); background:{palette["card"]};
  border:1px solid {palette["card_border"]}; border-radius:12px; padding:12px 14px; box-shadow:0 10px 30px rgba(0,0,0,.35); display:none; }}
.lf-card.lf-show {{ display:block; }}
.lf-card h3 {{ margin:0 26px 6px 0; font-size:15px; }}
.lf-card dl {{ margin:0; display:grid; grid-template-columns:auto 1fr; gap:4px 10px; font-size:12.5px; }}
.lf-card dt {{ color:{palette["text"]}; font-weight:600; }}
.lf-card dd {{ margin:0; }}
.lf-card .lf-deduced {{ margin:8px 0 0; font-size:12px; color:{charts.STATUS_COLORS["warning"]}; }}
.lf-card .lf-x {{ position:absolute; top:8px; right:10px; border:0; background:none; color:{palette["text"]}; font-size:18px; cursor:pointer; }}
@media (prefers-reduced-motion: reduce) {{ .lf-piece.lf-working .lf-tile, .lf-live .lf-bar .lf-dot {{ animation:none; }} }}
"""


# The animation, as the author asked: a piece that works alone lights up and pulses; a communication is a message
# that travels from whoever asks to whoever answers, and the answer comes back along the same path.
SCRIPT = r"""
(function () {
  const data = JSON.parse(document.getElementById('lf-data').textContent);
  const svg = document.querySelector('.lf-svg');
  const card = document.querySelector('.lf-card');
  const pauseButton = document.getElementById('lf-pause');
  const replayButton = document.getElementById('lf-replay');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ns = 'http://www.w3.org/2000/svg';
  let paused = false, timer = null, frames = [];
  const node = (id) => document.getElementById('arrow-' + id) || document.getElementById('piece-' + id);
  function clearMarks() {
    document.querySelectorAll('.lf-done, .lf-failed, .lf-working, .lf-active').forEach((el) =>
      el.classList.remove('lf-done', 'lf-failed', 'lf-working', 'lf-active'));
    document.querySelectorAll('.lf-message').forEach((dot) => dot.remove());
    frames.forEach((frame) => cancelAnimationFrame(frame)); frames = [];
  }
  function mark(step, kind) {
    step.elements.forEach((id) => { const el = node(id); if (el) el.classList.add(kind); });
  }
  function travel(path, color, reverse, done) {
    const length = path.getTotalLength();
    const dot = document.createElementNS(ns, 'circle');
    dot.setAttribute('r', '6'); dot.setAttribute('fill', color); dot.setAttribute('class', 'lf-message');
    svg.appendChild(dot);
    const duration = Math.max(700, Math.min(1400, length * 4));
    let start = null;
    function frame(time) {
      if (paused) { start = null; frames.push(requestAnimationFrame(frame)); return; }
      if (start === null) start = time - (dot.progress || 0) * duration;
      const progress = Math.min(1, (time - start) / duration);
      dot.progress = progress;
      const point = path.getPointAtLength((reverse ? 1 - progress : progress) * length);
      dot.setAttribute('cx', point.x); dot.setAttribute('cy', point.y);
      if (progress < 1) frames.push(requestAnimationFrame(frame)); else { dot.remove(); if (done) done(); }
    }
    frames.push(requestAnimationFrame(frame));
  }
  function play(step, onEnd) {
    mark(step, 'lf-working');
    const arrows = step.elements.filter((id) => document.getElementById('arrow-' + id));
    arrows.forEach((id) => document.getElementById('arrow-' + id).classList.add('lf-active'));
    if (reduced || !arrows.length) { timer = setTimeout(onEnd, 1500); return; }
    let left = arrows.length;
    arrows.forEach((id) => {
      const path = document.querySelector('#arrow-' + id + ' .lf-line');
      travel(path, data.request, false, () => travel(path, data.answer, true, () => { if (--left === 0) onEnd(); }));
    });
  }
  function live() {
    clearMarks();
    const index = data.timeline.findIndex((step) => step.state === 'in_progress');
    data.timeline.forEach((step, position) => {
      if (step.state === 'ok' && (index < 0 || position < index)) mark(step, 'lf-done');
      if (step.state === 'failed') mark(step, 'lf-failed');
    });
    if (index < 0) return;
    const loop = () => { if (!paused) play(data.timeline[index], () => { document.querySelectorAll('.lf-message').forEach((d) => d.remove()); loop(); }); else timer = setTimeout(loop, 300); };
    loop();
  }
  function replay() {
    clearMarks(); clearTimeout(timer);
    let position = 0;
    const next = () => {
      if (position > 0) { const before = data.timeline[position - 1]; before.elements.forEach((id) => { const el = node(id); if (el) { el.classList.remove('lf-working', 'lf-active'); el.classList.add(before.state === 'failed' ? 'lf-failed' : 'lf-done'); } }); }
      if (position >= data.timeline.length) return;
      const step = data.timeline[position++];
      document.getElementById('lf-step').textContent = step.name;
      if (paused) { position--; timer = setTimeout(next, 300); return; }
      play(step, next);
    };
    next();
  }
  pauseButton.addEventListener('click', () => {
    paused = !paused;
    pauseButton.textContent = paused ? '▶ ' + data.labels.resume : '⏸ ' + data.labels.pause;
    document.querySelectorAll('.lf-working .lf-tile').forEach((tile) => tile.style.animationPlayState = paused ? 'paused' : 'running');
  });
  if (replayButton) replayButton.addEventListener('click', () => { paused = false; pauseButton.textContent = '⏸ ' + data.labels.pause; replay(); });
  function open(id) {
    const text = data.arrows[id];
    document.querySelectorAll('.lf-open').forEach((el) => el.classList.remove('lf-open'));
    document.getElementById('arrow-' + id).classList.add('lf-open');
    card.querySelector('h3').textContent = text.title;
    const list = card.querySelector('dl'); list.replaceChildren();
    const rows = [['ask', text.ask], ['answer', text.answer], ['when', text.when], ['why', text.why]];
    if (data.facts[id]) rows.push(['last', data.facts[id]]);
    rows.forEach(([key, value]) => {
      const term = document.createElement('dt'); term.textContent = data.labels[key];
      const value_ = document.createElement('dd'); value_.textContent = value;
      list.append(term, value_);
    });
    card.querySelector('.lf-deduced').textContent = text.deduced ? data.labels.deduced : '';
    card.classList.add('lf-show');
  }
  document.querySelectorAll('.lf-arrow').forEach((arrow) => {
    arrow.addEventListener('click', () => open(arrow.dataset.id));
    arrow.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(arrow.dataset.id); } });
  });
  card.querySelector('.lf-x').addEventListener('click', () => { card.classList.remove('lf-show'); document.querySelectorAll('.lf-open').forEach((el) => el.classList.remove('lf-open')); });
  if (data.mode === 'live') live();
})();
"""


def build_html(palette: dict[str, str], model: dict[str, Any], focus: bool = False) -> str:
    """The live view: a status line with «Pausar» (and, with no run in progress, «Repetir la última ejecución»), the
    diagram, and the card that opens on an arrow. The data travels as JSON; the script builds every text with
    textContent."""
    labels = {key: t(value) for key, value in LABELS.items()}
    data = {
        "mode": model["mode"],
        "timeline": model["timeline"],
        "facts": model["facts"],
        "arrows": arrow_texts(),
        "labels": labels,
        "request": REQUEST_COLOR,
        "answer": ANSWER_COLOR,
    }
    replay = (
        f'<button id="lf-replay" type="button">▶ {esc(labels["replay"])}</button>'
        if model["mode"] == "still" and model["timeline"]
        else ""
    )
    run_link = (
        f'<a href="{esc(model["run_url"])}" target="_blank" rel="noopener noreferrer">{esc(labels["open"])} ↗</a>'
        if model.get("run_url") and not focus
        else ""
    )
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return (
        '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<style>{build_css(palette)}</style></head>"
        f'<body><div class="lf lf-{model["mode"]}">'
        f'<div class="lf-bar"><span class="lf-dot"></span><b>{esc(model["status"])}</b>'
        f'<span id="lf-step"></span>{replay}<button id="lf-pause" type="button">⏸ {esc(labels["pause"])}</button>'
        f'{run_link}<span class="lf-hint">{esc(labels["hint"])}</span></div>'
        f'<div class="lf-stage">{build_svg(palette, focus)}'
        f'<div class="lf-card" role="dialog"><button class="lf-x" type="button" aria-label="{esc(labels["close"])}">×</button>'
        f'<h3></h3><dl></dl><p class="lf-deduced"></p></div></div></div>'
        f'<script type="application/json" id="lf-data">{payload}</script>'
        f"<script>{SCRIPT}</script></body></html>"
    )


def build_static_html(palette: dict[str, str], caption: str) -> str:
    """The fixed picture for the SAD (D-412): the same diagram with no script and no state, and the date of the latest
    real load under it."""
    return (
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        f"html, body {{ margin:0; background:transparent; color:{palette['text']}; "
        "font:13px/1.4 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }"
        ".lf-svg { width:100%; height:auto; display:block; } p { margin:4px 0 0; text-align:center; }"
        f"</style></head><body>{build_svg(palette)}<p>{esc(caption)}</p></body></html>"
    )


# endregion
