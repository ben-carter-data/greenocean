"""The files of bi/static/ (D-543, D-544): the JavaScript, the HTML and the CSS the panel injects, each in a file of
its own language.

The modules that draw a view read them once, when they load, and inject them as they did when the code lived inside a
Python string: the text that reaches the page is the same, character for character.
"""

from pathlib import Path

# region Variables
FOLDER = Path(__file__).resolve().parent / "static"
# endregion


# region Reading
def read(name):
    """The text of bi/static/<name>, exactly as the page receives it."""
    return (FOLDER / name).read_text(encoding="utf-8")


def fill(name, values):
    """A file of bi/static/ with each of its marks replaced by its value (R-003): `var(--go-accent)` by the colour of
    the theme in CSS, `__GO_NAME__` in JavaScript or HTML, `/* insert: … */` by a block of CSS. The file keeps the code;
    Python only gives the values."""
    text = read(name)
    for mark, value in values.items():
        text = text.replace(mark, str(value))
    return text


def style(name, values=None):
    """A stylesheet of bi/static/ as the <style> block the page receives, its marks filled when it has values."""
    return "<style>" + (fill(name, values) if values else read(name)) + "</style>"


def script(name, values=None):
    """A script of bi/static/ as the <script> block the page receives, its marks filled when it has values."""
    return "<script>" + (fill(name, values) if values else read(name)) + "</script>"


# endregion
