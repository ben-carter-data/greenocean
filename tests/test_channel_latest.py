"""«Último dato por canal» (D-365): each source with its own latest week, its change by family and its products."""

from pathlib import Path

import duckdb
import pandas as pd
import re

import pytest
from streamlit.testing.v1 import AppTest

from bi import channel_latest, dashboard, home_mockup, i18n

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
    # D-494: the page left the menu; its channels are step 2 of «Semanal», and its old address opens it
    assert dashboard.PAGE_CHANNELS not in next(pages for key, _, pages in dashboard.MENU_BLOCKS if key == "negocio")
    assert dashboard.RETIRED_VIEWS[dashboard.PAGE_CHANNELS] == dashboard.HOME_PAGE


needs_database = pytest.mark.skipif(not dashboard.queries.DATABASE_FILE.exists(), reason="datos.duckdb is not here")


@needs_database
def test_d405_a_channel_page_is_the_panorama_with_that_channel_and_the_panorama_keeps_its_own():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    # D-494: an old address of the channel page opens «Semanal» with that channel chosen in step 2
    app.query_params.update({"vista": dashboard.PAGE_CHANNELS, "canal": "Feria libre"})
    app.run()
    assert not app.exception
    page = " ".join(block.value for block in app.markdown)
    assert "Semanal › </span><b>Feria libre</b>" in page  # the path names the channel
    assert re.search(r'class="mock-channel-row mock-channel-tile \w+ selected"', page)  # its block, lit
    assert 'class="mock-products-table"' in page and "mock-movement" in page  # the Dashboard's own panels
    channels = set(re.findall(r'</td><td>([^<]+)</td><td class="num">', page))
    assert channels == {"Feria libre"}, channels  # only that channel's products
    # the Dashboard, opened right after in the same visit, keeps all its channels and its own state
    app.query_params.clear()
    app.query_params.update({"vista": dashboard.HOME_PAGE})
    app.run()
    assert not app.exception
    panorama = " ".join(block.value for block in app.markdown)
    assert "Semanal › </span>" not in panorama and 'class="mock-channel-row selected"' in panorama  # «Todos»


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


@needs_database
def test_d494_what_a_channel_holds_is_said_under_its_name_and_matches_the_data():
    from bi import data_terms

    with duckdb.connect(str(dashboard.queries.DATABASE_FILE), read_only=True) as connection:
        frame = connection.execute("SELECT channel, product_group, product FROM latest_by_source").df()
    families = frame.groupby("channel")["product_group"].agg(set).to_dict()
    # what each label says is what ODEPA publishes in that channel
    assert families["Mayorista"] == {"Frutas", "Hortalizas"}
    pulses = frame[frame["channel"] == "Mercado Mayorista"]
    assert set(pulses["product_group"]) == {"Abarrotes y otros"}
    assert all(re.match(r"(Poroto|Lenteja|Garbanzo|Arveja)", name) for name in pulses["product"])
    assert families["Carnicería"] <= {"Carne bovina", "Carne de Cerdo - Ave - Cordero"}
    assert families["Panadería"] == {"Pan"}
    # a channel without a label sells several families
    for channel, found in families.items():
        assert channel in data_terms.CHANNEL_CONTENTS or len(found) >= 3, channel
    assert data_terms.channel_content("Mayorista") == "frutas y hortalizas"
    assert data_terms.channel_content("Supermercado") is None


@needs_database
def test_d406_a_channel_that_covers_some_families_says_which_read_from_the_data():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.query_params.update({"vista": dashboard.PAGE_CHANNELS, "canal": "Panadería"})
    app.run()
    assert not app.exception
    captions = " ".join(caption.value for caption in app.caption)
    assert "Este canal publica 1 de las 7 familias: Pan." in captions


def test_d494_a_channel_is_chosen_in_place_like_a_region_or_a_family():
    # The links of step 2 point to «Semanal» itself, whatever the channel: they are captured, not followed.
    assert "const samePage = params.get('vista') === here.get('vista');" in dashboard.HOME_LINKS_JS
    assert "canal" in dashboard.HOME_LINK_PARAMETERS
    cards = channel_latest.channel_cards(sample())
    markup = home_mockup.channel_list(cards, lambda c: f"?canal={c}", "Feria libre", "?", lambda c: "", step=2)
    assert markup.count('class="mock-channel-row') == len(cards) + 1  # «Todos los canales» first
    assert "2</b><span>Elige un canal" in markup and 'href="?canal=Feria libre"' in markup
    assert "Opcional: sin elegir, se ven todos." in markup  # it says it is never required
    assert re.search(r'class="mock-channel-row mock-channel-tile \w+ selected" href="\?canal=Feria libre"', markup)
    assert "+10,0 %" in markup  # the median change of its card (D-404)


@needs_database
def test_d452_a_channel_behaves_exactly_like_the_dashboard_and_never_folds():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.session_state["visitor_profile"] = "profesional"
    app.session_state["home_region_done@Feria libre"] = True
    app.session_state["home_family_done@Feria libre"] = True
    app.query_params.update({"vista": dashboard.PAGE_CHANNELS, "canal": "Feria libre", "familia": "Frutas"})
    app.run()
    assert not app.exception
    page = " ".join(block.value for block in app.markdown)
    assert 'class="mock-chile-map"' in page and "mock-movement-row rise selected" in page  # the map and the families
    assert 'class="mock-chosen"' not in page and 'class="mock-products-table"' in page
    assert not {"home_change_region", "home_change_family"} & {str(button.key) for button in app.button}


def test_d453_each_channel_card_has_its_own_3d_icon_in_its_own_colours():
    from bi import channel_icons

    channels = [
        "Mayorista",
        "Supermercado",
        "Feria libre",
        "Carnicería",
        "Supermercado en Línea",
        "Mercado Minorista",
        "Panadería",
        "Mercado Mayorista",
    ]
    assert set(channels) <= set(channel_icons.ICONS)
    drawings = [channel_icons.svg(channel) for channel in channels]
    assert len(set(drawings)) == len(channels)  # one drawing each
    for drawing in drawings:
        assert "<linearGradient" in drawing and 'opacity=".22"' in drawing  # the 3D shading and the floor shadow
    first_colours = [re.search(r'stop-color="(#[0-9a-f]{6})"', drawing)[1] for drawing in drawings]
    assert len(set(first_colours)) == len(channels)  # each in its own colours
    assert channel_icons.svg("Otro canal") == channel_icons.svg("Otro")  # a channel added later still gets a mark
    image = channel_icons.image("Panadería")
    assert image.startswith('<img class="ch-icon" src="data:image/svg+xml;base64,') and 'alt=""' in image
    cards = [
        {
            "channel": "Panadería",
            "source": "consumer",
            "week": "2026-10-26",
            "median": 0.008,
            "prices": 45,
            "compared": 40,
            "families": ["Pan"],
            "late": None,
        }
    ]
    markup = home_mockup.channel_list(cards, lambda c: "#", None, "#", lambda c: channel_icons.image(c, 20), step=2)
    assert '<img class="ch-icon"' in markup and ">pan</small>" in markup  # D-494: its icon, and what it holds
