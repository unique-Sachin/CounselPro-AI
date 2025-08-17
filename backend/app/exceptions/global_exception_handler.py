from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback

from .custom_exception import (
    BaseAppException,
    BadRequestException,
    NotFoundException,
    ExceptionResponse,
)


def register_exception_handlers(app):
    """Register all exception handlers on the given FastAPI app instance"""

    @app.exception_handler(BaseAppException)
    async def base_app_exception_handler(request: Request, exc: BaseAppException):
        print(
            f"🔥 Custom exception caught: {exc.error}, {exc.details}, status: {exc.status_code}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ExceptionResponse(
                error=exc.error, details=exc.details
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = [
            {"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=ExceptionResponse(
                error="Validation Error", details=errors
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ExceptionResponse(error=str(exc.detail), details=None).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        print(f"🚨 Unhandled exception: {str(exc)}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content=ExceptionResponse(
                error="Internal Server Error",
                details=str(exc),
            ).model_dump(),
        )

    print("✅ Exception handlers registered successfully")
