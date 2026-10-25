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
    SPANISH: {"purpose": "Propósito", "version": "Versión", "date": "Fecha", "index": "Índice",
              "history": "Historial de versiones", "glossary": "Glosario"},
    ENGLISH: {"purpose": "Purpose", "version": "Version", "date": "Date", "index": "Contents",
              "history": "Version history", "glossary": "Glossary"},
}

# Spanish text → English text. Grouped by where it shows; data (products, regions, channels) is never translated.
EN = {
    # Menu: sections, pages and sources
    "Negocio · BI": "Business · BI",
    "Ingeniería de datos": "Data engineering",
    "DevOps y seguridad": "DevOps and security",
    "Stack y evidencia": "Stack and evidence",
    "Documentos": "Documents",
    "Fuentes de datos": "Data sources",
    "Resumen semanal": "Weekly summary",
    "Precios e inflación": "Prices and inflation",
    "Pipeline y linaje": "Pipeline and lineage",
    "Modelo de datos": "Data model",
    "Calidad y auditoría": "Quality and audit",
    "Consultas SQL": "SQL queries",
    "Centro de operación": "Operations center",
    "Arquitectura de seguridad": "Security architecture",
    "Carpeta de documentos": "Documents folder",
    "ODEPA: precios mayoristas": "ODEPA: wholesale prices",
    "ODEPA: precios al consumidor": "ODEPA: consumer prices",
    "INE: IPC de alimentos": "INE: food CPI",
    # The documents, by the name of their page
    "PRD · Requisitos del producto": "PRD · Product requirements",
    "SAD · Arquitectura": "SAD · Architecture",
    "ADR · Decisiones de arquitectura": "ADR · Architecture decisions",
    "Escalabilidad": "Scalability",
    "Plan de pruebas de seguridad": "Security test plan",
    "Manual de operación": "Operations runbook",
    "Índice de decisiones": "Decision index",
    "Diccionario de datos": "Data dictionary",
    "Plan de pruebas": "Test plan",
    "Glosario": "Glossary",
    # Sidebar footer
    "Apariencia": "Appearance",
    "Apariencia del panel": "Panel appearance",
    "Cambiar los colores: Corporativo, Vantablack, Blue Light o Dark Grey.":
        "Change the colors: Corporativo, Vantablack, Blue Light or Dark Grey.",
    "Fuente: ODEPA · actualización automática cada martes.": "Source: ODEPA · automatic update every Tuesday.",
    "GitHub del proyecto": "The project on GitHub",
    "Idioma": "Language",
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
    ("Datos: Oficina de Estudios y Políticas Agrarias (ODEPA), Ministerio de Agricultura de Chile, licencia Creative "
     "Commons Atribución; IPC de alimentos: Instituto Nacional de Estadísticas (INE). Este proyecto no es un producto "
     "oficial de ODEPA ni del INE. Lectura de los datos: el precio nacional es un promedio simple de las regiones, sin "
     "ponderar por población o ventas; cada variación semanal compara las mismas regiones en ambas semanas. Los "
     "indicadores describen el histórico; no predicen precios. Los precios se reconstruyen desde la fuente en las "
     "pruebas automáticas."):
        ("Data: Office of Agricultural Studies and Policies (ODEPA), Ministry of Agriculture of Chile, Creative Commons "
         "Attribution license; food CPI: National Statistics Institute (INE). This project is not an official product "
         "of ODEPA or the INE. Reading the data: the national price is a simple average of the regions, not weighted by "
         "population or sales; each weekly change compares the same regions in both weeks. The indicators describe the "
         "history; they do not forecast prices. Prices are rebuilt from the source in the automated tests."),
    # The dbt badge of the footers
    "Linaje dbt: en migración": "dbt lineage: being migrated",
    "Última construcción de dbt:": "Last dbt build:",
    "modelos": "models",
    "pruebas superadas": "tests passed",
    # Documents: folder, actions and printing
    "Los documentos del proyecto, leídos de docs/: cada uno se abre aquí, se imprime como PDF o se lee en GitHub.":
        "The documents of the project, read from docs/: each one opens here, prints as a PDF or reads on GitHub.",
    "Vista de la carpeta": "Folder view",
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
    "Cómo está construido, por vistas: contexto, contenedores, datos, despliegue y seguridad.":
        "How it is built, view by view: context, containers, data, deployment and security.",
    "Las decisiones de arquitectura que más pesan: contexto, decisión, opciones y consecuencias.":
        "The architecture decisions that weigh most: context, decision, options and consequences.",
    "Cómo se buscan, se corrigen y se prueban en cada push los puntos débiles.":
        "How weak points are found, fixed and tested on every push.",
    "Capacidad actual, qué cede primero y cuándo se justificaría una nube.":
        "Current capacity, what gives way first and when a cloud would be justified.",
    "Cómo operar el proyecto y resolver sus fallas.": "How to operate the project and solve its failures.",
    "Las decisiones que cambian la arquitectura, los datos, la seguridad o la operación, por tema.":
        "The decisions that change the architecture, the data, the security or the operations, by theme.",
    "Cada tabla y cada columna de la base servida.": "Each table and each column of the served database.",
    "Qué se prueba, cómo y con qué criterios se acepta un cambio.":
        "What is tested, how, and with which criteria a change is accepted.",
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
