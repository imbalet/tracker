import csv
from datetime import datetime
from typing import cast
from uuid import uuid4

from src.schemas import DataResult, StaticticsTrackerData
from src.services.database.data_service import DataService
from src.use_cases import (
    GetCSVUseCase,
    GetStatisticsUseCase,
)


async def test_valid_get_csv(data_service_mock):
    data_service_mock.get_all_data.return_value = [
        DataResult(date=datetime.now(), value={"int": 123}),
        DataResult(date=datetime.now(), value={"int": 321}),
    ]
    data_service_mock = cast(DataService, data_service_mock)

    uc = GetCSVUseCase(data_service=data_service_mock)
    res = await uc.execute(tracker_id=uuid4(), from_date=datetime.now())

    assert res

    content = res.getvalue().decode("utf-8")
    reader = csv.reader(content.splitlines())
    rows = list(reader)

    assert rows[0] == ["date", "int"]
    assert rows[1][1] == "123"
    assert rows[2][1] == "321"


async def test_valid_get_csv_with_comma(data_service_mock):
    data_service_mock.get_all_data.return_value = [
        DataResult(date=datetime.now(), value={"tex, t": "text, 1"}),
        DataResult(date=datetime.now(), value={"tex, t": "text, 2"}),
    ]
    data_service_mock = cast(DataService, data_service_mock)

    uc = GetCSVUseCase(data_service=data_service_mock)
    res = await uc.execute(tracker_id=uuid4(), from_date=datetime.now())

    assert res

    content = res.getvalue().decode("utf-8")
    reader = csv.reader(content.splitlines())
    rows = list(reader)

    assert rows[0] == ["date", "tex, t"]
    assert rows[1][1] == "text, 1"
    assert rows[2][1] == "text, 2"


async def test_empty_get_csv(data_service_mock):
    data_service_mock.get_all_data.return_value = []
    data_service_mock = cast(DataService, data_service_mock)

    uc = GetCSVUseCase(data_service=data_service_mock)
    res = await uc.execute(tracker_id=uuid4(), from_date=datetime.now())

    assert res is None


async def test_valid_get_statistics(data_service_mock):
    data_service_mock.get_statistics.return_value = [
        StaticticsTrackerData(
            type="numeric", min=1, max=1, avg=1, sum=1, count=1, field_name="int"
        ),
        StaticticsTrackerData(type="categorial", mode="1", count=1, field_name="name"),
    ]
    data_service_mock = cast(DataService, data_service_mock)

    uc = GetStatisticsUseCase(data_service=data_service_mock)
    res = await uc.execute(
        tracker_id=uuid4(),
        numeric_fields=["int"],
        categorial_fields=["name"],
        from_date=datetime.now(),
    )
    assert res


async def test_empty_get_statistics(data_service_mock):
    data_service_mock.get_statistics.return_value = []
    data_service_mock = cast(DataService, data_service_mock)

    uc = GetStatisticsUseCase(data_service=data_service_mock)
    res = await uc.execute(
        tracker_id=uuid4(),
        numeric_fields=["int"],
        categorial_fields=["name"],
        from_date=datetime.now(),
    )

    assert res == []
