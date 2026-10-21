from pydantic import BaseModel, model_validator
from decimal import Decimal
from typing import Self
from src.schemas.users import UserRead


class DebtRead(BaseModel):
  id: int
  amount: Decimal
  is_settled: bool
  expense_id: int
  debtor: UserRead

class DebtUpdate(BaseModel):
  is_settled: bool

class BalanceRead(BaseModel):
  from_user: UserRead
  to_user: UserRead
  amount: Decimal

class SettlementCreate(BaseModel):
  from_user_id: int
  to_user_id: int

  @model_validator(mode='after')
  def check_different_users(self) -> Self:
    if self.from_user_id == self.to_user_id:
      raise ValueError("from_user_id and to_user_id must be different")
    return self
