from typing import Any, Dict

from werkzeug.security import check_password_hash, generate_password_hash

from repositories.user_repository import create_user, get_user_by_email
from schemas import UserLogin, UserRegistration


class InvalidCredentialsError(Exception):
    pass


class AuthenticationUnavailableError(Exception):
    pass


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


def authenticate_user(payload: UserLogin) -> Dict[str, Any]:
    email = payload.email.strip().lower()
    try:
        user = get_user_by_email(email)
    except Exception as exc:
        raise AuthenticationUnavailableError from exc

    if not user:
        raise InvalidCredentialsError

    try:
        password_matches = check_password_hash(user["password_hash"], payload.password)
    except (TypeError, ValueError) as exc:
        raise InvalidCredentialsError from exc

    if not password_matches:
        raise InvalidCredentialsError

    return {"id": user["id"], "name": user["name"]}


__all__ = [
    "register_user",
    "hash_password",
    "authenticate_user",
    "InvalidCredentialsError",
    "AuthenticationUnavailableError",
]
