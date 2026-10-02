from typing import Any, Dict

from werkzeug.security import generate_password_hash

from repositories.user_repository import create_user, get_user_by_email
from schemas import UserRegistration


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def register_user(payload: UserRegistration) -> Dict[str, Any]:
    normalized = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    normalized["name"] = normalized["name"].strip()
    normalized["email"] = normalized["email"].strip().lower()

    try:
        existing_user = get_user_by_email(normalized["email"])
        if existing_user:
            raise ValueError("An account with this email already exists.")

        password_hash = hash_password(normalized["password"])
        user = create_user(
            name=normalized["name"],
            email=normalized["email"],
            password_hash=password_hash,
        )
        return user
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Unable to process registration at this time. Please try again later.") from exc


__all__ = ["register_user", "hash_password"]
