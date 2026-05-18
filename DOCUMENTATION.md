# ICICI Prudential AMC — Voice AI Agent
## Full Technical Documentation

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [System Flow Diagram](#2-system-flow-diagram)
3. [LiveKit Methods & Concepts Used](#3-livekit-methods--concepts-used)
4. [API Reference](#4-api-reference)
5. [Voice Pipeline Deep Dive](#5-voice-pipeline-deep-dive)
6. [False Transcription Handling](#6-false-transcription-handling)
7. [Database Schema](#7-database-schema)
8. [How to Run](#8-how-to-run)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                             │
│                   React + TypeScript + Vite                         │
│              @livekit/components-react  |  port 5173               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │  REST API calls (fetch)
                           │  HTTP/WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                                │
│                    Python 3.11  |  port 8000                        │
│                                                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │  Router  │→ │ Service  │→ │  Repository  │→ │  SQLite DB   │  │
│   │ /api/v1  │  │  Layer   │  │    Layer     │  │  leads.db    │  │
│   └──────────┘  └────┬─────┘  └──────────────┘  └──────────────┘  │
│                       │                                             │
│                       │ Creates LiveKit Room via LiveKit API        │
│                       ▼                                             │
│              LiveKit Cloud API (REST)                               │
└──────────────────────────────────────────────────────────────────────┘
                           │
                           │  WebSocket (wss://)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│               LIVEKIT CLOUD  (wss://icici-q14xf7vl.livekit.cloud)  │
│                    Signalling + Media Relay                         │
│                        Region: India South                          │
└────────────────┬────────────────────────────────────────────────────┘
                 │ WebSocket job dispatch
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LIVEKIT AGENT WORKER                             │
│                  Python  |  livekit-agents 1.5.9                   │
│                                                                     │
│   Microphone Audio (WebRTC)                                         │
│        │                                                            │
│        ▼                                                            │
│   [Silero VAD] ──noise──► DROPPED                                   │
│        │ speech detected                                            │
│        ▼                                                            │
│   [Deepgram STT] ──nova-2-phonecall──► transcript text             │
│        │                                                            │
│        ▼                                                            │
│   [llm_node filter] ──noise/filler──► DROPPED (no LLM call)       │
│        │ clean transcript                                           │
│        ▼                                                            │
│   [Groq LLM] ──llama-3-8b-8192──► response text                   │
│        │                                                            │
│        ▼                                                            │
│   [Cartesia TTS] ──sonic-2──► audio stream                         │
│        │                                                            │
│        ▼                                                            │
│   Speaker (WebRTC back to browser)                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. System Flow Diagram

### 2a. Outbound Call Flow (Full Sequence)

```
 Operator          Frontend           FastAPI            LiveKit Cloud      Agent Worker
    │                  │                  │                    │                  │
    │  Click "📞 Call" │                  │                    │                  │
    │─────────────────►│                  │                    │                  │
    │                  │ POST /leads/{id}/dial                 │                  │
    │                  │─────────────────►│                    │                  │
    │                  │                  │ CreateRoom(name=   │                  │
    │                  │                  │  lead-call-{id})   │                  │
    │                  │                  │───────────────────►│                  │
    │                  │                  │◄───────────────────│                  │
    │                  │                  │  room created      │                  │
    │                  │                  │                    │                  │
    │                  │                  │ GenerateToken      │                  │
    │                  │                  │  (lead identity)   │                  │
    │                  │◄─────────────────│                    │                  │
    │                  │ {room_name,       │                    │                  │
    │                  │  participant_token│                    │                  │
    │                  │  livekit_url}     │                    │                  │
    │                  │                  │                    │                  │
    │                  │ LiveKitRoom       │                    │                  │
    │                  │ connect(token)    │                    │                  │
    │                  │──────────────────────────────────────►│                  │
    │                  │  WebRTC connected │                    │                  │
    │                  │◄──────────────────────────────────────│                  │
    │                  │                  │                    │                  │
    │                  │                  │                    │  dispatch_job()  │
    │                  │                  │                    │─────────────────►│
    │                  │                  │                    │                  │
    │                  │                  │                    │  entrypoint(ctx) │
    │                  │                  │                    │◄─────────────────│
    │                  │                  │                    │                  │
    │                  │                  │                    │  ctx.connect()   │
    │                  │                  │                    │◄─────────────────│
    │                  │                  │                    │  agent joins room│
    │                  │                  │                    │─────────────────►│
    │                  │                  │                    │                  │
    │◄─────────────────────────────────────────────────────────────────────────── │
    │  "Hello! I'm Priya from ICICI Prudential AMC..."  (TTS audio via WebRTC)   │
    │                  │                  │                    │                  │
    │  speaks...       │                  │                    │                  │
    │─────────────────────────────────────────────────────────────────────────── ►│
    │  (microphone audio via WebRTC → VAD → STT → LLM → TTS → back to browser)  │
    │                  │                  │                    │                  │
    │  "Yes I'm interested in ELSS funds"│                    │                  │
    │─────────────────────────────────────────────────────────────────────────── ►│
    │                  │                  │                    │                  │
    │                  │                  │◄────────────────────────────────────── │
    │                  │                  │ UPDATE lead status │                  │
    │                  │                  │ → INTERESTED       │                  │
    │                  │                  │ → fund: ELSS       │                  │
```

### 2b. Voice Pipeline (Per Turn)

```
User speaks into mic
        │
        ▼
┌───────────────────┐
│   Silero VAD      │  Detects speech vs silence
│  threshold: 0.55  │  min_speech: 150ms
│  silence: 400ms   │  Cuts audio chunks
└────────┬──────────┘
         │ speech detected
         ▼
┌───────────────────┐
│  Deepgram STT     │  Model: nova-2-phonecall
│  Endpointing:     │  Optimised for phone quality
│  300ms            │  smart_format: true
│  filler_words:off │  No "um/uh" in transcript
└────────┬──────────┘
         │ raw transcript + confidence
         ▼
┌───────────────────┐
│  Noise Filter     │  llm_node() override
│  (llm_node hook)  │  < 2 words → DROP
│                   │  all fillers → DROP
│                   │  Returns silently → no LLM call
└────────┬──────────┘
         │ clean transcript
         ▼
┌───────────────────┐
│   Groq LLM        │  Model: llama3-8b-8192
│   via Groq API    │  Fastest TTFT (~200ms)
│                   │  System prompt: Priya persona
└────────┬──────────┘
         │ response text (streaming)
         ▼
┌───────────────────┐
│  Cartesia TTS     │  Model: sonic-2
│                   │  Streaming audio synthesis
│                   │  ~100ms first audio chunk
└────────┬──────────┘
         │ PCM audio stream
         ▼
  WebRTC → Browser speaker
```

---

## 3. LiveKit Methods & Concepts Used

### 3a. LiveKit Cloud REST API (from FastAPI service)

| Method | Where Used | Purpose |
|--------|-----------|---------|
| `livekit_api.LiveKitAPI()` | `lead_service.py` | Authenticated API client |
| `lk.room.create_room(CreateRoomRequest)` | `lead_service.py` | Creates a named room for the call |
| `livekit_api.AccessToken()` | `lead_service.py` | Generates participant JWT token |
| `.with_identity(id)` | `lead_service.py` | Sets participant identity |
| `.with_grants(VideoGrants(...))` | `lead_service.py` | Sets room join permissions |
| `.with_ttl(30*60)` | `lead_service.py` | 30-minute token expiry |
| `.to_jwt()` | `lead_service.py` | Signs and returns the token |
| `lk.aclose()` | `lead_service.py` | Closes the API connection |

### 3b. LiveKit Agents SDK (worker process)

| Class / Method | File | Purpose |
|---------------|------|---------|
| `Agent` | `worker.py` | Base class — defines agent personality and hooks |
| `Agent.on_enter()` | `worker.py` | Called when agent joins a room — plays greeting |
| `Agent.llm_node()` | `worker.py` | Override — intercepts transcript before LLM, drops noise |
| `Agent.on_user_turn_completed()` | `worker.py` | Called after user finishes speaking — persists qualification |
| `AgentSession(stt, llm, tts, vad)` | `worker.py` | Wires the full STT→LLM→TTS pipeline |
| `AgentSession.start(room, agent)` | `worker.py` | Attaches session to LiveKit room |
| `AgentSession.say(text)` | `worker.py` | Speaks a fixed string to the room |
| `JobContext` | `worker.py` | Per-job context passed by the worker runtime |
| `ctx.connect()` | `worker.py` | Agent connects to the LiveKit room |
| `ctx.wait_for_disconnect()` | `worker.py` | Keeps process alive until room closes |
| `WorkerOptions(entrypoint_fnc)` | `worker.py` | Registers the agent with LiveKit Cloud |
| `cli.run_app(WorkerOptions)` | `worker.py` | Starts the worker event loop |
| `RoomInputOptions(audio_enabled)` | `worker.py` | Enables microphone input from participants |

### 3c. LiveKit Plugins Used

| Plugin | Version | Role | Key Settings |
|--------|---------|------|-------------|
| `livekit-plugins-silero` | 1.5.9 | VAD (Voice Activity Detection) | threshold=0.55, silence=400ms |
| `livekit-plugins-deepgram` | 1.5.9 | STT (Speech-to-Text) | nova-2-phonecall, endpointing=300ms |
| `livekit-plugins-groq` | 1.5.9 | LLM (Language Model) | llama3-8b-8192 |
| `livekit-plugins-cartesia` | 1.5.9 | TTS (Text-to-Speech) | sonic-2, Priya voice |

### 3d. LiveKit React Components (Frontend)

| Component | File | Purpose |
|-----------|------|---------|
| `<LiveKitRoom>` | `VoiceRoom.tsx` | WebRTC connection container — wraps the whole call UI |
| `<RoomAudioRenderer>` | `VoiceRoom.tsx` | Renders remote audio tracks (agent voice) to speakers |
| `<ControlBar>` | `VoiceRoom.tsx` | Mute / leave buttons |
| `useVoiceAssistant()` | `VoiceRoom.tsx` | Hook — gives agent state: speaking / listening / thinking |
| `useConnectionState()` | `VoiceRoom.tsx` | Hook — gives WebRTC connection status |

---

## 4. API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### `GET /health`
Health check.
```json
Response 200:
{ "status": "ok", "version": "0.1.0" }
```

---

#### `POST /leads`
Create a new lead.

**Request Body:**
```json
{
  "name": "Rajesh Kumar",
  "phone_number": "+919876543210",
  "email": "rajesh@example.com",       // optional
  "fund_preference": "equity",          // equity | debt | hybrid | index | elss | unknown
  "notes": "Interested in SIP"         // optional
}
```

**Response 201:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Rajesh Kumar",
  "phone_number": "+919876543210",
  "email": null,
  "status": "pending",
  "fund_preference": "equity",
  "call_direction": "outbound",
  "notes": null,
  "livekit_room": null,
  "created_at": "2026-05-14T10:00:00Z",
  "updated_at": "2026-05-14T10:00:00Z"
}
```

---

#### `GET /leads`
List all leads with pagination.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Results per page (max 100) |
| `status` | string | — | Filter by status |

**Response 200:**
```json
{
  "total": 42,
  "page": 1,
  "page_size": 20,
  "items": [ ...LeadResponse ]
}
```

---

#### `GET /leads/{lead_id}`
Get a single lead.

**Response 200:** `LeadResponse`
**Response 404:** `{ "detail": "Lead '...' not found." }`

---

#### `PATCH /leads/{lead_id}`
Update lead details or status.

**Request Body (all optional):**
```json
{
  "status": "interested",
  "fund_preference": "elss",
  "notes": "Wants ₹5000/month SIP"
}
```

**Response 200:** `LeadResponse`

---

#### `DELETE /leads/{lead_id}`
Delete a lead.

**Response 204:** No content.

---

#### `POST /leads/{lead_id}/dial`
**This is the core endpoint.** Provisions a LiveKit room and returns a join token.

**Response 200:**
```json
{
  "room_name": "lead-call-550e8400-e29b-41d4-a716-446655440000",
  "participant_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "livekit_url": "wss://icici-q14xf7vl.livekit.cloud"
}
```

**What happens internally:**
```
1. Fetch lead from DB
2. Build room_name = "lead-call-{lead_id}"
3. Call LiveKit API: CreateRoom(name, empty_timeout=120, max_participants=2)
4. Generate JWT AccessToken with VideoGrants(room_join=True, room=room_name)
5. Save room_name to lead record in DB
6. Return token to frontend
7. Frontend connects to room → agent auto-joins via worker dispatch
```

---

## 5. Voice Pipeline Deep Dive

### End-to-End Latency Budget

```
┌─────────────────────────────────────────────────┐
│         Latency Breakdown (target <800ms)        │
├──────────────────────────────┬──────────────────┤
│ Component                    │ Typical Latency  │
├──────────────────────────────┼──────────────────┤
│ Silero VAD endpointing       │ ~300-400ms       │
│ Deepgram STT (nova-2)        │ ~100-200ms       │
│ Network round-trip           │ ~20-50ms         │
│ Groq LLM TTFT (llama3-8b)   │ ~150-250ms       │
│ Cartesia TTS first chunk     │ ~80-150ms        │
├──────────────────────────────┼──────────────────┤
│ TOTAL                        │ ~650-1050ms      │
└──────────────────────────────┴──────────────────┘
```

Why each provider was chosen for speed:
- **Deepgram nova-2-phonecall** — fastest STT for voice calls, purpose-built for phone audio
- **Groq** — runs LLM inference on custom LPU hardware, 10x faster than GPU-based APIs
- **Cartesia sonic-2** — streaming TTS, starts playing before full response is generated

---

## 6. False Transcription Handling

The agent has **three layers** of noise filtering:

### Layer 1 — Silero VAD (Before STT)
```python
silero.VAD.load(
    min_speech_duration=0.15,     # Ignore blips < 150ms
    min_silence_duration=0.4,     # Wait 400ms of silence before cutting
    activation_threshold=0.55,    # 55% probability threshold
)
```
Prevents background noise from ever reaching Deepgram.

### Layer 2 — Deepgram Config (At STT)
```python
deepgram.STT(
    filler_words=False,   # Strip "um", "uh", "like" from transcript
    punctuate=True,       # Proper punctuation improves LLM accuracy
    endpointing_ms=300,   # Finalize after 300ms of silence
)
```

### Layer 3 — llm_node Override (After STT, Before LLM)
```python
async def llm_node(self, chat_ctx, tools, model_settings):
    last_text = user_messages[-1].text_content or ""
    
    # Drop if < 2 words (catches single beeps transcribed as words)
    if len(words) < MIN_TRANSCRIPT_WORDS:
        return   # ← No LLM call. No TTS. Complete silence.
    
    # Drop if all filler words
    if all(word in {"um","uh","hmm","hm","ah","oh"} for word in words):
        return
    
    # Otherwise, forward to LLM normally
    async for chunk in Agent.default.llm_node(...):
        yield chunk
```

**Result:** The bot never responds to TV audio, coughing, or background noise.

---

## 7. Database Schema

```
Table: leads
┌──────────────────┬────────────────────────────────────────────────────┐
│ Column           │ Type / Constraint                                  │
├──────────────────┼────────────────────────────────────────────────────┤
│ id               │ VARCHAR(36)  PRIMARY KEY  (UUID v4)                │
│ name             │ VARCHAR(120) NOT NULL                              │
│ phone_number     │ VARCHAR(20)  UNIQUE  INDEX                         │
│ email            │ VARCHAR(254) NULLABLE                              │
│ status           │ ENUM(pending|interested|not_interested|            │
│                  │      callback_requested|unreachable)  INDEX        │
│ fund_preference  │ ENUM(equity|debt|hybrid|index|elss|unknown)        │
│ call_direction   │ ENUM(outbound|inbound)                             │
│ notes            │ VARCHAR(2000) NULLABLE                             │
│ livekit_room     │ VARCHAR(120)  NULLABLE                             │
│ created_at       │ DATETIME(timezone=True) DEFAULT now()              │
│ updated_at       │ DATETIME(timezone=True) DEFAULT now() ON UPDATE    │
└──────────────────┴────────────────────────────────────────────────────┘
```

### Status Lifecycle
```
           ┌─────────┐
           │ PENDING │  ← Lead created, call not yet made
           └────┬────┘
                │  call made, agent qualifies
        ┌───────┼───────────────────┐
        ▼       ▼                   ▼
 ┌──────────┐ ┌───────────────┐ ┌──────────────────┐
 │INTERESTED│ │NOT_INTERESTED │ │CALLBACK_REQUESTED│
 └──────────┘ └───────────────┘ └──────────────────┘
        
  Also possible:
 ┌─────────────┐
 │ UNREACHABLE │  ← Set manually if call couldn't connect
 └─────────────┘
```

---

## 8. How to Run

### Start Everything (Recommended)

Double-click **`start-all.bat`** from the project root.

This opens 3 separate terminal windows:
1. **FastAPI** — `http://localhost:8000`
2. **LiveKit Agent Worker** — connects to `wss://icici-q14xf7vl.livekit.cloud`
3. **Frontend** — `http://localhost:5173`

### Start Individually

```bash
# Terminal 1 — API
start-backend.bat

# Terminal 2 — Voice Agent
start-agent.bat

# Terminal 3 — UI
start-frontend.bat
```

### Run Tests
```bash
cd backend
poetry run pytest -v
```

### API Docs (Interactive)
Open `http://localhost:8000/docs` for Swagger UI — try all endpoints live.

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `LIVEKIT_URL` | LiveKit Cloud WebSocket URL | `wss://xxx.livekit.cloud` |
| `LIVEKIT_API_KEY` | LiveKit API Key | `APIxxxxxxxxx` |
| `LIVEKIT_API_SECRET` | LiveKit API Secret | `xxxxxxxx...` |
| `DEEPGRAM_API_KEY` | Deepgram API Key for STT | `5b52033c...` |
| `GROQ_API_KEY` | Groq API Key for LLM | `gsk_xxxxx` |
| `CARTESIA_API_KEY` | Cartesia API Key for TTS | `sk_car_xxx` |
| `DATABASE_URL` | SQLAlchemy async URL | `sqlite+aiosqlite:///./data/leads.db` |
| `MIN_TRANSCRIPT_WORDS` | Noise filter threshold | `2` |
| `MIN_TRANSCRIPT_CONFIDENCE` | Deepgram confidence floor | `0.65` |
| `LLM_MODEL` | Groq model name | `llama3-8b-8192` |
| `CARTESIA_VOICE_ID` | Cartesia voice UUID | `79a125e8-...` |
