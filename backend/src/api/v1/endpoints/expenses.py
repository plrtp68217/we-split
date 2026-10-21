from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.v1.dependencies import SessionDep
from src.models import Expense, Event, Debt, User
from src.schemas.expenses import ExpenseRead, ExpenseCreate
from src.services.expenses_service import split_equally

router = APIRouter(tags=["expenses"])

EXPENSE_LOAD = (
  selectinload(Expense.payer),
  selectinload(Expense.debts).selectinload(Debt.debtor),
)

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
  expense = await session.scalar(
    select(Expense).where(Expense.id == expense_id).options(*EXPENSE_LOAD)
  )

  if expense is None:
    raise HTTPException(status_code=404, detail="Expense not found")

  return expense

@router.post("/events/{event_id}/expenses", response_model=ExpenseRead, status_code=201)
async def create_expense(session: SessionDep, event_id: int, data: ExpenseCreate):
  event = await session.get(Event, event_id)

  if event is None:
    raise HTTPException(status_code=404, detail="Event not found")

  member_ids = [eu.user_id for eu in event.events_users]

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

  expense = Expense(
    name=data.name,
    amount=data.amount,
    event_id=event_id,
    payer_id=data.payer_id
  )

  for user_id, amount in shares.items():
    # при делении поровну мелкой суммы доля может округлиться до нуля
    if user_id != data.payer_id and amount > 0:
      expense.debts.append(Debt(debtor_id=user_id, amount=amount))

  session.add(expense)
  await session.commit()

  expense = (await session.scalars(
    select(Expense).where(Expense.id == expense.id).options(*EXPENSE_LOAD)
  )).one()

  return expense
