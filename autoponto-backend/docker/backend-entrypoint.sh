#!/bin/sh
set -e

python /app/autoponto/manage.py migrate --noinput
python /app/autoponto/manage.py collectstatic --noinput

exec "$@"
