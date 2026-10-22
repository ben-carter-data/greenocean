"""Turn medicion.json (from medir.cjs) into the Markdown tables of the measurement report.

    python tests/medicion/tabla.py <medicion.json>
"""
import json
import sys
from collections import defaultdict

DESKTOP = [(1440, 700), (1440, 900), (1920, 1080)]
PHONE = [(390, 844), (844, 390)]
# A page may leave at most this share of the window empty under its last element.
MAX_EMPTY = 10


def top(row):
    return row["parts"][0]


def total(row, key):
    if key == "nOverlapIcon":
        # A one or two character glyph (the «✓» inside its own icon) is part of the icon.
        return sum(len([o for o in part["overlapIcon"] if len(o["t"]) > 2]) for part in row["parts"])
    return sum(part[key] for part in row["parts"])


def fits(row):
    main = top(row)["main"]
    return bool(main) and main["scroll"] <= main["client"] + 1


def cell(rows):
    """Natural height of the content and the verdict, same for both themes or marked."""
    out = []
    for row in rows:
        part = top(row)
        height = part["block"]["h"]
        if not fits(row):
            out.append(f"{height} ✘ desplaza")
        elif part["emptyPct"] > MAX_EMPTY:
            out.append(f"{height} ✘ vacío {part['emptyPct']} %")
        else:
            out.append(f"{height} ✔")
    return out[0] if len(set(out)) == 1 else " / ".join(out)


CHROME = ("app_header", "header_preferences", "report_page", "window_page", "return_to_previous")


def grower(row):
    """The tallest blocks with a name of their own (a key, an iframe, a table, an SVG)."""
    items = [item for part in row["parts"] for item in part["tall"]
             if not any(skip in item["el"] for skip in CHROME)
             and not (item["el"].startswith("div[stVerticalBlock]") and "st-key-" not in item["el"])
             and not item["el"].startswith("iframe[stIFrame]")]
    items += [{"el": "iframe", "h": f["h"]} for part in row["parts"] for f in part["frames"] if f["h"] >= 300]
    items.sort(key=lambda item: -item["h"])
    return "; ".join(f"{item['el'].replace('div[stVerticalBlock].st-key-', '')} {item['h']} px"
                     for item in items[:2]) or "—"


def issues(rows):
    """Counts over the worst of both themes, at the three desktop sizes."""
    worst = defaultdict(int)
    for row in rows:
        worst["small"] = max(worst["small"], total(row, "nSmall"))
        worst["text"] = max(worst["text"], total(row, "nOverlapText"))
        worst["icon"] = max(worst["icon"], total(row, "nOverlapIcon"))
        worst["clip"] = max(worst["clip"], total(row, "nClipped"))
    return worst


def main(path):
    data = json.load(open(path))
    pages = []
    for row in data:
        if (row["n"], row["slug"]) not in pages:
            pages.append((row["n"], row["slug"]))

    def pick(n, theme, size):
        return [r for r in data if r["n"] == n and r["theme"] == theme and (r["w"], r["h"]) == size]

    print("## Alto natural y desplazamiento (Vantablack / Blue Light si difieren)\n")
    print("| # | Página | 1440 × 700 | 1440 × 900 | 1920 × 1080 | Qué la hace crecer (1440 × 900) |")
    print("|--:|---|---|---|---|---|")
    for n, slug in pages:
        cells = []
        for size in DESKTOP:
            rows = [pick(n, t, size)[0] for t in ("Vantablack", "Blue Light") if pick(n, t, size)]
            cells.append(cell(rows) if rows else "—")
        ref = pick(n, "Vantablack", (1440, 900))
        print(f"| {n} | {slug} | " + " | ".join(cells) + f" | {grower(ref[0]) if ref else '—'} |")

    print("\n## Texto menor de 11 px, superposiciones y recortes (peor caso de ambos temas, 3 pantallas)\n")
    print("| # | Página | Texto < 11 px | Texto × texto | Texto × ícono | Texto recortado | SVG fuera de la ventana |")
    print("|--:|---|--:|--:|--:|--:|---|")
    for n, slug in pages:
        rows = [r for r in data if r["n"] == n and (r["w"], r["h"]) in DESKTOP]
        worst = issues(rows)
        cut = sorted({name for r in rows for p in r["parts"] for name in p["svgCut"]})
        print(f"| {n} | {slug} | {worst['small']} | {worst['text']} | {worst['icon']} | {worst['clip']} | {', '.join(cut) or '—'} |")

    print("\n## Teléfono (Vantablack): alto natural / ventana\n")
    print("| # | Página | 390 × 844 | 844 × 390 |")
    print("|--:|---|---|---|")
    for n, slug in pages:
        cells = []
        for size in PHONE:
            rows = pick(n, "Vantablack", size)
            if not rows:
                cells.append("—")
                continue
            main_ = top(rows[0])["main"] or {}
            cells.append(f"{main_.get('scroll', '—')} / {main_.get('client', '—')}")
        print(f"| {n} | {slug} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main(sys.argv[1])
