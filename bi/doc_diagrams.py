"""The diagrams of the project documents, by the name of their [[diagrama:…]] marker.

D-205: the document views are drawn in the pipeline's own visual language (bi/doc_views.py):
actors and use cases, real screens of the panel (mockups), C4 context and containers and the
Tuesday sequence. The live panel diagrams (platform, pipeline, star model, security map) are
drawn by the dashboard itself, so a document and its page never disagree.
"""
from bi import doc_views

# Marker → function(mode) returning one HTML document for st.iframe.
DOC_DIAGRAMS = {name: builder for name, (builder, _) in doc_views.VIEWS.items()}
# Marker → height of its frame in the page, in pixels.
HEIGHTS = {name: height for name, (_, height) in doc_views.VIEWS.items()}
# Markers that reuse a live panel diagram (drawn by the dashboard, not here).
LIVE_DIAGRAMS = ("plataforma", "pipeline", "modelo", "seguridad")
