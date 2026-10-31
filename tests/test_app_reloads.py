"""D-357: a reload the app makes by itself (opening or printing a document from the folder, the theme's base) keeps the
visit's view once; a reload the reader makes still asks for it (D-340), and the author's view is never kept."""

import json
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

from bi import dashboard

ROOT = Path(__file__).resolve().parent.parent


def reload_page(kept, view="SQAP · Plan de calidad del software"):
    """A fresh session on a document's address, whose browser tab kept «kept» (or nothing) before the reload."""
    script = (
        f"import sys\nsys.path.insert(0, {str(ROOT)!r})\nimport streamlit as st\nfrom bi import dashboard\n"
        "ORIGINAL = st.components.v2.component\n"
        "def fake(name, js=None):\n"
        "    if name != 'profile_keeper':\n        return ORIGINAL(name, js=js)\n"
        f"    return lambda **kwargs: __import__('types').SimpleNamespace(keep={kept!r}, reopen=None)\n"
        "st.components.v2.component = fake\n"
        f"st.query_params['vista'] = {view!r}\n"
        "try:\n    dashboard.main()\nfinally:\n    st.components.v2.component = ORIGINAL\n"
    )
    return AppTest.from_string(script, default_timeout=90).run()


def test_d357_opening_or_printing_a_document_from_the_folder_does_not_ask_for_the_view_again():
    kept = json.dumps({"p": "profesional", "r": "bi", "t": 0})
    app = reload_page(kept)
    assert not app.exception
    assert not [box for box in app.text_input if box.key == "profile_author_code"]  # no «Elige tu vista»
    assert app.session_state["visitor_profile"] == "profesional"
    assert not app.session_state.get("admin_unlocked")  # the author's view is never kept
    assert any("Plan de calidad del software" in block.value for block in app.markdown)  # still on the document


def test_d357_a_reload_the_reader_makes_still_asks_for_the_view():
    app = reload_page(None)
    assert [box for box in app.text_input if box.key == "profile_author_code"]  # «Elige tu vista» is back
    assert "visitor_profile" not in app.session_state or not app.session_state["visitor_profile"]
    forged = reload_page(json.dumps({"p": "autor", "r": "", "t": 0}))  # anything but a public view is ignored
    assert [box for box in forged.text_input if box.key == "profile_author_code"]


def test_d357_every_reload_the_app_makes_remembers_the_view_first():
    source = (ROOT / "bi" / "dashboard.py").read_text(encoding="utf-8")
    assert ".df-actions a, .doc-path a, .doc-print" in dashboard.PROFILE_KEEPER_JS  # «Abrir», «PDF», the path, print
    for reload in (
        "page.location.reload();",
        "window.location.assign(url.toString());",
        "window.location.replace(url.toString());",
    ):
        before = source[: source.index(reload)].rsplit("\n", 2)[-2:]
        assert any("__goRemember" in line for line in before), reload
    assert re.search(r"Date\.now\(\) - kept\.t < \d+", dashboard.PROFILE_KEEPER_JS)  # used once and only fresh
