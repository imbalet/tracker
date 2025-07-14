from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.schemas import (
    TrackerResponse,
    TrackerStructureCreate,
    TrackerCreate,
    TrackerDataCreate,
    TrackerDataResponse,
)
from src.models import TrackerDataOrm, TrackerOrm, TrackerStructureOrm


class TrackerService:

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def create(
        self, tracker: TrackerCreate, structure: TrackerStructureCreate
    ) -> TrackerResponse:
        async with self.session_factory() as session:
            new_structure = TrackerStructureOrm(data=structure.data)
            session.add(new_structure)
            await session.flush()
            new_tracker = TrackerOrm(
                structure_id=new_structure.id,
                user_id=tracker.user_id,
                name=tracker.name,
            )
            session.add(new_tracker)
            await session.commit()
            await session.refresh(new_tracker)
            return TrackerResponse.model_validate(new_tracker, from_attributes=True)

    async def add_data(self, data: TrackerDataCreate):
        async with self.session_factory() as session:
            new_data = TrackerDataOrm(tracker_id=data.tracker_id, data=data.data)
            session.add(new_data)
            await session.commit()
            await session.refresh(new_data)
            return TrackerDataResponse.model_validate(new_data, from_attributes=True)
