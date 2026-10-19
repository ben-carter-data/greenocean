"""Content of the project page: documents, SQL catalog, files and real examples.

The page shows text from docs/ and README.md, read here (one source: the
dashboard copies no long text). Every figure comes from datos.db when the page
is drawn. The dashboard only draws what these functions return.
"""
import fnmatch
import inspect
import re
from pathlib import Path

import pandas as pd

from bi import alerts, charts, explorer, lag, queries
from etl import etl

# region Constants
PROJECT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_DIR / "docs"
PROJECT_GUIDE_FILE = DOCS_DIR / "PROYECTO.md"
MANUAL_FILE = DOCS_DIR / "MANUAL.md"
DESIGN_FILE = DOCS_DIR / "DISENO.md"
DECISIONS_FILE = DOCS_DIR / "DECISIONES.md"
README_FILE = PROJECT_DIR / "README.md"
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
DECISION_HEADING_PATTERN = re.compile(r"^## (D-\d+[a-z]? · .+)$", re.MULTILINE)

# Clauses shown as labels, with the pattern that finds them in a query without
# comments. Only clauses really present are shown.
SQL_CLAUSE_PATTERNS = {
    "WITH": r"^\s*WITH\b",
    "SELECT": r"\bSELECT\b",
    "JOIN": r"\bJOIN\b",
    # The same table twice in FROM/JOIN, under two different aliases.
    "Auto-join": r"(?s)\b(?:FROM|JOIN)\s+(\w+)\s+AS\s+(\w+)\b.*\bJOIN\s+\1\s+AS\s+(?!\2\b)\w+",
    "WHERE": r"\bWHERE\b",
    "GROUP BY": r"\bGROUP\s+BY\b",
    "Agregados": r"\b(?:COUNT|SUM|AVG|MIN|MAX|TOTAL)\s*\(",
    "HAVING": r"\bHAVING\b",
    "ORDER BY": r"\bORDER\s+BY\b",
    "Funciones de ventana": r"\bOVER\b",
    "LAG": r"\bLAG\s*\(",
    "CASE": r"\bCASE\b",
    "Subconsultas": r"\(\s*SELECT\b",
    "Funciones de fecha": r"\b(?:STRFTIME|JULIANDAY|DATE|DATETIME)\s*\(",
}
# Label of a query whose result a test compares with a Python version (D-049).
PYTHON_RECONCILIATION = "Reconciliación con Python"
# Complexity levels (T-57). A query takes the highest level whose labels it uses;
# a query with none of them is Simple. Labels not listed do not change the level.
LEVEL_SIMPLE = "Simple"
LEVEL_INTERMEDIATE = "Intermedio"
LEVEL_ADVANCED = "Avanzado"
QUERY_LEVELS = [LEVEL_SIMPLE, LEVEL_INTERMEDIATE, LEVEL_ADVANCED]
LEVEL_LABELS = {
    LEVEL_ADVANCED: ["Funciones de ventana", "LAG", "HAVING", PYTHON_RECONCILIATION],
    LEVEL_INTERMEDIATE: ["JOIN", "Auto-join", "Subconsultas", "Funciones de fecha"],
}
LEVEL_CRITERIA = {
    LEVEL_SIMPLE: "SELECT, WHERE, GROUP BY y agregados",
    LEVEL_INTERMEDIATE: "joins del modelo estrella, auto-joins, subconsultas o funciones "
                        "de fecha",
    LEVEL_ADVANCED: "funciones de ventana, LAG, HAVING o reconciliación con Python",
}
PREVIEW_ROW_COUNT = 20
# Python functions that compute the same as an alternative SQL query (D-049).
PYTHON_VERSIONS = {
    "k6_usual_range_sql": [alerts.add_weekly_variation, alerts.add_usual_range,
                           alerts.find_price_alerts],
    "k5_weekly_variations_sql": [lag.add_weekly_variations, lag.has_enough_weeks],
}
# Name given in the catalog to the K7 query, which lives in etl/etl.py.
MATCH_COVERAGE_QUERY_NAME = "k7_match_coverage"
# An example of the SQL the Consultas page builds: tomato in two channels.
EXPLORER_EXAMPLE_FILTERS = dict(
    {field: explorer.ALL for field in explorer.LIST_FIELD_COLUMNS},
    **{explorer.FIELD_PRODUCT: "Tomate", explorer.FIELD_REGION: "Región Metropolitana de Santiago",
       explorer.FIELD_FIRST_WEEK: "2026-09-07", explorer.FIELD_LAST_WEEK: "2026-10-05"})

TABLE_NAMES = ["weekly_price", "dim_product", "dim_region", "dim_channel", "dim_date",
               "etl_run", "rejection"]
DIMENSION_TABLES = ["dim_product", "dim_region", "dim_channel", "dim_date"]
RUN_TABLES = ["etl_run", "rejection"]

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


def read_subsection(text, heading):
    """Text under '### heading' until the next heading of any level."""
    lines = text.splitlines()
    start = lines.index(f"### {heading}") + 1
    end = next((position for position in range(start, len(lines))
                if lines[position].startswith("#")), len(lines))
    return "\n".join(lines[start:end]).strip()


def read_paragraphs(text):
    """The plain paragraphs of a section: no lists, tables or headings."""
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    return [block for block in blocks if not re.match(r"^(-|\d+\.|\||#)", block)]


def read_numbered_items(text):
    """The text of each item of a numbered list, as written (bold and code included)."""
    return re.findall(r"^\d+\. (.+)$", text, flags=re.MULTILINE)


def read_section_lead(text):
    """A section up to its first '### ' subsection."""
    return text.split("\n### ")[0]


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


def split_sections(text):
    """[(heading, body)] for every '## ' section of a document."""
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    return [(parts[position].strip(), parts[position + 1].strip())
            for position in range(1, len(parts), 2)]


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


def list_decisions():
    """[(title, body)] of every decision of docs/DECISIONES.md, in order."""
    return [(heading, body) for heading, body in split_sections(read_document(DECISIONS_FILE))
            if DECISION_HEADING_PATTERN.match(f"## {heading}")]
# endregion


# region SQL catalog
def strip_sql_comments(sql):
    """The query without its '-- ...' comments."""
    return re.sub(r"--[^\n]*", "", sql)


def detect_sql_clauses(sql):
    """Clauses really used by a query, in a fixed order.

    The body of a WITH block, «name AS (SELECT …)», is not a subquery, so its
    parenthesis is removed before looking for subqueries.
    """
    code = strip_sql_comments(sql).upper()
    code = re.sub(r"\bAS\s*\(\s*SELECT\b", "AS SELECT", code)
    return [label for label, pattern in SQL_CLAUSE_PATTERNS.items()
            if re.search(pattern, code, re.MULTILINE)]


def build_preview_sql(sql):
    """The query limited to its first 20 rows, for the «Ver resultado» button."""
    query = strip_sql_comments(sql).strip().rstrip(";")
    return f"SELECT * FROM (\n{query}\n) LIMIT {PREVIEW_ROW_COUNT}"


def run_preview(sql, parameters=(), database_file=queries.DATABASE_FILE):
    """First 20 rows of a query, run on the read-only connection."""
    connection = queries.open_database(database_file)
    rows = queries.read_dataframe(connection, build_preview_sql(sql), parameters)
    connection.close()
    return rows


def read_python_versions(query_name):
    """Source code of the Python functions that compute the same as the query."""
    return [inspect.getsource(function) for function in PYTHON_VERSIONS.get(query_name, [])]


def classify_query_level(clauses):
    """(level, labels that set it) from the labels detected in a query."""
    for level in [LEVEL_ADVANCED, LEVEL_INTERMEDIATE]:
        reasons = [clause for clause in clauses if clause in LEVEL_LABELS[level]]
        if reasons:
            return level, reasons
    return LEVEL_SIMPLE, []


def describe_query(sql, has_python_version=False):
    """{clauses, level, level_reasons} of a query, all read from its text."""
    clauses = detect_sql_clauses(sql) + ([PYTHON_RECONCILIATION] if has_python_version else [])
    level, reasons = classify_query_level(clauses)
    return {"clauses": clauses, "level": level, "level_reasons": reasons}


def list_named_queries():
    """Every named query of bi/queries.sql with its question and page (docs/PROYECTO.md)."""
    descriptions = {row["Consulta"]: row for row in read_guide_table("Consultas SQL")}
    catalog = []
    for name, sql in queries.load_queries().items():
        python_versions = read_python_versions(name)
        catalog.append({"name": name, "sql": sql.strip(),
                        "question": descriptions[name]["Qué responde"],
                        "page": ("Dashboard" if descriptions[name]["Página"] == "Inicio"
                                 else descriptions[name]["Página"]),
                        "python": python_versions,
                        **describe_query(sql, bool(python_versions))})
    return catalog


def group_queries_by_level(catalog):
    """{level: queries of that level}, from Simple to Avanzado, in catalog order."""
    return {level: [query for query in catalog if query["level"] == level]
            for level in QUERY_LEVELS}


def build_explorer_example():
    """(SQL, parameters) that Consulta por clics builds: tomato in the Metropolitan
    Region, five weeks."""
    return explorer.build_search_query(EXPLORER_EXAMPLE_FILTERS)
# endregion


# region Data model
def count_table_rows(database_file=queries.DATABASE_FILE):
    """{table: number of rows} for every table of the data warehouse."""
    connection = queries.open_database(database_file)
    counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
              for table in TABLE_NAMES}
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


# region Repository files
def parse_readme_structure(readme_text):
    """[(path, description)] from the tree of the README section «Estructura»."""
    tree = read_section(readme_text, "Estructura").strip("`\n")
    folders = []
    entries = []
    for line in tree.splitlines():
        branch = re.search(r"[├└]── ", line)
        if not branch:
            continue
        depth = branch.start() // 4
        # Names have no spaces; whatever follows the name is its description.
        name, _, description = line[branch.end():].partition(" ")
        folders = folders[:depth]
        entries.append(("".join(folders) + name, description.strip()))
        if name.endswith("/"):
            folders.append(name)
    return entries


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


def list_repository_files():
    """[(path, description, GitHub address or None)] from the README tree."""
    return [(path, description, build_github_url(path) if is_in_repository(path) else None)
            for path, description in parse_readme_structure(read_document(README_FILE))]
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


def build_k1_example(margin_rows):
    """K1 step by step for the example product, the latest week with a margin."""
    rows = select_example_rows(margin_rows)
    if rows.empty:
        return []
    row = rows.loc[rows["week_start"].idxmax()]
    return [f"Semana del {format_week(row['week_start'])}, {EXAMPLE_REGION}, "
            f"{EXAMPLE_CHANNEL}.",
            f"Precio mayorista: {format_money(row['wholesale_price'])} por kilo.",
            f"Precio al consumidor: {format_money(row['consumer_price'])} por kilo.",
            f"({format_money(row['consumer_price'])} − {format_money(row['wholesale_price'])}) / "
            f"{format_money(row['wholesale_price'])} = "
            f"{charts.format_percent(row['margin'] * 100)}."]


def build_k2_example(gap_rows):
    """K2 step by step: supermarket against street market, latest week."""
    rows = select_example_rows(gap_rows, channel=EXAMPLE_OTHER_CHANNEL)
    rows = rows[rows["reference_channel"] == EXAMPLE_CHANNEL]
    if rows.empty:
        return []
    row = rows.loc[rows["week_start"].idxmax()]
    return [f"Semana del {format_week(row['week_start'])}, {EXAMPLE_REGION}.",
            f"{EXAMPLE_OTHER_CHANNEL}: {format_money(row['price'])}; "
            f"{EXAMPLE_CHANNEL}: {format_money(row['reference_price'])}.",
            f"{format_money(row['price'])} / {format_money(row['reference_price'])} − 1 = "
            f"{charts.format_signed_percent(row['gap'] * 100)}."]


def build_k3_example(regional_rows):
    """K3 step by step: the region against the national price, latest week."""
    rows = select_example_rows(regional_rows)
    if rows.empty:
        return []
    row = rows.loc[rows["week_start"].idxmax()]
    return [f"Semana del {format_week(row['week_start'])}, {EXAMPLE_CHANNEL}.",
            f"Precio en la {EXAMPLE_REGION}: {format_money(row['price'])}.",
            f"Promedio simple de las regiones con dato: {format_money(row['national_price'])}.",
            f"{format_money(row['price'])} / {format_money(row['national_price'])} = "
            f"{charts.format_index(row['regional_index'])}: "
            f"{charts.describe_regional_index(row['regional_index'])}."]


def build_k4_example(seasonal_rows):
    """K4 step by step: the national price of the latest week against its year."""
    rows = select_example_rows(seasonal_rows, region=None)
    if rows.empty:
        return []
    row = rows.loc[rows["week_start"].idxmax()]
    return [f"Semana del {format_week(row['week_start'])}, {EXAMPLE_CHANNEL}, precio nacional: "
            f"{format_money(row['national_price'])}.",
            f"Promedio de las {row['week_count']} semanas de {row['price_year']}: "
            f"{format_money(row['yearly_price'])}.",
            f"{format_money(row['national_price'])} / {format_money(row['yearly_price'])} = "
            f"{charts.format_index(row['seasonal_index'])}."]


def build_k5_example(margin_rows):
    """K5 step by step for the example series (bi/lag.py)."""
    rows = select_example_rows(margin_rows)
    if not lag.has_enough_weeks(rows):
        return []
    best = lag.find_lag(lag.correlate_by_lag(rows))
    if best is None:
        return []
    best_lag, correlation, pair_count = best
    threshold = lag.SIGNIFICANCE_FACTOR / pair_count ** 0.5
    verdict = (f"rezago: {charts.describe_weeks(best_lag)}"
               if lag.is_clear_relation(correlation, pair_count) else "sin relación clara")
    return [f"{EXAMPLE_REGION}, {EXAMPLE_CHANNEL}: {rows['week_start'].nunique()} semanas "
            "con ambos precios.",
            f"La correlación más alta es {charts.format_index(correlation)}, con un desfase "
            f"de {charts.describe_weeks(best_lag)} y {pair_count} pares de cambios semanales.",
            f"Umbral 2/√{pair_count} = {charts.format_index(threshold)}: {verdict}."]


def build_k6_example(alert_rows):
    """K6 step by step: the largest movement of the latest week with alerts."""
    if alert_rows.empty:
        return []
    latest_week = alert_rows[alert_rows["week_start"] == alert_rows["week_start"].max()]
    row = latest_week.loc[latest_week["variation"].abs().idxmax()]
    limit = alerts.ALERT_DEVIATIONS * row["variation_deviation"] * 100
    return [f"Semana del {format_week(row['week_start'])}: {row['product']} "
            f"{row['variety']} · {row['quality']}, {row['channel']}.",
            f"Cambio de la semana: {charts.format_signed_percent(row['variation'] * 100)}. "
            f"Cambio habitual (12 semanas previas): "
            f"{charts.format_signed_percent(row['usual_variation'] * 100)}.",
            f"Desviación estándar: {charts.format_percent(row['variation_deviation'] * 100)}; "
            f"el límite es 2 × {charts.format_percent(row['variation_deviation'] * 100)} = "
            f"{charts.format_percent(limit)} alrededor de lo habitual: es alerta."]


def build_k7_example(keys_with_margin, consumer_keys):
    """K7 step by step from the coverage query of etl/etl.py."""
    return [f"Claves de frutas y verduras del consumidor: {consumer_keys}.",
            f"De ellas, con un precio mayorista en la misma semana, región y unidad: "
            f"{keys_with_margin}.",
            f"{keys_with_margin} / {consumer_keys} = "
            f"{charts.format_percent(keys_with_margin / consumer_keys * 100)}."]


def build_k8_example(latest_run, rejection_rows):
    """K8 step by step from the latest ETL run."""
    rows_read = charts.format_thousands(latest_run["rows_read"])
    if rejection_rows.empty:
        return [f"Filas leídas en la última ejecución: {rows_read}.",
                "Filas rechazadas: 0, así que K8 = 0 %."]
    return ([f"Filas leídas en la última ejecución: {rows_read}."]
            + [f"{row['source']} · {row['reason']}: "
               f"{charts.format_thousands(row['rejected_rows'])} filas = "
               f"{charts.format_percent(row['rejected_share'] * 100, decimals=3)}."
               for row in rejection_rows.to_dict("records")])
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


# File order follows execution and dependency flow, rather than claiming a commit chronology.
CODE_WALKTHROUGH = [
    ("agent/agent.py", "Téléchargement", "Descargar y validar las fuentes",
     "Descarga los CSV de ODEPA, valida encabezados y deja un manifiesto por archivo.",
     "agent/input.csv y URLs de ODEPA", "CSV descargados y manifest.json",
     "Reintentar fallas de conexión y detectar un archivo inesperado antes de cargarlo."),
    ("etl/etl.py", "Transformation", "Limpiar, aplicar reglas y cargar",
     "Conserva el original, normaliza unidades y semanas, aplica controles y carga el modelo estrella.",
     "CSV descargados", "raw.db, datos.db y registro de rechazos",
     "Evitar comparar unidades distintas y guardar una carga que no pasa los controles de calidad."),
    ("bi/queries.py", "Accès aux données", "Leer los indicadores en modo solo lectura",
     "Ejecuta consultas SQL por nombre y limita los datos al producto solicitado.",
     "datos.db y queries.sql", "tablas de resultados para el panel",
     "Consultar sin modificar la base y pasar los filtros como parámetros, sin concatenar sus valores."),
    ("bi/alerts.py", "Analyse", "Detectar variaciones fuera de lo habitual",
     "Calcula cambios semanales y compara cada uno con las 12 variaciones anteriores.",
     "precios nacionales semanales", "alertas K6 con variación y rango habitual",
     "No tratar un salto entre semanas faltantes como una variación semanal ni usar el dato evaluado en su propio rango."),
    ("bi/lag.py", "Analyse", "Medir el rezago descriptivo",
     "Compara los cambios mayoristas y al consumidor para varios desfases.",
     "series de precios comparables", "correlaciones y desfase K5",
     "Exigir historia suficiente y distinguir una asociación descriptiva de una afirmación causal."),
    ("bi/data_browser.py", "Accès aux données", "Consultar precios por páginas",
     "Filtra, cuenta y ordena resultados en SQLite antes de devolver una página de hasta 100 filas.",
     "filtros de precios, variaciones o brechas", "página de resultados y conteo total",
     "Conservar el nivel semanal, comparar claves equivalentes y no enviar toda la base al navegador."),
    ("bi/explorer.py", "Accès aux données", "Construir consultas con clics",
     "Traduce los filtros del explorador a SQL parametrizado y organiza las opciones disponibles.",
     "selección de producto, región, canal y fechas", "consulta y parámetros separados",
     "Permitir explorar sin escribir SQL y sin ejecutar texto introducido por el visitante."),
    ("bi/charts.py", "Visualisation", "Convertir indicadores en gráficos",
     "Dibuja comparaciones, tendencias y calendarios con formatos chilenos y colores coherentes.",
     "tablas de indicadores", "gráficos Altair y paletas",
     "Elegir una forma legible para cada pregunta y mantener identificables canales, alzas y bajas."),
    ("bi/market_charts.py", "Visualisation", "Explorar el mercado de un producto",
     "Dibuja la composición semanal, la evolución de un producto y el índice regional por región y canal.",
     "observaciones válidas e indicadores K3 y K6 de una clave comparable", "gráficos Plotly interactivos",
     "Comparar la misma variedad, calidad y unidad, y conservar semanas sin dato."),
    ("bi/market_style.py", "Visualisation", "Presentar paneles flotantes con la paleta del proyecto",
     "Aplica al dashboard un fondo alimentario local y superficies con contraste según el tema.",
     "paletas de charts.py y fondo de bi/assets", "estilos exclusivos del dashboard",
     "Conservar la dominante Vantablack, las superficies pizarra y el cian sin alterar los gráficos."),
    ("bi/control.py", "Opération", "Consultar y ejecutar el pipeline",
     "Lee estados de GitHub Actions y permite solicitar una ejecución con credenciales de administración.",
     "API de GitHub y credenciales en secretos", "estados, pasos y diagnóstico HTTP seguro",
     "Explicar fallas de red, permisos o límites de consultas sin exponer tokens ni respuestas sensibles."),
    ("bi/architecture.py", "Visualisation", "Dibujar el recorrido y la infraestructura",
     "Construye diagramas SVG con los estados y cifras reales que recibe del panel.",
     "estados del pipeline y cifras de la carga", "pipeline y arquitectura por plataforma",
     "Distinguir un estado conocido de uno sin evidencia y explicar cada componente al pasar el mouse."),
    ("bi/star_model.py", "Visualisation", "Explicar el modelo estrella",
     "Presenta tablas, relaciones y claves del data warehouse con explicaciones accesibles.",
     "columnas del esquema y conteos reales", "diagrama del modelo y detalle de tablas",
     "Mostrar qué guarda cada tabla y cómo se relacionan sus claves sin exigir conocer SQL."),
    ("bi/zoom.py", "Visualisation", "Explorar los diagramas",
     "Añade zoom y desplazamiento dentro del marco del diagrama.",
     "SVG del pipeline o de la arquitectura", "marco interactivo con acercar, alejar y restablecer",
     "Conservar el contexto de la página al ampliar un detalle, también con interacción táctil."),
    ("bi/project.py", "Documentation", "Vincular documentación, SQL y ejemplos",
     "Lee el diseño, las reglas, los archivos y las consultas desde el repositorio.",
     "docs/, consultas SQL y archivos públicos", "catálogos y ejemplos documentados",
     "Evitar mantener versiones distintas de la explicación y el código real."),
    ("bi/dashboard.py", "Présentation", "Presentar el seguimiento y el análisis",
     "Conecta el dashboard, los filtros, los diagramas, la documentación y la operación.",
     "indicadores, estados y perfil del visitante", "este sistema de seguimiento en Streamlit",
     "Dar contexto antes de pedir filtros y conservar un recorrido claro desde el resultado hasta su implementación."),
    ("bi/report.py", "Opération", "Publicar el informe semanal",
     "Resume el estado de la carga y las alertas de la semana para el informe automatizado.",
     "datos.db y ejecución semanal", "informe para GitHub Issues",
     "Dejar un resultado verificable de cada ejecución además de actualizar la base."),
]


def list_code_walkthrough():
    """Public source files only, with context and source read from the working tree."""
    entries = []
    for number, (path, stage, title, purpose, inputs, outputs, challenge) in enumerate(
            CODE_WALKTHROUGH, 1):
        entries.append({"number": number, "path": path, "folder": path.split('/')[0],
                        "title": title, "purpose": purpose, "input": inputs,
                        "output": outputs, "challenge": challenge,
                        "source": read_document(PROJECT_DIR / path)})
    return entries
