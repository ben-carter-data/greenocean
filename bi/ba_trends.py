"""«Análisis BA y BI» (D-456, D-457): the history of food prices, read two ways that never mix. «Mensual» is one
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

from bi import charts, home_mockup, i18n, inflation_view, overview, weeks

BASKET = inflation_view.BASKET_NAME
IPC = inflation_view.IPC_NAME
BASE = (inflation_view.BASE_YEAR, inflation_view.BASE_MONTH)
LAST_YEAR = "Últimos 12 meses"
PACE = inflation_view.SAME_PACE_POINTS
ZOOM_WIDTH, ZOOM_HEIGHT = 680, 250  # the enlarged chart, inside a window never wider than the page

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


def family_label(family: str) -> str:
    """The family as a chart or a table names it."""
    return say("Toda la canasta", "The whole basket") if family == BASKET else home_mockup.short_family(family)


def family_name(family: str) -> str:
    """The family inside a sentence: «toda la canasta», «la familia Frutas»."""
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


def month_domain(start: tuple[int, int], end: tuple[int, int], counted: bool = False) -> list[str]:
    """The time axis of a chart: the whole period, so every chart starts at its start month even where it has no data
    (no alert can be raised in the first 12 weeks of the history). counted: from the first month whose weeks count."""
    first = first_counted(start, end) if counted else start
    last = next_month(end) if counted else end  # bars fill their month, so the axis runs to the end of the last one
    return [f"{first[0]}-{first[1]:02d}-01", f"{last[0]}-{last[1]:02d}-01"]


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
    months = [start]
    while months[-1] < end:
        months.append(next_month(months[-1]))
    key = rows["year"] * 100 + rows["month"]
    panel = rows[
        rows["product_group"].isin([family, IPC]) & key.between(start[0] * 100 + start[1], end[0] * 100 + end[1])
    ]
    wide = panel.pivot_table(index=["year", "month"], columns="product_group", values="index")
    wide = wide.reindex(pd.MultiIndex.from_tuples(months, names=["year", "month"]))
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
            say(f"{span(first_week, end)} · subidas y bajadas (K6)", f"{span(first_week, end)} · rises and falls (K6)"),
            say(
                f"Las semanas en que un producto de {name} cambió fuera de su rango habitual (K6): los valores "
                f"atípicos.{first_alert}",
                f"The weeks in which a product of {name} changed outside its usual range (K6): the outliers.{first_alert}",
            ),
            say("Ninguna alerta en el período.", "No alert in the period.")
            if busiest is None
            else say(
                f"{charts.format_thousands(figures['alerts'])} alertas: {charts.format_thousands(figures['rises'])} "
                f"subidas y {charts.format_thousands(figures['falls'])} bajadas. El mes con más fue "
                f"{month_label(busiest[:2])}, con {charts.format_thousands(busiest[2])}.",
                f"{charts.format_thousands(figures['alerts'])} alerts: {charts.format_thousands(figures['rises'])} rises "
                f"and {charts.format_thousands(figures['falls'])} falls. The month with most was "
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
    """One KPI card: what it measures, its figure, one line under it and, on hover, how it is computed."""
    return (
        f'<div class="ba-card" tabindex="0" title="{html.escape(hint, quote=True)}"><span class="ba-card-label">'
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
            f"Cambio del índice de {month_label(start)} a {month_label(end)}.",
            f"Change of the index from {month_label(start)} to {month_label(end)}.",
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
            f"{charts.format_thousands(figures['rises'])} subidas · {charts.format_thousands(figures['falls'])} bajadas",
            f"{charts.format_thousands(figures['rises'])} rises · {charts.format_thousands(figures['falls'])} falls",
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
def sized(chart: Any, width: Any, height: int, mode: str) -> Any:
    return charts.apply_chart_style(chart.properties(width=width, height=height), mode)


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
        value=lambda frame: frame["index"] / frame["product_group"].map(first) * 100,
        serie=lambda frame: frame["product_group"].map({family: names[0], IPC: names[1]}),
    )
    color = inflation_view.FAMILY_COLORS.get(family, palette["accent"])
    several_years = end[0] - start[0] > 2
    chart = (
        alt.Chart(panel)
        .mark_line(interpolate="monotone", strokeWidth=2.4)
        .encode(
            x=alt.X(
                "month_start:T",
                title=None,
                scale=alt.Scale(domain=month_domain(start, end)),
                axis=alt.Axis(format="%Y" if several_years else "%b %Y", tickCount=6, labelFontSize=10),
            ),
            y=alt.Y("value:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(labelFontSize=10, tickCount=4)),
            color=alt.Color(
                "serie:N", scale=alt.Scale(domain=names, range=[color, palette["strong_text"]]), legend=None
            ),
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
            x=alt.X("mes:N", sort=order, title=None, axis=alt.Axis(labelAngle=-45, labelFontSize=9)),
            y=alt.Y("change:Q", title=None, axis=alt.Axis(labelFontSize=10, tickCount=4)),
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
    """The K6 alerts of each month, rises over falls, on the whole period's axis."""
    palette = charts.get_palette(mode)
    rises, falls = say("Subidas", "Rises"), say("Bajadas", "Falls")
    if alert_rows.empty:
        frame = pd.DataFrame(columns=["month_start", "kind", "alerts"])
    else:
        stamp = pd.to_datetime(alert_rows["week_start"])
        frame = (
            alert_rows.assign(
                month_start=stamp.dt.to_period("M").dt.to_timestamp(),
                kind=[rises if value > 0 else falls for value in alert_rows["variation"]],
            )
            .groupby(["month_start", "kind"], as_index=False)
            .size()
            .rename(columns={"size": "alerts"})
        )
    chart = (
        alt.Chart(frame)
        .mark_bar()
        .encode(
            x=alt.X(
                "month_start:T",
                timeUnit="yearmonth",
                title=None,
                scale=alt.Scale(domain=month_domain(start, end, counted=True)),
                axis=alt.Axis(format="%b %Y", tickCount=6, labelFontSize=10),
            ),
            y=alt.Y("alerts:Q", title=None, stack="zero", axis=alt.Axis(labelFontSize=10, tickCount=4)),
            color=alt.Color(
                "kind:N", scale=alt.Scale(domain=[rises, falls], range=[palette["rise"], palette["fall"]]), legend=None
            ),
            tooltip=[
                alt.Tooltip("month_start:T", title=say("Mes", "Month"), format="%b %Y"),
                alt.Tooltip("kind:N", title=say("Tipo", "Kind")),
                alt.Tooltip("alerts:Q", title=say("Alertas", "Alerts")),
            ],
        )
    )
    return sized(chart, width, height, mode)


def years_chart(years: pd.DataFrame, mode: str, width: Any = "container", height: int = 150) -> Any:
    """The change of each year: a bar for the family, a short line for the food IPC of that year."""
    palette = charts.get_palette(mode)
    rose, fell = say("subió", "rose"), say("bajó", "fell")
    frame = years.assign(
        label=[f"{year} ({note})" if note else year for year, note in zip(years["year"], years["note"])],
        tone=[rose if value > 0 else fell for value in years["change"]],
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
            x=alt.X("year:N", title=None, axis=alt.Axis(labelAngle=0, labelFontSize=10)),
            y=alt.Y("change:Q", title=None, axis=alt.Axis(labelFontSize=10, tickCount=4)),
            color=alt.Color(
                "tone:N", scale=alt.Scale(domain=[rose, fell], range=[palette["rise"], palette["fall"]]), legend=None
            ),
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
            x=alt.X("mes:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=10)),
            y=alt.Y(
                "change:Q",
                title=None,
                axis=alt.Axis(
                    labelFontSize=10, tickCount=4, labelExpr="datum.value > 0 ? '+' + datum.label : datum.label"
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
    header = f"<th>{html.escape(say('Familia', 'Family'))}</th>" + "".join(
        f'<th title="{html.escape(hint, quote=True)}">{html.escape(label)}</th>' for label, hint, _ in columns
    )
    body = []
    for item in summaries:
        lit = ' class="ba-chosen"' if item["family"] == chosen else ""
        cells = []
        for _, _, cell in columns:
            text, shade, numeric = cell(item)
            cells.append(f'<td class="{"num " if numeric else ""}{shade}">{html.escape(text)}</td>')
        body.append(f"<tr{lit}><td>{html.escape(family_label(item['family']))}</td>{''.join(cells)}</tr>")
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


# region Zoom
def zoom_text(measures: str, deduce: str) -> str:
    """The words of an enlarged chart: what it measures and what follows from it."""
    return (
        f'<p class="ba-zoom-line"><b>{html.escape(say("Qué mide", "What it measures"))}</b> {html.escape(measures)}</p>'
        f'<p class="ba-zoom-line"><b>{html.escape(say("Qué se deduce", "What follows"))}</b> {html.escape(deduce)}</p>'
    )


def build_css(palette: dict[str, str]) -> str:
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
.ba-card {{ display:flex; flex-direction:column; gap:2px; padding:10px 12px; border:1px solid {border}; border-radius:12px;
  background:{card_color}; cursor:help; outline:none; }}
.ba-card:hover, .ba-card:focus-visible {{ border-color:{accent}; }}
.ba-card-label {{ font-size:12px; line-height:1.25; color:{muted}; }}
.ba-card-value {{ font-size:24px; font-weight:700; color:{ink}; font-variant-numeric:tabular-nums; line-height:1.2; }}
.ba-card-value.rise {{ color:{rise}; }} .ba-card-value.fall {{ color:{fall}; }}
.ba-card-note {{ font-size:11.5px; line-height:1.3; color:{text}; display:-webkit-box; -webkit-line-clamp:2;
  -webkit-box-orient:vertical; overflow:hidden; }}
.ba-chart-title {{ margin:0 !important; font-size:13.5px !important; font-weight:600; color:{ink} !important;
  line-height:1.3 !important; }}
.ba-chart-title span {{ display:block; font-weight:400; color:{muted}; font-size:11.5px; }}
/* D-457: a chart grows on hover, never past the page, and says what it measures and what follows from it. */
[class*="st-key-ba_tile_"] {{ position:relative; cursor:zoom-in; }}
[class*="st-key-ba_tile_"] [data-testid="stElementToolbar"] {{ display:none !important; }}
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-ba_zoom_"]) {{ display:contents; }}
[class*="st-key-ba_zoom_"] {{ position:absolute !important; top:-10px; z-index:60;
  width:min({ZOOM_WIDTH + 70}px, 72vw) !important; max-width:none !important; gap:6px !important; padding:12px 16px 10px;
  border:1px solid {accent}; border-radius:14px; background:{card_color}; box-shadow:0 18px 40px -16px rgba(0,0,0,.55);
  opacity:0; visibility:hidden; pointer-events:none; cursor:default;
  transition:opacity .15s ease .15s, visibility 0s linear .3s; }}
[class*="st-key-ba_tile_"]:hover [class*="st-key-ba_zoom_"] {{ opacity:1; visibility:visible; pointer-events:auto;
  transition:opacity .15s ease .15s; }}
.st-key-ba_zoom_0 {{ left:-10px; }} .st-key-ba_zoom_1 {{ left:50%; transform:translateX(-50%); }}
.st-key-ba_zoom_2 {{ right:-10px; }}
.ba-zoom-line {{ margin:0 0 3px !important; font-size:13px !important; line-height:1.45 !important;
  color:{text} !important; }}
.ba-zoom-line b {{ color:{ink}; margin-right:4px; }}
.ba-table table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
.ba-table th {{ text-align:left; font-weight:600; color:{muted}; padding:5px 8px; border-bottom:1px solid {border};
  cursor:help; }}
.ba-table td {{ padding:3px 8px; border-bottom:1px solid {border}; color:{text}; }}
.ba-table td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.ba-table td.rise {{ color:{rise}; }} .ba-table td.fall {{ color:{fall}; }}
.ba-table tr.ba-chosen td {{ background:color-mix(in srgb, {accent} 10%, transparent); color:{ink}; font-weight:600; }}
@media (max-width:1100px) {{ .ba-cards {{ grid-template-columns:repeat(3, minmax(0, 1fr)); }} }}
</style>"""


# endregion
