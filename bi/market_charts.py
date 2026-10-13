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


def draw_regional_3d(rows, mode, revision):
    """Real 3D stems: region × channel × index, for a single comparable product key."""
    check_product_key(rows)
    palette = charts.get_palette(mode)
    regions = sorted(rows["region"].unique())
    channels = sorted(rows["channel"].unique())
    region_positions = {region: position for position, region in enumerate(regions)}
    figure = go.Figure()
    for channel, points in rows.groupby("channel", sort=True):
        x = [region_positions[region] for region in points["region"]]
        y = [channels.index(channel)] * len(points)
        z = (points["regional_index"] * 100).tolist()
        color = charts.get_channel_color(channel, mode)
        stem_x, stem_y, stem_z = [], [], []
        for px, py, pz in zip(x, y, z):
            stem_x.extend([px, px, None])
            stem_y.extend([py, py, None])
            stem_z.extend([0, pz, None])
        figure.add_trace(go.Scatter3d(
            x=stem_x, y=stem_y, z=stem_z, mode="lines", showlegend=False,
            hoverinfo="skip", line=dict(color=color, width=6), opacity=.65))
        details = [[html.escape(row.region), html.escape(row.channel),
                    charts.format_index(row.regional_index * 100),
                    charts.format_thousands(row.price), charts.format_thousands(row.national_price),
                    html.escape(row.normalized_unit),
                    charts.describe_regional_index(row.regional_index)]
                   for row in points.itertuples()]
        figure.add_trace(go.Scatter3d(
            x=x, y=y, z=z, mode="markers", name=channel,
            marker=dict(size=7, color=color, opacity=1, line=dict(color=palette["strong_text"], width=.5)),
            customdata=details,
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Índice: %{customdata[2]}"
                          "<br>%{customdata[6]}<br>Precio regional: $ %{customdata[3]}/%{customdata[5]}"
                          "<br>Promedio nacional del canal: $ %{customdata[4]}/%{customdata[5]}<extra></extra>"))
    axis = dict(backgroundcolor=palette["card"], gridcolor=palette["grid"],
                zerolinecolor=palette["reference"], showbackground=True, tickfont=dict(size=9))
    figure.update_layout(scene=dict(
        xaxis=dict(**axis, title="Región", tickvals=list(range(len(regions))),
                   ticktext=[charts.shorten_region_name(region) for region in regions]),
        yaxis=dict(**axis, title="Canal", tickvals=list(range(len(channels))), ticktext=channels),
        zaxis=dict(**axis, title="Índice · 100 = nacional", rangemode="tozero"),
        bgcolor="rgba(0,0,0,0)", aspectmode="manual", aspectratio=dict(x=1.5, y=1, z=.9),
        camera=dict(eye=dict(x=1.8, y=1.9, z=1.5))),
        dragmode="orbit")
    return finish(figure, mode, 450, revision)


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


def build_scene_axis(palette):
    """Axis style shared by the 3D scenes."""
    return dict(backgroundcolor=palette["card"], gridcolor=palette["grid"],
                zerolinecolor=palette["reference"], showbackground=True, tickfont=dict(size=10))


def draw_seasonality_surface(rows, mode, revision):
    """3D surface of the seasonal index: months × years, higher and darker = dearer.

    rows needs the columns year, month (1 to 12) and value (the index, 1 = year average).
    """
    palette = charts.get_palette(mode)
    matrix = rows.pivot(index="year", columns="month", values="value").reindex(
        columns=range(1, 13)).sort_index()
    text = [["Sin dato" if pd.isna(value) else charts.format_index(value) for value in row]
            for row in matrix.to_numpy()]
    figure = go.Figure(go.Surface(
        x=list(range(12)), y=list(range(len(matrix.index))), z=matrix.to_numpy(),
        text=text, colorscale=list(zip([0, .33, .66, 1], charts.HEAT_RAMPS[mode])),
        colorbar=dict(title="Índice", thickness=12, len=.7),
        contours=dict(z=dict(show=True, usecolormap=True, project_z=True, width=1)),
        customdata=[[[month, year] for month in charts.MONTH_NAMES] for year in matrix.index],
        hovertemplate="%{customdata[0]} %{customdata[1]}<br>Índice: %{text}"
                      "<br>1 = promedio de su año<extra></extra>"))
    axis = build_scene_axis(palette)
    figure.update_layout(scene=dict(
        xaxis=dict(**axis, title="", tickvals=list(range(12)), ticktext=charts.MONTH_NAMES),
        yaxis=dict(**axis, title="", tickvals=list(range(len(matrix.index))),
                   ticktext=[str(year) for year in matrix.index]),
        zaxis=dict(**axis, title="Índice"), bgcolor="rgba(0,0,0,0)",
        aspectmode="manual", aspectratio=dict(x=1.6, y=1, z=.6),
        camera=dict(eye=dict(x=1.3, y=-1.4, z=.85), center=dict(x=0, y=0, z=-.1))),
        dragmode="orbit", margin=dict(l=0, r=0, t=0, b=0))
    figure.update_traces(colorbar=dict(thickness=10, len=.6, x=.98))
    return finish(figure, mode, 430, revision).update_layout(margin=dict(l=0, r=0, t=0, b=0))


def draw_gap_ribbons(rows, mode, revision):
    """3D ribbons of the gap: one ribbon per channel along the weeks, its height the gap.

    rows needs the columns week_start, channel and gap (percent). Each channel is its own
    ribbon, so nothing is interpolated between channels.
    """
    palette = charts.get_palette(mode)
    figure = go.Figure()
    channels = sorted(rows["channel"].unique())
    for position, channel in enumerate(channels):
        points = rows[rows["channel"] == channel].sort_values("week_start")
        weeks = points["week_start"].dt.strftime("%d-%m-%Y").tolist()
        color = charts.get_channel_color(channel, mode)
        gaps = points["gap"].to_numpy()
        figure.add_trace(go.Surface(
            x=[weeks, weeks], y=[[position - .3] * len(weeks), [position + .3] * len(weeks)],
            z=[gaps, gaps], showscale=False, opacity=.9, name=channel,
            colorscale=[[0, color], [1, color]],
            text=[[charts.format_signed_percent(gap) for gap in gaps]] * 2,
            hovertemplate=f"<b>{html.escape(channel)}</b><br>Semana %{{x}}<br>"
                          "Brecha: %{text}<extra></extra>"))
    axis = build_scene_axis(palette)
    figure.update_layout(scene=dict(
        xaxis=dict(**axis, title="Semana", nticks=6),
        yaxis=dict(**axis, title="Canal", tickvals=list(range(len(channels))),
                   ticktext=channels),
        zaxis=dict(**axis, title="Brecha (%)"), bgcolor="rgba(0,0,0,0)",
        aspectmode="manual", aspectratio=dict(x=2.2, y=.9, z=.6),
        camera=dict(eye=dict(x=1.0, y=-1.25, z=.55), center=dict(x=0, y=0, z=-.15))),
        dragmode="orbit", showlegend=False)
    return finish(figure, mode, 460, revision).update_layout(margin=dict(l=0, r=0, t=0, b=0))
