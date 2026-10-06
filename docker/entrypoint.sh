#!/bin/sh
set -e

python main.py migrate --noinput
# Ignore Tailwind source tree if it ever lands under a collected prefix again.
python main.py collectstatic --noinput -i src -i "*.map"

exec "$@"
