"""The project documents (PRD, SAD, ADR) as premium PDF files (step 6 of the refonte).

build_pdf turns the Markdown of docs/ into a short PDF (two pages at most, D-210): a title
band on the first page, styled headings and tables, and numbered pages. It reads only the subset of
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
                                ListItem, NextPageTemplate, PageTemplate, Paragraph, Spacer, Table, TableStyle)

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
# The title band on top of the first page, instead of a cover (D-210).
BAND_HEIGHT = 30 * mm

DIAGRAM_MARKER = re.compile(r"^\[\[diagrama:(\w+)\]\]\s*$")
TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
BULLET = re.compile(r"^\s*[-*]\s+(.*)$")
NUMBERED = re.compile(r"^\s*(\d+)\.\s+(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def _styles():
    base = dict(fontName="Helvetica", textColor=INK, alignment=TA_LEFT)
    return {
        "body": ParagraphStyle("body", fontSize=9.6, leading=13.4, spaceAfter=5, **base),
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=13.5, leading=17, textColor=GREEN_DARK,
                             spaceBefore=8, spaceAfter=5),
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
                story.append(CondPageBreak(30 * mm))
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
        body_height = PAGE_HEIGHT - 2 * MARGIN - 4 * mm
        first = Frame(MARGIN, MARGIN, CONTENT_WIDTH, body_height - BAND_HEIGHT + 4 * mm, id="first")
        frame = Frame(MARGIN, MARGIN, CONTENT_WIDTH, body_height, id="body")
        self.addPageTemplates([PageTemplate("first", [first], onPage=self._draw_first),
                               PageTemplate("body", [frame], onPage=self._draw_page)])

    def _draw_first(self, canvas, document):
        """A green band with the project, the title, the subtitle and the date."""
        canvas.saveState()
        top = PAGE_HEIGHT - BAND_HEIGHT
        canvas.setFillColor(GREEN_DARK)
        canvas.rect(0, top, PAGE_WIDTH, BAND_HEIGHT, stroke=0, fill=1)
        canvas.setFillColor(GREEN)
        canvas.rect(0, top - 1.2 * mm, PAGE_WIDTH, 1.2 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#72e7ad"))
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN, PAGE_HEIGHT - 9 * mm, PROJECT_NAME.upper())
        canvas.setFillColor(colors.HexColor("#d7efe2"))
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 9 * mm, self.issued)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 17)
        canvas.drawString(MARGIN, PAGE_HEIGHT - 18 * mm, _plain(self.document_title))
        canvas.setFillColor(colors.HexColor("#d7efe2"))
        canvas.setFont("Helvetica", 10)
        canvas.drawString(MARGIN, PAGE_HEIGHT - 25 * mm, _plain(self.subtitle))
        canvas.restoreState()
        self._draw_footer(canvas)

    def _draw_footer(self, canvas):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, 15 * mm, PAGE_WIDTH - MARGIN, 15 * mm)
        canvas.drawString(MARGIN, 11 * mm, f"{PROJECT_NAME} · {_plain(self.document_title)}")
        total = f" de {self.total_pages}" if self.total_pages else ""
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 11 * mm, f"Página {canvas.getPageNumber()}{total}")
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
        canvas.restoreState()
        self._draw_footer(canvas)

    def afterFlowable(self, flowable):
        if isinstance(flowable, _Heading):
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
    """The captures two per row, each with its caption; a missing file is skipped."""
    cells = []
    for file_name, caption in MOCKUP_FILES:
        path = MOCKUP_DIR / file_name
        if not path.exists():
            continue
        image = Image(str(path))
        scale = min(CONTENT_WIDTH * 0.47 / image.imageWidth, 52 * mm / image.imageHeight)
        image.drawWidth, image.drawHeight = image.imageWidth * scale, image.imageHeight * scale
        cells.append([image, Paragraph(escape(caption), styles["note"])])
    if not cells:
        return []
    rows = [cells[index:index + 2] + [""] * (2 - len(cells[index:index + 2])) for index in range(0, len(cells), 2)]
    grid = Table(rows, colWidths=[CONTENT_WIDTH / 2] * 2)
    grid.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2)]))
    return [grid]


def build_pdf(markdown_text, title, subtitle, issued=None):
    """The Markdown document as PDF bytes: a title band (project, title, subtitle, date),
    styled content and numbered pages."""
    styles = _styles()
    issued_text = _issued_text(issued or date.today())
    total_pages = None
    # Two builds: the first counts the pages, the second writes «Página n de N».
    for _ in range(2):
        buffer = BytesIO()
        document = _Document(buffer, title, subtitle, issued_text)
        document.total_pages = total_pages
        story = [NextPageTemplate("body")] + build_story(markdown_text, styles)
        document.multiBuild(story)
        total_pages = document.page
    return buffer.getvalue()
# endregion
