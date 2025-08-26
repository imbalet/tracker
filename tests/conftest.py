import datetime
import random
from typing import Any
from uuid import UUID

import pytest

from src.core.dynamic_json.types import FieldType, field_types_list
from src.schemas import (
    TrackerCreate,
    TrackerDataCreate,
    TrackerDataResponse,
    TrackerResponse,
    TrackerStructureCreate,
    TrackerStructureResponse,
    UserCreate,
    UserResponse,
)

random.seed(42)


@pytest.fixture
def fixed_now():
    return datetime.datetime(2025, 8, 26, 12, 0, 0, tzinfo=datetime.UTC)


@pytest.fixture
def fixed_uuid():
    return UUID("12345678-1234-5678-1234-567812345678")


# DATA


@pytest.fixture
def sample_user_create():
    return UserCreate(id="123")


@pytest.fixture
def sample_user_response(sample_user_create: UserCreate):
    return UserResponse(id=sample_user_create.id)


@pytest.fixture
def sample_tracker_create(
    sample_user_response: UserResponse,
    sample_tracker_structure_create: TrackerStructureCreate,
) -> TrackerCreate:
    return TrackerCreate(
        name="name",
        user_id=sample_user_response.id,
        structure=sample_tracker_structure_create,
    )


@pytest.fixture
def sample_tracker_response(
    sample_tracker_create: TrackerCreate,
    sample_user_response: UserResponse,
    sample_tracker_structure_response: TrackerStructureResponse,
    fixed_uuid: UUID,
    fixed_now: datetime.datetime,
) -> TrackerResponse:
    return TrackerResponse(
        name=sample_tracker_create.name,
        user_id=sample_user_response.id,
        user=sample_user_response,
        created_at=fixed_now,
        structure_id=sample_tracker_structure_response.id,
        data=[],
        id=fixed_uuid,
        structure=sample_tracker_structure_response,
    )


@pytest.fixture
def sample_tracker_structure() -> FieldType:
    structure: FieldType = {}
    for i in field_types_list:
        structure[f"{i}_name"] = {"type": i}
        if i == "enum":
            structure[f"{i}_name"]["values"] = ["val1", "val2", "val3"]
    return structure


@pytest.fixture
def sample_tracker_structure_create() -> TrackerStructureCreate:
    structure: FieldType = {}
    for i in field_types_list:
        structure[f"{i}_name"] = {"type": i}
        if i == "enum":
            structure[f"{i}_name"]["values"] = ["val1", "val2", "val3"]
    return TrackerStructureCreate(data=structure)


@pytest.fixture
def sample_tracker_data(
    sample_tracker_structure_create: TrackerStructureCreate,
) -> dict[str, Any]:
    data = {}
    for name, props in sample_tracker_structure_create.data.items():
        match props["type"]:
            case "int":
                value = 42
            case "float":
                value = 14.5
            case "string":
                value = "string"
            case "enum":
                value = random.choice(props["values"])  # type: ignore
            case _:
                raise ValueError()

        data[name] = value
    return data


@pytest.fixture
def sample_tracker_structure_response(
    sample_tracker_structure_create: TrackerStructureCreate, fixed_uuid: UUID
):
    return TrackerStructureResponse(
        data=sample_tracker_structure_create.data,
        id=fixed_uuid,
    )


@pytest.fixture
def sample_tracker_data_create(
    sample_tracker_response: TrackerResponse, sample_tracker_data: dict[str, Any]
) -> TrackerDataCreate:
    return TrackerDataCreate(
        tracker_id=sample_tracker_response.id, data=sample_tracker_data
    )


@pytest.fixture
def sample_tracker_data_response(
    sample_tracker_data_create: TrackerDataCreate,
    fixed_uuid: UUID,
    fixed_now: datetime.datetime,
) -> TrackerDataResponse:
    return TrackerDataResponse(
        tracker_id=sample_tracker_data_create.tracker_id,
        data=sample_tracker_data_create.data,
        id=fixed_uuid,
        created_at=fixed_now,
    )
