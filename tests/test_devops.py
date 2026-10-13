"""The DevOps cycle stays local, accessible and honest about recorded states."""
import xml.etree.ElementTree as ET

import pytest

from bi import charts, control, devops


@pytest.mark.parametrize("mode", charts.THEMES)
def test_cycle_uses_real_tool_logos_and_six_explained_stages(mode):
    svg = devops.build_svg({}, mode)
    root = ET.fromstring(svg)
    assert root.attrib["role"] == "img"
    for _, title, description, slugs, *_ in devops.STAGES:
        assert title in svg and description in svg
        assert all(devops.logo_body(slug) in svg for slug in slugs)
    assert "http" not in svg.replace('xmlns="http://www.w3.org/2000/svg"', '')
    assert "animateMotion" not in svg


def test_illustrative_animation_keeps_the_recorded_failure_visible_and_can_stop():
    states = {"workflow": control.RUN_FAILED}
    svg = devops.build_svg(states, charts.MODE_DARK, True)
    assert "animateMotion" in svg and "prefers-reduced-motion" in svg
    assert "<title>Falla</title>" in svg
    assert "animateMotion" not in devops.build_svg(states, charts.MODE_DARK, False)
    assert "<title>OK</title>" not in devops.build_svg({}, charts.MODE_DARK, True)
