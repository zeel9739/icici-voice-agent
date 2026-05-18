from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.enums import CallDirection, FundCategory, LeadStatus


# ── Request DTOs ───────────────────────────────────────────────────────────────

class LeadCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{7,14}$")
    email: EmailStr | None = None
    fund_preference: FundCategory = FundCategory.UNKNOWN
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("phone_number")
    @classmethod
    def normalise_phone(cls, v: str) -> str:
        return v.strip().replace(" ", "").replace("-", "")


class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    status: LeadStatus | None = None
    fund_preference: FundCategory | None = None
    notes: str | None = Field(default=None, max_length=2000)


# ── Response DTOs ──────────────────────────────────────────────────────────────

class LeadResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    phone_number: str
    email: str | None
    status: LeadStatus
    fund_preference: FundCategory
    call_direction: CallDirection
    notes: str | None
    livekit_room: str | None
    created_at: datetime
    updated_at: datetime


class LeadListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[LeadResponse]


class DialResponse(BaseModel):
    room_name: str
    participant_token: str
    livekit_url: str
