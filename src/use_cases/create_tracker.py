from enum import StrEnum, auto

from src.core.dynamic_json import DynamicJson
from src.schemas import TrackerCreate, TrackerResponse, TrackerStructureCreate
from src.services.database import TrackerService, UserService

__all__ = [
    "CreateTrackerDraftUseCase",
    "ProcessEnumValuesUseCase",
    "ProcessFieldNameUseCase",
    "FinishTrackerCreation",
]


class CreateTrackerDraftUseCase:
    class Error(StrEnum):
        NO_TEXT = auto()

    def execute(self, name: str) -> tuple[dict, Error | None]:
        name = name.strip()
        if not name:
            return {}, self.Error.NO_TEXT
        return {"name": name, "fields": {}}, None


class ProcessEnumValuesUseCase:
    class Error(StrEnum):
        NO_TEXT = auto()
        WRONG_COUNT = auto()

    def execute(self, text: str | None) -> tuple[list[str], Error | None]:
        if not text or not text.strip():
            return ([], self.Error.NO_TEXT)
        text = text.strip()
        options = list(map(str.strip, text.split("/")))
        if len(options) < 2:
            return (options, self.Error.WRONG_COUNT)
        return (options, None)


class ProcessFieldNameUseCase:
    class Error(StrEnum):
        NO_TEXT = auto()
        ALREADY_EXISTS = auto()

    def execute(
        self,
        field_name: str | None,
        field_type: str,
        enum_values: str | None,
        tracker: dict,
    ) -> tuple[dict, Error | None]:
        if not field_name or not field_name.strip():
            return ({}, self.Error.NO_TEXT)
        field_name = field_name.strip()
        if field_name in tracker["fields"]:
            return ({}, self.Error.ALREADY_EXISTS)

        field_data = {"type": field_type}
        if field_type == "enum" and enum_values:
            field_data["values"] = enum_values
        tracker["fields"][field_name] = field_data

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
        self, tracker: dict, user_id: str
    ) -> tuple[TrackerResponse | None, Error | None]:
        if len(tracker["fields"]) == 0:
            return None, self.Error.AT_LEAST_ONE_FIELD_REQUIRED

        user = await self.user_service.get(user_id)
        if user is None:
            user = await self.user_service.create(user_id)

        structure = TrackerStructureCreate(data=tracker["fields"])

        self.dj = DynamicJson.from_fields(fields=structure.data)
        created_tracker = await self.tracker_service.create(
            tracker=TrackerCreate(name=tracker["name"], user_id=user_id),
            structure=structure,
        )
        return created_tracker, None
