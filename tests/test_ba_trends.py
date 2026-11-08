"""«Análisis» · «Mensual» and «Histórico» (D-456, D-457): every figure is recomputed from the database, the
ones the page shares with «Precios e inflación» are the same numbers, and every sentence a chart says on hover holds
the figures it explains."""

import math
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from bi import alerts, ba_trends, charts, dashboard, inflation_view, overview, queries, weeks

# region Constants
IPC = inflation_view.IPC_NAME
# endregion


# region Variables
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")
# endregion


# region «Análisis» · «Mensual» and «Histórico»: periods, figures and charts (D-456, D-457)
@pytest.fixture(scope="module")
def history():
    rows, last = inflation_view.build_family_index(
        queries.run_sql(inflation_view.SERIES_SQL),
        queries.run_sql("SELECT year, month, food_index FROM ipc_monthly"),
        basket=True,
    )
    margins = ba_trends.add_month_key(queries.run_query("k1_margin"))
    found = ba_trends.add_month_key(alerts.find_price_alerts(queries.run_query("k6_national_weekly_price")))
    return rows, last, margins, found


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
    rows, last, margins, found = history
    for family in [ba_trends.BASKET] + ba_trends.families(rows):
        for period in ba_trends.periods(last):
            start, end = ba_trends.bounds(period, last)
            figures = ba_trends.monthly(rows, margins, found, family, start, end)
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
        whole = ba_trends.history(rows, margins, found, family, last)
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
    rows, last, margins, found = history
    summary, ipc_total, ipc_year = inflation_view.summarize_families(
        rows[rows["product_group"] != inflation_view.BASKET_NAME], last
    )
    start, end = ba_trends.bounds(ba_trends.LAST_YEAR, last)
    for family in summary["family"]:
        figures = ba_trends.summarize(rows, margins, found, family, start, end)
        expected = summary.set_index("family").loc[family, "yearly"]
        assert figures["change"] == pytest.approx(expected), family  # the 12 months of «Precios e inflación»
        assert figures["ipc"] == pytest.approx(ipc_year)
        assert figures["gap"] == pytest.approx(figures["change"] - ipc_year)
        whole = ba_trends.history(rows, margins, found, family, last)
        assert whole["change"] == pytest.approx(summary.set_index("family").loc[family, "total"]), family
        assert whole["ipc"] == pytest.approx(ipc_total)
    # K1 and K6 recomputed by hand for the whole basket in the last 12 months
    months = ba_trends.counted_months(start, end)
    stamp = pd.to_datetime(margins["week_start"])
    key = stamp.dt.year * 100 + stamp.dt.month
    chosen = margins[key.between(*months)]
    figures = ba_trends.summarize(rows, margins, found, ba_trends.BASKET, start, end)
    assert figures["margin"] == pytest.approx(chosen["margin"].median() * 100) and figures["pairs"] == len(chosen)
    alert_key = pd.to_datetime(found["week_start"]).dt.year * 100 + pd.to_datetime(found["week_start"]).dt.month
    picked = found[alert_key.between(*months)]
    assert figures["alerts"] == len(picked) == figures["rises"] + figures["falls"]
    # K1 exists only where ODEPA has a wholesale price
    assert ba_trends.wholesale_families(margins) == sorted(set(margins["product_group"]))


@needs_database
def test_d457_each_chart_says_its_months_and_its_hover_holds_the_figures_it_explains(history):
    rows, last, margins, found = history
    start, end = ba_trends.bounds(ba_trends.LAST_YEAR, last)
    figures = ba_trends.monthly(rows, margins, found, ba_trends.BASKET, start, end)
    (_, price_note, _, price, _, _), (_, sharp_note, _, sharp, _, _) = ba_trends.monthly_tiles(
        rows, figures, start, end, "Vantablack"
    )
    first = (start[0] + 1, 1) if start[1] == 12 else (start[0], start[1] + 1)
    assert price_note == f"{label(start)} – {label(end)} · base {label(start)} = 100"
    assert sharp_note == f"{label(first)} – {label(end)} · cuántas hubo cada mes (K6)"
    assert price.startswith(
        f"De {label(start)} a {label(end)} cambió {charts.format_signed_percent(figures['change'])}"
    )
    assert f"({charts.format_signed_percent(figures['ipc'])})" in price and figures["verdict"] in price
    # D-556: the sharp changes say which dominate, and their typical sizes, from the alert rows themselves
    changes = figures["alert_rows"]["variation"] * 100
    rises, falls = int((changes > 0).sum()), int((changes < 0).sum())
    assert sharp.startswith(f"{charts.format_thousands(rises)} alzas fuertes y {charts.format_thousands(falls)} bajas")
    assert ("hubo más alzas que bajas" if rises > falls else "hubo más bajas que alzas") in sharp
    assert charts.format_signed_percent(changes[changes > 0].median()) in sharp
    # «Histórico»: from January 2022 and the change of each year
    whole = ba_trends.history(rows, margins, found, ba_trends.BASKET, last)
    (_, since_note, _, since, _, _), (_, year_note, _, yearly, _, _) = ba_trends.history_tiles(
        rows, whole, last, "Vantablack"
    )
    assert since_note == f"ene 2022 – {label(last)} · base ene 2022 = 100"
    assert year_note == f"2022–{last[0]} · de diciembre a diciembre"
    assert since.startswith(f"De ene 2022 a {label(last)} cambió {charts.format_signed_percent(whole['change'])}")
    assert f"El año que más subió fue {whole['best'][0]} ({charts.format_signed_percent(whole['best'][1])}" in yearly
    assert f"en {len(whole['above'])} de {len(whole['years'])} años" in yearly or not whole["above"]
    # the first alert of the history can only come after 12 weeks: the year 2022 says so
    start, end = ba_trends.bounds("2022", last)
    first_year = ba_trends.monthly(rows, margins, found, ba_trends.BASKET, start, end)
    sharp_measure = ba_trends.monthly_tiles(rows, first_year, start, end, "Vantablack")[1][2]
    assert "El primer cambio fuerte posible es de abril 2022" in sharp_measure
    assert pd.to_datetime(found["week_start"]).min() >= pd.Timestamp("2022-04-01")


@needs_database
def test_d554_each_chart_names_under_its_title_every_colour_it_draws(history):
    rows, last, margins, found = history
    start, end = ba_trends.bounds(ba_trends.LAST_YEAR, last)
    monthly = ba_trends.monthly(rows, margins, found, ba_trends.BASKET, start, end)
    whole = ba_trends.history(rows, margins, found, ba_trends.BASKET, last)
    tiles = ba_trends.monthly_tiles(rows, monthly, start, end, "Vantablack") + ba_trends.history_tiles(
        rows, whole, last, "Vantablack"
    )
    for title, _, _, _, draw, legend in tiles:
        spec = draw().to_dict()
        layers = spec.get("layer") or [spec]
        scales = [layer["encoding"]["color"]["scale"] for layer in layers if "color" in layer.get("encoding", {})]
        colours = [colour for scale in scales for _, colour in zip(scale["domain"], scale["range"])]
        colours += [layer["mark"]["color"] for layer in layers if "color" in layer["mark"]]
        assert colours and all(colour in legend for colour in colours), title


def test_d457_every_card_and_column_explains_itself_on_hover_with_the_definitions_of_metodo():
    figures = {
        "family": ba_trends.BASKET, "change": 6.1, "ipc": 3.9, "gap": 2.2, "verdict": "más que la inflación",
        "margin": 78.9, "pairs": 31354, "alerts": 916, "rises": 635, "falls": 281, "top": (2026, 7, 3.9),
        "low": (2025, 10, -1.9), "best": ("2022", 16.4, "desde ene"),
    }  # fmt: skip
    definitions = {name: how for name, how, _ in overview.KPIS}
    monthly = ba_trends.monthly_cards(figures, (2025, 9), (2026, 9), ["Frutas", "Hortalizas"])
    whole = ba_trends.history_cards(figures, (2026, 9))
    for cards, count in ((monthly, 5), (whole, 4)):
        assert cards.count('class="ba-card" tabindex="0" title="') == count
        for text in ("K6: " + alerts.describe_rule(), definitions["Alza frente al IPC"]):
            assert text in cards, text
    assert "K1: " + definitions["Brecha consumidor–mayorista"] in monthly
    assert "Solo Frutas y Hortalizas tienen precio mayorista" in monthly
    assert "sep 2025 → sep 2026" in monthly and "ene 2022 → sep 2026" in whole
    assert ">jul 2026<" in monthly and ">2022<" in whole
    for table, count in (
        (ba_trends.monthly_table([dict(figures, months=None)], ba_trends.BASKET), 5),
        (ba_trends.history_table([figures], ba_trends.BASKET), 4),
    ):
        assert table.count("<th title=") == count and 'class="ba-chosen"' in table


def test_d456_every_time_chart_starts_at_the_start_of_its_period():
    # The first alert can only come 12 weeks into the history (K6), so the alerts chart used to start its axis in
    # 2023 although 2022 had alerts; the axis is now the whole period, also its months without an alert.
    assert [day.to_dict() for day in ba_trends.month_domain((2022, 1), (2026, 9))] == [
        {"year": 2022, "month": 1, "date": 1},
        {"year": 2026, "month": 9, "date": 1},
    ]  # local time, like the data: a text date is midnight UTC, the day before in Chile (D-457)
    assert ba_trends.months_between((2025, 11), (2026, 2)) == [(2025, 11), (2025, 12), (2026, 1), (2026, 2)]
    frame = pd.DataFrame({"week_start": ["2022-04-04"], "variation": [0.2]})
    spec = ba_trends.extremes_chart(frame, (2022, 1), (2022, 12), "Vantablack").to_dict()
    assert spec["encoding"]["x"]["scale"]["domain"] == [f"{month} 2022" for month in weeks.MONTHS]
    last_year = ba_trends.extremes_chart(frame.iloc[:0], (2025, 9), (2026, 9), "Vantablack").to_dict()
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
    assert (
        axis["tickCount"] == {"interval": "month", "step": 1} and axis["labelOverlap"] == "parity"
    )  # D-483: every month while they fit
    assert spec["mark"]["point"]["filled"] is True
    # D-460: on the page, each month in two short lines, the year under the first month and under January
    assert axis["labelAngle"] == 0 and axis["labelExpr"] == (
        "[timeFormat(datum.value, '%b'), datum.index == 0 || month(datum.value) == 0 ? timeFormat(datum.value, '%Y') : '']"
    )
    large = ba_trends.trend_chart(rows, "Pan", (2025, 9), (2026, 9), "Vantablack", height=300).to_dict()
    assert large["encoding"]["x"]["axis"]["format"] == "%b %Y" and "labelExpr" not in large["encoding"]["x"]["axis"]
    whole = ba_trends.trend_chart(rows, "Pan", (2022, 1), (2026, 9), "Vantablack").to_dict()
    assert whole["encoding"]["x"]["axis"]["format"] == "%Y" and "point" not in whole["mark"]  # «Histórico»: years
    frame = pd.DataFrame({"week_start": ["2025-10-06", "2025-11-03"], "variation": [0.2, -0.15]})
    bars = ba_trends.extremes_chart(frame, (2025, 9), (2026, 9), "Vantablack").to_dict()
    axis = bars["encoding"]["x"]["axis"]  # every month of the sharp changes, too, «oct 2025» split in two
    assert axis["labelOverlap"] == "parity" and "split(datum.value, ' ')[0] == 'ene'" in axis["labelExpr"]
    heights = {row["kind"]: row["height"] for row in bars["datasets"][bars["data"]["name"]]}
    assert heights == {"Alzas fuertes": 1, "Bajas fuertes": -1}  # D-556: the drops hang below the line


# endregion


# region The magnifier, the old address and the green panel (D-457, D-458, D-460)
def test_d460_the_green_magnifier_opens_the_chart_large_in_a_window():
    css = ba_trends.build_css(charts.get_palette("Vantablack"), "#39ff14")
    assert '[class*="st-key-ba_enlarge_"] button [data-testid="stIconMaterial"] { color:#39ff14 !important;' in css
    assert "drop-shadow(0 0 3px #39ff14)" in css  # it glows
    assert "st-key-ba_zoom_" not in css and ":hover [class*" not in css  # no more opening on hover
    # D-461: on a low window the charts keep 230 px and the table scrolls inside its box, its header in sight
    assert "min-height:max(calc(100vh - 603px), 230px)" in css
    assert (
        ".ba-table {{ max-height:max(calc(100vh - 588px), 140px); overflow:auto; }}".replace("{{", "{").replace(
            "}}", "}"
        )
        in css
    )
    assert "position:sticky; top:0;" in css
    words = ba_trends.zoom_text("lo que mide", "lo que se deduce")
    assert "<b>Qué mide</b> lo que mide" in words and "<b>Qué se deduce</b> lo que se deduce" in words


@needs_database
@pytest.mark.parametrize("tab", [dashboard.BA_MONTHLY_TAB, dashboard.BA_HISTORY_TAB])
def test_d460_each_tab_draws_its_charts_and_each_magnifier_opens_its_window(tab):
    app = AppTest.from_file(str(Path(dashboard.__file__)), default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.session_state[dashboard.BA_TAB_KEY] = tab
    app.query_params.update({"vista": dashboard.PAGE_BA})
    app.run()
    assert not app.exception
    markup = " ".join(block.value for block in app.markdown)
    count = 2  # D-554, D-556: each tab draws two, wider
    assert markup.count('class="ba-chart-title"') == count and "<b>Qué mide</b>" not in markup
    assert len(app.get("arrow_vega_lite_chart") + app.get("vega_lite_chart")) == count
    assert [box.key for box in app.selectbox if box.key in ("ba_period", "ba_family")] == (
        ["ba_period", "ba_family"] if tab == dashboard.BA_MONTHLY_TAB else ["ba_family"]
    )
    # D-460: its green magnifier opens a chart large in a window, with what it measures and what follows from it
    assert [button.key for button in app.button if str(button.key).startswith("ba_enlarge_")] == [
        f"ba_enlarge_{index}" for index in range(count)
    ]
    app.button(key="ba_enlarge_1").click().run()
    assert not app.exception
    window = app.get("dialog")
    assert len(window) == 1
    words = " ".join(block.value for block in window[0].markdown)
    assert "<b>Qué mide</b>" in words and "<b>Qué se deduce</b>" in words
    assert len(window[0].get("arrow_vega_lite_chart") + window[0].get("vega_lite_chart")) == 1


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
    assert "ene 2022 = 100, el primer mes de los datos" in detail
    assert "El primer cambio fuerte posible es de abril 2022" in detail
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


def draw_ba_page(state):
    """The markdown «Análisis» draws for a Profesional with `state` in the session."""
    app = AppTest.from_file(str(Path(dashboard.__file__)), default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    for key, value in state.items():
        app.session_state[key] = value
    app.query_params.update({"vista": dashboard.PAGE_BA})
    app.run()
    assert not app.exception
    return " ".join(block.value for block in app.markdown)


@needs_database
def test_d458_the_panel_sits_above_the_tabs_and_follows_the_tab_and_the_period():
    markup = draw_ba_page({})
    assert markup.index('class="ba-context"') < markup.index('class="ba-card"')  # above the tabs and the report
    assert "Estás viendo los últimos 12 meses" in markup
    assert "Estás viendo 2024: de ene 2024 a dic 2024." in draw_ba_page({"ba_period": "2024"})
    assert "Estás viendo toda la historia" in draw_ba_page({dashboard.BA_TAB_KEY: dashboard.BA_HISTORY_TAB})
    inflation = draw_ba_page({dashboard.BA_TAB_KEY: "Precios e inflación"})  # its note moved into the panel, said once
    assert inflation.count("no prueba que la inflación cause la subida") == 1
    stakeholders = draw_ba_page({dashboard.BA_TAB_KEY: "Interesados"})  # the rule of the rings too
    assert stakeholders.count("Cada anillo dice cuánto depende") == 1 and 'class="im-criterion"' not in stakeholders


# endregion


# region The colour of each year and a family made of its products (D-466, D-478)
def test_d466_each_year_has_its_own_colour():
    years = pd.DataFrame(
        {
            "year": ["2022", "2023", "2024"],
            "change": [16.4, 5.6, 4.6],
            "ipc": [22.7, 5.2, 3.6],
            "note": ["desde ene", "", ""],
        }
    )
    spec = ba_trends.years_chart(years, "Vantablack").to_dict()
    color = spec["layer"][0]["encoding"]["color"]
    assert color["field"] == "year" and color["scale"]["range"] == ba_trends.YEAR_COLORS
    assert len(set(ba_trends.YEAR_COLORS)) == len(ba_trends.YEAR_COLORS) >= 5  # 2022 to 2026, each apart


@needs_database
def test_d478_a_family_is_the_sum_of_its_products(history):
    rows, last, margins, found = history
    series = queries.run_sql(inflation_view.SERIES_SQL)
    ipc = queries.run_sql("SELECT year, month, food_index FROM ipc_monthly")
    product_rows, product_margins, product_found, family_of = ba_trends.product_frames(series, ipc, margins, found)
    for family in ba_trends.families(rows):
        whole = ba_trends.history(rows, margins, found, family, last)
        parts = [
            ba_trends.history(product_rows, product_margins, product_found, key, last)
            for key in ba_trends.products_of(family_of, family)
        ]
        # what is counted adds up exactly: the family's alerts and K1 pairs are its products'
        assert whole["alerts"] == sum(part["alerts"] for part in parts), family
        assert whole["rises"] == sum(part["rises"] for part in parts), family
        assert whole["pairs"] == sum(part["pairs"] for part in parts), family
    # a product's index is the median of its own consumer series against January 2022, recomputed by hand
    key = ba_trends.PRODUCT + "Plátano"
    own = series[series["product"] == "Plátano"].assign(
        key=lambda frame: (
            frame["product_id"].astype(str) + "|" + frame["channel_id"].astype(str) + "|" + frame["normalized_unit"]
        )
    )
    base = own[(own["year"] == 2022) & (own["month"] == 1)].set_index("key")["price"]
    end = own[(own["year"] == last[0]) & (own["month"] == last[1])].set_index("key")["price"]
    kept = sorted(set(base.index) & set(end.index))
    expected = (end[kept] / base[kept] * 100).median()
    drawn = product_rows[
        (product_rows["product_group"] == key) & (product_rows["month_start"] == pd.Timestamp(*last, 1))
    ]
    assert drawn["index"].iloc[0] == pytest.approx(expected)
    assert ba_trends.family_label(key) == "Plátano" and ba_trends.family_name(key) == "el producto Plátano"
    assert family_of[key] == "Frutas"


@needs_database
def test_d478_mensual_shows_a_family_over_its_products():
    app = AppTest.from_file(str(Path(dashboard.__file__)), default_timeout=90)
    app.query_params.update({"vista": dashboard.PAGE_BA, "perfil": "profesional"})
    app.session_state["ba_family"] = "Frutas"
    app.session_state["ba_product"] = ba_trends.PRODUCT + "Plátano"
    app.run()
    assert not app.exception
    page = " ".join(block.value for block in app.markdown)
    assert "Familia y sus productos" in page
    table = page[page.index("Familia y sus productos") :]
    assert (
        table.index(">Frutas<") < table.index(">Plátano<") < table.index(">Aceituna")
    )  # the chosen one under its family


# endregion


# region The insight of the food CPI (D-518)
def food_cpi(decembers, tail=None):
    """A monthly food CPI with only its Decembers, plus the months in «tail»: (year, month, index)."""
    rows = [(year, 12, value) for year, value in decembers.items()] + list(tail or [])
    return pd.DataFrame(rows, columns=["year", "month", "food_index"])


def test_d518_the_insight_says_the_largest_jump_and_what_came_after():
    ipc = food_cpi({2009: 100.0, 2010: 105.0, 2011: 131.25, 2012: 136.5, 2013: 139.23}, [(2014, 3, 141.0)])
    lead, detail, hover = ba_trends.food_cpi_insight(ipc)
    assert lead == "Los alimentos subieron +25,0 % en 2011 según el IPC del INE, el mayor salto desde 2010."
    assert (
        detail == "Desde 2012 suben entre 2,0 % y 4,0 % al año: el alza se moderó, pero los precios no volvieron atrás."
    )
    assert hover == "IPC de alimentos del INE, de diciembre a diciembre, en años completos."  # a year with its December


def test_d518_the_sentence_only_says_what_the_data_holds():
    # the prices went back below the December of the jump: that clause goes
    fell = food_cpi({2009: 100.0, 2010: 130.0, 2011: 120.0})
    assert ba_trends.food_cpi_insight(fell)[1] == "Desde 2011 cambian -7,7 % al año: el alza se moderó."
    # the largest jump is the last whole year: nothing came after it yet
    assert ba_trends.food_cpi_insight(food_cpi({2009: 100.0, 2010: 103.0, 2011: 120.0}))[1] == ""
    # too little history says nothing
    assert ba_trends.food_cpi_insight(food_cpi({2009: 100.0})) is None
    assert ba_trends.food_cpi_insight(food_cpi({})) is None
    # a year without its December is never compared across the gap
    gap = ba_trends.food_cpi_insight(food_cpi({2009: 100.0, 2010: 101.0, 2012: 150.0, 2013: 153.0}))
    assert gap[0].startswith("Los alimentos subieron +2,0 % en 2013")


def test_d518_the_year_the_prices_start_explains_why_its_line_reads_lower():
    ipc = food_cpi({2021: 100.0, 2022: 125.0, 2023: 130.0}, [(2022, 1, 101.0)])
    _, _, hover = ba_trends.food_cpi_insight(ipc)
    assert "En «Cambio de cada año», 2022 parte en enero" in hover and "su raya marca +23,8 %" in hover


def test_d518_the_insight_reads_in_english(monkeypatch):
    monkeypatch.setattr(ba_trends.i18n, "is_english", lambda: True)
    ipc = food_cpi({2021: 100.0, 2022: 125.0, 2023: 130.0, 2024: 136.5}, [(2022, 1, 101.0)])
    lead, detail, hover = ba_trends.food_cpi_insight(ipc)
    assert lead == "Food prices rose +25.0 % in 2022 according to the INE CPI, the largest jump since 2022."
    assert (
        detail
        == "Since 2023 they rise between 4.0 % and 5.0 % a year: the rise has slowed, but prices did not go back."
    )
    assert "In «Change of each year», 2022 starts in January" in hover and "+23.8 %" in hover


@needs_database
def test_d518_the_box_shows_only_in_historico_with_figures_recomputed_from_the_base():
    ipc = queries.run_sql("SELECT year, month, food_index FROM ipc_monthly")
    december = ipc[ipc["month"] == 12].set_index("year")["food_index"].sort_index()
    changes = (december / december.shift() - 1).dropna() * 100
    lead, detail, hover = ba_trends.food_cpi_insight(ipc)
    assert charts.format_signed_percent(changes.max()) in lead and f" en {changes.idxmax()} " in lead
    assert f"desde {changes.index[0]}." in lead
    after = changes[changes.index > changes.idxmax()]
    assert charts.format_percent(after.min()) in detail and charts.format_percent(after.max()) in detail
    history = draw_ba_page({dashboard.BA_TAB_KEY: dashboard.BA_HISTORY_TAB})
    box = ba_trends.insight_html(lead, detail, hover)
    assert box in history and history.index('class="ba-card"') < history.index(box) < history.index('class="ba-table"')
    assert 'ba-insight"' not in draw_ba_page({dashboard.BA_TAB_KEY: dashboard.BA_MONTHLY_TAB})
    # the line of the chart and the sentence on hover give the same figure
    rows, last, *_ = dashboard.read_ba_history(dashboard.get_database_version())
    years = ba_trends.yearly_changes(rows, ba_trends.IPC, last).set_index("year")
    if changes.idxmax() == ba_trends.BASE[0]:
        assert ba_trends.percent(years.loc[str(ba_trends.BASE[0]), "ipc"]) in hover


# endregion
