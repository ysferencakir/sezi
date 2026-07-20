import pytest

from modules.evds.module import _to_float


@pytest.mark.parametrize("raw,expected", [
    ("41.23", 41.23),
    (41.23, 41.23),
    (None, None),
    ("", None),
    ("not-a-number", None),
])
def test_to_float(raw, expected):
    assert _to_float(raw) == expected
