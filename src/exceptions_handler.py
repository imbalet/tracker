from aiogram.types import ErrorEvent, Update

from src.core.dynamic_json.exceptions import (
    AttributeException,
    TypeException,
    ValidationException,
)
from src.exceptions import NotFoundException


def get_chat_info(update: Update):
    chat_id = None
    bot = None
    if update.message:
        chat_id = update.message.chat.id
        bot = update.message.bot
    elif update.callback_query and update.callback_query.message:
        chat_id = update.callback_query.message.chat.id
        bot = update.callback_query.message.bot
    return chat_id, bot


async def dynamic_json_exceptions_handler(event: ErrorEvent):
    chat_id, bot = get_chat_info(event.update)
    exception = event.exception
    if chat_id and bot:
        match exception:
            case TypeException() | ValidationException():
                await bot.send_message(chat_id, str(exception))
            case AttributeException() | _:
                await bot.send_message(
                    chat_id, "Произошла непредвиденная ошибка ошибка"
                )
    # logging here
    return True


async def service_exceptions_handler(event: ErrorEvent):
    chat_id, bot = get_chat_info(event.update)
    exception = event.exception
    if chat_id and bot:
        match exception:
            case NotFoundException():
                await bot.send_message(chat_id, str(exception))
            case _:
                await bot.send_message(
                    chat_id, "Произошла непредвиденная ошибка ошибка"
                )
    # logging here
    return True
