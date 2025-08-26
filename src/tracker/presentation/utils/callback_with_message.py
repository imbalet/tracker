from aiogram.types import CallbackQuery, Message


class CallbackQueryWithMessage(CallbackQuery):
    message: Message  # type: ignore
