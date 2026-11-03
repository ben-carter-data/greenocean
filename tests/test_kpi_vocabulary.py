"""One definition of the price alert (K6) everywhere, and the K code next to each business KPI (D-385)."""

import re

from bi import alerts, dashboard, i18n, overview, project


def test_d385_the_alert_rule_is_written_once_from_the_constants_of_the_code():
    rule = alerts.describe_rule()
    for value in (
        f"± {alerts.ALERT_DEVIATIONS} desviaciones",
        f"{alerts.ALERT_WINDOW_WEEKS} semanas previas",
        f"{round(alerts.ALERT_MINIMUM_CHANGE * 100)} %",
        f"{alerts.QUOTE_WORDS[alerts.ALERT_MINIMUM_QUOTES]} cotizaciones",
    ):
        assert value in rule, value
    assert dict((name, how) for name, how, _ in overview.KPIS)["Alerta de precio"] == rule
    # The documents and the two working sources say the same, with the same numbers.
    words = rule.removeprefix("Un cambio fuera del ").rstrip(".")
    prd = i18n.document_path("PRD.md", "es").read_text(encoding="utf-8")
    assert words in next(line for line in prd.splitlines() if line.startswith("| RF-05 |"))
    guide = {row["KPI"]: row for row in project.read_guide_table("KPI")}
    assert words in guide["K6"]["En palabras"]
    design = {row["ID"]: row for row in project.read_design_table(project.INDICATORS_HEADING)}
    assert words in design["K6"]["Fórmula"]
    english = i18n.document_path("PRD.md", "en").read_text(encoding="utf-8")
    assert "± 2 deviations of its previous 12 weeks, of at least 10 % and with two quotes in each week" in english
    assert i18n.lookup(rule)  # and the panel says it in English too


def test_d385_each_business_kpi_names_its_technical_indicator_or_says_it_has_none():
    names = [name for name, _, _ in overview.KPIS]
    assert set(overview.KPI_CODES) <= set(names)
    assert set(overview.KPI_CODES.values()) <= set(dashboard.KPI_PRESENTATION)
    for name in names:
        cell = dashboard.build_kpi_code_html(name)
        code = overview.KPI_CODES.get(name)
        if code:
            assert f"{code} · {dashboard.KPI_PRESENTATION[code][0]}" in cell and re.search(rf"kpi={code}\b", cell), name
        else:
            assert cell == "—", name


def test_d479_the_alert_chips_say_their_rule_in_the_words_of_each_view():
    change, window = round(alerts.ALERT_MINIMUM_CHANGE * 100), alerts.ALERT_WINDOW_WEEKS
    for rise in (True, False):
        plain, formula = alerts.describe_kind(rise, False), alerts.describe_kind(rise, True)
        assert f"al menos {change} % frente a la semana anterior" in plain
        assert f"cambio promedio de sus {window} semanas previas" in plain and "(desviación estándar)" in plain
        assert f"{alerts.ALERT_DEVIATIONS} desviaciones estándar" in formula and f"{window} semanas previas" in formula
        assert i18n.lookup(plain) and i18n.lookup(formula)
    assert "Una oportunidad de compra." in alerts.describe_kind(False, False)
    # Each level says its threshold on hover of «Nivel» (D-492), taken from the same table that colours the rows.
    plain, formula = dashboard.level_guide_text(False, False), dashboard.level_guide_text(False, True)
    for floor, label, _, _ in dashboard.DROP_LEVELS:
        assert label in plain
        assert (f"{label}: {floor}× o más" if floor else f"{label}: más de {alerts.ALERT_DEVIATIONS}×") in plain
        assert (f"{label}: {floor} σ o más" if floor else f"{label}: más de {alerts.ALERT_DEVIATIONS} σ") in formula
    assert "desviación estándar" in plain and "desviación estándar" in formula


def test_d482_the_alert_window_shows_the_two_published_prices_of_its_change():
    rows = dashboard.read_price_alerts()
    week = rows[rows["week_start"] == rows["week_start"].max()]
    for row in week.to_dict("records"):
        before, now = dashboard.alert_prices(row)
        # «Anterior» and «Actual» are the prices the change is computed from, never one worked back from the other
        assert (row["same_region_previous_price"], row["same_region_price"]) == (before, now)
        assert abs(now / before - 1 - row["variation"]) < 1e-9
