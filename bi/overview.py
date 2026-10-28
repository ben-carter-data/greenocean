"""«Dashboard» (D-296): the macro view of the whole project, one screen per tab, in the manner of a BI tool.

Three tabs: the market (what prices did this week and the weeks before), inflation (which families rose more than the
food CPI) and the data and its operation (the loads, the flags, the quality). Each tab has a row of scorecards with
their trend and four charts: a combined bar and line chart, a donut, ranked bars and a heat table.

Every figure is computed with the same definitions as the page it summarizes, so the dashboard and the Resumen, the
Precios e inflación page and Calidad y auditoría never disagree: the weekly change of a series compares the same regions
in both weeks (D-144), a family moves by the median of its series, «sin cambio» is below 0.05 % and a family is «al
ritmo de la inflación» within ±2 points of the CPI. Pure functions: no Streamlit.
"""

from __future__ import annotations

from typing import Any

import base64
import html
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from bi import charts, home_mockup, i18n, inflation_view

# A change smaller than this, as a fraction, reads «sin cambio», as in the Resumen.
STILL = 0.0005
QUIET = 0.3  # in %: the weekly change under which the weeks table shows only a dot (D-314)
# A state that passes (every test, every indicator in its threshold): green, never the blue of a fall.
GOOD = "#199e70"
MARKET_WEEKS = 26
HEAT_WEEKS = 8


# region Data
def comparable(variations: pd.DataFrame) -> pd.DataFrame:
    """The weekly changes that can be read: a number, not infinite."""
    return variations[variations["variation"].notna() & variations["variation"].abs().lt(float("inf"))]


def market_weeks(
    prices: pd.DataFrame,
    variations: pd.DataFrame,
    alerts: pd.DataFrame,
    weeks: int = MARKET_WEEKS,
    family: str | None = None,
) -> pd.DataFrame:
    """One row per week: the prices with a value (every national series of the week), those with a valid comparison,
    the typical change (median, in %) and the alerts. With a family, only its series."""
    if family:
        prices = prices[prices["product_group"] == family]
        variations = variations[variations["product_group"] == family]
        alerts = alerts[alerts["product_group"] == family]
    last = sorted(variations["week_start"].unique())[-weeks:]
    rows = prices[prices["week_start"].isin(last)]
    valid = comparable(variations[variations["week_start"].isin(last)])
    frame = pd.DataFrame({"week_start": last})
    frame["prices"] = frame["week_start"].map(rows.groupby("week_start").size()).fillna(0).astype(int)
    frame["comparable"] = frame["week_start"].map(valid.groupby("week_start").size()).fillna(0).astype(int)
    frame["typical"] = frame["week_start"].map(valid.groupby("week_start")["variation"].median() * 100)
    frame["alerts"] = frame["week_start"].map(alerts.groupby("week_start").size()).fillna(0).astype(int)
    return frame


def family_moves(prices: pd.DataFrame, variations: pd.DataFrame, week: Any) -> pd.DataFrame:
    """The families of one week: median change in %, prices, comparisons and their state, as in the Resumen."""
    rows = prices[prices["week_start"] == week]
    valid = comparable(variations[variations["week_start"] == week])
    frame = valid.groupby("product_group")["variation"].median().mul(100).rename("change").reset_index()
    frame["prices"] = frame["product_group"].map(rows.groupby("product_group").size()).astype(int)
    frame["comparable"] = frame["product_group"].map(valid.groupby("product_group").size()).astype(int)
    frame["state"] = frame["change"].map(state)
    frame["family"] = frame["product_group"].map(home_mockup.short_family)
    return frame.sort_values("change", ascending=False).reset_index(drop=True)


def directions(variations: pd.DataFrame, week: Any, family: str | None = None) -> pd.DataFrame:
    """How the comparable prices of one week moved: how many rose, fell or stayed (below 0.05 %), as in the Resumen."""
    rows = comparable(variations[variations["week_start"] == week])
    if family:
        rows = rows[rows["product_group"] == family]
    values = rows["variation"]
    return pd.DataFrame(
        {
            "direction": ["Subieron", "Bajaron", "Sin cambio"],
            "prices": [int((values >= STILL).sum()), int((values <= -STILL).sum()), int((values.abs() < STILL).sum())],
        }
    )


# North to south, by the official number of each region.


def state(change: float) -> str:
    """«Subió», «Bajó» or «Sin cambio» for a change in %."""
    return "Subió" if change >= STILL * 100 else "Bajó" if change <= -STILL * 100 else "Sin cambio"


def family_heat(variations: pd.DataFrame, weeks: int = HEAT_WEEKS) -> pd.DataFrame:
    """Families by week: the median change in % of the last weeks, for the heat table."""
    last = sorted(variations["week_start"].unique())[-weeks:]
    valid = comparable(variations[variations["week_start"].isin(last)])
    frame = valid.groupby(["product_group", "week_start"])["variation"].median().mul(100).rename("change").reset_index()
    frame["family"] = frame["product_group"].map(home_mockup.short_family)
    months = charts.CHILE_LOCALE["time"]["shortMonths"]
    many = len(last) > 8
    frame["week"] = [
        f"{w.day}/{w.month}" if many else f"{w.day:02d} {months[w.month - 1].lower()}" for w in frame["week_start"]
    ]
    return frame


def ipc_twelve_months(rows: pd.DataFrame) -> pd.DataFrame:
    """The food CPI's change against the same month a year before, in %, month by month."""
    ipc = (
        rows[rows["product_group"] == inflation_view.IPC_NAME]
        .sort_values("month_start")
        .set_index("month_start")["index"]
    )
    frame = ((ipc / ipc.shift(12) - 1) * 100).dropna().rename("change").reset_index()
    return frame


# endregion


# region Scorecards
def build_css(palette: dict[str, str]) -> str:
    ink, text, muted, card, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    return f"""<style>
.ov-scores {{ display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:10px; margin:0 0 2px; }}
.ov-score {{ display:flex; flex-direction:column; gap:1px; padding:6px 12px 5px; border-radius:10px; background:{card};
  border:1px solid {border}; min-width:0; }}
.ov-score-label {{ font-size:11.5px; font-weight:500; color:{muted}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ov-score-value {{ font-size:20px; font-weight:600; color:{ink}; letter-spacing:-.01em; line-height:1.15; white-space:nowrap; }}
.ov-score-foot {{ display:flex; align-items:center; justify-content:space-between; gap:8px; min-height:22px; }}
.ov-score-note {{ font-size:11.5px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ov-rise {{ color:{palette['rise']}; }} .ov-fall {{ color:{palette['fall']}; }} .ov-neutral {{ color:{text}; }}
.ov-good {{ color:{GOOD}; }}
.ov-spark {{ display:block; flex:none; }}
.ov-score {{ position:relative; cursor:help; }}
.ov-tip {{ display:none; position:absolute; top:calc(100% + 6px); left:0; z-index:60; width:max(100%, 270px); max-width:330px;
  padding:9px 12px; border-radius:10px; background:{card}; border:1px solid {border}; color:{text};
  box-shadow:0 14px 34px -14px rgba(0,0,0,.45); font-size:12px; font-weight:400; line-height:1.45; text-align:left;
  white-space:normal; letter-spacing:0; text-transform:none; }}
.ov-score:nth-child(n+4) .ov-tip {{ left:auto; right:0; }}
.ov-score:hover .ov-tip, .ov-score:focus .ov-tip {{ display:block; }}
.ov-card-title {{ position:relative; cursor:help; }}
.ov-card-title .ov-info {{ display:inline-flex; align-items:center; justify-content:center; width:15px; height:15px; margin-left:6px;
  border-radius:50%; border:1px solid {muted}; color:{muted}; font-size:10px; font-weight:600; vertical-align:2px; }}
.ov-card-title .ov-tip {{ top:calc(100% + 4px); width:min(360px, 92%); max-width:none; }}
.ov-card-title:hover .ov-tip {{ display:block; }}
.ov-card-title:hover .ov-info {{ border-color:{accent}; color:{accent}; }}
[class*="st-key-ov_card_"] {{ background:{card}; border:1px solid {border} !important; border-radius:12px !important;
  padding:12px 16px 8px !important; gap:2px !important; height:max(calc((100vh - 318px) / 2), 196px) !important;
  min-height:max(calc((100vh - 318px) / 2), 196px) !important; }}
[class*="st-key-ov_card_"] [data-testid="stElementContainer"]:has([data-testid="stVegaLiteChart"]) {{
  flex:1 1 0; min-height:0; display:flex; flex-direction:column; }}
[class*="st-key-ov_card_"] [data-testid="stFullScreenFrame"], [class*="st-key-ov_card_"] [data-testid="stFullScreenFrame"] > div,
[class*="st-key-ov_card_"] [data-testid="stVegaLiteChart"] {{ flex:1 1 auto; height:100%; min-height:0; }}
[class*="st-key-ov_card_"] [data-testid="stElementToolbar"] {{ display:none !important; }}
.st-key-ov_tabs {{ margin-top:-14px; }}
[class*="st-key-ov_card_"][class*="_small"] {{ height:auto !important; min-height:0 !important; }}
[class*="st-key-ov_card_"][class*="_wide"] {{ height:auto !important; min-height:0 !important; max-height:max(calc(100vh - 500px), 236px); overflow:auto; }}
[class*="st-key-ov_card_"][class*="_wide"] [data-testid="stElementContainer"]:has(.ov-ht),
[class*="st-key-ov_card_"][class*="_wide"] [data-testid="stElementContainer"]:has(.ov-qt) {{ flex:0 0 auto; min-height:0; overflow:visible; }}
[class*="st-key-ov_card_"][class*="_wide"] [data-testid="stMarkdown"]:has(.ov-ht),
[class*="st-key-ov_card_"][class*="_wide"] [data-testid="stMarkdownContainer"]:has(.ov-ht) {{ height:100%; }}
.st-key-ov_tabs [data-testid="stTabs"] [role="tabpanel"] {{ padding-top:10px; }}
[class*="st-key-ov_head_"] {{ align-items:center; justify-content:space-between; }}
[class*="st-key-ov_head_"] [data-testid="stSlider"] {{ padding:0 4px; }}
[class*="st-key-ov_head_"] [data-testid="stSliderTickBar"], [class*="st-key-ov_head_"] [data-testid="stTooltipIcon"] {{
  display:none !important; }}
.ov-card-title {{ margin:0 !important; font-size:14px !important; font-weight:600; color:{ink} !important; line-height:1.3 !important; }}
[class*="st-key-ov_card_"] [data-testid="stElementContainer"]:has(.ov-card-title) {{ margin-bottom:14px !important; }}
[class*="st-key-ov_card_"] [data-testid="stMarkdown"] {{ margin-bottom:0 !important; }}
.ov-card-note {{ margin:0 !important; font-size:11.5px !important; color:{muted} !important; line-height:1.35 !important;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.st-key-ov_tabs [data-baseweb="tab-list"] {{ gap:4px; }}
.st-key-ov_tabs [data-baseweb="tab"] p {{ font-size:13.5px; font-weight:600; }}
@media (max-width:1100px) {{ .ov-scores {{ grid-template-columns:repeat(3, minmax(0, 1fr)); }} }}
</style>"""


# endregion


# region Charts
def style(chart: Any, mode: str, height: int | None = None) -> Any:
    """Width and height from the card: the charts grow with the window (D-296)."""
    return charts.apply_chart_style(chart.properties(width="container", height=height or "container"), mode)


def build_heat_table_html(
    frame: pd.DataFrame,
    row: str,
    column: str,
    value: str,
    columns: list[str],
    rows: list[str],
    palette: dict[str, str],
    logos: dict[str, str] | None = None,
    totals: dict[str, float] | None = None,
    total_title: str = "",
) -> str:
    """D-301: the heat table as an HTML table that fills its card: one row per family with its picture, one column per
    period, each cell tinted by its change (red rises, blue falls, the stronger the darker) and its value written in it.
    On a narrow window the first column stays and the periods scroll."""
    cells = {(r, c): v for r, c, v in zip(frame[row], frame[column], frame[value])}
    limit = max(1.0, float(frame[value].abs().quantile(0.9))) if not frame.empty else 1.0
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in columns)
    body = []
    for name in rows:
        picture = (logos or {}).get(name)
        full = next((family for family, short in home_mockup.FAMILY_SHORT_NAMES.items() if short == name), name)
        label = (
            f'<img src="{picture}" alt="">' if picture else '<span class="ov-ht-dot"></span>'
        ) + f"<span>{html.escape(name)}</span>"
        tds = []
        for c in columns:
            v = cells.get((name, c))
            if v is None:
                tds.append('<td class="ov-ht-empty">·</td>')
                continue
            if totals is not None and abs(v) < QUIET:  # a change this small is a dot, never «-0,0» (D-314)
                tds.append('<td class="ov-ht-quiet">·</td>')
                continue
            tone = palette["rise"] if v >= STILL * 100 else palette["fall"] if v <= -STILL * 100 else None
            strength = min(1.0, abs(v) / limit)
            style = (
                f' style="background:color-mix(in srgb, {tone} {12 + strength * 70:.0f}%, transparent)"' if tone else ""
            )
            strong = " ov-ht-strong" if tone and strength > 0.6 else ""
            number = f"{v:+.1f}".replace(".", ",")
            tds.append(f'<td class="ov-ht-cell{strong}"{style}>{number}</td>')
        if totals is not None:
            total = totals.get(name)
            text = "" if total is None else ("0,0 %" if round(total, 1) == 0 else f"{total:+.1f} %".replace(".", ","))
            tds.append(f'<td class="ov-ht-total">{text}</td>')
        body.append(f'<tr><th scope="row" title="{html.escape(full, quote=True)}">{label}</th>{"".join(tds)}</tr>')
    if totals is not None:
        head += f'<th class="ov-ht-total-head">{html.escape(total_title)}</th>'
    return f'<div class="ov-ht" style="--cols:{len(columns) + (totals is not None)}"><table><thead><tr><th></th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def heat_table_css(palette: dict[str, str]) -> str:
    ink, muted, border = palette["strong_text"], palette["reference"], palette["card_border"]
    return f"""<style>
.ov-ht {{ overflow-x:auto; }}
.ov-ht table {{ width:100%; min-width:calc(170px + var(--cols) * 64px); border-collapse:collapse; table-layout:fixed; margin:0; }}
.ov-ht th, .ov-ht td {{ border:1px solid {border} !important; }}
.ov-ht thead th {{ border-top:0 !important; }}
.ov-ht thead th {{ font-size:12px; font-weight:600; color:{muted}; text-align:center; padding:0 0 2px; background:transparent !important; }}
.ov-ht thead th:first-child, .ov-ht tbody th {{ width:24%; min-width:150px; }}
.ov-ht tbody th {{ text-align:left; font-weight:600; font-size:13px; color:{ink}; padding:0 8px 0 0; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; position:sticky; left:0; background:{palette['card']} !important; }}
.ov-ht tbody th img {{ width:20px; height:20px; vertical-align:middle; margin-right:8px; object-fit:contain; }}
.ov-ht tbody th span {{ vertical-align:middle; }}
.ov-ht-dot {{ display:inline-block; width:20px; height:20px; margin-right:8px; vertical-align:middle; }}
.ov-ht td {{ text-align:center; font-size:13px; line-height:1.2; font-variant-numeric:tabular-nums; color:{ink};
  background:color-mix(in srgb, {border} 30%, transparent); padding:0 2px; min-width:54px; }}
.ov-ht td.ov-ht-strong {{ color:#ffffff; font-weight:600; }}
.ov-ht td.ov-ht-empty {{ color:{muted}; }}
.ov-ht td.ov-ht-quiet {{ color:{muted}; opacity:.55; background:transparent !important; }}
.ov-ht td.ov-ht-total {{ font-weight:700; color:{ink}; border-left:2px solid {border} !important; }}
.ov-ht thead th.ov-ht-total-head {{ color:{ink}; border-left:2px solid {border} !important; }}
</style>"""


# endregion


# region Insights (D-302)
# What the dashboard answers, the KPIs that answer it and why, and the insights of the current load.
KPIS = [
    (
        "Cambio típico",
        "Mediana de los cambios semanales de los precios comparables: los que tienen precio en las mismas "
        "regiones ambas semanas.",
        "La mediana no se mueve por un precio extremo, y comparar las mismas regiones evita "
        "confundir un cambio de cobertura con un cambio de precio.",
    ),
    (
        "Subieron y bajaron",
        "Precios comparables con un cambio de al menos +0,05 % (o −0,05 %), sobre el total de comparables.",
        "Dice si el movimiento es general o de unos pocos productos.",
    ),
    (
        "Dirección de una región",
        "Una región sube o baja solo si sus alzas y bajas difieren más de lo que da el azar "
        "(prueba de signo, p < 0,05).",
        "Un 52 % contra un 48 % no es una tendencia: es una moneda al aire.",
    ),
    (
        "Alerta de precio",
        "Un cambio fuera del promedio ± 2 desviaciones de sus 12 semanas previas, de al menos 10 % y con "
        "dos cotizaciones en cada semana.",
        "Separa lo inusual y material del ruido de cada semana.",
    ),
    (
        "Alza frente al IPC",
        "Índice de la familia (enero 2022 = 100, mediana de sus series de consumidor) frente al IPC de "
        "alimentos del INE; ± 2 puntos es «al ritmo».",
        "Dice si una familia se encareció o se abarató en términos reales.",
    ),
    (
        "Precio real",
        "Precio de la semana × IPC del último mes publicado ÷ IPC del mes de esa semana.",
        "Permite comparar precios de distintos años en pesos de hoy.",
    ),
    (
        "Brecha consumidor–mayorista",
        "(Precio al consumidor − precio mayorista) ÷ precio mayorista, mismo producto, región, unidad y semana.",
        "Muestra cuánto se agrega entre el mercado mayorista y la góndola.",
    ),
    (
        "Calidad de los datos",
        "11 indicadores en cinco dimensiones (completitud, actualidad, validez, unicidad y "
        "consistencia) más controles de exactitud.",
        "Una cifra solo vale si los datos de origen están completos y son válidos.",
    ),
]


def signed(value: float) -> str:
    """A change in %, with the decimal mark of the language: lists of names are not translated as a whole."""
    text = f"{value:+.1f} %"
    return text if i18n.is_english() else text.replace(".", ",")


def join(names: Any) -> str:
    return i18n.join_names(list(names))


def period_totals(heat: pd.DataFrame) -> pd.Series:
    """Each family's change over the whole period of the weeks table, its weekly medians chained, in %."""
    return (
        heat.sort_values("week_start")
        .groupby("family")["change"]
        .apply(lambda changes: ((1 + changes / 100).prod() - 1) * 100)
    )


def weeks_insight(heat: pd.DataFrame) -> list[str]:
    """The reading of the whole period of the weeks table (D-311, D-314): the family that got dearest and the one that
    got cheapest (the first and last of the table's Total column), how many weeks each rose or fell by at least what
    the table paints, and how many weeks more families rose than fell. Every figure comes from the table's cells."""
    weeks = heat["week_start"].nunique()
    chained = period_totals(heat)
    rose = (heat["change"] >= QUIET).groupby(heat["family"]).sum().reindex(chained.index, fill_value=0)
    fell = (heat["change"] <= -QUIET).groupby(heat["family"]).sum().reindex(chained.index, fill_value=0)
    by_week = (heat["change"] >= QUIET).groupby(heat["week_start"]).sum() - (heat["change"] <= -QUIET).groupby(
        heat["week_start"]
    ).sum()
    top, low = chained.idxmax(), chained.idxmin()
    return [
        i18n.tr("En estas {} semanas, {} es la que más se encareció: {} acumulado, con alzas en {} de ellas.").format(
            weeks, i18n.tr(top), signed(chained[top]), int(rose[top])
        ),
        i18n.tr("{} es la que más bajó: {} acumulado, con bajas en {} semanas.").format(
            i18n.tr(low), signed(chained[low]), int(fell[low])
        ),
        i18n.tr("En {} de las {} semanas subieron más familias de las que bajaron.").format(
            int((by_week > 0).sum()), weeks
        ),
    ]


def best_drops(variations: pd.DataFrame, week: Any, count: int = 3) -> list[tuple[str, str, float]]:
    """The largest weekly drops of the week, resting on two quotes in each week (as the Resumen ranks them)."""
    rows = comparable(variations[variations["week_start"] == week])
    if "same_region_quotes" in rows:
        rows = rows[(rows["same_region_quotes"] >= 2) & (rows["same_region_previous_quotes"] >= 2)]
    rows = rows[rows["variation"] < 0].nsmallest(count, "variation")
    return [
        (product, channel, value * 100)
        for product, channel, value in zip(rows["product"], rows["channel"], rows["variation"])
    ]


def consumer_insights(
    moves: pd.DataFrame, drops: list[tuple[str, str, float]], summary: pd.DataFrame, ipc_total: float, ipc_year: float
) -> list[str]:
    """For whoever buys food: what got cheaper this week and which families weigh more than inflation."""
    fell = moves[moves["state"] == "Bajó"]
    rose = moves[moves["state"] == "Subió"]
    above = summary[summary["verdict"] == "más que la inflación"]
    below = summary[summary["verdict"] == "menos que la inflación"]
    short = home_mockup.short_family
    lines = []
    if len(fell):
        lines.append(
            f"Esta semana bajaron {join(f'{short(f)} ({signed(c)})' for f, c in zip(fell['product_group'], fell['change']))}; "
            f"subieron {join(f'{short(f)} ({signed(c)})' for f, c in zip(rose['product_group'], rose['change'])) or 'ninguna familia'}."
        )
    if drops:
        lines.append(
            "Las mayores bajas, con al menos dos cotizaciones por semana: "
            + join(f"{product} · {channel.lower()} ({signed(value)})" for product, channel, value in drops)
            + "."
        )
    if len(above):
        lines.append(
            f"Desde enero 2022, {join(short(f) for f in above['family'])} subieron más que el IPC de alimentos "
            f"({signed(ipc_total)}): son las que más pesan hoy en la canasta. "
            + (
                f"{join(short(f) for f in below['family'])} subieron menos: en términos reales, se abarataron."
                if len(below)
                else ""
            )
        )
    lines.append(f"En los últimos 12 meses, los alimentos subieron {signed(ipc_year)}.")
    return lines


def architect_insights(
    latest: Any,
    tests: tuple[int, int],
    green: int,
    indicators: int,
    database: Any,
    flags: pd.DataFrame,
    comparable_now: int,
    prices_now: int,
) -> list[str]:
    """For whoever designs the data: what the load brought, how much of it reaches the indicators and where it is lost."""

    def number(value: float) -> str:
        return f"{int(value):,}".replace(",", ".")

    day = f"{latest['started_at'][8:10]}-{latest['started_at'][5:7]}-{latest['started_at'][:4]}"
    total = int(flags["weekly_prices"].sum())
    by_flag = flags.groupby("flag")["weekly_prices"].sum()
    unconvertible, outliers = int(by_flag.get("UNIDAD_NO_CONVERTIBLE", 0)), int(by_flag.get("ATIPICO", 0))

    def share(part: float) -> str:
        return f"{part / total * 100:.1f} %".replace(".", ",")

    lines = [
        f"La carga del {day} leyó {number(latest['rows_read'])} filas de los archivos de ODEPA y rechazó "
        f"{number(latest['rows_rejected'])} con su motivo; pasaron {tests[0]} de {tests[1]} pruebas de dbt y {green} de "
        f"{indicators} indicadores de calidad están en su umbral.",
        f"La base servida tiene {number(database['prices'])} precios semanales en {number(database['weeks'])} semanas sin "
        f"huecos, de {database['regions']} regiones y {database['channels']} canales.",
    ]
    if unconvertible or outliers:
        bigger = "las unidades que no se pueden convertir" if unconvertible >= outliers else "los precios atípicos"
        lines.append(
            f"{number(unconvertible)} precios ({share(unconvertible)}) quedan fuera de los indicadores por unidad no "
            f"convertible y {number(outliers)} ({share(outliers)}) por atípicos: la mayor pérdida está en {bigger}, "
            "donde una regla nueva sumaría más datos."
        )
    lines.append(
        f"Esta semana, {number(comparable_now)} de {number(prices_now)} precios tienen comparación con la anterior: "
        "el resto no tiene precio la semana previa en las mismas regiones."
    )
    return lines


# endregion


def wholesale_insights(variations: pd.DataFrame, week: Any, margins: pd.DataFrame) -> list[str]:
    """For whoever buys wholesale (a shop, a restaurant): how the wholesale price moved this week, its biggest drops and
    the gap up to the consumer price. ODEPA's wholesale prices cover fruit and vegetables only."""
    short = home_mockup.short_family
    rows = comparable(variations[(variations["week_start"] == week) & (variations["channel"] == "Mayorista")])
    lines = []
    if not rows.empty:
        moves = rows.groupby("product_group")["variation"].median().mul(100)
        lines.append(
            "En el mercado mayorista, el cambio típico de la semana fue "
            + join(f"{short(f)} {signed(v)}" for f, v in moves.items())
            + "."
        )
        drops = list(
            {
                product: (product, channel, value)
                for product, channel, value in reversed(best_drops(rows.assign(week_start=week), week, count=8))
            }.values()
        )[::-1][:3]
        if drops:
            lines.append(
                "Las mayores bajas mayoristas: "
                + join(f"{product} ({signed(value)})" for product, _, value in drops)
                + "."
            )
    week_margins = margins[margins["week_start"] == f"{week:%Y-%m-%d}"]
    if not week_margins.empty:
        gaps = week_margins.groupby("product_group")["margin"].median().mul(100)
        lines.append(
            "Del precio mayorista al consumidor, el mismo producto sube típicamente "
            + join(f"{short(f)} {signed(v)}" for f, v in gaps.items())
            + ": es el margen que separa la compra por mayor de la góndola."
        )
    lines.append("ODEPA publica precios mayoristas solo de frutas y hortalizas.")
    return lines


# region Points of sale (D-306): what exists in each region; the Insights read it
POINTS_FILE = Path(__file__).with_name("assets") / "points_of_sale.json"


def read_points() -> dict[str, Any]:
    """{region: {wholesale, consumer, sectors}}: what exists in each region, from ODEPA's own files (no price)."""
    return json.loads(POINTS_FILE.read_text(encoding="utf-8"))


POINT_ICONS = {
    "person": "persona",
    "mercado": "mercado",
    "datos": "datos",
    "Supermercado": "supermercado",
    "Supermercado en Línea": "linea",
    "Feria libre": "feria",
    "Carnicería": "carniceria",
    "Panadería": "panaderia",
    "Mercado Minorista": "minorista",
    "Mercado Mayorista": "mercado",
}


@lru_cache(maxsize=None)
def point_icon(name: str) -> str:
    """An icon of the folder bi/assets/points as an image (st.html drops inline SVG)."""
    path = POINTS_FILE.parent / "points" / f"{POINT_ICONS.get(name, 'mercado')}.svg"
    return (
        f'<img class="ov-icon" alt="" src="data:image/svg+xml;base64,{base64.b64encode(path.read_bytes()).decode()}">'
    )


# endregion
