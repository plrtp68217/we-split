from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.v1.dependencies import SessionDep
from src.schemas.debts import DebtRead, DebtUpdate
from src.models import Debt, Expense

router = APIRouter(tags=["debts"])

@router.get("/debts", response_model=list[DebtRead])
async def get_debts(
  session: SessionDep,
  debtor_id: int | None = None,
  creditor_id: int | None = None,
  event_id: int | None = None,
  is_settled: bool | None = None,
):
  query = select(Debt).options(selectinload(Debt.debtor))

  if debtor_id is not None:
    query = query.where(Debt.debtor_id == debtor_id)

  if is_settled is not None:
    query = query.where(Debt.is_settled == is_settled)

  # кредитор и событие хранятся в трате, а не в долге
  if creditor_id is not None or event_id is not None:
    query = query.join(Debt.expense)

    if creditor_id is not None:
      query = query.where(Expense.payer_id == creditor_id)

    if event_id is not None:
      query = query.where(Expense.event_id == event_id)

  debts = (await session.scalars(query.order_by(Debt.id))).all()

  return debts

@router.get("/expenses/{expense_id}/debts", response_model=list[DebtRead])
async def get_expense_debts(session: SessionDep, expense_id: int):
  expense = await session.get(Expense, expense_id)

  if expense is None:
    raise HTTPException(status_code=404, detail="Expense not found")

  debts = (await session.scalars(
    select(Debt).where(Debt.expense_id == expense_id).options(selectinload(Debt.debtor))
  )).all()

  return debts

@router.patch("/debts/{debt_id}", response_model=DebtRead)
async def update_debt(session: SessionDep, debt_id: int, data: DebtUpdate):
  debt = await session.scalar(
    select(Debt).where(Debt.id == debt_id).options(selectinload(Debt.debtor))
  )

  if debt is None:
    raise HTTPException(status_code=404, detail="Debt not found")

  debt.is_settled = data.is_settled
  await session.commit()

  return debt
