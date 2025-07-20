from aiogram import html
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.presentation.callbacks import ActionCallback, FieldTypeCallback
from src.schemas import TrackerResponse


def get_tracker_description(data: dict) -> str:
    name = data.get("name", "Без названия")
    fields = data.get("fields", {})

    text = f"Создание трекера: {html.bold(name)}\n\n"
    text += "Поля:\n"

    if not fields:
        text += "  -> Пока нет полей\n"
    else:
        for i, (field_name, field) in enumerate(fields.items(), 1):
            text += (
                f"  {i}. {field['type']}"
                f" {field['values'] if field["type"] == "enum" else ""}"
                f" -> {html.italic(field_name)}\n"
            )

    return text


def get_tracker_description_from_dto(data: TrackerResponse) -> str:
    return get_tracker_description({"name": data.name, "fields": data.structure.data})


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
