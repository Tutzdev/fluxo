FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 10001 fluxo

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY fluxo ./fluxo

USER fluxo
EXPOSE 8000

# Migrations run before the server starts, so the schema and the code always match.
CMD ["sh", "-c", "alembic upgrade head && exec gunicorn --workers 2 --bind 0.0.0.0:8000 --access-logfile - fluxo.wsgi:app"]
