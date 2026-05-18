import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import CallDirection, FundCategory, LeadStatus
from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(120))
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)

    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.PENDING, index=True
    )
    fund_preference: Mapped[FundCategory] = mapped_column(
        Enum(FundCategory), default=FundCategory.UNKNOWN
    )
    call_direction: Mapped[CallDirection] = mapped_column(
        Enum(CallDirection), default=CallDirection.OUTBOUND
    )

    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    livekit_room: Mapped[str | None] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Lead id={self.id} name={self.name!r} status={self.status}>"
