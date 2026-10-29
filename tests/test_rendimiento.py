"""Performance budget of the named queries (D-323): every query of bi/queries.sql answers in less than a second on the
served database, the median of three runs. Since D-330 time is no longer a quality indicator of docs/calidad: the test
stays, with the budget the author approved in D-323."""

import statistics
import time

import pytest

from bi import queries

BUDGET = 1.0  # seconds a query, approved in D-323


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
