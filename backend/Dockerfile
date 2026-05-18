# ── Stage 1: dependency installer ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV POETRY_VERSION=1.8.3
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install --upgrade pip \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

ENV PATH="${POETRY_VENV}/bin:${PATH}"

WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Export deps to a plain requirements file so the runtime stage stays lean
RUN poetry export --without dev --no-interaction --no-ansi -f requirements.txt -o /tmp/requirements.txt


# ── Stage 2: runtime image ─────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install from the exported requirements (no Poetry needed at runtime)
COPY --from=builder /tmp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create writable data directory for SQLite
RUN mkdir -p /app/data
