"""«Flujo del sistema en vivo» (D-412): every arrow says who asks, what, what comes back and when; every piece is real in
the repository; every step of the weekly workflow moves something; the live state follows GitHub's answer; the logs are
the author's only; and it reads whole in English."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from bi import charts, control, github_actions, i18n, live_flow

# region Constants
FACTS = {"odepa": "2 archivos · 63,1 MB · 2026-10-31 04:40"}
# endregion


# region Variables
ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = str(ROOT / "bi" / "dashboard.py")
PALETTE = charts.get_palette(charts.MODE_DARK)
STARTED = datetime(2026, 10, 31, 4, 38, tzinfo=timezone.utc)
# endregion


# region «Flujo del sistema en vivo»
def run(state):
    return {"id": 9, "state": state, "started_at": STARTED, "url": "https://github.com/x/y/actions/runs/9"}


def step(name, state):
    return {"job": "weekly-load", "name": name, "state": state, "started": STARTED, "seconds": 3}


def test_d412_every_arrow_says_who_asks_what_what_comes_back_and_when_in_both_languages():
    pieces = set(live_flow.PIECES) | {live_flow.RUNNER}
    for arrow_id, arrow in live_flow.ARROWS.items():
        assert arrow["ask_by"] in pieces and arrow["answer_by"] in pieces, arrow_id
        for key in ("label", "ask", "answer", "when", "why"):
            spanish, english = arrow[key]
            assert spanish.strip() and english.strip() and spanish != "", (arrow_id, key)
        assert re.fullmatch(r"M[\d ]+( [HV]\d+)+", arrow["d"]), arrow_id  # straight lines and right angles only
    assert [arrow_id for arrow_id, arrow in live_flow.ARROWS.items() if arrow.get("deduced")] == ["deploy"]


@pytest.mark.parametrize("piece_id", list(live_flow.PIECES))
def test_d412_every_piece_is_real_in_the_repository(piece_id):
    *_, evidence, needle = live_flow.PIECES[piece_id]
    assert needle in (ROOT / evidence).read_text(encoding="utf-8"), (piece_id, evidence)


def workflow_steps():
    """The names GitHub gives the steps of semanal.yml: its own name, or «Run» and what it uses or runs."""
    names = []
    for block in re.split(r"\n      - ", (ROOT / ".github/workflows/semanal.yml").read_text(encoding="utf-8"))[1:]:
        named = re.match(r"name: (.+)", block)
        uses = re.match(r"uses: (\S+)", block)
        command = re.match(r"run: (.+)", block)
        names.append(named.group(1) if named else f"Run {uses.group(1)}" if uses else f"Run {command.group(1)}")
    return names


def test_d412_every_step_of_the_weekly_load_moves_a_piece_or_an_arrow():
    names = workflow_steps()
    assert "Download the ODEPA files" in names and "Run actions/checkout@v4" in names and len(names) >= 13
    for name in names:
        assert name in live_flow.STEP_ELEMENTS, name
    known = set(live_flow.ARROWS) | set(live_flow.PIECES) | {live_flow.RUNNER}
    assert all(element in known for elements in live_flow.STEP_ELEMENTS.values() for element in elements)
    assert live_flow.step_elements("Something GitHub adds") == [live_flow.RUNNER]  # it works inside the runner


def test_d412_a_run_in_progress_is_followed_live_and_an_ended_one_waits_still_with_its_replay():
    steps = [
        step("Set up job", "ok"),
        step("Download the ODEPA files", "ok"),
        step("Build the data warehouse with dbt", "in_progress"),
    ]
    live = live_flow.build_model([run(control.RUN_IN_PROGRESS)], steps, FACTS)
    assert live["mode"] == "live" and live["status"] == "En curso · Build the data warehouse with dbt"
    assert live["timeline"][2]["elements"] == ["ine", "parquet", "dbt", "duckdb"]  # a message to INE, three pieces work
    page = live_flow.build_html(PALETTE, live)
    assert 'class="lf lf-live"' in page and 'id="lf-replay"' not in page and 'id="lf-pause"' in page
    ended = live_flow.build_model(
        [run(control.RUN_OK)], [step("Set up job", "ok"), step("Publish the database", "ok")], FACTS
    )
    assert ended["mode"] == "still" and ended["status"].startswith("Sin ejecución en curso · última ejecución real:")
    assert "(correcta)" in ended["status"] and 'id="lf-replay"' in live_flow.build_html(PALETTE, ended)
    nothing = live_flow.build_model([], [], FACTS)
    assert nothing["timeline"] == [] and nothing["status"].startswith("Sin datos de GitHub")


def test_d412_the_page_carries_only_states_texts_and_facts_never_a_log_or_a_token():
    steps = [step("Set up job", "ok"), step("Run the tests against the new database", "failed")]
    page = live_flow.build_html(PALETTE, live_flow.build_model([run(control.RUN_FAILED)], steps, FACTS))
    data = json.loads(re.search(r'<script type="application/json" id="lf-data">(.*?)</script>', page, re.S).group(1))
    assert set(data) == {"mode", "timeline", "facts", "arrows", "labels", "request", "answer"}
    assert data["facts"] == FACTS and all(set(item) == {"name", "elements", "state"} for item in data["timeline"])
    assert "Authorization" not in page and "github_pat_" not in page and "log" not in json.dumps(data["timeline"])
    assert "textContent" in live_flow.SCRIPT and "innerHTML" not in live_flow.SCRIPT  # the script never writes markup


def test_d412_the_animation_follows_the_authors_rule():
    script = live_flow.SCRIPT
    # a communication: a message from whoever asks to whoever answers, and the answer back along the same path
    assert "travel(path, data.request, false, () => travel(path, data.answer, true" in script
    css = live_flow.build_css(PALETTE)
    assert (
        ".lf-piece.lf-working .lf-tile" in css and "lf-pulse" in css and "drop-shadow" in css
    )  # a piece glows and pulses
    assert "prefers-reduced-motion" in css and "reduced" in script


def test_d412_facts_are_read_from_what_the_load_leaves():
    manifest = {
        "wholesale_2026.csv": {"bytes": 34_000_000, "downloaded_at": "2026-10-31T04:40:48"},
        "consumer_2026.csv": {"bytes": 29_000_000, "downloaded_at": "2026-10-31T04:41:02"},
        "wholesale_2022.csv": {"bytes": 30_000_000, "downloaded_at": "2026-01-02T12:00:00"},
    }
    pointer = {"sha256": "ab" * 32, "bytes": 14_692_352, "published_at": "2026-10-31T04:43:31+00:00"}
    facts = live_flow.read_facts(manifest, pointer, 202, 9)
    assert (
        facts["odepa"] == "2 archivos · 63,0 MB · 31-10-2026 01:41"
    )  # the agent writes UTC; the panel says Chile time
    assert facts["cache"] == "1 archivos de años cerrados" and facts["ine"] == "202 meses del IPC"
    assert facts["release"].startswith("datos.duckdb · 14,7 MB · huella abababababab…")
    assert facts["issues"] == "«Informe semanal 2026-10-31»"


def test_d412_the_fixed_picture_has_no_script_and_the_focus_keeps_the_run():
    picture = live_flow.build_static_html(PALETTE, "Última carga real: 31-10-2026")
    assert "<script" not in picture and "Última carga real" in picture and 'id="arrow-odepa"' in picture
    assert 'viewBox="-10 -8 1190 525"' in live_flow.build_svg(PALETTE, focus=True)


def test_d412_every_text_has_its_english(monkeypatch):
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    texts = live_flow.arrow_texts()
    assert texts["odepa"]["title"] == "Load runner → ODEPA" and texts["deploy"]["deduced"]
    page = live_flow.build_html(PALETTE, live_flow.build_model([], [], {}))
    assert 'id="lf-replay"' not in page and "Pause" in page and "No data from GitHub" in page
    for pair in [piece[4] for piece in live_flow.PIECES.values()] + [piece[5] for piece in live_flow.PIECES.values()]:
        assert not re.search(r"[áéíóúñ¿]", pair[1]), pair


class Answer:
    def __init__(self, payload):
        self.payload, self.status_code, self.headers = payload, 200, {}

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


def fake_github(url, headers=None, params=None, timeout=None):
    """GitHub answering that the weekly load is running its dbt step. The flow reads with no token here."""
    assert "Authorization" not in (headers or {})
    path = url.removeprefix(control.API_URL)
    if path.endswith("/workflows/semanal.yml/runs"):
        return Answer(
            {
                "workflow_runs": [
                    {
                        "id": 5,
                        "status": "in_progress",
                        "conclusion": None,
                        "run_started_at": "2026-11-03T12:00:05Z",
                        "updated_at": "2026-11-03T12:03:00Z",
                        "head_sha": "abc",
                        "head_branch": "main",
                        "event": "schedule",
                        "html_url": "https://github.com/x/y/actions/runs/5",
                    }
                ]
            }
        )
    if path.endswith("/actions/runs/5"):
        return Answer(
            {"status": "in_progress", "conclusion": None, "html_url": "https://github.com/x/y/actions/runs/5"}
        )
    if path.endswith("/actions/runs/5/jobs"):
        steps = [
            {
                "name": "Set up job",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-11-03T12:00:05Z",
                "completed_at": "2026-11-03T12:00:09Z",
            },
            {
                "name": "Build the data warehouse with dbt",
                "status": "in_progress",
                "conclusion": None,
                "started_at": "2026-11-03T12:02:00Z",
                "completed_at": None,
            },
        ]
        return Answer(
            {"jobs": [{"id": 50, "name": "weekly-load", "status": "in_progress", "conclusion": None, "steps": steps}]}
        )
    raise AssertionError(f"unexpected request: {path}")


@pytest.mark.parametrize("unlocked", [False, True])
def test_d412_the_stack_page_follows_a_run_and_only_the_author_gets_the_way_to_the_logs(monkeypatch, unlocked):
    monkeypatch.setattr(github_actions.requests, "get", fake_github)
    st.cache_data.clear()
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.session_state["stack_view"] = "Flujo del sistema en vivo"
    if unlocked:
        app.session_state["admin_unlocked"] = True
        app.session_state["quality_alert_seen"] = True
    app.query_params.update({"vista": "Stack y evidencia"})
    app.run()
    st.cache_data.clear()
    assert not app.exception
    frames = [element.proto.srcdoc for element in app.get("iframe") if "lf-data" in element.proto.srcdoc]
    assert len(frames) == 1 and 'class="lf lf-live"' in frames[0]
    assert "En curso · Build the data warehouse with dbt" in frames[0]
    captions = " ".join(caption.value for caption in app.caption)
    assert ("«GitHub Actions», solo para el autor" in captions) is unlocked


def test_d412_in_english_the_view_leaves_nothing_in_spanish(monkeypatch):
    from tests import i18n_audit

    monkeypatch.setattr(github_actions.requests, "get", fake_github)
    st.cache_data.clear()
    state = {"stack_view": "Flujo del sistema en vivo"}
    assert i18n_audit.spanish_left("Stack y evidencia", i18n_audit.read_data_values(), state=state) == []
    st.cache_data.clear()


def test_d413_the_run_window_shows_the_flow_focused_on_the_run_above_its_steps():
    from tests.test_dashboard import FAKE_TOKEN, draw_control_page, open_run_dialog

    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="in_progress", dialog=True)
    open_run_dialog(app, "clave")
    app.run()
    assert not app.exception
    frames = [element.proto.srcdoc for element in app.get("iframe") if "lf-data" in element.proto.srcdoc]
    assert len(frames) == 2 and frames[0] == frames[1]  # the wide place and the narrow one: the same frame
    assert 'class="lf lf-live"' in frames[0] and 'viewBox="-10 -8 1190 525"' in frames[0]
    assert "En curso · Run the ETL" in frames[0] and FAKE_TOKEN not in frames[0]
    assert "run_minimize" in [button.key for button in app.button]  # the steps and their buttons, as before
    css = " ".join(block.value for block in app.markdown)
    assert "@media (max-width:900px) {.st-key-rw_flow {display:none;}" in css
    focus = live_flow.build_svg(PALETTE, focus=True)  # what the run touches: no browser and no DevSecOps band
    assert 'id="piece-browser"' not in focus and 'id="arrow-browser"' not in focus and 'id="piece-gate"' not in focus
    assert all(f'id="arrow-{arrow}"' in focus for arrow in ("odepa", "ine", "release", "repo", "start"))


def test_d414_the_sad_carries_the_fixed_picture_in_both_languages():
    from bi import doc_diagrams

    for language in ("es", "en"):
        text = i18n.document_path("SAD.md", language).read_text(encoding="utf-8")
        assert "\n[[diagrama:flujo]]\n" in text
    page = doc_diagrams.DOC_DIAGRAMS["flujo"](charts.MODE_CORPORATE)
    assert "<script" not in page and doc_diagrams.PRINT_STYLE in page and 'id="arrow-deploy"' in page
    published = json.loads(live_flow.POINTER.read_text(encoding="utf-8"))["published_at"]
    assert "Última carga real publicada:" in page and published[:4] in page


# endregion
