#!/bin/sh
set -e
user="${APP_USER:-bot}"
mkdir -p /app/logs /app/tmp
chown -R "$user:$user" /app/logs /app/tmp || true
exec gosu "$user" "$@"
