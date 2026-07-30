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
import random
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
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
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RequestOTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "register"


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    purpose: str = "register"


class VerifyOTPResponse(BaseModel):
    verification_token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    verification_token: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str
    verification_token: str


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
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
    x_api_key: Annotated[str | None, Depends(_api_key_header)] = None,
) -> User:
    token_or_key = x_api_key or (credentials.credentials if credentials else None)
    if not token_or_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    # Try JWT decoding
    try:
        user_id = await _decode_token(token_or_key, settings)
        result = await session.execute(select(User).where(User.id == user_id, User.is_active == True))  # noqa: E712
        user = result.scalar_one_or_none()
        if user is not None:
            return user
    except HTTPException:
        pass  # Fall through to API key check

    # Try API key check
    result = await session.execute(select(User).where(User.is_active == True))  # noqa: E712
    users = result.scalars().all()
    for user in users:
        if user.verify_api_key(token_or_key):
            return user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or API key.")


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


from server.core.email import send_otp_email
from server.core.otp import (
    create_and_store_otp,
    decode_verification_token,
    generate_verification_token,
    verify_otp_code,
)

@router.post("/request-otp", summary="Request an OTP via email")
async def request_otp(
    body: RequestOTPRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    if body.purpose not in ("register", "reset_password"):
        raise HTTPException(status_code=400, detail="Invalid purpose.")
        
    # Check if email already exists for registration
    existing = await session.execute(select(User).where(User.email == body.email))
    user_exists = existing.scalar_one_or_none() is not None
    
    if body.purpose == "register" and user_exists:
        raise HTTPException(status_code=400, detail="Email already registered.")
        
    # Generate and store OTP
    plain_otp = await create_and_store_otp(session, body.email, body.purpose)
    
    # Send email
    send_otp_email(body.email, plain_otp, body.purpose)
    
    return {"message": "OTP sent successfully."}


@router.post("/verify-otp", response_model=VerifyOTPResponse, summary="Verify an OTP")
async def verify_otp(
    body: VerifyOTPRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> VerifyOTPResponse:
    is_valid = await verify_otp_code(session, body.email, body.otp, body.purpose)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
        
    token = generate_verification_token(body.email, body.purpose)
    return VerifyOTPResponse(verification_token=token)


@router.post("/register", response_model=LoginResponse, summary="Register a new account")
async def register(
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    """Create a new user and return a JWT access token and an API key."""
    # Verify the OTP token
    verified_email = decode_verification_token(body.verification_token, "register")
    if verified_email != body.email:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")

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


@router.post("/reset-password", summary="Reset a user's password")
async def reset_password(
    body: ResetPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    """Reset a user's password using an OTP verification token."""
    verified_email = decode_verification_token(body.verification_token, "reset_password")
    if verified_email != body.email:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
        
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    user.set_password(body.new_password)
    await session.commit()
    logger.info("auth.reset_password", user_id=user.id, email=user.email)
    
    return {"message": "Password reset successfully."}


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
