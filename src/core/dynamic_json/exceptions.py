class DynamicJsonException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AttributeException(DynamicJsonException):
    pass


class DataException(DynamicJsonException):
    pass
