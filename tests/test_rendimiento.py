"""Performance budget of the named queries (D-323): every query of bi/queries.sql answers in less than the budget of
docs/calidad/metas.json on the served database, the median of three runs. The page budget is checked in a browser by
tests/medicion/calidad.cjs and scripts/verificar_calidad.py."""

import json
import statistics
import time
from pathlib import Path

import pytest

from bi import queries

BUDGET = json.loads(
    (Path(__file__).resolve().parent.parent / "docs" / "calidad" / "metas.json").read_text(encoding="utf-8")
)["segundos_por_consulta"]["max"]


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")
@pytest.mark.parametrize("name", list(queries.load_queries()))
def test_d323_each_named_query_answers_within_its_budget(name):
    queries.run_query(name)  # the first run warms the file cache, as the dashboard's would
    runs = []
    for _ in range(3):
        start = time.perf_counter()
        queries.run_query(name)
        runs.append(time.perf_counter() - start)
    assert statistics.median(runs) < BUDGET, f"{name}: {statistics.median(runs):.2f} s"
