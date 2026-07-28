"""
Authentication API and dependency helpers.

Endpoints
---------
POST  /auth/login    — email + password → JWT access token + API key
POST  /auth/logout   — client-side only (stateless JWT; token blacklist is future work)
GET   /auth/whoami   — return current user info
POST  /auth/rotate   — regenerate API key

Dependency
----------
``get_current_user`` — validates the ``Authorization: Bearer <token>`` header and
returns the authenticated :class:`~server.models.user.User`.

``get_current_admin`` — same, but also asserts ``is_admin=True``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.config import Settings, get_settings
from server.core.metrics import AUTH_FAILURE_TOTAL, AUTH_SUCCESS_TOTAL
from server.db.database import get_session
from server.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    api_key: str
    email: str


class WhoAmIResponse(BaseModel):
    id: int
    email: str
    is_admin: bool
    max_tunnels: int
    created_at: datetime


class RotateKeyResponse(BaseModel):
    api_key: str


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _create_access_token(user_id: int, settings: Settings) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)  # type: ignore[return-value]


async def _decode_token(token: str, settings: Settings) -> int:
    """Return user_id from a valid JWT, raise HTTPException otherwise."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
        return int(user_id_str)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    user_id = await _decode_token(credentials.credentials, settings)
    result = await session.execute(select(User).where(User.id == user_id, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=LoginResponse, summary="Register a new account")
async def register(
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    """Create a new user and return a JWT access token and an API key."""
    # Check if email already exists
    existing = await session.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    user, plain_key = User.create_with_key(
        email=body.email,
        password=body.password,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = _create_access_token(user.id, settings)
    logger.info("auth.register", user_id=user.id, email=user.email)

    return LoginResponse(
        access_token=token,
        api_key=plain_key,
        email=user.email,
    )


@router.post("/login", response_model=LoginResponse, summary="Authenticate and get tokens")
async def login(
    body: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    """Exchange email + password for a JWT access token and an API key."""
    result = await session.execute(select(User).where(User.email == body.email, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()

    if user is None or not user.verify_password(body.password):
        AUTH_FAILURE_TOTAL.labels(method="password").inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    # Rotate API key on each login so the user always gets the current key.
    # The plain-text key is returned here and stored client-side.
    plain_key = user.rotate_api_key()
    await session.commit()

    token = _create_access_token(user.id, settings)
    AUTH_SUCCESS_TOTAL.labels(method="password").inc()
    logger.info("auth.login", user_id=user.id, email=user.email)

    return LoginResponse(
        access_token=token,
        api_key=plain_key,
        email=user.email,
    )


@router.post("/logout", summary="Logout (client-side token discard)")
async def logout() -> dict[str, str]:
    """
    Stateless logout — the client should discard its local token and API key.

    Future: token blocklist for immediate invalidation.
    """
    return {"message": "Logged out. Delete your local token and API key."}


@router.get("/whoami", response_model=WhoAmIResponse, summary="Return current user info")
async def whoami(
    user: Annotated[User, Depends(get_current_user)],
) -> WhoAmIResponse:
    return WhoAmIResponse(
        id=user.id,
        email=user.email,
        is_admin=user.is_admin,
        max_tunnels=user.max_tunnels,
        created_at=user.created_at,
    )


@router.post("/rotate", response_model=RotateKeyResponse, summary="Rotate API key")
async def rotate_api_key(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RotateKeyResponse:
    """Generate a new API key.  The old key is immediately invalidated."""
    plain_key = user.rotate_api_key()
    await session.commit()
    logger.info("auth.rotate_key", user_id=user.id)
    return RotateKeyResponse(api_key=plain_key)
