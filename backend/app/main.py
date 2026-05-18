import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.session import create_all_tables

logger = logging.getLogger(__name__)
_settings = get_settings()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    await create_all_tables()
    logger.info("Database tables ready.")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=_settings.APP_NAME,
        version=_settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_lifespan,
    )

    # ── CORS (allow the Vite dev server and any public URL) ────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global error handler ───────────────────────────────────────────────────
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    # ── Routes ─────────────────────────────────────────────────────────────────
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "version": _settings.APP_VERSION}

    return app


app = create_app()


def start() -> None:
    """Poetry script entry point: poetry run start-api"""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=_settings.DEBUG,
    )
