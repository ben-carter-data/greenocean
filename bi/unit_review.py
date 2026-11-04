"""D-520, D-524: the sale units of ODEPA reviewed by hand, and the new ones nobody has classified yet.

etl/reviewed_units.csv holds every unit ODEPA has used, with the reading checked against the prices of the same product.
Each load keeps in the Base DuckDB the units it saw (source_unit), so «Catálogo de controles» and the «Informe semanal»
can name a new unit also where etl/raw.db does not exist: new units do not pile up in silence.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from bi import queries

REVIEWED_FILE = Path(__file__).resolve().parent.parent / "etl" / "reviewed_units.csv"
# One package and one quantity, or a price already per kilo, unit or liter: nothing that can be read two ways.
PLAIN_PACKAGE = re.compile(
    r"^\$/(?:(?:kilo|unidad|litro)\b.*"
    r"|(?!docena|media|cien)[a-záéíóúñ]+(?: de)? \(?\d+(?:,\d+)? ?(?:kilos?|unidades|gramos|grs|litros?|ml)\)?"
    r"(?: [a-záéíóúñ]+)?(?: \(volumen en unidades\))?)$"
)


def read_reviewed() -> pd.DataFrame:
    return pd.read_csv(REVIEWED_FILE, dtype=str, keep_default_na=False)


def is_plain_package(unit: str) -> bool:
    return bool(PLAIN_PACKAGE.match(unit.lower()))


def read_source_units(database_file: Path = queries.DATABASE_FILE) -> pd.DataFrame | None:
    """The units the last load saw; None on a base published before the table (D-524)."""
    try:
        return queries.run_sql("SELECT * FROM source_unit ORDER BY row_count DESC, unit", database_file)
    except duckdb.Error:
        return None


def find_unclassified(units: pd.DataFrame, reviewed: pd.DataFrame | None = None) -> pd.DataFrame:
    """The units of the source without a reading reviewed by hand. A unit that gets a price without being a plain package
    could publish a wrong figure: it stops the load (tests/test_unit_review.py)."""
    known = set((read_reviewed() if reviewed is None else reviewed)["unit"])
    new = units[~units["unit"].isin(known)].copy()
    new["priced"] = new["normalized_unit"].notna()
    new["stops_the_load"] = new["priced"] & ~new["unit"].map(is_plain_package)
    return new


def summarize(database_file: Path = queries.DATABASE_FILE) -> dict[str, Any]:
    """What «Catálogo de controles» and the «Informe semanal» say about the units."""
    reviewed = read_reviewed()
    units = read_source_units(database_file)
    return {
        "reviewed": len(reviewed),
        "known": units is not None,
        "seen": None if units is None else units["unit"].nunique(),
        "new": [] if units is None else find_unclassified(units, reviewed).to_dict("records"),
    }
