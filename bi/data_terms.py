"""D-403: the words the data brings, in the reader's language: families, channels, qualities and units.

ODEPA writes them in Spanish and the database keeps them as published. The panel translates them only when it draws a
page (the Dashboard, the channel pages), never in the data: the SQL studio and the downloads show what is stored. The
product names are not translated. A test checks that every family, channel, quality and unit of the served database
has its English here.
"""

import re

from bi import i18n

FAMILIES = {
    "Abarrotes y otros": "Groceries and others",
    "Carne bovina": "Beef",
    "Carne de Cerdo - Ave - Cordero": "Pork - Poultry - Lamb",
    "Frutas": "Fruit",
    "Hortalizas": "Vegetables",
    "Lácteos - Huevos - Margarinas": "Dairy - Eggs - Margarines",
    "Pan": "Bread",
    # The short names the Dashboard draws (D-301)
    "Cerdo · Ave · Cordero": "Pork · Poultry · Lamb",
    "Lácteos y huevos": "Dairy and eggs",
}
CHANNELS = {
    "Carnicería": "Butcher shop",
    "Feria libre": "Street market",
    "Mayorista": "Wholesale",
    "Mercado Mayorista": "Wholesale market",
    "Mercado Minorista": "Retail market",
    "Panadería": "Bakery",
    "Supermercado": "Supermarket",
    "Supermercado en Línea": "Online supermarket",
}
UNITS = {"kilo": "kilo", "litro": "liter", "unidad": "unit"}
QUALITIES = {
    "1a (cosecha lavada)": "1st (washed, harvest)",
    "1a (cosecha)": "1st (harvest)",
    "1a (guarda lavada)": "1st (washed, storage)",
    "1a (guarda)": "1st (storage)",
    "1a (nueva lavada)": "1st (washed, new)",
    "1a amarillo": "1st yellow",
    "1a nueva(o)": "1st new",
    "1a plateado": "1st silver",
    "2a (cosecha)": "2nd (harvest)",
    "2a (guarda)": "2nd (storage)",
    "2a amarillo": "2nd yellow",
    "2a nueva(o)": "2nd new",
    "2a plateado": "2nd silver",
    "3a (cosecha)": "3rd (harvest)",
    "3a (guarda)": "3rd (storage)",
    "3a amarillo": "3rd yellow",
    "3a nueva (o)": "3rd new",
    "3a plateado": "3rd silver",
    "4a nueva (o)": "4th new",
    "Banquete": "Banquet",
    "Camote": "Camote",
    "Camote amarillo": "Yellow camote",
    "Camote plateado": "Silver camote",
    "Cuarta": "Fourth",
    "Dedos": "Fingers",
    "Especial": "Special",
    "Especial amarillo": "Special yellow",
    "Especial nueva (o)": "Special new",
    "Especial plateado": "Special silver",
    "Extra": "Extra",
    "Extra (doble especial)": "Extra (double special)",
    "Extra (muy buena)": "Extra (very good)",
    "Extra Cosecha": "Extra harvest",
    "Extra Guarda": "Extra storage",
    "Extra nueva (o)": "Extra new",
    "Maduro": "Ripe",
    "Pintón": "Half-ripe",
    "Primera": "First",
    "Primera Maduro": "First, ripe",
    "Primera Pintón": "First, half-ripe",
    "Primera Verde": "First, green",
    "Primor": "Premium",
    "Segunda": "Second",
    "Sin especificar": "Unspecified",
    "Super": "Super",
    "Tercera": "Third",
    "Verde": "Green",
    "s/e (semillón cosecha)": "n/s (semillón, harvest)",
    "s/e (semillón nueva)": "n/s (semillón, new)",
}
TERMS = {**FAMILIES, **CHANNELS, **UNITS, **QUALITIES}
SIZE = re.compile(r"^Calibre (\d+)$")  # «Calibre 120» and its siblings: the size class, by number


def english(value):
    """The English of one word of the data, or None when the table does not have it."""
    text = str(value)
    if text in TERMS:
        return TERMS[text]
    size = SIZE.match(text)
    return f"Size {size.group(1)}" if size else None


def term(value):
    """A word of the data as the reader reads it: its English when the visit is in English, otherwise as stored."""
    if value is None or not i18n.is_english():
        return value
    return english(value) or str(value)
