"""«Análisis BA y BI» · «Mensual» and «Histórico» (D-456, D-457): every figure is recomputed from the database, the
ones the page shares with «Precios e inflación» are the same numbers, and every sentence a chart says on hover holds
the figures it explains."""

import math
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from bi import alerts, ba_trends, charts, dashboard, inflation_view, overview, queries, weeks

needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")
IPC = inflation_view.IPC_NAME


@pytest.fixture(scope="module")
def history():
    rows, last = inflation_view.build_family_index(
        queries.run_sql(inflation_view.SERIES_SQL),
        queries.run_sql("SELECT year, month, food_index FROM ipc_monthly"),
        basket=True,
    )
    margins = ba_trends.add_month_key(queries.run_query("k1_margin"))
    seasonal = ba_trends.add_month_key(queries.run_query("k4_seasonal_index"))
    found = ba_trends.add_month_key(alerts.find_price_alerts(queries.run_query("k6_national_weekly_price")))
    return rows, last, margins, seasonal, found


def label(pair):
    """A month as the panel writes it in Spanish, written here by hand: «sep 2026»."""
    return f"{weeks.MONTHS[pair[1] - 1]} {pair[0]}"


def test_d457_monthly_has_the_periods_and_historico_the_whole_history():
    last = (2026, 9)
    assert ba_trends.periods(last) == ["Últimos 12 meses", "2026", "2025", "2024", "2023", "2022"]
    assert ba_trends.bounds("Últimos 12 meses", last) == ((2025, 9), (2026, 9))
    assert ba_trends.bounds("2026", last) == ((2025, 12), (2026, 9))  # the year so far, from the December before
    assert ba_trends.bounds("2025", last) == ((2024, 12), (2025, 12))
    assert ba_trends.bounds("2022", last) == ((2022, 1), (2022, 12))  # no index before January 2022
    # a change is measured from the start month; the weeks counted are those of the months after it
    assert ba_trends.counted_months((2025, 9), (2026, 9)) == (202510, 202609)
    assert ba_trends.counted_months((2022, 1), (2026, 9)) == (202201, 202609)
    # each chart says its months, and each card the two months it compares
    assert ba_trends.span((2025, 10), (2026, 9)) == "oct 2025 – sep 2026"
    assert ba_trends.compared((2025, 9), (2026, 9)) == "sep 2025 → sep 2026"
    assert [ba_trends.year_note(year, last) for year in (2022, 2023, 2026)] == ["desde ene", "", "hasta sep"]
    assert ba_trends.year_note(2026, (2026, 12)) == ""


def test_d457_a_month_without_an_index_stays_a_gap():
    months = [(2025, month) for month in range(9, 13)] + [(2026, month) for month in range(1, 4)]
    rows = pd.DataFrame(
        [(family, year, month, 100 + index) for index, (year, month) in enumerate(months) for family in ("Pan", IPC)],
        columns=["product_group", "year", "month", "index"],
    )
    rows = rows[~((rows["product_group"] == "Pan") & (rows["year"] == 2025) & (rows["month"] == 11))]
    changes = ba_trends.monthly_changes(rows, "Pan", (2025, 9), (2026, 3)).set_index(["year", "month"])
    assert list(changes.index) == months[1:]  # the months after the start
    assert math.isnan(changes.loc[(2025, 11), "change"]) and math.isnan(changes.loc[(2025, 12), "change"])
    assert changes.loc[(2025, 10), "change"] == pytest.approx((101 / 100 - 1) * 100)
    assert changes.loc[(2025, 11), "ipc"] == pytest.approx((102 / 101 - 1) * 100)  # the IPC has the month


@needs_database
def test_d457_the_months_chain_to_the_change_of_their_period_and_the_years_to_the_change_since_2022(history):
    rows, last, margins, seasonal, found = history
    for family in [ba_trends.BASKET] + ba_trends.families(rows):
        for period in ba_trends.periods(last):
            start, end = ba_trends.bounds(period, last)
            figures = ba_trends.monthly(rows, margins, seasonal, found, family, start, end)
            months = ba_trends.monthly_changes(rows, family, start, end)
            assert len(months) == (end[0] - start[0]) * 12 + end[1] - start[1], (family, period)
            if months["change"].notna().all():
                chained = ((months["change"] / 100 + 1).prod() - 1) * 100
                assert chained == pytest.approx(figures["change"]), (family, period)
                assert ((months["ipc"] / 100 + 1).prod() - 1) * 100 == pytest.approx(figures["ipc"])
            if figures["top"]:
                top = months.loc[months["change"].idxmax()]
                assert figures["top"][:2] == (top["year"], top["month"])
                assert figures["rising"] == int((months["change"] > 0).sum())
        whole = ba_trends.history(rows, margins, seasonal, found, family, last)
        years = whole["years"]
        assert list(years["year"]) == [str(year) for year in range(2022, last[0] + 1)], family
        assert ((years["change"] / 100 + 1).prod() - 1) * 100 == pytest.approx(whole["change"]), family
        for year, change, ipc in zip(years["year"], years["change"], years["ipc"]):
            start = (2022, 1) if year == "2022" else (int(year) - 1, 12)
            end = (int(year), 12) if int(year) < last[0] else last
            assert change == pytest.approx(inflation_view.change(rows, family, start, end)), (family, year)
            assert ipc == pytest.approx(inflation_view.change(rows, IPC, start, end))
        assert whole["above"] == [year for year, gap in zip(years["year"], years["change"] - years["ipc"]) if gap > 2]
        assert whole["best"][0] == years.loc[years["change"].idxmax(), "year"]


@needs_database
def test_d456_the_figures_are_those_of_prices_and_inflation_and_recompute_from_the_queries(history):
    rows, last, margins, seasonal, found = history
    summary, ipc_total, ipc_year = inflation_view.summarize_families(
        rows[rows["product_group"] != inflation_view.BASKET_NAME], last
    )
    start, end = ba_trends.bounds(ba_trends.LAST_YEAR, last)
    for family in summary["family"]:
        figures = ba_trends.summarize(rows, margins, seasonal, found, family, start, end)
        expected = summary.set_index("family").loc[family, "yearly"]
        assert figures["change"] == pytest.approx(expected), family  # the 12 months of «Precios e inflación»
        assert figures["ipc"] == pytest.approx(ipc_year)
        assert figures["gap"] == pytest.approx(figures["change"] - ipc_year)
        whole = ba_trends.history(rows, margins, seasonal, found, family, last)
        assert whole["change"] == pytest.approx(summary.set_index("family").loc[family, "total"]), family
        assert whole["ipc"] == pytest.approx(ipc_total)
    # K1, K6 and K4 recomputed by hand for the whole basket in the last 12 months
    months = ba_trends.counted_months(start, end)
    stamp = pd.to_datetime(margins["week_start"])
    key = stamp.dt.year * 100 + stamp.dt.month
    chosen = margins[key.between(*months)]
    figures = ba_trends.summarize(rows, margins, seasonal, found, ba_trends.BASKET, start, end)
    assert figures["margin"] == pytest.approx(chosen["margin"].median() * 100) and figures["pairs"] == len(chosen)
    alert_key = pd.to_datetime(found["week_start"]).dt.year * 100 + pd.to_datetime(found["week_start"]).dt.month
    picked = found[alert_key.between(*months)]
    assert figures["alerts"] == len(picked) == figures["rises"] + figures["falls"]
    season_key = pd.to_datetime(seasonal["week_start"])
    in_period = seasonal[(season_key.dt.year * 100 + season_key.dt.month).between(*months)]
    by_month = in_period.groupby(pd.to_datetime(in_period["week_start"]).dt.month)["seasonal_index"].median()
    assert figures["cheapest"][0] == int(by_month.idxmin()) and figures["dearest"][0] == int(by_month.idxmax())
    assert figures["cheapest"][1] == pytest.approx((by_month.min() - 1) * 100)
    # K1 exists only where ODEPA has a wholesale price
    assert ba_trends.wholesale_families(margins) == sorted(set(margins["product_group"]))


@needs_database
def test_d457_each_chart_says_its_months_and_its_hover_holds_the_figures_it_explains(history):
    rows, last, margins, seasonal, found = history
    start, end = ba_trends.bounds(ba_trends.LAST_YEAR, last)
    figures = ba_trends.monthly(rows, margins, seasonal, found, ba_trends.BASKET, start, end)
    (_, price_note, _, price, _), (_, month_note, _, moves, _), (_, alert_note, _, outliers, _) = (
        ba_trends.monthly_tiles(rows, figures, start, end, "Vantablack")
    )
    first = (start[0] + 1, 1) if start[1] == 12 else (start[0], start[1] + 1)
    assert price_note == f"{label(start)} – {label(end)} · base {label(start)} = 100"
    assert month_note == f"{label(first)} – {label(end)} · frente al mes anterior"
    assert alert_note == f"{label(first)} – {label(end)} · subidas y bajadas (K6)"
    assert price.startswith(
        f"De {label(start)} a {label(end)} cambió {charts.format_signed_percent(figures['change'])}"
    )
    assert f"({charts.format_signed_percent(figures['ipc'])})" in price and figures["verdict"] in price
    top = figures["top"]
    assert f"Subió en {figures['rising']} de {len(figures['months'])} meses" in moves
    assert f"{label(top[:2])} ({charts.format_signed_percent(top[2])})" in moves
    per_month = figures["alert_rows"].groupby("month_key").size()
    busiest = int(per_month.idxmax())
    assert outliers.startswith(f"{charts.format_thousands(figures['alerts'])} alertas")
    assert f"{label((busiest // 100, busiest % 100))}, con {charts.format_thousands(per_month.max())}" in outliers
    # «Histórico»: from January 2022, the change of each year and the season
    whole = ba_trends.history(rows, margins, seasonal, found, ba_trends.BASKET, last)
    (_, since_note, _, since, _), (_, year_note, _, yearly, _), (_, season_note, _, season, _) = (
        ba_trends.history_tiles(rows, whole, last, "Vantablack")
    )
    assert since_note == f"ene 2022 – {label(last)} · base ene 2022 = 100"
    assert year_note == f"2022–{last[0]} · de diciembre a diciembre" and season_note.startswith(f"2022–{last[0]} · ")
    assert since.startswith(f"De ene 2022 a {label(last)} cambió {charts.format_signed_percent(whole['change'])}")
    assert f"El año que más subió fue {whole['best'][0]} ({charts.format_signed_percent(whole['best'][1])}" in yearly
    assert f"en {len(whole['above'])} de {len(whole['years'])} años" in yearly or not whole["above"]
    cheapest = ba_trends.full_month(whole["cheapest"][0])
    assert season.startswith(
        f"{cheapest} suele ser el mes más barato ({charts.format_signed_percent(whole['cheapest'][1])}"
    )
    # the first alert of the history can only come after 12 weeks: the year 2022 says so
    start, end = ba_trends.bounds("2022", last)
    first_year = ba_trends.monthly(rows, margins, seasonal, found, ba_trends.BASKET, start, end)
    alerts_measure = ba_trends.monthly_tiles(rows, first_year, start, end, "Vantablack")[2][2]
    assert "La primera alerta posible es de abril 2022" in alerts_measure
    assert pd.to_datetime(found["week_start"]).min() >= pd.Timestamp("2022-04-01")


def test_d457_every_card_and_column_explains_itself_on_hover_with_the_definitions_of_metodo():
    figures = {
        "family": ba_trends.BASKET, "change": 6.1, "ipc": 3.9, "gap": 2.2, "verdict": "más que la inflación",
        "margin": 78.9, "pairs": 31354, "alerts": 916, "rises": 635, "falls": 281, "cheapest": (2, -3.6),
        "dearest": (11, 2.5), "top": (2026, 7, 3.9), "low": (2025, 10, -1.9), "best": ("2022", 16.4, "desde ene"),
    }  # fmt: skip
    definitions = {name: how for name, how, _ in overview.KPIS}
    monthly = ba_trends.monthly_cards(figures, (2025, 9), (2026, 9), ["Frutas", "Hortalizas"])
    whole = ba_trends.history_cards(figures, (2026, 9))
    for cards in (monthly, whole):
        assert cards.count('class="ba-card" tabindex="0" title="') == 5
        for text in ("K6: " + alerts.describe_rule(), definitions["Alza frente al IPC"]):
            assert text in cards, text
    assert "K1: " + definitions["Brecha consumidor–mayorista"] in monthly
    assert "Solo Frutas y Hortalizas tienen precio mayorista" in monthly
    assert "sep 2025 → sep 2026" in monthly and "ene 2022 → sep 2026" in whole
    assert ">jul 2026<" in monthly and ">2022<" in whole and ">Febrero<" in whole
    for table in (
        ba_trends.monthly_table([dict(figures, months=None)], ba_trends.BASKET),
        ba_trends.history_table([figures], ba_trends.BASKET),
    ):
        assert table.count("<th title=") == 5 and 'class="ba-chosen"' in table


def test_d456_every_time_chart_starts_at_the_start_of_its_period():
    # The first alert can only come 12 weeks into the history (K6), so the alerts chart used to start its axis in
    # 2023 although 2022 had alerts; the axis is now the whole period, also its months without an alert.
    assert [day.to_dict() for day in ba_trends.month_domain((2022, 1), (2026, 9))] == [
        {"year": 2022, "month": 1, "date": 1},
        {"year": 2026, "month": 9, "date": 1},
    ]  # local time, like the data: a text date is midnight UTC, the day before in Chile (D-457)
    assert ba_trends.months_between((2025, 11), (2026, 2)) == [(2025, 11), (2025, 12), (2026, 1), (2026, 2)]
    frame = pd.DataFrame({"week_start": ["2022-04-04"], "variation": [0.2]})
    spec = ba_trends.alerts_chart(frame, (2022, 1), (2022, 12), "Vantablack").to_dict()
    assert spec["encoding"]["x"]["scale"]["domain"] == [f"{month} 2022" for month in weeks.MONTHS]
    last_year = ba_trends.alerts_chart(frame.iloc[:0], (2025, 9), (2026, 9), "Vantablack").to_dict()
    assert (
        last_year["encoding"]["x"]["scale"]["domain"][0] == "oct 2025"
        and len(last_year["encoding"]["x"]["scale"]["domain"]) == 12
    )


def test_d457_every_month_of_a_period_has_its_point_and_its_label():
    # «Precio mes a mes» had a point per month but named one month in three (Vega leaves out labels that would
    # touch), so it was not clear which months it drew: each month now has its dot and its label, with its year.
    months = ba_trends.months_between((2025, 9), (2026, 9))
    rows = pd.DataFrame(
        [(family, year, month, 100.0 + index) for index, (year, month) in enumerate(months) for family in ("Pan", IPC)],
        columns=["product_group", "year", "month", "index"],
    )
    rows["month_start"] = pd.to_datetime(dict(year=rows["year"], month=rows["month"], day=1))
    spec = ba_trends.trend_chart(rows, "Pan", (2025, 9), (2026, 9), "Vantablack").to_dict()
    axis = spec["encoding"]["x"]["axis"]
    assert axis["tickCount"] == {"interval": "month", "step": 1} and axis["format"] == "%b %Y"
    assert axis["labelOverlap"] is False and spec["mark"]["point"]["filled"] is True
    whole = ba_trends.trend_chart(rows, "Pan", (2022, 1), (2026, 9), "Vantablack").to_dict()
    assert whole["encoding"]["x"]["axis"]["format"] == "%Y" and "point" not in whole["mark"]  # «Histórico»: years
    bars = ba_trends.months_chart(ba_trends.monthly_changes(rows, "Pan", (2025, 9), (2026, 9)), "Vantablack").to_dict()
    assert bars["layer"][0]["encoding"]["x"]["axis"]["labelOverlap"] is False  # every month of the change, too


def test_d456_the_season_says_which_years_each_calendar_month_gathers():
    # A bar of «Temporada» is a month of the calendar, not of one year: with several years it gathers that month of
    # each of them, and each bar says its years on hover.
    weeks_found = pd.DataFrame(
        {
            "week_start": ["2024-02-05", "2025-02-03", "2025-03-03", "2026-02-02"],
            "seasonal_index": [0.97, 0.95, 1.02, 0.99],
        }
    )
    profile = ba_trends.season(weeks_found).set_index("month")
    assert profile.loc[2, "years"] == "2024–2026" and profile.loc[3, "years"] == "2025"
    assert profile.loc[2, "change"] == pytest.approx((0.97 - 1) * 100) and profile.loc[2, "weeks"] == 3
    spec = ba_trends.season_chart(ba_trends.season(weeks_found), "Vantablack").to_dict()
    assert any(item.get("field") == "years" for item in spec["encoding"]["tooltip"])


def test_d457_a_chart_grows_on_hover_never_past_the_page():
    css = ba_trends.build_css(charts.get_palette("Vantablack"))
    assert '[class*="st-key-ba_tile_"]:hover [class*="st-key-ba_zoom_"]' in css and "visibility:visible" in css
    assert f"width:min({ba_trends.ZOOM_WIDTH + 70}px, 72vw)" in css  # never wider than the page
    assert ".st-key-ba_zoom_0 { left:-10px; }" in css and ".st-key-ba_zoom_2 { right:-10px; }" in css
    words = ba_trends.zoom_text("lo que mide", "lo que se deduce")
    assert "<b>Qué mide</b> lo que mide" in words and "<b>Qué se deduce</b> lo que se deduce" in words


@needs_database
@pytest.mark.parametrize("tab", [dashboard.BA_MONTHLY_TAB, dashboard.BA_HISTORY_TAB])
def test_d457_each_tab_draws_three_charts_each_with_its_enlarged_twin(tab):
    app = AppTest.from_file(str(Path(dashboard.__file__)), default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.session_state[dashboard.BA_TAB_KEY] = tab
    app.query_params.update({"vista": dashboard.PAGE_BA})
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    assert markup.count('class="ba-chart-title"') == 6 and markup.count("<b>Qué mide</b>") == 3
    assert len(app.get("arrow_vega_lite_chart") + app.get("vega_lite_chart")) == 6
    assert [box.key for box in app.selectbox if box.key in ("ba_period", "ba_family")] == (
        ["ba_period", "ba_family"] if tab == dashboard.BA_MONTHLY_TAB else ["ba_family"]
    )


@needs_database
def test_d457_the_old_address_of_tendencias_opens_mensual():
    app = AppTest.from_file(str(Path(dashboard.__file__)), default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.query_params.update({"vista": dashboard.PAGE_BA, dashboard.BA_TAB_PARAMETER: "Tendencias"})
    app.run()
    assert not app.exception and app.session_state[dashboard.BA_TAB_KEY] == dashboard.BA_MONTHLY_TAB


def test_d458_the_green_panel_says_from_which_month_to_which_and_why_for_each_period():
    last = (2026, 9)
    lead, detail = ba_trends.monthly_context("Últimos 12 meses", last)
    assert lead == "Estás viendo los últimos 12 meses: de oct 2025 a sep 2026."
    assert "Termina en sep 2026: es el último mes con la inflación del INE" in detail and "sep 2025 = 100" in detail
    lead, detail = ba_trends.monthly_context("2026", last)  # the year so far: it ends in the last month of the INE
    assert lead == "Estás viendo 2026: de ene 2026 a sep 2026."
    assert "Termina en sep 2026" in detail and "dic 2025 = 100, el cierre del año anterior" in detail
    assert "lo que va del año" in detail
    lead, detail = ba_trends.monthly_context("2025", last)  # a whole year, December to December
    assert lead == "Estás viendo 2025: de ene 2025 a dic 2025."
    assert (
        detail.startswith("Es el año completo.") and "dic 2024 = 100" in detail and "de diciembre a diciembre" in detail
    )
    lead, detail = ba_trends.monthly_context("2022", last)  # no index before January 2022, no alert before April
    assert "ene 2022 = 100, el primer mes de los datos" in detail and "empieza en febrero" in detail
    assert "La primera alerta posible es de abril 2022" in detail
    lead, detail = ba_trends.history_context(last)
    assert lead == "Estás viendo toda la historia: de ene 2022 a sep 2026."
    assert "termina en sep 2026" in detail and detail.endswith("2022 desde enero y 2026 hasta septiembre.")
    assert ba_trends.history_context((2026, 12))[1].endswith("2022 desde enero.")  # a whole last year says nothing more
    lead, detail = ba_trends.inflation_context(last)
    assert lead.endswith("de ene 2022 a sep 2026.") and "no prueba que la inflación cause la subida" in detail
    lead, detail = ba_trends.insights_context(pd.Timestamp("2026-10-19"), last)
    assert "la semana 19–25 oct 2026" in detail and "hasta sep 2026" in detail  # a week by its range (D-374)
    panel = ba_trends.context_html("Estás viendo <esto>.", "Y por qué.")
    assert panel.startswith('<div class="ba-context">') and "<b>Estás viendo &lt;esto&gt;.</b> Y por qué." in panel
    assert "min-height:calc(2.9em + 16px)" in ba_trends.build_context_css(charts.get_palette("Vantablack"), "#39ff14")


@needs_database
def test_d458_the_panel_sits_above_the_tabs_and_follows_the_tab_and_the_period():
    def draw(state):
        app = AppTest.from_file(str(Path(dashboard.__file__)), default_timeout=120)
        app.session_state["visitor_profile"] = "profesional"
        for key, value in state.items():
            app.session_state[key] = value
        app.query_params.update({"vista": dashboard.PAGE_BA})
        app.run()
        assert not app.exception
        return " ".join(block.value for block in app.markdown)

    markup = draw({})
    assert markup.index('class="ba-context"') < markup.index('class="ba-card"')  # above the tabs and the report
    assert "Estás viendo los últimos 12 meses" in markup
    assert "Estás viendo 2024: de ene 2024 a dic 2024." in draw({"ba_period": "2024"})
    assert "Estás viendo toda la historia" in draw({dashboard.BA_TAB_KEY: dashboard.BA_HISTORY_TAB})
    inflation = draw({dashboard.BA_TAB_KEY: "Precios e inflación"})  # its note moved into the panel, said once
    assert inflation.count("no prueba que la inflación cause la subida") == 1
    stakeholders = draw({dashboard.BA_TAB_KEY: "Interesados"})  # the rule of the rings too
    assert stakeholders.count("Cada anillo dice cuánto depende") == 1 and 'class="im-criterion"' not in stakeholders
