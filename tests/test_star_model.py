"""Tests for the star model diagram: layout, cards and the audit trail (D-097)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts, project, star_model  # noqa: E402

COLUMNS = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
ROW_COUNTS = {"weekly_price": 811578, "dim_product": 1609, "dim_region": 9,
              "dim_channel": 8, "dim_date": 249, "etl_run": 4, "rejection": 201}
IPC_COUNTS = {"ine_ipc_source": 202, "ipc_monthly": 202, "ipc_weekly": 250}


def rect_overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def test_t59_schema_columns_come_from_schema_sql_with_their_keys():
    assert COLUMNS["dim_product"][0] == ("product_id", "PK")
    assert COLUMNS["dim_date"][0] == ("week_start", "PK")
    assert ("region_id", "FK") in COLUMNS["weekly_price"]
    assert ("price", "") in COLUMNS["weekly_price"]
    assert all(name != "UNIQUE" for columns in COLUMNS.values() for name, _ in columns)


def test_d097_layout_never_overlaps_whatever_the_column_counts():
    layout, height = star_model.compute_layout(COLUMNS)
    assert set(layout) == {"dim_date", "weekly_price", "dim_product", "dim_region", "dim_channel"}
    rects = list(layout.values())
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            assert not rect_overlap(a, b)
        x, y, w, h = a
        assert x >= 0 and y >= 0 and x + w <= star_model.WIDTH and y + h <= height
    # dim_date sits above weekly_price; dim_channel sits below it (D-097: a real
    # dimension, replacing the old dashed "week" placeholder).
    assert layout["dim_date"][1] + layout["dim_date"][3] < layout["weekly_price"][1]
    assert layout["weekly_price"][1] + layout["weekly_price"][3] < layout["dim_channel"][1]


def test_d097_layout_grows_with_more_columns_without_overlapping():
    wide_columns = dict(COLUMNS)
    wide_columns["dim_date"] = COLUMNS["dim_date"] + [("extra_one", ""), ("extra_two", ""),
                                                      ("extra_three", "")]
    layout, height = star_model.compute_layout(wide_columns)
    base_layout, base_height = star_model.compute_layout(COLUMNS)
    assert layout["dim_date"][3] > base_layout["dim_date"][3]
    assert height > base_height
    rects = list(layout.values())
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            assert not rect_overlap(a, b)


def test_t59_star_draws_every_real_column_keys_and_measures_apart():
    svg = star_model.build_star_svg(COLUMNS, ROW_COUNTS, charts.MODE_DARK)
    for table in ["weekly_price", "dim_product", "dim_region", "dim_channel", "dim_date"]:
        for name, _ in COLUMNS[table]:
            assert name in svg
    for text in ["product_id (PK)", "product_id (FK)", "week_start (PK)", "811.578 filas"]:
        assert text in svg
    attributes, measures = star_model.list_fact_lines(COLUMNS["weekly_price"])
    assert [name for name, _ in measures] == star_model.MEASURES
    assert [kind for _, kind in attributes][:3] == ["FK", "FK", "FK"]
    # Vantablack: black cards and cyan borders.
    assert 'fill="#000000"' in svg and 'stroke="#22d3ee"' in svg


def test_d097_the_selected_table_is_highlighted_and_others_are_not():
    svg = star_model.build_star_svg(COLUMNS, ROW_COUNTS, charts.MODE_DARK, selected="dim_product")
    assert 'class="star-table star-dim_product" filter=' in svg
    assert 'class="star-table star-dim_region" filter=' not in svg


def test_d097_no_zoom_controls_no_script_and_text_scales_with_its_container():
    svg = star_model.build_star_svg(COLUMNS, ROW_COUNTS, charts.MODE_LIGHT)
    assert "<script" not in svg
    assert "zoom" not in svg.lower()
    assert 'width="100%"' in svg
    assert svg.startswith('<svg xmlns=')


def test_d097_audit_trail_shows_etl_run_feeding_rejection_apart_from_the_star():
    svg = star_model.build_star_svg(COLUMNS, ROW_COUNTS, charts.MODE_DARK)
    assert "AUDITORÍA DE CARGAS" in svg
    assert svg.index("etl_run") < svg.index("rejection")
    assert "4 filas" in svg and "201 filas" in svg
    assert "run_id (FK)" in svg
    layout, height = star_model.compute_layout(COLUMNS)
    # The audit group sits below dim_region, inside the same right-hand margin,
    # but never overlaps any of the five star cards.
    audit_top = layout["dim_region"][1] + layout["dim_region"][3] + star_model.GAP
    audit_rect = (star_model.WIDTH - star_model.MARGIN - star_model.AUDIT_WIDTH, audit_top,
                 star_model.AUDIT_WIDTH, 2 * star_model.AUDIT_HEIGHT + star_model.AUDIT_GAP)
    for rect in layout.values():
        assert not rect_overlap(rect, audit_rect)
    assert audit_rect[1] + audit_rect[3] <= height - star_model.MARGIN


def test_t59_text_from_the_data_is_escaped():
    hostile = dict(COLUMNS)
    hostile["weekly_price"] = [("<b>col</b>", "PK")]
    svg = star_model.build_star_svg(hostile, ROW_COUNTS, charts.MODE_DARK)
    assert "<b>col</b>" not in svg and "&lt;b&gt;col&lt;/b&gt;" in svg


def test_d190_the_ipc_group_hangs_from_dim_date_and_never_overlaps_the_star():
    svg = star_model.build_star_svg(COLUMNS, {**ROW_COUNTS, **IPC_COUNTS}, charts.MODE_DARK)
    assert "IPC DE ALIMENTOS (INE)" in svg
    assert svg.index("ine_ipc_source") < svg.index("ipc_monthly") < svg.index("ipc_weekly")
    assert "202 filas" in svg and "250 filas" in svg and "dim_date" in svg
    assert 'aria-label="Modelo estrella de datos.duckdb"' in svg
    layout, _ = star_model.compute_layout(COLUMNS)
    ipc_rect = (star_model.MARGIN, star_model.MARGIN + 34, star_model.AUDIT_WIDTH,
                3 * star_model.AUDIT_HEIGHT + 2 * star_model.IPC_GAP)
    for rect in layout.values():
        assert not rect_overlap(rect, ipc_rect)
    # Without the counts of its tables (the schema file has none) the group is not drawn.
    assert "IPC DE ALIMENTOS" not in star_model.build_star_svg(COLUMNS, ROW_COUNTS, charts.MODE_DARK)
