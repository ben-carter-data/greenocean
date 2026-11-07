"""The project's documents (D-541): the folder «Documentos del proyecto» with its five main documents and four
annexes, each document's page with its diagrams, links and print button, the folder «Análisis de la fuente de datos»
with its notebooks, and the Autor's links page.
"""

import functools
import html
import re
from urllib.parse import parse_qs, urlencode

import streamlit as st

from bi import (
    architecture,
    buttons,
    charts,
    doc_diagrams,
    documents_folder,
    github_page,
    i18n,
    project,
    source_study,
    zoom,
)
from bi.app_frame import (
    build_page_address,
    build_repository_link_html,
    find_menu_page,
    get_mode,
    is_author,
    is_dark_theme,
    show_compact_page_header,
    show_page_bar,
)
from bi.constants import (
    FOLDER_ANNEXES,
    FOLDER_DOCUMENTS,
    NO_ACCESS,
    PAGE_ADR,
    PAGE_CLOSURE,
    PAGE_DECISION_INDEX,
    PAGE_FOLDER,
    PAGE_GLOSSARY,
    PAGE_MANUAL,
    PAGE_PRD,
    PAGE_QUALITY_PLAN,
    PAGE_SAD,
    PAGE_SOURCE_STUDY,
    PAGE_TEST_PLAN,
    SIDEBAR_LABELS,
    THEME_PARAMETER,
)
from bi.i18n import tr

# region Constants
PROJECT_DOCUMENTS = {
    PAGE_PRD: ("PRD.md", "Qué resuelve el producto, para quién y con qué requisitos."),
    PAGE_CLOSURE: ("ACTA_DE_CIERRE.md", "Cómo empezó el proyecto, qué se aprendió y a quién sirve."),
    PAGE_SAD: ("SAD.md", "Cómo está construido, cómo corre cada semana, dónde viven sus datos y cómo puede crecer."),
    PAGE_ADR: ("ADR.md", "Las decisiones de arquitectura que más pesan: contexto, decisión, opciones y consecuencias."),
    PAGE_MANUAL: ("MANUAL.md", "Cómo operar el proyecto y resolver sus fallas."),
    PAGE_DECISION_INDEX: (
        "INDICE_DECISIONES.md",
        "Las decisiones que cambian la arquitectura, los datos, la seguridad o la operación, por tema.",
    ),
    PAGE_TEST_PLAN: (
        "PLAN_PRUEBAS.md",
        "Qué se prueba, quién participa en la seguridad y con qué criterios se acepta un cambio.",
    ),
    PAGE_GLOSSARY: ("GLOSARIO.md", "Las siglas y los términos del panel y de los documentos."),
    PAGE_QUALITY_PLAN: (
        "PLAN_DE_CALIDAD.md",
        "Qué calidad cuida el proyecto, cómo la mide, quién decide y qué pasa cuando algo falla.",
    ),
}


FOLDER_VIEW_KEY = "folder_view"


DOCUMENT_DIAGRAM = re.compile(r"^\[\[diagrama:(\w+)\]\]\s*$", re.MULTILINE)


# D-247: a document points to the page of the panel where a view lives, instead of copying it: [[vista:Modelo de datos]].
DOCUMENT_VIEW = re.compile(r"\[\[vista:([^\]]+)\]\]")


DOCUMENT_LINK = re.compile(r"\]\((?:\.\./[a-z]+/)?([A-Z_]+\.md)(#[^)]*)?\)")  # D-381: «../negocio/PRD.md» too


HEADING = re.compile(r"^(#{2,4}) (.+)$", re.MULTILINE)


REPOSITORY_LINK = re.compile(r"\[([^\]]+)\]\(https://github\.com/[^)]*\)")


CODE_SPAN = re.compile(r"`([^`\n]+)`")


# D-248: the downloadable document is the page itself, printed by the browser: the same text, diagrams and order.
# Only the document pages carry this stylesheet; it hides the menu and the navigation and lets the page run on.
PRINT_DOCUMENT_CSS = """<style>
@media print {
  /* D-358: every sheet says its number, and the cover has a sheet of its own. */
  @page { size: A4; margin: 12mm 12mm 16mm;
    @bottom-center { content: "__PAGE__ " counter(page) " __OF__ " counter(pages); font: 9pt -apple-system, "Segoe UI", sans-serif; color: #5f6b7c; } }
  .doc-cover { break-after: page; }
  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
  [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
  .st-key-app_header, .st-key-doc_actions, .st-key-compact_footer, .st-key-route_footer, .doc-path,
  [data-testid="stElementContainer"]:has(.page-lineage), [data-testid="stCaptionContainer"],
  hr { display: none !important; }
  html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
    height: auto !important; min-height: 0 !important; overflow: visible !important; position: static !important; }
  /* The page is laid out at its screen width and scaled to the sheet, so the paper shows the same lines as the screen. */
  [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: none !important; zoom: 0.86; }
  .st-key-project_document { max-width: none !important; margin: 0 !important; box-shadow: none !important;
    padding: 40px 50px 44px !important; }
  [data-testid="stIFrame"], figure, tr { break-inside: avoid; }
  thead { display: table-header-group; }
  h2, h3 { break-after: avoid; }
}
</style>"""


# D-280: the PDF is always a white sheet. From a dark theme the button reopens the page in the light theme with
# «imprimir=<theme>», which prints it and comes back to the reader's theme.
PRINT_PARAMETER = "imprimir"


PRINT_THEME = charts.MODE_CORPORATE


PRINT_BUTTON_HTML = (
    buttons.build_button_html("Imprimir o guardar como PDF", icon="print", variant="primary", extra="doc-print")
    + r"""
<script>
document.querySelectorAll(".doc-print").forEach((button) => { button.onclick = () => {
  const light = "__LIGHT__";
  if (!light) { window.print(); return; }
  const url = new URL(window.location.href);
  url.searchParams.set("imprimir", url.searchParams.get("tema") || "");
  url.searchParams.set("tema", light);
  if (window.__goRemember) window.__goRemember();  // D-357: the app reloads, the visit keeps its view
  window.location.assign(url.toString());
}; });
</script>"""
)


AUTO_PRINT_SCRIPT = r"""<script>
(() => {
  if (window.__documentPrinted) return;
  window.__documentPrinted = true;
  window.addEventListener("afterprint", () => {
    const url = new URL(window.location.href);
    url.searchParams.set("tema", url.searchParams.get("imprimir"));
    url.searchParams.delete("imprimir");
    if (window.__goRemember) window.__goRemember();
    window.location.replace(url.toString());
  }, { once: true });
  // D-427: print only the document: wait until «Elige tu vista» is gone (the view comes back a moment after the load).
  let tries = 0;
  const ready = () => {
    if (!document.querySelector(".profile-ask")) { window.print(); return; }
    tries += 1;
    if (tries > 40) return;  // after 20 s with the window still open, nothing is printed (no less-than sign: D-280)
    setTimeout(ready, 500);
  };
  setTimeout(ready, 3000);
})();
</script>"""
# endregion


# region «Documentos del proyecto»
def build_print_address(page):
    """The address that opens a document and prints it (D-248), on a white sheet from any theme (D-280)."""
    path, _, query = build_page_address(page).partition("?")
    parameters = {key: values[0] for key, values in parse_qs(query).items()}
    reader = get_mode()
    parameters.update({THEME_PARAMETER: PRINT_THEME if is_dark_theme(reader) else reader, PRINT_PARAMETER: reader})
    return f"{path}?{urlencode(parameters)}"


def read_folder_files():
    """Every main document of the folder as the folder shows it, read from its file; the annexes are left out (D-536)."""
    files = []
    for page, family in FOLDER_DOCUMENTS:
        if page in FOLDER_ANNEXES:
            continue
        path = i18n.document_path(PROJECT_DOCUMENTS[page][0])
        files.append(
            documents_folder.describe(path.read_text(encoding="utf-8"))
            | {
                "page": page,
                "family": family,
                "open": build_page_address(page),
                "pdf": build_print_address(page),
                # D-500: only the Autor gets the link to the file in the repository
                "github": project.build_github_url(path.relative_to(project.PROJECT_DIR).as_posix())
                if is_author()
                else "",
            }
        )
    return files


def show_documents_folder(mode):
    """«Documentos del proyecto» (D-282, D-533): the folder of docs/, as files in a grid or a list."""
    files = read_folder_files()
    # D-288: the folder opens as a list, like a file explorer in detail view.
    st.session_state.setdefault(FOLDER_VIEW_KEY, documents_folder.VIEW_LIST)
    show_page_bar(
        PAGE_FOLDER,
        PAGE_FOLDER,
        "Los documentos del proyecto, leídos de docs/: cada uno se abre aquí, se imprime como PDF o se lee en GitHub.",
        side=lambda: st.segmented_control(
            tr("Vista de la carpeta"),
            [documents_folder.VIEW_GRID, documents_folder.VIEW_LIST],
            format_func=tr,
            key=FOLDER_VIEW_KEY,
            label_visibility="collapsed",
            width="content",
        ),
    )
    st.markdown(documents_folder.build_css(charts.get_palette(mode)), unsafe_allow_html=True)
    view = st.session_state.get(FOLDER_VIEW_KEY) or documents_folder.VIEW_LIST
    st.markdown(documents_folder.build_folder_html(files, view), unsafe_allow_html=True)


def build_folder_path_html(title):
    """«Documentos / PRD»: the thin path of a document, back to its folder (D-282)."""
    return (
        f'<nav class="doc-path" aria-label="{tr("Ruta")}"><a href="{html.escape(build_page_address(PAGE_FOLDER), quote=True)}" '
        f'target="_self">{tr(PAGE_FOLDER)}</a><i>/</i><span>{html.escape(tr(SIDEBAR_LABELS.get(title, title)))}</span></nav>'
    )


# endregion


# region A document's page
def heading_anchor(text):
    """The anchor GitHub gives a heading, so an index link works the same in GitHub and in the panel (D-279)."""
    return re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")


def build_document_address(pages, match):
    """The address a link to a project document points to: its page in the panel, or its file on GitHub."""
    filename, anchor = match.group(1), match.group(2) or ""
    address = (
        build_page_address(pages[filename])
        if filename in pages
        else project.build_github_url(
            f"docs/{i18n.DOCUMENT_FOLDERS.get(filename, '')}/{filename}".replace("docs//", "docs/")
        )
    )
    return f"]({address}{anchor})"


def link_document_views(text):
    """Each [[vista:…]] of a document as a link to its page in the panel; each link to another document of docs/
    to that document's page, or to GitHub when it has none; each heading with the anchor its index points to."""
    text = DOCUMENT_VIEW.sub(
        lambda match: (
            f"[{match.group(1)}]({build_page_address(find_menu_page(match.group(1)))})"
            if find_menu_page(match.group(1))
            else match.group(1)
        ),
        text,
    )
    pages = {filename: title for title, (filename, _) in PROJECT_DOCUMENTS.items()}

    text = DOCUMENT_LINK.sub(functools.partial(build_document_address, pages), text)
    if not is_author():  # D-500: for anyone else, a link to GitHub reads as plain text, in every document
        text = REPOSITORY_LINK.sub(r"\1", text)
    return HEADING.sub(
        lambda match: f'<a id="{heading_anchor(match.group(2))}"></a>\n\n{match.group(1)} {match.group(2)}', text
    )


def show_document_diagram(name, mode):
    """One marker of a document: the document views and the security map in their own frame
    (hover tips and gradients need it, D-205), the live diagrams inline. D-455: the interest map is drawn inline, with the
    panel's icon font."""
    if name in doc_diagrams.INLINE:
        st.markdown(doc_diagrams.INLINE[name](mode), unsafe_allow_html=True)
        return
    st.iframe(doc_diagrams.DOC_DIAGRAMS[name](mode), height=doc_diagrams.HEIGHTS[name])


def build_print_button_html(mode):
    """The print button; from a dark theme it prints the light version of the page (D-280)."""
    return PRINT_BUTTON_HTML.replace("Imprimir o guardar como PDF", tr("Imprimir o guardar como PDF")).replace(
        "__LIGHT__", PRINT_THEME if is_dark_theme(mode) else ""
    )


def show_document_actions(mode, source_label, source_url):
    """The document's source in GitHub and the button that prints the page itself (D-248)."""
    with st.container(
        key="doc_actions", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
    ):
        st.markdown(
            '<div class="doc-source">' + build_repository_link_html(source_label, source_url, "secondary") + '</div>',
            unsafe_allow_html=True,
        )
        st.html(build_print_button_html(mode), unsafe_allow_javascript=True)
    st.markdown(
        PRINT_DOCUMENT_CSS.replace("__PAGE__", tr("Página")).replace("__OF__", tr("de")), unsafe_allow_html=True
    )
    if st.query_params.get(PRINT_PARAMETER) in charts.THEMES:
        st.html(AUTO_PRINT_SCRIPT, unsafe_allow_javascript=True)


def soften_code_breaks(text):
    """D-297: a name in code may break only after «_», «/», «.» or «::», never in the middle of a word: a zero-width
    space after each of them (in the page only; the file keeps its text)."""
    return CODE_SPAN.sub(lambda match: "`" + re.sub(r"(::|[_/.](?=\w))", "\\1\u200b", match.group(1)) + "`", text)


def show_project_document(mode, title):
    """A document of docs/ as a page: the same text as in GitHub, its diagrams drawn
    from the live project, no code."""
    filename, lead = PROJECT_DOCUMENTS[title]
    # D-283: the document in the language of the visit, from docs/ or docs/en/.
    path = i18n.document_path(filename)
    text = path.read_text(encoding="utf-8")
    source = path.relative_to(project.PROJECT_DIR).as_posix()
    st.markdown(build_folder_path_html(title), unsafe_allow_html=True)
    show_compact_page_header(title, lead)
    show_document_actions(mode, f"{source} {tr('en GitHub')}", project.build_github_url(source))
    # D-288: the document opens with its cover, read from its header table; the title and the table do not repeat.
    header = documents_folder.read_header(text)
    related = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: (
            f'<a href="{html.escape(match.group(2), quote=True)}" target="_self">{html.escape(match.group(1))}</a>'
        ),
        link_document_views(documents_folder.field(header, "related")).split("<a id=", 1)[0],
    )
    cover = documents_folder.build_cover_html(text, related)
    text = soften_code_breaks(documents_folder.strip_header_table(re.sub(r"\A# .*\n", "", text)))
    st.markdown(documents_folder.build_cover_css(charts.get_palette(mode)), unsafe_allow_html=True)
    with st.container(key="project_document"):
        st.markdown(cover, unsafe_allow_html=True)
        position = 0
        for marker in DOCUMENT_DIAGRAM.finditer(text):
            st.markdown(link_document_views(text[position : marker.start()]), unsafe_allow_html=True)
            show_document_diagram(marker.group(1), mode)
            position = marker.end()
        st.markdown(link_document_views(text[position:]), unsafe_allow_html=True)
    st.html(zoom.ZOOM_SCRIPT, unsafe_allow_javascript=True)
    st.html(zoom.TIP_SCRIPT, unsafe_allow_javascript=True)


# endregion


# region «Análisis de la fuente de datos»
def show_source_study(mode):
    """«Análisis de la fuente de datos» (D-533): the notebook that studies ODEPA's raw wholesale file. Only the one in the
    language of the visit is listed (D-535); it opens here, read only, with the outputs its file keeps, and downloads."""
    files = source_study.read_files()
    show_page_bar(
        PAGE_SOURCE_STUDY,
        PAGE_SOURCE_STUDY,
        "El estudio del archivo mayorista de ODEPA: cada anomalía encontrada, con su decisión y su solución.",
    )
    palette = charts.get_palette(mode)
    st.markdown(documents_folder.build_css(palette) + source_study.build_css(palette), unsafe_allow_html=True)
    language = i18n.get_language()
    opened = next(
        (
            file
            for file in files
            if file["language"] == language and st.query_params.get(source_study.NOTEBOOK_PARAMETER) == file["language"]
        ),
        None,
    )
    if opened:
        show_notebook(opened)
        return
    st.markdown(source_study.build_head_html(language), unsafe_allow_html=True)
    # Only the notebook of the visit's language is listed (D-443, D-535); the head line names the other one.
    for file in (file for file in files if file["language"] == language):
        address = build_page_address(PAGE_SOURCE_STUDY) + f"&{source_study.NOTEBOOK_PARAMETER}={file['language']}"
        with st.container(key=f"notebook_row_{file['language']}", horizontal=True, vertical_alignment="center"):
            st.markdown(source_study.build_file_html(file, address), unsafe_allow_html=True, width="stretch")
            show_notebook_download(file)


def show_notebook_download(file):
    st.download_button(
        tr("Descargar"),
        file["path"].read_bytes(),
        file_name=file["file"],
        mime="application/x-ipynb+json",
        key=f"notebook_download_{file['language']}",
        icon=":material/download:",
        width="content",
    )


def show_notebook(file):
    """One notebook, read only: its texts, its code and the outputs its file keeps; the panel never runs it."""
    with st.container(key="notebook_path", horizontal=True, vertical_alignment="center"):
        st.markdown(
            source_study.build_path_html(build_page_address(PAGE_SOURCE_STUDY), tr(PAGE_SOURCE_STUDY), file["file"]),
            unsafe_allow_html=True,
            width="stretch",
        )
        show_notebook_download(file)
    # The notebook is already in the visit's language: its texts and outputs are drawn verbatim, never translated.
    for cell in source_study.read_notebook(file["path"])["cells"]:
        source = source_study.text_of(cell["source"])
        if cell["cell_type"] == "markdown":
            st.markdown(i18n.Verbatim(source))
            continue
        st.code(source, language="python")
        outputs = source_study.build_output_html(cell.get("outputs", []))
        if outputs:
            st.html(i18n.Verbatim(outputs))


# endregion


# region The Autor's links
def build_github_icon_svg(size=22):
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="currentColor" '
        f'aria-hidden="true">{architecture.brand_icons.logo_body("github")}</svg>'
    )


def show_links_page(mode):
    """The repository is the single destination for commits, executions and full
    documents (D-106): one hero with the repository, then its three uses —
    automatización, trazabilidad, documentación — each item opening GitHub in a new
    tab (D-116) with its own copy button. ODEPA and the INE live in «Fuentes» (D-118). D-500: only for the Autor."""
    if not is_author():
        st.info(tr(NO_ACCESS), icon=":material/lock:")
        return
    # Our own trusted markup, in its own frame: st.html sanitises the SVG gradients,
    # filters and buttons the page is made of.
    st.iframe(
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"></head>'
        '<body style="margin:0;background:transparent">'
        + github_page.build_github_page_html(mode)
        + github_page.GITHUB_PAGE_SCRIPT
        + '</body></html>',
        height="content",
    )


# endregion
