"""«Último dato por canal» (D-365): each source with its own latest week, its change by family and its products."""

from pathlib import Path

import duckdb
import pandas as pd
import re

import pytest
from streamlit.testing.v1 import AppTest

from bi import channel_latest, dashboard, i18n

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


def test_d404_the_page_draws_one_whole_card_per_channel_and_a_card_opens_its_channel(monkeypatch):
    for profile in ("consulta", "profesional"):
        app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
        app.session_state["visitor_profile"] = profile
        app.run()
        assert "Último dato por canal" in [link.proto.label for link in app.sidebar.get("page_link")], profile
    # D-398: the overview's header no longer links to it; the menu does, in every view.
    assert "Ver último dato por canal" not in [link.proto.label for link in app.main.get("page_link")]
    script = (
        f"import sys\nsys.path.insert(0, {str(ROOT)!r})\nimport pandas as pd\nfrom bi import dashboard\n"
        "from tests.test_channel_latest import sample\n"
        # AppTest runs in this process: the sample is put back at the end and the channel caches are emptied,
        # or the next tests read the sample instead of the database.
        "SAVED = dashboard.read_latest_by_source\n"
        "dashboard.read_latest_by_source = lambda version: sample()\n"
        "try:\n"
        "    dashboard.render_page(dashboard.PAGE_CHANNELS)\n"
        "finally:\n"
        "    dashboard.read_latest_by_source = SAVED\n"
        "    for cached in (dashboard.read_channel_frame, dashboard.read_channel_national_prices,\n"
        "                   dashboard.read_channel_week_snapshot, dashboard.read_cached_all_variations_in):\n"
        "        cached.clear()\n"
    )
    page = AppTest.from_string(script, default_timeout=90).run()
    assert not page.exception
    text = " ".join(block.value for block in page.markdown)
    assert text.count('<a class="ch-card"') == 2  # the whole card is the link, one per channel
    assert "canal=Mercado" in text and "canal=Feria+libre" in text
    assert "Semana 12–18 oct" in text and "Semana 19–25 oct" in text  # D-374: each channel's own week
    assert text.count('class="ch-state late"') == 1 and "ODEPA aún no publica la semana 19–25 oct" in text
    assert text.count('class="ch-state ok"') == 1
    # a card opens its channel: its own latest week and its products
    page.query_params["canal"] = "Feria libre"
    page.run()
    assert not page.exception
    detail = " ".join(block.value for block in page.markdown)
    assert 'class="mock-products-table"' in detail and '<a class="ch-card"' not in detail


def test_d404_each_channel_card_says_its_week_prices_change_and_state():
    cards = {card["channel"]: card for card in channel_latest.channel_cards(sample())}
    assert [card["source"] for card in channel_latest.channel_cards(sample())] == ["wholesale", "consumer"]
    feria, mercado = cards["Feria libre"], cards["Mercado"]
    assert (feria["week"], feria["before"], feria["prices"], feria["late"]) == ("2026-10-19", "2026-10-12", 2, None)
    assert mercado["week"] == "2026-10-12" and mercado["late"] == "2026-10-19"  # behind the newest week published
    assert feria["median"] == pytest.approx(0.1) and feria["families"] == ["Frutas"]


def test_d365_the_table_is_served_and_documented():
    from etl import pipeline

    assert "latest_by_source" in pipeline.SERVING_TABLES
    model = (ROOT / "dbt" / "models" / "marts" / "latest_by_source.sql").read_text(encoding="utf-8")
    assert (
        "row_number() over (partition by source order by week_start desc) <= 2" in model
        and "int_prices__weekly" in model
    )
    assert "### latest_by_source" in i18n.document_path("SAD.md", "es").read_text(encoding="utf-8")
    assert dashboard.PAGE_CHANNELS in next(pages for key, _, pages in dashboard.MENU_BLOCKS if key == "negocio")


def test_d380_the_channel_page_hands_its_scope_in_spanish_so_the_sentences_translate_whole():
    import inspect

    from bi import dashboard

    source = inspect.getsource(dashboard.show_channels_page)
    # A scope translated before drawing («all of Chile») leaves «…mediana de 51 precios comparables · all of Chile»
    # half in each language; the page translates whole sentences, as the Panorama's does.
    assert 'tr("todo Chile")' not in source
    # D-405: a channel page is drawn by the Panorama itself, which hands its scope in Spanish and translates whole.
    assert "show_market_overview(mode" in inspect.getsource(dashboard.show_channel_detail)


needs_database = pytest.mark.skipif(not dashboard.queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")


@needs_database
def test_d405_a_channel_page_is_the_panorama_with_that_channel_and_the_panorama_keeps_its_own():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.query_params.update({"vista": dashboard.PAGE_CHANNELS, "canal": "Feria libre"})
    app.run()
    assert not app.exception
    page = " ".join(block.value for block in app.markdown)
    assert "Último dato por canal › </span><b>Feria libre</b>" in page  # the path names the channel
    assert 'class="mock-products-table"' in page and "mock-movement" in page  # the Panorama's own panels
    channels = set(re.findall(r'</td><td>([^<]+)</td><td class="num">', page))
    assert channels == {"Feria libre"}, channels  # only that channel's products
    # the Panorama, opened right after in the same visit, keeps all its channels and its own state
    app.query_params.clear()
    app.query_params.update({"vista": dashboard.HOME_PAGE})
    app.run()
    assert not app.exception
    panorama = " ".join(block.value for block in app.markdown)
    assert "Último dato por canal ›" not in panorama


@needs_database
def test_d405_in_the_common_week_a_channel_has_the_same_national_prices_as_the_panorama():
    from bi import queries

    version = dashboard.get_database_version()
    channel = "Supermercado"
    own = dashboard.read_channel_national_prices(version, channel)
    week = own["week_start"].max()
    mine = own[own["week_start"] == week].set_index(dashboard.NATIONAL_KEY[1:])["national_price"]
    panorama = queries.run_query("k6_national_weekly_price")
    panorama = panorama[(panorama["week_start"] == f"{week:%Y-%m-%d}") & (panorama["channel"] == channel)]
    if panorama.empty:
        pytest.skip("the channel's own week is not the common week yet")
    theirs = panorama.set_index(dashboard.NATIONAL_KEY[1:])["national_price"]
    assert len(mine) == len(theirs)
    assert mine.sort_index().values == pytest.approx(theirs.sort_index().values)


def test_d406_the_cards_share_one_scale_and_say_their_coverage():
    cards = channel_latest.channel_cards(sample())
    markup = dashboard.build_channel_cards_html(cards, lambda channel: f"?canal={channel}", total_families=3)
    widths = re.findall(r'class="ch-bar"[^>]*><i class="[^"]*" style="[^"]*width:([\d.]+)%', markup)
    assert len(widths) == 2 and max(float(width) for width in widths) == 50.0  # the largest change fills its half
    assert markup.count("1 de 3 familias") == 2  # each covers one family of three
    assert dashboard.bar_style(-0.05, 0.1) == "left:25.0%;width:25.0%" and dashboard.bar_style(None, 1) == "width:0"


@needs_database
def test_d406_a_channel_that_covers_some_families_says_which_read_from_the_data():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.query_params.update({"vista": dashboard.PAGE_CHANNELS, "canal": "Panadería"})
    app.run()
    assert not app.exception
    captions = " ".join(caption.value for caption in app.caption)
    assert "Este canal publica 1 de las 7 familias: Pan." in captions


def test_d406_a_card_keeps_the_view_and_the_steps_of_a_channel_do_not_reload_the_page():
    # A card reloads the page like a document of the folder does: the view is kept once (D-357), never the author.
    assert "a.ch-card" in dashboard.PROFILE_KEEPER_JS
    # The map and family links of a channel page point to that same page: they are captured, not followed.
    assert (
        "params.get('vista') === here.get('vista') && params.get('canal') === here.get('canal')"
        in dashboard.HOME_LINKS_JS
    )


@needs_database
def test_d408_a_channel_folds_its_steps_like_the_panorama():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.session_state["home_region_done@Feria libre"] = True
    app.session_state["home_family_done@Feria libre"] = True
    app.query_params.update({"vista": dashboard.PAGE_CHANNELS, "canal": "Feria libre", "familia": "Frutas"})
    app.run()
    assert not app.exception
    page = " ".join(block.value for block in app.markdown)
    assert '<span>Familia</span><strong>Frutas</strong>' in page and 'class="mock-chile-map"' not in page
    app.button(key="home_change_region").click().run()  # the state of the channel, never the Panorama's
    assert app.session_state["home_expanded@Feria libre"] and "home_expanded" not in app.session_state
