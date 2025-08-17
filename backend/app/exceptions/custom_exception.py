from typing import Any, List, Optional
from pydantic import BaseModel


# Pydantic model for exception responses
class ExceptionResponse(BaseModel):
    error: str
    details: Optional[Any] = None


# Custom Exception Classes
class BaseAppException(Exception):
    def __init__(
        self, error: str, details: Optional[Any] = None, status_code: int = 400
    ):
        self.error = error
        self.details = details
        self.status_code = status_code
        super().__init__(self.error)


class BadRequestException(BaseAppException):
    def __init__(self, details: Optional[Any] = None):
        super().__init__(error="Bad Request", details=details, status_code=400)


class NotFoundException(BaseAppException):
    def __init__(self, details: Optional[Any] = None):
        super().__init__(error="Not Found", details=details, status_code=404)
