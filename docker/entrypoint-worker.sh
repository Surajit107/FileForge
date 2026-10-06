#!/bin/sh
# Worker/beat entry: no migrate/collectstatic — web owns schema + static.
set -e
exec "$@"
