"""What the CI checks, run here before a push (D-570), so nothing of the project reaches GitHub red.

    python scripts/antes_de_subir.py              check the commit about to be pushed (HEAD)
    python scripts/antes_de_subir.py --instalar   install it as the git pre-push hook: every push runs it

It runs, in order, and stops at the first check that fails: Ruff (rules and format) and mypy, as pruebas.yml; the secret
scan and Bandit with the versions calidad.yml installs (no unclassified candidate, no high finding); and the whole suite
as pruebas.yml runs it: in a separate copy of the commit, with the database the last load published and the clock in UTC
(D-527). It takes three to four minutes. `git push --no-verify` skips it, when the author decides so.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# region Constants
ROOT = Path(__file__).resolve().parent.parent
PROJECT_BIN = ROOT / ".venv" / "bin"
# The scan tools live outside the project, in the versions calidad.yml installs, so they are never a dependency of it.
TOOLS_DIR = Path.home() / ".cache" / "greenocean-herramientas"
TOOL_NAMES = ("bandit", "detect-secrets")
QUALITY_WORKFLOW = ROOT / ".github" / "workflows" / "calidad.yml"
# The Python of the tools: the one of dbt (3.12, as the CI) when this computer has it, else this one.
TOOLS_PYTHON = ROOT / ".venv-dbt" / "bin" / "python"
POINTER_FILE = Path("etl") / "datos.version"
DATABASE_FILE = Path("etl") / "datos.duckdb"
HOOK = """#!/bin/sh
# GreenOcean (D-570): what the CI checks, before every push. `git push --no-verify` skips it.
top="$(git rev-parse --show-toplevel)"
exec "$top/.venv/bin/python" "$top/scripts/antes_de_subir.py"
"""
# endregion


# region Steps
def say(text):
    print(text, flush=True)


def run(name, command, folder, extra_env=None):
    """One check: its name, how long it took and whether it passed; its own output only when it fails."""
    started = time.monotonic()
    env = {**os.environ, **(extra_env or {})}
    done = subprocess.run(command, cwd=folder, capture_output=True, text=True, env=env)
    seconds = time.monotonic() - started
    if done.returncode != 0:
        say(f"✗ {name} ({seconds:.0f} s)")
        say((done.stdout + done.stderr).strip()[-4000:])
        return False
    say(f"✓ {name} ({seconds:.0f} s)")
    return True


def tool_versions():
    """The pinned versions calidad.yml installs, read from it so the two never differ."""
    text = QUALITY_WORKFLOW.read_text(encoding="utf-8")
    return [found.group(0) for name in TOOL_NAMES if (found := re.search(rf"{re.escape(name)}==[\d.]+", text))]


def ensure_tools():
    """The scan tools in their own environment, created once and installed again when calidad.yml changes a version."""
    wanted = tool_versions()
    stamp = TOOLS_DIR / "versiones.txt"
    if stamp.exists() and stamp.read_text(encoding="utf-8").split() == wanted:
        return TOOLS_DIR / "bin"
    say("· Instalando las herramientas de escaneo (una sola vez): " + " ".join(wanted))
    python = str(TOOLS_PYTHON) if TOOLS_PYTHON.exists() else sys.executable
    shutil.rmtree(TOOLS_DIR, ignore_errors=True)
    subprocess.run([python, "-m", "venv", str(TOOLS_DIR)], check=True)
    subprocess.run([str(TOOLS_DIR / "bin" / "pip"), "install", "-q", *wanted], check=True)
    stamp.write_text(" ".join(wanted), encoding="utf-8")
    return TOOLS_DIR / "bin"


def published_database(copy):
    """The database the last load published, in the copy: from the local cache when its fingerprint is the pointer's,
    else downloaded (and kept for the next push)."""
    sha = json.loads((copy / POINTER_FILE).read_text(encoding="utf-8"))["sha256"]
    cached = TOOLS_DIR / f"datos-{sha[:12]}.duckdb"
    if cached.exists():
        shutil.copy2(cached, copy / DATABASE_FILE)
        return True
    if not run("Base publicada", [str(PROJECT_BIN / "python"), "bi/served_database.py"], copy):
        return False
    for old in TOOLS_DIR.glob("datos-*.duckdb"):
        old.unlink()
    shutil.copy2(copy / DATABASE_FILE, cached)
    return True


def scans(copy, tools):
    """The secret scan and Bandit, measured as calidad.yml measures them."""
    code = (
        "import json, sys; sys.path.insert(0, 'scripts'); import medir_calidad as m; "
        f"s = m.measure_secrets({str(tools)!r}); b = m.measure_bandit({str(tools)!r}); "
        "print(json.dumps({'secretos': s['sin_clasificar'], 'bandit': b['alta']})); "
        "sys.exit(0 if s['sin_clasificar'] == 0 and b['alta'] == 0 else 1)"
    )
    return run("Secretos sin clasificar y Bandit alto en 0", [str(PROJECT_BIN / "python"), "-c", code], copy)


def check(copy, tools):
    """Every check in the order of the CI; False at the first that fails."""
    python, ruff, mypy = (str(PROJECT_BIN / name) for name in ("python", "ruff", "mypy"))
    return (
        run("Ruff, reglas", [ruff, "check", "."], copy)
        and run("Ruff, formato", [ruff, "format", "--check", "."], copy)
        and run("mypy", [mypy], copy)
        and scans(copy, tools)
        and published_database(copy)
        and run(
            "Todas las pruebas, como el CI",
            [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-m", "not rendimiento"],
            copy,
            {"TZ": "UTC"},
        )
    )


# endregion


# region Run
def main():
    if "--instalar" in sys.argv:
        hooks = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        hook = (ROOT / hooks / "pre-push").resolve()
        hook.write_text(HOOK, encoding="utf-8")
        hook.chmod(0o755)
        say(f"Instalado: cada git push revisa antes lo mismo que el CI ({hook}).")
        return 0
    started = time.monotonic()
    say("Revisión antes de subir: lo mismo que el CI, sobre el commit que se va a subir.")
    tools = ensure_tools()
    copy = Path(tempfile.mkdtemp(prefix="greenocean-antes-de-subir-"))
    copy.rmdir()
    subprocess.run(["git", "worktree", "add", "--detach", "-q", str(copy), "HEAD"], cwd=ROOT, check=True)
    try:
        passed = check(copy, tools)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(copy)], cwd=ROOT)
    minutes = (time.monotonic() - started) / 60
    if passed:
        say(f"Todo en verde ({minutes:.1f} min): se puede subir.")
        return 0
    say(
        f"No se sube ({minutes:.1f} min): corrige lo que está en rojo, o usa git push --no-verify si decides subir igual."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
# endregion
