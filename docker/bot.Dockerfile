# ---- builder ----
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN poetry install --without dev --no-root

# ---- runtime ----
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    LOG_FILE=/app/logs/bot.log \
    POETRY_VIRTUALENVS_IN_PROJECT=true

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r bot && useradd -r -g bot -d /app -s /sbin/nologin bot

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY pyproject.toml poetry.lock* ./
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/
COPY alembic.ini ./

RUN mkdir -p /app/logs /app/tmp && chown -R bot:bot /app
USER bot

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=40s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)" || exit 1

CMD ["python", "-m", "bot.main"]
