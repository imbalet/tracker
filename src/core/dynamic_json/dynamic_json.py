from enum import Enum
from typing import Any

from pydantic import BaseModel, create_model

from .exceptions import AttributeException, DataException
from .types import FieldType


class DynamicJson:
    def __init__(self, fields: FieldType, structure: type[BaseModel]) -> None:
        self.model: BaseModel | None = None
        self.data: list[BaseModel] | None = None
        self.raw_fields = fields
        self.structure = structure

    @classmethod
    def from_fields(cls: type["DynamicJson"], fields: FieldType) -> "DynamicJson":
        structure = cls.create_dynamic_model(fields=fields)
        return cls(fields=fields, structure=structure)

    @staticmethod
    def create_dynamic_model(fields: FieldType) -> type[BaseModel]:
        field_types: dict[str, Any] = {}
        for field_name, field_props in fields.items():

            if field_props["type"] == "int":
                field_types[field_name] = (int, ...)
            elif field_props["type"] == "float":
                field_types[field_name] = (float, ...)
            elif field_props["type"] == "enum":
                options = field_props["values"].split("/")  # type: ignore
                enum_name = f"{field_name}_Enum"
                enum_class = Enum(enum_name, {opt: opt for opt in options})  # type: ignore
                field_types[field_name] = (enum_class, ...)
            elif field_props["type"] == "string":
                field_types[field_name] = (str, ...)
            else:
                raise DataException(f"Unsupported type: {field_props['type']}")
        structure = create_model("dynamic_model", **field_types)
        return structure

    def validate(self, data: dict[str, str]):
        return self.structure.model_validate(data)

    def fill_one(self, data: dict[str, str]):
        model = self.structure.model_validate(data)
        self.model = model

    def fill_list(self, data: list[dict[str, str]]):
        self.data = [self.structure.model_validate(i) for i in data]

    def dump_structure(self):
        return self.raw_fields

    def dump_data(self):
        if not self.model:
            raise AttributeException(f"{self.__class__.__name__}.model is None")
        return self.model.model_dump(mode="json")

    def dump_all(self):
        if not self.model:
            raise AttributeException(f"{self.__class__.__name__}.model is None")
        return {
            "structure": self.raw_fields,
            "data": self.model.model_dump(mode="json"),
        }
