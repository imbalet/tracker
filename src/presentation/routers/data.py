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
from src.presentation.constants import (
    PERIOD_TYPES,
    ST_DT_ACTION,
    ST_DT_PERIOD_TYPE,
    ST_DT_PERIOD_VALUE,
    ST_DT_SELECTED_FIELDS,
    ST_TRACKER_ID,
)
from src.presentation.constants.text import Language, MsgKey
from src.presentation.states import DataState
from src.presentation.utils import (
    CallbackQueryWithMessage,
    build_period_keyboard,
    build_tracker_data_action_keyboard,
    build_tracker_fields_keyboard,
    convert_date,
    t,
    update_main_message,
)
from src.services.database.data_service import DataService
from src.services.database.tracker_service import TrackerService
from src.use_cases import GetCSVUseCase, GetStatisticsUseCase

router = Router(name=__name__)


@router.callback_query(DataState.AWAIT_FIELDS_SELECTION, CancelCallback.filter())
@router.callback_query(TrackerActionsCallback.filter(F.action == "get_options"))
@router.callback_query(DataState.AWAIT_PERIOD_TYPE, BackCallback.filter())
async def tracker_actions_options(
    callback: CallbackQueryWithMessage, state: FSMContext, lang: Language
):
    await state.set_state(DataState.AWAIT_ACTION)
    await update_main_message(
        state=state,
        message=callback.message,
        text=t(lang, MsgKey.DT_SELECT_ACTION),
        reply_markup=build_tracker_data_action_keyboard(
            lang, extra_buttons=[(t(lang, MsgKey.BACK), BackCallback())]
        ),
    )
    await callback.answer()


@router.callback_query(TrackerDataActionsCallback.filter())
async def period_type_select(
    callback: CallbackQueryWithMessage,
    callback_data: TrackerDataActionsCallback,
    state: FSMContext,
    lang: Language,
):
    await state.set_state(DataState.AWAIT_PERIOD_TYPE)
    await state.update_data(data={ST_DT_ACTION: callback_data.action})

    await update_main_message(
        state=state,
        message=callback.message,
        text=t(lang, MsgKey.DT_SELECT_PERIOD_TYPE),
        reply_markup=build_period_keyboard(
            lang, extra_buttons=[(t(lang, MsgKey.BACK), BackCallback())]
        ),
    )
    await callback.answer()


@router.callback_query(PeriodCallback.filter())
async def period_select(
    callback: CallbackQueryWithMessage,
    callback_data: PeriodCallback,
    state: FSMContext,
    lang: Language,
):
    period_word = t(lang, PERIOD_TYPES[callback_data.period])
    await state.set_state(DataState.AWAIT_PERIOD_VALUE)
    await state.update_data(data={ST_DT_PERIOD_TYPE: callback_data.period})

    await update_main_message(
        state=state,
        message=callback.message,
        text=t(lang, MsgKey.DT_PERIOD_ENTER_NUMBER, period_word=period_word),
    )
    await callback.answer()


@router.message(DataState.AWAIT_PERIOD_VALUE)
async def handle_period_value(
    message: Message,
    state: FSMContext,
    data_service: DataService,
    tracker_service: TrackerService,
    lang: Language,
):
    if not message.text or not message.text.isdecimal():
        await message.answer(t(lang, MsgKey.DT_WRONG_VALUE))
        return
    try:
        period_value = int(message.text)
    except (ValueError, TypeError):
        await message.answer(t(lang, MsgKey.DT_WRONG_VALUE))
        return

    await state.update_data(data={ST_DT_PERIOD_VALUE: period_value})
    data = await state.get_data()
    action = data[ST_DT_ACTION]

    match action:
        case "csv":
            await state.clear()
            uc = GetCSVUseCase(data_service)
            res = await uc.execute(
                data[ST_TRACKER_ID],
                convert_date(data[ST_DT_PERIOD_TYPE], int(message.text)),
            )
            file = BufferedInputFile(res.getvalue(), filename="data.csv")
            await message.answer(t(lang, MsgKey.DT_SENDING_CSV))
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
            tracker = await tracker_service.get_by_id(data[ST_TRACKER_ID])
            await state.update_data(data={ST_DT_SELECTED_FIELDS: []})
            await update_main_message(
                state=state,
                message=message,
                text=t(lang, MsgKey.DT_SELECT_FIELDS),
                reply_markup=build_tracker_fields_keyboard(
                    tracker,
                    lang,
                    extra_buttons=[
                        (t(lang, MsgKey.CONFIRM), ConfirmCallback()),
                        (t(lang, MsgKey.CANCEL), CancelCallback()),
                    ],
                ),
            )


@router.callback_query(DataState.AWAIT_FIELDS_SELECTION, FieldCallback.filter())
async def handle_field(
    callback: CallbackQueryWithMessage,
    callback_data: FieldCallback,
    state: FSMContext,
    tracker_service: TrackerService,
    lang: Language,
):
    field_name = callback_data.name
    data = await state.get_data()
    selected_fields: list = data[ST_DT_SELECTED_FIELDS]
    if field_name in selected_fields:
        selected_fields.remove(field_name)
    else:
        selected_fields.append(field_name)
    await state.update_data(data={ST_DT_SELECTED_FIELDS: selected_fields})

    fields_text = "\n".join([f"- {i}" for i in selected_fields])
    tracker = await tracker_service.get_by_id(data[ST_TRACKER_ID])
    await update_main_message(
        state=state,
        message=callback.message,
        text=t(lang, MsgKey.DT_SELECTED_FIELDS, selected_fields=fields_text),
        reply_markup=build_tracker_fields_keyboard(
            tracker,
            lang,
            marked_fields=set(selected_fields),
            mark="✅",
            extra_buttons=[
                (t(lang, MsgKey.CONFIRM), ConfirmCallback()),
                (t(lang, MsgKey.CANCEL), CancelCallback()),
            ],
        ),
    )


@router.callback_query(DataState.AWAIT_FIELDS_SELECTION, ConfirmCallback.filter())
async def handle_field_confirm(
    callback: CallbackQueryWithMessage,
    state: FSMContext,
    data_service: DataService,
    tracker_service: TrackerService,
    lang: Language,
):
    await state.set_state(None)
    data = await state.get_data()
    selected_fields: list = data[ST_DT_SELECTED_FIELDS]
    tracker = await tracker_service.get_by_id(data[ST_TRACKER_ID])
    numeric_fields = [
        i
        for i in selected_fields
        if tracker.structure.data[i]["type"] in ("int", "float")
    ]
    categorial_fields = [
        i
        for i in selected_fields
        if tracker.structure.data[i]["type"] not in ("int", "float")
    ]

    uc = GetStatisticsUseCase(data_service=data_service)
    res = await uc.execute(
        categorial_fields=categorial_fields,
        numeric_fields=numeric_fields,
        tracker_id=data[ST_TRACKER_ID],
        from_date=convert_date(data[ST_DT_PERIOD_TYPE], data[ST_DT_PERIOD_VALUE]),
    )
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
