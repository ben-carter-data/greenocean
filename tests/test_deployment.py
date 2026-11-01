"""«Despliegue» (D-255): the deployment diagram says what the workflows, the files and the services really are."""

from pathlib import Path
from urllib.parse import urlparse


from bi import architecture, charts, control, deployment, project, queries

REPOSITORY = Path(__file__).resolve().parent.parent
STATES = {"sources": control.RUN_OK, "workflow": control.RUN_OK, "panel": control.RUN_OK}
FIGURES = {
    "next_run": "27-10 09:00",
    "week_prices": "semana 12-10: 3.032 precios",
    "panel_time": "datos al 20-10 12:54",
}


def draw(states=None, figures=None):
    return deployment.build_deployment_html(charts.get_palette("Vantablack"), states or STATES, figures or FIGURES)


def test_the_diagram_has_the_nodes_and_the_environments_of_a_deployment_diagram():
    page = draw()
    for stereotype in ("«dispositivo»", "«plataforma»", "«entorno de ejecución»"):
        assert stereotype in page
    for key in list(deployment.NODES) + list(deployment.ENVIRONMENTS):
        assert f'id="n-{key}"' in page and f'id="tip-{key}"' in page, key
    for protocol in (
        "HTTPS",
        "git push",
        "API REST de GitHub",
        "lanzar, leer estado y logs, cancelar",
        "despliegue de main",
    ):
        assert protocol in page
    assert "<script" not in page


def test_what_is_drawn_exists_in_the_workflows_and_the_repository():
    weekly = (REPOSITORY / ".github/workflows/semanal.yml").read_text(encoding="utf-8")
    tests = (REPOSITORY / ".github/workflows/pruebas.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch" in weekly and "runs-on: ubuntu-latest" in weekly and 'python-version: "3.11"' in weekly
    assert "runs-on: ubuntu-latest" in tests and "actions/cache" in weekly
    assert "gh issue create" in weekly or "issues" in weekly
    # D-270: the repository keeps the pointer of the served database; the file itself is in the release.
    for path in (
        "etl/datos.version",
        "bi/served_database.py",
        "agent/downloads/manifest.json",
        "bi/dashboard.py",
        ".github/workflows/semanal.yml",
        ".github/workflows/pruebas.yml",
    ):
        assert (REPOSITORY / path).exists(), path
    assert "gh release upload base-actual" in weekly
    page = draw()
    for artifact in (
        "semanal.yml",
        "pruebas.yml",
        "dashboard.py",
        "manifest.json",
        "datos.version",
        "release",
        "st.secrets",
    ):
        assert artifact in page, artifact


def test_the_hosts_and_the_sizes_are_read_not_typed():
    page = draw()
    assert urlparse(project.WHOLESALE_SOURCE_URL).netloc in page and urlparse(project.INE_IPC_SOURCE_URL).netloc in page
    assert f"datos.duckdb · {project.describe_file_size(queries.DATABASE_FILE)}" in page
    for figure in FIGURES.values():
        assert figure in page


def test_a_failed_workflow_is_drawn_in_its_color_and_an_unknown_one_has_no_dot():
    failed = draw(dict(STATES, workflow=control.RUN_FAILED))
    assert architecture.STATE_COLORS[control.RUN_FAILED] in failed
    unknown = draw(
        dict(
            STATES,
            workflow=architecture.STATE_UNKNOWN,
            panel=architecture.STATE_UNKNOWN,
            sources=architecture.STATE_UNKNOWN,
        )
    )
    assert unknown.count("<circle cx=") == 1  # only the legend's dot


def test_d383_the_weekly_report_is_an_issue_and_the_quality_report_a_pull_request():
    from bi import i18n_en

    page = draw()
    assert "workflow_dispatch" not in page
    assert ">Issues<" in page and ">informe semanal<" in page
    assert ">Pull requests<" in page and ">informe de calidad<" in page
    weekly = (REPOSITORY / ".github/workflows/semanal.yml").read_text(encoding="utf-8")
    assert 'gh issue create --title "Informe semanal' in weekly  # the weekly report is an issue
    calidad = (REPOSITORY / ".github/workflows/calidad.yml").read_text(encoding="utf-8")
    assert "workflow_run" in calidad and "informe-calidad/" in calidad  # the quality report is a pull request
    for text in (
        "API REST de GitHub",
        "lanzar, leer estado y logs, cancelar",
        "informe semanal",
        "informe de calidad",
        deployment.TIPS["issues"],
        deployment.TIPS["pulls"],
    ):
        assert text in i18n_en.PAGES, text


def test_d422_the_release_has_its_own_box_and_the_three_workflows_are_drawn():
    page = draw()
    size = project.describe_file_size(queries.DATABASE_FILE)
    # the served database lives in the release; the repository keeps only its pointer (D-270)
    release = page.split('id="n-release"')[1].split("</g>")[0]
    repo = page.split('id="n-repo"')[1].split("</g>")[0]
    assert "Release «base-actual»" in release and f"datos.duckdb · {size}" in release
    assert "datos.version" in repo and "datos.duckdb" not in repo
    # the weekly runner holds the load and its quality report; the tests of each push run on a runner of their own
    runner = page.split('id="n-runner"')[1].split('id="n-python"')[0]
    tests = page.split('id="n-tests"')[1].split("</g>")[0]
    assert "semanal.yml" in runner and "calidad.yml" in runner and "pruebas.yml" not in runner
    assert "pruebas.yml" in tests and "en cada push" in tests and "calidad.yml" in tests
    calidad = (REPOSITORY / ".github/workflows/calidad.yml").read_text(encoding="utf-8")
    assert "push:" in calidad and "workflow_run" in calidad  # it measures on each push and proposes after the load
    # the load uploads to the release, the panel downloads from it and every push starts the tests
    paths = [d for d, *_ in deployment.PATHS]
    assert "M542 316 H892 V290" in paths and "M1020 278 H984" in paths and "M542 450 H590" in paths
    # nothing is drawn past the frame: the side of the last node ends inside the drawing (no stripe on the right)
    right = max(x + width + deployment.DEPTH for x, _, width, *_ in deployment.NODES.values())
    assert right <= deployment.WIDTH
