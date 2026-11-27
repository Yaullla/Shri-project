import pytest

from radar.quote_engine import calculate_quote


def test_quote():
    result = calculate_quote(10000, 1, 1000, 2000, 500, 12, 20)
    assert result["landed"] == "13500.00"
    assert result["sale"] == "19852.95"
    assert result["status"] == "estimate_only"
    assert result["margin"] == "20.00"


@pytest.mark.parametrize("args", [
    ("NaN", 1, 0, 0, 0, 0, 20),
    (100, 0, 0, 0, 0, 0, 20),
    (100, 1, 0, 0, 0, 80, 20),
    (0.00001, 1, 0, 0, 0, 0, 20),
])
def test_invalid(args):
    with pytest.raises(ValueError):
        calculate_quote(*args)
