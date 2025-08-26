import csv
from datetime import datetime
from enum import StrEnum, auto
from io import BytesIO, TextIOWrapper
from uuid import UUID

from schemas.tracker import TrackerResponse
from src.schemas.result import StatisticsTrackerData
from src.services.database import DataService, TrackerService

__all__ = [
    "GetCSVUseCase",
    "GetStatisticsUseCase",
    "HandlePeriodValueUseCase",
    "HandleFieldUseCase",
    "SplitFieldsByTypeUseCase",
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
    """Get statistics for a tracker with selected fields."""

    class Error(StrEnum):
        NO_FIELDS = auto()

    def __init__(self, data_service: DataService) -> None:
        self.data_service = data_service

    async def execute(
        self,
        tracker_id: UUID,
        numeric_fields: list[str],
        categorical_fields: list[str],
        from_date: datetime | None = None,
    ) -> tuple[list[StatisticsTrackerData], Error | None]:
        """Get statistics for a tracker with selected fields.

        Args:
            tracker_id (UUID): Tracker ID.
            numeric_fields (list[str]): List of numeric fields (int or float).
            categorical_fields (list[str]): List of categorical fields (string or enum).
            from_date (datetime | None, optional): Start date for statistics filtering. Defaults to None.

        Returns:
            tuple[list[StatisticsTrackerData], Error | None]:
                A list of statistics DTOs for each passed field (empty if an error occurred)
                and an error code (or None if successful).
        """
        if not numeric_fields and not categorical_fields:
            return [], self.Error.NO_FIELDS
        stats = await self.data_service.get_statistics(
            tracker_id=tracker_id,
            numeric_fields=numeric_fields,
            categorical_fields=categorical_fields,
            from_date=from_date,
        )
        return stats, None


class HandlePeriodValueUseCase:
    """Validates user input and extracts int value."""

    class Error(StrEnum):
        NO_TEXT = auto()
        WRONG_VALUE = auto()

    def execute(self, text: str | None) -> tuple[int, Error | None]:
        """Validates user input and extracts int value.

        Args:
            text (str | None): The entered text or None.

        Returns:
            tuple[int, Error | None]:
                Parsed int value (-1 if an error occurred)
                and an error code (or None if successful).
        """
        if not text or not (text := text.strip()):
            return -1, self.Error.NO_TEXT
        try:
            period_value = int(text)
        except Exception:
            return -1, self.Error.WRONG_VALUE
        return period_value, None


class HandleFieldUseCase:
    """Adds or removes a field from the selected fields list and generates a response text."""

    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(
        self, field_name: str, selected_fields: list[str]
    ) -> tuple[list[str], str]:
        """Adds or removes a field from the selected fields list and generates a response text.

        Args:
            field_name (str): Field name.
            selected_fields (list[str]): List of currently selected fields.

        Returns:
            tuple[list[str], str]:
                The list with updated selected fields
                and formatted text for response.
        """
        if field_name in selected_fields:
            selected_fields.remove(field_name)
        else:
            selected_fields.append(field_name)

        fields_text = "\n".join([f"- {i}" for i in selected_fields])
        return selected_fields, fields_text


class SplitFieldsByTypeUseCase:
    """Split the selected fields into numeric and categorical fields."""

    def __init__(self, tracker_service: TrackerService) -> None:
        self.tracker_service = tracker_service

    async def execute(
        self, selected_fields: list[str], tracker: TrackerResponse
    ) -> tuple[list[str], list[str]]:
        """Split the selected fields into numeric and categorical fields.

        Args:
            selected_fields (list[str]):  List of selected field names.
            tracker (TrackerResponse): Tracker DTO with structure.

        Returns:
            tuple[list[str], list[str]]:
                The list with numeric fields
                and the list with categorical fields.
        """
        numeric_fields = [
            i
            for i in selected_fields
            if tracker.structure.data[i]["type"] in ("int", "float")
        ]
        categorical_fields = [
            i
            for i in selected_fields
            if tracker.structure.data[i]["type"] in ("string", "enum")
        ]
        return numeric_fields, categorical_fields
