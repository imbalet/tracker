import csv
from datetime import datetime
from uuid import uuid4

import pytest
from tracker.schemas import DataResult, StatisticsTrackerData, TrackerResponse
from tracker.use_cases import (
    GetCSVUseCase,
    GetStatisticsUseCase,
    HandleFieldUseCase,
    SplitFieldsByTypeUseCase,
    ValidatePeriodValueUseCase,
)


async def test_valid_get_csv(data_service_mock):
    data_service_mock.get_all_data.return_value = [
        DataResult(date=datetime.now(), value={"int": 123}),
        DataResult(date=datetime.now(), value={"int": 321}),
    ]

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

    uc = GetCSVUseCase(data_service=data_service_mock)
    res = await uc.execute(tracker_id=uuid4(), from_date=datetime.now())

    assert res is None


async def test_valid_get_statistics(data_service_mock):
    data_service_mock.get_statistics.return_value = [
        StatisticsTrackerData(
            type="numeric", min=1, max=1, avg=1, sum=1, count=1, field_name="int"
        ),
        StatisticsTrackerData(type="categorical", mode="1", count=1, field_name="name"),
    ]

    uc = GetStatisticsUseCase(data_service=data_service_mock)
    res, err = await uc.execute(
        tracker_id=uuid4(),
        numeric_fields=["int"],
        categorical_fields=["name"],
        from_date=datetime.now(),
    )
    assert err is None
    assert len(res) == 2
    data_service_mock.get_statistics.assert_awaited_once()


async def test_empty_get_statistics(data_service_mock):
    data_service_mock.get_statistics.return_value = []

    uc = GetStatisticsUseCase(data_service=data_service_mock)
    res, err = await uc.execute(
        tracker_id=uuid4(),
        numeric_fields=["int"],
        categorical_fields=["name"],
        from_date=datetime.now(),
    )

    assert err is None
    assert len(res) == 0
    data_service_mock.get_statistics.assert_awaited_once()


async def test_no_fields_get_statistics(data_service_mock):
    uc = GetStatisticsUseCase(data_service=data_service_mock)
    res, err = await uc.execute(
        tracker_id=uuid4(),
        numeric_fields=[],
        categorical_fields=[],
        from_date=datetime.now(),
    )

    assert err == GetStatisticsUseCase.Error.NO_FIELDS
    data_service_mock.get_statistics.assert_not_awaited()


@pytest.mark.parametrize(
    "input, expected_value",
    [
        ("123", 123),
        (" 123 ", 123),
        ("0123", 123),
    ],
)
def test_valid_validate_period_value(input: str, expected_value: int):
    uc = ValidatePeriodValueUseCase()
    res, err = uc.execute(text=input)

    assert err is None
    assert res == expected_value


@pytest.mark.parametrize(
    "input",
    [None, "", "   "],
)
def test_no_text_validate_period_value(
    input: str,
):
    uc = ValidatePeriodValueUseCase()
    _, err = uc.execute(text=input)

    assert err == ValidatePeriodValueUseCase.Error.NO_TEXT


@pytest.mark.parametrize(
    "input",
    [
        "not_number",
        "*123",
        "12 3" "12.3",
        "12,3",
        "-123",
    ],
)
def test_wrong_value_validate_period_value(
    input: str,
):
    uc = ValidatePeriodValueUseCase()
    _, err = uc.execute(text=input)

    assert err == ValidatePeriodValueUseCase.Error.WRONG_VALUE


@pytest.mark.parametrize(
    "selected_fields",
    [
        [],
        ["one"],
        ["one", "two"],
    ],
)
def test_valid_add_handle_field(selected_fields: list):
    uc = HandleFieldUseCase()
    field_list, text = uc.execute(field_name="name", selected_fields=selected_fields)

    assert text is not None
    assert "name" in field_list


@pytest.mark.parametrize(
    "selected_fields",
    [
        ["name"],
        ["name", "one"],
        ["name", "one", "two"],
    ],
)
def test_valid_remove_handle_field(selected_fields: list):
    uc = HandleFieldUseCase()
    field_list, text = uc.execute(field_name="name", selected_fields=selected_fields)

    assert text is not None
    assert "name" not in field_list


def test_valid_split_fields_by_type(
    sample_tracker_response: TrackerResponse,
):
    selected_fields = list(sample_tracker_response.structure.data)

    uc = SplitFieldsByTypeUseCase()
    numeric, categorical = uc.execute(
        selected_fields=selected_fields, tracker=sample_tracker_response
    )

    assert len(numeric) == 2
    assert "int_name" in numeric and "float_name" in numeric
    assert len(categorical) == 2
    assert "string_name" in categorical and "enum_name" in categorical


def test_empty_split_fields_by_type(
    sample_tracker_response: TrackerResponse,
):
    selected_fields = []

    uc = SplitFieldsByTypeUseCase()
    numeric, categorical = uc.execute(
        selected_fields=selected_fields, tracker=sample_tracker_response
    )

    assert len(numeric) == 0
    assert len(categorical) == 0
