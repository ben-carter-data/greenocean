"""The «Documentos» folder (D-282): every document of docs/ as a file, in a grid or a list.

Each file shows its standard name, one line of content, its version and date (read from the header table of the file
itself), its reading time and three actions: Abrir, PDF (the printed page, D-248) and GitHub. On hover, a preview with
the document's index. The page draws itself as HTML; its links are the component of bi/buttons.py.
"""
import html
import math
import re

from bi import buttons

VIEW_GRID, VIEW_LIST = "Cuadrícula", "Lista"
WORDS_PER_MINUTE = 200
PREVIEW_ENTRIES = 9
# The family of each document gives the color of its file: product, architecture, quality and security, operation and
# reference.
FAMILY_COLORS = {"producto": "#3b82f6", "arquitectura": "#8b5cf6", "calidad": "#10b981", "operacion": "#f59e0b",
                 "referencia": "#64748b"}
HEADER_ROW = re.compile(r"^\| ([^|]+?) \| (.+?) \|$", re.MULTILINE)


def esc(value):
    return html.escape(str(value), quote=True)


def read_header(text):
    """{field: value} of the header table, the table above the first «## » heading."""
    return {field: value for field, value in HEADER_ROW.findall(text.split("\n## ", 1)[0]) if field != "Campo"}


def read_title(text):
    return text.splitlines()[0].lstrip("# ").strip()


def read_index(text):
    """The entries of the document's «Índice», without their numbers or links."""
    if "## Índice" not in text:
        return []
    body = text.split("## Índice", 1)[1].split("\n## ", 1)[0]
    # A numbered list, or a table whose first column links to each record (the ADR).
    return (re.findall(r"^\d+\. \[([^\]]+)\]", body, re.MULTILINE)
            or [f"{code} · {title.strip()}" for code, title in
                re.findall(r"^\| \[([^\]]+)\]\([^)]*\) \| ([^|]+) \|", body, re.MULTILINE)])


def reading_minutes(text):
    return max(1, math.ceil(len(text.split()) / WORDS_PER_MINUTE))


def describe(text):
    """What the folder shows of one document, all of it read from the file."""
    header = read_header(text)
    return {"name": read_title(text), "purpose": header.get("Propósito", ""), "version": header.get("Versión", ""),
            "date": header.get("Fecha", ""), "minutes": reading_minutes(text), "index": read_index(text)}


def latest_date(files):
    """The most recent «Fecha» of the folder, dd-mm-yyyy."""
    return max((file["date"] for file in files), key=lambda day: day.split("-")[::-1], default="")


def build_file_glyph(color):
    return f'<span class="df-glyph" style="--df-color:{color}"><span class="df-fold"></span><b>MD</b></span>'


def build_preview(file):
    entries = "".join(f"<li>{esc(entry)}</li>" for entry in file["index"][:PREVIEW_ENTRIES])
    more = len(file["index"]) - PREVIEW_ENTRIES
    tail = f'<p class="df-more">y {more} más</p>' if more > 0 else ""
    return f'<span class="df-preview" aria-hidden="true"><em>Índice</em><ol>{entries}</ol>{tail}</span>'


def build_actions(file):
    return ('<span class="df-actions">'
            + buttons.build_link_html("Abrir", file["open"], variant="primary", size="compact")
            + buttons.build_link_html("PDF", file["pdf"], icon="print", size="compact",
                                      note="Abre el documento y lo imprime o guarda como PDF")
            + buttons.build_link_html("GitHub", file["github"], icon="github", variant="text", size="compact",
                                      external=True, note="El archivo en GitHub")
            + "</span>")


def build_meta(file):
    return (f'<span class="df-meta"><span>v{esc(file["version"])}</span><span>{esc(file["date"])}</span>'
            f'<span>{file["minutes"]} min</span></span>')


def build_file(file):
    return (f'<div class="df-file" data-family="{esc(file["family"])}">'
            f'<a class="df-body" href="{esc(file["open"])}" target="_self" title="{file["minutes"]} min de lectura">'
            f'<span class="df-top">{build_file_glyph(FAMILY_COLORS[file["family"]])}<b class="df-name">{esc(file["name"])}</b></span>'
            f'<span class="df-purpose">{esc(file["purpose"])}</span>{build_preview(file)}</a>'
            f'{build_meta(file)}{build_actions(file)}</div>')


def build_folder_html(files, view):
    """The folder: its path, how many documents and the last change, then the files in the chosen view."""
    kind = "df-grid" if view == VIEW_GRID else "df-list"
    head = (f'<div class="df-head"><span class="df-path">GreenOcean <i>/</i> <b>docs</b></span>'
            f'<span class="df-count">{len(files)} documentos · último cambio {esc(latest_date(files))}</span></div>')
    return f'<div class="df-folder">{head}<div class="{kind}">' + "".join(build_file(file) for file in files) + "</div></div>"


def build_css(palette):
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"],
                                              palette["card"], palette["card_border"], palette["accent"])
    return f"""<style>
.df-folder {{ display:flex; flex-direction:column; gap:14px; }}
.df-head {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
.df-path {{ font-size:15px; color:{muted}; }} .df-path b {{ color:{ink}; font-weight:500; }} .df-path i {{ font-style:normal; margin:0 4px; }}
.df-count {{ font-size:12.5px; color:{muted}; }}
.df-grid {{ display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:12px; }}
.df-file {{ position:relative; display:flex; flex-direction:column; gap:8px; padding:12px; border:1px solid {border};
  border-radius:14px; background:color-mix(in srgb, {card} 70%, transparent); transition:border-color .18s ease, box-shadow .18s ease; }}
.df-file:hover {{ z-index:5; border-color:color-mix(in srgb, {accent} 60%, {border}); box-shadow:0 10px 26px -18px {accent}; }}
.df-body {{ position:relative; display:flex; flex-direction:column; gap:7px; color:inherit !important; text-decoration:none !important; }}
.df-top {{ display:flex; align-items:center; gap:10px; min-height:49px; }}
.df-glyph {{ position:relative; flex:none; display:inline-flex; align-items:flex-end; justify-content:center; width:28px; height:34px;
  padding-bottom:4px; box-sizing:border-box; border:1.5px solid var(--df-color); border-radius:5px 12px 5px 5px;
  background:color-mix(in srgb, var(--df-color) 10%, transparent); }}
.df-glyph b {{ font-size:8.5px; font-weight:600; letter-spacing:.06em; color:var(--df-color); }}
.df-fold {{ position:absolute; top:-1.5px; right:-1.5px; width:9px; height:9px; border-left:1.5px solid var(--df-color);
  border-bottom:1.5px solid var(--df-color); border-radius:0 0 0 4px; background:{card}; }}
.df-name {{ font-size:12.5px; font-weight:500; line-height:1.3; color:{ink}; display:-webkit-box; -webkit-line-clamp:3;
  -webkit-box-orient:vertical; overflow:hidden; }}
.df-purpose {{ font-size:12px; line-height:1.4; min-height:2.8em; color:{text}; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
.df-meta {{ display:flex; flex-wrap:wrap; gap:4px 10px; font-size:11.5px; color:{muted}; font-variant-numeric:tabular-nums; }}
.df-actions {{ display:flex; flex-wrap:wrap; gap:4px; align-items:center; }}
.df-grid .df-actions .go-btn--secondary .go-icon {{ display:none; }}
.df-grid .df-actions .go-btn--text span:not(.go-icon) {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }}
.df-preview {{ position:absolute; left:calc(100% + 18px); top:-12px; width:250px; z-index:6; display:flex; flex-direction:column;
  gap:4px; padding:12px 14px; border-radius:12px; background:{card}; border:1px solid {border};
  box-shadow:0 18px 40px -18px rgba(0,0,0,.45); opacity:0; visibility:hidden; transition:opacity .16s ease; pointer-events:none; }}
.df-grid .df-file:nth-child(5n) .df-preview, .df-grid .df-file:nth-child(5n-1) .df-preview {{ left:auto; right:calc(100% + 18px); }}
.df-preview em {{ font-style:normal; font-size:10.5px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{muted}; }}
.df-preview ol {{ margin:0; padding-left:18px; font-size:12px; line-height:1.45; color:{ink}; }}
.df-more {{ margin:0; font-size:11.5px; color:{muted}; }}
.df-body:hover .df-preview, .df-body:focus-visible .df-preview {{ opacity:1; visibility:visible; }}
.df-list {{ display:flex; flex-direction:column; gap:5px; }}
.df-list .df-file {{ flex-direction:row; align-items:center; gap:18px; padding:4px 14px; }}
.df-list .df-body {{ flex-direction:row; align-items:center; gap:14px; flex:1; min-width:0; }}
.df-list .df-top {{ flex:none; width:330px; min-height:0; }}
.df-list .df-glyph {{ width:22px; height:27px; padding-bottom:2px; }}
.df-list .df-glyph b {{ font-size:7px; }}
.df-list .df-purpose {{ -webkit-line-clamp:1; min-height:0; flex:1; }}
.df-list .df-meta {{ flex:none; width:170px; }}
.df-list .df-preview {{ left:32px; top:calc(100% + 4px); }}
@media (max-width:1100px) {{ .df-grid {{ grid-template-columns:repeat(3, minmax(0, 1fr)); }}
  .df-grid .df-file:nth-child(n) .df-preview {{ left:0; right:auto; top:calc(100% + 6px); }} }}
@media (max-width:700px) {{ .df-grid {{ grid-template-columns:repeat(2, minmax(0, 1fr)); }} }}
@media (max-width:900px) {{ .df-list .df-file {{ flex-wrap:wrap; }} .df-list .df-meta {{ width:auto; }} }}
@media (prefers-reduced-motion:reduce) {{ .df-file, .df-preview {{ transition:none; }} }}
</style>"""
