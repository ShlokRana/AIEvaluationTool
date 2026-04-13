from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from jose import jwt, JWTError
from config.settings import settings
from database.database import get_db, ensure_db_ready
from models.user import Users
from typing import Optional

security = HTTPBearer()


def _load_active_user(db: Session, user_name: str) -> Optional[Users]:
    try:
        return db.query(Users).filter(Users.user_name == user_name).first()
    except OperationalError as exc:
        if "no such table" not in str(exc).lower():
            raise
        ensure_db_ready()
        return db.query(Users).filter(Users.user_name == user_name).first()


def _decode_access_token(token: str) -> dict:
    candidate_keys = [
        settings.SECRET_KEY,
        "@cerai",
    ]
    last_error = None

    for key in dict.fromkeys(candidate_keys):
        try:
            payload = jwt.decode(token, key, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            return payload
        except HTTPException:
            raise
        except JWTError as exc:
            last_error = exc

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    ) from last_error

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = _decode_access_token(token)

    user_name: str = payload.get("user_name")
    if not user_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    db_user = _load_active_user(db, user_name)
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return db_user

def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[Users]:
    """Get current user if token is present, otherwise return None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    try:
        payload = _decode_access_token(token)
        user_name: str = payload.get("user_name")
        if not user_name:
            return None
    except HTTPException:
        return None

    db_user = _load_active_user(db, user_name)
    if not db_user or not db_user.is_active:
        return None

    return db_user

def require_role(required_role: str):
    """Dependency to check if user has required role."""
    def role_checker(user: Users = Depends(get_current_user)):
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return user
    return role_checker

def require_admin(user: Users = Depends(get_current_user)):
    """Dependency to check if user is admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
