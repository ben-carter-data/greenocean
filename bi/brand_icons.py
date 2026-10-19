"""Locally bundled brand paths shared by technical diagrams."""
import html
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET


@lru_cache(maxsize=16)
def logo_body(slug):
    root = ET.fromstring((Path(__file__).with_name("assets") / "logos" / f"{slug}.svg").read_text())
    return "".join(f'<path d="{html.escape(node.attrib["d"], quote=True)}"/>'
                   for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "path")


def logo(slug, x, y, color, size=28):
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="{color}" aria-hidden="true">{logo_body(slug)}</svg>')
