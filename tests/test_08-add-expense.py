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
from schemas import ExpenseCreate


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


def test_anonymous_add_expense_page_redirects_to_login():
    response = TestClient(app_module.app).get(
        "/expenses/add",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_anonymous_add_expense_post_redirects_to_login():
    response = TestClient(app_module.app).post(
        "/expenses/add",
        data={
            "title": "Lunch",
            "amount": "250.50",
            "category": "Food",
            "description": "Office takeaway",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_authenticated_add_expense_page_renders_form(monkeypatch):
    client = _authenticated_client(monkeypatch)

    response = client.get("/expenses/add")

    assert response.status_code == 200
    assert "Add expense" in response.text
    assert 'name="title"' in response.text
    assert 'name="amount"' in response.text
    assert 'name="category"' in response.text
    assert 'name="description"' in response.text
    assert 'href="http://testserver/profile"' in response.text


def test_invalid_expense_title_shows_error_and_preserves_input(monkeypatch):
    client = _authenticated_client(monkeypatch)

    response = client.post(
        "/expenses/add",
        data={
            "title": "",
            "amount": "42.00",
            "category": "Food",
            "description": "Office lunch",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "Title is required." in response.text
    assert 'name="description"' in response.text
    assert "Office lunch" in response.text


def test_successful_expense_submission_redirects_and_uses_authenticated_user(monkeypatch):
    observed = []

    def fake_create(user_id, payload):
        observed.append((user_id, payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()))
        return {
            "id": 42,
            "user_id": user_id,
            "title": "Lunch",
            "amount": "250.50",
            "category": "Food",
            "description": "Office takeaway",
        }

    monkeypatch.setattr(expense_routes, "create_expense", fake_create)
    client = _authenticated_client(monkeypatch)

    response = client.post(
        "/expenses/add",
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
    assert observed[0][1]["title"] == "Lunch"
    assert observed[0][1]["amount"] == Decimal("250.50")
    assert observed[0][1]["category"] == "Food"
    assert observed[0][1]["description"] == "Office takeaway"


def test_expense_service_normalizes_and_rejects_invalid_values(monkeypatch):
    executed = []

    def fake_create(user_id, title, amount, category, description=None):
        executed.append((user_id, title, amount, category, description))
        return {
            "id": 12,
            "user_id": user_id,
            "title": title,
            "amount": str(amount),
            "category": category,
            "description": description,
        }

    monkeypatch.setattr(
        expense_service,
        "create_expense_record",
        fake_create,
    )

    payload = ExpenseCreate(
        title="  Groceries  ",
        amount="18.75",
        category="  ",
        description="   Fresh produce   ",
    )
    result = expense_service.create_expense(7, payload)

    assert result["title"] == "Groceries"
    assert result["amount"] == "18.75"
    assert result["category"] == "General"
    assert result["description"] == "Fresh produce"
    assert executed == [(7, "Groceries", Decimal("18.75"), "General", "Fresh produce")]

    with pytest.raises(ValidationError, match="Amount must be greater than zero"):
        ExpenseCreate(title="Taxi", amount="0")


def test_expense_repository_uses_parameterized_user_scoped_insert(monkeypatch):
    calls = []

    def fake_execute(query, params=None, fetch=False):
        calls.append((query, params, fetch))
        if fetch is False:
            return 99
        return []

    def fake_read(expense_id):
        return {"id": expense_id, "user_id": 7, "title": "Lunch", "amount": "250.50", "category": "Food", "description": "Office takeaway"}

    monkeypatch.setattr(expense_repository, "execute_query", fake_execute)
    monkeypatch.setattr(expense_repository, "get_expense_by_id", fake_read)

    result = expense_repository.create_expense(7, "Lunch", "250.50", "Food", "Office takeaway")

    assert result["id"] == 99
    assert len(calls) == 1
    assert "INSERT INTO expenses" in calls[0][0]
    assert calls[0][1] == (7, "Lunch", "250.50", "Food", "Office takeaway")
    assert calls[0][2] is False
