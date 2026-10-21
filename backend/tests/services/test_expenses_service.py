from decimal import Decimal

from src.services.expenses_service import split_equally


def test_splits_evenly():
    assert split_equally(Decimal("900"), [1, 2, 3]) == {
        1: Decimal("300"),
        2: Decimal("300"),
        3: Decimal("300"),
    }


def test_rounding_remainder_goes_to_first_user():
    shares = split_equally(Decimal("100"), [1, 2, 3])

    assert shares == {1: Decimal("33.34"), 2: Decimal("33.33"), 3: Decimal("33.33")}


def test_shares_always_add_up_to_amount():
    for amount in ["0.01", "0.05", "10", "99.99", "1234.56"]:
        for user_count in range(1, 8):
            shares = split_equally(Decimal(amount), list(range(1, user_count + 1)))

            assert sum(shares.values()) == Decimal(amount)


def test_single_user_gets_everything():
    assert split_equally(Decimal("42.50"), [7]) == {7: Decimal("42.50")}


def test_small_amount_leaves_zero_shares():
    shares = split_equally(Decimal("0.01"), [1, 2, 3])

    assert shares == {1: Decimal("0.01"), 2: Decimal("0"), 3: Decimal("0")}
