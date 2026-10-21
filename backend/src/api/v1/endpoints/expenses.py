from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.v1.dependencies import SessionDep
from src.models import Expense, Event, EventUser, Debt, User
from src.schemas.expenses import ExpenseRead, ExpenseCreate
from src.services.expenses_service import split_equally

router = APIRouter(tags=["expenses"])

EXPENSE_LOAD = (
  selectinload(Expense.payer),
  selectinload(Expense.debts).selectinload(Debt.debtor),
)

async def load_expense(session: SessionDep, expense_id: int) -> Expense | None:
  # populate_existing перезаписывает объект, уже лежащий в сессии (например, после изменения payer_id)
  return await session.scalar(
    select(Expense)
    .where(Expense.id == expense_id)
    .options(*EXPENSE_LOAD)
    .execution_options(populate_existing=True)
  )

async def get_member_ids(session: SessionDep, event_id: int) -> list[int]:
  # не через event.events_users: событие могло попасть в сессию по цепочке selectin
  # (Expense.payer -> User.events_users -> EventUser.event) без этой коллекции,
  # и обращение к ней вызовет MissingGreenlet
  return list(await session.scalars(select(EventUser.user_id).where(EventUser.event_id == event_id)))

def calculate_debts(data: ExpenseCreate, member_ids: list[int]) -> list[Debt]:
  if data.payer_id not in member_ids:
    raise HTTPException(400, "Payer is not in this event")

  if data.split_type == "equal":
    shares = split_equally(data.amount, member_ids)
  else:
    shares = {share.user_id: share.amount for share in data.shares}

    if any(user_id not in member_ids for user_id in shares):
      raise HTTPException(400, "Some users are not in this event")

    if sum(shares.values()) != data.amount:
      raise HTTPException(400, "Shares do not add up to the total amount")

  return [
    Debt(debtor_id=user_id, amount=amount)
    for user_id, amount in shares.items()
    # при делении поровну мелкой суммы доля может округлиться до нуля
    if user_id != data.payer_id and amount > 0
  ]

def check_no_settled_debts(expense: Expense) -> None:
  if any(debt.is_settled for debt in expense.debts):
    raise HTTPException(409, "Expense has settled debts and cannot be changed")

@router.get("/events/{event_id}/expenses", response_model=list[ExpenseRead])
async def get_event_expenses(session: SessionDep, event_id: int, payer_id: int | None = None):
  event = await session.get(Event, event_id)

  if event is None:
    raise HTTPException(status_code=404, detail="Event not found")

  query = select(Expense).where(Expense.event_id == event_id).options(*EXPENSE_LOAD)

  if payer_id is not None:
    query = query.where(Expense.payer_id == payer_id)

  expenses = (await session.scalars(query)).all()

  return expenses

@router.get("/users/{user_id}/expenses", response_model=list[ExpenseRead])
async def get_user_expenses(session: SessionDep, user_id: int):
  user = await session.get(User, user_id)

  if user is None:
    raise HTTPException(status_code=404, detail="User not found")

  expenses = (await session.scalars(
    select(Expense).where(Expense.payer_id == user_id).options(*EXPENSE_LOAD)
  )).all()

  return expenses

@router.get("/expenses/{expense_id}", response_model=ExpenseRead)
async def get_expense(session: SessionDep, expense_id: int):
  expense = await load_expense(session, expense_id)

  if expense is None:
    raise HTTPException(status_code=404, detail="Expense not found")

  return expense

@router.post("/events/{event_id}/expenses", response_model=ExpenseRead, status_code=201)
async def create_expense(session: SessionDep, event_id: int, data: ExpenseCreate):
  event = await session.get(Event, event_id)

  if event is None:
    raise HTTPException(status_code=404, detail="Event not found")

  expense = Expense(
    name=data.name,
    amount=data.amount,
    event_id=event_id,
    payer_id=data.payer_id,
    debts=calculate_debts(data, await get_member_ids(session, event_id)),
  )

  session.add(expense)
  await session.commit()

  return await load_expense(session, expense.id)

@router.put("/expenses/{expense_id}", response_model=ExpenseRead)
async def update_expense(session: SessionDep, expense_id: int, data: ExpenseCreate):
  expense = await load_expense(session, expense_id)

  if expense is None:
    raise HTTPException(status_code=404, detail="Expense not found")

  check_no_settled_debts(expense)

  # старые долги удаляются благодаря cascade='all, delete-orphan'
  expense.debts = calculate_debts(data, await get_member_ids(session, expense.event_id))
  expense.name = data.name
  expense.amount = data.amount
  expense.payer_id = data.payer_id

  await session.commit()

  return await load_expense(session, expense.id)

@router.delete("/expenses/{expense_id}", status_code=204)
async def delete_expense(session: SessionDep, expense_id: int):
  expense = await load_expense(session, expense_id)

  if expense is None:
    raise HTTPException(status_code=404, detail="Expense not found")

  check_no_settled_debts(expense)

  await session.delete(expense)
  await session.commit()

  return Response(status_code=204)
