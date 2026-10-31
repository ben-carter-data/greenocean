"""«Último dato por canal» (D-365): the last week each source published, each in its own block.

Since D-356 the Price overview and the indicators publish up to the last week complete in both sources. This page reads
`latest_by_source`, which keeps the last two weeks of each source without that cut, and shows each source with its own
latest week: the change by family against its previous week and its products, like the overview. A source behind the
other says which week it has not published yet. Pure: no Streamlit; the dashboard draws the blocks.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd

from bi import home_mockup

SOURCES = (("wholesale", "Mayorista"), ("consumer", "Consumidor"))
KEY = ["product_group", "product", "variety", "quality", "normalized_unit", "channel"]
STILL = 0.05  # a regional change under this many percent is «no change» for the up and down counts


def weeks_of(frame: pd.DataFrame, source: str) -> list[str]:
    """The weeks of one source in the table, newest first (two at most)."""
    return sorted(frame.loc[frame["source"] == source, "week_start"].unique(), reverse=True)


def late_week(frame: pd.DataFrame, source: str) -> str | None:
    """The week this source has not published yet while the other has: the week after its last; None when it is not
    behind."""
    own = weeks_of(frame, source)
    newest = max(frame["week_start"].unique(), default=None)
    if not own or newest is None or own[0] >= newest:
        return None
    return str(date.fromisoformat(own[0]) + timedelta(days=7))


def build_rows(frame: pd.DataFrame, source: str) -> tuple[str | None, str | None, list[dict[str, Any]]]:
    """(latest week, previous week, rows) of one source. Each row is one product and channel: the average of the
    regions with a price in both weeks (the variation compares those), the national price of each week and the regions
    that rose and fell, as the overview's table reads it. Flagged prices and unconvertible units stay out."""
    weeks = weeks_of(frame, source)
    if len(weeks) < 2:
        return (weeks[0] if weeks else None), None, []
    now, before = weeks[0], weeks[1]
    valid = frame[
        (frame["source"] == source) & frame["flag"].isna() & frame["normalized_unit"].notna() & frame["price"].notna()
    ]
    current, previous = valid[valid["week_start"] == now], valid[valid["week_start"] == before]
    regional = ["region_id", "region"]
    matched = current.merge(previous[KEY + regional + ["price"]], on=KEY + regional, suffixes=("", "_before"))
    national_now = current.groupby(KEY)["price"].mean()
    national_before = previous.groupby(KEY)["price"].mean()
    rows = []
    for key, group in matched.groupby(KEY):
        same_now, same_before = group["price"].mean(), group["price_before"].mean()
        if not same_before:
            continue
        changes = [
            (home_mockup.short_region(region), (price / price_before - 1) * 100)
            for region, price, price_before in zip(group["region"], group["price"], group["price_before"])
            if price_before
        ]
        up = sum(change >= STILL for _, change in changes)
        down = sum(change <= -STILL for _, change in changes)
        row = dict(zip(KEY, key))
        row.update(
            national_price=float(national_now[key]),
            _previous_price=float(national_before[key]),
            _same_now=float(same_now),
            _same_before=float(same_before),
            variation=float(same_now / same_before - 1),
            _regions=(up, down, sorted(changes)),
        )
        rows.append(row)
    rows.sort(key=lambda row: (-abs(row["variation"]), row["product"]))
    return now, before, rows


def matches(row: dict[str, Any], query: str) -> bool:
    """The search of the table: the product, its variety or its channel contain the words, case and accents aside."""
    text = " ".join(str(row.get(field) or "") for field in ("product", "variety", "channel"))
    return all(word in home_mockup_plain(text) for word in home_mockup_plain(query).split())


def home_mockup_plain(text: str) -> str:
    import unicodedata

    return "".join(c for c in unicodedata.normalize("NFKD", str(text).lower()) if not unicodedata.combining(c))
