from typing import TypedDict

from aiogram import html

from src.core.dynamic_json.types import FieldDefinition
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
