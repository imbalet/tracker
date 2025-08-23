from aiogram import F, Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.presentation.callbacks import ActionCallback, CancelCallback, FieldTypeCallback
from src.presentation.constants import (
    ST_CR_CUR_ENUM_VALUES,
    ST_CR_CUR_FIELD_TYPE,
    ST_CR_TRACKER,
)
from src.presentation.constants.text import MsgKey
from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.states import TrackerCreation
from src.presentation.utils import (
    CallbackQueryWithMessage,
    KeyboardBuilder,
    TFunction,
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
    if not message.text:
        await message.answer(t(MsgKey.CR_AT_LEAST_ONE_SYM))
        return

    tracker_dict = {"name": message.text, "fields": {}}
    await state.update_data(data={ST_CR_TRACKER: tracker_dict})
    await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)

    await update_main_message(
        state=state,
        message=message,
        text=get_tracker_description(tracker_dict, t(MsgKey.CR_CREATING)),  # type: ignore
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
    await state.update_data(data={ST_CR_CUR_FIELD_TYPE: callback_data.type})

    if callback_data.type == "enum":
        next_state = TrackerCreation.AWAIT_ENUM_VALUES
        message_text = t(MsgKey.CR_SELECTED_ENUM, type=callback_data.type.upper())
    else:
        next_state = TrackerCreation.AWAIT_FIELD_NAME
        message_text = t(MsgKey.CR_SELECTED, type=callback_data.type.upper())
    await state.set_state(next_state)

    await update_main_message(
        state=state,
        message=callback.message,
        text=message_text,
    )
    await callback.answer()


@router.message(TrackerCreation.AWAIT_ENUM_VALUES)
async def process_enum_values(message: Message, state: FSMContext, t: TFunction):
    if not message.text:
        await update_main_message(
            state=state,
            message=message,
            text=t(MsgKey.CR_EMPTY_ENUM),
            create_new=True,
        )
        return

    options = str(message.text).split("/")
    if len(options) < 2:
        await update_main_message(
            state=state,
            message=message,
            text=t(MsgKey.CR_ENUM_WRONG_COUNT, count=len(options)),
            create_new=True,
        )
        return

    await state.update_data(data={ST_CR_CUR_ENUM_VALUES: message.text})
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)

    text = t(MsgKey.CR_SELECTED_ENUM_VALUES, enum_values=", ".join(options))
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
    if not message.text:
        await update_main_message(
            state=state,
            message=message,
            text=t(MsgKey.CR_NO_FIELD_NAME),
            create_new=True,
        )
        return

    data = await state.get_data()
    field_name = str(message.text).strip()
    field_type = data[ST_CR_CUR_FIELD_TYPE]
    tracker = data[ST_CR_TRACKER]

    if field_name in tracker["fields"]:
        await update_main_message(
            state=state,
            message=message,
            text=(
                t(
                    MsgKey.CR_FIELD_NAME_EXISTS_ENUM,
                    name=message.text,
                    field_name=data[ST_CR_CUR_FIELD_TYPE],
                    values=data[ST_CR_CUR_ENUM_VALUES],
                )
                if data[ST_CR_CUR_FIELD_TYPE] == "enum"
                else t(
                    MsgKey.CR_FIELD_NAME_EXISTS,
                    name=message.text,
                    field_name=data[ST_CR_CUR_FIELD_TYPE],
                )
            ),
            create_new=True,
        )
        return

    field_data = {"type": field_type}
    if field_type == "enum":
        field_data["values"] = data.get(ST_CR_CUR_ENUM_VALUES, "")
    tracker["fields"][field_name] = field_data

    await state.update_data(
        data={
            ST_CR_TRACKER: tracker,
            ST_CR_CUR_FIELD_TYPE: None,
            ST_CR_CUR_ENUM_VALUES: None,
        }
    )
    await state.set_state(TrackerCreation.AWAIT_NEXT_ACTION)

    await update_main_message(
        state=state,
        message=message,
        text=get_tracker_description(tracker, t(MsgKey.CR_CREATING)),
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
    data = await state.get_data()
    tracker = data[ST_CR_TRACKER]
    await state.set_state(TrackerCreation.AWAIT_FIELD_TYPE)
    await update_main_message(
        state=state,
        message=callback.message,
        text=get_tracker_description(tracker, t(MsgKey.CR_CREATING)),
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
    data = await state.get_data()
    tracker = data[ST_CR_TRACKER]
    if len(tracker["fields"]) == 0:
        await callback.message.answer(t(MsgKey.CR_AT_LEAST_ONE_FIELD_REQUIRED))
        return

    uc = CreateTrackerStructureUseCase(tracker_service, user_service)
    res = await uc.execute(
        user_id=str(callback.message.chat.id),
        tracker_name=tracker["name"],
        structure=TrackerStructureCreate(data=tracker["fields"]),
    )

    await update_main_message(
        state=state,
        message=callback.message,
        text=t(MsgKey.CR_CREATED, description=get_tracker_description_from_dto(res)),
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
