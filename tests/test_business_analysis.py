"""«Análisis de negocio y sistemas» (D-377): the BA and BSA work told as a case, read from the PRD, the SQAP and the
decisions in both languages; the KPI definitions live here, not in Insights."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import business_analysis as ba
from bi import charts, dashboard, doc_figures, i18n, overview, queries

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = str(Path(dashboard.__file__))
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")


def test_d377_the_case_has_ten_blocks_in_reading_order_each_with_its_english():
    assert ba.BLOCKS == [
        "El problema",
        "Interesados",
        "Qué escuchamos",
        "Requisitos",
        "Alcance",
        "Proceso",
        "KPIs",
        "Decisiones de sistema",
        "Evaluación",
        "Del feedback al cambio",
    ]
    for title in ba.BLOCKS + [title for title, *_ in ba.SYSTEM_DECISIONS]:
        assert i18n.EN[title], title


def test_d377_every_block_is_read_from_the_documents_in_both_languages():
    for language in ("es", "en"):
        problem = ba.read_problem(language)
        assert len(problem) == 2 and "ODEPA" in problem[0] and "**" not in problem[0]
        requirements = ba.read_requirements(language)
        assert [row[0] for row in requirements] == [f"RF-0{number}" for number in range(1, 10)]
        assert all(row[1] and row[2] for row in requirements)  # each with its measurable criterion
        scope = ba.read_scope(language)
        assert len(scope) == 5 and all(len(row) == 4 and all(row) for row in scope)  # includes, why, excludes, why
        assert all(len(row) == 2 and all(row) for row in ba.read_acceptance(language))
        assert ba.read_evaluation(language).startswith(("Lo miden pruebas automáticas", "Automated tests measure it"))
    assert ba.read_scope("es")[2][3].startswith("El panel describe lo que pasó con los precios")  # the author's reason


def test_d377_what_we_heard_claims_two_reviews_and_nothing_more():
    assert ba.read_heard("es") == (
        "Usuarios reales hicieron dos revisiones: una de uso y una de arquitectura. "
        "Cada cambio que salió de ellas tiene su decisión."
    )
    rows = ba.read_feedback("es")
    assert [row[0] for row in rows] == ["Revisión de uso", "Revisión de arquitectura"]
    assert rows[0][3] == "D-352, D-372" and rows[1][1] == "Por un usuario real, sin cambios solicitados"
    assert rows[1][2] == "—" and rows[1][3] == "—"  # no change and no decision are tied to it
    assert [row[3] for row in ba.read_feedback("en")] == [row[3] for row in rows]
    decisions = i18n.document_path("DECISIONES.md", "es").read_text(encoding="utf-8")
    assert "## D-352 ·" in decisions and "## D-372 ·" in decisions


def test_d377_each_system_decision_is_one_line_of_the_sqap_with_a_page():
    for language in ("es", "en"):
        plan = ba.plain(i18n.document_path("PLAN_DE_CALIDAD.md", language).read_text(encoding="utf-8"))
        lines = ba.system_decisions(language)
        assert [item["title"] for item in lines] == [title for title, *_ in ba.SYSTEM_DECISIONS]
        for item in lines:
            assert item["parts"] and all(part in plan for part in item["parts"]), item["title"]  # read, never rewritten
            assert item["line"] == " ".join(item["parts"]) and item["page"] in dashboard.SYSTEM_DECISION_PAGES
        measured = lines[0]["parts"]  # «qué medimos y qué no»: section 3, then the first thing that is not measured
        assert len(measured) == 2 and measured[1].startswith(("Tiempo de respuesta", "Response time"))
        assert lines[0]["labels"] == [None, "No medimos"] and i18n.EN["No medimos"] == "We do not measure"
    assert "aviso urgente" in ba.system_decisions("es")[-1]["line"]
    assert ba.system_decisions("en")[-1]["line"].endswith("urgent alert.")
    assert ba.system_decisions("es")[3]["line"].startswith("Se publica hasta la última semana completa")


def test_d377_the_weekly_cycle_figure_names_the_five_stages():
    assert "ciclo_semanal" in doc_figures.FIGURES
    svg = doc_figures.FIGURES["ciclo_semanal"](charts.THEMES[0])
    for word in ("Carga", "Pruebas", "Publicación", "Informe semanal", "Informe de calidad", "la semana siguiente"):
        assert word in svg, word


def test_d377_the_kpi_definitions_left_insights_for_the_analysis_page():
    source = Path(dashboard.__file__).read_text(encoding="utf-8")
    assert '["Preguntas", "KPIs"]' not in source and "OVERVIEW_INSIGHT_VIEW" not in source
    assert source.count("overview.KPIS") == 1
    before = source[: source.index("overview.KPIS")]
    assert before[before.rindex("\ndef ") : before.rindex("\ndef ") + 30].startswith("\ndef show_analysis_block")


@needs_database
def test_d456_the_method_tab_draws_the_kpis_and_the_system_decisions_and_insights_links_to_it():
    """The old page «Análisis de negocio y sistemas» is the tab «Método» of «Análisis BA y BI»: only what the PRD does
    not hold, the KPIs and the system decisions; its address opens that tab, and so does the link from Insights."""
    for profile in ("consulta", "profesional"):
        app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
        app.session_state["visitor_profile"] = profile
        app.query_params.update({"vista": dashboard.PAGE_ANALYSIS, "lang": "es"})
        app.run()
        assert not app.exception, profile
        assert app.session_state[dashboard.BA_TAB_KEY] == "Método"
        markup = " ".join(block.value for block in app.markdown)
        assert overview.KPIS[0][0] in markup and "Qué medimos y qué no, y por qué" in markup
        assert "analysis_block" not in app.session_state  # no list of ten blocks any more
    insights = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    insights.session_state["visitor_profile"] = "consulta"
    insights.query_params.update({"vista": dashboard.PAGE_INSIGHTS, "lang": "es"})
    insights.run()
    assert not insights.exception and insights.session_state[dashboard.BA_TAB_KEY] == "Insights"
    link = next(
        link for link in insights.main.get("page_link") if link.proto.label == "Ver las definiciones de los KPI"
    )
    assert "pestana=M%C3%A9todo" in link.proto.query_string


@needs_database
def test_d456_the_method_tab_reads_in_english():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.query_params.update({"vista": dashboard.PAGE_BA, "pestana": "Método", "lang": "en"})
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert "What we measure and what we do not, and why" in markup  # read from docs/en/PLAN_DE_CALIDAD.md


def test_d455_the_problem_block_reads_whole_sentences_and_never_points_at_itself():
    # «El problema» is read from PRD 2: a sentence that leads to a diagram («…:») would hang on the page, and the page
    # must not send the reader to itself.
    for language, page in (("es", "Análisis de negocio y sistemas"), ("en", "Business and systems analysis")):
        problem = ba.read_problem(language)
        assert problem and all(paragraph.endswith(".") for paragraph in problem), problem
        assert not any(page in paragraph for paragraph in problem)
