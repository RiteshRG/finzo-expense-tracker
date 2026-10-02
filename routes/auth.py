import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from dependencies.auth import get_current_user_id
from schemas import UserLogin, UserRegistration
from services.auth_service import (
    AuthenticationUnavailableError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)


def _redirect_authenticated_user(request: Request) -> RedirectResponse | None:
    user_id = request.session.get("user_id")
    if isinstance(user_id, int) and user_id > 0:
        return RedirectResponse(url="/", status_code=303)
    return None


@router.get("/register", name="register")
def register_page(request: Request):
    redirect = _redirect_authenticated_user(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request=request, name="register.html", context={})


@router.post("/register", name="register_submit")
def register_submit(
    request: Request,
    name: str | None = Form(None),
    email: str | None = Form(None),
    password: str | None = Form(None),
):
    redirect = _redirect_authenticated_user(request)
    if redirect:
        return redirect

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


@router.get("/login", name="login")
def login_page(request: Request):
    redirect = _redirect_authenticated_user(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None, "email": ""},
    )


@router.post("/login", name="login_submit")
def login_submit(
    request: Request,
    email: str | None = Form(None),
    password: str | None = Form(None),
):
    redirect = _redirect_authenticated_user(request)
    if redirect:
        return redirect

    try:
        credentials = UserLogin(email=email or "", password=password or "")
    except ValidationError:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Enter a valid email address and password.",
                "email": (email or "").strip().lower(),
            },
        )

    try:
        user = authenticate_user(credentials)
    except InvalidCredentialsError:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Email or password is incorrect.",
                "email": credentials.email,
            },
        )
    except AuthenticationUnavailableError:
        logger.exception("Authentication could not be completed because the user store is unavailable.")
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Sign-in is temporarily unavailable. Please try again later.",
                "email": credentials.email,
            },
            status_code=503,
        )

    request.session.clear()
    request.session["user_id"] = user["id"]
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout", name="logout")
def logout(
    request: Request,
    _user_id: int = Depends(get_current_user_id),
):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


__all__ = [
    "router",
    "register_page",
    "register_submit",
    "login_page",
    "login_submit",
    "logout",
]
