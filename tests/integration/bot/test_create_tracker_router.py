import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiogram.fsm.context import FSMContext
from pytest_mock import MockerFixture

from tests.integration.bot.utils import create_callback, create_message
from tracker.presentation.callbacks import FieldTypeCallback
from tracker.presentation.routers.create_tracker import (
    DataModel,
    DataModelStrict,
    cancel_creation,
    process_enum_values,
    process_field_name,
    process_field_type,
    process_next_action_add_field,
    process_next_action_finish,
    process_tracker_name,
    start_tracker_creation,
)
from tracker.presentation.states import TrackerCreation
from tracker.presentation.utils.keyboard import KeyboardBuilder
from tracker.schemas import (
    TrackerCreate,
    TrackerResponse,
    TrackerStructureCreate,
    TrackerStructureResponse,
    UserResponse,
)

# TODO add translation for strings


async def test_valid_start_tracker_creation(state: FSMContext, t_):
    message = create_message("/add_tracker")
    await state.update_data(temp_data="temp")

    await start_tracker_creation(message, state, t_)

    assert await state.get_state() == TrackerCreation.AWAIT_TRACKER_NAME
    assert len(await state.get_data()) == 0
    message.answer.assert_awaited_once()


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
    message.answer.assert_awaited_once()


@pytest.mark.parametrize(
    "callback_data",
    [
        FieldTypeCallback(type="float"),
        FieldTypeCallback(type="int"),
        FieldTypeCallback(type="string"),
    ],
)
async def test_valid_process_field_type_simple_types(
    state: FSMContext, callback_data, t_
):
    message = create_message("")
    callback = create_callback(message)

    await process_field_type(callback, callback_data, state, t_)
    data = await DataModel.load(state)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert data.cur_field_type == callback_data.type


async def test_valid_process_field_type_enum_type(state: FSMContext, t_):
    message = create_message("")
    callback = create_callback(message)
    callback_data = FieldTypeCallback(type="enum")

    await process_field_type(callback, callback_data, state, t_)
    data = await DataModel.load(state)

    assert await state.get_state() == TrackerCreation.AWAIT_ENUM_VALUES
    assert data.cur_field_type == callback_data.type


async def test_valid_process_enum_values(state: FSMContext, t_):
    await state.set_state(TrackerCreation.AWAIT_ENUM_VALUES)
    message = create_message("yes/no")

    await process_enum_values(message, state, t_)
    data = await DataModel.load(state)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert data.cur_enum_values == ["yes", "no"]


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
        ("int", []),
        ("float", []),
        ("string", []),
        ("enum", ["yes", "no"]),
    ],
)
async def test_valid_process_field_name(
    state: FSMContext, field_type, enum_values, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("name")
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await DataModelStrict(
        tracker=TrackerCreate(
            name="name", user_id="", structure=TrackerStructureCreate(data={})
        ),
        cur_field_type=field_type,
        cur_enum_values=enum_values,
    ).save(state)

    await process_field_name(message, state, t_, kbr_builder)
    data = await DataModel.load(state)

    assert await state.get_state() == TrackerCreation.AWAIT_NEXT_ACTION
    assert data.cur_enum_values is None
    assert data.cur_field_type is None
    assert data.tracker
    assert "name" in data.tracker.structure.data


@pytest.mark.parametrize("text", [None, ""])
async def test_empty_message_process_field_name(
    state: FSMContext, text, t_, kbr_builder: KeyboardBuilder
):
    message = create_message(text)
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await DataModelStrict(
        tracker=TrackerCreate(
            name="name", user_id="", structure=TrackerStructureCreate(data={})
        ),
        cur_field_type="int",
        cur_enum_values=[],
    ).save(state)

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
    await DataModelStrict(
        tracker=TrackerCreate(
            name="name",
            user_id="",
            structure=TrackerStructureCreate(data={"existing": {"type": "int"}}),
        ),
        cur_field_type="int",
        cur_enum_values=[],
    ).save(state)

    await process_field_name(message, state, t_, kbr_builder)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert "выберите другое имя для поля" in message.answer.call_args.kwargs["text"]


async def test_add_existing_field_name_enum_type_process_field_name(
    state: FSMContext, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("existing")
    await state.set_state(TrackerCreation.AWAIT_FIELD_NAME)
    await DataModelStrict(
        tracker=TrackerCreate(
            name="name",
            user_id="",
            structure=TrackerStructureCreate(data={"existing": {"type": "int"}}),
        ),
        cur_field_type="enum",
        cur_enum_values=["yes", "no"],
    ).save(state)

    await process_field_name(message, state, t_, kbr_builder)

    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_NAME
    assert "со значениями yes, no" in message.answer.call_args.kwargs["text"]


async def test_valid_process_next_action_add_field(
    state: FSMContext, t_, kbr_builder: KeyboardBuilder
):
    message = create_message("tracker_name")
    callback = create_callback(message)
    await DataModel(
        tracker=TrackerCreate(
            name="name",
            user_id="",
            structure=TrackerStructureCreate(data={}),
        ),
        cur_field_type=None,
        cur_enum_values=None,
    ).save(state)

    src_data = await DataModel.load(state)
    await process_next_action_add_field(callback, state, t_, kbr_builder)
    data = await DataModel.load(state)

    assert data.tracker == src_data.tracker
    assert await state.get_state() == TrackerCreation.AWAIT_FIELD_TYPE


async def test_valid_process_next_action_finish(
    state: FSMContext, mocker: MockerFixture, user_service, tracker_service, t_
):
    message = create_message("tracker_name")
    callback = create_callback(message)
    await DataModel(
        tracker=TrackerCreate(
            name="name",
            user_id="",
            structure=TrackerStructureCreate(data={"field": {"type": "int"}}),
        ),
        cur_field_type=None,
        cur_enum_values=None,
    ).save(state)
    uc_mock = MagicMock()
    mocker.patch(
        "tracker.presentation.routers.create_tracker.FinishTrackerCreation",
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
