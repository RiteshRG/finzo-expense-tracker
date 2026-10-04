import os
from pathlib import Path
from unittest.mock import MagicMock, Mock

os.environ.setdefault("DATABASE_URL", "mysql+pymysql://user:password@127.0.0.1:3306/finzo_test")
os.environ.setdefault(
    "SESSION_SECRET_KEY",
    "test-only-session-secret-key-32chars",
)

from fastapi.testclient import TestClient
import pytest

import app as app_module
import database as database_module


def test_health_returns_ok_when_database_is_available(monkeypatch):
    check = Mock()
    monkeypatch.setattr(app_module, "check_database_connection", check)

    response = TestClient(app_module.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    check.assert_called_once_with()


def test_health_returns_generic_unavailable_response_when_database_fails(
    monkeypatch, caplog
):
    monkeypatch.setattr(
        app_module,
        "check_database_connection",
        Mock(side_effect=RuntimeError("private database details")),
    )

    response = TestClient(app_module.app).get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "private database details" not in response.text
    assert "Application health check failed." in caplog.text


def test_database_health_check_runs_query_and_closes_connection(monkeypatch):
    connection = Mock()
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    connection.cursor.return_value = cursor
    connect = Mock(return_value=connection)
    monkeypatch.setattr(database_module.pymysql, "connect", connect)
    monkeypatch.setenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@db.example.test:3307/finzo",
    )

    database_module.check_database_connection()

    connect.assert_called_once()
    assert connect.call_args.kwargs["host"] == "db.example.test"
    assert connect.call_args.kwargs["port"] == 3307
    assert connect.call_args.kwargs["database"] == "finzo"
    cursor.execute.assert_called_once_with("SELECT 1")
    connection.close.assert_called_once_with()


def test_database_health_check_closes_connection_when_query_fails(monkeypatch):
    connection = Mock()
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    connection.cursor.return_value = cursor
    cursor.execute.side_effect = RuntimeError("query failed")
    monkeypatch.setattr(
        database_module.pymysql,
        "connect",
        Mock(return_value=connection),
    )
    monkeypatch.setenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@127.0.0.1:3306/finzo",
    )

    with pytest.raises(RuntimeError, match="query failed"):
        database_module.check_database_connection()

    connection.close.assert_called_once_with()


def test_startup_rejects_missing_database_configuration(monkeypatch, caplog):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
        app_module.startup_event()

    assert "Application startup checks failed." in caplog.text


def test_startup_rejects_invalid_database_port(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@127.0.0.1:invalid/finzo",
    )

    with pytest.raises(RuntimeError, match="valid MySQL port"):
        app_module.startup_event()


def test_startup_rejects_missing_or_short_session_secret(monkeypatch):
    monkeypatch.delenv("SESSION_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SESSION_SECRET_KEY must be set"):
        app_module._get_session_secret()

    monkeypatch.setenv("SESSION_SECRET_KEY", "too-short")
    with pytest.raises(RuntimeError, match="SESSION_SECRET_KEY must be set"):
        app_module._get_session_secret()


def test_production_startup_validates_config_without_initializing_or_seeding(
    monkeypatch,
):
    validate = Mock()
    init_db = Mock()
    seed_db = Mock()
    monkeypatch.setattr(app_module, "validate_database_config", validate)
    monkeypatch.setattr(app_module, "init_db", init_db)
    monkeypatch.setattr(app_module, "seed_db", seed_db)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SEED_DEMO_DATA", "true")

    app_module.startup_event()

    validate.assert_called_once_with()
    init_db.assert_not_called()
    seed_db.assert_not_called()


def test_development_startup_initializes_schema_but_only_seeds_on_opt_in(
    monkeypatch,
):
    validate = Mock()
    init_db = Mock()
    seed_db = Mock()
    monkeypatch.setattr(app_module, "validate_database_config", validate)
    monkeypatch.setattr(app_module, "init_db", init_db)
    monkeypatch.setattr(app_module, "seed_db", seed_db)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")

    app_module.startup_event()

    validate.assert_called_once_with()
    init_db.assert_called_once_with()
    seed_db.assert_not_called()

    monkeypatch.setenv("SEED_DEMO_DATA", "true")
    app_module.startup_event()
    assert init_db.call_count == 2
    seed_db.assert_called_once_with()


def test_startup_initialization_failure_is_logged_and_propagated(
    monkeypatch, caplog
):
    monkeypatch.setattr(app_module, "validate_database_config", Mock())
    monkeypatch.setattr(
        app_module,
        "init_db",
        Mock(side_effect=RuntimeError("schema setup failed")),
    )
    monkeypatch.setenv("APP_ENV", "development")

    with pytest.raises(RuntimeError, match="schema setup failed"):
        app_module.startup_event()

    assert "Application startup checks failed." in caplog.text


def test_docker_image_uses_runtime_port_non_root_user_and_safe_build_context():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in dockerfile
    assert "USER finzo" in dockerfile
    assert "PORT=8000" in dockerfile
    assert "--host 0.0.0.0" in dockerfile
    assert r'--port \"${PORT:-8000}\"' in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "COPY . " not in dockerfile
    assert ".env" in dockerignore
    assert ".env.*" in dockerignore
    assert ".git" in dockerignore
    assert ".venv" in dockerignore
    assert "venv" in dockerignore
    assert "__pycache__" in dockerignore
    assert ".pytest_cache" in dockerignore
