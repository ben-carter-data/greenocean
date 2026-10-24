"""The attacks of the security review (D-199, D-200), kept as permanent tests: each one
must stay stopped by the barrier the «Seguridad» view names."""
import re
import subprocess
from pathlib import Path

import pytest

from bi import queries, security_map, sql_explorer

REPOSITORY = Path(__file__).resolve().parent.parent
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="etl/datos.duckdb is not built")
SECRET_TEXT = 'CONTROL_CODE = "secreto-de-prueba"'
FILE_ATTACKS = [
    "SELECT * FROM read_text('{path}')",
    "SELECT * FROM READ_TEXT ('{path}')",
    "SELECT * FROM read_csv_auto('{path}')",
    "SELECT * FROM sniff_csv('{path}')",
    "SELECT * FROM glob('{folder}/*')",
    "SELECT * FROM parquet_metadata('{path}')",
    "SELECT * FROM query_table('{path}')",
    "SELECT * FROM query('SELECT * FROM read_text(''{path}'')')",
    "SELECT * FROM query('SELECT * FROM rea' || 'd_text(''{path}'')')",
    "SELECT * FROM '{path}'",
    "SELECT * FROM \"{path}\"",
    "SELECT * FROM 'file://{path}'",
    "SELECT * FROM read/**/_text('{path}')",
    "WITH x AS (SELECT 1) SELECT * FROM read_text('{path}')",
    "SELECT * FROM read_text('https://example.com/robado')",
    "SELECT 1; COPY (SELECT 1) TO '{folder}/fuera.csv'",
    "SELECT * FROM (COPY (SELECT 1) TO '{folder}/fuera.csv')",
    "SELECT getenv('HOME')",
    "SELECT * FROM duckdb_extensions()",
]
ENGINE_ATTACKS = [
    "SELECT * FROM read_text('{path}')",
    "SET enable_external_access = true",
    "SET lock_configuration = false",
    "COPY (SELECT 1) TO '{folder}/fuera.csv'",
    "ATTACH '{folder}/otra.db'",
    "INSTALL httpfs",
    "LOAD httpfs",
    "CREATE TABLE t AS SELECT 1",
    "DELETE FROM weekly_price",
]


@pytest.fixture
def secret_file(tmp_path):
    path = tmp_path / "secrets.toml"
    path.write_text(SECRET_TEXT)
    return path


@needs_database
@pytest.mark.parametrize("attack", FILE_ATTACKS)
def test_the_filter_and_the_engine_stop_every_attack_on_the_server_files(attack, secret_file):
    sql = attack.format(path=secret_file, folder=secret_file.parent)
    try:
        result = sql_explorer.run_user_query(sql, timeout=5)
    except Exception:
        result = None
    assert result is None or "secreto-de-prueba" not in result.rows.to_string()
    assert not (secret_file.parent / "fuera.csv").exists()


@needs_database
@pytest.mark.parametrize("attack", ENGINE_ATTACKS)
def test_the_engine_refuses_even_if_the_filter_is_bypassed(attack, secret_file):
    connection = sql_explorer.open_explorer_connection()
    try:
        with pytest.raises(Exception):
            connection.execute(attack.format(path=secret_file, folder=secret_file.parent)).fetchall()
    finally:
        connection.close()
    assert not (secret_file.parent / "fuera.csv").exists() and not (secret_file.parent / "otra.db").exists()


def test_no_secret_is_tracked_by_git():
    ignored = (REPOSITORY / ".gitignore").read_text()
    assert ".streamlit/secrets.toml" in ignored and ".env" in ignored
    tracked = subprocess.run(["git", "ls-files"], cwd=REPOSITORY, capture_output=True, text=True).stdout.split()
    assert ".streamlit/secrets.toml" not in tracked
    token = re.compile(r"(ghp_|gho_|github_pat_)[A-Za-z0-9_]{20,}")
    for name in tracked:
        path = REPOSITORY / name
        if path.suffix in {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt", ".cfg", ".sql"} and path.is_file():
            assert not token.search(path.read_text(errors="ignore")), name


def test_the_weekly_job_has_least_privilege():
    workflow = (REPOSITORY / ".github" / "workflows" / "semanal.yml").read_text()
    block = workflow.split("permissions:", 1)[1].split("\n\n", 1)[0]
    granted = dict(re.findall(r"(\w[\w-]*):\s*(\w+)", block))
    assert granted == {"contents": "write", "issues": "write"}


def test_every_control_of_the_map_points_to_a_test_that_exists():
    for number, title, *_, tests, verifiable in security_map.CONTROLS:
        assert bool(tests) == verifiable, title  # only the platform's own sign-in has no test, and it says so
        for test in tests:
            path, name = test.split("::")
            assert f"def {name}(" in (REPOSITORY / path).read_text(), test


def test_d249_the_security_architecture_reads_threat_mitigation_verification_and_asset_with_the_improvement_loop():
    from bi import charts
    page = security_map.build_security_html(charts.get_palette("Vantablack"))
    assert [name for name, _ in security_map.COLUMNS] == ["Amenaza · OWASP", "Mitigación", "Verificación", "Activo protegido"]
    numbers = {control[0] for control in security_map.CONTROLS}
    assert numbers == set(range(1, 8))
    used = set()
    for tid, title, owasp, controls, cases, asset in security_map.THREATS:
        assert f'id="row-{tid}"' in page and f'id="tip-{tid}"' in page and title in page
        assert all(code in security_map.OWASP for code in owasp.split(" · ")), tid
        used |= set(controls)
        # a threat is verified by tests exactly when its controls have tests
        assert bool(cases) == all(security_map.CONTROLS[n - 1][7] for n in controls), tid
    assert used == numbers  # every control mitigates some threat
    assert [step[0] for step in security_map.LOOP] == ["Revisar", "Atacar", "Corregir", "Probar", "Repetir"]
    assert "Mejora continua" in page and "cada revisión vuelve a empezar" in page
    assert page.count('class="num declared"') == 1 and "No verificable aquí" in page
    assert "<script" not in page and "secreto-de-prueba" not in page and "ghp_" not in page


def test_d249_the_map_says_what_the_author_decided_about_the_code_and_the_sql_studio():
    controls = {control[1]: control for control in security_map.CONTROLS}
    code = controls["Clave de control"]
    assert "evita ejecuciones accidentales" in code[2] and "hmac.compare_digest" in code[4]
    assert "No hay límite de intentos" in code[4]  # the accepted risk is stated, not hidden
    sql = controls["SQL público con límites"]
    assert "abierto a cualquier visitante" in sql[3] and "10 segundos" in sql[4] and "5.000 filas" in sql[4]
    assert sql_explorer.TIMEOUT_SECONDS == 10 and sql_explorer.ROW_LIMIT == 5000 and sql_explorer.MEMORY_LIMIT == "1GB"
    declared = controls["Inicio de sesión externo"]
    assert not declared[7] and "no verificable" in declared[2]
