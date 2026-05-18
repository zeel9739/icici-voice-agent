GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# LiveKit room name prefix for outbound lead qualification calls
ROOM_PREFIX = "lead-call-"

# Silero VAD thresholds tuned for phone-quality audio
VAD_MIN_SPEECH_DURATION = 0.05    # seconds — more sensitive for browser mic
VAD_MIN_SILENCE_DURATION = 0.3    # seconds
VAD_ACTIVATION_THRESHOLD = 0.3    # lowered for browser WebRTC audio

# Deepgram STT settings — nova-3 works better than phonecall model for browser mic
DEEPGRAM_MODEL = "nova-3"
DEEPGRAM_ENDPOINTING_MS = 200

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
