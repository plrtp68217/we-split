from pydantic import BaseModel, Field, model_validator
from decimal import Decimal
from typing import Annotated, Literal, Self

from src.schemas.users import UserRead
from src.schemas.debts import DebtRead

# совпадает с Numeric(10, 2) в моделях
Money = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]

class ShareIn(BaseModel):
    user_id: int
    amount: Money

class ExpenseRead(BaseModel):
  id: int
  name: str
  amount: Decimal
  payer: UserRead
  debts: list[DebtRead]

class ExpenseCreate(BaseModel):
  name: str = Field(min_length=1, max_length=50)
  amount: Money
  payer_id: int
  split_type: Literal["equal", "custom"]
  shares: list[ShareIn] = []

  @model_validator(mode='after')
  def check_shares(self) -> Self:
    if self.split_type == "equal":
      if self.shares:
        raise ValueError("shares are only allowed for custom split")
      return self

    if not self.shares:
      raise ValueError("shares are required for custom split")

    user_ids = [share.user_id for share in self.shares]
    if len(set(user_ids)) != len(user_ids):
      raise ValueError("shares must have unique user_id")

    return self
