"""The page «GitHub Actions» (D-339): only the author sees it, the token is never drawn, read only, cached two minutes."""

import re
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from bi import control, github_actions
from tests.test_github_actions import LOG, READ_TOKEN, SHAPED, TOKEN, Answer, Network

DASHBOARD_FILE = str(Path(__file__).resolve().parent.parent / "bi" / "dashboard.py")


@pytest.fixture
def network(monkeypatch):
    fake = Network()
    monkeypatch.setattr(github_actions.requests, "get", fake)
    st.cache_data.clear()  # the page keeps its answers two minutes: every test starts without them
    yield fake
    st.cache_data.clear()


def draw(unlocked=True, language="es", secrets=("read", "usual"), view="GitHub Actions"):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.query_params.update({"perfil": "profesional", "lang": language, "vista": view})
    if unlocked:
        app.session_state["admin_unlocked"] = True
        app.session_state["quality_alert_seen"] = True  # the quality alert (D-335) is another window, not this test's
    if "read" in secrets:
        app.secrets["GITHUB_READ_TOKEN"] = READ_TOKEN
    if "usual" in secrets:
        app.secrets["GITHUB_TOKEN"] = TOKEN
    app.run()
    return app


def tokens_sent(network):
    """The credentials of the requests only this page makes (logs, annotations, token date and the other two workflows);
    the Operations center's own reading of the weekly workflow is another feature and keeps its own token."""
    own = ("/logs", "/annotations", "/rate_limit", "pruebas.yml/runs", "calidad.yml/runs")
    return {headers.get("Authorization") for url, headers in network.calls if url.endswith(own)}


def everything_drawn(app):
    """Every text the page put on the screen, whatever the element."""
    parts = []
    for kind in ("markdown", "code", "caption", "info", "warning", "error", "success", "text", "exception", "title"):
        parts += [str(getattr(element, "value", "")) for element in app.get(kind)]
    return "\n".join(parts)


def menu_labels(app):
    return [link.proto.label for link in app.sidebar.get("page_link")]


def test_d339_only_the_author_has_the_page_in_the_menu_and_it_sits_in_devops_and_security(network):
    visitor = draw(unlocked=False, view="Dashboard")
    assert not visitor.exception and "GitHub Actions" not in menu_labels(visitor)
    author = draw(unlocked=True, view="Dashboard")
    assert not author.exception
    labels = menu_labels(author)
    assert "GitHub Actions" in labels
    assert labels.index("GitHub Actions") == labels.index("Centro de operación") + 1  # right under it, in its section
    assert labels.index("GitHub Actions") < labels.index("Arquitectura de seguridad")


def test_d339_without_the_author_key_the_address_shows_one_line_and_nothing_is_asked_of_github(network):
    app = draw(unlocked=False)
    assert not app.exception
    assert [item.value for item in app.info] == ["Esta página es solo para el autor."]
    page = everything_drawn(app)
    assert "ga-table" not in page and "Abrir en GitHub" not in page and "pytest" not in page
    assert network.calls == []  # no request at all


def test_d339_the_author_sees_the_runs_the_failure_its_tests_and_the_last_sixty_lines(network):
    app = draw()
    assert not app.exception
    page = everything_drawn(app)
    assert page.count('class="ga-table"') == 3 and page.count("Abrir en GitHub") == 9  # 3 workflows x 3 runs
    for name in ("Pruebas", "Carga semanal", "Calidad"):
        assert name in page
    assert "pytest (3.12)" in page and "Run pytest" in page and "Process completed with exit code 1." in page
    assert "tests/test_a.py::test_one" in page and "tests/test_b.py::test_two[es]" in page
    assert page.count("tests/test_a.py::test_one") >= 1 and "Pruebas que fallan (2)" in page
    tail = [item.value for item in app.code][0].splitlines()
    assert len(tail) == github_actions.LOG_LINES and tail[-1] == "line 69"
    assert "Últimas 60 líneas del log" in page and "843decd" in page


def test_d339_the_page_only_reads_it_has_no_button_to_start_cancel_or_re_run(network):
    app = draw()
    # The only button of the frame is «Volver» (back to the previous page of the visit): nothing acts on GitHub.
    assert {button.label for button in app.main.button} <= {"Volver"}
    drawn = " ".join(item.value for item in app.markdown if "ga-" in item.value)
    assert not re.search(r"(?i)re-?run|cancelar|relanzar|ejecutar", drawn)


def test_d339_the_token_is_never_drawn_not_even_when_the_log_prints_it(monkeypatch):
    # A log whose LAST lines print both tokens and something shaped like one: on the screen if they were not covered.
    log = LOG + f"2026-10-29T13:15:00.0000000Z Authorization: Bearer {TOKEN}\n"
    log += f"2026-10-29T13:15:01.0000000Z key={READ_TOKEN} {SHAPED}\n"
    network = Network(log=log)
    monkeypatch.setattr(github_actions.requests, "get", network)
    st.cache_data.clear()
    app = draw()
    page = everything_drawn(app) + " ".join(f"{key}={app.session_state[key]!r}" for key in list(app.session_state))
    for secret in (TOKEN, READ_TOKEN, "FAKE0123456789", "READ0123456789"):
        assert secret not in page, secret
    assert "Bearer ***" in page and SHAPED not in page  # the log's line is there, with the token covered
    assert tokens_sent(network) == {f"Bearer {READ_TOKEN}"}
    # The usual token is the fallback when the read-only one is missing; the same rule applies to it.
    st.cache_data.clear()
    network.calls.clear()
    fallback = draw(secrets=("usual",))
    assert tokens_sent(network) == {f"Bearer {TOKEN}"}
    assert TOKEN not in everything_drawn(fallback)


def test_d339_without_any_token_only_the_states_show_with_a_notice(network):
    app = draw(secrets=())
    assert not app.exception
    notice = [item.value for item in app.warning]
    assert len(notice) == 1 and "GITHUB_READ_TOKEN" in notice[0] and "Sin token solo se ven los estados" in notice[0]
    page = everything_drawn(app)
    assert (
        page.count('class="ga-table"') == 3
        and "Pruebas que fallan" not in page
        and not [block for block in app.code if "line 69" in block.value]
    )
    paths = [url.removeprefix(control.API_URL) for url, _ in network.calls]
    assert not any(path.endswith(("/logs", "/annotations", "/rate_limit")) for path in paths)


def test_d339_an_expired_or_unpermitted_token_says_what_to_do_and_the_states_still_show(monkeypatch):
    failing = Network(fail={"/rate_limit": Answer(status=401)})
    monkeypatch.setattr(github_actions.requests, "get", failing)
    st.cache_data.clear()
    expired = draw()
    assert "venció o no es válido" in " ".join(item.value for item in expired.error)
    assert everything_drawn(expired).count('class="ga-table"') == 3 and not list(expired.code)
    st.cache_data.clear()
    denied = Network(fail={"/logs": Answer(status=403)})
    monkeypatch.setattr(github_actions.requests, "get", denied)
    forbidden = draw()
    assert "no tiene permiso para leer los logs" in " ".join(item.value for item in forbidden.warning)
    assert "pytest (3.12)" in everything_drawn(forbidden)  # the job and the step still show
    st.cache_data.clear()


def test_d339_the_answers_are_kept_two_minutes_so_a_second_visit_asks_nothing(network):
    source = Path(DASHBOARD_FILE).read_text(encoding="utf-8")
    assert "@st.cache_data(ttl=github_actions.CACHE_SECONDS" in source and github_actions.CACHE_SECONDS == 120
    app = draw()
    asked = len(network.calls)
    assert asked > 0
    app.run()
    assert len(network.calls) == asked  # the cache answered


def test_d339_the_page_reads_in_english_too(network):
    app = draw(language="en")
    assert not app.exception
    page = everything_drawn(app)
    for text in ("Open in GitHub", "Failing tests (2)", "Latest failure", "Weekly load", "Last 60 lines of the log"):
        assert text in page, text
    for spanish in ("Abrir en GitHub", "Pruebas que fallan", "Último fallo", "Carga semanal"):
        assert spanish not in page, spanish
    closed = draw(unlocked=False, language="en")
    assert [item.value for item in closed.info] == ["This page is for the author only."]


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"perfil": "consulta"},
        {"perfil": "profesional", "rol": "devops"},
        {"perfil": "autor"},
        {"perfil": "profesional", "admin_unlocked": "true", "autor": "1", "clave": "x"},
        {"perfil": "consulta", "vista": "GitHub Actions"},
        {"perfil": "profesional", "vista": "GitHub Actions", "admin_unlocked": "True"},
        {"perfil": "profesional", "vista": "GitHub Actions", "lang": "en"},
    ],
)
def test_d339_a_fresh_visit_or_a_reload_never_reaches_the_author_part_whatever_the_address_says(network, params):
    """Every reload is a new session: the author key is never in the address, so no address opens the author's part."""
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.query_params.update(params)
    app.run()
    assert not app.exception
    assert app.get("dialog")  # D-340: the entry window opens whatever the address says, on every visit and reload
    assert not app.session_state["admin_unlocked"] if "admin_unlocked" in app.session_state else True
    assert "perfil" not in app.query_params and "rol" not in app.query_params  # nothing of it is kept
    assert "GitHub Actions" not in menu_labels(app)
    page = everything_drawn(app)
    assert "Abrir en GitHub" not in page and 'class="ga-table"' not in page
    assert not [url for url, _ in network.calls if url.endswith(("/logs", "/annotations", "/rate_limit"))]
