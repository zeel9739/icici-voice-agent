class AppError(Exception):
    """Base class for all application-level errors."""

    status_code: int = 500
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found."


class ConflictError(AppError):
    status_code = 409
    detail = "Resource already exists."


class ValidationError(AppError):
    status_code = 422
    detail = "Validation failed."


class LiveKitError(AppError):
    status_code = 502
    detail = "LiveKit service error."
