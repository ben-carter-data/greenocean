"""The files of bi/static/ (D-543): the JavaScript and the HTML the panel injects, each in a file of its own language.

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


# endregion
