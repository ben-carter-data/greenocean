"""Measures the project against the quality method of the panel's «Método y calidad» page (D-320).

Every number of docs/calidad/medicion.json comes from a real run of a tool, with the command that produced it. A tool
that is not installed, or a check that cannot run here, is written as «no verificado», never as a guess.

Usage (the quality tools live in a virtual environment of their own, outside the project):
    python scripts/medir_calidad.py --tools /path/to/venv/bin
"""

import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# region Constants
CODE = ["bi", "etl", "agent"]
CRITICAL_MODULES = [
    "etl/etl.py",
    "etl/bronze.py",
    "etl/ine.py",
    "etl/pipeline.py",
    "bi/queries.py",
    "bi/alerts.py",
    "bi/overview.py",
    "bi/inflation_view.py",
    "bi/control.py",
    "bi/served_database.py",
    "bi/quality.py",
]
TYPED_MODULES = [
    "etl/etl.py",
    "etl/bronze.py",
    "etl/ine.py",
    "etl/pipeline.py",
    "bi/queries.py",
    "bi/alerts.py",
    "bi/overview.py",
    "bi/inflation_view.py",
    "bi/control.py",
    "bi/served_database.py",
]
NOT_VERIFIED = "no verificado"
SECRET_NAME = re.compile(
    r'(SECRET|TOKEN|CODE)[A-Z_]*\s*=\s*"[A-Z_]+"|secretos|st\.secrets|"Secrets"|FAKE', re.IGNORECASE
)
# endregion


# region Variables
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "calidad" / "medicion.json"
SECRETS_BASELINE = ROOT / ".secrets.baseline"
# endregion


# region Running the tools
def run(command, cwd=ROOT, check=False):
    """The output of one command, stdout and stderr together; never raises on a non-zero exit."""
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return done.returncode, (done.stdout + done.stderr)


def tool(tools, name):
    path = Path(tools) / name
    return str(path) if path.exists() else None


def count_formatting(output):
    """(files to reformat, files already formatted) from `ruff format --check`, which leaves out a count that is zero."""
    pending = re.search(r"(\d+) files? would be reformatted", output)
    done = re.search(r"(\d+) files? already formatted", output)
    if not pending and not done:
        return None, None
    return int(pending.group(1)) if pending else 0, int(done.group(1)) if done else 0


# endregion


# region Code measures
def measure_ruff(tools):
    """The rules E, F and W of pyproject.toml, which leaves out E501; the lines over 120 columns are counted apart, so the
    baseline (measured with E501 inside) and every later measurement compare the same rules."""
    binary = tool(tools, "ruff")
    if not binary:
        return {"estado": NOT_VERIFIED}
    command = [binary, "check", *CODE, "tests", "--select", "E,F,W", "--output-format", "json"]
    _, out = run(command)
    by_code = {}
    for finding in json.loads(out):
        by_code[finding["code"]] = by_code.get(finding["code"], 0) + 1
    _, long_lines = run([binary, "check", *CODE, "tests", "--select", "E501", "--output-format", "json"])
    by_code["E501"] = len(json.loads(long_lines))
    _, formatted = run([binary, "format", "--check", *CODE, "tests"])
    pending, done = count_formatting(formatted)
    return {
        "orden": " ".join(command[:-2]),
        "version": run([binary, "--version"])[1].strip(),
        "errores": sum(by_code.values()),
        "por_codigo": by_code,
        "errores_sin_largo_de_linea": sum(count for code, count in by_code.items() if code != "E501"),
        "formato": {
            "orden": f"ruff format --check {' '.join(CODE)} tests",
            "por_reformatear": pending,
            "ya_formateados": done,
        },
    }


def measure_mypy(tools, python=None):
    binary = tool(tools, "mypy")
    if not binary:
        return {"estado": NOT_VERIFIED}
    command = [binary, *TYPED_MODULES, "--ignore-missing-imports", "--follow-imports=silent", "--no-error-summary"]
    if python:
        # D-330: with the project's dependencies in sight, as in CI; without them mypy missed a real error.
        command += ["--python-executable", python]
    _, out = run(command)
    errors = [line for line in out.splitlines() if ": error:" in line]
    _, deep = run(command + ["--check-untyped-defs"])
    deep_errors = [line for line in deep.splitlines() if ": error:" in line]
    per_module = {}
    for line in deep_errors:
        module = line.split(":")[0]
        per_module[module] = per_module.get(module, 0) + 1
    annotated = typed = 0
    for module in TYPED_MODULES:
        for node in ast.walk(ast.parse((ROOT / module).read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef):
                typed += 1
                annotated += 1 if node.returns is not None else 0
    return {
        "orden": "mypy " + " ".join(TYPED_MODULES) + " --ignore-missing-imports --follow-imports=silent",
        "version": run([binary, "--version"])[1].strip(),
        "modulos": len(TYPED_MODULES),
        "errores": len(errors),
        "errores_revisando_cuerpos_sin_tipos": len(deep_errors),
        "por_modulo": per_module,
        "funciones": typed,
        "con_tipo_de_retorno": annotated,
    }


def run_suite_with_coverage(python, report):
    """The whole suite here, with coverage written to `report`: (exit code, passed, skipped)."""
    command = [
        python,
        "-m",
        "pytest",
        "-q",
        "-m",
        "not rendimiento",  # D-341: speed budgets run locally, never on a shared runner
        "-p",
        "no:cacheprovider",
        *[f"--cov={name}" for name in CODE],
        f"--cov-report=json:{report}",
    ]
    code, out = run(command)
    match = re.search(r"(\d+) passed(?:, (\d+) skipped)?", out)
    return code, int(match.group(1)) if match else None, int(match.group(2) or 0) if match else None


def combine_group_coverage(python, folder, report):
    """D-555: the coverage the CI groups of pruebas.yml already measured, combined into `report`, so the suite does not
    run a third time: (exit code, passed, skipped) from their .coverage.N and junit-N.xml files, or None without them."""
    parts = sorted(str(part) for part in Path(folder).rglob(".coverage.*"))
    if not parts:
        return None
    data = Path(report).with_suffix(".data")
    run([python, "-m", "coverage", "combine", "--keep", f"--data-file={data}", *parts])
    code, _ = run([python, "-m", "coverage", "json", f"--data-file={data}", "-o", str(report), "-q"])
    counts = {"tests": 0, "skipped": 0, "failures": 0, "errors": 0}
    for junit in sorted(Path(folder).rglob("junit-*.xml")):
        suite = re.search(r"<testsuite\b[^>]*>", junit.read_text(encoding="utf-8"))
        for name in counts:
            found = re.search(rf'\b{name}="(\d+)"', suite.group(0)) if suite else None
            counts[name] += int(found.group(1)) if found else 0
    broken = counts["failures"] + counts["errors"]
    return int(code or broken > 0), counts["tests"] - counts["skipped"] - broken, counts["skipped"]


def measure_coverage(python, groups=None):
    with tempfile.TemporaryDirectory() as folder:
        report = Path(folder) / "coverage.json"
        combined = combine_group_coverage(python, groups, report) if groups else None
        code, passed, skipped = combined or run_suite_with_coverage(python, report)
        if not report.exists():
            return {"estado": NOT_VERIFIED, "motivo": "pytest-cov no está instalado en el entorno del proyecto"}
        data = json.loads(report.read_text())
    files = data["files"]
    covered = sum(files[name]["summary"]["covered_lines"] for name in CRITICAL_MODULES if name in files)
    statements = sum(files[name]["summary"]["num_statements"] for name in CRITICAL_MODULES if name in files)
    return {
        "orden": 'pytest -q -m "not rendimiento" '
        + " ".join(f"--cov={name}" for name in CODE)
        + (" (los grupos de pruebas.yml, combinados)" if combined else ""),
        "pruebas_ok": passed,
        "pruebas_omitidas": skipped,
        "salida": code,
        "total": round(data["totals"]["percent_covered"], 1),
        "logica_critica": round(covered / statements * 100, 1) if statements else None,
        "modulos_criticos": {
            name: round(files[name]["summary"]["percent_covered"], 1) for name in CRITICAL_MODULES if name in files
        },
        "modulos": {
            name: round(item["summary"]["percent_covered"], 1)
            for name, item in files.items()
            if item["summary"]["num_statements"]
        },
    }


def measure_bandit(tools):
    binary = tool(tools, "bandit")
    if not binary:
        return {"estado": NOT_VERIFIED}
    _, out = run([binary, "-r", *CODE, "-f", "json", "-q"])
    data = json.loads(out[out.index("{") :])
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    kinds = {}
    for item in data["results"]:
        counts[item["issue_severity"]] += 1
        kinds[item["test_id"]] = kinds.get(item["test_id"], 0) + 1
    return {
        "orden": "bandit -r bi etl agent",
        "version": run([binary, "--version"])[1].splitlines()[0].strip(),
        "alta": counts["HIGH"],
        "media": counts["MEDIUM"],
        "baja": counts["LOW"],
        "por_regla": kinds,
    }


def measure_audit(tools):
    binary = tool(tools, "pip-audit")
    if not binary:
        return {"estado": NOT_VERIFIED}
    result = {}
    for name in ("requirements.txt", "requirements-pipeline.txt"):
        code, out = run([binary, "-r", name, "--progress-spinner", "off"])
        advisories = len([line for line in out.splitlines() if re.search(r"GHSA-|PYSEC-|CVE-", line)])
        if "No known vulnerabilities found" in out:
            result[name] = {"vulnerabilidades": 0}
        elif advisories:
            result[name] = {"vulnerabilidades": advisories}
        else:
            result[name] = {
                "estado": NOT_VERIFIED,
                "motivo": "las dependencias no se pueden resolver con este Python (dbt pide 3.11 o 3.12)",
            }
    return {
        "orden": "pip-audit -r <requirements>",
        "version": run([binary, "--version"])[1].strip(),
        "archivos": result,
    }


# endregion


# region Secrets
def reviewed_secret_hashes():
    """The candidates the author reviewed and marked as not secret (`"is_secret": false`) in .secrets.baseline."""
    if not SECRETS_BASELINE.exists():
        return set()
    results = json.loads(SECRETS_BASELINE.read_text(encoding="utf-8"))["results"]
    return {item["hashed_secret"] for items in results.values() for item in items if item.get("is_secret") is False}


def classify_secret_candidates(results):
    """What detect-secrets proposes, sorted by what each candidate is: a SHA-256 of a file (the manifest and the pointer of
    the served database), the name of a secret or a word in a text, never its value, or a candidate already reviewed in
    .secrets.baseline. What fits none stays unclassified."""
    reviewed = reviewed_secret_hashes()
    false, open_ = 0, 0
    for name, items in results.items():
        lines = (ROOT / name).read_text(encoding="utf-8").splitlines()
        for item in items:
            text = lines[item["line_number"] - 1]
            if item["hashed_secret"] in reviewed:
                false += 1
            elif item["type"].startswith("Hex") and re.search(r'"[0-9a-f]{64}"', text):
                false += 1
            elif item["type"].startswith("Secret") and SECRET_NAME.search(text):
                false += 1
            else:
                open_ += 1
    return {"falsos_positivos": false, "sin_clasificar": open_}


def measure_secrets(tools):
    binary = tool(tools, "detect-secrets")
    if not binary:
        return {"estado": NOT_VERIFIED}
    _, tracked = run(["git", "ls-files"])
    # .secrets.baseline is detect-secrets' own list of reviewed candidates: hashes, never a value.
    files = [
        name
        for name in tracked.split()
        if not name.endswith((".png", ".jpg", ".pem", ".svg"))
        and name != SECRETS_BASELINE.name
        and (ROOT / name).is_file()
    ]
    _, out = run([binary, "scan", *files])
    results = json.loads(out[out.index("{") :])["results"]
    hits = {name: [item["type"] for item in items] for name, items in results.items()}
    reviewed = classify_secret_candidates(results)
    _, history = run(
        [
            "git",
            "log",
            "--all",
            "-p",
            "-G",
            r"(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{50,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY)",
            "--oneline",
            "--",
            "bi",
            "etl",
            "agent",
            ".github",
        ]
    )
    return {
        "orden": "detect-secrets scan $(git ls-files)",
        "version": run([binary, "--version"])[1].strip(),
        "archivos_revisados": len(files),
        "candidatos": sum(len(items) for items in hits.values()),
        "por_archivo": hits,
        "falsos_positivos": reviewed["falsos_positivos"],
        "sin_clasificar": reviewed["sin_clasificar"],
        "historial_con_patrones_de_claves": len(
            [line for line in history.splitlines() if re.match(r"^[0-9a-f]{7,} ", line)]
        ),
        "nota": "gitleaks no está instalado en este equipo; se usó detect-secrets y una búsqueda de patrones en el historial",
    }


# endregion


# region Data and tests measures
def measure_dbt():
    models = {
        layer: len(list((ROOT / "dbt" / "models" / layer).rglob("*.sql")))
        for layer in ("staging", "intermediate", "marts")
    }
    result = {"modelos_por_capa": models, "pruebas_sql_propias": len(list((ROOT / "dbt" / "tests").rglob("*.sql")))}
    database = ROOT / "etl" / "datos.duckdb"
    if not database.exists():
        return {**result, "ultima_construccion": NOT_VERIFIED}
    import duckdb

    connection = duckdb.connect(str(database), read_only=True)
    try:
        status = dict(connection.execute("SELECT status, count(*) FROM dbt_result GROUP BY status").fetchall())
        tests = {name: count for name, count in status.items() if name != "success"}
        result["ultima_construccion"] = {
            "modelos_ok": int(status.get("success", 0)),
            "pruebas_ok": int(tests.get("pass", 0)),
            "pruebas_total": int(sum(tests.values())),
        }
    finally:
        connection.close()
    return result


def measure_data(python):
    """The quality of the real data, read from the served database by the project's own code (D-323): of the latest
    week's prices that also had a price the week before, the share with a valid comparison in the same regions (D-475;
    the prices that reappear after a gap are counted apart and never alert), the regions and channels present in each
    of the 8 weeks before that are missing in the latest one, the share of the latest week's prices marked ATIPICO, the
    share of the series seen in the last 12 weeks that have a price in the latest one, and how old the latest data and
    the latest load are."""
    code = r"""
import json, datetime
import pandas as pd
from bi import queries, alerts, overview
prices = queries.run_query("k6_national_weekly_price")
variations = alerts.add_weekly_variation(prices.copy())
key = ["product", "variety", "quality", "channel", "normalized_unit"]
variations = variations.sort_values(key + ["week_start"])
gap = (variations["week_start"] - variations.groupby(key)["week_start"].shift(1)).dt.days
variations["had_last_week"] = gap == 7
week = variations["week_start"].max()
now = variations[variations["week_start"] == week]
base = now[now["had_last_week"]]
valid = base["variation"].notna().sum()
weeks = sorted(prices["week_start"].unique())
recent = prices[prices["week_start"].isin(weeks[-12:])]
seen = recent[key].drop_duplicates()
latest = prices[prices["week_start"] == weeks[-1]][key].drop_duplicates()
present = queries.run_sql(
    "SELECT w.week_start, r.region, c.channel FROM weekly_price w JOIN dim_region r USING (region_id) "
    "JOIN dim_channel c USING (channel_id) WHERE w.flag IS NULL GROUP BY ALL"
)
last_weeks = sorted(present["week_start"].unique())
def missing(column):
    steady = set.intersection(*[set(present.loc[present["week_start"] == w, column]) for w in last_weeks[-9:-1]])
    return sorted(steady - set(present.loc[present["week_start"] == last_weeks[-1], column]))
regions, channels = missing("region"), missing("channel")
flags = queries.run_sql(
    "SELECT count(*) AS precios, count(*) FILTER (WHERE flag = 'ATIPICO') AS atipicos FROM weekly_price "
    "WHERE week_start = (SELECT max(week_start) FROM weekly_price)"
).iloc[0]
runs = queries.run_sql("SELECT max(started_at) AS last FROM etl_run")
load = queries.run_sql("SELECT rows_read, rows_rejected FROM etl_run ORDER BY run_id DESC LIMIT 1").iloc[0]
today = datetime.date.today()
last_week = datetime.date.fromisoformat(str(weeks[-1])[:10])
last_load = datetime.date.fromisoformat(str(runs["last"][0])[:10])
print(json.dumps({"semana": str(weeks[-1])[:10], "precios_semana": int(len(now)),
                  "con_semana_anterior": int(len(base)), "con_comparacion": int(valid),
                  "pct_comparacion": round(valid / len(base) * 100, 1) if len(base) else None,
                  "reapariciones": int(len(now) - len(base)),
                  "regiones_ausentes": regions, "canales_ausentes": channels,
                  "regiones_canales_ausentes": len(regions) + len(channels),
                  "precios_atipicos": int(flags["atipicos"]), "precios_semana_base": int(flags["precios"]),
                  "pct_atipicos": round(int(flags["atipicos"]) / int(flags["precios"]) * 100, 3) if int(flags["precios"]) else None,
                  "series_activas": int(len(seen)),
                  "series_con_dato": int(len(latest.merge(seen))), "pct_series_con_dato": round(len(latest.merge(seen)) / len(seen) * 100, 1),
                  "dias_desde_ultima_semana": (today - last_week).days - 6, "dias_desde_ultima_carga": (today - last_load).days,
                  "filas_leidas": int(load["rows_read"]), "filas_rechazadas": int(load["rows_rejected"]),
                  "pct_rechazadas": round(int(load["rows_rejected"]) / int(load["rows_read"]) * 100, 3),
                  "medido": str(today)}))
"""
    status, out = run([python, "-c", code])
    try:
        return {
            "orden": "python scripts/medir_calidad.py (función measure_data)",
            **json.loads(out.strip().splitlines()[-1]),
        }
    except (ValueError, IndexError):
        return {"estado": NOT_VERIFIED, "salida": out[-300:]}


def measure_tests(python):
    # D-341: the same tests the coverage run executes; the speed budgets left out are not failures.
    _, out = run([python, "-m", "pytest", "--collect-only", "-q", "-m", "not rendimiento"])
    match = re.search(r"(\d+) tests? collected", out) or re.search(r"^(\d+)/", out, re.MULTILINE)
    count = len([line for line in out.splitlines() if "::" in line])
    files = len(list((ROOT / "tests").glob("test_*.py")))
    return {"pruebas": count or (int(match.group(1)) if match else None), "archivos_de_prueba": files}


# endregion


# region The measurement from start to end
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tools", required=True, help="bin folder of the virtual environment with ruff, mypy, bandit, ..."
    )
    parser.add_argument("--python", default=str(ROOT / ".venv" / "bin" / "python"), help="the project's own Python")
    parser.add_argument("--output", default=str(OUTPUT), help="where to write the JSON")
    parser.add_argument(
        "--coverage",
        help="folder with the .coverage.N and junit-N.xml of the CI groups (D-555); without it, the suite runs",
    )
    arguments = parser.parse_args()
    _, commit = run(["git", "rev-parse", "--short", "HEAD"])
    report = {
        "generado": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "commit": commit.strip(),
        "python": sys.version.split()[0],
        # D-330: only the quality of the published data and of the code that treats it.
        "ruff": measure_ruff(arguments.tools),
        "mypy": measure_mypy(arguments.tools, arguments.python),
        "cobertura": measure_coverage(arguments.python, arguments.coverage),
        "bandit": measure_bandit(arguments.tools),
        "pip_audit": measure_audit(arguments.tools),
        "secretos": measure_secrets(arguments.tools),
        "dbt": measure_dbt(),
        "pruebas": measure_tests(arguments.python),
        "datos": measure_data(arguments.python),
    }
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"escrito {output}")


# endregion


# region Run
if __name__ == "__main__":
    main()
# endregion
