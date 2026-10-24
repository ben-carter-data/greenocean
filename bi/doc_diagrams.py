"""The diagrams of the project documents, by the name of their [[diagrama:…]] marker.

The document views are drawn in the pipeline's own visual language (bi/doc_views.py): the system context and its
containers (SAD), the use cases and the real screens of the panel (PRD) and, in the Plan de pruebas de seguridad, the procedure as a cycle and the ten cases around the lock (bi/security_plan.py). A view that lives in a page of the panel is linked with [[vista:…]] instead of copied (D-247).
"""
from bi import doc_views, security_plan

# Marker → function(mode) returning one HTML document for st.iframe.
DOC_DIAGRAMS = {name: builder for name, (builder, _) in doc_views.VIEWS.items()}
DOC_DIAGRAMS.update(sop=security_plan.build_cycle_html, pruebas=security_plan.build_cases_html)
# Marker → height of its frame in the page, in pixels.
HEIGHTS = {name: height for name, (_, height) in doc_views.VIEWS.items()}
HEIGHTS.update(sop=440, pruebas=600)
