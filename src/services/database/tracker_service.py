from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.exceptions import NotFoundException
from src.models import TrackerDataOrm, TrackerOrm, TrackerStructureOrm
from src.schemas import (
    TrackerCreate,
    TrackerDataCreate,
    TrackerDataResponse,
    TrackerResponse,
    TrackerStructureCreate,
)


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

    async def get_by_name(self, name: str) -> TrackerResponse:
        async with self.session_factory() as session:
            stmt = select(TrackerOrm).filter_by(name=name)
            res = await session.execute(stmt)
            result = res.scalar_one_or_none()
            if result is None:
                raise NotFoundException(f"Tracker with name {name} not found")
            return TrackerResponse.model_validate(result, from_attributes=True)

    async def get_by_id(self, tracker_id: UUID) -> TrackerResponse:
        async with self.session_factory() as session:
            res = await session.get(TrackerOrm, tracker_id)
            if res is None:
                raise NotFoundException(f"Tracker with id {tracker_id} not found")
            return TrackerResponse.model_validate(res, from_attributes=True)

    async def get_by_user_id(self, user_id: str) -> list[TrackerResponse]:
        async with self.session_factory() as session:
            stmt = select(TrackerOrm).filter_by(user_id=user_id)
            res = await session.execute(stmt)
            result = res.scalars().all()
            if result is None:
                raise NotFoundException(f"Trackers with user_id {user_id} not found")
            return [
                TrackerResponse.model_validate(i, from_attributes=True) for i in result
            ]

    async def add_data(self, data: TrackerDataCreate) -> TrackerDataResponse:
        async with self.session_factory() as session:
            new_data = TrackerDataOrm(tracker_id=data.tracker_id, data=data.data)
            session.add(new_data)
            await session.commit()
            await session.refresh(new_data)
            return TrackerDataResponse.model_validate(new_data, from_attributes=True)
