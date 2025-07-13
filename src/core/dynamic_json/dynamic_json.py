from enum import Enum
from typing import Any

from pydantic import create_model, BaseModel

from .exceptions import AttributeException, DataException


class DynamicData(BaseModel):
    structure: type[BaseModel]
    data: list[BaseModel]


class DynamicJson:
    def __init__(
        self, name: str, fields: dict[str, str], structure: type[BaseModel]
    ) -> None:
        self.model: BaseModel | None = None
        self.raw_fields = fields
        self.name = name
        self.structure = structure

    @classmethod
    def from_fields(
        cls: type["DynamicJson"], name: str, fields: dict[str, str]
    ) -> "DynamicJson":
        structure = cls.create_dynamic_model(name=name, fields=fields)
        return cls(name=name, fields=fields, structure=structure)

    @staticmethod
    def create_dynamic_model(name: str, fields: dict[str, str]) -> type[BaseModel]:
        field_types: dict[str, Any] = {}
        for field_name, field_type in fields.items():

            if field_type == "int":
                field_types[field_name] = (int, ...)
            elif field_type == "float":
                field_types[field_name] = (float, ...)
            elif "/" in field_type:
                options = field_type.split("/")
                enum_name = f"{name}_{field_name}_Enum"
                enum_class = Enum(enum_name, {opt: opt for opt in options})  # type: ignore
                field_types[field_name] = (enum_class, ...)
            elif field_type == "string":
                field_types[field_name] = (str, ...)
            else:
                raise DataException(f"Unsupported type: {field_type}")
        structure = create_model(name, **field_types)
        return structure

    def fill(self, data: dict[str, str]):
        model = self.structure.model_validate(data)
        self.model = model

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
            "name": self.name,
            "structure": self.raw_fields,
            "data": self.model.model_dump(mode="json"),
        }
