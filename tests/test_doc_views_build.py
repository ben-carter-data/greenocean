"""Every view of doc_views a document can embed is built in both bases of the palette (D-323)."""

import pytest

from bi import charts, doc_views


@pytest.mark.parametrize("name", list(doc_views.VIEWS))
@pytest.mark.parametrize("mode", [charts.THEMES[0], charts.THEMES[1]])
def test_d323_each_document_view_is_a_whole_page_with_its_nodes(name, mode):
    builder, height = doc_views.VIEWS[name]
    page = builder(mode)
    assert page.startswith("<!doctype html>") and page.rstrip().endswith("</html>") and height > 0
    assert page.count("<div") == page.count("</div>")  # every block closes
