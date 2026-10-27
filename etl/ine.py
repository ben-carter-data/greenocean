"""IPC of the INE (Chile) for real prices (D-155).

Two official CSV files of the INE, both read as published:
- the time series of the IPC, base 2023 = 100, from January 2024;
- the spliced series of the IPC divisions, from December 2009 to December 2023.
Only division 1, «Alimentos y bebidas no alcohólicas», is used. The files go to the
bronze layer in Parquet; dbt links the two series (models stg_ine__ipc_monthly and
ipc_monthly). If the INE cannot be reached, the load keeps the IPC already published.
"""

import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl import bronze  # noqa: E402

INE_FILES = {
    "base_2023": "https://www.ine.gob.cl/docs/default-source/%C3%ADndice-de-precios-al-consumidor/"
    "cuadros-estadisticos/base-anual-2023_100/series-de-tiempo/"
    "ipc_base_20237baa955a44fe4eada201c196338fb3be.csv?download=true",
    "divisiones_empalmadas": "https://www.ine.gob.cl/docs/default-source/%C3%ADndice-de-precios-al-consumidor/"
    "cuadros-estadisticos/series-empalmadas-y-antecedentes-historicos/"
    "series-empalmadas-diciembre-2009-a-la-fecha/"
    "serie-hist%C3%B3rica-empalmada-divisiones-ipc-diciembre-2009-a-la-fecha-csv.csv?download=true",
}
FOOD_DIVISION = "1"
BRONZE_TABLE = "ine_ipc"
REQUEST_TIMEOUT_SECONDS = 60


def parse_rows(text, file_name):
    """Rows of division 1 (the division itself, not its groups): year, month, index and
    monthly change, as text exactly as published."""
    lines = [line for line in text.splitlines() if line.strip()]
    header = [cell.strip('"') for cell in lines[0].split(";")]
    rows = []
    for line in lines[1:]:
        cells = dict(zip(header, [cell.strip('"') for cell in line.split(";")]))
        is_division = cells.get("División") == FOOD_DIVISION and not cells.get("Grupo")
        if is_division:
            rows.append(
                {
                    "file": file_name,
                    "year": cells["Año"],
                    "month": cells["Mes"],
                    "index_value": cells["Índice"],
                    "monthly_change": cells.get("Variación Mensual (%)", ""),
                }
            )
    return rows


def download(session=None):
    """{file name: rows} of both files, or None if any of them could not be read."""
    session = session or requests.Session()
    result = {}
    for name, url in INE_FILES.items():
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": "greenocean"})
        response.raise_for_status()
        rows = parse_rows(response.content.decode("latin-1"), name)
        if not rows:
            raise ValueError(f"{name}: sin filas de la división {FOOD_DIVISION}")
        result[name] = rows
    return result


def write_bronze(files, bronze_dir=bronze.BRONZE_DIR):
    """bronze/ine_ipc/file=<name>/data.parquet, every column as published (text)."""
    for name, rows in files.items():
        folder = bronze_dir / BRONZE_TABLE / f"file={name}"
        folder.mkdir(parents=True, exist_ok=True)
        columns = ["year", "month", "index_value", "monthly_change"]
        table = pa.table(
            {column: [row[column] for row in rows] for column in columns},
            schema=pa.schema([(column, pa.string()) for column in columns]),
        )
        pq.write_table(table, folder / "data.parquet")


def main():
    try:
        files = download()
    except Exception as error:  # the INE is unreachable or changed its files
        has_previous = (bronze.BRONZE_DIR / BRONZE_TABLE).exists()
        print(
            f"IPC | no se pudo descargar ({error}); "
            + ("se usa el último bronce disponible" if has_previous else "sin IPC previo")
        )
        return 0 if has_previous else 1
    write_bronze(files)
    for name, rows in files.items():
        print(f"IPC | {name} | {len(rows)} meses | último {rows[-1]['year']}-{rows[-1]['month']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
