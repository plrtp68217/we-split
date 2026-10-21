from pydantic import BaseModel
from decimal import Decimal
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
