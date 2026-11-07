"""The diagrams of the project documents, by the name of their [[diagrama:…]] marker.

The document views are drawn in the pipeline's own visual language (bi/doc_views.py): the system context and its
containers (SAD), the use cases and the real screens of the panel (PRD) and, in the Plan de pruebas y seguridad, the procedure as a cycle and the fourteen cases around the lock (bi/security_plan.py). A view that lives in a page of the panel is linked with [[vista:…]] instead of copied (D-247).
"""

from bi import app_diagrams, doc_figures, doc_views, live_flow, security_plan

# region Constants
# D-280: Chrome prints a blurred shadow as a grey rectangle; on paper the diagrams have no shadows or filters.
PRINT_STYLE = (
    "<style>@media print { *, *::before, *::after { box-shadow:none !important; filter:none !important; } }</style>"
)
# endregion


# region Doc diagrams
def for_print(builder):
    return lambda mode: builder(mode).replace("</head>", PRINT_STYLE + "</head>", 1)


# Marker → function(mode) returning one HTML document for st.iframe.
DOC_DIAGRAMS = {name: for_print(builder) for name, (builder, _) in doc_views.VIEWS.items()}
DOC_DIAGRAMS.update(pruebas=for_print(security_plan.build_cases_html))
# Marker → height of its frame in the page, in pixels.
HEIGHTS = {name: height for name, (_, height) in doc_views.VIEWS.items()}
HEIGHTS.update(pruebas=620)
# D-414: the fixed picture of the live system flow (D-412), for the SAD.
DOC_DIAGRAMS.update(flujo=for_print(live_flow.build_document_html))
HEIGHTS.update(flujo="content")
# D-289: the figures of every document; each frame takes the height of its figure.
DOC_DIAGRAMS.update({name: for_print(builder) for name, builder in doc_figures.FIGURES.items()})
HEIGHTS.update({name: "content" for name in doc_figures.FIGURES})
# D-448: the SAD draws the panel's own data and deployment diagrams, from the same code, instead of copies.
DOC_DIAGRAMS.update(
    estrella=for_print(app_diagrams.build_star_html),
    entidad_relacion=for_print(app_diagrams.build_entity_relation_html),
    almacenamiento=for_print(app_diagrams.build_storage_html),
    cruces=for_print(app_diagrams.build_crossings_html),
    herramientas=for_print(app_diagrams.build_stack_html),
    despliegue=for_print(app_diagrams.build_deployment_html),
)
# D-455: and the other documents' diagrams that the panel already draws.
DOC_DIAGRAMS.update(
    recorrido=for_print(app_diagrams.build_journey_html),
    cicd=for_print(app_diagrams.build_cicd_html),
    monitoreo=for_print(app_diagrams.build_monitoring_html),
    seguridad=for_print(app_diagrams.build_security_html),
    calidad=for_print(app_diagrams.build_quality_html),
    git_workflow=for_print(app_diagrams.build_git_workflow_html),
)
HEIGHTS.update(
    recorrido="content",
    cicd="content",
    monitoreo="content",
    seguridad="content",
    calidad="content",
    git_workflow="content",
    estrella="content",
    entidad_relacion="content",
    almacenamiento=560,
    cruces=660,
    herramientas="content",
    despliegue="content",
)
# D-455: a diagram drawn inline in the document, not in a frame: the interest map's icons are letters of the panel's
# own icon font, which a frame does not have.
INLINE = {"interes": app_diagrams.build_interest_html}
# endregion
