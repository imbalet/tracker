from src.core.dynamic_json import DynamicJson
from src.schemas import TrackerCreate, TrackerResponse, TrackerStructureCreate
from src.services.database import TrackerService


class CreateTrackerStructureUseCase:
    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(
        self, tracker: TrackerCreate, structure: TrackerStructureCreate
    ) -> TrackerResponse:
        self.structure = structure
        self.dj = DynamicJson.from_fields(fields=structure.data)
        res = await self.tracker_service.create(tracker=tracker, structure=structure)
        return res
