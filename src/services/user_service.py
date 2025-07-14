from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.schemas import UserResponse
from src.models import UserOrm


class UserService:

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def create(self, chat_id: str) -> UserResponse:
        async with self.session_factory() as session:
            new_user = UserOrm(chat_id=chat_id)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return UserResponse.model_validate(new_user, from_attributes=True)

    async def get(self, user_id: UUID) -> UserResponse | None:
        async with self.session_factory() as session:
            result = await session.get(UserOrm, user_id)
            if result is None:
                return None
            return UserResponse.model_validate(result, from_attributes=True)
