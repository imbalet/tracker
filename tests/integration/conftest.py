import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tracker.models import Base
from tracker.schemas import (
    TrackerResponse,
    UserCreate,
    UserResponse,
)
from tracker.schemas.tracker import TrackerCreate
from tracker.services.database import DataService, TrackerService, UserService

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


@pytest.fixture
async def sample_user_created(
    sample_user_create: UserCreate, user_service: UserService
):
    return await user_service.create(sample_user_create.id)


@pytest.fixture
async def sample_tracker_created(
    sample_tracker_create: TrackerCreate,
    sample_user_created: UserResponse,
    tracker_service: TrackerService,
) -> TrackerResponse:
    return await tracker_service.create(tracker=sample_tracker_create)
