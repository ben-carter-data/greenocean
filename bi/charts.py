"""Charts and visual style of the dashboard, drawn with Altair (installed with Streamlit).

Every chart takes the active mode ("dark" or "light") and uses its palette.
Every channel keeps the same hue in every chart, so a reader learns it once.
Numbers in labels and tooltips are written as in Chile: 1.234 and 12,5 %.
"""
import altair as alt
import pandas as pd

# region Constants
MODE_DARK = "dark"
MODE_LIGHT = "light"

# Categorical palette validated for color blindness, one step per mode
# (checked against each mode's card color). The wholesale price is a reference,
# so it gets neutral ink instead of a hue.
PALETTES = {
    MODE_DARK: {
        "channels": {"Feria libre": "#3987e5", "Supermercado": "#d95926",
                     "Supermercado en Línea": "#199e70", "Mercado Minorista": "#c98500",
                     "Carnicería": "#d55181", "Panadería": "#008300",
                     "Mercado Mayorista": "#9085e9", "Mayorista": "#c3c2b7"},
        "rise": "#e66767", "fall": "#3987e5", "accent": "#3987e5",
        "text": "#c3c2b7", "grid": "#26262a", "reference": "#6f6e69",
        "card": "#141416", "card_border": "#26262a", "strong_text": "#f0efec",
    },
    MODE_LIGHT: {
        "channels": {"Feria libre": "#2a78d6", "Supermercado": "#eb6834",
                     "Supermercado en Línea": "#1baf7a", "Mercado Minorista": "#eda100",
                     "Carnicería": "#e87ba4", "Panadería": "#008300",
                     "Mercado Mayorista": "#6250d6", "Mayorista": "#52514e"},
        "rise": "#e34948", "fall": "#2a78d6", "accent": "#2a78d6",
        "text": "#52514e", "grid": "#ece5d6", "reference": "#a8a497",
        "card": "#fffdf8", "card_border": "#e7dfcf", "strong_text": "#1d1b17",
    },
}
CHART_FONT = "Source Sans Pro, sans-serif"
CHART_HEIGHT = 300
SPARKLINE_HEIGHT = 70
BAR_HEIGHT = 28
# Share of the value axis left free beyond the bars, so their labels fit.
BAR_LABEL_ROOM = 0.18
# Month and year: with several years loaded, a day and month alone repeat and
# cannot be told apart.
WEEK_AXIS_FORMAT = "%b %Y"
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
    """Palette of the active mode; dark when the mode is unknown."""
    return PALETTES.get(mode, PALETTES[MODE_DARK])


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
                  else alt.Axis(format=".0f"))
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
                            is_money=False):
    """One series by week as a soft area (rows: week_start, value)."""
    rows = add_week_labels(rows, value_labels)
    color = get_palette(mode)["accent"]
    value_axis = alt.Axis(format=MONEY_AXIS_FORMAT) if is_money else alt.Axis()
    base = alt.Chart(rows).encode(
        x=alt.X("week_start:T", title=None, axis=alt.Axis(format=WEEK_AXIS_FORMAT)),
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
                         is_sorted_by_value=True):
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
    base = alt.Chart(rows).encode(
        y=alt.Y("label:N", title=None, sort=order,
                axis=alt.Axis(labelLimit=260, labelPadding=10)),
        tooltip=tooltip)
    bars = base.mark_bar(cornerRadiusEnd=6, height={"band": 0.65}).encode(
        x=alt.X("value:Q", title=value_title, axis=alt.Axis(tickCount=5),
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
    if reference_value is not None:
        # Same rows as the bars (so the bands stay intact) but no y: one full line.
        layers.insert(0, alt.Chart(rows).mark_rule(
            color=palette["reference"], strokeDash=[4, 4]).encode(x=alt.datum(reference_value)))
    # One fixed band height per bar, so long lists stay readable.
    chart = alt.layer(*layers).properties(height=alt.Step(BAR_HEIGHT))
    return apply_chart_style(chart, mode)


def draw_variation_bars(rows, mode):
    """Weekly price changes in percent: rises in red, falls in blue.

    rows needs the columns label and value (percent).
    """
    palette = get_palette(mode)
    rows = rows.assign(value_label=rows["value"].map(format_signed_percent),
                       meaning=rows["value"].map(describe_weekly_change))
    colors = [palette["rise"] if value > 0 else palette["fall"] for value in rows["value"]]
    return draw_horizontal_bars(rows, "Variación semanal (%)", mode, colors, reference_value=0)


def draw_donut(rows, colors, mode):
    """Shares of a whole as a ring (rows: label, value, value_label)."""
    rows = rows.assign(color=colors)
    ring = alt.Chart(rows).mark_arc(innerRadius=62, outerRadius=96, cornerRadius=4,
                                    padAngle=0.02).encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color("color:N", scale=None),
        order=alt.Order("value:Q", sort="descending"),
        tooltip=[alt.Tooltip("label:N", title=" "),
                 alt.Tooltip("value_label:N", title="Precios semanales")])
    return apply_chart_style(ring.properties(height=210, width=210), mode)
# endregion
