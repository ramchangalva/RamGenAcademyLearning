"""
Dependencies for API routes
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from typing import Optional

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Authenticate via session cookie and/or Bearer token.

    Cookie is tried first (canonical for form login + HttpOnly sessions). If an invalid
    ``Authorization: Bearer`` header is present—e.g. from an extension or stale client
    value—the valid cookie must still authenticate; previously Bearer was preferred and
    caused false 401s and frontend redirects to login.
    """
    tokens_to_try = []
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        tokens_to_try.append(cookie_token)
    if credentials and credentials.credentials:
        if credentials.credentials not in tokens_to_try:
            tokens_to_try.append(credentials.credentials)

    if not tokens_to_try:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_headers = {"WWW-Authenticate": "Bearer"}

    for token in tokens_to_try:
        payload = decode_access_token(token)
        if payload is None:
            continue

        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            continue

        try:
            user_id = int(user_id_raw)
        except (ValueError, TypeError):
            continue

        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            continue

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers=auth_headers,
    )
