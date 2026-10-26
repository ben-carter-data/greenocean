"""Tests for the live data journey diagram."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import architecture, charts, control  # noqa: E402

FIGURES = {"source_years": "año 2026", "last_run": "última 12-10 05:51",
           "rows_read": "397.814 filas leídas", "rows_rejected": "0 filas",
           "weekly_prices": "131.144 precios", "latest_week": "hasta 05-10-2026",
           "panel_time": "datos al 12-10 05:52", "next_run": "13-10 09:00"}
STATE_NAMES = ["sources", "download", "etl", "tests", "report", "workflow", "load", "panel"]


def make_states(state):
    return {name: state for name in STATE_NAMES}


def test_every_layer_and_step_is_drawn():
    svg = architecture.build_journey_svg(make_states(control.RUN_OK), FIGURES,
                                         charts.MODE_DARK)
    for text in ["FUENTES", "INGESTA", "ATERRIZAJE", "BRONZE", "STAGING", "INTERMEDIO",
                 "MARTS", "SERVING", "CONSUMO", "raw.db", "Parquet · bronce", "datos.duckdb",
                 "Rechazos", "GitHub Actions", "OBSERVABILIDAD", "INE · IPC", "Descarga INE"]:
        assert text in svg


def test_medallion_bands_read_bronze_silver_gold_left_to_right_without_overlap():
    """Bronze is the Parquet copy, silver the dbt staging and intermediate steps, gold the
    marts and datos.duckdb; dbt is a bracket over staging to marts, across silver and gold."""
    states = make_states(control.RUN_OK)
    for mode in [charts.MODE_DARK, charts.MODE_LIGHT]:
        svg = architecture.build_journey_svg(states, dict(FIGURES, dbt="16 modelos"), mode)
        bands = re.findall(r'class="medallion-band medallion-(\w+)" x="([\d.]+)" y="[\d.]+" width="([\d.]+)"', svg)
        assert [key for key, _, _ in bands] == ["bronze", "silver", "gold"]
        spans = [(float(x), float(x) + float(width)) for _, x, width in bands]
        assert all(right < next_left for (_, right), (next_left, _) in zip(spans, spans[1:]))
        column = architecture.COLUMN_X
        for (left, right), columns in zip(spans, [["bronze"], ["staging", "intermediate"], ["marts", "gold"]]):
            assert all(left < column[name] < right for name in columns)
        for key, detail in [("BRONZE", "Parquet"), ("SILVER", "Transformación dbt"),
                            ("GOLD", "Marts → datos.duckdb")]:
            assert f">{key}</tspan>" in svg and f"· {detail}</tspan>" in svg
            assert architecture.tech_glossary.describe(key.lower()) in svg
        assert "dbt CORE · staging → intermedio → marts · 16 modelos" in svg
    vertical = architecture.build_vertical_journey_svg(states, FIGURES, charts.MODE_DARK)
    assert [key for key in re.findall(r'class="medallion-band medallion-(\w+)"', vertical)] == ["bronze", "silver", "gold"]


def test_d154_d155_the_delivered_stack_replaces_sqlite_except_in_the_landing_zone():
    """Bronze is Parquet, dbt transforms and tests, DuckDB serves; only the landing
    database raw.db is still SQLite, and the INE IPC is the second source."""
    states = make_states(control.RUN_OK)
    for build in [architecture.build_journey_svg, architecture.build_vertical_journey_svg]:
        svg = build(states, FIGURES, charts.MODE_DARK)
        # Visible text only: hover explanations may still name the SQLite backup.
        visible = re.sub(r"<title>[^<]*</title>", "", svg)
        assert visible.count("SQLite") == (visible.count("SQLite · raw.db")
                                           + visible.count("SQLite · tal cual"))
        assert "datos.db<" not in visible and "datos.db " not in visible
        for text in ["Staging", "Intermedio", "Marts y pruebas", "datos.duckdb", "INE · IPC"]:
            assert text in svg
    for slug in ["duckdb", "dbt", "apacheparquet"]:
        assert architecture.brand_icons.logo_body(slug) in architecture.build_journey_svg(
            states, FIGURES, charts.MODE_DARK)


def test_pipeline_names_the_real_technology_used_at_each_stage():
    svg = architecture.build_journey_svg(make_states(control.RUN_OK), FIGURES,
                                         charts.MODE_DARK, animate_flow=True)
    # Informe semanal and Consultas SQL now show their first line as technology
    # pills (D-103: GitHub CLI/Markdown, SQL); every other label is untouched
    # because its own pills added nothing beyond what the node already said.
    for label in ["HTTPS · CSV · sin API", "Python · requests", "SQLite · raw.db",
                  "Parquet · copia exacta", "dbt · tipos y textos", "dbt · modelos y pruebas",
                  "DuckDB · modelo estrella", "dbt build", "pytest · si fallan",
                  "GitHub Actions · Secrets", "Streamlit · historial",
                  "DuckDB · una fila por carga"]:
        assert label in svg
    # SQLite's own node draws the traditional database cylinder, not the brand
    # mark (D-103 follow-up): its title already spells out "SQLite" in words.
    for slug in ["python", "streamlit", "github", "duckdb", "dbt", "apacheparquet"]:
        assert architecture.brand_icons.logo_body(slug) in svg
    assert architecture.brand_icons.logo_body("sqlite") not in svg


def test_d103_stack_pills_name_the_real_tools_without_inventing_any():
    """Every id in PIPELINE_STACK is a real, declared dependency (D-103)."""
    root = Path(__file__).resolve().parent.parent
    requirements = ((root / "requirements.txt").read_text()
                    + (root / "requirements-pipeline.txt").read_text())
    declared = {line.split(">=")[0].split("==")[0].split("<")[0].strip().lower()
               for line in requirements.splitlines() if line.strip()}
    # These are pip packages that must be declared (dbt as dbt-core); "python" names
    # the interpreter itself and sqlite3/parquet/markdown-text/https/csv/sql/github-cli
    # are not pip packages, so they are not checked against the requirements.
    library_ids = {"pandas", "requests", "pyarrow", "duckdb", "dbt-core"}
    for tech_id in library_ids:
        assert tech_id in declared, f"{tech_id} is not in requirements.txt"
    for stack in architecture.PIPELINE_STACK.values():
        for tech_id in stack:
            assert tech_id in architecture.TECH, tech_id


def test_d103_a_node_gets_pills_only_for_tools_its_own_icon_does_not_already_show():
    # Agente ODEPA's icon is Python; the pill row should add "requests" but
    # not repeat "Python".
    stack = architecture.visible_stack("Agente ODEPA", architecture.draw_python_icon)
    assert stack == ["requests"]
    # The dbt models show dbt as their tile: the pills add SQL and DuckDB.
    assert architecture.visible_stack("Staging", architecture.draw_dbt_icon) == ["sql", "duckdb"]
    assert architecture.visible_stack("Parquet · bronce",
                                      architecture.draw_parquet_icon) == ["python", "pyarrow"]
    # SQLite · raw.db already spells "SQLite" out in its own title: no pill needed.
    assert architecture.visible_stack("SQLite · raw.db", architecture.draw_sqlite_icon) is None
    # Informe semanal's icon is GitHub; python and markdown are new information.
    stack = architecture.visible_stack("Informe semanal", architecture.draw_github_icon)
    assert stack == ["python", "markdown"]
    # A step outside PIPELINE_STACK gets no row at all.
    assert architecture.visible_stack("Rechazos", architecture.draw_warning_icon) is None


def test_d103_pills_render_as_local_logos_or_styled_text_never_a_broken_image():
    svg = architecture.build_journey_svg(make_states(control.RUN_OK), FIGURES,
                                         charts.MODE_DARK)
    assert ">requests<" in svg and ">pyarrow<" in svg and ">CSV<" in svg and ">HTTPS<" in svg
    assert ">Markdown<" in svg and ">SQL<" in svg and ">DuckDB<" in svg and ">dbt<" in svg
    # No <image>/CDN reference: logos are inlined <path> data from bi/assets/logos/.
    assert "<image" not in svg
    vertical = architecture.build_vertical_journey_svg(make_states(control.RUN_OK), FIGURES,
                                                        charts.MODE_DARK)
    assert ">pyarrow<" in vertical and ">requests<" in vertical


def test_figures_from_the_data_appear_under_their_steps():
    svg = architecture.build_journey_svg(make_states(control.RUN_OK), FIGURES,
                                         charts.MODE_LIGHT)
    for figure in FIGURES.values():
        assert figure in svg


def test_status_dots_follow_the_real_state_and_only_running_steps_pulse():
    states = make_states(control.RUN_OK)
    states["etl"] = control.RUN_IN_PROGRESS
    svg = architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK)
    # The ETL state is shown on the two dbt transformation steps: staging and intermediate.
    assert svg.count('class="journey-running"') == 2
    states["load"] = control.RUN_FAILED
    svg = architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK)
    assert architecture.STATE_COLORS[control.RUN_FAILED] in svg


def test_text_from_the_data_is_escaped():
    figures = dict(FIGURES, rows_read="<b>397.814</b>")
    svg = architecture.build_journey_svg(make_states(control.RUN_OK), figures,
                                         charts.MODE_DARK)
    assert "<b>397.814</b>" not in svg
    assert "&lt;b&gt;397.814&lt;/b&gt;" in svg


def test_d043_dots_travel_along_the_arrows_only_while_a_run_is_in_progress():
    idle_svg = architecture.build_journey_svg(make_states(control.RUN_OK), FIGURES,
                                              charts.MODE_DARK)
    assert "animateMotion" not in idle_svg
    running_states = dict(make_states(control.RUN_OK), workflow=control.RUN_IN_PROGRESS)
    running_svg = architecture.build_journey_svg(running_states, FIGURES, charts.MODE_DARK)
    assert "animateMotion" in running_svg


def test_only_real_states_get_a_dot_and_an_unknown_one_gets_none():
    states = dict(make_states(control.RUN_OK), report=architecture.STATE_UNKNOWN,
                  etl_run=control.RUN_FAILED)
    svg = architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK)
    grey = architecture.STATE_COLORS[architecture.STATE_UNKNOWN]
    # The grey of the column subtitles is text, not a dot: only circles count.
    assert f'r="7" fill="{grey}"' not in svg
    assert f'r="5" fill="{grey}"' not in svg
    # etl_run takes the state of the latest load.
    assert architecture.STATE_COLORS[control.RUN_FAILED] in svg
    # Items with no state to read (secrets, logs, mail) have no dot.
    item_without_state = architecture.build_band_item(0, 0, "Secretos", "clave",
                                                      charts.get_palette(charts.MODE_DARK))
    assert "<circle" not in item_without_state


def test_vertical_journey_has_every_step_figure_and_real_state():
    states = dict(make_states(control.RUN_OK), load=control.RUN_FAILED,
                  report=architecture.STATE_UNKNOWN)
    svg = architecture.build_vertical_journey_svg(states, FIGURES, charts.MODE_DARK)
    for text in ["FUENTES", "INGESTA", "ATERRIZAJE", "BRONZE", "STAGING", "INTERMEDIO",
                 "MARTS", "SERVING", "CONSUMO", "raw.db", "datos.duckdb", "INE · IPC", "Rechazos",
                 "GitHub Actions", "OBSERVABILIDAD", "Panel Streamlit", "Informe semanal",
                 "Consultas SQL"]:
        assert text in svg
    for figure in FIGURES.values():
        assert figure in svg
    assert architecture.STATE_COLORS[control.RUN_FAILED] in svg
    grey = architecture.STATE_COLORS[architecture.STATE_UNKNOWN]
    assert f'r="7" fill="{grey}"' not in svg


def test_vertical_journey_moves_its_dots_only_while_a_run_is_in_progress():
    idle_svg = architecture.build_vertical_journey_svg(make_states(control.RUN_OK), FIGURES,
                                                       charts.MODE_LIGHT)
    assert "animateMotion" not in idle_svg
    running_states = dict(make_states(control.RUN_OK), workflow=control.RUN_IN_PROGRESS)
    assert "animateMotion" in architecture.build_vertical_journey_svg(
        running_states, FIGURES, charts.MODE_LIGHT)


def test_every_piece_of_every_diagram_explains_itself_on_hover():
    """Each card, band item and link label carries a <title>: the browser shows it on
    hover. Acronyms are spelled out where they appear."""
    import re
    states = make_states(control.RUN_OK)
    for svg in [architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK),
                architecture.build_vertical_journey_svg(states, FIGURES, charts.MODE_DARK)]:
        titles = re.findall(r'font-weight="700" fill="[^"]+">([^<]+)</text>', svg)
        explained = set(re.findall(r"<title>([^<]+)</title>", svg))
        assert titles and len(explained) >= len(set(titles)) // 2
    journey = architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK)
    assert "ETL = extraer, transformar y cargar" in journey
    assert all(text in architecture.TOOLTIPS
               for text in ["Pruebas (CI)", "datos.duckdb", "raw.db", "INE · IPC"])


def test_explicit_flow_illustration_moves_without_changing_the_recorded_state():
    states = make_states(control.RUN_OK)
    for builder in [architecture.build_journey_svg, architecture.build_vertical_journey_svg]:
        still = builder(states, FIGURES, charts.MODE_DARK)
        animated = builder(states, FIGURES, charts.MODE_DARK, animate_flow=True)
        assert "animateMotion" not in still
        assert "animateMotion" in animated
        assert 'class="journey-running"' not in animated
        assert ".journey-flow { display: none; }" in animated
        assert set(states.values()) == {control.RUN_OK}


def test_flow_can_be_paused_without_changing_a_real_running_status():
    states = make_states(control.RUN_OK)
    states["workflow"] = control.RUN_IN_PROGRESS
    paused = architecture.build_journey_svg(states, FIGURES, charts.MODE_DARK, animate_flow=False)
    assert "animateMotion" not in paused
    assert 'class="journey-running"' in paused
    assert states["workflow"] == control.RUN_IN_PROGRESS


