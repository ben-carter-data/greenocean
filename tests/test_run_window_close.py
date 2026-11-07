"""Closing the window of the manual run (D-379): «Minimizar» and «Cerrar» are callbacks that first cancel the window's
refresh timer, so a refresh that lands while the page reruns cannot leave the window open with dead buttons."""

import pytest

from bi import dashboard, queries, run_monitor
from tests import code_shape  # noqa: E402
from tests.test_dashboard import FAKE_TOKEN, button_keys, draw_control_page, open_run_dialog

# region Variables
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")
# endregion


# region Closing the window of the manual run
def test_d379_the_two_actions_that_close_the_window_are_callbacks_not_inline_reruns():
    shape = code_shape.tree_of(dashboard.render_run_window)
    clicks = {code_shape.keyword(call, "on_click") for call in code_shape.calls(shape, "st.button")}
    assert {"minimize_run_window", "close_run_window"} <= clicks
    inline = set(code_shape.buttons_tested_inline(shape))
    assert not {code_shape.normal('tr("Minimizar")'), code_shape.normal('tr("Cerrar")')} & inline
    assert not code_shape.deletes(shape)  # forgetting the run happens in the callback, before the refresh
    # Cancelling still asks first and reruns only the window (nothing to close yet).
    reruns = code_shape.calls(shape, "st.rerun")
    assert sum(code_shape.keyword(call, "scope") == code_shape.normal('"fragment"') for call in reruns) == 3


def test_d379_the_window_is_held_by_a_keyed_shell_that_closes_the_page_without_drawing_the_refreshing_part():
    request = code_shape.tree_of(dashboard.request_run_window_close)
    assert code_shape.sets_true(request, "RUN_WINDOW_CLOSING")
    assert [code_shape.arguments(call) for call in code_shape.calls(request, "st.rerun")] == [["RUN_WINDOW_KEY"]]
    shell = code_shape.tree_of(dashboard.show_run_window_shell)
    fragments = code_shape.calls(shell, "st.fragment")
    closing, rerun = code_shape.uses(shell, "RUN_WINDOW_CLOSING"), code_shape.calls(shell, "st.rerun")
    assert code_shape.first(closing) < code_shape.first(rerun) < code_shape.first(fragments)
    assert [code_shape.arguments(call)[0] for call in fragments] == ["render_run_window"]
    shells = code_shape.calls(code_shape.tree_of(dashboard.show_run_now_dialog), "st.fragment")
    assert [code_shape.keyword(call, "key") for call in shells] == ["RUN_WINDOW_KEY"]
    assert not any(code_shape.keyword(call, "run_every") for call in shells)  # the shell has no timer of its own
    window = code_shape.tree_of(dashboard.render_run_window)
    assert code_shape.first(code_shape.calls(window, "st.session_state.get")) < code_shape.first(
        code_shape.calls(window, "run_monitor.refresh")
    )
    assert "watch is None" in code_shape.conditions(window)  # a copy of the window that outlived its run closes


def test_d379_closing_forgets_the_run_and_minimizing_keeps_it(monkeypatch):
    state = {}
    monkeypatch.setattr(dashboard.st, "session_state", state)
    requested = []
    monkeypatch.setattr(dashboard.st, "rerun", lambda key: requested.append(key))
    watch = state[run_monitor.WATCH] = {"phase": "running", "minimized": False}
    dashboard.minimize_run_window()
    assert state[run_monitor.WATCH] is watch and watch["minimized"] and watch["phase"] == "running"
    assert state[dashboard.RUN_WINDOW_CLOSING] is True and requested == [dashboard.RUN_WINDOW_KEY]
    state.pop(dashboard.RUN_WINDOW_CLOSING)
    dashboard.close_run_window()
    assert run_monitor.WATCH not in state and state[dashboard.RUN_WINDOW_CLOSING] is True
    assert requested == [dashboard.RUN_WINDOW_KEY] * 2  # always the shell first, never the whole page directly


@needs_database
def test_d379_a_finished_run_closes_with_cerrar_and_a_running_one_minimizes_and_goes_on():
    app = draw_control_page({"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="ok", dialog=True)
    open_run_dialog(app, "clave")
    app.run()
    assert "run_close" in button_keys(app)
    finished = app.session_state["run_watch"]
    app.button(key="run_close").click().run().run()
    # The harness opens the window again on every run (a browser reruns the page without it), so closing shows here as
    # the finished run forgotten and a fresh one started; the callbacks themselves are checked above.
    assert not app.exception and app.session_state["run_watch"] is not finished
    assert app.session_state["run_watch"]["started"] > finished["started"]
    running = draw_control_page(
        {"CONTROL_CODE": "clave", "GITHUB_TOKEN": FAKE_TOKEN}, run_state="in_progress", dialog=True
    )
    open_run_dialog(running, "clave")
    running.run()
    running.button(key="run_minimize").click().run().run()
    watch = running.session_state["run_watch"]
    assert not running.exception and watch["minimized"] and watch["phase"] == "running"


# endregion
# (The run goes on in GitHub and the menu's indicator brings the window back, D-351: see its own tests.)
