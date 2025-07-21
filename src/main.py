import asyncio
import logging
import sys
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.methods.delete_webhook import DeleteWebhook
from aiogram.types import BotCommand, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from presentation.routers import create_tracker_router, tracker_control_router
from src.config import config
from src.database import create_tables


async def get_sessionmaker():
    engine = create_async_engine(
        config.DB_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        future=True,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    await create_tables(engine)
    return AsyncSessionLocal


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
        return await handler(event, data)


dp = Dispatcher()


async def main() -> None:
    global dp
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
    dp.update.middleware(DBMiddleware(await get_sessionmaker()))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
