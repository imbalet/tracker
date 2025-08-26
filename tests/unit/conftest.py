import inspect
from unittest.mock import AsyncMock, create_autospec

import pytest

from src.services.database import DataService, TrackerService, UserService


@pytest.fixture
def service_mock_factory():
    def _make_mock(cls):
        mock = create_autospec(cls, instance=True)
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            if inspect.iscoroutinefunction(member):
                setattr(mock, name, AsyncMock())
        return mock

    return _make_mock


@pytest.fixture
def data_service_mock(service_mock_factory):
    return service_mock_factory(DataService)


@pytest.fixture
def user_service_mock(service_mock_factory):
    return service_mock_factory(UserService)


@pytest.fixture
def tracker_service_mock(service_mock_factory):
    return service_mock_factory(TrackerService)
