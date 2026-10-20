from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.api.v1.dependencies import SessionDep
from src.schemas.users import UserRead, UserCreate, UserUpdate
from src.schemas.events import EventRead
from src.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserRead])
async def get_all_users(session: SessionDep):
  users = (await session.scalars(select(User))).all()

  return users

@router.get("/{user_id}", response_model=UserRead)
async def get_user(session: SessionDep, user_id: int):
  user = await session.scalar(select(User).where(User.id == user_id))

  if user is None:
    raise HTTPException(status_code=404, detail="User not found")

  return user

@router.get("/{user_id}/events", response_model=list[EventRead])
async def get_events_in_user(session: SessionDep, user_id: int):
  user = await session.scalar(select(User).where(User.id == user_id))
  
  if user is None:
    raise HTTPException(status_code=404, detail="User not found")

  events = [eu.event for eu in user.events_users]

  return events

@router.post("/",  response_model=UserRead, status_code=201)
async def create_user(session: SessionDep, data: UserCreate):
  user = User(**data.model_dump())
  session.add(user)
  try:
    await session.commit()
  except IntegrityError:
    await session.rollback()
    raise HTTPException(status_code=409, detail="User with this email already exists")

  await session.refresh(user)

  return user

@router.patch("/{user_id}", response_model=UserRead)
async def update_user(session: SessionDep, user_id: int, data: UserUpdate):
  user = await session.scalar(select(User).where(User.id == user_id))

  if user is None:
    raise HTTPException(status_code=404, detail="User not found")

  for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
    setattr(user, field, value)

  try:
    await session.commit()
  except IntegrityError:
    await session.rollback()
    raise HTTPException(status_code=409, detail="User with this email already exists")

  return user

@router.delete("/{user_id}", status_code=204)
async def delete_user(session: SessionDep, user_id: int):
  user = await session.scalar(select(User).where(User.id == user_id))

  if user is None:
    raise HTTPException(status_code=404, detail="User not found")

  await session.delete(user)
  await session.commit()

  return Response(status_code=204)