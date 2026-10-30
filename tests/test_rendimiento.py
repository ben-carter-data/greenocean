"""Performance budget of the named queries (D-323): every query of bi/queries.sql answers in less than a second on the
served database, the median of three runs. Since D-330 time is no longer a quality indicator of docs/calidad: the test
stays, with the budget the author approved in D-323. Since D-341 it carries the marker «rendimiento» and the CI leaves it
out, because shared runners are not a stable place to measure speed; locally: pytest -m rendimiento."""

import statistics
import time

import pytest

from bi import queries

BUDGET = 1.0  # seconds a query, approved in D-323


@pytest.mark.rendimiento
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


def test_d341_no_shared_runner_measures_speed_the_ci_the_weekly_load_and_the_quality_measure_leave_it_out():
    """The three places that run the suite on GitHub's shared runners: the CI, the weekly load and the quality measure
    (F-10, its third occurrence). Each leaves the speed budgets out; they run locally with pytest -m rendimiento."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for workflow in ("pruebas.yml", "semanal.yml"):
        text = (root / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
        runs = [line for line in text.splitlines() if "run: pytest" in line]  # the runs of the suite, not its install
        assert runs and all('-m "not rendimiento"' in line for line in runs), workflow
    script = (root / "scripts" / "medir_calidad.py").read_text(encoding="utf-8")
    assert '"-m",\n            "not rendimiento",' in script
