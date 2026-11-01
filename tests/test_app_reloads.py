"""D-357, D-430: any reload of the tab keeps the visit's view (a document of the folder, printing, the theme's base, an
ordinary link, F5); a new tab asks for it. D-427: the author's view comes back only with a ticket the server issued."""

import json
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


def test_d357_a_tab_with_nothing_kept_asks_for_the_view():
    app = reload_page(None)  # D-430: a new tab or a new visit
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
    assert "Date.now() - kept.t" not in dashboard.PROFILE_KEEPER_JS  # D-430: kept for the life of the tab


def test_d427_the_author_comes_back_after_a_reload_the_app_makes_only_with_a_ticket_the_server_issued():
    """D-427, D-428."""
    tickets = dashboard.AUTHOR_TICKETS
    tickets["ticket-de-prueba"] = 4_000_000_000  # issued by the server, far from expiring
    app = reload_page(json.dumps({"p": "profesional", "r": "bi", "a": "ticket-de-prueba", "t": 0}))
    assert not app.exception and app.session_state["admin_unlocked"] is True
    assert not [box for box in app.text_input if box.key == "profile_author_code"]  # no «Elige tu vista», no key
    assert app.session_state["author_ticket"] == "ticket-de-prueba"  # D-428: the new session takes the ticket over
    # D-428: Streamlit Community Cloud loads the page twice; the second load comes back as the Autor too
    app = reload_page(json.dumps({"p": "profesional", "r": "bi", "a": "ticket-de-prueba", "t": 0}))
    assert not app.exception and app.session_state["admin_unlocked"] is True
    # a revoked ticket, a ticket the server never issued, or an expired one: the view comes back without the Autor
    tickets.pop("ticket-de-prueba")
    tickets["ticket-vencido"] = 1
    for ticket in ("ticket-de-prueba", "inventado", "ticket-vencido"):
        app = reload_page(json.dumps({"p": "profesional", "r": "bi", "a": ticket, "t": 0}))
        assert not app.exception and app.session_state["visitor_profile"] == "profesional", ticket
        assert not app.session_state.get("admin_unlocked"), ticket


def test_d427_only_an_author_session_holds_a_ticket_and_leaving_it_revokes_it(monkeypatch):
    state = {}
    monkeypatch.setattr(dashboard.st, "session_state", state)
    assert dashboard.issue_author_ticket(now=100) == ""  # not the Autor: no ticket
    state[dashboard.ADMIN_UNLOCKED] = True
    ticket = dashboard.issue_author_ticket(now=100)
    assert len(ticket) >= 40 and dashboard.AUTHOR_TICKETS[ticket] == 100 + dashboard.AUTHOR_IDLE_SECONDS
    assert dashboard.issue_author_ticket(now=200) == ticket  # the same session keeps its ticket, renewed
    dashboard.leave_author()
    assert ticket not in dashboard.AUTHOR_TICKETS and not dashboard.redeem_author_ticket(ticket, now=200)


def test_d427_the_document_is_printed_only_when_choose_your_view_is_gone():
    script = dashboard.AUTO_PRINT_SCRIPT
    assert 'document.querySelector(".profile-ask")' in script
    assert script.count("window.print()") == 1 and "if (!document.querySelector" in script
    assert "a: data.autor" in dashboard.PROFILE_KEEPER_JS


def test_d428_each_page_reads_the_kept_view_once_and_leaves_it_for_the_second_load_of_the_cloud():
    script = dashboard.PROFILE_KEEPER_JS
    assert "window.__goKeptRead ? null : store.getItem(KEY)" in script and "window.__goKeptRead = true" in script
    assert "removeItem" not in script  # D-430: the view stays for every later reload of the tab


def test_d430_every_run_keeps_the_view_so_no_reload_of_the_tab_asks_for_it_again():
    script = dashboard.PROFILE_KEEPER_JS
    body = script.split("window.__goRemember = remember;")[1]
    assert body.lstrip().startswith("remember();")  # each run, before any reload: links, the alert, F5
    assert "if (!data || !data.perfil) return;" in script  # a session that has not chosen keeps nothing
