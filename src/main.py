import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters.exception import ExceptionTypeFilter
from aiogram.methods.delete_webhook import DeleteWebhook
from aiogram.types import BotCommand

from src.config import config
from src.core.dynamic_json.exceptions import DynamicJsonException
from src.database import get_sessionmaker
from src.exceptions import ServiceExceptions
from src.exceptions_handler import (
    dynamic_json_exceptions_handler,
    service_exceptions_handler,
)
from src.presentation.middleware import DBMiddleware, LanguageMiddleware
from src.presentation.routers import (
    create_tracker_router,
    data_router,
    general_router,
    tracker_control_router,
)


async def main() -> None:
    dp = Dispatcher()

    dp.errors.register(
        dynamic_json_exceptions_handler, ExceptionTypeFilter(DynamicJsonException)
    )
    dp.errors.register(
        service_exceptions_handler, ExceptionTypeFilter(ServiceExceptions)
    )
    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/help", description="Помощь"),
        BotCommand(command="/add_tracker", description="Добавить трекер"),
        BotCommand(command="/my_trackers", description="Просмотр списка трекеров"),
        BotCommand(command="/track", description="Добавить данные в трекер"),
    ]  # TODO: move it
    await bot.set_my_commands(commands)

    await bot(DeleteWebhook(drop_pending_updates=True))
    dp.include_router(create_tracker_router)
    dp.include_router(tracker_control_router)
    dp.include_router(general_router)
    dp.include_router(data_router)

    dp.update.middleware(DBMiddleware(await get_sessionmaker()))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
