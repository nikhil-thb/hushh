"""
Request Log ORM model.

Stores request history for each tunnel.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db.database import Base


class RequestLog(Base):
    """Persistent log of an HTTP request through a tunnel."""

    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tunnel_id: Mapped[int] = mapped_column(Integer, ForeignKey("tunnel_records.id", ondelete="CASCADE"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationship
    tunnel: Mapped[TunnelRecord] = relationship("TunnelRecord", back_populates="requests")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<RequestLog id={self.id} method={self.method} status={self.status} tunnel_id={self.tunnel_id}>"
