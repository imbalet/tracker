from datetime import datetime, timezone
from typing import Literal

from src.presentation.constants import PERIOD_DELTAS


def convert_date(
    date_type: Literal["years", "months", "weeks", "days", "hours", "minutes"],
    count: int,
) -> datetime:
    return datetime.now(timezone.utc) - PERIOD_DELTAS[date_type](count)
