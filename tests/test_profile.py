import os
from datetime import date
from decimal import Decimal

os.environ.setdefault(
    "SESSION_SECRET_KEY",
    "test-only-session-secret-key-32chars",
)

from fastapi.testclient import TestClient
import pytest

import app as app_module
import dependencies.auth as auth_dependencies
import routes.auth as auth_routes
from services.profile_service import (
    _build_category_breakdown,
    _category_class,
    _format_currency,
    _format_date,
    get_profile_context,
)


def _authenticated_client(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda credentials: {"id": 7, "name": "Finzo User"},
    )
    client = TestClient(app_module.app)
    response = client.post(
        "/login",
        data={"email": "user@example.com", "password": "correct-password"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return client


def test_profile_redirects_anonymous_visitors_to_login():
    response = TestClient(app_module.app).get(
        "/profile",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


@pytest.mark.parametrize("user_id", [None, True, 0, -1, "7", 7.0])
def test_session_user_id_rejects_invalid_values(user_id):
    from starlette.requests import Request

    request = Request(
        {
            "type": "http",
            "headers": [],
            "session": {"user_id": user_id},
        }
    )

    assert auth_dependencies.get_session_user_id(request) is None


def test_current_user_dependency_keeps_unauthorized_response():
    from fastapi import HTTPException
    from starlette.requests import Request

    request = Request(
        {
            "type": "http",
            "headers": [],
            "session": {},
        }
    )

    with pytest.raises(HTTPException) as error:
        auth_dependencies.get_current_user_id(request)

    assert error.value.status_code == 401


def test_profile_renders_mock_user_and_summary(monkeypatch):
    client = _authenticated_client(monkeypatch)
    response = client.get("/profile")

    assert response.status_code == 200
    assert "Aisha Sharma" in response.text
    assert "aisha.sharma@example.com" in response.text
    assert "AS" in response.text
    assert "January 2024" in response.text
    assert "₹24,680" in response.text
    assert "18" in response.text
    assert "Food" in response.text
    assert "Preview data" in response.text


def test_profile_renders_transactions_and_category_breakdown(monkeypatch):
    client = _authenticated_client(monkeypatch)
    response = client.get("/profile")

    assert response.status_code == 200
    assert "Recent transactions" in response.text
    assert "02 Oct 2026" in response.text
    assert "Weekly groceries" in response.text
    assert "Metro pass" in response.text
    assert "Electricity bill" in response.text
    assert "₹2,450" in response.text
    assert "Category breakdown" in response.text
    assert "category-food" in response.text
    assert "category-travel" in response.text
    assert "category-bills" in response.text
    assert "51% of spending" in response.text
    assert 'tabindex="0"' in response.text
    assert 'role="region"' in response.text


def test_profile_route_does_not_query_database(monkeypatch):
    def unexpected_query(*_args, **_kwargs):
        raise AssertionError("Profile sample data must not query MySQL.")

    monkeypatch.setattr("database.execute_query", unexpected_query)
    client = _authenticated_client(monkeypatch)

    response = client.get("/profile")

    assert response.status_code == 200


def test_profile_displays_empty_states_for_empty_data(monkeypatch):
    context = get_profile_context()
    context["transactions"] = []
    context["category_breakdown"] = []
    monkeypatch.setattr(app_module, "get_profile_context", lambda: context)
    client = _authenticated_client(monkeypatch)

    response = client.get("/profile")

    assert response.status_code == 200
    assert "No transactions to show yet." in response.text
    assert "No category data to show yet." in response.text


def test_profile_navigation_is_only_shown_for_authenticated_sessions(monkeypatch):
    anonymous_response = TestClient(app_module.app).get("/")
    assert "Profile" not in anonymous_response.text

    client = _authenticated_client(monkeypatch)
    authenticated_response = client.get("/profile")

    assert 'href="http://testserver/profile"' in authenticated_response.text
    assert "Sign out" in authenticated_response.text
    assert "Get started" not in authenticated_response.text


def test_profile_context_uses_indian_currency_dates_and_category_classes():
    context = get_profile_context()

    assert _format_currency(Decimal("123456.50")) == "₹1,23,456.50"
    assert _format_currency(Decimal("1000.00")) == "₹1,000"
    assert _format_currency(Decimal("-1500.00")) == "-₹1,500"
    assert _format_date(date(2026, 10, 2)) == "02 Oct 2026"
    assert _category_class("  Coffee & Snacks ") == "category-coffee-snacks"
    assert _category_class("   ") == "category-general"
    assert sum(item["share"] for item in context["category_breakdown"]) == 100


def test_category_breakdown_rounding_sums_to_100_and_handles_zero_total():
    categories = [
        {"name": "One", "amount": Decimal("1")},
        {"name": "Two", "amount": Decimal("1")},
        {"name": "Three", "amount": Decimal("1")},
    ]
    rounded = _build_category_breakdown(categories, Decimal("3"))
    zeroed = _build_category_breakdown(categories, Decimal("0"))

    assert sum(item["share"] for item in rounded) == 100
    assert all(item["share"] == 0 for item in zeroed)
