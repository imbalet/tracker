from aiogram import Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.core.dynamic_json.dynamic_json import DynamicJson
from src.presentation.callbacks import (
    BackCallback,
    CancelCallback,
    FieldCallback,
    TrackerCallback,
)
from src.presentation.constants import (
    ST_TR_CURRENT_FIELD,
    ST_TR_CURRENT_TRACKER,
    ST_TR_FIELD_VALUES,
    ST_TRACKER_ID,
)
from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.states import AddingData, DataState, TrackerControlState
from src.presentation.utils import (
    CallbackQueryWithMessage,
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


@router.callback_query(
    or_f(
        DataState.AWAIT_FIELDS_SELECTION,
        TrackerControlState.AWAIT_TRACKER_ACTION,
        DataState.AWAIT_ACTION,
    ),
    BackCallback.filter(),
)
async def show_trackers_button(
    callback: CallbackQueryWithMessage,
    state: FSMContext,
    tracker_service: TrackerService,
):
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
    await callback.answer()


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
    callback: CallbackQueryWithMessage,
    callback_data: TrackerCallback,
    state: FSMContext,
    tracker_service: TrackerService,
):
    res = await tracker_service.get_by_id(callback_data.id)
    if not res:
        await update_main_message(
            state=state,
            message=callback.message,
            text="Трекер не найден",
            create_new=True,
        )
        return

    await state.update_data(data={ST_TRACKER_ID: res.id})
    await state.set_state(TrackerControlState.AWAIT_TRACKER_ACTION)

    await update_main_message(
        state=state,
        message=callback.message,
        text=get_tracker_description_from_dto(res),
        reply_markup=build_tracker_action_keyboard(
            extra_buttons=[("Назад", BackCallback())]
        ),
    )
    await callback.answer()


@router.message(Command("track"))
async def start_tracking(
    message: Message, state: FSMContext, tracker_service: TrackerService
) -> None:
    await state.clear()
    # text can't be empty
    parts = message.text.split(maxsplit=1)  # type: ignore
    if len(parts) < 2:
        # TODO: add menu with trackers
        await message.answer(text="Ошибка: Не указан трекер!")
        return
    tracker_name = parts[1].strip()

    tracker = await tracker_service.get_by_name(tracker_name)
    if not tracker:
        await message.answer(text=f"Трекер '{tracker_name}' не найден")
        return
    await state.update_data(data={ST_TR_CURRENT_TRACKER: tracker.model_dump_json()})
    await state.set_state(AddingData.AWAIT_NEXT_ACTION)

    await update_main_message(
        state=state,
        message=message,
        text=get_tracker_data_description_from_dto(tracker, data={}),
        reply_markup=build_tracker_fields_keyboard(
            tracker, extra_buttons=[("Отмена", CancelCallback())]
        ),
        create_new=True,
    )


@router.callback_query(AddingData.AWAIT_NEXT_ACTION, FieldCallback.filter())
async def handle_field(
    callback: CallbackQueryWithMessage, callback_data: FieldCallback, state: FSMContext
):
    await state.update_data(data={ST_TR_CURRENT_FIELD: callback_data.name})
    await state.set_state(AddingData.AWAIT_FIELD_VALUE)

    await update_main_message(
        state=state,
        text=f"Введите значение поля {callback_data.name}",
        message=callback.message,
    )
    await callback.answer()


@router.message(AddingData.AWAIT_FIELD_VALUE)
async def handle_field_value(
    message: Message, state: FSMContext, tracker_service: TrackerService
):
    data = await state.get_data()
    current_field = data[ST_TR_CURRENT_FIELD]
    field_values: dict = data.get(ST_TR_FIELD_VALUES, {})
    current_field_value = message.text
    field_values[current_field] = current_field_value

    tracker = TrackerResponse.model_validate_json(data[ST_TR_CURRENT_TRACKER])
    dj = DynamicJson.from_fields(fields=tracker.structure.data)
    dj.validate_one_field(current_field, str(current_field_value))
    await state.update_data(data={ST_TR_FIELD_VALUES: field_values})

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
            message=message,
            reply_markup=build_tracker_fields_keyboard(
                tracker,
                set(field_values.keys()),
                extra_buttons=[("Отмена", CancelCallback())],
            ),
            create_new=True,
        )


@router.callback_query(AddingData.AWAIT_NEXT_ACTION, CancelCallback.filter())
async def handle_cancel(callback: CallbackQueryWithMessage, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        text="Добавление данных отменено",
        reply_markup=None,
    )
    await callback.answer()
