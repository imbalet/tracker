from typing import cast

from aiogram import Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.presentation.callbacks import (
    BackCallback,
    CancelCallback,
    EnumValuesCallback,
    FieldCallback,
    TrackerCallback,
)
from src.presentation.constants import (
    ST_TR_CURRENT_FIELD,
    ST_TR_CURRENT_TRACKER,
    ST_TR_FIELD_VALUES,
    ST_TRACKER_ID,
)
from src.presentation.constants.text import MsgKey
from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.states import AddingData, DataState, TrackerControlState
from src.presentation.utils import (
    CallbackQueryWithMessage,
    KeyboardBuilder,
    TFunction,
    get_tracker_data_description_from_dto,
    get_tracker_description_from_dto,
    update_main_message,
)
from src.schemas import TrackerResponse
from src.services.database import TrackerService
from src.use_cases import (
    DescribeTrackerUseCase,
    GetFieldType,
    HandleFieldValueUseCase,
    ShowTrackersUseCase,
    StartTrackingUseCase,
)

router = Router(name=__name__)
router.callback_query.middleware(CallbackMessageMiddleware())


@router.message(Command("my_trackers"))
async def show_trackers(
    message: Message,
    state: FSMContext,
    tracker_service: TrackerService,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
) -> None:
    show_trackers_uc = ShowTrackersUseCase(tracker_service=tracker_service)
    trackers, err = await show_trackers_uc.execute(user_id=str(message.chat.id))

    if err:
        match err:
            case ShowTrackersUseCase.Error.NO_TRACKERS:
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
    describe_tracker_uc = DescribeTrackerUseCase(tracker_service=tracker_service)
    tracker, err = await describe_tracker_uc.execute(tracker_id=callback_data.id)

    if err:
        match err:
            case DescribeTrackerUseCase.Error.NO_TRACKER:
                await update_main_message(
                    state=state,
                    message=callback.message,
                    text=t(MsgKey.TR_TRACKER_NOT_FOUND),
                    create_new=True,
                )
        return

    tracker = cast(TrackerResponse, tracker)
    await state.update_data(data={ST_TRACKER_ID: tracker.id})
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
    start_tracking_use_case = StartTrackingUseCase(tracker_service=tracker_service)
    tracker, tracker_name, err = await start_tracking_use_case.execute(
        text=message.text
    )

    await state.clear()
    if err:
        match err:
            case StartTrackingUseCase.Error.NO_TEXT:
                await message.answer(text=t(MsgKey.TR_TRACKER_NOT_ENTERED))
            case StartTrackingUseCase.Error.NO_TRACKER:
                await message.answer(
                    text=t(MsgKey.TR_TRACKER_NAME_NOT_FOUND, tracker_name=tracker_name)
                )
        return

    tracker = cast(TrackerResponse, tracker)
    await state.update_data(data={ST_TR_CURRENT_TRACKER: tracker.model_dump()})
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
    data = await state.get_data()
    get_field_type_uc = GetFieldType()
    field_type, tracker, err = get_field_type_uc.execute(
        tracker_dict=data[ST_TR_CURRENT_TRACKER], field_name=callback_data.name
    )
    if err:
        match err:
            case GetFieldType.Error.NO_FIELD:
                # impossible, TODO: add handling, just in case
                pass
        return

    await state.update_data(data={ST_TR_CURRENT_FIELD: callback_data.name})
    await state.set_state(AddingData.AWAIT_FIELD_VALUE)
    if field_type == "enum":
        enum_values = (
            tracker.structure.data[callback_data.name].get("values", "").split("/")  # type: ignore
        )
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
    data = await state.get_data()
    current_field = data[ST_TR_CURRENT_FIELD]
    field_values: dict = data.get(ST_TR_FIELD_VALUES, {})
    current_field_value = message.text
    field_values[current_field] = current_field_value

    handle_field_value_uc = HandleFieldValueUseCase(tracker_service)
    res, tracker, err = await handle_field_value_uc.execute(
        tracker_dict=data[ST_TR_CURRENT_TRACKER],
        field_name=current_field,
        field_value=current_field_value,
        field_values=field_values,
    )
    if err:
        match err:
            case HandleFieldValueUseCase.Error.NO_TEXT:
                pass
        return

    tracker = cast(TrackerResponse, tracker)
    if res:
        await update_main_message(
            state=state,
            text=t(MsgKey.TR_DATA_SAVED),
            message=message,
            create_new=True,
        )
        await state.clear()
    else:
        await state.update_data(data={ST_TR_FIELD_VALUES: field_values})
        await state.set_state(AddingData.AWAIT_NEXT_ACTION)
        await update_main_message(
            state=state,
            text=get_tracker_data_description_from_dto(tracker, field_values),
            message=message,
            reply_markup=kbr_builder.conf(
                add_cancel_button=True
            ).build_tracker_fields_keyboard(
                tracker, exclude_fields=set(field_values.keys())
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
    data = await state.get_data()
    current_field = data[ST_TR_CURRENT_FIELD]
    field_values: dict = data.get(ST_TR_FIELD_VALUES, {})
    current_field_value = callback_data.value
    field_values[current_field] = current_field_value

    handle_field_value_uc = HandleFieldValueUseCase(tracker_service)
    res, tracker, err = await handle_field_value_uc.execute(
        tracker_dict=data[ST_TR_CURRENT_TRACKER],
        field_name=current_field,
        field_value=current_field_value,
        field_values=field_values,
    )
    if err:
        match err:
            case HandleFieldValueUseCase.Error.NO_TEXT:
                pass
        return

    tracker = cast(TrackerResponse, tracker)
    if res:
        await update_main_message(
            state=state,
            text=t(MsgKey.TR_DATA_SAVED),
            message=callback.message,
        )
        await state.clear()
    else:
        await state.update_data(data={ST_TR_FIELD_VALUES: field_values})
        await state.set_state(AddingData.AWAIT_NEXT_ACTION)
        await update_main_message(
            state=state,
            text=get_tracker_data_description_from_dto(tracker, field_values),
            message=callback.message,
            reply_markup=kbr_builder.conf(
                add_cancel_button=True
            ).build_tracker_fields_keyboard(
                tracker, exclude_fields=set(field_values.keys())
            ),
        )
    callback.answer


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
