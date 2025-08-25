from enum import Enum
from typing import Any

from pydantic import BaseModel, ValidationError, create_model

from .exceptions import AttributeException, TypeException, ValidationException
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
            elif (
                field_props["type"] == "enum"
                and "values" in field_props
                and field_props["values"]
            ):
                options = field_props["values"]
                enum_name = f"{field_name}_Enum"
                enum_class = Enum(enum_name, {opt: opt for opt in options})
                field_types[field_name] = (enum_class, ...)
            elif field_props["type"] == "string":
                field_types[field_name] = (str, ...)
            else:
                raise TypeException(f"Unsupported type: {field_props['type']}")
        structure = create_model("dynamic_model", **field_types)
        return structure

    def validate(self, data: dict[str, str]):
        try:
            return self.structure.model_validate(data)
        except ValidationError as e:
            raise ValidationException("Error on data validation: ", e.errors()) from e

    def validate_one_field(self, field_name: str, field_value: str):
        if field_name not in self.structure.model_fields:
            raise AttributeException(
                f"Field '{field_name}' not found in model structure"
            )

        field_info = self.structure.model_fields[field_name]
        TempModel = create_model(
            "TempModel", **{field_name: (field_info.annotation, field_info)}  # type: ignore
        )
        try:
            TempModel(**{field_name: field_value})
        except ValidationError as e:
            raise ValidationException(
                f"Validation error for field '{field_name}' with value '{field_value}'",
                e.errors(),
            ) from e

    def fill_one(self, data: dict[str, str]):
        try:
            model = self.structure.model_validate(data)
            self.model = model
        except ValidationError as e:
            raise ValidationException("Error on data validation: ", e.errors()) from e

    def fill_list(self, data: list[dict[str, str]]):
        try:
            self.data = [self.structure.model_validate(i) for i in data]
        except ValidationError as e:
            raise ValidationException("Error on data validation: ", e.errors()) from e

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
