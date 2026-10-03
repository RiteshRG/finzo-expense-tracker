from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies.auth import get_session_user_id

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/analytics", name="analytics")
def analytics(request: Request):
    if get_session_user_id(request) is None:
        if "user_id" in request.session:
            request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={},
    )


__all__ = ["router", "analytics"]
