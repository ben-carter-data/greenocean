"""«Método y calidad» (D-320, D-323): every measured number of the page comes from the files of docs/calidad, the ISO
grades come from the author's dated review, the measurable gaps from the indicators, the wording never claims
certification, and the line under the logo opens the page in both languages."""

import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import compact_table, i18n, quality_method, quality_metrics

# region Constants
# D-475: indicators added after the construction series closed (C-1 to C-7 keep their twelve).
ADDED_AFTER_BUILD = {"ausencias_region_canal", "atipicos_pct"}
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
        "paginas": {"Dashboard": {"seconds": 0.3, "violations": 0}},
        "violaciones_wcag": 0,
        "navegadores": {"chromium": {"checks": 3, "passed": 3, "failed": []}},
    },
}
# endregion


# region The indicators and the verifier
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


def test_d332_the_header_names_the_latest_report():
    reports, _, _ = quality_method.read_page()
    latest = reports[-1]
    within, nonconforming, measured = quality_metrics.report_counts(latest)
    header = quality_method.build_header(latest)
    # D-571: one line with the report, its date and its counts; how the report is made, on hover
    line = f"{quality_metrics.report_name(latest)} · {str(latest['fecha'])[:10]} · {within} de {measured}"
    assert f">{line} dentro de lo aceptable · {nonconforming} no conformidad" in header
    assert 'title="Autoevaluación automática, revisada y aprobada por el autor."' in header and "ISO" not in header
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
    count = len(found[".github/workflows/calidad.yml"])  # D-568: the GH_TOKEN line joined the reviewed ones
    assert count >= 2 and medir_calidad.classify_secret_candidates(found) == {
        "falsos_positivos": count,
        "sin_clasificar": 0,
    }


@pytest.fixture
def construction_series(monkeypatch):
    """D-431: these checks read the closed history of C-1 to C-7; the page itself reads the current series (F-33)."""
    monkeypatch.setattr(quality_metrics, "current_series", lambda: quality_metrics.SERIES_BUILD)


def test_f33_the_page_reads_the_weekly_series_once_it_has_a_report():
    assert any(quality_metrics.WEEKLY_FOLDER.glob("informe-*.json"))
    reports = quality_method.read_page()[0]
    assert reports and all(report["serie"] == quality_metrics.SERIES_WEEKLY for report in reports)
    assert quality_metrics.report_code(reports[0]) == "N° 1"
    assert quality_metrics.read_reports(quality_metrics.SERIES_BUILD)[-1]["numero"] == 7  # the closed series stays


def test_d332_the_reports_tab_lists_every_report_newest_first(construction_series, monkeypatch):
    monkeypatch.setattr(i18n, "is_english", lambda: False)
    reports, *_ = quality_method.read_page()
    for report in reports:  # one line each: number, date and how many indicators are within the acceptable
        within, nonconforming, measured = quality_metrics.report_counts(report)
        line = quality_method.report_summary(report)
        code = quality_metrics.report_code(report)  # D-431: «C-7» in the construction series, «N° 1» in the weekly
        assert line.startswith(f"{code} · {report['fecha']}") and f"{within} / {measured}" in line
        assert f"<li><b>No conformidades:</b> {nonconforming}</li>" in quality_method.build_report_detail(
            report, reports
        )


def load_reports_module():
    sys.path.insert(0, str(ROOT / "scripts"))
    import informe_calidad

    return informe_calidad


def test_d331_the_reports_are_numbered_frozen_and_the_latest_is_the_markdown():
    informe_calidad = load_reports_module()
    # D-431: the construction series stays as written, C-1 to C-7, and is never rebuilt with today's rules
    reports = quality_metrics.read_series(quality_metrics.SERIES_BUILD)
    assert [report["numero"] for report in reports] == list(range(1, 8))
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    for report in reports:
        assert report["titulo"] == f"Informe de calidad N° {report['numero']}" and "sqap" not in report
        assert (
            report["codigo_evaluado"] == report["medicion"]["commit"]
            and report["fecha"] == report["medicion"]["generado"]
        )
        assert report["anterior"] == (report["numero"] - 1 or None)
        # The report keeps the acceptables it was judged against and, per indicator, what the reader needs.
        # D-475: the two indicators added after the series closed are not in it
        assert set(report["aceptables"]) == {key for key, *_ in quality_metrics.INDICATORS} - ADDED_AFTER_BUILD
        for row in report["indicadores"]:
            assert {"valor", "falla", "falla_aceptable", "estado", "insight", "variacion"} <= set(row)
        # Rebuilt today from its own frozen measurement and acceptables, it says the same: nothing was edited.
        previous = reports[report["numero"] - 2] if report["numero"] > 1 else None
        rebuilt = quality_metrics.evaluate(
            report["medicion"],
            report["aceptables"],
            {**policy, "modo_datos": report["modo_datos"]},
            previous["medicion"] if previous else None,
        )
        rebuilt = [row for row in rebuilt if row["clave"] in report["aceptables"]]
        assert [row["estado"] for row in rebuilt] == [row["estado"] for row in report["indicadores"]]
    # The first reports are the measurements of the history, without anything made up.
    assert [report["codigo_evaluado"] for report in reports[:4]] == ["cf561e7", "6c6286c", "d66804c", "b015e3a"]
    assert {row["clave"]: row["estado"] for row in reports[0]["indicadores"]}["comparables_pct"] == "sin_medicion"
    text = (ROOT / "docs" / "calidad" / "INFORME.md").read_text(encoding="utf-8")
    weekly = informe_calidad.read_reports()
    if weekly:  # the latest weekly report; until the first one, INFORME.md keeps C-7 as it was written
        assert text == informe_calidad.render_markdown(weekly[-1], policy)
    else:
        assert text.startswith("# Informe de calidad N° 7")
    assert "```" not in text and not any(word in text.lower() for word in FORBIDDEN)


def test_d331_a_report_is_never_rewritten_and_the_pull_request_compares_with_the_previous(tmp_path):
    informe_calidad = load_reports_module()
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    first, new = informe_calidad.add_report(REPORT, goals, policy, folder=tmp_path)
    assert new and first["numero"] == 1 and (tmp_path / "informe-001.json").exists()
    again, new = informe_calidad.add_report(REPORT, goals, policy, folder=tmp_path)
    assert not new and len(list(tmp_path.glob("informe-*.json"))) == 1  # the same measurement adds nothing
    # D-431: a weekly report holds only the three data indicators of the load, and the SQAP version it was measured by
    assert [row["clave"] for row in first["indicadores"]] == list(quality_metrics.WEEKLY_INDICATORS)
    assert set(first["aceptables"]) == set(quality_metrics.WEEKLY_INDICATORS) and first["serie"] == "semanal"
    assert first["sqap"] == quality_metrics.sqap_version() and first["sqap"]
    fixed = dict(REPORT, commit="def5678", generado="2026-11-03 12:00 UTC")
    second, new = informe_calidad.add_report(fixed, goals, policy, folder=tmp_path)
    assert new and second["numero"] == 2 and second["anterior"] == 1
    body = informe_calidad.build_pull_request(second, first, policy)
    within, nonconforming, measured = informe_calidad.counts(second)
    assert "Informe semanal de calidad N° 2" in body and "comparada con el informe N° 1" in body
    assert f"{within} de {measured} indicadores dentro de lo aceptable" in body
    with pytest.raises(FileExistsError):  # the file mode refuses to overwrite a report
        with open(tmp_path / "informe-001.json", "x", encoding="utf-8"):
            pass


def test_d332_the_header_and_the_report_detail_never_claim_an_external_attestation(monkeypatch):
    for series in (quality_metrics.SERIES_WEEKLY, quality_metrics.SERIES_BUILD):
        reports = quality_metrics.read_series(series)
        for english in (False, True):
            monkeypatch.setattr(i18n, "is_english", lambda english=english: english)
            for report in reports:
                text = quality_method.build_header(report) + quality_method.build_report_detail(report, reports)
                assert not any(word in text.lower() for word in FORBIDDEN), (series, english, report["numero"])


@pytest.mark.parametrize("language", ["es", "en"])
def test_d571_the_page_is_the_archive_of_the_reports_and_the_quality_section_holds_it_in_both_languages(language):
    """No tabs: one line with the latest report and its counts, then the reports, newest first. The indicators of
    today live in «Controles de datos» and the failures in «Cambios e incidentes», never here."""
    english = language == "en"
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params.update({"perfil": "profesional", "lang": language, "vista": "Método y calidad"})
    app.run()
    assert not app.exception and len(app.tabs) == 0
    menu = " ".join(block.value for block in app.sidebar.markdown)
    assert "Quality self-assessment" not in menu and "Autoevaluación de calidad ·" not in menu  # D-343: gone
    labels = [link.proto.label for link in app.sidebar.get("page_link")]
    audit, method = ("Data controls", "Quality plan") if english else ("Controles de datos", "Plan de calidad")
    assert labels.index(audit) == labels.index(method) + 1  # D-343, D-507: the two sit together in «Calidad»
    reports = quality_metrics.read_reports()
    within, nonconforming, measured = quality_metrics.report_counts(reports[-1])
    counts = (
        f"{within} of {measured} within the acceptable · {nonconforming} non-conformit"
        if english
        else f"{within} de {measured} dentro de lo aceptable · {nonconforming} no conformidad"
    )
    head = next(block.value for block in app.markdown if 'class="qm-head"' in block.value)
    assert f"{quality_metrics.report_name(reports[-1], english)} · {str(reports[-1]['fecha'])[:10]} · {counts}" in head
    rows = [str(button.label) for button in app.button if str(button.key).startswith("cr_reports_toggle_")]
    newest = [f"{quality_metrics.report_code(report, english)} · {report['fecha']} · " for report in reports[::-1]]
    newest = newest[: compact_table.PAGE_SIZE]  # the list shows one page of rows at a time
    assert len(rows) == len(newest) and all(row.startswith(start) for row, start in zip(rows, newest)), rows
    content = " ".join(block.value for block in app.markdown if "qm-" in block.value)
    assert 'class="qm-group' not in content and "qm-row" not in content and "qm-overview" not in content
    markup = " ".join(block.value for block in app.markdown)
    assert "Últimas fallas" not in markup and "Latest failures" not in markup
    assert not re.search(r"month_start|>None<|\bnan\b", content)


# endregion


# region Acceptables, goals and insights (D-330)
def test_d330_metas_keeps_the_approved_indicators_with_their_explanation():
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    keys = [key for key, *_ in quality_metrics.INDICATORS]
    assert set(keys) == {key for key in goals if key != "nota"} and len(keys) == 14  # D-475: 12 and two of data
    assert sum(goals[key]["tipo"] == "datos" for key in keys) == 6
    for key in keys:
        goal = goals[key]
        assert ("max" in goal) != ("min" in goal) and "meta" in goal and "margen_critico" in goal, key
        assert all(len(goal[field]) == 2 and all(goal[field]) for field in ("que_mide", "por_que", "como", "accion"))
    # The approved numbers (2026-10-29).
    assert goals["cobertura_total"]["min"] == 90 and goals["cobertura_por_modulo"]["min"] == 70
    assert goals["comparables_pct"]["min"] == 97 and goals["vigencia_dias"]["max"] == 8  # D-475: the 5th percentile
    assert goals["comparables_pct"]["meta"] == 97  # the goal goes with the acceptable, as in every indicator (D-337)
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
    report = dict(REPORT, datos={"pct_comparacion": 90.0, "pct_rechazadas": 0.01, "dias_desde_ultima_carga": 7})
    rows = {row["clave"]: row for row in quality_metrics.evaluate(report, goals, policy)}
    comparables = rows["comparables_pct"]
    assert (comparables["falla"], comparables["falla_aceptable"], comparables["estado"]) == (10.0, 3, "urgente")
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
def test_d333_the_viewer_has_four_slides_read_from_the_report_and_compares_with_the_previous():
    from bi import quality_viewer

    reports = quality_metrics.read_series(quality_metrics.SERIES_BUILD)
    _, goals, policy = quality_method.read_page()
    # The latest report whose failing tests are a non-conformity (N° 4): its cause is the author's and the viewer shows it.
    latest = next(
        report
        for report in reversed(reports)
        if any(
            row["clave"] == "pruebas_fallidas" and row["estado"] in ("urgente", "critico")
            for row in report["indicadores"]
        )
    )
    record = {
        "informe": latest["numero"],
        "indicador": "pruebas_fallidas",
        "causa": "Enlaces del repositorio sin renombrar.",
        "accion": "",
        "estado": "cerrada",
    }
    page = quality_viewer.build_viewer_html(reports, latest["numero"], goals, policy, [record], [])
    assert page.startswith("<!doctype html>") and page.count('<section class="slide') == 4  # D-431
    assert f"Informe de calidad C-{latest['numero']}" in page and latest["codigo_evaluado"] in page
    assert "Enlaces del repositorio sin renombrar." in page and "cerrada" in page  # the author's cause and state
    assert '"a": ' + str(latest["anterior"]) in page and "Serie de construcción" in page
    assert "window.print()" in page and "requestFullscreen" in page and "ArrowRight" in page
    assert not any(word in page.lower() for word in FORBIDDEN)
    # Report C-2 covers from C-1's date to its own: an incident on its day is a row of the one table (D-431).
    second = reports[1]
    incident = [
        {
            "fecha": second["fecha"][:10],
            "fuente": "ODEPA",
            "indicador": "comparables_pct",
            "causa": ["La fuente se atrasó.", "The source was late."],
            "respuesta": ["Se muestra el último dato.", "The last data is shown."],
        }
    ]
    english = quality_viewer.build_viewer_html(reports, second["numero"], goals, policy, [], incident, True)
    assert "Quality report C-2" in english and "Download PDF" in english and "External incident · ODEPA" in english
    assert "The source was late." in english and "The last data is shown." in english
    assert "Qué falló" not in english and "Comparación" not in english and "La fuente se atrasó." not in english


def test_d333_the_reports_tab_filters_by_year_month_week_and_search_and_links_each_report(construction_series):
    from bi import dashboard

    reports, _, _ = quality_method.read_page()
    every = dashboard.ALL_VALUES
    assert dashboard.filter_reports(reports, every, every, every, "") == reports
    assert [r["numero"] for r in dashboard.filter_reports(reports, every, every, every, "b015e3a")] == [4]
    assert [r["numero"] for r in dashboard.filter_reports(reports, every, every, every, "N° 2")] == [2]
    assert dashboard.filter_reports(reports, "2025", every, every, "") == []
    # D-399: each week filters the reports of that week, whatever the weeks are; N° 1 has no data week.
    weeks = {report["semana"] for report in reports if report["semana"]}
    for week in weeks:
        expected = [report["numero"] for report in reports if report["semana"] == week]
        found = dashboard.filter_reports(reports, week[:4], week[5:7], week, "")
        assert [report["numero"] for report in found] == expected, week
    assert sum(1 for report in reports if report["semana"]) == len(reports) - 1
    detail = quality_method.build_report_detail(reports[2], reports[2:3] + reports[:1] + reports[1:2])
    assert "<b>Variación:</b> +2" in detail  # N° 3 against N° 2, though only N° 3 is listed


# endregion


# region Non-conformities, mitigation and external incidents (D-334)
def test_d334_every_nonconformity_of_the_reports_is_registered_and_the_author_writes_action_and_state(
    construction_series,
):
    folder = quality_metrics.FOLDER
    records = quality_metrics.read(folder / "no_conformidades.json")["registros"]
    found = {
        (report["numero"], row["clave"])
        for report in quality_metrics.read_reports()
        for row in report["indicadores"]
        if row["estado"] in ("urgente", "critico")
    }
    assert {(item["informe"], item["indicador"]) for item in records} == found
    for item in records:  # the author's to write: both empty, or both written in the two languages (D-419)
        written = (item["accion"], item["estado"])
        assert written == ("", "") or all(isinstance(text, list) and len(text) == 2 and all(text) for text in written)
    plan = quality_metrics.read(folder / "plan_mitigacion.json")["fallas"]
    assert [item["id"] for item in plan] == [f"F-{n:02d}" for n in range(1, len(plan) + 1)]
    assert {item["causa"] for item in plan} == {"interna", "externa"}
    # D-342: every failure has its category, its station of the git flow (1 to 15) and its occurrences
    assert {item["categoria"] for item in plan} <= {"datos", "código", "operación"} and "operación" in {
        item["categoria"] for item in plan
    }
    assert all(isinstance(item["estacion"], int) and 1 <= item["estacion"] <= 15 for item in plan)
    keys = {"fecha", "ocurrencia", "diagnostico", "solucion", "comentario", "estacion", "estado", "referencia"}
    for item in plan:
        for occurrence in item["ocurrencias"]:
            assert set(occurrence) == keys and occurrence["estado"] in ("abierta", "resuelta")
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", occurrence["fecha"]) and 1 <= occurrence["estacion"] <= 15
            for text in ("ocurrencia", "diagnostico", "solucion", "comentario"):  # Spanish and English, both written
                assert len(occurrence[text]) == 2 and all(occurrence[text])
    assert sum(len(item["ocurrencias"]) for item in plan if item["categoria"] == "operación") >= 8
    incidents = quality_metrics.read(folder / "incidentes_externos.json")
    assert incidents["respuestas_por_defecto"]["estado"] == "pendiente de aprobación del autor"
    assert isinstance(incidents["registros"], list)
    for record in incidents["registros"]:  # D-418: each incident says what, why and the answer, in both languages
        assert {"fecha", "fuente", "tipo", "que_paso", "causa", "respuesta", "estado", "referencia"} <= set(record)
        assert record["tipo"] in incidents["respuestas_por_defecto"] and record["fuente"] in ("ODEPA", "INE")
        assert all(len(record[text]) == 2 and all(record[text]) for text in ("que_paso", "causa", "respuesta"))


# endregion


# region The author's alert and the automatic diagnosis (D-335)
def test_d335_the_diagnosis_says_what_failed_where_since_when_and_whose_cause_without_a_secret(construction_series):
    every, goals, policy = quality_method.read_page()
    # The history these checks read: N° 1 to 4, when the failing tests were out of their acceptable in a row.
    reports = [report for report in every if report["numero"] <= 4]
    latest = reports[-1]
    failed = next(row for row in latest["indicadores"] if row["clave"] == "pruebas_fallidas")
    es, en = quality_metrics.diagnose(failed, latest, reports, policy)
    assert "pruebas fallan" in es["donde"] and "tests fail" in en["donde"]
    assert "informe N° 1" in es["desde"]  # out of its acceptable in all four reports, without a break
    cut = quality_metrics.diagnose({"clave": "ruff_avisos", "tipo": "codigo", "valor": 3}, reports[1], reports, policy)
    assert "informe N° 1" in cut[0]["desde"]  # Ruff: critical in N° 1 and N° 2, then fixed
    first = quality_metrics.diagnose(
        {"clave": "mypy_errores", "tipo": "codigo", "valor": 2}, reports[2], reports, policy
    )
    assert "Primera vez" in first[0]["desde"]
    assert es["origen"] == policy["diagnostico"]["origen_codigo"][0]
    data = quality_metrics.diagnose({"clave": "vigencia_dias", "tipo": "datos", "valor": 9}, latest, reports, policy)
    assert "puede ser interna o de la fuente" in data[0]["origen"]
    text = " ".join(" ".join(item.values()) for item in (es, en)).lower()
    assert not any(word in text for word in ("token", "password", "/users/", "secret"))


def test_d335_the_alert_lists_the_critical_first_with_everything_the_author_needs_and_nothing_else(
    construction_series, monkeypatch
):
    monkeypatch.setattr(i18n, "is_english", lambda: False)
    reports, goals, policy = quality_method.read_page()
    two = next(report for report in reports if report["numero"] == 2)
    html_text = quality_method.build_alert(
        [two], goals, policy, [], lambda report: f"?informe={quality_metrics.report_ref(report)}", "27-10"
    )
    assert html_text.index("Crítico · Pruebas que fallan") < html_text.index("Crítico · Avisos de Ruff")
    for needle in (
        "Por qué importa",
        "Qué falló",
        "Causa",
        "Acción sugerida",
        "Última medición",
        "2026-10-26"[:0],
        "informe=C2",
    ):
        assert needle in html_text
    assert "La carga del 27-10 falló" in html_text and "no_conformidades.json" in html_text
    recorded = [
        {"informe": 2, "indicador": "pruebas_fallidas", "causa": ["Enlaces sin renombrar.", "Links not renamed."]}
    ]
    assert "Enlaces sin renombrar." in quality_method.build_alert([two], goals, policy, recorded)
    clean = dict(two, indicadores=[dict(row, estado="cumple") for row in two["indicadores"]])
    # all well: nothing; F-43: measured on the report's own day, so the test does not age with the calendar (D-361)
    assert quality_method.build_alert([clean], goals, policy, [], today=date.fromisoformat(two["fecha"][:10])) == ""
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    assert "Action required" not in html_text and "Why it matters" in quality_method.build_alert(
        [two], goals, policy, []
    )


def test_d335_the_new_reports_store_their_diagnosis_and_the_old_ones_are_not_touched():
    informe_calidad = load_reports_module()
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    reports = quality_metrics.read_series(quality_metrics.SERIES_BUILD)
    stored = [
        row for report in reports if report["numero"] <= 4 for row in report["indicadores"] if "diagnostico" in row
    ]
    assert stored == []  # N° 1 to 4 were frozen before the diagnosis existed: never rewritten
    for report in reports[4:]:  # the later ones keep the diagnosis of what was out of its acceptable
        assert all(
            len(row["diagnostico"]) == 2 for row in report["indicadores"] if row["estado"] in ("urgente", "critico")
        )
    report = informe_calidad.build_report(5, dict(REPORT, datos={"pct_comparacion": 70.0}), goals, policy, None, [])
    broken = [row for row in report["indicadores"] if row["estado"] in ("urgente", "critico")]
    assert broken and all(len(row["diagnostico"]) == 2 for row in broken)


@pytest.mark.parametrize("unlocked", [False, True])
def test_d335_only_the_author_session_can_be_alerted_and_the_visit_never_breaks(unlocked):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params.update({"lang": "es"})
    app.session_state["visitor_profile"] = "profesional"
    if unlocked:
        app.session_state["admin_unlocked"] = True
    app.run()
    assert not app.exception
    # D-431: only when the latest report still has something open (the construction series ended all closed)
    reports, _, _ = quality_method.read_page()
    register = quality_metrics.read(quality_metrics.FOLDER / "no_conformidades.json")["registros"]
    pending = bool(reports) and bool(quality_method.open_rows(reports[-1], register))
    assert ("quality_alert_seen" in app.session_state and app.session_state["quality_alert_seen"]) == (
        unlocked and pending
    )


# endregion


# region The viewer as a presentation (D-347)
def test_d347_the_viewer_is_a_presentation_with_thumbnails_counter_fullscreen_and_a_fade():
    from bi import quality_viewer

    reports, goals, policy = quality_method.read_page()
    for english in (False, True):
        page = quality_viewer.build_viewer_html(reports, reports[-1]["numero"], goals, policy, [], [], english)
        assert page.count('<section class="slide') == 4  # D-431
        assert (
            "id='thumbs'" in page and "id='stage'" in page and "id='canvas'" in page
        )  # thumbnails left, slide centred
        assert "width:960px;height:540px" in page  # one 16:9 canvas that is scaled to the stage
        assert "grid-template-columns:168px" in page and "grid-template-rows:minmax(0,1fr) auto" in page  # strip below
        assert "pos.textContent=(at+1)+' / '+slides.length" in page  # the counter «3 / 4»
        assert "transition:opacity" in page and "translate" not in page.split("<style>")[1].split("</style>")[
            0
        ].replace("translate(-", "")  # a fade, not a slide of the page
        assert "ArrowRight" in page and "ArrowLeft" in page and "requestFullscreen" in page and "window.print()" in page
        assert 'id="cmp-a"' in page and 'id="cmp-b"' in page  # «Comparar con…» stays
        assert ("Download PDF" if english else "Descargar PDF") in page and (
            "Slides" if english else "Diapositivas"
        ) in page
        assert "classList.toggle('current'" in page  # the current thumbnail is highlighted
        assert "@media print" in page and "page-break-after:always" in page  # the PDF still prints every slide


# endregion


# region The failure log and old alerts
def test_d354_each_occurrence_is_one_short_line_per_field_and_the_policy_says_so():
    plan = quality_metrics.read(quality_metrics.FOLDER / "plan_mitigacion.json")["fallas"]
    for item in plan:
        for occurrence in item["ocurrencias"]:
            for field in ("ocurrencia", "diagnostico", "solucion", "comentario"):
                for text in occurrence[field]:
                    assert "\n" not in text and len(text) <= 160, (item["id"], field, text)
    rule = quality_metrics.read(quality_metrics.POLICY_FILE)["registro_de_fallas"]["regla"]
    assert rule[0].startswith("Cada ocurrencia del registro") and rule[1].startswith("Each occurrence of the register")
    assert "una línea por campo" in (quality_metrics.FOLDER / "README.md").read_text(encoding="utf-8")


def test_d361_an_alert_from_an_old_report_says_it_is_old_and_is_not_shown_as_todays_critical(construction_series):
    from datetime import date

    reports, goals, policy = quality_method.read_page()
    latest = dict(reports[-1], fecha="2026-10-27 11:37 UTC")
    latest["indicadores"] = [
        dict(row, estado="critico") if row["clave"] == "pruebas_fallidas" else row for row in latest["indicadores"]
    ]
    fresh = quality_method.build_alert([latest], goals, policy, [], today=date(2026, 10, 30))
    old = quality_method.build_alert([latest], goals, policy, [], today=date(2026, 11, 5))
    assert "qm-alert-stale" not in fresh and "qm-critico" in fresh  # 3 days: today's state
    assert "Última medición del 27-10: puede no reflejar el estado actual." in old  # 9 days: an old picture
    assert "qm-critico" not in old and "qm-antigua" in old
    assert quality_method.is_stale(latest, date(2026, 11, 4)) is False and quality_method.is_stale(
        latest, date(2026, 11, 5)
    )


def test_d363_a_push_only_measures_and_the_report_comes_only_after_a_weekly_load_in_green():
    workflow = (ROOT / ".github" / "workflows" / "calidad.yml").read_text(encoding="utf-8")
    triggers = workflow.split("permissions:")[0]
    assert "  push:" in triggers and "  workflow_dispatch:" in triggers
    assert "  workflow_run:\n    workflows: [semanal]\n    types: [completed]" in triggers  # active, not commented out
    step = workflow.split("- name: Proponer el informe al autor")[1].split("- name:")[0]
    # D-431: never by hand nor after a failed load, so never in the middle of a deployment
    assert "github.event_name == 'workflow_run' && github.event.workflow_run.conclusion == 'success'" in step
    assert "workflow_dispatch" not in step.split("run:")[0]
    gate = workflow.split("- name: Fallar si un indicador de código pasa lo aceptable")[1]
    assert (
        "github.event_name" not in gate.split("run:")[0]
    )  # every run, a push included, still fails past the acceptable


def test_d401_creating_a_report_registers_its_nonconformities_once(tmp_path):
    informe_calidad = load_reports_module()
    register = tmp_path / "no_conformidades.json"
    register.write_text('{\n  "nota": "x",\n  "registros": []\n}\n', encoding="utf-8")
    report = {
        "numero": 9,
        "fecha": "2026-11-03 13:00 UTC",
        "indicadores": [
            {"clave": "pruebas_fallidas", "estado": "critico"},
            {"clave": "comparables_pct", "estado": "urgente"},
            {"clave": "cobertura_total", "estado": "cumple"},
        ],
    }
    assert informe_calidad.register_nonconformities(report, register) == 2
    assert informe_calidad.register_nonconformities(report, register) == 0  # a second run adds nothing
    rows = json.loads(register.read_text(encoding="utf-8"))["registros"]
    assert [(row["informe"], row["indicador"], row["fecha"]) for row in rows] == [
        (9, "pruebas_fallidas", "2026-11-03"),
        (9, "comparables_pct", "2026-11-03"),
    ]
    assert all(row["causa"] == row["accion"] == row["estado"] == "" for row in rows)  # the author's to write
    workflow = (ROOT / ".github" / "workflows" / "calidad.yml").read_text(encoding="utf-8")
    assert "docs/calidad/no_conformidades.json" in workflow  # the pull request carries them


def test_d419_the_alert_hides_what_is_resolved_reads_the_external_incident_and_writes_each_language(
    construction_series, monkeypatch
):
    reports, goals, policy = quality_method.read_page()
    register = quality_metrics.read(quality_metrics.FOLDER / "no_conformidades.json")["registros"]
    incidents = quality_metrics.read(quality_metrics.FOLDER / "incidentes_externos.json")["registros"]
    latest = reports[-1]
    # D-431: the construction series ended with its open non-conformities closed, so its alert is empty; the rules are
    # checked on the register as it was before that closing. F-43: read on the day of its report, so the notice of an
    # old measurement (D-361) does not depend on the day the test runs (D-564)
    measured = date.fromisoformat(str(latest["fecha"])[:10])
    assert (
        quality_method.build_alert(reports, goals, policy, register, today=measured, incidents=incidents) == ""
        or reports[-1].get("serie") == quality_metrics.SERIES_WEEKLY
    )
    nonconformities = [
        dict(item, estado="", accion="") if str((item.get("estado") or [""])[0]).startswith("cerrad") else item
        for item in register
    ]
    for language in (False, True):
        monkeypatch.setattr(i18n, "is_english", lambda english=language: english)
        alert = quality_method.build_alert(reports, goals, policy, nonconformities, incidents=incidents)
        # a figure is «723 of 868» in English and «723 de 868» in Spanish, never the other language's word
        assert not re.search(r"\d de \d" if language else r"\d of \d", alert), alert
        for row in latest["indicadores"]:
            record = quality_method.record_of(latest, row, nonconformities)
            if quality_metrics.is_resolved(record):  # a resolved non-conformity does not appear
                assert html.escape(quality_method.t(*row["nombre"])) not in alert
        for incident in incidents:
            row = next((item for item in latest["indicadores"] if item["clave"] == incident.get("indicador")), None)
            if row and quality_metrics.incident_for(row, latest, reports, incidents) is incident:
                assert html.escape(quality_method.t(*incident["causa"])) in alert  # the cause the incident wrote
    assert quality_metrics.is_resolved({"estado": ["resuelta", "resolved"]}) and quality_metrics.is_resolved(
        {"estado": "Resuelta"}
    )
    assert not quality_metrics.is_resolved({"estado": ""}) and not quality_metrics.is_resolved({})
    assert quality_metrics.is_resolved({"estado": ["cerrada", "closed"]})  # D-431
    figures = quality_metrics.where_text("comparables_pct", {"datos": {"con_comparacion": 7, "precios_semana": 9}}, {})
    english = quality_metrics.where_text(
        "comparables_pct", {"datos": {"con_comparacion": 7, "precios_semana": 9}}, {}, english=True
    )
    assert figures["detalle"] == "7 de 9" and english["detalle"] == "7 of 9"


# endregion


# region The weekly report (D-431)
def test_d431_the_weekly_report_is_four_pages_measured_by_the_sqap_with_one_table_of_issues(tmp_path):
    from bi import quality_viewer

    informe_calidad = load_reports_module()
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    low = dict(REPORT, datos={"pct_comparacion": 80.0, "con_comparacion": 8, "precios_semana": 10})
    first, _ = informe_calidad.add_report(low, goals, policy, folder=tmp_path)
    reports = informe_calidad.read_reports(tmp_path)
    record = {
        "informe": 1,
        "serie": "semanal",
        "indicador": "comparables_pct",
        "fecha": "2026-11-03",
        "causa": "Una causa.",
    }
    old = {"informe": 1, "indicador": "comparables_pct", "causa": "De la serie de construcción."}
    page = quality_viewer.build_viewer_html(reports, 1, goals, policy, [record, old], [], sqap_url="https://x/sqap")
    slides = page.count('<section class="slide')
    assert slides == 4 and "Informe semanal de calidad N° 1" in page
    assert f'<a href="https://x/sqap" target="_blank" rel="noopener">SQAP v{first["sqap"]}</a>' in page
    assert "Qué medimos y por qué" not in page and "Cómo se mide" not in page and "Anexo técnico" not in page
    # one table: indicator, state, cause, disposition, date; only the records of this series
    assert "<th>Indicador</th><th>Estado</th><th>Causa</th><th>Disposición</th><th>Fecha</th>" in page
    assert "Una causa." in page and "De la serie de construcción." not in page
    # the code and the days since the last load are not in it
    assert {row["clave"] for row in first["indicadores"]} == set(quality_metrics.WEEKLY_INDICATORS)
    assert (
        set(quality_metrics.WEEKLY_INDICATORS)
        == {"pruebas_dbt_pct", "comparables_pct", "rechazadas_pct"} | ADDED_AFTER_BUILD
    )
    # the comparison warns when the two reports do not measure the same indicators
    assert "cmp-warn" in page and "no miden los mismos indicadores" in page


def test_d431_the_construction_series_is_named_c_and_opens_by_its_own_address():
    built = quality_metrics.read_series(quality_metrics.SERIES_BUILD)
    assert [quality_metrics.report_code(item) for item in built] == [f"C-{n}" for n in range(1, 8)]
    assert quality_metrics.report_ref(built[-1]) == "C7" and quality_metrics.find_report("C7")[1] == 7
    assert quality_metrics.find_report("C9") is None and quality_metrics.find_report("x") is None
    weekly = {"numero": 1, "serie": "semanal"}
    assert quality_metrics.report_name(weekly) == "Informe semanal de calidad N° 1"
    assert quality_metrics.report_name(weekly, True) == "Weekly quality report No. 1"
    assert quality_metrics.report_ref(weekly) == "1"
    # a non-conformity of the weekly N° 1 is not the one of C-1
    assert not quality_metrics.same_report({"informe": 1, "indicador": "x"}, weekly)
    assert quality_metrics.same_report({"informe": 1, "serie": "semanal"}, weekly)


# endregion


# region Thresholds and causes
def test_d433_the_comparable_prices_acceptable_is_the_fifth_percentile_and_the_closed_reports_keep_theirs():
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    goal = goals["comparables_pct"]
    # D-475: measured over the prices that had one the week before, the 5th percentile is 97 %
    assert (goal["min"], goal["meta"], goal["margen_critico"]) == (97, 97, 10)
    # 98.1 %, the week of 2026-10-26 measured that way: within the acceptable, not a non-conformity
    assert quality_metrics.state(98.1, goal) == "cumple" and quality_metrics.state(90.0, goal) == "urgente"
    assert quality_metrics.state(86.9, goal) == "critico"
    rows = quality_metrics.evaluate({"datos": {"pct_comparacion": 98.1}}, goals, policy)
    assert {row["clave"]: row["estado"] for row in rows}["comparables_pct"] == "cumple"
    # C-1 to C-7 are closed records: they keep the 90 % they were measured with and are never evaluated again
    for report in quality_metrics.read_series(quality_metrics.SERIES_BUILD):
        frozen = report["aceptables"]["comparables_pct"]
        assert frozen["min"] == 90, report["numero"]
    seventh = quality_metrics.read_series(quality_metrics.SERIES_BUILD)[-1]
    assert {row["clave"]: row["estado"] for row in seventh["indicadores"]}["comparables_pct"] == "urgente"
    adr = i18n.document_path("ADR.md", "es").read_text(encoding="utf-8")
    assert "## ADR-36" in adr and "| 5 | 81,2 % |" in adr and "no una relajación del estándar" in adr


def test_d434_the_cause_of_the_incident_is_the_measured_one():
    incident = next(
        item
        for item in quality_metrics.read(quality_metrics.FOLDER / "incidentes_externos.json")["registros"]
        if item.get("referencia") == "D-418"
    )
    spanish, english = incident["causa"]
    assert "más de 12 semanas" in spanish and "73" in spanish and "58" in spanish and "14" in spanish
    assert "73" in english and "scripts/semanas_sin_precio.py --semana 2026-10-26" in english
    decisions = (ROOT / "docs" / "DECISIONES.md").read_text(encoding="utf-8")
    d418 = decisions.split("## D-418 ")[1].split("\n## ")[0]
    assert "**Corrección (D-434):**" in d418 and "Era incorrecta" in d418
    from bi import queries

    if not queries.DATABASE_FILE.exists():
        pytest.skip("Sin la Base DuckDB no se puede volver a medir")
    sys.path.insert(0, str(ROOT / "scripts"))
    import semanas_sin_precio

    found = semanas_sin_precio.count_gaps(queries.run_query("k6_national_weekly_price"), "2026-10-26")
    # D-520: the unit rule adds a price to that week and shortens one gap: the first figures hold until the next load
    # publishes it, the second ones after it. D-521 and D-522 are in the second ones too. D-578: ODEPA added six late
    # prices to that week, all with a comparison, in the load of 10 November; the gaps did not change.
    assert (found["prices"], found["without"]) in ((868, 145), (869, 150), (875, 150))
    gaps = (found["one_week"], found["two_to_twelve"], found["over_twelve"], found["never"])
    assert gaps in ((14, 58, 73, 0), (19, 59, 72, 0))  # D-522: five prices that only changed package join the first
    fruit_and_vegetables = found["groups"].get("Frutas", 0) + found["groups"].get("Hortalizas", 0)
    assert fruit_and_vegetables in (141, 146) and found["without"] - fruit_and_vegetables == 4


def test_d436_the_report_is_merged_by_itself_only_with_the_code_in_range_and_an_open_one_is_replaced():
    workflow = (ROOT / ".github" / "workflows" / "calidad.yml").read_text(encoding="utf-8")
    step = workflow.split("- name: Proponer el informe al autor")[1].split("- name:")[0]
    lines = [line.strip() for line in step.splitlines() if not line.strip().startswith("#")]
    code = "\n".join(lines)
    # an earlier report still open is closed and its branch deleted before the new one takes its number
    assert code.index("gh pr close") < code.index("informe_calidad.py") < code.index("gh pr create")
    assert '.title == "Actualizar medición de calidad"' in code and "--delete-branch" in code
    # merged directly, only when «verificar» (the code indicators) passed; never GitHub's --auto
    merge = code.split("gh pr create")[1]
    assert 'if [ "${{ steps.verificar.outcome }}" = "success" ]; then' in merge
    assert 'gh pr merge "$branch" --squash --delete-branch' in merge and "--auto" not in code
    assert "::warning::" in merge  # a refused merge leaves the request open and says so
    assert "steps.verificar.outcome == 'failure'" in workflow  # the code out of range still fails the run


def test_d437_a_weekly_non_conformity_closes_by_itself_when_its_indicator_is_back_and_the_construction_series_is_untouched(
    tmp_path,
):
    informe_calidad = load_reports_module()
    register = {
        "nota": "",
        "registros": [
            {
                "informe": 1,
                "serie": "semanal",
                "indicador": "comparables_pct",
                "causa": "",
                "accion": "Revisé.",
                "estado": "",
            },
            {"informe": 1, "serie": "semanal", "indicador": "rechazadas_pct", "causa": "", "accion": "", "estado": ""},
            {"informe": 1, "indicador": "comparables_pct", "causa": "", "accion": "", "estado": ""},  # construction
            {"informe": 2, "serie": "semanal", "indicador": "pruebas_dbt_pct", "causa": "", "accion": "", "estado": ""},
        ],
    }
    path = tmp_path / "no_conformidades.json"
    path.write_text(json.dumps(register, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "numero": 2,
        "serie": "semanal",
        "indicadores": [
            {"clave": "comparables_pct", "estado": "cumple"},
            {"clave": "rechazadas_pct", "estado": "urgente"},
            {"clave": "pruebas_dbt_pct", "estado": "cumple"},
        ],
    }
    assert informe_calidad.close_back_in_range(report, path) == 1
    records = json.loads(path.read_text(encoding="utf-8"))["registros"]
    assert records[0]["estado"] == ["resuelta automáticamente, informe N° 2", "resolved automatically, report No. 2"]
    assert records[0]["accion"] == "Revisé." and quality_metrics.is_resolved(records[0])  # the author's text stays
    assert records[1]["estado"] == ""  # still out of its acceptable
    assert records[2]["estado"] == ""  # the construction series is never touched (D-431)
    assert records[3]["estado"] == ""  # opened by this same report: only a later report closes it
    assert informe_calidad.close_back_in_range(report, path) == 0  # a second run closes nothing more


def test_d475_comparables_count_only_last_weeks_prices_and_two_data_indicators_watch_absences_and_outliers():
    """B: the comparison is measured over the prices that also had one the week before, the reappearances apart; C: a
    region or channel that stops reporting, and a week with too many atypical prices, are indicators of their own."""
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    assert (goals["ausencias_region_canal"]["max"], goals["ausencias_region_canal"]["medida"]) == (0, "conteo")
    assert (goals["atipicos_pct"]["max"], goals["atipicos_pct"]["margen_critico"]) == (
        0.25,
        0.25,
    )  # the 95th percentile
    data = {
        "con_semana_anterior": 737,
        "con_comparacion": 723,
        "pct_comparacion": 98.1,
        "reapariciones": 131,
        "regiones_ausentes": ["Región de Los Lagos"],
        "canales_ausentes": [],
        "regiones_canales_ausentes": 1,
        "precios_atipicos": 12,
        "precios_semana_base": 3300,
        "pct_atipicos": 0.364,
    }
    rows = {row["clave"]: row for row in quality_metrics.evaluate({"datos": data}, goals, policy)}
    assert rows["comparables_pct"]["estado"] == "cumple"
    assert rows["ausencias_region_canal"]["estado"] == "urgente" and rows["atipicos_pct"]["estado"] == "urgente"
    measured = {"datos": data}
    assert quality_metrics.where_text("comparables_pct", measured, {})["detalle"] == "723 de 737"
    assert quality_metrics.where_text("ausencias_region_canal", measured, {})["detalle"] == "Región de Los Lagos"
    assert quality_metrics.where_text("atipicos_pct", measured, {}, english=True)["detalle"] == "12 of 3300"
    # a share under 1 % keeps two decimals, so the acceptable is not rounded away
    assert quality_metrics.show(0.25, "%") == "0,25 %" and quality_metrics.goal_text(goals["atipicos_pct"]) == "≤ 0,25"
    assert quality_metrics.show(98.1, "%") == "98,1 %"
    measurement = quality_metrics.read(quality_metrics.REPORT_FILE)["datos"]
    assert measurement["con_comparacion"] <= measurement["con_semana_anterior"] <= measurement["precios_semana"]
    assert measurement["reapariciones"] == measurement["precios_semana"] - measurement["con_semana_anterior"]
    sqap = quality_metrics.SQAP_FILE.read_text(encoding="utf-8")
    assert "Son los 14 indicadores del plan de calidad: 8 del código y 6 de los datos." in sqap and "97 %" in sqap
    adr = i18n.document_path("ADR.md", "es").read_text(encoding="utf-8")
    assert "**Revisión (D-475, 03-11-2026):**" in adr and "| 5 | 97,1 % |" in adr


# endregion
