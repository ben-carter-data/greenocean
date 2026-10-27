"""Content of the project page: documents, SQL catalog, files and real examples.

The page shows text from docs/ and README.md, read here (one source: the
dashboard copies no long text). Every figure comes from datos.db when the page
is drawn. The dashboard only draws what these functions return.
"""

import re
from pathlib import Path

import pandas as pd

from bi import queries
from etl import etl

# region Constants
PROJECT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_DIR / "docs"
PROJECT_GUIDE_FILE = DOCS_DIR / "PROYECTO.md"
DESIGN_FILE = DOCS_DIR / "DISENO.md"
SCHEMA_FILE = PROJECT_DIR / "etl" / "schema.sql"
TESTS_DIR = PROJECT_DIR / "tests"

GITHUB_URL = "https://github.com/cben6514-boop/greenocean"
GITHUB_BRANCH = "main"
COMMITS_URL = f"{GITHUB_URL}/commits/{GITHUB_BRANCH}"
# The release that holds the served database, replaced by every load (D-270).
RELEASE_URL = f"{GITHUB_URL}/releases/tag/base-actual"
ACTIONS_URL = f"{GITHUB_URL}/actions"
ISSUES_URL = f"{GITHUB_URL}/issues"
WHOLESALE_SOURCE_URL = "https://datos.odepa.gob.cl/dataset/precios-mayoristas-de-frutas-y-hortalizas"
CONSUMER_SOURCE_URL = "https://datos.odepa.gob.cl/dataset/precios-consumidor"
INE_IPC_SOURCE_URL = (
    "https://www.ine.gob.cl/estadisticas/economia/indices-de-precio-e-inflacion/indice-de-precios-al-consumidor"
)
# Administration (T-54): its links are shown only after the control code is typed.
WORKFLOW_PAGE_URL = f"{GITHUB_URL}/actions/workflows/semanal.yml"
STREAMLIT_ADMIN_URL = "https://share.streamlit.io"
TOKEN_CREATE_URL = "https://github.com/settings/personal-access-tokens/new"
TOKENS_URL = "https://github.com/settings/tokens"
# Every address of the project, in one place (D-070). Each name says where the link goes
# before leaving the panel; «page» names the page of the panel that already shows that
# content, so it is read there and the original stays one click away. A link without an
# address (the video, the post) stays hidden until it exists.
PROJECT_LINKS = [
    # «Código» is retired (D-118): the GitHub page's own repo-header strip already
    # opens the repository root, so a second link to the same place was redundant.
    {
        "name": "GitHub Actions",
        "description": "Logs completos de cada ejecución del workflow.",
        "url": ACTIONS_URL,
        "icon": "history",
        "group": "Código y operación",
    },
    {
        "name": "Informes semanales",
        "description": "El informe publicado tras cada ejecución (Issues).",
        "url": ISSUES_URL,
        "icon": "description",
        "group": "Código y operación",
    },
    {
        "name": "Historial de cambios",
        "description": "Cada commit, con su tarea.",
        "url": COMMITS_URL,
        "icon": "commit",
        "group": "Código y operación",
    },
    # ODEPA moved to its own sidebar folder, «Fuentes» (D-118): it is not GitHub,
    # so it no longer belongs on the GitHub page.
    {
        "name": "MANUAL",
        "description": "Qué pasa cada martes y qué hacer si algo falla.",
        "url": f"{GITHUB_URL}/blob/{GITHUB_BRANCH}/docs/MANUAL.md",
        "icon": "menu_book",
        "group": "Documentos",
    },
    {
        "name": "DECISIONES",
        "description": "Qué se decidió, por qué y qué se descartó.",
        "url": f"{GITHUB_URL}/blob/{GITHUB_BRANCH}/docs/DECISIONES.md",
        "icon": "gavel",
        "group": "Documentos",
    },
    {
        "name": "Video",
        "description": "El proyecto explicado en dos minutos.",
        "url": None,
        "icon": "play_circle",
        "group": "Documentos",
    },
    {
        "name": "Post de LinkedIn",
        "description": "La presentación del proyecto.",
        "url": None,
        "icon": "campaign",
        "group": "Documentos",
    },
]
# Not part of a visitor's route: each service asks for its own login and permissions.
ADMIN_LINKS = [
    {
        "name": "Administrar la app en Streamlit",
        "description": "Reboot, secretos y registros del panel publicado.",
        "url": STREAMLIT_ADMIN_URL,
        "icon": "settings",
    },
    {
        "name": "Lanzar el workflow en GitHub",
        "description": "Run workflow, desde GitHub.",
        "url": WORKFLOW_PAGE_URL,
        "icon": "play_circle",
    },
    {
        "name": "Crear token en GitHub",
        "description": "Clave nueva para «Ejecutar ahora».",
        "url": TOKEN_CREATE_URL,
        "icon": "key",
    },
    {
        "name": "Ver mis tokens en GitHub",
        "description": "Vencimiento y permisos de cada clave.",
        "url": TOKENS_URL,
        "icon": "vpn_key",
    },
]

INDICATORS_HEADING = "7. Indicadores"
# A table cell may contain an escaped pipe (\|), which is not a column border.
CELL_BORDER_PATTERN = re.compile(r"(?<!\\)\|")
DEFINITION_PATTERN = re.compile(r"^- `([^`]+)`: (.+)$", re.MULTILINE)

# Name given in the catalog to the K7 query, which lives in etl/etl.py.
MATCH_COVERAGE_QUERY_NAME = "k7_match_coverage"

TABLE_NAMES = ["weekly_price", "dim_product", "dim_region", "dim_channel", "dim_date", "etl_run", "rejection"]
# The food IPC of the INE, drawn beside the star (D-190): not in etl/schema.sql, which is the
# SQLite backup's; dbt builds them in the served DuckDB.
IPC_TABLE_NAMES = ["ipc_weekly", "ipc_monthly", "ine_ipc_source"]

# The case every KPI example uses: the one the dashboard opens with.
EXAMPLE_PRODUCT = {"product": "Tomate", "variety": "Larga vida", "quality": "Primera", "normalized_unit": "kilo"}
EXAMPLE_KEY = dict(EXAMPLE_PRODUCT, product_group="Hortalizas")
EXAMPLE_REGION = "Región Metropolitana de Santiago"
EXAMPLE_CHANNEL = "Feria libre"
EXAMPLE_OTHER_CHANNEL = "Supermercado"
# endregion


# region Documents
def read_document(path):
    """Text of one document of the repository."""
    return Path(path).read_text(encoding="utf-8")


def read_section(text, heading):
    """Text under '## heading' until the next '## ' heading (without the heading)."""
    lines = text.splitlines()
    start = lines.index(f"## {heading}") + 1
    end = next((position for position in range(start, len(lines)) if lines[position].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).strip()


def parse_markdown_table(text):
    """Rows of the first Markdown table in text, as dictionaries {header: cell}."""
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    rows = [
        [cell.strip().replace("\\|", "|") for cell in CELL_BORDER_PATTERN.split(line.strip("|"))]
        for line in table_lines
    ]
    headers, body = rows[0], rows[2:]  # rows[1] is the |---| separator
    return [dict(zip(headers, cells)) for cells in body]


def parse_definitions(text):
    """{name: sentence} from the lines '- `name`: sentence'."""
    return dict(DEFINITION_PATTERN.findall(text))


def read_guide_table(heading):
    """One table of docs/PROYECTO.md."""
    return parse_markdown_table(read_section(read_document(PROJECT_GUIDE_FILE), heading))


GLOSSARY_FILE = DOCS_DIR / "GLOSARIO.md"


def read_glossary():
    """The rows of the common glossary, docs/GLOSARIO.md (D-279)."""
    return parse_markdown_table(read_section(read_document(GLOSSARY_FILE), "2. Términos"))


def read_design_table(heading):
    """One table of docs/DISENO.md (questions, rules or indicators)."""
    return parse_markdown_table(read_section(read_document(DESIGN_FILE), heading))


# endregion


# region SQL catalog
# endregion


# region Data model
def count_table_rows(database_file=queries.DATABASE_FILE):
    """{table: number of rows} for every table of the data warehouse."""
    connection = queries.open_database(database_file)
    counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in TABLE_NAMES + IPC_TABLE_NAMES
    }
    connection.close()
    return counts


def count_week_prices(week_start, database_file=queries.DATABASE_FILE):
    """Number of weekly prices of one week (week_start: Monday, YYYY-MM-DD)."""
    connection = queries.open_database(database_file)
    count = connection.execute("SELECT COUNT(*) FROM weekly_price WHERE week_start = ?", (week_start,)).fetchone()[0]
    connection.close()
    return count


def describe_file_size(path):
    """Size of a file in megabytes, with a decimal comma: «33,9 MB»."""
    return f"{path.stat().st_size / 1_000_000:.1f} MB".replace(".", ",")


def count_test_functions(tests_dir=TESTS_DIR):
    """Number of test functions in the repository (a parametrized one counts once)."""
    return sum(path.read_text(encoding="utf-8").count("\ndef test_") for path in tests_dir.glob("test_*.py"))


def read_schema_columns(schema_text):
    """{table: [(column, "PK", "FK" or "")]} from the CREATE TABLE statements."""
    tables = {}
    for match in re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\n\);", schema_text, re.DOTALL):
        lines = [line.split("--")[0].strip() for line in match.group(2).splitlines()]
        columns = [line for line in lines if line and not line.startswith("UNIQUE")]
        tables[match.group(1)] = [
            (column.split()[0], "PK" if "PRIMARY KEY" in column else "FK" if "REFERENCES" in column else "")
            for column in columns
        ]
    return tables


def read_week_span(database_file=queries.DATABASE_FILE):
    """(number of weeks, first Monday, last Monday) with prices."""
    connection = queries.open_database(database_file)
    span = connection.execute(
        "SELECT COUNT(DISTINCT week_start), MIN(week_start), MAX(week_start) FROM weekly_price"
    ).fetchone()
    connection.close()
    return span


# endregion


def build_github_url(path):
    """Address of a file (blob) or a folder (tree) of the repository on GitHub."""
    kind = "tree" if path.endswith("/") else "blob"
    return f"{GITHUB_URL}/{kind}/{GITHUB_BRANCH}/{path.rstrip('/')}"


# endregion


# region KPI examples
def select_example_rows(rows, region=EXAMPLE_REGION, channel=EXAMPLE_CHANNEL):
    """Rows of the example product, region and channel (each only if the column exists)."""
    conditions = dict(EXAMPLE_PRODUCT, region=region, channel=channel)
    for column, value in conditions.items():
        if column in rows.columns and value is not None:
            rows = rows[rows[column] == value]
    return rows


def format_week(week_start):
    """'05-10-2026'."""
    return f"{pd.Timestamp(week_start):%d-%m-%Y}"


# endregion


# endregion


# region Coverage
def read_match_coverage(database_file=queries.DATABASE_FILE):
    """K7 as (keys with margin, consumer keys), with the query of etl/etl.py."""
    connection = queries.open_database(database_file)
    coverage = etl.measure_match_coverage(connection)
    connection.close()
    return coverage


# endregion
