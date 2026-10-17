from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


if TYPE_CHECKING:
    from src.models.event_user import EventUser
    from src.models.expense import Expense


class Event(TimestampMixin, Base):
    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))

    events_users: Mapped[list['EventUser']] = relationship(back_populates='event')
    expenses: Mapped[list['Expense']] = relationship(back_populates='event')