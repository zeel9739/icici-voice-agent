# HLD and LLD — Voice AI Agent Design Diagrams
## ICICI Prudential AMC | Lead Qualification Voice Agent
**Version:** 1.1.0  
**Last Updated:** 2026-05-15  
**Status:** Production-Ready

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Design (HLD)](#2-high-level-design-hld)
3. [Technology Stack](#3-technology-stack)
4. [Component Architecture](#4-component-architecture)
5. [Low-Level Design (LLD)](#5-low-level-design-lld)
6. [Database Schema](#6-database-schema)
7. [API Reference](#7-api-reference)
8. [Agent Pipeline Configuration](#8-agent-pipeline-configuration)
9. [Key Implementation Details](#9-key-implementation-details)
10. [Deployment Architecture](#10-deployment-architecture)

---

## 1. System Overview

The ICICI Prudential AMC Voice AI Agent is an automated outbound call system that qualifies leads for mutual fund investments. A voice AI agent named **"Priya"** calls leads, engages them in a natural conversation, and records their interest level in ICICI Prudential fund products.

### Goals
- Automate lead qualification calls at scale
- Classify leads as: `interested`, `not_interested`, or `callback_requested`
- Provide real-time voice interaction with sub-800ms end-to-end latency
- Store qualification outcomes in a persistent database for CRM follow-up

---

## 2. High-Level Design (HLD)

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ICICI Prudential AMC                             │
│                     Voice AI Agent System                               │
└─────────────────────────────────────────────────────────────────────────┘

 ┌──────────────┐    REST API     ┌──────────────────────────────────────┐
 │   Operator   │ ─────────────► │         Backend (FastAPI)            │
 │  Dashboard   │                │         Port 8000                    │
 │  (React +    │ ◄───────────── │                                      │
 │   Vite)      │   JSON resp.   │  ┌─────────────┐  ┌───────────────┐ │
 └──────────────┘                │  │ Leads API   │  │ LeadService   │ │
                                 │  │ /api/v1/    │  │               │ │
                                 │  │ leads       │  │ create / list │ │
                                 │  │             │  │ update / dial │ │
                                 │  └─────────────┘  └───────┬───────┘ │
                                 │                            │         │
                                 │  ┌─────────────────────────▼───────┐ │
                                 │  │       SQLite Database           │ │
                                 │  │   (data/icici_leads.db)        │ │
                                 │  └─────────────────────────────────┘ │
                                 └────────────────┬─────────────────────┘
                                                  │ CreateAgentDispatch
                                                  │ CreateRoom + Token
                                                  ▼
                                 ┌────────────────────────────────────────┐
                                 │          LiveKit Cloud                 │
                                 │    wss://icici-q14xf7vl.livekit.cloud  │
                                 │                                        │
                                 │  ┌──────────────┐  ┌────────────────┐ │
                                 │  │  Room:       │  │  Agent Worker  │ │
                                 │  │  lead-call-  │  │  (dispatched)  │ │
                                 │  │  {lead_id}   │◄─┤               │ │
                                 │  └──────┬───────┘  └───────┬────────┘ │
                                 └─────────┼───────────────────┼─────────┘
                                           │ WebRTC            │ WebSocket
                                           │ Audio             │
                                  ┌────────▼────────┐ ┌────────▼────────────┐
                                  │  Lead's Browser  │ │  Agent Worker       │
                                  │  (VoiceRoom.tsx) │ │  (Python process)   │
                                  │                  │ │                     │
                                  │  LiveKitRoom +   │ │  VAD → STT → LLM   │
                                  │  RoomAudioRender │ │      → TTS          │
                                  └──────────────────┘ └─────────────────────┘
```

### Call Flow (HLD Sequence)

```
Operator          Backend           LiveKit Cloud       Agent Worker     Lead Browser
   │                 │                    │                   │               │
   │─── POST /leads/{id}/dial ──────────► │                   │               │
   │                 │── CreateRoom ─────► │                   │               │
   │                 │── DispatchAgent ──► │── Dispatch ──────►│               │
   │                 │◄── token ──────────┤                   │               │
   │◄── DialResponse─┤                    │                   │               │
   │                 │                    │                   │               │
   │─── share token with lead ───────────────────────────────────────────────►│
   │                 │                    │◄── join room ──────────────────────│
   │                 │                    │◄── join room ──────│               │
   │                 │                    │                   │── on_enter()   │
   │                 │                    │◄──────── greeting TTS audio ──────►│
   │                 │                    │                   │               │
   │                 │                    │◄─── mic audio ─────────────────────│
   │                 │                    │── audio ─────────►│               │
   │                 │                    │           VAD detects speech       │
   │                 │                    │           STT transcribes          │
   │                 │                    │           LLM generates response   │
   │                 │                    │           TTS synthesises voice    │
   │                 │                    │◄──────── response audio ──────────►│
   │                 │                    │                   │               │
   │                 │       (repeats until call ends)        │               │
   │                 │                    │                   │               │
   │                 │◄── persist status ─│◄── keyword detect │               │
```

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | React + TypeScript | 18.x | Operator dashboard + call UI |
| **Frontend Build** | Vite | 5.x | Dev server + bundler |
| **Frontend Audio** | `@livekit/components-react` | latest | WebRTC room, audio rendering |
| **Backend** | FastAPI + Python | 3.11 / 0.115.x | REST API, lead management |
| **Backend ORM** | SQLAlchemy (async) | 2.x | Database access layer |
| **Database** | SQLite + aiosqlite | — | Lead storage (dev/prod) |
| **Agent Framework** | livekit-agents | **1.5.9** | Voice agent orchestration |
| **RTC Infrastructure** | LiveKit Cloud | — | WebRTC SFU, room management |
| **VAD** | Silero VAD | — | Voice activity detection |
| **STT** | Deepgram | nova-3 | Speech-to-text |
| **LLM** | Groq | llama-3.1-8b-instant | Conversation generation |
| **TTS** | Cartesia | sonic-2 | Text-to-speech synthesis |

---

## 4. Component Architecture

### 4.1 Frontend (React + Vite)

```
frontend/src/
├── components/
│   ├── VoiceRoom.tsx          # LiveKit room component (call UI)
│   │   ├── LiveKitRoom        # WebRTC connection, audio=true, video=false
│   │   ├── RoomAudioRenderer  # Plays agent TTS audio in browser
│   │   ├── AgentStatus        # Displays speaking/listening/thinking/waiting
│   │   └── ControlBar         # Mic toggle + leave button
│   └── ...
└── ...
```

**VoiceRoom component responsibilities:**
- Connects to LiveKit room using the participant token from `/dial` endpoint
- Publishes browser microphone audio (`audio={true}`)
- Renders agent audio via `RoomAudioRenderer`
- Shows real-time agent state using `useVoiceAssistant()` hook

### 4.2 Backend (FastAPI)

```
backend/app/
├── main.py                    # FastAPI app factory, CORS, lifespan
├── api/v1/
│   ├── router.py              # Mounts /api/v1
│   └── endpoints/leads.py     # CRUD + /dial endpoint
├── services/
│   └── lead_service.py        # Business logic, LiveKit provisioning
├── repositories/
│   └── lead_repository.py     # SQLAlchemy async CRUD
├── models/
│   └── lead.py                # SQLAlchemy Lead model
├── schemas/
│   └── lead.py                # Pydantic schemas (in/out)
├── core/
│   ├── config.py              # Settings (reads .env via pydantic-settings)
│   ├── constants.py           # VAD/STT tuning constants
│   ├── enums.py               # LeadStatus, FundCategory, CallDirection
│   └── exceptions.py          # AppError, LiveKitError
├── db/
│   ├── base.py                # DeclarativeBase
│   └── session.py             # AsyncSession factory, create_all_tables()
└── agent/
    ├── worker.py              # LiveKit agent worker (entrypoint)
    └── prompts.py             # SYSTEM_PROMPT + GREETING_TEMPLATE
```

### 4.3 Agent Worker (livekit-agents 1.5.9)

```
Agent Worker Process (port 8081 internal)
│
├── WorkerOptions
│   ├── agent_name: "icici-lead-qualifier"
│   ├── ws_url: wss://icici-q14xf7vl.livekit.cloud
│   └── entrypoint_fnc: entrypoint()
│
└── entrypoint(ctx: JobContext)
    ├── ctx.connect()           # Connect worker to LiveKit room
    ├── extract lead_id from room name (lead-call-{id})
    ├── extract lead_name from job metadata
    ├── AgentSession(
    │   ├── VAD: Silero
    │   ├── STT: Deepgram nova-3
    │   ├── LLM: Groq llama-3.1-8b-instant
    │   └── TTS: Cartesia sonic-2
    │   )
    └── session.start(room, agent=LeadQualifierAgent)
        │
        └── LeadQualifierAgent
            ├── on_enter()              # Send greeting
            ├── llm_node()              # Noise filter before LLM
            └── on_user_turn_completed() # Keyword detection → DB update
```

---

## 5. Low-Level Design (LLD)

### 5.1 Agent Pipeline Detail

```
Browser Microphone (WebRTC, 48 kHz, browser audio)
    │
    ▼
┌─────────────────────────────────┐
│    Silero VAD                   │
│  activation_threshold: 0.30     │  ← lowered from 0.55 for browser WebRTC
│  min_speech_duration:  0.05 s   │  ← short utterances captured
│  min_silence_duration: 0.30 s   │
└────────────────┬────────────────┘
                 │ speech segment
                 ▼
┌─────────────────────────────────┐
│    Deepgram STT                 │
│  model:          nova-3         │  ← optimised for WebRTC/browser audio
│  endpointing_ms: 200            │  ← fast end-of-utterance detection
│  smart_format:   true           │
│  punctuate:      true           │
│  filler_words:   false          │
└────────────────┬────────────────┘
                 │ transcript text
                 ▼
┌─────────────────────────────────┐
│    Noise Filter (llm_node)      │
│  MIN_TRANSCRIPT_WORDS: 1        │  ← drops empty transcripts only
│  filler check: um/uh/hmm/hm/ah  │  ← drops pure filler turns
└────────────────┬────────────────┘
                 │ clean transcript
                 ▼
┌─────────────────────────────────┐
│    Groq LLM                     │
│  model: llama-3.1-8b-instant    │  ← Groq's fastest hosted Llama 3.1
│  system: SYSTEM_PROMPT (Priya)  │
│  min_interruption_words: 3      │
└────────────────┬────────────────┘
                 │ response text
                 ▼
┌─────────────────────────────────┐
│    Cartesia TTS                 │
│  model: sonic-2                 │
│  voice: 79a125e8-cd45-4c13-...  │  ← Priya's voice ID
└────────────────┬────────────────┘
                 │ audio stream
                 ▼
         Lead's Browser
       (RoomAudioRenderer)
```

### 5.2 Lead Qualification State Machine

```
         ┌──────────┐
         │  PENDING │  ← initial state on lead creation
         └────┬─────┘
              │  /dial called
              ▼
         ┌──────────────┐
         │  call active │  (no DB state change)
         └──────┬───────┘
                │
        ┌───────┼────────────────┐
        ▼       ▼                ▼
 ┌──────────┐  ┌──────────────┐  ┌────────────────────┐
 │INTERESTED│  │NOT_INTERESTED│  │CALLBACK_REQUESTED  │
 └──────────┘  └──────────────┘  └────────────────────┘
        │               │                │
        │  keyword       │  keyword       │  keyword
        │  "interested"  │  "not         │  "call back"
        │  "yes"         │   interested"  │  "callback"
        │  "sure"        │  "no thanks"   │  "later"
        │  "definitely"  │  "not now"     │  "busy"
        └───────────────┴────────────────┘
                    (auto-detected by on_user_turn_completed)
```

### 5.3 Dial Flow (LeadService.dial_lead)

```
POST /api/v1/leads/{lead_id}/dial
          │
          ▼
   LeadRepository.get_by_id()
          │
          ▼
   LiveKitAPI.room.create_room(
       name="lead-call-{lead_id}",
       empty_timeout=120,      # 2 min silence → auto-close
       max_participants=2
   )
          │
          ▼
   AccessToken.to_jwt()
       identity: "lead-{lead_id}"
       grants: room_join, can_publish, can_subscribe
       TTL: 30 minutes
          │
          ▼
   AgentDispatch.create_dispatch(
       room="lead-call-{lead_id}",
       agent_name="icici-lead-qualifier",
       metadata=lead.name           # passed to entrypoint as ctx.job.metadata
   )
          │
          ▼
   LeadRepository.set_room()       # store room name on lead record
          │
          ▼
   DialResponse {
       room_name, participant_token, livekit_url
   }
```

### 5.4 Agent Worker Startup Sequence

```
poetry run start-agent start
    │
    ▼
load_dotenv()               # Load .env before CLI parsing
    │
    ▼
cli.run_app(WorkerOptions(
    entrypoint_fnc=entrypoint,
    agent_name="icici-lead-qualifier",
    ws_url=LIVEKIT_URL,
    api_key=LIVEKIT_API_KEY,
    api_secret=LIVEKIT_API_SECRET,
))
    │
    ▼
Worker registers with LiveKit Cloud
    │
    ▼
Waits for agent dispatch events from LiveKit
    │
    ▼
On dispatch received → spawn entrypoint(ctx)
    │
    ├── ctx.connect()
    ├── parse lead_id, lead_name from room/metadata
    ├── build AgentSession (VAD+STT+LLM+TTS)
    └── session.start() → agent runs until room closes
         NOTE: ctx.wait_for_disconnect() does NOT exist in
               livekit-agents 1.5.9 — session lifecycle is
               managed internally by the framework
```

---

## 6. Database Schema

### Table: `leads`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PK | UUID v4 |
| `name` | VARCHAR(120) | NOT NULL | Lead's full name |
| `phone_number` | VARCHAR(20) | UNIQUE, INDEX | Contact number |
| `email` | VARCHAR(254) | NULLABLE | Optional email |
| `status` | ENUM | INDEX, default=`pending` | Qualification outcome |
| `fund_preference` | ENUM | default=`unknown` | Preferred fund category |
| `call_direction` | ENUM | default=`outbound` | Call direction |
| `notes` | VARCHAR(2000) | NULLABLE | Agent/operator notes |
| `livekit_room` | VARCHAR(120) | NULLABLE | LiveKit room name after dial |
| `created_at` | DATETIME+TZ | server_default=now() | Creation timestamp |
| `updated_at` | DATETIME+TZ | onupdate=now() | Last update timestamp |

### Enum Values

**LeadStatus:** `pending` | `interested` | `not_interested` | `callback_requested` | `unreachable`

**FundCategory:** `equity` | `debt` | `hybrid` | `index` | `elss` | `unknown`

**CallDirection:** `outbound` | `inbound`

---

## 7. API Reference

Base URL: `http://localhost:8000/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/leads` | Create a new lead |
| `GET` | `/leads` | List leads (paginated, filterable by status) |
| `GET` | `/leads/{id}` | Get single lead |
| `PATCH` | `/leads/{id}` | Update lead (status, notes, fund_preference) |
| `DELETE` | `/leads/{id}` | Delete lead |
| `POST` | `/leads/{id}/dial` | Provision LiveKit room + dispatch agent → returns join token |
| `GET` | `/health` | Health check |

### POST /leads/{id}/dial — Response

```json
{
  "room_name": "lead-call-{uuid}",
  "participant_token": "eyJ...<JWT>",
  "livekit_url": "wss://icici-q14xf7vl.livekit.cloud"
}
```

---

## 8. Agent Pipeline Configuration

### 8.1 VAD (Silero)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `activation_threshold` | `0.30` | Lowered from 0.55 — browser WebRTC audio has lower energy than PSTN |
| `min_speech_duration` | `0.05 s` | Captures short responses ("yes", "no") |
| `min_silence_duration` | `0.30 s` | Reasonable pause detection |

### 8.2 STT (Deepgram)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `model` | `nova-3` | Optimised for WebRTC/browser audio (48 kHz). Do NOT use `nova-2-phonecall` — that model is tuned for PSTN 8 kHz audio |
| `endpointing_ms` | `200` | Fast end-of-utterance detection |
| `smart_format` | `true` | Auto-formats numbers, dates |
| `punctuate` | `true` | Adds punctuation to transcript |
| `filler_words` | `false` | Filters um/uh from STT output |

### 8.3 LLM (Groq)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `model` | `llama-3.1-8b-instant` | Groq-hosted Llama 3.1 8B. NOTE: `llama3-8b-8192` was decommissioned by Groq in May 2026 |
| `min_interruption_words` | `3` | Lead must say ≥3 words to interrupt Priya speaking |

### 8.4 TTS (Cartesia)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `model` | `sonic-2` | Latest Cartesia generation model |
| `voice` | `79a125e8-cd45-4c13-8a67-188112f4dd22` | Priya's voice ID |

### 8.5 Noise Filter

| Parameter | Value | Notes |
|-----------|-------|-------|
| `MIN_TRANSCRIPT_WORDS` | `1` | Drop empty transcripts only |
| Filler detection | `um, uh, hmm, hm, ah, oh, er, ugh` | Drop turns that are all filler words |

---

## 9. Key Implementation Details

### 9.1 Instructions Class (livekit-agents 1.5.9)

`Agent.__init__()` requires `instructions` to be an `Instructions` instance (a subclass of `str` with `.audio` and `.text` properties), **not** a plain `str`.

```python
from livekit.agents.voice.agent import Instructions

class LeadQualifierAgent(Agent):
    def __init__(self, lead_name: str, lead_id: str) -> None:
        super().__init__(instructions=Instructions(SYSTEM_PROMPT))  # NOT: instructions=SYSTEM_PROMPT
```

Passing a plain `str` causes a `PydanticSerializationError` in OpenTelemetry tracing (`chat_ctx.to_dict()`) because the pydantic serializer calls `.audio` on all `ChatContent` union values including plain strings.

### 9.2 RoomOptions (not RoomInputOptions)

`RoomInputOptions` is deprecated in livekit-agents 1.5.9. Use:

```python
from livekit.agents.voice.room_io.types import RoomOptions

await session.start(
    room=ctx.room,
    agent=agent,
    room_options=RoomOptions(audio_input=True, audio_output=True),
)
```

### 9.3 chat_ctx.messages() is a Method

In livekit-agents 1.5.9, `ChatContext.messages` is a **method**, not a property. Always call with parentheses:

```python
user_messages = [m for m in chat_ctx.messages() if m.role == "user"]  # correct
# user_messages = [m for m in chat_ctx.messages if ...]              # TypeError
```

### 9.4 No wait_for_disconnect in 1.5.9

`ctx.wait_for_disconnect()` does not exist in livekit-agents 1.5.9. After `session.start()` returns, the framework manages the session lifecycle. The entrypoint function simply returns:

```python
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    # ... build session ...
    await session.start(room=ctx.room, agent=agent, room_options=...)
    # That's it — do NOT call ctx.wait_for_disconnect()
```

### 9.5 Qualification Auto-Detection

`LeadQualifierAgent.on_user_turn_completed()` scans each user utterance for keywords and writes the qualification result to the database asynchronously:

```
"interested" / "yes" / "sure" / "definitely" / "sounds good" → INTERESTED
"not interested" / "no thanks" / "not now" / "don't want"     → NOT_INTERESTED
"call back" / "callback" / "later" / "busy"                   → CALLBACK_REQUESTED
```

### 9.6 Agent Name Matching

The worker registers with `agent_name="icici-lead-qualifier"`. The `/dial` endpoint dispatches with the **same name**. If these don't match, the agent is never dispatched into the room.

---

## 10. Deployment Architecture

### Local Development

```
localhost:5173  ← Vite dev server (frontend)
localhost:8000  ← Uvicorn (FastAPI backend, reload=true)
localhost:8081  ← Agent worker internal HTTP (livekit-agents)

External:
wss://icici-q14xf7vl.livekit.cloud   ← LiveKit Cloud (India South region)
api.deepgram.com                      ← Deepgram STT
api.groq.com                          ← Groq LLM
api.cartesia.ai                       ← Cartesia TTS
```

### Startup Commands

```bash
# Backend API
cd backend
poetry run start-api

# Agent Worker (separate terminal)
cd backend
poetry run start-agent start

# Frontend
cd frontend
npm run dev
```

### Environment Variables (.env)

```ini
# Application
DEBUG=true
APP_NAME=ICICI Prudential Voice Agent
APP_VERSION=0.1.0

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/icici_leads.db

# LiveKit
LIVEKIT_URL=wss://icici-q14xf7vl.livekit.cloud
LIVEKIT_API_KEY=<your-key>
LIVEKIT_API_SECRET=<your-secret>

# Deepgram STT
DEEPGRAM_API_KEY=<your-key>

# Groq LLM
GROQ_API_KEY=<your-key>

# Cartesia TTS
CARTESIA_API_KEY=<your-key>

# Agent Tuning
MIN_TRANSCRIPT_WORDS=1
MIN_TRANSCRIPT_CONFIDENCE=0.65
LLM_MODEL=llama-3.1-8b-instant
CARTESIA_VOICE_ID=79a125e8-cd45-4c13-8a67-188112f4dd22
```

---

## Appendix: Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-14 | Initial implementation |
| 1.1.0 | 2026-05-15 | Fixed no-voice bug: Instructions class, RoomOptions, chat_ctx.messages(), removed wait_for_disconnect; upgraded STT model to nova-3; updated LLM to llama-3.1-8b-instant; tuned VAD for browser WebRTC audio |
