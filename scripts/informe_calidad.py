"""Weekly quality reports (D-323, D-331, D-431): «Informe semanal de calidad N° X», one per data week, never edited.

    python scripts/informe_calidad.py [--medicion docs/calidad/medicion.json] [--cuerpo cuerpo.md]

Each report is a frozen copy of one measurement, kept in docs/calidad/informes/semanales/informe-NNN.json with its
number, date, data week, evaluated code (the commit), the SQAP version it was measured by, the acceptables it was judged
against, and per indicator its value, failure against the acceptable, state, insight and change against the previous
report. D-431: only the three indicators measured once per load (q.WEEKLY_INDICATORS); the code is checked by the CI of
every push. The seven reports of docs/calidad/informes/ are the closed construction series, C-1 to C-7. A report is never rewritten: a second run
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
NONCONFORMITIES = q.FOLDER / "no_conformidades.json"
OUT_OF_RANGE = ("urgente", "critico")
FOLDER = q.WEEKLY_FOLDER
GOAL_FIELDS = ("max", "min", "meta", "margen_critico", "tipo", "medida")


def read_reports(folder=FOLDER):
    """Every weekly report, oldest first."""
    return [
        {**json.loads(path.read_text(encoding="utf-8")), "serie": q.SERIES_WEEKLY}
        for path in sorted(folder.glob("informe-*.json"))
    ]


def build_report(number, measurement, goals, policy, previous=None, history=None):
    """The report of one measurement: what was measured, against which acceptables, and how it came out."""
    rows = [
        row
        for row in q.evaluate(measurement, goals, policy, previous["medicion"] if previous else None)
        if row["clave"] in q.WEEKLY_INDICATORS
    ]
    draft = {"numero": number, "fecha": measurement.get("generado"), "medicion": measurement, "serie": q.SERIES_WEEKLY}
    for row in rows:
        if row["estado"] in ("urgente", "critico"):
            # D-335: the diagnosis of what is out of its acceptable is stored with the report, once, never rewritten.
            row["diagnostico"] = q.diagnose(row, {**draft, "indicadores": rows}, history or [], policy)
    return {
        "numero": number,
        "titulo": f"Informe semanal de calidad N° {number}",
        "serie": q.SERIES_WEEKLY,
        "sqap": q.sqap_version(),
        "fecha": measurement.get("generado"),
        "semana": measurement.get("datos", {}).get("semana"),
        "codigo_evaluado": measurement.get("commit"),
        "anterior": previous["numero"] if previous else None,
        "aceptables": {
            key: {field: goals[key][field] for field in GOAL_FIELDS if field in goals.get(key, {})}
            for key in q.WEEKLY_INDICATORS
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
    report = build_report((previous["numero"] + 1) if previous else 1, measurement, goals, policy, previous, reports)
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / f"informe-{report['numero']:03d}.json", "x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report, True


def register_nonconformities(report, path=NONCONFORMITIES):
    """D-401: each indicator of the report out of its acceptable gets its line in the register of non-conformities
    (D-334), with the cause, the action and the state blank for the author. Adds only what is missing, so a second run
    adds nothing; returns how many it added."""
    text = path.read_text(encoding="utf-8")
    register = json.loads(text)
    known = {(item["informe"], item.get("serie", q.SERIES_BUILD), item["indicador"]) for item in register["registros"]}
    added = [
        {
            "informe": report["numero"],
            "serie": q.SERIES_WEEKLY,
            "indicador": row["clave"],
            "fecha": report["fecha"][:10],
            "causa": "",
            "accion": "",
            "estado": "",
        }
        for row in report["indicadores"]
        if row["estado"] in OUT_OF_RANGE and (report["numero"], q.SERIES_WEEKLY, row["clave"]) not in known
    ]
    if added:
        register["registros"] += added
        path.write_text(
            json.dumps(register, ensure_ascii=False, indent=2) + ("\n" if text.endswith("\n") else ""), encoding="utf-8"
        )
    return len(added)


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
        f"| **Medido según** | SQAP v{report.get('sqap') or '—'} |",
        "",
        f"Autoevaluación automática de la carga semanal: {within} de {measured} indicadores de datos dentro de lo "
        f"aceptable; {nonconforming} no conformidades. Los aceptables son los de `metas.json` al crearse el informe; el "
        "método está en el SQAP (`docs/calidad/PLAN_DE_CALIDAD.md`).",
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
        "Cada informe se guarda en `docs/calidad/informes/semanales/` y no se edita: un error se corrige en el informe "
        "siguiente. Los informes C-1 a C-7 de `docs/calidad/informes/` son la serie de construcción, cerrada.",
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
    register_nonconformities(report)
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
