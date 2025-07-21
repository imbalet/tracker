from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.presentation.callbacks import CancelCallback, FieldCallback, TrackerCallback
from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.states import AddingData
from src.presentation.utils import (
    build_tracker_fields_keyboard,
    build_trackers_keyboard,
    get_tracker_data_description_from_dto,
    get_tracker_description_from_dto,
)
from src.schemas import TrackerDataCreate, TrackerResponse
from src.services.database import TrackerService

router = Router(name=__name__)
router.callback_query.middleware(CallbackMessageMiddleware())


async def answer_message(
    state: FSMContext, message: Message, text: str, reply_markup=None
):
    data = await state.get_data()
    if "main_message_id" in data:
        if not message.bot:
            raise ValueError()
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data["main_message_id"],
            text=text,
            reply_markup=reply_markup,
        )
        if data["main_message_id"] != message.message_id:
            await message.delete()
    else:
        msg = await message.answer(text=text, reply_markup=reply_markup)
        await state.update_data(main_message_id=msg.message_id)
        await message.delete()


@router.message(Command("my_trackers"))
async def start_tracker_creation(
    message: Message, tracker_service: TrackerService
) -> None:
    res = await tracker_service.get_by_user_id(str(message.chat.id))
    keyboard = build_trackers_keyboard(res)
    await message.answer("Трекеры:", reply_markup=keyboard)


@router.callback_query(TrackerCallback.filter())
async def discribe_tracker(
    callback: CallbackQuery,
    callback_data: TrackerCallback,
    tracker_service: TrackerService,
):
    res = await tracker_service.get_by_id(callback_data.id)
    await callback.message.edit_text(text=get_tracker_description_from_dto(res))  # type: ignore
    await callback.answer()


@router.message(Command("track"))
async def add_tracker_data(
    message: Message, state: FSMContext, tracker_service: TrackerService
) -> None:
    await state.clear()

    parts = message.text.split(maxsplit=1)  # type: ignore
    if len(parts) < 2:
        await message.answer("Ошибка: Не указан трекер!")
        return
    tracker_name = parts[1].strip()

    res = await tracker_service.get_by_name(tracker_name)
    await state.update_data(
        current_tracker=res.model_dump_json(),
        filled_fields=set(),
        current_tracker_id=res.id,
    )
    await state.set_state(AddingData.AWAIT_NEXT_ACTION)

    new_message = await message.answer(
        text=get_tracker_data_description_from_dto(res, data={}),
        reply_markup=build_tracker_fields_keyboard(res),
    )
    await state.update_data(main_message_id=new_message.message_id)


@router.callback_query(AddingData.AWAIT_NEXT_ACTION, FieldCallback.filter())
async def handle_field(
    callback: CallbackQuery, callback_data: FieldCallback, state: FSMContext
):
    await state.update_data(current_field=callback_data.name)
    await state.set_state(AddingData.AWAIT_FIELD_VALUE)

    await answer_message(
        state=state,
        text=f"Введите значение поля {callback_data.name}",
        message=callback.message,  # type: ignore
    )
    await callback.answer()


@router.message(AddingData.AWAIT_FIELD_VALUE)
async def handle_field_value(
    message: Message, state: FSMContext, tracker_service: TrackerService
):
    data = await state.get_data()
    filled_fields = set(data["filled_fields"])

    filled_fields.add(data["current_field"])

    field_values: dict = data.get("field_values", {})
    field_values[data["current_field"]] = message.text  # type: ignore

    await state.update_data(field_values=field_values, filled_fields=filled_fields)
    await state.set_state(AddingData.AWAIT_NEXT_ACTION)

    tracker = TrackerResponse.model_validate_json(data["current_tracker"])
    if len(filled_fields) == len(tracker.structure.data):
        await tracker_service.add_data(
            TrackerDataCreate(tracker_id=data["current_tracker_id"], data=field_values)
        )
        await answer_message(
            state=state,
            text="Все данные сохранены!",
            message=message,
        )
        await state.clear()
    else:
        await state.set_state(AddingData.AWAIT_NEXT_ACTION)
        await answer_message(
            state=state,
            text=get_tracker_data_description_from_dto(tracker, field_values),
            message=message,  # type: ignore
            reply_markup=build_tracker_fields_keyboard(tracker, filled_fields),
        )


@router.callback_query(AddingData.AWAIT_NEXT_ACTION, CancelCallback.filter())
async def handle_cancel(
    callback: CallbackQuery, callback_data: CancelCallback, state: FSMContext
):
    await state.clear()

    await callback.message.edit_text(  # type: ignore
        text="Добавление данных отменено",
        reply_markup=None,
    )
    await callback.answer()
