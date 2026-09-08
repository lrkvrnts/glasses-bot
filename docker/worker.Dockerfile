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
    LOG_FILE=/app/logs/worker.log

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 gosu \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r worker && useradd -r -g worker -d /app -s /sbin/nologin worker

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
COPY pyproject.toml poetry.lock* ./
COPY docker/entrypoint.sh /entrypoint.sh

RUN mkdir -p /app/logs /app/tmp \
    && chown -R worker:worker /app \
    && chmod +x /entrypoint.sh

ENV APP_USER=worker
ENTRYPOINT ["/entrypoint.sh"]
CMD ["celery", "-A", "bot.tasks.celery_app", "worker", "-l", "INFO", "--concurrency=4"]
