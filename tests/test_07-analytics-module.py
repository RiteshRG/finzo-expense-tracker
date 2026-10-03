import os

os.environ.setdefault(
    "SESSION_SECRET_KEY",
    "test-only-session-secret-key-32chars",
)

from fastapi.testclient import TestClient
import pytest
from starlette.requests import Request

from app import app
import routes.analytics as analytics_routes
import routes.auth as auth_routes


def _authenticated_client(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda _credentials: {"id": 7, "name": "Finzo User"},
    )
    client = TestClient(app)
    response = client.post(
        "/login",
        data={"email": "user@example.com", "password": "password"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return client


def test_anonymous_analytics_page_redirects_to_login():
    response = TestClient(app).get("/analytics", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_analytics_is_not_shown_in_logged_out_navigation():
    response = TestClient(app).get("/login")

    assert response.status_code == 200
    assert "Analytics" not in response.text


def test_authenticated_analytics_page_renders_coming_soon_design(monkeypatch):
    client = _authenticated_client(monkeypatch)

    response = client.get("/analytics")

    assert response.status_code == 200
    assert "Advanced Analytics" in response.text
    assert "Coming Soon" in response.text
    assert "powerful insights and visualisations" in response.text
    assert "spending patterns better" in response.text
    assert "We're crafting something special" in response.text
    assert 'class="analytics-icon" aria-hidden="true"' in response.text
    assert 'class="analytics-dots" aria-hidden="true"' in response.text


def test_authenticated_navigation_links_to_analytics_and_marks_it_current(
    monkeypatch,
):
    client = _authenticated_client(monkeypatch)

    response = client.get("/analytics")

    assert response.status_code == 200
    assert 'href="http://testserver/analytics"' in response.text
    assert 'class="nav-analytics-link is-active"' in response.text
    assert 'aria-current="page"' in response.text


@pytest.mark.parametrize("user_id", [True, 0, -1, "7", 7.0])
def test_analytics_clears_malformed_session_and_redirects(user_id):
    request = Request(
        {
            "type": "http",
            "headers": [],
            "session": {"user_id": user_id, "unrelated": "value"},
        }
    )

    response = analytics_routes.analytics(request)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert request.session == {}
