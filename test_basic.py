from src.utils import american_to_decimal, decimal_to_american
from src.kelly import kelly_stake, expected_ev

def test_utils_roundtrip():
    for price in [-200, -110, +100, +150, +250]:
        dec = american_to_decimal(price)
        back = decimal_to_american(dec)
        assert abs(price - back) <= 1

def test_kelly():
    stake = kelly_stake(10000, +120, 0.55, 0.5, 0.02)
    assert stake >= 0
    ev = expected_ev(+120, 0.55, stake)
    assert isinstance(ev, float)
