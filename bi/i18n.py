"""Spanish and English for the whole panel (D-283).

The panel is written in Spanish; `tr` gives the English text of a Spanish string when the reader chose English,
like the theme does with colors. The language lives in the session and in the address (`?lang=en`), so a shared link
opens in its language. The documents exist in both languages: docs/ in Spanish and docs/en/ in English, with the same
file names, structure and identifiers. No dependency: the translations are dictionaries of the project.
"""

from pathlib import Path

import streamlit as st

SPANISH, ENGLISH = "es", "en"
LANGUAGES = (SPANISH, ENGLISH)
LANGUAGE_PARAMETER = "lang"
LANGUAGE_STATE = "language"
LANGUAGE_NAMES = {SPANISH: "Español", ENGLISH: "English"}
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
# The header table and the standard sections of a document, by language.
DOCUMENT_FIELDS = {
    SPANISH: {
        "purpose": "Propósito",
        "version": "Versión",
        "date": "Fecha",
        "index": "Índice",
        "history": "Historial de versiones",
        "glossary": "Glosario",
        "type": "Tipo de documento",
        "status": "Estado",
        "owner": "Responsable",
        "audience": "Audiencia",
        "related": "Documentos relacionados",
        "project": "Proyecto",
    },
    ENGLISH: {
        "purpose": "Purpose",
        "version": "Version",
        "date": "Date",
        "index": "Contents",
        "history": "Version history",
        "glossary": "Glossary",
        "type": "Document type",
        "status": "Status",
        "owner": "Owner",
        "audience": "Audience",
        "related": "Related documents",
        "project": "Project",
    },
}

# Spanish text → English text. Grouped by where it shows; data (products, regions, channels) is never translated.
EN = {
    "Ampliar": "Enlarge",
    "Sin precios comparables esta semana": "No comparable prices this week",
    "En el promedio nacional": "At the national average",
    "{} más cara": "{} dearer",
    "{} más barata": "{} cheaper",
    "Mediana de {} precios comparados con el promedio nacional de los mismos productos": "Median of {} prices compared with the national average of the same products",
    "La más cara": "The dearest",
    "La más barata": "The cheapest",
    "De norte a sur: dónde queda cada región y cuán cara es frente al promedio nacional, con los mismos productos (semana {}).": "North to south: where each region lies and how dear it is against the national average, on the same products (week {}).",
    "Lugares de compra por región": "Places to buy, by region",
    "Ordenados de norte a sur. Cada región muestra dónde queda en el mapa.": "North to south. Each region shows where it lies on the map.",
    "Mercado o terminal mayorista": "Wholesale market or terminal",
    "Feria o vega": "Fair or vega",
    "Norte → Sur": "North → South",
    "Mapa": "Map",
    "Método y calidad": "Method and quality",
    "Evaluado según ISO/IEC 25010 · 25012": "Assessed against ISO/IEC 25010 · 25012",
    "Cómo se evaluó el proyecto: normas usadas como método, mediciones reales y lo que falta. Una autoevaluación, no una certificación.": "How the project was assessed: standards used as a method, real measurements and what is missing. A self-assessment, not a certification.",
    "Introducción": "Introduction",
    "Estándares": "Standards",
    "Datos": "Data",
    "Código": "Code",
    "Verificar": "Verify",
    "Límites": "Limits",
    ":material/storefront: Mayorista": ":material/storefront: Wholesale",
    ":material/database: Datos": ":material/database: Data",
    "Ampliar la tabla de productos": "Enlarge the products table",
    "Variación semanal, %. Rojo: subió · Azul: bajó.": "Weekly change, %. Red: rose · Blue: fell.",
    "Últimas {} semanas": "Last {} weeks",
    "Total {} sem": "Total {} wk",
    "¿Qué familias vienen subiendo, semana a semana?": "Which families keep rising, week by week?",
    "Lectura del período": "Reading of the period",
    "En estas {} semanas, {} es la que más se encareció: {} acumulado, con alzas en {} de ellas.": "In these {} weeks, {} got the dearest: {} in all, rising in {} of them.",
    "{} es la que más bajó: {} acumulado, con bajas en {} semanas.": "{} fell the most: {} in all, falling in {} weeks.",
    "En {} de las {} semanas subieron más familias de las que bajaron.": "In {} of the {} weeks more families rose than fell.",
    "Sectores": "Sectors",
    "Los mercados mayoristas y los puntos de venta de cada región, de norte a sur. Solo información: no hay precios por mercado, porque lo que sube en una región sube en todos sus mercados.": "The wholesale markets and points of sale of each region, north to south. Information only: there are no prices per market, because what rises in a region rises in all its markets.",
    "Preguntas reales de quien compra, de quien vende por mayor y de quien diseña los datos, con la respuesta de hoy.": "Real questions from whoever buys, whoever sells wholesale and whoever designs the data, with today's answer.",
    "Dónde comprar": "Where to buy",
    "Dónde se compra": "Where it is bought",
    "Comercio al detalle": "Retail shops",
    "Cada fila es una familia y cada columna una semana: rojo, subió; azul, bajó.": "Each row is a family and each column a week: red, rose; blue, fell.",
    "Tabla de las últimas semanas: qué familias vienen subiendo.": "Table of the last weeks: which families keep rising.",
    "Precios e inflación: qué alimentos subieron más que la inflación.": "Prices and inflation: which foods rose more than inflation.",
    "Alimentos desde 2022": "Food since 2022",
    "lo que subió la canasta": "how much the basket rose",
    "Alza en el último año": "Rise over the last year",
    "{} frente a un año antes": "{} against a year before",
    "Subieron más que la canasta": "Rose more than the basket",
    "Subieron menos que la canasta": "Rose less than the basket",
    "Iguales a la canasta": "Equal to the basket",
    "familias": "families",
    # Menu: sections, pages and sources
    "Negocio · BI": "Business · BI",
    "Ingeniería de datos": "Data engineering",
    "DevOps y seguridad": "DevOps and security",
    "Stack y evidencia": "Stack and evidence",
    "Documentos": "Documents",
    "Fuentes de datos": "Data sources",
    "Panorama de precios": "Price overview",
    "Precios e inflación": "Prices and inflation",
    "Pipeline y linaje": "Pipeline and lineage",
    "Modelo de datos": "Data model",
    "Calidad y auditoría": "Quality and audit",
    "Consultas SQL": "SQL queries",
    "Centro de operación": "Operations center",
    "Arquitectura de seguridad": "Security architecture",
    "Carpeta de documentos": "Documents folder",
    "Mapa de la app": "App map",
    # D-295: the profile dialog and the switch under the menu
    # D-296: the dashboard
    'Profesional': 'Professional',
    'todas las familias': 'all families',
    'Semana actual': 'Current week',
    'Precios comparables': 'Comparable prices',
    'Subieron': 'Rose',
    'Bajaron': 'Fell',
    'Alertas de precio': 'Price alerts',
    'inusuales': 'unusual',
    'Semanas': 'Weeks',
    'Cuántas semanas mostrar': 'How many weeks to show',
    'IPC de alimentos': 'Food CPI',
    'desde 2022': 'since 2022',
    'IPC en 12 meses': 'CPI over 12 months',
    'Sobre la inflación': 'Above inflation',
    'familias subieron más': 'families rose more',
    'Bajo la inflación': 'Below inflation',
    'familias subieron menos': 'families rose less',
    'Al ritmo': 'At pace',
    'familias a ± 2 puntos': 'families within ± 2 points',
    'Última carga': 'Last load',
    'publicada': 'published',
    'Filas leídas': 'Rows read',
    'de ODEPA': 'from ODEPA',
    'Filas rechazadas': 'Rows rejected',
    'Pruebas de dbt': 'dbt tests',
    'superadas': 'passed',
    'Indicadores de calidad': 'Quality indicators',
    'dentro de su umbral': 'within their threshold',
    'Semana': 'Week',
    'Mercado': 'Market',
    'Inflación': 'Inflation',
    'Datos y operación': 'Data and operations',
    'Dashboard': 'Dashboard',
    'lunes {}': 'Monday {}',
    'antes {}': 'before {}',
    'de {}': 'of {}',
    '{} vs anterior': '{} vs previous',
    "La carga del {} falló": "The load of {} failed",
    "El panel muestra la última carga válida.": "The panel shows the last valid load.",
    "Ver qué paso falló": "See which step failed",
    "La carga del {} falló: el panel muestra la última carga válida.": "The load of {} failed: the panel shows the last valid load.",
    'Ver': 'View',
    'Dimensión': 'Dimension',
    'Indicador': 'Indicator',
    'Valor': 'Value',
    'Qué significa': 'What it means',
    'Insights': 'Insights',
    "Para quién": "For whom",
    "Sectores de la ciudad": "City sectors",
    "Mercados mayoristas": "Wholesale markets",
    "Sin mercado mayorista en los datos": "No wholesale market in the data",
    "Puntos de venta al consumidor": "Consumer sales points",
    ":material/person: Persona común": ":material/person: Everyday person",
    ":material/storefront: Comerciante mayorista": ":material/storefront: Wholesale trader",
    ":material/database: Quien diseña los datos": ":material/database: Data designer",
    "Para": "For",
    "Una persona común": "An everyday person",
    "Un comerciante que compra por mayor": "A trader who buys wholesale",
    "Quien diseña o revisa los datos": "Whoever designs or reviews the data",
    "Elige tu vista": "Choose your view",
    "Usuario": "User",
    "Todas las familias": "All families",
    "Vista de usuario": "User view",
    "Vista profesional": "Professional view",
    "Ver todo el proyecto": "See the whole project",
    "La ingeniería de datos, la operación, la seguridad, el stack y la documentación.": "The data engineering, operations, security, the stack and the documentation.",
    "Clave": "Code",
    "Desbloquear": "Unlock",
    "Seguridad": "Security",
    "ODEPA: precios mayoristas": "ODEPA: wholesale prices",
    "ODEPA: precios al consumidor": "ODEPA: consumer prices",
    "INE: IPC de alimentos": "INE: food CPI",
    # The documents, by the name of their page
    "PRD · Requisitos del producto": "PRD · Product requirements",
    "SAD · Arquitectura": "SAD · Architecture",
    "ADR · Decisiones de arquitectura": "ADR · Architecture decisions",
    "Manual de operación": "Operations runbook",
    "Índice de decisiones": "Decision index",
    "Plan de pruebas y seguridad": "Test and security plan",
    "Glosario": "Glossary",
    # Sidebar footer
    "Apariencia": "Appearance",
    "Apariencia del panel": "Panel appearance",
    "Cambiar los colores: Corporativo, Vantablack, Blue Light o Dark Grey.": "Change the colors: Corporativo, Vantablack, Blue Light or Dark Grey.",
    "Fuente: ODEPA · actualización automática cada martes.": "Source: ODEPA · automatic update every Tuesday.",
    "GitHub del proyecto": "The project on GitHub",
    "Idioma": "Language",
    "Fuentes": "Sources",
    "Cambiar el idioma del panel y de los documentos.": "Change the language of the panel and of the documents.",
    # Header bar, freshness and footers
    "Volver": "Back",
    "Volver al punto anterior del proyecto, con su selección.": "Back to the previous point of the project, with its selection.",
    "Datos al": "Data as of",
    "Carga correcta": "Load succeeded",
    "Última carga con falla": "Last load failed",
    "← Anterior: {}": "← Previous: {}",
    "Siguiente: {} →": "Next: {} →",
    "Ruta": "Path",
    (
        "Datos: Oficina de Estudios y Políticas Agrarias (ODEPA), Ministerio de Agricultura de Chile, licencia Creative "
        "Commons Atribución; IPC de alimentos: Instituto Nacional de Estadísticas (INE). Este proyecto no es un producto "
        "oficial de ODEPA ni del INE. Lectura de los datos: el precio nacional es un promedio simple de las regiones, sin "
        "ponderar por población o ventas; cada variación semanal compara las mismas regiones en ambas semanas. Los "
        "indicadores describen el histórico; no predicen precios. Los precios se reconstruyen desde la fuente en las "
        "pruebas automáticas."
    ): (
        "Data: Office of Agricultural Studies and Policies (ODEPA), Ministry of Agriculture of Chile, Creative Commons "
        "Attribution license; food CPI: National Statistics Institute (INE). This project is not an official product "
        "of ODEPA or the INE. Reading the data: the national price is a simple average of the regions, not weighted by "
        "population or sales; each weekly change compares the same regions in both weeks. The indicators describe the "
        "history; they do not forecast prices. Prices are rebuilt from the source in the automated tests."
    ),
    # GitHub's answers, as the operations center describes them (bi/control.py)
    "GitHub no respondió en {} s": "GitHub did not answer within {} s",
    "no hubo conexión con GitHub": "there was no connection with GitHub",
    "error inesperado al consultar GitHub ({})": "unexpected error when querying GitHub ({})",
    "se agotó el límite de consultas sin clave (60 por hora)": "the limit of requests without a key ran out (60 per hour)",
    "se agotó el límite de consultas": "the limit of requests ran out",
    "GitHub respondió {}: {}": "GitHub answered {}: {}",
    "GitHub respondió {}: {}; se renueva en {} min": "GitHub answered {}: {}; it renews in {} min",
    "la clave no es válida o venció": "the key is not valid or expired",
    "acceso denegado": "access denied",
    "no se encontró el workflow": "the workflow was not found",
    "error interno de GitHub": "GitHub internal error",
    "GitHub no está disponible": "GitHub is not available",
    "error al consultar GitHub": "error when querying GitHub",
    "se muestra la última respuesta guardada": "the last saved answer is shown",
    "los estados salen de la última carga guardada en la base ({})": "the states come from the last load saved in the database ({})",
    "GitHub no respondió ({}); {}.": "GitHub did not answer ({}); {}.",
    # The SQL studio, where some texts are preformatted (bi/sql_explorer.py)
    "{}: todas": "{}: all",
    "Período": "Period",
    "Familia": "Family",
    "Producto": "Product",
    "Canal": "Channel",
    "Región": "Region",
    "Año": "Year",
    "Sin mensajes todavía. Ejecuta una consulta.": "No messages yet. Run a query.",
    "La consulta no se ejecutó.": "The query did not run.",
    "Se muestran las primeras {} filas; el resultado tenía más.": "The first {} rows are shown; the result had more.",
    "({} filas afectadas)": "({} rows affected)",
    "Consulta ejecutada correctamente.": "Query executed successfully.",
    "Tiempo: {} ms": "Time: {} ms",
    # The dbt badge of the footers
    "Linaje dbt: en migración": "dbt lineage: being migrated",
    "Última construcción de dbt:": "Last dbt build:",
    "modelos": "models",
    "pruebas superadas": "tests passed",
    # Documents: folder, actions and printing
    "Los documentos del proyecto, leídos de docs/: cada uno se abre aquí, se imprime como PDF o se lee en GitHub.": "The documents of the project, read from docs/: each one opens here, prints as a PDF or reads on GitHub.",
    "Vista de la carpeta": "Folder view",
    "Documentación": "Documentation",
    "Cuadrícula": "Grid",
    "Lista": "List",
    "documentos · último cambio": "documents · last change",
    "Índice": "Contents",
    "y {} más": "and {} more",
    "min de lectura": "min read",
    "Abrir": "Open",
    "Abre el documento y lo imprime o guarda como PDF": "Opens the document and prints it or saves it as a PDF",
    "El archivo en GitHub": "The file on GitHub",
    "Imprimir o guardar como PDF": "Print or save as PDF",
    "en GitHub": "on GitHub",
    "Qué resuelve el producto, para quién y con qué requisitos.": "What the product solves, for whom and with which requirements.",
    "Cómo está construido, cómo corre cada semana, dónde viven sus datos y cómo puede crecer.": "How it is built, how it runs each week, where its data lives and how it can grow.",
    "Las decisiones de arquitectura que más pesan: contexto, decisión, opciones y consecuencias.": "The architecture decisions that weigh most: context, decision, options and consequences.",
    "Cómo operar el proyecto y resolver sus fallas.": "How to operate the project and solve its failures.",
    "Las decisiones que cambian la arquitectura, los datos, la seguridad o la operación, por tema.": "The decisions that change the architecture, the data, the security or the operations, by theme.",
    "Qué se prueba, quién participa en la seguridad y con qué criterios se acepta un cambio.": "What is tested, who takes part in security and with which criteria a change is accepted.",
    "Las siglas y los términos del panel y de los documentos.": "The acronyms and terms of the panel and the documents.",
}


def get_language():
    """The language of the visit; Spanish until the reader chooses English."""
    language = st.session_state.get(LANGUAGE_STATE)
    return language if language in LANGUAGES else SPANISH


def settle_language():
    """The address wins when it names a language (a shared link); otherwise the session keeps it."""
    requested = st.query_params.get(LANGUAGE_PARAMETER)
    if requested in LANGUAGES:
        st.session_state[LANGUAGE_STATE] = requested
    choose_language(get_language())


def choose_language(language):
    """Spanish is the default and keeps the addresses as they were; English shows as ?lang=en."""
    st.session_state[LANGUAGE_STATE] = language
    if language == SPANISH:
        st.query_params.pop(LANGUAGE_PARAMETER, None)
    else:
        st.query_params[LANGUAGE_PARAMETER] = language


def address_parameters():
    """What a link adds to its address to keep the language: nothing in Spanish, lang=en in English."""
    return {} if get_language() == SPANISH else {LANGUAGE_PARAMETER: get_language()}


def is_english():
    return get_language() == ENGLISH


def tr(text):
    """The text in the language of the visit: English from EN when the reader chose it, otherwise as written."""
    return EN.get(text, text) if is_english() else text


def documents_dir(language=None):
    """docs/ for Spanish, docs/en/ for English: the same files, in each language."""
    return DOCS_DIR / "en" if (language or get_language()) == ENGLISH else DOCS_DIR


def document_field(name, language=None):
    return DOCUMENT_FIELDS[language or get_language()][name]


# region Translation at render time (D-284)
# The pages are written in Spanish in many modules. Instead of wrapping every literal, the panel translates what it
# draws, at the boundary with Streamlit: each text node and each visible attribute of an HTML block, each label of a
# widget, each column of a table. A text is translated only as a whole (an exact entry, or a template whose «{}» stand
# for numbers or data), never word by word, so an untranslated sentence stays whole instead of half translated.
import html as _html  # noqa: E402
import re as _re  # noqa: E402

from bi import i18n_en  # noqa: E402

PAGES = i18n_en.PAGES
NUMBER = _re.compile(r"[−+-]?\d[\d.,]*\d|[−+-]?\d")
ONLY_FIGURES = _re.compile(r"[\s$%−+\-–·/()×↑↓=~≈±]*(?:\d[\d.,\s]*[\s$%−+\-–·/()×↑↓=~≈±.:;]*)+")
TEXT_NODE = _re.compile(r">([^<>]+)<")
ATTRIBUTE = _re.compile(
    r'(\b(?:title|aria-label|alt|placeholder|data-tip|data-title|data-label|data-what)=")([^"]*)(")'
)
# Scripts keep their code (only their whole strings are looked up); styles, code and preformatted text are left alone.
BLOCK = _re.compile(
    r"(<script\b[^>]*>)(.*?)(</script>)|(<style\b[^>]*>.*?</style>|<pre\b[^>]*>.*?</pre>|<code\b[^>]*>.*?</code>)",
    _re.DOTALL | _re.IGNORECASE,
)
JS_STRING = _re.compile(r"""(["'])((?:(?!\1)[^\\\n]|\\.){2,}?)\1""")
_templates = None


def localize_number(text):
    """A Spanish figure written the English way: 1.609 → 1,609 and 0,2 → 0.2."""
    # Only a figure written the Spanish way: 1.609, 2.521.012, 0,2 or 33,7; a version like 1.5.6 stays as it is.
    if not _re.fullmatch(r"[−+-]?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?", text):
        return text
    swapped = text.replace(".", "\u0000").replace(",", ".").replace("\u0000", ",")
    return swapped


def localize_figures(text):
    return NUMBER.sub(lambda match: localize_number(match.group(0)), text)


MONTHS = dict(
    zip(
        ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    )
)
MONTH = "(" + "|".join(MONTHS) + ")"
FULL_MONTHS = dict(
    zip(
        [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ],
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
    )
)


def localize_date(text):
    """A Spanish date written the English way, or None: 05-10-2026 → 2026-10-05, 12–18 oct 2026 → Oct 12–18, 2026,
    20 oct → Oct 20, 05-10 → Oct 5."""
    if match := _re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", text):
        return f"{match[3]}-{match[2]}-{match[1]}"
    if match := _re.fullmatch(rf"(\d{{1,2}})[–-](\d{{1,2}}) {MONTH} (\d{{4}})", text):
        return f"{MONTHS[match[3]]} {match[1]}–{match[2]}, {match[4]}"
    if match := _re.fullmatch(rf"(\d{{1,2}})[–-](\d{{1,2}}) {MONTH}", text):
        return f"{MONTHS[match[3]]} {match[1]}–{match[2]}"
    if match := _re.fullmatch(rf"(\d{{1,2}}) {MONTH}( \d{{4}})?((?: · \d{{2}}:\d{{2}})?)", text):
        return f"{MONTHS[match[2]]} {match[1]}{',' + match[3] if match[3] else ''}{match[4]}"
    if match := _re.fullmatch(r"(" + "|".join(FULL_MONTHS) + r")(?: de)? (\d{4})", text, _re.IGNORECASE):
        return f"{FULL_MONTHS[match[1].lower()]} {match[2]}"
    if match := _re.fullmatch(rf"{MONTH}\.? (\d{{4}})", text):
        return f"{MONTHS[match[1]]} {match[2]}"
    if match := _re.fullmatch(r"(\d{2})-(\d{2})( \d{2}:\d{2})", text):
        return (
            f"{list(MONTHS.values())[int(match[2]) - 1]} {int(match[1])}{match[3]}"
            if 1 <= int(match[2]) <= 12
            else None
        )
    if match := _re.fullmatch(r"(\d{2})-(\d{2})", text):
        return f"{list(MONTHS.values())[int(match[2]) - 1]} {int(match[1])}" if 1 <= int(match[2]) <= 12 else None
    return None


# What each placeholder of a template may hold: «{}» anything, «{n}» a figure, «{m}» a month and year, «{d}» a date.
PLACEHOLDERS = {
    "{}": r"(.+?)",
    "{n}": r"([−+-]?\d[\d.,]*(?: ?%)?)",
    "{m}": r"((?:" + "|".join(FULL_MONTHS) + r") \d{4})",
    "{d}": r"(\d{1,2}[-–]\d{1,2}(?:[-–]\d{2,4})?|\d{1,2}(?:[–-]\d{1,2})? (?:" + "|".join(MONTHS) + r")(?: \d{4})?)",
}
PLACEHOLDER = _re.compile(r"\{[nmd]?\}")


def compile_templates():
    """Entries with placeholders become patterns, the most specific first."""
    patterns = []
    for spanish, english in {**EN, **PAGES}.items():
        holes = PLACEHOLDER.findall(spanish)
        if holes and len(holes) == len(PLACEHOLDER.findall(english)):
            literal = [_re.escape(part) for part in PLACEHOLDER.split(spanish)]
            pattern = literal[0] + "".join(PLACEHOLDERS[hole] + part for hole, part in zip(holes, literal[1:]))
            patterns.append((_re.compile(pattern + r"\Z", _re.DOTALL), PLACEHOLDER.sub("{}", english)))
    patterns.sort(key=lambda item: -len(item[0].pattern))
    return patterns


def lookup(text):
    """The English of a whole text, or None."""
    global _templates
    if text in EN:
        return EN[text]
    if text in PAGES:
        return PAGES[text]
    if ONLY_FIGURES.fullmatch(text):
        return localize_figures(text)
    if _templates is None:
        _templates = compile_templates()
    for pattern, english in _templates:
        match = pattern.match(text)
        if match:
            return english.format(*[translate_part(part) for part in match.groups()])
    return None


def translate_part(part):
    """What a «{}» of a template holds: a date, a figure, an entry, or data kept as it is."""
    stripped = part.strip()
    english = localize_date(stripped) or (localize_figures(stripped) if ONLY_FIGURES.fullmatch(stripped) else None)
    return part.replace(stripped, english, 1) if english else translate_text(part)


def translate_text(text):
    """A text in the language of the visit, keeping the spaces around it."""
    if not text or not is_english():
        return text
    stripped = text.strip()
    if not stripped:
        return text
    english = lookup(stripped) or localize_date(stripped)
    if english is None and "\n" in stripped:
        lines = stripped.split("\n")
        translated = [translate_text(line) for line in lines]
        english = "\n".join(translated) if translated != lines else None
    return text if english is None else text.replace(stripped, english, 1)


def translate_markup_text(text):
    """A text node or attribute of HTML: unescaped to look it up, escaped again."""
    plain = _html.unescape(text)
    english = translate_text(plain)
    return text if english == plain else _html.escape(english, quote=False)


def translate_script(script):
    """Inside a script, only string literals that are a whole entry: the texts a script writes on the page."""

    def string(match):
        english = lookup(match.group(2))
        return (
            f"{match.group(1)}{english}{match.group(1)}"
            if english and match.group(1) not in english
            else match.group(0)
        )

    return JS_STRING.sub(string, script)


def translate_html(markup):
    """Each text node and visible attribute of an HTML block. Protected blocks are set aside behind a marker shaped
    like a tag, so the text right before or after them still reads as a whole node."""
    if not markup or not is_english() or not isinstance(markup, str):
        return markup
    kept = []

    def keep(block):
        kept.append(
            block.group(1) + translate_script(block.group(2)) + block.group(3) if block.group(1) else block.group(4)
        )
        return f"<\u0001{len(kept) - 1}\u0001>"

    marked = _translate_plain_html(BLOCK.sub(keep, markup))
    return _re.sub("<\u0001(\\d+)\u0001>", lambda match: kept[int(match.group(1))], marked)


def _translate_plain_html(markup):
    markup = TEXT_NODE.sub(lambda match: ">" + translate_markup_text(match.group(1)) + "<", markup)
    return ATTRIBUTE.sub(lambda match: match.group(1) + translate_markup_text(match.group(2)) + match.group(3), markup)


def translate_any(value):
    """A label or a body: HTML when it has tags, otherwise a whole text, line by line for Markdown."""
    if not isinstance(value, str) or not is_english():
        return value
    if "<" in value and ">" in value:
        return translate_html(value)
    whole = translate_text(value)
    if whole != value:
        return whole
    return "\n".join(translate_markdown_line(line) for line in value.split("\n"))


MARKDOWN_PREFIX = _re.compile(r"^(\s*(?:#{1,6}\s+|[-*]\s+|>\s*|\d+\.\s+)?)(.*)$", _re.DOTALL)


def translate_markdown_line(line):
    """A Markdown line: its heading, list or quote mark kept, the rest translated whole."""
    mark, rest = MARKDOWN_PREFIX.match(line).groups()
    return mark + translate_text(rest) if rest.strip() else line


def join_names(names):
    """«a, b y c» in Spanish, «a, b and c» in English."""
    names = list(names)
    if len(names) < 2:
        return "".join(names)
    return ", ".join(names[:-1]) + (" and " if is_english() else " y ") + names[-1]


QUOTED = _re.compile(r"""(["'])((?:(?!\1).){2,}?)\1""")


def translate_dataset(data):
    """A chart's data as Streamlit carries it, Arrow bytes (D-294): its text cells that are a whole entry, translated
    like the same names in the scales and conditions. Without it, a series renamed in its scale («Food CPI (INE)»)
    no longer finds its rows («IPC alimentos (INE)») and its line disappears."""
    import pyarrow as pa
    from streamlit import dataframe_util

    try:
        table = pa.ipc.open_stream(data).read_all()
    except (pa.ArrowInvalid, TypeError):
        return data
    changed = False
    columns = []
    for column in table.columns:
        if pa.types.is_string(column.type) or pa.types.is_large_string(column.type):
            values = column.to_pylist()
            english = [
                (lookup(value.strip()) or value) if isinstance(value, str) and value.strip() else value
                for value in values
            ]
            if english != values:
                changed = True
                column = pa.array(english, type=column.type)
        columns.append(column)
    if not changed:
        return data
    return dataframe_util.convert_arrow_table_to_arrow_bytes(pa.Table.from_arrays(columns, schema=table.schema))


def translate_spec(spec):
    """A chart: its titles, labels, tooltips and the labels of its series, wherever they appear, so the data, the
    scales and the conditions keep naming the same thing."""
    if isinstance(spec, (bytes, bytearray)):
        return translate_dataset(bytes(spec))
    if isinstance(spec, dict):
        return {key: translate_spec(value) for key, value in spec.items()}
    if isinstance(spec, list):
        return [translate_spec(value) for value in spec]
    if isinstance(spec, str):
        english = lookup(spec.strip()) if spec.strip() else None
        if english:
            return english
        if "'" in spec or '"' in spec:  # an expression that names a series: datum.serie == 'IPC de alimentos (INE)'
            return QUOTED.sub(lambda m: f"{m[1]}{EN.get(m[2]) or PAGES.get(m[2]) or m[2]}{m[1]}", spec)
    return spec


def translate_frame(frame):
    """A table: its column names and the cells that are a whole entry (labels, never data)."""
    try:
        import pandas as pd
    except ImportError:  # pragma: no cover
        return frame
    if not is_english() or not isinstance(frame, pd.DataFrame):
        return frame
    frame = frame.rename(columns=lambda column: translate_text(column) if isinstance(column, str) else column)
    for column in frame.columns:
        if frame[column].dtype == object:
            frame[column] = frame[column].map(lambda cell: translate_text(cell) if isinstance(cell, str) else cell)
    return frame


def _wrap(method, first="body", keys=("label", "help", "placeholder", "caption"), frame=False, options=False):
    def translated(self, *args, **kwargs):
        if is_english():
            args = list(args)
            if args:
                args[0] = (
                    translate_frame(args[0])
                    if frame
                    else (
                        [translate_any(item) for item in args[0]]
                        if isinstance(args[0], (list, tuple)) and options
                        else translate_any(args[0])
                    )
                )
            for key in (first, *keys):
                if key in kwargs:
                    kwargs[key] = translate_frame(kwargs[key]) if frame and key == first else translate_any(kwargs[key])
            if options and "format_func" not in kwargs and len(args) > 1 and not frame:
                kwargs["format_func"] = lambda option: translate_any(str(option))
        return method(self, *args, **kwargs)

    translated.__wrapped__ = method
    return translated


def install():
    """Translate everything the panel draws through Streamlit (once per process)."""
    from streamlit.delta_generator import DeltaGenerator

    if getattr(DeltaGenerator, "_i18n_installed", False):
        return
    plain = [
        "markdown",
        "html",
        "caption",
        "subheader",
        "title",
        "header",
        "text",
        "info",
        "warning",
        "error",
        "success",
        "button",
        "link_button",
        "download_button",
        "page_link",
        "expander",
        "popover",
        "toggle",
        "checkbox",
        "text_input",
        "text_area",
        "metric",
    ]
    for name in plain:
        setattr(
            DeltaGenerator,
            name,
            _wrap(getattr(DeltaGenerator, name), first={"page_link": "label", "button": "label"}.get(name, "body")),
        )
    for name in ("radio", "selectbox", "segmented_control", "pills", "multiselect"):
        setattr(DeltaGenerator, name, _wrap(getattr(DeltaGenerator, name), first="label", options=True))
    setattr(DeltaGenerator, "tabs", _wrap(DeltaGenerator.tabs, first="tabs", options=True))
    for name in ("dataframe", "table"):
        setattr(DeltaGenerator, name, _wrap(getattr(DeltaGenerator, name), first="data", frame=True))
    setattr(DeltaGenerator, "iframe", _wrap(DeltaGenerator.iframe, first="src"))
    from streamlit.elements import vega_charts

    prepare = vega_charts._prepare_vega_lite_spec

    def prepare_translated(spec, *args, **kwargs):
        spec = prepare(spec, *args, **kwargs)
        return translate_spec(spec) if is_english() else spec

    vega_charts._prepare_vega_lite_spec = prepare_translated
    DeltaGenerator._i18n_installed = True
    for name in plain + [
        "radio",
        "selectbox",
        "segmented_control",
        "pills",
        "multiselect",
        "tabs",
        "dataframe",
        "table",
        "iframe",
    ]:
        setattr(st, name, getattr(st._main, name))


# endregion
