"""
User ORM model and related helpers.

Users authenticate with an API key (hashed with bcrypt).
The plain-text key is shown only once at creation time.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from passlib.context import CryptContext
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db.database import Base

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _generate_api_key() -> str:
    """Generate a secure random API key with prefix ``hushh_``."""
    return f"hushh_{secrets.token_urlsafe(32)}"


class User(Base):
    """Hushh Tunnel user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_tunnels: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    tunnel_records: Mapped[list["TunnelRecord"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "TunnelRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # ── Password helpers ──────────────────────────────────────────────────

    def set_password(self, plain: str) -> None:
        self.hashed_password = _pwd_ctx.hash(plain)

    def verify_password(self, plain: str) -> bool:
        return _pwd_ctx.verify(plain, self.hashed_password)

    # ── API key helpers ───────────────────────────────────────────────────

    @classmethod
    def create_with_key(
        cls,
        email: str,
        password: str,
        *,
        is_admin: bool = False,
        max_tunnels: int = 5,
    ) -> tuple["User", str]:
        """
        Create a new user and return ``(user, plain_api_key)``.

        The plain key is NOT stored — only its hash is persisted.
        """
        plain_key = _generate_api_key()
        user = cls(
            email=email,
            api_key_hash=_pwd_ctx.hash(plain_key),
            is_admin=is_admin,
            max_tunnels=max_tunnels,
        )
        user.set_password(password)
        return user, plain_key

    def verify_api_key(self, plain_key: str) -> bool:
        return _pwd_ctx.verify(plain_key, self.api_key_hash)

    def rotate_api_key(self) -> str:
        """Generate a new API key, update the hash, and return the plain key."""
        plain_key = _generate_api_key()
        self.api_key_hash = _pwd_ctx.hash(plain_key)
        self.updated_at = datetime.now(UTC)
        return plain_key

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} admin={self.is_admin}>"
