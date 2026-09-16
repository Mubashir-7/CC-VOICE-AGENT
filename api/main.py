"""
main.py — FastAPI application entrypoint.

Wires together: app, CORS, routes, DB startup, error handlers.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from dotenv import load_dotenv

load_dotenv()

from api.db import create_all_tables
from api.routes.patients import router as patients_router

# ── Lifespan (replaces deprecated on_event) ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all DB tables on startup. Safe to call repeatedly."""
    create_all_tables()
    yield

# ── App configuration ─────────────────────────────────────────────────────────
app = FastAPI(
    title="Voice AI Patient Registration API",
    description=(
        "REST API for the Voice AI Patient Registration Agent. "
        "Handles patient demographics collected via phone by a Vapi voice agent. "
        "Backed by SQLite for zero-ops persistence."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
cors_origins = [o.strip() for o in cors_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Custom error handlers ─────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Convert FastAPI/Pydantic request body validation errors to our envelope.
    { "data": null, "error": "field: message" }
    This fires for 422 errors on route body parsing.
    """
    errors = exc.errors()
    messages = [
        f"{' → '.join(str(loc) for loc in e['loc'] if loc != 'body')}: {e['msg']}"
        for e in errors
    ]
    return JSONResponse(
        status_code=422,
        content={"data": None, "error": "; ".join(messages)},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convert FastAPI HTTPExceptions (404, 400 etc.) to our envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "error": exc.detail},
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_error_handler(request: Request, exc: ValidationError):
    """Catch Pydantic model-level validation errors — return our envelope."""
    errors = exc.errors()
    messages = [
        f"{' → '.join(str(loc) for loc in e['loc'])}: {e['msg']}"
        for e in errors
    ]
    return JSONResponse(
        status_code=422,
        content={"data": None, "error": "; ".join(messages)},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors — return consistent envelope."""
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": "An unexpected server error occurred"},
    )


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(patients_router, prefix="/patients", tags=["patients"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def health_check():
    """
    Health check endpoint.
    Used by Railway/Render to verify the service is alive.
    Returns: { "status": "ok", "service": "...", "version": "..." }
    """
    return {
        "status": "ok",
        "service": "Voice AI Patient Registration API",
        "version": "1.0.0",
        "phone_number": os.getenv("VAPI_PHONE_NUMBER", "+13854069126"),
    }
