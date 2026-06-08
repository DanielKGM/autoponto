from rest_framework import status


class AppError(Exception):
    default_code = "application_error"
    default_status = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        message: str,
        code: str | None = None,
        status_code: int | None = None,
        extra: dict | None = None,
    ):
        self.message = message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status
        self.extra = extra or {}
        super().__init__(message)


class NotFoundError(AppError):
    default_code = "not_found"
    default_status = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    default_code = "conflict"
    default_status = status.HTTP_409_CONFLICT


class DomainValidationError(AppError):
    default_code = "domain_validation_error"
    default_status = status.HTTP_400_BAD_REQUEST
