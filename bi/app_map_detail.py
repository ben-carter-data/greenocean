"""«Mapa de la app», the detail behind each piece (D-441): who owns it, how often it moves, its card and its inside.

Everything the system already records is read here, never written by hand: the dbt models and tests (dbt_node,
dbt_result), the loads (etl_run), the served tables and their rows, the manifest of downloads, the list of sources
(agent/input.csv), the expected headers of each source, the steps of the three workflows, the requirements with their
caps, the quality indicators (metas.json), the pointer of the published database and the security cases of the test
plan. Only the «why» of each piece is written by hand, with the decision that records it (docs/DECISIONES.md or
docs/arquitectura/ADR.md); a test checks that every decision named here exists. Pure functions: no Streamlit.
"""

import csv
import html
import json
import re
from pathlib import Path

from bi import devops, quality_metrics

ROOT = Path(__file__).resolve().parent.parent
NOT_VERIFIED = "no verificado aquí"

# Who owns each piece (D-441): drawn as boxes, solid for what the project wrote, dotted for what it does not control.
OWNERS = {
    "fuente": "Fuentes externas",
    "proyecto": "Proyecto GreenOcean",
    "plataforma": "Plataformas externas",
    "persona": "Personas",
    "fuera": "Fuera del sistema",
}
# How often a piece moves, and the piece that sets each rhythm (its button sits next to it).
RHYTHMS = [
    ("week", "Cada martes"),
    ("month", "Cada mes"),
    ("push", "Cada push"),
    ("manual", "Manual"),
    ("always", "Al abrir el panel"),  # D-473: nothing runs all the time; the panel works when opened
]
RHYTHM_OWNER = {"week": "semanal", "month": "ine", "push": "pruebas", "manual": "author", "always": "streamlit"}


def esc(value):
    return html.escape(str(value), quote=True)


def number(value):
    """A figure written the Spanish way (821.072): the English layer rewrites the figures of the texts it translates, so
    a figure already in English would be turned around (5,000 → 5.000)."""
    return quality_metrics.number(value, 0) if isinstance(value, int) else str(value)


# region Reading what the system records
def parse_workflow(text):
    """{triggers, cron, timeout, jobs: [(job, [step label, ...])]} of a workflow file, read line by line."""
    jobs, triggers, cron, timeout = [], [], None, None
    in_on = in_jobs = False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^on:\s*$", line):
            in_on, in_jobs = True, False
            continue
        if re.match(r"^jobs:\s*$", line):
            in_on, in_jobs = False, True
            continue
        if re.match(r"^\S", line):
            in_on = in_jobs = False
            continue
        if in_on and re.match(r"^  [a-z_]+:", line):
            triggers.append(line.strip().rstrip(":").split(":")[0])
        found = re.search(r'cron:\s*"([^"]+)"', line)
        if found:
            cron = found.group(1)
        if in_jobs and re.match(r"^  [\w-]+:\s*$", line):
            jobs.append((line.strip().rstrip(":"), []))
            continue
        found = re.match(r"^    timeout-minutes:\s*(\d+)", line)
        if found and timeout is None:
            timeout = int(found.group(1))
        step = re.match(r"^      - (name|uses|run):\s*(.+)$", line)
        if in_jobs and step and jobs:
            jobs[-1][1].append(step.group(2).strip().strip('"'))
    return {"triggers": triggers, "cron": cron, "timeout": timeout, "jobs": jobs}


def read_requirements(root=ROOT):
    """[(package, versions)] of both requirement files, comments left out."""
    found = []
    for name in ("requirements.txt", "requirements-pipeline.txt"):
        for line in (root / name).read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line and not line.startswith("-r"):
                package = re.split(r"[<>=!~ ]", line)[0]
                found.append((package, line[len(package) :]))
    return found


def read_security_cases(root=ROOT):
    """[(S-xx, name)] from the table of the test and security plan."""
    text = (root / "docs" / "calidad" / "PLAN_PRUEBAS.md").read_text(encoding="utf-8")
    return re.findall(r"^\| (S-\d+) \| ([^|]+?) \|", text, re.MULTILINE)


def read_documents(root=ROOT):
    """[(document, version)] of the nine documents of the folder, read from their header."""
    paths = [
        "negocio/PRD.md",
        "negocio/ACTA_DE_CIERRE.md",
        "arquitectura/SAD.md",
        "arquitectura/ADR.md",
        "arquitectura/INDICE_DECISIONES.md",
        "calidad/PLAN_DE_CALIDAD.md",
        "calidad/PLAN_PRUEBAS.md",
        "operacion/MANUAL.md",
        "negocio/GLOSARIO.md",
    ]
    found = []
    for path in paths:
        text = (root / "docs" / path).read_text(encoding="utf-8")
        version = re.search(r"^\| Versión \| ([^|]+?) \|", text, re.MULTILINE)
        found.append((Path(path).stem, version.group(1) if version else "—"))
    return found


def read_data_files(root=ROOT):
    """How many test files guard the data (tests/conftest.py, D-366)."""
    text = (root / "tests" / "conftest.py").read_text(encoding="utf-8")
    block = text.split("DATA_FILES = {", 1)[1].split("}", 1)[0]
    return len(re.findall(r'"test_\w+"', block))


def read_database(database_file):
    """What the DuckDB database records about itself; None when it is not there."""
    if not database_file or not Path(database_file).exists():
        return None
    import duckdb

    connection = duckdb.connect(str(database_file), read_only=True)
    try:
        tables = [row[0] for row in connection.execute("SHOW TABLES").fetchall()]
        rows = {table: connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0] for table in tables}
        nodes = connection.execute(
            "SELECT unique_id, name, resource_type, layer, depends_on, test_type FROM dbt_node ORDER BY name"
        ).fetchall()
        results = dict(connection.execute("SELECT status, count(*) FROM dbt_result GROUP BY 1").fetchall())
        built = connection.execute("SELECT max(generated_at) FROM dbt_result").fetchone()[0]
        last = connection.execute(
            "SELECT started_at, status, rows_read, rows_loaded, rows_rejected FROM etl_run ORDER BY run_id DESC LIMIT 1"
        ).fetchone()
        weeks = connection.execute("SELECT min(week_start), max(week_start) FROM dim_date").fetchone()
    finally:
        connection.close()
    return {"rows": rows, "nodes": nodes, "results": results, "built": built, "last_run": last, "weeks": weeks}


def read_facts(database_file=None, root=ROOT, menu=None, runs_tabs=None):
    """Every figure of the cards and the insides, from what the system records. «menu» and «runs_tabs» come from the
    panel itself (its sections and the tabs of the Operations center), so the map never repeats them by hand."""
    from agent import agent
    from bi import project
    from etl import etl, ine

    with open(root / "agent" / "input.csv", encoding="utf-8") as handle:
        inputs = list(csv.DictReader(handle))
    pointer_file = root / "etl" / "datos.version"
    goals = quality_metrics.read(root / "docs" / "calidad" / "metas.json")
    plan = quality_metrics.read(root / "docs" / "calidad" / "plan_mitigacion.json")
    queries_text = (root / "bi" / "queries.sql").read_text(encoding="utf-8")
    return {
        "database": read_database(database_file),
        "inputs": inputs,
        "headers": {source: len(columns) for source, columns in agent.EXPECTED_HEADERS.items()},
        "manifest": json.loads((root / "agent" / "downloads" / "manifest.json").read_text(encoding="utf-8")),
        "pointer": json.loads(pointer_file.read_text(encoding="utf-8")) if pointer_file.exists() else None,
        "workflows": {
            path.name: parse_workflow(path.read_text(encoding="utf-8"))
            for path in sorted((root / ".github" / "workflows").glob("*.yml"))
        },
        "requirements": read_requirements(root),
        "goals": {key: value for key, value in goals.items() if isinstance(value, dict)},
        "failures": len(plan.get("fallas", [])),
        "tests": project.count_test_functions(root / "tests"),
        "data_files": read_data_files(root),
        "security": read_security_cases(root),
        "documents": read_documents(root),
        "queries": len(re.findall(r"^-- name: ", queries_text, re.MULTILINE)),
        "caches": sum(
            len(re.findall(r"^@st\.cache_(?:data|resource)", path.read_text(encoding="utf-8"), re.MULTILINE))
            for path in (root / "bi").glob("*.py")
        ),
        "ine_files": len(ine.INE_FILES),
        "rows_ratio": int(etl.MINIMUM_ROWS_RATIO * 100),
        "late_weeks": etl.MAX_LATE_WEEKS,
        "menu": menu or [],
        "runs_tabs": runs_tabs or [],
    }


def read_decision(reference, root=ROOT, english=False):
    """The title of a decision as its file writes it: D-xxx from docs/DECISIONES.md (only in Spanish), ADR-xx from the
    ADR in the visit's language."""
    if reference.startswith("ADR-"):
        folder = root / "docs" / "en" if english else root / "docs"
        text = (folder / "arquitectura" / "ADR.md").read_text(encoding="utf-8")
    elif english:
        # DECISIONES.md is only in Spanish (D-338): in English, the row of the decision index that cites it, if any.
        text = (root / "docs" / "en" / "arquitectura" / "INDICE_DECISIONES.md").read_text(encoding="utf-8")
        for line in text.splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if line.startswith("| ") and len(cells) > 1 and re.search(rf"\b{re.escape(reference)}\b", cells[-1]):
                return cells[0]
        return None
    else:
        text = (root / "docs" / "DECISIONES.md").read_text(encoding="utf-8")
    found = re.search(rf"^## {re.escape(reference)} · (.+)$", text, re.MULTILINE)
    return found.group(1).strip() if found else None


# endregion


# region Small readers used by the cards
def database(facts):
    return (facts or {}).get("database")


def table_rows(facts, table):
    data = database(facts)
    return number(data["rows"][table]) if data and table in data["rows"] else NOT_VERIFIED


def models_by_layer(facts):
    """{layer: [model]} of dbt_node, in the order of the layers and, inside a layer, in the order they are built: a model
    after the models it reads (read from depends_on)."""
    nodes = [node for node in (database(facts) or {}).get("nodes", []) if node[2] == "model"]
    parents = {node[0]: json.loads(node[4] or "[]") for node in nodes}
    depth = {}

    def level(unique_id):
        if unique_id not in depth:
            depth[unique_id] = 1 + max(
                (level(parent) for parent in parents.get(unique_id, []) if parent in parents), default=0
            )
        return depth[unique_id]

    found = {"staging": [], "intermediate": [], "marts": []}
    for unique_id, name, _, layer, *_ in sorted(nodes, key=lambda node: (level(node[0]), node[1])):
        found.setdefault(layer, []).append(name)
    return found


def count_kind(facts, kind):
    data = database(facts)
    return number(sum(1 for node in data["nodes"] if node[2] == kind)) if data else NOT_VERIFIED


def inputs_of(facts, source):
    return [row for row in (facts or {}).get("inputs", []) if row["source"] == source]


def workflow(facts, name):
    return (facts or {}).get("workflows", {}).get(name, {"jobs": [], "triggers": [], "cron": None, "timeout": None})


def steps_of(facts, name):
    return [step for _, steps in workflow(facts, name)["jobs"] for step in steps]


def goals_of(facts, kind):
    return [key for key, goal in (facts or {}).get("goals", {}).items() if goal.get("tipo") == kind]


# endregion


# region The card of each piece of the map
# key: (owner, rhythm, what can fail and what happens then, why it is so, [decisions]). The «what it does» is the node's
# own role in bi/app_map.py, so the hover text and the card never disagree.
CARDS = {
    "odepa": (
        "fuente",
        "week",
        "Si cambia las columnas de un archivo, la ingesta lo rechaza con UNEXPECTED_HEADER y la carga se detiene. Si "
        "lleva más de 2 semanas sin publicar, la carga también se detiene; si solo se atrasa, se publica hasta la "
        "última semana completa.",
        "Solo los archivos oficiales: cualquiera puede bajar el mismo CSV y recalcular cada cifra del panel.",
        ["ADR-01", "D-356"],
    ),
    "odepa_consumer": (
        "fuente",
        "week",
        "Lo mismo que la fuente mayorista: encabezado validado y la regla de las fuentes retrasadas.",
        "Es la fuente que dice qué paga la gente; cruzada con la mayorista, da la brecha entre canales.",
        ["ADR-01", "D-356"],
    ),
    "ine": (
        "fuente",
        "month",
        "Si el INE no responde, la carga usa las filas del IPC que ya están en la Base DuckDB publicada "
        "(ine_ipc_source); sin ninguna de las dos, la carga se detiene.",
        "Sin el IPC solo habría precios nominales; con él, el panel compara cada precio con la inflación.",
        ["ADR-33", "D-155"],
    ),
    "agent": (
        "proyecto",
        "week",
        "Un archivo con otras columnas se rechaza con UNEXPECTED_HEADER. Una falla de red solo afecta al año en curso: "
        "los años cerrados vienen de la caché.",
        "Guardar cada archivo tal como llegó, con su huella, permite rehacer todo sin volver a descargar y demostrar "
        "qué entregó la fuente ese día.",
        ["D-047", "D-164"],
    ),
    "sqlite": (
        "proyecto",
        "week",
        "Si el respaldo no da las mismas cifras que la Base DuckDB, la prueba de paridad falla y no se publica.",
        "Un segundo camino, sin dbt, comprueba que dbt no cambió ninguna cifra. Los datos crudos nunca se suben al "
        "repositorio.",
        ["D-020", "ADR-34"],
    ),
    "parquet": (
        "proyecto",
        "week",
        "Sin bronce, dbt no tiene fuentes y la carga se detiene antes de construir.",
        "Parquet por columnas y por año: dbt lee solo lo que necesita, en un formato abierto.",
        ["ADR-30", "D-154"],
    ),
    "dbt": (
        "proyecto",
        "week",
        "Si falla un modelo o una de sus pruebas, la carga se detiene y la base publicada no cambia.",
        "Las reglas de negocio quedan versionadas y probadas como modelos SQL, no escondidas en un script.",
        ["ADR-30", "ADR-11"],
    ),
    "duckdb": (
        "proyecto",
        "week",
        "Si una carga falla, la base publicada sigue siendo la anterior, con su fecha a la vista.",
        "Un archivo sin servidor: costo cero, nada que mantener encendido y consultas al instante desde el panel.",
        ["ADR-31", "ADR-34"],
    ),
    "release": (
        "proyecto",
        "week",
        "Si el archivo no coincide con la huella del puntero, el panel no lo usa y sigue con la base que tiene.",
        "Una sola copia publicada que cada carga reemplaza: el historial de git no crece con los datos.",
        ["ADR-35", "D-270"],
    ),
    "streamlit": (
        "proyecto",
        "always",
        "Sin base nueva, muestra la última con su fecha. Duerme si no tiene visitas; no verificado cuánto tarda.",
        "Solo lectura por diseño: ningún error de la pantalla puede cambiar un dato.",
        ["ADR-02", "D-283"],
    ),
    "visitor": (
        "persona",
        "always",
        "",
        "Sin cuenta: los datos son públicos y el panel es de solo lectura.",
        ["D-295", "D-382"],
    ),
    "professional": (
        "persona",
        "always",
        "",
        "Sin clave: el rol solo ordena el menú; quien quiera revisar todo el proyecto puede hacerlo.",
        ["D-295", "D-382"],
    ),
    "author": (
        "persona",
        "manual",
        "Es el único que recibe avisos: «Acción requerida» al entrar y «La carga del … falló» arriba del menú.",
        "Una sola clave, comprobada en el servidor antes de cada página y de cada acción.",
        ["D-421", "D-420"],
    ),
    "secrets": (
        "proyecto",
        "always",
        "Sin GITHUB_TOKEN, «Ejecutar pipeline ahora» queda inactivo; sin GITHUB_READ_TOKEN, el panel lee GitHub sin "
        "clave, con 60 consultas por hora.",
        "Dos tokens con alcance distinto: el que solo lee no puede lanzar nada.",
        ["D-397", "D-421"],
    ),
    "devops": (
        "proyecto",
        "manual",
        "Sin ser Autor, cada página dice «No tienes acceso»: el servidor lo comprueba antes de dibujarla.",
        "La operación se ve y se hace desde el mismo panel, sin entrar a GitHub, y solo con la clave.",
        ["D-420", "D-409"],
    ),
    "semanal": (
        "proyecto",
        "week",
        "Si un paso falla, los siguientes no corren y la base publicada no cambia; GitHub manda un correo y el Autor "
        "ve el aviso. No verificado: qué cuenta como actividad para que GitHub no apague el cron tras 60 días.",
        "Todo en GitHub Actions para no mantener un servidor propio; publica solo si pasan las pruebas.",
        ["ADR-02", "ADR-11"],
    ),
    "calidad": (
        "proyecto",
        "week",
        "Un indicador de datos fuera de su aceptable no frena la publicación: queda como no conformidad y aparece en "
        "«Acción requerida».",
        "Lo que bloquea y lo que avisa quedan separados: un dato malo nunca se publica, un aviso nunca deja el panel "
        "sin datos.",
        ["D-431", "D-436"],
    ),
    "pruebas": (
        "proyecto",
        "push",
        "El push queda en rojo en GitHub; los datos publicados no se tocan.",
        "Una falla de pantalla nunca frena la publicación de datos: las pruebas de pantalla corren aquí, no en la carga.",
        ["D-366", "D-323"],
    ),
    "github": (
        "plataforma",
        "always",
        "Sin GitHub no hay carga, ni release, ni estado en vivo; el panel sigue con la última base descargada.",
        "Gratis y sin vencimiento: aloja el código, corre los workflows y publica la base.",
        ["ADR-02", "ADR-35"],
    ),
    "pypi": (
        "plataforma",
        "push",
        "Una versión nueva incompatible rompió dos cargas: certifi y DuckDB. Desde D-435 cada dependencia tiene tope.",
        "Actualizar una dependencia pasa a ser una decisión del autor, no una sorpresa de un martes.",
        ["D-435", "D-227"],
    ),
    "stcloud": (
        "plataforma",
        "always",
        "Duerme la app sin visitas, y el visitante debe despertarla. No verificado: cuánto tarda en dormirla y si toma "
        "un commit nuevo sin «Reboot».",
        "Junto con GitHub, permite que el proyecto corra sin nube de pago.",
        ["ADR-02", "ADR-31"],
    ),
    "ci": (
        "proyecto",
        "push",
        "Una prueba en rojo deja el push en rojo, o detiene la carga si es una prueba de datos.",
        "Cada cifra del panel se recalcula desde la fuente en una prueba.",
        ["D-366", "D-323"],
    ),
    "web": (
        "proyecto",
        "always",
        "Si un script del navegador falla, la página sigue mostrando su HTML: se pierden la animación, el zoom o el texto al pasar el cursor. Las pruebas de pantalla corren en cada push con pruebas.yml.",
        "El panel genera sus propias vistas: nada se descarga de terceros al abrirlo.",
        [],
    ),
    "charts": (
        "proyecto",
        "always",
        "Si el navegador no dibuja un gráfico, el resto de la página se ve igual; sus cifras siguen en la Base DuckDB y en «Consultas SQL».",
        "Gráficos declarativos con el formato de números del idioma.",
        [],
    ),
    "gates": (
        "proyecto",
        "week",
        "Basta un criterio para detener la carga: la base publicada no cambia y el Autor recibe el aviso.",
        "Nunca se publica una cifra que no pasó las pruebas: mejor la semana anterior, fechada, que un dato dudoso.",
        ["ADR-11", "D-356"],
    ),
    "parity": (
        "proyecto",
        "week",
        "Si las dos bases no coinciden, una de las dos implementaciones tiene un error y la carga se detiene.",
        "Dos caminos independientes que coinciden dan más confianza que uno solo bien probado.",
        ["D-154", "ADR-34"],
    ),
    "security": (
        "proyecto",
        "push",
        "Un ataque que pasa deja el push en rojo antes de publicar el cambio.",
        "Cada control se demuestra con una prueba que lo ataca.",
        ["D-421", "D-393"],
    ),
    "monitoring": (
        "proyecto",
        "week",
        "Si una carga falla, la Base DuckDB publicada no cambia y etl_run no la anota: la falla queda en el log de GitHub Actions, en el correo de GitHub y en el aviso «La carga del … falló» del panel.",
        "Cada carga deja su registro, así se sabe qué pasó sin entrar a la máquina.",
        ["D-342"],
    ),
    "docs": (
        "proyecto",
        "push",
        "Si un documento pierde una sección, un diagrama o su par en inglés, sus pruebas fallan y pruebas.yml queda en rojo en ese push.",
        "Cada documento es una página del panel y su PDF es esa página impresa.",
        ["D-279", "D-248"],
    ),
    "measurement": (
        "proyecto",
        "manual",
        "Corre a mano, fuera del CI: si no se corre, un cambio de diseño llega sin medir. Necesita Playwright instalado fuera del proyecto.",
        "Las pantallas se miden en un navegador real, no a ojo.",
        ["D-277"],
    ),
    "ai": (
        "fuera",
        "manual",
        "No es parte del sistema: sin ella, la carga, el panel y las pruebas corren igual.",
        "Apoyo para revisar; nunca corre en la carga ni en el panel.",
        [],
    ),
}


def inside_of(key, facts):
    """«What it has inside»: its real pieces, read from what the system records when it can be."""
    layers = models_by_layer(facts)
    data = database(facts) or {}
    found = {
        "odepa": [f"{row['year']}: {row['url'].rsplit('/', 1)[-1]}" for row in inputs_of(facts, "wholesale")],
        "odepa_consumer": [f"{row['year']}: {row['url'].rsplit('/', 1)[-1]}" for row in inputs_of(facts, "consumer")],
        "agent": ["agent/agent.py", "agent/input.csv", "agent/downloads/manifest.json", "etl/ine.py"],
        "sqlite": ["etl/raw.db", "etl/etl.py", "etl/datos.db"],
        "parquet": ["etl/bronze.py", "etl/bronze/odepa_wholesale", "etl/bronze/odepa_consumer", "etl/bronze/ine_ipc"],
        "dbt": [f"{layer} · {len(names)}" for layer, names in layers.items() if names],
        "duckdb": [f"{table} · {number(rows)}" for table, rows in data.get("rows", {}).items()],
        "release": ["etl/datos.duckdb", "etl/datos.version", "bi/served_database.py"],
        "streamlit": [label for label, _ in (facts or {}).get("menu", [])],
        "devops": [
            page for label, pages in (facts or {}).get("menu", []) for page in pages if label == "DevOps y seguridad"
        ],
        "semanal": [STEP_NAMES.get(f"semanal.yml::{step}", (step,))[0] for step in steps_of(facts, "semanal.yml")],
        "calidad": steps_of(facts, "calidad.yml"),
        "pruebas": [f"{job} · {len(steps)}" for job, steps in workflow(facts, "pruebas.yml")["jobs"]],
        "github": ["main", "Actions", "Release «base-actual»", "Issues", "Pull requests", "API"],
        "pypi": [f"{package}{versions}" for package, versions in (facts or {}).get("requirements", [])],
        "stcloud": ["CONTROL_CODE", "GITHUB_TOKEN", "GITHUB_READ_TOKEN", "requirements.txt"],
        "secrets": ["CONTROL_CODE", "GITHUB_TOKEN", "GITHUB_READ_TOKEN"],
        "security": [f"{case} · {name}" for case, name in (facts or {}).get("security", [])],
        "docs": [f"{name} · v{version}" for name, version in (facts or {}).get("documents", [])],
    }
    return found.get(key, [])


def numbers_of(key, facts):
    """«The numbers»: (what, figure, the command that produces it). A figure that cannot be read here says so."""
    data = database(facts)
    last = data["last_run"] if data else None
    pointer = (facts or {}).get("pointer")
    manifest = (facts or {}).get("manifest", {})

    def count(rows):
        return number(len(rows))

    found = {
        "odepa": [
            ("archivos", count(inputs_of(facts, "wholesale")), "grep -c wholesale agent/input.csv"),
            (
                "columnas esperadas",
                number(facts["headers"]["wholesale"]) if facts else NOT_VERIFIED,
                "agent.EXPECTED_HEADERS",
            ),
        ],
        "odepa_consumer": [
            ("archivos", count(inputs_of(facts, "consumer")), "grep -c consumer agent/input.csv"),
            (
                "columnas esperadas",
                number(facts["headers"]["consumer"]) if facts else NOT_VERIFIED,
                "agent.EXPECTED_HEADERS",
            ),
            ("canales", table_rows(facts, "dim_channel"), "SELECT count(*) FROM dim_channel"),
        ],
        "ine": [
            ("archivos", number(facts["ine_files"]) if facts else NOT_VERIFIED, "len(etl.ine.INE_FILES)"),
            ("meses del IPC", table_rows(facts, "ipc_monthly"), "SELECT count(*) FROM ipc_monthly"),
        ],
        "agent": [
            ("direcciones", count((facts or {}).get("inputs", [])), "agent/input.csv"),
            ("archivos con huella", number(len(manifest)), "agent/downloads/manifest.json"),
        ],
        "dbt": [
            ("modelos", count_kind(facts, "model"), "SELECT count(*) FROM dbt_node WHERE resource_type = 'model'"),
            ("pruebas", count_kind(facts, "test"), "SELECT count(*) FROM dbt_node WHERE resource_type = 'test'"),
            (
                "resultado de la última construcción",
                " · ".join(f"{status} {number(n)}" for status, n in sorted(data["results"].items()))
                if data
                else NOT_VERIFIED,
                "SELECT status, count(*) FROM dbt_result GROUP BY 1",
            ),
        ],
        "duckdb": [
            ("tablas", number(len(data["rows"])) if data else NOT_VERIFIED, "SHOW TABLES"),
            ("precios semanales", table_rows(facts, "weekly_price"), "SELECT count(*) FROM weekly_price"),
            ("semanas", table_rows(facts, "dim_date"), "SELECT count(*) FROM dim_date"),
        ],
        "release": [
            ("bytes", number(pointer["bytes"]) if pointer else NOT_VERIFIED, "etl/datos.version"),
            ("publicada", pointer["published_at"] if pointer else NOT_VERIFIED, "etl/datos.version"),
        ],
        "streamlit": [
            ("secciones del menú", count((facts or {}).get("menu", [])), "MENU_BLOCKS"),
            (
                "consultas con nombre",
                number(facts["queries"]) if facts else NOT_VERIFIED,
                "grep -c '^-- name:' bi/queries.sql",
            ),
        ],
        "devops": [("pestañas del Centro de operación", count((facts or {}).get("runs_tabs", [])), "RUNS_VIEWS")],
        "semanal": [
            ("pasos", count(steps_of(facts, "semanal.yml")), ".github/workflows/semanal.yml"),
            ("cron", workflow(facts, "semanal.yml")["cron"] or NOT_VERIFIED, ".github/workflows/semanal.yml"),
            ("minutos como máximo", number(workflow(facts, "semanal.yml")["timeout"] or 0), "timeout-minutes"),
        ],
        "calidad": [
            ("indicadores de código", count(goals_of(facts, "codigo")), "docs/calidad/metas.json"),
            ("indicadores de datos", count(goals_of(facts, "datos")), "docs/calidad/metas.json"),
            ("pasos", count(steps_of(facts, "calidad.yml")), ".github/workflows/calidad.yml"),
        ],
        "pruebas": [
            (
                "funciones de prueba",
                number(facts["tests"]) if facts else NOT_VERIFIED,
                "grep -c '^def test_' tests/test_*.py",
            ),
            (
                "archivos que guardan los datos",
                number(facts["data_files"]) if facts else NOT_VERIFIED,
                "tests/conftest.py",
            ),
        ],
        "ci": [
            (
                "funciones de prueba",
                number(facts["tests"]) if facts else NOT_VERIFIED,
                "grep -c '^def test_' tests/test_*.py",
            )
        ],
        "gates": [
            (
                "filas mínimas frente a la última carga",
                f"{facts['rows_ratio']} %" if facts else NOT_VERIFIED,
                "etl.MINIMUM_ROWS_RATIO",
            ),
            (
                "semanas de atraso que detienen",
                number(facts["late_weeks"]) if facts else NOT_VERIFIED,
                "etl.MAX_LATE_WEEKS",
            ),
        ],
        "pypi": [("dependencias con tope", count((facts or {}).get("requirements", [])), "requirements*.txt")],
        "security": [("casos de seguridad", count((facts or {}).get("security", [])), "docs/calidad/PLAN_PRUEBAS.md")],
        "monitoring": [
            ("cargas registradas", table_rows(facts, "etl_run"), "SELECT count(*) FROM etl_run"),
            (
                "fallas registradas",
                number(facts["failures"]) if facts else NOT_VERIFIED,
                "docs/calidad/plan_mitigacion.json",
            ),
        ],
        "docs": [("documentos", count((facts or {}).get("documents", [])), "docs/")],
    }
    if last:
        found["monitoring"].append(
            (
                "última carga",
                f"{last[0][:16]} · {number(last[2])} / {number(last[3])} / {number(last[4])}",
                "SELECT started_at, rows_read, rows_loaded, rows_rejected FROM etl_run",
            )
        )
    return found.get(key, [])


# endregion


# region The inside of each piece: columns, logos and lines, as in the map
def piece(key, logo, name, sub="", what="", row=None):
    """A piece of an inside; «row» places it beside the piece it comes from, otherwise it stacks in its column."""
    return {"id": key, "logo": logo, "name": name, "sub": sub, "what": what, "row": row}


def inside_source(facts, source, label):
    rows = inputs_of(facts, source)
    years = [row["year"] for row in rows]
    current = max(years) if years else "—"
    columns = facts and facts.get("headers", {}).get(source)
    return {
        "columns": [
            (
                "Publica",
                [
                    piece(
                        "pub",
                        "source:odepa",
                        label,
                        "datos.odepa.gob.cl",
                        "Un CSV por año, en el portal de datos abiertos.",
                    )
                ],
            ),
            (
                "Archivos",
                [
                    piece(
                        "files",
                        "icon:files",
                        f"{len(rows)} CSV",
                        " · ".join(years),
                        "Las direcciones están en agent/input.csv.",
                    ),
                ],
            ),
            (
                "Descarga",
                [
                    piece(
                        "closed",
                        "brand:github",
                        "Años cerrados",
                        "caché de Actions",
                        "No cambian: se recuperan de la caché (D-047).",
                    ),
                    piece(
                        "current",
                        "brand:python",
                        f"Año {current}",
                        "agent/agent.py",
                        "Se descarga cada martes, con su huella SHA-256.",
                    ),
                ],
            ),
            (
                "Validación",
                [
                    piece(
                        "header",
                        "icon:shield",
                        "Encabezado",
                        f"{columns} columnas esperadas" if columns else NOT_VERIFIED,
                        "agent.EXPECTED_HEADERS: el archivo debe traer exactamente esas columnas, en ese orden.",
                    )
                ],
            ),
            (
                "Si cambia el formato",
                [
                    piece(
                        "reject",
                        "icon:stop",
                        "UNEXPECTED_HEADER",
                        "la carga se detiene",
                        "La base publicada no cambia.",
                    ),
                    piece(
                        "incident",
                        "icon:files",
                        "Incidente externo",
                        "incidentes_externos.json",
                        "Se registra con su causa medida.",
                    ),
                ],
            ),
        ],
        "links": [
            ("pub", "files", "", False),
            ("files", "closed", "", False),
            ("files", "current", "", False),
            ("current", "header", "valida", False),
            ("closed", "header", "", True),
            ("header", "reject", "si no coincide", True),
            ("reject", "incident", "registra", True),
        ],
    }


def inside_ine(facts):
    return {
        "columns": [
            ("Publica", [piece("pub", "source:ine", "INE", "www.ine.gob.cl", "El IPC, cada mes.")]),
            (
                "Archivos",
                [
                    piece("base", "icon:files", "Serie base 2023", "CSV", "La serie vigente, base 2023 = 100."),
                    piece(
                        "joined",
                        "icon:files",
                        "Serie empalmada",
                        "desde diciembre de 2009",
                        "Extiende la serie hacia atrás.",
                    ),
                ],
            ),
            (
                "Lectura",
                [
                    piece(
                        "ine",
                        "brand:python",
                        "etl/ine.py",
                        "división 1, alimentos",
                        "Descarga ambos CSV en cada carga.",
                    )
                ],
            ),
            (
                "Bronce",
                [
                    piece(
                        "bronze",
                        "brand:apacheparquet",
                        "ine_ipc",
                        "etl/bronze/ine_ipc",
                        "Las filas tal como se leyeron.",
                    )
                ],
            ),
            (
                "dbt",
                [
                    piece("stg", "brand:dbt", "stg_ine__ipc_monthly", "staging", ""),
                    piece(
                        "monthly",
                        "brand:duckdb",
                        "ipc_monthly",
                        f"{table_rows(facts, 'ipc_monthly')} meses",
                        "Una serie, base 2023 = 100 (D-155).",
                    ),
                    piece(
                        "weekly",
                        "brand:duckdb",
                        "ipc_weekly",
                        f"{table_rows(facts, 'ipc_weekly')} semanas",
                        "El deflactor de cada semana.",
                    ),
                ],
            ),
            (
                "Si el INE falla",
                [
                    piece(
                        "backup",
                        "brand:duckdb",
                        "ine_ipc_source",
                        f"{table_rows(facts, 'ine_ipc_source')} filas",
                        "Las filas del IPC de la base publicada.",
                    )
                ],
            ),
        ],
        "links": [
            ("pub", "base", "", False),
            ("pub", "joined", "", False),
            ("base", "ine", "", False),
            ("joined", "ine", "", False),
            ("ine", "bronze", "", False),
            ("bronze", "stg", "", False),
            ("stg", "monthly", "", False),
            ("monthly", "weekly", "", False),
            ("backup", "bronze", "si el INE no responde", True),
        ],
    }


def inside_agent(facts):
    manifest = (facts or {}).get("manifest", {})
    inputs = (facts or {}).get("inputs", [])
    return {
        "columns": [
            (
                "Lista",
                [
                    piece(
                        "input",
                        "icon:files",
                        "agent/input.csv",
                        f"{len(inputs)} direcciones",
                        "Fuente, año y dirección de cada CSV.",
                    )
                ],
            ),
            (
                "Descarga",
                [
                    piece("cache", "brand:github", "Caché de Actions", "años cerrados", "D-047."),
                    piece(
                        "agent",
                        "brand:python",
                        "agent/agent.py",
                        "año en curso",
                        "requests, con la raíz emSign (D-164).",
                    ),
                    piece("ine", "brand:python", "etl/ine.py", "IPC del INE", "Escribe directo en bronce."),
                ],
            ),
            (
                "Control",
                [piece("header", "icon:shield", "Encabezado", "UNEXPECTED_HEADER", "Columnas exactas por fuente.")],
            ),
            (
                "Registro",
                [
                    piece(
                        "manifest",
                        "icon:key",
                        "manifest.json",
                        f"{len(manifest)} archivos con huella",
                        "SHA-256 de cada archivo.",
                    ),
                    piece("raw", "brand:sqlite", "etl/raw.db", "aterrizaje", "Las filas tal como llegaron."),
                ],
            ),
        ],
        "links": [
            ("input", "cache", "", False),
            ("input", "agent", "", False),
            ("cache", "header", "", True),
            ("agent", "header", "", False),
            ("header", "manifest", "huella", False),
            ("header", "raw", "filas", False),
        ],
    }


def inside_sqlite(facts):
    return {
        "columns": [
            ("Entrada", [piece("csv", "icon:files", "CSV descargados", "agent/downloads/", "")]),
            (
                "Aterrizaje",
                [
                    piece(
                        "raw",
                        "brand:sqlite",
                        "etl/raw.db",
                        "raw_wholesale · raw_consumer",
                        "Copia fiel; no se publica.",
                    )
                ],
            ),
            (
                "Dos caminos",
                [
                    piece("bronze", "brand:apacheparquet", "etl/bronze/", "hacia dbt", "Camino principal."),
                    piece("etl", "brand:python", "etl/etl.py", "pandas, sin dbt", "Las mismas reglas de negocio."),
                ],
            ),
            (
                "Respaldo",
                [
                    piece(
                        "backup",
                        "brand:sqlite",
                        "etl/datos.db",
                        NOT_VERIFIED,
                        "Se rehace en cada carga; no se publica.",
                    )
                ],
            ),
        ],
        "links": [
            ("csv", "raw", "load_raw_files", False),
            ("raw", "bronze", "", False),
            ("raw", "etl", "", False),
            ("etl", "backup", "", False),
        ],
    }


def inside_parquet(facts):
    return {
        "columns": [
            ("Aterrizaje", [piece("raw", "brand:sqlite", "etl/raw.db", "", "")]),
            (
                "Exportación",
                [piece("bronze", "brand:python", "etl/bronze.py", "pyarrow", "Todas las columnas como texto.")],
            ),
            (
                "Bronce",
                [
                    piece("w", "brand:apacheparquet", "odepa_wholesale", "un archivo por año", ""),
                    piece("c", "brand:apacheparquet", "odepa_consumer", "un archivo por año", ""),
                    piece("i", "brand:apacheparquet", "ine_ipc", "un archivo por serie", "Lo escribe etl/ine.py."),
                ],
            ),
            ("dbt", [piece("src", "brand:dbt", "sources.yml", "read_parquet", "dbt lee el bronce, nunca raw.db.")]),
        ],
        "links": [
            ("raw", "bronze", "", False),
            ("bronze", "w", "", False),
            ("bronze", "c", "", False),
            ("w", "src", "", False),
            ("c", "src", "", False),
            ("i", "src", "", False),
        ],
    }


def inside_dbt(facts):
    """The models of dbt_node by layer, joined by their real dependencies; the tests as one piece."""
    data = database(facts)
    if not data:
        return {"columns": [("dbt", [piece("none", "brand:dbt", "dbt", NOT_VERIFIED, "")])], "links": []}
    layers = models_by_layer(facts)
    sources = [node for node in data["nodes"] if node[2] == "source"]
    tests = [node for node in data["nodes"] if node[2] == "test"]
    singular = [node[1] for node in tests if node[5] == "singular"]
    marts = layers.get("marts", [])
    dims = [name for name in marts if name.startswith("dim_")]
    ipc = [name for name in marts if "ipc" in name]
    rest = [name for name in marts if name not in dims + ipc]

    def to_piece(name, sub):
        return piece(name, "brand:dbt", name, sub, "")

    columns = [
        ("Fuentes", [piece(node[0], "brand:apacheparquet", node[1], "bronce", "") for node in sources]),
        ("Staging", [to_piece(name, "vista") for name in layers.get("staging", [])]),
        ("Intermedio", [to_piece(name, "tabla") for name in layers.get("intermediate", [])]),
        ("Marts · dimensiones", [to_piece(name, "tabla") for name in dims]),
        ("Marts · hechos", [to_piece(name, "tabla") for name in rest]),
        ("Marts · IPC", [to_piece(name, "tabla") for name in ipc]),
        (
            "Pruebas",
            [
                piece(
                    "tests", "icon:shield", f"{len(tests)} pruebas", f"{len(singular)} singulares", " · ".join(singular)
                )
            ],
        ),
    ]
    ids = {node[0]: node[1] for node in data["nodes"]}
    shown = {item["id"] for _, items in columns for item in items}
    links = []
    for unique_id, name, kind, _, depends_on, _ in data["nodes"]:
        if kind != "model":
            continue
        for parent in json.loads(depends_on or "[]"):
            source = parent if parent in shown else ids.get(parent)
            if source in shown and name in shown:
                links.append((source, name, "", False))
    return {"columns": columns, "links": links}


def inside_duckdb(facts):
    data = database(facts)
    rows = data["rows"] if data else {}

    def tab(name, sub=""):
        return piece(name, "brand:duckdb", name, f"{number(rows[name])} filas" if name in rows else NOT_VERIFIED, sub)

    return {
        "columns": [
            ("Dimensiones", [tab("dim_product"), tab("dim_region"), tab("dim_channel"), tab("dim_date")]),
            (
                "Hechos",
                [
                    tab("weekly_price", "Un precio por semana, producto, región, canal y unidad."),
                    tab(
                        "weekly_same_package", "El cambio de cada precio contra la semana anterior, en el mismo envase."
                    ),
                ],
            ),
            ("IPC", [tab("ipc_monthly"), tab("ipc_weekly"), tab("ine_ipc_source")]),
            ("Última semana", [tab("latest_by_source", "Las dos últimas semanas de cada fuente (D-365).")]),
            ("Registro de la carga", [tab("etl_run"), tab("rejection"), tab("dbt_node"), tab("dbt_result")]),
            (
                "Quién la lee",
                [
                    piece(
                        "panel",
                        "brand:streamlit",
                        "Panel web",
                        "todas, en solo lectura",
                        "Sin acceso a archivos ni a la red.",
                    )
                ],
            ),
        ],
        "links": [
            (name, "weekly_price", "", False) for name in ("dim_product", "dim_region", "dim_channel", "dim_date")
        ]
        + [("ipc_monthly", "ipc_weekly", "", False)],
    }


def inside_release(facts):
    pointer = (facts or {}).get("pointer") or {}
    return {
        "columns": [
            (
                "Construida",
                [piece("db", "brand:duckdb", "etl/datos.duckdb", f"{number(pointer.get('bytes', 0))} bytes", "")],
            ),
            (
                "Sube",
                [piece("upload", "brand:github", "gh release upload", "--clobber", "Reemplaza el archivo anterior.")],
            ),
            (
                "Release",
                [
                    piece(
                        "rel", "brand:github", "Release «base-actual»", "una sola copia", "Fuera del historial de git."
                    )
                ],
            ),
            (
                "Puntero en main",
                [
                    piece(
                        "ptr",
                        "icon:key",
                        "etl/datos.version",
                        pointer.get("published_at", NOT_VERIFIED),
                        "SHA-256, tamaño y fecha.",
                    )
                ],
            ),
            (
                "Verifica",
                [
                    piece(
                        "served",
                        "brand:python",
                        "bi/served_database.py",
                        "SHA-256",
                        "Solo usa el archivo si la huella coincide.",
                    )
                ],
            ),
            ("Lee", [piece("panel", "brand:streamlit", "Panel web", "solo lectura", "")]),
        ],
        "links": [
            ("db", "upload", "", False),
            ("upload", "rel", "", False),
            ("rel", "ptr", "commit", True),
            ("ptr", "served", "huella", True),
            ("rel", "served", "descarga", False),
            ("served", "panel", "", False),
        ],
    }


def inside_panel(facts):
    menu = (facts or {}).get("menu", [])

    def pages(count):
        return f"{count} página" if count == 1 else f"{count} páginas"

    sections = [
        piece(f"s{index}", "icon:files", label, pages(len(items)), " · ".join(items))
        for index, (label, items) in enumerate(menu)
    ]
    queries = number(facts["queries"]) if facts else NOT_VERIFIED
    devops = next((item["id"] for item in sections if item["name"] == "DevOps y seguridad"), None)
    return {
        "columns": [
            ("Entrada", [piece("ask", "icon:key", "«Elige tu vista»", "RF-09", "Una vez por pestaña (D-430).")]),
            ("Secciones", sections or [piece("none", "icon:files", NOT_VERIFIED)]),
            (
                "Datos",
                [
                    piece(
                        "db", "brand:duckdb", "Base DuckDB", "todas la leen en solo lectura", "bi/served_database.py."
                    ),
                    piece("q", "icon:code", "bi/queries.sql", f"{queries} consultas con nombre", ""),
                ],
            ),
            ("Fuera", [piece("api", "brand:github", "API de GitHub", "GITHUB_READ_TOKEN", "Estado en vivo.")]),
        ],
        "links": [("ask", item["id"], "", False) for item in sections]
        + [("db", "q", "", False)]
        + ([("api", devops, "estado", True)] if devops else []),
    }


def inside_devops(facts):
    tabs = (facts or {}).get("runs_tabs", [])
    return {
        "columns": [
            (
                "Entrada",
                [
                    piece(
                        "key",
                        "icon:key",
                        "CONTROL_CODE",
                        "tiempo constante",
                        "Tras 3 fallos, espera creciente (D-393).",
                    )
                ],
            ),
            (
                "Páginas",
                [
                    piece("ops", "icon:pulse", "Centro de operación", "", "", row=1),
                    piece("gha", "brand:github", "GitHub Actions", "", "", row=3),
                    piece("cfg", "icon:files", "Configuración", "", "", row=4),
                ],
            ),
            (
                "Qué hace",
                [
                    piece(
                        "buttons",
                        "icon:play",
                        "«Ejecutar pipeline ahora» · «Cancelar»",
                        "«Recargar datos» · «Cerrar acceso»",
                        "«Ejecutar pipeline ahora» está activo solo con GITHUB_TOKEN; «Cancelar» pide «¿Seguro?».",
                        row=1,
                    ),
                    piece("tabs", "icon:files", "Pestañas", " · ".join(tabs) or NOT_VERIFIED, "", row=2),
                    piece("logs", "brand:github", "Estado y logs", "de cada workflow", "", row=3),
                    piece(
                        "tokens",
                        "icon:key",
                        "Tokens y casos del MANUAL",
                        "vencimientos, última carga, informe",
                        "",
                        row=4,
                    ),
                ],
            ),
            (
                "API de GitHub",
                [
                    piece(
                        "write",
                        "brand:github",
                        "GITHUB_TOKEN",
                        "lanza y cancela",
                        "Solo bi/control.py escribe (S-14).",
                        row=1,
                    ),
                    piece("read", "brand:github", "GITHUB_READ_TOKEN", "solo lee", "D-397.", row=3),
                ],
            ),
        ],
        "links": [
            ("key", "ops", "", False),
            ("key", "gha", "", False),
            ("key", "cfg", "", False),
            ("ops", "buttons", "", False),
            ("ops", "tabs", "", True),
            ("gha", "logs", "", False),
            ("cfg", "tokens", "", False),
            ("buttons", "write", "", False),
            ("logs", "read", "", False),
        ],
    }


def step_logo(step):
    text = step.lower()
    for words, logo in (
        (("pip install",), "brand:python"),
        (("checkout", "issue", "release", "publish", "upload-artifact", "propon"), "brand:github"),
        (("dbt",), "brand:dbt"),
        (("pytest", "test", "medir", "comparar", "verific"), "brand:pytest"),
        (("etl", "sqlite"), "brand:sqlite"),
        (("cache", "closed-year"), "brand:github"),
    ):
        if any(word in text for word in words):
            return logo
    return "brand:python"


# The phases of each workflow, each with the words of its first step: a step goes to the phase it opens or stays in the
# one before. The steps themselves are read from the file.
# The Spanish name of each step of semanal.yml, the same one the DevOps diagram shows: (title, detail, what it does).
STEP_NAMES = {
    step[7]: (step[3].split(" · ")[-1], step[4], step[5])
    for step in devops.STEPS
    if step[7] and "::" in step[7] and step[3][0].isdigit()
}
PHASES = {
    "semanal.yml": [
        ("Preparación", ("tuesday's load", "checkout")),
        ("Lo que ya existe", ("current year",)),
        ("Ingesta", ("download",)),
        ("Construcción", ("etl",)),
        ("Pruebas", ("simulate",)),
        ("Publicación", ("publish the database",)),
    ],
    "calidad.yml": [
        ("Preparación", ("checkout",)),
        ("Medición", ("medir",)),
        ("Comparación", ("comparar",)),
        ("Informe", ("proponer",)),
        ("Resultado", ("fallar",)),
    ],
}


def inside_workflow(facts, name):
    """The steps of a workflow in the order of the file, in columns by phase (or by job), joined one after another."""
    found = workflow(facts, name)
    trigger = " · ".join(found["triggers"]) + (f" · {found['cron']}" if found["cron"] else "")
    columns = [
        (
            "Disparo",
            [piece("on", "icon:clock", trigger or NOT_VERIFIED, f"{found['timeout']} min" if found["timeout"] else "")],
        )
    ]
    phases = PHASES.get(name)
    for job, steps in found["jobs"]:
        for index, step in enumerate(steps):
            title, sub, what = STEP_NAMES.get(f"{name}::{step}", (step, "", ""))
            item = piece(f"{job}-{index}", step_logo(step), title, sub, what)
            opens = next((label for label, words in phases or [] if any(word in step.lower() for word in words)), None)
            if phases is None:
                opens = job if index == 0 else None
            if opens and (len(columns) == 1 or columns[-1][0] != opens):
                columns.append((opens, []))
            columns[-1][1].append(item)
    if phases is None:
        # One column per job: the jobs run side by side, each from the trigger, and its steps one after another.
        links = [
            link
            for _, items in columns[1:]
            for link in [("on", items[0]["id"], "", False)]
            + [(items[index]["id"], items[index + 1]["id"], "", False) for index in range(len(items) - 1)]
        ]
        return {"columns": columns, "links": links}
    snake(columns)
    order = [item["id"] for _, items in columns for item in items]
    links = [(order[index], order[index + 1], "", False) for index in range(len(order) - 1)]
    return {"columns": columns, "links": links}


def snake(columns):
    """Places a chain so each column starts on the row where the one before ended, going down or up: every line between
    two steps then runs straight across or straight down."""
    height = max(len(items) for _, items in columns)
    row = 1
    for _, items in columns:
        down = row + len(items) - 1 <= height
        rows = range(row, row + len(items)) if down else range(row, row - len(items), -1)
        if not down and row - len(items) + 1 < 1:
            rows = range(height - len(items) + 1, height + 1)
        for item, place in zip(items, rows):
            item["row"] = place
        row = list(rows)[-1]


def inside_semanal(facts):
    return inside_workflow(facts, "semanal.yml")


def inside_calidad(facts):
    inside = inside_workflow(facts, "calidad.yml")
    inside["columns"].append(
        (
            "Indicadores",
            [
                piece("code", "icon:shield", f"{len(goals_of(facts, 'codigo'))} de código", "verifica el CI", ""),
                piece("data", "icon:chart", f"{len(goals_of(facts, 'datos'))} de datos", "el informe semanal", ""),
            ],
        )
    )
    return inside


def inside_pruebas(facts):
    return inside_workflow(facts, "pruebas.yml")


def inside_github(facts):
    workflows = list((facts or {}).get("workflows", {}))
    return {
        "columns": [
            (
                "Código",
                [
                    piece(
                        "main",
                        "brand:git",
                        "main",
                        "repositorio público",
                        "Código, documentos y el puntero de la base.",
                    )
                ],
            ),
            ("Actions", [piece(name, "brand:github", name, "", "") for name in workflows]),
            (
                "Lo que guarda",
                [
                    piece("cache", "brand:github", "Caché de Actions", "años cerrados", ""),
                    piece("rel", "brand:github", "Release «base-actual»", "la base publicada", ""),
                ],
            ),
            (
                "Lo que publica",
                [
                    piece("issues", "brand:github", "Issues", "«Informe semanal»", ""),
                    piece("pr", "brand:github", "Pull requests", "«Actualizar medición de calidad»", ""),
                ],
            ),
            (
                "Para el panel",
                [piece("api", "brand:github", "API", "dos tokens", "Caché de 300 s; 120 s en «GitHub Actions».")],
            ),
        ],
        "links": [("main", name, "", False) for name in workflows]
        + [
            ("semanal.yml", "cache", "", True),
            ("semanal.yml", "rel", "", False),
            ("semanal.yml", "issues", "", False),
            ("calidad.yml", "pr", "", False),
            ("rel", "api", "", True),
        ],
    }


def inside_pypi(facts):
    requirements = (facts or {}).get("requirements", [])
    return {
        "columns": [
            ("Índice", [piece("pypi", "icon:box", "PyPI", "pypi.org", "")]),
            (
                "Dependencias",
                [piece(package, "icon:box", package, versions, "") for package, versions in requirements[:5]],
            ),
            ("·", [piece(package, "icon:box", package, versions, "") for package, versions in requirements[5:]]),
            (
                "Controles",
                [
                    piece("caps", "icon:shield", "Tope de versión", "D-435", ""),
                    piece("audit", "icon:shield", "pip-audit", "en cada push", ""),
                ],
            ),
        ],
        "links": [("pypi", package, "", False) for package, _ in requirements[:5]]
        + [("pypi", package, "", True) for package, _ in requirements[5:]],
    }


def inside_stcloud(facts):
    return {
        "columns": [
            ("Origen", [piece("main", "brand:git", "main", "repositorio del proyecto", "")]),
            ("Construye", [piece("req", "icon:box", "requirements.txt", "con topes", "")]),
            ("Corre", [piece("app", "brand:streamlit", "bi/dashboard.py", "Panel web", "")]),
            (
                "Secretos",
                [
                    piece("cc", "icon:key", "CONTROL_CODE", "", ""),
                    piece("gt", "icon:key", "GITHUB_TOKEN", "", ""),
                    piece("gr", "icon:key", "GITHUB_READ_TOKEN", "", ""),
                ],
            ),
            (
                "Visitas",
                [piece("sleep", "icon:clock", "Duerme sin visitas", NOT_VERIFIED, "El plazo no está verificado.")],
            ),
        ],
        "links": [
            ("main", "req", "", False),
            ("req", "app", "", False),
            ("cc", "app", "", True),
            ("gt", "app", "", True),
            ("gr", "app", "", True),
            ("app", "sleep", "", True),
        ],
    }


def inside_secrets(facts):
    return {
        "columns": [
            (
                "Dónde vive",
                [
                    piece(
                        "cloud",
                        "icon:cloud",
                        "Streamlit Community Cloud",
                        "Settings › Secrets",
                        "Nunca en el repositorio (S-06).",
                    )
                ],
            ),
            (
                "Secreto",
                [
                    piece("cc", "icon:key", "CONTROL_CODE", "", ""),
                    piece("gt", "icon:key", "GITHUB_TOKEN", "", ""),
                    piece("gr", "icon:key", "GITHUB_READ_TOKEN", "", ""),
                ],
            ),
            (
                "Quién lo usa",
                [
                    piece("gate", "icon:shield", "hmac.compare_digest", "tiempo constante", "S-04."),
                    piece("ctrl", "brand:python", "bi/control.py", "lanza y cancela", "S-14."),
                    piece("read", "brand:python", "bi/github_actions.py", "solo lee", "D-397."),
                ],
            ),
        ],
        "links": [
            ("cloud", "cc", "", False),
            ("cloud", "gt", "", False),
            ("cloud", "gr", "", False),
            ("cc", "gate", "", False),
            ("gt", "ctrl", "", False),
            ("gr", "read", "", False),
        ],
    }


def inside_gates(facts):
    """The criteria in the order the load checks them: dbt (with the test of the missing weeks), the late sources, the
    rows against the last load, then pytest; if one fails, the load stops."""
    ratio = facts["rows_ratio"] if facts else NOT_VERIFIED
    late = facts["late_weeks"] if facts else NOT_VERIFIED
    files = facts["data_files"] if facts else NOT_VERIFIED
    return {
        "columns": [
            ("Orquesta", [piece("pipe", "brand:python", "etl/pipeline.py", "dbt build y la puerta", "")]),
            (
                "1 · dbt",
                [
                    piece(
                        "dbt",
                        "brand:dbt",
                        "Modelos y pruebas",
                        f"{count_kind(facts, 'test')} pruebas",
                        "Una falla basta.",
                    ),
                    piece(
                        "gaps",
                        "icon:clock",
                        "Semanas sin huecos",
                        "d042_no_unexpected_missing_week",
                        "Una prueba de dbt (D-095).",
                    ),
                ],
            ),
            (
                "2 · Fuentes",
                [
                    piece(
                        "late",
                        "source:odepa",
                        "Atraso de una fuente",
                        f"más de {late} semanas detiene",
                        "etl.MAX_LATE_WEEKS · D-356.",
                    )
                ],
            ),
            (
                "3 · Filas",
                [
                    piece(
                        "rows",
                        "icon:chart",
                        "Filas leídas",
                        f"≥ {ratio} % de la última carga",
                        "etl.MINIMUM_ROWS_RATIO · RN-14.",
                    )
                ],
            ),
            (
                "4 · pytest",
                [
                    piece(
                        "pytest", "brand:pytest", "Pruebas de datos", f"{files} archivos", "«pytest -m datos» · D-366."
                    )
                ],
            ),
            (
                "Resultado",
                [
                    piece(
                        "ok", "brand:duckdb", "Publica", "los cuatro pasan", "Se escribe la base y la carga en etl_run."
                    ),
                    piece(
                        "stop",
                        "icon:stop",
                        "Detiene",
                        "si uno falla",
                        "La base publicada no cambia y el Autor recibe el aviso.",
                    ),
                ],
            ),
        ],
        "links": [
            ("pipe", "dbt", "", False),
            ("dbt", "gaps", "", False),
            ("dbt", "late", "", False),
            ("late", "rows", "", False),
            ("rows", "pytest", "", False),
            ("pytest", "ok", "", False),
            ("pytest", "stop", "si uno falla", True),
        ],
    }


def inside_parity(facts):
    return {
        "columns": [
            ("Mismos CSV", [piece("csv", "icon:files", "Archivos descargados", "agent/downloads/", "")]),
            (
                "Dos caminos",
                [
                    piece("dbt", "brand:dbt", "dbt", "bronce → marts", "Camino principal."),
                    piece(
                        "etl",
                        "brand:python",
                        "etl/etl.py",
                        "pandas, sin dbt",
                        "Otra implementación de las mismas reglas.",
                    ),
                ],
            ),
            (
                "Dos bases",
                [
                    piece("duck", "brand:duckdb", "etl/datos.duckdb", "Base DuckDB", ""),
                    piece("sqlite", "brand:sqlite", "etl/datos.db", "respaldo", "No se publica."),
                ],
            ),
            ("Compara", [piece("test", "brand:pytest", "test_migration_parity.py", "cifra por cifra", "")]),
            (
                "Resultado",
                [
                    piece("ok", "brand:github", "Publica", "si coinciden", ""),
                    piece("stop", "icon:stop", "Detiene", "si difieren", ""),
                ],
            ),
        ],
        "links": [
            ("csv", "dbt", "", False),
            ("csv", "etl", "", False),
            ("dbt", "duck", "", False),
            ("etl", "sqlite", "", False),
            ("duck", "test", "", False),
            ("sqlite", "test", "", False),
            ("test", "ok", "", False),
            ("test", "stop", "", True),
        ],
    }


def inside_ci(facts):
    tests = facts["tests"] if facts else NOT_VERIFIED
    return {
        "columns": [
            ("Pruebas", [piece("all", "brand:pytest", f"{tests} funciones", "tests/", "")]),
            (
                "Dónde corren",
                [
                    piece("push", "brand:github", "pruebas.yml", "todas, en cada push", ""),
                    piece("week", "brand:github", "semanal.yml", "«pytest -m datos»", "D-366."),
                ],
            ),
            (
                "Qué protegen",
                [
                    piece(
                        "data",
                        "brand:duckdb",
                        "Las cifras",
                        f"{facts['data_files'] if facts else NOT_VERIFIED} archivos de datos",
                        "",
                    ),
                    piece("screen", "icon:code", "Las pantallas", "solo en el CI", ""),
                ],
            ),
        ],
        "links": [
            ("all", "push", "", False),
            ("all", "week", "", False),
            ("push", "screen", "", False),
            ("week", "data", "", False),
        ],
    }


def inside_security(facts):
    cases = dict((facts or {}).get("security", []))
    groups = [
        ("Identidad y acceso", ["S-04", "S-05", "S-10", "S-11", "S-12"], "icon:key"),
        ("Secretos", ["S-06", "S-07", "S-13"], "icon:shield"),
        ("Mínimo privilegio", ["S-08", "S-14"], "icon:shield"),
        ("Consultas SQL", ["S-01", "S-02", "S-03"], "icon:code"),
        ("Evidencia", ["S-09"], "icon:files"),
    ]
    return {
        "columns": [
            (
                "Controles",
                [
                    piece(f"g{index}", logo, label, " · ".join(ids), " · ".join(cases.get(case, case) for case in ids))
                    for index, (label, ids, logo) in enumerate(groups)
                ],
            ),
            ("Prueba", [piece("tests", "brand:pytest", "tests/test_security.py", "en cada push", "")]),
        ],
        "links": [(f"g{index}", "tests", "", True) for index in range(len(groups))],
    }


def inside_monitoring(facts):
    return {
        "columns": [
            (
                "Señal",
                [
                    piece("run", "brand:duckdb", "etl_run", f"{table_rows(facts, 'etl_run')} cargas", ""),
                    piece("dbt", "brand:duckdb", "dbt_result", "", ""),
                    piece("log", "brand:github", "Log de cada paso", "GitHub Actions", ""),
                ],
            ),
            (
                "Aviso",
                [
                    piece("mail", "icon:files", "Correo «Run failed»", "GitHub", ""),
                    piece("alert", "icon:pulse", "«Acción requerida»", "solo al Autor", ""),
                    piece("fail", "icon:stop", "«La carga del … falló»", "arriba del menú", ""),
                ],
            ),
            (
                "Registro",
                [
                    piece(
                        "plan",
                        "icon:files",
                        "plan_mitigacion.json",
                        f"{facts['failures'] if facts else NOT_VERIFIED} fallas",
                        "",
                    )
                ],
            ),
        ],
        "links": [
            ("run", "alert", "", True),
            ("log", "mail", "", False),
            ("run", "fail", "", False),
            ("alert", "plan", "", True),
        ],
    }


def inside_docs(facts):
    documents = (facts or {}).get("documents", [])
    return {
        "columns": [
            ("Documentos", [piece(name, "icon:files", name, f"v{version}", "") for name, version in documents[:4]]),
            ("·", [piece(name, "icon:files", name, f"v{version}", "") for name, version in documents[4:]]),
            (
                "En el panel",
                [
                    piece("page", "brand:streamlit", "Una página", "«Imprimir o guardar como PDF»", "D-248."),
                    piece("en", "icon:files", "docs/en/", "la misma estructura", "D-283."),
                ],
            ),
        ],
        "links": [(name, "page", "", True) for name, _ in documents],
    }


INSIDES = {
    "odepa": lambda facts: inside_source(facts, "wholesale", "ODEPA mayorista"),
    "odepa_consumer": lambda facts: inside_source(facts, "consumer", "ODEPA consumidor"),
    "ine": inside_ine,
    "agent": inside_agent,
    "sqlite": inside_sqlite,
    "parquet": inside_parquet,
    "dbt": inside_dbt,
    "duckdb": inside_duckdb,
    "release": inside_release,
    "streamlit": inside_panel,
    "devops": inside_devops,
    "semanal": inside_semanal,
    "calidad": inside_calidad,
    "pruebas": inside_pruebas,
    "github": inside_github,
    "pypi": inside_pypi,
    "stcloud": inside_stcloud,
    "secrets": inside_secrets,
    "gates": inside_gates,
    "parity": inside_parity,
    "ci": inside_ci,
    "security": inside_security,
    "monitoring": inside_monitoring,
    "docs": inside_docs,
}
# endregion


# region How each tool works (D-441): the magnifier of a tool shows the tool itself, as GreenOcean uses it
def engine(*stages):
    """A tool drawn as a chain: one column per stage, its main piece on the first row joined to the next one; a piece
    under it is joined to it by a dashed line, without a label that would cover the piece above. stages: (header,
    piece, label of the line to the next stage, [pieces under it])."""
    columns, links = [], []
    for index, (header, main, label, under) in enumerate(stages):
        main["row"] = 1
        for place, extra in enumerate(under, start=2):
            extra["row"] = place
            links.append((extra["id"], main["id"], "", True))
        columns.append((header, [main, *under]))
        if index + 1 < len(stages):
            links.append((main["id"], stages[index + 1][1]["id"], label, False))
    return {"columns": columns, "links": links}


def engine_duckdb(facts):
    from bi import sql_explorer

    data = database(facts)
    pointer = (facts or {}).get("pointer")
    tables = f"{number(len(data['rows']))} tablas" if data else NOT_VERIFIED
    size = f"{number(pointer['bytes'])} bytes" if pointer else NOT_VERIFIED
    limits = f"{number(sql_explorer.ROW_LIMIT)} filas · {sql_explorer.TIMEOUT_SECONDS} s · {sql_explorer.MEMORY_LIMIT}"
    return engine(
        (
            "Quién la abre",
            piece(
                "host",
                "brand:python",
                "Proceso anfitrión",
                "sin servidor",
                "DuckDB no es un servidor: corre dentro del programa que lo llama, aquí Streamlit y la carga semanal. No "
                "hay puerto ni red de por medio.",
            ),
            "consulta",
            [
                piece(
                    "console",
                    "icon:console",
                    "«Consultas SQL»",
                    limits,
                    "Cada consulta del Profesional corre con un límite de filas, de tiempo y de memoria, sin acceso a "
                    "archivos ni a la red, y con la configuración bloqueada.",
                )
            ],
        ),
        (
            "Plan",
            piece(
                "plan",
                "icon:code",
                "Analizador y optimizador",
                "SQL → plan",
                "Lee la consulta y arma un plan: aplica los filtros lo antes posible y pide solo las columnas que usa.",
            ),
            "plan",
            [],
        ),
        (
            "Ejecución",
            piece(
                "vector",
                "icon:play",
                "Ejecución vectorizada",
                "lotes de 2.048 valores",
                "Procesa cada columna en lotes de 2.048 valores, no fila por fila: así agrega cientos de miles de filas "
                "sin índices.",
            ),
            "lee solo sus columnas",
            [],
        ),
        (
            "Almacenamiento",
            piece(
                "columns",
                "icon:files",
                "Almacenamiento columnar",
                "comprimido por columna",
                "Cada columna se guarda aparte y comprimida, en grupos de filas: las columnas repetitivas, como región o "
                "canal, ocupan muy poco.",
            ),
            "",
            [],
        ),
        (
            "Archivo",
            piece(
                "file",
                "brand:duckdb",
                "etl/datos.duckdb",
                f"{tables} · {size}",
                "Toda la base vive en un archivo: se copia, se comprueba por su huella y se publica en el release "
                "«base-actual».",
            ),
            "",
            [
                piece(
                    "readonly",
                    "icon:shield",
                    "Solo lectura",
                    "read_only=True",
                    "El panel abre el archivo en solo lectura: ninguna página puede escribir la base.",
                )
            ],
        ),
    )


def engine_dbt(facts):
    models, tests = count_kind(facts, "model"), count_kind(facts, "test")
    return engine(
        (
            "Código",
            piece(
                "sql",
                "brand:dbt",
                "Modelos .sql",
                "SQL con Jinja",
                "Cada modelo es un SELECT; ref() y source() nombran de dónde lee, sin escribir rutas ni tablas a mano.",
            ),
            "ref()",
            [],
        ),
        (
            "Grafo",
            piece(
                "dag",
                "icon:parity",
                "Grafo de dependencias",
                "DAG",
                "Con cada ref() dbt arma el grafo y decide el orden: ningún modelo se construye antes que lo que lee.",
            ),
            "orden",
            [],
        ),
        (
            "Compilación",
            piece(
                "compile",
                "icon:code",
                "SQL compilado",
                "Jinja → SQL",
                "Reemplaza cada ref() por la tabla real en DuckDB y deja SQL puro.",
            ),
            "SQL",
            [],
        ),
        (
            "Ejecución",
            piece(
                "run",
                "brand:duckdb",
                "dbt-duckdb",
                f"{models} modelos",
                "Corre cada modelo en DuckDB: staging como vista; intermedio y marts como tabla (dbt/dbt_project.yml).",
            ),
            "",
            [],
        ),
        (
            "Pruebas",
            piece(
                "test",
                "icon:shield",
                "Cada prueba es una consulta",
                f"{tests} pruebas",
                "Una prueba pasa si su consulta devuelve 0 filas; si devuelve alguna, falla y dbt build termina en error.",
            ),
            "resultado",
            [
                piece(
                    "yml",
                    "icon:files",
                    "Declaradas en .yml",
                    "y en dbt/tests/",
                    "Las pruebas genéricas se declaran junto a cada modelo; las propias viven en dbt/tests/.",
                )
            ],
        ),
        (
            "Rastro",
            piece(
                "trace",
                "icon:files",
                "manifest.json · run_results.json",
                "dbt_node · dbt_result",
                "dbt deja el grafo y el resultado de cada nodo; etl/pipeline.py los copia a dbt_node y dbt_result de la "
                "Base DuckDB.",
            ),
            "",
            [],
        ),
    )


def engine_sqlite(facts):
    return engine(
        (
            "Biblioteca",
            piece(
                "lib",
                "brand:python",
                "sqlite3 de Python",
                "sin servidor",
                "SQLite es una biblioteca dentro del programa: no hay servidor, ni usuario, ni puerto.",
            ),
            "escribe",
            [],
        ),
        (
            "Transacción",
            piece(
                "tx",
                "icon:shield",
                "Transacción",
                "todo o nada",
                "Una escritura se confirma entera o no se confirma: un corte a la mitad no deja la base a medias.",
            ),
            "",
            [],
        ),
        (
            "Páginas",
            piece(
                "btree",
                "icon:files",
                "Árbol B en páginas",
                "tablas e índices",
                "Cada tabla es un árbol B guardado en páginas de tamaño fijo dentro del archivo.",
            ),
            "",
            [],
        ),
        (
            "Archivo",
            piece(
                "file",
                "brand:sqlite",
                "Un solo archivo",
                "etl/raw.db · etl/datos.db",
                "El aterrizaje y el respaldo son dos archivos de la máquina de la carga; ninguno se publica.",
            ),
            "",
            [],
        ),
    )


def engine_parquet(facts):
    return engine(
        (
            "Escritura",
            piece(
                "write",
                "brand:python",
                "pyarrow",
                "etl/bronze.py",
                "Escribe cada año de cada fuente en su carpeta file_year=AAAA, con todas las columnas como texto.",
            ),
            "",
            [],
        ),
        (
            "Grupos de filas",
            piece(
                "groups",
                "icon:files",
                "Grupos de filas",
                "row groups",
                "El archivo se divide en grupos de filas; dentro de cada grupo, cada columna va en su propio bloque.",
            ),
            "",
            [],
        ),
        (
            "Compresión",
            piece(
                "zstd",
                "icon:box",
                "Compresión zstd",
                "por columna",
                "Cada bloque de columna se comprime por separado: los valores repetidos, como regiones o productos, "
                "ocupan muy poco.",
            ),
            "",
            [],
        ),
        (
            "Pie",
            piece(
                "footer",
                "icon:code",
                "Pie con metadatos",
                "esquema y estadísticas",
                "Al final del archivo van el esquema y, por grupo de filas, el mínimo y el máximo de cada columna.",
            ),
            "lee el pie primero",
            [],
        ),
        (
            "Lectura",
            piece(
                "read",
                "brand:dbt",
                "read_parquet",
                "hive_partitioning",
                "dbt lee todas las carpetas como una sola tabla y toma el año del nombre de la carpeta "
                "(dbt/models/staging/sources.yml).",
            ),
            "",
            [],
        ),
    )


def engine_streamlit(facts):
    caches = (facts or {}).get("caches")
    return engine(
        (
            "Navegador",
            piece(
                "browser",
                "icon:code",
                "Página en React",
                "el navegador",
                "La página recibe del servidor cada elemento y lo dibuja; un clic vuelve al servidor.",
            ),
            "clic",
            [],
        ),
        (
            "Conexión",
            piece(
                "socket",
                "icon:parity",
                "WebSocket",
                "una por pestaña",
                "El navegador y el servidor quedan conectados mientras la pestaña está abierta.",
            ),
            "evento",
            [],
        ),
        (
            "Script",
            piece(
                "rerun",
                "brand:streamlit",
                "bi/dashboard.py",
                "corre de nuevo",
                "Cada clic vuelve a correr el script entero, de arriba abajo; cada st.* que encuentra se vuelve un "
                "elemento de la página.",
            ),
            "consulta",
            [
                piece(
                    "state",
                    "icon:key",
                    "st.session_state",
                    "por visita",
                    "Guarda lo de cada visita entre una corrida y otra: la vista, el idioma y la página anterior.",
                )
            ],
        ),
        (
            "Caché",
            piece(
                "cache",
                "icon:box",
                "st.cache_data · st.cache_resource",
                f"{caches} funciones" if caches else NOT_VERIFIED,
                "Guardan el resultado de una consulta o una conexión abierta, para no repetirlas en cada corrida.",
            ),
            "si no la tiene",
            [],
        ),
        (
            "Datos",
            piece(
                "db",
                "brand:duckdb",
                "Base DuckDB",
                "solo lectura",
                "Las páginas leen etl/datos.duckdb con bi/queries.py.",
            ),
            "",
            [],
        ),
    )


def engine_github(facts):
    triggers = sorted(
        {trigger for found in (facts or {}).get("workflows", {}).values() for trigger in found["triggers"]}
    )
    return engine(
        (
            "Evento",
            piece(
                "event",
                "icon:clock",
                "Evento",
                " · ".join(triggers) or NOT_VERIFIED,
                "Un workflow corre cuando pasa lo que su sección on: declara: el cron, un push, un pedido manual o el fin "
                "de otro workflow.",
            ),
            "dispara",
            [],
        ),
        (
            "Máquina",
            piece(
                "runner",
                "brand:github",
                "Runner",
                "ubuntu-latest",
                "GitHub crea una máquina virtual nueva para cada job y la borra al terminar: nada pasa de una ejecución a "
                "otra, salvo lo que se guarda aparte.",
            ),
            "",
            [],
        ),
        (
            "Pasos",
            piece(
                "steps",
                "icon:play",
                "Jobs y pasos",
                "en orden",
                "Cada paso es un comando o una acción ya hecha (uses:); si uno falla, los siguientes no corren y el job "
                "queda en rojo.",
            ),
            "deja",
            [
                piece(
                    "perm",
                    "icon:key",
                    "Permisos",
                    "permissions:",
                    "semanal.yml y calidad.yml declaran qué pueden escribir en el repositorio; pruebas.yml no escribe "
                    "nada.",
                )
            ],
        ),
        (
            "Lo que queda",
            piece(
                "keep",
                "icon:files",
                "Lo que queda",
                "logs · caché · release · issues",
                "Los logs de cada paso, la caché de los años cerrados, el release «base-actual», los issues y los pull "
                "requests.",
            ),
            "",
            [],
        ),
    )


def engine_pypi(facts):
    requirements = (facts or {}).get("requirements", [])
    return engine(
        (
            "Pedido",
            piece(
                "req",
                "icon:files",
                "requirements*.txt",
                f"{len(requirements)} dependencias" if requirements else NOT_VERIFIED,
                "Cada dependencia con su versión máxima (D-435).",
            ),
            "rangos",
            [],
        ),
        (
            "Resolución",
            piece(
                "pip",
                "brand:python",
                "pip",
                "resuelve versiones",
                "Busca una versión de cada paquete, y de lo que cada uno necesita, que cumpla todos los rangos a la vez.",
            ),
            "consulta",
            [],
        ),
        (
            "Índice",
            piece(
                "index",
                "icon:box",
                "pypi.org",
                "índice público",
                "Guarda cada versión de cada paquete; un archivo publicado no se puede reemplazar por otro con el mismo "
                "nombre.",
            ),
            "descarga",
            [],
        ),
        (
            "Ruedas",
            piece(
                "wheel",
                "icon:box",
                "Ruedas (wheels)",
                "ya compiladas",
                "pip baja el paquete ya compilado para la máquina y su versión de Python, sin compilar nada.",
            ),
            "instala",
            [],
        ),
        (
            "Entorno",
            piece(
                "env",
                "brand:github",
                "Entorno del runner",
                "se borra al terminar",
                "Se instala de nuevo en cada ejecución: no hay nada instalado de antes.",
            ),
            "",
            [],
        ),
    )


def engine_pytest(facts):
    tests = number(facts["tests"]) if facts else NOT_VERIFIED
    files = facts["data_files"] if facts else NOT_VERIFIED
    return engine(
        (
            "Recolección",
            piece(
                "collect",
                "brand:pytest",
                "Recolección",
                f"{tests} pruebas",
                "Busca en tests/ los archivos test_*.py y, dentro, las funciones que empiezan por test_.",
            ),
            "",
            [],
        ),
        (
            "Selección",
            piece(
                "mark",
                "icon:files",
                "Marcas",
                "«-m datos»",
                f"La carga semanal corre solo las marcadas «datos» ({files} archivos); el CI de cada push corre todas, "
                "menos las de rendimiento.",
            ),
            "",
            [],
        ),
        (
            "Fixtures",
            piece(
                "fixture",
                "icon:box",
                "Fixtures",
                "lo que una prueba necesita",
                "Preparan antes de cada prueba lo que usa, como la conexión a la Base DuckDB, y lo cierran después.",
            ),
            "",
            [],
        ),
        (
            "Comprobación",
            piece(
                "assert",
                "icon:shield",
                "assert",
                "lo obtenido = lo esperado",
                "Cada prueba compara lo que obtiene con lo esperado; si no coincide, falla y muestra la diferencia.",
            ),
            "",
            [],
        ),
        (
            "Resultado",
            piece(
                "exit",
                "brand:github",
                "Código de salida",
                "0 = verde",
                "Si una prueba falla, pytest termina con un código distinto de 0 y el paso del workflow queda en rojo.",
            ),
            "",
            [],
        ),
    )


def engine_charts(facts):
    return engine(
        (
            "Python",
            piece(
                "altair",
                "brand:python",
                "Altair",
                "bi/charts.py",
                "El panel describe cada gráfico: qué datos, qué ejes, qué colores y el formato de números del idioma.",
            ),
            "",
            [],
        ),
        (
            "Especificación",
            piece(
                "spec",
                "icon:code",
                "JSON de Vega-Lite",
                "con sus datos",
                "Altair convierte esa descripción en un JSON de Vega-Lite que lleva los datos adentro.",
            ),
            "al navegador",
            [],
        ),
        (
            "Compilación",
            piece(
                "vega",
                "icon:chart",
                "Vega",
                "en el navegador",
                "Vega-Lite compila el JSON a Vega, que calcula escalas, ejes y leyendas.",
            ),
            "",
            [],
        ),
        (
            "Dibujo",
            piece(
                "draw",
                "icon:chart",
                "Dibujo",
                "canvas o SVG",
                "El navegador dibuja el gráfico y responde al cursor; el servidor no dibuja nada.",
            ),
            "",
            [],
        ),
    )


ENGINES = {
    "duckdb": engine_duckdb,
    "dbt": engine_dbt,
    "sqlite": engine_sqlite,
    "parquet": engine_parquet,
    "streamlit": engine_streamlit,
    "github": engine_github,
    "pypi": engine_pypi,
    "ci": engine_pytest,
    "charts": engine_charts,
}
# endregion
