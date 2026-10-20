"""The project documents (PRD, SAD, ADR) as premium PDF files (step 6 of the refonte).

build_pdf turns the Markdown of docs/ into a PDF with a cover page, a table of
contents, styled headings and tables, and numbered pages. It reads only the subset of
Markdown the documents use: headings, paragraphs, tables, bullet and numbered lists,
quotes, horizontal rules, bold, italic and inline code. A [[diagrama:…]] marker
becomes a short note, because the diagram is drawn live in the panel.

Pure function: no Streamlit, no files, no network.
"""
import re
import unicodedata
from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (Image, BaseDocTemplate, CondPageBreak, Frame, KeepTogether, ListFlowable,
                                ListItem, NextPageTemplate, PageBreak, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

PROJECT_NAME = "GreenOcean"
DIAGRAM_NOTE = "Diagrama interactivo disponible en el panel"
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]

# Palette: the panel's dark green, a soft mint for table headers and quiet greys.
INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#5f6b76")
GREEN = colors.HexColor("#167046")
GREEN_DARK = colors.HexColor("#0e3b27")
MINT = colors.HexColor("#e8f4ee")
RULE = colors.HexColor("#d5dde3")
ZEBRA = colors.HexColor("#f7f9fa")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

DIAGRAM_MARKER = re.compile(r"^\[\[diagrama:(\w+)\]\]\s*$")
TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
BULLET = re.compile(r"^\s*[-*]\s+(.*)$")
NUMBERED = re.compile(r"^\s*(\d+)\.\s+(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def _styles():
    base = dict(fontName="Helvetica", textColor=INK, alignment=TA_LEFT)
    return {
        "body": ParagraphStyle("body", fontSize=10, leading=14.5, spaceAfter=6, **base),
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=GREEN_DARK,
                             spaceBefore=14, spaceAfter=8),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=GREEN,
                             spaceBefore=10, spaceAfter=5),
        "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=INK,
                             spaceBefore=6, spaceAfter=3),
        "cell": ParagraphStyle("cell", fontSize=8.6, leading=11.4, **base),
        "header": ParagraphStyle("header", fontName="Helvetica-Bold", fontSize=8.6, leading=11.4,
                                 textColor=GREEN_DARK),
        "quote": ParagraphStyle("quote", fontName="Helvetica-Oblique", fontSize=9.6, leading=14,
                                textColor=MUTED, leftIndent=10, spaceAfter=6),
        "note": ParagraphStyle("note", fontName="Helvetica-Oblique", fontSize=9.4, leading=13,
                               textColor=GREEN, spaceBefore=2, spaceAfter=8),
        "toc_title": ParagraphStyle("toc_title", fontName="Helvetica-Bold", fontSize=20, leading=24,
                                    textColor=GREEN_DARK, spaceAfter=14),
        "toc1": ParagraphStyle("toc1", fontName="Helvetica", fontSize=10.5, leading=17, textColor=INK,
                               leftIndent=0),
        "toc2": ParagraphStyle("toc2", fontName="Helvetica", fontSize=9.5, leading=14, textColor=MUTED,
                               leftIndent=14),
    }


# region Inline Markdown
def _clean_text(text):
    """Characters the built-in PDF fonts can draw: superscripts become <super>, the
    minus sign a dash, anything else outside Windows-1252 its closest ASCII form."""
    text = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+", lambda m: "\x00" + m.group(0).translate(SUPERSCRIPTS) + "\x01", text)
    text = text.replace("−", "–")
    cleaned = []
    for character in text:
        try:
            character.encode("cp1252")
            cleaned.append(character)
        except UnicodeEncodeError:
            cleaned.append(unicodedata.normalize("NFKD", character).encode("ascii", "ignore").decode() or "?")
    return "".join(cleaned)


def inline_markup(text):
    """Markdown inline (bold, italic, code) as reportlab paragraph markup, escaped."""
    text = _clean_text(text)
    codes = []

    def keep_code(match):
        codes.append(match.group(1))
        return f"\x02{len(codes) - 1}\x03"

    text = re.sub(r"`([^`]+)`", keep_code, text)
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"(?<![\w])_(?!\s)(.+?)(?<!\s)_(?![\w])", r"<i>\1</i>", text)
    text = re.sub(r"\x02(\d+)\x03", lambda m: '<font name="Courier" size="8.8" color="#0e3b27">'
                  + escape(codes[int(m.group(1))]) + "</font>", text)
    return text.replace("\x00", "<super>").replace("\x01", "</super>")


def _plain_keep_code(text):
    """Text without bold or italic marks, code spans kept between backticks."""
    return re.sub(r"\*", "", _clean_text(text)).replace("\x00", "").replace("\x01", "")


def _plain(text):
    """A heading as plain text for the table of contents and the bookmarks."""
    return re.sub(r"`", "", _plain_keep_code(text))
# endregion


# region Blocks
def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def parse_blocks(markdown_text):
    """[(kind, payload)] for heading, paragraph, table, bullets, numbers, quote, diagram."""
    lines = markdown_text.replace("\r\n", "\n").split("\n")
    blocks = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            index += 1
            continue
        diagram = DIAGRAM_MARKER.match(stripped)
        if diagram:
            blocks.append(("diagram", diagram.group(1)))
            index += 1
            continue
        heading = HEADING.match(stripped)
        if heading:
            blocks.append(("heading", (len(heading.group(1)), heading.group(2).strip())))
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and TABLE_SEPARATOR.match(lines[index + 1].strip()):
            header = _split_row(stripped)
            rows = []
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                row = _split_row(lines[index])
                rows.append((row + [""] * len(header))[:len(header)])
                index += 1
            blocks.append(("table", (header, rows)))
            continue
        if BULLET.match(line) or NUMBERED.match(line):
            numbered = bool(NUMBERED.match(line))
            pattern = NUMBERED if numbered else BULLET
            items = []
            while index < len(lines) and pattern.match(lines[index]):
                items.append(pattern.match(lines[index]).groups()[-1].strip())
                index += 1
                # Continuation lines of the same item.
                while (index < len(lines) and lines[index].startswith("  ") and lines[index].strip()
                       and not BULLET.match(lines[index]) and not NUMBERED.match(lines[index])):
                    items[-1] += " " + lines[index].strip()
                    index += 1
            blocks.append(("numbers" if numbered else "bullets", items))
            continue
        if stripped.startswith(">"):
            quote = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote.append(lines[index].strip().lstrip(">").strip())
                index += 1
            blocks.append(("quote", " ".join(quote)))
            continue
        paragraph = [stripped]
        index += 1
        while index < len(lines):
            following = lines[index].strip()
            if (not following or HEADING.match(following) or following.startswith(("|", ">"))
                    or BULLET.match(lines[index]) or NUMBERED.match(lines[index])
                    or DIAGRAM_MARKER.match(following)):
                break
            paragraph.append(following)
            index += 1
        blocks.append(("paragraph", " ".join(paragraph)))
    return blocks


def _measure(cell, bold=False):
    """(widest word, whole line) of a cell in points, code spans in Courier."""
    widest = whole = 0.0
    for position, part in enumerate(re.split(r"`([^`]+)`", _plain_keep_code(cell))):
        font, size = ("Courier", 8.8) if position % 2 else ("Helvetica-Bold" if bold else "Helvetica", 8.6)
        whole += stringWidth(part, font, size)
        # Paths break only at spaces, so a long path is one word.
        for word in part.split():
            widest = max(widest, stringWidth(word, font, size))
    return widest, whole


def _column_widths(header, rows):
    """Every column at least as wide as its longest word; the rest of the width goes
    where the text is, so short labels never break inside a word."""
    padding = 11
    count = len(header)
    minimum, natural = [], []
    for column in range(count):
        measures = [_measure(header[column], bold=True)] + [_measure(row[column]) for row in rows]
        minimum.append(min(max(widest for widest, _ in measures) + padding, CONTENT_WIDTH * 0.45))
        natural.append(max(max(whole for _, whole in measures) + padding, minimum[-1]))
    if sum(minimum) >= CONTENT_WIDTH:
        return [CONTENT_WIDTH * width / sum(minimum) for width in minimum]
    if sum(natural) <= CONTENT_WIDTH:
        return [CONTENT_WIDTH * width / sum(natural) for width in natural]
    spare = CONTENT_WIDTH - sum(minimum)
    need = [natural[column] - minimum[column] for column in range(count)]
    # A power below one tempers the widest column, so prose columns share the space.
    weights = [value ** 0.75 for value in need]
    return [minimum[column] + spare * weights[column] / sum(weights) for column in range(count)]


def _table(header, rows, styles):
    data = [[Paragraph(inline_markup(cell), styles["header"]) for cell in header]]
    data += [[Paragraph(inline_markup(cell), styles["cell"]) for cell in row] for row in rows]
    table = Table(data, colWidths=_column_widths(header, rows), repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), MINT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.9, GREEN),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for row in range(2, len(data), 2):
        commands.append(("BACKGROUND", (0, row), (-1, row), ZEBRA))
    table.setStyle(TableStyle(commands))
    return table


class _Heading(Paragraph):
    """A heading that feeds the table of contents and the PDF bookmarks."""

    def __init__(self, text, style, level, key):
        super().__init__(inline_markup(text), style)
        self.toc_level = level
        self.toc_text = _plain(text)
        self.toc_key = key


def build_story(markdown_text, styles):
    story = []
    blocks = parse_blocks(markdown_text)
    # The document's own H1 is the cover title.
    if blocks and blocks[0][0] == "heading" and blocks[0][1][0] == 1:
        blocks = blocks[1:]
    heading_number = 0
    for kind, payload in blocks:
        if kind == "heading":
            level, text = payload
            heading_number += 1
            if level <= 2:
                story.append(CondPageBreak(45 * mm))
                story.append(_Heading(text, styles["h1"], 0, f"h{heading_number}"))
            else:
                story.append(CondPageBreak(30 * mm))
                story.append(_Heading(text, styles["h2" if level == 3 else "h3"], 1, f"h{heading_number}"))
        elif kind == "paragraph":
            story.append(Paragraph(inline_markup(payload), styles["body"]))
        elif kind == "quote":
            story.append(Paragraph(inline_markup(payload), styles["quote"]))
        elif kind == "diagram" and payload == "mockups":
            story += build_mockup_flowables(styles)
        elif kind == "diagram":
            story.append(Paragraph(DIAGRAM_NOTE + f" ({payload}).", styles["note"]))
        elif kind == "table":
            header, rows = payload
            table = _table(header, rows, styles)
            story.append(KeepTogether([table]) if len(rows) <= 6 else table)
            story.append(Spacer(1, 8))
        elif kind in ("bullets", "numbers"):
            items = [ListItem(Paragraph(inline_markup(item), styles["body"]), leftIndent=14)
                     for item in payload]
            options = dict(bulletType="1", bulletFontName="Helvetica-Bold") if kind == "numbers" else dict(
                bulletType="bullet", start="•", bulletColor=GREEN)
            story.append(ListFlowable(items, leftIndent=14, bulletFontSize=9.5, **options))
            story.append(Spacer(1, 4))
    return story
# endregion


# region Document
class _Document(BaseDocTemplate):
    def __init__(self, buffer, title, subtitle, issued):
        super().__init__(buffer, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=MARGIN + 4 * mm, bottomMargin=MARGIN, title=f"{PROJECT_NAME} · {title}",
                         author=PROJECT_NAME, subject=subtitle, creator=PROJECT_NAME)
        self.document_title = title
        self.subtitle = subtitle
        self.issued = issued
        self.total_pages = None
        frame = Frame(MARGIN, MARGIN, CONTENT_WIDTH, PAGE_HEIGHT - 2 * MARGIN - 4 * mm, id="body")
        cover = Frame(MARGIN, MARGIN, CONTENT_WIDTH, PAGE_HEIGHT - 2 * MARGIN, id="cover")
        self.addPageTemplates([PageTemplate("cover", [cover], onPage=self._draw_cover),
                               PageTemplate("body", [frame], onPage=self._draw_page)])

    def _draw_cover(self, canvas, _document):
        canvas.saveState()
        canvas.setFillColor(GREEN_DARK)
        canvas.rect(0, PAGE_HEIGHT * 0.38, PAGE_WIDTH, PAGE_HEIGHT * 0.62, stroke=0, fill=1)
        canvas.setFillColor(GREEN)
        canvas.rect(0, PAGE_HEIGHT * 0.38 - 3 * mm, PAGE_WIDTH, 3 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#72e7ad"))
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawString(MARGIN, PAGE_HEIGHT - 32 * mm, PROJECT_NAME.upper())
        canvas.setFillColor(colors.white)
        title_style = ParagraphStyle("cover_title", fontName="Helvetica-Bold", fontSize=30, leading=35,
                                     textColor=colors.white)
        subtitle_style = ParagraphStyle("cover_subtitle", fontName="Helvetica", fontSize=13, leading=18,
                                        textColor=colors.HexColor("#d7efe2"))
        title = Paragraph(inline_markup(self.document_title), title_style)
        _, title_height = title.wrap(CONTENT_WIDTH, PAGE_HEIGHT)
        title_top = PAGE_HEIGHT * 0.38 + 70 * mm
        title.drawOn(canvas, MARGIN, title_top)
        subtitle = Paragraph(inline_markup(self.subtitle), subtitle_style)
        _, subtitle_height = subtitle.wrap(CONTENT_WIDTH * 0.85, PAGE_HEIGHT)
        subtitle.drawOn(canvas, MARGIN, title_top - subtitle_height - 8 * mm)
        canvas.setFillColor(INK)
        canvas.setFont("Helvetica", 10)
        canvas.drawString(MARGIN, PAGE_HEIGHT * 0.38 - 20 * mm, "Monitor semanal de precios de alimentos en Chile")
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, PAGE_HEIGHT * 0.38 - 27 * mm, "Datos abiertos de ODEPA e IPC del INE")
        canvas.setStrokeColor(RULE)
        canvas.line(MARGIN, 30 * mm, PAGE_WIDTH - MARGIN, 30 * mm)
        canvas.setFont("Helvetica", 9)
        canvas.drawString(MARGIN, 23 * mm, self.issued)
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 23 * mm, PROJECT_NAME)
        canvas.restoreState()

    def _draw_page(self, canvas, _document):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(GREEN)
        canvas.drawString(MARGIN, PAGE_HEIGHT - 12 * mm, PROJECT_NAME.upper())
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 12 * mm, _plain(self.document_title))
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, PAGE_HEIGHT - 14 * mm, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 14 * mm)
        canvas.line(MARGIN, 15 * mm, PAGE_WIDTH - MARGIN, 15 * mm)
        canvas.drawString(MARGIN, 11 * mm, f"{PROJECT_NAME} · {_plain(self.document_title)}")
        total = f" de {self.total_pages}" if self.total_pages else ""
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 11 * mm, f"Página {canvas.getPageNumber()}{total}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, _Heading):
            self.notify("TOCEntry", (flowable.toc_level, flowable.toc_text, self.page, flowable.toc_key))
            self.canv.bookmarkPage(flowable.toc_key)
            self.canv.addOutlineEntry(flowable.toc_text, flowable.toc_key, level=flowable.toc_level,
                                      closed=True)


def _issued_text(issued):
    return f"{issued.day} de {MONTHS[issued.month - 1]} de {issued.year}"


# The real screens of the PRD (D-205): the same captures the panel shows, two per row.
MOCKUP_DIR = Path(__file__).resolve().parent.parent / "docs" / "img"
MOCKUP_FILES = [("m1-resumen-vantablack.jpg", "M-1 · Resumen semanal · tema Vantablack"),
                ("m2-precios-claro.jpg", "M-2 · Precios e inflación · tema Claro"),
                ("m3-sql-corporativo.jpg", "M-3 · Consultas SQL · tema Corporativo"),
                ("m4-telefono-bluelight.jpg", "M-4 · Resumen semanal · teléfono, tema Blue Light")]


def build_mockup_flowables(styles):
    """The captures as images under each other, with a caption; a missing file is skipped."""
    flowables = []
    for file_name, caption in MOCKUP_FILES:
        path = MOCKUP_DIR / file_name
        if not path.exists():
            continue
        image = Image(str(path))
        scale = CONTENT_WIDTH * 0.9 / image.imageWidth
        image.drawWidth, image.drawHeight = image.imageWidth * scale, image.imageHeight * scale
        flowables.append(KeepTogether([image, Paragraph(escape(caption), styles["note"])]))
    return flowables


def build_pdf(markdown_text, title, subtitle, issued=None):
    """The Markdown document as PDF bytes: cover (project, title, subtitle, date),
    table of contents, styled content and numbered pages."""
    styles = _styles()
    issued_text = _issued_text(issued or date.today())
    total_pages = None
    # Two builds: the first counts the pages, the second writes «Página n de N».
    for _ in range(2):
        buffer = BytesIO()
        document = _Document(buffer, title, subtitle, issued_text)
        document.total_pages = total_pages
        contents = TableOfContents(levelStyles=[styles["toc1"], styles["toc2"]], dotsMinLevel=0)
        story = [NextPageTemplate("body"), PageBreak(),
                 Paragraph("Contenido", styles["toc_title"]), contents, PageBreak()]
        story += build_story(markdown_text, styles)
        document.multiBuild(story)
        total_pages = document.page
    return buffer.getvalue()
# endregion
