"""
OTP ORM model for email verification.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db.database import Base


class OTP(Base):
    """One-Time Password record for email verification."""

    __tablename__ = "otps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # We store the hashed OTP to prevent plaintext extraction from the DB
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)  # 'register' or 'reset_password'
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<OTP id={self.id} email={self.email!r} purpose={self.purpose} verified={self.verified}>"
