"""D-523: «Reglas de transformación» says what the pipeline does to the data and why, in words anyone can check."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bi import charts, dashboard, queries, transformation_rules as rules

# region Variables
DASHBOARD_FILE = str(Path(__file__).resolve().parents[1] / "bi" / "dashboard.py")
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")
PALETTE = charts.get_palette(charts.MODE_DARK)
# endregion


# region Transformation rules
def by_title(title):
    return next(rule for rule in rules.read_rules() if rule["titulo"][0] == title)


def test_d523_every_rule_justifies_itself_in_both_languages():
    read = rules.read_rules()
    assert [rule["n"] for rule in read] == list(range(1, len(read) + 1))
    layers = {entry[0]: entry[1] for entry in rules.LAYERS}
    for rule in read:
        assert rule["capa"] in layers, rule["n"]
        for field in ("titulo", "problema", "sin_ella"):
            spanish, english = rule[field]
            assert spanish and english and spanish != english, (rule["n"], field)
    pipeline = [rule["n"] for rule in read if layers[rule["capa"]] == rules.PIPELINE_TAB]
    calculations = [rule["n"] for rule in read if layers[rule["capa"]] == rules.CALCULATIONS_TAB]
    assert pipeline == list(range(1, len(pipeline) + 1)) and calculations[0] == len(pipeline) + 1
    assert sorted(set(rule["capa"] for rule in read if layers[rule["capa"]] == rules.PIPELINE_TAB)) == sorted(
        ["ingesta", "staging", "intermedio", "marts", "publicacion"]
    )


def test_d523_every_reference_points_at_a_line_that_exists():
    for rule in rules.read_rules():
        assert rule["codigo"], rule["n"]
        for reference in rule["codigo"]:
            assert rules.locate(reference["archivo"], reference["ancla"]), (rule["n"], reference)


def test_d523_the_decisions_and_rules_it_cites_exist():
    decisions = (rules.ROOT / "docs" / "DECISIONES.md").read_text(encoding="utf-8")
    guide = (rules.ROOT / "docs" / "PROYECTO.md").read_text(encoding="utf-8")
    for rule in rules.read_rules():
        for code in rule["respaldo"]:
            assert (f"## {code} " in decisions) if code.startswith("D-") else (f"| {code} |" in guide), (
                rule["n"],
                code,
            )


def test_d523_the_three_inferences_are_marked_and_nothing_else():
    inferred = {rule["n"]: rule["inferencia"][0] for rule in rules.read_rules() if rule.get("inferencia")}
    assert len(inferred) == 3
    text = " ".join(inferred.values())
    for reading in ("$/kilo (en caja de 17 kilos)", "$/docena de atados (3 kilos)", "$/cien en rama"):
        assert reading in text
    assert all("ODEPA no lo declara" in sentence for sentence in inferred.values())
    assert "1.357" in text  # what it would change if the reading were the other one


def test_d523_it_says_that_a_price_that_only_changed_package_leaves_the_comparison():
    rule = by_title("Compara cada semana solo en el mismo envase")
    assert "Los precios que solo cambiaron de envase quedan fuera de la comparación" in rule["ejemplo"][0]
    assert "Prices that only changed package are left out of the comparison" in rule["ejemplo"][1]
    assert "kiwi" in rule["ejemplo"][0].lower() and "Maule" in rule["ejemplo"][0]
    assert "quedan fuera de la comparación" in rules.TEXTS["same_package_note"][0]
    assert "betarraga" in by_title("No inventa un precio cuando no hay lectura segura")["ejemplo"][0].lower()


def test_d523_every_calculation_says_whether_it_uses_the_same_package_rule_and_why_not():
    read = rules.read_rules()
    calculations = [rule for rule in read if rule["capa"] in ("sql", "panel")]
    assert all(isinstance(rule.get("usa_mismo_envase"), bool) for rule in calculations)
    assert all(rule.get("por_que_no") for rule in calculations if rule["usa_mismo_envase"] is False)
    assert not any(rule.get("por_que_no") for rule in calculations if rule["usa_mismo_envase"])
    # what the author approved leaving out, and what he named as using it
    for title in (
        "K1: margen entre mayorista y consumidor",
        "K2: brecha entre canales",
        "K4: cada semana frente al promedio de su año",
    ):
        assert by_title(title)["usa_mismo_envase"] is False
    assert by_title("Calcula el índice por familia y de toda la canasta")["usa_mismo_envase"] is False
    for title in (
        "Decide qué es una alerta",
        "Arma la tabla de productos del paso 4",
        "Resume cada familia con su mediana",
        "Pinta cada región en el mapa",
        "Arma el Excel y el CSV de «Descargar»",
    ):
        assert by_title(title)["usa_mismo_envase"] is True


def test_d523_only_the_author_gets_links_to_the_repository():
    assert "github.com" not in rules.build_page_html(PALETTE, "es", author=False)
    author = rules.build_page_html(PALETTE, "es", author=True)
    assert re.search(r"github\.com/[^\"]+/blob/main/etl/etl\.py#L\d+", author)
    reference = {"archivo": "etl/etl.py", "ancla": "def load_raw_files"}
    assert (
        rules.code_reference(reference, False)["text"]
        == f'etl/etl.py:{rules.locate("etl/etl.py", "def load_raw_files")}'
    )
    assert "href" not in rules.code_reference(reference, False)


def test_d523_the_english_page_reads_in_english():
    accents = re.compile(r"[áéíóúñ¿¡]")
    for rule in rules.build_rules_data("en", False):
        for field in ("title", "problem", "without", "example", "inference", "whyNot"):
            text = rule[field] or ""
            text = re.sub(r"«[^»]*»|`[^`]*`", "", text).replace("La Araucanía", "")
            assert not accents.search(text), (rule["n"], field, text)
    for pair in rules.TEXTS.values():
        assert pair[0] != pair[1] or pair[0].isascii()
    page = rules.build_page_html(PALETTE, "en", False)
    assert "Calculations and indicators" in page and "Cálculos e indicadores" not in page


@pytest.mark.parametrize("tab", [rules.PIPELINE_TAB, rules.CALCULATIONS_TAB])
def test_d523_the_diagram_shows_where_each_rule_acts_with_straight_arrows(tab):
    data = rules.build_rules_data("es", False)
    svg = rules.build_diagram(tab, data, "es")
    mine = [rule["n"] for rule in data if rule["tab"] == tab]
    assert sorted(int(n) for n in re.findall(r'data-rule="(\d+)"', svg)) == mine
    arrows = re.findall(r'<path class="arrow" d="([^"]+)"', svg)
    assert arrows and all(
        re.fullmatch(r"M[\d.]+ [\d.]+ H[\d.]+", arrow) for arrow in arrows
    )  # a straight line, never a curve
    assert f"rule-head-{tab}" in svg  # its own marker: the other drawing is hidden and would take it with it
    for entry in rules.LAYERS:
        if entry[1] == tab:
            assert f'data-layer="{entry[0]}"' in svg
    # nothing leaves the drawing, and two neighbours never share a dot
    for entry in rules.LAYERS:
        if entry[1] == tab:
            count = sum(1 for rule in data if rule["layer"] == entry[0])
            half = min(count, entry[6]) / 2 * rules.PITCH
            assert half + rules.DOT <= entry[5] <= rules.WIDTH - half - rules.DOT


@needs_database
def test_d523_the_page_opens_for_the_professional_beside_the_pipeline_and_folds_the_menu():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PROFESSIONAL
    app.query_params[dashboard.VIEW_PARAMETER] = dashboard.PAGE_RULES
    app.run()
    assert not app.exception
    frames = [str(element.proto.srcdoc) for element in app.get("iframe")]
    assert any("Reglas del pipeline" in frame and "github.com" not in frame for frame in frames)
    assert dashboard.PAGE_RULES in dashboard.FOLD_MENU_VIEWS
    section = next(views for key, _, views in dashboard.MENU_BLOCKS if key == "ingenieria")
    assert section[:2] == [dashboard.PAGE_DIAGRAMS, dashboard.PAGE_RULES]


@needs_database
def test_d523_the_user_view_does_not_reach_it():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PUBLIC
    app.query_params[dashboard.VIEW_PARAMETER] = dashboard.PAGE_RULES
    app.run()
    assert not app.exception
    assert not any("Reglas del pipeline" in str(element.proto.srcdoc) for element in app.get("iframe"))


# endregion
