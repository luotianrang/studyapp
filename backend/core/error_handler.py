from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import AppException
from .logger import get_logger

logger = get_logger(__name__)


def error_response(message: str, data=None, status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "data": data},
    )


async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(
        "App exception | user_id=%s | path=%s | status=%s | message=%s",
        getattr(request.state, "user_id", "-"),
        request.url.path,
        exc.status_code,
        exc.message,
    )
    return error_response(exc.message, status_code=exc.status_code)


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP exception | user_id=%s | path=%s | status=%s | detail=%s",
        getattr(request.state, "user_id", "-"),
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return error_response(str(exc.detail), status_code=exc.status_code)


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(
        "Starlette HTTP exception | user_id=%s | path=%s | status=%s | detail=%s",
        getattr(request.state, "user_id", "-"),
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return error_response(str(exc.detail), status_code=exc.status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Validation exception | user_id=%s | path=%s | errors=%s",
        getattr(request.state, "user_id", "-"),
        request.url.path,
        exc.errors(),
    )
    return error_response("请求参数错误", status_code=422)


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception | user_id=%s | path=%s",
        getattr(request.state, "user_id", "-"),
        request.url.path,
    )
    return error_response("Internal Server Error", status_code=500)
