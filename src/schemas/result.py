from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DataResult(BaseModel):
    id: int
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
