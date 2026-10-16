from sqlalchemy import ForeignKey, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from decimal import Decimal

from src.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), index=True)
    email: Mapped[str] = mapped_column(unique=True)

    events_users: Mapped[list['EventUser']] = relationship(back_populates='user')
    expenses: Mapped[list['Expense']] = relationship(back_populates='payer')
    debts: Mapped[list['Debt']] = relationship(back_populates='debtor')


class Event(TimestampMixin, Base):
    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))

    events_users: Mapped[list['EventUser']] = relationship(back_populates='event')
    expenses: Mapped[list['Expense']] = relationship(back_populates='event')


class EventUser(Base):
    __tablename__ = 'events_users'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True,)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'), primary_key=True,)

    user: Mapped['User'] = relationship(back_populates='events_users')
    event: Mapped['Event'] = relationship(back_populates='events_users')


class Expense(TimestampMixin, Base):
    __tablename__ = 'expenses'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'))
    payer_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    event: Mapped['Event'] = relationship(back_populates='expenses')
    payer: Mapped['User'] = relationship(back_populates='expenses')
    debts: Mapped[list['Debt']] = relationship(back_populates='expense')


class Debt(Base):
    __tablename__ = 'debts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_settled: Mapped[bool] = mapped_column(default=False)

    debtor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    expense_id: Mapped[int] = mapped_column(ForeignKey('expenses.id'))

    debtor: Mapped['User'] = relationship(back_populates='debts')
    expense: Mapped['Expense'] = relationship(back_populates='debts')