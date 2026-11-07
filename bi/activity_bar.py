"""The activity bar of the menu (D-539, D-540): line icons in one tone, like VS Code's, and the stack of each area.

Each area of the project has an icon in the bar that opens the names of the tools and engineering concepts it uses,
in order of relevance, with no explanation: a list to show the stack and to study it. Every name is used in this
repository (D-540 lists where).
"""

import html

from bi.i18n import tr

# region Constants
# Line icons on a 24 px grid. The bar paints them through a CSS mask, so one shape takes the tone of each theme and
# brightens on hover or when its page is open.
ICONS = {
    "documents": (
        '<path d="M14 3H8.5A1.5 1.5 0 0 0 7 4.5v12A1.5 1.5 0 0 0 8.5 18h9a1.5 1.5 0 0 0 1.5-1.5V8z"/>'
        '<path d="M14 3v5h5"/><path d="M4 7.5v12A1.5 1.5 0 0 0 5.5 21H15"/>'
    ),
    "study": (
        '<path d="M9 3h6"/><path d="M10 3v6.2L4.6 18.4A1.7 1.7 0 0 0 6 21h12a1.7 1.7 0 0 0 1.4-2.6L14 9.2V3"/>'
        '<path d="M7.2 15h9.6"/>'
    ),
    "sources": (
        '<ellipse cx="12" cy="5.5" rx="7" ry="2.5"/><path d="M5 5.5v13c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-13"/>'
        '<path d="M5 12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5"/>'
    ),
    "code": '<path d="M8 7l-5 5 5 5"/><path d="M16 7l5 5-5 5"/><path d="M13.5 4.5l-3 15"/>',
    "data": (
        '<circle cx="5" cy="6" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="12" r="2"/>'
        '<path d="M7 6h3.5a3 3 0 0 1 3 3 3 3 0 0 0 3 3H17"/><path d="M7 18h3.5a3 3 0 0 0 3-3 3 3 0 0 1 3-3"/>'
    ),
    "quality": '<path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
    "devops": (
        '<path d="M7.5 8.5C5 8.5 3 10 3 12s2 3.5 4.5 3.5c3.5 0 5.5-7 9-7 2.5 0 4.5 1.5 4.5 3.5s-2 3.5-4.5 3.5'
        'c-3.5 0-5.5-7-9-7z"/>'
    ),
    "business": '<path d="M4 20h16"/><path d="M7 20v-6"/><path d="M12 20V8"/><path d="M17 20v-10"/>',
}

# (key, title, icon, names): the five areas, in the order of the bar; each list from the most to the least relevant.
STACK_AREAS = [
    (
        "code",
        "Stack · Código",
        "code",
        ["Python", "SQL", "pandas", "Git", "Jupyter", "requests", "Markdown"],
    ),
    (
        "data",
        "Stack · Ingeniería de datos",
        "data",
        [
            "ETL",
            "DuckDB",
            "dbt Core",
            "Staging · intermedio · marts",
            "Data warehouse",
            "Modelo estrella: hechos y dimensiones",
            "Parquet",
            "PyArrow",
            "SQLite",
            "Ingesta de datos",
            "Capa de aterrizaje y capa bronce",
            "Linaje de datos",
            "Normalización de unidades",
            "Carga semanal por lotes",
        ],
    ),
    (
        "quality",
        "Stack · Calidad",
        "quality",
        [
            "Pruebas de datos de dbt",
            "pytest",
            "Pruebas que recalculan las cifras",
            "Cobertura de código",
            "Ruff",
            "mypy",
            "Detección de atípicos",
            "AppTest de Streamlit",
            "Playwright",
            "Plan de calidad (SQAP)",
            "Plan de pruebas",
            "Registro de fallas y no conformidades",
        ],
    ),
    (
        "devops",
        "Stack · DevOps y seguridad",
        "devops",
        [
            "GitHub Actions",
            "CI/CD",
            "Cron",
            "GitHub",
            "Conventional Commits",
            "GitHub Releases",
            "Gestión de secretos",
            "Mínimo privilegio",
            "Bandit",
            "pip-audit",
            "detect-secrets",
            "OWASP",
            "Huella SHA-256",
            "Streamlit Community Cloud",
            "Dev Container",
        ],
    ),
    (
        "business",
        "Stack · Negocio · BA y BI",
        "business",
        [
            "Streamlit",
            "Dashboards",
            "KPI",
            "Altair",
            "Precios reales con el IPC",
            "Alertas de precio",
            "Requisitos del producto (PRD)",
            "Interesados",
            "Reglas de negocio",
            "Decisiones de arquitectura (ADR)",
            "Arquitectura de software (SAD)",
            "Excel y CSV",
        ],
    ),
]
# endregion


# region The activity bar of the menu
def build_icon_svg(name):
    """One icon as an SVG file, for the CSS mask of its button."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )


def build_stack_html(title, names):
    """The window of one area: its title and its names, numbered in order of relevance."""
    items = "".join(f"<li>{html.escape(tr(name))}</li>" for name in names)
    return f'<div class="stack-list"><p class="stack-title">{html.escape(tr(title))}</p><ol>{items}</ol></div>'


# endregion
