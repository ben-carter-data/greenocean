"""Precios e inflación (D-163, D-244): each family's change, recomputed in SQL from the tables (P-4)."""
import pytest

from bi import inflation_view, queries

needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")


def read_page_figures():
    rows, last = inflation_view.build_family_index(queries.run_sql(inflation_view.SERIES_SQL),
                                                   queries.run_sql("SELECT year, month, food_index FROM ipc_monthly"))
    summary, ipc_total, ipc_year = inflation_view.summarize_families(rows, last)
    return last, summary.set_index("family"), ipc_total


@needs_database
def test_p4_each_family_change_and_the_ipc_match_a_recomputation_in_sql():
    """The same products from January 2022 to the last month the INE published: the median of their price ratios."""
    last, summary, ipc_total = read_page_figures()
    families = queries.run_sql(f"""
        WITH national AS (
            SELECT wp.week_start, p.product_group, wp.product_id, wp.channel_id, wp.normalized_unit, avg(wp.price) AS price
            FROM weekly_price AS wp JOIN dim_product AS p USING (product_id) JOIN dim_channel AS ch USING (channel_id)
            WHERE wp.flag IS NULL AND ch.source = 'consumer'
            GROUP BY ALL),
        monthly AS (
            SELECT product_group, product_id, channel_id, normalized_unit, year(week_start::DATE) AS y,
                   month(week_start::DATE) AS m, avg(price) AS price
            FROM national GROUP BY ALL)
        SELECT b.product_group, (median(l.price / b.price) - 1) * 100 AS total, count(*) AS series
        FROM monthly AS b JOIN monthly AS l USING (product_group, product_id, channel_id, normalized_unit)
        WHERE b.y = 2022 AND b.m = 1 AND l.y = {last[0]} AND l.m = {last[1]}
        GROUP BY b.product_group""").set_index("product_group")
    assert set(families.index) == set(summary.index)
    for family, row in families.iterrows():
        assert summary.loc[family, "total"] == pytest.approx(row["total"], abs=1e-9), family
    ipc = queries.run_sql(f"""SELECT (max(food_index) FILTER (WHERE year = {last[0]} AND month = {last[1]})
                                     / max(food_index) FILTER (WHERE year = 2022 AND month = 1) - 1) * 100 AS total
                              FROM ipc_monthly""")["total"][0]
    assert ipc_total == pytest.approx(ipc, abs=1e-9)
    # The verdict follows from the two numbers: more than the IPC when the family rose over 2 points more.
    for family, row in summary.iterrows():
        expected = ("más que la inflación" if row["total"] - ipc_total > inflation_view.SAME_PACE_POINTS
                    else "menos que la inflación" if row["total"] - ipc_total < -inflation_view.SAME_PACE_POINTS
                    else "al ritmo de la inflación")
        assert row["verdict"] == expected, family
