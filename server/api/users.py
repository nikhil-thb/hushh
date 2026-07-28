"""
Users admin API.

Endpoints
---------
GET  /api/users        — list all users (admin only)
POST /api/users        — create a new user (admin only)
GET  /api/users/{id}   — get user detail (admin or self)
DELETE /api/users/{id} — deactivate user (admin only)
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.api.auth import get_current_admin, get_current_user
from server.db.database import get_session
from server.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UserInfo(BaseModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool
    max_tunnels: int
    created_at: datetime


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool = False
    max_tunnels: int = 5


class CreateUserResponse(BaseModel):
    user: UserInfo
    api_key: str  # shown only once


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[UserInfo], summary="List all users (admin)")
async def list_users(
    _admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[UserInfo]:
    result = await session.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [
        UserInfo(
            id=u.id,
            email=u.email,
            is_active=u.is_active,
            is_admin=u.is_admin,
            max_tunnels=u.max_tunnels,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED, summary="Create user (admin)")
async def create_user(
    body: CreateUserRequest,
    _admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreateUserResponse:
    existing = await session.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail=f"User '{body.email}' already exists.")

    user, plain_key = User.create_with_key(
        email=body.email,
        password=body.password,
        is_admin=body.is_admin,
        max_tunnels=body.max_tunnels,
    )
    session.add(user)
    await session.flush()
    logger.info("admin.create_user", email=user.email, user_id=user.id)

    return CreateUserResponse(
        user=UserInfo(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            max_tunnels=user.max_tunnels,
            created_at=user.created_at,
        ),
        api_key=plain_key,
    )


@router.get("/{user_id}", response_model=UserInfo, summary="Get user detail")
async def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserInfo:
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden.")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return UserInfo(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_admin=user.is_admin,
        max_tunnels=user.max_tunnels,
        created_at=user.created_at,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate user (admin)")
async def deactivate_user(
    user_id: int,
    _admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot deactivate an admin user.")

    user.is_active = False
    logger.info("admin.deactivate_user", user_id=user_id)
