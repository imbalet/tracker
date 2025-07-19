from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
)


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
