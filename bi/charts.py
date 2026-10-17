"""Charts and visual style of the dashboard, drawn with Altair (installed with Streamlit).

Every chart takes the active theme (Corporativo, Vantablack, Blue Light or Dark Grey)
and uses its palette.
Every channel keeps the same hue in every chart, so a reader learns it once.
Numbers in labels and tooltips are written as in Chile: 1.234 and 12,5 %.
"""
import altair as alt
import pandas as pd

# region Constants
# The four visible themes, Corporativo first: it is the default (D-071). Claro remains an
# export compatibility palette. Each theme sits on one of Streamlit's two base modes,
# which decides the colors of its own widgets (lists, tables, code).
MODE_DARK = "Vantablack"
MODE_CORPORATE = "Corporativo"
MODE_BLUE_LIGHT = "Blue Light"
MODE_GRAPHITE = "Dark Grey"
MODE_LIGHT = "Claro"
THEMES = [MODE_CORPORATE, MODE_DARK, MODE_BLUE_LIGHT, MODE_GRAPHITE]
BASE_DARK = "dark"
BASE_LIGHT = "light"

# Categorical palette validated for color blindness, one step per base mode
# (checked against each theme's card color). The wholesale price is a reference,
# so it gets neutral ink instead of a hue.
DARK_CHANNELS = {"Feria libre": "#3987e5", "Supermercado": "#d95926",
                 "Supermercado en Línea": "#199e70", "Mercado Minorista": "#c98500",
                 "Carnicería": "#d55181", "Panadería": "#008300",
                 "Mercado Mayorista": "#9085e9", "Mayorista": "#c3c2b7"}
LIGHT_CHANNELS = {"Feria libre": "#2a78d6", "Supermercado": "#eb6834",
                  "Supermercado en Línea": "#1baf7a", "Mercado Minorista": "#eda100",
                  "Carnicería": "#e87ba4", "Panadería": "#008300",
                  "Mercado Mayorista": "#6250d6", "Mayorista": "#52514e"}
PALETTES = {
    # Deep black with a cold cyan light on what matters (links, active tab, focus).
    MODE_DARK: {
        "base": BASE_DARK, "channels": DARK_CHANNELS,
        "rise": "#e66767", "fall": "#3987e5", "accent": "#2fd3f0",
        "text": "#c4ccd9", "grid": "#303b4b", "reference": "#94a3b8",
        "card": "#121a27", "card_border": "#344256", "strong_text": "#f3f5f9",
        "background": "#030304", "field": "#202c3d", "sidebar": "#0b111b", "sidebar_text": "#d6dae3",
        "glow": "rgba(47, 211, 240, 0.35)", "on_accent": "#021216",
    },
    # Neutral and serious: navy sidebar, cool grey page, white cards, business blue.
    MODE_CORPORATE: {
        "base": BASE_LIGHT, "channels": LIGHT_CHANNELS,
        "rise": "#e34948", "fall": "#2a78d6", "accent": "#1d5fbf",
        "text": "#475467", "grid": "#e4e9f0", "reference": "#7b8798",
        "card": "#ffffff", "card_border": "#d6dde8", "strong_text": "#0f1b2d",
        "background": "#eef2f7", "field": "#f3f6fa", "sidebar": "#0f2a4a", "sidebar_text": "#e6edf7",
        "glow": "rgba(29, 95, 191, 0.0)", "on_accent": "#ffffff",
    },
    # Very light blue page, white panels, dark ink and blue accents.
    MODE_BLUE_LIGHT: {
        "base": BASE_LIGHT, "channels": LIGHT_CHANNELS,
        "rise": "#e34948", "fall": "#2a78d6", "accent": "#1565d8",
        "text": "#3b4a63", "grid": "#dfe9f6", "reference": "#7b8798",
        "card": "#ffffff", "card_border": "#c9dbf3", "strong_text": "#0b1f3a",
        "background": "#eaf3ff", "field": "#f1f7ff", "sidebar": "#dcebff",
        "sidebar_text": "#0b1f3a", "glow": "rgba(21, 101, 216, 0.0)", "on_accent": "#ffffff",
    },
    # Dark Grey: charcoal page, deep-grey panels and the project's cyan, the same one
    # Streamlit gives its own controls on the dark base (D-071).
    MODE_GRAPHITE: {
        "base": BASE_DARK, "channels": DARK_CHANNELS,
        "rise": "#ef6a6a", "fall": "#5b9cf0", "accent": "#2fd3f0",
        "text": "#c5c5d2", "grid": "#4a4a4f", "reference": "#a3a3ad",
        "card": "#2f2f2f", "card_border": "#505055", "strong_text": "#f3f3f3",
        "background": "#212121", "field": "#424242", "sidebar": "#171717",
        "sidebar_text": "#ececec", "glow": "rgba(47, 211, 240, 0.18)",
        "on_accent": "#021216",
    },
    # Light and crisp: white and cool greys, no warm beige.
    MODE_LIGHT: {
        "base": BASE_LIGHT, "channels": LIGHT_CHANNELS,
        "rise": "#e34948", "fall": "#2a78d6", "accent": "#2563eb",
        "text": "#4b5563", "grid": "#eceff3", "reference": "#a3a9b4",
        "card": "#ffffff", "card_border": "#e3e7ed", "strong_text": "#111827",
        "background": "#f8f9fb", "field": "#f3f5f8", "sidebar": "#ffffff", "sidebar_text": "#1f2937",
        "glow": "rgba(37, 99, 235, 0.0)", "on_accent": "#ffffff",
    },
}
# Sequential ramps for a heat map, one hue, light (cheap) to dark (expensive):
# cyan in the dark themes, the business blue in the light ones. Each validated as an
# ordinal ramp against the card color of its theme (dataviz validator).
HEAT_RAMPS = {MODE_DARK: ["#a5f3fc", "#22d3ee", "#0891b2", "#155e75"],
              MODE_GRAPHITE: ["#2a8199", "#36a6c2", "#5fcbe3", "#a8eef9"],
              MODE_CORPORATE: ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"],
              MODE_BLUE_LIGHT: ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"],
              MODE_LIGHT: ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]}
# Status colors (fixed in every theme), always shown with an icon and a label.
STATUS_COLORS = {"good": "#22b35a", "warning": "#fab219", "serious": "#ec835a",
                 "critical": "#d03b3b", "running": "#5b9cf0", "unknown": "#8a8984"}
# On a white card the bright steps fall under 3:1, so their text takes a darker step
# of the same hue (4.5:1 or more on white). Marks (bars, dots) keep the bright step.
STATUS_TEXT_ON_LIGHT = {"good": "#15803d", "warning": "#a16207", "serious": "#c2410c",
                        "critical": "#b91c1c", "running": "#1d4ed8", "unknown": "#57534e"}
MONTH_NAMES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov",
               "dic"]
CHART_FONT = "Source Sans Pro, sans-serif"
CHART_HEIGHT = 300
SPARKLINE_HEIGHT = 70
BAR_HEIGHT = 28
# Share of the value axis left free beyond the bars, so their labels fit.
BAR_LABEL_ROOM = 0.18
# Month and year: with several years loaded, a day and month alone repeat and
# cannot be told apart.
WEEK_AXIS_FORMAT = "%b %Y"
# A few weeks: day and month, so no label repeats.
SHORT_WEEK_AXIS_FORMAT = "%d-%m"
MONEY_AXIS_FORMAT = ",.0f"
# Numbers and dates of every chart as in Chile: 1.234,5 and "mar 2024".
CHILE_LOCALE = {
    "number": {"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["$ ", ""],
               "minus": "-"},
    "time": {"dateTime": "%A, %e de %B de %Y, %X", "date": "%d-%m-%Y", "time": "%H:%M:%S",
             "periods": ["AM", "PM"],
             "days": ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes",
                      "sábado"],
             "shortDays": ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"],
             "months": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                        "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
             "shortMonths": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep",
                             "oct", "nov", "dic"]},
}
# Words removed from region names in charts, where space is short.
REGION_PREFIXES = ["Región de ", "Región del ", "Región "]
# endregion


# region Formats
def remove_negative_zero(value, decimals):
    """A value that rounds to zero is written 0, never -0."""
    return 0.0 if round(value, decimals) == 0 else value


def format_thousands(value):
    """1234.5 -> '1.235'."""
    return f"{value:,.0f}".replace(",", ".")


def format_percent(value, decimals=1):
    """A value already in percent: 12.34 -> '12,3 %'."""
    return f"{remove_negative_zero(value, decimals):.{decimals}f} %".replace(".", ",")


def format_signed_percent(value):
    """A value already in percent, with its sign: 12.34 -> '+12,3 %'."""
    return f"{value:+.1f} %".replace(".", ",")


def format_index(value):
    """An index around 1: 1.234 -> '1,23'."""
    return f"{remove_negative_zero(value, 2):.2f}".replace(".", ",")


def describe_weekly_change(change):
    """A change in percent in plain words: 12.3 -> 'Subió 12,3 % frente a la semana anterior'."""
    if round(change, 1) == 0:
        # Same rule as the arrow «=»: a change that rounds to 0,0 % did not move.
        return "Sin cambio frente a la semana anterior"
    verb = "Subió" if change > 0 else "Bajó"
    return f"{verb} {format_percent(abs(change))} frente a la semana anterior"


def describe_regional_index(index):
    """1.46 -> '46 % más caro que el promedio nacional'."""
    if round(index, 2) == 1:
        return "Igual al promedio nacional"
    word = "más caro" if index > 1 else "más barato"
    return f"{format_percent(abs(index - 1) * 100, decimals=0)} {word} que el promedio nacional"


def describe_weeks(weeks):
    """0 -> 'la misma semana', 1 -> '1 semana', 3 -> '3 semanas'."""
    if weeks == 0:
        return "la misma semana"
    return "1 semana" if weeks == 1 else f"{weeks} semanas"


def describe_margin(margin):
    """A margin in percent: 145 -> 'El consumidor paga 2,45 veces el precio mayorista'."""
    times = f"{1 + margin / 100:.2f}".replace(".", ",")
    return f"El consumidor paga {times} veces el precio mayorista"


def describe_channel_gap(gap, reference_channel):
    """62.7 -> '62,7 % más caro que Feria libre'."""
    word = "más caro" if gap > 0 else "más barato"
    return f"{format_percent(abs(gap))} {word} que {reference_channel}"


def shorten_region_name(region):
    """'Región Metropolitana de Santiago' -> 'Metropolitana de Santiago'."""
    for prefix in REGION_PREFIXES:
        if region.startswith(prefix):
            return region[len(prefix):]
    return region
# endregion


# region Shared pieces
def get_palette(mode):
    """Palette of the active theme; Vantablack when the theme is unknown."""
    return PALETTES.get(mode, PALETTES[MODE_CORPORATE])


def get_status_text_color(status, mode):
    """Color of a status written as text: bright on Vantablack, darker on light themes."""
    base = get_palette(mode)["base"]
    return (STATUS_TEXT_ON_LIGHT if base == BASE_LIGHT else STATUS_COLORS)[status]


def get_channel_color(channel, mode):
    """Fixed color of one channel in the active mode."""
    palette = get_palette(mode)
    return palette["channels"].get(channel, palette["accent"])


def build_channel_color_scale(channels, mode):
    """Color scale with only the channels present, each with its fixed color.

    Series that are not channels (products or regions in the Consultas page)
    take the same validated colors, in order.
    """
    channel_colors = get_palette(mode)["channels"]
    present_channels = [channel for channel in channel_colors if channel in set(channels)]
    if not present_channels:
        series_names = sorted(set(channels))
        colors = list(channel_colors.values())
        return alt.Scale(domain=series_names, range=[
            colors[position % len(colors)] for position in range(len(series_names))])
    return alt.Scale(domain=present_channels,
                     range=[channel_colors[channel] for channel in present_channels])


def apply_chart_style(chart, mode):
    """Transparent background, quiet grid and the mode's text colors."""
    palette = get_palette(mode)
    return chart.configure(background="transparent", font=CHART_FONT,
                           locale=CHILE_LOCALE).configure_view(
        strokeWidth=0).configure_axis(
        gridColor=palette["grid"], domain=False, ticks=False,
        labelColor=palette["text"], titleColor=palette["text"],
        labelFontSize=12, titleFontSize=12, titleFontWeight="normal").configure_legend(
        labelColor=palette["text"], titleColor=palette["text"], orient="bottom",
        symbolType="circle")


def add_week_labels(rows, value_labels):
    """Columns shown in tooltips: the week as dd-mm-yyyy and the formatted value."""
    return rows.assign(week_label=rows["week_start"].dt.strftime("%d-%m-%Y"),
                       value_label=value_labels)
# endregion


# region Charts
def draw_sparkline(rows, color, mode):
    """Small area chart without axes, for a key figure card (rows: week_start, value)."""
    line = alt.Chart(rows).mark_area(
        line={"color": color, "strokeWidth": 2}, color=color, opacity=0.18,
        interpolate="monotone").encode(
        x=alt.X("week_start:T", axis=None),
        y=alt.Y("value:Q", axis=None, scale=alt.Scale(zero=False)))
    return apply_chart_style(line.properties(height=SPARKLINE_HEIGHT), mode)


def draw_weekly_lines(rows, value_title, value_labels, mode, is_money):
    """Lines by week, one per channel, with a tooltip on every point.

    rows needs the columns week_start, channel and value.
    """
    rows = add_week_labels(rows, value_labels)
    value_axis = (alt.Axis(format=MONEY_AXIS_FORMAT) if is_money
                  else alt.Axis(format=".2f", tickCount=5, labelOverlap=True))
    base = alt.Chart(rows).encode(
        x=alt.X("week_start:T", title=None, axis=alt.Axis(format=WEEK_AXIS_FORMAT)),
        y=alt.Y("value:Q", title=value_title, axis=value_axis, scale=alt.Scale(zero=False)),
        color=alt.Color("channel:N", title=None,
                        scale=build_channel_color_scale(rows["channel"], mode)))
    lines = base.mark_line(strokeWidth=2.5, interpolate="monotone")
    # Invisible wide points: easy to hover, and they carry the tooltip.
    hover_points = base.mark_point(size=160, opacity=0).encode(
        tooltip=[alt.Tooltip("week_label:N", title="Semana"),
                 alt.Tooltip("channel:N", title="Canal"),
                 alt.Tooltip("value_label:N", title=value_title)])
    chart = alt.layer(lines, hover_points).properties(height=CHART_HEIGHT)
    return apply_chart_style(chart, mode)


def draw_single_weekly_area(rows, value_title, value_labels, mode, reference_value=None,
                            is_money=False, week_format=WEEK_AXIS_FORMAT):
    """One series by week as a soft area (rows: week_start, value)."""
    rows = add_week_labels(rows, value_labels)
    color = get_palette(mode)["accent"]
    value_axis = alt.Axis(format=MONEY_AXIS_FORMAT) if is_money else alt.Axis()
    base = alt.Chart(rows).encode(
        x=alt.X("week_start:T", title=None, axis=alt.Axis(format=week_format)),
        y=alt.Y("value:Q", title=value_title, axis=value_axis, scale=alt.Scale(zero=False)))
    area = base.mark_area(line={"color": color, "strokeWidth": 2.5}, color=color,
                          opacity=0.16, interpolate="monotone")
    hover_points = base.mark_point(size=160, opacity=0).encode(
        tooltip=[alt.Tooltip("week_label:N", title="Semana"),
                 alt.Tooltip("value_label:N", title=value_title)])
    layers = [area, hover_points]
    if reference_value is not None:
        layers.insert(0, alt.Chart(rows).mark_rule(
            color=get_palette(mode)["reference"], strokeDash=[4, 4]).encode(
            y=alt.datum(reference_value)))
    return apply_chart_style(alt.layer(*layers).properties(height=CHART_HEIGHT), mode)


def calculate_bar_domain(values):
    """Value axis from zero (or the lowest value) to the highest, plus room for labels."""
    lowest = min(0, values.min())
    highest = max(0, values.max())
    room = (highest - lowest) * BAR_LABEL_ROOM
    return [lowest - room if lowest < 0 else 0, highest + room]


def draw_horizontal_bars(rows, value_title, mode, colors=None, reference_value=None,
                         is_sorted_by_value=True, reference_label=None, select_field=None,
                         label_limit=150):
    """Horizontal bars with their value written next to them.

    rows needs the columns label, value and value_label; colors, when given,
    is a list with one color per row. An optional column "meaning" explains the
    value in plain words in the tooltip. Bars go from the largest value down,
    or keep the order of rows when is_sorted_by_value is False.
    """
    palette = get_palette(mode)
    rows = rows.assign(color=colors if colors is not None else palette["accent"])
    if is_sorted_by_value:
        rows = rows.sort_values("value", ascending=False)
    order = rows["label"].to_list()
    tooltip = [alt.Tooltip("label:N", title=" "),
               alt.Tooltip("value_label:N", title=value_title)]
    if "meaning" in rows.columns:
        tooltip.append(alt.Tooltip("meaning:N", title="Qué significa"))
    if "detail" in rows.columns:
        # The whole description lives here, so the axis can keep a short name.
        tooltip.insert(1, alt.Tooltip("detail:N", title="Detalle"))
    base = alt.Chart(rows).encode(
        y=alt.Y("label:N", title=None, sort=order,
                axis=alt.Axis(labelLimit=label_limit, labelPadding=8)),
        tooltip=tooltip)
    bars = base.mark_bar(cornerRadiusEnd=6, height={"band": 0.65}, cursor="pointer"
                         if select_field else "default").encode(
        x=alt.X("value:Q", title=value_title, axis=alt.Axis(tickCount=5, labelOverlap=True),
                scale=alt.Scale(domain=calculate_bar_domain(rows["value"]), nice=False)),
        color=alt.Color("color:N", scale=None))
    # Positive values are written after the end of their bar. Negative values
    # are written just right of zero: written at the end of a negative bar,
    # they ran over the names column.
    positive_labels = base.transform_filter("datum.value >= 0").mark_text(
        align="left", dx=6, color=palette["text"]).encode(x="value:Q", text="value_label:N")
    negative_labels = base.transform_filter("datum.value < 0").mark_text(
        align="left", dx=6, color=palette["text"]).encode(x=alt.datum(0),
                                                          text="value_label:N")
    layers = [bars, positive_labels, negative_labels]
    if select_field:
        # A click anywhere on the row selects it (a short bar is hard to hit); the page
        # filters the other charts (D-069). The row is almost transparent, on top.
        layers.append(draw_row_targets(base, rows, select_field))
    if reference_value is not None:
        # Same rows as the bars (so the bands stay intact) but no y: one full line.
        layers.insert(0, alt.Chart(rows).mark_rule(
            color=palette["reference"], strokeDash=[4, 4]).encode(x=alt.datum(reference_value)))
        if reference_label:
            # The name of the dashed line, at its top, so it reads without a legend.
            # Above the plot, never over a bar.
            layers.append(alt.Chart(rows.head(1)).mark_text(
                align="center", baseline="bottom", dy=-4, fontSize=11,
                color=palette["text"]).encode(x=alt.datum(reference_value), y=alt.value(0),
                                              text=alt.datum(reference_label)))
    # One fixed band height per bar, so long lists stay readable.
    chart = alt.layer(*layers).properties(height=alt.Step(BAR_HEIGHT))
    return apply_chart_style(chart, mode)


def draw_row_targets(base, rows, select_field):
    """An invisible band over each whole row that carries the click selection «pick»."""
    low, high = calculate_bar_domain(rows["value"])
    return base.mark_bar(height={"band": 1}, opacity=0.001, cursor="pointer").encode(
        x=alt.datum(low), x2=alt.datum(high)).add_params(
        alt.selection_point(name="pick", fields=[select_field], on="click", clear="dblclick"))


def draw_variation_bars(rows, mode, keep_rank_order=False, select_field=None, label_limit=150):
    """Weekly price changes in percent: rises in red, falls in blue.

    rows needs the columns label and value (percent).
    """
    palette = get_palette(mode)
    # The arrow says the direction without color: ▲ rose, ▼ fell.
    def arrow(value):
        return "▲" if round(value, 1) > 0 else "▼" if round(value, 1) < 0 else "="
    rows = rows.assign(value_label=[f"{arrow(value)} {format_signed_percent(value)}"
                                    for value in rows["value"]],
                       meaning=rows["value"].map(describe_weekly_change))
    colors = [palette["rise"] if value > 0 else palette["fall"] for value in rows["value"]]
    return draw_horizontal_bars(rows, "Variación semanal (%)", mode, colors, reference_value=0,
                                is_sorted_by_value=not keep_rank_order,
                                select_field=select_field, label_limit=label_limit)


def draw_dumbbell(rows, unit, mode):
    """Wholesale price and consumer price of each channel, joined by a line.

    rows needs the columns channel, wholesale_price, consumer_price and gap_label;
    the gap is written at the right of each channel.
    """
    palette = get_palette(mode)
    rows = rows.sort_values("consumer_price", ascending=False).assign(
        wholesale_label=rows["wholesale_price"].map(lambda value: f"$ {format_thousands(value)}"),
        consumer_label=rows["consumer_price"].map(lambda value: f"$ {format_thousands(value)}"))
    order = rows["channel"].to_list()
    money_axis = alt.Axis(format=MONEY_AXIS_FORMAT, tickCount=5)
    tooltip = [alt.Tooltip("channel:N", title="Canal"),
               alt.Tooltip("wholesale_label:N", title=f"Mayorista $/{unit}"),
               alt.Tooltip("consumer_label:N", title=f"Consumidor $/{unit}"),
               alt.Tooltip("gap_label:N", title="Brecha")]
    base = alt.Chart(rows).encode(
        y=alt.Y("channel:N", title=None, sort=order,
                axis=alt.Axis(labelLimit=200, labelPadding=10)), tooltip=tooltip)
    joins = base.mark_rule(strokeWidth=2, color=palette["reference"]).encode(
        x=alt.X("wholesale_price:Q", title=f"$/{unit}", axis=money_axis,
                scale=alt.Scale(zero=False)), x2="consumer_price:Q")
    wholesale = base.mark_point(filled=True, size=110, opacity=1,
                                color=get_channel_color("Mayorista", mode),
                                stroke=palette["card"], strokeWidth=2).encode(
        x="wholesale_price:Q")
    consumers = base.mark_point(filled=True, size=130, opacity=1, stroke=palette["card"],
                                strokeWidth=2).encode(
        x="consumer_price:Q",
        color=alt.Color("channel:N", legend=None,
                        scale=build_channel_color_scale(rows["channel"], mode)))
    gaps = base.mark_text(align="left", dx=10, color=palette["text"]).encode(
        x="consumer_price:Q", text="gap_label:N")
    chart = alt.layer(joins, wholesale, consumers, gaps).properties(height=alt.Step(40))
    return apply_chart_style(chart, mode)


def draw_heatmap(rows, mode):
    """A calendar: one cell per month and year, darker when the price is higher.

    rows needs the columns year, month (1 to 12), value and value_label.
    """
    palette = get_palette(mode)
    rows = rows.assign(month_name=[MONTH_NAMES[month - 1] for month in rows["month"]])
    cells = alt.Chart(rows).mark_rect(cornerRadius=3, stroke=palette["card"],
                                      strokeWidth=2).encode(
        x=alt.X("month_name:O", title=None, sort=MONTH_NAMES,
                axis=alt.Axis(labelAngle=0, domain=False, ticks=False)),
        y=alt.Y("year:O", title=None, axis=alt.Axis(domain=False, ticks=False)),
        color=alt.Color("value:Q", title="Índice (1 = promedio del año)",
                        scale=alt.Scale(range=HEAT_RAMPS.get(mode, HEAT_RAMPS[MODE_LIGHT])),
                        legend=alt.Legend(orient="bottom", gradientLength=220,
                                          format=".2f")),
        tooltip=[alt.Tooltip("month_name:N", title="Mes"), alt.Tooltip("year:O", title="Año"),
                 alt.Tooltip("value_label:N", title="Índice estacional")])
    chart = cells.properties(height=alt.Step(34))
    return apply_chart_style(chart, mode)


def pick_text_color_on(fill):
    """Dark ink on a light cell, white on a dark one (relative luminance of the fill)."""
    red, green, blue = (int(fill[position:position + 2], 16) / 255 for position in (1, 3, 5))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "#0f172a" if luminance > 0.45 else "#ffffff"


def pick_cell_text_colors(values, ramp):
    """The ink of each heat cell: the ramp step its value falls on decides it."""
    low, high = values.min(), values.max()
    spread = (high - low) or 1
    steps = ((values - low) / spread * (len(ramp) - 1)).round().astype(int)
    return [pick_text_color_on(ramp[step]) for step in steps]


def draw_region_channel_map(rows, mode, chosen_region=None):
    """Regional index of one product as a region × channel heat map you can click.

    rows needs region, channel, regional_index and detail; 100 = national average.
    """
    palette = get_palette(mode)
    ramp = HEAT_RAMPS.get(mode, HEAT_RAMPS[MODE_LIGHT])
    index = rows["regional_index"] * 100
    # Whole numbers in the cell (102, not 102,05); its ink follows the cell's own fill.
    rows = rows.assign(index=index, index_label=index.round().astype(int).astype(str),
                       text_color=pick_cell_text_colors(index, ramp),
                       short_region=rows["region"].map(shorten_region_name))
    pick = alt.selection_point(name="pick", fields=["region"], on="click", clear="dblclick")
    base = alt.Chart(rows).encode(
        # Regions in rows and channels in columns: every name reads whole and level.
        x=alt.X("channel:N", title=None, axis=alt.Axis(orient="top", labelAngle=0,
                                                         labelLimit=90)),
        y=alt.Y("short_region:N", title=None, axis=alt.Axis(labelLimit=120)),
        tooltip=[alt.Tooltip("detail:N", title="Detalle"),
                 alt.Tooltip("index_label:N", title="Índice (100 = promedio nacional)")])
    opacity = (alt.condition(alt.datum.region == chosen_region, alt.value(1), alt.value(.45))
               if chosen_region else alt.value(1))
    cells = base.mark_rect(cornerRadius=3, stroke=palette["card"], strokeWidth=2,
                           cursor="pointer").encode(
        color=alt.Color("index:Q", title="Índice", scale=alt.Scale(range=ramp),
            # Under the grid, as in the mockup: the cells keep the card's whole width.
            legend=alt.Legend(orient="bottom", direction="horizontal", gradientLength=160,
                              format=".0f", title="Índice (100 = promedio del canal)")),
        opacity=opacity).add_params(pick)
    text = base.mark_text(fontSize=11).encode(text="index_label:N",
                                              color=alt.Color("text_color:N", scale=None))
    layers = [cells, text]
    # A region without a price in a channel reads «Sin dato» on a neutral cell: absent,
    # never a zero on the heat scale (D-072).
    grid = pd.MultiIndex.from_product([rows["short_region"].unique(), rows["channel"].unique()],
                                      names=["short_region", "channel"]).to_frame(index=False)
    missing = grid.merge(rows[["short_region", "channel"]], how="left", indicator=True)
    missing = missing[missing["_merge"] == "left_only"].drop(columns="_merge")
    if not missing.empty:
        empty = alt.Chart(missing.assign(label="Sin dato")).encode(
            x=alt.X("channel:N"), y=alt.Y("short_region:N"))
        layers += [empty.mark_rect(cornerRadius=3, stroke=palette["card"], strokeWidth=2,
                                   color=palette["grid"]),
                   empty.mark_text(fontSize=10, fontStyle="italic", color=palette["text"])
                   .encode(text="label:N")]
    # The ink has its own scale: it must not join the heat scale of the cells.
    return apply_chart_style(alt.layer(*layers).resolve_scale(color="independent"), mode)


def draw_donut(rows, colors, mode, center=None, center_note=None, size=210):
    """Shares of a whole as a ring (rows: label, value, value_label); center writes the
    whole in the middle, with center_note under it, so the reader knows what it adds up."""
    palette = get_palette(mode)
    rows = rows.assign(color=colors)
    outer = size * 0.46
    ring = alt.Chart(rows).mark_arc(innerRadius=outer * 0.68, outerRadius=outer, cornerRadius=4,
                                    padAngle=0.02).encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color("color:N", scale=None),
        order=alt.Order("value:Q", sort="descending"),
        tooltip=[alt.Tooltip("label:N", title=" "),
                 alt.Tooltip("value_label:N", title="Precios semanales")])
    layers = [ring]
    if center:
        middle = alt.Chart(pd.DataFrame({"text": [center]}))
        layers.append(middle.mark_text(fontSize=size * 0.1, fontWeight="bold", dy=-6,
                                       color=palette["strong_text"]).encode(text="text:N"))
        if center_note:
            layers.append(middle.mark_text(fontSize=size * 0.06, dy=size * 0.08,
                                           color=palette["text"]).encode(
                text=alt.datum(center_note)))
    return apply_chart_style(alt.layer(*layers).properties(height=size, width=size), mode)
# endregion


# Geographic assets stay local: the visitor does not need a map service or API key.
def draw_chile_map(rows, geometry, mode):
    """Join existing indices to the 16 regions; preserve missing values as missing."""
    import copy
    features = copy.deepcopy(geometry["features"])
    indexed = rows.set_index("region").to_dict("index")
    palette = get_palette(mode)
    extent = max(1, max((abs(float(value) * 100 - 100) for value in rows["regional_index"]), default=1))
    def index_color(value):
        if value is None:
            return palette["grid"]
        amount = min(1, abs(value - 100) / extent)
        target = palette["rise"] if value >= 100 else palette["fall"]
        return "#" + "".join(f"{round(int(palette['grid'][i:i+2],16) * (1-amount) + int(target[i:i+2],16) * amount):02x}"
                             for i in (1,3,5))
    for feature in features:
        values = indexed.get(feature["properties"]["region"])
        feature["properties"]["index"] = float(values["regional_index"] * 100) if values else None
        feature["properties"]["price"] = float(values["price"]) if values else None
        feature["properties"]["status"] = "Comparable" if values else "Sin dato comparable"
        feature["properties"]["fill"] = index_color(feature["properties"]["index"])
    pick = alt.selection_point(name="pick", fields=["properties.region"], on="click", clear="dblclick")
    chart = alt.Chart(alt.Data(values=features)).mark_geoshape(
        stroke=palette["background"], strokeWidth=.5, invalid=None).encode(
        color=alt.Color("properties.fill:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("properties.region:N", title="Región"),
                 alt.Tooltip("properties.status:N", title="Disponibilidad"),
                 alt.Tooltip("properties.index:Q", title="Índice (100 = promedio)", format=".0f"),
                 alt.Tooltip("properties.price:Q", title="Precio", format=",.0f")]
    ).project(type="mercator").add_params(pick).properties(height=170)
    return chart.configure_view(stroke=None).configure(background=palette["card"])


def draw_regional_ranking(rows, mode):
    """One channel: labels and index values readable without hover or truncation."""
    palette = get_palette(mode)
    data = rows.assign(index_value=rows["regional_index"] * 100,
                       short_region=rows["region"].map(shorten_region_name))
    base = alt.Chart(data).encode(y=alt.Y("short_region:N", title=None,
        sort=alt.SortField("index_value", order="descending"), axis=alt.Axis(labelLimit=180)))
    bars = base.mark_bar(cornerRadiusEnd=3, size=16).encode(
        x=alt.X("index_value:Q", title="Índice · 100 = promedio", scale=alt.Scale(
            domain=[0, max(100, float(data["index_value"].max())) * 1.18], nice=False)),
        color=alt.condition(alt.datum.index_value >= 100, alt.value(palette["rise"]), alt.value(palette["fall"])))
    labels = base.mark_text(align="left", dx=5, color=palette["strong_text"]).encode(
        x="index_value:Q", text=alt.Text("index_value:Q", format=".0f"))
    rule = alt.Chart(pd.DataFrame({"reference": [100]})).mark_rule(
        strokeDash=[3,3], color=palette["reference"]).encode(x="reference:Q")
    return (bars + labels + rule).properties(height=170).configure_view(stroke=None).configure(
        background=palette["card"], axis=alt.AxisConfig(labelColor=palette["text"],
        titleColor=palette["text"], gridColor=palette["grid"], labelFontSize=11))


REGIONAL_ZONES = [
    ("Arica y Parinacota", "Arica"), ("Tarapacá", "Tarapacá"),
    ("Antofagasta", "Antofagasta"), ("Atacama", "Atacama"),
    ("Coquimbo", "Coquimbo"), ("Valparaíso", "Valparaíso"),
    ("Metropolitana de Santiago", "Metropolitana"), ("Libertador General Bernardo O’Higgins", "O’Higgins"),
    ("Maule", "Maule"), ("Ñuble", "Ñuble"), ("Biobío", "Biobío"),
    ("La Araucanía", "Araucanía"), ("Los Ríos", "Los Ríos"), ("Los Lagos", "Los Lagos"),
    ("Aysén del General Carlos Ibáñez del Campo", "Aysén"),
    ("Magallanes y de la Antártica Chilena", "Magallanes"),
]


def draw_regional_zones(rows, mode):
    """A cartogram: equal-sized regions, real changes, missing distinct from zero."""
    import unicodedata
    def normalized(value):
        return "".join(c for c in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(c) != "Mn").replace("’", "'")
    palette = get_palette(mode)
    cells = []
    for index, (name, label) in enumerate(REGIONAL_ZONES):
        matches = rows[rows["region"].map(lambda value: normalized(name) in normalized(value))]
        row = matches.iloc[0] if len(matches) else None
        change = row["weekly_change"] if row is not None else None
        missing = change is None or pd.isna(change)
        stable = not missing and abs(change) < 1e-9
        status = "Sin comparación" if missing else "Sin cambio" if stable else "Subió" if change > 0 else "Bajó"
        color = palette["card"] if missing else "#858991" if stable else palette["rise"] if change > 0 else palette["fall"]
        value = "—" if missing else "= 0 %" if stable else ("▲ " if change > 0 else "▼ ") + ("<0,1" if abs(change) < .05 else f"{abs(change):.1f}".replace(".", ",")) + " %"
        cells.append(dict(region=row["region"] if row is not None else "Región de " + name,
            label=label, column=index % 4, row=index // 4, status=status, fill=color,
            value=value, weekly_change=None if missing else float(change),
            ink=palette["text"] if missing else "#ffffff"))
    base = alt.Chart(pd.DataFrame(cells)).encode(
        x=alt.X("column:O", axis=None, scale=alt.Scale(paddingInner=.07)),
        y=alt.Y("row:O", axis=None, scale=alt.Scale(paddingInner=.10)),
        tooltip=[alt.Tooltip("region:N", title="Región"), alt.Tooltip("status:N", title="Movimiento"),
                 alt.Tooltip("weekly_change:Q", title="Variación semanal (%)", format=".2f")])
    pick = alt.selection_point(name="pick", fields=["region"], on="click", clear="dblclick")
    zones = base.mark_rect(cornerRadius=5, stroke=palette["reference"], strokeWidth=.6).encode(
        color=alt.Color("fill:N", scale=None, legend=None)).add_params(pick)
    labels = base.mark_text(dy=-10, fontSize=11).encode(text="label:N", color=alt.Color("ink:N", scale=None, legend=None))
    values = base.mark_text(dy=11, fontSize=13, fontWeight=600).encode(text="value:N", color=alt.Color("ink:N", scale=None, legend=None))
    return (zones + labels + values).properties(height=268).configure_view(stroke=None).configure(background=palette["card"])


def draw_regional_change_map(rows, geometry, mode, full_country=True):
    """Real regional boundaries; missing comparisons never become zero changes."""
    import copy
    features = copy.deepcopy(geometry['features'])
    palette = get_palette(mode)
    indexed = rows.set_index('region').to_dict('index')
    comparable = []
    for feature in features:
        props = feature['properties']
        row = indexed.get(props['region'], {})
        change = row.get('weekly_change')
        missing = change is None or pd.isna(change)
        stable = not missing and abs(change) < 1e-9
        props.update(weekly_change=None if missing else float(change),
                     price=None if pd.isna(row.get('price', float('nan'))) else float(row['price']),
                     status='Sin comparación' if missing else 'Sin cambio' if stable else 'Subió' if change > 0 else 'Bajó',
                     fill=palette['card'] if missing else '#858991' if stable else palette['rise'] if change > 0 else palette['fall'])
        if not missing:
            comparable.append(feature)
    fit = {'type': 'FeatureCollection', 'features': features if full_country or not comparable else comparable}
    pick = alt.selection_point(name='pick', fields=['properties.region'], on='click', clear='dblclick')
    chart = alt.Chart(alt.Data(values=features)).mark_geoshape(
        stroke=palette['reference'], strokeWidth=1, invalid=None, clip=True).encode(
        color=alt.Color('properties.fill:N', scale=None, legend=None),
        tooltip=[alt.Tooltip('properties.region:N', title='Región'),
                 alt.Tooltip('properties.status:N', title='Movimiento'),
                 alt.Tooltip('properties.weekly_change:Q', title='Variación semanal (%)', format='.2f'),
                 alt.Tooltip('properties.price:Q', title='Precio por unidad seleccionada ($)', format=',.0f')]
    ).project(type='mercator', fit=fit).add_params(pick).properties(height=430)
    if full_country:
        labels = []
        for feature in features:
            coords = [point for polygon in feature['geometry']['coordinates'] for ring in polygon for point in ring]
            lon = (min(p[0] for p in coords) + max(p[0] for p in coords)) / 2
            lat = (min(p[1] for p in coords) + max(p[1] for p in coords)) / 2
            labels.append(dict(region=shorten_region_name(feature['properties']['region']), lon=lon, lat=lat, ink=palette['text'] if feature['properties']['weekly_change'] is None else feature['properties']['fill']))
        labels.sort(key=lambda row: -row['lat'])
        for i, row in enumerate(labels):
            row.update(label_lon=-65.5, label_lat=-18.5-i*2.35)
        base = alt.Chart(pd.DataFrame(labels))
        leaders = base.mark_rule(color=palette['reference'], strokeWidth=.5).encode(
            longitude='lon:Q', latitude='lat:Q', longitude2='label_lon:Q', latitude2='label_lat:Q')
        names = base.mark_text(align='left', dx=4, fontSize=10, color=palette['text']).encode(
            longitude='label_lon:Q', latitude='label_lat:Q', text='region:N', color=alt.Color('ink:N', scale=None, legend=None))
        chart.projection = alt.Undefined
        label_points = [{'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [r['label_lon']+8, r['label_lat']]}, 'properties': {}} for r in labels]
        chart = alt.layer(chart, leaders, names).project(type='mercator', fit={'type': 'FeatureCollection', 'features': features + label_points}).properties(height=580)
    return chart.configure_view(stroke=None).configure(background=palette['card'])


# region Contexto del precio (D-094)
CONTEXT_CHANNELS = {"Feria libre": "#2563C9", "Supermercado": "#D9622B"}
CONTEXT_STATE_WORDS = {"sobre": "sobre lo habitual", "bajo": "bajo lo habitual"}


def split_gaps(rows, value):
    """A segment number that changes after every missing week: lines break, never bridge."""
    rows = rows.sort_values("week_start").copy()
    rows["segment"] = rows[value].isna().cumsum()
    return rows[rows[value].notna()]


def draw_price_context(rows, mode, height=380):
    """52 weeks: one line per channel over its P25–P75 band of previous years.

    rows: week_start, channel, price, p25, p75, state. Missing weeks leave a gap.
    """
    palette = get_palette(mode)
    domain = [channel for channel in CONTEXT_CHANNELS if channel in set(rows["channel"])]
    colors = alt.Scale(domain=domain, range=[CONTEXT_CHANNELS[channel] for channel in domain])
    values = pd.concat([rows["price"], rows["p25"], rows["p75"]]).dropna()
    span = max(values.max() - values.min(), values.max() * .05, 1) if not values.empty else 1
    scale = alt.Scale(zero=False, nice=False,
                      domain=[max(0, values.min() - span * .12), values.max() + span * .12] if not values.empty else None)
    x = alt.X("week_start:T", title=None, axis=alt.Axis(format="%b %Y", tickCount=6, labelPadding=6))
    bands = split_gaps(rows.assign(band=rows["p25"]), "band")
    lines = split_gaps(rows, "price")
    band = alt.Chart(bands).mark_area(opacity=.16, interpolate="monotone").encode(
        x=x, y=alt.Y("p25:Q", scale=scale, title="$ por unidad", axis=alt.Axis(format=MONEY_AXIS_FORMAT, tickCount=5)),
        y2="p75:Q", color=alt.Color("channel:N", scale=colors, legend=None),
        detail=alt.Detail("segment:N"))
    line = alt.Chart(lines).mark_line(strokeWidth=2.2).encode(
        x=x, y=alt.Y("price:Q", scale=scale), color=alt.Color("channel:N", scale=colors, legend=None),
        detail=alt.Detail("segment:N"),
        tooltip=[alt.Tooltip("week_start:T", title="Semana", format="%d-%m-%Y"),
                 alt.Tooltip("channel:N", title="Canal"),
                 alt.Tooltip("price:Q", title="Precio", format=",.0f"),
                 alt.Tooltip("p25:Q", title="Habitual desde", format=",.0f"),
                 alt.Tooltip("p75:Q", title="Habitual hasta", format=",.0f")])
    last = lines.sort_values("week_start").groupby("channel").tail(1)
    point = alt.Chart(last).mark_point(filled=True, size=70, stroke=palette["card"], strokeWidth=1.5).encode(
        x=x, y=alt.Y("price:Q", scale=scale), color=alt.Color("channel:N", scale=colors, legend=None))
    flagged = last[last["state"].isin(CONTEXT_STATE_WORDS)].assign(
        label=lambda frame: frame["channel"].map(lambda c: c.split()[0]) + ": "
        + frame["state"].map(CONTEXT_STATE_WORDS))
    label = alt.Chart(flagged).mark_text(align="right", dx=-10, dy=-14, fontSize=12, fontWeight=700).encode(
        x=x, y=alt.Y("price:Q", scale=scale), text="label:N",
        color=alt.Color("channel:N", scale=colors, legend=None))
    chart = alt.layer(band, line, point, label).properties(height=height)
    return apply_chart_style(chart, mode)


def draw_seasonal_pattern(pattern, channel, month, mode, height=150):
    """12 bars, 100 = average of the year; the current month solid, the next two outlined."""
    color = CONTEXT_CHANNELS.get(channel, get_palette(mode)["accent"])
    following = {(month - 1 + step) % 12 + 1 for step in (1, 2)}
    rows = pd.DataFrame([{"month": number, "label": MONTH_NAMES[number - 1].capitalize(),
                          "value": pattern[number], "text": f"{pattern[number]:.0f}",
                          "kind": "actual" if number == month else "proximo" if number in following else "otro"}
                         for number in range(1, 13) if number in pattern])
    if rows.empty:
        return None
    low = max(0, min(rows["value"].min(), 100) - 12)
    scale = alt.Scale(domain=[low, max(rows["value"].max(), 100) + 8], nice=False)
    x = alt.X("label:N", sort=[name.capitalize() for name in MONTH_NAMES], title=None,
              axis=alt.Axis(labelAngle=0))
    rows["fill"] = rows["kind"].map({"actual": color, "proximo": color + "29", "otro": color + "38"})
    rows["outline"] = rows["kind"].map({"actual": color, "proximo": color, "otro": color + "00"})
    rows["base"] = low
    # Bars start at the bottom of the scale, not below it: they never cover the month names.
    bars = alt.Chart(rows).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, strokeWidth=1.5).encode(
        x=x, y=alt.Y("value:Q", scale=scale, title=None, axis=None), y2="base:Q",
        color=alt.Color("fill:N", scale=None, legend=None), stroke=alt.Stroke("outline:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("label:N", title="Mes"), alt.Tooltip("value:Q", title="Índice", format=".0f")])
    text = alt.Chart(rows).mark_text(dy=-7, fontSize=11, color=get_palette(mode)["text"]).encode(
        x=x, y=alt.Y("value:Q", scale=scale), text="text:N")
    rule = alt.Chart(pd.DataFrame({"value": [100]})).mark_rule(strokeDash=[3, 3], opacity=.5,
                                                               color=get_palette(mode)["text"]).encode(
        y=alt.Y("value:Q", scale=scale))
    return apply_chart_style(alt.layer(bars, rule, text).properties(height=height), mode)


def draw_full_history(rows, mode, height=360):
    """Every week of both channels, lines only (no areas), gaps where a week is missing."""
    domain = [channel for channel in CONTEXT_CHANNELS if channel in set(rows["channel"])]
    colors = alt.Scale(domain=domain, range=[CONTEXT_CHANNELS[channel] for channel in domain])
    full = []
    for channel, series in rows.groupby("channel"):
        calendar = pd.DataFrame({"week_start": pd.date_range(series["week_start"].min(),
                                                             series["week_start"].max(), freq="7D")})
        full.append(split_gaps(calendar.merge(series, on="week_start", how="left").assign(channel=channel),
                               "national_price"))
    data = pd.concat(full) if full else rows
    chart = alt.Chart(data).mark_line(strokeWidth=1.8).encode(
        x=alt.X("week_start:T", title=None, axis=alt.Axis(format="%b %Y")),
        y=alt.Y("national_price:Q", title="$ por unidad", scale=alt.Scale(zero=False),
                axis=alt.Axis(format=MONEY_AXIS_FORMAT)),
        color=alt.Color("channel:N", scale=colors, title=None), detail="segment:N",
        tooltip=[alt.Tooltip("week_start:T", title="Semana", format="%d-%m-%Y"),
                 alt.Tooltip("channel:N", title="Canal"),
                 alt.Tooltip("national_price:Q", title="Precio", format=",.0f")]).properties(height=height)
    return apply_chart_style(chart, mode)
# endregion
