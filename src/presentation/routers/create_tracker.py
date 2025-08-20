from aiogram import F, Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.presentation.callbacks import ActionCallback, CancelCallback, FieldTypeCallback
from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.states import TrackerCreation
from src.presentation.utils import (
    build_action_keyboard,
    build_field_type_keyboard,
    get_tracker_description,
    get_tracker_description_from_dto,
    update_main_message,
)
from src.schemas import TrackerStructureCreate
from src.services.database import TrackerService, UserService
from src.use_cases import CreateTrackerStructureUseCase

router = Router(name=__name__)
router.callback_query.middleware(CallbackMessageMiddleware())


@router.message(Command("add_tracker"))
async def start_tracker_creation(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TrackerCreation.AWAIT_TRACKER_NAME)
    await message.answer("Введите название трекера:")


@router.message(TrackerCreation.AWAIT_TRACKER_NAME)
async def process_tracker_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Имя должно состоять хотя бы из одного символа")
        return

    await state.update_data(tracker={"name": message.text, "fields": {}})
    await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)

    await update_main_message(
        state=state,
        message=message,
        text=get_tracker_description(
            {"name": message.text, "fields": {}}, "Создание трекера"
        ),
        reply_markup=build_field_type_keyboard(
            extra_buttons=[("Отмена", CancelCallback())]
        ),
        create_new=True,
    )


@router.callback_query(TrackerCreation.AWAIT_FIELD_TYPE, FieldTypeCallback.filter())
async def process_field_type(
    callback: CallbackQuery, callback_data: FieldTypeCallback, state: FSMContext
):
    await state.update_data(current_field_type=callback_data.type)

    if callback_data.type == "enum":
        next_state = TrackerCreation.AWAIT_ENUM_VALUES
        message_text = f"Выбран тип: {callback_data.type.upper()}\nВведите значения поля через слеш `/`:"
    else:
        next_state = TrackerCreation.AWAIT_FIELD_NAME
        message_text = (
            f"Выбран тип: {callback_data.type.upper()}\nВведите название поля:"
        )
    await state.set_state(next_state)

    await update_main_message(
        state=state,
        message=callback.message,  # type: ignore
        text=message_text,
    )
    await callback.answer()


@router.message(TrackerCreation.AWAIT_ENUM_VALUES)
async def process_enum_values(message: Message, state: FSMContext):
    if not message.text:
        await update_main_message(
            state=state,
            message=message,
            text="Сообщение должно включать значения поля enum",
            create_new=True,
        )
        return

    options = str(message.text).split("/")
    if len(options) < 2:
        await update_main_message(
            state=state,
            message=message,
            text=f"Значений enum должно быть более 1, получено {len(options)}",
            create_new=True,
        )
        return

    await state.update_data(current_enum_values=message.text)
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)

    text = (
        f"Выбраны следующие значения enum: {", ".join(options)}\nВведите название поля:"
    )
    await update_main_message(
        state=state,
        message=message,
        text=text,
        create_new=True,
    )


@router.message(TrackerCreation.AWAIT_FIELD_NAME)
async def process_field_name(message: Message, state: FSMContext):
    if not message.text:
        await update_main_message(
            state=state,
            message=message,
            text="Сообщение должно включать название поля",
            create_new=True,
        )
        return

    data = await state.get_data()
    field_name = str(message.text).strip()
    field_type = data["current_field_type"]
    tracker = data["tracker"]

    if field_name in tracker["fields"]:
        await update_main_message(
            state=state,
            message=message,
            text=(
                f'Имя "{message.text}" уже существует, выберете другое имя для поля {data["current_field_type"]}'
                + (
                    f' со значениями {data["current_enum_values"]}'
                    if data["current_field_type"] == "enum"
                    else ""
                )
            ),
            create_new=True,
        )
        return

    field_data = {"type": field_type}
    if field_data["type"] == "enum":
        field_data["values"] = data.get("current_enum_values", "")
    tracker["fields"][field_name] = field_data

    await state.update_data(
        tracker=tracker, current_field_type=None, current_enum_values=None
    )
    await state.set_state(TrackerCreation.AWAIT_NEXT_ACTION)

    await update_main_message(
        state=state,
        message=message,
        text=get_tracker_description(tracker, "Создание трекера"),
        reply_markup=build_action_keyboard(),
        create_new=True,
    )


@router.callback_query(
    TrackerCreation.AWAIT_NEXT_ACTION, ActionCallback.filter(F.action == "add_field")
)
async def process_next_action_add_field(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tracker = data["tracker"]
    await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)
    await update_main_message(
        state=state,
        message=callback.message,  # type: ignore
        text=get_tracker_description(tracker, "Создание трекера"),
        reply_markup=build_field_type_keyboard(
            extra_buttons=[("Отмена", CancelCallback())]
        ),
    )


@router.callback_query(
    TrackerCreation.AWAIT_NEXT_ACTION, ActionCallback.filter(F.action == "finish")
)
async def process_next_action_finish(
    callback: CallbackQuery,
    state: FSMContext,
    tracker_service: TrackerService,
    user_service: UserService,
):
    data = await state.get_data()
    tracker = data["tracker"]
    if len(data["tracker"]["fields"]) == 0:
        await callback.message.answer(  # type: ignore
            "Для сохранения в трекере должно быть хотя бы одно поле"
        )
        return

    uc = CreateTrackerStructureUseCase(tracker_service, user_service)
    res = await uc.execute(
        user_id=str(callback.message.chat.id),  # type: ignore
        tracker_name=tracker["name"],
        structure=TrackerStructureCreate(data=data["tracker"]["fields"]),
    )

    await update_main_message(
        state=state,
        message=callback.message,  # type: ignore
        text=f"Трекер создан!\n\n{get_tracker_description_from_dto(res, "Создание трекера")}",
    )
    await state.clear()
    await callback.answer()


@router.callback_query(
    or_f(TrackerCreation.AWAIT_FIELD_TYPE, TrackerCreation.AWAIT_NEXT_ACTION),
    CancelCallback.filter(),
)
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    await update_main_message(
        state=state,
        message=callback.message,  # type: ignore
        text="Создание трекера отменено",
    )
    await state.clear()
    await callback.answer()
