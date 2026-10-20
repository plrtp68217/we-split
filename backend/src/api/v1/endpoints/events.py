from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select

from src.api.v1.dependencies import SessionDep
from src.schemas.events import EventRead, EventCreate
from src.schemas.users import UserRead
from src.models import Event, EventUser

router = APIRouter()

@router.get("/events/{event_id}", response_model=EventRead)
async def get_event(session: SessionDep, event_id: int):
  event = await session.scalar(select(Event).where(Event.id == event_id))
  
  if event is None:
     raise HTTPException(status_code=404, detail="Event not found")
  
  return event

@router.get("/events/{event_id}/users", response_model=list[UserRead])
async def get_users_in_event(session: SessionDep, event_id: int):
  event = await session.scalar(select(Event).where(Event.id == event_id))
    
  if event is None:
     raise HTTPException(status_code=404, detail="Event not found")

  users = [eu.user for eu in event.events_users]

  return users

@router.post("/events", response_model=EventRead)
async def create_event(session: SessionDep, data: EventCreate):
  event = Event(name=data.name)

  for user_id in data.user_ids:
    event.events_users.append(EventUser(user_id=user_id))

  session.add(event)
  await session.commit()

  return event

@router.delete("/events/{event_id}", status_code=204)
async def delete_event(session: SessionDep, event_id: int):
  event = await session.scalar(select(Event).where(Event.id == event_id))

  if event is None:
    raise HTTPException(status_code=404, detail="Event not found")

  await session.delete(event)
  await session.commit()

  return Response(status_code=204)

@router.delete("/events/{event_id}/users/{user_id}", status_code=204)
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

  await session.delete(event_user)
  await session.commit()

  return Response(status_code=204)