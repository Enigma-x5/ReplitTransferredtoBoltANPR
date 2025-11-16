import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    license_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    node_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    camera_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<License {self.customer_id}>"


class UsageReport(Base):
    __tablename__ = "usage_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    node_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    camera_count: Mapped[int] = mapped_column(Integer, nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<UsageReport {self.node_id} - {self.reported_at}>"
