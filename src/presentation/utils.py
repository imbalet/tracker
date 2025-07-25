from typing import TypedDict

from aiogram import html
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.dynamic_json.types import FieldDefinition
from src.presentation.callbacks import (
    ActionCallback,
    CancelCallback,
    FieldCallback,
    FieldTypeCallback,
    TrackerCallback,
)
from src.schemas import TrackerResponse


class TrackerDefinition(TypedDict):
    name: str
    fields: dict[str, FieldDefinition]


def _get_tracker_text(
    tracker: TrackerDefinition, data: dict[str, str], additional_str: str = ""
):
    name = tracker["name"]
    fields = tracker["fields"]

    text = (
        f"{additional_str}\n" if additional_str else ""
    ) + f"{html.bold(name)}\n\n" "Поля:\n"

    if not fields:
        text += "  -> Пока нет полей\n"
    else:
        for i, (field_name, field) in enumerate(fields.items(), 1):
            text += (
                f"  {i}. {field['type']}"
                + f" {field['values'] if field['type'] == 'enum' else ''}"  # type: ignore
                + f" -> {html.italic(field_name)}"
                + (f" -> {data.get(field_name, 'Не заполнено')}\n" if data else "\n")
            )
    return text


def get_tracker_description(tracker: TrackerDefinition, add_string: str = "") -> str:
    return _get_tracker_text(tracker=tracker, data={}, additional_str=add_string)


def get_tracker_data_description(
    tracker: TrackerDefinition, data: dict[str, str], add_string: str = ""
) -> str:
    return _get_tracker_text(tracker=tracker, data=data, additional_str=add_string)


def get_tracker_description_from_dto(
    data: TrackerResponse, add_string: str = ""
) -> str:
    return get_tracker_description(
        {"name": data.name, "fields": data.structure.data}, add_string=add_string
    )


def get_tracker_data_description_from_dto(
    dto: TrackerResponse, data: dict, add_string: str = ""
) -> str:
    return get_tracker_data_description(
        {"name": dto.name, "fields": dto.structure.data},
        add_string=add_string,
        data=data,
    )


def build_field_type_keyboard():
    builder = InlineKeyboardBuilder()
    for t in ["int", "float", "enum", "string"]:
        builder.button(text=t.upper(), callback_data=FieldTypeCallback(type=t))  # type: ignore
    builder.button(text="Отменить", callback_data=ActionCallback(action="cancel"))
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def build_action_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Добавить поле", callback_data=ActionCallback(action="add_field")
    )
    builder.button(text="Завершить", callback_data=ActionCallback(action="finish"))
    builder.button(text="Отменить", callback_data=ActionCallback(action="cancel"))
    builder.adjust(2, 1)
    return builder.as_markup()


def build_trackers_keyboard(data: list[TrackerResponse]):
    builder = InlineKeyboardBuilder()
    for i in data:
        builder.button(text=i.name, callback_data=TrackerCallback(id=i.id))
    builder.adjust(3)
    return builder.as_markup()


def build_tracker_fields_keyboard(
    tracker: TrackerResponse, exclude_fields: set[str] | None = None
):
    builder = InlineKeyboardBuilder()
    for name, props in tracker.structure.data.items():
        if exclude_fields and name in exclude_fields:
            continue
        builder.button(
            text=f"{name}: {props['type'] if props['type'] != 'enum' else props['values']}",  # type: ignore
            callback_data=FieldCallback(name=name, tracker_id=tracker.id),
        )
    builder.button(text="Отменить", callback_data=CancelCallback(tracker_id=tracker.id))
    builder.adjust(1)
    return builder.as_markup()
