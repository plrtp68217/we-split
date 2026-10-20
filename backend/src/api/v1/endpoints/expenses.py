from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select

from src.api.v1.dependencies import SessionDep
from src.models import Expense, Event
from src.schemas.expenses import ExpenseRead, ExpenseCreate

router = APIRouter(prefix="/events", tags=["expenses"])

@router.get("/{event_id}/users/{user_id}/expenses", response_model=list[ExpenseRead])
async def get_all_expenses_by_user(session: SessionDep, event_id: int,  user_id: int):
  result = await session.execute(select(Expense).where(
    Expense.event_id == event_id,
    Expense.payer_id == user_id
  ))

  expenses = result.scalars().all()

  return expenses

@router.post("/expenses", response_model=ExpenseRead)
async def create_expense(session: SessionDep, data: ExpenseCreate):
  event = (await session.execute(select(Event).where(Event.id == data.event_id))).scalar()

  if event is None:
    raise HTTPException(status_code=404, detail="Event not found")

  member_ids = [eu.user_id for eu in event.events_users]

  if data.payer_id not in member_ids:
    raise HTTPException(400, "Payer is not in this event")

  if data.split_type == "equal":
    #TODO add in service function split_equally
    ...
  elif data.split_type == "custom":
    ...
    #TODO add logic to split custom
  else:
    raise HTTPException(400, "split_type is not in ['equal', 'custom']")

  # if data.split_type == "equal":
  #       shares = split_equally(data.amount, member_ids)
  # else:
  #     shares = {s.user_id: s.amount for s in data.shares}
  #     if any(uid not in member_ids for uid in shares):
  #         raise HTTPException(400, "Some users are not in this event")
  #     if sum(shares.values()) != data.amount:
  #         raise HTTPException(400, "Shares do not add up to the total amount")
  
  expense = Expense(
    name=data.name,
    amount=data.amount,
    event_id=data.event_id,
    payer_id=data.payer_id
  )

  # for user_id, amount in shares.items():
  #       if user_id != data.payer_id:
  #           expense.debts.append(Debt(debtor_id=user_id, amount=amount))

  session.add(expense)
  await session.commit()
  await session.refresh(expense)

  return expense