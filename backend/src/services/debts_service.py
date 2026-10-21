from collections import defaultdict
from decimal import Decimal
from typing import Iterable, NamedTuple


class Transfer(NamedTuple):
    from_id: int
    to_id: int
    amount: Decimal


def net_debts(debts: Iterable[tuple[int, int, Decimal]]) -> list[Transfer]:
    """Взаимозачёт долгов по парам: (debtor_id, creditor_id, amount) -> кто кому сколько переводит."""
    # ключ — пара (меньший id, больший id); плюс значит, что меньший должен большему
    balance: dict[tuple[int, int], Decimal] = defaultdict(Decimal)

    for debtor_id, creditor_id, amount in debts:
        if debtor_id < creditor_id:
            balance[(debtor_id, creditor_id)] += amount
        else:
            balance[(creditor_id, debtor_id)] -= amount

    result = []
    for (low_id, high_id), amount in balance.items():
        if amount > 0:
            result.append(Transfer(low_id, high_id, amount))
        elif amount < 0:
            result.append(Transfer(high_id, low_id, -amount))

    return sorted(result)
