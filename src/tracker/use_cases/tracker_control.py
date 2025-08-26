from enum import StrEnum, auto

from tracker.core.dynamic_json import DynamicJson
from tracker.schemas import TrackerResponse
from tracker.schemas.tracker import TrackerDataCreate
from tracker.services.database import TrackerService

__all__ = [
    "GetUserTrackersUseCase",
    "ValidateTrackingMessageUseCase",
    "HandleFieldValueUseCase",
]


class GetUserTrackersUseCase:
    """Return the list of trackers."""

    class Error(StrEnum):
        NO_TRACKERS = auto()

    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(self, user_id: str) -> tuple[list[TrackerResponse], Error | None]:
        """Return the list of trackers.

        Args:
            user_id (str): User ID.

        Returns:
            tuple[list[TrackerResponse], Error | None]:\
                The list of user's trackers (empty if an error occurred)\
                and an error code (or None if successful).
        """
        trackers = await self.tracker_service.get_by_user_id(user_id=user_id)
        if not trackers:
            return [], self.Error.NO_TRACKERS
        return trackers, None


class ValidateTrackingMessageUseCase:
    """Validates the user message for starting tracking."""

    class Error(StrEnum):
        NO_TEXT = auto()

    def execute(self, text: str | None) -> tuple[str, Error | None]:
        """Validates the user message for starting tracking.

        Args:
            text (str | None): The user's input.

        Returns:
            tuple[str, Error | None]:\
                The name of the entered tracker (empty if an error occurred)\
                and an error code (or None if successful).
        """
        if not text or not (text := text.strip()):
            return "", self.Error.NO_TEXT
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "", self.Error.NO_TEXT
        tracker_name = parts[1].strip()
        return tracker_name, None


class HandleFieldValueUseCase:
    """Validates provided field value, validates and saves the whole tracker if all fields are filled."""

    class Error(StrEnum):
        NO_TEXT = auto()

    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(
        self,
        tracker: TrackerResponse,
        field_name: str,
        field_value: str | None,
        field_values: dict,
    ) -> tuple[bool, Error | None]:
        """Validates provided field value, validates and saves the whole tracker if all fields are filled.

        Args:
            tracker (TrackerResponse): The tracker DTO.
            field_name (str): The name of the field.
            field_value (str | None): The value of the field.
            field_values (dict): Dict with filled fields.

        Returns:
            tuple[bool, Error | None]:\
                True if the tracker has been saved, False if not all fields are filled in, or on error\
                and an error code (or None if successful).
        """
        # TODO: divide validation and saving
        if not field_value or not (field_value := field_value.strip()):
            return False, self.Error.NO_TEXT
        dj = DynamicJson.from_fields(fields=tracker.structure.data)
        dj.validate_one_field(field_name=field_name, field_value=field_value)
        if len(field_values) == len(tracker.structure.data):
            dj.validate(field_values)
            await self.tracker_service.add_data(
                TrackerDataCreate(tracker_id=tracker.id, data=field_values)
            )
            return True, None
        return False, None
