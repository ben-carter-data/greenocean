"""The GitHub page: the repository at the centre and its five links branched below.

One self-contained HTML block (style scoped under .gh-page) for st.html, and one
script for the copy buttons. Every address comes from bi/project.py (D-070): a link
without an address stays out of the tree, and a branch left empty is not drawn.
"""

import html

from bi import brand_icons, charts, project

# region Constants
REPO_SLUG = project.GITHUB_URL.rstrip("/").split("github.com/")[-1]

# The three branches, left to right, each with its own hue in light and dark bases.
CATEGORIES = [
    {"key": "auto", "label": "Automatización", "light": "#16a34a", "dark": "#34d399"},
    {"key": "trace", "label": "Trazabilidad", "light": "#2563eb", "dark": "#60a5fa"},
    {"key": "docs", "label": "Documentación", "light": "#0d9488", "dark": "#2dd4bf"},
]
# Each item names the PROJECT_LINKS entry its address comes from.
ITEMS = [
    {
        "link": "GitHub Actions",
        "title": "GitHub Actions",
        "text": "Ejecuciones del workflow.",
        "category": "auto",
        "icon": "actions",
    },
    {
        "link": "Historial de cambios",
        "title": "Historial de cambios",
        "text": "Cada cambio y su propósito.",
        "category": "trace",
        "icon": "git",
    },
    {
        "link": "DECISIONES",
        "title": "Decisiones",
        "text": "Qué se decidió y por qué.",
        "category": "trace",
        "icon": "decisions",
    },
    {
        "link": "MANUAL",
        "title": "Manual",
        "text": "Operación semanal y resolución de fallos.",
        "category": "docs",
        "icon": "manual",
    },
    {
        "link": "Informes semanales",
        "title": "Informes semanales",
        "text": "Resultado publicado de cada ejecución.",
        "category": "docs",
        "icon": "report",
    },
]

COPY_ICON = (
    '<svg class="gh-ico-copy" viewBox="0 0 24 24" aria-hidden="true">'
    '<rect x="8.5" y="8.5" width="11" height="11" rx="2.6"/>'
    '<path d="M15.5 8.5V6.6A2.1 2.1 0 0 0 13.4 4.5H6.6A2.1 2.1 0 0 0 4.5 6.6v6.8'
    'a2.1 2.1 0 0 0 2.1 2.1h1.9"/></svg>'
    '<svg class="gh-ico-check" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M5 12.5l4.4 4.4L19 7.3"/></svg>'
)
ARROW = '<svg class="gh-arrow" viewBox="0 0 12 12" aria-hidden="true"><path d="M3.5 8.5l5-5M4.5 3.5h4v4"/></svg>'
# endregion


def _links_by_name():
    return {link["name"]: link["url"] for link in project.PROJECT_LINKS}


def page_items():
    """The items of the tree that have an address, each with its url."""
    urls = _links_by_name()
    return [{**item, "url": urls[item["link"]]} for item in ITEMS if urls.get(item["link"])]


# region Glyphs (viewBox 0 0 64 64, ids prefixed so they never collide with the panel)
def _gradient(gid, top, bottom, user_space=False):
    # In user space a straight horizontal stroke still takes the gradient (a box of
    # zero height draws nothing with the default bounding-box units).
    if user_space:
        return (
            f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="6" x2="22" y2="60">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>'
            '</linearGradient>'
        )
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="0.35" y2="1">'
        f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>'
        '</linearGradient>'
    )


def _glyph(kind, dark):
    shadow = (
        '<filter id="gh-gs" x="-30%" y="-30%" width="160%" height="170%">'
        '<feDropShadow dx="0" dy="2.2" stdDeviation="1.8" flood-color="#0b1f3a" '
        f'flood-opacity="{0.45 if dark else 0.22}"/></filter>'
    )
    if kind == "actions":
        return shadow, (
            _gradient("gh-g-act", "#4f8dff", "#1556d6", True)
            + '</defs><g filter="url(#gh-gs)" fill="none" stroke="url(#gh-g-act)" '
            'stroke-width="4" stroke-linecap="round">'
            '<path d="M19 28v18a8 8 0 0 0 8 8h3.5"/>'
            '<path d="M19 30a8 8 0 0 0 8 8h3.5"/><path d="M42.5 38h3"/>'
            '<circle cx="36.5" cy="38" r="6"/><circle cx="51.5" cy="38" r="6"/>'
            '<circle cx="36.5" cy="54" r="6"/></g>'
            '<g filter="url(#gh-gs)"><circle cx="19" cy="17" r="11.5" fill="url(#gh-g-act)"/>'
            '<path d="M15.6 11.4v11.2l9-5.6z" fill="#fff"/></g>'
            '<path d="M10.2 14a9.6 9.6 0 0 1 8-6.4" stroke="#fff" stroke-opacity=".55" '
            'stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        )
    if kind == "git":
        return shadow, (
            _gradient("gh-g-git", "#ff6a3d", "#e2421b")
            + '</defs><svg x="6" y="6" width="52" height="52" viewBox="0 0 24 24">'
            f'<g filter="url(#gh-gs)" fill="url(#gh-g-git)">{brand_icons.logo_body("git")}'
            '</g></svg><path d="M18 22l13-13" stroke="#fff" stroke-opacity=".35" '
            'stroke-width="1.6" stroke-linecap="round"/>'
        )
    if kind == "decisions":
        return shadow, (
            _gradient("gh-g-doc", "#5b95ff", "#1d5fd6", True)
            + _gradient("gh-g-doc2", "#ffffff", "#dfe8f7")
            + '</defs><g filter="url(#gh-gs)">'
            '<path d="M20 12h18l10 10v28a4 4 0 0 1-4 4H22a4 4 0 0 1-4-4V16a4 4 0 0 1 2-4z" '
            'fill="url(#gh-g-doc)" transform="translate(4 -2)" opacity=".55"/>'
            '<path d="M18 14a4 4 0 0 1 4-4h16l10 10v30a4 4 0 0 1-4 4H22a4 4 0 0 1-4-4z" '
            'fill="url(#gh-g-doc2)"/>'
            '<path d="M38 10v7a3 3 0 0 0 3 3h7z" fill="#c7d6ef"/></g>'
            '<g stroke="url(#gh-g-doc)" stroke-width="3.6" stroke-linecap="round">'
            '<path d="M24.5 27h17"/><path d="M24.5 34.5h17"/><path d="M24.5 42h17"/>'
            '<path d="M24.5 49.5h10"/></g>'
        )
    if kind == "manual":
        return shadow, (
            _gradient("gh-g-book", "#2dd4bf", "#0d8a7d")
            + _gradient("gh-g-page", "#ffffff", "#e3f1ef")
            + '</defs><g filter="url(#gh-gs)">'
            '<path d="M6 18c9-3 18-2 26 3 8-5 17-6 26-3v32c-9-3-18-2-26 3-8-5-17-6-26-3z" '
            'fill="url(#gh-g-book)"/>'
            '<path d="M10 15c8-2 15-1 21 3v31c-6-4-13-5-21-3z" fill="url(#gh-g-page)"/>'
            '<path d="M54 15c-8-2-15-1-21 3v31c6-4 13-5 21-3z" fill="url(#gh-g-page)"/></g>'
            '<g stroke="#8cc9c1" stroke-width="2.6" stroke-linecap="round">'
            '<path d="M15 24c4-.8 7.5-.5 11 1"/><path d="M15 30.5c4-.8 7.5-.5 11 1"/>'
            '<path d="M15 37c4-.8 7.5-.5 11 1"/><path d="M38 25c3.5-1.5 7-1.8 11-1"/>'
            '<path d="M38 31.5c3.5-1.5 7-1.8 11-1"/><path d="M38 38c3.5-1.5 7-1.8 11-1"/></g>'
        )
    return shadow, (
        _gradient("gh-g-rep", "#2dd4bf", "#0b8f80")
        + _gradient("gh-g-sheet", "#ffffff", "#e6f2f0")
        + '</defs><g filter="url(#gh-gs)">'
        '<rect x="12" y="8" width="40" height="48" rx="6" fill="url(#gh-g-sheet)"/></g>'
        '<g stroke="#9fd8cf" stroke-width="3" stroke-linecap="round">'
        '<path d="M19 17h18"/><path d="M19 23h12"/><path d="M19 49h26"/></g>'
        '<g fill="url(#gh-g-rep)"><rect x="19" y="36" width="5" height="7" rx="1.4"/>'
        '<rect x="27" y="32" width="5" height="11" rx="1.4"/>'
        '<rect x="35" y="27" width="5" height="16" rx="1.4"/>'
        '<rect x="43" y="21" width="5" height="22" rx="1.4"/></g>'
    )


def build_glyph_svg(kind, dark=False):
    """A glossy icon for one item, drawn only with SVG gradients and shadows."""
    shadow, body = _glyph(kind, dark)
    return f'<svg class="gh-glyph" viewBox="0 0 64 64" aria-hidden="true"><defs>{shadow}{body}</svg>'


# endregion


def build_hero_svg(palette):
    """The GitHub mark as a glossy sphere resting on a lit pedestal."""
    dark = palette["base"] == charts.BASE_DARK
    ped_top, ped_bottom = ("#2a3442", "#0e141d") if dark else ("#ffffff", "#d7deea")
    face_top, face_bottom = ("#3a4658", "#18212e") if dark else ("#fbfcfe", "#e6ebf3")
    glow = "#38bdf8" if dark else "#3b82f6"
    rim = palette["accent"] if dark else "#ffffff"
    return (
        '<svg class="gh-hero-art" viewBox="0 0 240 236" role="img" aria-label="GitHub">'
        '<defs>'
        f'<linearGradient id="gh-ped" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ped_top}"/>'
        f'<stop offset="1" stop-color="{ped_bottom}"/></linearGradient>'
        f'<linearGradient id="gh-face" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{face_top}"/>'
        f'<stop offset="1" stop-color="{face_bottom}"/></linearGradient>'
        '<radialGradient id="gh-ball" cx="0.38" cy="0.3" r="0.8">'
        '<stop offset="0" stop-color="#4a5260"/><stop offset="0.45" stop-color="#1b1f26"/>'
        '<stop offset="1" stop-color="#030405"/></radialGradient>'
        '<radialGradient id="gh-cat" cx="0.5" cy="0.35" r="0.7">'
        '<stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#dfe6f1"/></radialGradient>'
        '<linearGradient id="gh-spec" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".55"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<filter id="gh-blur" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="6"/></filter>'
        '<filter id="gh-blur2" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="2.2"/></filter>'
        '</defs>'
        # Floor shadow and the pedestal: body, lit ring, top face.
        '<ellipse cx="120" cy="214" rx="92" ry="14" fill="#0b1f3a" opacity=".16" filter="url(#gh-blur)"/>'
        '<path d="M34 186v14c0 12 38.5 22 86 22s86-10 86-22v-14z" fill="url(#gh-ped)"/>'
        f'<ellipse cx="120" cy="186" rx="86" ry="22" fill="url(#gh-face)" stroke="{rim}" '
        'stroke-opacity=".35"/>'
        f'<ellipse cx="120" cy="186" rx="66" ry="15" fill="none" stroke="{glow}" stroke-width="6" '
        'opacity=".55" filter="url(#gh-blur)"/>'
        f'<ellipse cx="120" cy="186" rx="64" ry="14" fill="none" stroke="{glow}" stroke-width="1.6" '
        'opacity=".9"/>'
        f'<ellipse cx="120" cy="186" rx="60" ry="12" fill="{glow}" opacity=".12"/>'
        # Contact shadow of the sphere on the face.
        '<ellipse cx="120" cy="184" rx="52" ry="9" fill="#000" opacity=".28" filter="url(#gh-blur2)"/>'
        # The sphere: the cat shows through the mark (a light disc behind the black path).
        '<circle cx="120" cy="96" r="80" fill="url(#gh-cat)"/>'
        '<svg x="38" y="14" width="164" height="164" viewBox="0 0 24 24">'
        f'<g fill="url(#gh-ball)">{brand_icons.logo_body("github")}</g></svg>'
        f'<circle cx="120" cy="96" r="81.5" fill="none" stroke="{rim}" stroke-opacity="{0.35 if dark else 0.6}" '
        'stroke-width="1.5"/>'
        '<ellipse cx="98" cy="40" rx="42" ry="18" fill="url(#gh-spec)" transform="rotate(-24 98 40)"/>'
        '</svg>'
    )


def _style(palette):
    dark = palette["base"] == charts.BASE_DARK
    tone = "dark" if dark else "light"
    colors = {cat["key"]: cat[tone] for cat in CATEGORIES}
    tile_top, tile_bottom = ("#2a3546", "#141c28") if dark else ("#ffffff", "#e9eef6")
    tile_edge = "rgba(255,255,255,.10)" if dark else "rgba(255,255,255,.95)"
    tile_shadow = (
        "0 18px 34px -12px rgba(0,0,0,.75), 0 4px 10px rgba(0,0,0,.45)"
        if dark
        else "0 20px 32px -14px rgba(15,40,90,.35), 0 4px 10px rgba(15,40,90,.08)"
    )
    line_alpha = ".75" if dark else ".6"
    button_bg = "rgba(255,255,255,.04)" if dark else "#ffffff"
    return f"""<style>
.gh-page {{
  --gh-ink: {palette["strong_text"]}; --gh-text: {palette["text"]};
  --gh-accent: {"#60a5fa" if dark else "#1d5fd6"}; --gh-border: {palette["card_border"]};
  --gh-auto: {colors["auto"]}; --gh-trace: {colors["trace"]}; --gh-docs: {colors["docs"]};
  --gh-btn-bg: {button_bg};
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", system-ui, sans-serif;
  color: var(--gh-text); max-width: 1120px; margin: 0 auto; padding: 4px 0 28px;
  box-sizing: border-box; -webkit-font-smoothing: antialiased;
}}
.gh-page *, .gh-page *::before, .gh-page *::after {{ box-sizing: border-box; }}
.gh-top {{ display: grid; grid-template-columns: 1fr auto 1fr; align-items: start; gap: 24px; }}
.gh-head h1 {{ margin: 34px 0 10px; font-size: 2.6rem; line-height: 1.05; font-weight: 500;
  letter-spacing: -.035em; color: var(--gh-ink); padding: 0; }}
.gh-head p {{ margin: 0; font-size: .98rem; line-height: 1.5; color: var(--gh-text); max-width: 25rem; }}
.gh-hero {{ display: flex; flex-direction: column; align-items: center; text-align: center; }}
.gh-hero-art {{ width: 214px; height: auto; display: block;
  filter: drop-shadow(0 22px 30px {"rgba(56,189,248,.18)" if dark else "rgba(59,130,246,.16)"}); }}
.gh-slug {{ margin: 8px 0 12px; font-size: 1.32rem; font-weight: 600; letter-spacing: -.015em;
  color: var(--gh-ink); word-break: break-word; }}
.gh-actions {{ display: flex; align-items: center; justify-content: center; gap: 10px; }}
.gh-btn {{ display: inline-flex; align-items: center; gap: 6px; height: 38px; padding: 0 18px;
  border-radius: 12px; border: 1.5px solid color-mix(in srgb, var(--gh-accent) 55%, transparent);
  background: var(--gh-btn-bg); color: var(--gh-accent) !important; text-decoration: none !important;
  font-weight: 500; font-size: .95rem; letter-spacing: -.005em;
  box-shadow: 0 1px 2px rgba(15,40,90,.06), inset 0 1px 0 rgba(255,255,255,{".06" if dark else "1"});
  transition: transform .15s ease, box-shadow .15s ease, background .15s ease; }}
.gh-btn:hover {{ transform: translateY(-1px); background: color-mix(in srgb, var(--gh-accent) 9%, var(--gh-btn-bg));
  box-shadow: 0 8px 18px -8px color-mix(in srgb, var(--gh-accent) 60%, transparent); }}
.gh-btn-main {{ height: 42px; padding: 0 22px; font-size: 1rem; }}
.gh-arrow {{ width: 12px; height: 12px; fill: none; stroke: currentColor; stroke-width: 1.8;
  stroke-linecap: round; stroke-linejoin: round; }}
.gh-copy {{ position: relative; width: 38px; height: 38px; border-radius: 11px; border: 1px solid transparent;
  background: transparent; color: var(--gh-ink); cursor: pointer; display: inline-grid; place-items: center;
  padding: 0; transition: background .15s ease, border-color .15s ease; }}
.gh-copy:hover {{ background: color-mix(in srgb, var(--gh-ink) 6%, transparent); border-color: var(--gh-border); }}
.gh-copy svg {{ width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 1.7;
  stroke-linecap: round; stroke-linejoin: round; grid-area: 1 / 1; transition: opacity .2s ease, transform .2s ease; }}
.gh-copy .gh-ico-check {{ opacity: 0; transform: scale(.6); stroke: var(--gh-auto); stroke-width: 2.4; }}
.gh-copy.is-copied .gh-ico-copy {{ opacity: 0; transform: scale(.6); }}
.gh-copy.is-copied .gh-ico-check {{ opacity: 1; transform: scale(1); }}
.gh-copy:focus-visible, .gh-btn:focus-visible {{ outline: 2px solid var(--gh-accent); outline-offset: 2px; }}
/* Tree: stem from the repository, one arm to each side branch. */
.gh-tree {{ margin-top: 4px; }}
.gh-trunk {{ position: relative; height: 56px; margin: 0 16.667%; }}
.gh-trunk::before {{ content: ""; position: absolute; left: 50%; top: 0; bottom: 0; width: 1.5px;
  transform: translateX(-50%); background: linear-gradient(var(--gh-trace), var(--gh-trace)); opacity: {line_alpha}; }}
.gh-arm {{ position: absolute; top: 22px; bottom: 0; width: 50%; opacity: {line_alpha}; }}
.gh-arm-left {{ left: 0; border-top: 1.5px solid var(--gh-auto); border-left: 1.5px solid var(--gh-auto);
  border-radius: 18px 0 0 0; }}
.gh-arm-right {{ right: 0; border-top: 1.5px solid var(--gh-docs); border-right: 1.5px solid var(--gh-docs);
  border-radius: 0 18px 0 0; }}
.gh-arm-left::after, .gh-arm-right::after {{ content: ""; position: absolute; top: -1.5px; width: 22px;
  height: 1.5px; }}
.gh-groups {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; }}
.gh-group {{ --c: var(--gh-trace); display: flex; flex-direction: column; align-items: center; min-width: 0; }}
.gh-group[data-cat="auto"] {{ --c: var(--gh-auto); }}
.gh-group[data-cat="docs"] {{ --c: var(--gh-docs); }}
.gh-dot {{ width: 9px; height: 9px; border-radius: 50%; background: var(--c);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--c) 22%, transparent), 0 0 10px color-mix(in srgb, var(--c) 60%, transparent); }}
.gh-pill {{ margin: 8px 0 0; padding: 8px 20px; border-radius: 999px; font-size: .8rem; font-weight: 600;
  letter-spacing: .06em; text-transform: uppercase;
  color: color-mix(in srgb, var(--c) {"88%, white" if dark else "78%, black"});
  background: color-mix(in srgb, var(--c) {"16%" if dark else "13%"}, transparent);
  border: 1px solid color-mix(in srgb, var(--c) 22%, transparent);
  box-shadow: inset 0 1px 0 rgba(255,255,255,{".08" if dark else ".7"}); }}
.gh-branch {{ position: relative; width: 100%; height: 40px; }}
.gh-branch::before {{ content: ""; position: absolute; left: 50%; top: 0; height: 100%; width: 1.5px;
  transform: translateX(-50%); background: var(--c); opacity: {line_alpha}; }}
.gh-branch.gh-split::before {{ height: 14px; }}
.gh-branch.gh-split::after {{ content: ""; position: absolute; left: 25%; right: 25%; top: 14px; bottom: 0;
  border: 1.5px solid var(--c); border-bottom: 0; border-radius: 14px 14px 0 0; opacity: {line_alpha}; }}
.gh-items {{ display: grid; grid-template-columns: repeat(var(--n), 1fr); width: 100%; }}
.gh-item {{ display: flex; flex-direction: column; align-items: center; text-align: center; padding: 0 8px; min-width: 0; }}
.gh-item > .gh-dot {{ margin-top: -4.5px; }}
.gh-tile {{ position: relative; width: 104px; height: 104px; margin: 14px 0 16px; border-radius: 28px;
  display: grid; place-items: center;
  background: linear-gradient(160deg, {tile_top} 0%, {tile_bottom} 100%);
  box-shadow: {tile_shadow}, inset 0 1.5px 0 {tile_edge}, inset 0 -3px 8px rgba(0,0,0,{".35" if dark else ".05"});
  transition: transform .2s ease; }}
.gh-tile::before {{ content: ""; position: absolute; inset: 1px 1px 52% 1px; border-radius: 27px 27px 40% 40% / 27px 27px 18px 18px;
  background: linear-gradient(rgba(255,255,255,{".10" if dark else ".85"}), rgba(255,255,255,0)); pointer-events: none; }}
.gh-tile::after {{ content: ""; position: absolute; inset: -10px; border-radius: 34px; z-index: -1;
  background: radial-gradient(closest-side, color-mix(in srgb, var(--c) {"30%" if dark else "22%"}, transparent), transparent);
  filter: blur(10px); }}
.gh-item:hover .gh-tile {{ transform: translateY(-3px); }}
.gh-glyph {{ position: relative; width: 74px; height: 74px; }}
.gh-item h3 {{ margin: 0 0 4px; padding: 0; font-size: 1.08rem; font-weight: 600; letter-spacing: -.015em;
  color: var(--gh-ink); line-height: 1.25; }}
.gh-item p {{ margin: 0 0 14px; font-size: .9rem; line-height: 1.4; color: var(--gh-text); max-width: 13.5rem;
  min-height: 2.8em; }}
.gh-item .gh-btn {{ height: 36px; padding: 0 18px; }}
/* The buttons share one baseline even when a title wraps onto two lines. */
@media (min-width: 761px) {{
  .gh-item h3 {{ min-height: 2.5em; display: flex; align-items: flex-start; justify-content: center; }}
  .gh-item p {{ min-height: 2.9em; }}
}}
@media (max-width: 760px) {{
  .gh-top {{ grid-template-columns: 1fr; gap: 10px; }}
  .gh-head h1 {{ margin-top: 8px; font-size: 2.2rem; }}
  .gh-top > .gh-spacer {{ display: none; }}
  .gh-hero-art {{ width: 176px; }}
  .gh-slug {{ font-size: 1.08rem; }}
  .gh-trunk {{ display: none; }}
  .gh-groups {{ grid-template-columns: 1fr; gap: 26px; margin-top: 22px; }}
  .gh-group > .gh-dot, .gh-branch {{ display: none; }}
  .gh-pill {{ margin: 0 0 12px; }}
  .gh-items {{ grid-template-columns: 1fr; gap: 12px; }}
  .gh-item {{ display: grid; grid-template-columns: 72px 1fr; grid-template-areas: "tile title" "tile text" "tile act";
    column-gap: 14px; text-align: left; align-items: center; padding: 14px; border-radius: 20px;
    background: color-mix(in srgb, {palette["card"]} {"70%" if dark else "75%"}, transparent);
    border: 1px solid color-mix(in srgb, var(--gh-border) 70%, transparent); }}
  .gh-item > .gh-dot {{ display: none; }}
  .gh-tile {{ grid-area: tile; width: 72px; height: 72px; margin: 0; border-radius: 20px; }}
  .gh-tile::before {{ border-radius: 19px 19px 40% 40% / 19px 19px 12px 12px; }}
  .gh-glyph {{ width: 52px; height: 52px; }}
  .gh-item h3 {{ grid-area: title; font-size: 1rem; }}
  .gh-item p {{ grid-area: text; margin: 0 0 8px; min-height: 0; max-width: none; font-size: .86rem; }}
  .gh-item .gh-actions {{ grid-area: act; justify-content: flex-start; }}
  .gh-item .gh-btn {{ height: 32px; padding: 0 14px; font-size: .88rem; }}
  .gh-item .gh-copy {{ width: 32px; height: 32px; }}
}}
</style>"""


def _actions(url, label, main=False):
    safe = html.escape(url, quote=True)
    css = "gh-btn gh-btn-main" if main else "gh-btn"
    return (
        f'<div class="gh-actions"><a class="{css}" href="{safe}" target="_blank" '
        f'rel="noopener noreferrer">{html.escape(label)} {ARROW}</a>'
        f'<button type="button" class="gh-copy" data-copy="{safe}" '
        f'aria-label="Copiar enlace" title="Copiar enlace">{COPY_ICON}</button></div>'
    )


def _item_html(item, dark):
    return (
        f'<div class="gh-item"><span class="gh-dot"></span>'
        f'<div class="gh-tile">{build_glyph_svg(item["icon"], dark)}</div>'
        f'<h3>{html.escape(item["title"])}</h3><p>{html.escape(item["text"])}</p>'
        f'{_actions(item["url"], "Abrir")}</div>'
    )


def build_github_page_html(mode):
    """The whole page: header, the repository hero and the tree of its links."""
    palette = charts.get_palette(mode)
    dark = palette["base"] == charts.BASE_DARK
    items = page_items()
    groups = []
    for category in CATEGORIES:
        members = [item for item in items if item["category"] == category["key"]]
        if not members:
            continue
        branch = "gh-branch gh-split" if len(members) > 1 else "gh-branch"
        groups.append(
            f'<div class="gh-group" data-cat="{category["key"]}"><span class="gh-dot"></span>'
            f'<div class="gh-pill">{html.escape(category["label"])}</div><div class="{branch}"></div>'
            f'<div class="gh-items" style="--n:{len(members)}">'
            + "".join(_item_html(item, dark) for item in members)
            + '</div></div>'
        )
    return (
        f'{_style(palette)}<section class="gh-page">'
        '<div class="gh-top"><header class="gh-head"><h1>GitHub</h1>'
        '<p>Código, automatización, trazabilidad y documentación en un solo lugar.</p></header>'
        f'<div class="gh-hero">{build_hero_svg(palette)}'
        f'<div class="gh-slug">{html.escape(REPO_SLUG)}</div>'
        f'{_actions(project.GITHUB_URL, "Abrir repositorio", main=True)}</div>'
        '<div class="gh-spacer"></div></div>'
        '<div class="gh-tree"><div class="gh-trunk"><span class="gh-arm gh-arm-left"></span>'
        '<span class="gh-arm gh-arm-right"></span></div>'
        f'<div class="gh-groups">{"".join(groups)}</div></div></section>'
    )


# One listener for the whole page (a page drawn twice does not copy twice). The DOM is
# touched only through JS APIs: st.html drops a script that holds markup-like strings.
GITHUB_PAGE_SCRIPT = """<script>
if (!window.ghPageCopyReady) {
    window.ghPageCopyReady = true;
    document.addEventListener("click", (event) => {
        const button = event.target.closest(".gh-copy");
        if (!button) { return; }
        const url = button.getAttribute("data-copy");
        const done = () => {
            button.classList.add("is-copied");
            button.setAttribute("title", "Copiado");
            clearTimeout(button.ghTimer);
            button.ghTimer = setTimeout(() => {
                button.classList.remove("is-copied");
                button.setAttribute("title", "Copiar enlace");
            }, 1500);
        };
        const copyWithField = () => {
            const field = document.createElement("textarea");
            field.value = url;
            field.style.position = "fixed";
            field.style.opacity = "0";
            document.body.appendChild(field);
            field.select();
            const copied = document.execCommand("copy");
            field.remove();
            if (copied) { done(); }
        };
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(done, copyWithField);
        } else {
            copyWithField();
        }
    });
}
</script>"""
