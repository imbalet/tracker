from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from src.services.database import TrackerService, UserService


@pytest.fixture
def user_service():
    service = AsyncMock(spec=UserService)
    return service


@pytest.fixture
def tracker_service():
    service = AsyncMock(spec=TrackerService)
    return service


@pytest.fixture
def state():
    return FSMContext(
        storage=MemoryStorage(), key=StorageKey(bot_id=0, chat_id=0, user_id=0)
    )
