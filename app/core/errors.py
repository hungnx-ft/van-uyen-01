import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)
CODES = {400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found",
         405: "method_not_allowed", 413: "payload_too_large", 409: "conflict", 422: "validation_error", 503: "unavailable"}


def error_response(status: int, message: str, *, details=None, headers=None):
    body = {"code": CODES.get(status, "internal_error"), "message": message}
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status, content={"error": body}, headers=headers)


def install_error_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return error_response(exc.status_code, str(exc.detail), headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Do not echo request input: it can contain passwords and tokens.
        details = [{"field": ".".join(map(str, e["loc"])), "message": e["msg"], "type": e["type"]}
                   for e in exc.errors()]
        return error_response(422, "Request validation failed", details=details)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError):
        return error_response(409, "The operation conflicts with existing data")

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        logger.error("Database operation failed (%s)", type(exc).__name__)
        return error_response(503, "Database is temporarily unavailable")

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error("Unexpected request failure (%s)", type(exc).__name__)
        return error_response(500, "An unexpected error occurred")
