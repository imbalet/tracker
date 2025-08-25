from enum import StrEnum, auto
from uuid import UUID

from src.core.dynamic_json import DynamicJson
from src.core.dynamic_json.types import FieldDataType
from src.schemas import TrackerResponse
from src.schemas.tracker import TrackerDataCreate
from src.services.database import TrackerService

__all__ = [
    "ShowTrackersUseCase",
    "DescribeTrackerUseCase",
    "StartTrackingUseCase",
    "GetFieldType",
    "HandleFieldValueUseCase",
]


class ShowTrackersUseCase:
    class Error(StrEnum):
        NO_TRACKERS = auto()

    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(self, user_id: str) -> tuple[list[TrackerResponse], Error | None]:
        trackers = await self.tracker_service.get_by_user_id(user_id=user_id)
        if not trackers:
            return [], self.Error.NO_TRACKERS
        return trackers, None


class DescribeTrackerUseCase:
    class Error(StrEnum):
        NO_TRACKER = auto()

    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(
        self, tracker_id: UUID
    ) -> tuple[TrackerResponse | None, Error | None]:
        tracker = await self.tracker_service.get_by_id(tracker_id=tracker_id)
        if not tracker:
            return None, self.Error.NO_TRACKER
        return tracker, None


class StartTrackingUseCase:
    class Error(StrEnum):
        NO_TEXT = auto()
        NO_TRACKER = auto()

    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(
        self, text: str | None
    ) -> tuple[TrackerResponse | None, str, Error | None]:
        if not text or not (text := text.strip()):
            return None, "", self.Error.NO_TEXT
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return None, "", self.Error.NO_TEXT
        tracker_name = parts[1].strip()
        tracker = await self.tracker_service.get_by_name(tracker_name)
        if not tracker:
            return None, tracker_name, self.Error.NO_TRACKER
        return tracker, tracker_name, None


class GetFieldType:
    class Error(StrEnum):
        NO_FIELD = auto()

    def execute(
        self, tracker: TrackerResponse, field_name: str
    ) -> tuple[FieldDataType | None, Error | None]:
        if field_name not in tracker.structure.data:
            return None, self.Error.NO_FIELD
        field_type = tracker.structure.data[field_name]["type"]
        return field_type, None


class HandleFieldValueUseCase:
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
