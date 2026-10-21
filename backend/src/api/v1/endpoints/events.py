from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import or_, select

from src.api.v1.dependencies import SessionDep
from src.schemas.events import EventRead, EventCreate, EventUserAdd
from src.schemas.users import UserRead
from src.models import Event, EventUser, User, Debt, Expense

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/{event_id}", response_model=EventRead)
async def get_event(session: SessionDep, event_id: int):
  event = await session.scalar(select(Event).where(Event.id == event_id))
  
  if event is None:
     raise HTTPException(status_code=404, detail="Event not found")
  
  return event

@router.get("/{event_id}/users", response_model=list[UserRead])
async def get_users_in_event(session: SessionDep, event_id: int):
  event = await session.scalar(select(Event).where(Event.id == event_id))
    
  if event is None:
     raise HTTPException(status_code=404, detail="Event not found")

  users = [eu.user for eu in event.events_users]

  return users

@router.post("/", response_model=EventRead)
async def create_event(session: SessionDep, data: EventCreate):
  existing_ids = set(await session.scalars(select(User.id).where(User.id.in_(data.user_ids))))
  missing_ids = set(data.user_ids) - existing_ids

  if missing_ids:
    raise HTTPException(status_code=400, detail=f"Users not found: {sorted(missing_ids)}")

  event = Event(name=data.name)

  for user_id in data.user_ids:
    event.events_users.append(EventUser(user_id=user_id))

  session.add(event)
  await session.commit()
  await session.refresh(event)

  return event

@router.post("/{event_id}/users", response_model=UserRead, status_code=201)
async def add_user_to_event(session: SessionDep, event_id: int, data: EventUserAdd):
  event = await session.get(Event, event_id)

  if event is None:
    raise HTTPException(status_code=404, detail="Event not found")

  user = await session.get(User, data.user_id)

  if user is None:
    raise HTTPException(status_code=400, detail="User not found")

  if any(eu.user_id == data.user_id for eu in event.events_users):
    raise HTTPException(status_code=409, detail="User is already in event")

  session.add(EventUser(event_id=event_id, user_id=data.user_id))
  await session.commit()

  return user

@router.delete("/{event_id}", status_code=204)
async def delete_event(session: SessionDep, event_id: int):
  event = await session.scalar(select(Event).where(Event.id == event_id))

  if event is None:
    raise HTTPException(status_code=404, detail="Event not found")

  await session.delete(event)
  await session.commit()

  return Response(status_code=204)

@router.delete("/{event_id}/users/{user_id}", status_code=204)
async def delete_user_in_event(session: SessionDep, event_id: int, user_id: int):
  result = await session.execute(
    select(EventUser).where(
        EventUser.event_id == event_id,
        EventUser.user_id == user_id,
    )
  )
  
  event_user = result.scalar_one_or_none()

  if event_user is None:
    raise HTTPException(status_code=404, detail="User not found in event")

  # пользователь может быть и должником, и кредитором (плательщиком траты)
  unsettled_debt_id = await session.scalar(
    select(Debt.id)
    .join(Debt.expense)
    .where(
      Expense.event_id == event_id,
      Debt.is_settled.is_(False),
      or_(Debt.debtor_id == user_id, Expense.payer_id == user_id),
    )
    .limit(1)
  )

  if unsettled_debt_id is not None:
    raise HTTPException(status_code=409, detail="User has unsettled debts in this event")

  await session.delete(event_user)
  await session.commit()

  return Response(status_code=204)