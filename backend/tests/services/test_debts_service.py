from decimal import Decimal

from src.services.debts_service import Transfer, net_debts

PETYA, VASYA, MASHA = 1, 2, 3


def test_no_debts():
    assert net_debts([]) == []


def test_single_debt_is_kept():
    assert net_debts([(PETYA, VASYA, Decimal("500"))]) == [Transfer(PETYA, VASYA, Decimal("500"))]


def test_mutual_debts_are_netted():
    debts = [
        (PETYA, VASYA, Decimal("500")),
        (VASYA, PETYA, Decimal("300")),
    ]

    assert net_debts(debts) == [Transfer(PETYA, VASYA, Decimal("200"))]


def test_direction_flips_when_reverse_debt_is_bigger():
    debts = [
        (PETYA, VASYA, Decimal("100")),
        (VASYA, PETYA, Decimal("250")),
    ]

    assert net_debts(debts) == [Transfer(VASYA, PETYA, Decimal("150"))]


def test_equal_mutual_debts_cancel_out():
    debts = [
        (PETYA, VASYA, Decimal("100")),
        (VASYA, PETYA, Decimal("100")),
    ]

    assert net_debts(debts) == []


def test_debts_of_same_pair_are_summed():
    debts = [
        (MASHA, PETYA, Decimal("10.50")),
        (MASHA, PETYA, Decimal("0.25")),
    ]

    assert net_debts(debts) == [Transfer(MASHA, PETYA, Decimal("10.75"))]


def test_pairs_are_netted_independently():
    # взаимозачёт только по парам: цепочка Маша -> Петя -> Вася не схлопывается в Маша -> Вася
    debts = [
        (MASHA, PETYA, Decimal("100")),
        (PETYA, VASYA, Decimal("100")),
    ]

    assert net_debts(debts) == [
        Transfer(PETYA, VASYA, Decimal("100")),
        Transfer(MASHA, PETYA, Decimal("100")),
    ]
