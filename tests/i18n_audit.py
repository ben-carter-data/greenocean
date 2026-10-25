"""What a page still shows in Spanish when the reader chose English (D-284).

Used by tests/test_i18n.py and runnable by hand to list what is left to translate:
    python tests/i18n_audit.py ["Página del menú" ...]
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

DASHBOARD_FILE = str(ROOT / "bi" / "dashboard.py")
SPANISH_MARKS = re.compile(r"[áéíóúñ¿¡]|\b(?:de|la|las|los|del|que|para|con|una|por|cada|sin|más|semana|semanas|precio|"
                           r"precios|carga|cargas|datos|fila|filas|pruebas|prueba|qué|cómo|dónde|cuándo|según|"
                           r"también|sólo|solo|está|están|es|se|al|el|en|y)\b", re.IGNORECASE)
TEXT_NODE = re.compile(r">([^<>]+)<")
ATTRIBUTE = re.compile(r'\b(?:title|aria-label|alt|placeholder|data-tip|data-title|data-label|data-what)="([^"]*)"')
CODE = re.compile(r"<(script|style|pre|code)\b[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
# The official name of a region, as the map of Chile writes it: «Región de Los Ríos».
OFFICIAL_REGION = re.compile(r"^Región (?:de |del )?[^\n·]+$", re.MULTILINE)


# Proper names drawn by the map of Chile and two-letter codes that are not Spanish words.
PROPER_NAMES = {"Arica y Parinacota", "Tarapacá", "Antofagasta", "Atacama", "Coquimbo", "Valparaíso", "Metropolitana",
                "O'Higgins", "Maule", "Ñuble", "Biobío", "La Araucanía", "Los Ríos", "Los Lagos", "Aysén", "Magallanes",
                "ES", "EN"}


def read_data_values():
    """ODEPA's own names (products, varieties, families, regions, channels): data, never translated."""
    import duckdb
    from bi import queries
    values = set(PROPER_NAMES)
    with duckdb.connect(str(queries.DATABASE_FILE), read_only=True) as connection:
        for table, column in (("dim_product", "product"), ("dim_product", "variety"), ("dim_product", "product_group"),
                              ("dim_product", "quality"), ("dim_region", "region"), ("dim_channel", "channel")):
            values |= {row[0] for row in connection.execute(f"SELECT DISTINCT {column} FROM {table}").fetchall() if row[0]}
    # The panel writes «Lácteos - Huevos - Margarinas» as «Lácteos · Huevos · Margarinas».
    return values | {value.replace(" - ", " · ") for value in values}


def texts_of(markup):
    """The text nodes and visible attributes of an HTML block, or the lines of a plain text."""
    if not isinstance(markup, str):
        return []
    if "<" in markup and ">" in markup:
        markup = CODE.sub("", markup)
        return [html.unescape(text).strip() for text in TEXT_NODE.findall(markup) + ATTRIBUTE.findall(markup)]
    return [line.strip() for line in markup.split("\n")]


def collect(app):
    texts = []
    for element in app.markdown:
        texts += texts_of(element.value)
    for kind in ("html", "iframe"):
        for element in app.get(kind):
            texts += texts_of(getattr(element.proto, "body", "") or getattr(element.proto, "srcdoc", ""))
    for kind in ("caption", "subheader", "title", "header", "info", "warning", "error", "success"):
        texts += [element.value for element in getattr(app, kind, [])]
    for button in app.button:
        texts.append(button.label)
    for tab in app.tabs:
        texts.append(tab.label)
    for link in app.get("page_link"):
        texts.append(link.proto.label)
    for kind in ("selectbox", "radio", "multiselect", "segmented_control", "pills"):
        for widget in app.get(kind):
            texts.append(getattr(widget, "label", "") or "")
            texts += [str(option) for option in (getattr(widget, "options", None) or [])]
    for widget in app.get("text_input"):
        texts += [widget.label, getattr(widget.proto, "placeholder", "")]
    for widget in app.get("expander") + app.get("popover"):
        texts.append(getattr(widget.proto, "label", "") or "")
    for frame in app.dataframe:
        texts += [str(column) for column in frame.value.columns]
    for chart in app.get("vega_lite_chart") + app.get("arrow_vega_lite_chart"):
        texts += chart_texts(json.loads(chart.proto.spec))
    return texts


def chart_texts(spec):
    """The titles and labels a chart writes."""
    found = []
    if isinstance(spec, dict):
        for key, value in spec.items():
            if key in ("title", "text", "description") and isinstance(value, str):
                found.append(value)
            else:
                found += chart_texts(value)
    elif isinstance(spec, list):
        for value in spec:
            found += chart_texts(value)
    return found


def spanish_left(view, data_values, theme=None, state=None):
    app = AppTest.from_file(DASHBOARD_FILE, default_timeout=120)
    app.query_params.update({"lang": "en", "vista": view} | ({"tema": theme} if theme else {}))
    for key, value in (state or {}).items():
        app.session_state[key] = value
    app.run()
    if app.exception:
        raise RuntimeError(app.exception)
    left = []
    names = sorted(data_values, key=len, reverse=True)
    for text in collect(app):
        text = (text or "").strip()
        if len(text) < 2 or text in data_values:
            continue
        # The data inside a sentence (a product, a family, a region) stays in Spanish: judge the rest.
        rest = OFFICIAL_REGION.sub("", text)
        for name in names:
            if name in rest:
                rest = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", "", rest)
        rest = re.sub(r"\]\([^)]*\)|https?://\S+|`[^`]*`", "", rest)  # link addresses and code keep their own names
        rest = re.sub(r"\S*[./_]\w\S*", "", rest)  # file names and identifiers: datos.duckdb, stg_odepa__consumer
        rest = re.sub(r"«[^»]*»|\*[^*\n]+\*|(?<!\w)ñ(?!\w)", "", rest)  # a name as the source writes it: «…», or in italics: *Oficina de …*
        if SPANISH_MARKS.search(rest):
            left.append(text)
    return sorted(set(left))


def screens():
    """Every screen to audit: each page of the menu, the views a page shows only after a switch or a click, and the
    documents."""
    from bi import dashboard, quality_evidence
    return [(view, None) for view in dashboard.MENU_ORDER] + [
        (dashboard.PAGE_DIAGRAMS, {dashboard.PIPELINE_VIEW_KEY: dashboard.PIPELINE_LINEAGE})] + [
        (dashboard.PAGE_ARCHITECTURE, {dashboard.MODEL_VIEW_KEY: view}) for view in dashboard.MODEL_VIEWS[1:]] + [
        (page, None) for page in dashboard.FOLDER_ORDER] + [
        (dashboard.PAGE_OPERATIONS, {dashboard.QUALITY_OPEN_KEY: title}) for title in quality_evidence.TITLES.values()]


if __name__ == "__main__":
    values = read_data_values()
    chosen = sys.argv[1:]
    for view, state in screens():
        if chosen and view not in chosen:
            continue
        left = spanish_left(view, values, state=state)
        print(f"\n## {view}{' · ' + str(state) if state else ''}: {len(left)}")
        for text in left:
            print(f"  {text!r}")
