"""The «Calidad y auditoría» overview draws the evidence it is given, nothing more."""
import copy
import re
from datetime import datetime

from bi import charts, quality_view

EVIDENCE = dict(
    run_id=4, run_started="13-10-2026 15:35", run_status="LOADED", run_ok=True,
    manifest_present=True, manifest_files=10, files_matching=10, files_total=10, files_failed=0,
    weeks=249, first_week="03-01-2022", last_week="05-10-2026",
    build=dict(models=16, tests=31, passing=31, ok=True, built_at="19-10-2026"),
    checks=dict(integrity_ok=True, foreign_keys=0, duplicates=0, invalid=0),
    parity=dict(rows=811578, rejections=201, backup_rows=811578, backup_rejections=201, ok=True),
)


def step_marks(markup):
    return re.findall(r'class="qa-mark qa-(\w+)"', markup)


def test_all_passing_page_matches_the_mockup():
    markup = quality_view.build_overview_html(EVIDENCE, charts.MODE_LIGHT)
    for title in ("Reconciliación fuente → base", "Recálculo independiente de indicadores",
                  "Concordancia cálculo → pantalla", "Contraste con otra fuente",
                  "Pruebas dbt de la última construcción", "Paridad SQLite ↔ DuckDB",
                  "Origen y archivos", "Integridad de archivos originales", "Cobertura temporal",
                  "Última carga registrada", "Comprobación de la base actual"):
        assert html_text(title) in markup
    assert markup.count("Verificado · pruebas automáticas") == 2
    assert "Verificado · alcance limitado" in markup
    assert markup.count(">Pendiente<") == 1
    assert "Ejecución 4 · 13-10-2026 15:35 (Chile) · LOADED" in markup and "Carga correcta" in markup
    assert step_marks(markup) == ["ok", "ok", "ok"]
    assert "qa-pill qa-fail" not in markup and "qa-pill qa-ok" in markup
    for figure in ("10 archivos registrados en manifest.json", "10 de 10 huellas coinciden",
                   "249 semanas", "03-01-2022 → 05-10-2026", "31 de 31 pruebas", "16 modelos",
                   "811.578 precios", "201 rechazos", "misma suma", "0 duplicados"):
        assert figure in re.sub(r"<[^>]+>", "", markup)
    # One HTML block for st.markdown: no script, no blank line that would end it.
    assert "<script" not in markup and "\n\n" not in markup


def test_failures_turn_pills_red_and_their_step_not_green():
    evidence = copy.deepcopy(EVIDENCE)
    evidence["checks"]["duplicates"] = 3
    evidence["files_matching"], evidence["files_failed"] = 9, 1
    evidence["run_ok"], evidence["run_status"] = False, "FAILED"
    markup = quality_view.build_overview_html(evidence, charts.MODE_DARK)
    assert markup.count('qa-pill qa-fail">') == 3
    assert step_marks(markup) == ["fail", "fail", "fail"]
    assert "Carga con falla" in markup and "1 discrepancia" in markup and "3 duplicados" in markup
    assert markup.count(">Pendiente<") == 1


def test_missing_build_and_backup_stay_pending_without_a_second_bare_pendiente():
    evidence = dict(EVIDENCE, build=None, parity=None)
    markup = quality_view.build_overview_html(evidence, charts.MODE_LIGHT)
    assert step_marks(markup) == ["ok", "pending", "pending"]
    assert markup.count(">Pendiente<") == 1
    assert "Sin respaldo SQLite para comparar." in markup


def test_build_evidence_from_the_page_objects():
    checks = dict(integrity_ok=True, foreign_keys=0, duplicates=0, invalid=0, weeks=249,
                  first="2022-01-03", last="2026-10-05")
    files = [dict(status="Verificado · SHA-256 coincide")] * 9 + [dict(status="Falla · SHA-256 distinto")]
    run = dict(run_id=4, started_at="2026-10-13T18:35:06", status="LOADED")
    build = dict(models=16, tests=31, passing=31, ok=True, built_at=datetime(2026, 10, 19))
    parity = dict(rows=(811578, 811578), rejections=(201, 201), ok=True)
    evidence = quality_view.build_evidence(checks, files, {"a": {}}, run, build, parity, lambda value: "13-10-2026 15:35")
    assert evidence["files_matching"] == 9 and evidence["files_failed"] == 1 and evidence["manifest_files"] == 10
    assert evidence["first_week"] == "03-01-2022" and evidence["last_week"] == "05-10-2026"
    assert evidence["run_ok"] and evidence["run_started"] == "13-10-2026 15:35"
    assert evidence["build"]["built_at"] == "19-10-2026" and evidence["parity"]["rows"] == 811578
    assert set(evidence) >= {"run_id", "run_status", "weeks", "checks"}


def html_text(text):
    return quality_view.html.escape(text)
