import logging
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "mysql://test:test@127.0.0.1/finzo_test")
os.environ.setdefault(
    "SESSION_SECRET_KEY",
    "test-only-session-secret-key-32chars",
)

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

import app as app_module
import routes.auth as auth_routes
import routes.profile as profile_routes
import services.profile_service as profile_service
from repositories import expense_repository


USER_ID = 41
FIXED_UTC_NOW = datetime(2025, 1, 14, 12, tzinfo=timezone.utc)


def _stub_profile_storage(monkeypatch, recent=None, categories=None):
    monkeypatch.setattr(
        profile_service,
        "get_user_by_id",
        lambda _user_id: {
            "id": USER_ID,
            "name": "Finzo User",
            "email": "user@example.com",
            "created_at": datetime(2024, 1, 1),
        },
    )
    monkeypatch.setattr(
        profile_service,
        "get_recent_transactions",
        lambda *_args: list(recent or []),
    )
    monkeypatch.setattr(
        profile_service,
        "get_category_totals_for_range",
        lambda *_args: list(categories or []),
    )


def _authenticated_client(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda _credentials: {"id": USER_ID, "name": "Finzo User"},
    )
    client = TestClient(app_module.app)
    response = client.post(
        "/login",
        data={"email": "user@example.com", "password": "correct-password"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return client


def test_profile_defaults_to_current_utc_month():
    start, end, _, _ = profile_service._resolve_date_range(
        None,
        None,
        datetime(
            2025, 1, 1, 0, 30, tzinfo=timezone(timedelta(hours=2))
        ),
    )

    assert start == date(2024, 12, 1)
    assert end == date(2024, 12, 31)


@pytest.mark.parametrize(
    ("label", "start", "end"),
    [
        ("This month", date(2025, 1, 1), date(2025, 1, 31)),
        ("Last 3 months", date(2024, 11, 1), date(2025, 1, 31)),
        ("Last 6 months", date(2024, 8, 1), date(2025, 1, 31)),
    ],
)
def test_profile_builds_calendar_month_presets_and_marks_active(
    monkeypatch, label, start, end
):
    _stub_profile_storage(monkeypatch)

    context = profile_service.get_profile_context(
        USER_ID,
        start_date=start,
        end_date=end,
        now=FIXED_UTC_NOW,
    )

    assert context is not None
    assert [
        (preset["label"], preset["start_date"], preset["end_date"])
        for preset in context["date_presets"]
    ] == [
        ("This month", "2025-01-01", "2025-01-31"),
        ("Last 3 months", "2024-11-01", "2025-01-31"),
        ("Last 6 months", "2024-08-01", "2025-01-31"),
    ]
    assert [
        preset["label"]
        for preset in context["date_presets"]
        if preset["is_active"]
    ] == [label]


def test_profile_custom_range_is_inclusive_and_used_for_all_sections(monkeypatch):
    observed = []
    _stub_profile_storage(monkeypatch)
    monkeypatch.setattr(
        profile_service,
        "get_recent_transactions",
        lambda user_id, start, end: observed.append(
            ("recent", user_id, start, end)
        )
        or [
            {
                "id": 1,
                "title": "Last moment of end date",
                "amount": Decimal("20.00"),
                "category": "Travel",
                "created_at": datetime(2025, 1, 2, 23, 59, 59, 999999),
            }
        ],
    )
    monkeypatch.setattr(
        profile_service,
        "get_category_totals_for_range",
        lambda user_id, start, end: observed.append(
            ("categories", user_id, start, end)
        )
        or [
            {
                "name": "Travel",
                "amount": Decimal("20.00"),
                "transaction_count": 1,
            },
            {
                "name": "Food",
                "amount": Decimal("10.00"),
                "transaction_count": 1,
            },
        ],
    )

    context = profile_service.get_profile_context(
        USER_ID,
        start_date=date(2024, 12, 31),
        end_date=date(2025, 1, 2),
        now=FIXED_UTC_NOW,
    )

    expected = (USER_ID, datetime(2024, 12, 31), datetime(2025, 1, 3))
    assert context is not None
    assert observed == [("recent", *expected), ("categories", *expected)]
    assert context["summary"]["total_spent"] == "₹30"
    assert context["summary"]["transaction_count"] == 2
    assert context["summary"]["top_category"] == "Travel"
    assert context["transactions"][0]["description"] == "Last moment of end date"
    assert {
        (category["name"], category["amount"], category["share"])
        for category in context["category_breakdown"]
    } == {
        ("Travel", "₹20", 67),
        ("Food", "₹10", 33),
    }


@pytest.mark.parametrize(
    ("start_date", "end_date", "expected_start", "expected_end"),
    [
        (
            date(2024, 12, 20),
            None,
            datetime(2024, 12, 20),
            datetime(2025, 2, 1),
        ),
        (
            None,
            date(2025, 1, 12),
            datetime(2025, 1, 1),
            datetime(2025, 1, 13),
        ),
    ],
)
def test_partial_date_range_defaults_omitted_bound_to_current_month(
    monkeypatch, start_date, end_date, expected_start, expected_end
):
    observed = []
    _stub_profile_storage(monkeypatch)
    monkeypatch.setattr(
        profile_service,
        "get_recent_transactions",
        lambda user_id, start, end: observed.append((user_id, start, end))
        or [],
    )

    profile_service.get_profile_context(
        USER_ID,
        start_date=start_date,
        end_date=end_date,
        now=FIXED_UTC_NOW,
    )

    assert observed == [(USER_ID, expected_start, expected_end)]


def test_reversed_date_range_returns_400_before_context_or_expense_reads(
    monkeypatch,
):
    monkeypatch.setattr(
        profile_service,
        "get_user_by_id",
        lambda _user_id: {
            "id": USER_ID,
            "name": "Finzo User",
            "email": "user@example.com",
            "created_at": datetime(2024, 1, 1),
        },
    )
    expense_reads = []

    def unexpected_expense_read(*_args, **_kwargs):
        expense_reads.append(True)
        raise AssertionError("Reversed dates must not read expense data.")

    monkeypatch.setattr(
        profile_service, "get_recent_transactions", unexpected_expense_read
    )
    monkeypatch.setattr(
        profile_service,
        "get_category_totals_for_range",
        unexpected_expense_read,
    )
    client = _authenticated_client(monkeypatch)

    response = client.get(
        "/profile?start_date=2025-01-10&end_date=2025-01-09"
    )

    assert response.status_code == 400
    assert "on or before" in response.text
    assert expense_reads == []


def test_malformed_date_returns_422_without_loading_profile(monkeypatch):
    def unexpected_context_call(*_args, **_kwargs):
        raise AssertionError("Malformed dates must fail request validation.")

    monkeypatch.setattr(
        profile_routes, "get_profile_context", unexpected_context_call
    )
    client = _authenticated_client(monkeypatch)

    response = client.get("/profile?start_date=not-a-date")

    assert response.status_code == 422


def test_anonymous_and_malformed_sessions_redirect_to_login():
    anonymous_response = TestClient(app_module.app).get(
        "/profile",
        follow_redirects=False,
    )
    assert anonymous_response.status_code == 303
    assert anonymous_response.headers["location"] == "/login"

    request = Request(
        {
            "type": "http",
            "headers": [],
            "session": {"user_id": "41"},
        }
    )
    response = profile_routes.profile(request)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert request.session == {}


def test_deleted_user_session_is_cleared(monkeypatch):
    monkeypatch.setattr(
        profile_routes, "get_profile_context", lambda *_args: None
    )
    client = _authenticated_client(monkeypatch)

    response = client.get("/profile", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert "session=" in response.headers.get("set-cookie", "")


def test_empty_range_has_zero_summary_and_empty_sections(monkeypatch):
    _stub_profile_storage(monkeypatch)

    context = profile_service.get_profile_context(
        USER_ID,
        start_date=date(2025, 1, 5),
        end_date=date(2025, 1, 5),
        now=FIXED_UTC_NOW,
    )

    assert context is not None
    assert context["summary"]["total_spent"] == "₹0"
    assert context["summary"]["transaction_count"] == 0
    assert context["summary"]["top_category"] == ""
    assert context["transactions"] == []
    assert context["category_breakdown"] == []


@pytest.mark.parametrize(
    "repository_method",
    [
        expense_repository.get_recent_transactions,
        expense_repository.get_category_totals_for_range,
    ],
)
def test_repository_uses_parameterized_user_scoped_date_predicates(
    monkeypatch, repository_method
):
    start = datetime(2025, 1, 1)
    end = datetime(2025, 2, 1)
    executed = {}

    def fake_execute_query(query, params=None, fetch=False):
        executed.update(query=query, params=params, fetch=fetch)
        return [{"id": 1}]

    monkeypatch.setattr(expense_repository, "execute_query", fake_execute_query)
    rows = repository_method(USER_ID, start, end)

    normalized_query = " ".join(executed["query"].lower().split())
    assert rows == [{"id": 1}]
    assert executed["params"] == (USER_ID, start, end)
    assert executed["fetch"] is True
    assert "where user_id = %s" in normalized_query
    assert "created_at >= %s" in normalized_query
    assert "created_at < %s" in normalized_query
    assert "limit" not in normalized_query
    if repository_method is expense_repository.get_category_totals_for_range:
        assert "sum(amount)" in normalized_query
        assert "count(*)" in normalized_query
        assert "group by category" in normalized_query


def test_recent_transaction_query_returns_all_rows_in_deterministic_order(
    monkeypatch,
):
    start = datetime(2025, 1, 1)
    end = datetime(2025, 2, 1)
    all_rows = [{"id": row_id} for row_id in range(1, 26)]
    executed = {}

    def fake_execute_query(query, params=None, fetch=False):
        executed.update(query=query, params=params, fetch=fetch)
        return all_rows

    monkeypatch.setattr(
        expense_repository, "execute_query", fake_execute_query
    )

    rows = expense_repository.get_recent_transactions(USER_ID, start, end)

    assert rows == all_rows
    assert len(rows) == 25
    normalized_query = " ".join(executed["query"].lower().split())
    assert "order by created_at desc, id desc" in normalized_query


def test_profile_renders_presets_custom_dates_and_range_label(monkeypatch):
    _stub_profile_storage(monkeypatch)
    get_profile_context = profile_service.get_profile_context
    monkeypatch.setattr(
        profile_routes,
        "get_profile_context",
        lambda user_id, start_date, end_date: get_profile_context(
            user_id,
            start_date,
            end_date,
            now=FIXED_UTC_NOW,
        ),
    )
    client = _authenticated_client(monkeypatch)

    response = client.get(
        "/profile?start_date=2024-11-01&end_date=2025-01-31"
    )

    assert response.status_code == 200
    assert "This month" in response.text
    assert "Last 3 months" in response.text
    assert "Last 6 months" in response.text
    assert 'aria-current="date"' in response.text
    assert 'class="profile-date-preset is-active"' in response.text
    assert (
        "start_date=2024-11-01&amp;end_date=2025-01-31"
        in response.text
    )
    assert 'value="2024-11-01"' in response.text
    assert 'value="2025-01-31"' in response.text
    assert 'method="get"' in response.text
    assert 'name="start_date"' in response.text
    assert 'name="end_date"' in response.text
    assert response.text.count("01 Nov 2024 to 31 Jan 2025") == 2
    assert "Transactions in this range" in response.text
    assert "All 0 shown" in response.text


def test_database_failure_returns_generic_logged_503(monkeypatch, caplog):
    def fail_profile_load(*_args, **_kwargs):
        raise profile_service.ProfileDataUnavailableError(
            "private database details"
        )

    monkeypatch.setattr(
        profile_routes, "get_profile_context", fail_profile_load
    )
    client = _authenticated_client(monkeypatch)

    with caplog.at_level(logging.ERROR, logger="routes.profile"):
        response = client.get("/profile")

    assert response.status_code == 503
    assert "temporarily unavailable" in response.text
    assert "private database details" not in response.text
    assert any(
        record.message == "Profile data could not be loaded."
        for record in caplog.records
    )
