"""The global stylesheets of the panel (D-541): the theme, the app's own CSS, the code colors and the menu with its
activity bar. Streamlit has no stylesheet file of its own, so each function writes the CSS of the chosen theme and the
panel injects it; the page stylesheets stay with their pages.
"""

import base64

from bi import activity_bar, charts, static_files, zoom

# region Constants
# Code colors for the light themes: Streamlit's own steps fall under 3:1 on white,
# so each kind of token takes a darker step of its hue (4.5:1 or more).
LIGHT_CODE_COLORS = {
    "string": "#15803d",
    "boolean": "#15803d",
    "number": "#0f766e",
    "operator": "#c2410c",
    "keyword": "#1d4ed8",
    "function": "#1d4ed8",
    "comment": "#57606a",
    "punctuation": "#57606a",
}


# (text, heading, icon, hover fill, current fill, accent bar, hairline) for dark and light sidebars.
MENU_INK = {
    True: (
        "#cfd4dc",
        "#8b929c",
        "#aeb5bf",
        "rgba(255,255,255,.04)",
        "rgba(255,255,255,.07)",
        "#3b9eff",
        "rgba(255,255,255,.08)",
    ),
    False: (
        "#2b3340",
        "#596069",  # D-323: 4.5:1 on the lightest sidebar (Blue Light)
        "#4b5563",
        "rgba(15,23,42,.04)",
        "rgba(15,23,42,.07)",
        "#1d5fbf",
        "rgba(15,23,42,.09)",
    ),
}


ACTIVITY_BAR = 40  # D-539: the width of the column of icons on the menu's left edge, like VS Code's activity bar


# A dashboard in miniature: three figures over a bar chart and a line, in the colours of the charts.
DASHBOARD_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 46"><rect x="1" y="1" width="62" height="44" rx="6" '
    'fill="#1d3557" stroke="#5aa9ea" stroke-width="1.5"/><rect x="6" y="6" width="15" height="8" rx="2" fill="#5aa9ea"/>'
    '<rect x="24.5" y="6" width="15" height="8" rx="2" fill="#5fd39b"/><rect x="43" y="6" width="15" height="8" rx="2" '
    'fill="#f0b347"/><rect x="7" y="31" width="5" height="9" rx="1" fill="#8ac6f5"/><rect x="15" y="26" width="5" '
    'height="14" rx="1" fill="#8ac6f5"/><rect x="23" y="21" width="5" height="19" rx="1" fill="#8ac6f5"/>'
    '<path d="M34 37l7-8 6 4 11-12" fill="none" stroke="#5fd39b" stroke-width="2.4" stroke-linecap="round" '
    'stroke-linejoin="round"/></svg>'
)


# D-452: the same dashboard, split in two sources side by side, each with its own latest week.
CHANNELS_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 46"><rect x="1" y="1" width="62" height="44" rx="6" '
    'fill="#1d3557" stroke="#5aa9ea" stroke-width="1.5"/><path d="M32 6v34" stroke="#5aa9ea" stroke-width="1.2" '
    'stroke-dasharray="2 2"/><rect x="6" y="6" width="21" height="7" rx="2" fill="#5fd39b"/><rect x="37" y="6" '
    'width="21" height="7" rx="2" fill="#f0b347"/><rect x="8" y="27" width="5" height="13" rx="1" fill="#8ac6f5"/>'
    '<rect x="16" y="21" width="5" height="19" rx="1" fill="#8ac6f5"/><rect x="39" y="24" width="5" height="16" rx="1" '
    'fill="#8ac6f5"/><rect x="47" y="18" width="5" height="22" rx="1" fill="#8ac6f5"/></svg>'
)


# D-456: «Análisis»: a report with a line over bars and a magnifier, the history read closely.
BA_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 46"><rect x="1" y="1" width="62" height="44" rx="6" '
    'fill="#1d3557" stroke="#5aa9ea" stroke-width="1.5"/><rect x="7" y="27" width="5" height="12" rx="1" fill="#8ac6f5"/>'
    '<rect x="15" y="21" width="5" height="18" rx="1" fill="#8ac6f5"/><rect x="23" y="24" width="5" height="15" rx="1" '
    'fill="#8ac6f5"/><path d="M7 19l9-7 8 5 10-9" fill="none" stroke="#f0b347" stroke-width="2.4" stroke-linecap="round" '
    'stroke-linejoin="round"/><circle cx="46" cy="25" r="9" fill="#1d3557" stroke="#5fd39b" stroke-width="3"/>'
    '<path d="M52.5 31.5l6 6" stroke="#5fd39b" stroke-width="3.4" stroke-linecap="round"/></svg>'
)


SOURCES_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 50"><ellipse cx="28" cy="10" rx="20" ry="6" '
    'fill="#5fd39b"/><path d="M8 10v28c0 3.3 9 6 20 6s20-2.7 20-6V10c0 3.3-9 6-20 6S8 13.3 8 10z" '
    'fill="#2fb57a"/><path d="M8 24c0 3.3 9 6 20 6s20-2.7 20-6" fill="none" stroke="#5fd39b" stroke-width="2"/>'
    '<circle cx="50" cy="38" r="10" fill="#1f8f5f"/><path d="M46 42l8-8M49 34h5v5" fill="none" stroke="#fff" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


# A Finder-like folder, two blues, drawn once as an image the menu shows above «Documentos».
# D-533: the folder of the study of the source, in the green of its notebooks.
STUDY_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 50"><path d="M3 9a5 5 0 0 1 5-5h15.5'
    'a4 4 0 0 1 3 1.3L30 9h26a5 5 0 0 1 5 5v4H3z" fill="#22b35a"/><rect x="3" y="14" width="58" height="33" '
    'rx="5" fill="#5fd39b"/><rect x="3" y="14" width="58" height="3" fill="#8fe3b8"/></svg>'
)


FOLDER_TILE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 50"><path d="M3 9a5 5 0 0 1 5-5h15.5'
    'a4 4 0 0 1 3 1.3L30 9h26a5 5 0 0 1 5 5v4H3z" fill="#5aa9ea"/><rect x="3" y="14" width="58" height="33" '
    'rx="5" fill="#8ac6f5"/><rect x="3" y="14" width="58" height="3" fill="#a9d6f8"/></svg>'
)
# endregion


# region Colors
def is_dark_surface(color):
    """Whether a hex surface needs the luminous brand colors."""
    rgb = tuple(int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return sum(rgb) / 3 < 0.5


# endregion


# region App styles
def build_theme_css(palette):
    """Page, sidebar and links in the colors of the active theme (T-44, D-052).

    Streamlit's own widgets keep the colors of its base mode; the theme only
    restyles what it can do without fighting them.
    """
    return static_files.fill(
        "theme.css",
        {
            'var(--go-background)': palette["background"],
            'var(--go-text)': palette["text"],
            'var(--go-strong-text)': palette["strong_text"],
            'var(--go-card)': palette["card"],
            'var(--go-card-border)': palette["card_border"],
            'var(--go-field)': palette["field"],
            'var(--go-background-2)': palette['background'],
            'var(--go-sidebar)': palette["sidebar"],
            'var(--go-sidebar-text)': palette["sidebar_text"],
            'var(--go-accent)': palette["accent"],
            'var(--go-glow)': palette["glow"],
            'var(--go-on-accent)': palette["on_accent"],
        },
    )


def build_code_colors_css(palette):
    """Darker code tokens on the light themes; Vantablack keeps Streamlit's colors."""
    if palette["base"] != charts.BASE_LIGHT:
        return ""
    return "".join(
        static_files.fill("code_token.css", {"var(--go-token)": token, "var(--go-color)": color})
        for token, color in LIGHT_CODE_COLORS.items()
    )


def build_style_css(mode):
    """Cards, key figures, chips and tables, in the colors of the active theme."""
    palette = charts.get_palette(mode)
    return build_theme_css(palette) + static_files.fill(
        "app.css",
        {
            'var(--go-card)': palette["card"],
            'var(--go-card-border)': palette["card_border"],
            'var(--go-glow)': palette["glow"],
            'var(--go-reference)': palette["reference"],
            'var(--go-accent)': palette["accent"],
            'var(--go-text)': palette["text"],
            'var(--go-strong-text)': palette["strong_text"],
            'var(--go-charts-get-status-text-color-critical-mode)': charts.get_status_text_color("critical", mode),
            'var(--go-charts-get-status-text-color-good-mode)': charts.get_status_text_color("good", mode),
            'var(--go-rise)': palette["rise"],
            'var(--go-grid)': palette["grid"],
            'var(--go-sidebar-text)': palette["sidebar_text"],
            'var(--go-charts-get-status-text-color-running-mode)': charts.get_status_text_color("running", mode),
            'var(--go-fall)': palette["fall"],
            '/* insert: zoom-zoom-palette */': zoom.build_zoom_css(palette),
            'var(--go-background)': palette["background"],
            'var(--go-on-accent)': palette["on_accent"],
            '/* insert: code-colors-palette */': build_code_colors_css(palette),
            'var(--go-reference-2)': palette['reference'],
            'var(--go-accent-2)': palette['accent'],
            'var(--go-card-2)': palette['card'],
            'var(--go-card-border-2)': palette['card_border'],
            'var(--go-strong-text-2)': palette['strong_text'],
            'var(--go-text-2)': palette['text'],
            'var(--go-field)': palette["field"],
        },
    )


# endregion


# region Menu styles
def build_section_colors_css(dark):
    """The flat menu (D-231): sections divided by a hairline, rows with a thin icon; the current page has a faint fill
    and a blue bar on its left. D-501: the sizes of a side panel like those of VS Code or Apple: rows of 13 px and thin,
    grey section headings of 11 px in plain case, and a menu of 232 px."""
    text, heading, icon, hover, current, accent, line = MENU_INK[dark]
    return static_files.fill(
        "menu_sections.css",
        {
            'var(--go-line)': line,
            'var(--go-heading)': heading,
            'var(--go-text)': text,
            'var(--go-hover)': hover,
            'var(--go-icon)': icon,
            'var(--go-current)': current,
            'var(--go-accent)': accent,
        },
    )


def build_icon_mask(name):
    """D-540: one icon of the activity bar as a CSS mask image."""
    encoded = base64.b64encode(activity_bar.build_icon_svg(name).encode()).decode()
    return f'url("data:image/svg+xml;base64,{encoded}")'


def build_bar_icons_css(quiet, bright):
    """D-540: the icon of each button of the activity bar, as a CSS mask in one tone, like VS Code's."""

    buttons = {
        '[class*="st-key-nav_folder_tile_0"] [data-testid="stPageLink"] a': "documents",
        '[class*="st-key-nav_folder_tile_1"] [data-testid="stPageLink"] a': "study",
        ".st-key-sources_tile button": "sources",
    } | {f".st-key-stack_tile_{key} button": icon for key, _, icon, _ in activity_bar.STACK_AREAS}
    rules = [
        static_files.fill(
            "bar_icon.css",
            {"var(--go-button)": selector, "var(--go-quiet)": quiet, "var(--go-mask)": build_icon_mask(icon)},
        )
        for selector, icon in buttons.items()
    ]
    lit = ", ".join(selector + ":hover::before" for selector in buttons)
    rules.append(static_files.fill("bar_icon_lit.css", {"var(--go-lit)": lit, "var(--go-bright)": bright}))
    return "\n    ".join(rules)


def build_sidebar_css(mode):
    palette = charts.get_palette(mode)
    # The sidebar is flat (D-231): one plain surface, no gradient, border or shadow. Its text
    # follows that surface: Corporativo has a light page but a dark navy sidebar.
    dark = is_dark_surface(palette["sidebar"])
    text = MENU_INK[dark][0]
    hairline = MENU_INK[dark][6]
    quiet = "rgba(214, 218, 227, .68)" if dark else "rgba(31, 41, 55, .68)"
    # The price alert sits on the page, not in the sidebar (D-264): its red follows the page's surface.
    alert_text = "#ff9ca4" if is_dark_surface(palette["background"]) else "#9d1f2c"
    drop_text = "#6ee7a0" if is_dark_surface(palette["background"]) else "#15693a"
    view_ink = "#7dd3fc" if dark else palette["accent"]  # D-373: the view button reads on the sidebar's surface
    return static_files.style(
        "menu.css",
        {
            'var(--go-sidebar)': palette['sidebar'],
            'var(--go-232-activity-bar)': 232 + ACTIVITY_BAR,
            'var(--go-hairline)': hairline,
            'var(--go-activity-bar)': ACTIVITY_BAR,
            '/* insert: section-colors-dark */': build_section_colors_css(dark),
            'var(--go-accent)': palette['accent'],
            'var(--go-view-ink)': view_ink,
            'var(--go-text)': text,
            'var(--go-alert-text)': alert_text,
            'var(--go-drop-text)': drop_text,
            'var(--go-quiet)': quiet,
            'var(--go-menu-ink-6)': MENU_INK[dark][6],
            'var(--go-sources-tile-svg)': base64.b64encode(SOURCES_TILE_SVG.encode()).decode(),
            'var(--go-menu-ink-3)': MENU_INK[dark][3],
            'var(--go-folder-tile-svg)': base64.b64encode(FOLDER_TILE_SVG.encode()).decode(),
            'var(--go-menu-ink-4)': MENU_INK[dark][4],
            'var(--go-menu-ink-5)': MENU_INK[dark][5],
            'var(--go-study-tile-svg)': base64.b64encode(STUDY_TILE_SVG.encode()).decode(),
            'var(--go-channels-tile-svg)': base64.b64encode(CHANNELS_TILE_SVG.encode()).decode(),
            'var(--go-ba-tile-svg)': base64.b64encode(BA_TILE_SVG.encode()).decode(),
            'var(--go-dashboard-tile-svg)': base64.b64encode(DASHBOARD_TILE_SVG.encode()).decode(),
            'var(--go-activity-bar-8)': ACTIVITY_BAR + 8,
            'var(--go-activity-bar-16)': ACTIVITY_BAR + 16,
            '/* insert: bar-icons-quiet-text */': build_bar_icons_css(quiet, text),
        },
    )


# endregion


# region Shared page styles
def build_runs_css(mode):
    palette = charts.get_palette(mode)
    return static_files.style(
        "runs.css",
        {
            'var(--go-strong-text)': palette['strong_text'],
            'var(--go-text)': palette['text'],
            'var(--go-reference)': palette['reference'],
            'var(--go-card-border)': palette['card_border'],
            'var(--go-accent)': palette['accent'],
        },
    )


# endregion
