from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, model_validator


class DataResult(BaseModel):
    date: datetime
    value: dict


class FieldResult(BaseModel):
    date: datetime
    value: Any


class AggregatedNumericData(BaseModel):
    id: int
    interval_start: datetime
    interval_end: datetime
    sum: float | None = None
    avg: float | None = None
    min: float | None = None
    max: float | None = None
    record_count: int


class StatisticsTrackerData(BaseModel):
    type: Literal["numeric", "categorical"]
    min: float | int | None = None
    max: float | int | None = None
    avg: float | int | None = None
    sum: float | int | None = None
    mode: str | None = None
    count: int
    field_name: str

    @model_validator(mode="after")
    def validate_at_least_one_not_none(self) -> "StatisticsTrackerData":
        if self.type == "categorical" and (
            self.mode is None or any([self.min, self.max, self.avg, self.sum])
        ):
            raise ValueError()
        if self.type == "numeric" and (
            self.mode is not None or not all([self.min, self.max, self.avg, self.sum])
        ):
            raise ValueError()
        return self

    @staticmethod
    def _format_float(num):
        formatted = f"{num:.2f}"
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted

    @property
    def formatted(self) -> str:
        if self.type == "numeric":
            return (
                f"{self.field_name}: min - {self._format_float(self.min)}, "
                f"max - {self._format_float(self.max)}, "
                f"avg - {self._format_float(self.avg)}, "
                f"sum - {self._format_float(self.sum)}, "
                f"count - {self.count}"
            )
        else:
            return f"{self.field_name}: mode - {self.mode}, count - {self.count}"
