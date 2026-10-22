"""The views that work must stay on their page (D-230).

D-226 replaced the star model and the entity-relation diagram with a generic summary and
nobody noticed, because no test asked a page for its own diagram. These tests draw each
page and fail if the SVG of its builder is not there.
"""
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from bi import dashboard  # noqa: E402
from tests.test_dashboard import draw_page, needs_database  # noqa: E402

# aria-label of the SVG that each builder returns.
STAR_LABEL = 'aria-label="Modelo estrella de datos.duckdb"'
ER_LABEL = 'aria-label="Modelo entidad-relación de datos.duckdb"'
JOURNEY_LABEL = 'aria-label="Recorrido de los datos de ODEPA al panel"'


# A diagram inside one of these is hidden behind a click: that is how D-226 lost it.
HIDING_CONTAINERS = {"popover", "expander", "dialog"}


def read_markdown(app):
    return " ".join(block.value for block in app.markdown)


def find_open_markdown(node, label, ancestors=()):
    """The markdown elements holding `label` that the reader sees without clicking."""
    found = []
    if getattr(node, "type", None) == "markdown" and label in node.value \
            and not HIDING_CONTAINERS & set(ancestors):
        found.append(node)
    for child in getattr(node, "children", {}).values():
        found += find_open_markdown(child, label, ancestors + (getattr(node, "type", None),))
    return found


@needs_database
def test_d230_the_star_model_page_draws_the_star_svg():
    app = draw_page(dashboard.PAGE_ARCHITECTURE, state={dashboard.MODEL_VIEW_KEY: dashboard.MODEL_VIEWS[1]})
    assert not app.exception
    page = read_markdown(app)
    assert find_open_markdown(app.main, STAR_LABEL), "the star SVG is not open on its page"
    assert ER_LABEL not in page
    # The fact table in the middle and its dimensions around it.
    for table in ("weekly_price", "dim_product", "dim_region", "dim_channel", "dim_date"):
        assert table in page


@needs_database
def test_d230_the_entity_relation_page_draws_the_er_svg():
    app = draw_page(dashboard.PAGE_ARCHITECTURE, state={dashboard.MODEL_VIEW_KEY: dashboard.MODEL_VIEWS[2]})
    assert not app.exception
    assert find_open_markdown(app.main, ER_LABEL), "the ER SVG is not open on its page"
    assert STAR_LABEL not in read_markdown(app)


@needs_database
def test_d230_the_pipeline_page_draws_the_journey_svg():
    app = draw_page(dashboard.PAGE_DIAGRAMS)
    assert not app.exception
    assert find_open_markdown(app.main, JOURNEY_LABEL), "the pipeline SVG is not open on its page"

