"""Content of the project page: documents, SQL catalog, files and real examples.

The page shows text from docs/ and README.md, read here (one source: the
dashboard copies no long text). Every figure comes from datos.db when the page
is drawn. The dashboard only draws what these functions return.
"""
import fnmatch
import re
from pathlib import Path

import pandas as pd

from bi import charts, queries
from etl import etl

# region Constants
PROJECT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_DIR / "docs"
PROJECT_GUIDE_FILE = DOCS_DIR / "PROYECTO.md"
MANUAL_FILE = DOCS_DIR / "MANUAL.md"
DESIGN_FILE = DOCS_DIR / "DISENO.md"
GITIGNORE_FILE = PROJECT_DIR / ".gitignore"
SCHEMA_FILE = PROJECT_DIR / "etl" / "schema.sql"
TESTS_DIR = PROJECT_DIR / "tests"

GITHUB_URL = "https://github.com/cben6514-boop/monitor-precios-hito1"
GITHUB_BRANCH = "main"
COMMITS_URL = f"{GITHUB_URL}/commits/{GITHUB_BRANCH}"
ACTIONS_URL = f"{GITHUB_URL}/actions"
ISSUES_URL = f"{GITHUB_URL}/issues"
WHOLESALE_SOURCE_URL = ("https://datos.odepa.gob.cl/dataset/"
                        "precios-mayoristas-de-frutas-y-hortalizas")
CONSUMER_SOURCE_URL = "https://datos.odepa.gob.cl/dataset/precios-consumidor"
INE_IPC_SOURCE_URL = ("https://www.ine.gob.cl/estadisticas/economia/indices-de-precio-e-inflacion/"
                      "indice-de-precios-al-consumidor")
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
    {"name": "GitHub Actions", "description": "Logs completos de cada ejecución del workflow.",
     "url": ACTIONS_URL, "icon": "history", "group": "Código y operación"},
    {"name": "Informes semanales", "description": "El informe publicado tras cada ejecución (Issues).",
     "url": ISSUES_URL, "icon": "description", "group": "Código y operación"},
    {"name": "Historial de cambios", "description": "Cada commit, con su tarea.",
     "url": COMMITS_URL, "icon": "commit", "group": "Código y operación"},
    # ODEPA moved to its own sidebar folder, «Fuentes» (D-118): it is not GitHub,
    # so it no longer belongs on the GitHub page.
    {"name": "MANUAL", "description": "Qué pasa cada martes y qué hacer si algo falla.",
     "url": f"{GITHUB_URL}/blob/{GITHUB_BRANCH}/docs/MANUAL.md", "icon": "menu_book",
     "group": "Documentos"},
    {"name": "DECISIONES", "description": "Qué se decidió, por qué y qué se descartó.",
     "url": f"{GITHUB_URL}/blob/{GITHUB_BRANCH}/docs/DECISIONES.md", "icon": "gavel",
     "group": "Documentos"},
    {"name": "Video", "description": "El proyecto explicado en dos minutos.",
     "url": None, "icon": "play_circle", "group": "Documentos"},
    {"name": "Post de LinkedIn", "description": "La presentación del proyecto.",
     "url": None, "icon": "campaign", "group": "Documentos"},
]
# Not part of a visitor's route: each service asks for its own login and permissions.
ADMIN_LINKS = [
    {"name": "Administrar la app en Streamlit",
     "description": "Reboot, secretos y registros del panel publicado.",
     "url": STREAMLIT_ADMIN_URL, "icon": "settings"},
    {"name": "Lanzar el workflow en GitHub", "description": "Run workflow, desde GitHub.",
     "url": WORKFLOW_PAGE_URL, "icon": "play_circle"},
    {"name": "Crear token en GitHub", "description": "Clave nueva para «Ejecutar ahora».",
     "url": TOKEN_CREATE_URL, "icon": "key"},
    {"name": "Ver mis tokens en GitHub", "description": "Vencimiento y permisos de cada clave.",
     "url": TOKENS_URL, "icon": "vpn_key"},
]

# Headings of docs/DISENO.md that hold the business questions, rules and indicators.
QUESTIONS_HEADING = "3. Preguntas de negocio"
RULES_HEADING = "6. Reglas de negocio"
INDICATORS_HEADING = "7. Indicadores"
# A table cell may contain an escaped pipe (\|), which is not a column border.
CELL_BORDER_PATTERN = re.compile(r"(?<!\\)\|")
DEFINITION_PATTERN = re.compile(r"^- `([^`]+)`: (.+)$", re.MULTILINE)

# Name given in the catalog to the K7 query, which lives in etl/etl.py.
MATCH_COVERAGE_QUERY_NAME = "k7_match_coverage"

TABLE_NAMES = ["weekly_price", "dim_product", "dim_region", "dim_channel", "dim_date",
               "etl_run", "rejection"]
# The food IPC of the INE, drawn beside the star (D-190): not in etl/schema.sql, which is the
# SQLite backup's; dbt builds them in the served DuckDB.
IPC_TABLE_NAMES = ["ipc_weekly", "ipc_monthly", "ine_ipc_source"]

# The case every KPI example uses: the one the dashboard opens with.
EXAMPLE_PRODUCT = {"product": "Tomate", "variety": "Larga vida", "quality": "Primera",
                   "normalized_unit": "kilo"}
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
    end = next((position for position in range(start, len(lines))
                if lines[position].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).strip()


def parse_labeled_items(text, numbered=False):
    """[(label, text)] of the list items that start in bold: «- **Label:** text», also
    «- **Label** text» (or «1. ...»)."""
    marker = r"\d+\." if numbered else "-"
    return re.findall(rf"^{marker} \*\*(.+?):?\*\*:? ?(.+)$", text, flags=re.MULTILINE)


def read_closing_paragraph(text):
    """The last paragraph of a section that is not part of a list."""
    paragraphs = [block.strip() for block in text.split("\n\n") if block.strip()]
    return next(block for block in reversed(paragraphs)
                if not re.match(r"^(-|\d+\.) ", block))


def parse_markdown_table(text):
    """Rows of the first Markdown table in text, as dictionaries {header: cell}."""
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    rows = [[cell.strip().replace("\\|", "|") for cell in
             CELL_BORDER_PATTERN.split(line.strip("|"))] for line in table_lines]
    headers, body = rows[0], rows[2:]  # rows[1] is the |---| separator
    return [dict(zip(headers, cells)) for cells in body]


def parse_definitions(text):
    """{name: sentence} from the lines '- `name`: sentence'."""
    return dict(DEFINITION_PATTERN.findall(text))


def read_guide_table(heading):
    """One table of docs/PROYECTO.md."""
    return parse_markdown_table(read_section(read_document(PROJECT_GUIDE_FILE), heading))


def read_design_table(heading):
    """One table of docs/DISENO.md (questions, rules or indicators)."""
    return parse_markdown_table(read_section(read_document(DESIGN_FILE), heading))


# endregion


# region SQL catalog
def strip_sql_comments(sql):
    """The query without its '-- ...' comments."""
    return re.sub(r"--[^\n]*", "", sql)


# endregion


# region Data model
def count_table_rows(database_file=queries.DATABASE_FILE):
    """{table: number of rows} for every table of the data warehouse."""
    connection = queries.open_database(database_file)
    counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
              for table in TABLE_NAMES + IPC_TABLE_NAMES}
    connection.close()
    return counts


def count_week_prices(week_start, database_file=queries.DATABASE_FILE):
    """Number of weekly prices of one week (week_start: Monday, YYYY-MM-DD)."""
    connection = queries.open_database(database_file)
    count = connection.execute("SELECT COUNT(*) FROM weekly_price WHERE week_start = ?",
                               (week_start,)).fetchone()[0]
    connection.close()
    return count


def describe_file_size(path):
    """Size of a file in megabytes, with a decimal comma: «33,9 MB»."""
    return f"{path.stat().st_size / 1_000_000:.1f} MB".replace(".", ",")


def count_test_functions(tests_dir=TESTS_DIR):
    """Number of test functions in the repository (a parametrized one counts once)."""
    return sum(path.read_text(encoding="utf-8").count("\ndef test_")
               for path in tests_dir.glob("test_*.py"))


def read_schema_columns(schema_text):
    """{table: [(column, "PK", "FK" or "")]} from the CREATE TABLE statements."""
    tables = {}
    for match in re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\n\);", schema_text,
                             re.DOTALL):
        lines = [line.split("--")[0].strip() for line in match.group(2).splitlines()]
        columns = [line for line in lines if line and not line.startswith("UNIQUE")]
        tables[match.group(1)] = [(column.split()[0], "PK" if "PRIMARY KEY" in column
                                   else "FK" if "REFERENCES" in column else "")
                                  for column in columns]
    return tables


def read_week_span(database_file=queries.DATABASE_FILE):
    """(number of weeks, first Monday, last Monday) with prices."""
    connection = queries.open_database(database_file)
    span = connection.execute("SELECT COUNT(DISTINCT week_start), MIN(week_start), "
                              "MAX(week_start) FROM weekly_price").fetchone()
    connection.close()
    return span

# endregion


def read_ignored_patterns():
    """Patterns of .gitignore: files kept out of the repository (D-020)."""
    return [line.strip() for line in read_document(GITIGNORE_FILE).splitlines()
            if line.strip() and not line.startswith("#")]


def is_in_repository(path):
    """True when the path exists here and .gitignore does not keep it out of GitHub."""
    is_ignored = any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(Path(path).name, pattern)
                     for pattern in read_ignored_patterns())
    return (PROJECT_DIR / path).exists() and not is_ignored


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


def format_money(value):
    """'$ 1.234'."""
    return f"$ {charts.format_thousands(value)}"


def format_week(week_start):
    """'05-10-2026'."""
    return f"{pd.Timestamp(week_start):%d-%m-%Y}"


# endregion


# region Rule evidence
# One query per rule, run on datos.db, and the sentence that shows its answer.
RULE_EVIDENCE = {
    "RN-02": ("SELECT COUNT(*) AS keys, SUM(variety = 'Sin especificar' "
              "AND quality = 'Sin especificar') AS unspecified FROM dim_product",
              "{keys} claves de producto; {unspecified} sin variedad ni calidad "
              "(«Sin especificar»)."),
    "RN-03": ("SELECT COUNT(*) AS prices FROM weekly_price JOIN dim_channel USING (channel_id) "
              "WHERE dim_channel.source = 'wholesale' AND normalized_unit = 'kilo'",
              "{prices} precios semanales mayoristas quedaron por kilo."),
    "RN-04": ("SELECT COUNT(*) AS prices FROM weekly_price JOIN dim_channel USING (channel_id) "
              "WHERE dim_channel.source = 'wholesale' AND normalized_unit = 'unidad'",
              "{prices} precios semanales mayoristas quedaron por unidad."),
    "RN-05": ("SELECT COUNT(*) AS prices FROM weekly_price WHERE flag = 'UNIDAD_NO_CONVERTIBLE'",
              "{prices} precios semanales conservados con la marca UNIDAD_NO_CONVERTIBLE."),
    "RN-07": ("SELECT ROUND(AVG(observation_count), 1) AS average, MAX(observation_count) "
              "AS maximum FROM weekly_price JOIN dim_channel USING (channel_id) "
              "WHERE dim_channel.source = 'wholesale' AND price IS NOT NULL",
              "Cada precio semanal mayorista junta en promedio {average} precios diarios "
              "(máximo {maximum})."),
    "RN-08": ("SELECT COUNT(DISTINCT week_start) AS weeks, "
              "COUNT(DISTINCT CASE WHEN dayofweek(CAST(week_start AS DATE)) <> 1 THEN week_start END) "
              "AS other_days FROM weekly_price",
              "{weeks} semanas en la base; {other_days} empiezan en un día que no es lunes."),
    "RN-09": ("SELECT ROUND(AVG(observation_count), 1) AS average FROM weekly_price "
              "JOIN dim_channel USING (channel_id) WHERE dim_channel.source = 'consumer'",
              "Cada precio semanal al consumidor promedia {average} puntos de venta."),
    "RN-10": ("SELECT COUNT(*) AS prices FROM weekly_price JOIN dim_channel USING (channel_id) "
              "WHERE dim_channel.source = 'consumer' AND dim_channel.channel = 'Mercado Mayorista'",
              "{prices} precios semanales del canal «Mercado Mayorista» del consumidor."),
    "RN-12": ("SELECT COUNT(*) AS prices FROM weekly_price WHERE flag = 'ATIPICO'",
              "{prices} precios semanales marcados como atípicos y fuera de los indicadores."),
    "RN-13": ("SELECT COUNT(*) AS names FROM dim_product WHERE product LIKE '%  %' "
              "OR product LIKE '%' || chr(160) || '%' OR variety LIKE '%  %' "
              "OR quality LIKE '%  %'",
              "{names} nombres de producto con espacios repetidos o no separables en la base."),
    "RN-14": ("SELECT (SELECT COUNT(*) FROM etl_run WHERE status = 'LOADED') AS runs, "
              "(SELECT COUNT(*) FROM (SELECT 1 FROM weekly_price GROUP BY week_start, product_id, "
              "region_id, channel_id, normalized_unit HAVING COUNT(*) > 1)) AS duplicates",
              "{runs} cargas correctas registradas; {duplicates} claves repetidas en "
              "weekly_price."),
}


def format_evidence_value(value):
    """Whole numbers with a dot every three digits; decimals with a comma."""
    if isinstance(value, float) and not value.is_integer():
        return f"{value}".replace(".", ",")
    return charts.format_thousands(value or 0)


def read_rule_evidence(database_file=queries.DATABASE_FILE):
    """{rule: sentence with its real figure} for the rules that datos.db can show."""
    connection = queries.open_database(database_file)
    evidence = {}
    for rule, (sql, sentence) in RULE_EVIDENCE.items():
        row = queries.read_dataframe(connection, sql).iloc[0]
        evidence[rule] = sentence.format(**{column: format_evidence_value(row[column])
                                            for column in row.index})
    connection.close()
    return evidence


def describe_margin_evidence(margin_count):
    """RN-06: margins exist only between prices of the same unit."""
    return (f"{charts.format_thousands(margin_count)} márgenes semanales calculados, "
            f"todos entre precios de la misma unidad.")


def describe_rejection_evidence(rejection_rows, example_row=None):
    """RN-11: rejected rows of the latest run, by reason, with one example."""
    if rejection_rows.empty:
        return "La última ejecución no rechazó filas."
    reasons = ", ".join(f"{row['reason']}: {charts.format_thousands(row['rejected_rows'])}"
                        for row in rejection_rows.to_dict("records"))
    example = f" Ejemplo guardado: {example_row}" if example_row else ""
    return f"Filas rechazadas en la última ejecución: {reasons}.{example}"


def read_rejection_example(database_file=queries.DATABASE_FILE):
    """One rejected row exactly as it was read, or None."""
    connection = queries.open_database(database_file)
    row = connection.execute("SELECT original_row FROM rejection LIMIT 1").fetchone()
    connection.close()
    return row[0] if row else None
# endregion


# region Coverage
def read_match_coverage(database_file=queries.DATABASE_FILE):
    """K7 as (keys with margin, consumer keys), with the query of etl/etl.py."""
    connection = queries.open_database(database_file)
    coverage = etl.measure_match_coverage(connection)
    connection.close()
    return coverage
# endregion


