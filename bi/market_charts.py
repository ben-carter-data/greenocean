"""Complementary market views; every plotted value comes from the price database."""
import html

import pandas as pd
import plotly.graph_objects as go

from bi import charts, queries


GROUP_CHANNEL_COLORS = dict(zip(
    ["Frutas", "Hortalizas", "Abarrotes y otros", "Carne bovina",
     "Carne de Cerdo - Ave - Cordero", "Lácteos - Huevos - Margarinas", "Pan"],
    ["Supermercado", "Feria libre", "Mercado Minorista", "Carnicería",
     "Mercado Mayorista", "Supermercado en Línea", "Panadería"]))


def finish(figure, mode, height, revision):
    """Transparent charts use the existing palette and retain the reader's camera."""
    palette = charts.get_palette(mode)
    figure.update_layout(
        template="none", height=height, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(color=palette["text"], family=charts.CHART_FONT),
        margin=dict(l=12, r=12, t=12, b=12), uirevision=revision,
        separators=",.",
        legend=dict(orientation="h", y=-.12, x=0, font=dict(size=11)),
        hoverlabel=dict(bgcolor=palette["card"], font_color=palette["strong_text"],
                        bordercolor=palette["card_border"]))
    return figure


def check_product_key(rows):
    """Prevent a chart from comparing different varieties, qualities or units."""
    if len(rows[queries.KEY_COLUMNS].drop_duplicates()) > 1:
        raise ValueError("La vista requiere un solo producto, variedad, calidad y unidad.")


def draw_group_share(rows, mode):
    """Shares count valid weekly observations, not spending or market share."""
    totals = rows.groupby("product_group").size().sort_values(ascending=False)
    palette = charts.get_palette(mode)
    figure = go.Figure(go.Pie(
        labels=totals.index.tolist(), values=totals.tolist(), hole=.68, sort=False,
        marker=dict(colors=[palette["channels"].get(GROUP_CHANNEL_COLORS.get(group),
                                                  palette["accent"]) for group in totals.index],
                    line=dict(color=palette["card"], width=3)),
        textinfo="text", textposition="outside", textfont=dict(size=11),
        text=[charts.format_percent(value / totals.sum() * 100) for value in totals],
        customdata=[charts.format_thousands(value) for value in totals],
        hovertemplate="<b>%{label}</b><br>%{customdata} observaciones válidas"
                      "<br>%{text} de la semana<extra></extra>"))
    figure.update_layout(annotations=[dict(
        text=f"<b>{charts.format_thousands(totals.sum())}</b><br>observaciones",
        x=.5, y=.5, showarrow=False, font=dict(size=16, color=palette["strong_text"]))],
        showlegend=True)
    return finish(figure, mode, 340, "market-groups")


def draw_price_trend(rows, mode, revision):
    """National prices for one complete product key, with missing weeks kept as gaps."""
    check_product_key(rows)
    figure = go.Figure()
    if rows.empty:
        return finish(figure, mode, 340, revision)
    unit = rows["normalized_unit"].iloc[0]
    for channel, channel_rows in rows.groupby("channel", sort=True):
        channel_rows = channel_rows.sort_values("week_start").set_index("week_start")
        weeks = pd.date_range(rows["week_start"].min(), rows["week_start"].max(), freq="7D")
        prices = channel_rows["national_price"].reindex(weeks)
        color = charts.get_channel_color(channel, mode)
        rgb = ",".join(str(int(color[index:index + 2], 16)) for index in (1, 3, 5))
        figure.add_trace(go.Scatter(
            name=channel, x=weeks.tolist(), y=[None if pd.isna(p) else p for p in prices],
            mode="lines+markers", connectgaps=False,
            line=dict(color=color, width=2), marker=dict(size=4), fill="tozeroy",
            fillcolor=f"rgba({rgb},.06)",
            customdata=[[week.strftime("%d-%m-%Y"),
                         "Sin dato" if pd.isna(price) else charts.format_thousands(price)]
                        for week, price in prices.items()],
            hovertemplate=f"%{{fullData.name}}<br>%{{customdata[0]}}<br>$ %{{customdata[1]}}/{html.escape(unit)}"
                          "<extra></extra>"))
    palette = charts.get_palette(mode)
    figure.update_xaxes(title=None, showgrid=False, tickformat="%d-%m", tickfont=dict(size=10))
    figure.update_yaxes(title=f"Precio nacional · $/{unit}", gridcolor=palette["grid"],
                        rangemode="tozero", separatethousands=True, tickformat=",.0f",
                        automargin=True, title_standoff=14)
    figure.update_layout(separators=",.", hovermode="x unified")
    figure = finish(figure, mode, 340, revision)
    figure.update_layout(margin=dict(l=75, r=12, t=12, b=35))
    return figure


def draw_regional_heatmap(rows, mode, revision):
    """An exclusive 2D alternative for exact reading or devices without WebGL."""
    check_product_key(rows)
    matrix = rows.pivot(index="channel", columns="region", values="regional_index").sort_index()
    details = [["Sin dato" if pd.isna(value) else charts.format_index(value * 100)
                for value in row] for row in matrix.to_numpy()]
    palette = charts.get_palette(mode)
    figure = go.Figure(go.Heatmap(
        x=[charts.shorten_region_name(region) for region in matrix.columns],
        y=matrix.index.tolist(), z=(matrix * 100).to_numpy(), text=details,
        texttemplate="%{text}", hoverongaps=False,
        colorscale=[[0, palette["card"]], [1, palette["accent"]]],
        colorbar=dict(title="Índice"),
        hovertemplate="%{x}<br>%{y}<br>Índice: %{text}<br>100 = promedio nacional del canal<extra></extra>"))
    figure.update_xaxes(title="Región", tickfont=dict(size=10), automargin=True,
                        showgrid=False, zeroline=False)
    figure.update_yaxes(title="Canal", automargin=True, showgrid=False, zeroline=False)
    return finish(figure, mode, 450, revision)
