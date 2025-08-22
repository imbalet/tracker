import pytest
from pytest_mock import MockerFixture

from src.services.database.data_service import DataService


@pytest.fixture
def data_service_mock(mocker: MockerFixture):
    mock = mocker.Mock(spec=DataService)
    return mock
