from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.database import DATABASE_URL, get_session
from src.main import app
from src.models import Base

# тесты работают с отдельной базой <имя рабочей базы>_test на том же сервере
TEST_DATABASE_URL = make_url(DATABASE_URL).set(database=f"{make_url(DATABASE_URL).database}_test")

# NullPool: соединения не переиспользуются между тестами, нет проблем с event loop
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def create_test_database() -> None:
    admin_engine = create_async_engine(DATABASE_URL, poolclass=NullPool, isolation_level="AUTOCOMMIT")

    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DATABASE_URL.database},
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DATABASE_URL.database}"'))

    await admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def prepare_database() -> AsyncIterator[None]:
    await create_test_database()

    # схема создаётся по моделям, миграции здесь не проверяются
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    await test_engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables() -> AsyncIterator[None]:
    yield

    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with test_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


async def get_test_session() -> AsyncIterator[AsyncSession]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_session] = get_test_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def users(client: AsyncClient) -> dict[str, int]:
    """Три пользователя: имя -> id."""
    ids = {}
    for name in ["Petya", "Vasya", "Masha"]:
        response = await client.post("/users/", json={"name": name, "email": f"{name.lower()}@example.com"})
        ids[name] = response.json()["id"]
    return ids


@pytest.fixture
async def event_id(client: AsyncClient, users: dict[str, int]) -> int:
    """Событие, в котором участвуют все три пользователя."""
    response = await client.post("/events/", json={"name": "Trip", "user_ids": list(users.values())})
    return response.json()["id"]


AddExpense = Callable[..., Awaitable[dict[str, Any]]]


@pytest.fixture
def add_expense(client: AsyncClient, event_id: int) -> AddExpense:
    """Создаёт трату в событии и возвращает её JSON."""
    async def add(payer_id: int, amount: str, shares: dict[int, str] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"name": "Expense", "amount": amount, "payer_id": payer_id, "split_type": "equal"}

        if shares is not None:
            body["split_type"] = "custom"
            body["shares"] = [{"user_id": user_id, "amount": share} for user_id, share in shares.items()]

        response = await client.post(f"/events/{event_id}/expenses", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return add
