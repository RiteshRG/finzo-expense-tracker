from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from dependencies.auth import get_session_user_id
from schemas import ExpenseCreate
from services.expense_service import ExpenseCreationError, create_expense

router = APIRouter()
templates = Jinja2Templates(directory="templates")

COMMON_CATEGORIES = [
    "Food",
    "Travel",
    "Bills",
    "Entertainment",
    "Health",
    "Education",
    "Shopping",
    "Other",
]


def _categories() -> list[str]:
    return COMMON_CATEGORIES


@router.get("/expenses/add", name="add_expense")
def add_expense_page(request: Request):
    user_id = get_session_user_id(request)
    if user_id is None:
        if "user_id" in request.session:
            request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="expenses/add.html",
        context={
            "error": None,
            "form": {
                "title": "",
                "amount": "",
                "category": "Food",
                "description": "",
            },
            "categories": _categories(),
        },
    )


@router.post("/expenses/add", name="add_expense_submit")
def add_expense_submit(
    request: Request,
    title: str | None = Form(None),
    amount: str | None = Form(None),
    category: str | None = Form(None),
    description: str | None = Form(None),
):
    user_id = get_session_user_id(request)
    if user_id is None:
        if "user_id" in request.session:
            request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    form_data = {
        "title": title or "",
        "amount": amount or "",
        "category": category or "Food",
        "description": description or "",
    }

    try:
        payload = ExpenseCreate(
            title=title or "",
            amount=amount or "",
            category=category,
            description=description,
        )
        create_expense(user_id, payload)
    except (ExpenseCreationError, ValueError, ValidationError) as exc:
        message = str(exc)
        if isinstance(exc, ValidationError):
            details = exc.errors()
            if details:
                message = details[0].get("msg", "Please provide valid expense details.")
        return templates.TemplateResponse(
            request=request,
            name="expenses/add.html",
            context={
                "error": message,
                "form": form_data,
                "categories": _categories(),
            },
            status_code=400,
        )

    return RedirectResponse(url="/profile", status_code=303)


__all__ = ["router", "add_expense_page", "add_expense_submit"]
