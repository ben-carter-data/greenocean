"""«Último dato por canal» (D-365): each source with its own latest week, its change by family and its products."""

from pathlib import Path

import duckdb
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from bi import channel_latest, dashboard

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = str(ROOT / "bi" / "dashboard.py")


def sample():
    """The consumer source already has the week of 19-10; the wholesale one stops at 12-10."""
    rows = []
    for source, weeks in (("consumer", ["2026-10-12", "2026-10-19"]), ("wholesale", ["2026-10-05", "2026-10-12"])):
        for index, week in enumerate(weeks):
            for region_id, region, base in (
                (13, "Región Metropolitana de Santiago", 1000),
                (5, "Región de Valparaíso", 1100),
            ):
                rows.append(
                    dict(
                        week_start=week,
                        source=source,
                        channel="Feria libre" if source == "consumer" else "Mercado",
                        region_id=region_id,
                        region=region,
                        product_group="Frutas",
                        product="Manzana",
                        variety="Fuji",
                        quality="Primera",
                        normalized_unit="kilo",
                        price=base * (1 + 0.1 * index),
                        observation_count=3,
                        flag=None,
                    )
                )
    rows.append(dict(rows[-1], product="Pera", price=999999.0, flag="ATIPICO"))  # a flagged price stays out
    return pd.DataFrame(rows)


def test_d365_each_source_reads_its_own_latest_week_and_says_which_one_it_has_not_published():
    frame = sample()
    week, before, rows = channel_latest.build_rows(frame, "consumer")
    assert (week, before) == ("2026-10-19", "2026-10-12")
    week, before, rows = channel_latest.build_rows(frame, "wholesale")
    assert (week, before) == ("2026-10-12", "2026-10-05") and all(row["product"] != "Pera" for row in rows)
    assert channel_latest.late_week(frame, "wholesale") == "2026-10-19"  # the week the consumer source has
    assert channel_latest.late_week(frame, "consumer") is None


def test_d365_the_change_of_each_product_is_recomputed_by_sql_from_the_table():
    frame = sample()
    connection = duckdb.connect()
    connection.register("latest", frame)
    for source in ("consumer", "wholesale"):
        _, _, rows = channel_latest.build_rows(frame, source)
        expected = connection.execute(
            """
            with weeks as (select week_start from latest where source = ? group by 1 order by 1 desc limit 2),
                 now as (select max(week_start) as w from weeks), prev as (select min(week_start) as w from weeks)
            select a.product, avg(a.price) / avg(b.price) - 1
            from latest a join latest b using (source, product, variety, quality, normalized_unit, channel, region_id)
            where a.source = ? and a.flag is null and b.flag is null
              and a.week_start = (select w from now) and b.week_start = (select w from prev)
            group by 1
            """,
            [source, source],
        ).fetchall()
        assert {row["product"]: row["variation"] for row in rows} == pytest.approx(dict(expected))
        assert all(row["_regions"][:2] == (2, 0) for row in rows)  # both regions rose 10 %


def test_d365_the_page_draws_both_blocks_for_every_view_and_the_overview_links_to_it(monkeypatch):
    for profile in ("consulta", "profesional"):
        app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
        app.session_state["visitor_profile"] = profile
        app.run()
        assert "Último dato por canal" in [link.proto.label for link in app.sidebar.get("page_link")], profile
    assert "Ver último dato por canal" in [link.proto.label for link in app.main.get("page_link")]  # on the overview
    script = (
        f"import sys\nsys.path.insert(0, {str(ROOT)!r})\nimport pandas as pd\nfrom bi import dashboard\n"
        "from tests.test_channel_latest import sample\n"
        "dashboard.read_latest_by_source = lambda version: sample()\n"
        "dashboard.render_page(dashboard.PAGE_CHANNELS)\n"
    )
    page = AppTest.from_string(script, default_timeout=90).run()
    assert not page.exception
    text = " ".join(block.value for block in page.markdown) + " ".join(caption.value for caption in page.caption)
    assert "Mayorista · semana del 12-10" in text and "Consumidor · semana del 19-10" in text
    assert text.count("ODEPA aún no publica la semana del 19-10") == 1  # only the wholesale block is behind
    assert text.count('class="mock-products-table"') == 2 and "Toda la canasta" not in text
    assert [box.key for box in page.text_input] == ["latest_search_wholesale", "latest_search_consumer"]


def test_d365_the_table_is_served_and_documented():
    from etl import pipeline

    assert "latest_by_source" in pipeline.SERVING_TABLES
    model = (ROOT / "dbt" / "models" / "marts" / "latest_by_source.sql").read_text(encoding="utf-8")
    assert (
        "row_number() over (partition by source order by week_start desc) <= 2" in model
        and "int_prices__weekly" in model
    )
    assert "### latest_by_source" in (ROOT / "docs" / "SAD.md").read_text(encoding="utf-8")
    assert dashboard.PAGE_CHANNELS in next(pages for key, _, pages in dashboard.MENU_BLOCKS if key == "negocio")
