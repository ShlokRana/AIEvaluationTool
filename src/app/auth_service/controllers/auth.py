from sqlalchemy.orm import Session
from models.user import User
from schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, LogoutRequest
from utils.auth import hash_password, verify_password, create_access_token, create_refresh_token, verify_refresh_token
# get_user_by_username,
from fastapi import HTTPException, status
from typing import Dict
import logging

# In-memory storage for refresh tokens (in production, use Redis or database)
refresh_token_store: Dict[str, str] = {}
logger = logging.getLogger(__name__)


def _normalize_role(role) -> str:
    if isinstance(role, str):
        return role
    for attr in ("value", "code", "name"):
        value = getattr(role, attr, None)
        if isinstance(value, str):
            return value
    return str(role)

def authenticate_user(db: Session, user: LoginRequest):
    db_user = get_user_by_username(db, user.user_name)
    if not db_user:
        logger.warning("AuthService: login failed, user not found (user_name=%s)", user.user_name)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not verify_password(user.password, db_user.password):
        logger.warning("AuthService: login failed, bad password (user_name=%s)", user.user_name)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not db_user.is_active:
        logger.warning("AuthService: login failed, user deactivated (user_name=%s)", user.user_name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )

    return db_user

def login(db: Session, user: LoginRequest) -> TokenResponse:
    db_user = authenticate_user(db, user)
    role = _normalize_role(db_user.role)

    token_data = {
        "user_name": db_user.user_name,
        "role": role,
        "user_id": db_user.user_id
    }

    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    # Store refresh token
    refresh_token_store[refresh_token] = db_user.user_name

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_name=db_user.user_name,
        role=role
    )

def refresh_access_token(db: Session, token_data: RefreshTokenRequest):
    try:
        payload = verify_refresh_token(token_data.refresh_token)
        user_name = payload.get("user_name")

        if not user_name:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Check if refresh token is in store
        if token_data.refresh_token not in refresh_token_store:
            raise HTTPException(status_code=401, detail="Refresh token not found or revoked")

        # Verify user still exists
        db_user = get_user_by_username(db, user_name)
        if not db_user or not db_user.is_active:
            raise HTTPException(status_code=401, detail="User not found or deactivated")
        role = _normalize_role(db_user.role)

        # Generate new tokens
        token_data_dict = {
            "user_name": db_user.user_name,
            "role": role,
            "user_id": db_user.user_id
        }
        new_access_token = create_access_token(data=token_data_dict)
        new_refresh_token = create_refresh_token(data=token_data_dict)

        # Remove old refresh token and store new one
        del refresh_token_store[token_data.refresh_token]
        refresh_token_store[new_refresh_token] = db_user.user_name

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user_name=db_user.user_name,
            role=role
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def logout(token_data: LogoutRequest):
    if token_data.refresh_token in refresh_token_store:
        del refresh_token_store[token_data.refresh_token]
        return {"message": "Successfully logged out"}
    return {"message": "Token not found"}

def get_user_by_username(db: Session, user_name: str):
    return db.query(User).filter(User.user_name == user_name).first()
