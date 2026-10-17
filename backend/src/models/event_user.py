from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.event import Event

class EventUser(Base):
    __tablename__ = 'events_users'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True,)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'), primary_key=True,)

    user: Mapped['User'] = relationship(back_populates='events_users')
    event: Mapped['Event'] = relationship(back_populates='events_users')