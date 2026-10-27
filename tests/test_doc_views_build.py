"""Every view a document can embed is built in both bases of the palette (D-323): the context and container views of
the SAD among them, which the documents draw with the [[diagrama:…]] markers."""

import pytest

from bi import charts, doc_views


@pytest.mark.parametrize("name", list(doc_views.VIEWS))
@pytest.mark.parametrize("mode", [charts.THEMES[0], charts.THEMES[1]])
def test_d323_each_document_view_is_a_whole_page_with_its_nodes(name, mode):
    builder, height = doc_views.VIEWS[name]
    page = builder(mode)
    assert page.startswith("<!doctype html>") and page.rstrip().endswith("</html>") and height > 0
    assert page.count("<div") == page.count("</div>")  # every block closes


def test_d323_a_tip_opens_away_from_the_edges_it_is_near():
    near_left = doc_views.tip_html(0, 0, [("Qué es", "algo")])
    near_right_bottom = doc_views.tip_html(doc_views.WIDTH, doc_views.HEIGHT, [("Qué es", "algo")])
    assert 'class="tip start"' in near_left and 'class="tip end up"' in near_right_bottom
