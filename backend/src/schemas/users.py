from pydantic import BaseModel, Field


class UserRead(BaseModel):
  id: int
  name: str
  email: str

class UserCreate(BaseModel):
  name: str = Field(min_length=1, max_length=50)
  email: str

class UserUpdate(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=50)
  email: str | None = None