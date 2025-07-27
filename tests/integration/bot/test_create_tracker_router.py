import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from pytest_mock import MockerFixture

from src.presentation.callbacks import ActionCallback, FieldTypeCallback
from src.presentation.routers.create_tracker import (
    cancel_creation,
    process_enum_values,
    process_field_name,
    process_field_type,
    process_next_action,
    process_tracker_name,
    start_tracker_creation,
)
from src.presentation.states import TrackerCreation
from src.schemas import TrackerResponse, TrackerStructureResponse, UserResponse
from src.services.database import TrackerService, UserService


def create_message(text: str | None):
    chat = types.Chat(id=0, type="private")

    message = AsyncMock(spec=types.Message)
    message.message_id = 0
    message.chat = chat
    message.text = text
    message.date = datetime.datetime.now(datetime.UTC)
    message.bot = AsyncMock()

    message.answer = AsyncMock()
    message.delete = AsyncMock()
    return message


def create_callback(message) -> AsyncMock:
    callback = AsyncMock(types.CallbackQuery)
    callback.message = message
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def user_service():
    service = AsyncMock(spec=UserService)
    return service


@pytest.fixture
def tracker_service():
    service = AsyncMock(spec=TrackerService)
    return service


@pytest.fixture
def state():
    return FSMContext(
        storage=MemoryStorage(), key=StorageKey(bot_id=0, chat_id=0, user_id=0)
    )


async def test_valid_start_tracker_creation(state: FSMContext):
    message = create_message("/add_tracker")
    await state.update_data(temp_data="temp")

    await start_tracker_creation(message, state)

    assert await state.get_state() == TrackerCreation.AWAIT_TRACKER_NAME
    assert len(await state.get_data()) == 0
    message.answer.assert_awaited_with("Введите название трекера:")


async def test_valid_process_tracker_name(state: FSMContext):
    message = create_message("tracker_name")
    await state.set_state(TrackerCreation.AWAIT_TRACKER_NAME)

    await process_tracker_name(message, state)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_TYPE
    assert len(data) > 0

    assert "tracker" in data and data["tracker"]["name"] == "tracker_name"
    assert "reply_markup" in message.answer.call_args.kwargs


@pytest.mark.parametrize("text", [None, ""])
async def test_empty_name_process_tracker_name(state: FSMContext, text):
    message = create_message(text)
    await state.set_state(TrackerCreation.AWAIT_TRACKER_NAME)

    await process_tracker_name(message, state)
    assert await state.get_state() == TrackerCreation.AWAIT_TRACKER_NAME
    message.answer.assert_awaited_with("Имя должно состоять хотя бы из одного символа")


@pytest.mark.parametrize(
    "callback_data",
    [
        FieldTypeCallback(type="float"),
        FieldTypeCallback(type="int"),
        FieldTypeCallback(type="string"),
    ],
)
async def test_valid_process_field_type_simple_types(state: FSMContext, callback_data):
    message = create_message("")
    callback = create_callback(message)

    await process_field_type(callback, callback_data, state)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert data["current_field_type"] == callback_data.type


async def test_valid_process_field_type_enum_type(state: FSMContext):
    message = create_message("")
    callback = create_callback(message)
    callback_data = FieldTypeCallback(type="enum")

    await process_field_type(callback, callback_data, state)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_ENUM_VALUES
    assert data["current_field_type"] == callback_data.type


async def test_valid_process_enum_values(state: FSMContext):
    await state.set_state(TrackerCreation.AWAIT_ENUM_VALUES)
    message = create_message("yes/no")

    await process_enum_values(message, state)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert data["current_enum_values"] == "yes/no"


@pytest.mark.parametrize("text", [None, ""])
async def test_empty_message_process_enum_values(state: FSMContext, text):
    await state.set_state(TrackerCreation.AWAIT_ENUM_VALUES)
    message = create_message(text)

    await process_enum_values(message, state)

    assert await state.get_state() == TrackerCreation.AWAIT_ENUM_VALUES
    assert (
        "Сообщение должно включать значения поля enum"
        in message.answer.call_args.kwargs["text"]
    )


async def test_one_option_process_enum_values(state: FSMContext):
    await state.set_state(TrackerCreation.AWAIT_ENUM_VALUES)
    message = create_message("text")

    await process_enum_values(message, state)

    assert await state.get_state() == TrackerCreation.AWAIT_ENUM_VALUES
    assert (
        "Значений enum должно быть более 1, получено 1"
        in message.answer.call_args.kwargs["text"]
    )


@pytest.mark.parametrize(
    "field_type, enum_values",
    [
        ("int", None),
        ("float", None),
        ("string", None),
        ("enum", "yes/no"),
    ],
)
async def test_valid_process_field_name(state: FSMContext, field_type, enum_values):
    message = create_message("name")
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await state.update_data(tracker={"name": "name", "fields": {}})
    await state.update_data(
        current_field_type=field_type, current_enum_values=enum_values
    )

    await process_field_name(message, state)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_NEXT_ACTION
    assert data["current_enum_values"] is None
    assert data["current_field_type"] is None
    assert "name" in data["tracker"]["fields"]


@pytest.mark.parametrize("text", [None, ""])
async def test_empty_message_process_field_name(state: FSMContext, text):
    message = create_message(text)
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await state.update_data(tracker={"name": "name", "fields": {}})

    await process_field_name(message, state)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert (
        "Сообщение должно включать название поля"
        in message.answer.call_args.kwargs["text"]
    )


async def test_add_existing_field_name_simple_types_process_field_name(
    state: FSMContext,
):
    message = create_message("existing")
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await state.update_data(
        tracker={"name": "name", "fields": {"existing": {"type": "int"}}},
        current_field_type="int",
    )

    await process_field_name(message, state)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert "выберете другое имя для поля" in message.answer.call_args.kwargs["text"]


async def test_add_existing_field_name_enum_type_process_field_name(
    state: FSMContext,
):
    message = create_message("existing")
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await state.update_data(
        tracker={"name": "name", "fields": {"existing": {"type": "int"}}},
        current_field_type="enum",
        current_enum_values="yes/no",
    )

    await process_field_name(message, state)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert "со значениями yes/no" in message.answer.call_args.kwargs["text"]


async def test_valid_process_next_action_add_field(
    state: FSMContext, user_service, tracker_service
):
    message = create_message("tracker_name")
    callback = create_callback(message)
    callback_data = ActionCallback(action="add_field")
    await state.update_data(tracker={"name": "name", "fields": {}})

    src_data = await state.get_data()
    await process_next_action(
        callback,
        callback_data,
        state,
        tracker_service=tracker_service,
        user_service=user_service,
    )
    data = await state.get_data()

    assert data["tracker"] == src_data["tracker"]
    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_TYPE


async def test_valid_process_next_action_finish(
    state: FSMContext, mocker: MockerFixture, user_service, tracker_service
):
    message = create_message("tracker_name")
    callback = create_callback(message)
    callback_data = ActionCallback(action="finish")
    await state.update_data(
        tracker={"name": "name", "fields": {"field": {"type": "int"}}}
    )
    uc_mock = MagicMock()
    mocker.patch(
        "src.presentation.routers.create_tracker.CreateTrackerStructureUseCase",
        MagicMock(return_value=uc_mock),
    )
    uc_mock.execute = AsyncMock(
        return_value=TrackerResponse(
            name="name",
            user_id="0",
            user=UserResponse(id="0"),
            id=uuid4(),
            created_at=datetime.datetime.now(),
            structure=TrackerStructureResponse(
                data={"field": {"type": "int"}}, id=uuid4()
            ),
            data=[],
            structure_id=uuid4(),
        )
    )

    await process_next_action(
        callback,
        callback_data,
        state,
        tracker_service=tracker_service,
        user_service=user_service,
    )
    data = await state.get_data()

    uc_mock.execute.assert_awaited_once()
    assert await state.get_state() is None
    assert len(data) == 0


async def test_valid_cancel_creation(state: FSMContext):
    message = create_message("message")
    callback = create_callback(message)

    await cancel_creation(callback, state)
    data = await state.get_data()

    assert len(data) == 0
    assert await state.get_state() is None
