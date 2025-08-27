from typing import cast

from aiogram import Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tracker.presentation.callbacks import (
    BackCallback,
    CancelCallback,
    EnumValuesCallback,
    FieldCallback,
    TrackerCallback,
)
from tracker.presentation.constants.text import MsgKey
from tracker.presentation.states import AddingData, DataState, TrackerControlState
from tracker.presentation.utils import (
    CallbackQueryWithMessage,
    KeyboardBuilder,
    TFunction,
    get_tracker_data_description_from_dto,
    get_tracker_description_from_dto,
    update_main_message,
)
from tracker.presentation.utils.state import StateModel
from tracker.schemas import TrackerResponse
from tracker.services.database import TrackerService
from tracker.use_cases import (
    GetUserTrackersUseCase,
    HandleFieldValueUseCase,
    ValidateTrackingMessageUseCase,
)

router = Router(name=__name__)


class DataModelStrictTracker(StateModel):
    tracker: TrackerResponse


class DataModelStrict(DataModelStrictTracker):
    cur_field: str
    field_values: dict[str, str]


class DataModelTR(DataModelStrictTracker):
    cur_field: str
    field_values: dict[str, str] | None = None


class DataModel(StateModel):
    tracker: TrackerResponse | None = None
    cur_field: str | None = None
    field_values: dict[str, str] | None = None


@router.message(Command("my_trackers"))
async def show_trackers(
    message: Message,
    state: FSMContext,
    tracker_service: TrackerService,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
) -> None:
    show_trackers_uc = GetUserTrackersUseCase(tracker_service=tracker_service)
    trackers, err = await show_trackers_uc.execute(user_id=str(message.chat.id))

    if err:
        match err:
            case GetUserTrackersUseCase.Error.NO_TRACKERS:
                await message.answer(text=t(MsgKey.TR_NO_TRACKERS))
        return

    await update_main_message(
        state=state,
        message=message,
        text=t(MsgKey.TR_TRACKERS),
        reply_markup=kbr_builder.build_trackers_keyboard(trackers),
    )


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
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    await show_trackers(
        message=callback.message,
        state=state,
        tracker_service=tracker_service,
        t=t,
        kbr_builder=kbr_builder,
    )
    await callback.answer()


@router.callback_query(TrackerCallback.filter())
async def describe_tracker(
    callback: CallbackQueryWithMessage,
    callback_data: TrackerCallback,
    state: FSMContext,
    tracker_service: TrackerService,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    tracker = await tracker_service.get_by_id(callback_data.id)

    if not tracker:
        await update_main_message(
            state=state,
            message=callback.message,
            text=t(MsgKey.TR_TRACKER_NOT_FOUND),
            create_new=True,
        )
        return

    tracker = cast(TrackerResponse, tracker)
    await DataModel(tracker=tracker).save(state)

    await state.set_state(TrackerControlState.AWAIT_TRACKER_ACTION)
    await update_main_message(
        state=state,
        message=callback.message,
        text=get_tracker_description_from_dto(tracker),
        reply_markup=kbr_builder.conf(
            add_back_button=True
        ).build_tracker_action_keyboard(),
    )
    await callback.answer()


@router.message(Command("track"))
async def start_tracking(
    message: Message,
    state: FSMContext,
    tracker_service: TrackerService,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
) -> None:
    await state.clear()

    validating_input_uc = ValidateTrackingMessageUseCase()
    tracker_name, err = validating_input_uc.execute(text=message.text)

    if err:
        await message.answer(
            text=t(MsgKey.TR_TRACKER_NAME_NOT_FOUND, tracker_name=tracker_name)
        )
        return

    tracker = await tracker_service.get_by_name(tracker_name)
    if not tracker:
        await message.answer(
            text=t(MsgKey.TR_TRACKER_NAME_NOT_FOUND, tracker_name=tracker_name)
        )
        return

    tracker = cast(TrackerResponse, tracker)
    await DataModel(tracker=tracker).save(state)

    await state.set_state(AddingData.AWAIT_NEXT_ACTION)
    await update_main_message(
        state=state,
        message=message,
        text=get_tracker_data_description_from_dto(tracker, data={}),
        reply_markup=kbr_builder.conf(
            add_cancel_button=True
        ).build_tracker_fields_keyboard(tracker),
        create_new=True,
    )


@router.callback_query(AddingData.AWAIT_NEXT_ACTION, FieldCallback.filter())
async def handle_field(
    callback: CallbackQueryWithMessage,
    callback_data: FieldCallback,
    state: FSMContext,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    data = await DataModelStrictTracker.load(state)

    field_type = data.tracker.structure.data.get(callback_data.name, {}).get("type")
    if not field_type:
        # impossible
        # TODO: add handling just in case
        pass
        return

    await DataModel(cur_field=callback_data.name).save(state)

    await state.set_state(AddingData.AWAIT_FIELD_VALUE)
    if field_type == "enum":
        enum_values = data.tracker.structure.data[callback_data.name].get("values", [])
        enum_values = enum_values or []
        kbr = kbr_builder.build_enum_values_keyboard(enum_values)
    else:
        kbr = None

    await update_main_message(
        state=state,
        message=callback.message,
        text=t(MsgKey.TR_ENTER_FIELD_VALUE, field_name=callback_data.name),
        reply_markup=kbr,
    )

    await callback.answer()


@router.message(AddingData.AWAIT_FIELD_VALUE)
async def handle_field_value(
    message: Message,
    state: FSMContext,
    tracker_service: TrackerService,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    data = await DataModelTR.load(state)
    current_field = data.cur_field
    field_values: dict = data.field_values or {}

    current_field_value = message.text
    field_values[current_field] = current_field_value

    handle_field_value_uc = HandleFieldValueUseCase(tracker_service)
    res, err = await handle_field_value_uc.execute(
        tracker=data.tracker,
        field_name=current_field,
        field_value=current_field_value,
        field_values=field_values,
    )
    if err:
        match err:
            case HandleFieldValueUseCase.Error.NO_TEXT:
                pass
        return

    if res:
        await update_main_message(
            state=state,
            text=t(MsgKey.TR_DATA_SAVED),
            message=message,
            create_new=True,
        )
        await state.clear()
    else:
        await DataModel(field_values=field_values).save(state)

        await state.set_state(AddingData.AWAIT_NEXT_ACTION)
        await update_main_message(
            state=state,
            text=get_tracker_data_description_from_dto(data.tracker, field_values),
            message=message,
            reply_markup=kbr_builder.conf(
                add_cancel_button=True
            ).build_tracker_fields_keyboard(
                data.tracker, exclude_fields=set(field_values.keys())
            ),
            create_new=True,
        )


@router.callback_query(AddingData.AWAIT_FIELD_VALUE, EnumValuesCallback.filter())
async def handle_enum_value(
    callback: CallbackQueryWithMessage,
    callback_data: EnumValuesCallback,
    state: FSMContext,
    tracker_service: TrackerService,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    data = await DataModelTR.load(state)
    current_field = data.cur_field
    field_values: dict = data.field_values or {}

    current_field_value = callback_data.value
    field_values[current_field] = current_field_value

    handle_field_value_uc = HandleFieldValueUseCase(tracker_service)
    res, err = await handle_field_value_uc.execute(
        tracker=data.tracker,
        field_name=current_field,
        field_value=current_field_value,
        field_values=field_values,
    )
    if err:
        match err:
            case HandleFieldValueUseCase.Error.NO_TEXT:
                pass
        return

    if res:
        await update_main_message(
            state=state,
            text=t(MsgKey.TR_DATA_SAVED),
            message=callback.message,
        )
        await state.clear()
    else:
        await DataModel(field_values=field_values).save(state)
        await state.set_state(AddingData.AWAIT_NEXT_ACTION)
        await update_main_message(
            state=state,
            text=get_tracker_data_description_from_dto(data.tracker, field_values),
            message=callback.message,
            reply_markup=kbr_builder.conf(
                add_cancel_button=True
            ).build_tracker_fields_keyboard(
                data.tracker, exclude_fields=set(field_values.keys())
            ),
        )
    await callback.answer()


@router.callback_query(AddingData.AWAIT_NEXT_ACTION, CancelCallback.filter())
async def handle_cancel(
    callback: CallbackQueryWithMessage, state: FSMContext, t: TFunction
):
    await state.clear()
    await callback.message.edit_text(
        text=t(MsgKey.TR_ADDING_DATA_CANCELED),
        reply_markup=None,
    )
    await callback.answer()
