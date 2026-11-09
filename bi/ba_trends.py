"""«Análisis» (D-456, D-457): the history of food prices, read two ways that never mix. «Mensual» is one
period, the last 12 months or one year, month by month; «Histórico» is the whole history, from January 2022 to the last
month the INE published, year by year. Each chart says which months it shows and, under its title, what each colour
and line means (D-554); on hover it grows and says what it measures and what follows from it, in words computed from
the same figures it draws. Every figure comes from the queries and rules the rest of the panel uses: the monthly index
of «Precios e inflación» (D-163), K1 (the gap) and K6 (the alerts); every definition, from «Método» (overview.KPIS).
Nothing here is typed by hand."""

from __future__ import annotations

import html
import math
from collections.abc import Callable
from functools import partial
from typing import Any

import altair as alt
import pandas as pd

from bi import charts, home_mockup, i18n, inflation_view, interest_map, overview, static_files, weeks

# region Constants
BASKET = inflation_view.BASKET_NAME
IPC = inflation_view.IPC_NAME
BASE = (inflation_view.BASE_YEAR, inflation_view.BASE_MONTH)
LAST_YEAR = "Últimos 12 meses"
PACE = inflation_view.SAME_PACE_POINTS
# D-478: «Mensual» and «Histórico» go down from a family to its products; a product is keyed with this mark in the
# frames' product_group, so its figures are computed exactly as a family's are.
PRODUCT = "producto:"
ALL_PRODUCTS = "Todos los productos"
ZOOM_HEIGHT = 300  # the enlarged chart, in the window its green magnifier opens (D-460)
# D-458: a tile takes the window's height less what is above and below it (the header, the green panel, the tabs, the
# cards and the table), never less than the floor.
TILES_RESERVED, TILES_FLOOR, NARROW_FLOOR = 585, 230, 210  # D-565: the green panel is one line, 18 px less
# D-461: on a low window the charts keep their floor and the table scrolls inside its own box, under the charts.
TABLE_RESERVED, TABLE_FLOOR = 570, 140
# D-556: two typical sizes of change read as «parecido» when the larger is at most this many times the smaller, measured
# as a ratio of prices (a −16,7 % drop is undone by a +20 % rise).
SIMILAR_SIZE = 1.25
# D-556: the share of the chart's height left past the longest bar on each side, for its count.
LABEL_ROOM = 0.18

# One chart of a tab: its title, the months it shows, what it measures, what follows from it, how to draw it at a
# width and a height, and what each colour and line of it means (D-554).
Tile = tuple[str, str, str, str, Callable[..., Any], str]
# D-466: one colour per year in «Cambio de cada año», so each year reads apart; the bar's height says whether it rose.
YEAR_COLORS = ["#5aa9ea", "#5fd39b", "#b49cff", "#f2b05e", "#ef7d8e", "#4dd0e1", "#f48fb1"]
# endregion


# region Words
def say(spanish: str, english: str) -> str:
    """The text in the reader's language; in English, its figures written the English way (31,354 and 3.2 %)."""
    return i18n.localize_figures(english) if i18n.is_english() else spanish


def month_name(month: int) -> str:
    return (weeks.MONTHS_EN if i18n.is_english() else weeks.MONTHS)[month - 1]


def full_month(month: int) -> str:
    """The month's whole name, as a card shows it: Febrero, February."""
    names = list(i18n.FULL_MONTHS.values()) if i18n.is_english() else list(i18n.FULL_MONTHS)
    return names[month - 1].capitalize()


def month_label(pair: tuple[int, int]) -> str:
    return f"{month_name(pair[1])} {pair[0]}"


def next_month(pair: tuple[int, int]) -> tuple[int, int]:
    return (pair[0] + 1, 1) if pair[1] == 12 else (pair[0], pair[1] + 1)


def span(first: tuple[int, int], last: tuple[int, int]) -> str:
    """The months a chart shows: «oct 2025 – sep 2026»."""
    return f"{month_label(first)} – {month_label(last)}"


def compared(start: tuple[int, int], end: tuple[int, int]) -> str:
    """The two months a change compares: «sep 2025 → sep 2026»."""
    return f"{month_label(start)} → {month_label(end)}"


def is_product(name: str) -> bool:
    return isinstance(name, str) and name.startswith(PRODUCT)


def product_name(name: str) -> str:
    """The product's own name, as ODEPA writes it (D-443: data names are never translated)."""
    return name[len(PRODUCT) :]


def family_label(family: str) -> str:
    """The family (or a product, D-478) as a chart or a table names it."""
    if is_product(family):
        return product_name(family)
    return say("Toda la canasta", "The whole basket") if family == BASKET else home_mockup.short_family(family)


def family_name(family: str) -> str:
    """The family inside a sentence: «toda la canasta», «la familia Frutas», «el producto Plátano» (D-478)."""
    if is_product(family):
        return say(f"el producto {product_name(family)}", f"the product {product_name(family)}")
    if family == BASKET:
        return say("toda la canasta", "the whole basket")
    short = home_mockup.short_family(family)
    return say(f"la familia {short}", f"the {short} family")


def definition(name: str) -> str:
    """How a KPI is computed, in the words of «Método», so a hover never says it another way (D-385)."""
    return i18n.translate_text(next(how for kpi, how, _ in overview.KPIS if kpi == name))


def percent(value: float | None) -> str:
    """A change as the panel writes it, +6,1 %; the English layer writes it +6.1 % (D-284)."""
    return "—" if value is None or pd.isna(value) else charts.format_signed_percent(value)


def points(value: float | None) -> str:
    return "—" if value is None or pd.isna(value) else charts.format_signed_percent(value).replace(" %", "") + " pts"


def verdict(gap: float | None) -> str | None:
    """The words of «Precios e inflación»: within ± 2 points, at the pace of inflation."""
    if gap is None or pd.isna(gap):
        return None
    if gap > PACE:
        return say("más que la inflación", "more than inflation")
    if gap < -PACE:
        return say("menos que la inflación", "less than inflation")
    return say("al ritmo de la inflación", "at the pace of inflation")


def against_ipc(figures: dict[str, Any]) -> str:
    """«+6,1 %, 2,2 puntos más que el IPC de alimentos (+3,9 %): más que la inflación»."""
    change, gap, ipc = figures["change"], figures["gap"], figures["ipc"]
    if gap is None or ipc is None:
        return say(f"{percent(change)}, sin IPC que comparar", f"{percent(change)}, with no CPI to compare")
    size = charts.format_percent(abs(gap)).removesuffix(" %")
    if size == "0,0":
        return say(
            f"{percent(change)}, lo mismo que el IPC de alimentos: {verdict(gap)}",
            f"{percent(change)}, the same as the food CPI: {verdict(gap)}",
        )
    more = gap > 0
    return say(
        f"{percent(change)}, {size} puntos {'más' if more else 'menos'} que el IPC de alimentos ({percent(ipc)}): "
        f"{verdict(gap)}",
        f"{percent(change)}, {size} points {'more' if more else 'less'} than the food CPI ({percent(ipc)}): "
        f"{verdict(gap)}",
    )


def list_words(items: list[str]) -> str:
    """«Frutas y Hortalizas», «Fruit and Vegetables»."""
    if len(items) < 2:
        return "".join(items)
    return f"{', '.join(items[:-1])} {say('y', 'and')} {items[-1]}"


# endregion


# region Period
def periods(last: tuple[int, int]) -> list[str]:
    """The periods of «Mensual»: the last 12 months and each year, the latest first. The whole history is «Histórico»."""
    return [LAST_YEAR] + [str(year) for year in range(last[0], BASE[0] - 1, -1)]


def bounds(period: str, last: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    """(start, end) months of a period. A change is measured from start to end, as «Precios e inflación» does: the last
    12 months from the same month a year before; a year from the December before, like the INE (2022 from January, the
    base month, and the current year up to the last month published)."""
    if period == LAST_YEAR:
        return (last[0] - 1, last[1]), last
    year = int(period)
    start = (year - 1, 12) if year > BASE[0] else BASE
    return start, (year, 12) if year < last[0] else last


def counted_months(start: tuple[int, int], end: tuple[int, int]) -> tuple[int, int]:
    """(first, last) as year * 100 + month: the months whose weeks a period counts. They are the months after its
    start, and the base month too when the period starts there."""
    first = start if start == BASE else next_month(start)
    return first[0] * 100 + first[1], end[0] * 100 + end[1]


def first_counted(start: tuple[int, int], end: tuple[int, int]) -> tuple[int, int]:
    first = counted_months(start, end)[0]
    return first // 100, first % 100


def add_month_key(frame: pd.DataFrame) -> pd.DataFrame:
    """The weekly rows with the month of their week as year * 100 + month, computed once."""
    stamp = pd.to_datetime(frame["week_start"])
    return frame.assign(month_key=stamp.dt.year * 100 + stamp.dt.month)


def months_between(first: tuple[int, int], last: tuple[int, int]) -> list[tuple[int, int]]:
    """Every month from first to last, both included."""
    months = [first]
    while months[-1] < last:
        months.append(next_month(months[-1]))
    return months


def month_domain(start: tuple[int, int], end: tuple[int, int]) -> list[Any]:
    """The time axis of the price: the whole period, from its start month, even where it has no data. Given in local
    time, like the data: a date written as text («2026-09-01») is read as midnight UTC, the day before in Chile, and
    the last month fell outside the axis without its label (D-457)."""
    return [alt.DateTime(year=year, month=month, date=1) for year, month in (start, end)]


def within(frame: pd.DataFrame, start: tuple[int, int], end: tuple[int, int], family: str) -> pd.DataFrame:
    """The weekly rows of a period and a family (every family for the whole basket)."""
    if frame.empty:
        return frame
    if "month_key" not in frame.columns:
        frame = add_month_key(frame)
    first, last = counted_months(start, end)
    chosen = frame[frame["month_key"].between(first, last)]
    return chosen if family == BASKET else chosen[chosen["product_group"] == family]


# endregion


# region Figures
def monthly_changes(rows: pd.DataFrame, family: str, start: tuple[int, int], end: tuple[int, int]) -> pd.DataFrame:
    """The change of each month of a period against the month before, for the family and for the food IPC, in %. The
    months are those after the start, so chained together they give the change of the whole period; a month without
    an index stays empty, never filled."""
    key = rows["year"] * 100 + rows["month"]
    panel = rows[
        rows["product_group"].isin([family, IPC]) & key.between(start[0] * 100 + start[1], end[0] * 100 + end[1])
    ]
    wide = panel.pivot_table(index=["year", "month"], columns="product_group", values="index")
    wide = wide.reindex(pd.MultiIndex.from_tuples(months_between(start, end), names=["year", "month"]))
    changed = (wide / wide.shift(1) - 1).mul(100).iloc[1:]
    result = pd.DataFrame(
        {
            "year": [pair[0] for pair in changed.index],
            "month": [pair[1] for pair in changed.index],
            "change": changed[family].to_numpy() if family in changed else float("nan"),
            "ipc": changed[IPC].to_numpy() if IPC in changed else float("nan"),
        }
    )
    result["month_start"] = pd.to_datetime(dict(year=result["year"], month=result["month"], day=1))
    return result


def year_note(year: int, last: tuple[int, int]) -> str:
    """What a year's change leaves out: 2022 starts in January (no index before it), the current year ends in the last
    month published."""
    start, end = bounds(str(year), last)
    if start == BASE:
        return say("desde ene", "from Jan")
    if end != (year, 12):
        return say(f"hasta {month_name(end[1])}", f"up to {month_name(end[1])}")
    return ""


def yearly_changes(rows: pd.DataFrame, family: str, last: tuple[int, int]) -> pd.DataFrame:
    """The change of each year, December to December, for the family and for the food IPC; year_note says where a
    year is shorter."""
    found = []
    for year in range(BASE[0], last[0] + 1):
        start, end = bounds(str(year), last)
        found.append(
            {
                "year": str(year),
                "change": inflation_view.change(rows, family, start, end),
                "ipc": inflation_view.change(rows, IPC, start, end),
                "note": year_note(year, last),
            }
        )
    return pd.DataFrame(found).astype({"change": float, "ipc": float})


def typical_size(alert_rows: pd.DataFrame, rise: bool) -> float | None:
    """D-556: the median change in % of the sharp rises (or drops) of a period, or None without any."""
    if alert_rows.empty:
        return None
    changes = alert_rows.loc[alert_rows["variation"] > 0 if rise else alert_rows["variation"] < 0, "variation"]
    return None if changes.empty else float(changes.median() * 100)


def summarize(
    rows: pd.DataFrame,
    alerts_found: pd.DataFrame,
    family: str,
    start: tuple[int, int],
    end: tuple[int, int],
) -> dict[str, Any]:
    """The figures of one family (or the whole basket) in one period."""
    change = inflation_view.change(rows, family, start, end)
    ipc = inflation_view.change(rows, IPC, start, end)
    gap = None if change is None or ipc is None else change - ipc
    alert_rows = within(alerts_found, start, end, family)
    return {
        "family": family,
        "change": change,
        "ipc": ipc,
        "gap": gap,
        "verdict": verdict(gap),
        "alerts": len(alert_rows),
        "rises": int((alert_rows["variation"] > 0).sum()) if not alert_rows.empty else 0,
        "falls": int((alert_rows["variation"] < 0).sum()) if not alert_rows.empty else 0,
        "rise_size": typical_size(alert_rows, rise=True),
        "fall_size": typical_size(alert_rows, rise=False),
        "alert_rows": alert_rows,
    }


def monthly(rows, alerts_found, family, start, end) -> dict[str, Any]:
    """«Mensual»: the figures of the period and the change of each of its months."""
    figures = summarize(rows, alerts_found, family, start, end)
    months = monthly_changes(rows, family, start, end).dropna(subset=["change"])
    figures["months"] = months
    return figures


def history(rows, alerts_found, family, last) -> dict[str, Any]:
    """«Histórico»: the figures from January 2022 to the last month, and the change of each year."""
    figures = summarize(rows, alerts_found, family, BASE, last)
    years = yearly_changes(rows, family, last).dropna(subset=["change"])
    figures["years"] = years
    figures["best"] = None
    figures["above"] = list(years.loc[(years["change"] - years["ipc"]) > PACE, "year"])
    if not years.empty:
        best = years.loc[years["change"].idxmax()]
        figures["best"] = (best["year"], float(best["change"]), best["note"])
    return figures


def families(rows: pd.DataFrame) -> list[str]:
    return sorted(set(rows["product_group"]) - {IPC, BASKET})


def _product_frames_down(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(product_group=PRODUCT + frame["product"])


def product_frames(
    series: pd.DataFrame, ipc: pd.DataFrame, alerts_found: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    """D-478: the frames of «Mensual» and «Histórico» one level down. Each product is keyed PRODUCT + its name, its
    index is the median of its own consumer series against January 2022 (the family's rule), and K6 keeps its rows
    under the product. The last item says the family of every product found in either, so a family's alerts are
    exactly the sum of its products' (a product without an index shows «—», never a guess)."""
    rows, _ = inflation_view.build_family_index(series.assign(product_group=PRODUCT + series["product"]), ipc)

    family_of = {
        PRODUCT + product: family
        for frame in (series, alerts_found)
        for product, family in zip(frame["product"], frame["product_group"])
    }
    return (
        rows,
        _product_frames_down(alerts_found),
        family_of,
    )


def products_of(family_of: dict[str, str], family: str) -> list[str]:
    """The products of a family (every product for the whole basket), by name."""
    return sorted((key for key, group in family_of.items() if family == BASKET or group == family), key=product_name)


# endregion


# region Legends
def ipc_label() -> str:
    """The name of the food CPI in a chart and in its legend."""
    return say("IPC de alimentos", "Food CPI")


def alert_kinds() -> tuple[str, str]:
    """The two kinds of sharp change (K6), as «Semanal» calls them, in their chart and in its legend."""
    return say("Alzas fuertes", "Sharp rises"), say("Bajas fuertes", "Sharp drops")


def series_color(family: str, palette: dict[str, str]) -> str:
    """The colour of the line of a family, the basket or a product: the same in its chart and in its legend."""
    return inflation_view.FAMILY_COLORS.get(family, palette["accent"])


def year_swatch(count: int) -> str:
    """The colours of the first `count` years side by side (D-466), for the legend of «Cambio de cada año»."""
    colors = YEAR_COLORS[: max(count, 1)]
    step = 100 / len(colors)
    stops = ", ".join(f"{color} {index * step:.0f}% {(index + 1) * step:.0f}%" for index, color in enumerate(colors))
    return f"linear-gradient(90deg, {stops})"


def legend(keys: list[tuple[str, str, str]]) -> str:
    """D-554: what each colour and line of a chart means, under its title: (mark, colour, label) for each key. The mark
    is drawn as in the chart: «box» a bar, «line» a line, «dash» a dashed line, «tick» the short line of the IPC."""
    items = "".join(
        f'<span class="ba-key"><i class="ba-mark {mark}" style="--key-color:{color}"></i>{html.escape(label)}</span>'
        for mark, color, label in keys
    )
    return f'<span class="ba-legend">{items}</span>'


# endregion


# region Tiles
def trend_tile(rows, figures, start, end, mode, title: str, since: str) -> Tile:
    name, palette = family_name(figures["family"]), charts.get_palette(mode)
    return (
        title,
        say(
            f"{span(start, end)} · base {month_label(start)} = 100",
            f"{span(start, end)} · base {month_label(start)} = 100",
        ),
        say(
            f"El índice de precios de {name} cada mes, con {month_label(start)} = 100, frente al IPC de alimentos del "
            "INE (línea punteada). Es la mediana de las series de consumidor de ODEPA con precio en enero 2022 y en el "
            "último mes, cada una frente a su precio de enero 2022.",
            f"The price index of {name} each month, with {month_label(start)} = 100, against the INE food CPI (dashed "
            "line). It is the median of ODEPA's consumer series priced in January 2022 and in the last month, each "
            "against its January 2022 price.",
        ),
        "—"
        if figures["change"] is None
        else say(
            f"{since[:1].upper()}{since[1:]} cambió {against_ipc(figures)}.",
            f"{since[:1].upper()}{since[1:]} it changed {against_ipc(figures)}.",
        ),
        partial(trend_chart, rows, figures["family"], start, end, mode),
        legend(
            [
                ("line", series_color(figures["family"], palette), family_label(figures["family"])),
                ("dash", palette["strong_text"], ipc_label()),
            ]
        ),
    )


def extremes_verdict(figures: dict[str, Any]) -> str:
    """D-556: what the chart of the sharp changes answers: were there more rises or more drops, and of what size."""
    rises, falls, up, down = figures["rises"], figures["falls"], figures["rise_size"], figures["fall_size"]
    if not rises and not falls:
        return say("Ningún cambio fuerte en el período.", "No sharp change in the period.")
    more = (
        say("hubo más alzas que bajas", "there were more rises than drops")
        if rises > falls
        else say("hubo más bajas que alzas", "there were more drops than rises")
        if falls > rises
        else say("hubo tantas alzas como bajas", "there were as many rises as drops")
    )
    counted = say(
        f"{charts.format_thousands(rises)} alzas fuertes y {charts.format_thousands(falls)} bajas fuertes: {more}.",
        f"{charts.format_thousands(rises)} sharp rises and {charts.format_thousands(falls)} sharp drops: {more}.",
    )
    if up is None or down is None:
        return counted
    lift, sink = math.log(1 + up / 100), -math.log(1 + down / 100)
    size = (
        say("de tamaño parecido", "of a similar size")
        if max(lift, sink) <= SIMILAR_SIZE * min(lift, sink)
        else say("las alzas, más grandes", "the rises, larger")
        if lift > sink
        else say("las bajas, más grandes", "the drops, larger")
    )
    return counted + say(
        f" Típicas: {percent(up)} y {percent(down)}, {size}.", f" Typical: {percent(up)} and {percent(down)}, {size}."
    )


def monthly_tiles(rows, figures: dict[str, Any], start, end, mode: str) -> list[Tile]:
    """The two charts of «Mensual» (D-556): the price against the food CPI, and the sharp rises and drops of each month."""
    name, palette, (rises, falls) = family_name(figures["family"]), charts.get_palette(mode), alert_kinds()
    first_week = first_counted(start, end)
    first_change = (
        say(
            " El primer cambio fuerte posible es de abril 2022: necesita 12 semanas previas.",
            " The first possible sharp change is from April 2022: it needs 12 previous weeks.",
        )
        if start == BASE
        else ""
    )
    return [
        trend_tile(
            rows,
            figures,
            start,
            end,
            mode,
            say("Precio mes a mes", "Price month by month"),
            say(f"de {month_label(start)} a {month_label(end)}", f"from {month_label(start)} to {month_label(end)}"),
        ),
        (
            say("Alzas y bajas fuertes", "Sharp rises and drops"),
            say(
                f"{span(first_week, end)} · cuántas hubo cada mes (K6)",
                f"{span(first_week, end)} · how many each month (K6)",
            ),
            say(
                f"Cuántos precios de {name} cambiaron fuera de su rango habitual cada mes (K6): las alzas fuertes hacia "
                "arriba y las bajas fuertes hacia abajo. Cada una nace en una semana en que el precio se alejó de sus 12 "
                f"semanas previas; la barra suma las de ese mes.{first_change}",
                f"How many prices of {name} changed outside their usual range each month (K6): the sharp rises upwards "
                "and the sharp drops downwards. Each one is born in a week in which the price moved away from its 12 "
                f"previous weeks; the bar adds up those of that month.{first_change}",
            ),
            extremes_verdict(figures),
            partial(extremes_chart, figures["alert_rows"], start, end, mode),
            legend(
                [
                    ("box", palette["rise"], f"{rises}: {charts.format_thousands(figures['rises'])}"),
                    ("box", palette["fall"], f"{falls}: {charts.format_thousands(figures['falls'])}"),
                ]
            ),
        ),
    ]


def history_tiles(rows, figures: dict[str, Any], last: tuple[int, int], mode: str) -> list[Tile]:
    """The charts of «Histórico»: the price since January 2022 and the change of each year."""
    name, best, above, years = family_name(figures["family"]), figures["best"], figures["above"], figures["years"]
    palette = charts.get_palette(mode)
    shorter = [f"{year} {note}" for year, note in zip(years["year"], years["note"]) if note]
    if best is None:
        yearly = "—"
    else:
        note = f", {best[2]}" if best[2] else ""
        beat = (
            say(
                f"Superó al IPC por más de {PACE:.0f} puntos en {len(above)} de {len(years)} años: {list_words(above)}.",
                f"It beat the CPI by more than {PACE:.0f} points in {len(above)} of {len(years)} years: "
                f"{list_words(above)}.",
            )
            if above
            else say(
                f"Ningún año superó al IPC por más de {PACE:.0f} puntos.",
                f"No year beat the CPI by more than {PACE:.0f} points.",
            )
        )
        yearly = say(
            f"El año que más subió fue {best[0]} ({percent(best[1])}{note}). {beat}",
            f"The year that rose most was {best[0]} ({percent(best[1])}{note}). {beat}",
        )
    return [
        trend_tile(
            rows,
            figures,
            BASE,
            last,
            mode,
            say("Precio desde enero 2022", "Price since January 2022"),
            say(f"de {month_label(BASE)} a {month_label(last)}", f"from {month_label(BASE)} to {month_label(last)}"),
        ),
        (
            say("Cambio de cada año", "Change of each year"),
            say(f"{BASE[0]}–{last[0]} · de diciembre a diciembre", f"{BASE[0]}–{last[0]} · December to December"),
            say(
                f"El cambio de {name} en cada año, de diciembre a diciembre, como el IPC del INE ({list_words(shorter)})."
                " La raya corta es el IPC de alimentos de ese año.",
                f"The change of {name} in each year, December to December, like the INE CPI ({list_words(shorter)}). "
                "The short line is that year's food CPI.",
            ),
            yearly,
            partial(years_chart, years, mode),
            legend(
                [
                    ("box", year_swatch(len(years)), family_label(figures["family"])),
                    ("tick", palette["strong_text"], ipc_label()),
                ]
            ),
        ),
    ]


# endregion


# region Cards
def card(label: str, value: str, note: str, hint: str, tone: str = "") -> str:
    """One KPI card: what it measures, its figure, one line under it and, on hover, its name and how it is computed (a
    narrow card cuts its lines short, D-460)."""
    return (
        f'<div class="ba-card" tabindex="0" title="{html.escape(label + ": " + hint, quote=True)}"><span class="ba-card-label">'
        f'{html.escape(label)}</span><b class="ba-card-value {tone}">{html.escape(value)}</b>'
        f'<span class="ba-card-note">{html.escape(note)}</span></div>'
    )


def cards_row(cards: list[str]) -> str:
    """The cards of a tab in one row, as many columns as cards (D-554: «Histórico» has four)."""
    return f'<div class="ba-cards" style="--cards:{len(cards)}">' + "".join(cards) + "</div>"


def tone(value: float | None) -> str:
    return "" if value is None or pd.isna(value) else "rise" if value > 0.05 else "fall" if value < -0.05 else ""


def change_card(label: str, figures: dict[str, Any], start, end) -> str:
    """D-565: how much the prices changed and, under it, how far from the food CPI: the two figures read together."""
    gap = figures["gap"]
    note = (
        say("sin IPC que comparar", "no CPI to compare")
        if gap is None or pd.isna(gap)
        else say(f"{points(gap)}: {verdict(gap)}", f"{points(gap)}: {verdict(gap)}")
    )
    return card(
        label,
        percent(figures["change"]),
        note,
        say(
            f"Cambio del índice de {month_label(start)} a {month_label(end)}; el índice usa solo las series con "
            "precio en enero 2022 y en el último mes.",
            f"Change of the index from {month_label(start)} to {month_label(end)}; the index uses only the series "
            "priced in January 2022 and in the last month.",
        )
        + " "
        + against_ipc(figures)
        + ". "
        + definition("Alza frente al IPC"),
        tone(figures["change"]),
    )


def lineup(summaries: list[dict[str, Any]], chosen: str) -> list[dict[str, Any]]:
    """What lies under the choice: the families of the basket, or the products of a family (D-478)."""
    items = [item for item in summaries if item["family"] not in (chosen, BASKET)]
    if any(is_product(item["family"]) for item in items):
        items = [item for item in items if is_product(item["family"])]
    return items


def dearest_card(summaries: list[dict[str, Any]], chosen: str) -> str:
    """D-565: of what lies under the choice, what rose most against the food CPI: what got dearer for real."""
    label = say("Se encareció más", "Rose the most")
    hint = say(
        "De lo que hay bajo la selección (las familias de la canasta o los productos de una familia), lo que más "
        "subió frente al IPC de alimentos en los mismos meses. La tabla los ordena así, de mayor a menor.",
        "Of what lies under the choice (the families of the basket or the products of a family), what rose most "
        "against the food CPI in the same months. The table sorts them this way, highest first.",
    )
    items = [item for item in lineup(summaries, chosen) if item["gap"] is not None and not pd.isna(item["gap"])]
    if not items:
        return card(label, "—", say("nada que comparar", "nothing to compare"), hint)
    top = max(items, key=lambda item: item["gap"])
    note = say(
        f"{points(top['gap'])} frente al IPC · {percent(top['change'])}",
        f"{points(top['gap'])} against the CPI · {percent(top['change'])}",
    )
    return card(label, family_label(top["family"]), note, hint, gap_tone(top["gap"]))


def risk_card(summaries: list[dict[str, Any]], chosen: str, figures: dict[str, Any]) -> str:
    """D-565: where the sharp rises of the choice gather: the two families (or products) with most of them and their
    share of the total."""
    total, falls = figures["rises"], figures["falls"]
    label = say("Dónde está el riesgo", "Where the risk is")
    hint = (
        "K6: "
        + definition("Alerta de precio")
        + " "
        + say(
            f"{charts.format_thousands(total)} alzas fuertes y {charts.format_thousands(falls)} bajas fuertes en el "
            "período. Se cuentan sin ponderar: lo que tiene más productos suma más.",
            f"{charts.format_thousands(total)} sharp rises and {charts.format_thousands(falls)} sharp drops in the "
            "period. They are counted unweighted: what has more products adds more.",
        )
    )
    if not total:
        return card(label, "0", say("sin alzas fuertes en el período", "no sharp rises in the period"), hint)
    items = sorted((item for item in lineup(summaries, chosen) if item["rises"] > 0), key=lambda item: -item["rises"])
    if not items:
        note = say(
            f"alzas fuertes · {charts.format_thousands(falls)} bajas",
            f"sharp rises · {charts.format_thousands(falls)} drops",
        )
        return card(label, charts.format_thousands(total), note, hint)
    top = items[:2]
    share = 100 * sum(item["rises"] for item in top) / total
    names = list_words([family_label(item["family"]) for item in top])
    note = say(
        f"de {charts.format_thousands(total)} alzas fuertes: {names}",
        f"of {charts.format_thousands(total)} sharp rises: {names}",
    )
    return card(label, charts.format_percent(share, 0), note, hint)


def months_card(figures: dict[str, Any]) -> str:
    """D-565: the two months in which the index rose most against the month before: they explain most of the period."""
    label = say("Meses que más subieron", "Months that rose most")
    hint = say(
        "Los dos meses en que más subió el índice frente al mes anterior, dentro del período; «Precio mes a mes» los "
        "muestra.",
        "The two months in which the index rose most against the month before, within the period; «Monthly price» "
        "shows them.",
    )
    months = figures["months"]
    rising = months[months["change"] > 0].nlargest(2, "change").sort_values(["year", "month"])
    if rising.empty:
        return card(label, "—", say("ningún mes subió", "no month rose"), hint)
    value = " · ".join(month_name(int(month)) for month in rising["month"])
    years = "–".join(str(year) for year in sorted(set(rising["year"].astype(int))))
    changes = list_words([percent(change) for change in rising["change"]])
    return card(label, value, say(f"{years}: {changes} en el mes", f"{years}: {changes} in the month"), hint, "rise")


def food_cpi_card(ipc: pd.DataFrame) -> str:
    """D-565: the largest yearly jump of the INE food CPI (D-518) as the last card of «Histórico»: the figure, what came
    after it, and the whole sentence on hover."""
    facts = food_cpi_facts(ipc)
    if facts is None:
        return ""
    lead, detail, hover = food_cpi_insight(ipc)
    after = facts["after"]
    if after.empty:
        note = say("IPC de alimentos del INE", "INE food CPI")
    else:
        spread = (
            charts.format_percent(after.min())
            if len(after) == 1
            else (f"{charts.format_percent(after.min())}–{charts.format_percent(after.max())}")
        )
        note = say(f"desde {facts['peak'] + 1}: {spread} al año", f"since {facts['peak'] + 1}: {spread} a year")
    return card(
        say(f"El salto de {facts['peak']}", f"The jump of {facts['peak']}"),
        percent(facts["changes"][facts["peak"]]),
        note,
        f"{lead} {detail} {hover}".strip(),
        "rise",
    )


def monthly_cards(figures: dict[str, Any], summaries: list[dict[str, Any]], chosen: str, start, end) -> str:
    """The four cards of «Mensual» (D-565): each says a finding, its figure under it and how it is computed on hover."""
    cards = [
        change_card(say("Cambio de precios", "Price change"), figures, start, end),
        dearest_card(summaries, chosen),
        risk_card(summaries, chosen, figures),
        months_card(figures),
    ]
    return cards_row(cards)


def history_cards(
    figures: dict[str, Any], summaries: list[dict[str, Any]], chosen: str, last: tuple[int, int], ipc: pd.DataFrame
) -> str:
    """The cards of «Histórico» (D-565): the same findings over the whole history, and the jump of the food CPI."""
    cards = [
        change_card(say("Cambio desde ene 2022", "Change since Jan 2022"), figures, BASE, last),
        dearest_card(summaries, chosen),
        risk_card(summaries, chosen, figures),
        food_cpi_card(ipc),
    ]
    return cards_row([item for item in cards if item])


# endregion


# region Charts
def sized(chart: Any, width: Any, height: int, mode: str) -> Any:
    return charts.apply_chart_style(chart.properties(width=width, height=height), mode)


def enlarged(height: Any) -> bool:
    """The chart of the zoom, drawn at a fixed height; a chart on the page takes the height of its tile."""
    return isinstance(height, int) and height >= 200


def label_size(height: Any, small: int = 10) -> int:
    """The letters of an axis: larger in the enlarged chart."""
    return small + 2 if enlarged(height) else small


def month_axis(height: Any, temporal: bool = False, **extra: Any) -> Any:
    """An axis that names every month of the period. Enlarged, each month with its year, «oct 2025». On the page, in two
    short lines that leave the chart its height (D-460): the month, and under it the year, only on the first month and
    where the year changes, «sep / 2025 · oct · nov · dic · ene / 2026»."""
    if enlarged(height):
        return alt.Axis(labelAngle=0, labelFontSize=label_size(height, 9), labelOverlap=False, **extra)
    if temporal:
        month, year, january = (
            "timeFormat(datum.value, '%b')",
            "timeFormat(datum.value, '%Y')",
            "month(datum.value) == 0",
        )
    else:  # the category is «oct 2025»
        month, year = "split(datum.value, ' ')[0]", "split(datum.value, ' ')[1]"
        january = f"{month} == '{month_name(1)}'"
    expression = f"[{month}, datum.index == 0 || {january} ? {year} : '']"
    return alt.Axis(
        labelAngle=0,
        labelFontSize=9,
        # D-483: every month while they fit; on a narrow window (a phone in landscape) every other one, never piled up
        labelOverlap="parity",
        labelFlush=False,
        labelExpr=expression,
        labelPadding=3,
        **extra,
    )


def trend_chart(
    rows: pd.DataFrame,
    family: str,
    start: tuple[int, int],
    end: tuple[int, int],
    mode: str,
    width: Any = "container",
    height: int = 150,
) -> Any:
    """The family (or the basket) and the food IPC, month by month, both at 100 on the start month."""
    palette = charts.get_palette(mode)
    key = rows["year"] * 100 + rows["month"]
    panel = rows[
        rows["product_group"].isin([family, IPC]) & key.between(start[0] * 100 + start[1], end[0] * 100 + end[1])
    ]
    first = panel[(panel["year"] == start[0]) & (panel["month"] == start[1])].set_index("product_group")["index"]
    names = [family_label(family), ipc_label()]
    panel = panel[panel["product_group"].isin(first.index)].assign(
        # astype: pandas 3.1 maps an empty selection to text, which cannot divide (D-486)
        value=lambda frame: frame["index"] / frame["product_group"].map(first).astype(float) * 100,
        serie=lambda frame: frame["product_group"].map({family: names[0], IPC: names[1]}),
    )
    color = series_color(family, palette)
    several_years = end[0] - start[0] > 2
    if several_years:
        line = alt.Chart(panel).mark_line(interpolate="monotone", strokeWidth=2.4)
        axis = alt.Axis(format="%Y", tickCount={"interval": "year", "step": 1}, labelFontSize=label_size(height))
    else:  # D-457: each month is a point, and each point has its month on the axis
        dot = alt.OverlayMarkDef(filled=True, size=40 if enlarged(height) else 22)
        line = alt.Chart(panel).mark_line(interpolate="monotone", strokeWidth=2.4, point=dot)
        axis = month_axis(height, temporal=True, format="%b %Y", tickCount={"interval": "month", "step": 1})
    chart = line.encode(
        x=alt.X("month_start:T", title=None, scale=alt.Scale(domain=month_domain(start, end)), axis=axis),
        y=alt.Y(
            "value:Q",
            title=None,
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labelFontSize=label_size(height), tickCount=4),
        ),
        color=alt.Color("serie:N", scale=alt.Scale(domain=names, range=[color, palette["strong_text"]]), legend=None),
        strokeDash=alt.StrokeDash("serie:N", scale=alt.Scale(domain=names, range=[[1, 0], [5, 4]]), legend=None),
        tooltip=[
            alt.Tooltip("serie:N", title=say("Serie", "Series")),
            alt.Tooltip("month_start:T", title=say("Mes", "Month"), format="%b %Y"),
            alt.Tooltip(
                "value:Q",
                title=say(f"Índice ({month_label(start)} = 100)", f"Index ({month_label(start)} = 100)"),
                format=",.1f",
            ),
        ],
    )
    return sized(chart, width, height, mode)


def extremes_chart(
    alert_rows: pd.DataFrame,
    start: tuple[int, int],
    end: tuple[int, int],
    mode: str,
    width: Any = "container",
    height: int = 150,
) -> Any:
    """D-556: the sharp rises of each month upwards and its sharp drops downwards, from one line, so the eye sees which
    dominate. The axis names every month of the period, also those without one: no sharp change can be found in the
    first 12 weeks of the history, so 2022 starts with three empty months."""
    palette = charts.get_palette(mode)
    rises, falls = alert_kinds()
    order = [month_label(pair) for pair in months_between(first_counted(start, end), end)]
    if alert_rows.empty:
        frame = pd.DataFrame(columns=["mes", "kind", "count", "height"])
    else:
        keys = alert_rows["month_key"] if "month_key" in alert_rows.columns else add_month_key(alert_rows)["month_key"]
        frame = (
            alert_rows.assign(
                mes=[month_label((int(key) // 100, int(key) % 100)) for key in keys],
                kind=[rises if value > 0 else falls for value in alert_rows["variation"]],
            )
            .groupby(["mes", "kind"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )
        frame["height"] = frame["count"].where(frame["kind"] == rises, -frame["count"])
    # D-556: room past the longest bar on each side, so its count never touches the months or the top
    top = float(frame["height"].max()) if not frame.empty else 1.0
    bottom = float(frame["height"].min()) if not frame.empty else -1.0
    room = LABEL_ROOM * (max(top, 0) - min(bottom, 0) or 1)
    base = alt.Chart(frame).encode(
        x=alt.X("mes:N", title=None, scale=alt.Scale(domain=order), axis=month_axis(height)),
        y=alt.Y(
            "height:Q",
            title=None,
            scale=alt.Scale(domain=[min(bottom, 0) - room, max(top, 0) + room], nice=False),
            axis=alt.Axis(labelFontSize=label_size(height), tickCount=4, labelExpr="abs(datum.value)"),
        ),
        color=alt.Color(
            "kind:N", scale=alt.Scale(domain=[rises, falls], range=[palette["rise"], palette["fall"]]), legend=None
        ),
    )
    bars = base.mark_bar().encode(
        tooltip=[
            alt.Tooltip("mes:N", title=say("Mes", "Month")),
            alt.Tooltip("kind:N", title=say("Tipo", "Kind")),
            alt.Tooltip("count:Q", title=say("Cantidad", "Count")),
        ]
    )
    # D-556: each bar says its count at its end, above the rises and under the drops, in the colour of its bar.
    size = label_size(height)
    above = (
        base.transform_filter("datum.height > 0")
        .mark_text(baseline="bottom", dy=-3, fontSize=size)
        .encode(text="count:Q")
    )
    below = (
        base.transform_filter("datum.height < 0").mark_text(baseline="top", dy=3, fontSize=size).encode(text="count:Q")
    )
    chart = alt.layer(bars, above, below)
    return sized(chart, width, height, mode)


def years_chart(years: pd.DataFrame, mode: str, width: Any = "container", height: int = 150) -> Any:
    """The change of each year: a bar for the family, in the colour of its year (D-466), a short line for the food IPC
    of that year."""
    palette = charts.get_palette(mode)
    frame = years.assign(
        label=[f"{year} ({note})" if note else year for year, note in zip(years["year"], years["note"])],
    )
    tooltip = [
        alt.Tooltip("label:N", title=say("Año", "Year")),
        alt.Tooltip("change:Q", title=say("Cambio del año (%)", "Change of the year (%)"), format="+.1f"),
        alt.Tooltip("ipc:Q", title=say("IPC de alimentos (%)", "Food CPI (%)"), format="+.1f"),
    ]
    bars = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("year:N", title=None, axis=alt.Axis(labelAngle=0, labelFontSize=label_size(height))),
            y=alt.Y("change:Q", title=None, axis=alt.Axis(labelFontSize=label_size(height), tickCount=4)),
            color=alt.Color("year:N", scale=alt.Scale(domain=list(frame["year"]), range=YEAR_COLORS), legend=None),
            tooltip=tooltip,
        )
    )
    marks = (
        alt.Chart(frame)
        .mark_tick(thickness=2.5, color=palette["strong_text"])
        .encode(x="year:N", y="ipc:Q", tooltip=tooltip)
    )
    return sized(alt.layer(bars, marks), width, height, mode)


# endregion


# region Tables
def build_table(summaries: list[dict[str, Any]], chosen: str, columns: list[tuple[str, str, Any]]) -> str:
    """By family: one figure per column, the whole basket first and the family chosen lit. columns: (label, hint,
    cell) where cell(figures) gives (text, tone, numeric)."""
    products = any(is_product(item["family"]) for item in summaries)  # D-478: a family over its products
    first = say("Familia y sus productos", "Family and its products") if products else say("Familia", "Family")
    header = f"<th>{html.escape(first)}</th>" + "".join(
        f'<th title="{html.escape(hint, quote=True)}">{html.escape(label)}</th>' for label, hint, _ in columns
    )
    body = []
    for item in summaries:
        lit = ' class="ba-chosen"' if item["family"] == chosen else ""
        cells = []
        for _, _, cell in columns:
            text, shade, numeric = cell(item)
            cells.append(f'<td class="{"num " if numeric else ""}{shade}">{html.escape(text)}</td>')
        indent = ' class="ba-product"' if is_product(item["family"]) else ""
        body.append(f"<tr{lit}><td{indent}>{html.escape(family_label(item['family']))}</td>{''.join(cells)}</tr>")
    return f'<div class="ba-table"><table><thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def gap_tone(gap: float | None) -> str:
    return "" if gap is None or pd.isna(gap) else "rise" if gap > PACE else "fall" if gap < -PACE else ""


def ipc_column() -> tuple[str, str, Any]:
    return (
        say("Frente al IPC", "Against the CPI"),
        say(
            f"Puntos sobre o bajo el IPC de alimentos; a más de {PACE:.0f}, en color.",
            f"Points over or under the food CPI; beyond {PACE:.0f}, in colour.",
        ),
        lambda item: (points(item["gap"]), gap_tone(item["gap"]), True),
    )


def ranked(summaries: list[dict[str, Any]], chosen: str) -> list[dict[str, Any]]:
    """D-565: the rows up to the choice stay where they are (the basket, or a family over its chosen product); the rest
    go from what rose most against the food CPI to what rose least, the rows without a CPI last."""
    names = [item["family"] for item in summaries]
    keep = names.index(chosen) + 1 if chosen in names else 1
    rest = sorted(summaries[keep:], key=lambda item: (item["gap"] is None or pd.isna(item["gap"]), -(item["gap"] or 0)))
    return summaries[:keep] + rest


def alerts_column(since: str) -> tuple[str, str, Any]:
    return (
        say("Alzas y bajas fuertes", "Sharp rises and drops"),
        say(f"Alzas y bajas fuertes (K6) {since}.", f"Sharp rises and drops (K6) {since}."),
        lambda item: (charts.format_thousands(item["alerts"]), "", True),
    )


def monthly_table(summaries: list[dict[str, Any]], chosen: str) -> str:
    """D-565: three columns, the rows sorted by «Frente al IPC»: what rose most for real comes first."""
    return build_table(
        ranked(summaries, chosen),
        chosen,
        [
            (
                say("Cambio", "Change"),
                say("Cambio del índice en el período.", "Change of the index in the period."),
                lambda item: (percent(item["change"]), "", True),
            ),
            ipc_column(),
            alerts_column(say("del período", "of the period")),
        ],
    )


def history_table(summaries: list[dict[str, Any]], chosen: str) -> str:
    """D-565: the same three columns over the whole history."""
    return build_table(
        ranked(summaries, chosen),
        chosen,
        [
            (
                say("Desde ene 2022", "Since Jan 2022"),
                say("Cambio del índice desde enero 2022.", "Change of the index since January 2022."),
                lambda item: (percent(item["change"]), "", True),
            ),
            ipc_column(),
            alerts_column(say("desde enero 2022", "since January 2022")),
        ],
    )


# endregion


# region Context
def context_html(lead: str, detail: str) -> str:
    """D-458: the green panel above the tabs: what the reader is looking at. D-565: one line; from which month to which
    and why, on hover of its «i» (and of the whole panel)."""
    return (
        f'<div class="ba-context" title="{html.escape(detail, quote=True)}">'
        '<span class="ba-context-icon" aria-hidden="true">info</span>'
        f"<p><b>{html.escape(lead)}</b></p></div>"
    )


def inflation_lag(last: tuple[int, int]) -> str:
    return say(
        f"Termina en {month_label(last)}: es el último mes con la inflación del INE, que llega una vez al mes y con "
        "atraso.",
        f"It ends in {month_label(last)}: the last month with the INE's inflation, which arrives once a month and "
        "late.",
    )


def monthly_context(period: str, last: tuple[int, int]) -> tuple[str, str]:
    """«Mensual»: the months of the period chosen, why it ends where it ends and why the price starts where it does."""
    start, end = bounds(period, last)
    first = first_counted(start, end)
    if period == LAST_YEAR:
        return (
            say(
                f"Estás viendo los últimos 12 meses: de {month_label(first)} a {month_label(end)}.",
                f"You are looking at the last 12 months: from {month_label(first)} to {month_label(end)}.",
            ),
            inflation_lag(last)
            + " "
            + say(
                f"El precio parte en {month_label(start)} = 100, un año antes, para medir el cambio de 12 meses.",
                f"The price starts at {month_label(start)} = 100, a year before, to measure the 12-month change.",
            ),
        )
    year = int(period)
    lead = say(
        f"Estás viendo {year}: de {month_label(first)} a {month_label(end)}.",
        f"You are looking at {year}: from {month_label(first)} to {month_label(end)}.",
    )
    ends = inflation_lag(last) if end != (year, 12) else say("Es el año completo.", "It is the whole year.")
    if start == BASE:
        starts = say(
            f"El precio parte en {month_label(BASE)} = 100, el primer mes de los datos: no hay índice antes. El primer "
            f"cambio fuerte posible es de abril {BASE[0]}: necesita 12 semanas previas.",
            f"The price starts at {month_label(BASE)} = 100, the first month of the data: there is no index before. The "
            f"first possible sharp change is from April {BASE[0]}: it needs 12 previous weeks.",
        )
    else:
        measures = (
            say("el año de diciembre a diciembre", "the year from December to December")
            if end == (year, 12)
            else say("lo que va del año", "the year so far")
        )
        starts = say(
            f"El precio parte en {month_label(start)} = 100, el cierre del año anterior, para medir {measures}, como el "
            "IPC del INE.",
            f"The price starts at {month_label(start)} = 100, the close of the year before, to measure {measures}, "
            "like the INE CPI.",
        )
    return lead, f"{ends} {starts}"


def history_context(last: tuple[int, int]) -> tuple[str, str]:
    """«Histórico»: from the first month of the data to the last month of the INE, and how a year is measured."""
    shorter = say(f" y {last[0]} hasta {full_month(last[1]).lower()}", f" and {last[0]} up to {full_month(last[1])}")
    shorter = shorter if last[1] != 12 else ""
    return (
        say(
            f"Estás viendo toda la historia: de {month_label(BASE)} a {month_label(last)}.",
            f"You are looking at the whole history: from {month_label(BASE)} to {month_label(last)}.",
        ),
        say(
            f"Empieza en {month_label(BASE)} = 100, el primer mes de los datos, y termina en {month_label(last)}, el "
            f"último mes con la inflación del INE, que llega con atraso. Cada año va de diciembre a diciembre: "
            f"{BASE[0]} desde enero{shorter}.",
            f"It starts at {month_label(BASE)} = 100, the first month of the data, and ends in {month_label(last)}, the "
            f"last month with the INE's inflation, which arrives late. Each year runs from December to December: "
            f"{BASE[0]} from January{shorter}.",
        ),
    )


def food_cpi_facts(ipc: pd.DataFrame) -> dict[str, Any] | None:
    """D-518: the yearly changes of the INE food CPI, December to December over whole years, its largest jump and the
    years after it; None with too little history."""
    december = ipc[ipc["month"] == 12].set_index("year")["food_index"].sort_index()
    if december.empty:
        return None
    december = december.reindex(range(int(december.index[0]), int(december.index[-1]) + 1))
    changes = december.pct_change(fill_method=None).dropna().mul(100)
    if changes.empty:
        return None
    peak = int(changes.idxmax())
    return {"december": december, "changes": changes, "first": int(changes.index[0]), "peak": peak,
            "after": changes[changes.index > peak]}  # fmt: skip


def food_cpi_insight(ipc: pd.DataFrame) -> tuple[str, str, str] | None:
    """D-518: the largest yearly jump of the INE food CPI and what came after it, in words. Every figure is recomputed
    from ipc_monthly, so the sentence follows the data: it says the prices did not go back only while that holds. The
    third text says why the line of the base year reads lower in «Cambio de cada año», which starts that year in
    January. D-565: it is said on hover of the last card of «Histórico»."""
    facts = food_cpi_facts(ipc)
    if facts is None:
        return None
    december, changes, first, peak, after = (facts[key] for key in ("december", "changes", "first", "peak", "after"))
    lead = say(
        f"Los alimentos subieron {percent(changes[peak])} en {peak} según el IPC del INE, el mayor salto desde {first}.",
        f"Food prices rose {percent(changes[peak])} in {peak} according to the INE CPI, the largest jump since {first}.",
    )
    detail = ""
    if not after.empty:
        low, high = charts.format_percent(after.min()), charts.format_percent(after.max())
        spread_es = f"entre {low} y {high}" if len(after) > 1 else low
        spread_en = f"between {low} and {high}" if len(after) > 1 else low
        latest = ipc.sort_values(["year", "month"])["food_index"].iloc[-1]
        held = latest >= december[peak]
        detail = say(
            f"Desde {peak + 1} {'suben' if after.min() >= 0 else 'cambian'} {spread_es} al año: el alza se moderó"
            + (", pero los precios no volvieron atrás." if held else "."),
            f"Since {peak + 1} they {'rise' if after.min() >= 0 else 'change'} {spread_en} a year: the rise has slowed"
            + (", but prices did not go back." if held else "."),
        )
    hover = say(
        "IPC de alimentos del INE, de diciembre a diciembre, en años completos.",
        "INE food CPI, from December to December, in whole years.",
    )
    start = ipc[(ipc["year"] == BASE[0]) & (ipc["month"] == BASE[1])]["food_index"]
    if peak == BASE[0] and not start.empty:
        shorter = percent((december[peak] / start.iloc[0] - 1) * 100)
        hover += " " + say(
            f"En «Cambio de cada año», {peak} parte en enero, el primer mes de los precios, y su raya marca {shorter}.",
            f"In «Change of each year», {peak} starts in January, the first month of the prices, and its line reads "
            f"{shorter}.",
        )
    return lead, detail, hover


def inflation_context(last: tuple[int, int]) -> tuple[str, str]:
    """«Precios e inflación»: its months and what rising with the CPI does not prove (the note under its cards)."""
    return (
        say(
            f"Estás viendo cada familia frente a la inflación: de {month_label(BASE)} a {month_label(last)}.",
            f"You are looking at each family against inflation: from {month_label(BASE)} to {month_label(last)}.",
        ),
        say(
            f"{month_label(BASE).capitalize()} = 100 es el primer mes de los datos y {month_label(last)}, el último "
            "con la inflación del INE, que llega con atraso. Subir con el IPC no prueba que la inflación cause la "
            "subida.",
            f"{month_label(BASE)} = 100 is the first month of the data and {month_label(last)}, the last one with the "
            "INE's inflation, which arrives late. Rising with the CPI does not prove that inflation causes the rise.",
        ),
    )


def insights_context(week: Any, last: tuple[int, int]) -> tuple[str, str]:
    """«Insights»: today's answers, from the week shown and the last month of the INE."""
    shown = weeks.week_range(week, year=True, english=i18n.is_english())
    return (
        say("Estás viendo las respuestas de hoy.", "You are looking at today's answers."),
        say(
            f"Los precios son de la semana {shown}; la inflación llega hasta {month_label(last)}, el último mes "
            "que publicó el INE.",
            f"The prices are those of the week of {shown}; inflation reaches {month_label(last)}, the last month the "
            "INE published.",
        ),
    )


def stakeholders_context() -> tuple[str, str]:
    """«Interesados»: who uses the data; the rule of the rings, which was under the map."""
    return (
        say("Estás viendo quién usa estos datos.", "You are looking at who uses these data."),
        i18n.translate_text(interest_map.CRITERION),
    )


def method_context() -> tuple[str, str]:
    return (
        say("Estás viendo cómo se calcula cada cifra.", "You are looking at how each figure is computed."),
        say(
            "Los KPI y las decisiones de sistema, leídos del PRD y del SQAP.",
            "The KPIs and the system decisions, read from the PRD and the SQAP.",
        ),
    )


def build_context_css(palette: dict[str, str], green: str) -> str:
    """The panel in the fluorescent green of GreenOcean (D-450): a green edge and a light green ground, the text in the
    ink of the theme so it reads on every theme. One line on every tab (D-565), so the tabs below it never jump. It ends
    in a div, so its bottom margin makes up for the -1rem of the block (D-173)."""
    return static_files.style(
        "ba_context.css",
        {
            'var(--go-green)': green,
            'var(--go-text)': palette["text"],
            'var(--go-strong_text)': palette["strong_text"],
        },
    )


# endregion


# region Zoom
def zoom_text(measures: str, deduce: str) -> str:
    """The words of an enlarged chart: what it measures and what follows from it."""
    return (
        f'<p class="ba-zoom-line"><b>{html.escape(say("Qué mide", "What it measures"))}</b> {html.escape(measures)}</p>'
        f'<p class="ba-zoom-line"><b>{html.escape(say("Qué se deduce", "What follows"))}</b> {html.escape(deduce)}</p>'
    )


def build_css(palette: dict[str, str], green: str) -> str:
    ink, text, muted, card_color, border = (
        palette["strong_text"],
        palette["text"],
        charts.legible(palette["reference"], palette["background"]),
        palette["card"],
        palette["card_border"],
    )
    rise, fall, accent = palette["rise"], palette["fall"], palette["accent"]
    return static_files.style(
        "ba_trends.css",
        {
            'var(--go-border)': border,
            'var(--go-card-color)': card_color,
            'var(--go-accent)': accent,
            'var(--go-muted)': muted,
            'var(--go-ink)': ink,
            'var(--go-rise)': rise,
            'var(--go-fall)': fall,
            'var(--go-text)': text,
            'var(--go-tiles-reserved)': TILES_RESERVED,
            'var(--go-tiles-floor)': TILES_FLOOR,
            'var(--go-green)': green,
            'var(--go-table-reserved)': TABLE_RESERVED,
            'var(--go-table-floor)': TABLE_FLOOR,
            'var(--go-narrow-floor)': NARROW_FLOOR,
            'var(--go-table-reserved-35)': TABLE_RESERVED - 35,
        },
    )


# endregion
