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
from src.schemas import TrackerCreate, TrackerStructureCreate
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
    await state.update_data(name=message.text)
    await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)
    data = await state.get_data()

    res = await message.answer(
        text=get_tracker_description(data, "Создание трекера"),
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
    data = await state.get_data()
    field_type = data["current_field_type"]
    if field_type == "enum":
        new_field = {
            "type": field_type,
            "values": data["current_enum_values"],
        }
    else:
        new_field = {"type": field_type}

    updated_fields = data.get("fields", {})
    if message.text in updated_fields:
        await answer_message(
            state=state,
            data=data,
            message=message,
            text=(
                f'Имя "{message.text}" уже существует,'
                f'выберете другое имя для поля enum со значениями {data["current_enum_values"]}'
            ),
        )

    updated_fields[message.text] = new_field
    await state.update_data(fields=updated_fields, current_field_type=None)

    main_data = await state.get_data()
    await state.set_state(TrackerCreation.AWAIT_NEXT_ACTION)

    text = get_tracker_description(main_data, "Создание трекера")
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

    if callback_data.action == "add_field":
        await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)
        data = await state.get_data()
        await callback.message.edit_text(  # type: ignore
            text=get_tracker_description(data, "Создание трекера"),
            reply_markup=build_field_type_keyboard(),
        )

    elif callback_data.action == "finish":
        data = await state.get_data()

        uc = CreateTrackerStructureUseCase(tracker_service)
        user = await user_service.get(str(callback.message.chat.id))  # type: ignore
        if user is None:
            user = await user_service.create(str(callback.message.chat.id))  # type: ignore

        res = await uc.execute(
            tracker=TrackerCreate(name=data["name"], user_id=user.id),
            structure=TrackerStructureCreate(data=data.get("fields", {})),
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
