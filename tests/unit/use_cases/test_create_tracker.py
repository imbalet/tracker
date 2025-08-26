import pytest

from src.core.dynamic_json.types import FieldDataType
from src.schemas import (
    TrackerCreate,
    TrackerResponse,
    TrackerStructureCreate,
    UserResponse,
)
from src.use_cases import (
    CreateTrackerDraftUseCase,
    FinishTrackerCreation,
    ProcessEnumValuesUseCase,
    ProcessFieldNameUseCase,
)


@pytest.mark.parametrize(
    "input",
    [
        "name",
        ".",
        "123",
        " 123 ",
        " . . ",
    ],
)
def test_valid_create_draft(input: str):
    uc = CreateTrackerDraftUseCase()
    tracker_dto, err = uc.execute(name=input)

    assert not err
    assert tracker_dto
    assert tracker_dto.name == input.strip()
    assert tracker_dto.structure.data == {}


@pytest.mark.parametrize(
    "input",
    [
        None,
        "",
        "   ",
    ],
)
def test_empty_name_create_draft(input: str | None):
    uc = CreateTrackerDraftUseCase()
    _, err = uc.execute(name=input)

    assert err == CreateTrackerDraftUseCase.Error.NO_TEXT


@pytest.mark.parametrize(
    "input, expected_options",
    [
        ("yes/no", ["yes", "no"]),
        ("   yes/no  ", ["yes", "no"]),
        ("   yes  /  no  ", ["yes", "no"]),
        ("1/2/3", ["1", "2", "3"]),
        ("./,/!", [".", ",", "!"]),
    ],
)
def test_valid_process_enum_values(input: str, expected_options: list):
    uc = ProcessEnumValuesUseCase()
    options, err = uc.execute(text=input)

    assert not err
    assert options == expected_options


@pytest.mark.parametrize(
    "input, expected_options",
    [
        ("yes/yes/no", ["yes", "no"]),
        ("yes/no/yes", ["yes", "no"]),
        ("yes/no/no/yes", ["yes", "no"]),
    ],
)
def test_duplicates_process_enum_values(input: str, expected_options: list):
    uc = ProcessEnumValuesUseCase()
    options, err = uc.execute(text=input)

    assert not err
    assert options == expected_options


@pytest.mark.parametrize(
    "input, expected_error",
    [
        ("", ProcessEnumValuesUseCase.Error.NO_TEXT),
        (None, ProcessEnumValuesUseCase.Error.NO_TEXT),
        ("     ", ProcessEnumValuesUseCase.Error.NO_TEXT),
        ("////", ProcessEnumValuesUseCase.Error.WRONG_COUNT),
        ("//yes//", ProcessEnumValuesUseCase.Error.WRONG_COUNT),
        ("/yes/", ProcessEnumValuesUseCase.Error.WRONG_COUNT),
        ("yes/yes/yes", ProcessEnumValuesUseCase.Error.WRONG_COUNT),
        ("yes", ProcessEnumValuesUseCase.Error.WRONG_COUNT),
    ],
)
def test_invalid_process_enum_values(
    input: str, expected_error: ProcessEnumValuesUseCase.Error
):
    uc = ProcessEnumValuesUseCase()
    _, err = uc.execute(text=input)

    assert err == expected_error


@pytest.mark.parametrize(
    "field_type",
    ["int", "float", "string"],
)
def test_valid_process_field_name(field_type: FieldDataType):
    tracker = TrackerCreate(
        name="name", user_id="", structure=TrackerStructureCreate(data={})
    )
    field_name = "name"

    uc = ProcessFieldNameUseCase()
    tracker, err = uc.execute(
        field_name=field_name, field_type=field_type, tracker=tracker
    )

    assert not err and tracker
    assert len(tracker.structure.data) == 1
    assert field_name in tracker.structure.data
    assert tracker.structure.data[field_name]["type"] == field_type
    assert "values" not in tracker.structure.data[field_name]


@pytest.mark.parametrize(
    "field_type",
    ["int", "float", "string"],
)
def test_valid_with_existing_process_field_name(field_type: FieldDataType):
    src_tracker = TrackerCreate(
        name="name",
        user_id="",
        structure=TrackerStructureCreate(
            data={
                "field": {"type": "int"},
                "enum_field": {"type": "enum", "values": ["yes", "no"]},
            }
        ),
    )
    field_name = "name"

    uc = ProcessFieldNameUseCase()
    tracker, err = uc.execute(
        field_name=field_name, field_type=field_type, tracker=src_tracker.model_copy()
    )

    assert not err and tracker
    assert len(tracker.structure.data) == 3
    assert field_name in tracker.structure.data
    assert tracker.structure.data[field_name]["type"] == field_type
    assert "values" not in tracker.structure.data[field_name]
    assert "field" in tracker.structure.data
    assert tracker.structure.data["field"] == src_tracker.structure.data["field"]
    assert (
        tracker.structure.data["enum_field"] == src_tracker.structure.data["enum_field"]
    )
    assert "enum_field" in tracker.structure.data


def test_valid_enum_process_field_name():
    tracker = TrackerCreate(
        name="name", user_id="", structure=TrackerStructureCreate(data={})
    )
    field_name = "name"
    field_values = ["1", "2", "3"]

    uc = ProcessFieldNameUseCase()
    tracker, err = uc.execute(
        tracker=tracker,
        field_name=field_name,
        field_type="enum",
        enum_values=field_values,
    )

    assert not err and tracker
    assert len(tracker.structure.data) == 1
    assert field_name in tracker.structure.data
    assert tracker.structure.data[field_name]["type"] == "enum"
    assert "values" in tracker.structure.data[field_name]
    assert tracker.structure.data[field_name].get("values") == field_values


@pytest.mark.parametrize(
    "field_name, field_type, enum_values, expected_error",
    [
        ("", "int", [], ProcessFieldNameUseCase.Error.NO_TEXT),
        ("   ", "int", [], ProcessFieldNameUseCase.Error.NO_TEXT),
        ("int", "int", ["enum"], ProcessFieldNameUseCase.Error.WRONG_STRUCTURE),
        ("int", "enum", [], ProcessFieldNameUseCase.Error.WRONG_STRUCTURE),
    ],
)
def test_invalid_process_field_name(
    field_name: str,
    field_type: FieldDataType,
    enum_values: list | None,
    expected_error: ProcessFieldNameUseCase.Error,
):
    tracker = TrackerCreate(
        name="name", user_id="", structure=TrackerStructureCreate(data={})
    )

    uc = ProcessFieldNameUseCase()
    _, err = uc.execute(
        tracker=tracker,
        field_name=field_name,
        field_type=field_type,
        enum_values=enum_values,
    )

    assert err == expected_error


@pytest.mark.parametrize(
    "data",
    [
        {"name": {"type": "int"}},
        {"name": {"type": "enum", "values": ["1", "2"]}},
    ],
)
@pytest.mark.parametrize(
    "field_type",
    ["int", "float", "string"],
)
def test_invalid_already_exists_process_field_name(
    field_type: FieldDataType, data: dict
):
    tracker = TrackerCreate(
        name="name",
        user_id="",
        structure=TrackerStructureCreate(data=data),
    )

    uc = ProcessFieldNameUseCase()
    _, err = uc.execute(
        tracker=tracker,
        field_name="name",
        field_type=field_type,
    )

    assert err == ProcessFieldNameUseCase.Error.ALREADY_EXISTS


async def test_valid_user_exists_finish_tracker_creation(
    sample_tracker_create: TrackerCreate,
    sample_tracker_response: TrackerResponse,
    sample_user_response: UserResponse,
    tracker_service_mock,
    user_service_mock,
):
    user_id = "user_id"
    user_service_mock.get.return_value = sample_user_response
    tracker_service_mock.create.return_value = sample_tracker_response

    uc = FinishTrackerCreation(
        tracker_service=tracker_service_mock, user_service=user_service_mock
    )
    res, err = await uc.execute(tracker=sample_tracker_create, user_id=user_id)

    assert err is None
    assert res == sample_tracker_response
    user_service_mock.get.assert_awaited_once()
    tracker_service_mock.create.assert_awaited_once()


async def test_valid_user_not_exists_finish_tracker_creation(
    sample_tracker_create: TrackerCreate,
    sample_tracker_response: TrackerResponse,
    sample_user_response: UserResponse,
    tracker_service_mock,
    user_service_mock,
):
    user_id = "user_id"
    user_service_mock.get.return_value = None
    user_service_mock.create.return_value = sample_user_response
    tracker_service_mock.create.return_value = sample_tracker_response

    uc = FinishTrackerCreation(
        tracker_service=tracker_service_mock, user_service=user_service_mock
    )
    res, err = await uc.execute(tracker=sample_tracker_create, user_id=user_id)

    assert err is None
    assert res == sample_tracker_response
    user_service_mock.get.assert_awaited_once_with(user_id)
    user_service_mock.create.assert_awaited_once_with(user_id)
    tracker_service_mock.create.assert_awaited_once()


async def test_invalid_no_fields_finish_tracker_creation(
    sample_tracker_create: TrackerCreate,
    tracker_service_mock,
    user_service_mock,
):
    user_id = "user_id"
    tracker = sample_tracker_create.model_copy()
    tracker.structure.data = {}

    uc = FinishTrackerCreation(
        tracker_service=tracker_service_mock, user_service=user_service_mock
    )
    _, err = await uc.execute(tracker=sample_tracker_create, user_id=user_id)

    assert err is not None
    assert err == FinishTrackerCreation.Error.AT_LEAST_ONE_FIELD_REQUIRED
