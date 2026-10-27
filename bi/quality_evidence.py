"""The evidence behind each card of «Calidad y auditoría» (D-171).

Every card of the board can be opened: what it checks, the rows that prove it as a
table, and the method (the SQL that runs, or the automated test). Nothing is drawn
here: bi/dashboard.py shows these frames in a dialog and lets the reader run the
checks again.
"""

import pandas as pd

from bi import project, quality

# The cards, in the board's order: key, title, what the check does.
CARDS = [
    (
        "files",
        "Origen y archivos",
        "Cada archivo que el agente descargó de ODEPA queda registrado en manifest.json con su "
        "fecha, su tamaño y su huella SHA-256.",
    ),
    (
        "shield",
        "Integridad de archivos originales",
        "Los archivos locales se vuelven a resumir con SHA-256 y se comparan con la huella "
        "registrada. Un archivo que no está en este servidor queda pendiente, no verificado.",
    ),
    (
        "calendar",
        "Cobertura temporal",
        "Las semanas con precios, de la primera a la última, y las que faltan en medio.",
    ),
    (
        "gear",
        "Última carga registrada",
        "Cada ejecución del pipeline deja una fila en etl_run: cuándo empezó, qué leyó, qué cargó y qué rechazó.",
    ),
    (
        "layers",
        "Pruebas dbt de la última construcción",
        "dbt corre sus pruebas de datos en cada construcción; la base publicada trae el resultado "
        "de cada una. Si una falla, la base no se reemplaza.",
    ),
    (
        "database",
        "Comprobación de la base actual",
        "La base publicada se lee completa: referencias entre tablas, claves duplicadas y precios "
        "utilizables con formato inválido.",
    ),
    (
        "parity",
        "Paridad SQLite ↔ DuckDB",
        "El respaldo SQLite y el data warehouse DuckDB deben tener los mismos precios, los mismos "
        "rechazos y la misma suma de precios (D-154).",
    ),
    (
        "reconcile",
        "Reconciliación fuente → base",
        "Una prueba automática reconstruye 120 precios semanales desde las filas crudas de ODEPA, "
        "sin pasar por el ETL, y los compara con la base.",
    ),
    (
        "calculator",
        "Recálculo independiente de indicadores",
        "Las alertas se calculan en Python y en SQL y deben coincidir (D-049); las variaciones del "
        "Resumen se comparan con un cálculo SQL independiente.",
    ),
    (
        "chart",
        "Concordancia cálculo → pantalla",
        "Las cifras de familias, ranking y margen de una semana se recalcularon a mano por región "
        "y coinciden con lo que muestra el panel (D-144, D-146).",
    ),
    (
        "warning",
        "Contraste con otra fuente",
        "No existe una segunda fuente oficial con la que contrastar estos precios: ODEPA es la "
        "única. Por eso este control queda pendiente, y así se dice.",
    ),
]
TITLES = {key: title for key, title, _ in CARDS}
EXPLANATIONS = {key: explanation for key, _, explanation in CARDS}
# The automated audits live in the repository; the panel links to them.
TEST_LINKS = {
    "reconcile": ("tests/test_data_audit.py", "tests/test_reconciliation.py"),
    "calculator": ("tests/test_queries.py", "tests/test_alerts.py"),
    "chart": ("tests/test_home_mockup.py", "tests/test_data_audit.py"),
}
MISSING_WEEKS_SQL = """WITH weeks AS (
    SELECT CAST(unnest(generate_series(CAST(MIN(week_start) AS DATE), CAST(MAX(week_start) AS DATE),
                                       INTERVAL 7 DAY)) AS DATE) AS week_start
    FROM weekly_price)
SELECT weeks.week_start AS semana
FROM weeks LEFT JOIN weekly_price USING (week_start)
WHERE weekly_price.week_start IS NULL
ORDER BY 1"""
DBT_TESTS_SQL = """SELECT n.name AS prueba, n.test_type AS tipo, NULLIF(n.column_name, '') AS columna,
       r.status AS estado, round(r.execution_time, 2) AS segundos, r.generated_at AS construida
FROM dbt_node AS n JOIN dbt_result AS r USING (unique_id)
WHERE n.resource_type = 'test'
ORDER BY r.status, n.name"""
RUNS_SQL = """SELECT run_id AS ejecucion, started_at AS inicio_utc, status AS estado, rows_read AS leidas,
       rows_loaded AS cargadas, rows_rejected AS rechazadas, message AS mensaje
FROM etl_run ORDER BY run_id DESC"""


def manifest_frame(manifest):
    """One row per registered download."""
    rows = [
        {
            "archivo": name,
            "año": item.get("year"),
            "bytes": item.get("bytes"),
            "descargado": item.get("downloaded_at", ""),
            "huella": str(item.get("hash", ""))[:12] + "…",
        }
        for name, item in sorted(manifest.items())
        if isinstance(item, dict)
    ]
    return pd.DataFrame(rows, columns=["archivo", "año", "bytes", "descargado", "huella"])


def files_frame(files):
    """The checked files: status, the registered fingerprint and the computed one."""

    def short(value):
        return f"{str(value)[:12]}…" if value else "—"

    return pd.DataFrame(
        [
            {
                "archivo": item["file"],
                "comprobación": item["status"],
                "huella registrada": short(item["expected"]),
                "huella calculada": short(item["actual"]),
                "descargado": item["downloaded_at"],
            }
            for item in files
        ],
        columns=["archivo", "comprobación", "huella registrada", "huella calculada", "descargado"],
    )


def checks_frame(checks):
    """The three database checks with their count and the SQL that counts it."""
    return pd.DataFrame(
        [
            {
                "comprobación": "Referencias entre tablas sin destino",
                "casos": checks["foreign_keys"],
                "sql": quality.FOREIGN_KEYS_SQL,
            },
            {
                "comprobación": "Claves de precio duplicadas",
                "casos": checks["duplicates"],
                "sql": quality.DUPLICATES_SQL,
            },
            {
                "comprobación": "Precios utilizables con formato inválido",
                "casos": checks["invalid"],
                "sql": quality.INVALID_SQL,
            },
        ]
    )


def parity_frame(parity):
    """SQLite against DuckDB, figure by figure; empty without a backup."""
    if not parity:
        return pd.DataFrame(columns=["cifra", "SQLite", "DuckDB", "coincide"])
    return pd.DataFrame(
        [
            {
                "cifra": "Precios semanales",
                "SQLite": parity["rows"][0],
                "DuckDB": parity["rows"][1],
                "coincide": parity["rows"][0] == parity["rows"][1],
            },
            {
                "cifra": "Filas rechazadas",
                "SQLite": parity["rejections"][0],
                "DuckDB": parity["rejections"][1],
                "coincide": parity["rejections"][0] == parity["rejections"][1],
            },
            {
                "cifra": "Suma de precios",
                "SQLite": "misma suma" if parity["ok"] else "distinta",
                "DuckDB": "misma suma" if parity["ok"] else "distinta",
                "coincide": parity["ok"],
            },
        ]
    )


def test_links(key):
    """(label, address) of the repository files that hold a card's automated audit."""
    return [(path, f"{project.GITHUB_URL}/blob/{project.GITHUB_BRANCH}/{path}") for path in TEST_LINKS.get(key, ())] + [
        ("Resultado en GitHub Actions (pruebas)", f"{project.GITHUB_URL}/actions/workflows/pruebas.yml")
    ]
