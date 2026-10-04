import logging
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from dotenv import load_dotenv

from database import (
    check_database_connection,
    init_db,
    seed_db,
    validate_database_config,
)
from dependencies.auth import get_session_user_id
from routes.analytics import router as analytics_router
from routes.auth import router as auth_router
from routes.expenses import router as expenses_router
from routes.profile import router as profile_router

load_dotenv()

logger = logging.getLogger(__name__)


def _get_session_secret() -> str:
    session_secret = os.getenv("SESSION_SECRET_KEY")
    if not session_secret or len(session_secret) < 32:
        raise RuntimeError(
            "SESSION_SECRET_KEY must be set to a secret of at least 32 characters."
        )
    return session_secret


session_secret = _get_session_secret()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(expenses_router)
app.include_router(analytics_router)
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    same_site="lax",
    https_only=os.getenv("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
)


@app.on_event("startup")
def startup_event() -> None:
    try:
        validate_database_config()
        if os.getenv("APP_ENV", "production").strip().lower() in {
            "development",
            "test",
        }:
            init_db()
            if os.getenv("SEED_DEMO_DATA", "").strip().lower() in {
                "1",
                "true",
                "yes",
            }:
                seed_db()
    except Exception:
        logger.exception("Application startup checks failed.")
        raise


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.get("/health", name="health")
def health() -> JSONResponse:
    try:
        check_database_connection()
    except Exception:
        logger.exception("Application health check failed.")
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable"},
        )
    return JSONResponse(content={"status": "ok"})


@app.get("/", name="landing")
def landing(request: Request):
    if get_session_user_id(request) is not None:
        return RedirectResponse(url="/profile", status_code=303)
    if "user_id" in request.session:
        request.session.clear()
    return templates.TemplateResponse(request=request, name="landing.html", context={})


@app.get("/terms", name="terms")
def terms(request: Request):
    return templates.TemplateResponse(request=request, name="terms.html", context={})


@app.get("/privacy", name="privacy")
def privacy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html", context={})


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5001, reload=True)
