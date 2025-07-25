from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.dynamic_json.types import FieldType, field_types_list
from src.models import Base
from src.schemas import (
    TrackerCreate,
    TrackerDataCreate,
    TrackerStructureCreate,
    UserCreate,
)
from src.schemas.user import UserResponse
from src.services.database import DataService, TrackerService, UserService
from tests.config import config


@pytest.fixture
async def async_session_factory():
    engine = create_async_engine(
        config.DB_URL,
        echo=True,
        pool_size=10,
        max_overflow=20,
        future=True,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield AsyncSessionLocal

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Data mocks


@pytest.fixture
def sample_user_create():
    return UserCreate(id="123")


@pytest.fixture
async def sample_user_created(
    sample_user_create: UserCreate, user_service: UserService
):
    return await user_service.create(sample_user_create.id)


@pytest.fixture
def sample_tracker_create(sample_user_created: UserResponse):
    return TrackerCreate(name="name", user_id=sample_user_created.id)


@pytest.fixture
def sample_tracker_structure() -> FieldType:
    structure: FieldType = {}
    for i in field_types_list:
        structure[f"{i}_name"] = {"type": i}
        if i == "enum":
            structure[f"{i}_name"]["values"] = "val1/val2/val3"

    return structure


@pytest.fixture
def sample_tracker_data(sample_tracker_structure: FieldType) -> dict[str, Any]:
    import random
    import string

    data = {}
    for name, props in sample_tracker_structure.items():
        match props["type"]:
            case "int":
                value = random.randint(-10, 10)
            case "float":
                value = random.uniform(-10, 10)
            case "string":
                value = "".join(
                    random.choices(string.ascii_letters + string.digits, k=5)
                )
            case "enum":
                value = random.choice(props["values"].split("/"))  # type: ignore
            case _:
                raise ValueError()

        data[name] = value
    return data


@pytest.fixture
def sample_tracker_structure_create(sample_tracker_structure):
    return TrackerStructureCreate(data=sample_tracker_structure)


@pytest.fixture
def sample_tracker_data_create(sample_tracker_created):
    return TrackerDataCreate(
        tracker_id=sample_tracker_created.id, data={"data1": "1", "data2": "yes"}
    )


@pytest.fixture
async def sample_tracker_created(
    sample_tracker_create,
    sample_tracker_structure_create,
    tracker_service: TrackerService,
):
    return await tracker_service.create(
        tracker=sample_tracker_create, structure=sample_tracker_structure_create
    )


# Services mocks


@pytest.fixture
def tracker_service(async_session_factory):
    return TrackerService(async_session_factory)


@pytest.fixture
def user_service(async_session_factory):
    return UserService(async_session_factory)


@pytest.fixture
def data_service(async_session_factory):
    return DataService(async_session_factory)
