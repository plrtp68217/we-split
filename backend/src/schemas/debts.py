from pydantic import BaseModel
from decimal import Decimal
from src.schemas.users import UserRead


class DebtRead(BaseModel):
  id: int
  amount: Decimal
  debtor: UserRead