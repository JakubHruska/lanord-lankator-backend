#!/usr/bin/env bash
set -e

echo ">>> Spouštím migrace..."
python manage.py migrate --noinput

echo ">>> Sbírám statické soubory..."
python manage.py collectstatic --noinput

echo ">>> Spouštím Gunicorn na portu 8000..."
exec gunicorn package_server.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --log-level info \
  --access-logfile - \
  --error-logfile -
