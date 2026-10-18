from typing import TYPE_CHECKING

from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from src.models.base import Base
from src.models.mixins.time_stamp import TimestampMixin


if TYPE_CHECKING:
    from src.models.user import User
    from src.models.event import Event
    from src.models.debt import Debt


class Expense(TimestampMixin, Base):
    __tablename__ = 'expenses'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'))
    payer_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))

    event: Mapped['Event'] = relationship(back_populates='expenses')
    payer: Mapped['User'] = relationship(back_populates='expenses')
    debts: Mapped[list['Debt']] = relationship(back_populates='expense', cascade='all, delete-orphan', passive_deletes=True)