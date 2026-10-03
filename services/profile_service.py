from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Any


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


def _format_currency(value: Decimal) -> str:
    amount = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    is_negative = amount < 0
    amount = abs(amount)
    rupees = _format_indian_grouping(int(amount))
    paise = int((amount % 1) * 100)
    fraction = f".{paise:02d}" if paise else ""
    sign = "-" if is_negative else ""
    return f"{sign}₹{rupees}{fraction}"


def _format_date(value: date) -> str:
    return f"{value.day:02d} {value:%b} {value.year}"


def _category_class(category: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", category.strip().lower()).strip("-")
    return f"category-{slug or 'general'}"


def _sample_transactions() -> list[dict[str, Any]]:
    return [
        {
            "date": date(2026, 10, 2),
            "description": "Weekly groceries",
            "category": "Food",
            "amount": Decimal("2450.00"),
        },
        {
            "date": date(2026, 9, 30),
            "description": "Metro pass",
            "category": "Travel",
            "amount": Decimal("1200.00"),
        },
        {
            "date": date(2026, 9, 28),
            "description": "Electricity bill",
            "category": "Bills",
            "amount": Decimal("1850.00"),
        },
        {
            "date": date(2026, 9, 26),
            "description": "Lunch with friends",
            "category": "Food",
            "amount": Decimal("860.00"),
        },
    ]


def _sample_category_totals() -> list[dict[str, Any]]:
    return [
        {"name": "Food", "amount": Decimal("12480.00")},
        {"name": "Travel", "amount": Decimal("7200.00")},
        {"name": "Bills", "amount": Decimal("5000.00")},
    ]


def _build_category_breakdown(
    categories: list[dict[str, Any]], total: Decimal
) -> list[dict[str, Any]]:
    if total <= 0:
        return [
            {
                "name": item["name"],
                "category_class": _category_class(item["name"]),
                "amount": _format_currency(item["amount"]),
                "share": 0,
            }
            for item in categories
        ]

    shares = [
        int(
            (item["amount"] * 100 / total).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
        for item in categories
    ]
    if shares:
        shares[max(range(len(shares)), key=lambda index: categories[index]["amount"])] += (
            100 - sum(shares)
        )

    return [
        {
            "name": item["name"],
            "category_class": _category_class(item["name"]),
            "amount": _format_currency(item["amount"]),
            "share": share,
        }
        for item, share in zip(categories, shares)
    ]


def get_profile_context() -> dict[str, Any]:
    """Build display-ready profile context from Step 04 sample data."""
    total_spent = Decimal("24680.00")
    categories = _sample_category_totals()
    transactions = _sample_transactions()

    return {
        "user": {
            "name": "Aisha Sharma",
            "email": "aisha.sharma@example.com",
            "initials": "AS",
            "member_since": "January 2024",
        },
        "summary": {
            "is_sample": True,
            "period": "This month",
            "total_spent": _format_currency(total_spent),
            "transaction_count": 18,
            "top_category": "Food",
        },
        "transactions": [
            {
                **transaction,
                "date": _format_date(transaction["date"]),
                "category_class": _category_class(transaction["category"]),
                "amount": _format_currency(transaction["amount"]),
            }
            for transaction in transactions
        ],
        "category_breakdown": _build_category_breakdown(categories, total_spent),
    }


__all__ = [
    "get_profile_context",
    "_format_currency",
    "_format_date",
    "_category_class",
    "_build_category_breakdown",
]
