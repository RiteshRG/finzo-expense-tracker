from decimal import Decimal
from typing import Any

from repositories.expense_repository import (
    create_expense as create_expense_record,
    update_expense as update_expense_record,
)
from schemas import ExpenseCreate, ExpenseUpdate


class ExpenseCreationError(ValueError):
    """Raised when a submitted expense payload is invalid."""


class ExpenseUpdateError(ValueError):
    """Raised when an expense update payload is invalid or cannot be saved."""


def create_expense(user_id: int, payload: ExpenseCreate) -> dict[str, Any]:
    normalized = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    title = (normalized.get("title") or "").strip()
    category = (normalized.get("category") or "General").strip() or "General"
    description = (normalized.get("description") or "").strip() or None
    amount = Decimal(str(normalized.get("amount") or 0))

    if not title:
        raise ExpenseCreationError("Title is required.")
    if amount <= 0:
        raise ExpenseCreationError("Amount must be greater than zero.")

    expense = create_expense_record(
        user_id=user_id,
        title=title,
        amount=amount,
        category=category,
        description=description,
    )
    if expense is None:
        raise ExpenseCreationError("Unable to create the expense right now.")
    return expense


def update_expense(user_id: int, expense_id: int, payload: ExpenseUpdate) -> dict[str, Any]:
    normalized = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    title = (normalized.get("title") or "").strip()
    category = (normalized.get("category") or "General").strip() or "General"
    description = (normalized.get("description") or "").strip() or None
    amount = Decimal(str(normalized.get("amount") or 0))

    if not title:
        raise ExpenseUpdateError("Title is required.")
    if amount <= 0:
        raise ExpenseUpdateError("Amount must be greater than zero.")

    expense = update_expense_record(
        expense_id=expense_id,
        user_id=user_id,
        title=title,
        amount=amount,
        category=category,
        description=description,
    )
    if expense is None:
        raise ExpenseUpdateError("Unable to update the expense right now.")
    return expense


__all__ = ["create_expense", "update_expense", "ExpenseCreationError", "ExpenseUpdateError"]
