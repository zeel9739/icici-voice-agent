from datetime import timedelta

from livekit import api as livekit_api
from livekit.protocol import room as livekit_room_proto
from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import ROOM_PREFIX
from app.core.enums import LeadStatus
from app.core.exceptions import LiveKitError
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import DialResponse, LeadCreate, LeadListResponse, LeadResponse, LeadUpdate

_settings = get_settings()


class LeadService:
    """Orchestrates lead management and LiveKit room provisioning."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = LeadRepository(session)

    # ── CRUD ───────────────────────────────────────────────────────────────────

    async def create_lead(self, payload: LeadCreate) -> LeadResponse:
        lead = await self._repo.create(payload)
        return LeadResponse.model_validate(lead)

    async def get_lead(self, lead_id: str) -> LeadResponse:
        lead = await self._repo.get_by_id(lead_id)
        return LeadResponse.model_validate(lead)

    async def update_lead(self, lead_id: str, payload: LeadUpdate) -> LeadResponse:
        lead = await self._repo.update(lead_id, payload)
        return LeadResponse.model_validate(lead)

    async def delete_lead(self, lead_id: str) -> None:
        await self._repo.delete(lead_id)

    async def list_leads(
        self, page: int, page_size: int, status: LeadStatus | None
    ) -> LeadListResponse:
        leads, total = await self._repo.list_all(page, page_size, status)
        return LeadListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[LeadResponse.model_validate(l) for l in leads],
        )

    # ── Outbound call provisioning ─────────────────────────────────────────────

    async def dial_lead(self, lead_id: str) -> DialResponse:
        """Create a LiveKit room for the lead and return a participant token.

        The agent worker polls LiveKit for new rooms and auto-joins when a
        room matching ROOM_PREFIX is created.
        """
        lead = await self._repo.get_by_id(lead_id)

        room_name = f"{ROOM_PREFIX}{lead_id}"

        try:
            lk = livekit_api.LiveKitAPI(
                url=_settings.LIVEKIT_URL,
                api_key=_settings.LIVEKIT_API_KEY,
                api_secret=_settings.LIVEKIT_API_SECRET,
            )

            # Create the room (idempotent — OK if it already exists)
            await lk.room.create_room(
                livekit_room_proto.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=120,   # close after 2 min of silence
                    max_participants=2,
                )
            )

            # Generate a short-lived token for the human participant
            token = (
                livekit_api.AccessToken(
                    _settings.LIVEKIT_API_KEY,
                    _settings.LIVEKIT_API_SECRET,
                )
                .with_identity(f"lead-{lead_id}")
                .with_name(lead.name)
                .with_grants(
                    livekit_api.VideoGrants(
                        room_join=True,
                        room=room_name,
                        can_publish=True,
                        can_subscribe=True,
                    )
                )
                .with_ttl(timedelta(minutes=30))
                .to_jwt()
            )

            # Dispatch the agent worker into the room, passing lead name as metadata
            await lk.agent_dispatch.create_dispatch(
                CreateAgentDispatchRequest(
                    room=room_name,
                    agent_name="icici-lead-qualifier",
                    metadata=lead.name,
                )
            )

            await lk.aclose()
        except Exception as exc:
            raise LiveKitError(f"Failed to provision room: {exc}") from exc

        await self._repo.set_room(lead_id, room_name)
        return DialResponse(
            room_name=room_name,
            participant_token=token,
            livekit_url=_settings.LIVEKIT_URL,
        )
