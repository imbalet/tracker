from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.core.dynamic_json.dynamic_json import DynamicJson
from src.presentation.callbacks import (
    CancelCallback,
    FieldCallback,
    TrackerActionsCallback,
    TrackerCallback,
    TrackerDataActionsCallback,
)
from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.states import AddingData
from src.presentation.utils import (
    build_tracker_action_keyboard,
    build_tracker_fields_keyboard,
    build_trackers_keyboard,
    get_tracker_data_description_from_dto,
    get_tracker_description_from_dto,
    update_main_message,
)
from src.schemas import TrackerDataCreate, TrackerResponse
from src.services.database import TrackerService

router = Router(name=__name__)
router.callback_query.middleware(CallbackMessageMiddleware())


@router.callback_query(TrackerActionsCallback.filter(F.action == "back"))
@router.callback_query(TrackerDataActionsCallback.filter(F.action == "back"))
async def show_trackers_button(
    callback: CallbackQuery,
    callback_data: TrackerDataActionsCallback,
    state: FSMContext,
    tracker_service: TrackerService,
):
    if not callback.message:
        callback.answer("Сообщение не найдено", show_alert=True)
        return

    res = await tracker_service.get_by_user_id(str(callback.message.chat.id))
    if not res:
        await callback.message.answer(text="У вас пока нет трекеров")
        return

    await update_main_message(
        state=state,
        message=callback.message,
        text="Трекеры:",
        reply_markup=build_trackers_keyboard(res),
    )
    callback.answer()


@router.message(Command("my_trackers"))
async def show_trackers(
    message: Message, state: FSMContext, tracker_service: TrackerService
) -> None:
    res = await tracker_service.get_by_user_id(str(message.chat.id))
    if not res:
        await message.answer(text="У вас пока нет трекеров")
        return

    await update_main_message(
        state=state,
        message=message,
        text="Трекеры:",
        reply_markup=build_trackers_keyboard(res),
        create_new=True,
    )


@router.callback_query(TrackerCallback.filter())
async def describe_tracker(
    callback: CallbackQuery,
    callback_data: TrackerCallback,
    state: FSMContext,
    tracker_service: TrackerService,
):
    res = await tracker_service.get_by_id(callback_data.id)
    if not res:
        await update_main_message(
            state=state,
            message=callback.message,  # type: ignore
            text="Трекер не найден",
            create_new=True,
        )
        return

    await state.update_data(tracker_id=res.id)

    await update_main_message(
        state=state,
        message=callback.message,  # type: ignore
        text=get_tracker_description_from_dto(res),
        reply_markup=build_tracker_action_keyboard(),
    )
    await callback.answer()


@router.message(Command("track"))
async def start_tracking(
    message: Message, state: FSMContext, tracker_service: TrackerService
) -> None:
    await state.clear()

    parts = message.text.split(maxsplit=1)  # type: ignore
    if len(parts) < 2:
        await message.answer(text="Ошибка: Не указан трекер!")
        return
    tracker_name = parts[1].strip()

    res = await tracker_service.get_by_name(tracker_name)
    if not res:
        await message.answer(text=f"Трекер '{tracker_name}' не найден")
        return

    await state.update_data(current_tracker=res.model_dump_json())
    await state.set_state(AddingData.AWAIT_NEXT_ACTION)
    await update_main_message(
        state=state,
        message=message,
        text=get_tracker_data_description_from_dto(res, data={}),
        reply_markup=build_tracker_fields_keyboard(res),
        create_new=True,
    )


@router.callback_query(AddingData.AWAIT_NEXT_ACTION, FieldCallback.filter())
async def handle_field(
    callback: CallbackQuery, callback_data: FieldCallback, state: FSMContext
):
    await state.update_data(current_field=callback_data.name)
    await state.set_state(AddingData.AWAIT_FIELD_VALUE)

    await update_main_message(
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
    current_field = data["current_field"]
    field_values: dict = data.get("field_values", {})
    current_field_value = message.text
    field_values[current_field] = current_field_value  # type: ignore

    tracker = TrackerResponse.model_validate_json(data["current_tracker"])
    dj = DynamicJson.from_fields(fields=tracker.structure.data)
    dj.validate_one_field(current_field, str(current_field_value))
    await state.update_data(field_values=field_values)

    if len(field_values) == len(tracker.structure.data):
        dj.validate(field_values)
        await tracker_service.add_data(
            TrackerDataCreate(tracker_id=tracker.id, data=field_values)
        )
        await update_main_message(
            state=state,
            text="Все данные сохранены!",
            message=message,
            create_new=True,
        )
        await state.clear()
    else:
        await state.set_state(AddingData.AWAIT_NEXT_ACTION)
        await update_main_message(
            state=state,
            text=get_tracker_data_description_from_dto(tracker, field_values),
            message=message,  # type: ignore
            reply_markup=build_tracker_fields_keyboard(
                tracker, set(field_values.keys())
            ),
            create_new=True,
        )


@router.callback_query(AddingData.AWAIT_NEXT_ACTION, CancelCallback.filter())
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(  # type: ignore
        text="Добавление данных отменено",
        reply_markup=None,
    )
    await callback.answer()
