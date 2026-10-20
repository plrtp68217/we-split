from pydantic import BaseModel

class EventRead(BaseModel):
  id: int
  name: str

class EventCreate(BaseModel):
    name: str
    user_ids: list[int]