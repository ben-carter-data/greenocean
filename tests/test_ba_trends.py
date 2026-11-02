"""«Análisis BA y BI» · «Tendencias» (D-456): every figure is recomputed from the database, and the ones the page shares
with «Precios e inflación» and «Insights» are the same numbers."""

import pandas as pd
import pytest

from bi import alerts, ba_trends, inflation_view, queries

needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")


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


def test_d456_the_periods_and_their_months():
    last = (2026, 9)
    assert ba_trends.periods(last) == ["Últimos 12 meses", "Desde ene 2022", "2026", "2025", "2024", "2023", "2022"]
    assert ba_trends.bounds("Últimos 12 meses", last) == ((2025, 9), (2026, 9))
    assert ba_trends.bounds("Desde ene 2022", last) == ((2022, 1), (2026, 9))
    assert ba_trends.bounds("2025", last) == ((2024, 12), (2025, 12)) and ba_trends.bounds("2022", last)[0] == (2022, 1)
    # a change is measured from the start month; the weeks counted are those of the months after it
    assert ba_trends.counted_months((2025, 9), (2026, 9)) == (202510, 202609)
    assert ba_trends.counted_months((2022, 1), (2026, 9)) == (202201, 202609)


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
    whole = ba_trends.summarize(
        rows, margins, seasonal, found, ba_trends.BASKET, *ba_trends.bounds(ba_trends.SINCE_BASE, last)
    )
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


def test_d456_every_card_and_column_explains_itself_on_hover():
    figures = {
        "change": 6.1, "ipc": 4.3, "gap": 1.8, "verdict": "al ritmo de la inflación", "margin": 78.9, "pairs": 31354,
        "alerts": 916, "rises": 635, "falls": 281, "cheapest": (2, -3.2), "dearest": (9, 2.4),
    }  # fmt: skip
    cards = ba_trends.build_cards(figures, (2025, 9), (2026, 9))
    assert cards.count('class="ba-card" tabindex="0" title="') == 5
    for word in ("K1", "K4", "K6", "IPC de alimentos del INE", "«Precios e inflación»"):
        assert word in cards, word
    table = ba_trends.build_table([dict(figures, family=ba_trends.BASKET)], ba_trends.BASKET)
    assert table.count("<th title=") == 5 and 'class="ba-chosen"' in table


def test_d456_every_time_chart_starts_at_the_start_of_its_period():
    # The first alert can only come 12 weeks into the history (K6), so the alerts chart used to start its axis in
    # 2023 although 2022 had alerts; the axis is now the whole period, bars filling their month.
    assert ba_trends.month_domain((2022, 1), (2026, 9)) == ["2022-01-01", "2026-09-01"]
    assert ba_trends.month_domain((2022, 1), (2026, 9), counted=True) == ["2022-01-01", "2026-10-01"]
    assert ba_trends.month_domain((2025, 9), (2026, 9), counted=True) == ["2025-10-01", "2026-10-01"]
    assert ba_trends.month_domain((2024, 12), (2025, 12), counted=True) == ["2025-01-01", "2026-01-01"]
    frame = pd.DataFrame({"week_start": ["2022-04-04"], "variation": [0.2]})
    spec = ba_trends.alerts_chart(frame, (2022, 1), (2026, 9), "Vantablack").to_dict()
    assert spec["encoding"]["x"]["scale"]["domain"] == ["2022-01-01", "2026-10-01"]
    assert spec["encoding"]["x"]["timeUnit"] == "yearmonth"


def test_d456_the_season_says_which_years_each_calendar_month_gathers():
    # A bar of «Temporada» is a month of the calendar, not of one year: with several years it gathers that month of
    # each of them, and the chart says from which month to which, and each bar its years.
    weeks = pd.DataFrame(
        {
            "week_start": ["2024-02-05", "2025-02-03", "2025-03-03", "2026-02-02"],
            "seasonal_index": [0.97, 0.95, 1.02, 0.99],
        }
    )
    profile = ba_trends.season(weeks).set_index("month")
    assert profile.loc[2, "years"] == "2024–2026" and profile.loc[3, "years"] == "2025"
    assert profile.loc[2, "change"] == pytest.approx((0.97 - 1) * 100) and profile.loc[2, "weeks"] == 3
    assert ba_trends.season_span((2022, 1), (2026, 9)) == ("ene 2022", "sep 2026")
    assert ba_trends.season_span((2025, 9), (2026, 9)) == ("oct 2025", "sep 2026")
    spec = ba_trends.season_chart(ba_trends.season(weeks), "Vantablack").to_dict()
    assert any(item.get("field") == "years" for item in spec["encoding"]["tooltip"])
