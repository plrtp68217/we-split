from decimal import ROUND_DOWN, Decimal


def split_equally(amount: Decimal, user_ids: list[int]) -> dict[int, Decimal]:
    share = (amount / len(user_ids)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    result = {uid: share for uid in user_ids}
    # копейки, оставшиеся от округления, отдаём первому
    result[user_ids[0]] += amount - share * len(user_ids)
    return result