from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from aiogram.fsm.context import FSMContext

from src.presentation.callbacks import FieldCallback, TrackerCallback
from src.presentation.constants.text import Language
from src.presentation.routers.tracker_control import (
    describe_tracker,
    handle_field,
    handle_field_value,
    show_trackers,
    start_tracking,
)
from src.presentation.states import AddingData
from src.schemas import TrackerResponse
from src.schemas.tracker import TrackerDataCreate
from tests.integration.bot.utils import create_callback, create_message


async def test_valid_show_trackers(
    tracker_service,
    sample_tracker_response: TrackerResponse,
    state: FSMContext,
    lang: Language,
):
    message = create_message("/my_trackers")
    tracker1 = sample_tracker_response.model_copy()
    tracker1.id = uuid4()
    tracker1.name = "new_name"
    tracker_service.get_by_user_id = AsyncMock(
        return_value=[sample_tracker_response, tracker1]
    )

    await show_trackers(message, state, tracker_service, lang)
    assert "Трекеры:" in message.answer.call_args.kwargs["text"]
    assert "reply_markup" in message.answer.call_args.kwargs


async def test_empty_show_trackers(
    tracker_service,
    state: FSMContext,
    lang: Language,
):
    message = create_message("/my_trackers")
    tracker_service.get_by_user_id = AsyncMock(return_value=[])

    await show_trackers(message, state, tracker_service, lang)

    assert "У вас пока нет трекеров" in message.answer.call_args.kwargs["text"]
    assert "reply_markup" not in message.answer.call_args.kwargs


async def test_valid_describe_tracker(
    state: FSMContext,
    tracker_service,
    sample_tracker_response: TrackerResponse,
    lang: Language,
):
    message = create_message("")
    callback = create_callback(message)
    tracker_service.get_by_id = AsyncMock(return_value=sample_tracker_response)

    await describe_tracker(
        callback,
        TrackerCallback(id=sample_tracker_response.id),
        state,
        tracker_service,
        lang,
    )

    tracker_service.get_by_id.assert_awaited_with(sample_tracker_response.id)


async def test_empty_describe_tracker(
    state: FSMContext,
    tracker_service,
    lang: Language,
):
    message = create_message("")
    callback = create_callback(message)
    tracker_service.get_by_id = AsyncMock(return_value=None)

    tracker_id = uuid4()
    await describe_tracker(
        callback, TrackerCallback(id=tracker_id), state, tracker_service, lang
    )

    tracker_service.get_by_id.assert_awaited_with(tracker_id)
    assert "Трекер не найден" in message.answer.call_args.kwargs["text"]


async def test_valid_start_tracking(
    state: FSMContext,
    tracker_service,
    sample_tracker_response: TrackerResponse,
    lang: Language,
):
    message = create_message(f"/track {sample_tracker_response.name}")
    tracker_service.get_by_name = AsyncMock(return_value=sample_tracker_response)

    await start_tracking(message, state, tracker_service, lang)

    assert await state.get_state() == AddingData.AWAIT_NEXT_ACTION
    tracker_service.get_by_name.assert_awaited_with(sample_tracker_response.name)
    assert "reply_markup" in message.answer.call_args.kwargs


async def test_not_exists_start_tracking(
    state: FSMContext,
    tracker_service,
    lang: Language,
):
    message = create_message("/track not_exists")
    tracker_service.get_by_name = AsyncMock(return_value=None)

    await start_tracking(message, state, tracker_service, lang)

    assert await state.get_state() is None
    tracker_service.get_by_name.assert_awaited_with("not_exists")
    assert "Трекер 'not_exists' не найден" in message.answer.call_args.kwargs["text"]


async def test_empty_start_tracking(
    state: FSMContext,
    tracker_service,
    lang: Language,
):
    message = create_message("/track")

    await start_tracking(message, state, tracker_service, lang)

    assert await state.get_state() is None
    assert "Ошибка: Не указан трекер!" in message.answer.call_args.kwargs["text"]


async def test_valid_handle_field(
    state: FSMContext,
    lang: Language,
):
    message = create_message("")
    callback = create_callback(message)
    callback_data = FieldCallback(name="field_name", type="int")

    await handle_field(callback, callback_data, state, lang)

    assert (await state.get_data())["current_field"] == "field_name"
    assert await state.get_state() == AddingData.AWAIT_FIELD_VALUE
    assert "Введите значение поля" in message.answer.call_args.kwargs["text"]


@pytest.mark.parametrize(
    "field_type, field_value",
    [
        ("int", "1"),
        ("int", "-1"),
        ("float", "1.1"),
        ("float", "-1.1"),
        ("string", "str"),
        ("enum", "yes"),
    ],
)
async def test_valid_first_call_handle_field_value(
    state: FSMContext,
    tracker_service,
    sample_tracker_response: TrackerResponse,
    field_type: str,
    field_value: str,
    lang: Language,
):
    message = create_message(field_value)
    sample_tracker_response.structure.data = {
        "field_name": {"type": field_type},  # type: ignore
        "another_name": {"type": "int"},
    }
    if field_type == "enum":
        sample_tracker_response.structure.data["field_name"]["values"] = "yes/no"
    await state.update_data(
        current_field="field_name",
        current_tracker=sample_tracker_response.model_dump_json(),
    )

    await handle_field_value(message, state, tracker_service, lang)

    data = await state.get_data()
    assert await state.get_state() == AddingData.AWAIT_NEXT_ACTION
    message.answer.assert_awaited_once()
    assert "field_values" in data and data["field_values"] == {
        "field_name": message.text
    }


@pytest.mark.parametrize(
    "field_type, field_value",
    [
        ("int", "1"),
        ("int", "-1"),
        ("float", "1.1"),
        ("float", "-1.1"),
        ("string", "str"),
        ("enum", "yes"),
    ],
)
async def test_valid_finish_handle_field_value(
    state: FSMContext,
    tracker_service,
    sample_tracker_response: TrackerResponse,
    field_type: str,
    field_value: str,
    lang: Language,
):
    message = create_message(field_value)
    tracker_service.add_data = AsyncMock(return_value=None)

    sample_tracker_response.structure.data = {
        "field_name": {"type": field_type},  # type: ignore
        "another_name": {"type": "int"},
    }
    if field_type == "enum":
        sample_tracker_response.structure.data["field_name"]["values"] = "yes/no"

    await state.update_data(
        current_field="field_name",
        current_tracker=sample_tracker_response.model_dump_json(),
        filled_fields=["another_name"],
        field_values={"another_name": "1"},
    )

    await handle_field_value(message, state, tracker_service, lang)

    assert await state.get_state() is None
    message.answer.assert_awaited_once()
    tracker_service.add_data.assert_awaited_once_with(
        TrackerDataCreate(
            tracker_id=sample_tracker_response.id,
            data={"another_name": "1", "field_name": message.text},
        )
    )
