"""Rules of «Contexto del precio» (D-094, D-098): usual range, state, gap, pattern."""
import pandas as pd
import pytest

from bi import price_context as pc


def series(prices):
    """{monday: price} → one price series."""
    return pd.DataFrame({"week_start": pd.to_datetime(list(prices)), "national_price": list(prices.values())})


# Monday of ISO week 41 (and its neighbours, weeks 40 and 42) in each year.
WEEK_40 = {2022: "2022-10-03", 2023: "2023-10-02", 2024: "2024-09-30", 2025: "2025-09-29", 2026: "2026-09-28"}
WEEK_41 = {2022: "2022-10-10", 2023: "2023-10-09", 2024: "2024-10-07", 2025: "2025-10-06", 2026: "2026-10-05"}
WEEK_42 = {2022: "2022-10-17", 2023: "2023-10-16", 2024: "2024-10-14", 2025: "2025-10-13", 2026: "2026-10-20"}


def test_usual_range_pools_the_week_and_its_iso_neighbours_across_previous_years():
    rows = series({WEEK_41[2022]: 100, WEEK_41[2023]: 200, WEEK_40[2024]: 250, WEEK_42[2025]: 500,
                   WEEK_41[2026]: 9999, "2025-11-03": 7000})
    low, high, years = pc.rango_habitual(rows, WEEK_41[2026])
    # The current year and a week outside the ±1 window stay out.
    assert years == 4
    assert low == pytest.approx(175) and high == pytest.approx(312.5)


def test_usual_range_needs_two_previous_years_with_a_price_in_the_window():
    rows = series({WEEK_41[2025]: 400, WEEK_41[2026]: 500})
    assert pc.rango_habitual(rows, WEEK_41[2026]) is None
    assert pc.estado_precio(500, None) == "sin_historia"


def test_a_missing_week_in_one_year_leaves_that_year_out():
    rows = series({WEEK_41[2022]: 100, WEEK_41[2024]: 300, "2023-11-20": 900})
    assert pc.rango_habitual(rows, WEEK_41[2026])[2] == 2
    # Incomplete years: only one previous year with a price in the window is not enough.
    assert pc.rango_habitual(series({WEEK_41[2024]: 300, "2023-11-20": 900}), WEEK_41[2026]) is None


def test_the_window_narrows_at_the_edges_of_the_calendar_instead_of_guessing():
    # ISO week 1 of 2026 starts 2025-12-29; it has no week 0, only weeks 1 and 2.
    rows = series({"2023-01-02": 100,    # 2023, week 1: counts
                   "2023-01-09": 200,    # 2023, week 2: counts
                   "2024-01-01": 300,    # 2024, week 1: counts
                   "2025-12-22": 9000})  # 2025, week 52: NOT a neighbour of week 1
    low, high, years = pc.rango_habitual(rows, "2025-12-29")
    assert years == 2
    assert low == pytest.approx(150) and high == pytest.approx(250)


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


def test_usual_gap_range_pools_the_same_iso_window_as_prices():
    gaps = pd.DataFrame({"week_start": pd.to_datetime([WEEK_40[2023], WEEK_41[2023], WEEK_42[2024], WEEK_41[2026]]),
                         "gap": [10.0, 20.0, 40.0, 5.0]})
    low, high, years = pc.brecha_rango_habitual(gaps, WEEK_41[2026])
    # 2023 contributes both its week-40 and week-41 gaps (10 and 20); 2024 contributes 40.
    assert years == 2 and low == pytest.approx(15.0) and high == pytest.approx(30.0)
    assert pc.brecha_rango_habitual(gaps[gaps["week_start"].dt.year != 2023], WEEK_41[2026]) is None


def test_seasonal_pattern_averages_months_then_years_and_leaves_the_current_year_out():
    rows = pd.DataFrame({
        "week_start": pd.to_datetime(["2024-01-01", "2024-01-08", "2025-01-06", "2026-01-05"]),
        "price_year": [2024, 2024, 2025, 2026],
        "seasonal_index": [0.8, 1.0, 1.2, 5.0]})
    pattern = pc.patron_estacional(rows, current_year=2026)
    # (mean 2024 = 0.9, 2025 = 1.2) → 1.05; 2026 is provisional and stays out.
    assert pattern == {1: pytest.approx(105.0)}
    assert pc.patron_estacional(rows.iloc[:0]) == {}


def test_next_months_default_to_three_and_wrap_the_year():
    pattern = {10: 95.0, 11: 100.0, 12: 90.0, 1: 110.0}
    assert pc.proximos_meses(pattern, 11) == [(12, pytest.approx(-10.0)), (1, pytest.approx(10.0))]
    assert [m for m, _ in pc.proximos_meses(pattern, 10)] == [11, 12, 1]
    assert pc.proximos_meses(pattern, 5) == []


def test_answer_sentence_is_built_from_states_and_names_missing_history():
    sentence = pc.answer_sentence("tomate larga vida", 10, {"Feria libre": "sobre", "Supermercado": "dentro"}, "menor")
    assert sentence == ("Esta semana, el precio de tomate larga vida en feria libre está sobre lo habitual para octubre; "
                        "en supermercado está dentro de lo habitual. "
                        "La diferencia entre ambos canales es menor que de costumbre.")
    assert "sin historia suficiente" in pc.answer_sentence("Tomate", 10, {"Feria libre": "sin_historia"}, None)
    # No gap_word: the clause about the gap is left out entirely (D-098).
    assert "diferencia" not in pc.answer_sentence("Tomate", 10, {"Feria libre": "dentro"}, None)


def test_answer_sentence_wrap_colours_each_channel_state_and_skips_missing_history():
    seen = []
    def wrap(channel, phrase):
        seen.append((channel, phrase))
        return f"[{channel}:{phrase}]"
    sentence = pc.answer_sentence("palta hass", 3, {"Feria libre": "sobre", "Supermercado": "sin_historia"},
                                  None, wrap=wrap)
    assert seen == [("Feria libre", "sobre lo habitual")]
    assert "[Feria libre:sobre lo habitual]" in sentence
    assert "sin historia suficiente para compararlo" in sentence
    assert "[Supermercado:" not in sentence


def test_calendar_columns_from_dim_date_drive_the_usual_range_and_the_month():
    # Columns joined from dim_date win over the ones computed from week_start.
    rows = series({"2023-03-06": 100, "2024-03-04": 300}).assign(iso_year=[2023, 2024], iso_week=[7, 7], month=[2, 2])
    assert pc.rango_habitual(rows, "2026-03-02", iso=(2026, 7))[2] == 2
    assert pc.rango_habitual(rows, "2026-03-02", iso=(2026, 20)) is None
    seasonal = pd.DataFrame({"week_start": pd.to_datetime(["2024-03-04", "2025-03-03"]), "price_year": [2024, 2025],
                             "seasonal_index": [1.0, 1.2], "month": [2, 2]})
    assert set(pc.patron_estacional(seasonal)) == {2}
