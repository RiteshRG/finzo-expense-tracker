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


__all__ = [
    "get_recent_transactions",
    "get_category_totals_for_range",
]
