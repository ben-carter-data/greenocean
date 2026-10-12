"""Weekly report: status of the load and price alerts, as Markdown text.

Run it with:  python bi/report.py > report.md

The weekly job publishes the text as an issue of the repository (D-017).
The report is written in Spanish; code and comments are in English.
"""
import sys
from pathlib import Path

# region Imports of the project
# This file runs as a script, so the project folder is added to the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import alerts, queries  # noqa: E402
from etl import etl  # noqa: E402
# endregion

# region Constants
MAXIMUM_ALERTS_IN_REPORT = 20
ATTRIBUTION_TEXT = ("Datos: ODEPA, Ministerio de Agricultura de Chile, licencia "
                    "Creative Commons Atribución. Precios nominales.")
# endregion


# region Sections
def format_count(number):
    """Write a count with a dot every three digits, as used in Chile."""
    return f"{number:,}".replace(",", ".")


def build_load_section(database_file):
    """Lines about the latest ETL run and the match coverage (K7)."""
    latest_run = queries.run_query("quality_runs", database_file).iloc[0]
    connection = queries.open_database(database_file)
    keys_with_margin, consumer_keys = etl.measure_match_coverage(connection)
    connection.close()
    lines = ["## Estado de la carga", "",
             f"- Última ejecución: **{latest_run['status']}** ({latest_run['started_at']})",
             f"- Filas leídas: {format_count(latest_run['rows_read'])}",
             f"- Filas cargadas: {format_count(latest_run['rows_loaded'])}",
             f"- Filas rechazadas: {format_count(latest_run['rows_rejected'])}",
             f"- Cobertura del cruce (K7): {keys_with_margin} de {consumer_keys} claves"]
    if latest_run["message"]:
        lines.append(f"- Mensaje: {latest_run['message']}")
    return lines


def format_percent(fraction):
    """Write a fraction as a signed percentage with a decimal comma: +12,3 %."""
    return f"{fraction * 100:+.1f} %".replace(".", ",")


def build_alert_line(alert):
    """One table line of the report for one alert."""
    return (f"| {alert['product']} | {alert['variety']} | {alert['quality']} "
            f"| {alert['channel']} | {format_count(round(alert['national_price']))} "
            f"| {format_percent(alert['variation'])} |")


def build_alerts_section(database_file):
    """Lines with the K6 alerts of the latest week, largest movements first."""
    prices = queries.run_query("k6_national_weekly_price", database_file)
    alert_rows = alerts.find_price_alerts(prices)
    latest_week = prices["week_start"].max()
    week_alerts = alert_rows[alert_rows["week_start"] == latest_week]
    lines = [f"## Alertas de la semana del {latest_week}", ""]
    if week_alerts.empty:
        return lines + ["Ningún producto se movió fuera de su rango habitual."]

    largest_first = week_alerts["variation"].abs().sort_values(ascending=False).index
    shown_alerts = week_alerts.loc[largest_first].head(MAXIMUM_ALERTS_IN_REPORT)
    lines += [f"{len(week_alerts)} productos fuera de su rango habitual (K6). "
              f"Se muestran los {len(shown_alerts)} mayores movimientos.", "",
              "| Producto | Variedad | Calidad | Canal | Precio nacional ($) | Variación |",
              "|---|---|---|---|---|---|"]
    lines += [build_alert_line(alert) for alert in shown_alerts.to_dict("records")]
    return lines


def build_report(database_file=queries.DATABASE_FILE):
    """Return the whole weekly report as one Markdown text."""
    lines = ["# Informe semanal del monitor de precios", ""]
    lines += build_load_section(database_file)
    lines += [""] + build_alerts_section(database_file)
    lines += ["", ATTRIBUTION_TEXT]
    return "\n".join(lines)
# endregion


# region Entry point
def main():
    """Print the report, so the job can save it to a file."""
    print(build_report())
    return 0


if __name__ == "__main__":
    sys.exit(main())
# endregion
