from src.services.database import UserService
from src.schemas import UserCreate, UserResponse


async def test_valid_add(sample_user_data: UserCreate, user_service: UserService):
    res = await user_service.create(sample_user_data.chat_id)
    assert res.chat_id == sample_user_data.chat_id


async def test_valid_get(sample_user: UserResponse, user_service: UserService):
    res = await user_service.get(sample_user.id)
    assert res is not None
    assert res.id == sample_user.id
