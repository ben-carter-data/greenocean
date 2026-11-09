"""The slowest and the failed tests of a CI group, as GitHub notes anyone can read in the run's summary (D-557).

    python scripts/pruebas_lentas.py <junit.xml> <title>

Reads the JUnit report pytest wrote and prints the slowest tests as `::notice` lines, so a group that suddenly takes
far longer names its culprit without opening the log. D-568: each failed test, with the first line of its error, as an
`::error` line, so a red group names the test that failed without opening the log either. It never fails the job.
"""

import re
import sys
from pathlib import Path
from xml.etree import ElementTree

# region Constants
SHOWN = 5
CASE = re.compile(r'<testcase\b[^>]*\bclassname="([^"]*)"[^>]*\bname="([^"]*)"[^>]*\btime="([\d.]+)"')
MESSAGE_LENGTH = 200
# endregion


# region The slowest tests
def slowest(report: str, count: int = SHOWN) -> list[tuple[float, str]]:
    """(seconds, test) of the `count` slowest test cases of a JUnit report, the slowest first."""
    cases = [(float(seconds), f"{module}::{name}") for module, name, seconds in CASE.findall(report)]
    return sorted(cases, reverse=True)[:count]


def failed(report: str) -> list[tuple[str, str]]:
    """(test, first line of its message) of every failed or erroring test case of a JUnit report (D-568)."""
    found = []
    for case in ElementTree.fromstring(report).iter("testcase"):
        problem = case.find("failure")
        problem = problem if problem is not None else case.find("error")
        if problem is not None:
            message = (problem.get("message") or problem.tag).strip().splitlines()
            found.append(
                (f"{case.get('classname')}::{case.get('name')}", (message or [problem.tag])[0][:MESSAGE_LENGTH])
            )
    return found


def main() -> int:
    path, title = Path(sys.argv[1]), sys.argv[2]
    if not path.exists():
        return 0
    report = path.read_text(encoding="utf-8")
    for seconds, test in slowest(report):
        print(f"::notice title={title}::{seconds:.1f} s · {test}")
    for test, message in failed(report):
        print(f"::error title={title}::{test} · {message}")
    return 0


# endregion


# region Run
if __name__ == "__main__":
    sys.exit(main())
# endregion
