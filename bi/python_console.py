"""Python console (D-135): the questions the project answers in Python, each one a
short script that calls the real functions of etl/ and bi/.

The script shown is exactly the one that runs. Visitors do not write the code:
running Python typed into a public server would hand that server over. They change
the parameters, and only to values from closed lists (or, for a unit, a quoted text),
so every script that can run is one of these templates.
"""
import inspect
import string
import time
from pathlib import Path

import pandas as pd

from bi import alerts, lag, price_context, queries
from etl import etl

# region Constants
PROJECT_DIR = Path(__file__).resolve().parent.parent
GROUP_ETL = "Limpieza y reglas · etl/etl.py"
GROUP_INDICATORS = "Indicadores · bi/"
UNIT_MAXIMUM_LENGTH = 60
DEFAULT_PRODUCT = "Tomate"
DEFAULT_REGION = "Región Metropolitana de Santiago"
DEFAULT_CHANNEL = "Feria libre"
# endregion


# region Parameter options
def list_margin_products():
    """Products with both prices (K1 pairs): the only ones K5 can measure."""
    return sorted(queries.run_query("k1_margin")["product"].unique())


def list_margin_regions():
    return sorted(queries.run_query("k1_margin")["region"].unique())


def list_consumer_channels():
    return sorted(queries.run_query("k1_margin")["channel"].unique())


def list_national_products():
    return sorted(queries.run_query("k6_national_weekly_price")["product"].unique())


def list_national_channels():
    return sorted(queries.run_query("k6_national_weekly_price")["channel"].unique())


OPTION_READERS = {
    "margin_product": list_margin_products, "margin_region": list_margin_regions,
    "consumer_channel": list_consumer_channels, "national_product": list_national_products,
    "national_channel": list_national_channels,
}
# endregion


# region Questions
QUESTIONS = [
    {"name": "rn11_rejections", "group": GROUP_ETL,
     "question": "¿Por qué se rechazaron filas?",
     "does": "Vuelve a limpiar y validar cada fila rechazada con las mismas funciones del ETL "
             "y compara el motivo recalculado con el guardado (RN-11).",
     "functions": [etl.clean, etl.validate_rows], "params": [],
     "code": '''import json

import pandas as pd

from bi import queries
from etl import etl

# Cada fila rechazada se guardó tal como llegó, con su motivo (RN-11).
connection = queries.open_database()
stored = pd.read_sql_query("SELECT source, reason, original_row FROM rejection", connection)
connection.close()

# Se limpia y valida otra vez con las funciones del ETL.
checked = []
for source, rows in stored.groupby("source"):
    raw = pd.DataFrame([json.loads(row) for row in rows["original_row"]]).astype(str)
    reasons = etl.validate_rows(etl.clean(raw, source))
    checked.append(rows.assign(recalculated=reasons.to_numpy()))
checked = pd.concat(checked)

result = (checked.groupby(["source", "reason", "recalculated"])
          .size().reset_index(name="rows"))
same = (checked["reason"] == checked["recalculated"]).mean()
answer = f"{len(checked)} filas rechazadas; el ETL llega al mismo motivo en el {same:.0%}."
'''},
    {"name": "rn03_units", "group": GROUP_ETL,
     "question": "¿Cómo se pasa una unidad a precio por kilo?",
     "does": "Lee la unidad de venta y devuelve la unidad común y la cantidad por la que se "
             "divide el precio (RN-03 a RN-05). Una unidad sin una sola cantidad no se compara.",
     "functions": [etl.convert_unit],
     "params": [{"name": "unit", "label": "Unidad de venta", "text": "$/caja 18 kilos"}],
     "code": '''import pandas as pd

from etl import etl

units = [$unit, "$/bandeja 250 gramos", "$/malla 1,5 a 2 kilos", "$/unidad"]
rows = []
for unit in units:
    normalized_unit, quantity = etl.convert_unit(unit)
    rows.append({"unit": unit, "normalized_unit": normalized_unit,
                 "divide_price_by": quantity})

result = pd.DataFrame(rows)
first = rows[0]
if first["divide_price_by"]:
    answer = (f"{first['unit']}: se divide por {first['divide_price_by']:g} "
              f"y queda en $/{first['normalized_unit']}.")
else:
    answer = f"{first['unit']}: no declara una sola cantidad; no se compara (RN-05)."
'''},
    {"name": "k6_alerts", "group": GROUP_INDICATORS,
     "question": "¿Qué precios salieron de su rango habitual?",
     "does": "K6: la variación semanal de cada serie frente al promedio ± 2 desviaciones de "
             "sus 12 semanas anteriores. Va en Python porque SQLite no tiene desviación estándar.",
     "functions": [alerts.add_weekly_variation, alerts.add_usual_range, alerts.find_price_alerts],
     "params": [{"name": "channel", "label": "Canal", "options": "national_channel",
                 "default": DEFAULT_CHANNEL}],
     "code": '''from bi import alerts, queries

prices = queries.run_query("k6_national_weekly_price")
found = alerts.find_price_alerts(prices)

latest = found[(found["week_start"] == found["week_start"].max())
               & (found["channel"] == $channel)]
result = latest[["week_start", "product", "variety", "normalized_unit",
                 "variation", "usual_variation", "variation_deviation"]]
answer = f"{len(result)} precios fuera de su rango habitual en {$channel}."
'''},
    {"name": "k5_lag", "group": GROUP_INDICATORS,
     "question": "¿Con qué desfase sigue el consumidor?",
     "does": "K5: correlación entre los cambios semanales de ambos precios con desfases de 0 a "
             "8 semanas. Es descriptiva: no prueba que un precio cause el otro.",
     "functions": [lag.add_weekly_variations, lag.correlate_by_lag, lag.find_lag,
                   lag.is_clear_relation],
     "params": [{"name": "product", "label": "Producto", "options": "margin_product",
                 "default": DEFAULT_PRODUCT},
                {"name": "region", "label": "Región", "options": "margin_region",
                 "default": DEFAULT_REGION},
                {"name": "channel", "label": "Canal", "options": "consumer_channel",
                 "default": DEFAULT_CHANNEL}],
     "code": '''from bi import lag, queries

pairs = queries.run_query("k1_margin")
pairs = pairs[(pairs["product"] == $product) & (pairs["region"] == $region)
              & (pairs["channel"] == $channel)]
# One series: the variety, quality and unit with the most weeks.
key = ["variety", "quality", "normalized_unit"]
series = max((rows for _, rows in pairs.groupby(key)), key=len, default=pairs)

result = lag.correlate_by_lag(series)
best = lag.find_lag(result) if lag.has_enough_weeks(series) else None
if best is None:
    answer = f"Sin historia suficiente: K5 pide {lag.MINIMUM_WEEKS} semanas con ambos precios."
elif lag.is_clear_relation(best[1], best[2]):
    weeks = "la misma semana" if best[0] == 0 else f"{best[0]} semanas después"
    answer = f"El consumidor sigue al mayorista {weeks} (correlación {best[1]:.2f})."
else:
    answer = "Sin relación clara: la correlación más alta no se distingue del ruido."
'''},
    {"name": "context_usual_range", "group": GROUP_INDICATORS,
     "question": "¿Es normal el precio de esta semana?",
     "does": "Compara el precio de la última semana con el rango P25–P75 de las mismas "
             "semanas (± 1) de los años anteriores.",
     "functions": [price_context.rango_habitual, price_context.estado_precio],
     "params": [{"name": "product", "label": "Producto", "options": "national_product",
                 "default": DEFAULT_PRODUCT},
                {"name": "channel", "label": "Canal", "options": "national_channel",
                 "default": DEFAULT_CHANNEL}],
     "code": '''import pandas as pd

from bi import price_context, queries

prices = queries.run_query("k6_national_weekly_price")
prices = prices[(prices["product"] == $product) & (prices["channel"] == $channel)]
key = ["variety", "quality", "normalized_unit"]
series = max((rows for _, rows in prices.groupby(key)), key=len, default=prices)

week = series["week_start"].max()
price = series.loc[series["week_start"] == week, "national_price"].iloc[0]
usual = price_context.rango_habitual(series, week)
state = price_context.estado_precio(price, usual)

result = pd.DataFrame([{"week_start": week, "price": price,
                        "p25": usual[0] if usual else None,
                        "p75": usual[1] if usual else None,
                        "years_compared": usual[2] if usual else 0,
                        "state": state}])
readings = {"sobre": "sobre su rango habitual", "dentro": "dentro de su rango habitual",
            "bajo": "bajo su rango habitual", "sin_historia": "sin años previos para comparar"}
shown = f"{price:,.0f}".replace(",", ".")
answer = f"{$product} en {$channel}: ${shown} por {series['normalized_unit'].iloc[0]}, {readings[state]}."
'''},
    {"name": "k4_seasonal_pattern", "group": GROUP_INDICATORS,
     "question": "¿En qué meses suele estar más caro?",
     "does": "K4: el índice estacional de cada mes (100 = promedio del año), promediando "
             "primero cada mes de cada año y luego los años.",
     "functions": [price_context.patron_estacional],
     "params": [{"name": "product", "label": "Producto", "options": "national_product",
                 "default": DEFAULT_PRODUCT},
                {"name": "channel", "label": "Canal", "options": "national_channel",
                 "default": DEFAULT_CHANNEL}],
     "code": '''import pandas as pd

from bi import price_context, queries

rows = queries.run_query("k4_seasonal_index")
rows = rows[(rows["product"] == $product) & (rows["channel"] == $channel)]
key = ["variety", "quality", "normalized_unit"]
series = max((group for _, group in rows.groupby(key)), key=len, default=rows)

pattern = price_context.patron_estacional(series)
result = pd.DataFrame({"month": [price_context.MONTHS[month - 1] for month in pattern],
                       "seasonal_index": list(pattern.values())})
if not result.empty:
    top = result.loc[result["seasonal_index"].idxmax()]
    answer = f"Mes más caro: {top['month']} ({top['seasonal_index']:.0f} frente a 100)."
'''},
]
QUESTIONS_BY_NAME = {question["name"]: question for question in QUESTIONS}
# endregion


# region Scripts
def default_parameters(question, options):
    """{name: value} with each parameter's default, or the first option offered."""
    values = {}
    for parameter in question["params"]:
        if "text" in parameter:
            values[parameter["name"]] = parameter["text"]
        else:
            offered = options[parameter["options"]]
            values[parameter["name"]] = (parameter["default"] if parameter["default"] in offered
                                         else offered[0])
    return values


def check_parameters(question, values, options):
    """Raise ValueError for a value outside its closed list, or a unit too long."""
    for parameter in question["params"]:
        value = values[parameter["name"]]
        if "text" in parameter:
            if not isinstance(value, str) or len(value) > UNIT_MAXIMUM_LENGTH:
                raise ValueError(f"{parameter['label']}: hasta {UNIT_MAXIMUM_LENGTH} caracteres.")
        elif value not in options[parameter["options"]]:
            raise ValueError(f"{parameter['label']}: valor fuera de la lista.")


def build_script(question, values):
    """The script with each parameter written as a Python literal (repr), so a value
    can only ever be data, never code."""
    literals = {name: repr(value) for name, value in values.items()}
    return string.Template(question["code"]).safe_substitute(literals)


def run_script(question, values, options):
    """{result, answer, ms} of one run; the parameters are checked first."""
    check_parameters(question, values, options)
    namespace = {"__name__": "python_console"}
    started = time.perf_counter()
    exec(compile(build_script(question, values), question["name"], "exec"), namespace)
    milliseconds = (time.perf_counter() - started) * 1000
    result = namespace.get("result")
    if not isinstance(result, pd.DataFrame):
        result = pd.DataFrame()
    return {"result": result.reset_index(drop=True), "answer": namespace.get("answer"),
            "ms": milliseconds}


def describe_function(function):
    """(file path from the repository root, first line, source) of a real function."""
    path = Path(inspect.getsourcefile(function)).resolve().relative_to(PROJECT_DIR)
    lines, first_line = inspect.getsourcelines(function)
    return path.as_posix(), first_line, "".join(lines)
# endregion
