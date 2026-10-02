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
from schemas import UserLogin
import services.auth_service as auth_service


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
    assert response.headers["location"] == "/"
    assert "session=" in response.headers["set-cookie"]

    authenticated_page = client.get("/")
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

    def unexpected_auth_call(*_args, **_kwargs):
        raise AssertionError("Authenticated users should be redirected before auth logic runs.")

    monkeypatch.setattr(auth_routes, "authenticate_user", unexpected_auth_call)
    monkeypatch.setattr(auth_routes, "register_user", unexpected_auth_call)
    request = getattr(client, method)
    response = request(path, data=form_data, follow_redirects=False) if form_data else request(
        path, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"

    # The redirect must not clear or replace the user's authenticated session.
    assert "Sign out" in client.get("/").text


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
