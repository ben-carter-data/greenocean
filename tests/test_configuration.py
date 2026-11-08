"""«Configuración» (D-409): only the author sees it; it never shows a token; its colours follow the dates; its cases,
steps and links are read from the runbook in both languages; and it replaces «Enlaces del autor»."""

from datetime import date, datetime, timedelta, timezone

import pytest

from bi import configuration, control, dashboard, i18n
from tests.test_actions_page import draw, everything_drawn, menu_labels, network  # noqa: F401
from tests.test_github_actions import READ_TOKEN, TOKEN

# region Constants
NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
# endregion


# region «Configuración»
def draw_author(language):
    """The page as the author opens it, with both tokens and the view already chosen: each case opens its window
    without the window «Elige tu vista» asking first."""
    app = draw(view="Configuración", language=language, run=False)
    app.session_state["visitor_profile"] = "profesional"
    return app.run()


def test_d409_only_the_author_has_the_page_in_devops_and_security(network):  # noqa: F811
    visitor = draw(unlocked=False, view="Dashboard")
    assert not visitor.exception and "Configuración" not in menu_labels(visitor)
    author = draw(unlocked=True, view="Dashboard")
    labels = menu_labels(author)
    assert labels.index("GitHub Actions") < labels.index("Configuración") < labels.index("Arquitectura de seguridad")
    network.calls.clear()
    closed = draw(unlocked=False, view="Configuración")
    assert [item.value for item in closed.info] == [dashboard.NO_ACCESS]
    assert network.calls == []  # without the key nothing is asked of GitHub


@pytest.mark.parametrize("language", ["es", "en"])
def test_d409_the_page_shows_six_states_five_cases_and_never_a_token(network, language):  # noqa: F811
    app = draw_author(language)
    assert not app.exception
    page = everything_drawn(app)
    assert page.count('class="cf-card ') == 6 and 'class="cf-tasks"' in page and 'class="cf-guide"' in page
    cases = [button for button in app.main.button if str(button.key).startswith("config_case_")]
    assert [button.label for button in cases] == [case["name"] for case in configuration.read_cases(language)]
    for index in range(len(cases)):
        app.button(key=f"config_case_{index}").click().run()
        assert not app.exception
        page += everything_drawn(app)
    assert TOKEN not in page and READ_TOKEN not in page and "github_pat_" not in page
    assert "Automático" in page if language == "es" else "Automatic" in page


def token_state(**kwargs):
    """The card of a token on the day NOW: present, with no expiration and no error unless `kwargs` say otherwise."""
    values = {"present": True, "expiration": None, "error": None} | kwargs
    return configuration.token_card("t", "Token", values["present"], values["expiration"], values["error"], NOW)


def test_d409_a_token_is_amber_at_fifteen_days_or_fewer_and_red_when_it_expired_or_is_missing():
    assert control.TOKEN_WARNING_DAYS == 15
    assert token_state(expiration=NOW + timedelta(days=16, hours=1))["state"] == configuration.OK
    amber = token_state(expiration=NOW + timedelta(days=15, hours=1))
    assert amber["state"] == configuration.WARN and amber["value"] == "15 días" and "16-11-2026" in amber["detail"]
    assert token_state(expiration=NOW - timedelta(days=1))["state"] == configuration.FAIL
    assert token_state(present=False)["state"] == configuration.FAIL and token_state(present=False)["value"] == "Falta"
    assert token_state(error="GitHub no respondió")["state"] == configuration.UNKNOWN
    assert token_state()["value"] == "Sin vencimiento"
    # the panel's own warning follows the same rule
    assert control.describe_token_expiration(NOW + timedelta(days=15, hours=1), NOW)[1]
    assert not control.describe_token_expiration(NOW + timedelta(days=16, hours=1), NOW)[1]


def test_d409_the_load_the_report_the_tests_and_the_sources_take_their_colour_from_what_they_read():
    loaded = NOW - timedelta(days=2)
    assert configuration.load_card(loaded, None, NOW)["state"] == configuration.OK
    assert configuration.load_card(NOW - timedelta(days=9), None, NOW)["state"] == configuration.WARN
    failed = configuration.load_card(loaded, NOW - timedelta(hours=1), NOW)
    assert failed["state"] == configuration.FAIL and "30-10-2026" in failed["detail"]
    report = {"numero": 7, "fecha": "2026-10-31", "indicadores": [{"estado": "aceptable"}, {"estado": "urgente"}]}
    assert configuration.report_card(report, date(2026, 11, 1))["state"] == configuration.WARN
    assert configuration.report_card(report, date(2026, 11, 20))["detail"].startswith("31-10-2026")
    critical = report | {"indicadores": [{"estado": "critico"}]}
    assert configuration.report_card(critical, date(2026, 11, 1))["state"] == configuration.FAIL
    # D-411: a test value never shaped like a key, so the secrets scan has nothing to flag
    run = {"branch": "main", "state": control.RUN_OK, "started_at": NOW, "sha": "1234567"}
    other = run | {"branch": "otra", "state": control.RUN_FAILED}
    assert configuration.ci_card([other, run], None)["value"] == "En verde"  # only main counts
    assert configuration.ci_card([], "sin red")["state"] == configuration.UNKNOWN
    assert configuration.sources_card("")["state"] == configuration.OK
    assert configuration.sources_card("ODEPA aún no publica la semana 26 oct – 1 nov")["state"] == configuration.WARN


def test_d409_the_cases_and_their_steps_are_the_runbook_s_in_both_languages():
    spanish, english = configuration.read_cases("es"), configuration.read_cases("en")
    assert [case["name"] for case in spanish] == [
        "La carga falló",
        "Llegó un informe",
        "Un token vence o falta",
        "Una fuente se atrasó",
        "La app no se actualiza",
    ]
    assert len(english) == len(spanish) == len(configuration.CASE_ICONS)
    for one, other in zip(spanish, english):
        assert [step["step"] for step in one["steps"]] == list(range(1, len(one["steps"]) + 1))
        assert [step["automatic"] for step in one["steps"]] == [step["automatic"] for step in other["steps"]]
        for mine, theirs in zip(one["steps"], other["steps"]):
            if mine["link"] and mine["link"]["kind"] == "url":
                assert mine["link"]["target"] == theirs["link"]["target"]
            elif mine["link"]:  # a page of the panel, named in each language, is the same page
                assert dashboard.find_menu_page(mine["link"]["target"]) == dashboard.find_menu_page(
                    theirs["link"]["target"]
                )
                assert dashboard.find_menu_page(mine["link"]["target"]) is not None
            else:
                assert theirs["link"] is None
    token = spanish[2]["steps"]
    assert any("una sola vez" in step["text"] for step in token) and "Reboot" in token[-1]["text"]
    step = configuration.build_step_html(token[1])
    assert 'target="_blank"' in step and "<code>GITHUB_TOKEN</code>" in step and "Manual" in step


def test_d409_the_guide_is_the_runbook_s_github_guide_with_both_token_links():
    for language in ("es", "en"):
        links = configuration.read_guide(language)
        addresses = [link["url"] for link in links]
        assert all(address.startswith("https://") for address in addresses)
        assert "https://github.com/settings/personal-access-tokens" in addresses
        assert "https://github.com/settings/personal-access-tokens/new" in addresses
    assert [link["url"] for link in configuration.read_guide("es")] == [
        link["url"] for link in configuration.read_guide("en")
    ]
    html = configuration.build_guide_html(configuration.read_guide("es"))
    assert html.count('target="_blank" rel="noopener noreferrer"') == len(configuration.read_guide("es"))


def test_d409_maintenance_dates_come_from_github_and_input_csv_is_checked_each_january():
    expiration = datetime(2027, 1, 17, tzinfo=timezone.utc)
    schedule = configuration.read_schedule("es")
    tasks = configuration.maintenance(
        [("token de lanzamiento", True, expiration), ("token de solo lectura", False, None)],
        2,
        schedule,
        date(2026, 11, 1),
        {"wholesale": {2026}, "consumer": {2026}},
    )
    whats = [task["what"] for task in tasks]
    assert tasks[0] == {"what": "Renovar el token de lanzamiento", "when": "antes del 17-01-2027", "state": "ok"}
    assert tasks[1]["state"] == configuration.FAIL and tasks[2]["when"] == "2 en GitHub"
    assert any("agent/input.csv" in what for what in whats) and any("agent/downloads" in what for what in whats)
    january = configuration.maintenance([], 0, schedule, date(2027, 1, 10), {"wholesale": {2026}, "consumer": {2026}})
    assert next(task for task in january if "input.csv" in task["what"])["state"] == configuration.FAIL
    done = configuration.maintenance([], 0, schedule, date(2027, 1, 10), {"wholesale": {2027}, "consumer": {2027}})
    assert next(task for task in done if "input.csv" in task["what"])["when"] == "hecho para 2027"
    line, whole = configuration.short(next(row["what"] for row in schedule if "agent/downloads" in row["what"]))
    assert line == "Copiar `agent/downloads` a otro disco" and "](" not in whole


def test_d409_the_cards_read_in_english(monkeypatch):
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    card = configuration.token_card("t", "Token", True, NOW + timedelta(days=20), None, NOW)
    assert card["value"] == "20 days" and card["detail"] == "expires on 2026-11-21"


def test_d409_in_english_nothing_is_left_in_spanish(network):  # noqa: F811
    from tests import i18n_audit

    state = {"admin_unlocked": True, "quality_alert_seen": True}
    assert i18n_audit.spanish_left("Configuración", i18n_audit.read_data_values(), state=state) == []


def test_d410_a_token_at_fifteen_days_or_fewer_joins_the_authors_alert():
    assert configuration.token_alert("token de lanzamiento", NOW + timedelta(days=16, hours=1), NOW) is None
    assert configuration.token_alert("token de lanzamiento", None, NOW) is None  # a token that never expires
    near = configuration.token_alert("token de lanzamiento", NOW + timedelta(days=15, hours=1), NOW)
    assert near == {"label": "token de lanzamiento", "days": 15, "date": "16-11-2026", "expired": False}
    gone = configuration.token_alert("token de solo lectura", NOW - timedelta(days=2), NOW)
    html = configuration.build_token_alerts_html([near, gone])
    assert '<div class="qm-alert qm-urgente"><h4>Token de lanzamiento · vence en 15 días</h4>' in html
    assert '<div class="qm-alert qm-critico"><h4>Token de solo lectura · venció el 30-10-2026</h4>' in html
    assert "«Configuración», en «Un token vence o falta»" in html
    assert configuration.build_token_alerts_html([]) == ""


@pytest.mark.parametrize("days, shown", [(10, True), (40, False)])
def test_d410_the_alert_opens_with_the_tokens_first_and_never_their_value(network, monkeypatch, days, shown):  # noqa: F811
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(control, "read_token_expiration", lambda token: now + timedelta(days=days, hours=1))
    app = draw(view="Dashboard", run=False)
    app.session_state["visitor_profile"] = "profesional"
    app.session_state["quality_alert_seen"] = False
    app.run()
    assert not app.exception
    page = everything_drawn(app)
    assert ("Token de lanzamiento · vence en 10 días" in page) is shown
    assert ("Token de solo lectura · vence en 10 días" in page) is shown
    if shown and 'class="qm-alert-foot"' in page:  # the report's part, when it has one, comes after the tokens
        assert page.index("Token de lanzamiento") < page.index('class="qm-alert-foot"')
    assert TOKEN not in page and READ_TOKEN not in page


# endregion
