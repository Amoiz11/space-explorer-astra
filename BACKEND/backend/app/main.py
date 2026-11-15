import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.api.router import api_router
from backend.app.database.init_db import init_database
from backend.app.utils.error_handlers import http_exception_handler, generic_exception_handler
from backend.app.core import bootstrap_state


def _run_bootstrap_background():
    """Execute bootstrap steps in a background worker so the server port opens immediately."""
    bootstrap_state.set_running()
    try:
        import sys as _sys
        import os as _os
        _scripts_dir = _os.path.abspath(
            _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "scripts")
        )
        if _scripts_dir not in _sys.path:
            _sys.path.insert(0, _scripts_dir)
        from scripts.bootstrap import run_bootstrap
        run_bootstrap()

        # After bootstrap, load SPICE kernels if now available
        from backend.app.services.lunar_geometry_service import KernelManager
        if KernelManager.are_kernels_available():
            KernelManager.load_kernels()
            print("[Bootstrap] SPICE kernels loaded successfully.")
        bootstrap_state.set_done()
    except Exception as _e:
        print(f"[Bootstrap] Startup error: {_e}")
        bootstrap_state.set_failed(str(_e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure seed DB is copied if main DB is missing or empty before creating tables
    try:
        import sys as _sys
        import os as _os
        _scripts_dir = _os.path.abspath(
            _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "scripts")
        )
        if _scripts_dir not in _sys.path:
            _sys.path.insert(0, _scripts_dir)
        from scripts.bootstrap import step_a_seed_database
        step_a_seed_database()
    except Exception as _e:
        print(f"[Startup] DB seed check warning: {_e}")

    # Initialize database tables and seed baseline data (SQLite / PostgreSQL)
    init_database()

    # Optional bootstrap: run in background thread so server port opens quickly
    if os.getenv("BOOTSTRAP_ON_START", "false").lower() == "true":
        t = threading.Thread(target=_run_bootstrap_background, daemon=True, name="bootstrap-worker")
        t.start()
    else:
        bootstrap_state.set_done()

    from backend.app.config import settings, ENV_FILE_PATH
    has_key = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip())
    print(
        f"[Startup] LLM Provider: {settings.LLM_PROVIDER}, "
        f"Key set: {has_key}, "
        f"Model: {settings.GROQ_MODEL}, "
        f".env path: {ENV_FILE_PATH}"
    )

    # Load SPICE ephemeris kernels if already available on disk
    try:
        from backend.app.services.lunar_geometry_service import KernelManager
        if KernelManager.are_kernels_available():
            KernelManager.load_kernels()
            print("[Startup] SPICE ephemeris kernels loaded successfully.")
    except Exception as e:
        print(f"[Startup] SPICE kernels not loaded: {e}")
    yield
    try:
        from backend.app.services.lunar_geometry_service import KernelManager
        KernelManager.unload_kernels()
    except Exception:
        pass

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Space Explorer Core Platform and Planetary Exploration APIs (NASA Space Apps)",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Custom exception handlers for consistent error formatting
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
        "is_placeholder": False,
        "bootstrap_status": bootstrap_state.get_status(),
    }

# Root route
@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_PREFIX,
        "is_placeholder": False
    }

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
