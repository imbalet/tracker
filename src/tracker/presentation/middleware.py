from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    Message,
    TelegramObject,
)
from tracker.presentation.utils import KeyboardBuilder, _t
from tracker.services.database import DataService, TrackerService, UserService


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
        t = data.get("t")
        if not t:
            raise RuntimeError("Error getting 't' func from middleware data")
        data["kbr_builder"] = KeyboardBuilder(t=t)
        return await handler(event, data)


class LanguageMiddleware(BaseMiddleware):
    def __init__(self, default_lang: str = "ru"):
        self.default_lang = default_lang

    async def __call__(  # type: ignore
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_obj = None
        if isinstance(event, Message):
            user_obj = event.from_user
        elif isinstance(event, CallbackQuery):
            user_obj = event.from_user
        elif hasattr(event, "message") and isinstance(event.message, Message):
            user_obj = event.message.from_user

        lang = getattr(user_obj, "language_code", None) or self.default_lang
        lang = "ru" if lang.startswith("ru") else "en"
        data["lang"] = lang
        data["t"] = lambda text, **kwargs: _t(lang=lang, key=text, **kwargs)
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
