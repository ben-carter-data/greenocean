"""«Git workflow» (D-344, D-345): the map of 15 stations, the incident log and who reads what."""

import json
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

from bi import git_workflow

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = str(ROOT / "bi" / "dashboard.py")
REFERENCE = ROOT / "docs" / "referencia" / "ciclo_git.html"


def draw(profile="profesional", unlocked=False, language="es", view="Git workflow"):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.query_params.update({"lang": language, "vista": view})
    app.session_state["visitor_profile"] = profile
    if unlocked:
        app.session_state["admin_unlocked"] = True
        app.session_state["quality_alert_seen"] = True
    app.run()
    return app


def test_d344_the_map_follows_its_reference_station_by_station():
    reference = REFERENCE.read_text(encoding="utf-8")
    titles = re.findall(r'\{n:(\d+),l:"([abc])",i:"\w+",t:"([^"]+)"', reference)
    assert [int(n) for n, *_ in titles] == list(range(1, 16))
    stations = git_workflow.STATIONS
    assert [(str(item["n"]), item["lane"], item["title"][1]) for item in stations] == titles
    assert {item["n"] for item in stations if item.get("optional")} == {4, 7, 10}  # dashed border
    assert {item["n"] for item in stations if item.get("gate")} == {8, 12, 14}  # yellow diamonds
    assert [item["n"] for item in stations if item.get("end")] == [15]  # «Deployed», green
    assert all(
        item["commands"] and all(pair and all(pair) for pair in (item["title"], item["what"], item["example"]))
        for item in stations
    )
    assert all("fail" in item for item in stations if item.get("gate") and item["n"] != 14 or item["n"] == 14)
    assert all(not re.search(r"(?i)github logo|octocat", json.dumps(item)) for item in stations)  # generic icons only


def test_d344_the_page_behaves_like_the_reference_panel_keys_copy_and_neighbours():
    html = git_workflow.build_map_html(
        {k: "#101820" for k in __import__("bi.charts", fromlist=["x"]).PALETTES["Corporativo"]}, "es", False
    )
    for needle in (
        "Escape",
        "ArrowRight",
        "ArrowLeft",
        "clipboard.writeText",
        "L.previous",
        "L.next",
        'aria-modal="true"',
    ):
        assert needle in html, needle
    assert "innerHTML = " not in git_workflow.SCRIPT.replace("t.innerHTML = paths", "")  # the DOM is built with its API


def test_d345_the_register_reaches_each_station_and_only_the_author_gets_the_diagnosis():
    failures = git_workflow.read_failures()
    assert failures and [row["fecha"] for row in failures] == sorted((row["fecha"] for row in failures), reverse=True)
    for language in ("es", "en"):
        public = git_workflow.build_data(language, failures, author=False)["stations"]
        private = git_workflow.build_data(language, failures, author=True)["stations"]
        counts = [len(station["register"]) for station in public]
        assert counts == [len(station["register"]) for station in private] and sum(counts) == len(failures)
        assert not any("diagnostico" in item for station in public for item in station["register"])
        assert all("diagnostico" in item for station in private for item in station["register"])
    diagnoses = [row["diagnostico"][0] for row in failures]
    palette = {key: "#102030" for key in __import__("bi.charts", fromlist=["x"]).PALETTES["Corporativo"]}
    page_public = git_workflow.build_map_html(palette, "es", False)
    page_author = git_workflow.build_map_html(palette, "es", True)
    assert not any(json.dumps(text, ensure_ascii=False)[1:-1] in page_public for text in diagnoses)
    assert all(json.dumps(text, ensure_ascii=False)[1:-1] in page_author for text in diagnoses)


def test_d345_the_incident_log_hides_the_diagnosis_from_the_professional():
    failures = git_workflow.read_failures()
    for language in ("es", "en"):
        public = git_workflow.build_log_table(language, False)
        private = git_workflow.build_log_table(language, True)
        head = "Diagnosis" if language == "en" else "Diagnóstico"
        assert head not in public and head in private
        assert public.count("<tr>") == len(failures) + 1 == private.count("<tr>")
        first = failures[0]
        assert first["fecha"] in public and first["fecha"] in private
        assert git_workflow.pick(tuple(first["diagnostico"]), language) not in public
        assert git_workflow.pick(tuple(first["diagnostico"]), language).replace("&", "&amp;") in private.replace(
            "&#x27;", "'"
        )


def test_d344_the_page_is_in_the_quality_section_for_the_professional_and_the_author_not_for_the_user():
    for profile, unlocked in (("profesional", False), ("profesional", True)):
        app = draw(profile, unlocked)
        assert not app.exception and len(app.tabs) == 2
        labels = [link.proto.label for link in app.sidebar.get("page_link")]
        assert labels.index("Git workflow") == labels.index("Método y calidad") + 1
    user = draw("consulta")
    assert "Git workflow" not in [link.proto.label for link in user.sidebar.get("page_link")]


def test_d344_the_page_has_the_same_name_in_both_languages_and_its_tabs_in_each():
    es, en = draw(language="es"), draw(language="en")
    assert [tab.label for tab in es.tabs] == ["Mapa", "Registro de incidentes"]
    assert [tab.label for tab in en.tabs] == ["Map", "Incident log"]
    assert "Git workflow" in [link.proto.label for link in en.sidebar.get("page_link")]
