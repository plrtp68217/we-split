from pydantic import BaseModel


class UserResponse(BaseModel):
  id: int
  name: str
  email: str

class UserRequest(BaseModel):
  name: str
  email: str