"""The diagrams of the project documents, by the name of their [[diagrama:…]] marker.

The document views are drawn in the pipeline's own visual language (bi/doc_views.py): the system context and its
containers (SAD), the use cases and the real screens of the panel (PRD) and, in the Plan de pruebas y seguridad, the procedure as a cycle and the fourteen cases around the lock (bi/security_plan.py). A view that lives in a page of the panel is linked with [[vista:…]] instead of copied (D-247).
"""

from bi import doc_figures, doc_views, security_plan

# D-280: Chrome prints a blurred shadow as a grey rectangle; on paper the diagrams have no shadows or filters.
PRINT_STYLE = (
    "<style>@media print { *, *::before, *::after { box-shadow:none !important; filter:none !important; } }</style>"
)


def for_print(builder):
    return lambda mode: builder(mode).replace("</head>", PRINT_STYLE + "</head>", 1)


# Marker → function(mode) returning one HTML document for st.iframe.
DOC_DIAGRAMS = {name: for_print(builder) for name, (builder, _) in doc_views.VIEWS.items()}
DOC_DIAGRAMS.update(pruebas=for_print(security_plan.build_cases_html))
# Marker → height of its frame in the page, in pixels.
HEIGHTS = {name: height for name, (_, height) in doc_views.VIEWS.items()}
HEIGHTS.update(pruebas=620)
# D-289: the figures of every document; each frame takes the height of its figure.
DOC_DIAGRAMS.update({name: for_print(builder) for name, builder in doc_figures.FIGURES.items()})
HEIGHTS.update({name: "content" for name in doc_figures.FIGURES})
