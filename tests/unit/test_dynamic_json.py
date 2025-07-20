import pytest

from src.core.dynamic_json import DynamicJson
from src.core.dynamic_json.types import FieldType


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
