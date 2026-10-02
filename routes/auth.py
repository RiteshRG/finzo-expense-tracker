from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from schemas import UserRegistration
from services.auth_service import register_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/register", name="register")
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={})


@router.post("/register", name="register_submit")
def register_submit(
    request: Request,
    name: str | None = Form(None),
    email: str | None = Form(None),
    password: str | None = Form(None),
):
    try:
        register_user(UserRegistration(name=name, email=email, password=password))
    except (ValueError, ValidationError) as exc:
        message = str(exc)
        if isinstance(exc, ValidationError):
            details = exc.errors()
            if details:
                message = details[0].get("msg", "Please provide valid registration details.")
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": message},
        )

    return RedirectResponse(url="/login", status_code=303)


__all__ = ["router", "register_page", "register_submit"]
