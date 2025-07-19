from aiogram.fsm.state import State, StatesGroup


class TrackerCreation(StatesGroup):
    AWAIT_TRACKER_NAME = State()
    AWAIT_FIELD_TYPE = State()
    AWAIT_FIELD_NAME = State()
    AWAIT_ENUM_VALUES = State()
    AWAIT_NEXT_ACTION = State()
