from typing import TYPE_CHECKING

from sqlalchemy import Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from src.models.base import Base


if TYPE_CHECKING:
    from src.models.user import User
    from src.models.expense import Expense


class Debt(Base):
    __tablename__ = 'debts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_settled: Mapped[bool] = mapped_column(default=False)

    debtor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    expense_id: Mapped[int] = mapped_column(ForeignKey('expenses.id'))

    debtor: Mapped['User'] = relationship(back_populates='debts')
    expense: Mapped['Expense'] = relationship(back_populates='debts')