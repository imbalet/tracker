from src.schemas import (
    TrackerCreate,
    TrackerDataCreate,
    TrackerResponse,
    TrackerStructureCreate,
    UserResponse,
)
from src.services.database import TrackerService


async def test_valid_create(
    sample_tracker_data: TrackerCreate,
    sample_tracker_structure_data: TrackerStructureCreate,
    tracker_service: TrackerService,
    sample_user: UserResponse,
):
    res = await tracker_service.create(
        tracker=sample_tracker_data, structure=sample_tracker_structure_data
    )
    assert res.user == sample_user
    assert len(res.data) == 0


async def test_valid_add_data(
    sample_tracker_data_data: TrackerDataCreate,
    sample_tracker: TrackerResponse,
    tracker_service: TrackerService,
):
    res = await tracker_service.add_data(sample_tracker_data_data)
    assert res.data == sample_tracker_data_data.data
