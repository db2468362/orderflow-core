from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from orderflow_core.exceptions.base import (
    ApplicationError,
    ConflictError,
    NotFoundError,
)

DEFAULT_ERROR_MAP: dict[type[ApplicationError], int] = {
    NotFoundError: HTTPStatus.NOT_FOUND,
    ConflictError: HTTPStatus.CONFLICT,
}


def register_exception_handlers(
    app: FastAPI,
    custom_map: dict[type[ApplicationError], int] | None = None,
) -> None:
    error_map = {**DEFAULT_ERROR_MAP, **(custom_map or {})}

    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        http_status = HTTPStatus.BAD_REQUEST
        for error_cls, code in error_map.items():
            if isinstance(exc, error_cls):
                http_status = code
                break

        return JSONResponse(
            status_code=http_status,
            content={
                'error': exc.__class__.__name__,
                'message': exc.message,
            },
        )
