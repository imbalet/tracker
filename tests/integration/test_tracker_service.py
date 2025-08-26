from tracker.schemas import (
    TrackerCreate,
    TrackerCreateBase,
    TrackerDataCreate,
    TrackerResponse,
    TrackerStructureCreate,
    UserResponse,
)
from tracker.services.database import TrackerService


async def test_valid_create(
    sample_tracker_create: TrackerCreate,
    tracker_service: TrackerService,
    sample_user_created: UserResponse,
):
    res = await tracker_service.create(tracker=sample_tracker_create)
    assert res.user == sample_user_created
    assert len(res.data) == 0


async def test_valid_add_data(
    sample_tracker_data_create: TrackerDataCreate,
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
):
    sample_tracker_data_create.tracker_id = sample_tracker_created.id
    res = await tracker_service.add_data(sample_tracker_data_create)
    assert res.data == sample_tracker_data_create.data
