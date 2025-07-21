from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    TelegramObject,
)

from src.services.database import DataService, TrackerService, UserService


class DBMiddleware(BaseMiddleware):
    def __init__(self, sessionmaker):
        super().__init__()
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["sessionmaker"] = self.sessionmaker
        data["data_service"] = DataService(session_factory=self.sessionmaker)
        data["tracker_service"] = TrackerService(session_factory=self.sessionmaker)
        data["user_service"] = UserService(session_factory=self.sessionmaker)
        return await handler(event, data)


class CallbackMessageMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        if event.message is None:
            await event.answer("Сообщение не найдено", show_alert=True)
            return

        if isinstance(event.message, InaccessibleMessage):
            bot: Bot = data.get("bot")  # type: ignore
            if bot:
                await bot.send_message(
                    chat_id=event.message.chat.id,
                    text="Сообщение недоступно",
                )
            await event.answer()
            return

        return await handler(event, data)
