# Speak Up: FastAPI backend serving the built React frontend, one container.
#
#   docker compose up --build        -> http://127.0.0.1:8000
#
# Behind a TLS-intercepting proxy, pass its CA bundle as a build secret:
#   docker build --secret id=ca,src=/path/to/ca-bundle.crt .
# The secret is only used during the build and never stored in the image.

ARG NODE_IMAGE=node:22-slim
ARG PYTHON_IMAGE=python:3.13-slim

# --- 1. Frontend build ------------------------------------------------------
FROM ${NODE_IMAGE} AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=secret,id=ca \
    if [ -s /run/secrets/ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca; fi \
    && npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- 2. Backend runtime -----------------------------------------------------
FROM ${PYTHON_IMAGE} AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/backend/.venv

RUN --mount=type=secret,id=ca \
    if [ -s /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi \
    && pip install --no-cache-dir "uv>=0.11,<0.12"

WORKDIR /app/backend
# Dependencies first, so code changes do not reinstall them.
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=secret,id=ca \
    if [ -s /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca; fi \
    && uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
RUN --mount=type=secret,id=ca \
    if [ -s /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca; fi \
    && uv sync --frozen --no-dev
COPY --from=frontend /app/frontend/dist /app/frontend/dist

RUN useradd --create-home --uid 1000 app && mkdir -p /app/data && chown app /app/data
USER app

# Optional: bake the GitHub Copilot runtime into the image (otherwise it is downloaded on first use).
ARG WITH_COPILOT_RUNTIME=false
RUN --mount=type=secret,id=ca,uid=1000 \
    if [ "$WITH_COPILOT_RUNTIME" = "true" ]; then \
      if [ -s /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca; fi; \
      /app/backend/.venv/bin/python -m copilot download-runtime; \
    fi

ENV PATH=/app/backend/.venv/bin:$PATH \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_URL=sqlite+aiosqlite:////app/data/english.db
EXPOSE 8000
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)"
CMD ["python", "-m", "english_app"]
