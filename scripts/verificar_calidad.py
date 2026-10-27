"""Compares a measurement with the goals of docs/calidad/metas.json (D-323).

    python scripts/verificar_calidad.py [docs/calidad/medicion.json]

Prints every indicator with its value and its goal, and exits with 1 naming the ones below their goal. It never
changes the code: a goal that is not met is for the author to fix.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import quality_metrics  # noqa: E402


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else quality_metrics.REPORT_FILE
    report = quality_metrics.read(path)
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    failed = []
    for row in quality_metrics.rows({}, report, goals):
        state = "no medido" if row["ok"] is None else "cumple" if row["ok"] else "NO CUMPLE"
        print(f"{row['key']:36s} {str(row['now']):>10s}  meta {quality_metrics.goal_text(row['goal']):8s}  {state}")
        if row["ok"] is False:
            failed.append(row["key"])
    if failed:
        print("\nBajo su meta: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
