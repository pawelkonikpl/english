# Local English learning app: FastAPI backend + React frontend.
.PHONY: install backend frontend dev build run test docker docker-down

install:
	cd backend && uv sync
	cd frontend && npm install

backend:
	cd backend && uv run uvicorn english_app.main:create_app --factory --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && npm run dev

# Backend with auto-reload and Vite dev server (http://localhost:5173), in parallel.
dev:
	$(MAKE) -j2 backend frontend

build:
	cd frontend && npm run build

# One command: build the frontend and serve everything from http://127.0.0.1:8000
run: build
	cd backend && uv run python -m english_app

# Backend (pytest) and frontend (vitest) tests; no real AI provider is called.
test:
	cd backend && uv run pytest
	cd frontend && npm test

# Docker: build and start in the background (http://127.0.0.1:8000); data lives in a volume.
docker:
	docker compose up --build -d

docker-down:
	docker compose down
