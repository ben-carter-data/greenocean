"""The slowest and the failed tests of a CI group, as GitHub notes anyone can read in the run's summary (D-557).

    python scripts/pruebas_lentas.py <junit.xml> <title>
    python scripts/pruebas_lentas.py --caida <pytest.log> <title>

Reads the JUnit report pytest wrote and prints the slowest tests as `::notice` lines, so a group that suddenly takes
far longer names its culprit without opening the log. D-568: each failed test, with the first line of its error, as an
`::error` line, so a red group names the test that failed without opening the log either. D-569: with --caida, the
output of a pytest that crashed (a native library that ends the process, so no JUnit report is written): the error
Python wrote as it died and the test frames of its trace. It never fails the job.
"""

import re
import sys
from pathlib import Path
from xml.etree import ElementTree

# region Constants
SHOWN = 5
CASE = re.compile(r'<testcase\b[^>]*\bclassname="([^"]*)"[^>]*\bname="([^"]*)"[^>]*\btime="([\d.]+)"')
MESSAGE_LENGTH = 200
# D-569: what Python writes as the process dies (faulthandler), and a frame of its trace that is a test
FATAL = re.compile(r"^Fatal Python error: (.+)$", re.M)
TEST_FRAME = re.compile(r'File "[^"]*?(tests/test_\w+\.py)", line (\d+) in (\w+)')
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


def crash(log: str) -> list[str]:
    """D-569: the error a crashed pytest wrote as it died and the test frames of its trace, the innermost first."""
    fatal = FATAL.search(log)
    if not fatal:
        return []
    frames = [f"{name}:{line} in {function}" for name, line, function in TEST_FRAME.findall(log[fatal.start() :])]
    return [fatal.group(1)] + list(dict.fromkeys(frames))[:3]


def main() -> int:
    if sys.argv[1] == "--caida":
        path, title = Path(sys.argv[2]), sys.argv[3]
        found = crash(path.read_text(encoding="utf-8", errors="replace")) if path.exists() else []
        print(f"::error title={title}::pytest se cayó: " + (" · ".join(found) or "sin rastro en su salida"))
        return 0
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
