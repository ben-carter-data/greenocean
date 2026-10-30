"""The view indicator at the foot of the menu (D-353): it names the current view, reopens «Elige tu vista», and leaving
the author's view closes the author's session."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

DASHBOARD_FILE = str(Path(__file__).resolve().parent.parent / "bi" / "dashboard.py")
KEY = "clave-larga"


def draw(profile=None, unlocked=False, language="es"):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.secrets["CONTROL_CODE"] = KEY
    app.query_params["lang"] = language
    if profile:
        app.session_state["visitor_profile"] = profile
    if unlocked:
        app.session_state["admin_unlocked"] = True
        app.session_state["quality_alert_seen"] = True
    return app.run()


def indicator(app):
    found = [button for button in app.sidebar.button if button.key == "profile_indicator"]
    return found[0] if found else None


def test_d353_the_indicator_names_the_current_view_in_both_languages():
    assert indicator(draw("consulta")).label == "Vista: Usuario ▾"
    assert indicator(draw("profesional")).label == "Vista: Profesional ▾"
    assert indicator(draw("profesional", unlocked=True)).label == "Vista: Autor ▾"
    assert indicator(draw("profesional", language="en")).label == "View: Professional ▾"
    assert indicator(draw()) is None  # before choosing there is the window itself, not an indicator


def test_d353_a_click_reopens_the_window_and_the_current_view_can_be_kept():
    app = draw("profesional")
    assert not app.get("dialog")
    indicator(app).click().run()
    assert not app.exception and app.get("dialog")
    assert [box for box in app.text_input if box.key == "profile_author_code"]  # «Elige tu vista» with its Autor door
    app.button(key="profile_keep").click().run()
    assert not app.get("dialog") and app.session_state["visitor_profile"] == "profesional"


def test_d353_choosing_another_view_updates_the_address_by_itself():
    app = draw("profesional")
    indicator(app).click().run()
    app.button(key="profile_choose_consulta").click().run()
    assert app.session_state["visitor_profile"] == "consulta" and app.query_params["perfil"] == "consulta"
    assert "rol" not in app.query_params and indicator(app).label == "Vista: Usuario ▾"
    indicator(app).click().run()
    app.button(key="profile_role_devops").click().run()
    assert app.query_params["perfil"] == "profesional" and app.query_params["rol"] == "devops"


def test_d353_leaving_the_author_view_closes_the_author_session_and_coming_back_asks_for_the_key():
    app = draw("profesional", unlocked=True)
    assert indicator(app).label == "Vista: Autor ▾"
    assert "GitHub Actions" in [link.proto.label for link in app.sidebar.get("page_link")]
    indicator(app).click().run()
    app.button(key="profile_choose_profesional").click().run()  # out of Autor, into Professional
    assert not app.session_state.get("admin_unlocked") and indicator(app).label == "Vista: Profesional ▾"
    assert "GitHub Actions" not in [link.proto.label for link in app.sidebar.get("page_link")]
    indicator(app).click().run()
    app.text_input(key="profile_author_code").set_value("equivocada").run()  # the door asks again
    assert not app.session_state.get("admin_unlocked") and [item.value for item in app.error] == ["Clave incorrecta."]
    app.text_input(key="profile_author_code").set_value(KEY).run()
    assert app.session_state["admin_unlocked"] is True and indicator(app).label == "Vista: Autor ▾"
