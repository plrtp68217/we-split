from pydantic import BaseModel, Field, field_validator


class EventRead(BaseModel):
  id: int
  name: str

class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    user_ids: list[int]

    @field_validator('user_ids')
    @classmethod
    def check_unique_user_ids(cls, user_ids: list[int]) -> list[int]:
        if len(set(user_ids)) != len(user_ids):
            raise ValueError("user_ids must be unique")
        return user_ids

class EventUserAdd(BaseModel):
    user_id: int
