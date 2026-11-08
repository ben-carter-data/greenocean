"""The test files of one group of the suite, so the CI runs the suite in parallel groups (D-555).

    python scripts/grupo_pruebas.py <group> <groups>

Prints the test files of group <group> (from 1) out of <groups>, one per line. Every file of tests/ lands in exactly one
group, and a new test file joins one by itself. The groups are balanced by the size of each file, the largest first,
each into the group that holds the least so far: a stable split, the same on every runner.
"""

import sys
from pathlib import Path

# region Constants
TESTS = Path(__file__).resolve().parent.parent / "tests"
PATTERN = "test_*.py"
# endregion


# region The groups
def split(files: list[Path], groups: int) -> list[list[Path]]:
    """The files dealt into `groups` groups of similar size: the largest first, each into the lightest group."""
    loads = [0] * groups
    chosen: list[list[Path]] = [[] for _ in range(groups)]
    for file in sorted(files, key=lambda path: (-path.stat().st_size, path.name)):
        lightest = loads.index(min(loads))
        chosen[lightest].append(file)
        loads[lightest] += file.stat().st_size
    return [sorted(group) for group in chosen]


def main() -> int:
    group, groups = int(sys.argv[1]), int(sys.argv[2])
    if not 1 <= group <= groups:
        print(f"group must be between 1 and {groups}", file=sys.stderr)
        return 2
    for file in split(sorted(TESTS.glob(PATTERN)), groups)[group - 1]:
        print(file.relative_to(TESTS.parent).as_posix())
    return 0


# endregion


# region Run
if __name__ == "__main__":
    sys.exit(main())
# endregion
