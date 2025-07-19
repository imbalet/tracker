from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    chat_id: str


class UserResponse(UserCreate):
    id: UUID
