#!/bin/sh
set -e

python main.py migrate --noinput
python main.py collectstatic --noinput

exec "$@"
