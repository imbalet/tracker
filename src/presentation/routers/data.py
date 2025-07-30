from datetime import datetime, timedelta, timezone
from typing import Literal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types.input_file import BufferedInputFile

from src.presentation.callbacks import (
    PeriodCallback,
    TrackerActionsCallback,
    TrackerDataActionsCallback,
)
from src.presentation.states import DataStates
from src.presentation.utils import (
    build_period_keyboard,
    build_tracker_data_action_keyboard,
    update_main_message,
)
from src.services.database.data_service import DataService
from src.use_cases import GetCSVUseCase

router = Router(name=__name__)


@router.callback_query(TrackerActionsCallback.filter(F.action == "get_options"))
@router.callback_query(PeriodCallback.filter(F.period == "back"))
async def tracker_actions_options(callback: CallbackQuery, state: FSMContext):
    await update_main_message(
        state=state,
        message=callback.message,  # type: ignore
        text="Выберете действие",
        reply_markup=build_tracker_data_action_keyboard(),
    )
    await state.set_state(None)
    await state.update_data(period_type=None)
    await callback.answer()


@router.callback_query(TrackerDataActionsCallback.filter(F.action != "back"))
async def period_type_select(
    callback: CallbackQuery,
    callback_data: TrackerDataActionsCallback,
    state: FSMContext,
):
    await update_main_message(
        state=state,
        message=callback.message,  # type: ignore
        text="Выберете единицу измерения периода",
        reply_markup=build_period_keyboard(),
    )
    await state.update_data(action=callback_data.action)
    await callback.answer()


@router.callback_query(PeriodCallback.filter(F.period != "back"))
async def period_select(
    callback: CallbackQuery,
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
        message=callback.message,  # type: ignore
        text=f"Введите число {period_word}",
    )
    await state.set_state(DataStates.AWAIT_PERIOD_VALUE)
    await state.update_data(period_type=callback_data.period)
    await callback.answer()


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


@router.message(DataStates.AWAIT_PERIOD_VALUE)
async def handle_period_value(
    message: Message, state: FSMContext, data_service: DataService
):
    if not message.text or not message.text.isdecimal():
        message.answer("Ошибочное значение")
        return
    await state.update_data(period_value=int(message.text))
    await state.set_state(None)
    data = await state.get_data()
    action = data["action"]

    match action:
        case "csv":
            uc = GetCSVUseCase(data_service)
            res = await uc.execute(
                data["tracker_id"], convert_date(data["period_type"], int(message.text))
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
            await message.answer("stats")
