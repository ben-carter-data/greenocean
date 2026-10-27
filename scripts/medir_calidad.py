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

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "calidad" / "medicion.json"
CODE = ["bi", "etl", "agent"]
LINE_LENGTH = 120
MAX_COMPLEXITY = 10
MAX_FUNCTION_LINES = 50
MAX_PARAMETERS = 5
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


def python_files():
    return [
        path for folder in CODE for path in sorted((ROOT / folder).rglob("*.py")) if "__pycache__" not in path.parts
    ]


def measure_functions():
    """Length and parameters of every function of the code (tests excluded), from the syntax tree."""
    long, many, total, longest = [], [], 0, (0, "")
    for path in python_files():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total += 1
                length = node.end_lineno - node.lineno + 1
                name = f"{path.relative_to(ROOT)}:{node.name}"
                if length > MAX_FUNCTION_LINES:
                    long.append((length, name))
                if length > longest[0]:
                    longest = (length, name)
                args = node.args
                count = (
                    len(args.args)
                    + len(args.kwonlyargs)
                    - (1 if args.args and args.args[0].arg in ("self", "cls") else 0)
                )
                if count > MAX_PARAMETERS:
                    many.append((count, name))
    lines = sum(len(path.read_text(encoding="utf-8").splitlines()) for path in python_files())
    return {
        "funciones": total,
        "lineas_de_codigo": lines,
        "mas_de_50_lineas": len(long),
        "mas_largas": sorted(long, reverse=True)[:5],
        "mas_de_5_parametros": len(many),
        "mas_parametros": sorted(many, reverse=True)[:5],
        "mas_larga": longest,
    }


def measure_complexity(tools):
    binary, radon = tool(tools, "ruff"), tool(tools, "radon")
    result = {}
    if binary:
        command = [
            binary,
            "check",
            *CODE,
            "--select",
            "C901",
            "--config",
            f"lint.mccabe.max-complexity={MAX_COMPLEXITY}",
            "--output-format",
            "json",
        ]
        _, out = run(command)
        over = json.loads(out)
        worst = sorted(
            (
                (
                    int(re.search(r"\((\d+) >", item["message"]).group(1)),
                    item["filename"].replace(str(ROOT) + "/", ""),
                    re.search(r"`(\w+)`", item["message"]).group(1),
                )
                for item in over
            ),
            reverse=True,
        )
        result.update(
            {
                "orden": "ruff check bi etl agent --select C901 --config lint.mccabe.max-complexity=10",
                "funciones_sobre_10": len(over),
                "mas_complejas": worst[:5],
            }
        )
    else:
        result["estado"] = NOT_VERIFIED
    if radon:
        _, out = run([radon, "cc", *CODE, "-a", "-s"])
        match = re.search(r"Average complexity: (\w) \(([\d.]+)\)", out)
        result["promedio_radon"] = {"nota": match.group(1), "valor": float(match.group(2))} if match else NOT_VERIFIED
    return result


def measure_dead_code(tools):
    binary = tool(tools, "vulture")
    if not binary:
        return {"estado": NOT_VERIFIED}
    _, out = run([binary, *CODE, "--min-confidence", "60"])
    functions = [
        line.split("unused function ")[1].split(" ")[0].strip("'")
        for line in out.splitlines()
        if "unused function" in line
    ]
    variables = sum(1 for line in out.splitlines() if "unused variable" in line or "unused attribute" in line)
    return {
        "orden": "vulture bi etl agent --min-confidence 60",
        "version": run([binary, "--version"])[1].strip(),
        "funciones_sin_uso": functions,
        "variables_o_atributos_sin_uso": variables,
    }


def measure_mypy(tools):
    binary = tool(tools, "mypy")
    if not binary:
        return {"estado": NOT_VERIFIED}
    command = [binary, *TYPED_MODULES, "--ignore-missing-imports", "--follow-imports=silent", "--no-error-summary"]
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


def measure_coverage(python):
    with tempfile.TemporaryDirectory() as folder:
        report = Path(folder) / "coverage.json"
        command = [
            python,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *[f"--cov={name}" for name in CODE],
            f"--cov-report=json:{report}",
        ]
        code, out = run(command)
        if not report.exists():
            return {"estado": NOT_VERIFIED, "motivo": "pytest-cov no está instalado en el entorno del proyecto"}
        data = json.loads(report.read_text())
    files = data["files"]
    covered = sum(files[name]["summary"]["covered_lines"] for name in CRITICAL_MODULES if name in files)
    statements = sum(files[name]["summary"]["num_statements"] for name in CRITICAL_MODULES if name in files)
    match = re.search(r"(\d+) passed(?:, (\d+) skipped)?", out)
    return {
        "orden": "pytest -q " + " ".join(f"--cov={name}" for name in CODE),
        "pruebas_ok": int(match.group(1)) if match else None,
        "pruebas_omitidas": int(match.group(2) or 0) if match else None,
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


SECRET_NAME = re.compile(
    r'(SECRET|TOKEN|CODE)[A-Z_]*\s*=\s*"[A-Z_]+"|secretos|st\.secrets|"Secrets"|FAKE', re.IGNORECASE
)


SECRETS_BASELINE = ROOT / ".secrets.baseline"


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


def measure_sql(tools):
    binary = tool(tools, "sqlfluff")
    if not binary:
        return {"estado": NOT_VERIFIED}
    config = (
        "[sqlfluff]\ndialect = duckdb\ntemplater = jinja\nmax_line_length = 120\n"
        "[sqlfluff:templater:jinja:macros]\nref = {% macro ref(name) %}{{ name }}{% endmacro %}\n"
        "source = {% macro source(group, name) %}{{ group }}_{{ name }}{% endmacro %}\n"
        "config = {% macro config() %}{% endmacro %}\n"
    )
    result = {"orden": "sqlfluff lint <ruta> --dialect duckdb", "version": run([binary, "--version"])[1].strip()}
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / ".sqlfluff"
        path.write_text(config)
        for label, target in (("bi/queries.sql", "bi/queries.sql"), ("dbt/models", "dbt/models")):
            code, out = run([binary, "lint", target, "--config", str(path), "-f", "json"])
            try:
                data = json.loads(out[out.index("[") :])
            except ValueError:
                result[label] = {"estado": NOT_VERIFIED, "salida": out.strip()[-200:]}
                continue
            violations = sum(len(item["violations"]) for item in data)
            by_code = {}
            for item in data:
                for violation in item["violations"]:
                    by_code[violation["code"]] = by_code.get(violation["code"], 0) + 1
            result[label] = {
                "archivos": len(data),
                "violaciones": violations,
                "principales": dict(sorted(by_code.items(), key=lambda pair: -pair[1])[:5]),
            }
    return result


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


def measure_dora():
    """Delivery metrics from the GitHub Actions history (public, without a key: 60 requests an hour), and from the loads the
    served database records. What GitHub does not answer stays «no verificado»."""
    import urllib.request

    result = {"cargas_registradas": None}
    database = ROOT / "etl" / "datos.duckdb"
    if database.exists():
        import duckdb

        connection = duckdb.connect(str(database), read_only=True)
        try:
            first, last, count = connection.execute(
                "SELECT min(started_at), max(started_at), count(*) FROM etl_run"
            ).fetchone()
            result.update({"cargas_registradas": int(count), "primera": str(first)[:10], "ultima": str(last)[:10]})
        finally:
            connection.close()
    repository = "cben6514-boop/greenocean"
    for workflow in ("semanal", "pruebas"):
        url = f"https://api.github.com/repos/{repository}/actions/workflows/{workflow}.yml/runs?per_page=100"
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "greenocean-quality"}), timeout=20
            ) as answer:
                runs = json.loads(answer.read())["workflow_runs"]
        except Exception as error:  # rate limit, renamed repository, no network
            result[workflow] = {"estado": NOT_VERIFIED, "motivo": str(error)[:80]}
            continue
        done = [run_ for run_ in runs if run_["conclusion"] in ("success", "failure")]
        result[workflow] = {
            "ejecuciones": len(done),
            "fallidas": sum(1 for run_ in done if run_["conclusion"] == "failure"),
        }
    return result


def measure_process():
    _, log = run(["git", "log", "--pretty=%s"])
    subjects = log.splitlines()
    conventional = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?!?: ")
    workflows = {path.name: path.read_text(encoding="utf-8") for path in (ROOT / ".github" / "workflows").glob("*.yml")}
    steps = {
        name: [
            tool
            for tool in (
                "pytest",
                "ruff",
                "mypy",
                "bandit",
                "pip-audit",
                "sqlfluff",
                "dbt parse",
                "dbt build",
                "gitleaks",
            )
            if tool in text
        ]
        for name, text in workflows.items()
    }
    return {
        "commits": len(subjects),
        "conventional_commits": sum(1 for subject in subjects if conventional.match(subject)),
        "pre_commit_configurado": (ROOT / ".pre-commit-config.yaml").exists(),
        "ci": steps,
    }


def measure_data(python):
    """The quality of the real data, read from the served database by the project's own code (D-323): the share of the
    latest week's prices that have a valid comparison with the week before, the share of the series seen in the last 12
    weeks that have a price in the latest one, and how old the latest data and the latest load are."""
    code = r"""
import json, datetime
from bi import queries, alerts, overview
prices = queries.run_query("k6_national_weekly_price")
variations = alerts.add_weekly_variation(prices.copy())
week = variations["week_start"].max()
now = variations[variations["week_start"] == week]
valid = now["variation"].notna().sum()
weeks = sorted(prices["week_start"].unique())
recent = prices[prices["week_start"].isin(weeks[-12:])]
key = ["product", "variety", "quality", "channel", "normalized_unit"]
seen = recent[key].drop_duplicates()
latest = prices[prices["week_start"] == weeks[-1]][key].drop_duplicates()
runs = queries.run_sql("SELECT max(started_at) AS last FROM etl_run")
today = datetime.date.today()
last_week = datetime.date.fromisoformat(str(weeks[-1])[:10])
last_load = datetime.date.fromisoformat(str(runs["last"][0])[:10])
print(json.dumps({"semana": str(weeks[-1])[:10], "precios_semana": int(len(now)), "con_comparacion": int(valid),
                  "pct_comparacion": round(valid / len(now) * 100, 1), "series_activas": int(len(seen)),
                  "series_con_dato": int(len(latest.merge(seen))), "pct_series_con_dato": round(len(latest.merge(seen)) / len(seen) * 100, 1),
                  "dias_desde_ultima_semana": (today - last_week).days - 6, "dias_desde_ultima_carga": (today - last_load).days,
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


def measure_queries(python, repeats=3):
    """How long each named query of bi/queries.sql takes on the served database, the median of three runs, in seconds."""
    code = (
        r"""
import json, time, statistics
from bi import queries
times = {}
for name in queries.load_queries():
    runs = []
    for _ in range(%d):
        start = time.perf_counter(); queries.run_query(name); runs.append(time.perf_counter() - start)
    times[name] = round(statistics.median(runs), 3)
print(json.dumps(times))
"""
        % repeats
    )
    _, out = run([python, "-c", code])
    try:
        times = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"estado": NOT_VERIFIED, "salida": out[-300:]}
    return {
        "orden": "mediana de 3 ejecuciones de cada consulta de bi/queries.sql",
        "consultas": times,
        "mas_lenta": max(times.items(), key=lambda pair: pair[1]),
    }


def summarize_browsers(data):
    pages = data["pages"]
    return {
        "orden": "node tests/medicion/calidad.cjs http://localhost:8599",
        "paginas": pages,
        "pagina_mas_lenta": max(((name, page["seconds"]) for name, page in pages.items()), key=lambda pair: pair[1]),
        "violaciones_wcag": sum(page["violations"] for page in pages.values()),
        "nodos_wcag": sum(page["nodes"] for page in pages.values()),
        "navegadores": data["browsers"],
    }


def measure_browsers(python, node_path, port=8599, saved=""):
    """Page load time, WCAG 2.1 AA violations (axe-core) and layout checks in Chromium, Firefox and WebKit, from
    tests/medicion/calidad.cjs against a dashboard started here."""
    import os
    import time
    import urllib.request

    if saved:
        return summarize_browsers(json.loads(Path(saved).read_text(encoding="utf-8")))
    if not node_path:
        return {"estado": NOT_VERIFIED, "motivo": "sin --node-path con playwright y axe-core"}
    server = subprocess.Popen(
        [
            str(Path(python).parent / "streamlit"),
            "run",
            "bi/dashboard.py",
            "--server.port",
            str(port),
            "--server.headless",
            "true",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://localhost:{port}/healthz", timeout=2)
                break
            except Exception:
                time.sleep(1)
        done = subprocess.run(
            ["node", "tests/medicion/calidad.cjs", f"http://localhost:{port}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env={**os.environ, "NODE_PATH": node_path},
        )
    finally:
        server.terminate()
    try:
        data = json.loads(done.stdout)
    except ValueError:
        return {"estado": NOT_VERIFIED, "salida": done.stderr[-300:]}
    return summarize_browsers(data)


def count_adr():
    text = (ROOT / "docs" / "ADR.md").read_text(encoding="utf-8")
    decisions = (ROOT / "docs" / "DECISIONES.md").read_text(encoding="utf-8")
    return {
        "adr": len(set(re.findall(r"^#{2,3} ADR-(\d+)", text, re.MULTILINE))),
        "decisiones": len(re.findall(r"^## D-\d+", decisions, re.MULTILINE)),
    }


def measure_tests(python):
    _, out = run([python, "-m", "pytest", "--collect-only", "-q"])
    match = re.search(r"(\d+) tests? collected", out) or re.search(r"^(\d+)/", out, re.MULTILINE)
    count = len([line for line in out.splitlines() if "::" in line])
    files = len(list((ROOT / "tests").glob("test_*.py")))
    return {"pruebas": count or (int(match.group(1)) if match else None), "archivos_de_prueba": files}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tools", required=True, help="bin folder of the virtual environment with ruff, mypy, bandit, ..."
    )
    parser.add_argument("--python", default=str(ROOT / ".venv" / "bin" / "python"), help="the project's own Python")
    parser.add_argument(
        "--node-path", default="", help="NODE_PATH with playwright and axe-core, for the browser checks"
    )
    parser.add_argument("--output", default=str(OUTPUT), help="where to write the JSON")
    parser.add_argument(
        "--browsers-from", default="", help="reuse the output of tests/medicion/calidad.cjs instead of running it"
    )
    arguments = parser.parse_args()
    _, commit = run(["git", "rev-parse", "--short", "HEAD"])
    report = {
        "generado": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "commit": commit.strip(),
        "python": sys.version.split()[0],
        "limites": {
            "largo_de_linea": LINE_LENGTH,
            "complejidad": MAX_COMPLEXITY,
            "lineas_por_funcion": MAX_FUNCTION_LINES,
            "parametros": MAX_PARAMETERS,
        },
        "ruff": measure_ruff(arguments.tools),
        "funciones": measure_functions(),
        "complejidad": measure_complexity(arguments.tools),
        "codigo_muerto": measure_dead_code(arguments.tools),
        "mypy": measure_mypy(arguments.tools),
        "cobertura": measure_coverage(arguments.python),
        "bandit": measure_bandit(arguments.tools),
        "pip_audit": measure_audit(arguments.tools),
        "secretos": measure_secrets(arguments.tools),
        "sql": measure_sql(arguments.tools),
        "dbt": measure_dbt(),
        "proceso": measure_process(),
        "pruebas": measure_tests(arguments.python),
        "dora": measure_dora(),
        "adr": count_adr(),
        "datos": measure_data(arguments.python),
        "consultas": measure_queries(arguments.python),
        "navegadores": measure_browsers(arguments.python, arguments.node_path, saved=arguments.browsers_from),
    }
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"escrito {output}")


if __name__ == "__main__":
    main()
