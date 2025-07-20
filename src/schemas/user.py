from pydantic import BaseModel


class UserCreate(BaseModel):
    id: str


class UserResponse(UserCreate):
    pass
