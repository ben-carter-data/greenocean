"""Streamlit dashboard for the price monitor.

Run it with:  streamlit run bi/dashboard.py

It only reads etl/datos.db, through the named queries of bi/queries.sql.
Texts shown to the user are in Spanish; code and comments are in English.
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# region Imports of the project
# Streamlit runs this file as a script, so the project folder is added to the
# import path to reach the other modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import alerts, queries  # noqa: E402
from etl import etl  # noqa: E402
# endregion

# region Constants
PROFILE_ANALYST = "Analista de pricing / compras"
PROFILE_DATA_TEAM = "Equipo de datos"

VIEW_MARGINS = "Márgenes"
VIEW_CHANNELS_AND_REGIONS = "Canales y regiones"
VIEW_SEASONALITY = "Estacionalidad"
VIEW_ALERTS = "Alertas"
VIEW_DATA_QUALITY = "Calidad de datos"
VIEWS_BY_PROFILE = {
    PROFILE_ANALYST: [VIEW_MARGINS, VIEW_CHANNELS_AND_REGIONS, VIEW_SEASONALITY,
                      VIEW_ALERTS],
    PROFILE_DATA_TEAM: [VIEW_DATA_QUALITY],
}

# Choices shown first when they exist, so the dashboard opens with a known case.
DEFAULT_GROUP = "Hortalizas"
DEFAULT_PRODUCT = "Tomate"
DEFAULT_REGION = "Región Metropolitana de Santiago"
DEFAULT_CHANNEL = "Feria libre"
DEFAULT_MARGIN_CHANNELS = ["Feria libre", "Supermercado"]
WHOLESALE_LABEL = "Mayorista"

NO_DATA_TEXT = "No hay datos para esta selección."
NOMINAL_PRICES_TEXT = "Precios nominales, sin ajuste por inflación."
ATTRIBUTION_TEXT = (
    "Datos: Oficina de Estudios y Políticas Agrarias (ODEPA), Ministerio de "
    "Agricultura de Chile, licencia Creative Commons Atribución. "
    "Este proyecto no es un producto oficial de ODEPA.")
# endregion


# region Data access
def add_display_columns(rows):
    """Add the date and the product key label used by filters and charts."""
    if "week_start" in rows.columns:
        rows["week_start"] = pd.to_datetime(rows["week_start"])
    if "variety" in rows.columns:
        # The unit is part of the label: one product can be sold by kilo and by unit.
        rows["key_label"] = (rows["variety"] + " · " + rows["quality"]
                             + " · $/" + rows["normalized_unit"])
    return rows


@st.cache_data
def read_indicator(query_name):
    """Rows of one indicator, read once and kept in memory between interactions."""
    return add_display_columns(queries.run_query(query_name))


@st.cache_data
def read_price_alerts():
    """K6 alerts of every week, computed once."""
    prices = queries.run_query("k6_national_weekly_price")
    return add_display_columns(alerts.find_price_alerts(prices))
# endregion


# region Filters
def choose_value(label, values, preferred_value=None):
    """Show a select box and return the chosen value."""
    options = sorted(values)
    index = options.index(preferred_value) if preferred_value in options else 0
    return st.selectbox(label, options, index=index)


def choose_product_rows(rows):
    """Narrow the rows to the group, product and variety/quality the user chooses."""
    group = choose_value("Grupo", rows["product_group"].unique(), DEFAULT_GROUP)
    rows = rows[rows["product_group"] == group]
    product = choose_value("Producto", rows["product"].unique(), DEFAULT_PRODUCT)
    rows = rows[rows["product"] == product]
    # The key with most data goes first, so the view opens with a full chart.
    key_labels = rows["key_label"].value_counts().index.to_list()
    key_label = st.selectbox("Variedad · calidad · unidad", key_labels)
    return rows[rows["key_label"] == key_label]
# endregion


# region Margins view
def summarize_margins(rows):
    """One line per channel: median margin and number of weeks with data."""
    summary = rows.groupby("channel")["margin_percent"].agg(["median", "count"])
    summary.columns = ["Margen mediano (%)", "Semanas con dato"]
    summary.index.name = "Canal"
    return summary.round(1)


def show_margins_view():
    """K1: margin between the wholesale price and each consumer channel."""
    st.header("Márgenes entre mayorista y consumidor")
    st.caption("K1 = (precio consumidor − precio mayorista) / precio mayorista. "
               "Solo se compara la misma variedad, calidad, región, semana y unidad.")
    rows = choose_product_rows(read_indicator("k1_margin"))
    region = choose_value("Región", rows["region"].unique(), DEFAULT_REGION)
    rows = rows[rows["region"] == region]
    available_channels = sorted(rows["channel"].unique())
    default_channels = [channel for channel in DEFAULT_MARGIN_CHANNELS
                        if channel in available_channels]
    channels = st.multiselect("Canal", available_channels, default=default_channels)
    rows = rows[rows["channel"].isin(channels)].copy()
    if rows.empty:
        st.info(NO_DATA_TEXT)
        return
    rows["margin_percent"] = rows["margin"] * 100

    st.subheader("Margen por semana (%)")
    st.line_chart(rows.pivot(index="week_start", columns="channel",
                             values="margin_percent"))
    st.subheader("Precio por semana ($)")
    prices = rows.pivot(index="week_start", columns="channel", values="consumer_price")
    prices[WHOLESALE_LABEL] = rows.groupby("week_start")["wholesale_price"].first()
    st.line_chart(prices)
    st.dataframe(summarize_margins(rows))
    st.caption(NOMINAL_PRICES_TEXT)
# endregion


# region Channels and regions view
def show_channel_gaps(rows):
    """K2: average price gap of each channel against a reference channel."""
    st.subheader("Diferencial entre canales (K2)")
    if rows.empty:
        st.info("Este producto se registra en un solo canal.")
        return
    reference_channel = choose_value("Canal de referencia",
                                     rows["reference_channel"].unique(),
                                     DEFAULT_CHANNEL)
    rows = rows[rows["reference_channel"] == reference_channel]
    average_gap = rows.groupby("channel")["gap"].mean() * 100
    st.bar_chart(average_gap.rename("Diferencial promedio (%)"), horizontal=True)
    st.caption(f"Cuánto más caro (+) o más barato (−) es cada canal que "
               f"«{reference_channel}», en promedio de las semanas y regiones "
               f"donde ambos tienen precio.")


def show_regional_index(rows):
    """K3: average regional index of each region for one channel."""
    st.subheader("Índice regional (K3)")
    channel = choose_value("Canal", rows["channel"].unique(), DEFAULT_CHANNEL)
    rows = rows[rows["channel"] == channel]
    average_index = rows.groupby("region")["regional_index"].mean()
    st.bar_chart(average_index.rename("Índice regional promedio"), horizontal=True)
    st.caption("1 = precio promedio nacional de la semana. Sobre 1, la región "
               "es más cara que el promedio; bajo 1, más barata.")


def show_channels_and_regions_view():
    """K2 and K3 for any product group, with or without a wholesale price."""
    st.header("Canales y regiones")
    regional_rows = choose_product_rows(read_indicator("k3_regional_index"))
    key_label = regional_rows["key_label"].iloc[0]
    product = regional_rows["product"].iloc[0]
    gap_rows = read_indicator("k2_channel_gap")
    gap_rows = gap_rows[(gap_rows["product"] == product)
                        & (gap_rows["key_label"] == key_label)]
    show_channel_gaps(gap_rows)
    show_regional_index(regional_rows)
    st.caption(NOMINAL_PRICES_TEXT)
# endregion


# region Seasonality view
def show_seasonality_view():
    """K4: national price of each week over the average of its year."""
    st.header("Estacionalidad")
    st.caption("K4 = precio nacional de la semana / precio promedio del año. "
               "Con un solo año cargado muestra la variación dentro de ese año; "
               "la estacionalidad se confirma al cargar el histórico.")
    rows = choose_product_rows(read_indicator("k4_seasonal_index"))
    channel = choose_value("Canal", rows["channel"].unique(), DEFAULT_CHANNEL)
    rows = rows[rows["channel"] == channel]
    st.subheader("Índice estacional por semana")
    st.line_chart(rows.pivot(index="week_start", columns="price_year",
                             values="seasonal_index"))
    st.subheader("Precio nacional por semana ($)")
    st.line_chart(rows.set_index("week_start")["national_price"])
    st.caption(NOMINAL_PRICES_TEXT)
# endregion


# region Alerts view
def show_alerts_view():
    """K6: products whose price moved outside their usual range in one week."""
    st.header("Alertas de variación")
    st.caption("K6: la variación semanal del precio nacional se sale de su media "
               "± 2 desviaciones estándar de las 12 semanas anteriores. Un producto "
               "necesita 13 semanas seguidas con precio para ser evaluado.")
    alert_rows = read_price_alerts()
    if alert_rows.empty:
        st.info("Todavía no hay semanas suficientes para calcular alertas.")
        return
    weeks = sorted(alert_rows["week_start"].dt.date.unique(), reverse=True)
    week = st.selectbox("Semana (lunes de inicio)", weeks)
    week_rows = alert_rows[alert_rows["week_start"].dt.date == week]
    st.metric("Productos fuera de su rango", len(week_rows))
    st.dataframe(format_alerts(week_rows), hide_index=True)
    st.caption(NOMINAL_PRICES_TEXT)


def format_alerts(alert_rows):
    """Alerts as a table for the reader, largest movements first."""
    table = pd.DataFrame({
        "Producto": alert_rows["product"],
        "Variedad": alert_rows["variety"],
        "Calidad": alert_rows["quality"],
        "Canal": alert_rows["channel"],
        "Unidad": alert_rows["normalized_unit"],
        "Precio nacional ($)": alert_rows["national_price"].round(0),
        "Variación (%)": (alert_rows["variation"] * 100).round(1),
        "Variación habitual (%)": (alert_rows["usual_variation"] * 100).round(1),
        "Desviación estándar (%)": (alert_rows["variation_deviation"] * 100).round(1),
    })
    order = table["Variación (%)"].abs().sort_values(ascending=False).index
    return table.loc[order]
# endregion


# region Data quality view
def show_latest_run(runs):
    """Counts and status of the latest ETL run."""
    latest_run = runs.iloc[0]
    st.subheader(f"Última ejecución: {latest_run['status']} · {latest_run['started_at']}")
    columns = st.columns(3)
    columns[0].metric("Filas leídas", f"{latest_run['rows_read']:,}")
    columns[1].metric("Filas cargadas", f"{latest_run['rows_loaded']:,}")
    columns[2].metric("Filas rechazadas", f"{latest_run['rows_rejected']:,}")
    if latest_run["message"]:
        st.error(latest_run["message"])


def show_match_coverage():
    """K7: consumer fruit and vegetable keys that have a margin."""
    connection = queries.open_database()
    keys_with_margin, consumer_keys = etl.measure_match_coverage(connection)
    connection.close()
    st.subheader("Cobertura del cruce (K7)")
    st.metric("Claves de frutas y verduras con margen",
              f"{keys_with_margin} de {consumer_keys}"
              f" ({keys_with_margin / consumer_keys:.1%})")
    st.caption("Clave = producto + variedad + calidad. Tiene margen si coincide con "
               "el mayorista en alguna semana, región y unidad.")


def show_rejections():
    """K8: rejected rows of the latest run, by source and reason."""
    st.subheader("Filas rechazadas por motivo (K8)")
    rejections = read_indicator("k8_rejected_rows")
    if rejections.empty:
        st.success("La última ejecución no rechazó ninguna fila.")
        return
    rejections["rejected_share"] = (rejections["rejected_share"] * 100).round(3)
    rejections.columns = ["Fuente", "Motivo", "Filas rechazadas", "% de filas leídas"]
    st.dataframe(rejections, hide_index=True)


def show_flagged_prices():
    """Weekly prices kept but left out of the indicators (RN-05, RN-12)."""
    st.subheader("Precios semanales marcados")
    flag_counts = read_indicator("quality_flag_counts").copy()
    flag_counts.columns = ["Fuente", "Marca", "Precios semanales"]
    st.dataframe(flag_counts, hide_index=True)
    st.caption("UNIDAD_NO_CONVERTIBLE: la unidad no se puede llevar a kilo, unidad "
               "o litro. ATIPICO: más de 5 veces, o menos de 1/5, de la mediana del "
               "producto esa semana en su fuente. Ambos se conservan, sin entrar "
               "en los indicadores.")
    outliers = read_indicator("quality_outliers").drop(columns="key_label").copy()
    outliers["week_start"] = outliers["week_start"].dt.date
    outliers.columns = ["Semana", "Fuente", "Canal", "Región", "Producto", "Variedad",
                        "Calidad", "Unidad", "Precio", "Observaciones"]
    st.dataframe(outliers, hide_index=True)


def show_data_quality_view():
    """Whether the latest load worked and what was left out."""
    st.header("Calidad de datos")
    runs = read_indicator("quality_runs").copy()
    if runs.empty:
        st.warning("Todavía no hay ejecuciones registradas.")
        return
    show_latest_run(runs)
    show_match_coverage()
    show_rejections()
    show_flagged_prices()
    st.subheader("Últimas ejecuciones")
    runs.columns = ["Ejecución", "Inicio", "Estado", "Filas leídas", "Filas cargadas",
                    "Filas rechazadas", "Mensaje"]
    st.dataframe(runs, hide_index=True)
# endregion


# region Entry point
SHOW_VIEW_BY_NAME = {
    VIEW_MARGINS: show_margins_view,
    VIEW_CHANNELS_AND_REGIONS: show_channels_and_regions_view,
    VIEW_SEASONALITY: show_seasonality_view,
    VIEW_ALERTS: show_alerts_view,
    VIEW_DATA_QUALITY: show_data_quality_view,
}


def show_attribution():
    """Footer with the data source, shown under every view."""
    st.divider()
    st.caption(ATTRIBUTION_TEXT)


def main():
    """Draw the profile selector, the chosen view and the footer."""
    st.set_page_config(page_title="Monitor de precios de alimentos", layout="wide")
    st.title("Monitor de precios y márgenes de alimentos en Chile")
    if not queries.DATABASE_FILE.exists():
        st.error("Falta etl/datos.db. Ejecuta primero: python etl/etl.py")
        return
    profile = st.sidebar.selectbox("¿Quién consulta?", list(VIEWS_BY_PROFILE))
    view = st.sidebar.radio("Vista", VIEWS_BY_PROFILE[profile])
    SHOW_VIEW_BY_NAME[view]()
    show_attribution()


if __name__ == "__main__":
    main()
# endregion
