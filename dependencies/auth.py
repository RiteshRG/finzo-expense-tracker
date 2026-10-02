from fastapi import HTTPException, Request, status


def get_current_user_id(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int) or user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user_id


__all__ = ["get_current_user_id"]