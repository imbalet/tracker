import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import Base
from src.schemas import (
    TrackerCreate,
    TrackerDataCreate,
    TrackerStructureCreate,
    UserCreate,
)
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


@pytest.fixture
def sample_user_data():
    return UserCreate(chat_id="chat_id")


@pytest.fixture
async def sample_user(sample_user_data, user_service: UserService):
    return await user_service.create(sample_user_data.chat_id)


@pytest.fixture
def sample_tracker_data(sample_user):
    return TrackerCreate(name="name", user_id=sample_user.id)


@pytest.fixture
def sample_tracker_structure_data():
    return TrackerStructureCreate(data={"data1": "int", "data2": "yes/no"})


@pytest.fixture
def sample_tracker_data_data(sample_tracker):
    return TrackerDataCreate(
        tracker_id=sample_tracker.id, data={"data1": "1", "data2": "yes"}
    )


@pytest.fixture
async def sample_tracker(
    sample_tracker_data, sample_tracker_structure_data, tracker_service: TrackerService
):
    return await tracker_service.create(
        tracker=sample_tracker_data, structure=sample_tracker_structure_data
    )


@pytest.fixture
def tracker_service(async_session_factory):
    return TrackerService(async_session_factory)


@pytest.fixture
def user_service(async_session_factory):
    return UserService(async_session_factory)


@pytest.fixture
def data_service(async_session_factory):
    return DataService(async_session_factory)
