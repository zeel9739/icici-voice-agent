import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import LeadStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadCreate, LeadUpdate


def _make_payload(**overrides) -> LeadCreate:
    defaults = {
        "name": "Anita Shah",
        "phone_number": "+919123456789",
        "fund_preference": "hybrid",
    }
    return LeadCreate(**{**defaults, **overrides})


@pytest.mark.asyncio
async def test_create_and_fetch(db_session: AsyncSession):
    repo = LeadRepository(db_session)
    lead = await repo.create(_make_payload())
    fetched = await repo.get_by_id(lead.id)
    assert fetched.id == lead.id
    assert fetched.name == "Anita Shah"


@pytest.mark.asyncio
async def test_create_duplicate_raises_conflict(db_session: AsyncSession):
    repo = LeadRepository(db_session)
    payload = _make_payload(phone_number="+919000000001")
    await repo.create(payload)
    with pytest.raises(ConflictError):
        await repo.create(payload)


@pytest.mark.asyncio
async def test_get_nonexistent_raises_not_found(db_session: AsyncSession):
    repo = LeadRepository(db_session)
    with pytest.raises(NotFoundError):
        await repo.get_by_id("00000000-0000-0000-0000-000000000000")


@pytest.mark.asyncio
async def test_update_status(db_session: AsyncSession):
    repo = LeadRepository(db_session)
    lead = await repo.create(_make_payload(phone_number="+919000000002"))
    updated = await repo.update(lead.id, LeadUpdate(status=LeadStatus.INTERESTED))
    assert updated.status == LeadStatus.INTERESTED


@pytest.mark.asyncio
async def test_list_pagination(db_session: AsyncSession):
    repo = LeadRepository(db_session)
    for i in range(5):
        await repo.create(_make_payload(phone_number=f"+9190000{i:05d}"))

    leads, total = await repo.list_all(page=1, page_size=3)
    assert len(leads) <= 3
    assert total >= 5


@pytest.mark.asyncio
async def test_delete(db_session: AsyncSession):
    repo = LeadRepository(db_session)
    lead = await repo.create(_make_payload(phone_number="+919000000099"))
    await repo.delete(lead.id)
    with pytest.raises(NotFoundError):
        await repo.get_by_id(lead.id)
