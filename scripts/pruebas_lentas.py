"""The slowest tests of a CI group, as GitHub notices anyone can read in the run's summary (D-557).

    python scripts/pruebas_lentas.py <junit.xml> <title>

Reads the JUnit report pytest wrote and prints the slowest tests as `::notice` lines, so a group that suddenly takes
far longer names its culprit without opening the log. It never fails the job.
"""

import re
import sys
from pathlib import Path

# region Constants
SHOWN = 5
CASE = re.compile(r'<testcase\b[^>]*\bclassname="([^"]*)"[^>]*\bname="([^"]*)"[^>]*\btime="([\d.]+)"')
# endregion


# region The slowest tests
def slowest(report: str, count: int = SHOWN) -> list[tuple[float, str]]:
    """(seconds, test) of the `count` slowest test cases of a JUnit report, the slowest first."""
    cases = [(float(seconds), f"{module}::{name}") for module, name, seconds in CASE.findall(report)]
    return sorted(cases, reverse=True)[:count]


def main() -> int:
    path, title = Path(sys.argv[1]), sys.argv[2]
    if not path.exists():
        return 0
    for seconds, test in slowest(path.read_text(encoding="utf-8")):
        print(f"::notice title={title}::{seconds:.1f} s · {test}")
    return 0


# endregion


# region Run
if __name__ == "__main__":
    sys.exit(main())
# endregion
