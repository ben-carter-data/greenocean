"""Performance budget of the named queries (D-323): every query of bi/queries.sql answers in less than a second on the
served database, the median of three runs. Since D-330 time is no longer a quality indicator of docs/calidad: the test
stays, with the budget the author approved in D-323. Since D-341 it carries the marker «rendimiento» and the CI leaves it
out, because shared runners are not a stable place to measure speed; locally: pytest -m rendimiento."""

import statistics
import time

import pytest

from bi import queries

# region Constants
BUDGET = 1.0  # seconds a query, approved in D-323
# endregion


# region Performance budget of the named queries
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
        # the runs of the suite, not its install; D-555: also inside a step of several lines
        runs = [line for line in text.splitlines() if "pytest -q" in line]
        assert runs and all('not rendimiento"' in line for line in runs), workflow
    # D-366: the weekly load runs only the data and pipeline tests; a screen test never stops the data.
    load = (root / ".github" / "workflows" / "semanal.yml").read_text(encoding="utf-8")
    assert [line.strip() for line in load.splitlines() if "run: pytest" in line] == [
        'run: pytest -q -m "datos and not rendimiento"'
    ]
    from tests import conftest

    from tests import code_shape

    for name in conftest.DATA_FILES:  # no screen test among the data ones
        tree = code_shape.file_tree(root / "tests" / f"{name}.py")
        assert not code_shape.uses(tree, "AppTest") and not code_shape.uses(tree, "i18n_audit"), name
        assert not [module for module in code_shape.imports(tree) if module.startswith("streamlit.testing")], name
    script = code_shape.file_tree(root / "scripts" / "medir_calidad.py")
    assert code_shape.has_sequence(script, ["-m", "not rendimiento"])
    # The count of tests the indicator divides by is taken with the same filter, or the ones left out count as failures.
    assert code_shape.has_sequence(script, ["--collect-only", "-q", "-m", "not rendimiento"])


# endregion
