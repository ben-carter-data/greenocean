"""D-366: which tests guard the data. The weekly load runs only these (pytest -m datos) before publishing; the tests
of the screens (pages, translations, AppTest, documents) run in the CI of every push and never stop the data from being
published."""

from pathlib import Path

import pytest

# The data and the pipeline: ingestion, ETL rules, dbt figures, the served database, the publication gate and the audit.
DATA_FILES = {
    "test_agent",
    "test_alerts",
    "test_data_audit",
    "test_dim_date",
    "test_etl",
    "test_etl_run",
    "test_ingesta",
    "test_ipc_audit",
    "test_lag",
    "test_late_sources",
    "test_migration_parity",
    "test_pipeline_gate",
    "test_profile_years",
    "test_queries",
    "test_quality",
    "test_quality_audit",
    "test_raw_load",
    "test_reconciliation",
    "test_report",
    "test_schema",
    "test_served_database",
}


def pytest_collection_modifyitems(items):
    for item in items:
        if Path(str(item.fspath)).stem in DATA_FILES:
            item.add_marker(pytest.mark.datos)
