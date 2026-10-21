from httpx import AsyncClient

from tests.api.conftest import AddExpense


async def test_list_events_newest_first(client: AsyncClient, users: dict[str, int]):
    for name in ["Trip", "Party"]:
        await client.post("/events/", json={"name": name, "user_ids": [users["Petya"]]})

    events = (await client.get("/events/")).json()

    assert [event["name"] for event in events] == ["Party", "Trip"]


async def test_create_event_with_unknown_user(client: AsyncClient, users: dict[str, int]):
    response = await client.post("/events/", json={"name": "Trip", "user_ids": [users["Petya"], 999]})

    assert response.status_code == 400
    assert response.json()["detail"] == "Users not found: [999]"


async def test_create_event_with_duplicate_users(client: AsyncClient, users: dict[str, int]):
    response = await client.post("/events/", json={"name": "Trip", "user_ids": [users["Petya"], users["Petya"]]})

    assert response.status_code == 422


async def test_add_user_to_event(client: AsyncClient, users: dict[str, int]):
    event = (await client.post("/events/", json={"name": "Trip", "user_ids": [users["Petya"]]})).json()

    response = await client.post(f"/events/{event['id']}/users", json={"user_id": users["Vasya"]})

    assert response.status_code == 201
    assert response.json()["name"] == "Vasya"

    members = (await client.get(f"/events/{event['id']}/users")).json()
    assert {member["name"] for member in members} == {"Petya", "Vasya"}


async def test_add_user_to_event_errors(client: AsyncClient, users: dict[str, int], event_id: int):
    already_in = await client.post(f"/events/{event_id}/users", json={"user_id": users["Petya"]})
    unknown_user = await client.post(f"/events/{event_id}/users", json={"user_id": 999})
    unknown_event = await client.post("/events/999/users", json={"user_id": users["Petya"]})

    assert already_in.status_code == 409
    assert unknown_user.status_code == 400
    assert unknown_event.status_code == 404


async def test_cannot_remove_user_with_unsettled_debts(
    client: AsyncClient, users: dict[str, int], event_id: int, add_expense: AddExpense
):
    await add_expense(payer_id=users["Petya"], amount="300")

    # и должник, и кредитор
    as_debtor = await client.delete(f"/events/{event_id}/users/{users['Vasya']}")
    as_creditor = await client.delete(f"/events/{event_id}/users/{users['Petya']}")

    assert as_debtor.status_code == 409
    assert as_creditor.status_code == 409


async def test_remove_user_after_settlement(
    client: AsyncClient, users: dict[str, int], event_id: int, add_expense: AddExpense
):
    await add_expense(payer_id=users["Petya"], amount="100", shares={users["Vasya"]: "100"})
    await client.post(
        f"/events/{event_id}/settlements",
        json={"from_user_id": users["Vasya"], "to_user_id": users["Petya"]},
    )

    response = await client.delete(f"/events/{event_id}/users/{users['Vasya']}")

    assert response.status_code == 204


async def test_delete_event_cascades(
    client: AsyncClient, users: dict[str, int], event_id: int, add_expense: AddExpense
):
    expense = await add_expense(payer_id=users["Petya"], amount="900")

    response = await client.delete(f"/events/{event_id}")

    assert response.status_code == 204
    assert (await client.get(f"/events/{event_id}")).status_code == 404
    assert (await client.get(f"/expenses/{expense['id']}")).status_code == 404
    assert (await client.get("/debts")).json() == []
    assert (await client.get(f"/users/{users['Petya']}")).status_code == 200
