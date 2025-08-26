from typing import Literal, NotRequired, TypedDict

# properties of fields in json structure
props = Literal["type", "values"]

"""
Example:
{
    "field_name": {
        "type": str,
        "values": str | None, # only for enum type
    }
}
"""

FieldDataType = Literal["int", "float", "string", "enum"]
field_types_list: list[FieldDataType] = ["int", "float", "string", "enum"]


# TODO rewrite to dataclass
class FieldDefinition(TypedDict):
    type: FieldDataType
    values: NotRequired[list[str] | None]  # only for enum type


FieldType = dict[str, FieldDefinition]
