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


def test_d275_each_signal_hangs_from_the_stage_where_it_is_born_on_the_side_of_its_reader():
    page = monitoring.build_monitoring_html(charts.get_palette(charts.MODE_DARK))
    stages = [key for key, *_ in monitoring.STAGES]
    for key, _, origin, name, records, where, who, produced_by in monitoring.SIGNALS:
        card = page.split(f'id="signal-{key}"')[1].split("</div>")[0]
        classes = page.split(f'id="signal-{key}"')[0].rsplit("<div", 1)[1].split('"')[1].split()
        assert "card" in classes and who in classes  # its colour is its reader's
        assert name in card and where in card and produced_by in card and records in card  # what it records: on hover
        if key == monitoring.EVERY_STEP:
            continue  # born at every step: the band under the run
        assert monitoring.STAGE_OF_SIGNAL[key] in stages
        row = int(card.split("grid-row:")[1].split(";")[0])
        assert row == (1 if who == "panel" else 5)  # above the run what the panel shows, below what only the author sees
    assert set(monitoring.STAGE_OF_SIGNAL) | {monitoring.EVERY_STEP} == {signal[0] for signal in monitoring.SIGNALS}
    assert {signal[6] for signal in monitoring.SIGNALS} == {"panel", "autor"}
    assert "<script" not in page and page.count('class="stage"') == len(monitoring.STAGES)
