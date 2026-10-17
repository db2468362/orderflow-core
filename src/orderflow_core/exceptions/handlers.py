from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from orderflow_core.exceptions.base import (
    ApplicationError,
    ConflictError,
    NotFoundError,
)

ERROR_MAP: dict[type[ApplicationError], HTTPStatus] = {
    NotFoundError: HTTPStatus.NOT_FOUND,
    ConflictError: HTTPStatus.CONFLICT,
}


def register_exception_handlers(
    app: FastAPI,
    custom_map: dict[type[ApplicationError], HTTPStatus] | None = None,
) -> None:
    error_map = {**ERROR_MAP, **(custom_map or {})}

    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        http_status = HTTPStatus.INTERNAL_SERVER_ERROR
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
