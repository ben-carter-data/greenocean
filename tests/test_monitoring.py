"""Monitoreo y observabilidad (D-249): every signal drawn exists in the file that produces it."""
from pathlib import Path

import duckdb
import pytest

from bi import charts, control, monitoring, queries

ROOT = Path(__file__).resolve().parent.parent


def test_every_signal_names_a_file_that_exists_and_produces_it():
    evidence = {"etl_run": "INSERT INTO etl_run", "dbt_result": "INSERT INTO dbt_result", "agent_log": "LOG_DIR",
                "actions_log": "name: semanal", "email": "name: semanal", "issue": "Informe semanal",
                "token": "TOKEN_WARNING_DAYS", "hashes": "SHA-256 distinto"}
    assert [signal[0] for signal in monitoring.SIGNALS] == list(evidence)
    for key, *_, produced_by in monitoring.SIGNALS:
        source = (ROOT / produced_by).read_text(encoding="utf-8")
        assert evidence[key] in source, (key, produced_by)
    assert control.TOKEN_WARNING_DAYS == 14  # the warning the view names


@pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")
def test_the_two_tables_the_panel_reads_are_in_the_served_database():
    with duckdb.connect(str(queries.DATABASE_FILE), read_only=True) as connection:
        tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
    assert {"etl_run", "dbt_result"} <= tables


def test_the_view_draws_one_row_per_signal_with_its_reader_and_no_script():
    page = monitoring.build_monitoring_html(charts.get_palette(charts.MODE_DARK))
    for key, *_ in monitoring.SIGNALS:
        assert f'id="signal-{key}"' in page
    assert {signal[6] for signal in monitoring.SIGNALS} == {"panel", "autor"}
    assert "<script" not in page and page.count('class="line"') == 3 * len(monitoring.SIGNALS)
