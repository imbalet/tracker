from uuid import UUID

from aiogram import Router, html
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.utils import (
    get_tracker_description_from_dto,
)
from src.schemas import TrackerDataCreate, TrackerResponse
from src.services.database import TrackerService


class AddingData(StatesGroup):
    AWAIT_FIELD_VALUE = State()
    AWAIT_NEXT_ACTION = State()


class TrackerCallback(CallbackData, prefix="tracker_"):
    id: UUID


class CancelCallback(CallbackData, prefix="cancel"):
    tracker_id: UUID


class FieldCallback(CallbackData, prefix="field"):
    name: str
    tracker_id: UUID


router = Router(name=__name__)
router.callback_query.middleware(CallbackMessageMiddleware())


def get_tracker_data_description(
    tracker: dict, data: dict, add_string: str = ""
) -> str:
    name = tracker.get("name", "Без названия")
    fields = tracker.get("fields", {})

    text = (f"{add_string}\n" if add_string else "") + f"{html.bold(name)}\n\n"
    text += "Поля:\n"

    if not fields:
        text += "  -> Пока нет полей\n"
    else:
        for i, (field_name, field) in enumerate(fields.items(), 1):
            text += (
                f"  {i}. {field['type']}"
                f" {field['values'] if field["type"] == "enum" else ""}"
                f": {html.italic(field_name)}"
                f" -> {data.get(field_name, "Не заполнено")}\n"
            )

    return text


def get_tracker_data_description_from_dto(
    dto: TrackerResponse, data: dict, add_string: str = ""
) -> str:
    return get_tracker_data_description(
        {"name": dto.name, "fields": dto.structure.data},
        add_string=add_string,
        data=data,
    )


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


def build_trackers_keyboard(data: list[TrackerResponse]):
    builder = InlineKeyboardBuilder()
    for i in data:
        builder.button(text=i.name, callback_data=TrackerCallback(id=i.id))
    builder.adjust(3)
    return builder.as_markup()


def build_tracker_fields_keyboard(
    tracker: TrackerResponse, exclude_fields: set | None = None
):
    builder = InlineKeyboardBuilder()
    for name, props in tracker.structure.data.items():
        if exclude_fields and name in exclude_fields:
            continue
        builder.button(
            text=f"{name}: {props["type"] if props["type"] != "enum" else props['values']}",  # type: ignore
            callback_data=FieldCallback(name=name, tracker_id=tracker.id),
        )
    builder.button(text="Отмена", callback_data=CancelCallback(tracker_id=tracker.id))
    builder.adjust(3, 1)
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
    sessionmaker,
):
    service = TrackerService(sessionmaker)
    res = await service.get_by_id(callback_data.id)
    await callback.message.edit_text(text=get_tracker_description_from_dto(res))  # type: ignore
    await callback.answer()


@router.message(Command("track"))
async def add_tracker_data(message: Message, state: FSMContext, sessionmaker) -> None:
    parts = message.text.split(maxsplit=1)  # type: ignore

    if len(parts) < 2:
        await message.answer("Ошибка: Не указан трекер!")
        return

    tracker_name = parts[1].strip()
    service = TrackerService(sessionmaker)
    res = await service.get_by_name(tracker_name)
    await state.clear()
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
async def handle_field_value(message: Message, state: FSMContext, sessionmaker):
    data = await state.get_data()

    filled_fields = set(data["filled_fields"])
    filled_fields.add(data["current_field"])

    fields: dict = data.get("field_values", {})
    fields[data["current_field"]] = message.text  # type: ignore

    await state.update_data(field_values=fields, filled_fields=filled_fields)
    await state.set_state(AddingData.AWAIT_NEXT_ACTION)

    tracker = TrackerResponse.model_validate_json(data["current_tracker"])
    if len(filled_fields) == len(tracker.structure.data):
        service = TrackerService(sessionmaker)
        await service.add_data(
            TrackerDataCreate(tracker_id=data["current_tracker_id"], data=fields)
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
            text=get_tracker_data_description_from_dto(tracker, fields),
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
