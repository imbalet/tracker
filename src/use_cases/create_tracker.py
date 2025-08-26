from enum import StrEnum, auto

from src.core.dynamic_json import DynamicJson
from src.core.dynamic_json.types import FieldDataType
from src.schemas import (
    TrackerCreate,
    TrackerResponse,
    TrackerStructureCreate,
)
from src.services.database import TrackerService, UserService

__all__ = [
    "CreateTrackerDraftUseCase",
    "ProcessEnumValuesUseCase",
    "ProcessFieldNameUseCase",
    "FinishTrackerCreation",
]


class CreateTrackerDraftUseCase:
    """Creates DTO for tracker creation."""

    class Error(StrEnum):
        NO_TEXT = auto()

    def execute(self, name: str | None) -> tuple[TrackerCreate | None, Error | None]:
        """Creates DTO for tracker creation.

        Args:
            name (str): The name of tracker.

        Returns:
            tuple[TrackerCreate | None, Error | None]:\
                DTO with tracker name and tracker data structure initialized as empty (or None if an error occurred)\
                and an error code (or None if successful).
        """
        if not name or not (name := name.strip()):
            return None, self.Error.NO_TEXT
        return (
            TrackerCreate(
                name=name, user_id="", structure=TrackerStructureCreate(data={})
            ),
            None,
        )


class ProcessEnumValuesUseCase:
    """Validates the provided enum values for a field."""

    class Error(StrEnum):
        NO_TEXT = auto()
        WRONG_COUNT = auto()

    def execute(self, text: str | None) -> tuple[list[str], Error | None]:
        """Validates the provided enum values for a field.

        Args:
            text (str | None): The text entered by the user

        Returns:
            tuple[list[str], Error | None]:\
                A list with enum values (or empty if an error occurred)\
                and an error code (or None if successful).
        """
        if not text or not (text := text.strip()):
            return ([], self.Error.NO_TEXT)

        items = map(str.strip, text.split("/"))
        options = list(filter(lambda x: x, dict.fromkeys(items)))
        if len(options) < 2:
            return (list(options), self.Error.WRONG_COUNT)
        return (list(options), None)


class ProcessFieldNameUseCase:
    """Validates the provided field name and updates the tracker structure."""

    class Error(StrEnum):
        NO_TEXT = auto()
        ALREADY_EXISTS = auto()
        WRONG_STRUCTURE = auto()

    def execute(
        self,
        tracker: TrackerCreate,
        field_name: str | None,
        field_type: FieldDataType,
        enum_values: list[str] | None = None,
    ) -> tuple[TrackerCreate | None, Error | None]:
        """Validates the provided field name and updates the tracker structure.

        Args:
            field_name (str | None): The name of the field.
            field_type (FieldDataType): The type of the field.
            enum_values (list[str] | None): The enum values for the field, used only if the field type is 'enum'.
            tracker (TrackerCreate): The tracker DTO to be updated.

        Returns:
            tuple[TrackerCreate | None, Error | None]:\
                A tuple containing the updated tracker DTO (or None if an error occurred)\
                and an error code (or None if successful).
        """
        enum_values = enum_values or []
        if not field_name or not (field_name := field_name.strip()):
            return (None, self.Error.NO_TEXT)
        if field_name in tracker.structure.data:
            return (None, self.Error.ALREADY_EXISTS)
        if (field_type == "enum" and not enum_values) or (
            field_type != "enum" and enum_values
        ):
            return (None, self.Error.WRONG_STRUCTURE)

        tracker.structure.data[field_name] = {"type": field_type}
        if field_type == "enum" and enum_values:
            tracker.structure.data[field_name]["values"] = enum_values

        return (tracker, None)


class FinishTrackerCreation:
    class Error(StrEnum):
        AT_LEAST_ONE_FIELD_REQUIRED = auto()

    def __init__(
        self, tracker_service: TrackerService, user_service: UserService
    ) -> None:
        self.tracker_service = tracker_service
        self.user_service = user_service

    async def execute(
        self, tracker: TrackerCreate, user_id: str
    ) -> tuple[TrackerResponse | None, Error | None]:
        """Validates the tracker structure and creates the tracker.

        Args:
            tracker (TrackerCreate): The tracker DTO.
            user_id (str): The ID of the user creating the tracker.

        Returns:
            tuple[TrackerResponse | None, Error | None]:\
                The created tracker DTO (or None if an error occurred)\
                and an error code (or None if successful).
        """
        if len(tracker.structure.data) == 0:
            return None, self.Error.AT_LEAST_ONE_FIELD_REQUIRED

        user = await self.user_service.get(user_id)
        if user is None:
            user = await self.user_service.create(user_id)

        DynamicJson.from_fields(fields=tracker.structure.data)
        created_tracker = await self.tracker_service.create(tracker=tracker)
        return created_tracker, None
