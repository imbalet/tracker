class DynamicJsonException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AttributeException(DynamicJsonException):
    """
    Raised when DynamicJson has initialization errors or required attributes are missing.
    """

    pass


class TypeException(DynamicJsonException):
    """
    Raised when a field has an unsopported type.
    """

    pass


class ValidationException(DynamicJsonException):
    """
    Raised for pydantic model validation errors.
    """

    def __init__(self, message: str, errors: list) -> None:
        formatted_errors = []
        for error in errors:
            location = "->".join(str(item) for item in error["loc"])
            message = error["msg"].strip()
            formatted_errors.append(f"{location}: {message}")
        error_details = "; ".join(formatted_errors)
        full_message = f"{message} {error_details}"
        super().__init__(full_message)
