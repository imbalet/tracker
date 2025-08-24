import csv
from datetime import datetime
from enum import StrEnum, auto
from io import BytesIO, TextIOWrapper
from typing import Literal
from uuid import UUID

from src.presentation.utils import convert_date
from src.schemas import TrackerResponse
from src.schemas.result import StaticticsTrackerData
from src.services.database import DataService, TrackerService

__all__ = [
    "GetCSVUseCase",
    "GetStatisticsUseCase",
    "HandlePeriodValueUseCase",
    "HandleActionUseCase",
    "HandleFieldUseCase",
    "HandleFieldsConfirmUseCase",
]


class GetCSVUseCase:
    def __init__(self, data_service: DataService) -> None:
        self.data_service = data_service

    async def execute(
        self,
        tracker_id: UUID,
        from_date: datetime | None = None,
        exclude_fields: list[str] | None = None,
    ) -> BytesIO | None:
        """Returns a BytesIO object containing a CSV file.

        Args:
            tracker_id (UUID): ID of the tracker.
            from_date (datetime | None): Start date for data selection. If None, no start data filter is applied.
            exclude_fields (list[str] | None): List of data fields to exclude. \
                If None or empty, all available fields are included.

        Returns:
            BytesIO: BytesIO object containing a CSV file.
        """
        res = await self.data_service.get_all_data(
            tracker_id=tracker_id,
            from_date=from_date,
            exclude_fields=exclude_fields,
        )
        if len(res) == 0:
            return None

        csv_buffer = BytesIO()
        text_buffer = TextIOWrapper(csv_buffer, encoding="utf-8", newline="")
        writer = csv.writer(text_buffer)
        writer.writerow(["date", *res[0].value.keys()])
        for i in res:
            row = [i.date, *i.value.values()]
            writer.writerow(row)
        text_buffer.flush()
        csv_buffer.seek(0)
        text_buffer.detach()
        return csv_buffer


class GetStatisticsUseCase:
    def __init__(self, data_service: DataService) -> None:
        self.data_service = data_service

    async def execute(
        self,
        tracker_id: UUID,
        numeric_fields: list[str],
        categorial_fields: list[str],
        from_date: datetime | None = None,
    ) -> list[StaticticsTrackerData]:
        stats = await self.data_service.get_statistics(
            tracker_id=tracker_id,
            numeric_fields=numeric_fields,
            categorial_fields=categorial_fields,
            from_date=from_date,
        )
        return stats


class HandlePeriodValueUseCase:
    class Error(StrEnum):
        NO_TEXT = auto()
        WRONG_VALUE = auto()

    def execute(self, text: str | None) -> tuple[int, Error | None]:
        if not text or not (text := text.strip()):
            return -1, self.Error.NO_TEXT
        try:
            period_value = int(text)
        except Exception:
            return -1, self.Error.WRONG_VALUE
        return period_value, None


class HandleActionUseCase:
    class Error(StrEnum):
        NO_RECORDS = auto()

    def __init__(
        self,
        tracker_service: TrackerService,
        data_service: DataService,
    ) -> None:
        self.tracker_service = tracker_service
        self.data_service = data_service

    async def execute_csv(
        self,
        tracker_id: UUID,
        period_type: Literal["years", "months", "weeks", "days", "hours", "minutes"],
        period_value: int,
    ) -> tuple[BytesIO | None, Error | None]:
        get_csv_uc = GetCSVUseCase(self.data_service)
        res = await get_csv_uc.execute(
            tracker_id=tracker_id,
            from_date=convert_date(period_type, period_value),
        )
        if not res:
            return None, self.Error.NO_RECORDS
        return res, None

    async def execute_statistics(self, tracker_id: UUID) -> TrackerResponse:
        tracker = await self.tracker_service.get_by_id(tracker_id=tracker_id)
        return tracker


class HandleFieldUseCase:
    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(
        self, field_name: str, selected_fields: list[str], tracker_id: UUID
    ) -> tuple[list[str], str, TrackerResponse]:
        if field_name in selected_fields:
            selected_fields.remove(field_name)
        else:
            selected_fields.append(field_name)

        fields_text = "\n".join([f"- {i}" for i in selected_fields])

        tracker = await self.tracker_service.get_by_id(tracker_id=tracker_id)

        return selected_fields, fields_text, tracker


class HandleFieldsConfirmUseCase:
    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(
        self, selected_fields: list[str], tracker_id: UUID
    ) -> tuple[list[str], list[str]]:
        tracker = await self.tracker_service.get_by_id(tracker_id=tracker_id)
        numeric_fields = [
            i
            for i in selected_fields
            if tracker.structure.data[i]["type"] in ("int", "float")
        ]
        categorial_fields = [
            i
            for i in selected_fields
            if tracker.structure.data[i]["type"] not in ("int", "float")
        ]
        return numeric_fields, categorial_fields
