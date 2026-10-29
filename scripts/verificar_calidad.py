"""Compares a measurement with the acceptables and goals of docs/calidad/metas.json (D-323, D-330).

    python scripts/verificar_calidad.py [docs/calidad/medicion.json]

Prints every indicator with its value, its failure against the acceptable and its state. It exits with 1 naming the
indicators worse than the acceptable (urgent or critical); one worse than the goal but within the acceptable is only a
warning. Data indicators stay in warning mode (docs/calidad/politica.json) until the author lets them block. It never
changes the code: an indicator out of its acceptable is for the author to fix.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import quality_metrics  # noqa: E402


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else quality_metrics.REPORT_FILE
    report = quality_metrics.read(path)
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    blocking, warnings = [], []
    for row in quality_metrics.evaluate(report, goals, policy):
        failure = "—" if row["falla"] is None else f"{row['falla']}{row['unidad_falla']}"
        acceptable = "—" if row["falla_aceptable"] is None else f"{row['falla_aceptable']}{row['unidad_falla']}"
        print(
            f"{row['clave']:28s} {row['tipo'] or '':7s} falla {failure:>10s}  aceptable {acceptable:>8s}  {row['estado']}"
        )
        if row["bloquea"]:
            blocking.append(row["clave"])
        elif row["estado"] in ("aviso", "urgente", "critico"):
            warnings.append(row["clave"])
    if warnings:
        print("\nAviso: " + ", ".join(warnings))
    if blocking:
        print("\nPeor que lo aceptable: " + ", ".join(blocking))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
