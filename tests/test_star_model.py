"""Tests for the star model drawn as a star, and for the zoomable frames (T-59)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts, project, star_model, zoom  # noqa: E402

COLUMNS = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
ROW_COUNTS = {"weekly_price": 811578, "dim_product": 1609, "dim_region": 9,
              "dim_channel": 8, "etl_run": 3, "rejection": 201}
PANELS = [("weekly_price", "weekly_price · tabla de hechos", "El centro", "JOIN x", "811.578"),
          ("week", "Semana", "La semana", "GROUP BY week_start", "249 semanas"),
          ("dim_product", "dim_product", "Productos", "JOIN dim_product", "1.609 filas")]


def test_t59_schema_columns_come_from_schema_sql_with_their_keys():
    assert COLUMNS["dim_product"][0] == ("product_id", "PK")
    assert ("region_id", "FK") in COLUMNS["weekly_price"]
    assert ("price", "") in COLUMNS["weekly_price"]
    assert all(name != "UNIQUE" for columns in COLUMNS.values() for name, _ in columns)


def test_t59_star_draws_every_real_column_keys_and_measures_apart():
    svg = star_model.build_star_svg(COLUMNS, ROW_COUNTS, charts.MODE_DARK)
    for table in ["weekly_price", "dim_product", "dim_region", "dim_channel"]:
        for name, _ in COLUMNS[table]:
            assert name in svg
    for text in ["product_id (PK)", "product_id (FK)", "Semana", "mejora: dim_date",
                 "811.578 filas", "<polygon"]:
        assert text in svg
    attributes, measures = star_model.list_fact_lines(COLUMNS["weekly_price"])
    assert [name for name, _ in measures] == star_model.MEASURES
    assert [kind for _, kind in attributes][:3] == ["FK", "FK", "FK"]
    # Vantablack: black cards and cyan borders.
    assert 'fill="#000000" stroke="#22d3ee"' in svg


def test_t59_each_table_can_be_touched_and_chooses_its_panel():
    page = star_model.build_star_model_html(COLUMNS, ROW_COUNTS, PANELS, "nota",
                                            charts.MODE_LIGHT)
    for table in star_model.CARDS:
        assert f'class="star-table star-{table}" tabindex="0"' in page
        assert f".star-model:has(.star-{table}:focus) .star-panel-{table}" in page
    assert 'class="star-panel star-panel-dim_product"' in page
    assert "<script" not in page
    assert 'class="zoom-frame ' in page


def test_t59_text_from_the_data_is_escaped_in_the_panel():
    panels = [("weekly_price", "<b>t</b>", "texto", "JOIN", "1 fila")]
    page = star_model.build_star_model_html(COLUMNS, ROW_COUNTS, panels, "nota",
                                            charts.MODE_DARK)
    assert "<b>t</b>" not in page and "&lt;b&gt;t&lt;/b&gt;" in page


def test_t59_zoom_frame_wraps_the_diagram_and_the_script_runs_once():
    frame = zoom.build_zoom_frame_html("<svg></svg>", "diagram-wide")
    assert frame.startswith('<div class="zoom-frame diagram-wide"><div class="zoom-viewport">')
    assert '<div class="zoom-content"><svg></svg></div>' in frame
    assert "window.diagramZoomReady" in zoom.ZOOM_SCRIPT
    for text in ["＋", "－", "⟲", "pointermove", "MutationObserver"]:
        assert text in zoom.ZOOM_SCRIPT
