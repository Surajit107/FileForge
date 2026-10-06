FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Exported from uv.lock: uv export --no-hashes --no-emit-project --group prod -o requirements/production.txt
COPY requirements/production.txt /tmp/requirements/production.txt
RUN pip install --no-cache-dir -r /tmp/requirements/production.txt

COPY . /app

RUN chmod +x /app/docker/entrypoint.sh \
    && useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
# Railway injects PORT; local docker-compose defaults to 8000.
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3"]
