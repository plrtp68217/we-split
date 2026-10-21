from pydantic import BaseModel
from decimal import Decimal
from typing import Literal

from src.schemas.users import UserRead
from src.schemas.debts import DebtRead

class ShareIn(BaseModel):
    user_id: int
    amount: Decimal

class ExpenseRead(BaseModel):
  id: int
  name: str
  amount: Decimal
  payer: UserRead
  debts: list[DebtRead]

class ExpenseCreate(BaseModel):
  name: str
  amount: Decimal
  payer_id: int
  split_type: Literal["equal", "custom"]
  shares: list[ShareIn] = []