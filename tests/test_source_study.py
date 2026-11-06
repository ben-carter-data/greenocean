"""D-533: «Análisis de la fuente de datos», the folder of the two notebooks that study ODEPA's raw wholesale file."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from bi import dashboard, source_study

DASHBOARD_FILE = str(Path(dashboard.__file__))


def draw(language="es", notebook=None, profile=dashboard.PROFILE_PROFESSIONAL):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.query_params["vista"] = dashboard.PAGE_SOURCE_STUDY
    if language == "en":
        app.query_params["lang"] = "en"
    if notebook:
        app.query_params[source_study.NOTEBOOK_PARAMETER] = notebook
    app.session_state[dashboard.PROFILE_STATE] = profile
    return app.run()


def test_d533_the_two_notebooks_are_the_same_study_and_keep_their_outputs():
    spanish, english = (source_study.read_notebook(path)["cells"] for _, path in source_study.NOTEBOOKS)
    assert [cell["cell_type"] for cell in spanish] == [cell["cell_type"] for cell in english]
    # Saved run, so the panel and GitHub show the results: the same cells print in both, and none failed.
    printed = [
        [bool(cell.get("outputs")) for cell in cells if cell["cell_type"] == "code"] for cells in (spanish, english)
    ]
    assert printed[0] == printed[1] and sum(printed[0]) >= 20
    for cells in (spanish, english):
        assert all(cell.get("execution_count") for cell in cells if cell["cell_type"] == "code")
        assert all(output["output_type"] != "error" for cell in cells for output in cell.get("outputs", []))


def test_d533_the_folder_lists_both_notebooks_and_opens_the_one_of_the_visit():
    for language in ("es", "en"):
        app = draw(language)
        assert not app.exception
        markup = " ".join(block.value for block in app.markdown)
        assert markup.count('class="df-file nb-file"') == 2
        assert len(app.get("download_button")) == 2
        opens = f"{source_study.NOTEBOOK_PARAMETER}={language}"
        other = "en" if language == "es" else "es"
        assert opens in markup and f"{source_study.NOTEBOOK_PARAMETER}={other}" not in markup


def test_d533_an_opened_notebook_shows_its_code_and_its_saved_outputs_without_running():
    app = draw("en", "en")
    assert not app.exception
    cells = source_study.read_notebook(source_study.NOTEBOOKS[1][1])["cells"]
    assert len(app.code) == sum(cell["cell_type"] == "code" for cell in cells)
    outputs = [block.proto.body for block in app.get("html") if source_study.OUTPUT_OPEN in block.proto.body]
    assert len(outputs) == sum(bool(cell.get("outputs")) for cell in cells if cell["cell_type"] == "code")
    assert any("155,857" in body for body in outputs)  # what the file printed, as it printed it
    assert len(app.get("download_button")) == 1


def test_d533_the_other_language_does_not_open_and_the_user_view_has_no_folder():
    app = draw("en", "es")  # the Spanish notebook in an English visit: the folder, not its Spanish text
    assert not app.exception and len(app.code) == 0
    user = draw(profile=dashboard.PROFILE_PUBLIC)
    labels = {link.proto.label for link in user.sidebar.get("page_link")}
    assert not set(dashboard.FOLDER_TILES) & labels and len(user.code) == 0
