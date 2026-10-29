"""Numbered quality reports (D-323, D-331): «Informe de calidad N° X», one per measurement, never edited.

    python scripts/informe_calidad.py [--medicion docs/calidad/medicion.json] [--cuerpo cuerpo.md]

Each report is a frozen copy of one measurement, kept in docs/calidad/informes/informe-NNN.json with its number, date,
data week and evaluated code (the commit), the acceptables it was judged against, and per indicator its value, failure
against the acceptable, state, insight and change against the previous report. A report is never rewritten: a second run
on the same measurement adds nothing, and an error is corrected in the next report. docs/calidad/INFORME.md shows the
latest one. With --cuerpo it also writes the body of the pull request «Actualizar medición de calidad». It never changes
code.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import quality_metrics as q  # noqa: E402

REPORT_PATH = q.FOLDER / "INFORME.md"
FOLDER = q.REPORTS_FOLDER
GOAL_FIELDS = ("max", "min", "meta", "margen_critico", "tipo", "medida")


def read_reports(folder=FOLDER):
    """Every report, oldest first."""
    return q.read_reports(folder)


def build_report(number, measurement, goals, policy, previous=None):
    """The report of one measurement: what was measured, against which acceptables, and how it came out."""
    rows = q.evaluate(measurement, goals, policy, previous["medicion"] if previous else None)
    return {
        "numero": number,
        "titulo": f"Informe de calidad N° {number}",
        "fecha": measurement.get("generado"),
        "semana": measurement.get("datos", {}).get("semana"),
        "codigo_evaluado": measurement.get("commit"),
        "anterior": previous["numero"] if previous else None,
        "aceptables": {
            key: {field: goals[key][field] for field in GOAL_FIELDS if field in goals.get(key, {})}
            for key, *_ in q.INDICATORS
        },
        "modo_datos": policy.get("modo_datos"),
        "indicadores": rows,
        "medicion": measurement,
    }


def add_report(measurement, goals, policy, folder=FOLDER):
    """Writes the next report, or returns the existing one when this measurement already has a report. Never
    overwrites: the file is opened in «x» mode, which fails if it exists."""
    reports = read_reports(folder)
    for report in reports:
        if report["codigo_evaluado"] == measurement.get("commit") and report["fecha"] == measurement.get("generado"):
            return report, False
    previous = reports[-1] if reports else None
    report = build_report((previous["numero"] + 1) if previous else 1, measurement, goals, policy, previous)
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / f"informe-{report['numero']:03d}.json", "x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report, True


def counts(report):
    """(within the acceptable, non-conformities, measured)."""
    return q.report_counts(report)


def failure_text(row, key="falla"):
    value = row[key]
    if value is None:
        return "—"
    unit = row["unidad_falla"]
    decimals = 2 if isinstance(value, float) and value % 1 else 0
    return q.number(value, decimals) + (f" {unit}" if unit else "")


def render_markdown(report, policy):
    """docs/calidad/INFORME.md: the latest report, short."""
    within, nonconforming, measured = counts(report)
    states = policy.get("estados", {})
    previous = f"N° {report['anterior']}" if report["anterior"] else "—"
    lines = [
        f"# {report['titulo']}",
        "",
        "| | |",
        "|---|---|",
        f"| **Fecha** | {report['fecha']} |",
        f"| **Semana de datos** | {report['semana'] or '—'} |",
        f"| **Código evaluado** | {report['codigo_evaluado']} |",
        f"| **Informe anterior** | {previous} |",
        "",
        f"Autoevaluación automática: {within} de {measured} indicadores medidos están dentro de lo aceptable; "
        f"{nonconforming} no conformidades. Los aceptables son los de `metas.json` al crearse el informe; los "
        "indicadores de datos van en modo aviso hasta que el autor apruebe que bloqueen la publicación.",
        "",
        "| Indicador | Tipo | Falla | Aceptable | Estado | Lectura |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["indicadores"]:
        lines.append(
            f"| {row['nombre'][0]} | {row['tipo']} | {failure_text(row)} | {failure_text(row, 'falla_aceptable')} | "
            f"{states.get(row['estado'], [row['estado']])[0]} | {row['insight'][0]} |"
        )
    lines += [
        "",
        "Cada informe se guarda en `docs/calidad/informes/` y no se edita: un error se corrige en el informe siguiente.",
        "",
    ]
    return "\n".join(lines)


def build_pull_request(report, previous, policy):
    """The body of «Actualizar medición de calidad»: every indicator against the previous report."""
    within, nonconforming, measured = counts(report)
    before = {row["clave"]: row for row in previous["indicadores"]} if previous else {}
    states = policy.get("estados", {})
    against = f"el informe N° {previous['numero']}" if previous else "ningún informe anterior"
    lines = [
        f"{report['titulo']}: medición del {report['fecha']} (código {report['codigo_evaluado']}), comparada con "
        f"{against}. {within} de {measured} indicadores dentro de lo aceptable; {nonconforming} no conformidades.",
        "",
        "| Indicador | Falla anterior | Falla nueva | Aceptable | Estado |",
        "|---|---|---|---|---|",
    ]
    for row in report["indicadores"]:
        earlier = before.get(row["clave"])
        lines.append(
            f"| {row['nombre'][0]} | {failure_text(earlier) if earlier else '—'} | {failure_text(row)} | "
            f"{failure_text(row, 'falla_aceptable')} | {states.get(row['estado'], [row['estado']])[0]} |"
        )
    lines += [
        "",
        "Nada se publica en la página «Método y calidad» hasta que el autor fusione este pull request. El workflow no "
        "cambió código: solo la medición, el informe nuevo e INFORME.md.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--medicion", default=str(q.REPORT_FILE), help="the measurement to report")
    parser.add_argument("--cuerpo", default="", help="where to write the pull request body")
    arguments = parser.parse_args()
    measurement = q.read(Path(arguments.medicion))
    goals, policy = q.read(q.GOALS_FILE), q.read(q.POLICY_FILE)
    report, new = add_report(measurement, goals, policy)
    q.HISTORY_FILE.write_text(
        json.dumps(q.add_to_history(q.read(q.HISTORY_FILE), measurement), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(render_markdown(read_reports()[-1], policy), encoding="utf-8")
    if arguments.cuerpo:
        previous = next((item for item in read_reports() if item["numero"] == report["anterior"]), None)
        Path(arguments.cuerpo).write_text(build_pull_request(report, previous, policy), encoding="utf-8")
    print(f"{report['titulo']} {'escrito' if new else 'ya existía'}")


if __name__ == "__main__":
    main()
