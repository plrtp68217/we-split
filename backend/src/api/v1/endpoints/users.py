from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.api.v1.dependencies import SessionDep
from src.schemas.users import UserResponse, UserRequest, UserUpdate
from src.models import User

router = APIRouter()

@router.get("/users", response_model=list[UserResponse])
async def get_all_users(session: SessionDep):
  users = (await session.scalars(select(User))).all()

  return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(session: SessionDep, user_id: int):
  user = await session.scalar(select(User).where(User.id == user_id))

  if user is None:
    raise HTTPException(status_code=404, detail="User not found")

  return user

@router.post("/users",  response_model=UserResponse, status_code=201)
async def create_user(session: SessionDep, data: UserRequest):
  user = User(**data.model_dump())
  session.add(user)
  try:
    await session.commit()
  except IntegrityError:
    await session.rollback()
    raise HTTPException(status_code=409, detail="User with this email already exists")

  return user


@router.patch("/users/{user_id}", response_model=UserResponse)
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


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(session: SessionDep, user_id: int):
  user = await session.scalar(select(User).where(User.id == user_id))

  if user is None:
    raise HTTPException(status_code=404, detail="User not found")

  await session.delete(user)
  await session.commit()