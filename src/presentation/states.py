from aiogram.fsm.state import State, StatesGroup


class TrackerCreation(StatesGroup):
    AWAIT_TRACKER_NAME = State()
    AWAIT_FIELD_TYPE = State()
    AWAIT_FIELD_NAME = State()
    AWAIT_ENUM_VALUES = State()
    AWAIT_NEXT_ACTION = State()


class TrackerControlState(StatesGroup):
    AWAIT_TRACKER_ACTION = State()


class AddingData(StatesGroup):
    AWAIT_FIELD_VALUE = State()
    AWAIT_NEXT_ACTION = State()


class DataState(StatesGroup):
    AWAIT_ACTION = State()
    AWAIT_PERIOD_TYPE = State()
    AWAIT_PERIOD_VALUE = State()
    AWAIT_FIELDS_SELECTION = State()
