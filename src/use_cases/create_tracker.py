from src.core.dynamic_json import DynamicJson
from src.schemas import TrackerCreate, TrackerResponse, TrackerStructureCreate
from src.services.database import TrackerService, UserService


class CreateTrackerStructureUseCase:
    def __init__(
        self, tracker_service: TrackerService, user_service: UserService
    ) -> None:
        self.tracker_service = tracker_service
        self.user_service = user_service

    async def execute(
        self, user_id: str, tracker_name: str, structure: TrackerStructureCreate
    ) -> TrackerResponse:
        user = await self.user_service.get(user_id)
        if user is None:
            user = await self.user_service.create(user_id)

        self.dj = DynamicJson.from_fields(fields=structure.data)
        res = await self.tracker_service.create(
            tracker=TrackerCreate(name=tracker_name, user_id=user_id),
            structure=structure,
        )
        return res
