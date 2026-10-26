"""Search of «Consulta por clics»: a form, a summary, a table and a detail (D-060).

The reader fills a form; the panel finds the weekly prices that match, says how
many of them are normal, worth a look or out of their usual range, lists them
page by page and opens the detail of the one chosen.

Every field is checked against a fixed list (an allowlist), so only known
columns reach a query. The values the reader chooses always travel as SQL
parameters (?), never inside the SQL text. The weekly change comes from SQL
(LAG); the alert state reuses K6 (bi/alerts.py), so its logic lives in one place.
"""



# region Constants
FIELD_GROUP = "group"
FIELD_PRODUCT = "product"
FIELD_VARIETY = "variety"
FIELD_QUALITY = "quality"
FIELD_REGION = "region"
FIELD_CHANNEL = "channel"
FIELD_SOURCE = "source"
ALL = "Todos"
SOURCE_NAMES = {"wholesale": "Mayorista", "consumer": "Consumidor"}


DAYS_IN_A_WEEK = 7


# endregion


# endregion


# endregion


# endregion
