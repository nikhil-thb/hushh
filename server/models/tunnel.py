"""
TunnelRecord ORM model.

Stores a persistent record for every tunnel that has ever been created.
The *live* tunnel state (WebSocket connection, pending futures) is held in
memory by :class:`server.core.tunnel_manager.TunnelManager`.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db.database import Base


class TunnelStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    TIMEOUT = "timeout"
    ERROR = "error"


class TunnelRecord(Base):
    """Persistent record of a tunnel session."""

    __tablename__ = "tunnel_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subdomain: Mapped[str] = mapped_column(String(63), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    local_port: Mapped[int] = mapped_column(Integer, nullable=False)

    # New dashboard fields
    protocol: Mapped[str] = mapped_column(String(16), default="http", nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=True) # E.g., 'localhost:3000'
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bytes_uploaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bytes_downloaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[TunnelStatus] = mapped_column(
        Enum(TunnelStatus, native_enum=False),
        default=TunnelStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    client_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Relationship
    user: Mapped[User] = relationship("User", back_populates="tunnel_records")  # type: ignore[name-defined]  # noqa: F821
    requests: Mapped[list[RequestLog]] = relationship("RequestLog", back_populates="tunnel", cascade="all, delete-orphan") # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<TunnelRecord subdomain={self.subdomain!r} status={self.status} user_id={self.user_id}>"
