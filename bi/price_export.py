"""D-509: the prices of step 4 as a file to work with, in Excel or in CSV.

The file holds every filtered price, not only the rows in sight, and reads in the language of the visit: headings,
families, channels and the notes. A product keeps the name ODEPA publishes, as every figure of the panel does.
"""

from __future__ import annotations

import csv
import io
import math
import unicodedata
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from bi import data_terms, home_mockup, i18n

SHEET_DATA, SHEET_NOTES = "Datos", "Notas"
# One column per question a BI tool asks of a price: what it is, where it is sold, what it cost and how it moved.
COLUMNS: tuple[tuple[str, str], ...] = (
    ("Familia", "text"),
    ("Producto", "text"),
    ("Variedad", "text"),
    ("Calidad", "text"),
    ("Canal", "text"),
    ("Unidad", "text"),
    ("Envase comparado", "text"),  # D-522: why this price can differ from the one in «Consultas SQL»
    ("Alcance", "text"),
    ("Semana anterior", "week"),
    ("Precio anterior", "money"),
    ("Semana", "week"),
    ("Precio", "money"),
    ("Variación", "percent"),
    ("Regiones al alza", "count"),
    ("Regiones a la baja", "count"),
    ("Una sola cotización", "text"),
)
MONEY_FORMAT = '"$"#,##0'
PERCENT_FORMAT = "+0.0 %;-0.0 %;0.0 %"


def tr(text: str) -> str:
    """The text in the language of the visit; the dictionaries of the app, never a translation of our own."""
    return i18n.tr(text)


def _prices(row: dict[str, Any]) -> tuple[float | None, float | None]:
    """The two prices the table shows: the same regions in both weeks when there are any (D-327)."""
    before, now = row.get("_same_before"), row.get("_same_now")
    like_for_like = all(
        value is not None and math.isfinite(float(value)) and float(value) > 0 for value in (before, now)
    )
    if like_for_like:
        return float(before), float(now)
    return home_mockup.previous_price(row), float(row["national_price"])


def build_rows(rows, week_label, previous_label, scope):
    """One list per price, in the order the table shows them and with its own figures, not a text of the table."""
    built = []
    for row in rows:
        before, now = _prices(row)
        regions = row.get("_regions") or (None, None)
        built.append(
            [
                data_terms.term(row.get("product_group")),
                row.get("product"),  # as ODEPA publishes it, in any language
                row.get("variety"),
                data_terms.term(row.get("quality")),
                data_terms.term(row.get("channel")),
                data_terms.term(row.get("normalized_unit")),
                home_mockup.package_label(row.get("_packages")),
                scope,
                previous_label,
                before,
                week_label,
                now,
                row.get("variation"),
                regions[0],
                regions[1],
                tr("Sí") if row.get("_single_quote") else "",
            ]
        )
    return built


def build_notes(week_label, filters, updated, model, published=None):
    """What the file is and what it leaves out, so a figure can be traced without the panel."""
    missing = (model or {}).get("missing")
    notes = [
        (tr("Semana"), week_label),
        *[(tr(label), value) for label, value in filters],
        (tr("Fecha de la carga"), updated),
        (
            tr("Fuente"),
            tr("ODEPA, Oficina de Estudios y Políticas Agrarias, Ministerio de Agricultura de Chile"),
        ),
        (tr("Licencia"), tr("Creative Commons Atribución: se puede reutilizar citando la fuente")),
        (
            tr("Cálculo de la variación"),
            tr(
                "Cada variación compara las mismas regiones y el mismo envase en ambas semanas; un precio que falta en una de las dos "
                "queda fuera, sin rellenar."
            ),
        ),
    ]
    if published:
        notes.append((tr("Regiones que publica la fuente"), published))
    if missing is not None:
        notes.append((tr("Precios sin comparación válida"), missing))
    notes.append(
        (
            tr("Precios nominales"),
            tr("Precios de ODEPA sin ajustar por inflación, redondeados; el cambio se calcula antes de redondear."),
        )
    )
    return notes


def build_csv(built):
    """The same table, UTF-8 with a BOM so Excel opens it with its accents in place."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow([tr(name) for name, _ in COLUMNS])
    for values in built:
        writer.writerow(["" if value is None else value for value in values])
    return buffer.getvalue().encode("utf-8-sig")


def _write_data_sheet(sheet, built):
    sheet.append([tr(name) for name, _ in COLUMNS])
    for values in built:
        sheet.append(values)
    widths = [len(tr(name)) + 4 for name, _ in COLUMNS]
    for index, (_, kind) in enumerate(COLUMNS, start=1):
        letter = get_column_letter(index)
        for cell in sheet[letter][1:]:
            if kind == "money":
                cell.number_format = MONEY_FORMAT
            elif kind == "percent":
                cell.number_format = PERCENT_FORMAT
            elif kind == "count":
                cell.number_format = "0"
            widths[index - 1] = max(widths[index - 1], min(38, len(str(cell.value or "")) + 2))
        sheet.column_dimensions[letter].width = widths[index - 1]
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(vertical="center")
    sheet.freeze_panes = "A2"  # the heading stays while the rows scroll
    if built:
        # An Excel Table: it carries the autofilter and lets a BI tool read the range by name.
        reference = f"A1:{get_column_letter(len(COLUMNS))}{len(built) + 1}"
        table = Table(displayName="Precios", ref=reference)
        table.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
        sheet.add_table(table)
    else:
        sheet.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}1"


def _write_notes_sheet(sheet, notes):
    sheet.append([tr("Nota"), tr("Detalle")])
    for label, value in notes:
        sheet.append([label, value])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    sheet.column_dimensions["A"].width = 34
    sheet.column_dimensions["B"].width = 96
    for row in sheet.iter_rows(min_row=2, min_col=2, max_col=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_workbook(built, notes):
    """The whole file: «Datos», a table with its autofilter and its formats, and «Notas», what it is and what it leaves
    out. No merged cells: a merged cell breaks a filter and a pivot table."""
    book = Workbook()
    data = book.active
    data.title = tr(SHEET_DATA)
    _write_data_sheet(data, [list(values) for values in built])
    _write_notes_sheet(book.create_sheet(tr(SHEET_NOTES)), notes)
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def build_name(week, scope, extension):
    """«greenocean-precios-2026-10-26-todo-chile.xlsx»: the week and the scope, so two files never read alike."""
    pieces = [str(part) for part in ("greenocean", tr("precios"), week, scope) if part]
    plain = unicodedata.normalize("NFD", "-".join(pieces).lower())
    plain = "".join(letter for letter in plain if unicodedata.category(letter) != "Mn")
    name = "".join(letter if letter.isalnum() or letter == "-" else "-" for letter in plain)
    while "--" in name:
        name = name.replace("--", "-")
    return f"{name.strip('-')}.{extension}"
