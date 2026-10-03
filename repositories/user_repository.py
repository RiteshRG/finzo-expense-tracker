from typing import Any, Dict, Optional

from database import execute_query


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    rows = execute_query(
        "SELECT id, name, email, password_hash FROM users WHERE email = %s LIMIT 1",
        (email,),
        fetch=True,
    )
    return rows[0] if rows else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    rows = execute_query(
        "SELECT id, name, email, created_at FROM users WHERE id = %s LIMIT 1",
        (user_id,),
        fetch=True,
    )
    return rows[0] if rows else None


def create_user(name: str, email: str, password_hash: str) -> Dict[str, Any]:
    execute_query(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        (name, email, password_hash),
        fetch=False,
    )
    return get_user_by_email(email)


__all__ = ["get_user_by_email", "get_user_by_id", "create_user"]
