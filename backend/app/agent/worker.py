"""LiveKit Voice Agent worker — livekit-agents 1.x

Pipeline (optimised for <800 ms end-to-end latency):
  Microphone → Silero VAD → Deepgram nova-2-phonecall STT
             → Noise filter (llm_node override)
             → Groq Llama-3 8B LLM
             → Cartesia TTS → Speaker

Run with:
    poetry run python -m app.agent.worker start
"""

import logging
from collections.abc import AsyncGenerator

from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.agents import llm as agents_llm
from livekit.agents.voice.agent import ModelSettings
from livekit.agents.voice.room_io.types import RoomOptions
from livekit.plugins import cartesia, deepgram, groq, silero

from app.agent.prompts import GREETING_TEMPLATE, SYSTEM_PROMPT
from app.core.config import get_settings
from app.core.constants import (
    DEEPGRAM_ENDPOINTING_MS,
    DEEPGRAM_MODEL,
    ROOM_PREFIX,
    VAD_ACTIVATION_THRESHOLD,
    VAD_MIN_SILENCE_DURATION,
    VAD_MIN_SPEECH_DURATION,
)

logger = logging.getLogger(__name__)
_settings = get_settings()


def _is_noise(text: str) -> bool:
    """Return True when a transcript is likely background noise or a false trigger."""
    words = text.strip().split()
    if len(words) < _settings.MIN_TRANSCRIPT_WORDS:
        return True
    fillers = {"um", "uh", "hmm", "hm", "ah", "oh", "er", "ugh"}
    if all(w.lower().strip(".,!?") in fillers for w in words):
        return True
    return False


class LeadQualifierAgent(Agent):
    """Voice agent that qualifies ICICI Prudential AMC leads."""

    def __init__(self, lead_name: str, lead_id: str) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._lead_name = lead_name
        self._lead_id = lead_id

    async def on_enter(self) -> None:
        """Greet the lead as soon as they join the room."""
        greeting = GREETING_TEMPLATE.format(name=self._lead_name)
        await self.session.say(greeting, allow_interruptions=False)

    async def llm_node(
        self,
        chat_ctx: agents_llm.ChatContext,
        tools: list,
        model_settings: ModelSettings,
    ) -> AsyncGenerator[agents_llm.ChatChunk, None]:
        """Drop turns that are pure background noise before they hit the LLM.

        Returning without yielding anything tells AgentSession to skip this
        turn entirely — no LLM call, no TTS, no bot response.
        """
        user_messages = [m for m in chat_ctx.messages() if m.role == "user"]
        if user_messages:
            last_text: str = user_messages[-1].text_content or ""
            if _is_noise(last_text):
                logger.debug("Dropping noisy transcript: %r", last_text)
                return  # silent drop — prevents bot stuttering

        async for chunk in Agent.default.llm_node(self, chat_ctx, tools, model_settings):
            yield chunk

    async def on_user_turn_completed(
        self,
        turn_ctx: agents_llm.ChatContext,
        new_message: agents_llm.ChatMessage,
    ) -> None:
        """After each completed user turn, persist qualification results if detected."""
        text = (new_message.text_content or "").lower()

        # NOT_INTERESTED must be checked BEFORE interested — "not interested" contains "interested"
        not_interested_phrases = (
            "not interested", "no thanks", "not now", "don't want", "dont want",
            "no interest", "not looking", "don't need", "dont need",
            "not for me", "no need", "not want", "don't want to",
        )
        interested_phrases = (
            "interested", "yes", "sure", "definitely", "sounds good",
            "tell me more", "want to know", "i want", "sign me up",
            "go ahead", "please do", "why not",
        )
        callback_phrases = (
            "call back", "callback", "call me later", "call me back",
            "later", "busy", "not a good time", "some other time",
        )

        if any(w in text for w in not_interested_phrases):
            await _persist_qualification(self._lead_id, "not_interested")
        elif any(w in text for w in interested_phrases):
            await _persist_qualification(self._lead_id, "interested")
        elif any(w in text for w in callback_phrases):
            await _persist_qualification(self._lead_id, "callback_requested")

        await super().on_user_turn_completed(turn_ctx, new_message)


async def _persist_qualification(lead_id: str, status: str) -> None:
    """Write the qualification outcome to the database from inside the agent process."""
    if lead_id == "unknown":
        return
    try:
        from app.core.enums import LeadStatus
        from app.db.session import _SessionFactory
        from app.repositories.lead_repository import LeadRepository
        from app.schemas.lead import LeadUpdate

        async with _SessionFactory() as session:
            repo = LeadRepository(session)
            await repo.update(lead_id, LeadUpdate(status=LeadStatus(status)))
            await session.commit()
            logger.info("Lead %s status updated → %s", lead_id, status)
    except Exception as exc:
        logger.warning("Could not persist qualification for %s: %s", lead_id, exc)


async def entrypoint(ctx: JobContext) -> None:
    """Called by the LiveKit worker for every new matching room."""
    await ctx.connect()

    room_name: str = ctx.room.name
    lead_id = room_name.removeprefix(ROOM_PREFIX) if room_name.startswith(ROOM_PREFIX) else "unknown"
    # metadata is set by create_dispatch(metadata=lead.name) in LeadService
    lead_name: str = (ctx.job.metadata or "").strip() or "there"

    session = AgentSession(
        vad=silero.VAD.load(
            min_speech_duration=VAD_MIN_SPEECH_DURATION,
            min_silence_duration=VAD_MIN_SILENCE_DURATION,
            activation_threshold=VAD_ACTIVATION_THRESHOLD,
        ),
        stt=deepgram.STT(
            model=DEEPGRAM_MODEL,
            smart_format=True,
            endpointing_ms=DEEPGRAM_ENDPOINTING_MS,
            filler_words=False,
            punctuate=True,
        ),
        llm=groq.LLM(model=_settings.LLM_MODEL),
        tts=cartesia.TTS(
            model="sonic-2",
            voice=_settings.CARTESIA_VOICE_ID,
        ),
        min_interruption_words=3,
    )

    await session.start(
        room=ctx.room,
        agent=LeadQualifierAgent(lead_name=lead_name, lead_id=lead_id),
        room_options=RoomOptions(audio_input=True, audio_output=True),
    )


def start() -> None:
    """Poetry script entry point: poetry run start-agent start"""
    # Explicitly load .env so livekit-agents picks up LIVEKIT_URL before CLI parsing
    from dotenv import load_dotenv
    load_dotenv(override=True)

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="icici-lead-qualifier",
            ws_url=_settings.LIVEKIT_URL,
            api_key=_settings.LIVEKIT_API_KEY,
            api_secret=_settings.LIVEKIT_API_SECRET,
        )
    )


if __name__ == "__main__":
    start()
