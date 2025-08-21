from datetime import datetime, timedelta, timezone
from typing import Literal

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
    ST_DT_ACTION,
    ST_DT_PERIOD_TYPE,
    ST_DT_PERIOD_VALUE,
    ST_DT_SELECTED_FIELDS,
    ST_TRACKER_ID,
)
from src.presentation.states import DataState
from src.presentation.utils import (
    CallbackQueryWithMessage,
    build_period_keyboard,
    build_tracker_data_action_keyboard,
    build_tracker_fields_keyboard,
    update_main_message,
)
from src.services.database.data_service import DataService
from src.services.database.tracker_service import TrackerService
from src.use_cases import GetCSVUseCase, GetStatisticsUseCase

router = Router(name=__name__)


@router.callback_query(TrackerActionsCallback.filter(F.action == "get_options"))
@router.callback_query(DataState.AWAIT_PERIOD_TYPE, BackCallback.filter())
async def tracker_actions_options(
    callback: CallbackQueryWithMessage, state: FSMContext
):
    await state.set_state(DataState.AWAIT_ACTION)
    await update_main_message(
        state=state,
        message=callback.message,
        text="Выберете действие",
        reply_markup=build_tracker_data_action_keyboard(
            extra_buttons=[("Назад", BackCallback())]
        ),
    )
    await callback.answer()


@router.callback_query(TrackerDataActionsCallback.filter())
async def period_type_select(
    callback: CallbackQueryWithMessage,
    callback_data: TrackerDataActionsCallback,
    state: FSMContext,
):
    await state.set_state(DataState.AWAIT_PERIOD_TYPE)
    await state.update_data(data={ST_DT_ACTION: callback_data.action})

    await update_main_message(
        state=state,
        message=callback.message,
        text="Выберете единицу измерения периода",
        reply_markup=build_period_keyboard(extra_buttons=[("Назад", BackCallback())]),
    )
    await callback.answer()


@router.callback_query(PeriodCallback.filter())
async def period_select(
    callback: CallbackQueryWithMessage,
    callback_data: PeriodCallback,
    state: FSMContext,
):
    # TODO: Use dict
    match callback_data.period:
        case "years":
            period_word = "лет"
        case "months":
            period_word = "месяцев"
        case "weeks":
            period_word = "недель"
        case "days":
            period_word = "дней"
        case "hours":
            period_word = "часов"
        case "minutes":
            period_word = "минут"
        case _:
            period_word = "чего-либо"

    await update_main_message(
        state=state,
        message=callback.message,
        text=f"Введите число {period_word}",
    )
    await state.set_state(DataState.AWAIT_PERIOD_VALUE)
    await state.update_data(data={ST_DT_PERIOD_TYPE: callback_data.period})
    await callback.answer()


# TODO: move to utils
def convert_date(
    date_type: Literal["years", "months", "weeks", "days", "hours", "minutes"],
    count: int,
) -> datetime:
    now_datetime = datetime.now(timezone.utc)
    match date_type:
        case "years":
            return now_datetime - timedelta(days=(365 * count))
        case "months":
            return now_datetime - timedelta(days=(30 * count))
        case "weeks":
            return now_datetime - timedelta(weeks=count)
        case "days":
            return now_datetime - timedelta(days=count)
        case "hours":
            return now_datetime - timedelta(hours=count)
        case "minutes":
            return now_datetime - timedelta(minutes=count)


@router.message(DataState.AWAIT_PERIOD_VALUE)
async def handle_period_value(
    message: Message,
    state: FSMContext,
    data_service: DataService,
    tracker_service: TrackerService,
):
    if not message.text or not message.text.isdecimal():
        await message.answer("Ошибочное значение")
        return
    await state.update_data(data={ST_DT_PERIOD_VALUE: int(message.text)})
    data = await state.get_data()
    action = data[ST_DT_ACTION]

    match action:
        case "csv":
            await state.set_state(None)
            uc = GetCSVUseCase(data_service)
            res = await uc.execute(
                data[ST_TRACKER_ID],
                convert_date(data[ST_DT_PERIOD_TYPE], int(message.text)),
            )
            file = BufferedInputFile(res.getvalue(), filename="data.csv")
            await message.answer("Вам будет отправлен CSV файл с данными.")
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
                text="Выберете поля",
                reply_markup=build_tracker_fields_keyboard(
                    tracker,
                    extra_buttons=[
                        ("Готово", ConfirmCallback()),
                        ("Отмена", CancelCallback()),
                    ],
                ),
            )


@router.callback_query(DataState.AWAIT_FIELDS_SELECTION, FieldCallback.filter())
async def handle_field(
    callback: CallbackQueryWithMessage,
    callback_data: FieldCallback,
    state: FSMContext,
    tracker_service: TrackerService,
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
        text=f"Выбранные поля: {fields_text}",
        reply_markup=build_tracker_fields_keyboard(
            tracker,
            marked_fields=set(selected_fields),
            mark="✅",
            extra_buttons=[("Готово", ConfirmCallback())],
        ),
    )


@router.callback_query(DataState.AWAIT_FIELDS_SELECTION, CancelCallback.filter())
async def handle_field_cancel(
    callback: CallbackQueryWithMessage,
    state: FSMContext,
):
    # TODO: change
    await state.set_state(None)
    await state.clear()
    await callback.message.delete()


@router.callback_query(DataState.AWAIT_FIELDS_SELECTION, ConfirmCallback.filter())
async def handle_field_confirm(
    callback: CallbackQueryWithMessage,
    state: FSMContext,
    data_service: DataService,
    tracker_service: TrackerService,
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
        text="\n".join(
            [
                f"- {i.field_name}: min - {i.min}, max - {i.max}, avg - {i.avg}, sum - {i.sum}, count - {i.count}"
                for i in res
            ]
        ),
    )
