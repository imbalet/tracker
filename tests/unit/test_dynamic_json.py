import pytest
from tracker.core.dynamic_json import DynamicJson
from tracker.core.dynamic_json.exceptions import ValidationException
from tracker.core.dynamic_json.types import FieldType


@pytest.fixture
def sample_data_string(sample_tracker_data):
    return {k: str(v) for k, v in sample_tracker_data.items()}


def test_valid_create(sample_tracker_structure: FieldType, sample_tracker_data):
    dj = DynamicJson.from_fields(sample_tracker_structure)
    dj.fill_one(sample_tracker_data)
    assert sample_tracker_data == dj.dump_data()


def test_valid_create_from_str(sample_tracker_structure: FieldType, sample_data_string):
    dj = DynamicJson.from_fields(sample_tracker_structure)
    dj.fill_one(sample_data_string)


@pytest.mark.parametrize(
    "field, value",
    [
        ("int_data", "10"),
        ("int_data", "-10"),
        ("int_data", "0"),
        ("string_data", ""),
        ("string_data", " "),
        ("string_data", "str"),
        ("string_data", "10"),
    ],
)
def test_valid_validate_one_field(field: str, value: str):
    dj = DynamicJson.from_fields(
        {"int_data": {"type": "int"}, "string_data": {"type": "string"}}
    )
    dj.validate_one_field(field, value)


@pytest.mark.parametrize(
    "field, value",
    [
        ("int_data", "0.1"),
        ("int_data", "-0.2"),
        ("int_data", ""),
        ("int_data", "str"),
        ("float_data", ""),
        ("float_data", "1a"),
    ],
)
def test_validation_exception_validate_one_field(field: str, value: str):
    dj = DynamicJson.from_fields(
        {"int_data": {"type": "int"}, "float_data": {"type": "float"}}
    )
    with pytest.raises(ValidationException):
        dj.validate_one_field(field, value)
