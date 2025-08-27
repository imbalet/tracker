from typing import cast

from aiogram import F, Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from pydantic import Field

from tracker.core.dynamic_json.types import FieldDataType
from tracker.presentation.callbacks import (
    ActionCallback,
    CancelCallback,
    FieldTypeCallback,
)
from tracker.presentation.constants.text import MsgKey
from tracker.presentation.states import TrackerCreation
from tracker.presentation.utils import (
    CallbackQueryWithMessage,
    KeyboardBuilder,
    StateModel,
    TFunction,
    get_tracker_description,
    get_tracker_description_from_dto,
    update_main_message,
)
from tracker.schemas import TrackerCreate
from tracker.services.database import TrackerService, UserService
from tracker.use_cases import (
    CreateTrackerDraftUseCase,
    FinishTrackerCreation,
    ProcessEnumValuesUseCase,
    ProcessFieldNameUseCase,
)

router = Router(name=__name__)


class DataModelTracker(StateModel):
    tracker: TrackerCreate


class DataModelStrict(StateModel):
    tracker: TrackerCreate
    cur_field_type: FieldDataType
    cur_enum_values: list[str] = Field(default_factory=list)


class DataModel(StateModel):
    tracker: TrackerCreate | None = None
    cur_field_type: FieldDataType | None = None
    cur_enum_values: list[str] | None = None


@router.message(Command("add_tracker"))
async def start_tracker_creation(
    message: Message, state: FSMContext, t: TFunction
) -> None:
    await state.clear()
    await state.set_state(TrackerCreation.AWAIT_TRACKER_NAME)
    await message.answer(t(MsgKey.CR_ENTER_NAME))


@router.message(TrackerCreation.AWAIT_TRACKER_NAME)
async def process_tracker_name(
    message: Message, state: FSMContext, t: TFunction, kbr_builder: KeyboardBuilder
):
    create_tracker_draft_uc = CreateTrackerDraftUseCase()
    tracker, err = create_tracker_draft_uc.execute(
        name=message.text or "", user_id=str(message.chat.id)
    )

    if err:
        match err:
            case CreateTrackerDraftUseCase.Error.NO_TEXT:
                await message.answer(t(MsgKey.CR_AT_LEAST_ONE_SYM))
        return

    tracker = cast(TrackerCreate, tracker)
    await DataModel(tracker=tracker).save(state)
    await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)
    await update_main_message(
        state=state,
        message=message,
        text=get_tracker_description(tracker, t(MsgKey.CR_CREATING)),  # type: ignore
        reply_markup=kbr_builder.conf(
            add_cancel_button=True
        ).build_field_type_keyboard(),
        create_new=True,
    )


@router.callback_query(TrackerCreation.AWAIT_FIELD_TYPE, FieldTypeCallback.filter())
async def process_field_type(
    callback: CallbackQueryWithMessage,
    callback_data: FieldTypeCallback,
    state: FSMContext,
    t: TFunction,
):
    if callback_data.type == "enum":
        next_state = TrackerCreation.AWAIT_ENUM_VALUES
        message_text = t(MsgKey.CR_SELECTED_ENUM, type=callback_data.type.upper())
    else:
        next_state = TrackerCreation.AWAIT_FIELD_NAME
        message_text = t(MsgKey.CR_SELECTED, type=callback_data.type.upper())

    await state.set_state(next_state)
    await DataModel(cur_field_type=callback_data.type).save(state)
    await update_main_message(state=state, message=callback.message, text=message_text)
    await callback.answer()


@router.message(TrackerCreation.AWAIT_ENUM_VALUES)
async def process_enum_values(message: Message, state: FSMContext, t: TFunction):
    process_enum_values_uc = ProcessEnumValuesUseCase()
    options, err = process_enum_values_uc.execute(message.text)

    if err:
        match err:
            case ProcessEnumValuesUseCase.Error.NO_TEXT:
                await update_main_message(
                    state=state,
                    message=message,
                    text=t(MsgKey.CR_EMPTY_ENUM),
                    create_new=True,
                )
            case ProcessEnumValuesUseCase.Error.WRONG_COUNT:
                await update_main_message(
                    state=state,
                    message=message,
                    text=t(MsgKey.CR_ENUM_WRONG_COUNT, count=len(options)),
                    create_new=True,
                )
        return

    text = t(MsgKey.CR_SELECTED_ENUM_VALUES, enum_values=", ".join(options))
    await DataModel(cur_enum_values=options).save(state)
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await update_main_message(
        state=state,
        message=message,
        text=text,
        create_new=True,
    )


@router.message(TrackerCreation.AWAIT_FIELD_NAME)
async def process_field_name(
    message: Message, state: FSMContext, t: TFunction, kbr_builder: KeyboardBuilder
):
    data = await DataModelStrict.load(state)

    process_field_name_uc = ProcessFieldNameUseCase()
    tracker, err = process_field_name_uc.execute(
        field_name=message.text,
        field_type=data.cur_field_type,
        enum_values=data.cur_enum_values,
        tracker=data.tracker,
    )
    if err:
        match err:
            case ProcessFieldNameUseCase.Error.NO_TEXT:
                await update_main_message(
                    state=state,
                    message=message,
                    text=t(MsgKey.CR_NO_FIELD_NAME),
                    create_new=True,
                )
            case ProcessFieldNameUseCase.Error.ALREADY_EXISTS:
                await update_main_message(
                    state=state,
                    message=message,
                    text=(
                        t(
                            MsgKey.CR_FIELD_NAME_EXISTS_ENUM,
                            name=message.text,
                            field_name=data.cur_field_type,
                            values=", ".join(data.cur_enum_values),
                        )
                        if data.cur_field_type == "enum"
                        else t(
                            MsgKey.CR_FIELD_NAME_EXISTS,
                            name=message.text,
                            field_name=data.cur_field_type,
                        )
                    ),
                    create_new=True,
                )
            case ProcessFieldNameUseCase.Error.WRONG_STRUCTURE:
                # TODO: handle
                pass
        return

    await DataModel(tracker=tracker, cur_enum_values=None, cur_field_type=None).save(
        state
    )
    await state.set_state(TrackerCreation.AWAIT_NEXT_ACTION)
    await update_main_message(
        state=state,
        message=message,
        text=get_tracker_description(tracker, t(MsgKey.CR_CREATING)),  # type: ignore
        reply_markup=kbr_builder.build_action_keyboard(),
        create_new=True,
    )


@router.callback_query(
    TrackerCreation.AWAIT_NEXT_ACTION, ActionCallback.filter(F.action == "add_field")
)
async def process_next_action_add_field(
    callback: CallbackQueryWithMessage,
    state: FSMContext,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    data = await DataModelTracker.load(state)

    await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)
    await update_main_message(
        state=state,
        message=callback.message,
        text=get_tracker_description(data.tracker, t(MsgKey.CR_CREATING)),
        reply_markup=kbr_builder.conf(
            add_cancel_button=True
        ).build_field_type_keyboard(),
    )


@router.callback_query(
    TrackerCreation.AWAIT_NEXT_ACTION, ActionCallback.filter(F.action == "finish")
)
async def process_next_action_finish(
    callback: CallbackQueryWithMessage,
    state: FSMContext,
    tracker_service: TrackerService,
    user_service: UserService,
    t: TFunction,
):
    data = await DataModelTracker.load(state)

    uc = FinishTrackerCreation(tracker_service, user_service)
    tracker, err = await uc.execute(tracker=data.tracker)
    if err:
        match err:
            case FinishTrackerCreation.Error.AT_LEAST_ONE_FIELD_REQUIRED:
                await callback.message.answer(t(MsgKey.CR_AT_LEAST_ONE_FIELD_REQUIRED))
        return

    await update_main_message(
        state=state,
        message=callback.message,
        text=t(
            MsgKey.CR_CREATED, description=get_tracker_description_from_dto(tracker)  # type: ignore
        ),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(
    or_f(TrackerCreation.AWAIT_FIELD_TYPE, TrackerCreation.AWAIT_NEXT_ACTION),
    CancelCallback.filter(),
)
async def cancel_creation(
    callback: CallbackQueryWithMessage, state: FSMContext, t: TFunction
):
    await update_main_message(
        state=state,
        message=callback.message,
        text=t(MsgKey.CR_CANCELED),
    )
    await state.clear()
    await callback.answer()
