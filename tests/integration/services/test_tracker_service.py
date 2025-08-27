from tracker.schemas import (
    TrackerCreate,
    TrackerDataCreate,
    TrackerResponse,
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


async def test_vald_get_by_name(
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
):
    res = await tracker_service.get_by_name(sample_tracker_created.name)
    assert res == sample_tracker_created


async def test_vald_get_by_id(
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
):
    res = await tracker_service.get_by_id(sample_tracker_created.id)
    assert res == sample_tracker_created


async def test_vald_get_by_user_id(
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
    sample_user_created: UserResponse,
):
    res = await tracker_service.get_by_user_id(sample_user_created.id)
    assert len(res) == 1
    assert res[0] == sample_tracker_created


async def test_valid_add_data(
    sample_tracker_data_create: TrackerDataCreate,
    sample_tracker_created: TrackerResponse,
    tracker_service: TrackerService,
):
    sample_tracker_data_create.tracker_id = sample_tracker_created.id
    res = await tracker_service.add_data(sample_tracker_data_create)
    assert res.data == sample_tracker_data_create.data
