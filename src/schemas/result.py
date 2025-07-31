from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, model_validator


class DataResult(BaseModel):
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


class StaticticsTrackerData(BaseModel):
    type: Literal["numeric", "categorial"]
    min: float | int | None = None
    max: float | int | None = None
    avg: float | int | None = None
    sum: float | int | None = None
    mode: str | None = None
    count: int
    field_name: str

    @model_validator(mode="after")
    def validate_at_least_one_not_none(self) -> "StaticticsTrackerData":
        if self.type == "categorial" and (
            self.mode is None or any([self.min, self.max, self.avg, self.sum])
        ):
            raise ValueError()
        if self.type == "numeric" and (
            self.mode is not None or not all([self.min, self.max, self.avg, self.sum])
        ):
            raise ValueError()
        return self
