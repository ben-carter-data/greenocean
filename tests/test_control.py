"""Tests for the pipeline control: schedule, run states and GitHub answers (faked)."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import control  # noqa: E402

GITHUB_RUN = {
    "id": 38226180308,
    "status": "completed",
    "conclusion": "success",
    "event": "workflow_dispatch",
    "run_started_at": "2026-10-12T08:51:00Z",
    "updated_at": "2026-10-12T08:51:57Z",
    "html_url": "https://github.com/x/y/actions/runs/38226180308",
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_next_run_is_the_coming_tuesday_at_noon_utc():
    monday = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)
    assert control.calculate_next_scheduled_run(monday) == datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)


def test_next_run_after_tuesday_noon_is_the_following_week():
    tuesday_afternoon = datetime(2026, 10, 13, 12, 30, tzinfo=timezone.utc)
    assert control.calculate_next_scheduled_run(tuesday_afternoon) == datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


def test_run_states_are_ok_failed_or_in_progress():
    assert control.classify_run("completed", "success") == control.RUN_OK
    assert control.classify_run("completed", "failure") == control.RUN_FAILED
    assert control.classify_run("in_progress", None) == control.RUN_IN_PROGRESS


def test_a_github_run_is_simplified_for_the_dashboard():
    run = control.simplify_run(GITHUB_RUN)
    assert run["state"] == control.RUN_OK
    assert run["trigger"] == "Manual"
    assert run["duration"] == timedelta(seconds=57)


def test_runs_are_read_from_the_github_api(monkeypatch):
    def fake_get(url, **arguments):
        assert url.endswith("/actions/workflows/semanal.yml/runs")
        return FakeResponse({"workflow_runs": [GITHUB_RUN]})

    monkeypatch.setattr(control.requests, "get", fake_get)
    assert [run["id"] for run in control.list_workflow_runs()] == [38226180308]


def test_only_known_steps_are_shown_in_spanish():
    job = {
        "steps": [
            {"name": "Set up job", "status": "completed", "conclusion": "success"},
            {"name": "Download the ODEPA files", "status": "completed", "conclusion": "success"},
            {"name": "Run the ETL", "status": "in_progress", "conclusion": None},
            {"name": "Simulate a failure", "status": "completed", "conclusion": "skipped"},
            {"name": "Save the updated database", "status": "completed", "conclusion": "skipped"},
        ]
    }
    # Step names copied from a real run of semanal.yml (12-10-2026).
    assert control.simplify_steps(job) == [
        ("Descarga de ODEPA", control.RUN_OK),
        ("Limpieza y reglas de negocio", control.RUN_IN_PROGRESS),
        ("Guardar la base actualizada", "skipped"),
    ]


def test_the_manual_run_started_after_the_click_is_found():
    clicked_at = datetime(2026, 10, 12, 8, 50, 50, tzinfo=timezone.utc)
    older_run = control.simplify_run({**GITHUB_RUN, "id": 1, "run_started_at": "2026-10-11T08:00:00Z"})
    new_run = control.simplify_run(GITHUB_RUN)
    assert control.find_run_started_after([new_run, older_run], clicked_at) == new_run
    assert control.find_run_started_after([older_run], clicked_at) is None


def test_the_token_is_only_sent_when_there_is_one():
    assert "Authorization" not in control.build_headers()
    assert control.build_headers("abc")["Authorization"] == "Bearer abc"


def test_failure_asked_for_on_purpose_is_marked_as_simulated(monkeypatch):
    simulated_steps = [("Limpieza y reglas de negocio", control.RUN_OK), ("Falla simulada", control.RUN_FAILED)]
    real_failure_steps = [("Limpieza y reglas de negocio", control.RUN_FAILED)]
    assert control.is_simulated_failure(simulated_steps)
    assert not control.is_simulated_failure(real_failure_steps)
    steps_by_run = {1: simulated_steps, 2: real_failure_steps}
    monkeypatch.setattr(control, "list_run_steps", lambda run_id, token=None: steps_by_run[run_id])
    runs = [
        {"id": 1, "state": control.RUN_FAILED},
        {"id": 2, "state": control.RUN_FAILED},
        {"id": 3, "state": control.RUN_OK},
    ]
    states = [run["state"] for run in control.mark_simulated_failures(runs)]
    assert states == [control.RUN_SIMULATED_FAILURE, control.RUN_FAILED, control.RUN_OK]


def make_http_error(status_code, headers=None):
    """An error as requests raises it, with a fake response."""
    response = requests.Response()
    response.status_code = status_code
    response.reason = "Forbidden" if status_code == 403 else "Error"
    response.headers.update(headers or {})
    return requests.HTTPError(response=response)


def test_github_error_says_the_real_cause_with_its_code():
    now = datetime(2026, 10, 12, 22, 0, tzinfo=timezone.utc)
    reset = int(datetime(2026, 10, 12, 22, 23, tzinfo=timezone.utc).timestamp())
    rate_limit = make_http_error(
        403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Limit": "60", "X-RateLimit-Reset": str(reset)}
    )
    assert control.describe_github_error(rate_limit, now) == (
        "GitHub respondió 403: se agotó el límite de consultas sin clave (60 por hora); se renueva en 23 min"
    )
    assert control.describe_github_error(make_http_error(401)) == (
        "GitHub respondió 401: la clave no es válida o venció"
    )
    assert control.describe_github_error(requests.Timeout()) == "GitHub no respondió en 10 s"
    assert control.describe_github_error(requests.ConnectionError()) == ("no hubo conexión con GitHub")


def test_github_error_never_shows_the_token():
    error = make_http_error(401, {"Authorization": "Bearer secret-token-123"})
    assert "secret-token-123" not in control.describe_github_error(error)


def test_github_error_handles_invalid_reset_and_untrusted_reason():
    error = make_http_error(429, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "invalid"})
    assert control.describe_github_error(error) == ("GitHub respondió 429: se agotó el límite de consultas")
    error = make_http_error(418)
    error.response.reason = "secret-token-123"
    assert control.describe_github_error(error) == ("GitHub respondió 418: error al consultar GitHub")


# region Token expiration (T-54)
def test_t54_token_expiration_is_read_in_both_formats_github_uses():
    assert control.parse_token_expiration("2026-12-31 12:00:00 UTC") == datetime(2026, 12, 31, 12, tzinfo=timezone.utc)
    assert control.parse_token_expiration("2026-12-31 09:00:00 -0300") == datetime(
        2026, 12, 31, 12, tzinfo=timezone.utc
    )
    assert control.parse_token_expiration(None) is None
    assert control.parse_token_expiration("not a date") is None


def test_t54_token_warning_is_highlighted_under_14_days():
    now = datetime(2026, 10, 13, tzinfo=timezone.utc)
    sentence, is_urgent = control.describe_token_expiration(now + timedelta(days=40), now)
    assert sentence == "Tu token vence en 40 días (22-11-2026)." and not is_urgent
    assert control.describe_token_expiration(now + timedelta(days=13), now)[1]
    assert control.describe_token_expiration(now - timedelta(days=1), now)[1]
    assert control.describe_token_expiration(None, now) == ("Tu token no tiene fecha de vencimiento.", False)


def test_t54_only_the_expiration_date_leaves_the_github_answer(monkeypatch):
    secret = "github_pat_FAKE_SECRET_123"
    seen = {}

    class Answer:
        headers = {control.TOKEN_EXPIRATION_HEADER: "2026-12-31 12:00:00 UTC"}

        def raise_for_status(self):
            return None

    def fake_get(url, headers, timeout):
        seen["authorization"] = headers["Authorization"]
        return Answer()

    monkeypatch.setattr(control.requests, "get", fake_get)
    expiration = control.read_token_expiration(secret)
    assert seen["authorization"] == f"Bearer {secret}"
    assert expiration == datetime(2026, 12, 31, 12, tzinfo=timezone.utc)
    assert secret not in control.describe_token_expiration(expiration, expiration)[0]


# endregion


def test_d199_the_right_code_opens_and_any_character_is_safe():
    assert control.check_control_code("clave", "clave") == (True, "")
    ok, message = control.check_control_code("contraseña ñ ü 🔑", "clave")  # used to raise TypeError
    assert not ok and message == "Clave incorrecta."
    assert control.check_control_code("piña", "piña")[0]
    assert not control.check_control_code("", "clave")[0] and not control.check_control_code("clave", None)[0]


def test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time():
    for _ in range(20):
        assert control.check_control_code("mal", "clave") == (False, "Clave incorrecta.")
    assert control.check_control_code("clave", "clave")[0]
    source = (Path(__file__).resolve().parent.parent / "bi" / "control.py").read_text(encoding="utf-8")
    assert "hmac.compare_digest" in source and not hasattr(control, "LoginGuard")


def test_d298_only_a_real_failure_of_the_last_finished_load_raises_the_alert():
    from datetime import datetime, timezone

    def run(state, number):
        return {"id": number, "state": state, "started_at": datetime(2026, 10, 20, tzinfo=timezone.utc)}

    assert control.latest_load_failure([run(control.RUN_FAILED, 2), run(control.RUN_OK, 1)])["id"] == 2
    assert control.latest_load_failure([run(control.RUN_IN_PROGRESS, 3), run(control.RUN_FAILED, 2)])["id"] == 2
    assert control.latest_load_failure([run(control.RUN_OK, 2), run(control.RUN_FAILED, 1)]) is None
    assert (
        control.latest_load_failure([run(control.RUN_SIMULATED_FAILURE, 2)]) is None
    )  # a requested test worries nobody
    assert control.latest_load_failure([]) is None


def test_d335_without_the_secret_no_key_opens_the_author_door():
    """The «Autor» door (D-335) uses the same CONTROL_CODE as «Acceso del autor». When that secret is not configured, it is
    None, and nothing opens: not an empty key, not the word None, not any text."""
    for typed in ("", None, "None", "null", "admin", "clave-de-prueba-local", " "):
        assert control.check_control_code(typed, None) == (False, "Clave incorrecta.")
        assert control.check_control_code(typed, "") == (False, "Clave incorrecta.")
    assert control.check_control_code("la-clave", "la-clave")[0]  # only the configured key opens it


def test_d335_a_visit_without_the_secret_never_unlocks_the_author_nor_raises_the_alert():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "bi" / "dashboard.py"), default_timeout=60)
    app.query_params.update({"perfil": "profesional", "lang": "es"})
    app.run()
    assert not app.exception
    assert not app.session_state["admin_unlocked"] if "admin_unlocked" in app.session_state else True
    assert not app.session_state["quality_alert_seen"] if "quality_alert_seen" in app.session_state else True


def test_d350_enter_sends_the_author_key_a_wrong_one_says_so_in_place_and_there_is_no_button():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "bi" / "dashboard.py"), default_timeout=60)
    app.secrets["CONTROL_CODE"] = "clave-larga"
    app.run()
    assert not app.exception and app.get("dialog")
    assert not [
        button for button in app.button if button.label == "Entrar" or str(button.key) == "profile_author_enter"
    ]
    app.text_input(key="profile_author_code").set_value("clave-mala").run()  # Enter on a wrong key
    assert not app.exception and app.get("dialog") and not app.session_state.get("admin_unlocked")
    assert [item.value for item in app.error] == ["Clave incorrecta."]  # in place, the window is still there
    assert app.text_input(key="profile_author_code").value == ""  # emptied, ready for another try
    app.text_input(key="profile_author_code").set_value("clave-larga").run()  # Enter on the right one
    assert not app.exception and app.session_state["admin_unlocked"] is True
    assert app.session_state["visitor_profile"] == "profesional" and not [
        box for box in app.text_input if box.key == "profile_author_code"
    ]
    assert not app.error and "clave-larga" not in str(dict(app.query_params))


def test_d350_the_english_reader_gets_the_error_in_english():
    from bi import i18n

    assert i18n.EN["Clave incorrecta."] == "Incorrect key."  # the message the door draws goes through tr()
    assert i18n.EN["Clave"] and i18n.EN["Autor"]


def test_d350_a_right_key_closes_the_window_with_a_full_rerun_because_the_window_is_a_fragment():
    import inspect

    from bi import dashboard

    body = inspect.getsource(dashboard.show_profile_dialog)
    assert "AUTHOR_ENTERED" in body and "st.rerun()" in body.split("AUTHOR_ENTERED")[1]
    assert "AUTHOR_ENTERED] = True" in inspect.getsource(dashboard.submit_author_code)


def test_d369_the_entry_window_offers_two_views_and_the_author_only_as_a_corner_link():
    from streamlit.testing.v1 import AppTest

    from bi import i18n

    for language, main, door in (
        ("es", ["Profesional", "Usuario"], "Acceso del autor"),
        ("en", ["Professional", "User"], "Author access"),
    ):
        app = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "bi" / "dashboard.py"), default_timeout=60)
        app.query_params.update({"lang": language})
        app.run()
        assert not app.exception and app.get("dialog")
        choices = [button.label for button in app.button if str(button.key).startswith("profile_choose_")]
        assert choices == main  # the two big options; the author is not one of them
        assert "Autor" not in choices and "Author" not in choices
        assert door in [popover.proto.popover.label for popover in app.get("popover")]
        assert app.text_input(key="profile_author_code")  # its key field, inside the link
    assert i18n.EN["Acceso del autor"] == "Author access"
    source = (Path(__file__).resolve().parent.parent / "bi" / "dashboard.py").read_text(encoding="utf-8")
    assert "profile_side_autor" not in source
    assert 'div[data-testid="stDialog"]:has(.st-key-profile_choices) {{ background:rgba(4, 8, 16, .97)' in source


def open_entry_window(view, language="es"):
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "bi" / "dashboard.py"), default_timeout=60)
    app.query_params.update({"vista": view, "lang": language})
    app.run()
    assert not app.exception and app.get("dialog")
    return app


def test_d371_any_profile_lands_on_the_panorama_from_any_page():
    from bi import dashboard

    for choice, view in (
        ("profile_choose_consulta", dashboard.PAGE_INSIGHTS),
        ("profile_choose_profesional", dashboard.PAGE_SECURITY),
        ("profile_role_data", dashboard.PAGE_RUNS),
    ):
        app = open_entry_window(view)
        app.button(key=choice).click().run()
        assert not app.exception and not app.get("dialog"), choice
        assert [box for box in app.selectbox if box.key == "home_products_channel"], choice  # the Panorama ran


def test_d371_a_document_the_address_opens_stays_after_the_choice():
    from bi import dashboard

    for language in ("es", "en"):
        app = open_entry_window(dashboard.PAGE_PRD, language)
        app.button(key="profile_choose_profesional").click().run()
        assert not app.exception and not app.get("dialog")
        assert dashboard.PAGE_PRD in str(app.query_params["vista"])


def test_d371_every_view_has_the_indicator_and_it_reopens_the_window():
    from bi import dashboard, i18n

    for choice, name in (
        ("profile_choose_consulta", "Usuario"),
        ("profile_choose_profesional", "Profesional"),
        ("profile_author_code", "Autor"),
    ):
        app = open_entry_window(dashboard.PAGE_PRD)
        if choice == "profile_author_code":
            app.secrets["CONTROL_CODE"] = "clave-larga"
            app.text_input(key=choice).set_value("clave-larga").run()
            if [button for button in app.button if button.key == "quality_alert_close"]:
                app.button(key="quality_alert_close").click().run()  # the author's alert comes first (D-335)
        else:
            app.button(key=choice).click().run()
        indicator = app.button(key="profile_indicator")
        assert name in indicator.label and not app.get("dialog"), name
        indicator.click().run()
        assert not app.exception and app.get("dialog") and app.button(key="profile_keep"), name
    assert all(i18n.EN[word] for word in ("Vista", "Usuario", "Profesional", "Autor"))
