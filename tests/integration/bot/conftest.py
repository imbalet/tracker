from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from tracker.presentation.utils.keyboard import KeyboardBuilder
from tracker.presentation.utils.translations import _t
from tracker.services.database import TrackerService, UserService


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


@pytest.fixture
def lang():
    return "ru"


@pytest.fixture
def t_(lang):
    return lambda text, **kwargs: _t(lang=lang, key=text, **kwargs)


@pytest.fixture
def kbr_builder(t_):
    return KeyboardBuilder(t=t_)
