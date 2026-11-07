"""D-520: every sale unit of the source was classified by hand. It fails on any new unit, also a harmless one, and the
weekly load does not run this file: see tests/test_unit_review.py for why."""

import pytest

from etl import etl
from tests.test_unit_review import REVIEWED_FILE, read_source_units, reviewed

# region Variables
needs_raw = pytest.mark.skipif(not etl.RAW_DATABASE_FILE.exists(), reason="etl/raw.db is not in the repository")
# endregion


# region Every sale unit of the source was classified by hand
@needs_raw
def test_d520_every_unit_of_the_source_was_classified_by_hand():
    new = sorted(read_source_units() - set(reviewed()["unit"]))
    assert not new, f"Add them to {REVIEWED_FILE.name} after checking the reading against the prices: {new}"


# endregion
