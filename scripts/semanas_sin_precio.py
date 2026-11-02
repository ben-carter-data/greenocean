"""Why the prices of a week have no valid comparison (D-434): how long each one had been without a price.

    python scripts/semanas_sin_precio.py [--semana 2026-10-26]

Reads the served database with the project's own code, the same as the indicator «Precios con comparación válida»
(scripts/medir_calidad.py): the query k6_national_weekly_price and alerts.add_weekly_variation. For each price of the
week without a comparison it finds the last earlier week with a price in the same series (product, variety, quality,
channel and unit) and counts them: one week (it had a price the week before, but in other regions), 2 to 12 weeks,
more than 12 weeks, or never before. It also counts them by product group. It never changes a figure.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import alerts, queries  # noqa: E402

SERIES = ["product", "variety", "quality", "channel", "normalized_unit"]


def count_gaps(prices, week=None):
    """{week, prices, with_comparison, without, one_week, two_to_twelve, over_twelve, never, groups} of one week."""
    prices = prices.assign(week_start=pd.to_datetime(prices["week_start"]))
    variations = alerts.add_weekly_variation(prices.copy())
    week = pd.Timestamp(week) if week else variations["week_start"].max()
    now = variations[variations["week_start"] == week]
    missing = now[now["variation"].isna()]
    order = {value: index for index, value in enumerate(sorted(prices["week_start"].unique()))}
    keys = prices[SERIES].fillna("").astype(str).agg("|".join, axis=1)
    earlier = prices.assign(key=keys)[prices["week_start"] < week].groupby("key")["week_start"].max()
    gaps = [
        order[week] - order[earlier[key]] if key in earlier.index else None
        for key in missing[SERIES].fillna("").astype(str).agg("|".join, axis=1)
    ]
    gaps = pd.Series(gaps, dtype="float")
    return {
        "week": str(week.date()),
        "prices": int(len(now)),
        "with_comparison": int(now["variation"].notna().sum()),
        "without": int(len(missing)),
        "one_week": int((gaps == 1).sum()),
        "two_to_twelve": int(gaps.between(2, 12).sum()),
        "over_twelve": int((gaps > 12).sum()),
        "never": int(gaps.isna().sum()),
        "groups": {str(name): int(count) for name, count in missing["product_group"].value_counts().items()},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--semana", default="", help="the Monday of the week (YYYY-MM-DD); the latest by default")
    arguments = parser.parse_args()
    found = count_gaps(queries.run_query("k6_national_weekly_price"), arguments.semana or None)
    print(f"Semana {found['week']}: {found['without']} de {found['prices']} precios sin comparación válida")
    print(f"  tenían precio la semana anterior, en otras regiones: {found['one_week']}")
    print(f"  volvieron tras 2 a 12 semanas sin precio: {found['two_to_twelve']}")
    print(f"  volvieron tras más de 12 semanas sin precio: {found['over_twelve']}")
    print(f"  sin precio antes: {found['never']}")
    print("  por grupo: " + ", ".join(f"{name} {count}" for name, count in found["groups"].items()))


if __name__ == "__main__":
    main()
