##
## ICICI Prudential AMC — Voice Agent
## Usage: make <target>
##

.PHONY: help install dev test build up down logs shell-backend

help:          ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Local development (no Docker) ─────────────────────────────────────────────
install:       ## Install backend + frontend deps locally
	cd backend && poetry install
	cd frontend && npm install

dev-api:       ## Start FastAPI dev server
	cd backend && poetry run uvicorn app.main:app --reload --port 8000

dev-agent:     ## Start LiveKit agent worker
	cd backend && poetry run python -m app.agent.worker start

dev-ui:        ## Start Vite dev server
	cd frontend && npm run dev

test:          ## Run backend tests
	cd backend && poetry run pytest -v

# ── Docker ─────────────────────────────────────────────────────────────────────
build:         ## Build all Docker images
	docker compose build

up:            ## Start all services (detached)
	docker compose up -d

down:          ## Stop all services
	docker compose down

logs:          ## Tail all service logs
	docker compose logs -f

logs-agent:    ## Tail agent logs only
	docker compose logs -f agent

shell-backend: ## Open a shell inside the backend container
	docker compose exec backend bash
