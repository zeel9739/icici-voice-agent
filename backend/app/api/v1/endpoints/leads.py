from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import LeadStatus
from app.db.session import get_db
from app.schemas.lead import (
    DialResponse,
    LeadCreate,
    LeadListResponse,
    LeadResponse,
    LeadUpdate,
)
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])


def _service(db: AsyncSession = Depends(get_db)) -> LeadService:
    return LeadService(db)


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreate,
    svc: LeadService = Depends(_service),
) -> LeadResponse:
    return await svc.create_lead(payload)


@router.get("", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: LeadStatus | None = Query(default=None),
    svc: LeadService = Depends(_service),
) -> LeadListResponse:
    return await svc.list_leads(page, page_size, status)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    svc: LeadService = Depends(_service),
) -> LeadResponse:
    return await svc.get_lead(lead_id)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    svc: LeadService = Depends(_service),
) -> LeadResponse:
    return await svc.update_lead(lead_id, payload)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: str,
    svc: LeadService = Depends(_service),
) -> None:
    await svc.delete_lead(lead_id)


@router.post("/{lead_id}/dial", response_model=DialResponse)
async def dial_lead(
    lead_id: str,
    svc: LeadService = Depends(_service),
) -> DialResponse:
    """Provision a LiveKit room and return a join token for the lead.

    The agent worker auto-joins the room; share the token + livekit_url
    with the customer via SMS/email so they can join from the browser.
    """
    return await svc.dial_lead(lead_id)
