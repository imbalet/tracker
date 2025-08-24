import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiogram.fsm.context import FSMContext
from pytest_mock import MockerFixture

from src.presentation.callbacks import FieldTypeCallback
from src.presentation.constants import (
    ST_CR_CUR_FIELD_TYPE,
    ST_CR_TRACKER,
)
from src.presentation.routers.create_tracker import (
    cancel_creation,
    process_enum_values,
    process_field_name,
    process_field_type,
    process_next_action_add_field,
    process_next_action_finish,
    process_tracker_name,
    start_tracker_creation,
)
from src.presentation.states import TrackerCreation
from src.presentation.utils.keyboard import KeyboardBuilder
from src.schemas import TrackerResponse, TrackerStructureResponse, UserResponse
from tests.integration.bot.utils import create_callback, create_message

# TODO add translation for strings


async def test_valid_start_tracker_creation(
    state: FSMContext, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("/add_tracker")
    await state.update_data(temp_data="temp")

    await start_tracker_creation(message, state, t_)

    assert await state.get_state() == TrackerCreation.AWAIT_TRACKER_NAME
    assert len(await state.get_data()) == 0
    message.answer.assert_awaited_with("Введите название трекера:")


async def test_valid_process_tracker_name(
    state: FSMContext, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("tracker_name")
    await state.set_state(TrackerCreation.AWAIT_TRACKER_NAME)

    await process_tracker_name(message, state, t_, kbr_builder)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_TYPE
    assert len(data) > 0

    assert "tracker" in data and data["tracker"]["name"] == "tracker_name"
    assert "reply_markup" in message.answer.call_args.kwargs


@pytest.mark.parametrize("text", [None, ""])
async def test_empty_name_process_tracker_name(
    state: FSMContext, text, t_, kbr_builder: KeyboardBuilder
):
    message = create_message(text)
    await state.set_state(TrackerCreation.AWAIT_TRACKER_NAME)

    await process_tracker_name(message, state, t_, kbr_builder)
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
async def test_valid_process_field_type_simple_types(
    state: FSMContext, callback_data, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("")
    callback = create_callback(message)

    await process_field_type(callback, callback_data, state, t_)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert data["current_field_type"] == callback_data.type


async def test_valid_process_field_type_enum_type(
    state: FSMContext, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("")
    callback = create_callback(message)
    callback_data = FieldTypeCallback(type="enum")

    await process_field_type(callback, callback_data, state, t_)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_ENUM_VALUES
    assert data["current_field_type"] == callback_data.type


async def test_valid_process_enum_values(
    state: FSMContext, t_, kbr_builder: KeyboardBuilder
):
    await state.set_state(TrackerCreation.AWAIT_ENUM_VALUES)
    message = create_message("yes/no")

    await process_enum_values(message, state, t_)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert data["current_enum_values"] == "yes/no"


@pytest.mark.parametrize("text", [None, ""])
async def test_empty_message_process_enum_values(state: FSMContext, text, t_):
    await state.set_state(TrackerCreation.AWAIT_ENUM_VALUES)
    message = create_message(text)

    await process_enum_values(message, state, t_)

    assert await state.get_state() == TrackerCreation.AWAIT_ENUM_VALUES
    assert (
        "Сообщение должно включать значения поля enum"
        in message.answer.call_args.kwargs["text"]
    )


async def test_one_option_process_enum_values(state: FSMContext, t_):
    await state.set_state(TrackerCreation.AWAIT_ENUM_VALUES)
    message = create_message("text")

    await process_enum_values(message, state, t_)

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
async def test_valid_process_field_name(
    state: FSMContext, field_type, enum_values, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("name")
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await state.update_data(tracker={"name": "name", "fields": {}})
    await state.update_data(
        current_field_type=field_type, current_enum_values=enum_values
    )

    await process_field_name(message, state, t_, kbr_builder)
    data = await state.get_data()

    assert await state.get_state() == TrackerCreation.AWAIT_NEXT_ACTION
    assert data["current_enum_values"] is None
    assert data["current_field_type"] is None
    assert "name" in data["tracker"]["fields"]


@pytest.mark.parametrize("text", [None, ""])
async def test_empty_message_process_field_name(
    state: FSMContext, text, t_, kbr_builder: KeyboardBuilder
):
    message = create_message(text)
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await state.update_data(
        data={
            ST_CR_TRACKER: {"name": "name", "fields": {}},
            ST_CR_CUR_FIELD_TYPE: "int",
        }
    )

    await process_field_name(message, state, t_, kbr_builder)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert (
        "Сообщение должно включать название поля"
        in message.answer.call_args.kwargs["text"]
    )


async def test_add_existing_field_name_simple_types_process_field_name(
    state: FSMContext, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("existing")
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await state.update_data(
        tracker={"name": "name", "fields": {"existing": {"type": "int"}}},
        current_field_type="int",
    )

    await process_field_name(message, state, t_, kbr_builder)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert "выберите другое имя для поля" in message.answer.call_args.kwargs["text"]


async def test_add_existing_field_name_enum_type_process_field_name(
    state: FSMContext, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("existing")
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await state.update_data(
        tracker={"name": "name", "fields": {"existing": {"type": "int"}}},
        current_field_type="enum",
        current_enum_values="yes/no",
    )

    await process_field_name(message, state, t_, kbr_builder)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert "со значениями yes/no" in message.answer.call_args.kwargs["text"]


async def test_valid_process_next_action_add_field(
    state: FSMContext, user_service, tracker_service, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("tracker_name")
    callback = create_callback(message)
    await state.update_data(tracker={"name": "name", "fields": {}})

    src_data = await state.get_data()
    await process_next_action_add_field(callback, state, t_, kbr_builder)
    data = await state.get_data()

    assert data["tracker"] == src_data["tracker"]
    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_TYPE


async def test_valid_process_next_action_finish(
    state: FSMContext,
    mocker: MockerFixture,
    user_service,
    tracker_service,
    t_,
    kbr_builder: KeyboardBuilder,
):
    message = create_message("tracker_name")
    callback = create_callback(message)
    await state.update_data(
        tracker={"name": "name", "fields": {"field": {"type": "int"}}}
    )
    uc_mock = MagicMock()
    mocker.patch(
        "src.presentation.routers.create_tracker.FinishTrackerCreation",
        MagicMock(return_value=uc_mock),
    )
    uc_mock.execute = AsyncMock(
        return_value=(
            TrackerResponse(
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
            ),
            None,
        )
    )

    await process_next_action_finish(
        callback,
        state,
        tracker_service=tracker_service,
        user_service=user_service,
        t=t_,
    )
    data = await state.get_data()

    uc_mock.execute.assert_awaited_once()
    assert await state.get_state() is None
    assert len(data) == 0


async def test_valid_cancel_creation(state: FSMContext, t_):
    message = create_message("message")
    callback = create_callback(message)

    await cancel_creation(callback, state, t_)
    data = await state.get_data()

    assert len(data) == 0
    assert await state.get_state() is None
