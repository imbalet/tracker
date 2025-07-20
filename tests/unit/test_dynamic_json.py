import pytest

from src.core.dynamic_json import DynamicJson
from src.core.dynamic_json.types import FieldType, field_types_list


@pytest.fixture
def sample_structure() -> FieldType:
    structure: FieldType = {}
    for i in field_types_list:
        structure[f"{i}_name"] = {"type": i}
        if i == "enum":
            structure[f"{i}_name"]["values"] = "val1/val2/val3"

    return structure


@pytest.fixture
def sample_data(sample_structure: FieldType):
    import random
    import string

    data = {}
    for name, props in sample_structure.items():
        match props["type"]:
            case "int":
                value = random.randint(-10, 10)
            case "float":
                value = random.uniform(-10, 10)
            case "string":
                value = "".join(
                    random.choices(string.ascii_letters + string.digits, k=5)
                )
            case "enum":
                value = random.choice(props["values"].split("/"))  # type: ignore
            case _:
                raise ValueError()

        data[name] = value
    return data


@pytest.fixture
def sample_data_string(sample_data):
    return {k: str(v) for k, v in sample_data.items()}


def test_valid_create(sample_structure: FieldType, sample_data):
    dj = DynamicJson.from_fields(sample_structure)
    dj.fill_one(sample_data)
    assert sample_data == dj.dump_data()


def test_valid_create_from_str(sample_structure: FieldType, sample_data_string):
    dj = DynamicJson.from_fields(sample_structure)
    dj.fill_one(sample_data_string)
