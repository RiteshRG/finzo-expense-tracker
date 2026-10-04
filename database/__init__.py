import os
from urllib.parse import ParseResult, urlparse

import pymysql

from .models import EXPENSE_TABLE_SQL, USER_TABLE_SQL
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def _get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set to a MySQL connection URL.")
    return database_url


def _parse_database_url() -> ParseResult:
    try:
        parsed = urlparse(_get_database_url())
    except ValueError as exc:
        raise RuntimeError("DATABASE_URL is not a valid MySQL connection URL.") from exc
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise RuntimeError("DATABASE_URL must use a MySQL PyMySQL URL.")
    if not parsed.hostname or not parsed.path.lstrip("/"):
        raise RuntimeError("DATABASE_URL must include a MySQL host and database name.")
    try:
        parsed.port
    except ValueError as exc:
        raise RuntimeError("DATABASE_URL must contain a valid MySQL port.") from exc
    return parsed


def validate_database_config() -> None:
    _parse_database_url()


def _get_connection_config(include_database: bool = True):
    parsed = _parse_database_url()

    config = {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": parsed.username or "",
        "password": parsed.password or "",
        "charset": "utf8mb4",
        "autocommit": False,
        "cursorclass": pymysql.cursors.DictCursor,
        "connect_timeout": 30,
    }
    if include_database:
        config["database"] = parsed.path.lstrip("/") or ""
    return config


def get_connection():
    config = _get_connection_config(include_database=False)
    database_name = _parse_database_url().path.lstrip("/")

    connection = pymysql.connect(**config)
    if database_name:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.select_db(database_name)
    with connection.cursor() as cursor:
        cursor.execute("SET time_zone = '+00:00'")
    return connection


def check_database_connection() -> None:
    connection = pymysql.connect(**_get_connection_config())
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    finally:
        connection.close()


def get_db():
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()


def execute_query(
    query: str,
    params=None,
    fetch: bool = False,
    return_rowcount: bool = False,
):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            connection.commit()
            if return_rowcount:
                return cursor.rowcount
            return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def ensure_user_name_column():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM users LIKE 'name'")
            exists = cursor.fetchone()
        if not exists:
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE users ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT '' AFTER id")
            connection.commit()
    finally:
        connection.close()


def init_db():
    try:
        execute_query(USER_TABLE_SQL)
        ensure_user_name_column()
        execute_query(EXPENSE_TABLE_SQL)
    except Exception as exc:  # pragma: no cover - surfaced during setup
        raise RuntimeError(f"Database initialization failed: {exc}") from exc


def seed_db():
    demo_name = "Demo User"
    demo_email = "demo@finzo.local"
    demo_password = "demo-password-hash"
    sample_expenses = [
        {"title": "Groceries", "amount": 42.5, "category": "Food", "description": "Weekly grocery run"},
        {"title": "Transport", "amount": 18.0, "category": "Travel", "description": "Commuter pass"},
        {"title": "Electricity", "amount": 65.25, "category": "Bills", "description": "Monthly utility bill"},
        {"title": "Coffee", "amount": 9.75, "category": "Food", "description": "Office coffee"},
        {"title": "Movie Night", "amount": 24.0, "category": "Entertainment", "description": "Weekend movie tickets"},
        {"title": "Gym", "amount": 30.0, "category": "Health", "description": "Monthly membership"},
        {"title": "Internet", "amount": 50.0, "category": "Bills", "description": "Home internet service"},
        {"title": "Books", "amount": 16.5, "category": "Education", "description": "Learning materials"},
    ]

    try:
        user = execute_query(
            "SELECT id FROM users WHERE email = %s LIMIT 1",
            (demo_email,),
            fetch=True,
        )
        if not user:
            user_id = execute_query(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                (demo_name, demo_email, demo_password),
                fetch=False,
            )
        else:
            user_id = user[0]["id"]

        for expense in sample_expenses:
            existing = execute_query(
                "SELECT id FROM expenses WHERE user_id = %s AND title = %s LIMIT 1",
                (user_id, expense["title"]),
                fetch=True,
            )
            if not existing:
                execute_query(
                    """
                    INSERT INTO expenses (user_id, title, amount, category, description)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        expense["title"],
                        expense["amount"],
                        expense["category"],
                        expense["description"],
                    ),
                    fetch=False,
                )
    except Exception as exc:
        raise RuntimeError(f"Database seeding failed: {exc}") from exc


__all__ = [
    "DATABASE_URL",
    "check_database_connection",
    "get_connection",
    "get_db",
    "execute_query",
    "init_db",
    "seed_db",
    "validate_database_config",
]
