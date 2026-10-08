#!/bin/sh

chown -R appuser:appuser /app/media /app/staticfiles

echo "Apply migrations"
gosu appuser python manage.py migrate --noinput

echo "Start server"
exec gosu appuser gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers=${GUNICORN_WORKERS:-3}