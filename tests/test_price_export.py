"""D-509: «Descargar» in step 4 gives every filtered price as an Excel table or a CSV, in the language of the visit."""

import csv
import io
from pathlib import Path

import pytest
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest

from bi import dashboard, i18n, price_export, queries

# region Variables
DASHBOARD_FILE = str(Path(__file__).resolve().parents[1] / "bi" / "dashboard.py")
needs_database = pytest.mark.skipif(not queries.DATABASE_FILE.exists(), reason="Requires real database")
ROWS = [
    {
        "product_group": "Frutas",
        "product": "Kiwi",
        "variety": "Hayward",
        "quality": "Especial",
        "channel": "Mayorista",
        "normalized_unit": "kilo",
        "national_price": 2008.0,
        "_same_before": 1598.0,
        "_same_now": 2008.0,
        "variation": 0.2565,
        "_regions": (3, 0, []),
        "_single_quote": False,
    },
    {
        "product_group": "Hortalizas",
        "product": "Lechuga",
        "variety": "Escarola",
        "quality": "Primera",
        "channel": "Feria libre",
        "normalized_unit": "unidad",
        "national_price": 790.0,
        "_previous_price": 820.0,
        "variation": -0.0366,
        "_regions": None,
        "_single_quote": True,
    },
]
WINDOW_SCRIPT = (
    "import streamlit as st\n"
    "from bi import dashboard\n"
    "st.session_state['dialog_products_search'] = 'lechuga'\n"
    "week = dashboard.read_cached_filter_options(dashboard.get_database_version())['week'][0]\n"
    f"rows = {ROWS!r}\n"
    "model = {'week_label': '26 oct – 1 nov', 'previous_label': '19–25 oct'}\n"
    "dashboard.draw_products_window('Frutas', 0.005, 'todo Chile', rows, week, model, None, None, '', '3 nov · 16:19')\n"
)
# endregion


# region Price export
def build():
    rows = price_export.build_rows(ROWS, "26 oct – 1 nov", "19–25 oct", "todo Chile")
    notes = price_export.build_notes("26 oct – 1 nov", [("Región", "Todo Chile")], "3 nov · 16:19", {"missing": 145}, 9)
    return rows, notes


def test_d509_the_rows_carry_the_figures_of_the_table_and_the_name_odepa_publishes():
    rows, _ = build()
    assert [row[1] for row in rows] == ["Kiwi", "Lechuga"]  # the product as ODEPA writes it
    kiwi, lettuce = rows
    assert kiwi[6] == ""  # D-522: without a package named, the column stays empty
    assert kiwi[9:13] == [1598.0, "26 oct – 1 nov", 2008.0, 0.2565]  # the same-region prices the table shows
    assert lettuce[9] == 820.0 and lettuce[11] == 790.0  # without same regions, the previous and the national
    assert kiwi[13:15] == [3, 0] and lettuce[13:15] == [None, None]
    assert kiwi[15] == "" and lettuce[15] == "Sí"
    assert len(kiwi) == len(price_export.COLUMNS)


def test_d509_the_workbook_is_a_table_with_its_filter_its_formats_and_its_notes_and_no_merged_cell():
    rows, notes = build()
    book = load_workbook(io.BytesIO(price_export.build_workbook(rows, notes)))
    assert book.sheetnames == ["Datos", "Notas"]
    data = book["Datos"]
    assert data.freeze_panes == "A2"
    assert list(data.tables) == ["Precios"] and data.tables["Precios"].ref == "A1:P3"
    assert data.tables["Precios"].autoFilter is not None
    assert not data.merged_cells.ranges and not book["Notas"].merged_cells.ranges
    headings = [cell.value for cell in data[1]]
    assert headings == [name for name, _ in price_export.COLUMNS]
    assert (
        data["J2"].number_format == price_export.MONEY_FORMAT and data["L2"].number_format == price_export.MONEY_FORMAT
    )
    assert data["M2"].number_format == price_export.PERCENT_FORMAT and data["M2"].value == 0.2565
    assert data["N2"].number_format == "0" and data["N2"].value == 3
    labels = [row[0].value for row in book["Notas"].iter_rows(min_row=2)]
    assert labels[:2] == ["Semana", "Región"]
    for needle in (
        "Fecha de la carga",
        "Fuente",
        "Licencia",
        "Cálculo de la variación",
        "Precios sin comparación válida",
    ):
        assert needle in labels
    assert book["Notas"]["B2"].value == "26 oct – 1 nov"
    assert any("145" in str(row[1].value) for row in book["Notas"].iter_rows(min_row=2))


def test_d509_the_csv_is_the_same_table_in_utf8_with_a_bom():
    rows, _ = build()
    raw = price_export.build_csv(rows)
    assert raw.startswith(b"\xef\xbb\xbf")
    lines = list(csv.reader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
    assert lines[0] == [name for name, _ in price_export.COLUMNS]
    assert lines[1][1] == "Kiwi" and lines[1][12] == "0.2565" and lines[2][15] == "Sí"
    assert len(lines) == 3


def test_d509_the_file_reads_in_english_except_the_product(monkeypatch):
    monkeypatch.setattr(i18n, "is_english", lambda: True)
    rows, notes = build()
    book = load_workbook(io.BytesIO(price_export.build_workbook(rows, notes)))
    assert book.sheetnames == ["Data", "Notes"]
    assert [cell.value for cell in book["Data"][1]][:3] == ["Family", "Product", "Variety"]
    assert book["Data"]["A2"].value == "Fruit" and book["Data"]["B2"].value == "Kiwi"
    assert book["Data"]["E2"].value == "Wholesale" and book["Data"]["P3"].value == "Yes"
    assert book["Notes"]["A2"].value == "Week" and book["Notes"]["A3"].value == "Region"
    assert price_export.build_name("2026-10-26", "todo Chile", "csv") == "greenocean-prices-2026-10-26-todo-chile.csv"


def test_d509_the_name_of_the_file_says_the_week_and_the_scope():
    assert (
        price_export.build_name("2026-10-26", "Región de Ñuble", "xlsx")
        == "greenocean-precios-2026-10-26-region-de-nuble.xlsx"
    )


def test_d522_the_file_names_the_package_each_price_compares():
    row = {**ROWS[0], "_packages": "$/bandeja 10 kilos · $/kilo (en bins de 450 kilos)"}
    built = price_export.build_rows([row], "26 oct – 1 nov", "19–25 oct", "todo Chile")[0]
    assert built[6] == "bandeja 10 kilos · kilo (en bins de 450 kilos)"
    assert price_export.COLUMNS[6][0] == "Envase comparado"
    assert "bandeja 10 kilos" in price_export.build_csv([built]).decode("utf-8-sig")


def test_d509_every_text_of_the_file_has_its_english():
    from tests import code_shape

    shown = [
        code_shape.literal(call.args[0]) for call in code_shape.calls_named(code_shape.tree_of(price_export), "tr")
    ]
    for text in filter(None, shown):
        assert text in i18n.EN, text
    for name, _ in price_export.COLUMNS:
        assert name in i18n.EN, name


@needs_database
def test_d509_the_panel_and_the_window_offer_the_download_with_every_filtered_price():
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PUBLIC
    app.query_params.update({"_home_region": dashboard.ALL_VALUES, "familia": "Frutas"})
    app.session_state[dashboard.scoped(dashboard.HOME_REGION_DONE)] = True
    app.session_state[dashboard.scoped(dashboard.HOME_FAMILY_DONE)] = True  # D-530: the address alone unlocks nothing
    app.run()
    assert not app.exception
    keys = {str(button.key) for button in app.get("download_button")}
    assert {"home_download_xlsx", "home_download_csv"} <= keys
    # every filtered price travels, not only the rows in sight: the caption counts them
    caption = next(c.value for c in app.caption if "precios, con los filtros" in c.value)
    count = int(caption.split(" ")[0].replace(".", ""))
    assert count > 20
    # the window carries its own copy of the menu
    app.button(key="home_products_enlarge").click().run()
    assert not app.exception
    keys = {str(button.key) for button in app.get("download_button")}
    assert {"dialog_download_xlsx", "dialog_download_csv"} <= keys


def counted(app):
    """The counts of the captions «n precios, con los filtros de esta pantalla», in drawing order."""
    return [int(c.value.split(" ")[0].replace(".", "")) for c in app.caption if "precios, con los filtros" in c.value]


def record_notes(monkeypatch, seen):
    """Keep the filters of every file built, so a test can read what its notes say."""
    original = price_export.build_notes
    monkeypatch.setattr(
        price_export, "build_notes", lambda *args, **kwargs: seen.append(list(args[1])) or original(*args, **kwargs)
    )


def alert_family(week):
    """The family with the most sharp rises in the week, so the test never depends on one family's luck."""
    sharp = dashboard.home_alert_rows(week, dashboard.ALL_VALUES, direction=dashboard.RISE)
    if sharp.empty:
        pytest.skip("no sharp rise this week")
    return sharp["product_group"].value_counts().index[0]


@needs_database
def test_d525_with_an_alert_chosen_the_file_carries_the_rows_of_the_alerts_table():
    week = dashboard.read_cached_filter_options(dashboard.get_database_version())["week"][0]
    family = alert_family(week)
    sharp = dashboard.home_alert_rows(week, family, direction=dashboard.RISE)
    rows = dashboard.alert_download_rows(week, family, dashboard.RISE, "", None, [])
    assert len(rows) == len(sharp) > 0
    for row, (_, alert) in zip(rows, sharp.iterrows()):
        assert [row[f] for f in ("product", "variety", "channel")] == [
            alert[f] for f in ("product", "variety", "channel")
        ]
        assert (row["_same_before"], row["_same_now"]) == dashboard.alert_prices(alert)  # the table's two prices
        assert row["variation"] == alert["variation"] and not row["_single_quote"]
    built = price_export.build_rows(rows, "26 oct – 1 nov", "19–25 oct", "todo Chile")
    assert [values[11] for values in built] == [row["_same_now"] for row in rows]
    # the search looks only among the alerts, as the table does
    name = rows[0]["product"]
    searched = dashboard.alert_download_rows(week, family, dashboard.RISE, name, None, [])
    assert searched and all(dashboard.matches_product_search(row, name) for row in searched)
    # the package compared travels from the family row of the same product (D-522)
    key = queries.KEY_COLUMNS + ["channel"]
    family_row = {**{field: rows[0][field] for field in key}, "_packages": "$/caja 10 kilos"}
    with_package = dashboard.alert_download_rows(week, family, dashboard.RISE, "", None, [family_row])
    assert with_package[0]["_packages"] == "$/caja 10 kilos"


@needs_database
def test_d525_the_panel_and_the_window_download_the_alerts_when_one_is_chosen(monkeypatch):
    seen = []
    record_notes(monkeypatch, seen)
    week = dashboard.read_cached_filter_options(dashboard.get_database_version())["week"][0]
    family = alert_family(week)
    sharp = len(dashboard.home_alert_rows(week, family, direction=dashboard.RISE))
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=90)
    app.session_state[dashboard.PROFILE_STATE] = dashboard.PROFILE_PUBLIC
    app.query_params.update({"_home_region": dashboard.ALL_VALUES, "familia": family, "alerta": dashboard.RISE})
    app.session_state[dashboard.scoped(dashboard.HOME_REGION_DONE)] = True
    app.session_state[dashboard.scoped(dashboard.HOME_FAMILY_DONE)] = True  # D-530: the address alone unlocks nothing
    app.run()
    assert not app.exception
    assert counted(app) == [sharp]  # the alerts, not the whole family
    assert ("Alertas", "Solo alzas fuertes") in seen[-1]
    app.button(key="home_products_enlarge").click().run()
    assert not app.exception and app.get("dialog")
    keys = {str(button.key) for button in app.get("download_button")}
    assert {"dialog_download_xlsx", "dialog_download_csv"} <= keys  # the window offers it with an alert too
    assert counted(app) == [sharp, sharp]
    assert ("Alertas", "Solo alzas fuertes") in seen[-1]


@needs_database
def test_d525_the_window_writes_its_own_choices_in_the_notes(monkeypatch):
    seen = []
    record_notes(monkeypatch, seen)
    app = AppTest.from_string(WINDOW_SCRIPT, default_timeout=90)
    app.run()
    assert not app.exception
    assert app.text_input(key="dialog_products_search").value == "lechuga"
    assert ("Búsqueda", "lechuga") in seen[-1] and ("Familia", "Frutas") in seen[-1]
    assert counted(app) == [1]  # only the lettuce, as the table shows


# endregion
