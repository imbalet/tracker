from tracker.schemas import UserCreate, UserResponse
from tracker.services.database import UserService


async def test_valid_add(sample_user_create: UserCreate, user_service: UserService):
    res = await user_service.create(sample_user_create.id)
    assert res.id == sample_user_create.id


async def test_valid_get(sample_user_created: UserResponse, user_service: UserService):
    res = await user_service.get(sample_user_created.id)
    assert res is not None
    assert res.id == sample_user_created.id
