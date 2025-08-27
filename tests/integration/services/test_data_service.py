import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from tracker.models import TrackerDataOrm
from tracker.schemas import (
    TrackerDataCreate,
    TrackerResponse,
)
from tracker.services.database import DataService, TrackerService


def generate_tracker_data(structure: dict, num: int):
    import random

    for _ in range(num):
        data = {}
        for name, props in structure.items():
            if props["type"] == "int":
                value = random.randint(-10, 10)
            elif props["type"] == "enum":
                value = random.choice(props["type"].split("/"))
            elif props["type"] == "float":
                value = random.uniform(-10, 10)
            elif props["type"] == "string":
                value = "".join(
                    random.choices(string.ascii_letters + string.digits, k=5)
                )
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
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
    data_service: DataService,
):
    data = [i for i in generate_tracker_data(sample_tracker_created.structure.data, 10)]
    await insert_data(data, tracker_service, sample_tracker_created)

    res = await data_service.get_field_by_name(
        tracker_id=sample_tracker_created.id, name="int_name"
    )
    assert len(res) == len(data)


async def test_valid_get_sum_fields_days(
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
    data_service: DataService,
    async_session_factory: async_sessionmaker,
):
    data = [i for i in generate_tracker_data(sample_tracker_created.structure.data, 10)]
    inserted = await insert_data(data, tracker_service, sample_tracker_created)
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
        tracker_id=sample_tracker_created.id,
        aggregates=["sum", "avg", "max", "min"],
        field="data1",
        interval="day",
    )
    assert res


async def test_valid_get_sum_fields_interval(
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
    data_service: DataService,
    async_session_factory: async_sessionmaker,
):
    data = [i for i in generate_tracker_data(sample_tracker_created.structure.data, 10)]
    inserted = await insert_data(data, tracker_service, sample_tracker_created)
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
        tracker_id=sample_tracker_created.id,
        aggregates=["sum", "avg", "max", "min"],
        field="data1",
        interval=2,
    )
    assert res


async def test_valid_get_all_data(
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
    data_service: DataService,
):
    data = [i for i in generate_tracker_data(sample_tracker_created.structure.data, 10)]
    inserted = await insert_data(data, tracker_service, sample_tracker_created)

    res = await data_service.get_all_data(tracker_id=sample_tracker_created.id)
    assert len(res) == 10
    assert res[0].value == inserted[0].data
    assert "int_name" in res[0].value
    assert "float_name" in res[0].value


async def test_valid_get_all_data_filter_fields(
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
    data_service: DataService,
):
    data = [i for i in generate_tracker_data(sample_tracker_created.structure.data, 10)]
    _ = await insert_data(data, tracker_service, sample_tracker_created)

    res = await data_service.get_all_data(
        tracker_id=sample_tracker_created.id, exclude_fields=["int_name", "float_name"]
    )
    assert len(res) == 10
    assert "int_name" not in res[0].value
    assert "float_name" not in res[0].value


async def test_valid_get_statistics_all_fields(
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
    data_service: DataService,
):
    data = [i for i in generate_tracker_data(sample_tracker_created.structure.data, 10)]
    _ = await insert_data(data, tracker_service, sample_tracker_created)

    res = await data_service.get_statistics(
        sample_tracker_created.id,
        numeric_fields=["int_name", "float_name"],
        categorical_fields=["string_name", "enum_name"],
    )

    for field in res:
        assert field.count
        if field.type == "numeric":
            assert field.min
            assert field.max
            assert field.avg
            assert field.sum
        if field.type == "categorical":
            assert field.mode
