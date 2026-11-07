"""The «Documentos del proyecto» folder (D-282, D-533): every document of docs/ as a file, in a grid or a list.

Each file shows its standard name, one line of content, its version and date (read from the header table of the file
itself), its reading time and three actions: Abrir, PDF (the printed page, D-248) and GitHub. On hover, a preview with
the document's index. The page draws itself as HTML; its links are the component of bi/buttons.py.
"""

import html
import math
import re

from bi import buttons, i18n, static_files
from bi.i18n import tr

# region Constants
VIEW_GRID, VIEW_LIST = "Cuadrícula", "Lista"
WORDS_PER_MINUTE = 200
PREVIEW_ENTRIES = 9
# D-381: the folder of each document gives the color of its file and the icon of its section. The four folders are
# docs/negocio, docs/arquitectura, docs/calidad and docs/operacion; each icon is a Material Symbols name.
FAMILY_COLORS = {
    "negocio": "#3b82f6",
    "arquitectura": "#8b5cf6",
    "calidad": "#10b981",
    "operacion": "#f59e0b",
}
FAMILY_ICONS = {
    "negocio": "business_center",
    "arquitectura": "architecture",
    "calidad": "verified_user",
    "operacion": "build",
}
FAMILY_TITLES = {
    "negocio": "Negocio",
    "arquitectura": "Arquitectura",
    "calidad": "Calidad",
    "operacion": "Operación",
}
HEADER_ROW = re.compile(r"^\| ([^|]+?) \| (.+?) \|$", re.MULTILINE)
INDEX_HEADINGS = tuple(f"## {fields['index']}" for fields in i18n.DOCUMENT_FIELDS.values())
# endregion


# region Reading each document
def esc(value):
    return html.escape(str(value), quote=True)


def read_header(text):
    """{field: value} of the header table, the table above the first «## » heading."""
    return {
        field: value
        for field, value in HEADER_ROW.findall(text.split("\n## ", 1)[0])
        if field not in ("Campo", "Field")
    }


def read_title(text):
    return text.splitlines()[0].lstrip("# ").strip()


def read_index(text):
    """The entries of the document's «Índice» (or «Contents»), without their numbers or links."""
    heading = next((heading for heading in INDEX_HEADINGS if heading in text), None)
    if not heading:
        return []
    body = text.split(heading, 1)[1].split("\n## ", 1)[0]
    # A numbered list, or a table whose first column links to each record (the ADR).
    return re.findall(r"^\d+\. \[([^\]]+)\]", body, re.MULTILINE) or [
        f"{code} · {title.strip()}"
        for code, title in re.findall(r"^\| \[([^\]]+)\]\([^)]*\) \| ([^|]+) \|", body, re.MULTILINE)
    ]


def reading_minutes(text):
    return max(1, math.ceil(len(text.split()) / WORDS_PER_MINUTE))


def describe(text):
    """What the folder shows of one document, all of it read from the file."""
    header = read_header(text)
    field = {
        name: next((header[fields[name]] for fields in i18n.DOCUMENT_FIELDS.values() if fields[name] in header), "")
        for name in ("purpose", "version", "date")
    }
    return {
        "name": read_title(text),
        "purpose": field["purpose"],
        "version": field["version"],
        "date": field["date"],
        "minutes": reading_minutes(text),
        "index": read_index(text),
    }


def sortable(day):
    """dd-mm-yyyy (Spanish) or yyyy-mm-dd (English) as yyyy-mm-dd."""
    parts = day.split("-")
    return "-".join(parts[::-1]) if len(parts[0]) == 2 else day


def latest_date(files):
    """The most recent date of the folder, as the files write it."""
    return max((file["date"] for file in files), key=sortable, default="")


def build_file_glyph(color):
    return f'<span class="df-glyph" style="--df-color:{color}"><span class="df-fold"></span><b>MD</b></span>'


def build_preview(file):
    entries = "".join(f"<li>{esc(entry)}</li>" for entry in file["index"][:PREVIEW_ENTRIES])
    more = len(file["index"]) - PREVIEW_ENTRIES
    tail = f'<p class="df-more">{tr("y {} más").format(more)}</p>' if more > 0 else ""
    return f'<span class="df-preview" aria-hidden="true"><em>{tr("Índice")}</em><ol>{entries}</ol>{tail}</span>'


def build_actions(file):
    return (
        '<span class="df-actions">'
        + buttons.build_link_html(tr("Abrir"), file["open"], variant="primary", size="compact")
        + buttons.build_link_html(
            "PDF",
            file["pdf"],
            icon="print",
            size="compact",
            note=tr("Abre el documento y lo imprime o guarda como PDF"),
        )
        + (  # D-500: only the Autor gets this address
            buttons.build_link_html(
                "GitHub",
                file["github"],
                icon="github",
                variant="text",
                size="compact",
                external=True,
                note=tr("El archivo en GitHub"),
            )
            if file["github"]
            else ""
        )
        + "</span>"
    )


def build_meta(file):
    return (
        f'<span class="df-meta"><span>v{esc(file["version"])}</span><span>{esc(file["date"])}</span>'
        f'<span>{file["minutes"]} min</span></span>'
    )


def build_file(file):
    return (
        f'<div class="df-file" data-family="{esc(file["family"])}">'
        f'<a class="df-body" href="{esc(file["open"])}" target="_self" title="{file["minutes"]} {tr("min de lectura")}">'
        # D-537: the grid has no groups, so each card names its folder of docs/ (the list shows it in its group head)
        f'<span class="df-family" style="--df-color:{FAMILY_COLORS[file["family"]]}">'
        f'{esc(tr(FAMILY_TITLES[file["family"]]))}</span>'
        f'<span class="df-top">{build_file_glyph(FAMILY_COLORS[file["family"]])}<b class="df-name">{esc(file["name"])}</b></span>'
        f'<span class="df-purpose">{esc(file["purpose"])}</span>{build_preview(file)}</a>'
        f'{build_meta(file)}{build_actions(file)}</div>'
    )


def build_group(family, files, kind):
    """One folder of docs/: its icon and name, how many documents, then its files (D-381)."""
    color = FAMILY_COLORS[family]
    return (
        f'<section class="df-group" data-family="{family}"><div class="df-group-head" role="heading" aria-level="3" style="--df-color:{color}">'
        f'<span class="df-group-icon" aria-hidden="true">{FAMILY_ICONS[family]}</span>'
        f'<span class="df-group-name">{esc(tr(FAMILY_TITLES[family]))}</span>'
        f'<span class="df-group-path">docs/{family}</span><span class="df-group-count">{len(files)}</span></div>'
        f'<div class="{kind}">' + "".join(build_file(file) for file in files) + "</div></section>"
    )


def build_folder_html(files, view):
    """The folder: its path, how many documents and the last change, then its files. The list groups them by their
    four folders of docs/; the grid lays them on one shelf that fills the width, like a library (D-537)."""
    head = (
        f'<div class="df-head"><span class="df-path">GreenOcean <i>/</i> <b>docs</b></span>'
        f'<span class="df-count">{len(files)} {tr("documentos · último cambio")} {esc(latest_date(files))}</span></div>'
    )
    if view == VIEW_GRID:
        return f'<div class="df-folder">{head}<div class="df-grid">{"".join(build_file(file) for file in files)}</div></div>'
    groups = "".join(
        build_group(family, [file for file in files if file["family"] == family], "df-list")
        for family in FAMILY_COLORS
        if any(file["family"] == family for file in files)
    )
    return f'<div class="df-folder">{head}{groups}</div>'


def build_css(palette):
    ink, text, muted, card, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    return static_files.style(
        "documents_folder.css",
        {
            'var(--go-muted)': muted,
            'var(--go-ink)': ink,
            'var(--go-border)': border,
            'var(--go-card)': card,
            'var(--go-accent)': accent,
            'var(--go-text)': text,
        },
    )


# endregion


# region Cover (D-288)
# The first thing a document shows, in the panel and on the first page of its PDF: the project, the kind of document,
# its title and purpose, and its version, date, status, owner and audience, read from its header table.
COVER_FIELDS = ("version", "date", "status", "owner")


def strip_header_table(text):
    """The document without its header table (the cover shows it); the table stays in the file for GitHub."""
    head, separator, rest = text.partition("\n## ")
    head = "\n".join(line for line in head.splitlines() if not line.startswith("|"))
    return head + separator + rest


def field(header, name):
    return next((header[fields[name]] for fields in i18n.DOCUMENT_FIELDS.values() if fields[name] in header), "")


def build_cover_html(text, related_html):
    """The cover of a document: kind, title and purpose, then its version, date, status, owner and audience."""
    header = read_header(text)
    meta = "".join(
        f'<div><dt>{esc(i18n.document_field(name))}</dt><dd>{esc(field(header, name))}</dd></div>'
        for name in COVER_FIELDS
        if field(header, name)
    )
    related = (
        f'<p class="doc-cover-related"><span>{esc(i18n.document_field("related"))}</span>{related_html}</p>'
        if related_html
        else ""
    )
    audience = (
        f'<p class="doc-cover-related"><span>{esc(i18n.document_field("audience"))}</span>'
        f'{esc(field(header, "audience"))}</p>'
        if field(header, "audience")
        else ""
    )
    kind = field(header, "type")
    # The kind of document, unless the title already says it.
    pill = f'<p class="doc-cover-kind">{esc(kind)}</p>' if kind and kind != read_title(text) else ""
    return (
        f'<header class="doc-cover"><p class="doc-cover-mark">GreenOcean <i>·</i> {esc(tr("Documentación"))}</p>{pill}'
        f'<h1 class="doc-cover-title">{esc(read_title(text))}</h1>'
        f'<p class="doc-cover-purpose">{esc(field(header, "purpose"))}</p>'
        f'<dl class="doc-cover-meta">{meta}</dl>{audience}{related}</header>'
    )


def build_cover_css(palette):
    ink, text, muted, card, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    return static_files.style(
        "document_cover.css",
        {
            'var(--go-border)': border,
            'var(--go-accent)': accent,
            'var(--go-card)': card,
            'var(--go-muted)': muted,
            'var(--go-ink)': ink,
            'var(--go-text)': text,
        },
    )


# endregion
