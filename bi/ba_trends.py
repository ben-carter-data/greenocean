"""«Análisis» (D-456, D-457): the history of food prices, read two ways that never mix. «Mensual» is one
period, the last 12 months or one year, month by month; «Histórico» is the whole history, from January 2022 to the last
month the INE published, year by year and by season. Each chart says which months it shows; on hover it grows and says
what it measures and what follows from it, in words computed from the same figures it draws. Every figure comes from
the queries and rules the rest of the panel uses: the monthly index of «Precios e inflación» (D-163), K1 (the gap), K4
(the season) and K6 (the alerts); every definition, from «Método» (overview.KPIS). Nothing here is typed by hand."""

from __future__ import annotations

import html
from collections.abc import Callable
from functools import partial
from typing import Any

import altair as alt
import pandas as pd

from bi import charts, home_mockup, i18n, inflation_view, interest_map, overview, weeks

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
TILES_RESERVED, TILES_FLOOR, NARROW_FLOOR = 603, 230, 210
# D-461: on a low window the charts keep their floor and the table scrolls inside its own box, under the charts.
TABLE_RESERVED, TABLE_FLOOR = 588, 140
INSIGHT_ROOM = 43  # D-518: the height of the green box of «Histórico», taken from the table so the page still fits

# One chart of a tab: its title, the months it shows, what it measures, what follows from it, and how to draw it at a
# width and a height.
Tile = tuple[str, str, str, str, Callable[..., Any]]


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
def season(seasonal: pd.DataFrame) -> pd.DataFrame:
    """K4 by calendar month: the median of the weekly seasonal index (price over the average of its year), as a % over
    or under that average, with the weeks behind each month and the years they come from: a month of the calendar
    gathers its weeks of every year of the period, so the chart says which."""
    if seasonal.empty:
        return pd.DataFrame(columns=["month", "change", "weeks", "years"])
    if "month_key" not in seasonal.columns:
        seasonal = add_month_key(seasonal)
    grouped = seasonal.assign(month=seasonal["month_key"] % 100, year=seasonal["month_key"] // 100).groupby("month")
    result = grouped["seasonal_index"].median().sub(1).mul(100).rename("change").to_frame()
    result["weeks"] = grouped["week_start"].nunique()
    first, last = grouped["year"].min(), grouped["year"].max()
    result["years"] = [str(a) if a == b else f"{a}–{b}" for a, b in zip(first, last)]
    return result.reset_index()


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


def summarize(
    rows: pd.DataFrame,
    margins: pd.DataFrame,
    seasonal: pd.DataFrame,
    alerts_found: pd.DataFrame,
    family: str,
    start: tuple[int, int],
    end: tuple[int, int],
) -> dict[str, Any]:
    """The figures of one family (or the whole basket) in one period."""
    change = inflation_view.change(rows, family, start, end)
    ipc = inflation_view.change(rows, IPC, start, end)
    gap = None if change is None or ipc is None else change - ipc
    margin_rows = within(margins, start, end, family)
    alert_rows = within(alerts_found, start, end, family)
    profile = season(within(seasonal, start, end, family))
    cheapest = profile.loc[profile["change"].idxmin()] if not profile.empty else None
    dearest = profile.loc[profile["change"].idxmax()] if not profile.empty else None
    return {
        "family": family,
        "change": change,
        "ipc": ipc,
        "gap": gap,
        "verdict": verdict(gap),
        "margin": None if margin_rows.empty else float(margin_rows["margin"].median() * 100),
        "pairs": len(margin_rows),
        "alerts": len(alert_rows),
        "rises": int((alert_rows["variation"] > 0).sum()) if not alert_rows.empty else 0,
        "falls": int((alert_rows["variation"] < 0).sum()) if not alert_rows.empty else 0,
        "alert_rows": alert_rows,
        "cheapest": None if cheapest is None else (int(cheapest["month"]), float(cheapest["change"])),
        "dearest": None if dearest is None else (int(dearest["month"]), float(dearest["change"])),
        "profile": profile,
    }


def monthly(rows, margins, seasonal, alerts_found, family, start, end) -> dict[str, Any]:
    """«Mensual»: the figures of the period, the change of each of its months and their highest and lowest."""
    figures = summarize(rows, margins, seasonal, alerts_found, family, start, end)
    months = monthly_changes(rows, family, start, end).dropna(subset=["change"])
    figures["months"] = months
    figures["top"] = figures["low"] = None
    figures["rising"] = int((months["change"] > 0).sum())
    if not months.empty:
        top, low = months.loc[months["change"].idxmax()], months.loc[months["change"].idxmin()]
        figures["top"] = (int(top["year"]), int(top["month"]), float(top["change"]))
        figures["low"] = (int(low["year"]), int(low["month"]), float(low["change"]))
    return figures


def history(rows, margins, seasonal, alerts_found, family, last) -> dict[str, Any]:
    """«Histórico»: the figures from January 2022 to the last month, and the change of each year."""
    figures = summarize(rows, margins, seasonal, alerts_found, family, BASE, last)
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


def product_frames(
    series: pd.DataFrame, ipc: pd.DataFrame, margins: pd.DataFrame, seasonal: pd.DataFrame, alerts_found: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str]]:
    """D-478: the frames of «Mensual» and «Histórico» one level down. Each product is keyed PRODUCT + its name, its
    index is the median of its own consumer series against January 2022 (the family's rule), and K1, K4 and K6 keep
    their rows under the product. The last item says the family of every product found in any of them, so a family's
    alerts and K1 pairs are exactly the sum of its products' (a product without an index shows «—», never a guess)."""
    rows, _ = inflation_view.build_family_index(series.assign(product_group=PRODUCT + series["product"]), ipc)

    def down(frame: pd.DataFrame) -> pd.DataFrame:
        return frame.assign(product_group=PRODUCT + frame["product"])

    family_of = {
        PRODUCT + product: family
        for frame in (series, margins, seasonal, alerts_found)
        for product, family in zip(frame["product"], frame["product_group"])
    }
    return rows, down(margins), down(seasonal), down(alerts_found), family_of


def products_of(family_of: dict[str, str], family: str) -> list[str]:
    """The products of a family (every product for the whole basket), by name."""
    return sorted((key for key, group in family_of.items() if family == BASKET or group == family), key=product_name)


def wholesale_families(margins: pd.DataFrame) -> list[str]:
    """The families with a wholesale price, the only ones with a consumer–wholesale gap (K1)."""
    return sorted(set(margins["product_group"]))


def busiest_month(alert_rows: pd.DataFrame) -> tuple[int, int, int] | None:
    """(year, month, alerts) of the month with most alerts; the earliest on a tie."""
    if alert_rows.empty:
        return None
    per_month = alert_rows.groupby("month_key").size()
    key = int(per_month.idxmax())
    return key // 100, key % 100, int(per_month.max())


# endregion


# region Tiles
def trend_tile(rows, figures, start, end, mode, title: str, since: str) -> Tile:
    name = family_name(figures["family"])
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
    )


def monthly_tiles(rows, figures: dict[str, Any], start, end, mode: str) -> list[Tile]:
    """The three charts of «Mensual»: the price, the change of each month and the alerts of each month."""
    name, top, low = family_name(figures["family"]), figures["top"], figures["low"]
    first_bar, first_week = next_month(start), first_counted(start, end)
    if top is None:
        moves = "—"
    else:
        rose = (
            say(
                f"La mayor alza fue {month_label(top[:2])} ({percent(top[2])})",
                f"The biggest rise was {month_label(top[:2])} ({percent(top[2])})",
            )
            if top[2] > 0
            else say("Ningún mes subió", "No month rose")
        )
        fell = (
            say(
                f"la mayor baja, {month_label(low[:2])} ({percent(low[2])})",
                f"the biggest fall, {month_label(low[:2])} ({percent(low[2])})",
            )
            if low[2] < 0
            else say("ningún mes bajó", "no month fell")
        )
        moves = say(
            f"Subió en {figures['rising']} de {len(figures['months'])} meses. {rose} y {fell}.",
            f"It rose in {figures['rising']} of {len(figures['months'])} months. {rose} and {fell}.",
        )
    busiest = busiest_month(figures["alert_rows"])
    first_alert = (
        say(
            " La primera alerta posible es de abril 2022: necesita 12 semanas previas.",
            " The first possible alert is from April 2022: it needs 12 previous weeks.",
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
            say("Cambio de cada mes", "Change of each month"),
            say(
                f"{span(first_bar, end)} · frente al mes anterior", f"{span(first_bar, end)} · against the month before"
            ),
            say(
                f"Cuánto cambió el precio de {name} cada mes frente al mes anterior. La raya corta es el IPC de alimentos "
                "de ese mes.",
                f"How much the price of {name} changed each month against the month before. The short line is that "
                "month's food CPI.",
            ),
            moves,
            partial(months_chart, figures["months"], mode),
        ),
        (
            say("Alertas de precio por mes", "Price alerts by month"),
            say(
                f"{span(first_week, end)} · alzas fuertes y bajas fuertes (K6)",
                f"{span(first_week, end)} · sharp rises and sharp drops (K6)",
            ),
            say(
                f"Las semanas en que un producto de {name} cambió fuera de su rango habitual (K6): los valores "
                f"atípicos.{first_alert}",
                f"The weeks in which a product of {name} changed outside its usual range (K6): the outliers.{first_alert}",
            ),
            say("Ninguna alerta en el período.", "No alert in the period.")
            if busiest is None
            else say(
                f"{charts.format_thousands(figures['alerts'])} alertas: {charts.format_thousands(figures['rises'])} "
                f"alzas fuertes y {charts.format_thousands(figures['falls'])} bajas fuertes. El mes con más fue "
                f"{month_label(busiest[:2])}, con {charts.format_thousands(busiest[2])}.",
                f"{charts.format_thousands(figures['alerts'])} alerts: {charts.format_thousands(figures['rises'])} sharp "
                f"rises and {charts.format_thousands(figures['falls'])} sharp drops. The month with most was "
                f"{month_label(busiest[:2])}, with {charts.format_thousands(busiest[2])}.",
            ),
            partial(alerts_chart, figures["alert_rows"], start, end, mode),
        ),
    ]


def history_tiles(rows, figures: dict[str, Any], last: tuple[int, int], mode: str) -> list[Tile]:
    """The three charts of «Histórico»: the price since January 2022, the change of each year and the season."""
    name, best, above, years = family_name(figures["family"]), figures["best"], figures["above"], figures["years"]
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
    cheapest, dearest = figures["cheapest"], figures["dearest"]
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
        ),
        (
            say("Temporada", "Season"),
            say(
                f"{BASE[0]}–{last[0]} · cada mes frente al promedio de su año",
                f"{BASE[0]}–{last[0]} · each month against its year's average",
            ),
            say(
                f"K4: el precio de cada semana sobre el promedio de su año; cada barra es la mediana de ese mes del "
                f"calendario, de {BASE[0]} a {last[0]}. Son precios del día: cuando suben durante el año, los primeros "
                "meses quedan bajo su promedio y los últimos sobre él.",
                f"K4: each week's price over the average of its year; each bar is the median of that calendar month, "
                f"from {BASE[0]} to {last[0]}. These are prices of the day: when they rise during the year, the first "
                "months stay under its average and the last ones over it.",
            ),
            "—"
            if cheapest is None
            else say(
                f"{full_month(cheapest[0])} suele ser el mes más barato ({percent(cheapest[1])} frente al promedio de "
                f"su año) y {full_month(dearest[0]).lower()} el más caro ({percent(dearest[1])}).",
                f"{full_month(cheapest[0])} tends to be the cheapest month ({percent(cheapest[1])} against the average "
                f"of its year) and {full_month(dearest[0])} the dearest ({percent(dearest[1])}).",
            ),
            partial(season_chart, figures["profile"], mode),
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


def tone(value: float | None) -> str:
    return "" if value is None or pd.isna(value) else "rise" if value > 0.05 else "fall" if value < -0.05 else ""


def change_card(label: str, figures: dict[str, Any], start, end) -> str:
    return card(
        label,
        percent(figures["change"]),
        compared(start, end),
        say(
            f"Cambio del índice de {month_label(start)} a {month_label(end)}; el índice usa solo las series con "
            "precio en enero 2022 y en el último mes.",
            f"Change of the index from {month_label(start)} to {month_label(end)}; the index uses only the series "
            "priced in January 2022 and in the last month.",
        )
        + " "
        + definition("Alza frente al IPC"),
        tone(figures["change"]),
    )


def ipc_card(figures: dict[str, Any]) -> str:
    return card(
        say("Frente al IPC", "Against the CPI"),
        points(figures["gap"]),
        figures["verdict"] or "—",
        say(
            "Puntos entre el cambio de precios y el del IPC de alimentos del INE en los mismos meses.",
            "Points between the price change and that of the INE food CPI in the same months.",
        )
        + " "
        + definition("Alza frente al IPC"),
        gap_tone(figures["gap"]),
    )


def alert_card(figures: dict[str, Any]) -> str:
    return card(
        say("Alertas de precio", "Price alerts"),
        charts.format_thousands(figures["alerts"]),
        say(
            f"{charts.format_thousands(figures['rises'])} alzas fuertes · "
            f"{charts.format_thousands(figures['falls'])} bajas fuertes",
            f"{charts.format_thousands(figures['rises'])} sharp rises · {charts.format_thousands(figures['falls'])} sharp drops",
        ),
        "K6: " + definition("Alerta de precio"),
    )


def monthly_cards(figures: dict[str, Any], start, end, wholesale: list[str]) -> str:
    """The five KPI cards of «Mensual»."""
    top = figures["top"]
    wholesale_names = list_words([home_mockup.short_family(name) for name in wholesale])
    if top is None or top[2] <= 0:
        rise_value, rise_note = "—", say("ningún mes subió", "no month rose")
    else:
        rise_value = month_label(top[:2])
        before = month_label((top[0], top[1] - 1) if top[1] > 1 else (top[0] - 1, 12))
        rise_note = say(f"{percent(top[2])} sobre {before}", f"{percent(top[2])} over {before}")
    cards = [
        change_card(say("Cambio de precios", "Price change"), figures, start, end),
        ipc_card(figures),
        card(
            say("Brecha consumidor–mayorista", "Consumer–wholesale gap"),
            "—" if figures["margin"] is None else charts.format_percent(figures["margin"]),
            say("sin precio mayorista que comparar", "no wholesale price to compare")
            if figures["margin"] is None
            else say(
                f"mediana de {charts.format_thousands(figures['pairs'])} pares",
                f"median of {charts.format_thousands(figures['pairs'])} pairs",
            ),
            "K1: "
            + definition("Brecha consumidor–mayorista")
            + " "
            + say(
                f"Solo {wholesale_names} tienen precio mayorista. No es ganancia: no descuenta costos.",
                f"Only {wholesale_names} have a wholesale price. It is not profit: it does not deduct costs.",
            ),
        ),
        alert_card(figures),
        card(
            say("Mayor alza mensual", "Biggest monthly rise"),
            rise_value,
            rise_note,
            say(
                "El mes en que más subió el índice frente al mes anterior, dentro del período.",
                "The month in which the index rose most against the month before, within the period.",
            ),
        ),
    ]
    return '<div class="ba-cards">' + "".join(cards) + "</div>"


def history_cards(figures: dict[str, Any], last: tuple[int, int]) -> str:
    """The five KPI cards of «Histórico»."""
    best, cheapest, dearest = figures["best"], figures["cheapest"], figures["dearest"]
    cards = [
        change_card(say("Cambio desde ene 2022", "Change since Jan 2022"), figures, BASE, last),
        ipc_card(figures),
        card(
            say("Año de mayor alza", "Year of the biggest rise"),
            "—" if best is None else best[0],
            "—" if best is None else say(*[percent(best[1]) + (f" · {best[2]}" if best[2] else "")] * 2),
            say(
                "El año en que más subió el índice, de diciembre a diciembre; 2022 desde enero y el año en curso hasta "
                "el último mes publicado.",
                "The year in which the index rose most, December to December; 2022 from January and the current year "
                "up to the last month published.",
            ),
        ),
        card(
            say("Mes más barato", "Cheapest month"),
            "—" if cheapest is None else full_month(cheapest[0]),
            "—"
            if cheapest is None
            else say(
                f"{percent(cheapest[1])} · más caro: {month_name(dearest[0])}",
                f"{percent(cheapest[1])} · dearest: {month_name(dearest[0])}",
            ),
            say(
                "K4: el precio de cada semana sobre el promedio de su año; la mediana de cada mes del calendario, de "
                "todos los años.",
                "K4: each week's price over the average of its year; the median of each calendar month, of every year.",
            ),
        ),
        alert_card(figures),
    ]
    return '<div class="ba-cards">' + "".join(cards) + "</div>"


# endregion


# region Charts
# D-466: one colour per year in «Cambio de cada año», so each year reads apart; the bar's height says whether it rose.
YEAR_COLORS = ["#5aa9ea", "#5fd39b", "#b49cff", "#f2b05e", "#ef7d8e", "#4dd0e1", "#f48fb1"]


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
    names = [family_label(family), say("IPC de alimentos", "Food CPI")]
    panel = panel[panel["product_group"].isin(first.index)].assign(
        # astype: pandas 3.1 maps an empty selection to text, which cannot divide (D-486)
        value=lambda frame: frame["index"] / frame["product_group"].map(first).astype(float) * 100,
        serie=lambda frame: frame["product_group"].map({family: names[0], IPC: names[1]}),
    )
    color = inflation_view.FAMILY_COLORS.get(family, palette["accent"])
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


def months_chart(months: pd.DataFrame, mode: str, width: Any = "container", height: int = 150) -> Any:
    """Each month's change against the month before: a bar for the family, a short line for the food IPC."""
    palette = charts.get_palette(mode)
    rose, fell = say("subió", "rose"), say("bajó", "fell")
    frame = months.assign(
        mes=[month_label((int(year), int(month))) for year, month in zip(months["year"], months["month"])],
        tone=[rose if value > 0 else fell for value in months["change"]],
    )
    order = list(frame["mes"])
    tooltip = [
        alt.Tooltip("mes:N", title=say("Mes", "Month")),
        alt.Tooltip(
            "change:Q",
            title=say("Cambio frente al mes anterior (%)", "Change against the month before (%)"),
            format="+.1f",
        ),
        alt.Tooltip("ipc:Q", title=say("IPC de alimentos (%)", "Food CPI (%)"), format="+.1f"),
    ]
    bars = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
        .encode(
            x=alt.X("mes:N", sort=order, title=None, axis=month_axis(height)),
            y=alt.Y("change:Q", title=None, axis=alt.Axis(labelFontSize=label_size(height), tickCount=4)),
            color=alt.Color(
                "tone:N", scale=alt.Scale(domain=[rose, fell], range=[palette["rise"], palette["fall"]]), legend=None
            ),
            tooltip=tooltip,
        )
    )
    marks = (
        alt.Chart(frame)
        .mark_tick(thickness=2, color=palette["strong_text"])
        .encode(x=alt.X("mes:N", sort=order), y="ipc:Q", tooltip=tooltip)
    )
    return sized(alt.layer(bars, marks), width, height, mode)


def alerts_chart(
    alert_rows: pd.DataFrame,
    start: tuple[int, int],
    end: tuple[int, int],
    mode: str,
    width: Any = "container",
    height: int = 150,
) -> Any:
    """The K6 alerts of each month, rises over falls. The axis names every month of the period, also those without an
    alert: no alert can be raised in the first 12 weeks of the history, so 2022 starts with three empty months."""
    palette = charts.get_palette(mode)
    rises, falls = say("Subidas", "Rises"), say("Bajadas", "Falls")
    order = [month_label(pair) for pair in months_between(first_counted(start, end), end)]
    if alert_rows.empty:
        frame = pd.DataFrame(columns=["mes", "kind", "alerts"])
    else:
        keys = alert_rows["month_key"] if "month_key" in alert_rows.columns else add_month_key(alert_rows)["month_key"]
        frame = (
            alert_rows.assign(
                mes=[month_label((int(key) // 100, int(key) % 100)) for key in keys],
                kind=[rises if value > 0 else falls for value in alert_rows["variation"]],
            )
            .groupby(["mes", "kind"], as_index=False)
            .size()
            .rename(columns={"size": "alerts"})
        )
    chart = (
        alt.Chart(frame)
        .mark_bar()
        .encode(
            x=alt.X("mes:N", title=None, scale=alt.Scale(domain=order), axis=month_axis(height)),
            y=alt.Y("alerts:Q", title=None, stack="zero", axis=alt.Axis(labelFontSize=label_size(height), tickCount=4)),
            color=alt.Color(
                "kind:N", scale=alt.Scale(domain=[rises, falls], range=[palette["rise"], palette["fall"]]), legend=None
            ),
            tooltip=[
                alt.Tooltip("mes:N", title=say("Mes", "Month")),
                alt.Tooltip("kind:N", title=say("Tipo", "Kind")),
                alt.Tooltip("alerts:Q", title=say("Alertas", "Alerts")),
            ],
        )
    )
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


def season_chart(profile: pd.DataFrame, mode: str, width: Any = "container", height: int = 150) -> Any:
    """Each calendar month against the average of its year (K4); a bar gathers that month of every year."""
    palette = charts.get_palette(mode)
    cheaper, dearer = say("más barato", "cheaper"), say("más caro", "dearer")
    frame = profile.assign(
        mes=[month_name(month) for month in profile["month"]],
        tone=[cheaper if value < 0 else dearer for value in profile["change"]],
    )
    order = [month_name(month) for month in range(1, 13)]
    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("mes:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=label_size(height))),
            y=alt.Y(
                "change:Q",
                title=None,
                axis=alt.Axis(
                    labelFontSize=label_size(height),
                    tickCount=4,
                    labelExpr="datum.value > 0 ? '+' + datum.label : datum.label",
                ),
            ),
            color=alt.Color(
                "tone:N",
                scale=alt.Scale(domain=[cheaper, dearer], range=[palette["fall"], palette["rise"]]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("mes:N", title=say("Mes", "Month")),
                alt.Tooltip(
                    "change:Q", title=say("% frente al promedio del año", "% against the year's average"), format="+.1f"
                ),
                alt.Tooltip("years:N", title=say("Años", "Years")),
                alt.Tooltip("weeks:Q", title=say("Semanas", "Weeks")),
            ],
        )
    )
    return sized(chart, width, height, mode)


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


def monthly_table(summaries: list[dict[str, Any]], chosen: str) -> str:
    return build_table(
        summaries,
        chosen,
        [
            (
                say("Cambio", "Change"),
                say("Cambio del índice en el período.", "Change of the index in the period."),
                lambda item: (percent(item["change"]), "", True),
            ),
            ipc_column(),
            (
                say("Brecha", "Gap"),
                say("Mediana de K1: consumidor sobre mayorista.", "Median of K1: consumer over wholesale."),
                lambda item: ("—" if item["margin"] is None else charts.format_percent(item["margin"]), "", True),
            ),
            (
                say("Alertas", "Alerts"),
                say("Alertas de precio (K6) del período.", "Price alerts (K6) of the period."),
                lambda item: (charts.format_thousands(item["alerts"]), "", True),
            ),
            (
                say("Mayor alza mensual", "Biggest monthly rise"),
                say("El mes que más subió frente al anterior.", "The month that rose most against the one before."),
                lambda item: (
                    "—"
                    if item["top"] is None or item["top"][2] <= 0
                    else say(*[f"{month_label(item['top'][:2])} · {percent(item['top'][2])}"] * 2),
                    "",
                    False,
                ),
            ),
        ],
    )


def history_table(summaries: list[dict[str, Any]], chosen: str) -> str:
    return build_table(
        summaries,
        chosen,
        [
            (
                say("Desde ene 2022", "Since Jan 2022"),
                say("Cambio del índice desde enero 2022.", "Change of the index since January 2022."),
                lambda item: (percent(item["change"]), "", True),
            ),
            ipc_column(),
            (
                say("Año de mayor alza", "Year of the biggest rise"),
                say(
                    "El año que más subió, de diciembre a diciembre.", "The year that rose most, December to December."
                ),
                lambda item: (
                    "—" if item["best"] is None else say(*[f"{item['best'][0]} · {percent(item['best'][1])}"] * 2),
                    "",
                    False,
                ),
            ),
            (
                say("Mes más barato", "Cheapest month"),
                say("El mes con el menor K4, de todos los años.", "The month with the lowest K4, of every year."),
                lambda item: ("—" if item["cheapest"] is None else full_month(item["cheapest"][0]), "", False),
            ),
            (
                say("Alertas", "Alerts"),
                say("Alertas de precio (K6) desde enero 2022.", "Price alerts (K6) since January 2022."),
                lambda item: (charts.format_thousands(item["alerts"]), "", True),
            ),
        ],
    )


# endregion


# region Context
def context_html(lead: str, detail: str) -> str:
    """D-458: the green panel above the tabs: what the reader is looking at, from which month to which, and why."""
    return (
        '<div class="ba-context"><span class="ba-context-icon" aria-hidden="true">info</span>'
        f"<p><b>{html.escape(lead)}</b> {html.escape(detail)}</p></div>"
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
            f"El precio parte en {month_label(BASE)} = 100, el primer mes de los datos: no hay índice antes, así que "
            f"el cambio de cada mes empieza en {full_month(next_month(BASE)[1]).lower()}. La primera alerta posible es de abril "
            f"{BASE[0]}: una alerta necesita 12 semanas previas.",
            f"The price starts at {month_label(BASE)} = 100, the first month of the data: there is no index before, so "
            f"the change of each month starts in {full_month(next_month(BASE)[1])}. The first possible alert is from "
            f"April {BASE[0]}: an alert needs 12 previous weeks.",
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


def food_cpi_insight(ipc: pd.DataFrame) -> tuple[str, str, str] | None:
    """D-518: the largest yearly jump of the INE food CPI and what came after it. Every figure is recomputed from
    ipc_monthly, December to December over whole years, so the sentence follows the data: it says the prices did not go
    back only while that holds. The third text, on hover, says why the line of the base year reads lower in «Cambio de
    cada año», which starts that year in January."""
    december = ipc[ipc["month"] == 12].set_index("year")["food_index"].sort_index()
    if december.empty:
        return None
    december = december.reindex(range(int(december.index[0]), int(december.index[-1]) + 1))
    changes = december.pct_change(fill_method=None).dropna().mul(100)
    if changes.empty:
        return None
    first, peak = int(changes.index[0]), int(changes.idxmax())
    lead = say(
        f"Los alimentos subieron {percent(changes[peak])} en {peak} según el IPC del INE, el mayor salto desde {first}.",
        f"Food prices rose {percent(changes[peak])} in {peak} according to the INE CPI, the largest jump since {first}.",
    )
    after = changes[changes.index > peak]
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


def insight_html(lead: str, detail: str, hover: str) -> str:
    """D-518: a fact of the history in a green box, in the style of the panel above the tabs."""
    return (
        f'<div class="ba-context ba-insight" title="{html.escape(hover, quote=True)}">'
        '<span class="ba-context-icon" aria-hidden="true">lightbulb</span>'
        f"<p><b>{html.escape(lead)}</b> {html.escape(detail)}</p></div>"
    )


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
    ink of the theme so it reads on every theme. It keeps the height of two lines on every tab, so the tabs below it
    never jump. It ends in a div, so its bottom margin makes up for the -1rem of the block (D-173)."""
    return f"""<style>
.ba-context {{ display:flex; gap:10px; align-items:center; padding:7px 14px; margin:-12px 0 6px; font-size:13px;
  min-height:calc(2.9em + 16px); box-sizing:border-box; border:1px solid {green}; border-radius:12px;
  background:color-mix(in srgb, {green} 11%, transparent); }}
.ba-context-icon {{ font-family:"Material Symbols Rounded"; font-feature-settings:"liga"; font-size:20px;
  line-height:1; color:{green}; }}
.ba-context p {{ margin:0 !important; font-size:13px !important; line-height:1.45 !important;
  color:{palette["text"]} !important; }}
.ba-context b {{ color:{palette["strong_text"]}; }}
.ba-insight {{ min-height:0; padding:5px 14px; margin:0 0 20px; cursor:help; }}
[data-testid="stMain"]:has(.ba-insight) .ba-table {{ max-height:max(calc(100vh - {TABLE_RESERVED + INSIGHT_ROOM}px),
  {TABLE_FLOOR}px); }}
</style>"""


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
    return f"""<style>
.ba-cards {{ display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:10px; margin:0 0 6px; }}
.st-key-ba_head {{ justify-content:space-between; gap:12px; flex-wrap:wrap; }}
.st-key-ba_filters [data-testid="stWidgetLabel"] p {{ font-size:12px !important; }}
/* D-460: thin cards, one line each: the label, the figure and its note, so the charts get the height. */
.ba-card {{ display:flex; flex-direction:column; gap:0; padding:6px 11px 7px; border:1px solid {border}; border-radius:12px;
  background:{card_color}; cursor:help; outline:none; min-width:0; }}
.ba-card:hover, .ba-card:focus-visible {{ border-color:{accent}; }}
.ba-card-label {{ font-size:11px; line-height:1.3; color:{muted}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ba-card-value {{ font-size:20px; font-weight:700; color:{ink}; font-variant-numeric:tabular-nums; line-height:1.2; }}
.ba-card-value.rise {{ color:{rise}; }} .ba-card-value.fall {{ color:{fall}; }}
.ba-card-note {{ font-size:11px; line-height:1.3; color:{text}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ba-chart-title {{ margin:0 !important; font-size:13.5px !important; font-weight:600; color:{ink} !important;
  line-height:1.3 !important; }}
.ba-chart-title span {{ display:block; font-weight:400; color:{muted}; font-size:11.5px; }}
/* D-458: the three charts take the height the window leaves, above a floor, so a tall window shows them larger. */
[class*="st-key-ba_tile_"] {{ min-height:max(calc(100vh - {TILES_RESERVED}px), {TILES_FLOOR}px); }}
[class*="st-key-ba_tile_"] > [data-testid="stElementContainer"]:has([data-testid="stVegaLiteChart"]) {{
  flex:1 1 0; min-height:0; display:flex; flex-direction:column; }}
[class*="st-key-ba_tile_"] > [data-testid="stElementContainer"] [data-testid="stFullScreenFrame"],
[class*="st-key-ba_tile_"] > [data-testid="stElementContainer"] [data-testid="stFullScreenFrame"] > div,
[class*="st-key-ba_tile_"] > [data-testid="stElementContainer"] [data-testid="stVegaLiteChart"] {{
  flex:1 1 auto; height:100%; min-height:0; }}
/* D-460: the green magnifier of a chart opens it large in a window; it glows in the green of GreenOcean (D-450). */
[class*="st-key-ba_tile_"] [data-testid="stElementToolbar"] {{ display:none !important; }}
[class*="st-key-ba_chart_head_"] {{ gap:4px !important; flex-wrap:nowrap !important; }}
[class*="st-key-ba_chart_head_"] > [data-testid="stElementContainer"]:first-child {{ flex:1 1 auto; min-width:0; }}
[class*="st-key-ba_enlarge_"] button {{ min-height:24px !important; padding:0 2px !important; background:transparent !important;
  border:0 !important; box-shadow:none !important; }}
[class*="st-key-ba_enlarge_"] button [data-testid="stMarkdownContainer"] {{ position:absolute !important; width:1px;
  height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }}
[class*="st-key-ba_enlarge_"] button [data-testid="stIconMaterial"] {{ color:{green} !important; font-size:22px !important;
  filter:drop-shadow(0 0 3px {green}) drop-shadow(0 0 7px color-mix(in srgb, {green} 55%, transparent));
  transition:transform .15s ease; }}
[class*="st-key-ba_enlarge_"] button:hover [data-testid="stIconMaterial"] {{ transform:scale(1.18); }}
.ba-zoom-line {{ margin:0 0 3px !important; font-size:13px !important; line-height:1.45 !important;
  color:{text} !important; }}
.ba-zoom-line b {{ color:{ink}; margin-right:4px; }}
.ba-zoom-title {{ margin:0 40px 8px 0 !important; font-size:17px !important; font-weight:700; color:{ink} !important;
  line-height:1.3 !important; }}
.ba-zoom-title span {{ display:block; font-weight:400; font-size:12.5px; color:{muted}; }}
[role="dialog"]:has(.ba-zoom-title) [data-testid="stElementToolbar"] {{ display:none !important; }}
.ba-table {{ max-height:max(calc(100vh - {TABLE_RESERVED}px), {TABLE_FLOOR}px); overflow:auto; }}
.ba-table table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
.ba-table th {{ text-align:left; font-weight:600; color:{muted}; padding:4px 8px; border-bottom:1px solid {border};
  cursor:help;  position:sticky; top:0; z-index:1; background:{card_color};}}
.ba-table td {{ padding:2px 8px; border-bottom:1px solid {border}; color:{text}; }}
.ba-table td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.ba-table td.rise {{ color:{rise}; }} .ba-table td.fall {{ color:{fall}; }}
.ba-table td.ba-product {{ padding-left:22px; }}
.ba-table tr.ba-chosen td {{ background:color-mix(in srgb, {accent} 10%, transparent); color:{ink}; font-weight:600; }}
@media (max-width:1100px) {{ .ba-cards {{ grid-template-columns:repeat(3, minmax(0, 1fr)); }} }}
/* D-458: under 1400 px the filters wrap under the six tabs; the green panel already names the period, so they drop
   their labels, and the charts accept a lower floor. */
@media (max-width:1399px) {{ .st-key-ba_filters [data-testid="stWidgetLabel"] {{ display:none !important; }}
  [class*="st-key-ba_tile_"] {{ min-height:max(calc(100vh - {TILES_RESERVED}px), {NARROW_FLOOR}px); }}
  /* D-460: the tabs and the filters keep one row down to 1250 px, so the charts keep that height. */
  .st-key-ba_tab [data-testid="stButtonGroup"] > div {{ gap:12px !important; }}
  .st-key-ba_tab button p {{ font-size:13.5px !important; }}
  .st-key-ba_filters [data-testid="stElementContainer"] {{ width:166px !important; max-width:166px !important; }}
  .st-key-ba_filters [data-testid="stElementContainer"]:last-child {{ width:172px !important; max-width:172px !important; }}
  .ba-context p {{ font-size:12.5px !important; }}
  .ba-table {{ max-height:max(calc(100vh - {TABLE_RESERVED - 35}px), {TABLE_FLOOR}px); }} }}
</style>"""


# endregion
