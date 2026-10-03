import logging
from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies.auth import get_session_user_id
from services.profile_service import (
    InvalidProfileDateRangeError,
    ProfileDataUnavailableError,
    get_profile_context,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)


@router.get("/profile", name="profile")
def profile(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
):
    user_id = get_session_user_id(request)
    if user_id is None:
        if "user_id" in request.session:
            request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    try:
        if start_date is not None and end_date is not None and start_date > end_date:
            raise InvalidProfileDateRangeError
        context = get_profile_context(user_id, start_date, end_date)
    except InvalidProfileDateRangeError:
        return PlainTextResponse(
            "Start date must be on or before end date.",
            status_code=400,
        )
    except ProfileDataUnavailableError:
        logger.exception("Profile data could not be loaded.")
        return PlainTextResponse(
            "Your profile is temporarily unavailable. Please try again later.",
            status_code=503,
        )

    if context is None:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context=context,
    )


__all__ = ["router", "profile"]
