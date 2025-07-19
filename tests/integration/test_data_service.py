from datetime import datetime, timezone, timedelta
from sqlalchemy import update
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from src.services.database import DataService, TrackerService
from src.schemas import (
    TrackerDataCreate,
    TrackerResponse,
)
from src.models import TrackerDataOrm


def generate_tracker_data(structure: dict, num: int):
    import random

    for _ in range(num):
        data = {}
        for name, type in structure.items():
            if type == "int":
                value = random.randint(-10, 10)
            elif "/" in type:
                value = random.choice(type.split("/"))
            elif type == "float":
                value = random.uniform(-10, 10)
            else:
                raise ValueError(f"Incorrect type value {type}")
            data[name] = value
        yield data


async def insert_data(
    data: list,
    tracker_service: TrackerService,
    sample_tracker: TrackerResponse,
):
    return [
        await tracker_service.add_data(
            TrackerDataCreate(tracker_id=sample_tracker.id, data=i)
        )
        for i in data
    ]


async def test_valid_get_field(
    sample_tracker: TrackerResponse,
    tracker_service: TrackerService,
    data_service: DataService,
):
    data = [i for i in generate_tracker_data(sample_tracker.structure.data, 10)]
    await insert_data(data, tracker_service, sample_tracker)

    res = await data_service.get_field_by_name(
        tracker_id=sample_tracker.id, name="data1"
    )
    assert len(res) == len(data)


async def test_valid_get_sum_fields_days(
    sample_tracker: TrackerResponse,
    tracker_service: TrackerService,
    data_service: DataService,
    async_session_factory: async_sessionmaker,
):
    data = [i for i in generate_tracker_data(sample_tracker.structure.data, 10)]
    inserted = await insert_data(data, tracker_service, sample_tracker)
    async with async_session_factory() as session:
        for idx, el in enumerate(inserted):
            stmt = (
                update(TrackerDataOrm)
                .filter_by(id=el.id)
                .values(created_at=datetime.now(timezone.utc) + timedelta(days=idx))
            )
            await session.execute(stmt)
            await session.commit()

    res = await data_service.get_field_aggregation_days(
        tracker_id=sample_tracker.id,
        aggregates=["sum", "avg", "max", "min"],
        field="data1",
        interval="day",
    )
    assert res


async def test_valid_get_sum_fields_interval(
    sample_tracker: TrackerResponse,
    tracker_service: TrackerService,
    data_service: DataService,
    async_session_factory: async_sessionmaker,
):
    data = [i for i in generate_tracker_data(sample_tracker.structure.data, 10)]
    inserted = await insert_data(data, tracker_service, sample_tracker)
    async with async_session_factory() as session:
        for idx, el in enumerate(inserted):
            stmt = (
                update(TrackerDataOrm)
                .filter_by(id=el.id)
                .values(created_at=datetime.now(timezone.utc) + timedelta(days=idx))
            )
            await session.execute(stmt)
            await session.commit()

    res = await data_service.get_sum_field(
        tracker_id=sample_tracker.id,
        aggregates=["sum", "avg", "max", "min"],
        field="data1",
        interval=2,
    )
    assert res
