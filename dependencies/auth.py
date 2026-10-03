from fastapi import HTTPException, Request, status


def get_session_user_id(request: Request) -> int | None:
    user_id = request.session.get("user_id")
    if type(user_id) is not int or user_id <= 0:
        return None
    return user_id


def get_current_user_id(request: Request) -> int:
    user_id = get_session_user_id(request)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user_id


__all__ = ["get_current_user_id", "get_session_user_id"]
