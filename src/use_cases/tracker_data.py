import csv
from datetime import datetime
from io import BytesIO, TextIOWrapper
from uuid import UUID

from src.schemas.result import StaticticsTrackerData
from src.services.database import DataService


class GetCSVUseCase:
    def __init__(self, data_service: DataService) -> None:
        self.data_service = data_service

    async def execute(
        self,
        tracker_id: UUID,
        from_date: datetime | None = None,
        exclude_fields: list[str] | None = None,
    ) -> BytesIO:
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

        csv_buffer = BytesIO()
        text_buffer = TextIOWrapper(csv_buffer, encoding="utf-8", newline="")
        writer = csv.writer(text_buffer)
        writer.writerow(res[0].value.keys())
        writer.writerows([i.value.values() for i in res])
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
