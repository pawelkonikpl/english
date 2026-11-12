FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/models

WORKDIR /srv

# The default PyPI torch wheel bundles CUDA (several GB); the CPU build is enough here.
RUN pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.4"

COPY pyproject.toml ./
COPY app ./app
RUN pip install ".[ml]"

# Model weights are downloaded into HF_HOME on first start; mount a volume there
# to keep them between container restarts.
RUN useradd --create-home --uid 10001 pii \
    && mkdir -p /models \
    && chown pii /models
USER pii

EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
