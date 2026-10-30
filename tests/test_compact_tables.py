"""Compact lists (D-348): no table that grows shows more than 20 rows at once, rows are collapsed and one opens at a time."""

import copy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from bi import compact_table, git_workflow

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = str(ROOT / "bi" / "dashboard.py")


def script():
    from bi import compact_table

    compact_table.show_compact_rows(
        "cr_test", list(range(45)), lambda row: f"row {row}", lambda row: f"<p>detail {row}</p>", signature="a"
    )


def row_buttons(app, prefix="cr_test"):
    return [button for button in app.button if str(button.key).startswith(f"{prefix}_toggle_")]


def test_d348_a_list_shows_at_most_twenty_rows_and_pages_through_the_rest():
    assert compact_table.PAGE_SIZE == 20 and compact_table.page_count(45) == 3 and compact_table.page_count(0) == 1
    app = AppTest.from_function(script).run()
    assert not app.exception and len(row_buttons(app)) == 20
    assert [caption.value for caption in app.caption] == ["Página 1 de 3 · 45 filas"]
    assert app.button(key="cr_test_prev").disabled and not app.button(key="cr_test_next").disabled
    app.button(key="cr_test_next").click().run()
    assert len(row_buttons(app)) == 20 and row_buttons(app)[0].label == "row 20"
    app.button(key="cr_test_next").click().run()
    assert len(row_buttons(app)) == 5 and app.button(key="cr_test_next").disabled  # 45 = 20 + 20 + 5


def test_d348_rows_start_collapsed_and_only_one_opens_at_a_time():
    app = AppTest.from_function(script).run()
    assert not [item for item in app.markdown if "detail" in item.value]
    app.button(key="cr_test_toggle_0").click().run()
    assert [item.value for item in app.markdown if "detail" in item.value] == ["<p>detail 0</p>"]
    app.button(key="cr_test_toggle_3").click().run()
    assert [item.value for item in app.markdown if "detail" in item.value] == ["<p>detail 3</p>"]  # the first closed
    app.button(key="cr_test_toggle_3").click().run()
    assert not [item for item in app.markdown if "detail" in item.value]


def incident_page(monkeypatch, many, unlocked):
    base = git_workflow.read_failures()
    rows = []
    for number in range(many):
        row = copy.deepcopy(base[number % len(base)])
        row["fecha"] = f"2026-10-{29 - number % 28:02d}"
        rows.append(row)
    monkeypatch.setattr(git_workflow, "read_failures", lambda: rows)
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.query_params.update({"vista": "Git workflow"})
    app.session_state["visitor_profile"] = "profesional"
    if unlocked:
        app.session_state["admin_unlocked"] = True
        app.session_state["quality_alert_seen"] = True
    app.run()
    return app, rows


def test_d348_the_incident_log_pages_by_twenty_and_the_diagnosis_is_the_authors(monkeypatch):
    app, rows = incident_page(monkeypatch, 45, unlocked=False)
    assert not app.exception and len(row_buttons(app, "cr_incidents")) == 20
    assert any("Página 1 de 3" in caption.value for caption in app.caption)
    app.button(key="cr_incidents_toggle_0").click().run()
    detail = " ".join(item.value for item in app.markdown if "cr-detail" in item.value and "<ul" in item.value)
    assert rows[0]["solucion"][0][:30] in detail and rows[0]["diagnostico"][0][:30] not in detail  # the professional
    author, rows = incident_page(monkeypatch, 45, unlocked=True)
    author.button(key="cr_incidents_toggle_0").click().run()
    detail = " ".join(item.value for item in author.markdown if "cr-detail" in item.value and "<ul" in item.value)
    assert rows[0]["diagnostico"][0][:30] in detail  # the author's


def test_d348_the_log_is_a_fixed_height_box_closed_by_default_and_the_reports_list_uses_the_same_component():
    source = Path(DASHBOARD_FILE).read_text(encoding="utf-8")
    block = source[source.index("def show_workflow_detail") : source.index("def show_actions_page")]
    assert "st.expander(" in block and "expanded=False" in block and "st.container(height=300)" in block
    assert 'compact_table.show_compact_rows(\n                "cr_reports"' in source.replace("\r", "")
    assert 'compact_table.show_compact_rows(\n        "cr_actions"' in source
