from typing import Literal
from uuid import UUID

from aiogram.filters.callback_data import CallbackData

from src.core.dynamic_json.types import FieldDataType


class FieldTypeCallback(CallbackData, prefix="field"):
    type: FieldDataType


class ActionCallback(CallbackData, prefix="action"):
    action: Literal["add_field", "finish", "cancel"]


class TrackerCallback(CallbackData, prefix="tracker"):
    id: UUID


class BackCallback(CallbackData, prefix="back"):
    pass


class CancelCallback(CallbackData, prefix="cancel"):
    pass


class ConfirmCallback(CallbackData, prefix="confirm"):
    pass


class FieldCallback(CallbackData, prefix="field"):
    name: str
    type: FieldDataType


class TrackerActionsCallback(CallbackData, prefix="tracker_action"):
    action: Literal["get_options"]


class TrackerDataActionsCallback(CallbackData, prefix="tracker_data_action"):
    action: Literal["csv", "graph", "table", "statistics"]


class PeriodCallback(CallbackData, prefix="period"):
    period: Literal["years", "months", "weeks", "days", "hours", "minutes"]


class EnumValuesCallback(CallbackData, prefix="enum"):
    value: str
