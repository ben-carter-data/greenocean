"""The diagrams of the project documents, by the name of their [[diagrama:…]] marker.

The document views are drawn in the pipeline's own visual language (bi/doc_views.py): the system context and its
containers (SAD), the use cases and the real screens of the panel (PRD) and the security test procedure (Plan de pruebas
de seguridad). A view that lives in a page of the panel is linked with [[vista:…]] instead of copied (D-247).
"""
from bi import doc_views

# Marker → function(mode) returning one HTML document for st.iframe.
DOC_DIAGRAMS = {name: builder for name, (builder, _) in doc_views.VIEWS.items()}
# Marker → height of its frame in the page, in pixels.
HEIGHTS = {name: height for name, (_, height) in doc_views.VIEWS.items()}
