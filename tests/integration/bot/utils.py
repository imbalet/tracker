import datetime
from unittest.mock import AsyncMock

from aiogram import types


def create_message(text: str | None):
    chat = types.Chat(id=0, type="private")

    message = AsyncMock(spec=types.Message)
    message.message_id = 0
    message.chat = chat
    message.text = text
    message.date = datetime.datetime.now(datetime.UTC)
    message.bot = AsyncMock()

    message.answer = AsyncMock()
    message.delete = AsyncMock()
    return message


def create_callback(message) -> AsyncMock:
    callback = AsyncMock(types.CallbackQuery)
    callback.message = message
    callback.answer = AsyncMock()
    return callback
