import os
import sys
from datetime import datetime
from time import perf_counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .database import SessionLocal, init_db
from .core.logger import get_logger, setup_logging
from .core.error_handler import (
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
    starlette_http_exception_handler,
)
from .core.exceptions import AppException
from .routers import admin, analysis, books, config_route, notifications, plan
from .routers.auth import router as auth_router
from .services.notification_service import start_notification_scheduler
from .services.seed_service import ensure_preset_books_seeded

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="StudyApp", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def user_context_middleware(request: Request, call_next):
    request.state.user_id = "-"
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            from .core.auth import decode_token

            payload = decode_token(auth_header.removeprefix("Bearer ").strip())
            if payload and payload.get("sub"):
                request.state.user_id = int(payload["sub"])
    except Exception:
        request.state.user_id = "-"
    return await call_next(request)


@app.middleware("http")
async def no_cache_middleware(request: Request, call_next):
    start = perf_counter()
    response = None
    try:
        response = await call_next(request)
    finally:
        duration_ms = round((perf_counter() - start) * 1000, 2)
        logger.info(
            "API request | time=%s | user_id=%s | path=%s | result=%s | duration_ms=%s",
            datetime.now().isoformat(timespec="seconds"),
            getattr(request.state, "user_id", "-"),
            request.url.path,
            response.status_code if response is not None else "error",
            duration_ms,
        )
    if response is not None:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get("/api/health")
def health():
    return {"status": "ok", "message": "StudyApp is running"}


app.include_router(auth_router)
app.include_router(books.router)
app.include_router(analysis.router)
app.include_router(plan.router)
app.include_router(notifications.router)
app.include_router(config_route.router)
app.include_router(admin.router)


@app.get("/")
async def root_redirect():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/go")


@app.get("/go")
async def serve_app():
    return FileResponse(
        frontend_dir / "index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database initialized")
    db = SessionLocal()
    try:
        seeded_count = ensure_preset_books_seeded(db)
        logger.info("Preset seed check finished | seeded=%s", seeded_count)
    finally:
        db.close()
    start_notification_scheduler(SessionLocal)
    logger.info("Application started")
