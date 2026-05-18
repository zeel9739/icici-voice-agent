from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import LeadStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate


class LeadRepository:
    """Data-access layer for Lead entities.

    All methods are async and take an explicit session so callers control
    transaction boundaries (no ambient session magic).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Queries ────────────────────────────────────────────────────────────────

    async def get_by_id(self, lead_id: str) -> Lead:
        lead = await self._session.get(Lead, lead_id)
        if lead is None:
            raise NotFoundError(f"Lead {lead_id!r} not found.")
        return lead

    async def get_by_phone(self, phone_number: str) -> Lead | None:
        stmt = select(Lead).where(Lead.phone_number == phone_number)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: LeadStatus | None = None,
    ) -> tuple[list[Lead], int]:
        stmt = select(Lead)
        count_stmt = select(func.count()).select_from(Lead)

        if status is not None:
            stmt = stmt.where(Lead.status == status)
            count_stmt = count_stmt.where(Lead.status == status)

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        total = (await self._session.execute(count_stmt)).scalar_one()
        leads = (await self._session.execute(stmt)).scalars().all()
        return list(leads), total

    # ── Commands ───────────────────────────────────────────────────────────────

    async def create(self, payload: LeadCreate) -> Lead:
        if await self.get_by_phone(payload.phone_number):
            raise ConflictError(
                f"Lead with phone {payload.phone_number!r} already exists."
            )
        lead = Lead(**payload.model_dump())
        self._session.add(lead)
        await self._session.flush()  # populate generated fields (id, created_at)
        await self._session.refresh(lead)
        return lead

    async def update(self, lead_id: str, payload: LeadUpdate) -> Lead:
        lead = await self.get_by_id(lead_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(lead, field, value)
        await self._session.flush()
        await self._session.refresh(lead)
        return lead

    async def set_room(self, lead_id: str, room_name: str) -> Lead:
        lead = await self.get_by_id(lead_id)
        lead.livekit_room = room_name
        await self._session.flush()
        await self._session.refresh(lead)
        return lead

    async def delete(self, lead_id: str) -> None:
        lead = await self.get_by_id(lead_id)
        await self._session.delete(lead)
        await self._session.flush()
