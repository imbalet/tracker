from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.presentation.callbacks import ActionCallback, FieldTypeCallback
from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.states import TrackerCreation
from src.presentation.utils import (
    build_action_keyboard,
    build_field_type_keyboard,
    get_tracker_description,
    get_tracker_description_from_dto,
)
from src.schemas import TrackerStructureCreate
from src.services.database import TrackerService, UserService
from src.use_cases import CreateTrackerStructureUseCase

router = Router(name=__name__)
router.callback_query.middleware(CallbackMessageMiddleware())


async def answer_message(
    state: FSMContext, data: dict, message: Message, text: str, reply_markup=None
):
    if "main_message_id" in data:
        if not message.bot:
            raise ValueError()
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data["main_message_id"],
            text=text,
            reply_markup=reply_markup,
        )
        await message.delete()
    else:
        msg = await message.answer(text=text, reply_markup=reply_markup)
        await state.update_data(main_message_id=msg.message_id)
        await message.delete()


@router.message(Command("add_tracker"))
async def start_tracker_creation(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TrackerCreation.AWAIT_TRACKER_NAME)

    res = await message.answer("Введите название трекера:")
    await state.update_data(main_message_id=res.message_id)


@router.message(TrackerCreation.AWAIT_TRACKER_NAME)
async def process_tracker_name(message: Message, state: FSMContext):
    tracker = {"name": message.text, "fields": {}}
    await state.update_data(tracker=tracker)

    await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)
    data = await state.get_data()

    res = await message.answer(
        text=get_tracker_description(data["tracker"], "Создание трекера"),
        reply_markup=build_field_type_keyboard(),
    )
    await state.update_data(main_message_id=res.message_id)


@router.callback_query(TrackerCreation.AWAIT_FIELD_TYPE, FieldTypeCallback.filter())
async def process_field_type(
    callback: CallbackQuery, callback_data: FieldTypeCallback, state: FSMContext
):

    await state.update_data(current_field_type=callback_data.type)

    if callback_data.type == "enum":
        next_state = TrackerCreation.AWAIT_ENUM_VALUES
        message_text = (
            f"Выбран тип: {callback_data.type.upper()}\nВведите значения поля:"
        )
    else:
        next_state = TrackerCreation.AWAIT_FIELD_NAME
        message_text = (
            f"Выбран тип: {callback_data.type.upper()}\nВведите название поля:"
        )

    await callback.message.edit_text(text=message_text)  # type: ignore
    await state.set_state(next_state)
    await callback.answer()


@router.message(TrackerCreation.AWAIT_ENUM_VALUES)
async def process_enum_values(message: Message, state: FSMContext):

    await state.update_data(current_enum_values=message.text)
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    data = await state.get_data()

    text = f"Выбраны следующие значения enum: {message.text}\nВведите название поля:"

    await answer_message(state=state, data=data, message=message, text=text)


@router.message(TrackerCreation.AWAIT_FIELD_NAME)
async def process_field_name(message: Message, state: FSMContext):
    await state.set_state(TrackerCreation.AWAIT_NEXT_ACTION)

    data = await state.get_data()
    field_type = data["current_field_type"]
    if field_type == "enum":
        new_field = {
            "type": field_type,
            "values": data["current_enum_values"],
        }
    else:
        new_field = {"type": field_type}

    tracker = data["tracker"]
    if message.text in tracker["fields"]:
        await answer_message(
            state=state,
            data=data,
            message=message,
            text=(
                f'Имя "{message.text}" уже существует,'
                f'выберете другое имя для поля enum со значениями {data["current_enum_values"]}'
            ),
        )

    tracker["fields"][message.text] = new_field
    await state.update_data(
        tracker=tracker, current_field_type=None, current_enum_values=None
    )

    text = get_tracker_description(tracker, "Создание трекера")
    keyboard = build_action_keyboard()

    await answer_message(
        state=state, data=data, message=message, text=text, reply_markup=keyboard
    )


@router.callback_query(TrackerCreation.AWAIT_NEXT_ACTION, ActionCallback.filter())
async def process_next_action(
    callback: CallbackQuery,
    callback_data: ActionCallback,
    state: FSMContext,
    tracker_service: TrackerService,
    user_service: UserService,
):
    data = await state.get_data()
    tracker = data["tracker"]

    if callback_data.action == "add_field":
        await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)
        await callback.message.edit_text(  # type: ignore
            text=get_tracker_description(tracker, "Создание трекера"),
            reply_markup=build_field_type_keyboard(),
        )

    elif callback_data.action == "finish":
        uc = CreateTrackerStructureUseCase(tracker_service, user_service)

        res = await uc.execute(
            user_id=str(callback.message.chat.id),  # type: ignore
            tracker_name=tracker["name"],
            structure=TrackerStructureCreate(data=data["tracker"]["fields"]),
        )

        await callback.message.edit_text(  # type: ignore
            text=f"Трекер создан!\n\n{get_tracker_description_from_dto(res, "Создание трекера")}"
        )
        await state.clear()

    elif callback_data.action == "cancel":
        await callback.message.edit_text("Создание трекера отменено")  # type: ignore
        await state.clear()

    await callback.answer()


@router.callback_query(ActionCallback.filter(F.action == "cancel"))
async def cancel_creation(callback: CallbackQuery, state: FSMContext):

    await callback.message.edit_text("Создание трекера отменено")  # type: ignore
    await state.clear()
    await callback.answer()
