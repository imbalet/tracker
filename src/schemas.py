from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    chat_id: str


class UserResponse(UserCreate):
    id: UUID


class TrackerDataCreate(BaseModel):
    tracker_id: UUID
    data: dict


class TrackerDataResponse(TrackerDataCreate):
    id: UUID
    created_at: datetime


class TrackerStructureCreate(BaseModel):
    data: dict


class TrackerStructureResponse(TrackerStructureCreate):
    id: UUID


class TrackerCreate(BaseModel):
    name: str
    user_id: UUID


class TrackerResponse(TrackerCreate):
    id: UUID
    user: UserResponse
    created_at: datetime
    structure: TrackerStructureResponse
    data: list[TrackerDataResponse]
    structure_id: UUID
