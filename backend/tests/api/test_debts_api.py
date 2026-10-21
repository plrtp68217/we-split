from decimal import Decimal

from httpx import AsyncClient

from tests.api.conftest import AddExpense


def balances_by_name(balances: list[dict]) -> list[tuple[str, str, Decimal]]:
    return [
        (balance["from_user"]["name"], balance["to_user"]["name"], Decimal(balance["amount"]))
        for balance in balances
    ]


async def test_debts_filters(client: AsyncClient, users: dict[str, int], add_expense: AddExpense):
    await add_expense(payer_id=users["Petya"], amount="900")
    await add_expense(payer_id=users["Vasya"], amount="100", shares={users["Masha"]: "100"})

    to_petya = (await client.get("/debts", params={"creditor_id": users["Petya"]})).json()
    masha_owes = (await client.get("/debts", params={"debtor_id": users["Masha"]})).json()

    assert {debt["debtor"]["name"] for debt in to_petya} == {"Vasya", "Masha"}
    assert sorted(Decimal(debt["amount"]) for debt in masha_owes) == [Decimal("100"), Decimal("300")]


async def test_settle_single_debt(client: AsyncClient, users: dict[str, int], add_expense: AddExpense):
    expense = await add_expense(payer_id=users["Petya"], amount="900")
    debt_id = expense["debts"][0]["id"]

    response = await client.patch(f"/debts/{debt_id}", json={"is_settled": True})

    assert response.status_code == 200
    assert response.json()["is_settled"] is True
    assert len((await client.get("/debts", params={"is_settled": False})).json()) == 1


async def test_balances_are_netted(
    client: AsyncClient, users: dict[str, int], event_id: int, add_expense: AddExpense
):
    await add_expense(payer_id=users["Petya"], amount="900")
    await add_expense(payer_id=users["Vasya"], amount="300", shares={users["Petya"]: "300"})

    balances = (await client.get(f"/events/{event_id}/balances")).json()

    # долги Пети и Васи друг другу (300 и 300) взаимно погасились
    assert balances_by_name(balances) == [("Masha", "Petya", Decimal("300"))]


async def test_settlement_settles_both_directions(
    client: AsyncClient, users: dict[str, int], event_id: int, add_expense: AddExpense
):
    await add_expense(payer_id=users["Petya"], amount="500", shares={users["Vasya"]: "500"})
    await add_expense(payer_id=users["Vasya"], amount="300", shares={users["Petya"]: "300"})

    response = await client.post(
        f"/events/{event_id}/settlements",
        json={"from_user_id": users["Vasya"], "to_user_id": users["Petya"]},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert (await client.get(f"/events/{event_id}/balances")).json() == []


async def test_settlement_wrong_direction(
    client: AsyncClient, users: dict[str, int], event_id: int, add_expense: AddExpense
):
    await add_expense(payer_id=users["Petya"], amount="500", shares={users["Vasya"]: "500"})

    response = await client.post(
        f"/events/{event_id}/settlements",
        json={"from_user_id": users["Petya"], "to_user_id": users["Vasya"]},
    )

    assert response.status_code == 400
    assert len((await client.get(f"/events/{event_id}/balances")).json()) == 1


async def test_settlement_errors(client: AsyncClient, users: dict[str, int], event_id: int):
    nothing_to_settle = await client.post(
        f"/events/{event_id}/settlements",
        json={"from_user_id": users["Vasya"], "to_user_id": users["Petya"]},
    )
    same_user = await client.post(
        f"/events/{event_id}/settlements",
        json={"from_user_id": users["Petya"], "to_user_id": users["Petya"]},
    )

    assert nothing_to_settle.status_code == 404
    assert same_user.status_code == 422
