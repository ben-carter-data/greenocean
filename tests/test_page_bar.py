"""The thin header bar of the main pages (D-267) and the reading of an enlarged family."""
import re
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from bi import charts, dashboard, inflation_view, page_bar, queries  # noqa: E402
from tests.test_dashboard import DASHBOARD_FILE, draw_page, needs_database  # noqa: E402

MAIN_PAGES = [dashboard.PAGE_SEASONALITY, dashboard.PAGE_DIAGRAMS, dashboard.PAGE_ARCHITECTURE,
              dashboard.PAGE_OPERATIONS, dashboard.PAGE_SQL, dashboard.PAGE_RUNS, dashboard.PAGE_SECURITY,
              dashboard.PAGE_STACK]


def test_the_title_is_not_said_twice_and_the_whole_path_stays_readable():
    bar = page_bar.build_bar_html("Ingeniería de datos › Modelo de datos", "Modelo de datos", "Cómo se organizan.")
    assert bar.count("Modelo de datos</") == 1 and 'aria-label="Página actual: Ingeniería de datos › Modelo de datos"' in bar
    assert '<span class="page-bar-path">Ingeniería de datos ›</span>' in bar
    question = page_bar.build_bar_html("Negocio · BI › Precios e inflación", "¿Qué subió?", "La respuesta.",
                                       [("<b>+1 %</b>", "Uno por ciento")])
    assert "<b>Precios e inflación</b>" in question and 'title="La respuesta."' in question
    assert '<span class="page-chip" title="Uno por ciento"><b>+1 %</b></span>' in question


def test_every_theme_styles_the_bar():
    for mode in charts.THEMES:
        css = page_bar.build_css(charts.get_palette(mode))
        assert ".st-key-page_bar" in css and ".page-bar-title" in css and ".page-bar-terms" in css


@needs_database
@pytest.mark.parametrize("view", MAIN_PAGES)
def test_d267_each_main_page_has_one_bar_and_no_other_header(view):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=60)
    app.query_params["vista"] = view
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert markup.count('class="page-bar-main"') == 1 and markup.count('class="page-bar-updated"') == 1
    assert 'class="compact-header"' not in markup and 'class="app-brand"' not in markup
    assert [str(button.key) for button in app.button].count("return_to_previous") == 1
    assert f'aria-label="Página actual: {dashboard.build_view_path(dashboard.WINDOW_OF_VIEW[view], view)}"' in markup


@needs_database
def test_d267_inflation_bar_counts_the_answer_and_names_its_kpi_and_metric():
    app = draw_page(dashboard.PAGE_SEASONALITY)
    markup = " ".join(block.value for block in app.markdown)
    rows, last, summary, ipc_total, ipc_year = dashboard.read_family_inflation(dashboard.get_database_version())
    above = (summary["verdict"] == "más que la inflación").sum()
    below = (summary["verdict"] == "menos que la inflación").sum()
    assert f'<b class="rise">{above} más</b><b class="fall">{below} menos</b>' in markup
    assert f"<em>IPC</em><b>{charts.format_signed_percent(ipc_total)}</b>" in markup
    assert "<em>KPI</em>" in markup and "<em>Métrica</em>" in markup
    assert 'class="ctx-answer"' not in markup  # the long answer lives on the title's hover


@pytest.fixture(scope="module")
def inflation():
    rows, last = inflation_view.build_family_index(queries.run_sql(inflation_view.SERIES_SQL),
                                                   queries.run_sql("SELECT year, month, food_index FROM ipc_monthly"))
    summary, ipc_total, ipc_year = inflation_view.summarize_families(rows, last)
    return rows, last, summary, ipc_total, ipc_year


@needs_database
def test_d267_the_reading_of_a_family_is_recomputed_from_its_index(inflation):
    rows, last, summary, ipc_total, ipc_year = inflation
    for row in summary.itertuples():
        reading = dict(inflation_view.family_insights(rows, summary, row.family, last))
        first = reading["Desde enero 2022"]
        assert first.startswith(f"Subió {charts.format_signed_percent(row.total)}")
        gap = round(row.total, 1) - round(ipc_total, 1)
        assert inflation_view.points(gap) in first and row.verdict in first
        series = rows[rows["product_group"] == row.family]
        peak = series.loc[series["index"].idxmax()]
        assert inflation_view.month_name(int(peak["year"]), int(peak["month"])) in reading["Máximo"]
        assert f"{int(series['series'].max())} series" in reading["Base del cálculo"]
        assert charts.format_signed_percent(series["real"].iloc[-1] - 100) in reading["Sin inflación"]


@needs_database
def test_d267_without_inflation_the_reading_follows_the_line_the_chart_draws(inflation):
    rows, last, summary, *_ = inflation
    family = summary["family"].iloc[0]
    reading = dict(inflation_view.family_insights(rows, summary, family, last, real=True))
    series = rows[rows["product_group"] == family]
    peak = series.loc[series["real"].idxmax()]
    assert f"{peak['real']:.1f}".replace(".", ",") in reading["Máximo (sin inflación)"]
    ipc = dict(inflation_view.family_insights(rows, summary, inflation_view.IPC_NAME, last, real=True))
    assert not any(label.startswith("Mayor movimiento") for label in ipc)  # the flat 100 line has no move
    counts = summary["verdict"].value_counts()
    assert re.match(rf"{counts.get('más que la inflación', 0)} subieron más", ipc["Frente a las familias"])


@needs_database
def test_d267_ampliar_shows_the_chart_beside_its_reading():
    app = draw_page(dashboard.PAGE_SEASONALITY, state={dashboard.FAMILY_FOCUS_KEY: "Hortalizas"})
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert 'class="inf-insights"' in markup and "Lectura de los datos" in markup
    assert len(app.get("vega_lite_chart")) == 1
