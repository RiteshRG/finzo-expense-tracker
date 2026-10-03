import os
from decimal import Decimal

os.environ.setdefault(
    "SESSION_SECRET_KEY",
    "test-only-session-secret-key-32chars",
)

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

import app as app_module
import routes.auth as auth_routes
import routes.expenses as expense_routes
import repositories.expense_repository as expense_repository
import services.expense_service as expense_service
from schemas import ExpenseUpdate


def _authenticated_client(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda credentials: {"id": 7, "name": "Finzo User"},
    )
    client = TestClient(app_module.app)
    response = client.post(
        "/login",
        data={"email": "user@example.com", "password": "password"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return client


def test_anonymous_edit_expense_page_redirects_to_login(monkeypatch):
    response = TestClient(app_module.app).get(
        "/expenses/99/edit",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_authenticated_edit_expense_page_renders_prefilled_form(monkeypatch):
    client = _authenticated_client(monkeypatch)
    monkeypatch.setattr(
        expense_routes,
        "get_expense_for_user",
        lambda expense_id, user_id: {
            "id": expense_id,
            "user_id": user_id,
            "title": "Groceries",
            "amount": Decimal("42.50"),
            "category": "Food",
            "description": "Weekly grocery run",
        },
    )

    response = client.get("/expenses/99/edit")

    assert response.status_code == 200
    assert "Edit expense" in response.text
    assert 'value="Groceries"' in response.text
    assert 'value="42.50"' in response.text
    assert 'Weekly grocery run' in response.text


def test_unauthorized_edit_expense_redirects_to_profile(monkeypatch):
    client = _authenticated_client(monkeypatch)
    monkeypatch.setattr(
        expense_routes,
        "get_expense_for_user",
        lambda expense_id, user_id: None,
    )

    response = client.get("/expenses/99/edit", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"


def test_successful_edit_expense_submission_redirects_and_updates_user(monkeypatch):
    observed = []

    def fake_get(expense_id, user_id):
        return {
            "id": expense_id,
            "user_id": user_id,
            "title": "Old title",
            "amount": Decimal("55.00"),
            "category": "Food",
            "description": "Old description",
        }

    def fake_update(user_id, expense_id, payload):
        observed.append((user_id, expense_id, payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()))
        return {
            "id": expense_id,
            "user_id": user_id,
            "title": "Lunch",
            "amount": Decimal("250.50"),
            "category": "Food",
            "description": "Office takeaway",
        }

    monkeypatch.setattr(expense_routes, "get_expense_for_user", fake_get)
    monkeypatch.setattr(expense_routes, "update_expense", fake_update)
    client = _authenticated_client(monkeypatch)

    response = client.post(
        "/expenses/99/edit",
        data={
            "title": "Lunch",
            "amount": "250.50",
            "category": "Food",
            "description": "Office takeaway",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"
    assert observed
    assert observed[0][0] == 7
    assert observed[0][1] == 99
    assert observed[0][2]["title"] == "Lunch"
    assert observed[0][2]["amount"] == Decimal("250.50")


def test_expense_service_updates_and_rejects_invalid_values(monkeypatch):
    executed = []

    def fake_update(expense_id, user_id, title, amount, category, description=None):
        executed.append((expense_id, user_id, title, amount, category, description))
        return {
            "id": expense_id,
            "user_id": user_id,
            "title": title,
            "amount": str(amount),
            "category": category,
            "description": description,
        }

    monkeypatch.setattr(expense_service, "update_expense_record", fake_update)

    payload = ExpenseUpdate(
        title="  Dinner  ",
        amount="18.75",
        category="  ",
        description="   Family meal   ",
    )
    result = expense_service.update_expense(7, 12, payload)

    assert result["title"] == "Dinner"
    assert result["amount"] == "18.75"
    assert result["category"] == "General"
    assert result["description"] == "Family meal"
    assert executed == [(12, 7, "Dinner", Decimal("18.75"), "General", "Family meal")]

    with pytest.raises(ValidationError, match="Amount must be greater than zero"):
        ExpenseUpdate(title="Taxi", amount="0")


def test_expense_repository_uses_parameterized_user_scoped_update(monkeypatch):
    calls = []

    def fake_execute(query, params=None, fetch=False):
        calls.append((query, params, fetch))
        if fetch:
            return [{"id": 99, "user_id": 7, "title": "Lunch", "amount": "250.50", "category": "Food", "description": "Office takeaway"}]
        return None

    def fake_get(expense_id, user_id):
        return {"id": expense_id, "user_id": user_id, "title": "Lunch", "amount": "250.50", "category": "Food", "description": "Office takeaway"}

    monkeypatch.setattr(expense_repository, "execute_query", fake_execute)
    monkeypatch.setattr(expense_repository, "get_expense_for_user", fake_get)

    result = expense_repository.update_expense(99, 7, "Lunch", "250.50", "Food", "Office takeaway")

    assert result["id"] == 99
    assert calls[0][0].strip().startswith("UPDATE expenses")
    assert calls[0][1] == ("Lunch", "250.50", "Food", "Office takeaway", 99, 7)
    assert calls[0][2] is False
