import os
from datetime import date, datetime, timezone
from decimal import Decimal

os.environ.setdefault(
    "DATABASE_URL",
    "mysql://test:test@127.0.0.1/finzo_test",
)
os.environ.setdefault(
    "SESSION_SECRET_KEY",
    "test-only-session-secret-key-32chars",
)

from fastapi.testclient import TestClient
import pytest

import app as app_module
import dependencies.auth as auth_dependencies
import routes.auth as auth_routes
import routes.profile as profile_routes
import services.profile_service as profile_service
from repositories import expense_repository


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


def _profile_data():
    return {
        "user": {
            "id": 7,
            "name": "Aisha Sharma",
            "email": "aisha.sharma@example.com",
            "initials": "AS",
            "member_since": "January 2024",
        },
        "summary": {
            "is_sample": False,
            "period": "This month",
            "total_spent": "₹24,680",
            "transaction_count": 3,
            "top_category": "Food",
        },
        "date_range": {
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        },
        "date_presets": [
            {
                "label": "This month",
                "start_date": "2026-10-01",
                "end_date": "2026-10-31",
                "is_active": True,
            },
            {
                "label": "Last 3 months",
                "start_date": "2026-08-01",
                "end_date": "2026-10-31",
                "is_active": False,
            },
            {
                "label": "Last 6 months",
                "start_date": "2026-05-01",
                "end_date": "2026-10-31",
                "is_active": False,
            },
        ],
        "transactions": [
            {
                "date": "02 Oct 2026",
                "description": "Weekly groceries",
                "category": "Food",
                "category_class": "category-food",
                "amount": "₹2,450",
            },
            {
                "date": "30 Sep 2026",
                "description": "Metro pass",
                "category": "Travel",
                "category_class": "category-travel",
                "amount": "₹1,200",
            },
            {
                "date": "28 Sep 2026",
                "description": "Electricity bill",
                "category": "Bills",
                "category_class": "category-bills",
                "amount": "₹1,850",
            },
        ],
        "category_breakdown": [
            {
                "name": "Food",
                "category_class": "category-food",
                "amount": "₹12,480",
                "share": 51,
            },
            {
                "name": "Travel",
                "category_class": "category-travel",
                "amount": "₹7,200",
                "share": 29,
            },
            {
                "name": "Bills",
                "category_class": "category-bills",
                "amount": "₹5,000",
                "share": 20,
            },
        ],
    }


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


def test_profile_renders_repository_backed_context(monkeypatch):
    monkeypatch.setattr(
        profile_routes,
        "get_profile_context",
        lambda _id, *_args: _profile_data(),
    )
    client = _authenticated_client(monkeypatch)

    response = client.get("/profile")

    assert response.status_code == 200
    assert "Aisha Sharma" in response.text
    assert "aisha.sharma@example.com" in response.text
    assert "AS" in response.text
    assert "January 2024" in response.text
    assert "₹24,680" in response.text
    assert "Recent transactions" in response.text
    assert "Weekly groceries" in response.text
    assert "Category breakdown" in response.text
    assert "Preview data" not in response.text
    assert 'value="2026-10-01"' in response.text
    assert 'value="2026-10-31"' in response.text
    assert "type=\"date\"" in response.text
    assert "This month" in response.text
    assert "Last 3 months" in response.text
    assert "Last 6 months" in response.text
    assert 'aria-current="date"' in response.text


def test_profile_clears_stale_user_session(monkeypatch):
    monkeypatch.setattr(
        profile_routes, "get_profile_context", lambda _id, *_args: None
    )
    client = _authenticated_client(monkeypatch)

    response = client.get("/profile", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert "session=" in response.headers.get("set-cookie", "")


def test_profile_database_failure_is_generic_503(monkeypatch):
    def fail(_user_id, *_args):
        raise profile_service.ProfileDataUnavailableError

    monkeypatch.setattr(profile_routes, "get_profile_context", fail)
    client = _authenticated_client(monkeypatch)

    response = client.get("/profile")

    assert response.status_code == 503
    assert "temporarily unavailable" in response.text
    assert "database" not in response.text.lower()


def test_profile_context_uses_current_month_bounds_and_formats_real_values(
    monkeypatch,
):
    user = {
        "id": 7,
        "name": "  ",
        "email": "aisha.sharma@example.com",
        "created_at": datetime(2024, 1, 15),
    }
    recent = [
        {
            "id": 12,
            "title": "Weekly groceries",
            "amount": Decimal("2450.00"),
            "category": "Food",
            "created_at": datetime(2026, 10, 2, 10),
        }
    ]
    bounds = []
    monkeypatch.setattr(profile_service, "get_user_by_id", lambda user_id: user)
    recent_bounds = []

    def recent_transactions(user_id, start, end):
        recent_bounds.append((user_id, start, end))
        return recent

    monkeypatch.setattr(
        profile_service, "get_recent_transactions", recent_transactions
    )

    def category_totals(user_id, start, end):
        bounds.append((user_id, start, end))
        return [
            {
                "name": "Other & Stuff",
                "amount": Decimal("50.00"),
                "transaction_count": 1,
            },
            {
                "name": "Food",
                "amount": Decimal("50.00"),
                "transaction_count": 1,
            },
        ]

    monkeypatch.setattr(
        profile_service, "get_category_totals_for_range", category_totals
    )

    context = profile_service.get_profile_context(
        7,
        now=datetime(2026, 10, 3, 12, tzinfo=timezone.utc),
    )

    assert context is not None
    assert context["user"]["name"] == "aisha.sharma@example.com"
    assert context["user"]["initials"] == "AI"
    assert context["user"]["member_since"] == "January 2024"
    assert context["summary"]["is_sample"] is False
    assert context["summary"]["total_spent"] == "₹100"
    assert context["summary"]["top_category"] == "Food"
    assert context["summary"]["period"] == "01 Oct 2026 to 31 Oct 2026"
    assert context["date_range"] == {
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
    }
    assert context["date_presets"] == [
        {
            "label": "This month",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
            "is_active": True,
        },
        {
            "label": "Last 3 months",
            "start_date": "2026-08-01",
            "end_date": "2026-10-31",
            "is_active": False,
        },
        {
            "label": "Last 6 months",
            "start_date": "2026-05-01",
            "end_date": "2026-10-31",
            "is_active": False,
        },
    ]
    assert context["transactions"][0]["date"] == "02 Oct 2026"
    assert context["transactions"][0]["category_class"] == "category-food"
    assert sum(item["share"] for item in context["category_breakdown"]) == 100
    assert bounds == [
        (7, datetime(2026, 10, 1), datetime(2026, 11, 1)),
    ]
    assert recent_bounds == bounds


def test_empty_profile_data_uses_zero_values_and_no_sample_rows(monkeypatch):
    monkeypatch.setattr(
        profile_service,
        "get_user_by_id",
        lambda _user_id: {
            "id": 7,
            "name": "New User",
            "email": "new@example.com",
            "created_at": datetime(2026, 10, 1),
        },
    )
    monkeypatch.setattr(
        profile_service, "get_recent_transactions", lambda *_args: []
    )
    monkeypatch.setattr(
        profile_service, "get_category_totals_for_range", lambda *_args: []
    )

    context = profile_service.get_profile_context(7)

    assert context is not None
    assert context["summary"]["total_spent"] == "₹0"
    assert context["summary"]["transaction_count"] == 0
    assert context["summary"]["top_category"] == ""
    assert context["transactions"] == []
    assert context["category_breakdown"] == []


def test_profile_context_uses_custom_inclusive_date_range(monkeypatch):
    expected_bounds = (datetime(2026, 9, 15), datetime(2026, 10, 2))
    recent_bounds = []
    category_bounds = []
    monkeypatch.setattr(
        profile_service,
        "get_user_by_id",
        lambda _user_id: {
            "id": 7,
            "name": "User",
            "email": "user@example.com",
            "created_at": datetime(2024, 1, 1),
        },
    )

    def get_recent(user_id, start, end):
        recent_bounds.append((user_id, start, end))
        return []

    def get_categories(user_id, start, end):
        category_bounds.append((user_id, start, end))
        return []

    monkeypatch.setattr(profile_service, "get_recent_transactions", get_recent)
    monkeypatch.setattr(
        profile_service, "get_category_totals_for_range", get_categories
    )

    context = profile_service.get_profile_context(
        7,
        start_date=date(2026, 9, 15),
        end_date=date(2026, 10, 1),
        now=datetime(2026, 10, 3, tzinfo=timezone.utc),
    )

    assert context is not None
    assert context["date_range"] == {
        "start_date": "2026-09-15",
        "end_date": "2026-10-01",
    }
    assert recent_bounds == [(7, *expected_bounds)]
    assert category_bounds == recent_bounds


@pytest.mark.parametrize(
    ("start_date", "end_date", "expected_start", "expected_end"),
    [
        (
            date(2026, 9, 15),
            None,
            datetime(2026, 9, 15),
            datetime(2026, 11, 1),
        ),
        (
            None,
            date(2026, 10, 12),
            datetime(2026, 10, 1),
            datetime(2026, 10, 13),
        ),
    ],
)
def test_profile_context_defaults_omitted_bound_to_current_month(
    monkeypatch, start_date, end_date, expected_start, expected_end
):
    monkeypatch.setattr(
        profile_service,
        "get_user_by_id",
        lambda _user_id: {
            "id": 7,
            "name": "User",
            "email": "user@example.com",
            "created_at": datetime(2024, 1, 1),
        },
    )
    observed_bounds = []
    monkeypatch.setattr(
        profile_service,
        "get_recent_transactions",
        lambda _user_id, start, end: observed_bounds.append((start, end)) or [],
    )
    monkeypatch.setattr(
        profile_service, "get_category_totals_for_range", lambda *_args: []
    )

    profile_service.get_profile_context(
        7,
        start_date=start_date,
        end_date=end_date,
        now=datetime(2026, 10, 3, 12, tzinfo=timezone.utc),
    )

    assert observed_bounds == [(expected_start, expected_end)]


def test_reversed_profile_date_range_fails_before_database_access(monkeypatch):
    def unexpected_database_call(*_args, **_kwargs):
        raise AssertionError("Invalid date ranges must be rejected before querying.")

    monkeypatch.setattr(
        profile_service, "get_user_by_id", unexpected_database_call
    )

    with pytest.raises(profile_service.InvalidProfileDateRangeError):
        profile_service.get_profile_context(
            7,
            start_date=date(2026, 10, 2),
            end_date=date(2026, 10, 1),
        )


def test_profile_rejects_reversed_date_range_before_loading_context(monkeypatch):
    def unexpected_context_call(*_args, **_kwargs):
        raise AssertionError("The profile context should not load.")

    monkeypatch.setattr(
        profile_routes, "get_profile_context", unexpected_context_call
    )
    client = _authenticated_client(monkeypatch)

    response = client.get(
        "/profile?start_date=2026-10-02&end_date=2026-10-01"
    )

    assert response.status_code == 400
    assert "Start date must be on or before end date" in response.text


def test_profile_rejects_malformed_date_query_parameters(monkeypatch):
    client = _authenticated_client(monkeypatch)

    response = client.get("/profile?start_date=not-a-date")

    assert response.status_code == 422


def test_profile_route_passes_date_query_parameters_to_service(monkeypatch):
    observed = []

    def profile_context(user_id, start_date, end_date):
        observed.append((user_id, start_date, end_date))
        return _profile_data()

    monkeypatch.setattr(
        profile_routes, "get_profile_context", profile_context
    )
    client = _authenticated_client(monkeypatch)

    response = client.get(
        "/profile?start_date=2026-09-15&end_date=2026-10-01"
    )

    assert response.status_code == 200
    assert observed == [(7, date(2026, 9, 15), date(2026, 10, 1))]


def test_profile_repository_queries_are_parameterized_and_user_scoped(monkeypatch):
    calls = []

    def record_query(query, params=None, fetch=False):
        calls.append((query, params, fetch))
        return []

    monkeypatch.setattr(expense_repository, "execute_query", record_query)

    start = datetime(2026, 10, 1)
    end = datetime(2026, 11, 1)
    expense_repository.get_recent_transactions(7, start, end)
    expense_repository.get_category_totals_for_range(7, start, end)

    assert len(calls) == 2
    for query, params, fetch in calls:
        assert "user_id = %s" in query
        assert params[0] == 7
        assert fetch is True
    assert calls[0][1] == (7, start, end)
    assert "LIMIT" not in calls[0][0]
    assert "ORDER BY created_at DESC, id DESC" in calls[0][0]
    assert calls[1][1] == (7, start, end)
    assert "created_at >= %s" in calls[1][0]
    assert "created_at < %s" in calls[1][0]
    assert "SUM(amount)" in calls[1][0]
    assert "COUNT(*)" in calls[1][0]
