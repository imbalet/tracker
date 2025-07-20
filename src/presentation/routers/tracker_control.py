from uuid import UUID

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.utils import (
    get_tracker_description_from_dto,
)
from src.schemas import TrackerResponse
from src.services.database import TrackerService


class TrackerCallback(CallbackData, prefix="tracker_"):
    id: UUID


router = Router(name=__name__)
router.callback_query.middleware(CallbackMessageMiddleware())


def build_trackers_keyboard(data: list[TrackerResponse]):
    builder = InlineKeyboardBuilder()
    for i in data:
        builder.button(text=i.name, callback_data=TrackerCallback(id=i.id))
    builder.adjust(3)
    return builder.as_markup()


@router.message(Command("my_trackers"))
async def start_tracker_creation(message: Message, sessionmaker) -> None:
    service = TrackerService(sessionmaker)
    res = await service.get_by_user_id(str(message.chat.id))
    keyboard = build_trackers_keyboard(res)
    await message.answer("Трекеры:", reply_markup=keyboard)


@router.callback_query(TrackerCallback.filter())
async def discribe_tracker(
    callback: CallbackQuery,
    callback_data: TrackerCallback,
    state: FSMContext,
    sessionmaker,
):
    await state.clear()
    service = TrackerService(sessionmaker)
    res = await service.get_by_id(callback_data.id)
    await callback.message.answer(get_tracker_description_from_dto(res))  # type: ignore
    await callback.answer()
