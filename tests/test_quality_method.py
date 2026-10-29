"""«Método y calidad» (D-320, D-323): every measured number of the page comes from the files of docs/calidad, the ISO
grades come from the author's dated review, the measurable gaps from the indicators, the wording never claims
certification, and the line under the logo opens the page in both languages."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import i18n, quality_method, quality_metrics

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = str(ROOT / "bi" / "dashboard.py")
FORBIDDEN = (
    "certificado",
    "certificada",
    "cumple la norma",
    "cumple con la norma",
    "complies with the standard",
    "is certified",
)
REPORT = {
    "generado": "2026-10-27 12:00 UTC",
    "commit": "abc1234",
    "ruff": {"errores": 3, "formato": {"por_reformatear": 0}},
    "cobertura": {
        "total": 94.2,
        "modulos": {"bi/a.py": 88.0, "etl/b.py": 71.5},
        "pruebas_ok": 10,
        "pruebas_omitidas": 1,
    },
    "pruebas": {"pruebas": 11},
    "mypy": {"errores": 0, "funciones": 10, "con_tipo_de_retorno": 10},
    "complejidad": {"funciones_sobre_10": 6},
    "bandit": {"alta": 0},
    "pip_audit": {"archivos": {"requirements.txt": {"vulnerabilidades": 0}}},
    "secretos": {"sin_clasificar": 0},
    "consultas": {"consultas": {"k1": 0.2, "k3": 0.4}},
    "navegadores": {
        "paginas": {"Panorama de precios": {"seconds": 0.3, "violations": 0}},
        "violaciones_wcag": 0,
        "navegadores": {"chromium": {"checks": 3, "passed": 3, "failed": []}},
    },
}


def test_d323_the_indicators_are_read_from_the_measurement_and_checked_against_the_goals():
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    values = quality_metrics.values(REPORT)
    assert values["ruff_avisos"] == 3 and values["cobertura_por_modulo"] == 71.5 and values["pruebas_fallidas"] == 0
    assert "segundos_por_consulta" not in values and "complejidad_sobre_10" not in values  # D-330: out of scope
    rows = {row["key"]: row for row in quality_metrics.rows({}, REPORT, goals)}
    assert rows["ruff_avisos"]["ok"] is False and rows["cobertura_total"]["ok"] is True
    assert quality_metrics.gaps(REPORT, goals) == {
        "mantenibilidad": [
            (
                "Avisos de Ruff (E, F y W; el largo de línea, aparte): 3 (meta ≤ 0)",
                "Ruff findings (E, F and W; line length apart): 3 (goal ≤ 0)",
            )
        ]
    }


def test_d323_the_verifier_fails_naming_the_indicator_below_its_goal(tmp_path):
    report = tmp_path / "medicion.json"
    report.write_text(json.dumps(REPORT))
    done = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verificar_calidad.py"), str(report)], capture_output=True, text=True
    )
    assert done.returncode == 1 and "Peor que lo aceptable: ruff_avisos" in done.stdout
    report.write_text(json.dumps({**REPORT, "ruff": {"errores": 0, "formato": {"por_reformatear": 0}}}))
    assert (
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verificar_calidad.py"), str(report)], capture_output=True
        ).returncode
        == 0
    )


def test_d332_the_header_names_the_latest_report_and_the_logo_line_promises_only_that():
    reports, _, _ = quality_method.read_page()
    latest = reports[-1]
    header = quality_method.build_header(latest)
    assert f"Informe de calidad N° {latest['numero']}" in header and latest["codigo_evaluado"] in header
    assert "revisada y aprobada por el autor" in header and "ISO" not in quality_method.sidebar_line(reports)
    assert quality_method.sidebar_line(reports) == f"Autoevaluación de calidad · Informe N° {latest['numero']}"
    assert "Todavía no hay informes" in quality_method.build_header(None)


def test_d323_ruff_counts_the_same_rules_before_and_after_and_a_zero_count_of_formatting_is_read():
    # The baseline counted E501 inside; the indicator compares E, F and W without it on both sides.
    assert quality_metrics.values({"ruff": {"errores": 1984, "errores_sin_largo_de_linea": 208}})["ruff_avisos"] == 208
    sys.path.insert(0, str(ROOT / "scripts"))
    import medir_calidad

    assert medir_calidad.count_formatting("145 files already formatted") == (0, 145)
    assert medir_calidad.count_formatting("2 files would be reformatted, 143 files already formatted") == (2, 143)
    assert medir_calidad.count_formatting("error: no files") == (None, None)


def test_d323_a_candidate_the_author_marked_as_not_secret_counts_as_reviewed():
    sys.path.insert(0, str(ROOT / "scripts"))
    import medir_calidad

    baseline = json.loads((ROOT / ".secrets.baseline").read_text())
    reviewed = medir_calidad.reviewed_secret_hashes()
    assert reviewed == {item["hashed_secret"] for items in baseline["results"].values() for item in items}
    found = {name: items for name, items in baseline["results"].items() if name == ".github/workflows/calidad.yml"}
    assert medir_calidad.classify_secret_candidates(found) == {"falsos_positivos": 1, "sin_clasificar": 0}


def test_d332_the_reports_tab_lists_every_report_newest_first(monkeypatch):
    monkeypatch.setattr(i18n, "is_english", lambda: False)
    reports, _, policy = quality_method.read_page()
    table = quality_method.build_reports_table(reports)
    numbers = [f"N° {report['numero']}</b>" for report in reports]
    assert [table.index(item) for item in numbers] == sorted((table.index(item) for item in numbers), reverse=True)
    for report in reports:
        within, nonconforming, measured = quality_metrics.report_counts(report)
        assert f"<td>{within} / {measured}</td><td>{nonconforming}</td>" in table
    view = quality_method.build_report_view(reports[-1], policy)
    assert view.count("<tr><td><b>") == 12 and reports[-1]["indicadores"][0]["insight"][0] in view


def load_reports_module():
    sys.path.insert(0, str(ROOT / "scripts"))
    import informe_calidad

    return informe_calidad


def test_d331_the_reports_are_numbered_frozen_and_the_latest_is_the_markdown():
    informe_calidad = load_reports_module()
    reports = informe_calidad.read_reports()
    assert [report["numero"] for report in reports] == list(range(1, len(reports) + 1)) and len(reports) >= 4
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    for report in reports:
        assert report["titulo"] == f"Informe de calidad N° {report['numero']}"
        assert (
            report["codigo_evaluado"] == report["medicion"]["commit"]
            and report["fecha"] == report["medicion"]["generado"]
        )
        assert report["anterior"] == (report["numero"] - 1 or None)
        # The report keeps the acceptables it was judged against and, per indicator, what the reader needs.
        assert set(report["aceptables"]) == {key for key, *_ in quality_metrics.INDICATORS}
        for row in report["indicadores"]:
            assert {"valor", "falla", "falla_aceptable", "estado", "insight", "variacion"} <= set(row)
        # Rebuilt today from its own frozen measurement and acceptables, it says the same: nothing was edited.
        previous = reports[report["numero"] - 2] if report["numero"] > 1 else None
        rebuilt = informe_calidad.build_report(
            report["numero"],
            report["medicion"],
            report["aceptables"],
            {**policy, "modo_datos": report["modo_datos"]},
            previous,
        )
        assert [row["estado"] for row in rebuilt["indicadores"]] == [row["estado"] for row in report["indicadores"]]
    # The first reports are the measurements of the history, without anything made up.
    assert [report["codigo_evaluado"] for report in reports[:4]] == ["cf561e7", "6c6286c", "d66804c", "b015e3a"]
    assert {row["clave"]: row["estado"] for row in reports[0]["indicadores"]}["comparables_pct"] == "sin_medicion"
    text = (ROOT / "docs" / "calidad" / "INFORME.md").read_text(encoding="utf-8")
    assert text == informe_calidad.render_markdown(reports[-1], policy) and "```" not in text
    assert not any(word in text.lower() for word in FORBIDDEN)


def test_d331_a_report_is_never_rewritten_and_the_pull_request_compares_with_the_previous(tmp_path):
    informe_calidad = load_reports_module()
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    first, new = informe_calidad.add_report(REPORT, goals, policy, folder=tmp_path)
    assert new and first["numero"] == 1 and (tmp_path / "informe-001.json").exists()
    again, new = informe_calidad.add_report(REPORT, goals, policy, folder=tmp_path)
    assert not new and len(list(tmp_path.glob("informe-*.json"))) == 1  # the same measurement adds nothing
    fixed = dict(REPORT, commit="def5678", generado="2026-11-03 12:00 UTC", ruff={"errores": 0})
    second, new = informe_calidad.add_report(fixed, goals, policy, folder=tmp_path)
    assert new and second["numero"] == 2 and second["anterior"] == 1
    assert {row["clave"]: row["variacion"] for row in second["indicadores"]}["ruff_avisos"] == -3
    body = informe_calidad.build_pull_request(second, first, policy)
    within, nonconforming, measured = informe_calidad.counts(second)
    assert "Informe de calidad N° 2" in body and "comparada con el informe N° 1" in body
    assert f"{within} de {measured} indicadores dentro de lo aceptable" in body
    with pytest.raises(FileExistsError):  # the file mode refuses to overwrite a report
        with open(tmp_path / "informe-001.json", "x", encoding="utf-8"):
            pass


def test_d332_the_summary_reads_the_latest_report_and_never_claims_an_external_attestation(monkeypatch):
    reports, goals, policy = quality_method.read_page()
    latest = reports[-1]
    for english in (False, True):
        monkeypatch.setattr(i18n, "is_english", lambda english=english: english)
        overview = quality_method.build_overview(latest, goals, policy)
        text = " ".join([quality_method.build_header(latest), overview, quality_method.build_reports_table(reports)])
        assert not any(word in text.lower() for word in FORBIDDEN), english
    monkeypatch.setattr(i18n, "is_english", lambda: False)
    overview = quality_method.build_overview(latest, goals, policy)
    within, nonconforming, measured = quality_metrics.report_counts(latest)
    assert f"Hoy: {within} de {measured} medidos dentro de lo aceptable" in overview
    assert "Medimos 12 indicadores: 4 de los datos que publicamos y 8 del código" in overview
    # Only the indicators out of their acceptable carry their insight in sight; the rest on hover.
    attention = [row for row in latest["indicadores"] if row["estado"] in ("urgente", "critico")]
    assert overview.count("<li class=") == len(attention)
    # The five counts share one line when all of them meet their acceptable.
    counts = [row for row in latest["indicadores"] if row["clave"] in quality_method.COUNTS]
    if all(row["estado"] == "cumple" for row in counts):
        assert "Ruff · mypy · Bandit · pip-audit · secretos" in overview


@pytest.mark.parametrize("language", ["es", "en"])
def test_d332_the_page_has_two_tabs_and_the_logo_line_opens_it_in_both_languages(language):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params.update({"perfil": "profesional", "lang": language})
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.sidebar.markdown)
    number = quality_metrics.read_reports()[-1]["numero"]
    expected = f"Quality self-assessment · Report No. {number}" if language == "en" else f"Informe N° {number}"
    assert expected in markup
    page = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    page.query_params.update({"perfil": "profesional", "lang": language, "vista": "Método y calidad"})
    page.run()
    assert not page.exception and len(page.tabs) == 2
    content = " ".join(block.value for block in page.markdown if "qm-" in block.value)
    assert "qm-overview" in content and "qm-reports" in content
    assert not re.search(r"month_start|>None<|\bnan\b", content)


# region Acceptables, goals and insights (D-330)
def test_d330_metas_keeps_the_approved_twelve_indicators_with_their_explanation():
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    keys = [key for key, *_ in quality_metrics.INDICATORS]
    assert set(keys) == {key for key in goals if key != "nota"} and len(keys) == 12
    assert sum(goals[key]["tipo"] == "datos" for key in keys) == 4
    for key in keys:
        goal = goals[key]
        assert ("max" in goal) != ("min" in goal) and "meta" in goal and "margen_critico" in goal, key
        assert all(len(goal[field]) == 2 and all(goal[field]) for field in ("que_mide", "por_que", "como", "accion"))
    # The approved numbers (2026-10-29).
    assert goals["cobertura_total"]["min"] == 90 and goals["cobertura_por_modulo"]["min"] == 70
    assert goals["comparables_pct"]["min"] == 90 and goals["vigencia_dias"]["max"] == 8
    assert (
        goals["pip_audit_vulnerabilidades"]["max"] == 0 and goals["pip_audit_vulnerabilidades"]["margen_critico"] == 0
    )


def test_d330_the_state_says_meets_warning_urgent_or_critical():
    coverage = {"min": 90, "meta": 95, "margen_critico": 5}
    assert [quality_metrics.state(value, coverage) for value in (96, 92, 86, 84, None)] == [
        "cumple",
        "aviso",
        "urgente",
        "critico",
        "sin_medicion",
    ]
    ruff = {"max": 0, "meta": 0, "margen_critico": 5}
    assert [quality_metrics.state(value, ruff) for value in (0, 3, 6)] == ["cumple", "urgente", "critico"]
    secrets = {"max": 0, "meta": 0, "margen_critico": 0}
    assert quality_metrics.state(1, secrets) == "critico"  # any case is critical


def test_d330_the_failure_reads_against_the_acceptable_and_the_insight_comes_from_the_policy():
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    report = dict(REPORT, datos={"pct_comparacion": 85.0, "pct_rechazadas": 0.01, "dias_desde_ultima_carga": 7})
    rows = {row["clave"]: row for row in quality_metrics.evaluate(report, goals, policy)}
    comparables = rows["comparables_pct"]
    assert (comparables["falla"], comparables["falla_aceptable"], comparables["estado"]) == (15.0, 10.0, "urgente")
    assert not comparables["bloquea"] and "modo aviso" in comparables["insight"][0]  # data warns until approved
    ruff = rows["ruff_avisos"]
    assert ruff["estado"] == "urgente" and ruff["bloquea"] and goals["ruff_avisos"]["accion"][0] in ruff["insight"][0]
    assert rows["cobertura_total"]["insight"][0] == policy["insight"]["cumple"][0]
    assert rows["pruebas_dbt_pct"]["estado"] == "sin_medicion" and rows["pruebas_dbt_pct"]["valor"] is None
    # The change against the previous report, never a made-up one.
    later = quality_metrics.evaluate(dict(report, ruff={"errores": 0}), goals, policy, previous=report)
    assert {row["clave"]: row["variacion"] for row in later}["ruff_avisos"] == -3


# endregion


# region Reports: filters, links and the slide viewer (D-333)
def test_d333_the_viewer_has_eight_slides_read_from_the_report_and_compares_with_the_previous():
    from bi import quality_viewer

    reports, goals, policy = quality_method.read_page()
    latest = reports[-1]
    record = {
        "informe": latest["numero"],
        "indicador": "pruebas_fallidas",
        "causa": "Enlaces del repositorio sin renombrar.",
        "accion": "",
        "estado": "cerrada",
    }
    page = quality_viewer.build_viewer_html(reports, latest["numero"], goals, policy, [record], [])
    assert page.startswith("<!doctype html>") and page.count('<section class="slide') == 8
    assert f"Informe de calidad N° {latest['numero']}" in page and latest["codigo_evaluado"] in page
    assert "Enlaces del repositorio sin renombrar." in page and "cerrada" in page  # the author's cause and state
    assert '"a": ' + str(latest["anterior"]) in page and "Sin incidentes externos en el período." in page
    assert "window.print()" in page and "requestFullscreen" in page and "ArrowRight" in page
    assert not any(word in page.lower() for word in FORBIDDEN)
    # Report N° 2 covers from N° 1's date to its own: an incident on its day is counted, only counted.
    second = reports[1]
    incident = [{"fecha": second["fecha"][:10], "detalle": "solo para el autor"}]
    english = quality_viewer.build_viewer_html(reports, second["numero"], goals, policy, [], incident, True)
    assert "Quality report No." in english and "Download PDF" in english and "1 external incident" in english
    assert "Qué falló" not in english and "Comparación" not in english and "solo para el autor" not in english


def test_d333_the_reports_tab_filters_by_year_month_week_and_search_and_links_each_report():
    from bi import dashboard

    reports, _, _ = quality_method.read_page()
    every = dashboard.ALL_VALUES
    assert dashboard.filter_reports(reports, every, every, every, "") == reports
    assert [r["numero"] for r in dashboard.filter_reports(reports, every, every, every, "b015e3a")] == [4]
    assert [r["numero"] for r in dashboard.filter_reports(reports, every, every, every, "N° 2")] == [2]
    assert dashboard.filter_reports(reports, "2025", every, every, "") == []
    assert len(dashboard.filter_reports(reports, "2026", "10", "2026-10-12", "")) == 3  # N° 1 has no data week
    table = quality_method.build_reports_table(reports[2:3], reports, lambda number: f"?vista=x&informe={number}")
    assert 'href="?vista=x&amp;informe=3"' in table and table.count("qm-pdf") == 1
    assert "<td>+2</td>" in table  # N° 3 against N° 2, though N° 2 is filtered out


# endregion


# region Non-conformities, mitigation and external incidents (D-334)
def test_d334_every_nonconformity_of_the_reports_is_registered_and_the_author_writes_action_and_state():
    folder = quality_metrics.FOLDER
    records = quality_metrics.read(folder / "no_conformidades.json")["registros"]
    found = {
        (report["numero"], row["clave"])
        for report in quality_metrics.read_reports()
        for row in report["indicadores"]
        if row["estado"] in ("urgente", "critico")
    }
    assert {(item["informe"], item["indicador"]) for item in records} == found
    assert all(item["accion"] == "" and item["estado"] == "" for item in records)  # the author's to write
    plan = quality_metrics.read(folder / "plan_mitigacion.json")["fallas"]
    assert [item["id"] for item in plan] == [f"F-{n:02d}" for n in range(1, len(plan) + 1)]
    assert {item["causa"] for item in plan} == {"interna", "externa"}
    incidents = quality_metrics.read(folder / "incidentes_externos.json")
    assert incidents["respuestas_por_defecto"]["estado"] == "pendiente de aprobación del autor"
    assert isinstance(incidents["registros"], list)


# endregion
