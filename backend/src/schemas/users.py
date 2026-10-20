from pydantic import BaseModel


class UserRead(BaseModel):
  id: int
  name: str
  email: str

class UserCreate(BaseModel):
  name: str
  email: str

class UserUpdate(BaseModel):
  name: str | None = None
  email: str | None = None