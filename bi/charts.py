"""Charts and visual style of the dashboard, drawn with Altair (installed with Streamlit).

Every chart takes the active theme (Corporativo, Vantablack, Blue Light or Dark Grey)
and uses its palette.
Every channel keeps the same hue in every chart, so a reader learns it once.
Numbers in labels and tooltips are written as in Chile: 1.234 and 12,5 %.
"""
import altair as alt
import pandas as pd

from bi import i18n

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
CHART_FONT = "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
CHART_HEIGHT = 300
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
# D-284: the same charts in English: 1,234.5 and "Mar 2024".
ENGLISH_LOCALE = {
    "number": {"decimal": ".", "thousands": ",", "grouping": [3], "currency": ["$ ", ""], "minus": "-"},
    "time": {"dateTime": "%A, %B %e, %Y, %X", "date": "%Y-%m-%d", "time": "%H:%M:%S", "periods": ["AM", "PM"],
             "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
             "shortDays": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
             "months": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                        "October", "November", "December"],
             "shortMonths": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]},
}


def chart_locale():
    return ENGLISH_LOCALE if i18n.is_english() else CHILE_LOCALE


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


def describe_weeks(weeks):
    """0 -> 'la misma semana', 1 -> '1 semana', 3 -> '3 semanas'."""
    if weeks == 0:
        return "la misma semana"
    return "1 semana" if weeks == 1 else f"{weeks} semanas"


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
                           locale=chart_locale()).configure_view(
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


# region Contexto del precio (D-094)
CONTEXT_CHANNELS = {"Feria libre": "#2563C9", "Supermercado": "#D9622B"}


# endregion
