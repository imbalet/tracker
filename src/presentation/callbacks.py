from typing import Literal
from uuid import UUID

from aiogram.filters.callback_data import CallbackData


class FieldTypeCallback(CallbackData, prefix="field_type"):
    type: Literal["int", "float", "enum", "string"]


class ActionCallback(CallbackData, prefix="action"):
    action: Literal["add_field", "finish", "cancel"]


class TrackerCallback(CallbackData, prefix="tracker_"):
    id: UUID


class CancelCallback(CallbackData, prefix="cancel"):
    tracker_id: UUID


class ConfirmCallback(CallbackData, prefix="confirm"):
    tracker_id: UUID


class FieldCallback(CallbackData, prefix="field"):
    name: str
    tracker_id: UUID


class TrackerActionsCallback(CallbackData, prefix="tracker_action"):
    action: Literal["back", "get_options"]


class TrackerDataActionsCallback(CallbackData, prefix="tracker_data_action"):
    action: Literal["back", "csv", "graph", "table", "statistics"]


class PeriodCallback(CallbackData, prefix="period"):
    period: Literal["back", "years", "months", "weeks", "days", "hours", "minutes"]
