"""Key figures of the panel, computed the way the panel computes them (D-153).

The reference of the week of 2026-10-05 lives in tests/fixtures/; the migration to
DuckDB (paso 2 del plan) must reproduce it exactly.
"""
import json
from pathlib import Path

from bi import dashboard, home_mockup, queries

SNAPSHOT_FILE = Path(__file__).parent / "fixtures" / "snapshot_2026-10-05.json"


def compute_snapshot():
    week = f"{dashboard.read_latest_week():%Y-%m-%d}"
    model = dashboard.read_home_model(week, dashboard.ALL_VALUES, dashboard.ALL_VALUES, 8)
    regions = dashboard.read_regional_movement_model(week)
    counts = queries.run_sql("""SELECT ch.source, COUNT(*) AS n, ROUND(SUM(price), 4) AS total
                                FROM weekly_price wp JOIN dim_channel ch USING(channel_id) GROUP BY 1""")
    flags = queries.run_sql("SELECT COALESCE(flag, 'SIN_MARCA') AS f, COUNT(*) AS n "
                            "FROM weekly_price GROUP BY 1")
    return {
        "week": week,
        "weekly_price_rows": int(queries.run_sql("SELECT COUNT(*) AS n FROM weekly_price")["n"][0]),
        "rows_by_source": {r["source"]: int(r["n"]) for r in counts.to_dict("records")},
        "price_sum_by_source": {r["source"]: float(r["total"]) for r in counts.to_dict("records")},
        "flags": {str(r["f"]): int(r["n"]) for r in flags.to_dict("records")},
        "rejected_rows": int(queries.run_sql("SELECT COUNT(*) AS n FROM rejection")["n"][0]),
        "alerts_latest_week": int(model["alert_count"]),
        "compared": int(sum(model["counts"])), "available": int(model["available"]),
        "family_medians": {family: round(value, 8)
                           for family, value, _ in home_mockup.family_averages(model["family_rows"])},
        "region_states": {row["region"]: row["state"] for row in regions},
    }


def read_reference():
    return json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
