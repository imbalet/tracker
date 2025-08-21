from datetime import timedelta

PERIOD_TYPES = {
    "years": "лет",
    "months": "месяцев",
    "weeks": "недель",
    "days": "дней",
    "hours": "часов",
    "minutes": "минут",
}

PERIOD_DELTAS = {
    "years": lambda c: timedelta(days=365 * c),
    "months": lambda c: timedelta(days=30 * c),
    "weeks": lambda c: timedelta(weeks=c),
    "days": lambda c: timedelta(days=c),
    "hours": lambda c: timedelta(hours=c),
    "minutes": lambda c: timedelta(minutes=c),
}
