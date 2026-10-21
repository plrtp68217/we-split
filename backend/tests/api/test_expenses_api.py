from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.api.conftest import AddExpense


def debts_by_name(expense: dict) -> dict[str, Decimal]:
    return {debt["debtor"]["name"]: Decimal(debt["amount"]) for debt in expense["debts"]}


async def test_equal_split(users: dict[str, int], add_expense: AddExpense):
    expense = await add_expense(payer_id=users["Petya"], amount="900")

    assert expense["payer"]["name"] == "Petya"
    assert debts_by_name(expense) == {"Vasya": Decimal("300"), "Masha": Decimal("300")}


async def test_custom_split(users: dict[str, int], add_expense: AddExpense):
    expense = await add_expense(
        payer_id=users["Petya"],
        amount="1000",
        shares={users["Petya"]: "100", users["Vasya"]: "600", users["Masha"]: "300"},
    )

    assert debts_by_name(expense) == {"Vasya": Decimal("600"), "Masha": Decimal("300")}


async def test_equal_split_skips_zero_debts(users: dict[str, int], add_expense: AddExpense):
    expense = await add_expense(payer_id=users["Petya"], amount="0.01")

    assert expense["debts"] == []


@pytest.mark.parametrize(
    "changes",
    [
        {"amount": "-100"},
        {"amount": "0"},
        {"amount": "10.999"},
        {"name": ""},
        {"name": "x" * 51},
        {"shares": [{"user_id": 1, "amount": "10"}]},
        {"split_type": "custom"},
        {"split_type": "custom", "shares": [{"user_id": 1, "amount": "5"}, {"user_id": 1, "amount": "5"}]},
    ],
)
async def test_invalid_body(client: AsyncClient, users: dict[str, int], event_id: int, changes: dict):
    body = {"name": "Food", "amount": "10", "payer_id": users["Petya"], "split_type": "equal", **changes}

    response = await client.post(f"/events/{event_id}/expenses", json=body)

    assert response.status_code == 422


async def test_business_rules(client: AsyncClient, users: dict[str, int], event_id: int):
    outsider = (await client.post("/users/", json={"name": "Outsider", "email": "out@example.com"})).json()["id"]
    base = {"name": "Food", "amount": "100", "payer_id": users["Petya"], "split_type": "custom"}

    payer_not_member = await client.post(
        f"/events/{event_id}/expenses", json={**base, "payer_id": outsider, "split_type": "equal"}
    )
    share_not_member = await client.post(
        f"/events/{event_id}/expenses", json={**base, "shares": [{"user_id": outsider, "amount": "100"}]}
    )
    wrong_sum = await client.post(
        f"/events/{event_id}/expenses", json={**base, "shares": [{"user_id": users["Vasya"], "amount": "99"}]}
    )

    assert payer_not_member.json()["detail"] == "Payer is not in this event"
    assert share_not_member.json()["detail"] == "Some users are not in this event"
    assert wrong_sum.json()["detail"] == "Shares do not add up to the total amount"


async def test_filter_by_payer(client: AsyncClient, users: dict[str, int], event_id: int, add_expense: AddExpense):
    await add_expense(payer_id=users["Petya"], amount="100")
    await add_expense(payer_id=users["Vasya"], amount="200")

    all_expenses = (await client.get(f"/events/{event_id}/expenses")).json()
    petya_expenses = (await client.get(f"/events/{event_id}/expenses", params={"payer_id": users["Petya"]})).json()

    assert len(all_expenses) == 2
    assert [expense["payer"]["name"] for expense in petya_expenses] == ["Petya"]


async def test_update_expense_recalculates_debts(
    client: AsyncClient, users: dict[str, int], add_expense: AddExpense
):
    expense = await add_expense(payer_id=users["Petya"], amount="900")

    response = await client.put(
        f"/expenses/{expense['id']}",
        json={"name": "Taxi", "amount": "600", "payer_id": users["Vasya"], "split_type": "equal"},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Taxi"
    assert updated["payer"]["name"] == "Vasya"
    assert debts_by_name(updated) == {"Petya": Decimal("200"), "Masha": Decimal("200")}
    assert len((await client.get("/debts")).json()) == 2


async def test_delete_expense(client: AsyncClient, users: dict[str, int], add_expense: AddExpense):
    expense = await add_expense(payer_id=users["Petya"], amount="900")

    response = await client.delete(f"/expenses/{expense['id']}")

    assert response.status_code == 204
    assert (await client.get(f"/expenses/{expense['id']}")).status_code == 404
    assert (await client.get("/debts")).json() == []


async def test_cannot_change_expense_with_settled_debts(
    client: AsyncClient, users: dict[str, int], add_expense: AddExpense
):
    expense = await add_expense(payer_id=users["Petya"], amount="900")
    await client.patch(f"/debts/{expense['debts'][0]['id']}", json={"is_settled": True})

    update = await client.put(
        f"/expenses/{expense['id']}",
        json={"name": "Food", "amount": "100", "payer_id": users["Petya"], "split_type": "equal"},
    )
    delete = await client.delete(f"/expenses/{expense['id']}")

    assert update.status_code == 409
    assert delete.status_code == 409


async def test_unknown_expense(client: AsyncClient):
    body = {"name": "Food", "amount": "100", "payer_id": 1, "split_type": "equal"}

    assert (await client.get("/expenses/999")).status_code == 404
    assert (await client.put("/expenses/999", json=body)).status_code == 404
    assert (await client.delete("/expenses/999")).status_code == 404
    assert (await client.post("/events/999/expenses", json=body)).status_code == 404
