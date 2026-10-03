from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from dependencies.auth import get_session_user_id
from repositories.expense_repository import get_expense_for_user
from schemas import ExpenseCreate, ExpenseUpdate
from services.expense_service import (
    ExpenseCreationError,
    ExpenseUpdateError,
    create_expense,
    update_expense,
)

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


def _render_expense_form(request: Request, *, template: str, error: str | None, form: dict, expense_id: int | None = None, status_code: int = 200):
    context = {
        "error": error,
        "form": form,
        "categories": _categories(),
    }
    if expense_id is not None:
        context["expense_id"] = expense_id
    return templates.TemplateResponse(
        request=request,
        name=template,
        context=context,
        status_code=status_code,
    )


@router.get("/expenses/add", name="add_expense")
def add_expense_page(request: Request):
    user_id = get_session_user_id(request)
    if user_id is None:
        if "user_id" in request.session:
            request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    return _render_expense_form(
        request,
        template="expenses/add.html",
        error=None,
        form={
            "title": "",
            "amount": "",
            "category": "Food",
            "description": "",
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
        return _render_expense_form(
            request,
            template="expenses/add.html",
            error=message,
            form=form_data,
            status_code=400,
        )

    return RedirectResponse(url="/profile", status_code=303)


@router.get("/expenses/{expense_id}/edit", name="edit_expense")
def edit_expense_page(request: Request, expense_id: int):
    user_id = get_session_user_id(request)
    if user_id is None:
        if "user_id" in request.session:
            request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    expense = get_expense_for_user(expense_id, user_id)
    if expense is None:
        return RedirectResponse(url="/profile", status_code=303)

    return _render_expense_form(
        request,
        template="expenses/edit.html",
        error=None,
        form={
            "title": expense["title"] or "",
            "amount": str(expense["amount"]),
            "category": expense["category"] or "Food",
            "description": expense["description"] or "",
        },
        expense_id=expense_id,
    )


@router.post("/expenses/{expense_id}/edit", name="edit_expense_submit")
def edit_expense_submit(
    request: Request,
    expense_id: int,
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

    expense = get_expense_for_user(expense_id, user_id)
    if expense is None:
        return RedirectResponse(url="/profile", status_code=303)

    form_data = {
        "title": title or "",
        "amount": amount or "",
        "category": category or expense["category"] or "Food",
        "description": description or "",
    }

    try:
        payload = ExpenseUpdate(
            title=title or "",
            amount=amount or "",
            category=category,
            description=description,
        )
        update_expense(user_id, expense_id, payload)
    except (ExpenseUpdateError, ValueError, ValidationError) as exc:
        message = str(exc)
        if isinstance(exc, ValidationError):
            details = exc.errors()
            if details:
                message = details[0].get("msg", "Please provide valid expense details.")
        return _render_expense_form(
            request,
            template="expenses/edit.html",
            error=message,
            form=form_data,
            expense_id=expense_id,
            status_code=400,
        )

    return RedirectResponse(url="/profile", status_code=303)


__all__ = [
    "router",
    "add_expense_page",
    "add_expense_submit",
    "edit_expense_page",
    "edit_expense_submit",
]
