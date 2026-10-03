import os

os.environ.setdefault(
    "SESSION_SECRET_KEY",
    "test-only-session-secret-key-32chars",
)

from fastapi.testclient import TestClient
import pytest
from starlette.requests import Request

import app as app_module
import database as database_module
import routes.auth as auth_routes
import routes.expenses as expense_routes
import routes.profile as profile_routes
import repositories.expense_repository as expense_repository
import services.expense_service as expense_service


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


def test_anonymous_delete_expense_redirects_to_login(monkeypatch):
    response = TestClient(app_module.app).post(
        "/expenses/99/delete",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_malformed_session_user_id_is_cleared_and_redirects_to_login(monkeypatch):
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/expenses/99/delete",
            "headers": [],
            "session": {"user_id": "not-an-int"},
        }
    )
    response = expense_routes.delete_expense_submit(request, 99)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert request.session == {}


def test_get_request_is_not_allowed_for_delete_route(monkeypatch):
    client = _authenticated_client(monkeypatch)

    response = client.get(
        "/expenses/99/delete",
        follow_redirects=False,
    )

    assert response.status_code == 405


def test_successful_delete_expense_uses_authenticated_user_id_not_form_data(monkeypatch):
    observed = []

    def fake_delete(user_id, expense_id):
        observed.append((user_id, expense_id))
        return True

    monkeypatch.setattr(expense_routes, "delete_expense", fake_delete)
    client = _authenticated_client(monkeypatch)

    response = client.post(
        "/expenses/99/delete",
        data={"user_id": "12345"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"
    assert observed == [(7, 99)]


def test_missing_or_other_user_delete_redirects_without_disclosing_details(monkeypatch):
    monkeypatch.setattr(expense_routes, "delete_expense", lambda user_id, expense_id: False)
    client = _authenticated_client(monkeypatch)

    response = client.post(
        "/expenses/999/delete",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"


def test_delete_expense_failure_is_logged_and_returns_generic_503(monkeypatch, caplog):
    def fake_delete(user_id, expense_id):
        raise expense_service.ExpenseDeletionError("database unavailable")

    monkeypatch.setattr(expense_routes, "delete_expense", fake_delete)
    client = _authenticated_client(monkeypatch)

    response = client.post(
        "/expenses/99/delete",
        follow_redirects=False,
    )

    assert response.status_code == 503
    assert response.text == "This expense could not be deleted right now. Please try again later."
    assert "database unavailable" not in response.text
    assert "Expense deletion could not be completed." in caplog.text


def test_profile_page_renders_confirmed_delete_form_for_each_transaction(monkeypatch):
    client = _authenticated_client(monkeypatch)
    context = {
        "summary": {
            "is_sample": False,
            "period": "Last 30 days",
            "total_spent": "₹1,234.00",
            "transaction_count": 1,
            "top_category": "Food",
        },
        "user": {
            "initials": "FU",
            "name": "Finzo User",
            "email": "user@example.com",
            "member_since": "2024-01-01",
        },
        "date_presets": [
            {
                "is_active": True,
                "label": "This month",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        ],
        "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        "transactions": [
            {
                "id": 99,
                "date": "2024-01-08",
                "description": "Groceries",
                "category": "Food",
                "amount": "₹500.00",
                "category_class": "food",
            }
        ],
    }
    monkeypatch.setattr(
        profile_routes,
        "get_profile_context",
        lambda user_id, start_date=None, end_date=None: context,
    )

    response = client.get("/profile")

    assert response.status_code == 200
    assert 'action="http://testserver/expenses/99/delete"' in response.text
    assert 'method="post"' in response.text
    assert 'type="button"' in response.text
    assert "data-delete-trigger" in response.text
    assert "data-delete-expense-form" in response.text
    assert '<dialog class="expense-delete-dialog"' in response.text
    assert "Are you sure you want to delete this expense?" in response.text
    assert "data-delete-cancel" in response.text
    assert "data-delete-confirm" in response.text
    assert "/static/js/main.js?v=delete-dialog-20261004" in response.text
    assert 'type="submit">Delete' not in response.text
    assert 'Delete' in response.text

    context["transactions"] = []
    empty_response = client.get("/profile")

    assert empty_response.status_code == 200
    assert "No transactions to show yet." in empty_response.text
    assert "data-delete-expense-form" not in empty_response.text


def test_expense_repository_delete_uses_parameterized_user_scoped_sql(monkeypatch):
    calls = []

    def fake_execute(query, params=None, fetch=False, return_rowcount=False):
        calls.append((query, params, fetch, return_rowcount))
        return 1

    monkeypatch.setattr(expense_repository, "execute_query", fake_execute)

    result = expense_repository.delete_expense(99, 7)

    assert result is True
    assert calls
    assert "DELETE FROM expenses" in calls[0][0]
    assert "WHERE id = %s AND user_id = %s" in calls[0][0]
    assert calls[0][1] == (99, 7)
    assert calls[0][3] is True


def test_expense_repository_returns_false_when_no_row_matches(monkeypatch):
    monkeypatch.setattr(expense_repository, "execute_query", lambda *args, **kwargs: 0)

    assert expense_repository.delete_expense(404, 7) is False


def test_execute_query_can_return_affected_rows_without_changing_default(monkeypatch):
    executed = []

    class FakeCursor:
        rowcount = 1
        lastrowid = 42

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, query, params):
            executed.append((query, params))

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(database_module, "get_connection", FakeConnection)

    assert database_module.execute_query(
        "DELETE FROM expenses WHERE id = %s AND user_id = %s",
        (99, 7),
        return_rowcount=True,
    ) == 1
    assert database_module.execute_query(
        "INSERT INTO expenses (user_id) VALUES (%s)",
        (7,),
    ) == 42
    assert executed == [
        ("DELETE FROM expenses WHERE id = %s AND user_id = %s", (99, 7)),
        ("INSERT INTO expenses (user_id) VALUES (%s)", (7,)),
    ]


def test_expense_service_wraps_repository_failure_for_delete(monkeypatch):
    def fake_delete(expense_id, user_id):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(expense_service, "delete_expense_record", fake_delete)

    with pytest.raises(expense_service.ExpenseDeletionError):
        expense_service.delete_expense(7, 99)
