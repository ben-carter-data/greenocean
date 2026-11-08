"""The «Controles de datos» overview draws the evidence it is given, nothing more."""

from datetime import datetime

from bi import quality_view

# region Constants
# endregion


# region The «Controles de datos» overview draws the evidence it is given, nothing more
def test_build_evidence_from_the_page_objects():
    checks = dict(
        integrity_ok=True, foreign_keys=0, duplicates=0, invalid=0, weeks=249, first="2022-01-03", last="2026-10-05"
    )
    files = [dict(status="Verificado · SHA-256 coincide")] * 9 + [dict(status="Falla · SHA-256 distinto")]
    run = dict(run_id=4, started_at="2026-10-13T18:35:06", status="LOADED")
    build = dict(models=16, tests=31, passing=31, ok=True, built_at=datetime(2026, 10, 19))
    parity = dict(rows=(811578, 811578), rejections=(201, 201), ok=True)
    evidence = quality_view.build_evidence(
        checks, files, {"a": {}}, run, build, parity, lambda value: "13-10-2026 15:35"
    )
    assert evidence["files_matching"] == 9 and evidence["files_failed"] == 1 and evidence["manifest_files"] == 10
    assert evidence["first_week"] == "3–9 ene 2022" and evidence["last_week"] == "5–11 oct 2026"  # D-374
    assert evidence["run_ok"] and evidence["run_started"] == "13-10-2026 15:35"
    assert evidence["build"]["built_at"] == "19-10-2026" and evidence["parity"]["rows"] == 811578
    assert set(evidence) >= {"run_id", "run_status", "weeks", "checks"}


# endregion
