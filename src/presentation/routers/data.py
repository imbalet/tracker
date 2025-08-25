from io import BytesIO
from typing import Literal, cast

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile

from src.presentation.callbacks import (
    BackCallback,
    CancelCallback,
    ConfirmCallback,
    FieldCallback,
    PeriodCallback,
    TrackerActionsCallback,
    TrackerDataActionsCallback,
)
from src.presentation.constants import PERIOD_TYPES
from src.presentation.constants.text import MsgKey
from src.presentation.states import DataState
from src.presentation.utils import (
    CallbackQueryWithMessage,
    KeyboardBuilder,
    TFunction,
    convert_date,
    update_main_message,
)
from src.presentation.utils.state import StateModel
from src.schemas.tracker import TrackerResponse
from src.services.database.data_service import DataService
from src.services.database.tracker_service import TrackerService
from src.use_cases import (
    GetStatisticsUseCase,
    HandleActionUseCase,
    HandleFieldsConfirmUseCase,
    HandleFieldUseCase,
    HandlePeriodValueUseCase,
)

router = Router(name=__name__)


class DataModelAction(StateModel):
    tracker: TrackerResponse
    action: str
    period_type: Literal["years", "months", "weeks", "days", "hours", "minutes"]


class DataModelStrict(DataModelAction):
    period_value: int
    selected_fields: list[str]


class DataModel(StateModel):
    tracker: TrackerResponse | None = None
    action: str | None = None
    period_type: str | None = None
    period_value: int | None = None
    selected_fields: list[str] | None = None


@router.callback_query(DataState.AWAIT_FIELDS_SELECTION, CancelCallback.filter())
@router.callback_query(TrackerActionsCallback.filter(F.action == "get_options"))
@router.callback_query(DataState.AWAIT_PERIOD_TYPE, BackCallback.filter())
async def tracker_actions_options(
    callback: CallbackQueryWithMessage,
    state: FSMContext,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    await state.set_state(DataState.AWAIT_ACTION)
    await update_main_message(
        state=state,
        message=callback.message,
        text=t(MsgKey.DT_SELECT_ACTION),
        reply_markup=kbr_builder.conf(
            add_back_button=True
        ).build_tracker_data_action_keyboard(),
    )
    await callback.answer()


@router.callback_query(TrackerDataActionsCallback.filter())
async def period_type_select(
    callback: CallbackQueryWithMessage,
    callback_data: TrackerDataActionsCallback,
    state: FSMContext,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    await state.set_state(DataState.AWAIT_PERIOD_TYPE)
    await DataModel(action=callback_data.action).save(state)

    await update_main_message(
        state=state,
        message=callback.message,
        text=t(MsgKey.DT_SELECT_PERIOD_TYPE),
        reply_markup=kbr_builder.conf(add_back_button=True).build_period_keyboard(),
    )
    await callback.answer()


@router.callback_query(PeriodCallback.filter())
async def period_value_select(
    callback: CallbackQueryWithMessage,
    callback_data: PeriodCallback,
    state: FSMContext,
    t: TFunction,
):
    period_word = t(PERIOD_TYPES[callback_data.period])
    await state.set_state(DataState.AWAIT_PERIOD_VALUE)
    await DataModel(period_type=callback_data.period).save(state)

    await update_main_message(
        state=state,
        message=callback.message,
        text=t(MsgKey.DT_PERIOD_ENTER_NUMBER, period_word=period_word),
    )
    await callback.answer()


@router.message(DataState.AWAIT_PERIOD_VALUE)
async def handle_period_value(
    message: Message,
    state: FSMContext,
    data_service: DataService,
    tracker_service: TrackerService,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    handle_period_value_uc = HandlePeriodValueUseCase()
    period_value, err = handle_period_value_uc.execute(text=message.text)

    if err:
        match err:
            case HandlePeriodValueUseCase.Error.NO_TEXT:
                await message.answer(t(MsgKey.DT_WRONG_VALUE))
            case HandlePeriodValueUseCase.Error.WRONG_VALUE:
                await message.answer(t(MsgKey.DT_WRONG_VALUE))
        return

    data = await DataModelAction.load(state)
    await DataModel(period_value=period_value).save(state)

    handle_action_uc = HandleActionUseCase(
        tracker_service=tracker_service, data_service=data_service
    )

    match data.action:
        case "csv":
            await state.clear()
            res, err = await handle_action_uc.execute_csv(
                tracker_id=data.tracker.id,
                period_type=data.period_type,
                period_value=period_value,
            )
            if err:
                match err:
                    case HandleActionUseCase.Error.NO_RECORDS:
                        await message.answer(t(MsgKey.DT_NO_RECORDS))
                return

            res = cast(BytesIO, res)
            file = BufferedInputFile(res.getvalue(), filename="data.csv")
            await message.answer(t(MsgKey.DT_SENDING_CSV))
            await message.answer_document(document=file)
        case "table":
            await message.answer("TODO")
            # TODO: add selecting fields, aggregations
            pass
        case "graph":
            # TODO: add selecting fields for axes, aggregations
            await message.answer("TODO")
            pass
        case "statistics":
            await state.set_state(DataState.AWAIT_FIELDS_SELECTION)
            tracker = await tracker_service.get_by_id(data.tracker.id)
            await DataModel(selected_fields=[]).save(state)
            await update_main_message(
                state=state,
                message=message,
                text=t(MsgKey.DT_SELECT_FIELDS),
                reply_markup=kbr_builder.conf(
                    add_cancel_button=True, add_confirm_button=True
                ).build_tracker_fields_keyboard(tracker),
            )


@router.callback_query(DataState.AWAIT_FIELDS_SELECTION, FieldCallback.filter())
async def handle_field(
    callback: CallbackQueryWithMessage,
    callback_data: FieldCallback,
    state: FSMContext,
    tracker_service: TrackerService,
    t: TFunction,
    kbr_builder: KeyboardBuilder,
):
    data = await DataModelStrict.load(state)
    selected_fields: list = data.selected_fields

    handle_field_uc = HandleFieldUseCase(tracker_service=tracker_service)
    selected_fields, fields_text, tracker = await handle_field_uc.execute(
        field_name=callback_data.name,
        selected_fields=selected_fields,
        tracker_id=data.tracker.id,
    )
    await DataModel(selected_fields=selected_fields).save(state)

    await update_main_message(
        state=state,
        message=callback.message,
        text=t(MsgKey.DT_SELECTED_FIELDS, selected_fields=fields_text),
        reply_markup=kbr_builder.conf(
            add_cancel_button=True, add_confirm_button=True
        ).build_tracker_fields_keyboard(
            tracker, marked_fields=set(selected_fields), mark="✅"
        ),
    )
    await callback.answer()


@router.callback_query(DataState.AWAIT_FIELDS_SELECTION, ConfirmCallback.filter())
async def handle_field_confirm(
    callback: CallbackQueryWithMessage,
    state: FSMContext,
    data_service: DataService,
    tracker_service: TrackerService,
    t: TFunction,
):
    await state.set_state(None)
    data = await DataModelStrict.load(state)
    selected_fields: list = data.selected_fields

    handle_fields_confirm_uc = HandleFieldsConfirmUseCase(
        tracker_service=tracker_service
    )
    numeric_fields, categorial_fields = await handle_fields_confirm_uc.execute(
        selected_fields=selected_fields, tracker_id=data.tracker.id
    )
    # TODO: add selected fields length validation
    uc = GetStatisticsUseCase(data_service=data_service)
    res, err = await uc.execute(
        categorial_fields=categorial_fields,
        numeric_fields=numeric_fields,
        tracker_id=data.tracker.id,
        from_date=convert_date(data.period_type, data.period_value),
    )
    if err:
        match err:
            case GetStatisticsUseCase.Error.NO_FIELDS:
                # TODO: change text
                await callback.message.answer(t(MsgKey.DT_NO_RECORDS))
                await callback.answer()
        return
    if not res:
        await callback.message.answer(t(MsgKey.DT_NO_RECORDS))
        await callback.answer()
        return
    await update_main_message(
        state=state,
        message=callback.message,
        # TODO move statistics presentation to a data model
        # TODO: add categorial fields processing
        text="\n".join(
            [
                f"- {i.field_name}: min - {i.min}, max - {i.max}, avg - {i.avg}, sum - {i.sum}, count - {i.count}"
                for i in res
            ]
        ),
    )
    await callback.answer()
