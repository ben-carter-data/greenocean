"""Tests for the star model diagram: layout, cards and the audit trail (D-097)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bi import charts, project, star_model  # noqa: E402

# region Constants
COLUMNS = project.read_schema_columns(project.read_document(project.SCHEMA_FILE))
ROW_COUNTS = {
    "weekly_price": 811578,
    "dim_product": 1609,
    "dim_region": 9,
    "dim_channel": 8,
    "dim_date": 249,
    "etl_run": 4,
    "rejection": 201,
}
IPC_COUNTS = {"ine_ipc_source": 202, "ipc_monthly": 202, "ipc_weekly": 250}
# endregion


# region Tests for the star model diagram
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


def all_rects(layout):
    """The five cards plus the audit and IPC groups: nothing in the drawing may overlap."""
    return list(layout.values()) + [star_model.audit_rect(layout), star_model.ipc_rect(layout)]


def assert_nothing_overlaps(layout, height):
    rects = all_rects(layout)
    for i, a in enumerate(rects):
        for b in rects[i + 1 :]:
            assert not rect_overlap(a, b)
        x, y, w, h = a
        assert x >= 0 and y >= 0 and x + w <= star_model.WIDTH and y + h <= height


def test_d097_layout_never_overlaps_whatever_the_column_counts():
    layout, height = star_model.compute_layout(COLUMNS)
    assert set(layout) == {"dim_date", "weekly_price", "dim_product", "dim_region", "dim_channel"}
    assert_nothing_overlaps(layout, height)
    # D-503: weekly_price in the middle, dim_date over dim_product on its left, dim_region over
    # dim_channel on its right (D-097: dim_channel is a real dimension, replacing the old
    # dashed "week" placeholder).
    fact_x, _, fact_width, _ = layout["weekly_price"]
    for table in ("dim_date", "dim_product"):
        assert layout[table][0] + layout[table][2] < fact_x
    for table in ("dim_region", "dim_channel"):
        assert layout[table][0] > fact_x + fact_width
    assert layout["dim_date"][1] + layout["dim_date"][3] < layout["dim_product"][1]
    assert layout["dim_region"][1] + layout["dim_region"][3] < layout["dim_channel"][1]


def test_d503_the_drawing_is_landscape_in_the_proportion_of_its_panel():
    # Twice as wide as tall (between 1.8 and 2.1), so the panel's width, not its height, sets
    # the scale and the column names read at 14 px or more in a 1440 × 900 window.
    layout, height = star_model.compute_layout(COLUMNS)
    assert 1.8 <= star_model.WIDTH / height <= 2.1
    assert star_model.WIDTH <= 1200 and height <= 600


def test_d097_layout_grows_with_more_columns_without_overlapping():
    for table in ("dim_date", "dim_region", "dim_channel", "weekly_price"):
        wide_columns = dict(COLUMNS)
        wide_columns[table] = COLUMNS[table] + [("extra_one", ""), ("extra_two", ""), ("extra_three", "")]
        layout, height = star_model.compute_layout(wide_columns)
        base_layout, base_height = star_model.compute_layout(COLUMNS)
        assert layout[table][3] > base_layout[table][3]
        assert height >= base_height
        assert_nothing_overlaps(layout, height)
    # A column with three more cards' worth of rows makes the drawing taller.
    wide_columns = dict(COLUMNS)
    wide_columns["dim_product"] = COLUMNS["dim_product"] + [(f"extra_{n}", "") for n in range(6)]
    layout, height = star_model.compute_layout(wide_columns)
    assert height > star_model.compute_layout(COLUMNS)[1]
    assert_nothing_overlaps(layout, height)
    # And a dim_date shorter than the IPC chain keeps the chain inside the margin.
    short_columns = dict(COLUMNS)
    short_columns["dim_date"] = COLUMNS["dim_date"][:1]
    layout, height = star_model.compute_layout(short_columns)
    assert star_model.ipc_rect(layout)[1] >= star_model.MARGIN
    assert_nothing_overlaps(layout, height)


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
    assert "REGISTRO DE CARGAS" in svg and "AUDITORÍA" not in svg  # D-526: the official name of etl_run
    assert svg.index("etl_run") < svg.index("rejection")
    assert "4 filas" in svg and "201 filas" in svg
    assert "run_id (FK)" in svg
    layout, height = star_model.compute_layout(COLUMNS)
    # D-503: the audit group closes the right column, under dim_channel and to the right of
    # the fact table, but never overlaps any of the five star cards.
    audit_rect = star_model.audit_rect(layout)
    assert audit_rect[1] >= layout["dim_channel"][1] + layout["dim_channel"][3] + star_model.GAP
    assert audit_rect[0] >= layout["weekly_price"][0] + layout["weekly_price"][2]
    for rect in layout.values():
        assert not rect_overlap(rect, audit_rect)
    assert audit_rect[1] + audit_rect[3] <= height - star_model.MARGIN
    # The boxes are drawn inside that rectangle, under its heading.
    assert f'<rect x="{audit_rect[0]:.1f}" y="{audit_rect[1] + star_model.GROUP_LABEL_HEIGHT:.1f}"' in svg


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
    # D-503: the chain is the leftmost column, beside dim_date (its link is a straight dashed
    # line from ipc_weekly to the card, on the level of ipc_weekly), never over a card.
    ipc_rect = star_model.ipc_rect(layout)
    date_x, date_y, _, date_height = layout["dim_date"]
    assert ipc_rect[0] + ipc_rect[2] < date_x
    assert date_y <= ipc_rect[1] and ipc_rect[1] + ipc_rect[3] <= date_y + date_height
    for rect in layout.values():
        assert not rect_overlap(rect, ipc_rect)
    assert not rect_overlap(ipc_rect, star_model.audit_rect(layout))
    assert f'<rect x="{ipc_rect[0]:.1f}" y="{ipc_rect[1] + star_model.GROUP_LABEL_HEIGHT:.1f}"' in svg
    assert f'H{date_x:.1f}" fill="none"' in svg  # the link ends on dim_date's left edge
    # Without the counts of its tables (the schema file has none) the group is not drawn.
    assert "IPC DE ALIMENTOS" not in star_model.build_star_svg(COLUMNS, ROW_COUNTS, charts.MODE_DARK)


# endregion
