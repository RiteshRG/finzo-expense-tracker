import pytest

import os

os.environ.setdefault(
    "SESSION_SECRET_KEY",
    "test-only-session-secret-key-32chars",
)

from fastapi.testclient import TestClient
from werkzeug.security import generate_password_hash

from app import app
import routes.auth as auth_routes
import routes.profile as profile_routes
from schemas import UserLogin
import services.auth_service as auth_service


@pytest.fixture(autouse=True)
def mock_profile_context(monkeypatch):
    monkeypatch.setattr(
        profile_routes,
        "get_profile_context",
        lambda user_id, *_args, **_kwargs: {
            "user": {
                "id": user_id,
                "name": "Finzo User",
                "email": "user@example.com",
                "initials": "FU",
                "member_since": "January 2024",
            },
            "summary": {
                "is_sample": False,
                "period": "This month",
                "total_spent": "₹0",
                "transaction_count": 0,
                "top_category": "",
            },
            "date_range": {
                "start_date": "2026-10-01",
                "end_date": "2026-10-31",
            },
            "transactions": [],
            "category_breakdown": [],
        },
    )


def test_login_page_renders():
    response = TestClient(app).get("/login")

    assert response.status_code == 200
    assert "Welcome back" in response.text


def test_login_success_sets_session_and_logout_clears_it(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda credentials: {"id": 7, "name": "Finzo User"},
    )
    client = TestClient(app)

    response = client.post(
        "/login",
        data={"email": "USER@example.com", "password": "correct-password"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"
    assert "session=" in response.headers["set-cookie"]

    authenticated_page = client.get("/profile")
    assert authenticated_page.status_code == 200
    assert "Sign out" in authenticated_page.text
    assert "Get started" not in authenticated_page.text

    logout_response = client.post("/logout", follow_redirects=False)
    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/login"

    anonymous_page = client.get("/")
    assert "Sign in" in anonymous_page.text
    assert "Get started" in anonymous_page.text


@pytest.mark.parametrize(
    ("method", "path", "form_data"),
    [
        ("get", "/login", None),
        ("post", "/login", {"email": "user@example.com", "password": "password"}),
        ("get", "/register", None),
        ("post", "/register", {"name": "Finzo User", "email": "user@example.com", "password": "password"}),
    ],
)
def test_authenticated_user_is_redirected_away_from_auth_pages(
    monkeypatch, method, path, form_data
):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda credentials: {"id": 7, "name": "Finzo User"},
    )
    client = TestClient(app)
    login_response = client.post(
        "/login",
        data={"email": "user@example.com", "password": "password"},
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/profile"

    def unexpected_auth_call(*_args, **_kwargs):
        raise AssertionError("Authenticated users should be redirected before auth logic runs.")

    monkeypatch.setattr(auth_routes, "authenticate_user", unexpected_auth_call)
    monkeypatch.setattr(auth_routes, "register_user", unexpected_auth_call)
    request = getattr(client, method)
    response = request(path, data=form_data, follow_redirects=False) if form_data else request(
        path, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"

    # Redirects must preserve the user's authenticated session.
    profile_response = client.get("/profile")
    assert profile_response.status_code == 200
    assert "Sign out" in profile_response.text


def test_authenticated_landing_page_redirects_to_profile(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda credentials: {"id": 7, "name": "Finzo User"},
    )
    client = TestClient(app)
    client.post(
        "/login",
        data={"email": "user@example.com", "password": "password"},
        follow_redirects=False,
    )

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"


def test_authenticated_post_login_redirects_to_profile_without_authenticating_again(
    monkeypatch,
):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda credentials: {"id": 7, "name": "Finzo User"},
    )
    client = TestClient(app)
    client.post(
        "/login",
        data={"email": "user@example.com", "password": "password"},
        follow_redirects=False,
    )

    def unexpected_authentication_call(*_args, **_kwargs):
        raise AssertionError("An authenticated session must redirect before auth.")

    monkeypatch.setattr(auth_routes, "authenticate_user", unexpected_authentication_call)
    response = client.post(
        "/login",
        data={"email": "bad-input", "password": ""},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"


def test_invalid_session_user_id_is_cleared_on_auth_page():
    from starlette.requests import Request

    request = Request(
        {
            "type": "http",
            "headers": [],
            "session": {"user_id": True, "unrelated": "value"},
        }
    )

    assert auth_routes._redirect_authenticated_user(request) is None
    assert request.session == {}


def test_unknown_email_and_wrong_password_use_same_generic_error(monkeypatch):
    def reject_credentials(_credentials):
        raise auth_service.InvalidCredentialsError

    monkeypatch.setattr(auth_routes, "authenticate_user", reject_credentials)
    client = TestClient(app)

    unknown_email = client.post(
        "/login",
        data={"email": "unknown@example.com", "password": "candidate-password"},
    )
    wrong_password = client.post(
        "/login",
        data={"email": "known@example.com", "password": "candidate-password"},
    )

    assert unknown_email.status_code == 200
    assert wrong_password.status_code == 200
    assert "Email or password is incorrect." in unknown_email.text
    assert "Email or password is incorrect." in wrong_password.text


def test_invalid_login_input_renders_form_error_without_authentication(monkeypatch):
    def unexpected_authentication_call(_credentials):
        raise AssertionError("Invalid input must be rejected before authentication.")

    monkeypatch.setattr(auth_routes, "authenticate_user", unexpected_authentication_call)
    client = TestClient(app)
    response = client.post(
        "/login",
        data={"email": "not-an-email", "password": "candidate-password"},
    )

    assert response.status_code == 200
    assert "Enter a valid email address and password." in response.text


def test_database_failure_is_logged_and_not_exposed(monkeypatch, caplog):
    def fail_authentication(_credentials):
        raise auth_service.AuthenticationUnavailableError from RuntimeError(
            "database secret detail"
        )

    monkeypatch.setattr(auth_routes, "authenticate_user", fail_authentication)
    response = TestClient(app).post(
        "/login",
        data={"email": "user@example.com", "password": "candidate-password"},
    )

    assert response.status_code == 503
    assert "Sign-in is temporarily unavailable." in response.text
    assert "database secret detail" not in response.text
    assert "database secret detail" in caplog.text


def test_service_verifies_werkzeug_hash_and_returns_minimal_user(monkeypatch):
    password_hash = generate_password_hash("correct-password")
    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        lambda email: {
            "id": 42,
            "name": "Finzo User",
            "email": email,
            "password_hash": password_hash,
        },
    )

    user = auth_service.authenticate_user(
        UserLogin(email=" USER@example.com ", password="correct-password")
    )

    assert user == {"id": 42, "name": "Finzo User"}
    assert "password_hash" not in user


def test_logout_requires_an_authenticated_session():
    response = TestClient(app).post("/logout", follow_redirects=False)

    assert response.status_code == 401
