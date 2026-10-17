"""Rules of «Contexto del precio» (D-094): usual range, state, gap and seasonal pattern."""
import pandas as pd
import pytest

from bi import price_context as pc


def series(prices):
    """{monday: price} → one price series."""
    return pd.DataFrame({"week_start": pd.to_datetime(list(prices)), "national_price": list(prices.values())})


# Monday of ISO week 41 in each year.
WEEK_41 = {2022: "2022-10-10", 2023: "2023-10-09", 2024: "2024-10-07", 2025: "2025-10-06", 2026: "2026-10-05"}


def test_usual_range_uses_the_same_iso_week_of_previous_years_only():
    rows = series({WEEK_41[2022]: 100, WEEK_41[2023]: 200, WEEK_41[2024]: 300, WEEK_41[2025]: 400,
                   WEEK_41[2026]: 9999, "2025-10-13": 5000})
    low, high, years = pc.rango_habitual(rows, WEEK_41[2026])
    # The current year and the neighbouring week stay out.
    assert years == 4
    assert low == pytest.approx(175) and high == pytest.approx(325)


def test_usual_range_needs_two_previous_years():
    rows = series({WEEK_41[2025]: 400, WEEK_41[2026]: 500})
    assert pc.rango_habitual(rows, WEEK_41[2026]) is None
    assert pc.estado_precio(500, None) == "sin_historia"


def test_a_missing_week_in_one_year_leaves_that_year_out():
    rows = series({WEEK_41[2022]: 100, WEEK_41[2024]: 300, "2023-10-16": 900})
    assert pc.rango_habitual(rows, WEEK_41[2026])[2] == 2
    # Incomplete years: only one previous year with that week is not enough.
    assert pc.rango_habitual(series({WEEK_41[2024]: 300, "2023-10-16": 900}), WEEK_41[2026]) is None


def test_price_state_against_p25_and_p75():
    usual = (100.0, 200.0, 3)
    assert pc.estado_precio(201, usual) == "sobre"
    assert pc.estado_precio(200, usual) == "dentro"
    assert pc.estado_precio(100, usual) == "dentro"
    assert pc.estado_precio(99, usual) == "bajo"
    assert pc.estado_precio(float("nan"), usual) == "sin_historia"


def test_weekly_context_keeps_missing_weeks_as_gaps():
    rows = series({WEEK_41[2022]: 100, WEEK_41[2023]: 200, WEEK_41[2024]: 300,
                   "2026-09-21": 250, WEEK_41[2026]: 350})
    context = pc.weekly_context(rows, WEEK_41[2026], weeks=3)
    assert list(context["week_start"].dt.strftime("%Y-%m-%d")) == ["2026-09-21", "2026-09-28", "2026-10-05"]
    assert context.loc[1, "price"] is None or pd.isna(context.loc[1, "price"])
    assert pd.isna(context.loc[1, "state"])
    assert context.loc[2, "state"] == "sobre"


def test_gap_is_supermarket_over_street_market_on_common_weeks():
    feria = series({"2026-09-28": 1000, "2026-10-05": 1000, "2026-10-12": 0})
    supermercado = series({"2026-10-05": 1250, "2026-10-12": 900, "2026-09-21": 800})
    gaps = pc.brecha(feria, supermercado)
    assert list(gaps["week_start"].dt.strftime("%Y-%m-%d")) == ["2026-10-05"]
    assert gaps["gap"].iloc[0] == pytest.approx(25.0)


def test_usual_gap_is_the_median_of_the_same_month_in_previous_years():
    gaps = pd.DataFrame({"week_start": pd.to_datetime(["2023-10-02", "2023-10-09", "2024-10-07",
                                                       "2024-11-04", "2026-10-05"]),
                         "gap": [10.0, 20.0, 40.0, 99.0, 5.0]})
    assert pc.brecha_habitual(gaps, "2026-10-05") == pytest.approx(20.0)
    assert pc.brecha_habitual(gaps[gaps["week_start"].dt.year != 2023], "2026-10-05") is None


def test_seasonal_pattern_averages_months_then_years_and_leaves_the_current_year_out():
    rows = pd.DataFrame({
        "week_start": pd.to_datetime(["2024-01-01", "2024-01-08", "2025-01-06", "2026-01-05"]),
        "price_year": [2024, 2024, 2025, 2026],
        "seasonal_index": [0.8, 1.0, 1.2, 5.0]})
    pattern = pc.patron_estacional(rows, current_year=2026)
    # (mean 2024 = 0.9, 2025 = 1.2) → 1.05; 2026 is provisional and stays out.
    assert pattern == {1: pytest.approx(105.0)}
    assert pc.patron_estacional(rows.iloc[:0]) == {}


def test_next_months_are_relative_to_the_current_month_and_wrap_the_year():
    pattern = {11: 100.0, 12: 90.0, 1: 110.0}
    assert pc.proximos_meses(pattern, 11) == [(12, pytest.approx(-10.0)), (1, pytest.approx(10.0))]
    assert pc.proximos_meses(pattern, 5) == []


def test_answer_sentence_is_built_from_states_and_names_missing_history():
    sentence = pc.answer_sentence("tomate larga vida", 10, {"Feria libre": "sobre", "Supermercado": "dentro"}, "menor")
    assert sentence == ("Esta semana, el precio de tomate larga vida en feria libre está sobre lo habitual para octubre; "
                        "en supermercado está dentro de lo habitual. "
                        "La diferencia entre ambos canales es menor que de costumbre.")
    assert "sin historia suficiente" in pc.answer_sentence("Tomate", 10, {"Feria libre": "sin_historia"}, None)
    assert pc.describe_gap_comparison(30, 20) == "mayor"
    assert pc.describe_gap_comparison(21, 20) == "similar"
    assert pc.describe_gap_comparison(None, 20) is None
