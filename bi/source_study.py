"""«Análisis de la fuente de datos» (D-533): the study of ODEPA's raw wholesale file, as two Jupyter notebooks.

The same study lives twice in notebooks/, one notebook per language. The folder lists only the one in the language of
the visit (D-535), with its title, its cells and its size; it opens read only in the panel and downloads as .ipynb.
The head line names the other language, where the same study also lives. The panel draws what the file holds,
outputs included: it never runs the notebook.
"""

import html
import json
import re
from pathlib import Path

from bi import buttons
from bi.i18n import tr

# region Constants and variables
PROJECT_DIR = Path(__file__).resolve().parent.parent
# (language, file): the Spanish study and its English version.
NOTEBOOKS = [
    ("es", PROJECT_DIR / "notebooks" / "estudio_fuente_odepa_es.ipynb"),
    ("en", PROJECT_DIR / "notebooks" / "odepa_source_study_en.ipynb"),
]
NOTEBOOK_PARAMETER = "cuaderno"
LANGUAGE_NAMES = {"es": "Español", "en": "English"}
# The head line of the folder in each visit language: it names the version the folder does not list (D-535).
OTHER_LANGUAGE_NOTES = {
    "es": "Cuaderno de Jupyter · el mismo estudio está también en inglés (EN)",
    "en": "Cuaderno de Jupyter · el mismo estudio está también en español (ES)",
}
NOTEBOOK_COLOR = "#22b35a"
# The block of a notebook output: the source's raw data as the notebook printed it (tests/i18n_audit.py reads it as
# data, not as a sentence of the panel).
OUTPUT_OPEN, OUTPUT_CLOSE = '<div class="nb-output">', "</div><!--/nb-output-->"
# endregion


# region «Análisis de la fuente de datos»
def esc(value):
    return html.escape(str(value), quote=True)


def read_notebook(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def text_of(lines):
    return "".join(lines) if isinstance(lines, list) else str(lines)


def describe(language, path):
    """What the folder shows of one notebook, all of it read from the file."""
    notebook = read_notebook(path)
    cells = notebook["cells"]
    first = text_of(cells[0]["source"]).strip().split("\n\n")
    return {
        "language": language,
        "path": Path(path),
        "file": Path(path).name,
        "title": first[0].strip("* "),
        "purpose": re.split(r"(?<=\.)\s", first[1].strip(), maxsplit=1)[0] if len(first) > 1 else "",
        "cells": len(cells),
        "code": sum(cell["cell_type"] == "code" for cell in cells),
        "kilobytes": max(1, round(Path(path).stat().st_size / 1024)),
    }


def read_files():
    return [describe(language, path) for language, path in NOTEBOOKS]


def build_glyph():
    return (
        f'<span class="df-glyph" style="--df-color:{NOTEBOOK_COLOR}"><span class="df-fold"></span><b>IPYNB</b></span>'
    )


def build_file_html(file, open_address):
    """One notebook as a row of the folder, drawn like the files of «Documentos del proyecto»."""
    action = (
        buttons.build_link_html(tr("Abrir"), open_address, variant="primary", size="compact") if open_address else ""
    )
    meta = (
        f'<span class="df-meta"><span>{esc(LANGUAGE_NAMES[file["language"]])}</span>'
        f'<span>{file["cells"]} {esc(tr("celdas"))}</span><span>{file["kilobytes"]} kB</span></span>'
    )
    # The notebook in the other language keeps its own title, quoted as a name (D-443).
    title = file["title"] if open_address else f"«{file['title']}»"
    name = f'<b class="df-name">{esc(title)}</b>'
    head = (
        f'<a class="df-body" href="{esc(open_address)}" target="_self">' if open_address else '<span class="df-body">'
    )
    return (
        f'<div class="df-list"><div class="df-file nb-file">{head}<span class="df-top">{build_glyph()}{name}</span>'
        f'<span class="df-purpose nb-file-name">{esc(file["file"])}</span>{"</a>" if open_address else "</span>"}'
        f'{meta}<span class="df-actions">{action}</span></div></div>'
    )


def build_head_html(language):
    """The folder's head line: the path, and the other language where the same study also lives (D-535)."""
    return (
        f'<div class="df-head"><span class="df-path">GreenOcean <i>/</i> <b>notebooks</b></span>'
        f'<span class="df-count">{esc(tr(OTHER_LANGUAGE_NOTES[language]))}</span></div>'
    )


def build_path_html(folder_address, folder_name, file):
    """«Análisis de la fuente de datos / estudio_fuente_odepa_es.ipynb»: back to the folder."""
    return (
        f'<nav class="doc-path nb-path" aria-label="{esc(tr("Ruta"))}"><a href="{esc(folder_address)}" target="_self">'
        f"{esc(folder_name)}</a><i>/</i><span>{esc(file)}</span></nav>"
    )


def build_output_html(outputs):
    """The outputs of a code cell as the file keeps them: printed text, then tables."""
    parts = []
    for output in outputs:
        if output["output_type"] == "stream":
            parts.append(f'<pre class="nb-stream">{esc(text_of(output["text"]).rstrip())}</pre>')
        elif output["output_type"] in ("execute_result", "display_data"):
            data = output.get("data", {})
            if "text/html" in data:
                parts.append(f'<div class="nb-table">{text_of(data["text/html"])}</div>')
            elif "text/plain" in data:
                parts.append(f'<pre class="nb-stream">{esc(text_of(data["text/plain"]).rstrip())}</pre>')
    return OUTPUT_OPEN + "".join(parts) + OUTPUT_CLOSE if parts else ""


def build_css(palette):
    ink, text, muted, card, border, accent = (
        palette["strong_text"],
        palette["text"],
        palette["reference"],
        palette["card"],
        palette["card_border"],
        palette["accent"],
    )
    return f"""<style>
.nb-file .df-glyph b {{ font-size:5.5px !important; letter-spacing:0; }}
.nb-file .df-actions {{ flex:none; width:60px; }}
.nb-file .df-top {{ width:auto !important; flex:1 1 auto !important; min-width:0; }}
.nb-file .nb-file-name {{ flex:none !important; font-family:ui-monospace, Menlo, monospace; font-size:11.5px; color:{muted}; }}
.nb-path {{ display:flex; gap:6px; align-items:baseline; font-size:13px; color:{muted}; margin:0 0 6px; }}
.nb-path a {{ color:{accent} !important; text-decoration:none; }} .nb-path i {{ font-style:normal; }}
.nb-path span {{ color:{ink}; font-family:ui-monospace, Menlo, monospace; font-size:12.5px; }}
.nb-output {{ margin:-6px 0 10px; padding:10px 12px; border:1px solid {border}; border-radius:10px;
  background:color-mix(in srgb, {card} 70%, transparent); color:{text}; font-size:12.5px; }}
.nb-stream {{ margin:0 0 6px; padding:0; background:transparent !important; border:0; white-space:pre-wrap;
  font-family:ui-monospace, Menlo, monospace; font-size:12.5px; line-height:1.5; color:{ink}; }}
.nb-table {{ max-height:360px; overflow:auto; }}
.nb-table table {{ border-collapse:collapse; font-size:12px; font-variant-numeric:tabular-nums; color:{ink}; }}
.nb-table th, .nb-table td {{ padding:4px 9px; border-bottom:1px solid {border}; text-align:left; white-space:nowrap; }}
.nb-table thead th {{ position:sticky; top:0; background:{card}; color:{muted}; font-weight:600; }}
</style>"""


# endregion
