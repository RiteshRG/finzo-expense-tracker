from decimal import Decimal
from typing import Any

from repositories.expense_repository import create_expense as create_expense_record
from schemas import ExpenseCreate


class ExpenseCreationError(ValueError):
    """Raised when a submitted expense payload is invalid."""


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


__all__ = ["create_expense", "ExpenseCreationError"]
