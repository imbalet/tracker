import pytest

from schemas.tracker import TrackerResponse
from src.use_cases import (
    GetUserTrackersUseCase,
    HandleFieldValueUseCase,
    ValidateTrackingMessageUseCase,
)


async def test_valid_get_user_trackers(
    sample_tracker_response: TrackerResponse, tracker_service_mock
):
    user_id = "user_id"
    tracker_service_mock.get_by_user_id.return_value = [
        sample_tracker_response,
        sample_tracker_response,
    ]

    uc = GetUserTrackersUseCase(tracker_service=tracker_service_mock)
    res, err = await uc.execute(user_id=user_id)

    assert not err
    assert res is not None
    assert len(res) == 2
    assert res[0] == sample_tracker_response and res[1] == sample_tracker_response
    tracker_service_mock.get_by_user_id.assert_awaited_once()


async def test_no_trackers_get_user_trackers(tracker_service_mock):
    user_id = "user_id"
    tracker_service_mock.get_by_user_id.return_value = []

    uc = GetUserTrackersUseCase(tracker_service=tracker_service_mock)
    _, err = await uc.execute(user_id=user_id)

    assert err == GetUserTrackersUseCase.Error.NO_TRACKERS
    tracker_service_mock.get_by_user_id.assert_awaited_once()


@pytest.mark.parametrize(
    "input, expected_name",
    [
        ("/track tracker", "tracker"),
        ("/track      tracker     ", "tracker"),
        ("/track tra cker", "tra cker"),
    ],
)
def test_valid_validate_tracking_message(input: str, expected_name: str):
    uc = ValidateTrackingMessageUseCase()
    tracker_name, err = uc.execute(text=input)

    assert not err
    assert tracker_name == expected_name


@pytest.mark.parametrize(
    "input",
    [
        None,
        "",
        "    ",
        "tracker",
    ],
)
def test_no_text_validate_tracking_message(input: str):
    uc = ValidateTrackingMessageUseCase()
    _, err = uc.execute(text=input)

    assert err == ValidateTrackingMessageUseCase.Error.NO_TEXT


@pytest.mark.parametrize(
    "field_name, field_value",
    [
        ("int_name", "10"),
        ("float_name", "15.5"),
        ("string_name", "string"),
    ],
)
async def test_valid_no_saving_handle_field_value(
    field_name: str,
    field_value: str,
    sample_tracker_response: TrackerResponse,
    tracker_service_mock,
):
    field_values = {"enum_name": "val1", field_name: field_value}
    uc = HandleFieldValueUseCase(tracker_service=tracker_service_mock)
    res, err = await uc.execute(
        tracker=sample_tracker_response,
        field_name=field_name,
        field_value=field_value,
        field_values=field_values,
    )

    assert not err
    assert res is False
    tracker_service_mock.add_data.assert_not_awaited()


async def test_valid_saving_handle_field_value(
    sample_tracker_response: TrackerResponse,
    tracker_service_mock,
):
    field_values = {
        "enum_name": "val1",
        "int_name": "10",
        "float_name": "15.5",
        "string_name": "string",
    }
    uc = HandleFieldValueUseCase(tracker_service=tracker_service_mock)
    res, err = await uc.execute(
        tracker=sample_tracker_response,
        field_name="string_name",
        field_value="string",
        field_values=field_values,
    )

    assert not err
    assert res is True
    tracker_service_mock.add_data.assert_awaited_once()


@pytest.mark.parametrize(
    "field_value",
    [
        None,
        "",
        "    ",
    ],
)
async def test_no_text_handle_field_value(
    field_value: str,
    sample_tracker_response: TrackerResponse,
    tracker_service_mock,
):
    uc = HandleFieldValueUseCase(tracker_service=tracker_service_mock)
    _, err = await uc.execute(
        tracker=sample_tracker_response,
        field_name="string_name",
        field_value=field_value,
        field_values={},
    )

    assert err == HandleFieldValueUseCase.Error.NO_TEXT
    tracker_service_mock.add_data.assert_not_awaited()
