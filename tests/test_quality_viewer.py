"""The report viewer (D-571): its slides write every figure as the rest of the app writes it, and the slide «Resultados»
says once, under its table, how to read its bars and ticks, which is what they show."""

import html
import json
import re

from bi import i18n, quality_method, quality_metrics, quality_viewer

# region Constants
# The failure and the acceptable of each row of «Resultados», as drawn; the bar and the tick of one row.
FIGURES = re.compile(r'<td class="num">([^<]*)</td><td class="num muted">([^<]*)</td>')
BAR = re.compile(r'<i style="width:([\d.]+)%')
TICK = re.compile(r'<b style="left:([\d.]+)%')
# (coverage %, Ruff warnings, comparable prices %, days since the last load): together they reach every state.
MEASUREMENTS = [(96, 0, 95, 3), (90, 0, 90, 8), (89, 1, 89, 9), (60, 7, 40, 30)]
# endregion


# region Figures written as the app writes them
def test_d571_the_results_write_each_failure_and_acceptable_as_the_app_does(monkeypatch):
    """0,01 % and 0,25 %, never 0,0 % and 0,2 %: the slide and the comparison write what quality_method.failure_text
    writes in the reader's language."""
    reports = quality_metrics.read_reports()
    report = reports[-1]
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    # The rows of the latest report, and one with the small shares that keep two decimals.
    rows = report["indicadores"] + [
        {**report["indicadores"][0], "falla": 0.008, "falla_aceptable": 0.25, "unidad_falla": "%"}
    ]
    for english in (False, True):
        monkeypatch.setattr(i18n, "is_english", lambda english=english: english)
        drawn = FIGURES.findall(quality_viewer.results_rows({"indicadores": rows}, policy, english))
        written = [
            (
                html.escape(quality_method.failure_text(row)),
                html.escape(quality_method.failure_text(row, "falla_aceptable")),
            )
            for row in rows
        ]
        assert drawn == written and drawn[-1] == (("0.01 %", "0.25 %") if english else ("0,01 %", "0,25 %"))
        # The comparison writes the failures of the same report with the same texts.
        page = quality_viewer.build_viewer_html(reports, report["numero"], goals, policy, [], [], english)
        data, _ = json.JSONDecoder().raw_decode(page, page.index("const DATA=") + len("const DATA="))
        compared = next(item for item in data["reports"] if item["n"] == report["numero"])
        assert [row[4] for row in compared["rows"]] == [
            quality_method.failure_text(row) for row in report["indicadores"]
        ]


# endregion


# region How to read the bars (moved from the page «Plan de calidad», D-337)
def test_d571_the_results_say_once_under_the_table_how_to_read_the_bars_in_each_language():
    reports = quality_metrics.read_reports()
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    spanish, english = policy["resumen"]["como_leerlo"]
    assert spanish.startswith("Cómo leerlo:") and english.startswith("How to read this:")
    for language, line, other in ((False, spanish, english), (True, english, spanish)):
        page = quality_viewer.build_viewer_html(reports, reports[-1]["numero"], goals, policy, [], [], language)
        results = page.split('data-key="resultados"')[1].split('<section class="slide')[0]
        assert page.count(html.escape(line)) == 1 and html.escape(other) not in page
        assert results.index("</table>") < results.index(f'<p class="muted small">{html.escape(line)}</p>')


def test_d571_a_row_meets_its_acceptable_exactly_when_its_bar_stays_short_of_its_tick():
    """«Cada barra es la falla actual (en %, en casos o en días), la raya marca el máximo aceptable y mientras la barra no
    pase la raya, cumple»: checked against the bars of «Resultados», state by state."""
    goals = quality_metrics.read(quality_metrics.GOALS_FILE)
    policy = quality_metrics.read(quality_metrics.POLICY_FILE)
    # The line says «cumple» for a bar short of the tick: that holds while the goal equals the acceptable.
    assert all(goal["meta"] == goal.get("max", goal.get("min")) for key, goal in goals.items() if key != "nota")
    seen = set()
    for coverage, ruff, comparables, days in MEASUREMENTS:
        measurement = {
            "cobertura": {"total": coverage},
            "ruff": {"errores": ruff},
            "datos": {"pct_comparacion": comparables, "dias_desde_ultima_carga": days},
        }
        rows = quality_metrics.evaluate(measurement, goals, policy)
        for row in rows:
            drawn = quality_viewer.results_rows({"indicadores": [row]}, policy, False)
            bar, tick = BAR.search(drawn), TICK.search(drawn)
            if row["falla"] is None:
                assert bar is None and tick is None  # not measured: no bar, no tick
                continue
            width, mark = float(bar.group(1)), float(tick.group(1))
            assert (row["estado"] == "cumple") == (width <= mark), (row["clave"], width, mark, row["estado"])
            # The tick is the acceptable, on the scale of its own bar: zero tolerance puts it at the left edge.
            if row["falla_aceptable"] == 0:
                assert mark == 0.0
            seen.add(row["estado"])
        # The failure is in %, in cases or in days, as the line says; nothing else.
        assert {row["unidad_falla"] for row in rows} <= {"%", "", "días"}
    assert {"cumple", "urgente", "critico"} <= seen


# endregion
