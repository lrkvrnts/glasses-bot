#!/usr/bin/env bash
# Run on the VPS after cloning the repo (keep .env only on the server).
set -euo pipefail
cd "$(dirname "$0")/.."
git pull --ff-only origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose exec -T bot alembic upgrade head
