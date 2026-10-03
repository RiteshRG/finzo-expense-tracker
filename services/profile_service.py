from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Any

from repositories.expense_repository import (
    get_category_totals_for_range,
    get_recent_transactions,
)
from repositories.user_repository import get_user_by_id


class ProfileDataUnavailableError(Exception):
    """Raised when profile data cannot be loaded from the database."""


class InvalidProfileDateRangeError(ValueError):
    """Raised when the requested profile date range is reversed."""


def _format_indian_grouping(value: int) -> str:
    digits = str(value)
    if len(digits) <= 3:
        return digits

    last_group = digits[-3:]
    prefix = digits[:-3]
    groups: list[str] = []
    while prefix:
        groups.append(prefix[-2:])
        prefix = prefix[:-2]
    return ",".join([*reversed(groups), last_group])


def _format_currency(value: Decimal | int | float | str) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    is_negative = amount < 0
    amount = abs(amount)
    rupees = _format_indian_grouping(int(amount))
    paise = int((amount % 1) * 100)
    fraction = f".{paise:02d}" if paise else ""
    sign = "-" if is_negative else ""
    return f"{sign}₹{rupees}{fraction}"


def _format_date(value: date | datetime) -> str:
    return f"{value.day:02d} {value:%b} {value.year}"


def _format_member_since(value: date | datetime | None) -> str:
    return value.strftime("%B %Y") if value is not None else ""


def _category_class(category: str | None) -> str:
    slug = re.sub(
        r"[^a-z0-9]+", "-", (category or "").strip().lower()
    ).strip("-")
    return f"category-{slug or 'general'}"


def _user_initials(name: str, email: str) -> str:
    words = name.strip().split()
    if not words:
        words = email.strip().split("@", maxsplit=1)[:1]
    if not words or not words[0]:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return f"{words[0][0]}{words[-1][0]}".upper()


def _current_month_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is not None:
        current = current.astimezone(timezone.utc).replace(tzinfo=None)
    start = datetime(current.year, current.month, 1)
    if current.month == 12:
        end = datetime(current.year + 1, 1, 1)
    else:
        end = datetime(current.year, current.month + 1, 1)
    return start, end


def _resolve_date_range(
    start_date: date | None,
    end_date: date | None,
    now: datetime | None = None,
) -> tuple[date, date, datetime, datetime]:
    month_start, month_end_exclusive = _current_month_bounds(now)
    effective_start = start_date or month_start.date()
    effective_end = end_date or (month_end_exclusive.date() - date.resolution)
    if effective_start > effective_end:
        raise InvalidProfileDateRangeError

    start = datetime(
        effective_start.year, effective_start.month, effective_start.day
    )
    end_exclusive = datetime(
        effective_end.year, effective_end.month, effective_end.day
    ) + date.resolution
    return effective_start, effective_end, start, end_exclusive


def _build_date_presets(
    effective_start: date, effective_end: date, now: datetime | None = None
) -> list[dict[str, Any]]:
    month_start, month_end_exclusive = _current_month_bounds(now)
    current_month_index = month_start.year * 12 + month_start.month - 1
    current_month_end = month_end_exclusive.date() - date.resolution
    presets: list[dict[str, Any]] = []

    for month_count, label in (
        (1, "This month"),
        (3, "Last 3 months"),
        (6, "Last 6 months"),
    ):
        start_month_index = current_month_index - month_count + 1
        start_year, start_month_index = divmod(start_month_index, 12)
        preset_start = date(start_year, start_month_index + 1, 1)
        presets.append(
            {
                "label": label,
                "start_date": preset_start.isoformat(),
                "end_date": current_month_end.isoformat(),
                "is_active": (
                    effective_start == preset_start
                    and effective_end == current_month_end
                ),
            }
        )

    return presets


def _decimal(value: Decimal | int | float | str | None) -> Decimal:
    return Decimal(str(value or 0))


def _build_category_breakdown(
    categories: list[dict[str, Any]], total: Decimal
) -> list[dict[str, Any]]:
    if total <= 0:
        return [
            {
                "name": item["name"] or "General",
                "category_class": _category_class(item["name"]),
                "amount": _format_currency(item["amount"]),
                "share": 0,
            }
            for item in categories
        ]

    shares = [
        int(
            (_decimal(item["amount"]) * 100 / total).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
        for item in categories
    ]
    if shares:
        largest_index = max(
            range(len(shares)),
            key=lambda index: _decimal(categories[index]["amount"]),
        )
        shares[largest_index] += 100 - sum(shares)

    return [
        {
            "name": item["name"] or "General",
            "category_class": _category_class(item["name"]),
            "amount": _format_currency(item["amount"]),
            "share": share,
        }
        for item, share in zip(categories, shares)
    ]


def get_profile_context(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """Build the display-ready profile context; return None for a deleted user."""
    effective_start, effective_end, start, end_exclusive = _resolve_date_range(
        start_date, end_date, now
    )
    try:
        user = get_user_by_id(user_id)
    except Exception as exc:
        raise ProfileDataUnavailableError from exc
    if user is None:
        return None

    try:
        recent_expenses = get_recent_transactions(user_id, start, end_exclusive)
        category_totals = get_category_totals_for_range(
            user_id, start, end_exclusive
        )
    except Exception as exc:
        raise ProfileDataUnavailableError from exc

    raw_name = (user.get("name") or "").strip()
    email = user["email"]
    display_name = raw_name or email
    categories = [
        {
            "name": category["name"] or "General",
            "amount": _decimal(category["amount"]),
        }
        for category in category_totals
    ]
    total_spent = sum(
        (category["amount"] for category in categories),
        start=Decimal("0"),
    )
    transaction_count = sum(
        int(category["transaction_count"])
        for category in category_totals
    )
    categories.sort(
        key=lambda item: (-item["amount"], item["name"].casefold())
    )
    top_category = categories[0]["name"] if categories else ""

    return {
        "user": {
            "id": user["id"],
            "name": display_name,
            "email": email,
            "initials": _user_initials(raw_name, email),
            "member_since": _format_member_since(user.get("created_at")),
        },
        "summary": {
            "is_sample": False,
            "period": (
                f"{_format_date(effective_start)} to "
                f"{_format_date(effective_end)}"
            ),
            "total_spent": _format_currency(total_spent),
            "transaction_count": transaction_count,
            "top_category": top_category,
        },
        "date_range": {
            "start_date": effective_start.isoformat(),
            "end_date": effective_end.isoformat(),
        },
        "date_presets": _build_date_presets(
            effective_start, effective_end, now
        ),
        "transactions": [
            {
                "id": expense["id"],
                "date": _format_date(expense["created_at"]),
                "description": expense["title"],
                "category": expense["category"] or "General",
                "category_class": _category_class(expense["category"]),
                "amount": _format_currency(expense["amount"]),
            }
            for expense in recent_expenses
        ],
        "category_breakdown": _build_category_breakdown(
            categories, total_spent
        ),
    }


__all__ = [
    "get_profile_context",
    "ProfileDataUnavailableError",
    "InvalidProfileDateRangeError",
    "_current_month_bounds",
    "_resolve_date_range",
    "_build_date_presets",
    "_format_currency",
    "_format_date",
    "_category_class",
    "_build_category_breakdown",
]
