from datetime import datetime
from typing import Any

from database import execute_query


def get_recent_transactions(
    user_id: int, start: datetime, end: datetime
) -> list[dict[str, Any]]:
    return execute_query(
        """
        SELECT id, title, amount, category, created_at
        FROM expenses
        WHERE user_id = %s
          AND created_at >= %s
          AND created_at < %s
        ORDER BY created_at DESC, id DESC
        """,
        (user_id, start, end),
        fetch=True,
    )


def get_category_totals_for_range(
    user_id: int, start: datetime, end: datetime
) -> list[dict[str, Any]]:
    rows = execute_query(
        """
        SELECT category AS name, SUM(amount) AS amount, COUNT(*) AS transaction_count
        FROM expenses
        WHERE user_id = %s
          AND created_at >= %s
          AND created_at < %s
        GROUP BY category
        ORDER BY category ASC
        """,
        (user_id, start, end),
        fetch=True,
    )
    return rows


def get_expense_by_id(expense_id: int) -> dict[str, Any] | None:
    rows = execute_query(
        """
        SELECT id, user_id, title, amount, category, description, created_at, updated_at
        FROM expenses
        WHERE id = %s
        LIMIT 1
        """,
        (expense_id,),
        fetch=True,
    )
    return rows[0] if rows else None


def get_expense_for_user(expense_id: int, user_id: int) -> dict[str, Any] | None:
    rows = execute_query(
        """
        SELECT id, user_id, title, amount, category, description, created_at, updated_at
        FROM expenses
        WHERE id = %s AND user_id = %s
        LIMIT 1
        """,
        (expense_id, user_id),
        fetch=True,
    )
    return rows[0] if rows else None


def create_expense(
    user_id: int,
    title: str,
    amount: float | str,
    category: str,
    description: str | None = None,
) -> dict[str, Any] | None:
    row_id = execute_query(
        """
        INSERT INTO expenses (user_id, title, amount, category, description)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, title, amount, category, description),
        fetch=False,
    )
    return get_expense_by_id(row_id)


def update_expense(
    expense_id: int,
    user_id: int,
    title: str,
    amount: float | str,
    category: str,
    description: str | None = None,
) -> dict[str, Any] | None:
    execute_query(
        """
        UPDATE expenses
        SET title = %s, amount = %s, category = %s, description = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s AND user_id = %s
        """,
        (title, amount, category, description, expense_id, user_id),
        fetch=False,
    )
    return get_expense_for_user(expense_id, user_id)


def delete_expense(expense_id: int, user_id: int) -> bool:
    deleted_rows = execute_query(
        """
        DELETE FROM expenses
        WHERE id = %s AND user_id = %s
        """,
        (expense_id, user_id),
        fetch=False,
        return_rowcount=True,
    )
    return deleted_rows == 1


__all__ = [
    "get_recent_transactions",
    "get_category_totals_for_range",
    "get_expense_by_id",
    "get_expense_for_user",
    "create_expense",
    "update_expense",
    "delete_expense",
]
