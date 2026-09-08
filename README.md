# Ozon Seller Bot

[![CI](https://github.com/lrkvrnts/glasses-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/lrkvrnts/glasses-bot/actions/workflows/ci.yml)

Telegram-бот для работы с Ozon Seller API: загрузка товаров, остатки, цены.

## Стек
- Python 3.12, Poetry (управление зависимостями)
- Aiogram 3, SQLAlchemy 2 async, PostgreSQL 16, Redis 7, Celery 5
- Caddy 2 (webhook + TLS)
- Docker Compose

## Возможности (MVP)
- Привязка кабинета Ozon (Client ID + API key, шифрование)
- Загрузка товаров через XLSX
- Управление остатками и ценами
- Многопользовательский режим (мульти-кабинет)

## Архитектура
См. [.hermes/plans/2026-09-01_153000-ozon-seller-bot-architecture.md](.hermes/plans/2026-09-01_153000-ozon-seller-bot-architecture.md)

## Требования
- Python 3.12+
- Poetry ([установка](https://python-poetry.org/docs/#installation))
- Docker + Docker Compose (для production-стека)

## Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/lrkvrnts/glasses-bot.git && cd glasses-bot

# 2. Скопировать env
cp .env.example .env
# Заполнить: BOT_TOKEN, ENCRYPTION_KEY, ...

# 3. Сконфигурировать Poetry
poetry config virtualenvs.in-project true

# 4. Установить зависимости
poetry install

# 5. Сгенерировать ключ шифрования
poetry run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Вставить в .env как ENCRYPTION_KEY

# 6. Поднять стек
make up

# 7. Применить миграции
make migrate

# 8. Режим получения апдейтов
# Локально без публичного домена: BOT_MODE=polling
# В production: BOT_MODE=webhook и WEBHOOK_URL=https://your-domain
# (не t.me/... — это страница бота, а не endpoint).
# При webhook-режиме бот сам вызовет setWebhook:
# ${WEBHOOK_URL}/webhook/${WEBHOOK_SECRET}
```

## Полезные команды

```bash
make install         # poetry install
make up              # docker compose up -d --build
make down            # docker compose down
make logs            # docker compose logs -f
make migrate         # alembic upgrade head
make test            # poetry run pytest
make lint            # poetry run ruff check
make format          # poetry run ruff format
make shell           # poetry shell
```

## Структура

```
src/bot/
  config/        # Settings, logging
  core/          # exceptions, types
  db/            # engine, session, models
  repositories/  # CRUD
  ozon/          # API client + modules (products, stocks, prices)
  services/      # бизнес-логика
  tasks/         # Celery
  bot_app/       # handlers, FSM, keyboards
  utils/         # xlsx, validators
  main.py        # entrypoint
```

## Безопасность
- API-ключи Ozon шифруются Fernet перед сохранением в БД
- Авторизация — только по Telegram ID
- Webhook защищён secret_token в URL path
- Все SQL через ORM (нет инъекций)

## Разработка

```bash
# Активировать venv
poetry shell

# Добавить новую зависимость
poetry add httpx

# Добавить dev-зависимость
poetry add --group dev pytest-mock

# Обновить lock-файл
poetry lock

# Обновить все пакеты
poetry update
```

## CI/CD

На каждый push/PR в `main` GitHub Actions:

1. **CI** — `ruff` + `pytest` + сборка Docker-образов (без публикации).
2. **CD** — после успешного CI публикует образы в [GHCR](https://github.com/lrkvrnts/glasses-bot/pkgs): `bot-latest` / `worker-latest`.

Выкладка на VPS **не включена**, пока в репозитории нет переменной `ENABLE_VPS_DEPLOY=true` и секретов:

| Secret / Variable | Назначение |
|---|---|
| `ENABLE_VPS_DEPLOY` (variable) | `true` — деплой по SSH после публикации образов |
| `VPS_HOST` | IP или домен сервера |
| `VPS_USER` | SSH-пользователь |
| `VPS_SSH_KEY` | приватный ключ |
| `VPS_PATH` | каталог клона, например `/opt/glasses-bot` |

На сервере один раз: клон репо, `.env` только там (не в git), затем `bash scripts/deploy.sh` или `make up-prod` + `make migrate`. Postgres/Redis снаружи не публикуются (`docker-compose.prod.yml`).
