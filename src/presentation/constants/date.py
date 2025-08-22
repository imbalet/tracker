from datetime import timedelta

from src.presentation.constants.text import MsgKey

PERIOD_TYPES = {
    "years": MsgKey.DATE_YEARS,
    "months": MsgKey.DATE_MONTHS,
    "weeks": MsgKey.DATE_WEEKS,
    "days": MsgKey.DATE_DAYS,
    "hours": MsgKey.DATE_HOURS,
    "minutes": MsgKey.DATE_MINUTES,
}

PERIOD_DELTAS = {
    "years": lambda c: timedelta(days=365 * c),
    "months": lambda c: timedelta(days=30 * c),
    "weeks": lambda c: timedelta(weeks=c),
    "days": lambda c: timedelta(days=c),
    "hours": lambda c: timedelta(hours=c),
    "minutes": lambda c: timedelta(minutes=c),
}
