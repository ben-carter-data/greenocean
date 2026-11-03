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
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

from bi import alerts, charts, data_terms, home_mockup, i18n, inflation_view
from bi.weeks import week_range

# A change smaller than this, as a fraction, reads «sin cambio», as in the Resumen.
STILL = 0.0005
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
    frame["week"] = [week_range(w) for w in frame["week_start"]]  # D-374: the range, never the Monday alone
    return frame


def normalize_search(text: str) -> str:
    """Lower case without accents: «Ají», «aji» and «AJI» read the same."""
    decomposed = unicodedata.normalize("NFD", str(text).lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").strip()


def matches_search(row: dict[str, Any], query: str) -> bool:
    """True when every searched word starts a word of the product or its variety (the products table's rule)."""
    words = re.split(r"[^0-9a-zñ]+", normalize_search(f"{row['product']} {row['variety']}"))
    return all(any(word.startswith(term) for word in words) for term in normalize_search(query).split())


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


# endregion


# region Insights (D-302)
# What the dashboard answers, the KPIs that answer it and why, and the insights of the current load.
# D-385: the code of the technical indicator (K1 to K8, «Indicadores explicados») each business KPI is, if any.
KPI_CODES = {"Alerta de precio": "K6", "Brecha consumidor–mayorista": "K1", "Calidad de los datos": "K8"}
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
        alerts.describe_rule(),  # D-385: the rule of bi/alerts.py, never written by hand
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
        "11 indicadores de calidad de los datos, medidos en cada carga, en cinco dimensiones (completitud, actualidad, "
        "validez, unicidad y consistencia) más controles de exactitud.",
        "Una cifra solo vale si los datos de origen están completos y son válidos.",
    ),
]


def signed(value: float) -> str:
    """A change in %, with the decimal mark of the language: lists of names are not translated as a whole."""
    text = f"{value:+.1f} %"
    return text if i18n.is_english() else text.replace(".", ",")


def join(names: Any) -> str:
    return i18n.join_names(list(names))


def best_drops(variations: pd.DataFrame, week: Any, count: int = 3) -> list[tuple[str, str, float, str]]:
    """The largest weekly drops of the week, resting on two quotes in each week (as the Resumen ranks them); D-478: each
    with its family, so a product is always found under its family."""
    rows = comparable(variations[variations["week_start"] == week])
    if "same_region_quotes" in rows:
        rows = rows[(rows["same_region_quotes"] >= 2) & (rows["same_region_previous_quotes"] >= 2)]
    rows = rows[rows["variation"] < 0].nsmallest(count, "variation")
    # D-482: the variety too, so two varieties of one product never read like the same product twice
    varieties = rows["variety"] if "variety" in rows else pd.Series("", index=rows.index)
    return [
        (product if variety in ("", "Sin especificar") else f"{product} {variety}", channel, value * 100, family)
        for product, variety, channel, value, family in zip(
            rows["product"], varieties.fillna(""), rows["channel"], rows["variation"], rows["product_group"]
        )
    ]


def consumer_insights(
    moves: pd.DataFrame,
    drops: list[tuple[str, str, float, str]],
    summary: pd.DataFrame,
    ipc_total: float,
    ipc_year: float,
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
            f"Esta semana, en mediana frente a la semana anterior, bajaron {join(f'{short(f)} ({signed(c)})' for f, c in zip(fell['product_group'], fell['change']))}; "
            f"subieron {join(f'{short(f)} ({signed(c)})' for f, c in zip(rose['product_group'], rose['change'])) or 'ninguna familia'}."
        )
    if drops:
        lines.append(
            "Las mayores bajas, con al menos dos cotizaciones por semana: "
            + join(
                f"{product} · {data_terms.term(short(family))} · {data_terms.term(channel).lower()} ({signed(value)})"
                for product, channel, value, family in drops
            )
            + "."
        )
    if len(above):
        lines.append(
            f"Desde enero 2022, {join(short(f) for f in above['family'])} subieron más de {inflation_view.SAME_PACE_POINTS:.0f} puntos sobre "
            f"el IPC de alimentos ({signed(ipc_total)}). "
            + (
                f"{join(short(f) for f in below['family'])} quedaron más de {inflation_view.SAME_PACE_POINTS:.0f} puntos por debajo: en "
                "términos reales, se abarataron."
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
        f"{indicators} indicadores de calidad de los datos están en su umbral.",
        f"La Base DuckDB tiene {number(database['prices'])} precios semanales en {number(database['weeks'])} semanas sin "
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
            "En el mercado mayorista, la mediana del cambio frente a la semana anterior fue "
            + join(f"{short(f)} {signed(v)}" for f, v in moves.items())
            + "."
        )
        drops = list(
            {
                product: (product, channel, value, family)
                for product, channel, value, family in reversed(best_drops(rows.assign(week_start=week), week, count=8))
            }.values()
        )[::-1][:3]
        if drops:
            lines.append(
                "Las mayores bajas mayoristas, con al menos dos cotizaciones por semana: "
                + join(f"{product} · {short(family)} ({signed(value)})" for product, _, value, family in drops)
                + "."
            )
    week_margins = margins[margins["week_start"] == f"{week:%Y-%m-%d}"]
    if not week_margins.empty:
        gaps = week_margins.groupby("product_group")["margin"].median().mul(100)
        lines.append(
            "Del precio mayorista al consumidor, el mismo producto sube en mediana (brecha K1) "
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
