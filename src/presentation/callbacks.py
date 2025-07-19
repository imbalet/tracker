from typing import Literal

from aiogram.filters.callback_data import CallbackData


class FieldTypeCallback(CallbackData, prefix="field_type"):
    type: Literal["int", "float", "enum", "string"]


class ActionCallback(CallbackData, prefix="action"):
    action: Literal["add_field", "finish", "cancel"]
